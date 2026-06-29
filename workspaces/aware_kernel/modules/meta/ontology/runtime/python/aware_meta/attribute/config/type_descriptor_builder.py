"""Language-agnostic factory that builds AttributeTypeDescriptor trees.

- Primary path: use plugin.type_descriptor_adapter to parse to TypeNode, then map Node → Descriptor.
- Safe fallback: use plugin.primitive_type.from_string to parse primitives/containers and map recursively.
- Last resort: treat unknown identifiers as ENUM (if name matches) or CLASS.
"""

from __future__ import annotations

# Kernel Graph Ontology
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.enum.enum_config import EnumConfig

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Code
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.type_descriptor_nodes import TypeNode, TypeNodeKind, CollectionKind

# Meta
from aware_meta.fqn_resolver import FqnScope
from aware_meta.primitive.config.builder import build_primitive_config

from aware_meta.graph.config.stable_ids import (
    stable_attribute_type_descriptor_id,
    stable_attribute_type_descriptor_link_id,
)

from aware_utils.string_transform import to_pascal_case
from aware_utils.logging import logger


def ensure_stable_descriptor_tree_ids(
    descriptor: AttributeTypeDescriptor,
) -> AttributeTypeDescriptor:
    """
    Ensure stable IDs (and FK backfills) for AttributeTypeDescriptor + AttributeTypeDescriptorLink trees.

    Without this, ORMModel defaults mint uuid4 IDs, causing churn across rebuilds.
    """
    # Recurse first so children have stable IDs.
    for link in list(descriptor.child_links):
        _ = ensure_stable_descriptor_tree_ids(link.child)

    # Backfill FK IDs from relationship objects (stable upstream).
    if descriptor.primitive_config is not None:
        descriptor.primitive_config_id = descriptor.primitive_config.id
    if descriptor.enum_config is not None:
        descriptor.enum_config_id = descriptor.enum_config.id
    if descriptor.class_config is not None:
        descriptor.class_config_id = descriptor.class_config.id

    # Normalize children for stable fingerprinting.
    child_entries: list[tuple[str, int, str]] = []
    for link in descriptor.child_links:
        position = int(link.position or 0)
        child_entries.append((link.role.value, position, str(link.child.id)))
    child_entries_sorted = sorted(
        child_entries,
        key=lambda x: (x[0], x[1], x[2]),
    )
    child_links_fingerprint = ";".join([f"{r}:{p}:{cid}" for r, p, cid in child_entries_sorted])

    kind = descriptor.kind.value
    collection_kind = descriptor.collection_kind.value if descriptor.collection_kind is not None else None
    entity_id = descriptor.class_config_id or descriptor.enum_config_id or descriptor.primitive_config_id

    descriptor.id = stable_attribute_type_descriptor_id(
        kind=kind,
        collection_kind=collection_kind,
        entity_id=entity_id,
        child_links_fingerprint=child_links_fingerprint,
    )

    # Update links: stable parent FK, stable child FK, stable link IDs, stable ordering.
    stable_links: list[AttributeTypeDescriptorLink] = []
    for link in descriptor.child_links:
        link.attribute_type_descriptor_id = descriptor.id
        link.child_id = link.child.id
        link.id = stable_attribute_type_descriptor_link_id(
            attribute_type_descriptor_id=descriptor.id,
            child_id=link.child.id,
            role=link.role.value,
            position=int(link.position or 0),
        )
        stable_links.append(link)
    descriptor.child_links = sorted(
        stable_links,
        key=lambda l: (
            l.role.value,
            int(l.position or 0),
            str(l.child_id),
        ),
    )

    return descriptor


def build_type_descriptor(
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    type_text: str,
) -> AttributeTypeDescriptor:
    # Preferred: adapter → TypeNode
    node: TypeNode = type_descriptor_adapter.parse_type(type_text)
    root = from_type_node(type_descriptor_adapter, primitive_codec, fqn_scope, node, type_text)
    return ensure_stable_descriptor_tree_ids(root)


