from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.enum.enum_option import EnumOption

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta_ontology.stable_ids import stable_enum_option_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def update_config(
    enum_option: EnumOption,
    label: str | None = None,
    description: str | None = None,
    position: int = 0,
) -> None:
    """
    Update mutable EnumOption metadata.

    Contract:
    - `value` is identity and is not mutable here.
    - Moving an option to another EnumConfig is replacement semantics.
    - This full-payload update treats nullable arguments as current
      semantic truth.
    """

    # --- AWARE: LOGIC START update_config
    if position < 0:
        raise RuntimeError("EnumOption.update_config requires position >= 0")
    enum_option.label = label
    enum_option.description = description
    enum_option.position = position
    return None
    # --- AWARE: LOGIC END update_config


async def create_via_enum_config(
    enum_config_id: UUID, value: str, label: str | None = None, description: str | None = None, position: int = 0
) -> EnumOption:
    """
    Create deterministic EnumOption under one EnumConfig.

    Contract:
    - Parent `EnumConfig` scope is propagated by traversal lowering.
    - Deterministic identity derives from parent scope + `(value)`.
    """

    # --- AWARE: LOGIC START create_via_enum_config
    normalized_value = value.strip()
    if not normalized_value:
        raise RuntimeError("EnumOption.create_via_enum_config requires non-empty value")
    if position < 0:
        raise RuntimeError("EnumOption.create_via_enum_config requires position >= 0")

    enum_option_id = stable_enum_option_id(enum_config_id=enum_config_id, value=normalized_value)
    session = current_handler_session()
    existing = session.imap_get(EnumOption, enum_option_id)
    if existing is not None:
        if (
            existing.enum_config_id != enum_config_id
            or (existing.value or "") != normalized_value
            or existing.position != position
        ):
            raise RuntimeError(
                "EnumOption.create_via_enum_config payload mismatch for existing option: "
                f"enum_option_id={enum_option_id}"
            )
        return existing

    option = EnumOption(
        id=enum_option_id,
        enum_config_id=enum_config_id,
        value=normalized_value,
        label=label,
        description=description,
        position=position,
    )
    return option
    # --- AWARE: LOGIC END create_via_enum_config
