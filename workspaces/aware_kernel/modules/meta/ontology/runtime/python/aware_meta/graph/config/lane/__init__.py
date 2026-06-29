from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, cast
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta.graph.config.lane.common import (
    DEFAULT_OCG_COMMIT_STATUS,
    DEFAULT_OCG_SOURCE_LANGUAGE,
    SYSTEM_ACTOR_ID,
)
from aware_meta.graph.config.lane.errors import (
    GraphIdentitySeedError,
    OcgLaneCommitError,
    OcgLaneHashContractDriftDetails,
    OcgLaneHashContractDriftError,
    OcgLaneHeadPreHashMismatchDetails,
    OcgLaneHeadPreHashMismatchError,
    OcgSeedError,
)
from aware_meta.graph.config.lane.identity_seed import (
    ensure_graph_identity_seeded_lane,
    preview_graph_identity_seed_plan,
)
from aware_meta.graph.config.lane.plan import (
    GraphIdentitySeedPlan,
    OCGDeltaCommitPlan,
    OCGSeedPlan,
)
from aware_meta.graph.config.lane.projection import (
    PreparedSeedProjection,
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
    resolve_ocg_seed_schema_view,
    schema_configs_by_id_from_schema_view,
)
from aware_meta.graph.config.lane.registry import (
    collect_lane_instance_models,
    collect_orm_models,
    resolve_root_class_instance_snapshot,
)
from aware_meta.graph.config.lane.scope import (
    CandidateScopedRelationship,
    relationship_in_candidate_scope,
)
from aware_meta.graph.config.lane.seed_commit import (
    build_ocg_seed_plan,
    ensure_ocg_seeded_lane,
)
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
    maybe_record_orm_session_metrics,
    maybe_timed,
)
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)

