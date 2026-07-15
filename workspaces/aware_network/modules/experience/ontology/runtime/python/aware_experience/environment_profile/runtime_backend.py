from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from aware_environment_service_dto.environment.environment import (
    ProvisionEnvironmentProfileRequest,
    ProvisionEnvironmentProfileResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)
from aware_experience_service_dto.experience.program import (
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience.environment_profile.materialization_runtime import (
    ApplyEnvironmentExperienceProgramsRequest,
    ApplyEnvironmentExperienceProgramsResponse,
)
from aware_experience.program.service import SubmitProgramTurnOperation

from aware_experience.environment_profile.api_models import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ApplyExperienceEnvironmentProfileProgramsResponse,
    ProvisionExperienceEnvironmentProfileRequest,
    ProvisionExperienceEnvironmentProfileResponse,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience.environment_profile import (
    materialization_runtime as environment_experience_materialization,
)


_SUCCESS_STATUSES = {"planned", "succeeded", "success", "ok"}


class EnvironmentRuntimeResolverLike(Protocol):
    async def get_manifest(self) -> tuple[Any, Any]: ...

    async def get_runtime(self, *, environment_id: object) -> Any: ...


@dataclass(frozen=True, slots=True)
class EnvironmentRuntimeExperienceProfileBackend:
    """Experience-owned adapter into profile materialization runtime."""

    resolver: EnvironmentRuntimeResolverLike
    environment_api_client: Any | None = None

    async def upsert_environment_profile(
        self,
        *,
        request: UpsertExperienceEnvironmentProfileRequest,
        host_context: Any | None = None,
    ) -> UpsertExperienceEnvironmentProfileResponse:
        environment_api_client = _environment_api_client_from_context(
            configured=self.environment_api_client,
            host_context=host_context,
        )
        if environment_api_client is not None:
            environment_response = await _upsert_environment_profile_via_api(
                environment_api_client=environment_api_client,
                request=request,
            )
            return _experience_upsert_response_from_environment_profile(
                environment_response,
                request=request,
                runtime_mutation=not request.validate_only,
            )
        raise RuntimeError(
            "Experience environment profile upsert requires an Environment API "
            "client; hosted Environment runtime materialization fallback is retired."
        )

    async def provision_environment_profile(
        self,
        *,
        request: ProvisionExperienceEnvironmentProfileRequest,
        host_context: Any | None = None,
    ) -> ProvisionExperienceEnvironmentProfileResponse:
        environment_api_client = _environment_api_client_from_context(
            configured=self.environment_api_client,
            host_context=host_context,
        )
        if environment_api_client is not None:
            environment_response = await _provision_environment_profile_via_api(
                environment_api_client=environment_api_client,
                request=request,
            )
            return _experience_provision_response_from_environment_profile(
                environment_response,
                request=request,
                runtime_mutation=not request.validate_only,
            )
        raise RuntimeError(
            "Experience environment profile provision requires an Environment API "
            "client; hosted Environment runtime materialization fallback is retired."
        )

    async def apply_environment_profile_programs(
        self,
        *,
        request: ApplyExperienceEnvironmentProfileProgramsRequest,
        host_context: Any | None = None,
    ) -> ApplyExperienceEnvironmentProfileProgramsResponse:
        environment_request = ApplyEnvironmentExperienceProgramsRequest.model_validate(
            _environment_request_payload(
                request,
                operation="apply_environment_experience_programs",
                drop_fields=(
                    "experience_name",
                    "profile_key",
                    "request_context",
                    "request_id",
                ),
            )
        )
        submit_program_turn_op = _environment_submit_program_turn_op(
            environment_api_client=_environment_api_client_from_context(
                configured=self.environment_api_client,
                host_context=host_context,
            )
        )
        environment_response = await environment_experience_materialization.apply_environment_experience_programs(
            self.resolver,
            environment_request,
            submit_program_turn_op=submit_program_turn_op,
        )
        return ApplyExperienceEnvironmentProfileProgramsResponse.model_validate(
            _experience_response_payload(
                environment_response,
                request=request,
                operation="apply_experience_environment_profile_programs",
                legacy_operation="apply_environment_experience_programs",
                runtime_mutation=not request.validate_only,
                profile_key=request.profile_key,
            )
        )


def _model_payload(value: object) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return dict(value)
    raise TypeError(f"Expected pydantic model or dict payload, got {type(value)!r}")


def _environment_request_payload(
    request: object,
    *,
    operation: str,
    drop_fields: tuple[str, ...],
) -> dict[str, Any]:
    payload = _model_payload(request)
    payload["operation"] = operation
    for field_name in drop_fields:
        payload.pop(field_name, None)
    return payload


def _experience_response_payload(
    response: ApplyEnvironmentExperienceProgramsResponse,
    *,
    request: (
        UpsertExperienceEnvironmentProfileRequest
        | ProvisionExperienceEnvironmentProfileRequest
        | ApplyExperienceEnvironmentProfileProgramsRequest
    ),
    operation: str,
    legacy_operation: str,
    runtime_mutation: bool,
    profile_key: str | None,
) -> dict[str, Any]:
    payload = response.model_dump(mode="json", exclude_none=True)
    status = str(payload.get("status") or "").strip().casefold()
    payload["operation"] = operation
    payload["request_id"] = request.request_id
    payload["success"] = payload.get("error") in (None, "") and (
        not status or status in _SUCCESS_STATUSES
    )
    payload["experience_name"] = request.experience_name
    payload["profile_key"] = profile_key
    payload["evidence"] = {
        "owner": "experience",
        "backend": "environment_runtime",
        "runtime_mutation": runtime_mutation,
        "legacy_operation": legacy_operation,
    }
    return payload


async def _upsert_environment_profile_via_api(
    *,
    environment_api_client: Any,
    request: UpsertExperienceEnvironmentProfileRequest,
) -> UpsertEnvironmentProfileResponse:
    profile_api = _environment_profile_api(environment_api_client)
    upsert = getattr(profile_api, "upsert_environment_profile", None)
    if not callable(upsert):
        raise RuntimeError(
            "Environment API client is missing environment.profile."
            "upsert_environment_profile"
        )
    api_request = UpsertEnvironmentProfileRequest.model_validate(
        _environment_request_payload(
            request,
            operation="upsert_environment_profile",
            drop_fields=("experience_name", "request_context", "request_id"),
        )
    )
    response = await upsert(api_request)
    if isinstance(response, UpsertEnvironmentProfileResponse):
        return response
    return UpsertEnvironmentProfileResponse.model_validate(response)


async def _provision_environment_profile_via_api(
    *,
    environment_api_client: Any,
    request: ProvisionExperienceEnvironmentProfileRequest,
) -> ProvisionEnvironmentProfileResponse:
    profile_api = _environment_profile_api(environment_api_client)
    provision = getattr(profile_api, "provision_environment_profile", None)
    if not callable(provision):
        raise RuntimeError(
            "Environment API client is missing environment.profile."
            "provision_environment_profile"
        )
    payload = _environment_request_payload(
        request,
        operation="provision_environment_profile",
        drop_fields=(
            "experience_name",
            "profile_key",
            "request_context",
            "request_id",
        ),
    )
    if (
        payload.get("environment_profile_id") is None
        and payload.get("environment_experience_profile_id") is not None
    ):
        payload["environment_profile_id"] = payload.pop(
            "environment_experience_profile_id"
        )
    api_request = ProvisionEnvironmentProfileRequest.model_validate(payload)
    response = await provision(api_request)
    if isinstance(response, ProvisionEnvironmentProfileResponse):
        return response
    return ProvisionEnvironmentProfileResponse.model_validate(response)


def _environment_profile_api(environment_api_client: Any) -> Any:
    environment = getattr(environment_api_client, "environment", None)
    profile = getattr(environment, "profile", None)
    if profile is None:
        raise RuntimeError("Environment API client is missing environment.profile")
    return profile


def _experience_upsert_response_from_environment_profile(
    response: UpsertEnvironmentProfileResponse,
    *,
    request: UpsertExperienceEnvironmentProfileRequest,
    runtime_mutation: bool,
) -> UpsertExperienceEnvironmentProfileResponse:
    payload = response.model_dump(mode="json", exclude_none=True)
    payload["operation"] = "upsert_experience_environment_profile"
    payload["request_id"] = request.request_id
    payload["success"] = _is_success_payload(payload)
    payload["experience_name"] = request.experience_name
    payload["profile_key"] = request.profile.key
    payload["environment_experience_profile_id"] = payload.pop(
        "environment_profile_id",
        None,
    )
    payload["evidence"] = {
        "owner": "experience",
        "backend": "environment_api",
        "topology_owner": "environment",
        "runtime_mutation": runtime_mutation,
    }
    return UpsertExperienceEnvironmentProfileResponse.model_validate(payload)


def _experience_provision_response_from_environment_profile(
    response: ProvisionEnvironmentProfileResponse,
    *,
    request: ProvisionExperienceEnvironmentProfileRequest,
    runtime_mutation: bool,
) -> ProvisionExperienceEnvironmentProfileResponse:
    payload = response.model_dump(mode="json", exclude_none=True)
    environment_profile_id = payload.pop("environment_profile_id", None)
    payload["operation"] = "provision_experience_environment_profile"
    payload["request_id"] = request.request_id
    payload["success"] = _is_success_payload(payload)
    payload["experience_name"] = request.experience_name
    payload["profile_key"] = request.profile_key
    payload["environment_experience_profile_id"] = environment_profile_id
    payload["runtime_mounts"] = [
        _experience_runtime_mount_payload(
            mount,
            environment_profile_id=environment_profile_id,
        )
        for mount in payload.get("runtime_mounts", [])
    ]
    payload["evidence"] = {
        "owner": "experience",
        "backend": "environment_api",
        "topology_owner": "environment",
        "runtime_mutation": runtime_mutation,
    }
    return ProvisionExperienceEnvironmentProfileResponse.model_validate(payload)


def _experience_runtime_mount_payload(
    value: object,
    *,
    environment_profile_id: object,
) -> dict[str, Any]:
    payload = _model_payload(value)
    payload["environment_experience_profile_id"] = payload.pop(
        "environment_profile_id",
        environment_profile_id,
    )
    return payload


def _is_success_payload(payload: Mapping[str, object]) -> bool:
    status = str(payload.get("status") or "").strip().casefold()
    return payload.get("error") in (None, "") and (
        not status or status in _SUCCESS_STATUSES
    )


def _environment_api_client_from_context(
    *,
    configured: Any | None,
    host_context: Any | None,
) -> Any | None:
    if configured is not None:
        return configured
    if host_context is None:
        return None
    if isinstance(host_context, Mapping):
        return host_context.get("environment_api_client")
    invocation_context = getattr(host_context, "invocation_context", None)
    if isinstance(invocation_context, Mapping):
        client = invocation_context.get("environment_api_client")
        if client is not None:
            return client
    return getattr(host_context, "environment_api_client", None)


def _environment_submit_program_turn_op(
    *,
    environment_api_client: Any | None,
) -> SubmitProgramTurnOperation | None:
    if environment_api_client is None:
        return None
    environment = getattr(environment_api_client, "environment", None)
    program_turn = getattr(environment, "program_turn", None)
    submit_program_turn = getattr(program_turn, "submit_program_turn", None)
    if not callable(submit_program_turn):
        raise RuntimeError(
            "Environment API client is missing environment.program_turn."
            "submit_program_turn"
        )

    async def _submit_program_turn(
        resolver: Any,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op: object = None,
        store: Any | None = None,
    ) -> SubmitProgramTurnResponse:
        _ = resolver, apply_program_ref_op, store
        response = await submit_program_turn(request)
        if isinstance(response, SubmitProgramTurnResponse):
            return response
        return SubmitProgramTurnResponse.model_validate(response)

    return _submit_program_turn


__all__ = [
    "EnvironmentRuntimeExperienceProfileBackend",
]
