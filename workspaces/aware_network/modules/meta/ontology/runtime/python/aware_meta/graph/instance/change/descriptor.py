from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
from uuid import UUID

from aware_meta.graph.instance.change.ocg_descriptor_spec import (
    OcgAttributeDescriptorSpec,
    OcgClassDescriptorSpec,
    OcgDescriptorSpec,
    OcgEnumOptionDescriptorSpec,
)

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)


@dataclass(frozen=True, slots=True)
class CommitChangeDescriptor:
    """Canonical descriptor for consumer-facing commit deltas.

    This is a projection layer: it normalizes raw OIG Change trees into
    atomic, ordered descriptors that can be narrated deterministically.
    """

    kind: Literal["class_instance", "attribute_value", "relationship"]
    op: Literal["create", "update", "delete"]

    class_instance_id: UUID | None = None
    class_config_id: UUID | None = None
    class_name: str | None = None

    attribute_id: UUID | None = None
    attribute_config_id: UUID | None = None
    attribute_name: str | None = None

    path: str | None = None
    value_kind: str | None = None
    value: Any | None = None

    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        def _jsonable(v: Any) -> Any:
            if isinstance(v, UUID):
                return str(v)
            if isinstance(v, ChangeType):
                return v.value
            return v

        out = asdict(self)
        for k, v in list(out.items()):
            if isinstance(v, dict):
                out[k] = {kk: _jsonable(vv) for kk, vv in v.items()}
            else:
                out[k] = _jsonable(v)
        return out


@dataclass(frozen=True, slots=True)
class _OcgDescriptorSpecIndex:
    classes_by_id: dict[UUID, OcgClassDescriptorSpec]
    attributes_by_id: dict[UUID, OcgAttributeDescriptorSpec]
    enum_options_by_id: dict[UUID, OcgEnumOptionDescriptorSpec]

    @staticmethod
    def from_spec(spec: OcgDescriptorSpec) -> "_OcgDescriptorSpecIndex":
        classes_by_id: dict[UUID, OcgClassDescriptorSpec] = {}
        attributes_by_id: dict[UUID, OcgAttributeDescriptorSpec] = {}
        enum_options_by_id: dict[UUID, OcgEnumOptionDescriptorSpec] = {}

        def index_type_descriptor(desc) -> None:
            enum_spec = getattr(desc, "enum_spec", None)
            if enum_spec is not None:
                for opt in enum_spec.options or []:
                    enum_options_by_id[opt.enum_option_id] = opt
            for link in getattr(desc, "attribute_type_descriptor_link_child_list", []) or []:
                if link.child is not None:
                    index_type_descriptor(link.child)

        for cls in spec.classes:
            classes_by_id[cls.class_config_id] = cls
            for attr in cls.attributes:
                attributes_by_id[attr.attribute_config_id] = attr
                index_type_descriptor(attr.type_descriptor)

            # Also index enum options referenced by function input/output types.
            for fn in cls.functions:
                for io in (fn.inputs or []) + (fn.returns or []):
                    index_type_descriptor(io.type_descriptor)

        return _OcgDescriptorSpecIndex(
            classes_by_id=classes_by_id,
            attributes_by_id=attributes_by_id,
            enum_options_by_id=enum_options_by_id,
        )

    def class_name(self, class_config_id: UUID | None) -> str | None:
        if class_config_id is None:
            return None
        cls = self.classes_by_id.get(class_config_id)
        return cls.name if cls is not None else None

    def attribute_name(self, attribute_config_id: UUID | None) -> str | None:
        if attribute_config_id is None:
            return None
        attr = self.attributes_by_id.get(attribute_config_id)
        return attr.name if attr is not None else None

    def enum_label(self, enum_option_id: UUID | None) -> str | None:
        if enum_option_id is None:
            return None
        opt = self.enum_options_by_id.get(enum_option_id)
        if opt is None:
            return None
        return opt.label or opt.value


