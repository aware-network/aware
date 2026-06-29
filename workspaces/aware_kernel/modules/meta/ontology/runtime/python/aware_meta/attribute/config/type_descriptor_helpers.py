from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.class_.class_config import ClassConfig

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType


@dataclass(frozen=True)
class AttributeTypeInfo:
    """Resolved typing information derived from the descriptor tree."""

    kind: AttributeTypeDescriptorKind
    primitive_config: PrimitiveConfig | None
    enum_config: EnumConfig | None
    class_config: ClassConfig | None
    collection_kind: AttributeCollectionType | None
    nullable: bool = False

    @property
    def is_collection(self) -> bool:
        return self.collection_kind is not None and self.collection_kind != AttributeCollectionType.single


def resolve_type_info(attribute_config: AttributeConfig) -> AttributeTypeInfo:
    """Resolve AttributeConfig typing from its descriptor tree."""
    return walk_descriptor(attribute_config.type_descriptor)


def resolve_type_class_config_id(attribute_config: AttributeConfig) -> UUID | None:
    """Resolve the canonical ClassConfig id from the descriptor tree, even if FK relations are unloaded."""
    return walk_descriptor_class_config_id(attribute_config.type_descriptor)


def walk_descriptor(node: AttributeTypeDescriptor, _seen: set[UUID] | None = None) -> AttributeTypeInfo:
    """Traverse descriptor tree to the base leaf and capture collection info."""
    seen = _seen if _seen is not None else set()
    if node.id in seen:
        return _structural_type_info(node)
    seen.add(node.id)
    try:
        return _walk_descriptor_inner(node, seen)
    finally:
        seen.remove(node.id)


def _walk_descriptor_inner(node: AttributeTypeDescriptor, seen: set[UUID]) -> AttributeTypeInfo:
    if node.kind == AttributeTypeDescriptorKind.collection:
        child = pick_child(node.child_links)
        child_info = walk_descriptor(child.child, seen)
        return AttributeTypeInfo(
            kind=child_info.kind,
            primitive_config=child_info.primitive_config,
            enum_config=child_info.enum_config,
            class_config=child_info.class_config,
            collection_kind=node.collection_kind,
            nullable=child_info.nullable,
        )
    if node.kind == AttributeTypeDescriptorKind.primitive:
        return AttributeTypeInfo(
            kind=node.kind,
            primitive_config=node.primitive_config,
            enum_config=None,
            class_config=None,
            collection_kind=node.collection_kind,
            nullable=False,
        )
    if node.kind == AttributeTypeDescriptorKind.enum:
        return AttributeTypeInfo(
            kind=node.kind,
            primitive_config=None,
            enum_config=node.enum_config,
            class_config=None,
            collection_kind=node.collection_kind,
            nullable=False,
        )
    if node.kind == AttributeTypeDescriptorKind.class_:
        return AttributeTypeInfo(
            kind=node.kind,
            primitive_config=None,
            enum_config=None,
            class_config=node.class_config,
            collection_kind=node.collection_kind,
            nullable=False,
        )
    if node.kind == AttributeTypeDescriptorKind.union:
        has_null = False
        candidate: AttributeTypeInfo | None = None
        for link in node.child_links:
            child_info = walk_descriptor(link.child, seen)
            if is_null_descriptor(child_info):
                has_null = True
                continue
            if candidate is None and (child_info.class_config or child_info.enum_config or child_info.primitive_config):
                candidate = child_info
        if candidate is None:
            return AttributeTypeInfo(
                kind=node.kind,
                primitive_config=None,
                enum_config=None,
                class_config=None,
                collection_kind=node.collection_kind,
                nullable=True,
            )
        return AttributeTypeInfo(
            kind=candidate.kind,
            primitive_config=candidate.primitive_config,
            enum_config=candidate.enum_config,
            class_config=candidate.class_config,
            collection_kind=candidate.collection_kind,
            nullable=True if has_null else candidate.nullable,
        )
    if node.kind == AttributeTypeDescriptorKind.tuple:
        for link in sorted(
            node.child_links,
            key=lambda item: item.position or 0,
        ):
            child_info = walk_descriptor(link.child, seen)
            if child_info.class_config or child_info.enum_config or child_info.primitive_config:
                return AttributeTypeInfo(
                    kind=child_info.kind,
                    primitive_config=child_info.primitive_config,
                    enum_config=child_info.enum_config,
                    class_config=child_info.class_config,
                    collection_kind=child_info.collection_kind,
                    nullable=child_info.nullable,
                )
        return AttributeTypeInfo(
            kind=node.kind,
            primitive_config=None,
            enum_config=None,
            class_config=None,
            collection_kind=node.collection_kind,
            nullable=False,
        )
    if node.kind == AttributeTypeDescriptorKind.mapping:
        # Prefer VALUE role, fall back to first child
        value_link = next(
            (link for link in node.child_links if link.role == AttributeTypeDescriptorRole.value_),
            None,
        )
        target = value_link.child if value_link else node.child_links[0].child if node.child_links else None
        if target:
            child_info = walk_descriptor(target, seen)
            return AttributeTypeInfo(
                kind=child_info.kind,
                primitive_config=child_info.primitive_config,
                enum_config=child_info.enum_config,
                class_config=child_info.class_config,
                collection_kind=child_info.collection_kind,
                nullable=child_info.nullable,
            )
        return AttributeTypeInfo(
            kind=node.kind,
            primitive_config=None,
            enum_config=None,
            class_config=None,
            collection_kind=node.collection_kind,
            nullable=False,
        )
    # Unsupported structural kinds fall back to Any
    return AttributeTypeInfo(
        kind=node.kind,
        primitive_config=None,
        enum_config=None,
        class_config=None,
        collection_kind=node.collection_kind,
        nullable=False,
    )


