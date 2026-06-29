from __future__ import annotations

import hashlib
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.enum.enum_option import EnumOption
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

# Aware Kernel Meta
from aware_meta.attribute.instance.value.validator import (
    canonicalize_attribute_value_tree,
    validate_attribute_value_tree_with_context,
)
from aware_meta.attribute.instance.value.stable_ids import (
    stable_attribute_value_id,
    stable_attribute_value_link_id,
)

# Code Runtime
from aware_code.types import Json

from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks
from aware_meta_ontology.class_.class_config_enums import ClassValueMode


class AttributeValueBuildError(ValueError):
    pass


@dataclass(frozen=True)
class UnionSelection:
    """
    Explicit union selection for AttributeValue building.

    position: 1-based position as defined on AttributeTypeDescriptorLink(role=MEMBER, position=N).
    value:    The payload value to build for the selected member descriptor.
    """

    position: int
    value: Any


EnumOptionResolver = Callable[[AttributeTypeDescriptor, Any], UUID]
ClassInstanceResolver = Callable[[AttributeTypeDescriptor, Any], UUID]


def build_attribute_value_tree(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    stable_root_id: UUID | None = None,
    validate_tree: bool = True,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union: UnionSelection | None = None,
) -> AttributeValue:
    """
    Build a canonical AttributeValue tree for the provided descriptor and runtime value.

    The resulting tree is:
    - descriptor-aligned (shape matches the descriptor tree),
    - deterministic (child link ordering is canonicalized),
    - structurally validated (raises if invariants are violated),
    - ready for diffing (stable slot keys via position/identity_key).

    Notes on inputs:
    - PRIMITIVE: accepts any Json-like value; stored in `primitive_value`.
    - ENUM: accepts UUID/EnumOption; for string-like values, provide enum_option_resolver.
    - CLASS: accepts UUID/ClassInstance; for other values, provide class_instance_resolver.
    - UNION: to avoid ambiguity, pass `union=UnionSelection(position, value)` unless:
        - value is None and a NULL member exists, or
        - the union has exactly one non-null member.
    """
    # Canonical value trees are pure in-memory artifacts; avoid polluting the
    # global ORM identity map via implicit session binding.
    with disable_change_tracking_hooks():
        with disable_autobind():
            root = _build_node(
                type_descriptor=type_descriptor,
                value=value,
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
                union=union,
                path=_Path(),
            )
            canonicalize_attribute_value_tree(root)
            if stable_root_id is not None:
                _assign_stable_value_tree_ids(root=root, stable_root_id=stable_root_id)
            if validate_tree:
                validate_attribute_value_tree_with_context(root, class_configs_by_id=class_configs_by_id)
            return root


@dataclass(frozen=True)
class _Path:
    parts: tuple[str, ...] = ()

    def push(self, part: str) -> "_Path":
        return _Path(self.parts + (part,))

    def render(self) -> str:
        return "/".join(self.parts) if self.parts else "<root>"


