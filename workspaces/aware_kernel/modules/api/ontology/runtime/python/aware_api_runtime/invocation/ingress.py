from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex

from .dispatcher import (
    ApiInvocationDispatchResult,
    ApiInvocationRuntimeProtocol,
    dispatch_api_invocation,
)
from .resolution import (
    ApiInvocationIR,
    ApiInvocationSourceCommit,
    ResolvedApiInvocationFulfillmentBinding,
    ResolvedApiInvocationStream,
    ResolvedApiInvocationStreamEvent,
)
from .spec import (
    ApiInvocationApiSpec,
    ApiInvocationCapabilitySpec,
    ApiInvocationEndpointSpec,
    ApiInvocationManifest,
)

if TYPE_CHECKING:
    from ..package_ref_resolution import (
        ApiRuntimePackageRef,
        ResolvedApiRuntimePackageRef,
    )


@dataclass(frozen=True, slots=True)
class ApiInvocationManifestEndpointBinding:
    api: ApiInvocationApiSpec
    capability: ApiInvocationCapabilitySpec
    endpoint: ApiInvocationEndpointSpec


@dataclass(frozen=True, slots=True)
class ApiPackageRefInvocationDispatchResult:
    package_binding: ResolvedApiRuntimePackageRef
    source_commit: ApiInvocationSourceCommit
    dispatch: ApiInvocationDispatchResult


async def dispatch_api_invocation_from_package_ref(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    package_ref: ApiRuntimePackageRef,
    source_lane: MaterializationLaneContext | None = None,
    endpoint_ref: str = "",
    discriminant: str = "",
    request_payload: Mapping[str, object] | None = None,
    call_key: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ApiPackageRefInvocationDispatchResult:
    """Resolve one Workspace ApiPackage ref, lower ingress, and dispatch against its pinned API commit."""

    from ..package_ref_resolution import (
        build_api_invocation_source_commit_from_package_ref,
        resolve_api_runtime_package_ref,
    )

    package_binding = await resolve_api_runtime_package_ref(
        index=index,
        package_ref=package_ref,
    )
    source_commit = build_api_invocation_source_commit_from_package_ref(package_binding)
    effective_source_lane = MaterializationLaneContext(
        branch_id=source_commit.branch_id,
        projection_hash=source_commit.projection_hash,
    )
    dispatch = await dispatch_api_invocation_from_manifest(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=effective_source_lane,
        target_lane=target_lane,
        manifest=package_binding.invocation_manifest,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        request_payload=request_payload,
        source_commit=source_commit,
        call_key=call_key,
        commit=commit,
        publish=publish,
    )
    return ApiPackageRefInvocationDispatchResult(
        package_binding=package_binding,
        source_commit=source_commit,
        dispatch=dispatch,
    )


async def dispatch_api_invocation_from_manifest(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    manifest: ApiInvocationManifest,
    endpoint_ref: str = "",
    discriminant: str = "",
    request_payload: Mapping[str, object] | None = None,
    source_commit: ApiInvocationSourceCommit | None = None,
    call_key: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ApiInvocationDispatchResult:
    """Lower one manifest-backed ingress request and dispatch it through API runtime."""
    ir = resolve_api_invocation_ir_from_manifest(
        index=index,
        manifest=manifest,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        request_payload=request_payload,
    )
    return await dispatch_api_invocation(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=ir,
        source_commit=source_commit,
        call_key=call_key,
        commit=commit,
        publish=publish,
    )


def resolve_api_invocation_ir_from_manifest(
    *,
    index: MetaGraphRuntimeIndex,
    manifest: ApiInvocationManifest,
    endpoint_ref: str = "",
    discriminant: str = "",
    request_payload: Mapping[str, object] | None = None,
) -> ApiInvocationIR:
    binding = resolve_api_invocation_manifest_endpoint(
        manifest=manifest,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )
    endpoint = binding.endpoint
    stream = endpoint.stream
    return ApiInvocationIR(
        api_name=_required_token("api.name", binding.api.name),
        capability_name=_required_token("capability.name", binding.capability.name),
        endpoint_name=_required_token("endpoint.name", endpoint.name),
        endpoint_ref=_required_token("endpoint.endpoint_ref", endpoint.endpoint_ref),
        discriminant=_required_token("endpoint.discriminant", endpoint.discriminant),
        source_path=_required_token("endpoint.source_path", endpoint.source_path),
        request_payload=dict(request_payload or {}),
        request_class_ref=_required_token(
            "endpoint.request.class_ref", endpoint.request.class_ref
        ),
        request_class_config_id=resolve_api_invocation_request_class_config_id(
            index=index,
            class_ref=endpoint.request.class_ref,
        ),
        request_source_path=_required_token(
            "endpoint.request.source_path", endpoint.request.source_path
        ),
        response_class_ref=(
            _required_token("endpoint.response.class_ref", endpoint.response.class_ref)
            if endpoint.response is not None
            else None
        ),
        response_source_path=(
            _required_token(
                "endpoint.response.source_path", endpoint.response.source_path
            )
            if endpoint.response is not None
            else None
        ),
        stream=(
            ResolvedApiInvocationStream(
                stream_mode=_required_token(
                    "endpoint.stream.stream_mode", stream.stream_mode
                ),
                source_path=_required_token(
                    "endpoint.stream.source_path", stream.source_path
                ),
                events=tuple(
                    ResolvedApiInvocationStreamEvent(
                        kind=_required_token("endpoint.stream.event.kind", event.kind),
                        class_ref=_required_token(
                            "endpoint.stream.event.class_ref", event.class_ref
                        ),
                        source_path=_required_token(
                            "endpoint.stream.event.source_path", event.source_path
                        ),
                        description=event.description,
                    )
                    for event in stream.events
                ),
                description=stream.description,
            )
            if stream is not None
            else None
        ),
        fulfillment_bindings=tuple(
            ResolvedApiInvocationFulfillmentBinding(
                name=_required_token("endpoint.fulfillment.name", binding_item.name),
                graph_target=_required_token(
                    "endpoint.fulfillment.graph_target",
                    binding_item.graph_target,
                ),
                graph_capability_function_name=_required_token(
                    "endpoint.fulfillment.graph_capability_function_name",
                    binding_item.graph_capability_function_name,
                ),
                source_path=_required_token(
                    "endpoint.fulfillment.source_path", binding_item.source_path
                ),
            )
            for binding_item in endpoint.fulfillment_bindings
        ),
        description=endpoint.description,
    )


def resolve_api_invocation_manifest_endpoint(
    *,
    manifest: ApiInvocationManifest,
    endpoint_ref: str = "",
    discriminant: str = "",
) -> ApiInvocationManifestEndpointBinding:
    endpoints_by_ref, endpoints_by_discriminant = _build_manifest_endpoint_indexes(
        manifest
    )
    normalized_endpoint_ref = endpoint_ref.strip()
    normalized_discriminant = discriminant.strip()

    if normalized_endpoint_ref:
        binding = endpoints_by_ref.get(normalized_endpoint_ref)
        if binding is None:
            raise KeyError(
                f"Unknown API invocation endpoint_ref {normalized_endpoint_ref!r}."
            )
        if (
            normalized_discriminant
            and binding.endpoint.discriminant.strip() != normalized_discriminant
        ):
            raise ValueError(
                "API invocation endpoint_ref and discriminant resolved inconsistently: "
                f"endpoint_ref={normalized_endpoint_ref!r} discriminant={normalized_discriminant!r}."
            )
        return binding

    if normalized_discriminant:
        binding = endpoints_by_discriminant.get(normalized_discriminant)
        if binding is None:
            raise KeyError(
                f"Unknown API invocation discriminant {normalized_discriminant!r}."
            )
        return binding

    raise ValueError("API invocation ingress requires endpoint_ref or discriminant.")


def resolve_api_invocation_request_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_ref: str,
) -> UUID | None:
    normalized = class_ref.strip()
    if not normalized:
        return None

    exact_matches = sorted(
        {
            class_config.id
            for class_config in index.class_configs_by_id.values()
            if class_config.id is not None
            and (class_config.class_fqn or "").strip() == normalized
        },
        key=str,
    )
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise RuntimeError(
            "API invocation request class ref resolved to multiple exact runtime ClassConfig ids: "
            f"class_ref={normalized!r} matches={[str(item) for item in exact_matches]}"
        )

    tail = ".".join(normalized.split(".")[-2:])
    if not tail:
        return None
    suffix = f".{tail}"
    suffix_matches = sorted(
        {
            class_config.id
            for class_config in index.class_configs_by_id.values()
            if class_config.id is not None
            and (class_config.class_fqn or "").strip().endswith(suffix)
        },
        key=str,
    )
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            "API invocation request class ref resolved ambiguously by runtime ClassConfig suffix: "
            f"class_ref={normalized!r} suffix={suffix!r} matches={[str(item) for item in suffix_matches]}"
        )
    return None


