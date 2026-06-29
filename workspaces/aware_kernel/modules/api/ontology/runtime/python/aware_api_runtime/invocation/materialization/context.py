from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID
import os

from aware_meta_ontology.class_.class_config import ClassConfig

if TYPE_CHECKING:
    from aware_api_ontology.api.api_call import ApiCall


@dataclass(frozen=True, slots=True)
class ApiCallMaterializationInput:
    request_payload: Mapping[str, object]
    request_class_config: ClassConfig | None = None
    request_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None


@dataclass(frozen=True, slots=True)
class ApiCallOutcomeMaterializationInput:
    response_payload: Mapping[str, object] | None
    response_class_config: ClassConfig | None = None
    response_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None
    api_call: ApiCall | None = None


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


@contextmanager
def scoped_api_call_materialization_input(
    *,
    request_payload: Mapping[str, object],
    request_class_config: ClassConfig | None = None,
    request_class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> Iterator[None]:
    token = _CURRENT_API_CALL_INPUT.set(
        ApiCallMaterializationInput(
            request_payload=request_payload,
            request_class_config=request_class_config,
            request_class_configs_by_id=request_class_configs_by_id,
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
        }
    container_field_count = 0
    nested_container_count = 0
    for value in payload.values():
        if _is_container_value(value):
            container_field_count += 1
            nested_container_count += _count_container_values(value)
    return {
        "field_count": len(payload),
        "container_field_count": container_field_count,
        "nested_container_count": nested_container_count,
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


def _count_container_values(value: object) -> int:
    if isinstance(value, Mapping):
        return 1 + sum(_count_container_values(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return 1 + sum(_count_container_values(child) for child in value)
    return 0


__all__ = [
    "ApiCallMaterializationInput",
    "ApiCallOutcomeMaterializationInput",
    "api_receipt_payload_summary",
    "current_api_call_materialization_input",
    "current_api_call_outcome_materialization_input",
    "scoped_api_call_materialization_input",
    "scoped_api_call_outcome_materialization_input",
    "should_use_compact_api_receipt_payload",
]
