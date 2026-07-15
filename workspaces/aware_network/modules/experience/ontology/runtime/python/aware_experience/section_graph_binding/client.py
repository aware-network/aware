from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, cast

from aware_code.types import JsonObject
from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ExperienceSectionGraphBindingActivationScope,
    ExperienceSectionGraphBindingServiceRequest,
    ExperienceSectionGraphBindingServiceResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceSectionGraphBindingRequest as ServiceActivateExperienceSectionGraphBindingRequest,
    GetExperienceSectionGraphBindingCatalogRequest as ServiceGetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingStateRequest as ServiceGetExperienceSectionGraphBindingStateRequest,
    InvokeExperienceViewInvocationActionRequest as ServiceInvokeExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionRequest as ServiceRecordExperienceViewInvocationActionRequest,
    WatchExperienceSectionGraphBindingsRequest as ServiceWatchExperienceSectionGraphBindingsRequest,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from pydantic import BaseModel


_TResponse = TypeVar(
    "_TResponse",
    bound=ExperienceSectionGraphBindingServiceResponse,
)
_EXPERIENCE_SERVICE_API_PACKAGE_NAME = "experience-service-api"


class ExperienceSectionGraphBindingClientTransport(Protocol):
    async def send_request(
        self,
        *,
        request: ExperienceSectionGraphBindingServiceRequest,
    ) -> ExperienceSectionGraphBindingServiceResponse: ...


@dataclass(frozen=True, slots=True)
class ExperienceSectionGraphBindingClient:
    transport: ExperienceSectionGraphBindingClientTransport

    async def get_catalog(
        self,
        request: GetExperienceSectionGraphBindingCatalogRequest,
    ) -> GetExperienceSectionGraphBindingCatalogResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=GetExperienceSectionGraphBindingCatalogResponse,
        )

    async def get_catalog_for_experience(
        self,
        *,
        experience_name: str,
        section_keys: list[str] | None = None,
        binding_keys: list[str] | None = None,
    ) -> GetExperienceSectionGraphBindingCatalogResponse:
        return await self.get_catalog(
            GetExperienceSectionGraphBindingCatalogRequest(
                experience_name=experience_name,
                section_keys=list(section_keys or ()),
                binding_keys=list(binding_keys or ()),
            )
        )

    async def get_state(
        self,
        request: GetExperienceSectionGraphBindingStateRequest,
    ) -> GetExperienceSectionGraphBindingStateResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=GetExperienceSectionGraphBindingStateResponse,
        )

    async def get_binding_state(
        self,
        *,
        experience_name: str,
        binding_key: str,
    ) -> GetExperienceSectionGraphBindingStateResponse:
        return await self.get_state(
            GetExperienceSectionGraphBindingStateRequest(
                experience_name=experience_name,
                binding_key=binding_key,
            )
        )

    async def activate(
        self,
        request: ActivateExperienceSectionGraphBindingRequest,
    ) -> ActivateExperienceSectionGraphBindingResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=ActivateExperienceSectionGraphBindingResponse,
        )

    async def activate_binding(
        self,
        *,
        experience_name: str,
        binding_key: str,
        rationale: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        focus_scope_title: str | None = None,
        focus_scope_description: str | None = None,
        activation_scope: (
            ExperienceSectionGraphBindingActivationScope | Mapping[str, object] | None
        ) = None,
    ) -> ActivateExperienceSectionGraphBindingResponse:
        resolved_activation_scope = _normalize_activation_scope(activation_scope)
        if resolved_activation_scope is None:
            resolved_activation_scope = (
                activation_scope_from_current_service_api_host_context()
            )
        return await self.activate(
            ActivateExperienceSectionGraphBindingRequest(
                experience_name=experience_name,
                binding_key=binding_key,
                activation_scope=resolved_activation_scope,
                rationale=rationale,
                section_title=section_title,
                section_description=section_description,
                focus_scope_title=focus_scope_title,
                focus_scope_description=focus_scope_description,
            )
        )

    async def record_invocation(
        self,
        request: RecordExperienceViewInvocationActionRequest,
    ) -> RecordExperienceViewInvocationActionResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=RecordExperienceViewInvocationActionResponse,
        )

    async def record_view_invocation_action(
        self,
        *,
        experience_name: str,
        projection_experience_view_instance_id: object,
        view_invocation_action_config_id: object,
        invocation_key: object,
        actor_id: object | None = None,
        api_call_id: object | None = None,
        sdk_operation_call_id: object | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> RecordExperienceViewInvocationActionResponse:
        return await self.record_invocation(
            RecordExperienceViewInvocationActionRequest.model_validate(
                {
                    "experience_name": experience_name,
                    "projection_experience_view_instance_id": (
                        projection_experience_view_instance_id
                    ),
                    "view_invocation_action_config_id": (
                        view_invocation_action_config_id
                    ),
                    "invocation_key": invocation_key,
                    "actor_id": actor_id,
                    "api_call_id": api_call_id,
                    "sdk_operation_call_id": sdk_operation_call_id,
                    "request_ref": request_ref,
                    "receipt_ref": receipt_ref,
                    "status": status,
                }
            )
        )

    async def invoke_view_invocation_action(
        self,
        request: InvokeExperienceViewInvocationActionRequest,
    ) -> InvokeExperienceViewInvocationActionResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=InvokeExperienceViewInvocationActionResponse,
        )

    async def invoke_api_view_invocation_action(
        self,
        *,
        experience_name: str,
        projection_experience_view_instance_id: object,
        view_invocation_action_config_id: object,
        invocation_key: object,
        actor_id: object | None = None,
        request_payload: Mapping[str, object] | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
    ) -> InvokeExperienceViewInvocationActionResponse:
        return await self.invoke_view_invocation_action(
            InvokeExperienceViewInvocationActionRequest.model_validate(
                {
                    "experience_name": experience_name,
                    "projection_experience_view_instance_id": (
                        projection_experience_view_instance_id
                    ),
                    "view_invocation_action_config_id": (
                        view_invocation_action_config_id
                    ),
                    "invocation_key": invocation_key,
                    "actor_id": actor_id,
                    "request_payload": dict(request_payload or {}),
                    "request_ref": request_ref,
                    "receipt_ref": receipt_ref,
                }
            )
        )

    async def watch(
        self,
        request: WatchExperienceSectionGraphBindingsRequest,
    ) -> WatchExperienceSectionGraphBindingsResponse:
        response = await self.transport.send_request(request=request)
        return _expect_response(
            response=response,
            response_type=WatchExperienceSectionGraphBindingsResponse,
        )

    async def watch_bindings(
        self,
        *,
        experience_name: str,
        section_keys: list[str] | None = None,
        binding_keys: list[str] | None = None,
        poll_interval_ms: int = 1000,
    ) -> WatchExperienceSectionGraphBindingsResponse:
        return await self.watch(
            WatchExperienceSectionGraphBindingsRequest(
                experience_name=experience_name,
                section_keys=list(section_keys or ()),
                binding_keys=list(binding_keys or ()),
                poll_interval_ms=poll_interval_ms,
            )
        )