def get_generic_type_descriptor(
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    type_text: str,
) -> AttributeTypeDescriptor:
    # Pre-check: direct enum by name (before primitive heuristics that may misclassify, e.g., 'interface_os')
    match_enum = try_resolve_enum(primitive_codec, fqn_scope, type_text)
    if match_enum is not None:
        return ensure_stable_descriptor_tree_ids(
            AttributeTypeDescriptor(kind=Kind.enum, enum_config_id=match_enum.id, enum_config=match_enum)
        )

    prim = primitive_codec.parse(type_text)
    if prim is not None:
        # Special-case: ARRAY with unknown item type (e.g., enum identifiers in SQL)
        if prim.base_type == CodePrimitiveBaseType.array and prim.item_type is None:
            # Recover inner type text using language-primitive helper
            inner_text = primitive_codec.get_inner_type(type_text)
            inner_text = (inner_text or "").strip()
            # Build COLLECTION parent
            parent = AttributeTypeDescriptor(kind=Kind.collection, collection_kind=AttributeCollectionType.list)
            # Decide child kind: ENUM if name matches, else try primitive parse, else CLASS
            child: AttributeTypeDescriptor
            match_enum = try_resolve_enum(primitive_codec, fqn_scope, inner_text)
            if match_enum is not None:
                child = AttributeTypeDescriptor(kind=Kind.enum, enum_config_id=match_enum.id, enum_config=match_enum)
            else:
                inner_prim = primitive_codec.parse(inner_text)
                if inner_prim is not None:
                    child = from_primitive_type(type_descriptor_adapter, primitive_codec, fqn_scope, inner_prim)
                else:
                    child = AttributeTypeDescriptor(kind=Kind.class_)
                    attach_class_reference(fqn_scope, child, inner_text, type_text)
            link = AttributeTypeDescriptorLink(
                role=Role.element,
                position=0,
                attribute_type_descriptor_id=parent.id,
                child=child,
            )
            parent.child_links.append(link)
            return ensure_stable_descriptor_tree_ids(parent)
        return from_primitive_type(type_descriptor_adapter, primitive_codec, fqn_scope, prim)

    # Let the language primitive helper decide if this is a collection
    is_list = primitive_codec.is_list(type_text)

    # Determine the base identifier (strip []/?) via enum_type helper
    ident = primitive_codec.enum_ident(type_text)
    normalized = ident
    pascal = to_pascal_case(normalized)

    # Build the leaf descriptor (ENUM if matches, else try primitive, else CLASS)
    leaf: AttributeTypeDescriptor
    match_enum = try_resolve_enum(primitive_codec, fqn_scope, normalized)
    if match_enum is not None:
        leaf = AttributeTypeDescriptor(kind=Kind.enum, enum_config_id=match_enum.id, enum_config=match_enum)
    else:
        inner_prim = None
        try:
            inner_prim = primitive_codec.parse(normalized)
        except Exception:
            logger.error(
                f"Failed to parse inner primitive type text {normalized} with primitive type {primitive_codec.parse(normalized)}"
            )
            inner_prim = None
        if inner_prim is not None:
            leaf = from_primitive_type(type_descriptor_adapter, primitive_codec, fqn_scope, inner_prim)
        else:
            leaf = AttributeTypeDescriptor(kind=Kind.class_)
            attach_class_reference(fqn_scope, leaf, normalized, type_text)

    if is_list:
        parent = AttributeTypeDescriptor(kind=Kind.collection, collection_kind=AttributeCollectionType.list)
        link = AttributeTypeDescriptorLink(
            role=Role.element,
            position=0,
            attribute_type_descriptor_id=parent.id,
            child=leaf,
        )
        parent.child_links.append(link)
        return ensure_stable_descriptor_tree_ids(parent)

    attach_class_reference(fqn_scope, leaf, normalized, type_text)
    return ensure_stable_descriptor_tree_ids(leaf)


