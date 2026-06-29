from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from aware_code.semantic_capability import (
    SemanticCapabilityActionBinding,
    SemanticCapabilityEvent,
    SemanticCapabilityFunctionCallBinding,
    SemanticCapabilityFunctionCallPlan,
)


def build_semantic_function_call_plan_previews(
    *,
    semantic_events: Iterable[object],
    action_bindings: Iterable[object],
) -> tuple[SemanticCapabilityFunctionCallPlan, ...]:
    events_by_key = _events_by_key(semantic_events)
    plans: list[SemanticCapabilityFunctionCallPlan] = []
    for action_binding in action_bindings:
        binding_payload = _action_binding_payload(action_binding)
        if _string_value(binding_payload.get("action_type")) != "function_call":
            continue
        event_key = _string_value(binding_payload.get("event_key"))
        if not event_key:
            continue
        function_call_binding = _function_call_binding_payload(
            binding_payload.get("function_call_binding")
        )
        if function_call_binding is None:
            continue
        for event_payload in events_by_key.get(event_key, ()):
            plans.append(
                _build_function_call_plan(
                    action_binding=binding_payload,
                    function_call_binding=function_call_binding,
                    event=event_payload,
                )
            )
    return tuple(plans)


def _build_function_call_plan(
    *,
    action_binding: Mapping[str, object],
    function_call_binding: Mapping[str, object],
    event: Mapping[str, object],
) -> SemanticCapabilityFunctionCallPlan:
    unresolved_templates: list[dict[str, str]] = []
    constant_arguments = _mapping_value(
        function_call_binding.get("constant_arguments")
    )
    argument_bindings = _string_mapping_value(
        function_call_binding.get("argument_bindings")
    )
    argument_ref_bindings = _string_mapping_value(
        function_call_binding.get("argument_ref_bindings")
    )
    arguments: dict[str, object] = dict(constant_arguments)
    argument_refs: dict[str, str] = {}
    for argument_name, template in sorted(argument_bindings.items()):
        value = _resolve_template(template=template, event=event)
        if value is _MISSING:
            unresolved_templates.append(
                {"target": f"arguments.{argument_name}", "template": template}
            )
            continue
        arguments[argument_name] = value
    for argument_name, template in sorted(argument_ref_bindings.items()):
        value = _resolve_template(template=template, event=event)
        if value is _MISSING:
            unresolved_templates.append(
                {"target": f"argument_refs.{argument_name}", "template": template}
            )
            continue
        argument_refs[argument_name] = str(value)
    receiver_template = _optional_string_value(
        function_call_binding.get("receiver_semantic_key_template")
    )
    receiver_semantic_key = _resolve_optional_template(
        template=receiver_template,
        event=event,
        target="receiver_semantic_key",
        unresolved_templates=unresolved_templates,
    )
    result_template = _optional_string_value(
        function_call_binding.get("result_semantic_key_template")
    )
    result_semantic_key = _resolve_optional_template(
        template=result_template,
        event=event,
        target="result_semantic_key",
        unresolved_templates=unresolved_templates,
    )
    metadata = dict(_mapping_value(function_call_binding.get("metadata")))
    metadata["preview_status"] = (
        "unresolved_templates" if unresolved_templates else "ready"
    )
    metadata["preview_kind"] = "semantic_event_action_policy"
    if unresolved_templates:
        metadata["unresolved_templates"] = tuple(unresolved_templates)
    return SemanticCapabilityFunctionCallPlan(
        function_ref=_string_value(function_call_binding.get("function_ref")),
        binding_key=_optional_string_value(function_call_binding.get("binding_key")),
        action_key=_optional_string_value(action_binding.get("action_key")),
        event_key=_optional_string_value(event.get("event_key")),
        receiver_semantic_key=receiver_semantic_key,
        arguments=arguments,
        argument_refs=argument_refs,
        result_semantic_key=result_semantic_key,
        metadata=metadata,
    )


def _resolve_optional_template(
    *,
    template: str | None,
    event: Mapping[str, object],
    target: str,
    unresolved_templates: list[dict[str, str]],
) -> str | None:
    if template is None:
        return None
    value = _resolve_template(template=template, event=event)
    if value is _MISSING:
        unresolved_templates.append({"target": target, "template": template})
        return None
    return str(value)


class _Missing:
    pass


_MISSING = _Missing()


def _resolve_template(*, template: str, event: Mapping[str, object]) -> object:
    if template == "semantic_key":
        return event.get("semantic_key", _MISSING)
    if template == "event_key":
        return event.get("event_key", _MISSING)
    if template == "source":
        return event.get("source", _MISSING)
    if template.startswith("payload."):
        current: object = event.get("payload", _MISSING)
        for segment in template.removeprefix("payload.").split("."):
            if not segment:
                return _MISSING
            if not isinstance(current, Mapping):
                return _MISSING
            current = current.get(segment, _MISSING)
            if current is _MISSING:
                return _MISSING
        return current
    return _MISSING


def _events_by_key(
    semantic_events: Iterable[object],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    collected: dict[str, list[Mapping[str, object]]] = {}
    for semantic_event in semantic_events:
        event_payload = _event_payload(semantic_event)
        event_key = _string_value(event_payload.get("event_key"))
        if not event_key:
            continue
        collected.setdefault(event_key, []).append(event_payload)
    return {
        event_key: tuple(event_payloads)
        for event_key, event_payloads in sorted(collected.items())
    }


def _event_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, SemanticCapabilityEvent):
        return value.evidence_payload()
    if isinstance(value, Mapping):
        return _mapping_value(value)
    return {}


def _action_binding_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, SemanticCapabilityActionBinding):
        return value.evidence_payload()
    if isinstance(value, Mapping):
        return _mapping_value(value)
    return {}


def _function_call_binding_payload(value: object) -> Mapping[str, object] | None:
    if isinstance(value, SemanticCapabilityFunctionCallBinding):
        return value.evidence_payload()
    if isinstance(value, Mapping):
        return _mapping_value(value)
    return None


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): _json_safe_value(item) for key, item in value.items()}


def _string_mapping_value(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and str(item).strip()
    }


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_string_value(value: object) -> str | None:
    text = _string_value(value)
    return text or None


def _json_safe_value(value: Any) -> object:
    if isinstance(value, Mapping):
        return _mapping_value(value)
    if isinstance(value, (list, tuple)):
        return tuple(_json_safe_value(item) for item in value)
    return value


__all__ = ["build_semantic_function_call_plan_previews"]
