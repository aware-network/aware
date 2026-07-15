from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID
import os

from aware_meta_ontology.class_.class_config import ClassConfig


_DEFAULT_API_RECEIPT_PAYLOAD_SUMMARY_CONTAINER_BUDGET = 256

if TYPE_CHECKING:
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )


@dataclass(frozen=True, slots=True)
class ApiCallMaterializationInput:
    request_payload: Mapping[str, object]
    request_class_config: ClassConfig | None = None
    request_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None
    request_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ApiCallOutcomeMaterializationInput:
    response_payload: Mapping[str, object] | None
    response_class_config: ClassConfig | None = None
    response_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None
    api_call: ApiCall | None = None


@dataclass(frozen=True, slots=True)
class ApiCallStreamEventMaterializationInput:
    event_values: Mapping[str, object] | None
    event_class_config: ClassConfig | None = None
    event_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None
    api_call: ApiCall | None = None
    api_capability_endpoint: ApiCapabilityEndpoint | None = None
    stream_event_config: ApiCapabilityEndpointStreamEventConfig | None = None


_CURRENT_API_CALL_INPUT: ContextVar[ApiCallMaterializationInput | None] = ContextVar(
    "aware_api_call_materialization_input",
    default=None,
)
_CURRENT_API_CALL_OUTCOME_INPUT: ContextVar[
    ApiCallOutcomeMaterializationInput | None
] = ContextVar(
    "aware_api_call_outcome_materialization_input",
    default=None,
)
_CURRENT_API_CALL_STREAM_EVENT_INPUT: ContextVar[
    ApiCallStreamEventMaterializationInput | None
] = ContextVar(
    "aware_api_call_stream_event_materialization_input",
    default=None,
)


@contextmanager
def scoped_api_call_materialization_input(
    *,
    request_payload: Mapping[str, object],
    request_class_config: ClassConfig | None = None,
    request_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    request_hash: str | None = None,
) -> Iterator[None]:
    token = _CURRENT_API_CALL_INPUT.set(
        ApiCallMaterializationInput(
            request_payload=request_payload,
            request_class_config=request_class_config,
            request_class_configs_by_id=request_class_configs_by_id,
            request_hash=request_hash,
        )
    )
    try:
        yield
    finally:
        _CURRENT_API_CALL_INPUT.reset(token)


def current_api_call_materialization_input() -> ApiCallMaterializationInput | None:
    return _CURRENT_API_CALL_INPUT.get()


@contextmanager
def scoped_api_call_outcome_materialization_input(
    *,
    response_payload: Mapping[str, object] | None,
    response_class_config: ClassConfig | None = None,
    response_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    api_call: ApiCall | None = None,
) -> Iterator[None]:
    token = _CURRENT_API_CALL_OUTCOME_INPUT.set(
        ApiCallOutcomeMaterializationInput(
            response_payload=response_payload,
            response_class_config=response_class_config,
            response_class_configs_by_id=response_class_configs_by_id,
            api_call=api_call,
        )
    )
    try:
        yield
    finally:
        _CURRENT_API_CALL_OUTCOME_INPUT.reset(token)


def current_api_call_outcome_materialization_input() -> (
    ApiCallOutcomeMaterializationInput | None
):
    return _CURRENT_API_CALL_OUTCOME_INPUT.get()


@contextmanager
def scoped_api_call_stream_event_materialization_input(
    *,
    event_values: Mapping[str, object] | None,
    event_class_config: ClassConfig | None = None,
    event_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    api_call: ApiCall | None = None,
    api_capability_endpoint: ApiCapabilityEndpoint | None = None,
    stream_event_config: ApiCapabilityEndpointStreamEventConfig | None = None,
) -> Iterator[None]:
    token = _CURRENT_API_CALL_STREAM_EVENT_INPUT.set(
        ApiCallStreamEventMaterializationInput(
            event_values=event_values,
            event_class_config=event_class_config,
            event_class_configs_by_id=event_class_configs_by_id,
            api_call=api_call,
            api_capability_endpoint=api_capability_endpoint,
            stream_event_config=stream_event_config,
        )
    )
    try:
        yield
    finally:
        _CURRENT_API_CALL_STREAM_EVENT_INPUT.reset(token)