# ---------- Mapping helpers ----------
def from_type_node(
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    node: TypeNode,
    type_text: str,
) -> AttributeTypeDescriptor:
    if node.kind == TypeNodeKind.PRIMITIVE:
        prim = primitive_codec.parse(node.text or "")
        if prim is None:
            prim = primitive_codec.any()
        primitive_config = build_primitive_config(prim)
        return AttributeTypeDescriptor(kind=Kind.primitive, primitive_config=primitive_config)
    if node.kind == TypeNodeKind.IDENT:
        if node.text:
            ident = node.text.strip()
            # Attempt ENUM resolution first; else treat as CLASS
            match = try_resolve_enum(primitive_codec, fqn_scope, ident)
            if match is not None:
                return AttributeTypeDescriptor(kind=Kind.enum, enum_config_id=match.id, enum_config=match)
            descriptor = AttributeTypeDescriptor(kind=Kind.class_)
            attach_class_reference(fqn_scope, descriptor, ident, type_text)
            return descriptor
    if node.kind == TypeNodeKind.COLLECTION:
        parent = AttributeTypeDescriptor(
            kind=Kind.collection,
            collection_kind=(
                AttributeCollectionType.list
                if node.collection_kind == CollectionKind.LIST
                else AttributeCollectionType.set
            ),
        )
        if node.element is not None:
            child = from_type_node(
                type_descriptor_adapter,
                primitive_codec,
                fqn_scope,
                node.element,
                type_text,
            )
            link = AttributeTypeDescriptorLink(
                role=Role.element,
                position=0,
                attribute_type_descriptor_id=parent.id,
                child=child,
            )
            parent.child_links.append(link)
        return parent
    if node.kind == TypeNodeKind.MAPPING:
        parent = AttributeTypeDescriptor(kind=Kind.mapping)
        if node.key is not None:
            k = from_type_node(type_descriptor_adapter, primitive_codec, fqn_scope, node.key, type_text)
            lk = AttributeTypeDescriptorLink(
                role=Role.key,
                position=0,
                attribute_type_descriptor_id=parent.id,
                child=k,
            )
            parent.child_links.append(lk)
        if node.value is not None:
            v = from_type_node(
                type_descriptor_adapter,
                primitive_codec,
                fqn_scope,
                node.value,
                type_text,
            )
            lv = AttributeTypeDescriptorLink(
                role=Role.value_,
                position=0,
                attribute_type_descriptor_id=parent.id,
                child=v,
            )
            parent.child_links.append(lv)
        return parent
    if node.kind == TypeNodeKind.TUPLE:
        parent = AttributeTypeDescriptor(kind=Kind.tuple)
        pos = 1
        for elem in node.elements:
            ch = from_type_node(type_descriptor_adapter, primitive_codec, fqn_scope, elem, type_text)
            link = AttributeTypeDescriptorLink(
                role=Role.member,
                position=pos,
                attribute_type_descriptor_id=parent.id,
                child=ch,
            )
            parent.child_links.append(link)
            pos += 1
        return parent
    if node.kind == TypeNodeKind.UNION:
        parent = AttributeTypeDescriptor(kind=Kind.union)
        pos = 1
        for mem in node.members:
            ch = from_type_node(type_descriptor_adapter, primitive_codec, fqn_scope, mem, type_text)
            link = AttributeTypeDescriptorLink(
                role=Role.member,
                position=pos,
                attribute_type_descriptor_id=parent.id,
                child=ch,
            )
            parent.child_links.append(link)
            pos += 1
        return parent
    # Fallback for unknown node kinds
    descriptor = AttributeTypeDescriptor(kind=Kind.class_)
    if node.text is not None:
        attach_class_reference(fqn_scope, descriptor, node.text, type_text)
    else:
        raise ValueError(f"Node text is None for type text {type_text}")
    return descriptor