def describe_oig_changes(
    *,
    changes_payload: list[dict[str, Any]],
    ocg_descriptor_spec: OcgDescriptorSpec | None = None,
) -> list[CommitChangeDescriptor]:
    """Convert raw OIG change payload into ordered descriptors."""
    spec_index = (
        _OcgDescriptorSpecIndex.from_spec(ocg_descriptor_spec)
        if ocg_descriptor_spec is not None
        else None
    )

    out: list[CommitChangeDescriptor] = []
    for raw in changes_payload:
        tree = ObjectInstanceGraphChange.model_validate(raw)
        if tree.type == ObjectInstanceGraphChangeType.object_instance:
            for ci_change in tree.class_instance_changes:
                out.extend(_describe_class_instance_change(ci_change=ci_change, spec_index=spec_index))
            continue

        if tree.type == ObjectInstanceGraphChangeType.object_instance_relationship:
            # v0: relationship narration is intentionally coarse.
            out.append(
                CommitChangeDescriptor(
                    kind="relationship",
                    op="update",
                    details={"relationship_change_count": len(tree.class_instance_relationship_changes)},
                )
            )
            continue

        raise ValueError(f"Unsupported ObjectInstanceGraphChangeType: {tree.type}")

    return out


def _describe_class_instance_change(
    *,
    ci_change: ClassInstanceChange,
    spec_index: _OcgDescriptorSpecIndex | None,
) -> list[CommitChangeDescriptor]:
    op = _op(ci_change.change.type)
    class_config_id = _scalar_uuid(ci_change.change, "class_config_id")
    class_name = spec_index.class_name(class_config_id) if spec_index is not None else None

    out: list[CommitChangeDescriptor] = []

    if op in ("create", "delete"):
        out.append(
            CommitChangeDescriptor(
                kind="class_instance",
                op=op,
                class_instance_id=ci_change.class_instance_id,
                class_config_id=class_config_id,
                class_name=class_name,
            )
        )

    for attr_change in ci_change.attribute_changes:
        out.extend(
            _describe_attribute_change(
                attr_change=attr_change,
                class_instance_id=ci_change.class_instance_id,
                class_config_id=class_config_id,
                class_name=class_name,
                spec_index=spec_index,
            )
        )

    return out


def _describe_attribute_change(
    *,
    attr_change: AttributeChange,
    class_instance_id: UUID,
    class_config_id: UUID | None,
    class_name: str | None,
    spec_index: _OcgDescriptorSpecIndex | None,
) -> list[CommitChangeDescriptor]:
    attribute_config_id = _scalar_uuid(attr_change.change, "attribute_config_id")
    attribute_name = spec_index.attribute_name(attribute_config_id) if spec_index is not None else None

    if attr_change.value_root_change is None:
        return [
            CommitChangeDescriptor(
                kind="attribute_value",
                op=_op(attr_change.change.type),
                class_instance_id=class_instance_id,
                class_config_id=class_config_id,
                class_name=class_name,
                attribute_id=attr_change.attribute_id,
                attribute_config_id=attribute_config_id,
                attribute_name=attribute_name,
                value_kind="missing_value_root_change",
                details={"attribute_change_id": str(attr_change.id)},
            )
        ]

    mutations = _collect_value_mutations(
        value_change=attr_change.value_root_change,
        path_prefix=attribute_name or (attribute_config_id.hex if attribute_config_id else "<attribute>"),
        spec_index=spec_index,
    )
    if mutations:
        return [
            CommitChangeDescriptor(
                kind="attribute_value",
                op=m.op,
                class_instance_id=class_instance_id,
                class_config_id=class_config_id,
                class_name=class_name,
                attribute_id=attr_change.attribute_id,
                attribute_config_id=attribute_config_id,
                attribute_name=attribute_name,
                path=m.path,
                value_kind=m.value_kind,
                value=m.value,
                details=m.details,
            )
            for m in mutations
        ]

    return [
        CommitChangeDescriptor(
            kind="attribute_value",
            op=_op(attr_change.change.type),
            class_instance_id=class_instance_id,
            class_config_id=class_config_id,
            class_name=class_name,
            attribute_id=attr_change.attribute_id,
            attribute_config_id=attribute_config_id,
            attribute_name=attribute_name,
            path=attribute_name,
            value_kind="complex",
            details={"attribute_change_id": str(attr_change.id)},
        )
    ]


