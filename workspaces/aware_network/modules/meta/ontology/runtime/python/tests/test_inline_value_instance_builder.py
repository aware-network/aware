from __future__ import annotations

from uuid import uuid4

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode

from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.class_.inline_value_instance import (
    resolve_inline_value_instance_attributes,
)
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)


def test_build_inline_value_instance_from_mapping_builds_attribute_edges() -> None:
    payload_cc = ClassConfig(
        name="Payload",
        class_fqn="aware_test_meta.Payload",
        value_mode=ClassValueMode.inline_value,
    )
    label_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    label_cfg = AttributeConfig(
        owner_key=payload_cc.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=label_desc,
        type_descriptor_id=label_desc.id,
    )
    payload_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=payload_cc.id,
            attribute_config=label_cfg,
            attribute_config_id=label_cfg.id,
            name=label_cfg.name,
            position=0,
        )
    ]

    owner_key = uuid4()
    instance = build_inline_value_instance_from_mapping(
        owner_key=owner_key,
        class_config=payload_cc,
        values={"label": "front-door"},
        class_configs_by_id={payload_cc.id: payload_cc},
    )

    assert instance.owner_key == owner_key
    assert len(instance.inline_value_instance_attributes) == 1
    attribute = instance.inline_value_instance_attributes[0].attribute
    assert attribute is not None
    assert attribute.attribute_config_id == label_cfg.id
    assert attribute.value_root.primitive_value == {"value": "front-door"}


def test_build_inline_value_instance_from_mapping_includes_parent_class_id_attributes() -> (
    None
):
    base_cc = ClassConfig(
        name="ConversationServiceRequest",
        class_fqn="aware_test_meta.ConversationServiceRequest",
        value_mode=ClassValueMode.inline_value,
    )
    child_cc = ClassConfig(
        name="CreateConversationSpaceRequest",
        class_fqn="aware_test_meta.CreateConversationSpaceRequest",
        value_mode=ClassValueMode.inline_value,
        parent_class_id=base_cc.id,
    )

    base_operation_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    base_operation_cfg = AttributeConfig(
        owner_key=base_cc.class_fqn,
        name="operation",
        is_required=True,
        type_descriptor=base_operation_desc,
        type_descriptor_id=base_operation_desc.id,
    )
    request_id_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    request_id_cfg = AttributeConfig(
        owner_key=base_cc.class_fqn,
        name="request_id",
        type_descriptor=request_id_desc,
        type_descriptor_id=request_id_desc.id,
    )
    child_operation_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_operation_cfg = AttributeConfig(
        owner_key=child_cc.class_fqn,
        name="operation",
        is_required=True,
        type_descriptor=child_operation_desc,
        type_descriptor_id=child_operation_desc.id,
    )
    title_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    title_cfg = AttributeConfig(
        owner_key=child_cc.class_fqn,
        name="title",
        type_descriptor=title_desc,
        type_descriptor_id=title_desc.id,
    )
    base_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=base_cc.id,
            attribute_config=base_operation_cfg,
            attribute_config_id=base_operation_cfg.id,
            name=base_operation_cfg.name,
            position=0,
        ),
        ClassConfigAttributeConfig(
            class_config_id=base_cc.id,
            attribute_config=request_id_cfg,
            attribute_config_id=request_id_cfg.id,
            name=request_id_cfg.name,
            position=1,
        ),
    ]
    child_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=child_cc.id,
            attribute_config=child_operation_cfg,
            attribute_config_id=child_operation_cfg.id,
            name=child_operation_cfg.name,
            position=0,
        ),
        ClassConfigAttributeConfig(
            class_config_id=child_cc.id,
            attribute_config=title_cfg,
            attribute_config_id=title_cfg.id,
            name=title_cfg.name,
            position=1,
        ),
    ]

    request_id = uuid4()
    instance = build_inline_value_instance_from_mapping(
        owner_key=uuid4(),
        class_config=child_cc,
        values={
            "operation": "create_conversation_space",
            "request_id": request_id,
            "title": "Conversation local dogfood",
        },
        class_configs_by_id={base_cc.id: base_cc, child_cc.id: child_cc},
    )

    resolved = resolve_inline_value_instance_attributes(
        inline_value_instance=instance,
        class_config=child_cc,
        class_configs_by_id={base_cc.id: base_cc, child_cc.id: child_cc},
    )

    assert [item.attribute_config.name for item in resolved] == [
        "operation",
        "request_id",
        "title",
    ]
    assert resolved[0].attribute_config.id == child_operation_cfg.id
    assert resolved[1].attribute.value_root.primitive_value == {
        "value": str(request_id)
    }


