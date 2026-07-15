from __future__ import annotations

from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)

from aware_meta.graph.config.stable_ids import (
    stable_object_projection_graph_identity_id,
)


def synthesize_object_projection_graph_identity(
    *,
    object_config_graph_identity: ObjectConfigGraphIdentity,
    object_projection_graph: ObjectProjectionGraph,
    label: str | None = None,
    is_branchable: bool = False,
) -> ObjectProjectionGraphIdentity:
    """Build the canonical OPGI boundary object from `(OCGI, OPG)` only."""

    ocgi_id = object_config_graph_identity.id
    if not isinstance(ocgi_id, UUID):
        raise ValueError("ObjectProjectionGraphIdentity synthesis requires ObjectConfigGraphIdentity.id")

    opg_id = object_projection_graph.id
    if not isinstance(opg_id, UUID):
        raise ValueError("ObjectProjectionGraphIdentity synthesis requires ObjectProjectionGraph.id")

    projection_name = (object_projection_graph.name or "").strip()
    if not projection_name:
        raise ValueError("ObjectProjectionGraphIdentity synthesis requires ObjectProjectionGraph.name")

    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg_id,
    )
    return ObjectProjectionGraphIdentity(
        id=opgi_id,
        object_projection_graph=object_projection_graph,
        object_projection_graph_id=opg_id,
        projection_name=projection_name,
        label=label or f"opg:{projection_name}",
        is_branchable=is_branchable,
        object_config_graph_identity_id=ocgi_id,
    )
