from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta.graph.config.model_bootstrap import get_function_config_owner_key
from aware_meta.graph.config.stable_ids import stable_function_config_attribute_config_id
from aware_meta.handlers.impl.attribute import attribute_config as attribute_config_handler

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def update_config(
    function_config_attribute_config: FunctionConfigAttributeConfig,
    position: int = 0,
    is_identity_key: bool = False,
    identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
) -> None:
    """
    Update mutable function-attribute membership metadata.

    Contract:
    - `function_config_id`, `attribute_config_id`, `name`, and `type` are identity keys and are not
    mutable here.
    - Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.
    - This full-payload update treats position and identity-key membership metadata as current semantic
    truth.
    """

    # --- AWARE: LOGIC START update_config
    if position < 0:
        raise RuntimeError("FunctionConfigAttributeConfig.update_config requires position >= 0")
    if not isinstance(identity_key_origin, FunctionIdentityKeyOrigin):
        identity_key_origin = FunctionIdentityKeyOrigin(str(identity_key_origin))
    function_config_attribute_config.position = position
    function_config_attribute_config.is_identity_key = is_identity_key
    function_config_attribute_config.identity_key_origin = identity_key_origin
    return None
    # --- AWARE: LOGIC END update_config


async def create_class_via_function_config(
    function_config_id: UUID,
    owner_key: str,
    name: str,
    type_class_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
    identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
) -> FunctionConfigAttributeConfig:
    """
    Create deterministic FunctionConfigAttributeConfig association edge for a class attribute.
    """

    # --- AWARE: LOGIC START create_class_via_function_config
    if position < 0:
        raise RuntimeError("FunctionConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    function_config = session.imap_get(FunctionConfig, function_config_id)
    if function_config is None:
        raise RuntimeError(
            "FunctionConfigAttributeConfig requires existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_owner_key = (get_function_config_owner_key(function_config) or "").strip().casefold()
    if function_owner_key and function_owner_key != normalized_owner_key:
        raise RuntimeError(
            "FunctionConfigAttributeConfig owner_key mismatch for existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_name = (function_config.name or "").strip().casefold()
    io_type = str(getattr(type, "value", type) or "").strip().casefold() or FunctionAttributeType.input.value
    io_owner_key = f"{normalized_owner_key}.{function_name}::{io_type}"
    attribute_config = await attribute_config_handler.create_class(
        owner_key=io_owner_key,
        name=normalized_name,
        type_class_config_id=type_class_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
    )
    attribute_config_id = attribute_config.id
    if attribute_config_id is None:
        raise RuntimeError("FunctionConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_function_config_attribute_config_id(
        function_config_id=function_config_id,
        name=normalized_name,
        type=str(getattr(type, "value", type) or ""),
    )
    existing = session.imap_get(FunctionConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing attribute_config_id mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing position mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_type = str(getattr(existing.type, "value", existing.type) or "").strip().casefold()
        requested_type = str(getattr(type, "value", type) or "").strip().casefold()
        if existing_type != requested_type:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing type mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing is_identity_key mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_origin = str(
            getattr(existing.identity_key_origin, "value", existing.identity_key_origin) or ""
        ).strip()
        requested_origin = str(getattr(identity_key_origin, "value", identity_key_origin) or "").strip()
        if existing_origin and requested_origin and existing_origin != requested_origin:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing identity_key_origin mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return FunctionConfigAttributeConfig(
        id=edge_id,
        function_config_id=function_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        name=normalized_name,
        position=position,
        type=type,
        is_identity_key=is_identity_key,
        identity_key_origin=identity_key_origin,
    )
    # --- AWARE: LOGIC END create_class_via_function_config


async def create_enum_via_function_config(
    function_config_id: UUID,
    owner_key: str,
    name: str,
    enum_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
    identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
) -> FunctionConfigAttributeConfig:
    """
    Create deterministic FunctionConfigAttributeConfig association edge for an enum attribute.
    """

    # --- AWARE: LOGIC START create_enum_via_function_config
    if position < 0:
        raise RuntimeError("FunctionConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    function_config = session.imap_get(FunctionConfig, function_config_id)
    if function_config is None:
        raise RuntimeError(
            "FunctionConfigAttributeConfig requires existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_owner_key = (get_function_config_owner_key(function_config) or "").strip().casefold()
    if function_owner_key and function_owner_key != normalized_owner_key:
        raise RuntimeError(
            "FunctionConfigAttributeConfig owner_key mismatch for existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_name = (function_config.name or "").strip().casefold()
    io_type = str(getattr(type, "value", type) or "").strip().casefold() or FunctionAttributeType.input.value
    io_owner_key = f"{normalized_owner_key}.{function_name}::{io_type}"
    attribute_config = await attribute_config_handler.create_enum(
        owner_key=io_owner_key,
        name=normalized_name,
        enum_config_id=enum_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
    )
    attribute_config_id = attribute_config.id
    if attribute_config_id is None:
        raise RuntimeError("FunctionConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_function_config_attribute_config_id(
        function_config_id=function_config_id,
        name=normalized_name,
        type=str(getattr(type, "value", type) or ""),
    )
    existing = session.imap_get(FunctionConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing attribute_config_id mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing position mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_type = str(getattr(existing.type, "value", existing.type) or "").strip().casefold()
        requested_type = str(getattr(type, "value", type) or "").strip().casefold()
        if existing_type != requested_type:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing type mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing is_identity_key mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_origin = str(
            getattr(existing.identity_key_origin, "value", existing.identity_key_origin) or ""
        ).strip()
        requested_origin = str(getattr(identity_key_origin, "value", identity_key_origin) or "").strip()
        if existing_origin and requested_origin and existing_origin != requested_origin:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing identity_key_origin mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return FunctionConfigAttributeConfig(
        id=edge_id,
        function_config_id=function_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        name=normalized_name,
        position=position,
        type=type,
        is_identity_key=is_identity_key,
        identity_key_origin=identity_key_origin,
    )
    # --- AWARE: LOGIC END create_enum_via_function_config


async def create_primitive_via_function_config(
    function_config_id: UUID,
    owner_key: str,
    name: str,
    primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
    identity_key_origin: FunctionIdentityKeyOrigin = FunctionIdentityKeyOrigin.standalone,
) -> FunctionConfigAttributeConfig:
    """
    Create deterministic FunctionConfigAttributeConfig association edge.
    """

    # --- AWARE: LOGIC START create_primitive_via_function_config
    if position < 0:
        raise RuntimeError("FunctionConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("FunctionConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    function_config = session.imap_get(FunctionConfig, function_config_id)
    if function_config is None:
        raise RuntimeError(
            "FunctionConfigAttributeConfig requires existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_owner_key = (get_function_config_owner_key(function_config) or "").strip().casefold()
    if function_owner_key and function_owner_key != normalized_owner_key:
        raise RuntimeError(
            "FunctionConfigAttributeConfig owner_key mismatch for existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )
    function_name = (function_config.name or "").strip().casefold()
    io_type = str(getattr(type, "value", type) or "").strip().casefold() or FunctionAttributeType.input.value
    io_owner_key = f"{normalized_owner_key}.{function_name}::{io_type}"
    attribute_config = await attribute_config_handler.create_primitive(
        owner_key=io_owner_key,
        name=normalized_name,
        primitive_base_type=primitive_base_type,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
    )
    attribute_config_id = attribute_config.id
    if attribute_config_id is None:
        raise RuntimeError("FunctionConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_function_config_attribute_config_id(
        function_config_id=function_config_id,
        name=normalized_name,
        type=str(getattr(type, "value", type) or ""),
    )
    existing = session.imap_get(FunctionConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing attribute_config_id mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing position mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_type = str(getattr(existing.type, "value", existing.type) or "").strip().casefold()
        requested_type = str(getattr(type, "value", type) or "").strip().casefold()
        if existing_type != requested_type:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing type mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing is_identity_key mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        existing_origin = str(
            getattr(existing.identity_key_origin, "value", existing.identity_key_origin) or ""
        ).strip()
        requested_origin = str(getattr(identity_key_origin, "value", identity_key_origin) or "").strip()
        if existing_origin and requested_origin and existing_origin != requested_origin:
            raise RuntimeError(
                "FunctionConfigAttributeConfig existing identity_key_origin mismatch: "
                f"function_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return FunctionConfigAttributeConfig(
        id=edge_id,
        function_config_id=function_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        name=normalized_name,
        position=position,
        type=type,
        is_identity_key=is_identity_key,
        identity_key_origin=identity_key_origin,
    )
    # --- AWARE: LOGIC END create_primitive_via_function_config
