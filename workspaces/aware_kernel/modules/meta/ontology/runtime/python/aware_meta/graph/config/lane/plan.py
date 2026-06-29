from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_orm.models.base_model import BaseORMModel


@dataclass(frozen=True, slots=True)
class OCGSeedPlan:
    seeded: bool
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    root_object_id: UUID
    graph_hash_pre: str
    graph_hash_post: str
    commit_id: UUID
    changes: list[ObjectInstanceGraphChange]
    before_oig: ObjectInstanceGraph
    after_oig: ObjectInstanceGraph
    objects_by_id: dict[UUID, BaseORMModel]


@dataclass(frozen=True, slots=True)
class OCGDeltaCommitPlan:
    committed: bool
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    root_object_id: UUID
    graph_hash_pre: str
    graph_hash_post: str
    commit_id: UUID | None
    delta_node_count: int
    changes: list[ObjectInstanceGraphChange]


@dataclass(frozen=True, slots=True)
class GraphIdentitySeedPlan:
    """Plan/result for deterministic identity seed commits (OCGI/OPGI)."""

    seeded: bool
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    root_object_id: UUID
    commit_id: UUID | None
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
