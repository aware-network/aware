import json
from typing import cast

# Kernel Graph Ontology
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind

# Code Runtime
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter

# Meta
from aware_meta.attribute.config.type_descriptor_builder import (
    build_type_descriptor,
    from_primitive_type,
)
from aware_meta.fqn_resolver import FqnScope
from aware_meta.graph.config.stable_ids import stable_attribute_config_id


_DEFAULT_VALUE_UNSET = object()


def build_attribute_config_from_primitive_type(
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    primitive_type: CodePrimitiveType,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    name: str,
    description: str | None = None,
    default_value: str | None = None,
    is_required: bool = False,
    is_unique: bool = False,
    is_primary: bool = False,
    is_public: bool = True,
    is_virtual: bool = False,
    owner_key: str | None = None,
) -> AttributeConfig:
    """
    Create an AttributeConfig from a primitive type.

    Args:
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        primitive_type: The primitive type to convert
        type_descriptor_adapter: Type descriptor adapter
        name: The name of the attribute
        description: The description of the attribute
        default_value: The default value of the attribute
        is_required: Whether the attribute is required
        is_unique: Whether the attribute is unique
        is_primary: Whether the attribute is primary
        is_public: Whether the attribute is public
        is_virtual: Whether the attribute is virtual
    Returns:
        An AttributeConfig instance
    """
    type_descriptor = from_primitive_type(type_descriptor_adapter, primitive_codec, fqn_scope, primitive_type)
    # Create the attribute config
    payload = {
        "name": name,
        "description": description,
        "default_value": default_value,
        "is_required": is_required,
        "is_unique": is_unique,
        "is_primary": is_primary,
        "is_public": is_public,
        "is_virtual": is_virtual,
        "type_descriptor": type_descriptor,
        "type_descriptor_id": type_descriptor.id,
    }
    if owner_key is not None:
        payload["id"] = stable_attribute_config_id(owner_key=owner_key, name=name)
        payload["owner_key"] = owner_key
    return AttributeConfig.model_validate(payload)


def build_attribute_config_from_code(
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    code_section_attribute: CodeSectionAttribute,
    is_virtual: bool = False,
    owner_key: str | None = None,
) -> AttributeConfig:
    """
    Create an AttributeConfig from a CodeSectionAttribute.

    Args:
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        code_section_attribute: The CodeSectionAttribute to convert
        is_virtual: Whether the attribute is virtual
    Returns:
        An AttributeConfig instance
    """
    # Get type from code section attribute
    if code_section_attribute.type_text:
        type_text = code_section_attribute.type_text
    else:
        type_any = primitive_codec.any()
        type_text = primitive_codec.render(type_any)
        if type_text is None:
            raise ValueError(f"No type found for {code_section_attribute.name}")

    # Build hierarchical type descriptor via language plugin adapter
    type_descriptor = build_type_descriptor(
        type_descriptor_adapter=type_descriptor_adapter,
        primitive_codec=primitive_codec,
        fqn_scope=fqn_scope,
        type_text=type_text,
    )

    # Parse the default value after type resolution so enum-backed defaults can preserve
    # their authored option token instead of collapsing bare `none` to null.
    default_value: str | None = None
    default_value_text = code_section_attribute.default_value_text
    if default_value_text:
        default_value = _serialize_default_value(
            default_value_text=default_value_text,
            type_descriptor=type_descriptor,
            primitive_codec=primitive_codec,
        )

    # Create the attribute config
    payload = {
        "name": code_section_attribute.name,
        "description": code_section_attribute.description,
        "default_value": default_value,
        "is_required": code_section_attribute.is_required,
        "is_unique": code_section_attribute.is_unique,
        "is_primary": code_section_attribute.is_primary,
        "is_public": code_section_attribute.is_public,
        "is_virtual": is_virtual,
        "type_descriptor": type_descriptor,
        "type_descriptor_id": type_descriptor.id,
        "code_section_attribute_id": code_section_attribute.id,
        "code_section_attribute": code_section_attribute,
    }
    if owner_key is not None:
        payload["id"] = stable_attribute_config_id(owner_key=owner_key, name=code_section_attribute.name)
        payload["owner_key"] = owner_key
    attribute_config = AttributeConfig.model_validate(payload)
    return attribute_config