def current_api_call_stream_event_materialization_input() -> (
    ApiCallStreamEventMaterializationInput | None
):
    return _CURRENT_API_CALL_STREAM_EVENT_INPUT.get()


def should_use_compact_api_receipt_payload(
    *,
    payload: Mapping[str, object] | None,
    commit: bool,
    receipt_projection_backend: str | None = None,
) -> bool:
    if not commit or not payload:
        return False

    mode = _api_receipt_payload_mode()
    if mode in {"full", "off", "disabled"}:
        return False
    if mode in {"compact", "on", "always"}:
        return True

    if _receipt_projection_backend_name(receipt_projection_backend) == "db":
        return False
    return _payload_has_container_value(payload)


def api_receipt_payload_summary(
    payload: Mapping[str, object] | None,
) -> Mapping[str, int]:
    if not payload:
        return {
            "field_count": 0,
            "container_field_count": 0,
            "nested_container_count": 0,
            "nested_container_count_truncated": 0,
        }
    container_field_count = 0
    nested_container_count = 0
    budget = _api_receipt_payload_summary_container_budget()
    for value in payload.values():
        if _is_container_value(value):
            container_field_count += 1
            counted, budget = _count_container_values(
                value=value,
                remaining_budget=budget,
            )
            nested_container_count += counted
            if budget <= 0:
                break
    return {
        "field_count": len(payload),
        "container_field_count": container_field_count,
        "nested_container_count": nested_container_count,
        "nested_container_count_truncated": int(budget <= 0),
    }


def _api_receipt_payload_mode() -> str:
    return (
        (
            os.getenv("AWARE_API_RECEIPT_PAYLOAD_MODE")
            or os.getenv("AWARE_API_RECEIPT_PAYLOAD_POLICY")
            or "auto"
        )
        .strip()
        .lower()
    )


def _receipt_projection_backend_name(receipt_projection_backend: str | None) -> str:
    backend = (
        receipt_projection_backend
        if receipt_projection_backend is not None
        else os.getenv("AWARE_PERSISTENCE_BACKEND")
    )
    return (backend or "").strip().lower()


def _payload_has_container_value(payload: Mapping[str, object]) -> bool:
    return any(_is_container_value(value) for value in payload.values())


def _is_container_value(value: object) -> bool:
    if isinstance(value, Mapping):
        return True
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return True
    return False


def _api_receipt_payload_summary_container_budget() -> int:
    raw_value = (os.getenv("AWARE_API_RECEIPT_PAYLOAD_SUMMARY_BUDGET") or "").strip()
    if not raw_value:
        return _DEFAULT_API_RECEIPT_PAYLOAD_SUMMARY_CONTAINER_BUDGET
    try:
        budget = int(raw_value)
    except ValueError:
        return _DEFAULT_API_RECEIPT_PAYLOAD_SUMMARY_CONTAINER_BUDGET
    return max(1, budget)


def _count_container_values(
    *,
    value: object,
    remaining_budget: int,
) -> tuple[int, int]:
    if remaining_budget <= 0:
        return 0, 0
    if isinstance(value, Mapping):
        count = 1
        remaining_budget -= 1
        for child in value.values():
            child_count, remaining_budget = _count_container_values(
                value=child,
                remaining_budget=remaining_budget,
            )
            count += child_count
            if remaining_budget <= 0:
                break
        return count, remaining_budget
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        count = 1
        remaining_budget -= 1
        for child in value:
            child_count, remaining_budget = _count_container_values(
                value=child,
                remaining_budget=remaining_budget,
            )
            count += child_count
            if remaining_budget <= 0:
                break
        return count, remaining_budget
    return 0, remaining_budget


__all__ = [
    "ApiCallMaterializationInput",
    "ApiCallOutcomeMaterializationInput",
    "ApiCallStreamEventMaterializationInput",
    "api_receipt_payload_summary",
    "current_api_call_materialization_input",
    "current_api_call_outcome_materialization_input",
    "current_api_call_stream_event_materialization_input",
    "scoped_api_call_materialization_input",
    "scoped_api_call_outcome_materialization_input",
    "scoped_api_call_stream_event_materialization_input",
    "should_use_compact_api_receipt_payload",
]
