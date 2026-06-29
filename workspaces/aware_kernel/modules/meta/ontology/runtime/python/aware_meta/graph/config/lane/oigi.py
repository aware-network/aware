from __future__ import annotations

from uuid import UUID

from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_instance_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


def resolve_ocg_lane_object_instance_graph_identity_id(
    *,
    identity_graph: ObjectConfigGraph,
    object_projection_graph: ObjectProjectionGraph,
    object_instance_graph_id: UUID,
) -> UUID:
    """Resolve canonical OIGI id for an OCG lane commit.

    OCG semantic lanes use the semantic OCG id as the domain OIG id. The
    identity id must still be derived from the graph that owns the lane OPG
    identity, not from the semantic OCG snapshot and never from the OIG id
    itself.
    """
    ocg_key = (identity_graph.fqn_prefix or "").strip() or (identity_graph.name or "").strip()
    ocgi = identity_graph.object_config_graph_identity
    if ocg_key:
        ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    else:
        if ocgi is None:
            raise ValueError("Cannot resolve OCG lane OIGI without OCGI or OCG key")
        ocgi_id = ocgi.id

    if ocgi is not None:
        source_opgi_id = _resolve_source_projection_identity_id(
            object_config_graph_identity=ocgi,
            container_object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=object_projection_graph.id,
        )
        if source_opgi_id is not None:
            return stable_object_instance_graph_identity_id(
                object_projection_graph_identity_id=source_opgi_id,
                object_instance_graph_id=object_instance_graph_id,
            )

    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=object_projection_graph.id,
    )
    return stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=object_instance_graph_id,
    )


def _resolve_source_projection_identity_id(
    *,
    object_config_graph_identity: object,
    container_object_config_graph_identity_id: UUID,
    object_projection_graph_id: UUID,
) -> UUID | None:
    identities = getattr(object_config_graph_identity, "object_projection_graph_identities", []) or []
    container_opgi_id: UUID | None = None
    for identity in identities:
        if getattr(identity, "object_projection_graph_id", None) != object_projection_graph_id:
            continue
        identity_ocgi_id = getattr(identity, "object_config_graph_identity_id", None)
        identity_id = getattr(identity, "id", None)
        if not isinstance(identity_ocgi_id, UUID) or not isinstance(identity_id, UUID):
            continue
        expected_identity_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=identity_ocgi_id,
            object_projection_graph_id=object_projection_graph_id,
        )
        if identity_id != expected_identity_id:
            continue
        if identity_ocgi_id == container_object_config_graph_identity_id:
            container_opgi_id = identity_id
            continue
        return identity_id
    return container_opgi_id


__all__ = ["resolve_ocg_lane_object_instance_graph_identity_id"]