@dataclass(frozen=True, slots=True)
class _ValueMutation:
    op: Literal["create", "update", "delete"]
    path: str
    value_kind: str | None
    value: Any | None
    details: dict[str, Any] = field(default_factory=dict)


def _collect_value_mutations(
    *,
    value_change: AttributeValueChange,
    path_prefix: str,
    spec_index: _OcgDescriptorSpecIndex | None,
) -> list[_ValueMutation]:
    out: list[_ValueMutation] = []

    value_kind, value = _extract_value(value_change.change, spec_index=spec_index)
    if value_kind is not None:
        out.append(
            _ValueMutation(
                op=_op(value_change.change.type),
                path=path_prefix,
                value_kind=value_kind,
                value=value,
                details={"attribute_value_id": str(value_change.attribute_value_id)},
            )
        )

    for link_change in value_change.attribute_value_link_changes:
        segment = _link_segment(link_change, fallback=f"<link:{link_change.attribute_value_link_id}>")
        child = link_change.child_attribute_value_change
        if child is None:
            continue

        out.extend(
            _collect_value_mutations(
                value_change=child,
                path_prefix=f"{path_prefix}{segment}",
                spec_index=spec_index,
            )
        )

    return out


def _link_segment(change: AttributeValueLinkChange, *, fallback: str) -> str:
    role = _scalar_str(change.change, "role")
    identity_key = _scalar_str(change.change, "identity_key")
    position = _scalar_int(change.change, "position")

    if identity_key is not None:
        return f"[{identity_key}]"
    if position is not None:
        return f"[{position}]"
    if role is not None:
        return f"[{role}]"
    return f"[{fallback}]"


def _extract_value(
    change: Change, *, spec_index: _OcgDescriptorSpecIndex | None
) -> tuple[str | None, Any | None]:
    primitive = _scalar_any(change, "primitive_value")
    if primitive is not None:
        return "primitive_value", primitive

    enum_option_id = _scalar_uuid(change, "enum_option_id")
    if enum_option_id is not None:
        label = spec_index.enum_label(enum_option_id) if spec_index is not None else None
        return "enum_option_id", label or str(enum_option_id)

    class_instance_id = _scalar_uuid(change, "class_instance_id")
    if class_instance_id is not None:
        return "class_instance_id", str(class_instance_id)

    inline_value_instance_id = _scalar_uuid(change, "inline_value_instance_id")
    if inline_value_instance_id is not None:
        return "inline_value_instance_id", str(inline_value_instance_id)

    return None, None


def _op(change_type: ChangeType) -> Literal["create", "update", "delete"]:
    match change_type:
        case ChangeType.create:
            return "create"
        case ChangeType.update:
            return "update"
        case ChangeType.delete:
            return "delete"
        case _:
            raise ValueError(f"Unsupported ChangeType: {change_type}")


def _scalar_any(change: Change, prop: str) -> Any | None:
    for d in change.change_deltas:
        if d.kind == ChangeDeltaKind.scalar_set and d.property == prop:
            return d.payload.get("value")
    return None


def _scalar_str(change: Change, prop: str) -> str | None:
    value = _scalar_any(change, prop)
    if value is None:
        return None
    return str(value)


def _scalar_int(change: Change, prop: str) -> int | None:
    value = _scalar_any(change, prop)
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _scalar_uuid(change: Change, prop: str) -> UUID | None:
    value = _scalar_any(change, prop)
    if value is None:
        return None
    return UUID(str(value))
