from __future__ import annotations

from typing import Dict, Tuple
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)

_plane_cache: Dict[Tuple[UUID, UUID], UUID] = {}


async def get_or_create_plane_oigb(
    underlying_branch_id: UUID, opg: ObjectProjectionGraph, ocg: ObjectConfigGraph
) -> ObjectInstanceGraphBranch:
    key = (underlying_branch_id, opg.id)

    # Cache
    cached = _plane_cache.get(key)
    if cached:
        existing = await ObjectInstanceGraphBranch.get_by_id(cached)
        if existing is not None:
            return existing

    # Try to find existing holder for this branch+opg
    try:
        candidate = await ObjectInstanceGraphBranch.get(field_name="branch_id", field_value=underlying_branch_id)
        if candidate and candidate.object_instance_graph_id:
            oig = await ObjectInstanceGraph.get_by_id(candidate.object_instance_graph_id)
            if oig and getattr(oig, "object_projection_graph_id", None) == opg.id:
                _plane_cache[key] = candidate.id
                return candidate
    except Exception:
        pass

    raise RuntimeError(
        "Plane holder creation requires a rooted ObjectInstanceGraph seed. "
        + "Rootless OIG placeholders are no longer allowed."
    )
