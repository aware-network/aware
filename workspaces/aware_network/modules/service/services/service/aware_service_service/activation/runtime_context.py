from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_history.stable_ids import stable_branch_id
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_service.local_sdk import (
    LocalGraphCommitReceipt,
    LocalGraphInvokeFunctionInput,
    LocalGraphRuntime,
    LocalGraphRuntimeContext,
    LocalGraphRuntimeIndexSnapshot,
    MaterializationLaneContext,
)
from aware_environment.stable_ids import stable_boot_thread_id
from aware_service_runtime.contracts import ServiceGraphGateway
from aware_types import JsonArray, JsonObject

from aware_service_service.ontology.projections import (
    resolve_canonical_service_host_projection,
    resolve_runtime_lane_projection_hash,
)


@dataclass(frozen=True, slots=True)
class ReadOnlyCommittedServiceHostRuntime:
    """Runtime sentinel for committed WorkspaceRevision read-model activation."""

    manifest_path: Path

    @property
    def invoker(self) -> object:
        raise RuntimeError(
            "Committed ServiceHost activation cannot use the local runtime "
            "invoker; use the WorkspaceRevision Meta read model and committed "
            "lane heads."
        )


@dataclass(frozen=True, slots=True)
class MetaSdkServiceHostInvoker:
    graph_gateway: ServiceGraphGateway

    async def invoke_function_with_index(
        self,
        *,
        index: LocalGraphRuntimeIndexSnapshot,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        return cast(
            MetaGraphInvokeFunctionResponse,
            await self.graph_gateway.invoke_function(
                request=request,
                graph_context=index,
            ),
        )

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        return cast(
            MetaGraphInvokeFunctionResponse,
            await self.graph_gateway.invoke_function(request=request),
        )


@dataclass(frozen=True, slots=True)
class ServiceHostMetaGraphInvocationBackend:
    graph_gateway: ServiceGraphGateway
    graph_context: object | None = None

    async def invoke_function(
        self,
        request: LocalGraphInvokeFunctionInput,
    ) -> LocalGraphCommitReceipt:
        graph_request = meta_graph_invoke_function_request_from_runtime_input(request)
        response = await self.graph_gateway.invoke_function(
            request=graph_request,
            graph_context=self.graph_context or request.index,
        )
        return meta_graph_commit_receipt_from_meta_response(response)


@dataclass(frozen=True, slots=True)
class MetaSdkServiceHostRuntime:
    """Runtime-shaped adapter over the ServiceHost Meta SDK graph gateway."""

    manifest_path: Path
    graph_gateway: ServiceGraphGateway
    index: LocalGraphRuntimeIndexSnapshot
    environment_id: UUID
    graph_context: object | None = None

    @property
    def invoker(self) -> MetaSdkServiceHostInvoker:
        return MetaSdkServiceHostInvoker(graph_gateway=self.graph_gateway)

    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> object:
        context_kwargs: dict[str, object] = {
            "index": self.index,
            "projection_hash_by_name": _projection_hash_by_name_from_index(self.index),
            "runtime_graph_ids": (),
            "composition_context_id": self.environment_id,
            "runtime_handler_provider_import_roots": (
                self.index.runtime_handler_provider_import_roots
            ),
        }
        implementation_policy = getattr(
            self.graph_context,
            "implementation_policy",
            None,
        )
        if implementation_policy is not None:
            context_kwargs["implementation_policy"] = implementation_policy
        runtime = LocalGraphRuntime(
            backend=ServiceHostMetaGraphInvocationBackend(
                graph_gateway=self.graph_gateway,
                graph_context=self.graph_context,
            ),
            context=LocalGraphRuntimeContext(**context_kwargs),
        )
        return runtime.bind(
            projection=projection,
            branch_id=branch_id,
            actor_id=actor_id,
        )


def _projection_hash_by_name_from_index(
    index: LocalGraphRuntimeIndexSnapshot,
) -> dict[str, str]:
    projection_hash_by_name: dict[str, str] = {}
    for projection_hash, opg in index.opg_by_hash.items():
        name = opg.name.strip()
        projection_hash_token = projection_hash.strip()
        if not name or not projection_hash_token:
            continue
        existing = projection_hash_by_name.get(name)
        if existing is not None and existing != projection_hash_token:
            raise ValueError(
                "Conflicting projection hashes for authored projection name "
                f"{name!r}: {existing!r} != {projection_hash_token!r}"
            )
        projection_hash_by_name[name] = projection_hash_token
    return projection_hash_by_name


@dataclass(frozen=True, slots=True)
class HostedImplementationLanes:
    api: MaterializationLaneContext
    api_call: MaterializationLaneContext
    service_config: MaterializationLaneContext
    service: MaterializationLaneContext


@dataclass(frozen=True, slots=True)
class ActivatedImplementationRuntimeContext:
    runtime: Any
    environment_config_id: UUID
    index: LocalGraphRuntimeIndexSnapshot
    lanes: HostedImplementationLanes
    runtime_index_source: str


@dataclass(frozen=True, slots=True)
class HostedRuntimeManifestContext:
    environment_config_id: UUID
    manifest_path: Path
    source: str


@dataclass(frozen=True, slots=True)
class ServiceProtocolRuntimeEnvironment:
    id: str


@dataclass(frozen=True, slots=True)
class ServiceProtocolRuntimeManifest:
    environment: ServiceProtocolRuntimeEnvironment


class ServiceProtocolRuntimeArtifactResolver:
    runtime_context_source = "service_protocol_runtime_artifacts"

    def __init__(self, resolution: Any) -> None:
        self._resolution = resolution
        self._runtime_resolution = getattr(resolution, "runtime_resolution", resolution)

    def resolve_manifest_path(self, *, environment_id: UUID) -> Path:
        _ = environment_id
        return self._manifest_path()

    async def get_manifest(self) -> tuple[Path, ServiceProtocolRuntimeManifest]:
        environment_config_id = getattr(
            self._runtime_resolution,
            "environment_config_id",
            None,
        )
        if environment_config_id is None:
            environment_handle = str(
                getattr(self._runtime_resolution, "environment_handle", "")
                or "service-protocol-runtime"
            )
            environment_config_id = uuid5(
                NAMESPACE_URL,
                f"aware-service-protocol-runtime:{environment_handle}",
            )
        return (
            self._manifest_path(),
            ServiceProtocolRuntimeManifest(
                environment=ServiceProtocolRuntimeEnvironment(
                    id=str(environment_config_id)
                )
            ),
        )

    def _manifest_path(self) -> Path:
        raw_manifest_path = getattr(self._runtime_resolution, "manifest_path", None)
        if raw_manifest_path is None:
            raw_manifest_path = getattr(self._resolution, "manifest_path")
        return Path(raw_manifest_path).expanduser().resolve()


class WorkspaceRevisionRuntimeContextResolver:
    """Initial runtime context for committed ServicePackage activation."""

    runtime_context_source = "workspace_revision_runtime_context"

    def __init__(self, *, manifest_path: Path, workspace_revision_id: UUID) -> None:
        self._manifest_path = manifest_path.expanduser().resolve()
        self._runtime_scope_id = uuid5(
            NAMESPACE_URL,
            f"aware-workspace-revision-runtime:{workspace_revision_id}",
        )

    async def get_manifest(self) -> tuple[Path, ServiceProtocolRuntimeManifest]:
        return (
            self._manifest_path,
            ServiceProtocolRuntimeManifest(
                environment=ServiceProtocolRuntimeEnvironment(
                    id=str(self._runtime_scope_id)
                )
            ),
        )


class MissingServiceHostRuntimeArtifactResolver:
    runtime_context_source = "missing_servicehost_runtime_artifacts"

    async def get_service_provider_modules(self, *, surface: str) -> tuple[str, ...]:
        _ = surface
        return ()

    async def get_service_surface_paths(self, *, surface: str) -> tuple[Path, ...]:
        _ = surface
        return ()

    async def get_manifest(self) -> tuple[Path, object]:
        self._raise_missing_runtime_artifacts()

    def _raise_missing_runtime_artifacts(self) -> NoReturn:
        raise RuntimeError(
            "ServiceHost activation requires ontology runtime artifact sources "
            "from Service protocol resolution or a generated Environment API "
            "route. The legacy Environment runtime manifest resolver is retired."
        )


async def resolve_hosted_runtime_manifest_context(
    resolver: Any,
) -> HostedRuntimeManifestContext:
    get_manifest = getattr(resolver, "get_manifest", None)
    if callable(get_manifest):
        get_manifest_fn = cast(Callable[[], Awaitable[tuple[Any, Any]]], get_manifest)
        manifest_path, manifest = await get_manifest_fn()
        return HostedRuntimeManifestContext(
            environment_config_id=UUID(manifest.environment.id),
            manifest_path=Path(manifest_path).expanduser().resolve(),
            source=str(getattr(resolver, "runtime_context_source", "manifest")),
        )
    raise RuntimeError(
        "ServiceHost runtime context requires resolver.get_manifest() backed by "
        "ontology runtime artifacts; hosted runtime fallback is retired."
    )


def meta_graph_invoke_function_request_from_runtime_input(
    request: LocalGraphInvokeFunctionInput,
) -> MetaGraphInvokeFunctionRequest:
    return MetaGraphInvokeFunctionRequest(
        actor_id=request.actor_id,
        domain_branch_id=request.domain_branch_id,
        domain_projection_hash=request.domain_projection_hash,
        call_target=MetaGraphFunctionCallTarget(request.call_target.value),
        target_object_id=request.target_object_id,
        object_projection_graph_id=request.object_projection_graph_id,
        function_id=request.function_id,
        args=JsonArray(list(request.args)),
        kwargs=JsonObject(dict(request.kwargs)),
        expected_graph_hash_pre=request.expected_graph_hash_pre,
        expected_head_commit_id=request.expected_head_commit_id,
        commit=request.commit,
        publish=request.publish,
    )


def meta_graph_commit_receipt_from_meta_response(
    response: MetaGraphInvokeFunctionResponse,
) -> LocalGraphCommitReceipt:
    return LocalGraphCommitReceipt(
        status=str(response.status),
        actor_id=response.actor_id,
        domain_branch_id=response.domain_branch_id,
        domain_projection_hash=response.domain_projection_hash,
        payload=response.payload,
        error=response.error,
        logs=tuple(response.logs or ()),
        execution_time_ms=response.execution_time_ms,
        root_object_id=response.root_object_id,
        graph_hash_pre=response.graph_hash_pre,
        graph_hash_post=response.graph_hash_post,
        changes=JsonArray(list(response.changes or ())),
        function_call_id=response.function_call_id,
        function_call_response_id=response.function_call_response_id,
        commit_id=response.domain_commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
    )


def required_meta_invocation_uuid(
    *,
    value: UUID | None,
    name: str,
) -> UUID:
    if value is None:
        raise RuntimeError(
            "ServiceHost Meta graph invocation is missing required "
            f"orchestration field: {name}"
        )
    return value


def build_implementation_package_lanes(
    *,
    runtime: Any | None,
    index: Any,
    environment_id: UUID,
) -> HostedImplementationLanes:
    thread_id = stable_boot_thread_id(environment_id=environment_id)
    branch_id = stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )

    def _lane(projection: str) -> MaterializationLaneContext:
        resolved_projection = resolve_canonical_service_host_projection(
            index=index,
            projection=projection,
        )
        if runtime is None:
            return MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=resolve_runtime_lane_projection_hash(
                    index=index,
                    projection=resolved_projection,
                ),
            )
        return bind_service_host_runtime_lane(
            runtime=runtime,
            projection=resolved_projection,
            branch_id=branch_id,
        )

    return HostedImplementationLanes(
        api=_lane("Api"),
        api_call=_lane("ApiCall"),
        service_config=_lane("ServiceConfig"),
        service=_lane("Service"),
    )


