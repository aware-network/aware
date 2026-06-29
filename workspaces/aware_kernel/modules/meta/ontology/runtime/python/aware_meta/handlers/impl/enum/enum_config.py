from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta.graph.config.model_bootstrap import build_enum_config
from aware_meta.graph.config.stable_ids import stable_enum_config_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def update_config(
    enum_config: EnumConfig, description: str | None = None
) -> None:
    """
    Update mutable EnumConfig metadata.

    Contract:
    - `enum_fqn` and `name` are identity and are not mutable here.
    - EnumOption membership and option metadata changes use explicit
      EnumConfig/EnumOption ontology functions.
    - This full-payload update treats nullable arguments as current
      semantic truth.
    """

    # --- AWARE: LOGIC START update_config
    enum_config.description = description
    return None
    # --- AWARE: LOGIC END update_config


async def create_enum_option(
    enum_config: EnumConfig,
    value: str,
    label: str | None = None,
    description: str | None = None,
    position: int = 0,
) -> EnumOption:
    """
    Materialize one EnumOption under this EnumConfig.
    """

    # --- AWARE: LOGIC START create_enum_option
    enum_config_id = enum_config.id
    if enum_config_id is None:
        raise RuntimeError("EnumConfig.create_enum_option requires enum_config.id")
    if position < 0:
        raise RuntimeError("EnumConfig.create_enum_option requires position >= 0")

    option = await EnumOption.create_via_enum_config(
        enum_config_id=enum_config_id,
        value=value,
        label=label,
        description=description,
        position=position,
    )

    for existing_option in enum_config.enum_options:
        if existing_option.id == option.id:
            return existing_option

    enum_config.enum_options.append(option)
    return option
    # --- AWARE: LOGIC END create_enum_option


async def delete_enum_option(
    enum_config: EnumConfig, value: str, enum_option_id: UUID | None = None
) -> None:
    """
    Remove one EnumOption membership from this EnumConfig.

    Contract:
    - Mutates only enum_options on this EnumConfig.
    - EnumOption identity comes from committed semantic baseline truth when available.
    - Rooted OIG commit reachability owns stale EnumOption deletion after membership removal.
    """

    # --- AWARE: LOGIC START delete_enum_option
    normalized_value = (value or "").strip()
    if not normalized_value:
        raise RuntimeError("EnumConfig.delete_enum_option requires non-empty value")
    normalized_enum_option_id = (
        UUID(str(enum_option_id)) if enum_option_id is not None else None
    )

    retained_options: list[EnumOption] = []
    removed = False
    for option in enum_config.enum_options:
        option_matches_id = (
            normalized_enum_option_id is not None
            and option.id == normalized_enum_option_id
        )
        option_matches_value = False
        if normalized_enum_option_id is None:
            option_matches_value = (option.value or "").strip() == normalized_value
        if option_matches_id or option_matches_value:
            removed = True
            continue
        retained_options.append(option)

    if not removed:
        raise RuntimeError(
            "EnumConfig.delete_enum_option could not find committed option: "
            f"value={normalized_value!r} enum_option_id={normalized_enum_option_id}"
        )

    enum_config.enum_options = retained_options
    return None
    # --- AWARE: LOGIC END delete_enum_option


async def create_via_object_config_graph_node(
    object_config_graph_node_id: UUID,
    enum_fqn: str,
    name: str,
    description: str | None = None,
    values: list[str] = [],
) -> EnumConfig:
    """
    Create deterministic EnumConfig with optional ordered EnumOption values.
    """

    # --- AWARE: LOGIC START create_via_object_config_graph_node
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError(
            "EnumConfig.create_via_object_config_graph_node requires non-empty name"
        )

    normalized_values: list[str] = []
    seen_values: set[str] = set()
    for raw_value in values:
        value_token = (raw_value or "").strip()
        if not value_token:
            raise RuntimeError("EnumConfig.create enum values must be non-empty")
        if value_token in seen_values:
            raise RuntimeError(
                f"EnumConfig.create received duplicate enum value {value_token!r}"
            )
        seen_values.add(value_token)
        normalized_values.append(value_token)

    normalized_enum_fqn = (enum_fqn or "").strip()
    if not normalized_enum_fqn:
        raise RuntimeError(
            "EnumConfig.create_via_object_config_graph_node requires non-empty enum_fqn"
        )

    enum_config_id = stable_enum_config_id(
        object_config_graph_node_id=object_config_graph_node_id,
        enum_fqn=normalized_enum_fqn,
    )
    session = current_handler_session()
    existing = session.imap_get(EnumConfig, enum_config_id)
    if existing is not None:
        existing_name = (existing.name or "").strip()
        if (
            (existing.enum_fqn or "").strip() != normalized_enum_fqn
            or existing_name != normalized_name
            or (existing.description or None) != (description or None)
        ):
            raise RuntimeError(
                "EnumConfig.create_via_object_config_graph_node payload mismatch for existing config: "
                f"enum_config_id={enum_config_id}"
            )
        return existing

    enum_config = build_enum_config(
        enum_config_id=enum_config_id,
        object_config_graph_node_id=object_config_graph_node_id,
        enum_fqn=normalized_enum_fqn,
        name=normalized_name,
        description=description,
    )

    for index, value_token in enumerate(normalized_values):
        option = await EnumOption.create_via_enum_config(
            enum_config_id=enum_config_id,
            value=value_token,
            label=None,
            description=None,
            position=index,
        )
        if all(
            existing_option.id != option.id
            for existing_option in enum_config.enum_options
        ):
            enum_config.enum_options.append(option)

    return enum_config
    # --- AWARE: LOGIC END create_via_object_config_graph_node
