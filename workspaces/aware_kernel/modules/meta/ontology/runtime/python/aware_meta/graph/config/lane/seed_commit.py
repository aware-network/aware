from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
from aware_meta.graph.config.lane.common import (
    DEFAULT_OCG_COMMIT_STATUS,
    DEFAULT_OCG_SOURCE_LANGUAGE,
    SEED_CREATED_AT,
    SYSTEM_ACTOR_ID,
    bool_env_default_true,
    clone_object_instance_graph_for_validation,
)
from aware_meta.graph.config.lane.errors import OcgSeedError
from aware_meta.graph.config.lane.plan import OCGSeedPlan
from aware_meta.graph.config.lane.oigi import (
    resolve_ocg_lane_object_instance_graph_identity_id,
)
from aware_meta.graph.config.lane.projection import (
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
    schema_configs_by_id_from_schema_view,
)
from aware_meta.graph.config.lane.registry import collect_lane_instance_models
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
    maybe_record_orm_session_metrics,
    maybe_timed,
)
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import (
    build_object_instance_graph,
    build_rooted_object_instance_graph_base,
)
from aware_meta.graph.instance.commit.builder import (
    OigCommitBuildError,
    build_object_instance_graph_commit_from_changes,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.validator import OigCommitValidationError
from aware_meta.graph.instance.diff import build_object_instance_graph_seed_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


def _int_env(name: str, *, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _seed_apply_hash_validation_size_gate(
    *,
    change_count: int,
) -> tuple[bool, int]:
    max_changes = _int_env(
        "AWARE_OCG_SEED_APPLY_HASH_VALIDATE_MAX_CHANGES",
        default=25_000,
    )
    return max_changes > 0 and change_count > max_changes, max_changes


def _head_commit_uuid(head: object) -> UUID | None:
    if not isinstance(head, dict):
        return None
    raw_commit_id = head.get("commit_id")
    if not isinstance(raw_commit_id, str) or not raw_commit_id.strip():
        return None
    try:
        return UUID(raw_commit_id)
    except ValueError:
        return None


def _head_graph_hash(head: object, key: str) -> str:
    if not isinstance(head, dict):
        return ""
    raw_value = head.get(key)
    return raw_value if isinstance(raw_value, str) else ""


def _build_ocg_seed_plan_and_commit(
    *,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    ocg_hash: str,
    opg_name: str,
    author_id: UUID,
    external_graphs: Iterable[ObjectConfigGraph],
    projection_hash_override: str | None,
    timings: SeedTimings | None,
) -> tuple[OCGSeedPlan, ObjectInstanceGraphCommit]:
    """
    Build the deterministic OCG seed snapshot plan and commit payload.

    This is shared by:
    - `ensure_ocg_seeded_lane` (compiler-owned lane writes/validation)
    - runtime DB seed flows that need the seed snapshot (without writing to the commit store)
    """
    maybe_record_orm_session_metrics(timings=timings, key_prefix="ocg_seed.orm_pre")

    external_graphs_list = list(external_graphs or ())

    with maybe_timed(timings, "ocg_seed.resolve_seed_projection_context"):
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
    if not opg.projection_hash:
        raise OcgSeedError("OCG seed requires ObjectProjectionGraph.projection_hash")
    lane_projection_hash = (
        str(projection_hash_override).strip()
        if projection_hash_override is not None
        else str(opg.projection_hash).strip()
    )
    if not lane_projection_hash:
        raise OcgSeedError("OCG seed requires a non-empty lane projection_hash")
    opg_for_lane = (
        opg
        if str(opg.projection_hash).strip() == lane_projection_hash
        else opg.model_copy(update={"projection_hash": lane_projection_hash})
    )

    # Performance contract:
    # - `schema_graph` (almost always kernel `meta-ontology`) is only needed for schema resolution.
    # - Traversing its *instances* is prohibitively expensive and can dominate compile time.
    # Only include external graphs whose instances may actually be referenced by the OCG snapshot.
    instance_external_graphs = [
        g for g in external_graphs_list if g.id != schema_graph.id
    ]
    maybe_metric(
        timings, "ocg_seed_instance_external_graph_count", len(instance_external_graphs)
    )
    with maybe_timed(timings, "ocg_seed.collect_instances"):
        objects_by_id = collect_lane_instance_models(
            ocg=ocg,
            external_graphs=instance_external_graphs,
        )
    if not objects_by_id:
        raise OcgSeedError("OCG seed requires at least one ORM object (empty OCG)")
    maybe_metric(timings, "ocg_seed_instance_count", len(objects_by_id))

    oig_id = ocg.id
    with maybe_timed(timings, "ocg_seed.build_oig_empty"):
        before_oig = build_rooted_object_instance_graph_base(
            key="object_config_graph",
            name="object_config_graph",
            description="OCG seed base snapshot",
            object_config_graph=schema_view,
            object_projection_graph=opg_for_lane,
            root_source_object_id=ocg.id,
            oig_id=oig_id,
        )

    with maybe_timed(timings, "ocg_seed.enum_resolver"):
        enum_option_resolver = build_enum_option_resolver(
            object_config_graph=schema_view,
        )

    with maybe_timed(timings, "ocg_seed.build_oig_post"):
        after_oig = build_object_instance_graph(
            root_instance=ocg,
            object_config_graph=schema_view,
            object_projection_graph=opg_for_lane,
            name="object_config_graph",
            description="OCG seed snapshot",
            oig_id=oig_id,
            instance_registry=sorted(objects_by_id.values(), key=lambda o: str(o.id)),
            enum_option_resolver=enum_option_resolver,
            timings=timings,
            timing_key_prefix="ocg_seed.build_oig_post",
        )
    maybe_metric(
        timings, "ocg_seed_oig_instance_count_post", len(after_oig.class_instances)
    )
    maybe_metric(
        timings,
        "ocg_seed_oig_relationship_count_post",
        len(after_oig.class_instance_relationships),
    )
    object_instance_graph_identity_id = (
        resolve_ocg_lane_object_instance_graph_identity_id(
            identity_graph=schema_graph,
            object_projection_graph=opg_for_lane,
            object_instance_graph_id=before_oig.id,
        )
    )

    with maybe_timed(timings, "ocg_seed.compute_hash_pre"):
        graph_hash_pre = compute_hash(before_oig, index=build_index(before_oig))
    with maybe_timed(timings, "ocg_seed.compute_hash_post"):
        graph_hash_post = compute_hash(after_oig, index=build_index(after_oig))
    with maybe_timed(timings, "ocg_seed.build_seed_changes"):
        changes = build_object_instance_graph_seed_changes(
            before=before_oig,
            new=after_oig,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            created_at=SEED_CREATED_AT,
        )
    if not changes:
        raise OcgSeedError("OCG seed commit missing change payload")
    maybe_metric(timings, "ocg_seed_change_count", len(changes))
    if not graph_hash_post:
        raise OcgSeedError("OCG seed commit missing graph_hash_post")

    validate_apply_hash = bool_env_default_true("AWARE_OIG_COMMIT_APPLY_HASH_VALIDATE")
    (
        validation_size_gate,
        validate_apply_hash_max_changes,
    ) = _seed_apply_hash_validation_size_gate(
        change_count=len(changes),
    )
    maybe_metric(
        timings,
        "ocg_seed_commit_apply_hash_validation_max_changes",
        validate_apply_hash_max_changes,
    )
    validation_skipped_for_size = validate_apply_hash and validation_size_gate
    if validation_skipped_for_size:
        validate_apply_hash = False
    maybe_metric(
        timings,
        "ocg_seed_commit_apply_hash_validation_enabled",
        validate_apply_hash,
    )
    maybe_metric(
        timings,
        "ocg_seed_commit_apply_hash_validation_skipped_for_size",
        validation_skipped_for_size,
    )
    if validate_apply_hash:
        schema_class_configs_by_id, schema_attribute_configs_by_id = (
            schema_configs_by_id_from_schema_view(schema_view)
        )
        with maybe_timed(timings, "ocg_seed.validate_commit_apply_hash"):
            with maybe_timed(timings, "ocg_seed.validate_commit_apply_hash_clone"):
                candidate_graph = clone_object_instance_graph_for_validation(
                    before_oig,
                    changes=changes,
                    timings=timings,
                    metric_prefix="ocg_seed_commit_apply_hash_validation",
                )
            _ = apply_object_instance_graph_changes(
                graph=candidate_graph,
                changes=changes,
                attribute_configs_by_id=schema_attribute_configs_by_id,
                class_configs_by_id=schema_class_configs_by_id,
            )
            candidate_hash = compute_hash(
                candidate_graph, index=build_index(candidate_graph)
            )
        if candidate_hash != graph_hash_post:
            maybe_metric(timings, "ocg_seed_commit_apply_hash_validation_ok", False)
            maybe_metric(
                timings,
                "ocg_seed_commit_apply_hash_validation_hash",
                candidate_hash,
            )
            raise OcgSeedError(
                "Seed commit apply+hash validation failed: "
                + "applying the Change graph to OIG(pre) did not reproduce the expected post hash. "
                + f"expected_post={graph_hash_post} got_post={candidate_hash}"
            )
        maybe_metric(timings, "ocg_seed_commit_apply_hash_validation_ok", True)

    commit_id = _seed_commit_id(ocg_hash=ocg_hash, graph_hash_post=graph_hash_post)
    with maybe_timed(timings, "ocg_seed.build_commit_from_changes"):
        commit = build_object_instance_graph_commit_from_changes(
            before_oig=before_oig,
            changes=changes,
            branch_id=branch_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=after_oig.id,
            projection_hash=lane_projection_hash,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            parent_commit_id=None,
            commit_id=commit_id,
            source_language=DEFAULT_OCG_SOURCE_LANGUAGE,
            status=DEFAULT_OCG_COMMIT_STATUS,
            created_at=SEED_CREATED_AT,
        )

    plan = OCGSeedPlan(
        seeded=False,
        branch_id=branch_id,
        projection_hash=lane_projection_hash,
        object_instance_graph_id=oig_id,
        root_object_id=ocg.id,
        graph_hash_pre=commit.graph_hash_pre,
        graph_hash_post=commit.graph_hash_post,
        commit_id=commit_id,
        changes=changes,
        before_oig=before_oig,
        after_oig=after_oig,
        objects_by_id=objects_by_id,
    )
    return plan, commit


def build_ocg_seed_plan(
    *,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    ocg_hash: str,
    opg_name: str = "ObjectConfigGraph",
    author_id: UUID = SYSTEM_ACTOR_ID,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    projection_hash_override: str | None = None,
    timings: SeedTimings | None = None,
) -> OCGSeedPlan:
    """Build the deterministic OCG seed snapshot plan (no commit-store IO)."""
    plan, _ = _build_ocg_seed_plan_and_commit(
        ocg=ocg,
        branch_id=branch_id,
        ocg_hash=ocg_hash,
        opg_name=opg_name,
        author_id=author_id,
        external_graphs=external_graphs,
        projection_hash_override=projection_hash_override,
        timings=timings,
    )
    return plan


def _seed_commit_id(*, ocg_hash: str, graph_hash_post: str) -> UUID:
    """
    Deterministic seed commit id.

    Include the post graph hash so the seed rail can evolve without colliding with
    historical deterministic ids that used only `ocg_hash`.
    """
    if not (ocg_hash or "").strip():
        raise OcgSeedError("OCG seed commit id requires a non-empty ocg_hash")
    if not (graph_hash_post or "").strip():
        raise OcgSeedError("OCG seed commit id requires a non-empty graph_hash_post")
    return uuid5(NAMESPACE_URL, f"aware:ocg-seed:{ocg_hash}:{graph_hash_post}")


async def ensure_ocg_seeded_lane(
    *,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    ocg_hash: str,
    opg_name: str = "ObjectConfigGraph",
    author_id: UUID = SYSTEM_ACTOR_ID,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    store: FSCommitStore | None = None,
    allow_append: bool = True,
    projection_hash_override: str | None = None,
    timings: SeedTimings | None = None,
) -> OCGSeedPlan:
    """Ensure the canonical OCG seed commit exists in the OIG lane."""
    store = store or FSCommitStore()
    lane_projection_hash_override = (
        str(projection_hash_override).strip()
        if projection_hash_override is not None
        else ""
    )
    if lane_projection_hash_override:
        with maybe_timed(timings, "ocg_seed.head"):
            head = await store.head(
                branch_id=branch_id,
                projection_hash=lane_projection_hash_override,
            )
        head_commit_id = _head_commit_uuid(head)
        head_oig_id = (
            head.get("object_instance_graph_id") if isinstance(head, dict) else None
        )
        if head_commit_id is not None:
            maybe_metric(timings, "ocg_seed_lane_empty", False)
            maybe_metric(timings, "ocg_seed_head_fast_path", True)
            if head_oig_id and str(head_oig_id) != str(ocg.id):
                raise OcgSeedError(
                    "OCG seed lane OIG id mismatch: "
                    + f"head_object_instance_graph_id={head_oig_id} "
                    + f"expected_object_instance_graph_id={ocg.id}"
                )
            placeholder_oig = ObjectInstanceGraph.model_construct(
                id=ocg.id,
                class_instances=[],
                class_instance_relationships=[],
            )
            maybe_record_orm_session_metrics(
                timings=timings, key_prefix="ocg_seed.orm_post"
            )
            return OCGSeedPlan(
                seeded=False,
                branch_id=branch_id,
                projection_hash=lane_projection_hash_override,
                object_instance_graph_id=ocg.id,
                root_object_id=ocg.id,
                graph_hash_pre=_head_graph_hash(head, "graph_hash_pre"),
                graph_hash_post=_head_graph_hash(head, "graph_hash_post"),
                commit_id=head_commit_id,
                changes=[],
                before_oig=placeholder_oig,
                after_oig=placeholder_oig,
                objects_by_id={ocg.id: ocg},
            )

    plan, commit = _build_ocg_seed_plan_and_commit(
        ocg=ocg,
        branch_id=branch_id,
        ocg_hash=ocg_hash,
        opg_name=opg_name,
        author_id=author_id,
        external_graphs=external_graphs,
        projection_hash_override=projection_hash_override,
        timings=timings,
    )

    with maybe_timed(timings, "ocg_seed.head"):
        head = await store.head(
            branch_id=branch_id, projection_hash=plan.projection_hash
        )
    head_oig_id = head.get("object_instance_graph_id") if head else None

    head_commit_id = head.get("commit_id") if head else None
    lane_empty = not bool(head_commit_id)
    maybe_metric(timings, "ocg_seed_lane_empty", lane_empty)
    if lane_empty and not allow_append:
        raise OcgSeedError(
            "OCG seed lane is empty (no HEAD commit). "
            + "Compiler must emit the deterministic OCG seed commit before runtime boot. "
            + f"branch_id={branch_id} projection_hash={plan.projection_hash} ocg_hash={ocg_hash}"
        )

    if (
        not lane_empty
        and head_oig_id
        and str(head_oig_id) != str(plan.object_instance_graph_id)
    ):
        raise OcgSeedError(
            "OCG seed lane OIG id mismatch: "
            + f"head_object_instance_graph_id={head_oig_id} "
            + f"expected_object_instance_graph_id={plan.object_instance_graph_id}"
        )

    existing = None
    with maybe_timed(timings, "ocg_seed.get_existing_commit_envelope"):
        existing_envelope = await store.get_commit_envelope(
            branch_id=branch_id,
            projection_hash=plan.projection_hash,
            commit_id=plan.commit_id,
        )
    if existing_envelope is None:
        with maybe_timed(timings, "ocg_seed.get_existing_commit_fallback"):
            existing = await store.get_commit(
                branch_id=branch_id,
                projection_hash=plan.projection_hash,
                commit_id=plan.commit_id,
            )
    else:
        maybe_metric(timings, "ocg_seed_existing_commit_envelope_hit", True)
        if (
            existing_envelope.graph_hash_pre != plan.graph_hash_pre
            or existing_envelope.graph_hash_post != plan.graph_hash_post
        ):
            raise OcgSeedError(
                "Existing OCG seed commit differs from expected payload: "
                + f"branch_id={branch_id} projection_hash={plan.projection_hash} seed_commit_id={plan.commit_id}"
            )
        if existing_envelope.parent_commit_ids:
            raise OcgSeedError(
                f"OCG seed commit must not have parents: commit_id={plan.commit_id} parents={len(existing_envelope.parent_commit_ids)}"
            )
        try:
            commit_path = (
                Path(store.aware_root)
                / ".aware"
                / "oig"
                / str(branch_id)
                / str(plan.projection_hash)
                / "commits"
                / f"{plan.commit_id}.json"
            )
            if commit_path.exists():
                maybe_metric(
                    timings, "ocg_seed_commit_bytes", int(commit_path.stat().st_size)
                )
        except Exception:
            pass
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_seed.orm_post"
        )
        return plan
    if existing is not None:
        maybe_metric(timings, "ocg_seed_existing_commit_envelope_hit", False)
        if (
            existing.graph_hash_pre != plan.graph_hash_pre
            or existing.graph_hash_post != plan.graph_hash_post
        ):
            raise OcgSeedError(
                "Existing OCG seed commit differs from expected payload: "
                + f"branch_id={branch_id} projection_hash={plan.projection_hash} seed_commit_id={plan.commit_id}"
            )
        parents = existing.commit.commit_parents
        if parents:
            raise OcgSeedError(
                f"OCG seed commit must not have parents: commit_id={plan.commit_id} parents={len(parents)}"
            )
        try:
            _ = await store.put_commit_file(
                branch_id=branch_id,
                projection_hash=plan.projection_hash,
                commit=commit,
            )
        except ValueError as exc:
            raise OcgSeedError(
                "Existing OCG seed commit failed metadata repair: "
                + f"branch_id={branch_id} projection_hash={plan.projection_hash} "
                + f"seed_commit_id={plan.commit_id}: {exc}"
            ) from exc
        try:
            commit_path = (
                Path(store.aware_root)
                / ".aware"
                / "oig"
                / str(branch_id)
                / str(plan.projection_hash)
                / "commits"
                / f"{plan.commit_id}.json"
            )
            if commit_path.exists():
                maybe_metric(
                    timings, "ocg_seed_commit_bytes", int(commit_path.stat().st_size)
                )
        except Exception:
            pass
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_seed.orm_post"
        )
        return plan

    if not lane_empty:
        # Iterative lane contract: seed exactly once (empty -> snapshot), then evolve via
        # deterministic deltas. Do not emit detached per-version seed commits on non-empty lanes.
        maybe_metric(timings, "ocg_seed_missing_on_nonempty_lane", True)
        maybe_record_orm_session_metrics(
            timings=timings, key_prefix="ocg_seed.orm_post"
        )
        return OCGSeedPlan(
            seeded=False,
            branch_id=plan.branch_id,
            projection_hash=plan.projection_hash,
            object_instance_graph_id=plan.object_instance_graph_id,
            root_object_id=plan.root_object_id,
            graph_hash_pre=plan.graph_hash_pre,
            graph_hash_post=plan.graph_hash_post,
            commit_id=plan.commit_id,
            changes=list(plan.changes),
            before_oig=plan.before_oig,
            after_oig=plan.after_oig,
            objects_by_id=dict(plan.objects_by_id),
        )

    if not allow_append:
        raise OcgSeedError(
            "Missing deterministic OCG seed commit (compiler must emit it): "
            + f"branch_id={branch_id} projection_hash={plan.projection_hash} seed_commit_id={plan.commit_id}"
        )

    try:
        with maybe_timed(timings, "ocg_seed.write_commit"):
            _ = await store.append(
                branch_id=branch_id,
                projection_hash=plan.projection_hash,
                commit=commit,
                root_object_id=ocg.id,
            )
    except OigCommitBuildError as exc:
        raise OcgSeedError(f"Failed to build OCG seed commit: {exc}") from exc
    except (ValueError, OigCommitValidationError) as exc:
        raise OcgSeedError(f"Failed to emit OCG seed commit: {exc}") from exc

    try:
        commit_path = (
            Path(store.aware_root)
            / ".aware"
            / "oig"
            / str(branch_id)
            / str(plan.projection_hash)
            / "commits"
            / f"{plan.commit_id}.json"
        )
        if commit_path.exists():
            maybe_metric(
                timings, "ocg_seed_commit_bytes", int(commit_path.stat().st_size)
            )
    except Exception:
        pass
    maybe_record_orm_session_metrics(timings=timings, key_prefix="ocg_seed.orm_post")

    return OCGSeedPlan(
        seeded=True,
        branch_id=plan.branch_id,
        projection_hash=plan.projection_hash,
        object_instance_graph_id=plan.object_instance_graph_id,
        root_object_id=plan.root_object_id,
        graph_hash_pre=plan.graph_hash_pre,
        graph_hash_post=plan.graph_hash_post,
        commit_id=plan.commit_id,
        changes=plan.changes,
        before_oig=plan.before_oig,
        after_oig=plan.after_oig,
        objects_by_id=plan.objects_by_id,
    )
