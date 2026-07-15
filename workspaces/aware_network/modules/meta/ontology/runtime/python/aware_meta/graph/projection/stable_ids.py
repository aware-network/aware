"""
Stable IDs for canonical ObjectProjectionGraph (kernel rail).

Contract:
- OPG identity is derived from (object_config_graph_id, name).
- Node/edge identity is derived from OPG id + rule natural keys.
- This module is independent from runtime/deprecated OPG rails.
"""

from __future__ import annotations

from uuid import UUID, uuid5


# Deterministic namespace for kernel OPG entities (constant across workspaces/time).
KERNEL_OPG_STABLE_ID_NAMESPACE = UUID("3d2b8c4a-0a4b-49ae-9f6f-56a0d7d4a8c1")


def _uuid(key: str) -> UUID:
    return uuid5(KERNEL_OPG_STABLE_ID_NAMESPACE, key)


def stable_object_projection_graph_id(
    *, object_config_graph_id: UUID, name: str
) -> UUID:
    return _uuid(f"opg:{object_config_graph_id}:{(name or '').strip()}")


def stable_object_projection_graph_node_id(
    *,
    opg_id: UUID,
    class_config_id: UUID,
    is_root: bool,
    required_for_validity: bool,
    selection: str,
    top_n: int | None,
    selector_condition_id: UUID | None,
    policy_refs: list[str],
) -> UUID:
    policy_key = ",".join(
        sorted({(p or "").strip() for p in (policy_refs or []) if (p or "").strip()})
    )
    return _uuid(
        "opg_node:"
        f"{opg_id}:{class_config_id}:{int(bool(is_root))}:{int(bool(required_for_validity))}:"
        f"{selection}:{top_n or ''}:{selector_condition_id or ''}:{policy_key}"
    )


def stable_object_projection_graph_edge_id(
    *,
    opg_id: UUID,
    class_config_relationship_id: UUID,
    include: str,
    multiplicity: str,
    traversal_direction: str,
    depth_limit: int | None,
    attribute_role: str | None,
    loading_override: str | None,
) -> UUID:
    return _uuid(
        "opg_edge:"
        f"{opg_id}:{class_config_relationship_id}:{include}:{multiplicity}:{traversal_direction}:"
        f"{depth_limit or ''}:{attribute_role or ''}:{loading_override or ''}"
    )


def stable_object_projection_graph_relationship_id(
    *,
    source_opg_id: UUID,
    class_config_relationship_id: UUID,
    target_opg_id: UUID,
) -> UUID:
    """
    Stable identity for ObjectProjectionGraphRelationship (portal) objects.

    Contract:
    - Deterministic across workspaces/time.
    - Derived from (source_opg_id, class_config_relationship_id, target_opg_id).
    """
    return _uuid(
        "opg_rel:" f"{source_opg_id}:{class_config_relationship_id}:{target_opg_id}"
    )


def stable_object_projection_graph_observable_id(
    *,
    object_projection_graph_identity_id: UUID,
    observable_key: str,
) -> UUID:
    """
    Stable identity for ObjectProjectionGraphObservable objects under an
    ObjectProjectionGraphIdentity.

    Contract:
    - Deterministic across workspaces/time.
    - Derived from (object_projection_graph_identity_id, observable_key).
    """
    return _uuid(
        "opg_observable:"
        f"{object_projection_graph_identity_id}:{(observable_key or '').strip()}"
    )
