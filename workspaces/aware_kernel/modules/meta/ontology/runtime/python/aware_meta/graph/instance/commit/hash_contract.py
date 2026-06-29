from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_meta.graph.config.lane.delta_support import strip_volatile_source_reference_attrs_from_oig
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index


@dataclass(frozen=True, slots=True)
class OigLaneHashState:
    raw_hash: str
    lane_hash: str
    volatile_source_reference_attrs_removed: int

    def accepted_hashes(self) -> tuple[str, ...]:
        if self.lane_hash == self.raw_hash:
            return (self.raw_hash,)
        return (self.raw_hash, self.lane_hash)

    def matches(self, expected_hash: str | None) -> bool:
        if not expected_hash:
            return False
        return expected_hash in self.accepted_hashes()

    def matched_hash_or_default(self, expected_hash: str | None) -> str:
        if expected_hash and self.matches(expected_hash):
            return expected_hash
        return self.lane_hash


def compute_oig_lane_hash_state(
    *,
    graph: ObjectInstanceGraph,
    schema_attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None,
    expected_hash: str | None = None,
) -> OigLaneHashState:
    raw_hash = compute_hash(graph, index=build_index(graph))
    if expected_hash and expected_hash == raw_hash:
        return OigLaneHashState(
            raw_hash=raw_hash,
            lane_hash=raw_hash,
            volatile_source_reference_attrs_removed=0,
        )

    if not schema_attribute_configs_by_id:
        return OigLaneHashState(
            raw_hash=raw_hash,
            lane_hash=raw_hash,
            volatile_source_reference_attrs_removed=0,
        )

    normalized_graph = graph.model_copy(deep=True)
    removed = strip_volatile_source_reference_attrs_from_oig(
        graph=normalized_graph,
        schema_attribute_configs_by_id=dict(schema_attribute_configs_by_id),
    )
    if removed == 0:
        return OigLaneHashState(
            raw_hash=raw_hash,
            lane_hash=raw_hash,
            volatile_source_reference_attrs_removed=0,
        )

    lane_hash = compute_hash(normalized_graph, index=build_index(normalized_graph))
    return OigLaneHashState(
        raw_hash=raw_hash,
        lane_hash=lane_hash,
        volatile_source_reference_attrs_removed=removed,
    )


__all__ = [
    "OigLaneHashState",
    "compute_oig_lane_hash_state",
]
