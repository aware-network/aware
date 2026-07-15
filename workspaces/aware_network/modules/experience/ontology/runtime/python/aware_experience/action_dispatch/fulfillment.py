from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class ActionTerminalFulfillmentError(RuntimeError):
    """Terminal action fulfillment did not return the selected API receipt."""


class ActionTerminalFulfillmentInvoker(Protocol):
    async def invoke_action_endpoint(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_values: Mapping[str, object],
        api_call_key: UUID,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class ActionDispatchTerminalOutcome:
    status: str
    endpoint_ref: str
    discriminant: str
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    api_call_key: UUID
    request_model_id: UUID
    api_call_outcome_id: UUID
    response_model_id: UUID | None
    response_class_config_id: UUID | None
    service_operation_id: UUID | None
    service_operation_config_id: UUID | None
    service_operation_commit_id: UUID | None
    service_operation_head_commit_id: UUID | None
    service_operation_branch_id: UUID | None
    service_operation_projection_hash: str | None
    api_call_outcome_commit_id: UUID | None
    api_call_outcome_head_commit_id: UUID | None
    api_call_outcome_branch_id: UUID | None
    api_call_outcome_projection_hash: str | None
    response_payload: object | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"


async def invoke_terminal_action_fulfillment(
    *,
    invoker: ActionTerminalFulfillmentInvoker,
    endpoint_ref: str,
    discriminant: str,
    request_values: Mapping[str, object],
    api_call_key: UUID,
    expected_api_call_id: UUID,
    expected_api_capability_endpoint_id: UUID,
    response_class_config_id: UUID | None,
) -> ActionDispatchTerminalOutcome:
    response = await invoker.invoke_action_endpoint(
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        request_values=request_values,
        api_call_key=api_call_key,
    )
    receipt = _field(response, "receipt")
    if receipt is None:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_receipt_missing"
        )

    returned_endpoint_ref = _required_text(receipt, "endpoint_ref")
    returned_discriminant = _required_text(receipt, "discriminant")
    if returned_endpoint_ref != endpoint_ref:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_endpoint_mismatch"
        )
    if returned_discriminant != discriminant:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_discriminant_mismatch"
        )

    api_call_id = _required_uuid(receipt, "api_call_id")
    if api_call_id != expected_api_call_id:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_api_call_id_mismatch"
        )
    endpoint_id = _required_uuid(receipt, "api_capability_endpoint_id")
    if endpoint_id != expected_api_capability_endpoint_id:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_endpoint_id_mismatch"
        )
    returned_call_key = _required_uuid(receipt, "call_key")
    if returned_call_key != api_call_key:
        raise ActionTerminalFulfillmentError(
            "action_terminal_fulfillment_api_call_key_mismatch"
        )

    status = _status_text(_field(receipt, "status") or _field(response, "status"))
    if status not in {"succeeded", "failed"}:
        raise ActionTerminalFulfillmentError(
            f"action_terminal_fulfillment_status_invalid:{status}"
        )
    response_model_id = _optional_uuid(receipt, "response_model_id")
    if status == "succeeded" and response_class_config_id is not None:
        if response_model_id is None:
            raise ActionTerminalFulfillmentError(
                "action_terminal_fulfillment_response_model_missing"
            )

    return ActionDispatchTerminalOutcome(
        status=status,
        endpoint_ref=returned_endpoint_ref,
        discriminant=returned_discriminant,
        api_call_id=api_call_id,
        api_capability_endpoint_id=endpoint_id,
        api_call_key=returned_call_key,
        request_model_id=_required_uuid(receipt, "request_model_id"),
        api_call_outcome_id=_required_uuid(receipt, "api_call_outcome_id"),
        response_model_id=response_model_id,
        response_class_config_id=response_class_config_id,
        service_operation_id=_optional_uuid(receipt, "service_operation_id"),
        service_operation_config_id=_optional_uuid(
            receipt, "service_operation_config_id"
        ),
        service_operation_commit_id=_optional_uuid(
            receipt, "service_operation_commit_id"
        ),
        service_operation_head_commit_id=_optional_uuid(
            receipt, "service_operation_head_commit_id"
        ),
        service_operation_branch_id=_optional_uuid(
            receipt, "service_operation_branch_id"
        ),
        service_operation_projection_hash=_optional_text(
            receipt, "service_operation_projection_hash"
        ),
        api_call_outcome_commit_id=_optional_uuid(
            receipt, "api_call_outcome_commit_id"
        ),
        api_call_outcome_head_commit_id=_optional_uuid(
            receipt, "api_call_outcome_head_commit_id"
        ),
        api_call_outcome_branch_id=_optional_uuid(
            receipt, "api_call_outcome_branch_id"
        ),
        api_call_outcome_projection_hash=_optional_text(
            receipt, "api_call_outcome_projection_hash"
        ),
        response_payload=_field(response, "response_payload"),
        error=_optional_text(response, "error"),
    )


def _field(value: object, name: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _required_text(value: object, name: str) -> str:
    result = _optional_text(value, name)
    if result is None:
        raise ActionTerminalFulfillmentError(
            f"action_terminal_fulfillment_{name}_missing"
        )
    return result


def _optional_text(value: object, name: str) -> str | None:
    raw = _field(value, name)
    if raw is None:
        return None
    text = str(getattr(raw, "value", raw)).strip()
    return text or None


def _status_text(value: object | None) -> str:
    return str(getattr(value, "value", value) or "").strip().casefold()


def _required_uuid(value: object, name: str) -> UUID:
    result = _optional_uuid(value, name)
    if result is None:
        raise ActionTerminalFulfillmentError(
            f"action_terminal_fulfillment_{name}_missing"
        )
    return result


def _optional_uuid(value: object, name: str) -> UUID | None:
    raw = _field(value, name)
    if raw is None or raw == "":
        return None
    if isinstance(raw, UUID):
        return raw
    try:
        return UUID(str(raw))
    except (TypeError, ValueError) as exc:
        raise ActionTerminalFulfillmentError(
            f"action_terminal_fulfillment_{name}_invalid"
        ) from exc


__all__ = [
    "ActionDispatchTerminalOutcome",
    "ActionTerminalFulfillmentError",
    "ActionTerminalFulfillmentInvoker",
    "invoke_terminal_action_fulfillment",
]
