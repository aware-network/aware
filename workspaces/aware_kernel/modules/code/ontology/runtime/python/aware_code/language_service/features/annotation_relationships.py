from __future__ import annotations

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.fqn_resolver import FqnScope
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode


def collect_structural_relationship_keys(
    *,
    class_cfg: ClassConfig,
    scope: FqnScope | None = None,
    workspace_language: CodeLanguage | None = None,
) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()

    for relationship in class_cfg.class_config_relationships:
        key = relationship.relationship_key.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    if keys:
        return keys

    if class_cfg.value_mode != ClassValueMode.graph_ref:
        return keys

    attribute_configs = _typed_attribute_configs(class_cfg=class_cfg)
    if attribute_configs:
        for attr_cfg in attribute_configs:
            if attr_cfg.is_virtual or not attr_cfg.is_public:
                continue
            key = attr_cfg.name.strip()
            if not key or key in seen:
                continue
            if not _descriptor_defines_graph_relationship(descriptor=attr_cfg.type_descriptor):
                continue
            seen.add(key)
            keys.append(key)
        return keys

    if scope is None or workspace_language is None or class_cfg.code_section_class is None:
        return keys

    for attr in class_cfg.code_section_class.code_section_attributes:
        if not attr.is_public:
            continue
        key = attr.name.strip()
        if not key or key in seen:
            continue
        if not _code_attribute_defines_graph_relationship(
            attribute=attr,
            scope=scope,
            workspace_language=workspace_language,
        ):
            continue
        seen.add(key)
        keys.append(key)

    return keys


def _typed_attribute_configs(*, class_cfg: ClassConfig) -> list[AttributeConfig]:
    return [
        class_attr_cfg.attribute_config
        for class_attr_cfg in class_cfg.class_config_attribute_configs
        if class_attr_cfg.attribute_config is not None
    ]


def _descriptor_defines_graph_relationship(*, descriptor: AttributeTypeDescriptor) -> bool:
    modes = _descriptor_leaf_class_value_modes(descriptor=descriptor)
    if not modes:
        return False
    if ClassValueMode.graph_ref in modes and ClassValueMode.inline_value in modes:
        return False
    return ClassValueMode.graph_ref in modes


def _descriptor_leaf_class_value_modes(*, descriptor: AttributeTypeDescriptor) -> set[ClassValueMode]:
    modes: set[ClassValueMode] = set()
    stack: list[AttributeTypeDescriptor] = [descriptor]
    while stack:
        current = stack.pop()
        if current.kind == AttributeTypeDescriptorKind.class_:
            if current.class_config is not None:
                modes.add(current.class_config.value_mode)
            continue
        for child_link in reversed(current.child_links):
            stack.append(child_link.child)
    return modes


def _code_attribute_defines_graph_relationship(
    *,
    attribute: CodeSectionAttribute,
    scope: FqnScope,
    workspace_language: CodeLanguage,
) -> bool:
    try:
        plugin = CodeLanguagePluginRegistry.get(workspace_language)
    except Exception:
        return False

    type_text = attribute.type_text or _fallback_type_text(workspace_language=workspace_language)
    try:
        node = plugin.type_descriptor_adapter.parse_type(type_text)
    except Exception:
        return False

    modes = _type_node_leaf_class_value_modes(node=node, scope=scope)
    if not modes:
        return False
    if ClassValueMode.graph_ref in modes and ClassValueMode.inline_value in modes:
        return False
    return ClassValueMode.graph_ref in modes


def _type_node_leaf_class_value_modes(*, node: TypeNode, scope: FqnScope) -> set[ClassValueMode]:
    modes: set[ClassValueMode] = set()
    stack: list[TypeNode] = [node]
    while stack:
        current = stack.pop()
        if current.kind == TypeNodeKind.IDENT:
            if current.text is None:
                continue
            if scope.try_resolve_enum(current.text) is not None:
                continue
            class_cfg = scope.try_resolve_class(current.text)
            if class_cfg is not None:
                modes.add(class_cfg.value_mode)
            continue
        if current.kind == TypeNodeKind.COLLECTION and current.element is not None:
            stack.append(current.element)
            continue
        if current.kind == TypeNodeKind.MAPPING:
            if current.key is not None:
                stack.append(current.key)
            if current.value is not None:
                stack.append(current.value)
            continue
        if current.kind == TypeNodeKind.TUPLE:
            stack.extend(reversed(current.elements))
            continue
        if current.kind == TypeNodeKind.UNION:
            stack.extend(reversed(current.members))
            continue
    return modes


def _fallback_type_text(*, workspace_language: CodeLanguage) -> str:
    if workspace_language == CodeLanguage.aware:
        return "Any"
    return "Any"
