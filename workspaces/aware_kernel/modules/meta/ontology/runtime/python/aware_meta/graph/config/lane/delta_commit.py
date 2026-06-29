from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import cast
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)

from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
from aware_meta.graph.config.lane.common import (
    DEFAULT_OCG_COMMIT_STATUS,
    DEFAULT_OCG_SOURCE_LANGUAGE,
    OCG_DELTA_HINT_VERSION,
    SYSTEM_ACTOR_ID,
    bool_env_default_true,
    clone_object_instance_graph_for_validation,
)
from aware_meta.graph.config.lane.delta_support import (
    collect_stale_schema_owned_type_descriptor_mismatches,
    expand_delta_scoped_candidate_ids,
    load_post_oig_diff_index_sidecar,
    load_pre_oig_diff_index_sidecar,
    log_ocg_delta_progress,
    lane_commit_id,
    load_pre_oig_from_snapshot_fast_path,
    oig_fingerprint_diff_scope,
    summarize_delta_drift,
    should_skip_oig_scoped_diff_by_relationship_scope,
    strip_volatile_source_reference_attrs_from_oig,
    write_post_oig_diff_index_sidecar,
    write_pre_oig_diff_index_sidecar,
)
from aware_meta.graph.config.lane.errors import (
    OcgLaneCommitError,
    OcgLaneHashContractDriftDetails,
    OcgLaneHashContractDriftError,
    OcgLaneHeadPreHashMismatchDetails,
    OcgLaneHeadPreHashMismatchError,
)
from aware_meta.graph.config.lane.oigi import (
    resolve_ocg_lane_object_instance_graph_identity_id,
)
from aware_meta.graph.config.lane.plan import OCGDeltaCommitPlan
from aware_meta.graph.config.lane.projection import (
    PreparedSeedProjection,
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
    schema_configs_by_id_from_schema_view,
)
from aware_meta.graph.config.lane.registry import (
    collect_lane_instance_models,
    resolve_root_class_instance_snapshot,
)
from aware_meta.graph.config.lane.scope import (
    candidate_class_instance_ids_for_source_object_ids,
)
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
    maybe_record_orm_session_metrics,
    maybe_timed,
)
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneBeforeOigHashMismatchError,
    LaneCommitError,
    LaneHeadPreHashMismatchError,
)
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
    FSSnapshotStore,
    JsonObject,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.scoped_index import (
    OigGraphDiffIndex,
    OigRelationshipScopeIndex,
    build_oig_relationship_scope_index,
    emit_relationship_scope_index_metrics,
    select_relationships_for_membership_tuples,
    select_relationships_from_scope_index,
)
from aware_orm.session.autobind import disable_autobind


@dataclass(frozen=True, slots=True)
class _OigScopedDiffResult:
    changes: list[ObjectInstanceGraphChange]
    needs_full_diff: bool
    scoped_fallback_to_full: bool
    commit_apply_hash_validated: bool
    diff_mode: str | None


