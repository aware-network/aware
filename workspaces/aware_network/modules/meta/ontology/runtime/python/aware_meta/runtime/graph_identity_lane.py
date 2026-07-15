from __future__ import annotations

from uuid import UUID

from aware_meta.runtime.commit.identity_history import (
    upsert_object_instance_graph_identity_history_from_domain_commit,
)
from aware_meta.runtime.commit.identity_lane import (
    ObjectInstanceGraphIdentityLaneContext,
    ensure_object_instance_graph_identity_lane_head,
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


async def register_domain_commit_in_graph_identity_lane(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit,
    source_class_instance_identity_id: UUID | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_graph_identity_lane",
    projector_mode: str = "handler",
) -> UUID:
    """Register a domain commit in the Meta graph identity lane."""

    return await upsert_object_instance_graph_identity_history_from_domain_commit(
        index=index,
        actor_id=actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit=domain_commit,
        source_class_instance_identity_id=source_class_instance_identity_id,
        perf_ms=perf_ms,
        perf_metric_prefix=perf_metric_prefix,
        projector_mode=projector_mode,
    )


async def advance_graph_identity_lane_head_from_domain_commit(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit,
    source_class_instance_identity_id: UUID | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_graph_identity_lane_head",
    projector_mode: str = "handler",
) -> UUID:
    """Advance Meta graph identity lane head truth for a domain commit."""

    return await register_domain_commit_in_graph_identity_lane(
        index=index,
        actor_id=actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit=domain_commit,
        source_class_instance_identity_id=source_class_instance_identity_id,
        perf_ms=perf_ms,
        perf_metric_prefix=perf_metric_prefix,
        projector_mode=projector_mode,
    )


__all__ = [
    "ObjectInstanceGraphIdentityLaneContext",
    "advance_graph_identity_lane_head_from_domain_commit",
    "ensure_object_instance_graph_identity_lane_head",
    "register_domain_commit_in_graph_identity_lane",
    "resolve_object_instance_graph_identity_lane_context",
    "upsert_object_instance_graph_identity_history_from_domain_commit",
]
