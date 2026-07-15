from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from aware_meta.class_.inline_value_instance.resolution import (
    resolve_class_config_attribute_configs,
)
from aware_meta_ontology.class_.class_config import ClassConfig


ALLOWED_ACTION_REQUEST_SOURCE_REFS: frozenset[str] = frozenset(
    {
        "event.id",
        "event.config_id",
        "event.activation_id",
        "event.event_type",
        "event.source",
        "event.status",
        "environment.id",
        "commit.branch_id",
        "commit.projection_hash",
        "commit.commit_id",
        "commit.object_instance_graph_id",
        "commit.object_instance_graph_commit_id",
        "intent.id",
        "intent.intent_key",
        "intent.action_config_id",
        "intent.event_config_condition_config_id",
        "intent.action_type",
        "intent.root_object_id",
        "intent.focus_scope_id",
        "intent.focus_id",
        "intent.view_id",
        "intent.interface_id",
        "intent.window_id",
        "intent.window_layout_id",
        "intent.window_section_id",
        "intent.visible_window_section_ids",
        "intent.graph_hash_post",
        "execution.id",
        "execution.key",
        "api_call.key",
        "binding.action_binding_id",
        "binding.action_experience_id",
        "binding.environment_profile_id",
        "binding.environment_event_id",
        "binding.invocation_config_id",
        "binding.endpoint_id",
        "actor.id",
        "subscription.id",
    }
)
_BINDING_NODE_SOURCE_REF_PREFIX = "binding.node."
_BINDING_NODE_SOURCE_REF_SUFFIXES: frozenset[str] = frozenset(
    {
        "class_instance_identity_id",
        "class_config_id",
        "object_id",
    }
)


class ActionRequestCompositionError(ValueError):
    """Raised when declared action request composition cannot fail closed."""


@dataclass(frozen=True, slots=True)
class ActionDispatchRequestFieldBinding:
    request_field_id: UUID | None
    attribute_config_id: UUID | None
    attribute_name: str | None
    source_ref: str
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ActionDispatchBindingNodeSource:
    alias: str
    class_instance_identity_id: UUID | None
    class_config_id: UUID | None
    object_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ActionDispatchCompositionContext:
    event_id: UUID
    event_config_id: UUID | None
    event_activation_id: UUID | None
    event_type: str
    event_source: str
    event_status: str | None
    commit_branch_id: UUID | None
    commit_projection_hash: str | None
    commit_id: UUID | None
    commit_object_instance_graph_id: UUID | None
    commit_object_instance_graph_commit_id: UUID | None
    intent_id: UUID
    intent_key: str
    intent_action_config_id: UUID | None
    execution_id: UUID
    execution_key: str
    api_call_key: UUID
    action_binding_id: UUID
    action_experience_id: UUID | None
    environment_profile_id: UUID | None
    environment_event_id: UUID | None
    invocation_config_id: UUID
    endpoint_id: UUID
    actor_id: UUID | None
    subscription_id: UUID | None
    environment_id: UUID | None = None
    intent_event_config_condition_config_id: UUID | None = None
    intent_action_type: str | None = None
    intent_root_object_id: UUID | None = None
    intent_focus_scope_id: UUID | None = None
    intent_focus_id: UUID | None = None
    intent_view_id: UUID | None = None
    intent_interface_id: UUID | None = None
    intent_window_id: UUID | None = None
    intent_window_layout_id: UUID | None = None
    intent_window_section_id: UUID | None = None
    intent_visible_window_section_ids: tuple[UUID, ...] = ()
    intent_graph_hash_post: str | None = None
    binding_node_sources: Mapping[str, ActionDispatchBindingNodeSource] = (
        MappingProxyType({})
    )