def _build_node(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    union: UnionSelection | None,
    path: _Path,
) -> AttributeValue:
    kind = type_descriptor.kind

    if kind == Kind.primitive:
        return AttributeValue(
            type_descriptor=type_descriptor,
            type_descriptor_id=type_descriptor.id,
            primitive_value=_coerce_primitive_value(value),
        )

    if kind == Kind.enum:
        enum_option_id = _resolve_enum_option_id(
            value=value,
            type_descriptor=type_descriptor,
            resolver=enum_option_resolver,
            path=path,
        )
        return AttributeValue(
            type_descriptor=type_descriptor,
            type_descriptor_id=type_descriptor.id,
            enum_option_id=enum_option_id,
        )

    if kind == Kind.class_:
        # CLASS descriptors have two semantic modes (SSOT: ClassConfig.value_mode):
        # - GRAPH_REF: the value is a graph-addressable ClassInstance id (UUID)
        # - INLINE_VALUE: the value is an inline payload object (DTO/value object) stored as Json
        #
        # IMPORTANT: This must not depend on ORMModelRegistry binding state (heuristic).
        class_config = _resolve_class_config_for_descriptor(
            type_descriptor=type_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        value_mode = class_config.value_mode if class_config is not None else ClassValueMode.graph_ref
        if value_mode == ClassValueMode.inline_value:
            if hasattr(value, "model_dump"):
                try:
                    value = value.model_dump(mode="json")  # type: ignore[call-arg]
                except Exception:
                    pass
            return AttributeValue(
                type_descriptor=type_descriptor,
                type_descriptor_id=type_descriptor.id,
                primitive_value=_coerce_primitive_value(value),
            )

        class_instance_id = _resolve_class_instance_id(
            value=value,
            type_descriptor=type_descriptor,
            resolver=class_instance_resolver,
            path=path,
        )
        return AttributeValue(
            type_descriptor=type_descriptor,
            type_descriptor_id=type_descriptor.id,
            class_instance_id=class_instance_id,
        )

    if kind == Kind.collection:
        return _build_collection(
            type_descriptor=type_descriptor,
            value=value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            path=path,
        )

    if kind == Kind.mapping:
        return _build_mapping(
            type_descriptor=type_descriptor,
            value=value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            path=path,
        )

    if kind == Kind.tuple:
        return _build_tuple(
            type_descriptor=type_descriptor,
            value=value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            path=path,
        )

    if kind == Kind.union:
        return _build_union(
            type_descriptor=type_descriptor,
            value=value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=union,
            path=path,
        )

    raise AttributeValueBuildError(f"{path.render()}: unsupported descriptor kind {kind}")


def _build_collection(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    path: _Path,
) -> AttributeValue:
    ck = type_descriptor.collection_kind
    if ck is None:
        raise AttributeValueBuildError(f"{path.render()}: collection descriptor missing collection_kind")

    element_desc = _pick_role_child(type_descriptor, Role.element)
    if element_desc is None:
        raise AttributeValueBuildError(f"{path.render()}: collection descriptor missing ELEMENT child")

    container = AttributeValue(
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
        child_links=[],
    )

    if ck == AttributeCollectionType.single:
        child = _build_node(
            type_descriptor=element_desc,
            value=value,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=None,
            path=path.push("E:0"),
        )
        container.child_links.append(
            AttributeValueLink(
                attribute_value_id=container.id,
                child=child,
                child_id=child.id,
                role=Role.element,
                position=0,
                identity_key=None,
            )
        )
        return container

    if ck == AttributeCollectionType.list:
        if not isinstance(value, (list, tuple)):
            raise AttributeValueBuildError(f"{path.render()}: LIST expects list/tuple, got {type(value).__name__}")

        for idx, item in enumerate(value):
            child = _build_node(
                type_descriptor=element_desc,
                value=item,
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
                union=None,
                path=path.push(f"E:{idx}"),
            )
            container.child_links.append(
                AttributeValueLink(
                    attribute_value_id=container.id,
                    child=child,
                    child_id=child.id,
                    role=Role.element,
                    position=idx,
                    identity_key=None,
                )
            )
        return container

    if ck == AttributeCollectionType.set:
        items: Iterable[Any]
        if isinstance(value, set):
            items = value
        elif isinstance(value, (list, tuple)):
            items = value
        else:
            raise AttributeValueBuildError(f"{path.render()}: SET expects set/list/tuple, got {type(value).__name__}")

        built: list[tuple[str, AttributeValue]] = []
        for item in items:
            child = _build_node(
                type_descriptor=element_desc,
                value=item,
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
                union=None,
                path=path.push("E:*"),
            )
            canonicalize_attribute_value_tree(child)
            ident = fingerprint_attribute_value(child)
            built.append((ident, child))

        # Deterministic order by identity_key
        built.sort(key=lambda t: t[0])

        seen: set[str] = set()
        for ident, child in built:
            if ident in seen:
                raise AttributeValueBuildError(f"{path.render()}: SET duplicate element identity_key={ident}")
            seen.add(ident)
            container.child_links.append(
                AttributeValueLink(
                    attribute_value_id=container.id,
                    child=child,
                    child_id=child.id,
                    role=Role.element,
                    position=None,
                    identity_key=ident,
                )
            )
        return container

    raise AttributeValueBuildError(f"{path.render()}: unsupported collection_kind {ck}")


def _build_mapping(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    path: _Path,
) -> AttributeValue:
    if not isinstance(value, Mapping):
        raise AttributeValueBuildError(f"{path.render()}: MAPPING expects dict-like, got {type(value).__name__}")

    key_desc = _pick_role_child(type_descriptor, Role.key)
    val_desc = _pick_role_child(type_descriptor, Role.value_)
    if key_desc is None or val_desc is None:
        raise AttributeValueBuildError(f"{path.render()}: MAPPING descriptor missing KEY or VALUE child")

    container = AttributeValue(
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
        child_links=[],
    )

    entries: list[tuple[str, AttributeValue, AttributeValue]] = []
    for raw_key, raw_val in value.items():
        key_node = _build_node(
            type_descriptor=key_desc,
            value=raw_key,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=None,
            path=path.push("K:*"),
        )
        canonicalize_attribute_value_tree(key_node)
        ident = fingerprint_attribute_value(key_node)

        val_node = _build_node(
            type_descriptor=val_desc,
            value=raw_val,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=None,
            path=path.push(f"V:{ident}"),
        )
        canonicalize_attribute_value_tree(val_node)

        entries.append((ident, key_node, val_node))

    # Deterministic order by key fingerprint.
    entries.sort(key=lambda e: e[0])

    seen: set[str] = set()
    for ident, key_node, val_node in entries:
        if ident in seen:
            raise AttributeValueBuildError(f"{path.render()}: MAPPING duplicate key identity_key={ident}")
        seen.add(ident)
        container.child_links.append(
            AttributeValueLink(
                attribute_value_id=container.id,
                child=key_node,
                child_id=key_node.id,
                role=Role.key,
                position=None,
                identity_key=ident,
            )
        )
        container.child_links.append(
            AttributeValueLink(
                attribute_value_id=container.id,
                child=val_node,
                child_id=val_node.id,
                role=Role.value_,
                position=None,
                identity_key=ident,
            )
        )

    return container


def _build_tuple(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    path: _Path,
) -> AttributeValue:
    if not isinstance(value, (list, tuple)):
        raise AttributeValueBuildError(f"{path.render()}: TUPLE expects list/tuple, got {type(value).__name__}")

    members = _member_descriptors(type_descriptor)
    if not members:
        raise AttributeValueBuildError(f"{path.render()}: TUPLE descriptor missing MEMBER children")

    # Canonical tuple arity is determined by descriptor member positions.
    expected_positions = list(members.keys())
    if len(value) != len(expected_positions):
        raise AttributeValueBuildError(
            f"{path.render()}: TUPLE arity mismatch expected={len(expected_positions)} got={len(value)}"
        )

    container = AttributeValue(
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
        child_links=[],
    )
    for offset, pos in enumerate(expected_positions):
        mem_desc = members[pos]
        child = _build_node(
            type_descriptor=mem_desc,
            value=value[offset],
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=None,
            path=path.push(f"M:{pos}"),
        )
        container.child_links.append(
            AttributeValueLink(
                attribute_value_id=container.id,
                child=child,
                child_id=child.id,
                role=Role.member,
                position=pos,
                identity_key=None,
            )
        )
    return container


def _build_union(
    *,
    type_descriptor: AttributeTypeDescriptor,
    value: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    union: UnionSelection | None,
    path: _Path,
) -> AttributeValue:
    members = _member_descriptors(type_descriptor)
    if not members:
        raise AttributeValueBuildError(f"{path.render()}: UNION descriptor missing MEMBER children")

    # 1) Explicit selection wins.
    if union is not None:
        if union.position not in members:
            raise AttributeValueBuildError(f"{path.render()}: UNION invalid selected position={union.position}")
        selected_pos = union.position
        selected_value = union.value
    else:
        # 2) Null shortcut (if a dedicated NULL member exists and the value is None).
        if value is None:
            null_positions = [pos for pos, d in members.items() if _is_null_member(d)]
            if len(null_positions) == 1:
                selected_pos = null_positions[0]
                selected_value = None
            else:
                raise AttributeValueBuildError(
                    f"{path.render()}: UNION value is None but no unique NULL member exists (members={list(members)})"
                )
        else:
            # 3) Unambiguous union: exactly one non-null member.
            non_null = [pos for pos, d in members.items() if not _is_null_member(d)]
            if len(non_null) == 1:
                selected_pos = non_null[0]
                selected_value = value
            else:
                raise AttributeValueBuildError(
                    f"{path.render()}: UNION selection required (members={list(members)}); pass union=UnionSelection(...)"
                )

    mem_desc = members[selected_pos]
    container = AttributeValue(
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
        child_links=[],
    )
    child = _build_node(
        type_descriptor=mem_desc,
        value=selected_value,
        class_configs_by_id=class_configs_by_id,
        enum_option_resolver=enum_option_resolver,
        class_instance_resolver=class_instance_resolver,
        union=None,
        path=path.push(f"SEL:{selected_pos}"),
    )
    container.child_links.append(
        AttributeValueLink(
            attribute_value_id=container.id,
            child=child,
            child_id=child.id,
            role=Role.member,
            position=selected_pos,
            identity_key=None,
        )
    )
    return container


def _resolve_enum_option_id(
    *,
    value: Any,
    type_descriptor: AttributeTypeDescriptor,
    resolver: EnumOptionResolver | None,
    path: _Path,
) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, EnumOption):
        return value.id
    if resolver is not None:
        try:
            return resolver(type_descriptor, value)
        except Exception as e:  # pragma: no cover
            raise AttributeValueBuildError(f"{path.render()}: enum resolver failed: {e}") from e
    raise AttributeValueBuildError(
        f"{path.render()}: ENUM expects UUID/EnumOption or resolver; got {type(value).__name__}"
    )