def _int_env(name: str, *, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _oig_commit_object_count(graph: object) -> int:
    class_instances = getattr(graph, "class_instances", ()) or ()
    relationships = getattr(graph, "class_instance_relationships", ()) or ()
    return len(class_instances) + len(relationships)


def _explicit_delta_full_fallback_guard_reason(
    *,
    before_oig: object,
    after_oig: object,
    delta_node_count: int,
    candidate_id_count: int,
    fallback_reason: str,
) -> str | None:
    max_oig_objects = _int_env(
        "AWARE_OCG_EXPLICIT_DELTA_FULL_FALLBACK_MAX_OIG_OBJECTS",
        default=25_000,
    )
    if max_oig_objects <= 0:
        return None
    before_count = _oig_commit_object_count(before_oig)
    after_count = _oig_commit_object_count(after_oig)
    max_count = max(before_count, after_count)
    if max_count <= max_oig_objects:
        return None
    return (
        "explicit_delta_full_fallback_guard:"
        f"reason={fallback_reason} max_oig_objects={max_count} "
        f"limit={max_oig_objects} delta_nodes={delta_node_count} "
        f"candidate_ids={candidate_id_count}"
    )


async def commit_ocg_delta_to_lane(
    *,
    previous_ocg: ObjectConfigGraph | None,
    ocg: ObjectConfigGraph,
    delta: ObjectConfigGraphDelta | None,
    branch_id: UUID,
    author_id: UUID = SYSTEM_ACTOR_ID,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    prepared_projection: PreparedSeedProjection | None = None,
    store: FSCommitStore | None = None,
    opg_name: str = "ObjectConfigGraph",
    commit_action: CommitActionDescriptor | None = None,
    source_language: CodeLanguage = DEFAULT_OCG_SOURCE_LANGUAGE,
    status: CommitStatus = DEFAULT_OCG_COMMIT_STATUS,
    allow_append: bool = True,
    projection_hash_override: str | None = None,
    timings: SeedTimings | None = None,
) -> OCGDeltaCommitPlan:
    """Commit an OCG evolution delta to the OIG lane."""
    maybe_record_orm_session_metrics(timings=timings, key_prefix="ocg_delta.orm_pre")
    maybe_metric(timings, "ocg_delta_prev_provided", bool(previous_ocg is not None))

    external_graphs_list = list(
        prepared_projection.external_graphs
        if prepared_projection is not None
        else (external_graphs or ())
    )
    if previous_ocg is not None and previous_ocg.id != ocg.id:
        raise OcgLaneCommitError(
            f"OCG delta commit requires matching ids; prev={previous_ocg.id} new={ocg.id}"
        )

    if delta is not None and previous_ocg is not None:
        if (
            delta.graph_hash_pre
            and previous_ocg.hash
            and delta.graph_hash_pre != previous_ocg.hash
        ):
            raise OcgLaneCommitError(
                "OCG delta pre-hash mismatch: "
                + f"delta.graph_hash_pre={delta.graph_hash_pre} previous_ocg.hash={previous_ocg.hash}"
            )
        if delta.graph_hash_post and ocg.hash and delta.graph_hash_post != ocg.hash:
            raise OcgLaneCommitError(
                "OCG delta post-hash mismatch: "
                + f"delta.graph_hash_post={delta.graph_hash_post} ocg.hash={ocg.hash}"
            )
    if (
        delta is not None
        and delta.graph_hash_post
        and ocg.hash
        and delta.graph_hash_post != ocg.hash
    ):
        raise OcgLaneCommitError(
            "OCG delta post-hash mismatch: "
            + f"delta.graph_hash_post={delta.graph_hash_post} ocg.hash={ocg.hash}"
        )

    if prepared_projection is None:
        maybe_metric(timings, "ocg_delta_projection_prepared", False)
        with maybe_timed(timings, "ocg_delta.resolve_seed_projection_context"):
            schema_graph, opg = resolve_ocg_seed_projection_context(
                ocg=ocg,
                external_graphs=external_graphs_list,
                opg_name=opg_name,
            )
        schema_view = compose_ocg_seed_schema_graph(
            schema_graph=schema_graph,
            external_graphs=external_graphs_list,
            object_projection_graph=opg,
            timings=timings,
        )
    else:
        maybe_metric(timings, "ocg_delta_projection_prepared", True)
        schema_graph = prepared_projection.schema_graph
        opg = prepared_projection.opg
        schema_view = prepared_projection.schema_view
    if not opg.projection_hash:
        raise OcgLaneCommitError(
            "OCG delta commit requires ObjectProjectionGraph.projection_hash"
        )
    lane_projection_hash = (
        str(projection_hash_override).strip()
        if projection_hash_override is not None
        else str(opg.projection_hash).strip()
    )
    if not lane_projection_hash:
        raise OcgLaneCommitError(
            "OCG delta commit requires a non-empty lane projection_hash"
        )
    log_ocg_delta_progress(
        "start",
        branch_id=branch_id,
        projection_hash=lane_projection_hash,
        has_previous_ocg=bool(previous_ocg is not None),
        delta_nodes=(0 if delta is None else len(delta.node_deltas)),
    )
    opg_for_lane = (
        opg
        if str(opg.projection_hash).strip() == lane_projection_hash
        else opg.model_copy(update={"projection_hash": lane_projection_hash})
    )
    object_instance_graph_identity_id = (
        resolve_ocg_lane_object_instance_graph_identity_id(
            identity_graph=schema_graph,
            object_projection_graph=opg_for_lane,
            object_instance_graph_id=ocg.id,
        )
    )

    if (
        delta is not None
        and not delta.node_deltas
        and (delta.graph_hash_pre or "") == (delta.graph_hash_post or "")
    ):
        return OCGDeltaCommitPlan(
            committed=False,
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            object_instance_graph_id=ocg.id,
            root_object_id=ocg.id,
            graph_hash_pre="",
            graph_hash_post="",
            commit_id=None,
            delta_node_count=0,
            changes=[],
        )

    store = store or FSCommitStore()
    with maybe_timed(timings, "ocg_delta.head"):
        head = await store.head(
            branch_id=branch_id, projection_hash=lane_projection_hash
        )
    head_commit_raw = head.get("commit_id") if head else None
    head_post_hash = head.get("graph_hash_post") if head else None
    log_ocg_delta_progress(
        "head_loaded",
        head_commit_id=head_commit_raw,
        head_graph_hash_post=head_post_hash,
    )
    if not head_commit_raw:
        raise OcgLaneCommitError(
            "OCG lane is empty (missing seed commit); "
            + "cannot append non-seed delta commit. "
            + f"branch_id={branch_id} projection_hash={lane_projection_hash}"
        )

    try:
        parent_commit_id = UUID(str(head_commit_raw))
    except Exception as exc:
        raise OcgLaneCommitError(
            f"Invalid lane HEAD commit_id: {head_commit_raw}"
        ) from exc

    schema_class_configs_by_id, schema_attribute_configs_by_id = (
        schema_configs_by_id_from_schema_view(schema_view)
    )
    instance_external_graphs = [
        graph for graph in external_graphs_list if graph.id != schema_graph.id
    ]

    def _build_post_oig() -> ObjectInstanceGraph:
        with maybe_timed(timings, "ocg_delta.collect_instances_post"):
            after_objects_by_id = collect_lane_instance_models(
                ocg=ocg,
                external_graphs=instance_external_graphs,
            )
        if not after_objects_by_id:
            raise OcgLaneCommitError(
                "OCG delta commit requires current OCG to contain ORM objects"
            )
        maybe_metric(timings, "ocg_delta_instance_count_post", len(after_objects_by_id))
        with maybe_timed(timings, "ocg_delta.enum_resolver_post"):
            after_enum_resolver = build_enum_option_resolver(
                object_config_graph=schema_view
            )
        with maybe_timed(timings, "ocg_delta.build_oig_post"):
            post_oig = build_object_instance_graph(
                root_instance=ocg,
                object_config_graph=schema_view,
                object_projection_graph=opg_for_lane,
                name="object_config_graph",
                description="OCG snapshot (post)",
                oig_id=ocg.id,
                instance_registry=sorted(
                    after_objects_by_id.values(), key=lambda obj: str(obj.id)
                ),
                enum_option_resolver=after_enum_resolver,
                timings=timings,
                timing_key_prefix="ocg_delta.build_oig_post",
            )
        log_ocg_delta_progress(
            "build_oig_post_done",
            oig_instances_post=len(post_oig.class_instances),
            oig_relationships_post=len(post_oig.class_instance_relationships),
        )
        return post_oig

    def _compute_post_hashes(*, post_oig: ObjectInstanceGraph) -> tuple[str, str, int]:
        with maybe_timed(timings, "ocg_delta.build_index_post_raw"):
            index_post_raw = build_index(post_oig)
        with maybe_timed(timings, "ocg_delta.compute_hash_post_raw"):
            graph_hash_post_raw_local = compute_hash(post_oig, index=index_post_raw)
        with maybe_timed(timings, "ocg_delta.strip_volatile_source_refs_post"):
            removed_post_local = strip_volatile_source_reference_attrs_from_oig(
                graph=post_oig,
                schema_attribute_configs_by_id=schema_attribute_configs_by_id,
                timings=timings,
                metric_prefix="ocg_delta",
            )
        with maybe_timed(timings, "ocg_delta.build_index_post"):
            index_post = build_index(post_oig)
        with maybe_timed(timings, "ocg_delta.compute_hash_post"):
            graph_hash_post_local = compute_hash(post_oig, index=index_post)
        return graph_hash_post_raw_local, graph_hash_post_local, removed_post_local

    after_oig: ObjectInstanceGraph | None = None
    graph_hash_post_raw = ""
    graph_hash_post = ""
    removed_post = 0
    post_hash_prefetched = False
    post_descriptor_validated = False

    def _validate_post_oig_schema(*, post_oig: ObjectInstanceGraph) -> None:
        stale_post_descriptor_mismatches = (
            collect_stale_schema_owned_type_descriptor_mismatches(
                graph=post_oig,
                schema_attribute_configs_by_id=schema_attribute_configs_by_id,
            )
        )
        if stale_post_descriptor_mismatches:
            mismatch_preview = "; ".join(stale_post_descriptor_mismatches)
            raise OcgLaneCommitError(
                "Post-build OIG does not match current schema-owned AttributeTypeDescriptor ids. "
                + "This indicates a latest-only builder/schema drift. "
                + f"Examples: {mismatch_preview}"
            )

    if head_post_hash:
        after_oig = _build_post_oig()
        graph_hash_post_raw, graph_hash_post, removed_post = _compute_post_hashes(
            post_oig=after_oig
        )
        post_hash_prefetched = True
        _validate_post_oig_schema(post_oig=after_oig)
        post_descriptor_validated = True
        if head_post_hash in {graph_hash_post_raw, graph_hash_post}:
            maybe_metric(timings, "ocg_delta_noop_reason", "head_post_hash_matches")
            maybe_record_orm_session_metrics(
                timings=timings, key_prefix="ocg_delta.orm_post"
            )
            log_ocg_delta_progress(
                "noop_head_hash_matches",
                graph_hash_post=graph_hash_post,
                commit_id=parent_commit_id,
            )
            return OCGDeltaCommitPlan(
                committed=False,
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                object_instance_graph_id=ocg.id,
                root_object_id=ocg.id,
                graph_hash_pre=str(head_post_hash),
                graph_hash_post=graph_hash_post,
                commit_id=parent_commit_id,
                delta_node_count=0 if delta is None else len(delta.node_deltas),
                changes=[],
            )

    if previous_ocg is None:
        log_ocg_delta_progress(
            "build_oig_pre_start",
            mode="materialize_lane_head",
            parent_commit_id=parent_commit_id,
        )
        with maybe_timed(timings, "ocg_delta.materialize_oig_pre"):
            fast_snapshot = load_pre_oig_from_snapshot_fast_path(
                store=store,
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                commit_id=parent_commit_id,
                timings=timings,
            )
            if fast_snapshot is not None:
                before_oig, _indexes = fast_snapshot
                maybe_metric(
                    timings,
                    "ocg_delta_materialize_pre_mode",
                    "snapshot_fast_path",
                )
            else:
                maybe_metric(
                    timings,
                    "ocg_delta_materialize_pre_mode",
                    "materializer",
                )
                materializer = OIGMaterializer(
                    commits=store,
                    snaps=FSSnapshotStore(root_dir=store.aware_root),
                )
                with maybe_timed(timings, "ocg_delta.materialize_oig_pre_materializer"):
                    before_oig, _indexes = await materializer.get(
                        branch_id=branch_id,
                        ocg=schema_view,
                        opg=opg_for_lane,
                        commit_id=parent_commit_id,
                        oig_id=ocg.id,
                        timings=timings,
                    )
    else:
        with maybe_timed(timings, "ocg_delta.collect_instances_pre"):
            before_objects_by_id = collect_lane_instance_models(
                ocg=previous_ocg,
                external_graphs=instance_external_graphs,
            )
        if not before_objects_by_id:
            raise OcgLaneCommitError(
                "OCG delta commit requires previous OCG to contain ORM objects"
            )
        maybe_metric(timings, "ocg_delta_instance_count_pre", len(before_objects_by_id))
        with maybe_timed(timings, "ocg_delta.enum_resolver_pre"):
            before_enum_resolver = build_enum_option_resolver(
                object_config_graph=schema_view
            )
        with maybe_timed(timings, "ocg_delta.build_oig_pre"):
            before_oig = build_object_instance_graph(
                root_instance=previous_ocg,
                object_config_graph=schema_view,
                object_projection_graph=opg_for_lane,
                name="object_config_graph",
                description="OCG snapshot (pre)",
                oig_id=ocg.id,
                instance_registry=sorted(
                    before_objects_by_id.values(), key=lambda obj: str(obj.id)
                ),
                enum_option_resolver=before_enum_resolver,
                timings=timings,
                timing_key_prefix="ocg_delta.build_oig_pre",
            )
    log_ocg_delta_progress(
        "build_oig_pre_done",
        oig_instances_pre=len(before_oig.class_instances),
        oig_relationships_pre=len(before_oig.class_instance_relationships),
    )
    snapshot_pre_hash_attr = str(before_oig.hash or "").strip()

    if after_oig is None:
        after_oig = _build_post_oig()

    stale_pre_descriptor_mismatches = (
        collect_stale_schema_owned_type_descriptor_mismatches(
            graph=before_oig,
            schema_attribute_configs_by_id=schema_attribute_configs_by_id,
        )
    )
    if stale_pre_descriptor_mismatches:
        mismatch_preview = "; ".join(stale_pre_descriptor_mismatches)
        raise OcgLaneCommitError(
            "Latest-only OIG lane snapshot is stale against current schema-owned "
            + "AttributeTypeDescriptor ids. Delete the existing OIG lane snapshots and "
            + "rebuild the lane from current Meta schema truth. "
            + f"Examples: {mismatch_preview}"
        )

    if not post_descriptor_validated:
        _validate_post_oig_schema(post_oig=after_oig)

    with maybe_timed(timings, "ocg_delta.build_index_pre_raw"):
        index_pre_raw = build_index(before_oig)
    with maybe_timed(timings, "ocg_delta.compute_hash_pre_raw"):
        graph_hash_pre_raw = compute_hash(before_oig, index=index_pre_raw)
    if previous_ocg is None and snapshot_pre_hash_attr:
        if snapshot_pre_hash_attr == graph_hash_pre_raw:
            maybe_metric(
                timings, "ocg_delta_pre_hash_raw_source", "snapshot_attr_validated"
            )
        else:
            maybe_metric(
                timings, "ocg_delta_pre_hash_raw_source", "computed_snapshot_attr_stale"
            )
            maybe_metric(
                timings, "ocg_delta_pre_hash_snapshot_attr", snapshot_pre_hash_attr
            )
    else:
        maybe_metric(timings, "ocg_delta_pre_hash_raw_source", "computed")
    if not post_hash_prefetched:
        graph_hash_post_raw, graph_hash_post, removed_post = _compute_post_hashes(
            post_oig=after_oig
        )

    with maybe_timed(timings, "ocg_delta.strip_volatile_source_refs_pre"):
        removed_pre = strip_volatile_source_reference_attrs_from_oig(
            graph=before_oig,
            schema_attribute_configs_by_id=schema_attribute_configs_by_id,
            timings=timings,
            metric_prefix="ocg_delta",
        )
    maybe_metric(
        timings, "ocg_delta_volatile_source_ref_attrs_removed_pre", removed_pre
    )
    maybe_metric(
        timings, "ocg_delta_volatile_source_ref_attrs_removed_post", removed_post
    )
    maybe_metric(timings, "ocg_delta_graph_hash_pre_raw", graph_hash_pre_raw)
    maybe_metric(timings, "ocg_delta_graph_hash_post_raw", graph_hash_post_raw)

    if previous_ocg is None and removed_pre == 0 and graph_hash_pre_raw:
        graph_hash_pre = graph_hash_pre_raw
        maybe_metric(timings, "ocg_delta_pre_hash_source", "snapshot_attr_no_strip")
    else:
        with maybe_timed(timings, "ocg_delta.build_index_pre"):
            index_pre = build_index(before_oig)
        with maybe_timed(timings, "ocg_delta.compute_hash_pre"):
            graph_hash_pre = compute_hash(before_oig, index=index_pre)
        maybe_metric(
            timings,
            "ocg_delta_pre_hash_source",
            "computed_after_strip" if previous_ocg is None else "computed",
        )
    maybe_metric(
        timings, "ocg_delta_oig_instance_count_pre", len(before_oig.class_instances)
    )
    maybe_metric(
        timings,
        "ocg_delta_oig_relationship_count_pre",
        len(before_oig.class_instance_relationships),
    )
    maybe_metric(
        timings, "ocg_delta_oig_instance_count_post", len(after_oig.class_instances)
    )
    maybe_metric(
        timings,
        "ocg_delta_oig_relationship_count_post",
        len(after_oig.class_instance_relationships),
    )

    if head_post_hash and head_post_hash in {graph_hash_post_raw, graph_hash_post}:
        maybe_metric(timings, "ocg_delta_noop_reason", "head_post_hash_matches")
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_delta.orm_post"
        )
        log_ocg_delta_progress(
            "noop_head_hash_matches",
            graph_hash_post=graph_hash_post,
            commit_id=parent_commit_id,
        )
        return OCGDeltaCommitPlan(
            committed=False,
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            object_instance_graph_id=ocg.id,
            root_object_id=ocg.id,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            commit_id=parent_commit_id,
            delta_node_count=0 if delta is None else len(delta.node_deltas),
            changes=[],
        )
    if head_post_hash and head_post_hash not in {graph_hash_pre_raw, graph_hash_pre}:
        raise OcgLaneHeadPreHashMismatchError(
            details=OcgLaneHeadPreHashMismatchDetails(
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                head_commit_id=parent_commit_id,
                head_graph_hash_post=str(head_post_hash),
                graph_hash_pre_raw=graph_hash_pre_raw,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                previous_ocg_supplied=previous_ocg is not None,
                source_error_type="delta_commit_head_check",
            )
        )

    graph_hash_pre_commit = graph_hash_pre
    if head_post_hash and head_post_hash in {graph_hash_pre_raw, graph_hash_pre}:
        graph_hash_pre_commit = str(head_post_hash)

    if graph_hash_pre == graph_hash_post:
        maybe_metric(timings, "ocg_delta_noop_reason", "pre_post_hash_matches")
        maybe_metric(timings, "ocg_delta_diff_mode", "hash_noop")
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_delta.orm_post"
        )
        log_ocg_delta_progress(
            "noop_pre_post_hash_matches",
            graph_hash_post=graph_hash_post,
            commit_id=parent_commit_id,
        )
        return OCGDeltaCommitPlan(
            committed=False,
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            object_instance_graph_id=ocg.id,
            root_object_id=ocg.id,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            commit_id=parent_commit_id,
            delta_node_count=0 if delta is None else len(delta.node_deltas),
            changes=[],
        )

    changes: list[ObjectInstanceGraphChange] = []
    created_at = datetime.now(timezone.utc)
    diff_mode: str | None = None
    commit_apply_hash_validated = False
    relationship_scope_index_pre: OigRelationshipScopeIndex | None = None
    relationship_scope_index_post: OigRelationshipScopeIndex | None = None
    relationship_membership_index_pre: OigRelationshipScopeIndex | None = None
    relationship_membership_index_post: OigRelationshipScopeIndex | None = None
    pre_diff_index_hint: OigGraphDiffIndex | None = None
    post_diff_index_hint: OigGraphDiffIndex | None = None

    def _get_relationship_scope_indexes() -> (
        tuple[OigRelationshipScopeIndex, OigRelationshipScopeIndex]
    ):
        nonlocal relationship_scope_index_pre, relationship_scope_index_post
        if relationship_scope_index_pre is None:
            with maybe_timed(timings, "ocg_delta.build_relationship_scope_index_pre"):
                relationship_scope_index_pre = build_oig_relationship_scope_index(
                    graph=before_oig,
                    include_scope_maps=True,
                    include_membership_map=False,
                )
            emit_relationship_scope_index_metrics(
                timings=timings,
                metric_prefix="ocg_delta_relationship_scope_index_pre",
                index=relationship_scope_index_pre,
            )
        if relationship_scope_index_post is None:
            with maybe_timed(timings, "ocg_delta.build_relationship_scope_index_post"):
                relationship_scope_index_post = build_oig_relationship_scope_index(
                    graph=after_oig,
                    include_scope_maps=True,
                    include_membership_map=False,
                )
            emit_relationship_scope_index_metrics(
                timings=timings,
                metric_prefix="ocg_delta_relationship_scope_index_post",
                index=relationship_scope_index_post,
            )
        return relationship_scope_index_pre, relationship_scope_index_post

    def _get_relationship_membership_indexes() -> (
        tuple[OigRelationshipScopeIndex, OigRelationshipScopeIndex]
    ):
        nonlocal relationship_membership_index_pre, relationship_membership_index_post
        if relationship_membership_index_pre is None:
            with maybe_timed(
                timings, "ocg_delta.build_relationship_membership_index_pre"
            ):
                relationship_membership_index_pre = build_oig_relationship_scope_index(
                    graph=before_oig,
                    include_scope_maps=False,
                    include_membership_map=True,
                )
            emit_relationship_scope_index_metrics(
                timings=timings,
                metric_prefix="ocg_delta_relationship_membership_index_pre",
                index=relationship_membership_index_pre,
            )
        if relationship_membership_index_post is None:
            with maybe_timed(
                timings, "ocg_delta.build_relationship_membership_index_post"
            ):
                relationship_membership_index_post = build_oig_relationship_scope_index(
                    graph=after_oig,
                    include_scope_maps=False,
                    include_membership_map=True,
                )
            emit_relationship_scope_index_metrics(
                timings=timings,
                metric_prefix="ocg_delta_relationship_membership_index_post",
                index=relationship_membership_index_post,
            )
        return relationship_membership_index_pre, relationship_membership_index_post

    log_ocg_delta_progress("diff_start")
    with maybe_timed(timings, "ocg_delta.diff_changes"):
        if delta is not None and delta.node_deltas:
            maybe_metric(timings, "ocg_delta_has_delta", True)
            candidate_entity_ids = {
                node_delta.entity_id for node_delta in delta.node_deltas
            }
            candidate_node_ids = {
                node_delta.node_id
                for node_delta in delta.node_deltas
                if node_delta.node_id is not None
            }
            candidate_ids = set(candidate_entity_ids) | set(candidate_node_ids)
            candidate_ids |= candidate_class_instance_ids_for_source_object_ids(
                graph=before_oig,
                source_object_ids=candidate_entity_ids,
            )
            candidate_ids |= candidate_class_instance_ids_for_source_object_ids(
                graph=after_oig,
                source_object_ids=candidate_entity_ids,
            )
            maybe_metric(
                timings,
                "ocg_delta_delta_scoped_candidate_entity_ids",
                len(candidate_entity_ids),
            )
            maybe_metric(
                timings,
                "ocg_delta_delta_scoped_candidate_node_ids",
                len(candidate_node_ids),
            )
            candidate_ids = expand_delta_scoped_candidate_ids(
                candidate_ids=candidate_ids,
                before_oig=before_oig,
                after_oig=after_oig,
                timings=timings,
            )
            maybe_metric(
                timings, "ocg_delta_delta_scoped_candidate_ids", len(candidate_ids)
            )

            before_by_id = {
                class_instance.id: class_instance
                for class_instance in before_oig.class_instances
            }
            after_by_id = {
                class_instance.id: class_instance
                for class_instance in after_oig.class_instances
            }
            old_instances = [
                before_by_id[candidate_id]
                for candidate_id in sorted(candidate_ids, key=str)
                if candidate_id in before_by_id
            ]
            new_instances = [
                after_by_id[candidate_id]
                for candidate_id in sorted(candidate_ids, key=str)
                if candidate_id in after_by_id
            ]

            pre_rel_index, post_rel_index = _get_relationship_scope_indexes()
            with maybe_timed(
                timings, "ocg_delta.select_delta_scoped_relationships_pre"
            ):
                old_rels = select_relationships_from_scope_index(
                    index=pre_rel_index,
                    candidate_ids=candidate_ids,
                    include_relationship_config_ids=True,
                )
            with maybe_timed(
                timings, "ocg_delta.select_delta_scoped_relationships_post"
            ):
                new_rels = select_relationships_from_scope_index(
                    index=post_rel_index,
                    candidate_ids=candidate_ids,
                    include_relationship_config_ids=True,
                )
            maybe_metric(
                timings, "ocg_delta_delta_scoped_relationship_selector", "indexed"
            )
            maybe_metric(
                timings, "ocg_delta_delta_scoped_instance_count_pre", len(old_instances)
            )
            maybe_metric(
                timings,
                "ocg_delta_delta_scoped_instance_count_post",
                len(new_instances),
            )
            maybe_metric(
                timings, "ocg_delta_delta_scoped_relationship_count_pre", len(old_rels)
            )
            maybe_metric(
                timings, "ocg_delta_delta_scoped_relationship_count_post", len(new_rels)
            )

            old_root_class_instance = resolve_root_class_instance_snapshot(
                class_instances=old_instances,
                expected_root_class_instance_id=before_oig.root_class_instance_id,
                fallback_root_class_instance=before_oig.root_class_instance,
            )
            new_root_class_instance = resolve_root_class_instance_snapshot(
                class_instances=new_instances,
                expected_root_class_instance_id=after_oig.root_class_instance_id,
                fallback_root_class_instance=after_oig.root_class_instance,
            )

            with disable_autobind():
                old_graph = ObjectInstanceGraph(
                    id=before_oig.id,
                    key=before_oig.key,
                    name=before_oig.name,
                    description=before_oig.description,
                    object_projection_graph_id=before_oig.object_projection_graph_id,
                    root_class_instance_id=before_oig.root_class_instance_id,
                    root_class_instance=old_root_class_instance,
                    class_instances=list(old_instances),
                    class_instance_relationships=list(old_rels),
                    hash=before_oig.hash,
                )
                new_graph = ObjectInstanceGraph(
                    id=before_oig.id,
                    key=after_oig.key,
                    name=before_oig.name,
                    description=before_oig.description,
                    object_projection_graph_id=after_oig.object_projection_graph_id,
                    root_class_instance_id=after_oig.root_class_instance_id,
                    root_class_instance=new_root_class_instance,
                    class_instances=list(new_instances),
                    class_instance_relationships=list(new_rels),
                    hash=after_oig.hash,
                )

            with maybe_timed(timings, "ocg_delta.diff_changes_delta_scoped"):
                changes = diff_object_instance_graph_changes(
                    old=old_graph,
                    new=new_graph,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    created_at=created_at,
                )
            maybe_metric(timings, "ocg_delta_diff_mode", "delta_scoped")
            diff_mode = "delta_scoped"

            needs_fallback = not changes and graph_hash_pre != graph_hash_post
            fallback_reason = "no_changes_but_hash_changed"
            if needs_fallback:
                maybe_metric(
                    timings,
                    "ocg_delta_delta_scoped_fallback_reason",
                    fallback_reason,
                )

            if not needs_fallback and changes:
                with maybe_timed(timings, "ocg_delta.validate_delta_scoped_changes"):
                    try:
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_delta_scoped_changes_clone",
                        ):
                            candidate_graph = (
                                clone_object_instance_graph_for_validation(
                                    before_oig,
                                    changes=changes,
                                    timings=timings,
                                    metric_prefix="ocg_delta_delta_scoped_validation",
                                )
                            )
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_delta_scoped_changes_apply",
                        ):
                            _ = apply_object_instance_graph_changes(
                                graph=candidate_graph,
                                changes=changes,
                                attribute_configs_by_id=schema_attribute_configs_by_id,
                                class_configs_by_id=schema_class_configs_by_id,
                            )
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_delta_scoped_changes_hash",
                        ):
                            candidate_hash = compute_hash(
                                candidate_graph,
                                index=build_index(candidate_graph),
                            )
                        if candidate_hash != graph_hash_post:
                            needs_fallback = True
                            fallback_reason = "validation_hash_mismatch"
                            maybe_metric(
                                timings,
                                "ocg_delta_delta_scoped_validation_ok",
                                False,
                            )
                            maybe_metric(
                                timings,
                                "ocg_delta_delta_scoped_validation_hash",
                                candidate_hash,
                            )
                        else:
                            maybe_metric(
                                timings,
                                "ocg_delta_delta_scoped_validation_ok",
                                True,
                            )
                            commit_apply_hash_validated = True
                    except Exception as exc:
                        needs_fallback = True
                        fallback_reason = f"validation_error:{type(exc).__name__}"
                        maybe_metric(
                            timings, "ocg_delta_delta_scoped_validation_ok", False
                        )
                        maybe_metric(
                            timings,
                            "ocg_delta_delta_scoped_validation_error",
                            str(exc),
                        )

            if needs_fallback:
                guard_reason = _explicit_delta_full_fallback_guard_reason(
                    before_oig=before_oig,
                    after_oig=after_oig,
                    delta_node_count=len(delta.node_deltas),
                    candidate_id_count=len(candidate_ids),
                    fallback_reason=fallback_reason,
                )
                if guard_reason is not None:
                    maybe_metric(
                        timings,
                        "ocg_delta_explicit_delta_full_fallback_guarded",
                        True,
                    )
                    maybe_metric(
                        timings,
                        "ocg_delta_explicit_delta_full_fallback_guard_limit",
                        _int_env(
                            "AWARE_OCG_EXPLICIT_DELTA_FULL_FALLBACK_MAX_OIG_OBJECTS",
                            default=25_000,
                        ),
                    )
                    raise OcgLaneCommitError(
                        "Explicit OCG delta scoped diff requested a full OIG fallback "
                        "on a broad lane. Refusing the unbounded fallback so the caller "
                        "can reset/reseed or provide a narrower delta. " + guard_reason
                    )
                maybe_metric(timings, "ocg_delta_diff_mode", "full_fallback")
                diff_mode = "full_fallback"
                commit_apply_hash_validated = False
                with maybe_timed(timings, "ocg_delta.diff_changes_full_fallback"):
                    changes = diff_object_instance_graph_changes(
                        old=before_oig,
                        new=after_oig,
                        object_instance_graph_identity_id=object_instance_graph_identity_id,
                        created_at=created_at,
                    )
        else:
            maybe_metric(timings, "ocg_delta_has_delta", bool(delta is not None))
            if previous_ocg is None:
                pre_diff_index_hint = load_pre_oig_diff_index_sidecar(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=lane_projection_hash,
                    commit_id=parent_commit_id,
                    graph=before_oig,
                    timings=timings,
                )
                maybe_metric(
                    timings,
                    "ocg_delta_oig_diff_index_pre_source",
                    "sidecar" if pre_diff_index_hint is not None else "rebuild",
                )
                post_diff_index_hint = load_post_oig_diff_index_sidecar(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=lane_projection_hash,
                    graph_hash=graph_hash_post,
                    graph=after_oig,
                    timings=timings,
                )
                maybe_metric(
                    timings,
                    "ocg_delta_oig_diff_index_post_source",
                    "sidecar" if post_diff_index_hint is not None else "rebuild",
                )
            scope = oig_fingerprint_diff_scope(
                before_oig=before_oig,
                after_oig=after_oig,
                timings=timings,
                before_graph_index_hint=pre_diff_index_hint,
                after_graph_index_hint=post_diff_index_hint,
            )
            if (
                previous_ocg is None
                and pre_diff_index_hint is None
                and scope.before_graph_index is not None
            ):
                maybe_metric(
                    timings,
                    "ocg_delta_oig_diff_index_pre_sidecar_written",
                    write_pre_oig_diff_index_sidecar(
                        store=store,
                        branch_id=branch_id,
                        projection_hash=lane_projection_hash,
                        commit_id=parent_commit_id,
                        graph_hash=graph_hash_pre_raw,
                        index=scope.before_graph_index,
                        timings=timings,
                    ),
                )
            if (
                previous_ocg is None
                and post_diff_index_hint is None
                and scope.after_graph_index is not None
            ):
                maybe_metric(
                    timings,
                    "ocg_delta_oig_diff_index_post_sidecar_written",
                    write_post_oig_diff_index_sidecar(
                        store=store,
                        branch_id=branch_id,
                        projection_hash=lane_projection_hash,
                        graph_hash=graph_hash_post,
                        index=scope.after_graph_index,
                        timings=timings,
                    ),
                )
            base_candidate_ids = set(scope.candidate_ids)
            changed_rel_tuples = set(scope.changed_relationship_tuples)
            needs_full_diff = True
            scoped_fallback_to_full = False
            if base_candidate_ids and graph_hash_pre != graph_hash_post:
                scoped_result = _run_oig_scoped_diff(
                    base_candidate_ids=base_candidate_ids,
                    changed_rel_tuples=changed_rel_tuples,
                    before_oig=before_oig,
                    after_oig=after_oig,
                    before_graph_index=scope.before_graph_index,
                    after_graph_index=scope.after_graph_index,
                    created_at=created_at,
                    graph_hash_pre=graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    schema_attribute_configs_by_id=schema_attribute_configs_by_id,
                    schema_class_configs_by_id=schema_class_configs_by_id,
                    timings=timings,
                    get_relationship_scope_indexes=_get_relationship_scope_indexes,
                    get_relationship_membership_indexes=_get_relationship_membership_indexes,
                )
                changes = scoped_result.changes
                needs_full_diff = scoped_result.needs_full_diff
                scoped_fallback_to_full = scoped_result.scoped_fallback_to_full
                commit_apply_hash_validated = scoped_result.commit_apply_hash_validated
                diff_mode = scoped_result.diff_mode

            if needs_full_diff:
                if scoped_fallback_to_full:
                    maybe_metric(timings, "ocg_delta_diff_mode", "full_fallback")
                    diff_mode = "full_fallback"
                    maybe_metric(timings, "ocg_delta_oig_scoped_full_fallback", True)
                    with maybe_timed(timings, "ocg_delta.diff_changes_full_fallback"):
                        changes = diff_object_instance_graph_changes(
                            old=before_oig,
                            new=after_oig,
                            object_instance_graph_identity_id=object_instance_graph_identity_id,
                            created_at=created_at,
                        )
                else:
                    with maybe_timed(timings, "ocg_delta.diff_changes_full"):
                        changes = diff_object_instance_graph_changes(
                            old=before_oig,
                            new=after_oig,
                            object_instance_graph_identity_id=object_instance_graph_identity_id,
                            created_at=created_at,
                        )
                    maybe_metric(timings, "ocg_delta_diff_mode", "full")
                    diff_mode = "full"
    maybe_metric(timings, "ocg_delta_change_count", len(changes))
    log_ocg_delta_progress(
        "diff_done", change_count=len(changes), diff_mode=(diff_mode or "unknown")
    )

    if not changes:
        if graph_hash_pre != graph_hash_post:
            raise OcgLaneCommitError(
                "No Change graph produced, but OIG content hash changed. "
                + f"pre={graph_hash_pre} post={graph_hash_post}"
            )
        return OCGDeltaCommitPlan(
            committed=False,
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            object_instance_graph_id=ocg.id,
            root_object_id=ocg.id,
            graph_hash_pre=graph_hash_pre_commit,
            graph_hash_post=graph_hash_post,
            commit_id=None,
            delta_node_count=0 if delta is None else len(delta.node_deltas),
            changes=[],
        )

    validate_apply_hash = bool_env_default_true("AWARE_OIG_COMMIT_APPLY_HASH_VALIDATE")
    maybe_metric(
        timings,
        "ocg_delta_commit_apply_hash_validation_enabled",
        validate_apply_hash,
    )
    if diff_mode:
        maybe_metric(timings, "ocg_delta_commit_diff_mode_final", diff_mode)

    if validate_apply_hash and not commit_apply_hash_validated:
        with maybe_timed(timings, "ocg_delta.validate_commit_apply_hash"):
            with maybe_timed(timings, "ocg_delta.validate_commit_apply_hash_clone"):
                candidate_graph = clone_object_instance_graph_for_validation(
                    before_oig,
                    changes=changes,
                    timings=timings,
                    metric_prefix="ocg_delta_commit_apply_hash_validation",
                )
            with maybe_timed(timings, "ocg_delta.validate_commit_apply_hash_apply"):
                _ = apply_object_instance_graph_changes(
                    graph=candidate_graph,
                    changes=changes,
                    attribute_configs_by_id=schema_attribute_configs_by_id,
                    class_configs_by_id=schema_class_configs_by_id,
                )
            with maybe_timed(timings, "ocg_delta.validate_commit_apply_hash_hash"):
                candidate_hash = compute_hash(
                    candidate_graph, index=build_index(candidate_graph)
                )
        if candidate_hash != graph_hash_post:
            maybe_metric(timings, "ocg_delta_commit_apply_hash_validation_ok", False)
            maybe_metric(
                timings,
                "ocg_delta_commit_apply_hash_validation_hash",
                candidate_hash,
            )
            raise OcgLaneCommitError(
                "Commit apply+hash validation failed: "
                + "applying the Change graph to OIG(pre) did not reproduce the expected post hash. "
                + f"pre={graph_hash_pre} expected_post={graph_hash_post} got_post={candidate_hash} "
                + f"diff_mode={diff_mode or 'unknown'}"
            )
        commit_apply_hash_validated = True

    if validate_apply_hash:
        maybe_metric(
            timings,
            "ocg_delta_commit_apply_hash_validation_ok",
            bool(commit_apply_hash_validated),
        )

    ocg_hash_post = (
        (delta.graph_hash_post if delta is not None else None) or ocg.hash or ""
    )
    if not ocg_hash_post:
        raise OcgLaneCommitError("OCG delta commit requires a non-empty OCG post-hash")

    commit_id = lane_commit_id(
        branch_id=branch_id,
        projection_hash=lane_projection_hash,
        parent_commit_id=parent_commit_id,
        ocg_hash_post=ocg_hash_post,
    )
    log_ocg_delta_progress("commit_id_computed", commit_id=commit_id)

    if not allow_append:
        existing = await store.get_commit(
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            commit_id=commit_id,
        )
        if existing is None:
            try:
                op_counts: Counter[str] = Counter()
                kind_counts: Counter[str] = Counter()
                for change in changes:
                    kind_counts[str(change.type.value or "unknown")] += 1
                    op_counts[str(change.change.type.value or "unknown")] += 1
                ops_repr = dict(op_counts)
                kinds_repr = dict(kind_counts)
            except Exception:
                ops_repr = {}
                kinds_repr = {}

            try:
                drift_samples = summarize_delta_drift(
                    changes=changes,
                    before_oig=before_oig,
                    after_oig=after_oig,
                    schema_class_configs_by_id=schema_class_configs_by_id,
                    schema_attribute_configs_by_id=schema_attribute_configs_by_id,
                )
                drift_samples_repr = json.dumps(
                    drift_samples, sort_keys=True, default=str
                )
            except Exception:
                drift_samples_repr = None

            raise OcgLaneCommitError(
                "Missing deterministic OCG delta commit (compiler must emit it): "
                + f"branch_id={branch_id} projection_hash={lane_projection_hash} commit_id={commit_id} "
                + f"parent_commit_id={parent_commit_id} head_commit_id={head_commit_raw} "
                + "head_graph_hash_post="
                + f"{head_post_hash} graph_hash_pre={graph_hash_pre} graph_hash_post={graph_hash_post} "
                + f"ocg_hash_post={ocg_hash_post} "
                + f"oig_instances_pre={len(before_oig.class_instances)} "
                + f"oig_relationships_pre={len(before_oig.class_instance_relationships)} "
                + f"oig_instances_post={len(after_oig.class_instances)} "
                + f"oig_relationships_post={len(after_oig.class_instance_relationships)} "
                + f"delta_nodes={(0 if delta is None else len(delta.node_deltas))} "
                + f"change_ops={ops_repr} change_kinds={kinds_repr} "
                + f"drift_samples={drift_samples_repr}"
            )
        if (
            existing.graph_hash_pre != graph_hash_pre_commit
            or existing.graph_hash_post != graph_hash_post
        ):
            raise OcgLaneCommitError(
                "Existing deterministic OCG delta commit differs from expected payload: "
                + f"branch_id={branch_id} projection_hash={lane_projection_hash} commit_id={commit_id}"
            )
        parents = existing.commit.commit_parents
        if len(parents) != 1 or str(parents[0].parent_commit_id) != str(
            parent_commit_id
        ):
            raise OcgLaneCommitError(
                "Existing deterministic OCG delta commit has unexpected parents: "
                + f"branch_id={branch_id} projection_hash={lane_projection_hash} commit_id={commit_id} "
                + f"expected_parent_commit_id={parent_commit_id} parents={len(parents)}"
            )
        if (
            existing.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise OcgLaneCommitError(
                "Existing deterministic OCG delta commit carries legacy OIGI metadata: "
                + f"branch_id={branch_id} projection_hash={lane_projection_hash} commit_id={commit_id} "
                + f"have={existing.object_instance_graph_identity_id} "
                + f"expected={object_instance_graph_identity_id}"
            )
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_delta.orm_post"
        )
        return OCGDeltaCommitPlan(
            committed=False,
            branch_id=branch_id,
            projection_hash=lane_projection_hash,
            object_instance_graph_id=ocg.id,
            root_object_id=ocg.id,
            graph_hash_pre=graph_hash_pre_commit,
            graph_hash_post=graph_hash_post,
            commit_id=commit_id,
            delta_node_count=0 if delta is None else len(delta.node_deltas),
            changes=[],
        )

    committer = FSLaneCommitter(store=store)
    log_ocg_delta_progress("write_commit_start", commit_id=commit_id)
    with maybe_timed(timings, "ocg_delta.write_commit"):
        try:
            oig_commit = await committer.commit(
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=ocg.id,
                before_oig=before_oig,
                root_object_id=ocg.id,
                changes=changes,
                graph_hash_pre=graph_hash_pre_commit,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                commit_id=commit_id,
                source_language=source_language,
                status=status,
                commit_action=commit_action,
                schema_attribute_configs_by_id=schema_attribute_configs_by_id,
            )
        except LaneHeadPreHashMismatchError as exc:
            raise OcgLaneHeadPreHashMismatchError(
                details=OcgLaneHeadPreHashMismatchDetails(
                    branch_id=branch_id,
                    projection_hash=lane_projection_hash,
                    head_commit_id=exc.details.head_commit_id,
                    head_graph_hash_post=exc.details.head_graph_hash_post,
                    graph_hash_pre_raw=graph_hash_pre_raw,
                    graph_hash_pre=exc.details.graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    previous_ocg_supplied=previous_ocg is not None,
                    source_error_type=type(exc).__name__,
                )
            ) from exc
        except LaneBeforeOigHashMismatchError as exc:
            raise OcgLaneHashContractDriftError(
                details=OcgLaneHashContractDriftDetails(
                    branch_id=branch_id,
                    projection_hash=lane_projection_hash,
                    object_instance_graph_id=exc.details.object_instance_graph_id,
                    head_commit_id=parent_commit_id,
                    head_graph_hash_post=(
                        None if head_post_hash is None else str(head_post_hash)
                    ),
                    graph_hash_pre_raw=graph_hash_pre_raw,
                    graph_hash_pre=exc.details.graph_hash_pre,
                    graph_hash_post=graph_hash_post,
                    lane_hash=exc.details.lane_hash,
                    raw_hash=exc.details.raw_hash,
                    previous_ocg_supplied=previous_ocg is not None,
                    source_error_type=type(exc).__name__,
                )
            ) from exc
        except LaneCommitError:
            raise
    committed = bool(oig_commit is not None)
    plan_commit_id = oig_commit.commit.id if oig_commit is not None else None
    log_ocg_delta_progress(
        "write_commit_done", committed=committed, commit_id=plan_commit_id
    )
    if plan_commit_id is not None:
        try:
            commit_path = (
                Path(store.aware_root)
                / ".aware"
                / "oig"
                / str(branch_id)
                / str(lane_projection_hash)
                / "commits"
                / f"{plan_commit_id}.json"
            )
            if commit_path.exists():
                maybe_metric(
                    timings, "ocg_delta_commit_bytes", int(commit_path.stat().st_size)
                )
        except Exception:
            pass

    if delta is not None and plan_commit_id is not None:
        hint_payload: JsonObject = {
            "v": OCG_DELTA_HINT_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": str(lane_projection_hash),
            "commit_id": str(plan_commit_id),
            "ocg_delta": cast(
                object,
                delta.model_dump(mode="json", exclude_none=True, by_alias=True),
            ),
        }
        with maybe_timed(timings, "ocg_delta.write_hint"):
            wrote_hint = store.put_ocg_delta_hint(
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                commit_id=plan_commit_id,
                payload=hint_payload,
            )
        maybe_metric(timings, "ocg_delta_hint_written", wrote_hint)
        maybe_metric(timings, "ocg_delta_hint_present", True)
        try:
            hint_path = store.ocg_delta_hint_path(
                branch_id=branch_id,
                projection_hash=lane_projection_hash,
                commit_id=plan_commit_id,
            )
            if hint_path.exists():
                maybe_metric(
                    timings, "ocg_delta_hint_bytes", int(hint_path.stat().st_size)
                )
        except Exception:
            pass

    maybe_record_orm_session_metrics(timings=timings, key_prefix="ocg_delta.orm_post")
    return OCGDeltaCommitPlan(
        committed=committed,
        branch_id=branch_id,
        projection_hash=lane_projection_hash,
        object_instance_graph_id=ocg.id,
        root_object_id=ocg.id,
        graph_hash_pre=graph_hash_pre_commit,
        graph_hash_post=graph_hash_post,
        commit_id=plan_commit_id,
        delta_node_count=0 if delta is None else len(delta.node_deltas),
        changes=list(changes),
    )