def compose_action_request_payload(
    *,
    request_class_config: ClassConfig | None,
    request_fields: tuple[ActionDispatchRequestFieldBinding, ...],
    context: ActionDispatchCompositionContext,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    precomposed_values_by_attribute_config_id: Mapping[UUID, object] | None = None,
) -> Mapping[str, object]:
    """Project declared dispatch context fields into an endpoint request payload."""

    precomposed_values = dict(precomposed_values_by_attribute_config_id or {})
    if not request_fields and not precomposed_values:
        return MappingProxyType({})
    if request_class_config is None:
        raise ActionRequestCompositionError(
            "action_request_composition_missing_request_class_config"
        )

    links = resolve_class_config_attribute_configs(
        class_config=request_class_config,
        class_configs_by_id=class_configs_by_id,
    )
    request_attributes_by_id = {}
    required_request_attribute_ids: set[UUID] = set()
    for link in links:
        attribute_config = link.attribute_config
        if attribute_config is None or attribute_config.id is None:
            continue
        request_attributes_by_id[attribute_config.id] = attribute_config
        if attribute_config.is_required:
            required_request_attribute_ids.add(attribute_config.id)

    payload: dict[str, object] = {}
    mapped_attribute_ids: set[UUID] = set()
    for attribute_config_id, value in sorted(
        precomposed_values.items(),
        key=lambda item: str(item[0]),
    ):
        attribute_config = request_attributes_by_id.get(attribute_config_id)
        if attribute_config is None:
            raise ActionRequestCompositionError(
                "action_request_composition_precomposed_attribute_not_in_request_class:"
                f"{attribute_config_id}"
            )
        attribute_name = str(attribute_config.name or "").strip()
        if not attribute_name:
            raise ActionRequestCompositionError(
                "action_request_composition_missing_attribute_name"
            )
        if value is None:
            if attribute_config.is_required:
                raise ActionRequestCompositionError(
                    "action_request_composition_precomposed_value_absent:"
                    f"{attribute_name}"
                )
            mapped_attribute_ids.add(attribute_config_id)
            continue
        payload[attribute_name] = value
        mapped_attribute_ids.add(attribute_config_id)

    for field in sorted(
        request_fields,
        key=lambda item: (
            item.position if item.position is not None else 0,
            item.attribute_name or "",
            str(item.attribute_config_id or ""),
        ),
    ):
        source_ref = field.source_ref.strip()
        if not _is_allowed_source_ref(source_ref):
            raise ActionRequestCompositionError(
                f"action_request_composition_source_ref_not_allowed:{source_ref}"
            )
        attribute_config_id = field.attribute_config_id
        if attribute_config_id is None:
            raise ActionRequestCompositionError(
                "action_request_composition_missing_attribute_config_id"
            )
        attribute_config = request_attributes_by_id.get(attribute_config_id)
        if attribute_config is None:
            raise ActionRequestCompositionError(
                "action_request_composition_attribute_not_in_request_class:"
                f"{attribute_config_id}"
            )
        attribute_name = (attribute_config.name or field.attribute_name or "").strip()
        if not attribute_name:
            raise ActionRequestCompositionError(
                "action_request_composition_missing_attribute_name"
            )
        if attribute_config_id in mapped_attribute_ids:
            raise ActionRequestCompositionError(
                "action_request_composition_duplicate_request_attribute:"
                f"{attribute_name}"
            )

        value = _resolve_source_value(context=context, source_ref=source_ref)
        if value is None:
            if field.required or attribute_config.is_required:
                raise ActionRequestCompositionError(
                    "action_request_composition_source_absent:"
                    f"{source_ref}->{attribute_name}"
                )
            mapped_attribute_ids.add(attribute_config_id)
            continue

        payload[attribute_name] = value
        mapped_attribute_ids.add(attribute_config_id)

    missing_required = sorted(
        (
            request_attributes_by_id[attribute_id].name or str(attribute_id)
            for attribute_id in required_request_attribute_ids - mapped_attribute_ids
        )
    )
    if missing_required:
        raise ActionRequestCompositionError(
            "action_request_composition_required_attribute_unmapped:"
            + ",".join(missing_required)
        )
    return MappingProxyType(payload)


def _resolve_source_value(
    *,
    context: ActionDispatchCompositionContext,
    source_ref: str,
) -> object | None:
    binding_node_ref = _parse_binding_node_source_ref(source_ref)
    if binding_node_ref is not None:
        alias, suffix = binding_node_ref
        node_source = context.binding_node_sources.get(alias)
        if node_source is None:
            raise ActionRequestCompositionError(
                "action_request_composition_binding_node_alias_not_declared:" f"{alias}"
            )
        if suffix == "class_instance_identity_id":
            return node_source.class_instance_identity_id
        if suffix == "class_config_id":
            return node_source.class_config_id
        if suffix == "object_id":
            return node_source.object_id
        raise ActionRequestCompositionError(
            f"action_request_composition_source_ref_not_allowed:{source_ref}"
        )

    values: Mapping[str, object | None] = {
        "environment.id": context.environment_id,
        "event.id": context.event_id,
        "event.config_id": context.event_config_id,
        "event.activation_id": context.event_activation_id,
        "event.event_type": context.event_type,
        "event.source": context.event_source,
        "event.status": context.event_status,
        "commit.branch_id": context.commit_branch_id,
        "commit.projection_hash": context.commit_projection_hash,
        "commit.commit_id": context.commit_id,
        "commit.object_instance_graph_id": context.commit_object_instance_graph_id,
        "commit.object_instance_graph_commit_id": (
            context.commit_object_instance_graph_commit_id
        ),
        "intent.id": context.intent_id,
        "intent.intent_key": context.intent_key,
        "intent.action_config_id": context.intent_action_config_id,
        "intent.event_config_condition_config_id": (
            context.intent_event_config_condition_config_id
        ),
        "intent.action_type": context.intent_action_type,
        "intent.root_object_id": context.intent_root_object_id,
        "intent.focus_scope_id": context.intent_focus_scope_id,
        "intent.focus_id": context.intent_focus_id,
        "intent.view_id": context.intent_view_id,
        "intent.interface_id": context.intent_interface_id,
        "intent.window_id": context.intent_window_id,
        "intent.window_layout_id": context.intent_window_layout_id,
        "intent.window_section_id": context.intent_window_section_id,
        "intent.visible_window_section_ids": list(
            context.intent_visible_window_section_ids
        ),
        "intent.graph_hash_post": context.intent_graph_hash_post,
        "execution.id": context.execution_id,
        "execution.key": context.execution_key,
        "api_call.key": context.api_call_key,
        "binding.action_binding_id": context.action_binding_id,
        "binding.action_experience_id": context.action_experience_id,
        "binding.environment_profile_id": context.environment_profile_id,
        "binding.environment_event_id": context.environment_event_id,
        "binding.invocation_config_id": context.invocation_config_id,
        "binding.endpoint_id": context.endpoint_id,
        "actor.id": context.actor_id,
        "subscription.id": context.subscription_id,
    }
    return values[source_ref]


def _is_allowed_source_ref(source_ref: str) -> bool:
    if source_ref in ALLOWED_ACTION_REQUEST_SOURCE_REFS:
        return True
    return _parse_binding_node_source_ref(source_ref) is not None


def _parse_binding_node_source_ref(source_ref: str) -> tuple[str, str] | None:
    if not source_ref.startswith(_BINDING_NODE_SOURCE_REF_PREFIX):
        return None
    body = source_ref.removeprefix(_BINDING_NODE_SOURCE_REF_PREFIX)
    alias, separator, suffix = body.rpartition(".")
    if not separator or not alias or not suffix:
        return None
    if suffix not in _BINDING_NODE_SOURCE_REF_SUFFIXES:
        return None
    return alias, suffix