def test_build_attribute_lowers_inline_value_leaf_to_nested_instance() -> None:
    payload_cc = ClassConfig(
        name="Payload",
        class_fqn="aware_test_meta.Payload",
        value_mode=ClassValueMode.inline_value,
    )
    label_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    label_cfg = AttributeConfig(
        owner_key=payload_cc.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=label_desc,
        type_descriptor_id=label_desc.id,
    )
    payload_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=payload_cc.id,
            attribute_config=label_cfg,
            attribute_config_id=label_cfg.id,
            name=label_cfg.name,
            position=0,
        )
    ]

    holder_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=payload_cc.id,
        class_config=payload_cc,
    )
    holder_cfg = AttributeConfig(
        owner_key="aware_test_meta.Holder",
        name="payload",
        is_required=True,
        type_descriptor=holder_desc,
        type_descriptor_id=holder_desc.id,
    )

    owner_key = uuid4()
    attribute = build_attribute(
        owner_key=owner_key,
        attribute_config=holder_cfg,
        value={"label": "front-door"},
        class_configs_by_id={payload_cc.id: payload_cc},
    )

    value_root = attribute.value_root
    assert value_root.inline_value_instance is not None
    assert value_root.inline_value_instance_id == value_root.inline_value_instance.id
    assert value_root.primitive_value is None
    nested_attribute = (
        value_root.inline_value_instance.inline_value_instance_attributes[0].attribute
    )
    assert nested_attribute is not None
    assert nested_attribute.value_root.primitive_value == {"value": "front-door"}


def test_build_attribute_prefers_context_class_config_for_inline_value_descriptor() -> (
    None
):
    payload_cc_id = uuid4()
    payload_cc = ClassConfig(
        id=payload_cc_id,
        name="Payload",
        class_fqn="aware_test_meta.Payload",
        value_mode=ClassValueMode.inline_value,
    )
    stale_embedded_cc = ClassConfig(
        id=payload_cc_id,
        name="Payload",
        class_fqn="aware_test_meta.Payload",
        value_mode=ClassValueMode.graph_ref,
    )
    label_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    label_cfg = AttributeConfig(
        owner_key=payload_cc.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=label_desc,
        type_descriptor_id=label_desc.id,
    )
    payload_cc.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=payload_cc.id,
            attribute_config=label_cfg,
            attribute_config_id=label_cfg.id,
            name=label_cfg.name,
            position=0,
        )
    ]
    holder_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=payload_cc.id,
        class_config=stale_embedded_cc,
    )
    holder_cfg = AttributeConfig(
        owner_key="aware_test_meta.Holder",
        name="payload",
        is_required=True,
        type_descriptor=holder_desc,
        type_descriptor_id=holder_desc.id,
    )

    attribute = build_attribute(
        owner_key=uuid4(),
        attribute_config=holder_cfg,
        value={"label": "front-door"},
        class_configs_by_id={payload_cc.id: payload_cc},
    )

    value_root = attribute.value_root
    assert value_root.inline_value_instance is not None
    nested_attribute = (
        value_root.inline_value_instance.inline_value_instance_attributes[0].attribute
    )
    assert nested_attribute is not None
    assert nested_attribute.value_root.primitive_value == {"value": "front-door"}