def _serialize_default_value(
    *,
    default_value_text: str,
    type_descriptor: AttributeTypeDescriptor,
    primitive_codec: CodePrimitiveCodec,
) -> str:
    parsed_value = _parse_descriptor_aware_default(
        default_value_text=default_value_text,
        type_descriptor=type_descriptor,
        primitive_codec=primitive_codec,
    )
    if parsed_value is _DEFAULT_VALUE_UNSET:
        parsed_value = primitive_codec.parse_literal(default_value_text)
    return json.dumps(parsed_value)


def _parse_descriptor_aware_default(
    *,
    default_value_text: str,
    type_descriptor: AttributeTypeDescriptor,
    primitive_codec: CodePrimitiveCodec,
) -> object:
    text = default_value_text.strip()
    if type_descriptor.kind == AttributeTypeDescriptorKind.enum:
        return _parse_scalar_enum_default(text=text, primitive_codec=primitive_codec)

    if type_descriptor.kind == AttributeTypeDescriptorKind.collection:
        child = _first_child_descriptor(type_descriptor)
        if child is not None and child.kind == AttributeTypeDescriptorKind.enum:
            return _parse_enum_collection_default(text=text, primitive_codec=primitive_codec)
        return _DEFAULT_VALUE_UNSET

    if type_descriptor.kind == AttributeTypeDescriptorKind.union:
        if _is_null_default_literal(text):
            return None
        non_null_members = [child for child in _child_descriptors(type_descriptor) if not _is_null_descriptor(child)]
        if len(non_null_members) == 1:
            return _parse_descriptor_aware_default(
                default_value_text=text,
                type_descriptor=non_null_members[0],
                primitive_codec=primitive_codec,
            )

    return _DEFAULT_VALUE_UNSET


def _parse_scalar_enum_default(*, text: str, primitive_codec: CodePrimitiveCodec) -> object:
    if _is_null_default_literal(text):
        return None
    if _is_quoted_literal(text):
        return primitive_codec.parse_literal(text)
    return _normalize_enum_token(text)


def _parse_enum_collection_default(*, text: str, primitive_codec: CodePrimitiveCodec) -> object:
    if _is_null_default_literal(text):
        return None
    if not (text.startswith("[") and text.endswith("]")):
        return _DEFAULT_VALUE_UNSET

    parsed_value = None
    try:
        parsed_value = primitive_codec.parse_literal(text)
    except Exception:
        parsed_value = None

    if isinstance(parsed_value, list):
        parsed_items = cast(list[object], parsed_value)
        return [
            None if item is None else _normalize_enum_token(str(item))
            for item in parsed_items
        ]

    inner = text[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar_enum_default(text=part.strip(), primitive_codec=primitive_codec) for part in inner.split(",")]


def _normalize_enum_token(text: str) -> str:
    token = text.split("::", 1)[0].strip()
    if "." in token and all(ch not in token for ch in " []{}(),\"'"):
        token = token.rsplit(".", 1)[-1]
    return token


def _is_quoted_literal(text: str) -> bool:
    return (
        len(text) >= 2
        and text[0] == text[-1]
        and text[0] in {"'", '"'}
    )


def _is_null_default_literal(text: str) -> bool:
    return text in {"null", "NULL", "None"}


def _first_child_descriptor(type_descriptor: AttributeTypeDescriptor) -> AttributeTypeDescriptor | None:
    children = _child_descriptors(type_descriptor)
    if not children:
        return None
    return children[0]


def _child_descriptors(type_descriptor: AttributeTypeDescriptor) -> list[AttributeTypeDescriptor]:
    return [link.child for link in type_descriptor.child_links]


def _is_null_descriptor(type_descriptor: AttributeTypeDescriptor) -> bool:
    if type_descriptor.kind != AttributeTypeDescriptorKind.primitive or type_descriptor.primitive_config is None:
        return False
    primitive_type = CodePrimitiveType.model_validate(type_descriptor.primitive_config.primitive_type)
    return primitive_type.base_type == CodePrimitiveBaseType.null
