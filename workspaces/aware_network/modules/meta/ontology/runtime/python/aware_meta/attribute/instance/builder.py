from collections.abc import Mapping
from typing import Any
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue

from aware_meta.attribute.instance.value.builder import (
    ClassInstanceResolver,
    EnumOptionResolver,
    UnionSelection,
    AttributeValueBuildError,
    build_attribute_value_tree,
)
from aware_meta.attribute.instance.value.validator import (
    validate_attribute_value_tree_with_context,
)
from aware_meta.attribute.instance.value.stable_ids import stable_attribute_value_id
from aware_meta.graph.config.stable_ids import stable_attribute_id

from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


class AttributeBuildError(ValueError):
    pass


def build_attribute(
    *,
    owner_key: UUID,
    attribute_config: AttributeConfig,
    value: Any,
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union: UnionSelection | None = None,
) -> Attribute:
    """
    Build a canonical instance Attribute for an owner-scoped structural rail.

    This builder is *build-only*: it does not compute diffs/changes.

    Invariants:
    - The Attribute's value is represented via a descriptor-driven `AttributeValue` tree (`value_root`).
    - The value tree MUST align with `attribute_config.type_descriptor`.
    - Stable identity is derived from `(owner_key, attribute_config_id)`.
    - Topology/containment is carried by owner-specific edge rails, not by `Attribute` itself.
    """
    try:
        # Stable identity contract:
        # - Attribute.id is derived from (owner_key, attribute_config_id)
        # - AttributeValue tree ids are derived from the Attribute.id + slot keys
        #
        # This is required so compiler-driven commits can be applied deterministically across
        # rebuilds (no random UUID drift in the base snapshot).
        if attribute_config.id is None:
            raise AttributeBuildError("AttributeConfig.id is required to build a stable Attribute instance id")

        # Root value id is derived from the attribute identity using the canonical
        # child-id formula with a fixed root slot contract.
        attribute_id = stable_attribute_id(owner_key=owner_key, attribute_config_id=attribute_config.id)
        value_root_id = stable_attribute_value_id(
            parent_value_id=attribute_id,
            role="member",
            position=0,
            identity_key="root",
        )
        value_root = build_attribute_value_tree(
            type_descriptor=attribute_config.type_descriptor,
            value=value,
            validate_tree=False,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union=union,
            stable_root_id=value_root_id,
        )
        _materialize_inline_value_instances(
            node=value_root,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
        )
        validate_attribute_value_tree_with_context(
            value_root,
            class_configs_by_id=class_configs_by_id,
        )
    except AttributeValueBuildError as exc:
        raise AttributeBuildError(f"Failed to build AttributeValue tree for {attribute_config.name!r}: {exc}") from exc

    # Canonical instance attributes are pure in-memory artifacts; avoid implicit
    # session binding side effects and change-tracking hook churn.
    with disable_change_tracking_hooks():
        with disable_autobind():
            return Attribute(
                id=attribute_id,
                owner_key=owner_key,
                attribute_config=attribute_config,
                attribute_config_id=attribute_config.id,
                value_root=value_root,
                value_root_id=value_root.id,
            )


def _materialize_inline_value_instances(
    *,
    node: AttributeValue,
    class_configs_by_id: dict[UUID, ClassConfig] | None,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
) -> None:
    type_descriptor = node.type_descriptor
    if type_descriptor is None:
        return

    if type_descriptor.kind == Kind.class_:
        class_config = _resolve_class_config_for_descriptor(
            type_descriptor=type_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        if class_config is None:
            return
        if class_config.value_mode == ClassValueMode.inline_value:
            payload = _unwrap_inline_payload(node.primitive_value)
            if payload is None:
                return
            if not isinstance(payload, Mapping):
                raise AttributeBuildError(
                    "Inline-value class payload must be object-like mapping for InlineValueInstance lowering: "
                    f"class_config_id={class_config.id} payload_type={type(payload).__name__}"
                )
            if node.id is None:
                raise AttributeBuildError(
                    "Inline-value class payload requires stable AttributeValue.id before lowering."
                )
            from aware_meta.class_.inline_value_instance.builder import (
                build_inline_value_instance_from_mapping,
            )

            inline_value_instance = build_inline_value_instance_from_mapping(
                owner_key=node.id,
                class_config=class_config,
                values={str(k): v for k, v in payload.items()},
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
            )
            node.inline_value_instance = inline_value_instance
            node.inline_value_instance_id = inline_value_instance.id
            node.primitive_value = None
            node.class_instance = None
            node.class_instance_id = None
            return

    for link in list(node.child_links or []):
        child = link.child
        if child is None:
            raise AttributeBuildError("AttributeValueLink missing child during inline-value lowering")
        _materialize_inline_value_instances(
            node=child,
            class_configs_by_id=class_configs_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
        )


def _unwrap_inline_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict) and set(value.keys()) == {"value"}:
        return value.get("value")
    return value


def _resolve_class_config_for_descriptor(
    *,
    type_descriptor: Any,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> ClassConfig | None:
    if class_configs_by_id is not None and type_descriptor.class_config_id is not None:
        resolved = class_configs_by_id.get(type_descriptor.class_config_id)
        if resolved is not None:
            return resolved
    return type_descriptor.class_config


__all__ = [
    "AttributeBuildError",
    "build_attribute",
]