def _run_oig_scoped_diff(
    *,
    base_candidate_ids: set[UUID],
    changed_rel_tuples: set[tuple[UUID, UUID, UUID]],
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    before_graph_index: OigGraphDiffIndex | None,
    after_graph_index: OigGraphDiffIndex | None,
    created_at: datetime,
    graph_hash_pre: str,
    graph_hash_post: str,
    object_instance_graph_identity_id: UUID,
    schema_attribute_configs_by_id: dict[UUID, AttributeConfig],
    schema_class_configs_by_id: dict[UUID, ClassConfig],
    timings: SeedTimings | None,
    get_relationship_scope_indexes: Callable[
        [],
        tuple[OigRelationshipScopeIndex, OigRelationshipScopeIndex],
    ],
    get_relationship_membership_indexes: Callable[
        [],
        tuple[OigRelationshipScopeIndex, OigRelationshipScopeIndex],
    ],
) -> _OigScopedDiffResult:
    raw_max = (os.getenv("AWARE_OCG_DELTA_CANDIDATE_MAX_IDS") or "").strip()
    try:
        max_ids = max(int(raw_max), 0) if raw_max else 20_000
    except Exception:
        max_ids = 20_000
    if max_ids and len(base_candidate_ids) > max_ids:
        maybe_metric(timings, "ocg_delta_oig_scoped_skipped", True)
        maybe_metric(
            timings,
            "ocg_delta_oig_scoped_skip_reason",
            "candidate_ids_too_large",
        )
        maybe_metric(
            timings,
            "ocg_delta_oig_scoped_candidate_ids_base",
            len(base_candidate_ids),
        )
        return _OigScopedDiffResult(
            changes=[],
            needs_full_diff=True,
            scoped_fallback_to_full=False,
            commit_apply_hash_validated=False,
            diff_mode=None,
        )

    maybe_metric(timings, "ocg_delta_oig_scoped_skipped", False)
    if before_graph_index is not None and after_graph_index is not None:
        before_by_id = before_graph_index.class_instances_by_id
        after_by_id = after_graph_index.class_instances_by_id
        maybe_metric(
            timings, "ocg_delta_oig_scoped_instance_index_source", "precomputed"
        )
    else:
        before_by_id = {
            class_instance.id: class_instance
            for class_instance in before_oig.class_instances
        }
        after_by_id = {
            class_instance.id: class_instance
            for class_instance in after_oig.class_instances
        }
        maybe_metric(timings, "ocg_delta_oig_scoped_instance_index_source", "scan")

    scope_candidates: list[tuple[str, set[UUID], bool]] = []
    if changed_rel_tuples:
        scope_candidates.append(("base_exact_rels", set(base_candidate_ids), True))
    scope_candidates.append(("base", set(base_candidate_ids), False))
    expanded_candidate_ids: set[UUID] | None = None
    expansion_attempted = False
    pending_scope_candidates = list(scope_candidates)
    needs_full_diff = True
    scoped_fallback_to_full = False
    commit_apply_hash_validated = False
    diff_mode: str | None = None
    scoped_changes: list[ObjectInstanceGraphChange] = []
    old_instances: list[ClassInstance] = []
    new_instances: list[ClassInstance] = []
    old_rels: list[ClassInstanceRelationship] = []
    new_rels: list[ClassInstanceRelationship] = []

    while pending_scope_candidates and needs_full_diff:
        for scope_mode, scope_ids, use_exact_rel_tuples in pending_scope_candidates:
            maybe_metric(timings, "ocg_delta_oig_scoped_scope_mode", scope_mode)
            old_instances = [
                before_by_id[candidate_id]
                for candidate_id in sorted(scope_ids, key=str)
                if candidate_id in before_by_id
            ]
            new_instances = [
                after_by_id[candidate_id]
                for candidate_id in sorted(scope_ids, key=str)
                if candidate_id in after_by_id
            ]
            if use_exact_rel_tuples:
                pre_rel_membership_index, post_rel_membership_index = (
                    get_relationship_membership_indexes()
                )
                with maybe_timed(
                    timings,
                    "ocg_delta.select_oig_scoped_exact_relationships_pre",
                ):
                    old_rels = select_relationships_for_membership_tuples(
                        index=pre_rel_membership_index,
                        membership_tuples=changed_rel_tuples,
                    )
                with maybe_timed(
                    timings,
                    "ocg_delta.select_oig_scoped_exact_relationships_post",
                ):
                    new_rels = select_relationships_for_membership_tuples(
                        index=post_rel_membership_index,
                        membership_tuples=changed_rel_tuples,
                    )
                maybe_metric(
                    timings,
                    "ocg_delta_oig_scoped_relationship_selector_mode",
                    "exact_membership",
                )
            else:
                pre_rel_scope_index, post_rel_scope_index = (
                    get_relationship_scope_indexes()
                )
                with maybe_timed(
                    timings,
                    "ocg_delta.select_oig_scoped_relationships_pre",
                ):
                    old_rels = select_relationships_from_scope_index(
                        index=pre_rel_scope_index,
                        candidate_ids=scope_ids,
                        include_relationship_config_ids=False,
                    )
                with maybe_timed(
                    timings,
                    "ocg_delta.select_oig_scoped_relationships_post",
                ):
                    new_rels = select_relationships_from_scope_index(
                        index=post_rel_scope_index,
                        candidate_ids=scope_ids,
                        include_relationship_config_ids=False,
                    )
                maybe_metric(
                    timings,
                    "ocg_delta_oig_scoped_relationship_selector_mode",
                    "candidate_scope",
                )
            maybe_metric(
                timings, "ocg_delta_oig_scoped_relationship_selector", "indexed"
            )
            maybe_metric(
                timings, "ocg_delta_oig_scoped_instance_count_pre", len(old_instances)
            )
            maybe_metric(
                timings, "ocg_delta_oig_scoped_instance_count_post", len(new_instances)
            )
            maybe_metric(
                timings, "ocg_delta_oig_scoped_relationship_count_pre", len(old_rels)
            )
            maybe_metric(
                timings, "ocg_delta_oig_scoped_relationship_count_post", len(new_rels)
            )
            (
                skip_scoped_diff,
                rel_coverage_pre,
                rel_coverage_post,
                rel_coverage_limit,
            ) = should_skip_oig_scoped_diff_by_relationship_scope(
                total_relationships_pre=len(before_oig.class_instance_relationships),
                total_relationships_post=len(after_oig.class_instance_relationships),
                scoped_relationships_pre=len(old_rels),
                scoped_relationships_post=len(new_rels),
            )
            maybe_metric(
                timings,
                "ocg_delta_oig_scoped_relationship_coverage_pre",
                rel_coverage_pre,
            )
            maybe_metric(
                timings,
                "ocg_delta_oig_scoped_relationship_coverage_post",
                rel_coverage_post,
            )
            maybe_metric(
                timings,
                "ocg_delta_oig_scoped_relationship_coverage_limit",
                rel_coverage_limit,
            )
            if skip_scoped_diff:
                maybe_metric(timings, "ocg_delta_oig_scoped_skipped", True)
                maybe_metric(
                    timings,
                    "ocg_delta_oig_scoped_skip_reason",
                    f"relationship_scope_too_broad:{scope_mode}",
                )
                continue

            old_root_class_instance = resolve_root_class_instance_snapshot(
                class_instances=old_instances,
                expected_root_class_instance_id=before_oig.root_class_instance_id,
                fallback_root_class_instance=before_oig.root_class_instance,
            )
            new_root_class_instance = resolve_root_class_instance_snapshot(
                class_instances=new_instances,
                expected_root_class_instance_id=after_oig.root_class_instance_id,
                fallback_root_class_instance=after_oig.root_class_instance,
            )

            with disable_autobind():
                old_graph = ObjectInstanceGraph(
                    id=before_oig.id,
                    key=before_oig.key,
                    name=before_oig.name,
                    description=before_oig.description,
                    object_projection_graph_id=before_oig.object_projection_graph_id,
                    root_class_instance_id=before_oig.root_class_instance_id,
                    root_class_instance=old_root_class_instance,
                    class_instances=list(old_instances),
                    class_instance_relationships=list(old_rels),
                    hash=before_oig.hash,
                )
                new_graph = ObjectInstanceGraph(
                    id=before_oig.id,
                    key=after_oig.key,
                    name=before_oig.name,
                    description=before_oig.description,
                    object_projection_graph_id=after_oig.object_projection_graph_id,
                    root_class_instance_id=after_oig.root_class_instance_id,
                    root_class_instance=new_root_class_instance,
                    class_instances=list(new_instances),
                    class_instance_relationships=list(new_rels),
                    hash=after_oig.hash,
                )

            with maybe_timed(timings, "ocg_delta.diff_changes_oig_scoped"):
                scoped_changes = diff_object_instance_graph_changes(
                    old=old_graph,
                    new=new_graph,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    created_at=created_at,
                )
            maybe_metric(timings, "ocg_delta_diff_mode", "oig_scoped")
            diff_mode = "oig_scoped"

            needs_scope_fallback = (
                not scoped_changes and graph_hash_pre != graph_hash_post
            )
            if needs_scope_fallback:
                maybe_metric(
                    timings,
                    "ocg_delta_oig_scoped_fallback_reason",
                    f"no_changes_but_hash_changed:{scope_mode}",
                )

            if not needs_scope_fallback and scoped_changes:
                with maybe_timed(timings, "ocg_delta.validate_oig_scoped_changes"):
                    try:
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_oig_scoped_changes_clone",
                        ):
                            candidate_graph = (
                                clone_object_instance_graph_for_validation(
                                    before_oig,
                                    changes=scoped_changes,
                                    timings=timings,
                                    metric_prefix="ocg_delta_oig_scoped_validation",
                                )
                            )
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_oig_scoped_changes_apply",
                        ):
                            _ = apply_object_instance_graph_changes(
                                graph=candidate_graph,
                                changes=scoped_changes,
                                attribute_configs_by_id=schema_attribute_configs_by_id,
                                class_configs_by_id=schema_class_configs_by_id,
                            )
                        with maybe_timed(
                            timings,
                            "ocg_delta.validate_oig_scoped_changes_hash",
                        ):
                            candidate_hash = compute_hash(
                                candidate_graph,
                                index=build_index(candidate_graph),
                            )
                        if candidate_hash != graph_hash_post:
                            needs_scope_fallback = True
                            maybe_metric(
                                timings, "ocg_delta_oig_scoped_validation_ok", False
                            )
                            maybe_metric(
                                timings,
                                "ocg_delta_oig_scoped_validation_hash",
                                candidate_hash,
                            )
                        else:
                            maybe_metric(
                                timings, "ocg_delta_oig_scoped_validation_ok", True
                            )
                            commit_apply_hash_validated = True
                    except Exception as exc:
                        needs_scope_fallback = True
                        maybe_metric(
                            timings, "ocg_delta_oig_scoped_validation_ok", False
                        )
                        maybe_metric(
                            timings,
                            "ocg_delta_oig_scoped_validation_error",
                            str(exc),
                        )

            if needs_scope_fallback:
                scoped_fallback_to_full = True
                commit_apply_hash_validated = False
                continue

            needs_full_diff = False
            break

        if not needs_full_diff:
            break

        if expanded_candidate_ids is None:
            expansion_attempted = True
            maybe_metric(timings, "ocg_delta_oig_scoped_lazy_expansion", True)
            expanded_candidate_ids = expand_delta_scoped_candidate_ids(
                candidate_ids=set(base_candidate_ids),
                before_oig=before_oig,
                after_oig=after_oig,
                metric_prefix="ocg_delta_oig_scoped",
                timings=timings,
            )
            if expanded_candidate_ids != base_candidate_ids:
                pending_scope_candidates = [("expanded", expanded_candidate_ids, False)]
                continue
        break

    if not expansion_attempted:
        maybe_metric(timings, "ocg_delta_oig_scoped_lazy_expansion", False)
        maybe_metric(timings, "ocg_delta_oig_scoped_candidate_ids_added_pre", 0)
        maybe_metric(timings, "ocg_delta_oig_scoped_candidate_ids_added_post", 0)
        maybe_metric(timings, "ocg_delta_oig_scoped_candidate_expansion_depth", 0)
        maybe_metric(
            timings, "ocg_delta_oig_scoped_candidate_expansion_truncated", False
        )
        maybe_metric(
            timings,
            "ocg_delta_oig_scoped_candidate_ids_expanded",
            len(base_candidate_ids),
        )

    return _OigScopedDiffResult(
        changes=scoped_changes,
        needs_full_diff=needs_full_diff,
        scoped_fallback_to_full=scoped_fallback_to_full,
        commit_apply_hash_validated=commit_apply_hash_validated,
        diff_mode=diff_mode,
    )


__all__ = ["commit_ocg_delta_to_lane"]