def walk_descriptor_class_config_id(node: AttributeTypeDescriptor, _seen: set[UUID] | None = None) -> UUID | None:
    """Traverse descriptor tree to the first class-typed leaf and return its FK id."""
    seen = _seen if _seen is not None else set()
    if node.id in seen:
        return None
    seen.add(node.id)
    try:
        return _walk_descriptor_class_config_id_inner(node, seen)
    finally:
        seen.remove(node.id)


def _walk_descriptor_class_config_id_inner(node: AttributeTypeDescriptor, seen: set[UUID]) -> UUID | None:
    if node.kind == AttributeTypeDescriptorKind.collection:
        child = pick_child(node.child_links)
        return walk_descriptor_class_config_id(child.child, seen)
    if node.kind == AttributeTypeDescriptorKind.class_:
        if node.class_config is not None:
            return node.class_config.id
        return node.class_config_id
    if node.kind == AttributeTypeDescriptorKind.union:
        for link in node.child_links:
            class_config_id = walk_descriptor_class_config_id(link.child, seen)
            if class_config_id is not None:
                return class_config_id
        return None
    if node.kind == AttributeTypeDescriptorKind.tuple:
        for link in sorted(node.child_links, key=lambda item: item.position or 0):
            class_config_id = walk_descriptor_class_config_id(link.child, seen)
            if class_config_id is not None:
                return class_config_id
        return None
    if node.kind == AttributeTypeDescriptorKind.mapping:
        value_link = next(
            (link for link in node.child_links if link.role == AttributeTypeDescriptorRole.value_),
            None,
        )
        target = value_link.child if value_link else node.child_links[0].child if node.child_links else None
        if target is None:
            return None
        return walk_descriptor_class_config_id(target, seen)
    return None


def _structural_type_info(node: AttributeTypeDescriptor) -> AttributeTypeInfo:
    return AttributeTypeInfo(
        kind=node.kind,
        primitive_config=None,
        enum_config=None,
        class_config=None,
        collection_kind=node.collection_kind,
        nullable=False,
    )


def pick_child(links: list[AttributeTypeDescriptorLink]) -> AttributeTypeDescriptorLink:
    """Pick the most relevant child descriptor (prefer ELEMENT role)."""
    if not links:
        raise ValueError("Collection descriptor missing child link")
    for link in links:
        if link.role == AttributeTypeDescriptorRole.element:
            return link
    return links[0]


def is_null_descriptor(info: AttributeTypeInfo) -> bool:
    """Return True if info describes a Null-only primitive."""
    if info.primitive_config is None:
        return False
    code_primitive_type = CodePrimitiveType.model_validate(info.primitive_config.primitive_type)
    return code_primitive_type.base_type == CodePrimitiveBaseType.null
