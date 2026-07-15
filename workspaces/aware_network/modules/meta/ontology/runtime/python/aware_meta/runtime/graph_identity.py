"""Meta-owned graph identity resolution helpers."""

from __future__ import annotations

from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_meta.graph.projection.identity import (
    synthesize_object_projection_graph_identity,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphCommitIndex
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)


def resolve_meta_graph_ocgi_opgi(
    *,
    index: MetaGraphCommitIndex,
    projection_hash: str,
) -> tuple[ObjectConfigGraphIdentity | None, ObjectProjectionGraphIdentity | None]:
    """Resolve stable Meta OCGI/OPGI identities for a projection hash."""

    if not projection_hash:
        return None, None

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        return None, None

    ocg = index.ocg
    ocgi = ocg.object_config_graph_identity
    ocg_key = (ocg.fqn_prefix or "").strip() or (ocg.name or "").strip()
    projection_name = (opg.name or "").strip()

    if not ocg_key:
        return ocgi, None

    ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    if ocgi is None or ocgi.id != ocgi_id:
        ocgi = ObjectConfigGraphIdentity(
            id=ocgi_id,
            key=ocg_key,
            label=f"ocg:{ocg_key}",
        )

    if not projection_name or opg.id is None:
        return ocgi, None

    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi.id,
        object_projection_graph_id=opg.id,
    )
    existing_identities = ocgi.object_projection_graph_identities

    for existing in existing_identities:
        if not isinstance(existing, ObjectProjectionGraphIdentity):
            continue
        if existing.object_projection_graph_id != opg.id:
            continue
        existing_ocgi_id = existing.object_config_graph_identity_id
        if existing_ocgi_id == ocgi.id:
            continue
        expected_existing_id = stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=existing_ocgi_id,
            object_projection_graph_id=opg.id,
        )
        if existing.id == expected_existing_id:
            return ocgi, existing

    for existing in existing_identities:
        if isinstance(existing, ObjectProjectionGraphIdentity) and existing.id == opgi_id:
            return ocgi, existing

    opgi = synthesize_object_projection_graph_identity(
        object_config_graph_identity=ocgi,
        object_projection_graph=opg,
    )
    if opgi.id != opgi_id:
        raise RuntimeError(
            "ObjectProjectionGraphIdentity synthesis mismatch: "
            + f"expected={opgi_id} actual={opgi.id}"
        )

    if all(existing.id != opgi.id for existing in existing_identities):
        existing_identities.append(opgi)

    return ocgi, opgi


__all__ = ["resolve_meta_graph_ocgi_opgi"]
