from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from aware_experience.action_dispatch.composer import (
    ALLOWED_ACTION_REQUEST_SOURCE_REFS,
    ActionDispatchBindingNodeSource,
    ActionDispatchCompositionContext,
    ActionDispatchRequestFieldBinding,
    ActionRequestCompositionError,
    compose_action_request_payload,
)
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


def _primitive_attribute(
    *,
    owner_key: str,
    name: str,
    is_required: bool = True,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
    )
    return AttributeConfig(
        owner_key=owner_key,
        name=name,
        is_required=is_required,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _request_class(
    *attribute_names: str,
    optional_attribute_names: tuple[str, ...] = (),
) -> tuple[ClassConfig, dict[str, AttributeConfig]]:
    class_config = ClassConfig(
        name="RememberEventRequest",
        class_fqn="aware_test.memory.RememberEventRequest",
        value_mode=ClassValueMode.inline_value,
    )
    attributes: dict[str, AttributeConfig] = {}
    for position, name in enumerate(attribute_names):
        attribute = _primitive_attribute(
            owner_key=class_config.class_fqn,
            name=name,
            is_required=name not in optional_attribute_names,
        )
        attributes[name] = attribute
        class_config.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=class_config.id,
                attribute_config=attribute,
                attribute_config_id=attribute.id,
                position=position,
            )
        )
    return class_config, attributes


def _context() -> ActionDispatchCompositionContext:
    return ActionDispatchCompositionContext(
        event_id=uuid4(),
        event_config_id=uuid4(),
        event_activation_id=uuid4(),
        event_type="memory.event.remember_requested",
        event_source="reactivity.policy",
        event_status="requested",
        commit_branch_id=uuid4(),
        commit_projection_hash="sha256:commit",
        commit_id=uuid4(),
        commit_object_instance_graph_id=uuid4(),
        commit_object_instance_graph_commit_id=uuid4(),
        intent_id=uuid4(),
        intent_key="subscription:memory.remember_event",
        intent_action_config_id=uuid4(),
        execution_id=uuid4(),
        execution_key="primary",
        api_call_key=uuid4(),
        action_binding_id=uuid4(),
        action_experience_id=uuid4(),
        environment_profile_id=uuid4(),
        environment_event_id=uuid4(),
        invocation_config_id=uuid4(),
        endpoint_id=uuid4(),
        actor_id=uuid4(),
        subscription_id=uuid4(),
    )


def _field(
    *,
    attribute: AttributeConfig,
    source_ref: str,
    required: bool = True,
    position: int = 0,
) -> ActionDispatchRequestFieldBinding:
    return ActionDispatchRequestFieldBinding(
        request_field_id=uuid4(),
        attribute_config_id=attribute.id,
        attribute_name=attribute.name,
        source_ref=source_ref,
        required=required,
        position=position,
    )


def test_action_request_composition_whitelist_is_context_only() -> None:
    assert "commit.commit_id" in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "source_commit.commit_id" not in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "event.payload.message" not in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "intent.action_payload.message" not in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "api_call.key" in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "environment.id" in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "intent.action_type" in ALLOWED_ACTION_REQUEST_SOURCE_REFS
    assert "binding.node.front_door.class_instance_identity_id" not in (
        ALLOWED_ACTION_REQUEST_SOURCE_REFS
    )


def test_compose_action_request_payload_maps_environment_and_intent_context() -> None:
    request_class, attributes = _request_class(
        "environment_id",
        "action_type",
        "visible_window_section_ids",
    )
    environment_id = uuid4()
    visible_window_section_ids = (uuid4(), uuid4())
    context = replace(
        _context(),
        environment_id=environment_id,
        intent_action_type="agent.turn.execute",
        intent_visible_window_section_ids=visible_window_section_ids,
    )

    payload = compose_action_request_payload(
        request_class_config=request_class,
        request_fields=(
            _field(
                attribute=attributes["environment_id"],
                source_ref="environment.id",
            ),
            _field(
                attribute=attributes["action_type"],
                source_ref="intent.action_type",
            ),
            _field(
                attribute=attributes["visible_window_section_ids"],
                source_ref="intent.visible_window_section_ids",
            ),
        ),
        context=context,
    )

    assert payload == {
        "environment_id": environment_id,
        "action_type": "agent.turn.execute",
        "visible_window_section_ids": list(visible_window_section_ids),
    }


def test_compose_action_request_payload_maps_declared_context_fields() -> None:
    request_class, attributes = _request_class(
        "event_id",
        "commit_id",
        "intent_key",
        "action_execution_id",
        "api_call_key",
        "subscription_id",
    )
    context = _context()

    payload = compose_action_request_payload(
        request_class_config=request_class,
        request_fields=(
            _field(attribute=attributes["event_id"], source_ref="event.id"),
            _field(attribute=attributes["commit_id"], source_ref="commit.commit_id"),
            _field(
                attribute=attributes["intent_key"],
                source_ref="intent.intent_key",
            ),
            _field(
                attribute=attributes["action_execution_id"],
                source_ref="execution.id",
            ),
            _field(attribute=attributes["api_call_key"], source_ref="api_call.key"),
            _field(
                attribute=attributes["subscription_id"],
                source_ref="subscription.id",
            ),
        ),
        context=context,
    )

    assert payload == {
        "event_id": context.event_id,
        "commit_id": context.commit_id,
        "intent_key": context.intent_key,
        "action_execution_id": context.execution_id,
        "api_call_key": context.api_call_key,
        "subscription_id": context.subscription_id,
    }