def bind_service_host_runtime_lane(
    *,
    runtime: Any,
    projection: str,
    branch_id: UUID,
) -> MaterializationLaneContext:
    bind = getattr(runtime, "bind", None)
    if not callable(bind):
        raise RuntimeError(
            "ServiceHost activation runtime must expose Meta graph bind(); "
            "legacy runtime lane binding is not supported in ServiceHost "
            "activation."
        )
    return cast(
        MaterializationLaneContext,
        bind(
            projection=projection,
            branch_id=branch_id,
        ),
    )


__all__ = [
    "ActivatedImplementationRuntimeContext",
    "HostedImplementationLanes",
    "HostedRuntimeManifestContext",
    "MetaSdkServiceHostRuntime",
    "MissingServiceHostRuntimeArtifactResolver",
    "ReadOnlyCommittedServiceHostRuntime",
    "ServiceProtocolRuntimeArtifactResolver",
    "ServiceProtocolRuntimeEnvironment",
    "ServiceProtocolRuntimeManifest",
    "WorkspaceRevisionRuntimeContextResolver",
    "bind_service_host_runtime_lane",
    "build_implementation_package_lanes",
    "meta_graph_invoke_function_request_from_runtime_input",
    "meta_graph_commit_receipt_from_meta_response",
    "required_meta_invocation_uuid",
    "resolve_hosted_runtime_manifest_context",
]
