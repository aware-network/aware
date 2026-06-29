from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink


class AttributeValueTreeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class _Path:
    parts: tuple[str, ...] = ()

    def push(self, part: str) -> "_Path":
        return _Path(self.parts + (part,))

    def render(self) -> str:
        return "/".join(self.parts) if self.parts else "<root>"


def canonicalize_attribute_value_tree(root: AttributeValue) -> None:
    """
    Canonicalize a value tree in-place.

    Today this provides deterministic ordering for `child_links` to ensure
    stable hashing and stable diffs.
    """
    _canonicalize_node(root)


def validate_attribute_value_tree(root: AttributeValue) -> None:
    """
    Validate that an AttributeValue tree is descriptor-driven and internally consistent.

    This is a *structural* validator:
    - Ensures each value node kind matches its referenced descriptor node kind.
    - Ensures container nodes express structure via child links only.
    - Ensures child link roles/keys satisfy the semantics of the descriptor kind.
    - Ensures leaf nodes carry only the payload permitted by the descriptor kind.

    It intentionally does not validate domain semantics (e.g. enum option membership)
    beyond basic presence, because those checks depend on richer OCG/registry context.
    """
    validate_attribute_value_tree_with_context(root, class_configs_by_id=None)


def validate_attribute_value_tree_with_context(
    root: AttributeValue, *, class_configs_by_id: Mapping[UUID, ClassConfig] | None
) -> None:
    """
    Validate an AttributeValue tree with optional external context.

    class_configs_by_id enables resolving CLASS value_mode when the descriptor's
    `class_config` relationship is not populated (common when loading OCG from msgpack).
    """
    if root.type_descriptor is None:
        raise AttributeValueTreeValidationError("AttributeValue missing type_descriptor")
    _validate_node(
        root,
        expected=root.type_descriptor,
        path=_Path(),
        class_configs_by_id=class_configs_by_id,
    )


def _canonicalize_node(node: AttributeValue) -> None:
    desc = node.type_descriptor
    if desc is None:
        return

    # Recurse first so fingerprints/identity checks can assume canonical children.
    for link in list(getattr(node, "child_links", []) or []):
        _canonicalize_node(link.child)

    node.child_links = sorted(node.child_links or [], key=lambda l: _link_sort_key(desc, l))


def _link_sort_key(desc: AttributeTypeDescriptor, link: AttributeValueLink) -> tuple:
    # Deterministic ordering: group by role then slot key.
    role = link.role.value if hasattr(link.role, "value") else str(link.role)

    if desc.kind == Kind.mapping:
        # Stable grouping by identity_key, then KEY before VALUE.
        ident = link.identity_key or ""
        role_rank = 0 if link.role == Role.key else 1 if link.role == Role.value_ else 2
        return (role_rank, ident, role)

    if desc.kind in (Kind.tuple, Kind.union):
        pos = link.position if link.position is not None else -1
        return (0, pos, role)

    if desc.kind == Kind.collection:
        ck = desc.collection_kind
        if ck == AttributeCollectionType.set:
            return (0, link.identity_key or "", role)
        # LIST (and SINGLE fallback): sort by position then identity_key
        pos = link.position if link.position is not None else -1
        return (0, pos, link.identity_key or "", role)

    # Fallback: stable but conservative
    return (
        role,
        link.position if link.position is not None else -1,
        link.identity_key or "",
    )