def test_compose_action_request_payload_merges_relational_precomposed_values() -> None:
    request_class, attributes = _request_class("event_id", "remembered_item_id")
    context = _context()
    remembered_item_id = uuid4()

    payload = compose_action_request_payload(
        request_class_config=request_class,
        request_fields=(
            _field(attribute=attributes["event_id"], source_ref="event.id"),
        ),
        context=context,
        precomposed_values_by_attribute_config_id={
            attributes["remembered_item_id"].id: remembered_item_id,
        },
    )

    assert payload == {
        "event_id": context.event_id,
        "remembered_item_id": remembered_item_id,
    }


def test_compose_action_request_payload_rejects_precomposed_field_overlap() -> None:
    request_class, attributes = _request_class("event_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="action_request_composition_duplicate_request_attribute:event_id",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(attribute=attributes["event_id"], source_ref="event.id"),
            ),
            context=_context(),
            precomposed_values_by_attribute_config_id={
                attributes["event_id"].id: uuid4(),
            },
        )


def test_compose_action_request_payload_rejects_intent_action_payload_source() -> None:
    request_class, attributes = _request_class("provider_key")

    with pytest.raises(
        ActionRequestCompositionError,
        match="source_ref_not_allowed:intent.action_payload.provider_key",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=attributes["provider_key"],
                    source_ref="intent.action_payload.provider_key",
                ),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_maps_binding_node_target_fields() -> None:
    request_class, attributes = _request_class(
        "target_class_instance_identity_id",
        "target_class_config_id",
        "target_object_id",
    )
    class_instance_identity_id = uuid4()
    class_config_id = uuid4()
    object_id = uuid4()
    context = replace(
        _context(),
        binding_node_sources={
            "front_door": ActionDispatchBindingNodeSource(
                alias="front_door",
                class_instance_identity_id=class_instance_identity_id,
                class_config_id=class_config_id,
                object_id=object_id,
            )
        },
    )

    payload = compose_action_request_payload(
        request_class_config=request_class,
        request_fields=(
            _field(
                attribute=attributes["target_class_instance_identity_id"],
                source_ref="binding.node.front_door.class_instance_identity_id",
            ),
            _field(
                attribute=attributes["target_class_config_id"],
                source_ref="binding.node.front_door.class_config_id",
            ),
            _field(
                attribute=attributes["target_object_id"],
                source_ref="binding.node.front_door.object_id",
            ),
        ),
        context=context,
    )

    assert payload == {
        "target_class_instance_identity_id": class_instance_identity_id,
        "target_class_config_id": class_config_id,
        "target_object_id": object_id,
    }


def test_compose_action_request_payload_rejects_undeclared_binding_node_alias() -> None:
    request_class, attributes = _request_class("target_class_instance_identity_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="binding_node_alias_not_declared:garage_door",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=attributes["target_class_instance_identity_id"],
                    source_ref=("binding.node.garage_door.class_instance_identity_id"),
                ),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_rejects_unsupported_binding_node_suffix() -> (
    None
):
    request_class, attributes = _request_class("target_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="source_ref_not_allowed",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=attributes["target_id"],
                    source_ref="binding.node.front_door.runtime_id",
                ),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_rejects_unknown_context_source() -> None:
    request_class, attributes = _request_class("event_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="source_ref_not_allowed",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=attributes["event_id"],
                    source_ref="event.payload.event_id",
                ),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_rejects_attribute_outside_request_class() -> (
    None
):
    request_class, _ = _request_class("event_id")
    _, foreign_attributes = _request_class("foreign_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="attribute_not_in_request_class",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=foreign_attributes["foreign_id"],
                    source_ref="event.id",
                ),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_rejects_unmapped_required_attribute() -> None:
    request_class, attributes = _request_class("event_id", "commit_id")

    with pytest.raises(
        ActionRequestCompositionError,
        match="required_attribute_unmapped:commit_id",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(attribute=attributes["event_id"], source_ref="event.id"),
            ),
            context=_context(),
        )


def test_compose_action_request_payload_rejects_absent_required_context_source() -> (
    None
):
    request_class, attributes = _request_class("event_status")
    context = replace(_context(), event_status=None)

    with pytest.raises(
        ActionRequestCompositionError,
        match="source_absent:event.status->event_status",
    ):
        compose_action_request_payload(
            request_class_config=request_class,
            request_fields=(
                _field(
                    attribute=attributes["event_status"],
                    source_ref="event.status",
                ),
            ),
            context=context,
        )
