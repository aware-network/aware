from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta.graph.config.stable_ids import stable_attribute_config_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_primitive(
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
) -> AttributeConfig:
    """
    Create deterministic primitive AttributeConfig and materialize descriptor chain.

    Contract:
    - Primitive descriptors are materialized from canonical primitive type semantics.
    - Parent traversal may materialize this standalone primitive, but parent propagation
      must not enter the AttributeConfig stable-id formula.
    """

    # --- AWARE: LOGIC START create_primitive
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("AttributeConfig identity requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("AttributeConfig identity requires non-empty name")
    attribute_config_id = stable_attribute_config_id(
        owner_key=normalized_owner_key,
        name=normalized_name,
    )
    descriptor = await AttributeTypeDescriptor.create_primitive(
        primitive_base_type=primitive_base_type,
    )

    session = current_handler_session()
    existing = session.imap_get(AttributeConfig, attribute_config_id)
    if existing is not None:
        existing_owner_key = (existing.owner_key or "").strip().casefold()
        existing_name = (existing.name or "").strip().casefold()
        if existing_owner_key != normalized_owner_key or existing_name != normalized_name:
            raise RuntimeError(
                "AttributeConfig identity mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        if existing.type_descriptor_id is not None and existing.type_descriptor_id != descriptor.id:
            raise RuntimeError(
                "AttributeConfig descriptor mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        return existing

    return AttributeConfig(
        id=attribute_config_id,
        owner_key=normalized_owner_key,
        name=normalized_name,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    # --- AWARE: LOGIC END create_primitive


async def create_enum(
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
) -> AttributeConfig:
    """
    Create deterministic enum AttributeConfig and materialize descriptor chain.
    """

    # --- AWARE: LOGIC START create_enum
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("AttributeConfig identity requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("AttributeConfig identity requires non-empty name")
    attribute_config_id = stable_attribute_config_id(
        owner_key=normalized_owner_key,
        name=normalized_name,
    )
    session = current_handler_session()
    enum_config = session.imap_get(EnumConfig, enum_config_id)
    if enum_config is None:
        raise RuntimeError(
            "AttributeConfig.create_enum requires existing EnumConfig: " f"enum_config_id={enum_config_id}"
        )
    descriptor = await AttributeTypeDescriptor.create_enum(enum_config_id=enum_config_id)

    existing = session.imap_get(AttributeConfig, attribute_config_id)
    if existing is not None:
        existing_owner_key = (existing.owner_key or "").strip().casefold()
        existing_name = (existing.name or "").strip().casefold()
        if existing_owner_key != normalized_owner_key or existing_name != normalized_name:
            raise RuntimeError(
                "AttributeConfig identity mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        if existing.type_descriptor_id is not None and existing.type_descriptor_id != descriptor.id:
            raise RuntimeError(
                "AttributeConfig descriptor mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        return existing

    return AttributeConfig(
        id=attribute_config_id,
        owner_key=normalized_owner_key,
        name=normalized_name,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    # --- AWARE: LOGIC END create_enum


async def create_class(
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
) -> AttributeConfig:
    """
    Create deterministic class AttributeConfig and materialize descriptor chain.
    """

    # --- AWARE: LOGIC START create_class
    if not isinstance(type_class_config_id, UUID):
        type_class_config_id = UUID(str(type_class_config_id))
    normalized_owner_key = (owner_key or "").strip().casefold()
    normalized_name = (name or "").strip().casefold()
    if not normalized_owner_key:
        raise RuntimeError("AttributeConfig identity requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("AttributeConfig identity requires non-empty name")
    attribute_config_id = stable_attribute_config_id(
        owner_key=normalized_owner_key,
        name=normalized_name,
    )
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, type_class_config_id)
    if class_config is None:
        try:
            class_config = current_handler_index().class_configs_by_id.get(
                type_class_config_id,
            )
        except (AttributeError, RuntimeError):
            class_config = None
    if class_config is None:
        raise RuntimeError(
            "AttributeConfig.create_class requires existing ClassConfig: " f"class_config_id={type_class_config_id}"
        )
    descriptor = await AttributeTypeDescriptor.create_class(class_config_id=type_class_config_id)

    existing = session.imap_get(AttributeConfig, attribute_config_id)
    if existing is not None:
        existing_owner_key = (existing.owner_key or "").strip().casefold()
        existing_name = (existing.name or "").strip().casefold()
        if existing_owner_key != normalized_owner_key or existing_name != normalized_name:
            raise RuntimeError(
                "AttributeConfig identity mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        if existing.type_descriptor_id is not None and existing.type_descriptor_id != descriptor.id:
            raise RuntimeError(
                "AttributeConfig descriptor mismatch for existing attribute config: "
                f"attribute_config_id={attribute_config_id}"
            )
        return existing

    return AttributeConfig(
        id=attribute_config_id,
        owner_key=normalized_owner_key,
        name=normalized_name,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    # --- AWARE: LOGIC END create_class


async def update_primitive(
    attribute_config: AttributeConfig,
    primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    exclude_serialization: bool = False,
) -> None:
    """
    Update the mutable scalar contract for an existing primitive AttributeConfig.

    Contract:
    - `owner_key` and `name` are identity keys and are not mutable here.
    - The descriptor is replaced through ontology runtime semantics, never by raw OIG patching.
    - Owner-edge fields such as position/function I/O type are updated on their edge objects.
    """

    # --- AWARE: LOGIC START update_primitive
    descriptor = await AttributeTypeDescriptor.create_primitive(
        primitive_base_type=primitive_base_type,
    )
    attribute_config.description = description
    attribute_config.default_value = default_value
    attribute_config.is_primary = is_primary
    attribute_config.is_public = is_public
    attribute_config.is_required = is_required
    attribute_config.is_unique = is_unique
    attribute_config.is_virtual = is_virtual
    attribute_config.exclude_serialization = exclude_serialization
    attribute_config.type_descriptor = descriptor
    attribute_config.type_descriptor_id = descriptor.id
    return None
    # --- AWARE: LOGIC END update_primitive


async def update_enum(
    attribute_config: AttributeConfig,
    enum_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    exclude_serialization: bool = False,
) -> None:
    """
    Update the mutable scalar contract for an existing enum AttributeConfig.

    Contract:
    - `owner_key` and `name` are identity keys and are not mutable here.
    - The enum target must already exist as committed ontology truth.
    - Owner-edge fields such as position/function I/O type are updated on their edge objects.
    """

    # --- AWARE: LOGIC START update_enum
    session = current_handler_session()
    enum_config = session.imap_get(EnumConfig, enum_config_id)
    if enum_config is None:
        raise RuntimeError(
            "AttributeConfig.update_enum requires existing EnumConfig: " f"enum_config_id={enum_config_id}"
        )
    descriptor = await AttributeTypeDescriptor.create_enum(enum_config_id=enum_config_id)
    attribute_config.description = description
    attribute_config.default_value = default_value
    attribute_config.is_primary = is_primary
    attribute_config.is_public = is_public
    attribute_config.is_required = is_required
    attribute_config.is_unique = is_unique
    attribute_config.is_virtual = is_virtual
    attribute_config.exclude_serialization = exclude_serialization
    attribute_config.type_descriptor = descriptor
    attribute_config.type_descriptor_id = descriptor.id
    return None
    # --- AWARE: LOGIC END update_enum


async def update_class(
    attribute_config: AttributeConfig,
    type_class_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    exclude_serialization: bool = False,
) -> None:
    """
    Update the mutable scalar contract for an existing class AttributeConfig.

    Contract:
    - `owner_key` and `name` are identity keys and are not mutable here.
    - The class target must already exist as committed ontology truth.
    - Owner-edge fields such as position/function I/O type are updated on their edge objects.
    """

    # --- AWARE: LOGIC START update_class
    if not isinstance(type_class_config_id, UUID):
        type_class_config_id = UUID(str(type_class_config_id))
    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, type_class_config_id)
    if class_config is None:
        try:
            class_config = current_handler_index().class_configs_by_id.get(
                type_class_config_id,
            )
        except (AttributeError, RuntimeError):
            class_config = None
    if class_config is None:
        raise RuntimeError(
            "AttributeConfig.update_class requires existing ClassConfig: " f"class_config_id={type_class_config_id}"
        )
    descriptor = await AttributeTypeDescriptor.create_class(class_config_id=type_class_config_id)
    attribute_config.description = description
    attribute_config.default_value = default_value
    attribute_config.is_primary = is_primary
    attribute_config.is_public = is_public
    attribute_config.is_required = is_required
    attribute_config.is_unique = is_unique
    attribute_config.is_virtual = is_virtual
    attribute_config.exclude_serialization = exclude_serialization
    attribute_config.type_descriptor = descriptor
    attribute_config.type_descriptor_id = descriptor.id
    return None
    # --- AWARE: LOGIC END update_class
