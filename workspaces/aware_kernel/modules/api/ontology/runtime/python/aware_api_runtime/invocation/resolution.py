from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from ..models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APIOwnership,
)


@dataclass(frozen=True, slots=True)
class ResolvedApiInvocationFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    source_path: str
    api_capability_endpoint_function_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ResolvedApiInvocationStreamEvent:
    kind: str
    class_ref: str
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedApiInvocationStream:
    stream_mode: str
    source_path: str
    events: tuple[ResolvedApiInvocationStreamEvent, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ApiInvocationIR:
    api_name: str
    capability_name: str
    endpoint_name: str
    endpoint_ref: str
    discriminant: str
    source_path: str
    request_payload: Mapping[str, object]
    request_class_ref: str
    request_class_config_id: UUID | None
    request_source_path: str
    response_class_ref: str | None
    response_source_path: str | None
    stream: ResolvedApiInvocationStream | None
    fulfillment_bindings: tuple[ResolvedApiInvocationFulfillmentBinding, ...]
    description: str | None = None
    api_capability_endpoint_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ApiInvocationSourceCommit:
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    object_instance_graph_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class MaterializedApiCallBinding:
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_hash: str
    request_model_id: UUID
    request_class_config_id: UUID
    fulfillment_bindings: tuple[ResolvedApiInvocationFulfillmentBinding, ...] = ()
    commit_id: UUID | None = None
    head_commit_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedApiInvocationEnvelope:
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_hash: str
    commit_id: UUID
    head_commit_id: UUID
    branch_id: UUID
    projection_hash: str
    api_name: str
    capability_name: str
    endpoint_name: str
    endpoint_ref: str
    discriminant: str
    source_path: str
    request_model_id: UUID
    request_class_config_id: UUID
    request_class_ref: str
    request_source_path: str
    response_class_ref: str | None
    response_source_path: str | None
    stream: ResolvedApiInvocationStream | None
    fulfillment_bindings: tuple[ResolvedApiInvocationFulfillmentBinding, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class _ResolvedEndpointBinding:
    api_name: str
    capability_name: str
    endpoint: APICapabilityEndpointOwnership

    @property
    def endpoint_name(self) -> str:
        return self.endpoint.name

    @property
    def endpoint_ref(self) -> str:
        return _endpoint_ref(self.api_name, self.capability_name, self.endpoint.name)

    @property
    def discriminant(self) -> str:
        return self.endpoint_ref


@dataclass(frozen=True, slots=True)
class ApiInvocationResolutionIndex:
    endpoints_by_ref: Mapping[str, _ResolvedEndpointBinding]
    endpoints_by_discriminant: Mapping[str, _ResolvedEndpointBinding]

    def get_endpoint_by_ref(self, endpoint_ref: str) -> _ResolvedEndpointBinding | None:
        return self.endpoints_by_ref.get(endpoint_ref.strip())

    def require_endpoint_by_ref(self, endpoint_ref: str) -> _ResolvedEndpointBinding:
        endpoint = self.get_endpoint_by_ref(endpoint_ref)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint ref '{endpoint_ref}'.")
        return endpoint

    def get_endpoint_by_discriminant(self, discriminant: str) -> _ResolvedEndpointBinding | None:
        return self.endpoints_by_discriminant.get(discriminant.strip())

    def require_endpoint_by_discriminant(self, discriminant: str) -> _ResolvedEndpointBinding:
        endpoint = self.get_endpoint_by_discriminant(discriminant)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint discriminant '{discriminant}'.")
        return endpoint

    def require_endpoint(
        self,
        *,
        api_name: str,
        capability_name: str,
        endpoint_name: str,
    ) -> _ResolvedEndpointBinding:
        return self.require_endpoint_by_ref(_endpoint_ref(api_name, capability_name, endpoint_name))


def build_api_invocation_resolution_index(
    *,
    api_ownership: tuple[APIOwnership, ...],
) -> ApiInvocationResolutionIndex:
    endpoints_by_ref: dict[str, _ResolvedEndpointBinding] = {}
    endpoints_by_discriminant: dict[str, _ResolvedEndpointBinding] = {}

    for api in api_ownership:
        api_name = _required_token("api.name", api.name)
        for capability in api.capabilities:
            capability_name = _required_token(
                f"capability.name[{api_name}]",
                capability.name,
            )
            for endpoint in capability.endpoints:
                endpoint_name = _required_token(
                    f"endpoint.name[{api_name}.{capability_name}]",
                    endpoint.name,
                )
                binding = _ResolvedEndpointBinding(
                    api_name=api_name,
                    capability_name=capability_name,
                    endpoint=endpoint,
                )
                endpoint_ref = _endpoint_ref(api_name, capability_name, endpoint_name)
                if endpoint_ref in endpoints_by_ref:
                    raise ValueError(f"Duplicate endpoint ref '{endpoint_ref}'.")
                endpoints_by_ref[endpoint_ref] = binding

                discriminant = endpoint_ref
                if discriminant in endpoints_by_discriminant:
                    raise ValueError(f"Duplicate endpoint discriminant '{discriminant}'.")
                endpoints_by_discriminant[discriminant] = binding

    return ApiInvocationResolutionIndex(
        endpoints_by_ref=MappingProxyType(dict(endpoints_by_ref)),
        endpoints_by_discriminant=MappingProxyType(dict(endpoints_by_discriminant)),
    )


def resolve_api_invocation_ir(
    *,
    api_ownership: tuple[APIOwnership, ...],
    request_payload: Mapping[str, object] | None = None,
    endpoint_ref: str | None = None,
    discriminant: str | None = None,
    api_name: str | None = None,
    capability_name: str | None = None,
    endpoint_name: str | None = None,
) -> ApiInvocationIR:
    index = build_api_invocation_resolution_index(api_ownership=api_ownership)
    binding = _resolve_endpoint_binding(
        index=index,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        api_name=api_name,
        capability_name=capability_name,
        endpoint_name=endpoint_name,
    )
    request_config = binding.endpoint.request_config
    response_config = request_config.response_config
    stream_config = request_config.stream_config
    return ApiInvocationIR(
        api_name=binding.api_name,
        capability_name=binding.capability_name,
        endpoint_name=binding.endpoint_name,
        endpoint_ref=binding.endpoint_ref,
        discriminant=binding.discriminant,
        source_path=_required_token(f"{binding.endpoint_ref}.source_path", binding.endpoint.source_path),
        request_payload=_normalize_request_payload(request_payload),
        request_class_ref=_required_token(
            f"{binding.endpoint_ref}.request.class_ref",
            request_config.class_ref,
        ),
        request_class_config_id=request_config.class_config_id,
        request_source_path=_required_token(
            f"{binding.endpoint_ref}.request.source_path",
            request_config.source_path,
        ),
        response_class_ref=(
            _required_token(f"{binding.endpoint_ref}.response.class_ref", response_config.class_ref)
            if response_config is not None
            else None
        ),
        response_source_path=(
            _required_token(f"{binding.endpoint_ref}.response.source_path", response_config.source_path)
            if response_config is not None
            else None
        ),
        stream=(
            ResolvedApiInvocationStream(
                stream_mode=_required_token(
                    f"{binding.endpoint_ref}.stream.stream_mode",
                    stream_config.stream_mode,
                ),
                source_path=_required_token(
                    f"{binding.endpoint_ref}.stream.source_path",
                    stream_config.source_path,
                ),
                description=stream_config.description,
                events=tuple(
                    ResolvedApiInvocationStreamEvent(
                        kind=_required_token(
                            f"{binding.endpoint_ref}.stream.event.kind",
                            event.kind,
                        ),
                        class_ref=_required_token(
                            f"{binding.endpoint_ref}.stream.event.class_ref",
                            event.class_ref,
                        ),
                        source_path=_required_token(
                            f"{binding.endpoint_ref}.stream.event.source_path",
                            event.source_path,
                        ),
                        description=event.description,
                    )
                    for event in stream_config.event_configs
                ),
            )
            if stream_config is not None
            else None
        ),
        fulfillment_bindings=tuple(
            _resolve_fulfillment_binding(endpoint_ref=binding.endpoint_ref, function=function)
            for function in binding.endpoint.functions
        ),
        description=binding.endpoint.description,
    )


def build_resolved_api_invocation_envelope(
    *,
    ir: ApiInvocationIR,
    materialized_call: MaterializedApiCallBinding,
) -> ResolvedApiInvocationEnvelope:
    commit_id = _required_uuid("materialized_call.commit_id", materialized_call.commit_id)
    head_commit_id = _required_uuid("materialized_call.head_commit_id", materialized_call.head_commit_id)
    branch_id = _required_uuid("materialized_call.branch_id", materialized_call.branch_id)
    projection_hash = _required_optional_token(
        "materialized_call.projection_hash",
        materialized_call.projection_hash,
    )
    return ResolvedApiInvocationEnvelope(
        api_call_id=materialized_call.api_call_id,
        api_capability_endpoint_id=materialized_call.api_capability_endpoint_id,
        call_key=materialized_call.call_key,
        request_hash=_required_token("materialized_call.request_hash", materialized_call.request_hash),
        commit_id=commit_id,
        head_commit_id=head_commit_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        api_name=ir.api_name,
        capability_name=ir.capability_name,
        endpoint_name=ir.endpoint_name,
        endpoint_ref=ir.endpoint_ref,
        discriminant=ir.discriminant,
        source_path=ir.source_path,
        request_model_id=materialized_call.request_model_id,
        request_class_config_id=materialized_call.request_class_config_id,
        request_class_ref=ir.request_class_ref,
        request_source_path=ir.request_source_path,
        response_class_ref=ir.response_class_ref,
        response_source_path=ir.response_source_path,
        stream=ir.stream,
        fulfillment_bindings=(
            materialized_call.fulfillment_bindings
            if materialized_call.fulfillment_bindings
            else ir.fulfillment_bindings
        ),
        description=ir.description,
    )


def _resolve_endpoint_binding(
    *,
    index: ApiInvocationResolutionIndex,
    endpoint_ref: str | None,
    discriminant: str | None,
    api_name: str | None,
    capability_name: str | None,
    endpoint_name: str | None,
) -> _ResolvedEndpointBinding:
    lookup_count = sum(value is not None for value in (endpoint_ref, discriminant))
    if api_name is not None or capability_name is not None or endpoint_name is not None:
        lookup_count += 1
    if lookup_count != 1:
        raise ValueError(
            "Exactly one endpoint locator is required: "
            "endpoint_ref, discriminant, or api_name+capability_name+endpoint_name."
        )
    if endpoint_ref is not None:
        return index.require_endpoint_by_ref(endpoint_ref)
    if discriminant is not None:
        return index.require_endpoint_by_discriminant(discriminant)
    if api_name is None or capability_name is None or endpoint_name is None:
        raise ValueError(
            "api_name, capability_name, and endpoint_name are required together "
            "when resolving an endpoint by names."
        )
    return index.require_endpoint(
        api_name=api_name,
        capability_name=capability_name,
        endpoint_name=endpoint_name,
    )


def _resolve_fulfillment_binding(
    *,
    endpoint_ref: str,
    function: APICapabilityEndpointFunctionOwnership,
) -> ResolvedApiInvocationFulfillmentBinding:
    return ResolvedApiInvocationFulfillmentBinding(
        name=_required_token(f"{endpoint_ref}.function.name", function.name),
        graph_target=_required_token(f"{endpoint_ref}.function.graph_target", function.graph_target),
        graph_capability_function_name=_required_token(
            f"{endpoint_ref}.function.graph_capability_function_name",
            function.graph_capability_function_name,
        ),
        source_path=_required_token(f"{endpoint_ref}.function.source_path", function.source_path),
    )


def _normalize_request_payload(request_payload: Mapping[str, object] | None) -> Mapping[str, object]:
    if request_payload is None:
        return MappingProxyType({})
    return MappingProxyType(dict(request_payload))


def _endpoint_ref(api_name: str, capability_name: str, endpoint_name: str) -> str:
    return ".".join((api_name, capability_name, endpoint_name))


def _required_token(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _required_optional_token(label: str, value: str | None) -> str:
    if value is None:
        raise RuntimeError(f"{label} is required for commit-backed ApiCall handoff.")
    return _required_token(label, value)


def _required_uuid(label: str, value: UUID | None) -> UUID:
    if value is None:
        raise RuntimeError(f"{label} is required for commit-backed ApiCall handoff.")
    return value


__all__ = [
    "ApiInvocationIR",
    "ApiInvocationResolutionIndex",
    "ApiInvocationSourceCommit",
    "MaterializedApiCallBinding",
    "ResolvedApiInvocationEnvelope",
    "ResolvedApiInvocationFulfillmentBinding",
    "ResolvedApiInvocationStream",
    "ResolvedApiInvocationStreamEvent",
    "build_api_invocation_resolution_index",
    "build_resolved_api_invocation_envelope",
    "resolve_api_invocation_ir",
]