if TYPE_CHECKING:
    from aware_meta.graph.config.lane.delta_support import (
        OigFingerprintDiffScope,
        collect_stale_schema_owned_type_descriptor_mismatches,
        expand_delta_scoped_candidate_ids,
        is_volatile_source_reference_attribute_name,
        load_post_oig_diff_index_sidecar,
        load_pre_oig_from_snapshot_fast_path,
        oig_diff_index_post_sidecar_path,
        oig_diff_index_sidecar_path,
        oig_fingerprint_diff_scope,
        should_skip_oig_scoped_diff_by_relationship_scope,
        strip_volatile_source_reference_attrs_from_oig,
        write_post_oig_diff_index_sidecar,
        write_pre_oig_diff_index_sidecar,
    )
    from aware_meta.graph.instance.scoped_index import build_oig_graph_diff_index

    _TYPECHECK_EXPORTS = (
        OigFingerprintDiffScope,
        collect_stale_schema_owned_type_descriptor_mismatches,
        expand_delta_scoped_candidate_ids,
        is_volatile_source_reference_attribute_name,
        load_post_oig_diff_index_sidecar,
        load_pre_oig_from_snapshot_fast_path,
        oig_diff_index_post_sidecar_path,
        oig_diff_index_sidecar_path,
        oig_fingerprint_diff_scope,
        should_skip_oig_scoped_diff_by_relationship_scope,
        strip_volatile_source_reference_attrs_from_oig,
        write_post_oig_diff_index_sidecar,
        write_pre_oig_diff_index_sidecar,
        build_oig_graph_diff_index,
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
    from aware_meta.graph.config.lane.delta_commit import commit_ocg_delta_to_lane as impl
    return await impl(
        previous_ocg=previous_ocg,
        ocg=ocg,
        delta=delta,
        branch_id=branch_id,
        author_id=author_id,
        external_graphs=external_graphs,
        prepared_projection=prepared_projection,
        store=store,
        opg_name=opg_name,
        commit_action=commit_action,
        source_language=source_language,
        status=status,
        allow_append=allow_append,
        projection_hash_override=projection_hash_override,
        timings=timings,
    )


_DELTA_SUPPORT_EXPORTS = frozenset(
    {
        "OigFingerprintDiffScope",
        "collect_stale_schema_owned_type_descriptor_mismatches",
        "expand_delta_scoped_candidate_ids",
        "is_volatile_source_reference_attribute_name",
        "load_post_oig_diff_index_sidecar",
        "load_pre_oig_from_snapshot_fast_path",
        "oig_diff_index_post_sidecar_path",
        "oig_diff_index_sidecar_path",
        "oig_fingerprint_diff_scope",
        "should_skip_oig_scoped_diff_by_relationship_scope",
        "strip_volatile_source_reference_attrs_from_oig",
        "write_post_oig_diff_index_sidecar",
        "write_pre_oig_diff_index_sidecar",
        "_collect_stale_schema_owned_type_descriptor_mismatches",
        "_expand_delta_scoped_candidate_ids",
        "_is_volatile_source_reference_attribute_name",
        "_load_pre_oig_from_snapshot_fast_path",
        "_oig_fingerprint_diff_scope",
        "_should_skip_oig_scoped_diff_by_relationship_scope",
        "_strip_volatile_source_reference_attrs_from_oig",
        "_write_post_oig_diff_index_sidecar",
        "_write_pre_oig_diff_index_sidecar",
    }
)
_DELTA_SUPPORT_ALIAS_MAP = {
    "_collect_stale_schema_owned_type_descriptor_mismatches": (
        "collect_stale_schema_owned_type_descriptor_mismatches"
    ),
    "_expand_delta_scoped_candidate_ids": "expand_delta_scoped_candidate_ids",
    "_is_volatile_source_reference_attribute_name": (
        "is_volatile_source_reference_attribute_name"
    ),
    "_load_pre_oig_from_snapshot_fast_path": "load_pre_oig_from_snapshot_fast_path",
    "_oig_fingerprint_diff_scope": "oig_fingerprint_diff_scope",
    "_should_skip_oig_scoped_diff_by_relationship_scope": (
        "should_skip_oig_scoped_diff_by_relationship_scope"
    ),
    "_strip_volatile_source_reference_attrs_from_oig": (
        "strip_volatile_source_reference_attrs_from_oig"
    ),
    "_write_post_oig_diff_index_sidecar": "write_post_oig_diff_index_sidecar",
    "_write_pre_oig_diff_index_sidecar": "write_pre_oig_diff_index_sidecar",
}


def __getattr__(name: str) -> object:
    if name in _DELTA_SUPPORT_EXPORTS:
        from aware_meta.graph.config.lane import delta_support as delta_support_module

        export_name = _DELTA_SUPPORT_ALIAS_MAP.get(name, name)
        try:
            return cast(object, delta_support_module.__dict__[export_name])
        except KeyError as exc:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    if name == "build_oig_graph_diff_index":
        from aware_meta.graph.instance.scoped_index import (
            build_oig_graph_diff_index as build_index_impl,
        )

        return build_index_impl
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CandidateScopedRelationship",
    "GraphIdentitySeedError",
    "GraphIdentitySeedPlan",
    "OCGDeltaCommitPlan",
    "OCGSeedPlan",
    "OigFingerprintDiffScope",
    "OcgLaneCommitError",
    "OcgLaneHashContractDriftDetails",
    "OcgLaneHashContractDriftError",
    "OcgLaneHeadPreHashMismatchDetails",
    "OcgLaneHeadPreHashMismatchError",
    "OcgSeedError",
    "SeedTimings",
    "build_ocg_seed_plan",
    "build_oig_graph_diff_index",
    "collect_lane_instance_models",
    "collect_orm_models",
    "commit_ocg_delta_to_lane",
    "compose_ocg_seed_schema_graph",
    "expand_delta_scoped_candidate_ids",
    "ensure_graph_identity_seeded_lane",
    "ensure_ocg_seeded_lane",
    "preview_graph_identity_seed_plan",
    "load_post_oig_diff_index_sidecar",
    "load_pre_oig_from_snapshot_fast_path",
    "maybe_metric",
    "maybe_record_orm_session_metrics",
    "maybe_timed",
    "oig_diff_index_post_sidecar_path",
    "oig_diff_index_sidecar_path",
    "oig_fingerprint_diff_scope",
    "relationship_in_candidate_scope",
    "resolve_ocg_seed_projection_context",
    "resolve_ocg_seed_schema_view",
    "resolve_root_class_instance_snapshot",
    "schema_configs_by_id_from_schema_view",
    "should_skip_oig_scoped_diff_by_relationship_scope",
    "write_post_oig_diff_index_sidecar",
    "write_pre_oig_diff_index_sidecar",
]