def _resolve_class_instance_id(
    *,
    value: Any,
    type_descriptor: AttributeTypeDescriptor,
    resolver: ClassInstanceResolver | None,
    path: _Path,
) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, ClassInstance):
        return value.id
    if resolver is not None:
        try:
            return resolver(type_descriptor, value)
        except Exception as e:  # pragma: no cover
            raise AttributeValueBuildError(f"{path.render()}: class instance resolver failed: {e}") from e
    raise AttributeValueBuildError(
        f"{path.render()}: CLASS expects UUID/ClassInstance or resolver; got {type(value).__name__}"
    )


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


def _pick_role_child(desc: AttributeTypeDescriptor, role: Role) -> AttributeTypeDescriptor | None:
    for link in desc.child_links:
        if link.child is None:
            raise AttributeValueBuildError("AttributeValueLink missing child (cannot pick role child)")
        if link.role == role:
            return link.child
    return None


def _member_descriptors(
    desc: AttributeTypeDescriptor,
) -> dict[int, AttributeTypeDescriptor]:
    members: dict[int, AttributeTypeDescriptor] = {}
    for link in desc.child_links:
        if link.child is None:
            raise AttributeValueBuildError("AttributeValueLink missing child (cannot pick role child)")
        if link.role != Role.member:
            continue
        pos = link.position
        if pos is None:
            continue
        members[pos] = link.child
    return dict(sorted(members.items(), key=lambda kv: kv[0]))


