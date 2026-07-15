from __future__ import annotations

from uuid import UUID, uuid5


# Keep deterministic value-tree identity semantics stable while compiler-owned
# formulas are being migrated onto explicit AttributeValue(.aware) constructors.
OIG_STABLE_ID_NAMESPACE = UUID("cba1c7a6-2d8a-4a0f-9a66-7f0c4f7d9d84")


def _position_token(position: int | None) -> str:
    return str(position) if position else ""


def stable_attribute_value_link_id(
    *,
    parent_value_id: UUID,
    role: str,
    position: int | None = None,
    identity_key: str | None = "",
) -> UUID:
    return uuid5(
        OIG_STABLE_ID_NAMESPACE,
        f"oig_value_link:{parent_value_id}:{role}:{_position_token(position)}:{identity_key or ''}",
    )


def stable_attribute_value_id(
    *,
    parent_value_id: UUID,
    role: str,
    position: int | None = None,
    identity_key: str | None = "",
) -> UUID:
    return uuid5(
        OIG_STABLE_ID_NAMESPACE,
        f"oig_value:{parent_value_id}:{role}:{_position_token(position)}:{identity_key or ''}",
    )


__all__ = [
    "stable_attribute_value_id",
    "stable_attribute_value_link_id",
]
