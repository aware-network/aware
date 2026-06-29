from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta.graph.config.model_bootstrap import get_class_config_fqn
from aware_meta.graph.config.stable_ids import stable_class_config_attribute_config_id
from aware_meta.handlers.impl.attribute import attribute_config as attribute_config_handler

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def update_config(
    class_config_attribute_config: ClassConfigAttributeConfig, position: int = 0, is_identity_key: bool = False
) -> None:
    """
    Update mutable class-attribute membership metadata.

    Contract:
    - `class_config_id` and `attribute_config_id` are identity keys and are not mutable here.
    - Attribute scalar/type descriptor metadata lives on AttributeConfig.update_*.
    - This full-payload update treats position and identity-key membership metadata as current semantic
    truth.
    """

    # --- AWARE: LOGIC START update_config
    if position < 0:
        raise RuntimeError("ClassConfigAttributeConfig.update_config requires position >= 0")
    class_config_attribute_config.position = position
    class_config_attribute_config.is_identity_key = is_identity_key
    return None
    # --- AWARE: LOGIC END update_config


async def create_class_via_class_config(
    class_config_id: UUID,
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
    position: int = 0,
    is_identity_key: bool = False,
) -> ClassConfigAttributeConfig:
    """
    Create deterministic ClassConfigAttributeConfig link for a class attribute.
    """

    # --- AWARE: LOGIC START create_class_via_class_config
    if position < 0:
        raise RuntimeError("ClassConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is not None:
        class_owner_key = (get_class_config_fqn(class_config) or "").strip().casefold()
        if class_owner_key and class_owner_key != normalized_owner_key:
            raise RuntimeError(
                "ClassConfigAttributeConfig owner_key mismatch for existing ClassConfig: "
                f"class_config_id={class_config_id}"
            )
    attribute_config = await attribute_config_handler.create_class(
        owner_key=normalized_owner_key,
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
        raise RuntimeError("ClassConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_class_config_attribute_config_id(
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(ClassConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing attribute_config_id mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing position mismatch: " f"class_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing is_identity_key mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return ClassConfigAttributeConfig(
        id=edge_id,
        class_config_id=class_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        position=position,
        is_identity_key=is_identity_key,
    )
    # --- AWARE: LOGIC END create_class_via_class_config


async def create_enum_via_class_config(
    class_config_id: UUID,
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
    position: int = 0,
    is_identity_key: bool = False,
) -> ClassConfigAttributeConfig:
    """
    Create deterministic ClassConfigAttributeConfig link for an enum attribute.
    """

    # --- AWARE: LOGIC START create_enum_via_class_config
    if position < 0:
        raise RuntimeError("ClassConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is not None:
        class_owner_key = (get_class_config_fqn(class_config) or "").strip().casefold()
        if class_owner_key and class_owner_key != normalized_owner_key:
            raise RuntimeError(
                "ClassConfigAttributeConfig owner_key mismatch for existing ClassConfig: "
                f"class_config_id={class_config_id}"
            )
    attribute_config = await attribute_config_handler.create_enum(
        owner_key=normalized_owner_key,
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
        raise RuntimeError("ClassConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_class_config_attribute_config_id(
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(ClassConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing attribute_config_id mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing position mismatch: " f"class_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing is_identity_key mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return ClassConfigAttributeConfig(
        id=edge_id,
        class_config_id=class_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        position=position,
        is_identity_key=is_identity_key,
    )
    # --- AWARE: LOGIC END create_enum_via_class_config


async def create_primitive_via_class_config(
    class_config_id: UUID,
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
    position: int = 0,
    is_identity_key: bool = False,
) -> ClassConfigAttributeConfig:
    """
    Create deterministic ClassConfigAttributeConfig link.

    Contract:
    - Parent `ClassConfig` scope is propagated by traversal lowering.
    - AttributeConfig is ensured via semantic standalone keys derived from the parent class context.
    - Deterministic edge identity derives from parent scope + `attribute_config_id`.
    """

    # --- AWARE: LOGIC START create_primitive_via_class_config
    if position < 0:
        raise RuntimeError("ClassConfigAttributeConfig position must be >= 0")
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("ClassConfigAttributeConfig requires non-empty name")
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is not None:
        class_owner_key = (get_class_config_fqn(class_config) or "").strip().casefold()
        if class_owner_key and class_owner_key != normalized_owner_key:
            raise RuntimeError(
                "ClassConfigAttributeConfig owner_key mismatch for existing ClassConfig: "
                f"class_config_id={class_config_id}"
            )
    attribute_config = await attribute_config_handler.create_primitive(
        owner_key=normalized_owner_key,
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
        raise RuntimeError("ClassConfigAttributeConfig requires attribute_config.id")
    edge_id = stable_class_config_attribute_config_id(
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(ClassConfigAttributeConfig, edge_id)
    if existing is not None:
        if existing.attribute_config_id not in (None, attribute_config_id):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing attribute_config_id mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if int(existing.position) != int(position):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing position mismatch: " f"class_config_attribute_config_id={edge_id}"
            )
        if bool(existing.is_identity_key) != bool(is_identity_key):
            raise RuntimeError(
                "ClassConfigAttributeConfig existing is_identity_key mismatch: "
                f"class_config_attribute_config_id={edge_id}"
            )
        if existing.attribute_config is None:
            existing.attribute_config = attribute_config
            existing.attribute_config_id = attribute_config_id
        return existing
    return ClassConfigAttributeConfig(
        id=edge_id,
        class_config_id=class_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config_id,
        position=position,
        is_identity_key=is_identity_key,
    )
    # --- AWARE: LOGIC END create_primitive_via_class_config