@dataclass(frozen=True, slots=True)
class HostContextExperienceSectionGraphBindingClientTransport:
    host_context: ServiceApiHostContext

    async def send_request(
        self,
        *,
        request: ExperienceSectionGraphBindingServiceRequest,
    ) -> ExperienceSectionGraphBindingServiceResponse:
        client = _require_experience_service_api_client(host_context=self.host_context)
        if isinstance(request, GetExperienceSectionGraphBindingCatalogRequest):
            capability = client.experience.get_experience_section_graph_binding_catalog
            response = await capability.get_experience_section_graph_binding_catalog(
                _convert_model(
                    request,
                    model_cls=ServiceGetExperienceSectionGraphBindingCatalogRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=GetExperienceSectionGraphBindingCatalogResponse,
            )
        if isinstance(request, GetExperienceSectionGraphBindingStateRequest):
            capability = client.experience.get_experience_section_graph_binding_state
            response = await capability.get_experience_section_graph_binding_state(
                _convert_model(
                    request,
                    model_cls=ServiceGetExperienceSectionGraphBindingStateRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=GetExperienceSectionGraphBindingStateResponse,
            )
        if isinstance(request, ActivateExperienceSectionGraphBindingRequest):
            capability = client.experience.activate_experience_section_graph_binding
            response = await capability.activate_experience_section_graph_binding(
                _convert_model(
                    request,
                    model_cls=ServiceActivateExperienceSectionGraphBindingRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=ActivateExperienceSectionGraphBindingResponse,
            )
        if isinstance(request, RecordExperienceViewInvocationActionRequest):
            capability = client.experience.record_experience_view_invocation_action
            response = await capability.record_experience_view_invocation_action(
                _convert_model(
                    request,
                    model_cls=ServiceRecordExperienceViewInvocationActionRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=RecordExperienceViewInvocationActionResponse,
            )
        if isinstance(request, InvokeExperienceViewInvocationActionRequest):
            capability = client.experience.invoke_experience_view_invocation_action
            response = await capability.invoke_experience_view_invocation_action(
                _convert_model(
                    request,
                    model_cls=ServiceInvokeExperienceViewInvocationActionRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=InvokeExperienceViewInvocationActionResponse,
            )
        if isinstance(request, WatchExperienceSectionGraphBindingsRequest):
            capability = client.experience.watch_experience_section_graph_bindings
            response = await capability.watch_experience_section_graph_bindings(
                _convert_model(
                    request,
                    model_cls=ServiceWatchExperienceSectionGraphBindingsRequest,
                )
            )
            return _convert_model(
                response,
                model_cls=WatchExperienceSectionGraphBindingsResponse,
            )
        raise TypeError(
            "Unsupported ExperienceSectionGraphBindingServiceRequest type: "
            + type(request).__name__
        )


def build_host_context_section_graph_binding_client(
    *,
    host_context: ServiceApiHostContext,
) -> ExperienceSectionGraphBindingClient:
    return ExperienceSectionGraphBindingClient(
        transport=HostContextExperienceSectionGraphBindingClientTransport(
            host_context=host_context,
        )
    )


def build_current_service_host_context_section_graph_binding_client() -> (
    ExperienceSectionGraphBindingClient | None
):
    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return build_host_context_section_graph_binding_client(host_context=host_context)


def activation_scope_from_current_service_api_host_context() -> (
    ExperienceSectionGraphBindingActivationScope | None
):
    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return activation_scope_from_invocation_context(host_context.invocation_context)


def activation_scope_from_invocation_context(
    invocation_context: Mapping[str, object] | None,
) -> ExperienceSectionGraphBindingActivationScope | None:
    if invocation_context is None:
        return None
    surface = _mapping_value(invocation_context.get("surface"))
    attention = _mapping_value(invocation_context.get("attention"))
    payload = _drop_none(
        {
            "window_key": _string_value(surface.get("window_key")),
            "layout_key": _string_value(surface.get("layout_key")),
            "section_key": _string_value(surface.get("section_key")),
            "layout_section_id": attention.get("layout_section_id"),
            "section_focus_scope_id": attention.get("section_focus_scope_id"),
            "focus_scope_id": attention.get("focus_scope_id"),
            "observable_id": attention.get("observable_id"),
            "branch_id": attention.get("branch_id"),
            "state_projection_hash": _string_value(
                attention.get("state_projection_hash")
            ),
        }
    )
    if not payload:
        return None
    return ExperienceSectionGraphBindingActivationScope.model_validate(payload)


def _normalize_activation_scope(
    activation_scope: (
        ExperienceSectionGraphBindingActivationScope | Mapping[str, object] | None
    ),
) -> ExperienceSectionGraphBindingActivationScope | None:
    if activation_scope is None:
        return None
    if isinstance(activation_scope, ExperienceSectionGraphBindingActivationScope):
        return activation_scope
    if isinstance(activation_scope, Mapping):
        return ExperienceSectionGraphBindingActivationScope.model_validate(
            dict(activation_scope)
        )
    raise TypeError(
        "activation_scope must be an ExperienceSectionGraphBindingActivationScope, "
        "mapping, or None."
    )


def _mapping_value(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _string_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _drop_none(payload: Mapping[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _require_experience_service_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> Any:
    from aware_experience_service_api import AwareExperienceServiceApiClient

    api_invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_EXPERIENCE_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if api_invoker is None:
        raise RuntimeError(
            "Experience section-graph-binding client requires a Service API "
            "dependency route for experience-service-api."
        )
    return AwareExperienceServiceApiClient(api_invoker)


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _convert_model(value: object, *, model_cls: type[BaseModel]) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


def _expect_response(
    *,
    response: ExperienceSectionGraphBindingServiceResponse,
    response_type: type[_TResponse],
) -> _TResponse:
    if isinstance(response, response_type):
        return response
    raise TypeError(
        "ExperienceSectionGraphBindingClient transport returned mismatched response type: "
        + f"expected={response_type.__name__} actual={type(response).__name__}"
    )


__all__ = [
    "activation_scope_from_current_service_api_host_context",
    "activation_scope_from_invocation_context",
    "ExperienceSectionGraphBindingClient",
    "ExperienceSectionGraphBindingClientTransport",
    "HostContextExperienceSectionGraphBindingClientTransport",
    "build_current_service_host_context_section_graph_binding_client",
    "build_host_context_section_graph_binding_client",
]