def _is_null_member(desc: AttributeTypeDescriptor) -> bool:
    if desc.kind != Kind.primitive:
        return False
    prim = desc.primitive_config
    if prim is None:
        return False
    prim_type = prim.primitive_type
    if prim_type.base_type == CodePrimitiveBaseType.null:
        return True
    return False


def fingerprint_attribute_value(node: AttributeValue) -> str:
    """
    Stable fingerprint of an AttributeValue subtree.

    This intentionally ignores AttributeValueLink.identity_key because identity_key is derived from
    this fingerprint for SET/MAPPING and including it would create recursion.
    """
    blob = json.dumps(
        _fingerprint_payload(node),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _assign_stable_value_tree_ids(*, root: AttributeValue, stable_root_id: UUID) -> None:
    """Assign deterministic ids to an AttributeValue tree in-place.

    This is required so OIG snapshots built from in-memory instances can be used as
    commit bases without introducing random UUID drift (which can break commit apply).
    """

    def walk(node: AttributeValue, *, node_id: UUID) -> None:
        node.id = node_id
        links = list(getattr(node, "child_links", []) or [])
        for link in links:
            role = link.role.value
            link_id = stable_attribute_value_link_id(
                parent_value_id=node_id,
                role=role,
                position=link.position,
                identity_key=link.identity_key,
            )
            child_id = stable_attribute_value_id(
                parent_value_id=node_id,
                role=role,
                position=link.position,
                identity_key=link.identity_key,
            )
            link.id = link_id
            link.attribute_value_id = node_id
            link.child_id = child_id

            child = link.child
            if child is None:
                raise AttributeValueBuildError("AttributeValueLink missing child (cannot assign stable ids)")
            walk(child, node_id=child_id)
            link.child = child

    walk(root, node_id=stable_root_id)


def _fingerprint_payload(node: AttributeValue) -> dict[str, Any]:
    desc = node.type_descriptor
    if desc is None:
        raise AttributeValueBuildError("AttributeValue missing type_descriptor (cannot fingerprint)")

    children = []
    for link in node.child_links:
        if link.child is None:
            raise AttributeValueBuildError("AttributeValueLink missing child (cannot fingerprint)")
        children.append(
            {
                "role": link.role.value,
                "position": link.position,
                "child": _fingerprint_payload(link.child),
            }
        )

    # Deterministic ordering
    children.sort(
        key=lambda c: (
            c["role"],
            c["position"] if c["position"] is not None else -1,
            json.dumps(c["child"], sort_keys=True),
        )
    )

    return {
        "descriptor_id": str(desc.id),
        "kind": desc.kind.value,
        "collection_kind": (desc.collection_kind.value if desc.collection_kind is not None else None),
        "primitive_value": _jsonify(node.primitive_value),
        "enum_option_id": (str(node.enum_option_id) if node.enum_option_id is not None else None),
        "class_instance_id": (str(node.class_instance_id) if node.class_instance_id is not None else None),
        "inline_value_instance_id": (
            str(node.inline_value_instance_id)
            if node.inline_value_instance_id is not None
            else (
                str(node.inline_value_instance.id)
                if getattr(node, "inline_value_instance", None) is not None
                and getattr(node.inline_value_instance, "id", None) is not None
                else None
            )
        ),
        "children": children,
    }


def _jsonify(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        # Match Pydantic's JSON encoding (UTC datetimes end with "Z").
        iso = value.isoformat()
        return iso.replace("+00:00", "Z")
    if hasattr(value, "value"):
        return getattr(value, "value")
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonify(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    return str(value)


def _coerce_primitive_value(value: Any) -> Json | None:
    """
    Coerce a primitive payload into the canonical Json envelope.

    The `Json` type in the kernel ontology is dict-backed; for scalar payloads we
    wrap as `{\"value\": <scalar>}` to preserve a stable schema and allow future
    delta/codec extensions without changing the leaf shape.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return Json(_jsonify(value))
    return Json({"value": _jsonify(value)})


__all__ = [
    "AttributeValueBuildError",
    "UnionSelection",
    "build_attribute_value_tree",
    "fingerprint_attribute_value",
]
