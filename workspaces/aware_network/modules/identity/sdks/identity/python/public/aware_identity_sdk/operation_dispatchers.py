from __future__ import annotations

from typing import Any, Awaitable, Callable, Mapping, cast
from uuid import UUID

from aware_api_service_dto.comms.models.api import ApiRequestStatus
from aware_identity_service_api._bindings import (
    IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
)
from aware_identity_service_dto.profile.requests import CreateProfileRequest
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
from aware_identity_service_dto.identity.admission import (
    IdentitySignupViaProfileRequest,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationResponse,
)

from aware_identity_sdk.client import (
    DEFAULT_IDENTITY_SDK_SOURCE,
    IdentityAdmission,
    IdentitySdkError,
)


IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF = "identity_sdk.admit_identity"


async def dispatch_identity_admit_identity(
    *,
    api_client: object,
    operation_ref: str,
    discriminant: str,
    request_payload: Mapping[str, Any],
    context: Mapping[str, object | None] | None = None,
    timeout_s: float | None = None,
) -> ServiceOperationResponse:
    _ = context
    if operation_ref != IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF:
        raise IdentitySdkError(f"Unsupported Identity SDK operation: {operation_ref}")
    if discriminant != operation_ref:
        raise IdentitySdkError(
            "Identity SDK operation discriminant must match operation_ref: "
            + f"{discriminant!r}"
        )

    profile_request = _profile_request_from_payload(request_payload)
    signup_request = IdentitySignupViaProfileRequest(
        public_key=_required_text(request_payload, "public_key"),
        create_profile_request=profile_request,
        request_id=_optional_uuid(request_payload.get("request_id")),
        source=_optional_text(request_payload.get("source"))
        or DEFAULT_IDENTITY_SDK_SOURCE,
    )
    response = await _invoke_identity_signup(
        api_client=api_client,
        request=signup_request,
        timeout_s=timeout_s,
    )
    if response.status is not RequestStatus.succeeded:
        return response
    if not isinstance(response.response_payload, Mapping):
        raise IdentitySdkError(
            "identity.signup_via_profile returned no IdentityAdmissionReceipt payload."
        )
    receipt = IdentityAdmissionReceipt.model_validate(response.response_payload)
    admission = IdentityAdmission.from_receipt(
        receipt=receipt,
        identity_type=profile_request.identity_type,
    )
    response_payload: dict[str, object] = {
        "identity_type": admission.identity_type.value,
        "receipt": admission.receipt.model_dump(
            mode="json",
            exclude_none=True,
        ),
    }
    for key, value in {
        "identity_id": _optional_uuid_text(admission.identity_id),
        "actor_id": _optional_uuid_text(admission.actor_id),
        "identity_profile_id": _optional_uuid_text(admission.identity_profile_id),
        "public_handle": admission.public_handle,
        "info": admission.info,
    }.items():
        if value is not None:
            response_payload[key] = value
    return ServiceOperationResponse(
        status=RequestStatus.succeeded,
        response_payload=response_payload,
    )


async def _invoke_identity_signup(
    *,
    api_client: object,
    request: IdentitySignupViaProfileRequest,
    timeout_s: float | None,
) -> ServiceOperationResponse:
    raw_invoke = getattr(api_client, "invoke_api_endpoint_raw", None)
    if not callable(raw_invoke):
        raise IdentitySdkError(
            "identity_sdk.admit_identity requires an API client with "
            "invoke_api_endpoint_raw(...)."
        )
    invoke = cast(Callable[..., Awaitable[Any]], raw_invoke)
    response = await invoke(
        endpoint_ref=IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
        discriminant=IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
        request_payload=request.model_dump(mode="json", exclude_none=True),
        timeout_s=timeout_s,
    )
    status_token = _status_token(getattr(response, "status", None))
    if status_token == ApiRequestStatus.succeeded.value:
        status = RequestStatus.succeeded
    elif status_token == ApiRequestStatus.pending.value:
        status = RequestStatus.pending
    else:
        status = RequestStatus.failed
    return ServiceOperationResponse(
        status=status,
        error=getattr(response, "error", None),
        response_payload=getattr(response, "response_payload", None),
    )


def _status_token(value: object) -> str:
    return str(getattr(value, "value", value) or "").strip()


def _profile_request_from_payload(
    request_payload: Mapping[str, Any],
) -> CreateProfileRequest:
    raw_profile = request_payload.get("create_profile_request")
    if not isinstance(raw_profile, Mapping):
        raise IdentitySdkError(
            "identity_sdk.admit_identity payload.create_profile_request "
            "must be an object."
        )
    return CreateProfileRequest.model_validate(raw_profile)


def _required_text(request_payload: Mapping[str, Any], key: str) -> str:
    raw = request_payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise IdentitySdkError(
            f"identity_sdk.admit_identity payload.{key} must be a non-empty string."
        )
    return raw.strip()


def _optional_text(raw: object) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise IdentitySdkError("Optional Identity SDK text values must be strings.")
    return raw.strip() or None


def _optional_uuid(raw: object) -> UUID | None:
    if raw is None:
        return None
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw.strip())
    raise IdentitySdkError("Optional Identity SDK UUID values must be UUID strings.")


def _optional_uuid_text(raw: UUID | None) -> str | None:
    return str(raw) if raw is not None else None


SDK_OPERATION_DISPATCHERS = {
    IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF: dispatch_identity_admit_identity,
}


__all__ = [
    "IDENTITY_SDK_ADMIT_IDENTITY_OPERATION_REF",
    "SDK_OPERATION_DISPATCHERS",
    "dispatch_identity_admit_identity",
]