def _build_manifest_endpoint_indexes(
    manifest: ApiInvocationManifest,
) -> tuple[
    dict[str, ApiInvocationManifestEndpointBinding],
    dict[str, ApiInvocationManifestEndpointBinding],
]:
    endpoints_by_ref: dict[str, ApiInvocationManifestEndpointBinding] = {}
    endpoints_by_discriminant: dict[str, ApiInvocationManifestEndpointBinding] = {}

    for api in manifest.apis:
        for capability in api.capabilities:
            for endpoint in capability.endpoints:
                binding = ApiInvocationManifestEndpointBinding(
                    api=api,
                    capability=capability,
                    endpoint=endpoint,
                )
                endpoint_ref = _required_token(
                    "endpoint.endpoint_ref", endpoint.endpoint_ref
                )
                if endpoint_ref in endpoints_by_ref:
                    raise ValueError(
                        f"Duplicate API invocation endpoint_ref {endpoint_ref!r}."
                    )
                endpoints_by_ref[endpoint_ref] = binding

                discriminant = _required_token(
                    "endpoint.discriminant", endpoint.discriminant
                )
                if discriminant in endpoints_by_discriminant:
                    raise ValueError(
                        f"Duplicate API invocation discriminant {discriminant!r}."
                    )
                endpoints_by_discriminant[discriminant] = binding

    return endpoints_by_ref, endpoints_by_discriminant


def _required_token(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


__all__ = [
    "ApiInvocationManifestEndpointBinding",
    "ApiPackageRefInvocationDispatchResult",
    "dispatch_api_invocation_from_manifest",
    "dispatch_api_invocation_from_package_ref",
    "resolve_api_invocation_ir_from_manifest",
    "resolve_api_invocation_manifest_endpoint",
    "resolve_api_invocation_request_class_config_id",
]
