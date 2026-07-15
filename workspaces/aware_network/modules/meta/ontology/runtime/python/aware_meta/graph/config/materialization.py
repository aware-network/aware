from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
)
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphIdentityMaterializationRecord:
    object_config_graph_identity_id: UUID
    key: str
    label: str


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphIdentityMaterializationResult:
    object_config_graph_identity: ObjectConfigGraphIdentity
    record: ObjectConfigGraphIdentityMaterializationRecord


def materialize_object_config_graph_identity(
    *,
    ocg_fqn_prefix: str,
    ocg_identity_label: str | None = None,
) -> ObjectConfigGraphIdentityMaterializationResult:
    """
    Materialize the OCG identity-plane root for a full OCG build.

    Projection materialization receives this OCGI as input and owns only OPGI
    plus observable identity-plane children.
    """

    ocg_key = (ocg_fqn_prefix or "").strip()
    if not ocg_key:
        raise ValueError("ObjectConfigGraph.fqn_prefix is required to derive OCGI")

    ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    label = ocg_identity_label or f"ocg:{ocg_key}"
    ocgi = ObjectConfigGraphIdentity(
        id=ocgi_id,
        key=ocg_key,
        label=label,
    )
    if "object_projection_graph_identities" in ObjectConfigGraphIdentity.model_fields:
        ocgi.object_projection_graph_identities = []

    return ObjectConfigGraphIdentityMaterializationResult(
        object_config_graph_identity=ocgi,
        record=ObjectConfigGraphIdentityMaterializationRecord(
            object_config_graph_identity_id=ocgi_id,
            key=ocg_key,
            label=label,
        ),
    )


__all__ = [
    "ObjectConfigGraphIdentityMaterializationRecord",
    "ObjectConfigGraphIdentityMaterializationResult",
    "materialize_object_config_graph_identity",
]
