from __future__ import annotations

from uuid import UUID

from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)

from aware_meta.graph.config.stable_ids import (
    stable_object_instance_graph_identity_id,
)


def synthesize_object_instance_graph_identity(
    *,
    object_projection_graph_identity: ObjectProjectionGraphIdentity,
    object_instance_graph: ObjectInstanceGraph,
    label: str | None = None,
) -> ObjectInstanceGraphIdentity:
    """Build the canonical OIGI boundary object from `(OPGI, OIG)` only."""

    opgi_id = object_projection_graph_identity.id
    if not isinstance(opgi_id, UUID):
        raise ValueError("ObjectInstanceGraphIdentity synthesis requires ObjectProjectionGraphIdentity.id")

    oig_id = object_instance_graph.id
    if not isinstance(oig_id, UUID):
        raise ValueError("ObjectInstanceGraphIdentity synthesis requires ObjectInstanceGraph.id")

    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=oig_id,
    )
    return ObjectInstanceGraphIdentity(
        id=oigi_id,
        label=label or f"oig:{oig_id.hex[:8]}",
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph=object_instance_graph,
        object_instance_graph_id=oig_id,
    )