def _from_primitive_type_raw(
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    prim: CodePrimitiveType,
) -> AttributeTypeDescriptor:
    bt = prim.base_type
    # Containers
    if bt == CodePrimitiveBaseType.array and prim.item_type is not None:
        parent = AttributeTypeDescriptor(kind=Kind.collection, collection_kind=AttributeCollectionType.list)
        child = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, prim.item_type)
        link = AttributeTypeDescriptorLink(
            role=Role.element,
            position=0,
            attribute_type_descriptor_id=parent.id,
            child=child,
        )
        parent.child_links.append(link)
        return parent

    if bt == CodePrimitiveBaseType.set and prim.item_type is not None:
        parent = AttributeTypeDescriptor(kind=Kind.collection, collection_kind=AttributeCollectionType.set)
        child = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, prim.item_type)
        link = AttributeTypeDescriptorLink(
            role=Role.element,
            position=0,
            attribute_type_descriptor_id=parent.id,
            child=child,
        )
        parent.child_links.append(link)
        return parent

    if bt == CodePrimitiveBaseType.dict and prim.key_type is not None and prim.value_type is not None:
        parent = AttributeTypeDescriptor(kind=Kind.mapping)
        key_desc = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, prim.key_type)
        val_desc = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, prim.value_type)
        link_key = AttributeTypeDescriptorLink(
            role=Role.key,
            position=0,
            attribute_type_descriptor_id=parent.id,
            child=key_desc,
        )
        link_val = AttributeTypeDescriptorLink(
            role=Role.value_,
            position=0,
            attribute_type_descriptor_id=parent.id,
            child=val_desc,
        )
        parent.child_links.extend([link_key, link_val])
        return parent

    if bt == CodePrimitiveBaseType.tuple and prim.element_types:
        parent = AttributeTypeDescriptor(kind=Kind.tuple)
        for idx, elem in enumerate(prim.element_types, start=1):
            child = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, elem)
            link = AttributeTypeDescriptorLink(
                role=Role.member,
                position=idx,
                attribute_type_descriptor_id=parent.id,
                child=child,
            )
            parent.child_links.append(link)
        return parent

    if bt == CodePrimitiveBaseType.union and prim.union_types:
        parent = AttributeTypeDescriptor(kind=Kind.union)
        for idx, mem in enumerate(prim.union_types, start=1):
            child = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, mem)
            link = AttributeTypeDescriptorLink(
                role=Role.member,
                position=idx,
                attribute_type_descriptor_id=parent.id,
                child=child,
            )
            parent.child_links.append(link)
        return parent

    # Leaf primitive
    primitive_config = build_primitive_config(prim)
    return AttributeTypeDescriptor(kind=Kind.primitive, primitive_config=primitive_config)


def from_primitive_type(
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    prim: CodePrimitiveType,
) -> AttributeTypeDescriptor:
    """
    Public entrypoint: build descriptor tree from CodePrimitiveType and ensure stable IDs.
    """
    root = _from_primitive_type_raw(type_descriptor_adapter, primitive_codec, fqn_scope, prim)
    return ensure_stable_descriptor_tree_ids(root)


def normalize_enum_identifier(primitive_codec: CodePrimitiveCodec, identifier: str) -> str:
    parts = [p for p in (identifier or "").strip().split(".") if p]
    if not parts:
        return ""
    # Normalize only the leaf symbol name (preserve schema/domain qualifiers).
    normalized_leaf = to_pascal_case(primitive_codec.enum_ident(parts[-1]))
    parts[-1] = normalized_leaf
    return ".".join(parts)


def try_resolve_enum(
    primitive_codec: CodePrimitiveCodec,
    fqn_scope: FqnScope,
    identifier: str,
) -> EnumConfig | None:
    normalized = normalize_enum_identifier(primitive_codec, identifier)
    if not normalized:
        return None
    return fqn_scope.try_resolve_enum(normalized)


def attach_class_reference(
    fqn_scope: FqnScope,
    descriptor: AttributeTypeDescriptor,
    identifier: str,
    type_text: str,
) -> None:
    if descriptor.kind != Kind.class_:
        return
    normalized = identifier.strip()
    resolved = fqn_scope.try_resolve_class_with_fqn(normalized)
    if resolved is None:
        raise ValueError(f"Class {identifier} not found for type text {type_text}")
    _, class_config = resolved

    # Link the class config to the descriptor
    descriptor.class_config_id = class_config.id
    descriptor.class_config = class_config