def _validate_node(
    node: AttributeValue,
    *,
    expected: AttributeTypeDescriptor,
    path: _Path,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    actual = node.type_descriptor
    if actual is None:
        raise AttributeValueTreeValidationError(f"{path.render()}: value node missing type_descriptor")

    # Strong identity check when IDs are available.
    if getattr(actual, "id", None) is not None and getattr(expected, "id", None) is not None:
        if actual.id != expected.id:
            raise AttributeValueTreeValidationError(
                f"{path.render()}: descriptor mismatch value={actual.id} expected={expected.id}"
            )

    if actual.kind != expected.kind:
        raise AttributeValueTreeValidationError(
            f"{path.render()}: kind mismatch value={actual.kind} expected={expected.kind}"
        )

    kind = expected.kind

    # Container invariants: no leaf payload.
    if kind in (Kind.collection, Kind.mapping, Kind.tuple, Kind.union):
        if node.primitive_value is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: container node must not set primitive_value")
        if node.enum_option_id is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: container node must not set enum_option_id")
        if node.class_instance_id is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: container node must not set class_instance_id")
        if node.inline_value_instance_id is not None:
            raise AttributeValueTreeValidationError(
                f"{path.render()}: container node must not set inline_value_instance_id"
            )

    # Leaf invariants: no children and only the right payload.
    if kind == Kind.primitive:
        _require_no_children(node, path)
        if node.enum_option_id is not None or node.class_instance_id is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: primitive leaf must not set enum/class payload")
        return

    if kind == Kind.enum:
        _require_no_children(node, path)
        if node.enum_option_id is None:
            raise AttributeValueTreeValidationError(f"{path.render()}: enum leaf must set enum_option_id")
        if (
            node.primitive_value is not None
            or node.class_instance_id is not None
            or node.inline_value_instance_id is not None
        ):
            raise AttributeValueTreeValidationError(
                f"{path.render()}: enum leaf must not set primitive/class/inline payload"
            )
        return

    if kind == Kind.class_:
        _require_no_children(node, path)
        # CLASS descriptors have two semantic modes (SSOT: ClassConfig.value_mode):
        # - GRAPH_REF: the value is a graph-addressable ClassInstance id (UUID)
        # - INLINE_VALUE: the value is a nested InlineValueInstance (DTO/value object)
        class_config = _resolve_class_config_for_descriptor(
            type_descriptor=expected,
            class_configs_by_id=class_configs_by_id,
        )
        value_mode = class_config.value_mode if class_config is not None else ClassValueMode.graph_ref

        if value_mode == ClassValueMode.inline_value:
            inline_value_instance_id = node.inline_value_instance_id
            if inline_value_instance_id is None and node.inline_value_instance is not None:
                inline_value_instance_id = node.inline_value_instance.id
            if inline_value_instance_id is None:
                raise AttributeValueTreeValidationError(
                    f"{path.render()}: inline class payload must set inline_value_instance_id"
                )
            if node.class_instance_id is not None or node.enum_option_id is not None or node.primitive_value is not None:
                raise AttributeValueTreeValidationError(
                    f"{path.render()}: inline class payload must not set class/enum/primitive payload"
                )
            return

        if node.class_instance_id is None:
            raise AttributeValueTreeValidationError(f"{path.render()}: class leaf must set class_instance_id")
        if node.primitive_value is not None or node.enum_option_id is not None or node.inline_value_instance_id is not None:
            raise AttributeValueTreeValidationError(
                f"{path.render()}: class leaf must not set primitive/enum/inline payload"
            )
        return

    if kind == Kind.collection:
        _validate_collection(node, expected, path, class_configs_by_id)
        return

    if kind == Kind.mapping:
        _validate_mapping(node, expected, path, class_configs_by_id)
        return

    if kind == Kind.tuple:
        _validate_tuple(node, expected, path, class_configs_by_id)
        return

    if kind == Kind.union:
        _validate_union(node, expected, path, class_configs_by_id)
        return

    raise AttributeValueTreeValidationError(f"{path.render()}: unsupported descriptor kind: {kind}")


def _require_no_children(node: AttributeValue, path: _Path) -> None:
    if node.child_links:
        raise AttributeValueTreeValidationError(f"{path.render()}: leaf node must not have child_links")


def _iter_links(node: AttributeValue) -> Iterable[AttributeValueLink]:
    return list(getattr(node, "child_links", []) or [])


def _resolve_class_config_for_descriptor(
    *,
    type_descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> ClassConfig | None:
    if class_configs_by_id is not None and type_descriptor.class_config_id is not None:
        resolved = class_configs_by_id.get(type_descriptor.class_config_id)
        if resolved is not None:
            return resolved
    return type_descriptor.class_config


def _validate_collection(
    node: AttributeValue,
    desc: AttributeTypeDescriptor,
    path: _Path,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    ck = desc.collection_kind
    if ck is None:
        raise AttributeValueTreeValidationError(f"{path.render()}: collection descriptor missing collection_kind")

    element_desc = _pick_role_child(desc, Role.element)
    if element_desc is None:
        raise AttributeValueTreeValidationError(f"{path.render()}: collection descriptor missing ELEMENT child")

    for link in _iter_links(node):
        if link.role != Role.element:
            raise AttributeValueTreeValidationError(f"{path.render()}: collection child role must be ELEMENT")

        if ck == AttributeCollectionType.set:
            if not link.identity_key:
                raise AttributeValueTreeValidationError(f"{path.render()}: SET element missing identity_key")
            if link.position is not None:
                raise AttributeValueTreeValidationError(f"{path.render()}: SET element must not set position")
            slot = f"E:{link.identity_key}"
        else:
            # LIST / SINGLE: positional ordering; identity_key is allowed but optional.
            if link.position is None:
                raise AttributeValueTreeValidationError(f"{path.render()}: LIST element missing position")
            slot = f"E:{link.position}"

        _validate_node(
            link.child,
            expected=element_desc,
            path=path.push(slot),
            class_configs_by_id=class_configs_by_id,
        )


def _validate_mapping(
    node: AttributeValue,
    desc: AttributeTypeDescriptor,
    path: _Path,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    key_desc = _pick_role_child(desc, Role.key)
    value_desc = _pick_role_child(desc, Role.value_)
    if key_desc is None or value_desc is None:
        raise AttributeValueTreeValidationError(f"{path.render()}: mapping descriptor must have KEY and VALUE children")

    # Group links by identity_key.
    by_ident: dict[str, list[AttributeValueLink]] = {}
    for link in _iter_links(node):
        if link.role not in (Role.key, Role.value_):
            raise AttributeValueTreeValidationError(f"{path.render()}: mapping child role must be KEY or VALUE")
        if link.position is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: mapping links must not set position")
        if not link.identity_key:
            raise AttributeValueTreeValidationError(f"{path.render()}: mapping links must set identity_key")
        by_ident.setdefault(link.identity_key, []).append(link)

    for ident, links in by_ident.items():
        keys = [l for l in links if l.role == Role.key]
        vals = [l for l in links if l.role == Role.value_]
        if len(keys) != 1 or len(vals) != 1:
            raise AttributeValueTreeValidationError(
                f"{path.render()}: mapping entry {ident} must have exactly one KEY and one VALUE"
            )

        _validate_node(
            keys[0].child,
            expected=key_desc,
            path=path.push(f"K:{ident}"),
            class_configs_by_id=class_configs_by_id,
        )
        _validate_node(
            vals[0].child,
            expected=value_desc,
            path=path.push(f"V:{ident}"),
            class_configs_by_id=class_configs_by_id,
        )


def _validate_tuple(
    node: AttributeValue,
    desc: AttributeTypeDescriptor,
    path: _Path,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    members = _member_descriptors(desc)
    if not members:
        raise AttributeValueTreeValidationError(f"{path.render()}: tuple descriptor missing MEMBER children")

    links_by_pos: dict[int, AttributeValueLink] = {}
    for link in _iter_links(node):
        if link.role != Role.member:
            raise AttributeValueTreeValidationError(f"{path.render()}: tuple child role must be MEMBER")
        if link.identity_key is not None:
            raise AttributeValueTreeValidationError(f"{path.render()}: tuple links must not set identity_key")
        if link.position is None:
            raise AttributeValueTreeValidationError(f"{path.render()}: tuple MEMBER missing position")
        if link.position in links_by_pos:
            raise AttributeValueTreeValidationError(f"{path.render()}: duplicate tuple MEMBER position={link.position}")
        links_by_pos[link.position] = link

    for pos, mem_desc in members.items():
        if pos not in links_by_pos:
            raise AttributeValueTreeValidationError(f"{path.render()}: tuple missing MEMBER position={pos}")
        _validate_node(
            links_by_pos[pos].child,
            expected=mem_desc,
            path=path.push(f"M:{pos}"),
            class_configs_by_id=class_configs_by_id,
        )


def _validate_union(
    node: AttributeValue,
    desc: AttributeTypeDescriptor,
    path: _Path,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> None:
    members = _member_descriptors(desc)
    if not members:
        raise AttributeValueTreeValidationError(f"{path.render()}: union descriptor missing MEMBER children")

    links = list(_iter_links(node))
    if len(links) != 1:
        raise AttributeValueTreeValidationError(f"{path.render()}: union value must select exactly one MEMBER")
    link = links[0]
    if link.role != Role.member:
        raise AttributeValueTreeValidationError(f"{path.render()}: union child role must be MEMBER")
    if link.identity_key is not None:
        raise AttributeValueTreeValidationError(f"{path.render()}: union links must not set identity_key")
    if link.position is None:
        raise AttributeValueTreeValidationError(f"{path.render()}: union MEMBER missing position")
    if link.position not in members:
        raise AttributeValueTreeValidationError(
            f"{path.render()}: union selected MEMBER position={link.position} invalid"
        )
    _validate_node(
        link.child,
        expected=members[link.position],
        path=path.push(f"SEL:{link.position}"),
        class_configs_by_id=class_configs_by_id,
    )


def _pick_role_child(desc: AttributeTypeDescriptor, role: Role) -> AttributeTypeDescriptor | None:
    for link in desc.child_links or []:
        if link.role == role:
            return link.child
    return None


def _member_descriptors(
    desc: AttributeTypeDescriptor,
) -> dict[int, AttributeTypeDescriptor]:
    members: dict[int, AttributeTypeDescriptor] = {}
    for link in desc.child_links or []:
        if link.role != Role.member:
            continue
        pos = link.position
        if pos is None:
            continue
        members[pos] = link.child
    return dict(sorted(members.items(), key=lambda kv: kv[0]))


__all__ = [
    "AttributeValueTreeValidationError",
    "canonicalize_attribute_value_tree",
    "validate_attribute_value_tree",
]
