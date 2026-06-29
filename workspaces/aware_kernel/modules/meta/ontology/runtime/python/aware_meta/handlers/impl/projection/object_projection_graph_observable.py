from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_observable import ObjectProjectionGraphObservable

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_observable_id,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_object_projection_graph_identity(
    object_projection_graph_identity_id: UUID,
    observable_key: str,
    key: str,
    kind: str | None = None,
    label: str | None = None,
    description: str | None = None,
    position: int | None = None,
    is_default: bool = False,
) -> ObjectProjectionGraphObservable:
    """
    Creates a new ObjectProjectionGraphObservable.

    Contract:
    - Parent `ObjectProjectionGraphIdentity` scope is propagated by traversal lowering.
    - Deterministic identity derives from parent scope + `(observable_key)`.
    - `key` is the caller-materialized canonical projection key.
    """

    # --- AWARE: LOGIC START create_via_object_projection_graph_identity
    observable_key_norm = (observable_key or "").strip()
    if not observable_key_norm:
        raise ValueError("ObjectProjectionGraphIdentity.create_observable requires observable_key")

    kind_norm: str | None = None
    if kind is not None:
        kind_norm = (kind or "").strip().lower() or None
        if kind_norm is not None and kind_norm not in {"construct", "instance"}:
            raise ValueError(
                "ObjectProjectionGraphIdentity.create_observable requires kind "
                f"(one of {{'construct','instance'}}), {kind!r}"
            )

    session = current_handler_session()
    parent = session.imap_get(ObjectProjectionGraphIdentity, object_projection_graph_identity_id)
    if parent is None:
        raise RuntimeError(
            "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity requires existing "
            f"ObjectProjectionGraphIdentity: object_projection_graph_identity_id={object_projection_graph_identity_id}"
        )

    projection_name = (parent.projection_name or "").strip()
    if not projection_name:
        raise RuntimeError(
            "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity "
            "requires parent projection_name: "
            f"object_projection_graph_identity_id={object_projection_graph_identity_id}"
        )

    observable_id = stable_object_projection_graph_observable_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        observable_key=observable_key_norm,
    )
    computed_key = f"{projection_name}:{observable_key_norm}"
    key_norm = (key or "").strip()
    if not key_norm:
        raise ValueError("ObjectProjectionGraphIdentity.create_observable requires key")
    if key_norm != computed_key:
        raise ValueError(
            "ObjectProjectionGraphIdentity.create_observable key mismatch: "
            f"have_key={key!r} expected_key={computed_key!r}"
        )

    # Idempotency: `ObjectProjectionGraphIdentity.create_observable` may be called
    # multiple times for the same observable key.
    existing = session.imap_get(ObjectProjectionGraphObservable, observable_id)
    if existing is not None:
        if existing.object_projection_graph_identity_id != object_projection_graph_identity_id:
            raise RuntimeError(
                "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity identity mismatch: "
                f"observable_id={observable_id} have_opgi_id={existing.object_projection_graph_identity_id} "
                f"expected_opgi_id={object_projection_graph_identity_id}"
            )
        existing_observable_key = (
            getattr(existing, "observable_key", None) or getattr(existing, "view_key", None) or ""
        ).strip()
        if existing_observable_key != observable_key_norm:
            raise RuntimeError(
                "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity observable_key "
                f"mismatch: observable_id={observable_id} have_observable_key={existing_observable_key!r} "
                f"expected_observable_key={observable_key_norm!r}"
            )
        if (existing.key or "").strip() != computed_key:
            raise RuntimeError(
                "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity key mismatch: "
                f"observable_id={observable_id} have_key={existing.key!r} expected_key={computed_key!r}"
            )
        if kind_norm is not None:
            existing_kind = (existing.kind or "").strip().lower() or None
            if existing_kind is None:
                existing.kind = kind_norm
            elif existing_kind != kind_norm:
                raise RuntimeError(
                    "ObjectProjectionGraphObservable.create_via_object_projection_graph_identity kind mismatch: "
                    f"observable_id={observable_id} have_kind={existing.kind!r} expected_kind={kind_norm!r}"
                )
        return existing
    return ObjectProjectionGraphObservable(
        id=observable_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        key=key_norm,
        observable_key=observable_key_norm,
        kind=kind_norm,
        label=label,
        description=description,
        position=position,
        is_default=is_default,
    )
    # --- AWARE: LOGIC END create_via_object_projection_graph_identity
