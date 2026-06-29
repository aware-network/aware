from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from aware_meta.graph.instance.change.ocg_descriptor_spec import (
    OcgAttributeDescriptorSpec,
    OcgAttributeTypeDescriptorKind,
    OcgAttributeTypeDescriptorSpec,
    OcgBaseType,
    OcgClassDescriptorSpec,
    OcgCodePrimitiveType,
    OcgDescriptorSpec,
    OcgPrimitiveDescriptorSpec,
)
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_code.types import Json
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)

from aware_meta.graph.instance.change.descriptor import describe_oig_changes
from aware_meta.graph.instance.change.narrator import narrate_change_descriptors
from aware_meta.graph.instance.change.semantics import build_change_semantics_payload


def _change(*, key: str, created_at: datetime) -> Change:
    return Change(
        key=key, type=ChangeType.update, change_deltas=[], created_at=created_at
    )


def test_describe_oig_changes_narrates_scalar_attribute_update() -> None:
    created_at = datetime.now(timezone.utc)
    task_class_config_id = uuid4()
    status_attribute_config_id = uuid4()

    status_type = OcgAttributeTypeDescriptorSpec(
        attribute_type_descriptor_id=uuid4(),
        kind=OcgAttributeTypeDescriptorKind.PRIMITIVE,
        primitive_spec=OcgPrimitiveDescriptorSpec(
            primitive_config_id=uuid4(),
            primitive_type=OcgCodePrimitiveType(
                base_type=OcgBaseType.STRING
            ),
        ),
        attribute_type_descriptor_link_child_list=[],
        is_nullable=False,
    )
    spec = OcgDescriptorSpec(
        classes=[
            OcgClassDescriptorSpec(
                class_config_id=task_class_config_id,
                name="Task",
                is_base=False,
                attributes=[
                    OcgAttributeDescriptorSpec(
                        attribute_config_id=status_attribute_config_id,
                        name="status",
                        required=True,
                        type_descriptor=status_type,
                    )
                ],
                functions=[],
            )
        ]
    )

    instance_id = uuid4()

    ci_change = _change(key="ci", created_at=created_at)
    ci_change.change_deltas = [
        ChangeDelta(
            change_id=ci_change.id,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=Json({"value": str(task_class_config_id)}),
        )
    ]
    ci = ClassInstanceChange(
        class_instance_id=instance_id,
        change=ci_change,
        change_id=ci_change.id,
        attribute_changes=[],
    )

    attr_change = _change(key="attr", created_at=created_at)
    attr_change.change_deltas = [
        ChangeDelta(
            change_id=attr_change.id,
            position=0,
            property="attribute_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=Json({"value": str(status_attribute_config_id)}),
        )
    ]

    value_change = _change(key="value", created_at=created_at)
    value_change.change_deltas = [
        ChangeDelta(
            change_id=value_change.id,
            position=0,
            property="primitive_value",
            kind=ChangeDeltaKind.scalar_set,
            payload=Json({"value": "done"}),
        )
    ]
    value_root_change = AttributeValueChange(
        attribute_value_id=uuid4(),
        change=value_change,
        change_id=value_change.id,
        attribute_value_link_changes=[],
    )

    attr = AttributeChange(
        attribute_id=uuid4(),
        class_instance_change_id=ci.id,
        change=attr_change,
        change_id=attr_change.id,
        value_root_change=value_root_change,
        value_root_change_id=value_root_change.id,
    )
    ci.attribute_changes.append(attr)

    root_change = _change(key="root", created_at=created_at)
    oigi_id = uuid4()
    tree = ObjectInstanceGraphChange(
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=uuid4(),
        type=ObjectInstanceGraphChangeType.object_instance,
        change=root_change,
        change_id=root_change.id,
        class_instance_changes=[ci],
        class_instance_relationship_changes=[],
    )

    payload = [tree.model_dump(mode="json", exclude_none=True)]

    descriptors = describe_oig_changes(changes_payload=payload, ocg_descriptor_spec=spec)
    lines = narrate_change_descriptors(descriptors)

    assert lines == ['Task.status = "done"']

    semantics = build_change_semantics_payload(
        changes=[tree],
        ocg_descriptor_spec=spec,
        include_descriptors=True,
    )
    assert semantics["descriptor_count"] == 1
    assert semantics["descriptor_kind_counts"] == {"attribute_value": 1}
    assert semantics["descriptor_op_counts"] == {"update": 1}
    assert semantics["narration_lines"] == ['Task.status = "done"']
    descriptors_payload = semantics["descriptors"]
    assert isinstance(descriptors_payload, list)
    assert len(descriptors_payload) == 1
