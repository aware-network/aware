from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    GetLaneHeadRequest,
    GetObjectInstanceGraphCommitRequest,
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
)
from aware_meta_sdk.client import MetaSdkClient, MetaSdkError
from aware_meta_service.local_sdk import (
    LocalMetaAwarePackageManifestSdkSession,
    build_local_meta_service_api_session_for_aware_package_manifests,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetLaneHeadResponse,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphGetObjectInstanceGraphCommitResponse,
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
    MetaGraphResolveProjectionRequest,
    MetaGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphResolveProjectionRequest,
)
from aware_types import JsonArray, JsonObject


class _EnvironmentFunctionCallClient(Protocol):
    async def invoke_function(
        self,
        request: InvokeFunctionRequest,
    ) -> object: ...


class _EnvironmentLaneHeadClient(Protocol):
    async def get_lane_head(
        self,
        request: GetLaneHeadRequest,
    ) -> object: ...


class _EnvironmentOigCommitClient(Protocol):
    async def get_object_instance_graph_commit(
        self,
        request: GetObjectInstanceGraphCommitRequest,
    ) -> object: ...


class _EnvironmentApiClient(Protocol):
    @property
    def function_call(self) -> _EnvironmentFunctionCallClient: ...

    @property
    def lane_head(self) -> _EnvironmentLaneHeadClient: ...

    @property
    def object_instance_graph_commit(self) -> _EnvironmentOigCommitClient: ...


class EnvironmentRoutedGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


class _OntologyProjectionGraphClient(Protocol):
    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> object: ...


class _OntologyProjectionApi(Protocol):
    @property
    def graph(self) -> _OntologyProjectionGraphClient: ...


class OntologyProjectionRoutedGeneratedApiClient(Protocol):
    @property
    def ontology(self) -> _OntologyProjectionApi: ...


@dataclass(frozen=True, slots=True)
class MetaSdkOntologyProjectionAuthorityRoute:
    """Target Ontology service authority for remote projection resolution."""

    api_client: OntologyProjectionRoutedGeneratedApiClient
    authority_ref: str | None = None
    provider_service_package_name: str | None = None
    provider_node_id: UUID | None = None
    host_id: str | None = None
    route_connection_id: UUID | None = None
    service_name: str | None = None
    provider_set_id: str | None = None
    workspace_revision_id: UUID | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None

    def describe(self) -> str:
        fields: list[str] = []
        if _clean(self.authority_ref):
            fields.append(f"authority_ref={self.authority_ref!r}")
        if _clean(self.provider_service_package_name):
            fields.append(
                "provider_service_package_name="
                f"{self.provider_service_package_name!r}"
            )
        if self.provider_node_id is not None:
            fields.append(f"provider_node_id={self.provider_node_id}")
        if _clean(self.host_id):
            fields.append(f"host_id={self.host_id!r}")
        if self.route_connection_id is not None:
            fields.append(f"route_connection_id={self.route_connection_id}")
        if _clean(self.service_name):
            fields.append(f"service_name={self.service_name!r}")
        if _clean(self.provider_set_id):
            fields.append(f"provider_set_id={self.provider_set_id!r}")
        if self.workspace_revision_id is not None:
            fields.append(f"workspace_revision_id={self.workspace_revision_id}")
        if _clean(self.workspace_deployment_revision_id):
            fields.append(
                "workspace_deployment_revision_id="
                f"{self.workspace_deployment_revision_id!r}"
            )
        if _clean(self.workspace_deployment_channel):
            fields.append(
                "workspace_deployment_channel=" f"{self.workspace_deployment_channel!r}"
            )
        if _clean(self.workspace_deployment_artifact_key):
            fields.append(
                "workspace_deployment_artifact_key="
                f"{self.workspace_deployment_artifact_key!r}"
            )
        return ", ".join(fields) if fields else "unlabeled ontology authority"


@dataclass(frozen=True, slots=True)
class MetaSdkEnvironmentRoute:
    """Environment API route used by Meta SDK remote graph execution."""

    api_client: EnvironmentRoutedGeneratedApiClient
    environment_id: UUID
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    ontology_projection_route: MetaSdkOntologyProjectionAuthorityRoute | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentRoutedMetaGeneratedApiClient:
    """Meta generated API adapter backed by Environment graph APIs."""

    route: MetaSdkEnvironmentRoute

    @property
    def meta(self) -> "_EnvironmentRoutedMetaNamespace":
        return _EnvironmentRoutedMetaNamespace(route=self.route)


@dataclass(frozen=True, slots=True)
class _EnvironmentRoutedMetaNamespace:
    route: MetaSdkEnvironmentRoute

    @property
    def graph(self) -> "_EnvironmentRoutedMetaGraphClient":
        return _EnvironmentRoutedMetaGraphClient(route=self.route)

    @property
    def diagnostics(self) -> "_UnsupportedMetaCapability":
        return _UnsupportedMetaCapability("meta.diagnostics")

    @property
    def package(self) -> "_UnsupportedMetaCapability":
        return _UnsupportedMetaCapability("meta.package")

    @property
    def persistence(self) -> "_UnsupportedMetaCapability":
        return _UnsupportedMetaCapability("meta.persistence")

    @property
    def runtime_read_model(self) -> "_UnsupportedMetaCapability":
        return _UnsupportedMetaCapability("meta.runtime_read_model")


@dataclass(frozen=True, slots=True)
class _UnsupportedMetaCapability:
    capability: str

    def __getattr__(self, operation: str) -> object:
        async def _unsupported(*_args: object, **_kwargs: object) -> object:
            raise MetaSdkError(
                "Environment-routed Meta SDK does not support "
                f"{self.capability}.{operation}; use a local Meta session or a "
                "dedicated service API route for this capability."
            )

        return _unsupported


@dataclass(frozen=True, slots=True)
class _EnvironmentRoutedMetaGraphClient:
    route: MetaSdkEnvironmentRoute

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        response = (
            await self.route.api_client.environment.function_call.invoke_function(
                _environment_invoke_request(route=self.route, request=request)
            )
        )
        return _meta_invoke_response(response)

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse:
        response = await self.route.api_client.environment.lane_head.get_lane_head(
            GetLaneHeadRequest(
                actor_id=request.actor_id or self.route.actor_id,
                environment_id=self.route.environment_id,
                process_id=self.route.process_id,
                thread_id=self.route.thread_id,
                branch_id=request.domain_branch_id,
                projection_hash=request.domain_projection_hash,
            )
        )
        return MetaGraphGetLaneHeadResponse(
            status=str(getattr(response, "status")),
            actor_id=getattr(response, "actor_id", None),
            domain_branch_id=_required_uuid(
                getattr(response, "branch_id", request.domain_branch_id),
                field_name="branch_id",
            ),
            domain_projection_hash=_required_text(
                getattr(response, "projection_hash", request.domain_projection_hash),
                field_name="projection_hash",
            ),
            error=getattr(response, "error", None),
            domain_commit_id=getattr(response, "commit_id", None),
            graph_hash_post=getattr(response, "graph_hash_post", None),
            object_instance_graph_id=getattr(
                response,
                "object_instance_graph_id",
                None,
            ),
            root_object_id=getattr(response, "root_object_id", None),
            head_version=getattr(response, "head_version", None),
        )

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse:
        response = await self.route.api_client.environment.object_instance_graph_commit.get_object_instance_graph_commit(
            GetObjectInstanceGraphCommitRequest(
                actor_id=request.actor_id or self.route.actor_id,
                environment_id=self.route.environment_id,
                process_id=self.route.process_id,
                thread_id=self.route.thread_id,
                branch_id=request.domain_branch_id,
                projection_hash=request.domain_projection_hash,
                commit_id=request.domain_commit_id,
            )
        )
        return MetaGraphGetObjectInstanceGraphCommitResponse(
            status=str(getattr(response, "status")),
            actor_id=getattr(response, "actor_id", None),
            domain_branch_id=_required_uuid(
                getattr(response, "branch_id", request.domain_branch_id),
                field_name="branch_id",
            ),
            domain_projection_hash=_required_text(
                getattr(response, "projection_hash", request.domain_projection_hash),
                field_name="projection_hash",
            ),
            domain_commit_id=getattr(response, "commit_id", None),
            object_instance_graph_commit_id=getattr(
                response,
                "object_instance_graph_commit_id",
                None,
            ),
            commit=getattr(response, "commit", None),
            error=getattr(response, "error", None),
        )

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse:
        ontology_route = self.route.ontology_projection_route
        if ontology_route is None:
            return MetaGraphResolveProjectionResponse(
                status="failed",
                actor_id=request.actor_id or self.route.actor_id,
                projection_name=request.projection_name,
                projection_hash=request.projection_hash,
                object_projection_graph_id=request.object_projection_graph_id,
                error=(
                    "Environment-routed Meta SDK projection resolution requires "
                    "a configured Ontology projection authority route."
                ),
            )
        response = await ontology_route.api_client.ontology.graph.resolve_projection(
            OntologyGraphResolveProjectionRequest(
                actor_id=request.actor_id or self.route.actor_id,
                projection_name=request.projection_name,
                projection_hash=request.projection_hash,
                object_projection_graph_id=request.object_projection_graph_id,
                include_available=request.include_available,
            )
        )
        return _meta_projection_response_from_ontology(
            response,
            request=request,
            route=ontology_route,
            actor_id=request.actor_id or self.route.actor_id,
        )


def build_environment_routed_meta_generated_api_client(
    *,
    route: MetaSdkEnvironmentRoute,
) -> EnvironmentRoutedMetaGeneratedApiClient:
    """Build a Meta generated API adapter that routes through Environment."""

    return EnvironmentRoutedMetaGeneratedApiClient(route=route)


def build_environment_routed_meta_sdk_client(
    *,
    route: MetaSdkEnvironmentRoute,
) -> MetaSdkClient:
    """Build a Meta SDK client backed by Environment graph APIs."""

    return MetaSdkClient(
        api_client=build_environment_routed_meta_generated_api_client(route=route),
    )


def build_environment_routed_meta_sdk_session_for_aware_package_manifests(
    *,
    route: MetaSdkEnvironmentRoute,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None = None,
    aware_root: Path | None = None,
    composite_name: str = "Aware Environment Routed Meta SDK Package Session",
    projection_name: str | None = None,
    actor_id: UUID | None = None,
    branch_id: UUID | None = None,
    endpoint: str = "aware-meta-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_meta",
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    generated_language_handler_module: object | None = None,
    generated_language_handler_modules: Sequence[object] = (),
    generated_language_handler_resolver: object | None = None,
    strict_package_graph_cache: bool = False,
    source_analysis_allowed_manifest_paths: Iterable[Path] = (),
) -> LocalMetaAwarePackageManifestSdkSession:
    """
    Build a package-manifest Meta SDK session that executes via Environment.

    Local package manifests still provide projection/function/class binding truth.
    Graph mutation, lane-head reads, and commit reads are routed through the
    Environment API client carried by ``route``.
    """

    service_session = build_local_meta_service_api_session_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=workspace_root,
        aware_root=aware_root,
        composite_name=composite_name,
        projection_name=projection_name,
        actor_id=actor_id or route.actor_id,
        branch_id=branch_id or route.branch_id,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
        invocation_context=invocation_context,
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        generated_language_handler_module=generated_language_handler_module,
        generated_language_handler_modules=generated_language_handler_modules,
        generated_language_handler_resolver=generated_language_handler_resolver,
        strict_package_graph_cache=strict_package_graph_cache,
        source_analysis_allowed_manifest_paths=source_analysis_allowed_manifest_paths,
    )
    api_client = build_environment_routed_meta_generated_api_client(route=route)
    return LocalMetaAwarePackageManifestSdkSession(
        sdk=MetaSdkClient(api_client=api_client),
        api_client=api_client,
        service_session=service_session,
    )


def build_environment_routed_meta_sdk_client_for_aware_package_manifests(
    **kwargs: Any,
) -> MetaSdkClient:
    """Build an Environment-routed Meta SDK client from package manifests."""

    return build_environment_routed_meta_sdk_session_for_aware_package_manifests(
        **kwargs,
    ).sdk


def _environment_invoke_request(
    *,
    route: MetaSdkEnvironmentRoute,
    request: MetaGraphInvokeFunctionRequest,
) -> InvokeFunctionRequest:
    return InvokeFunctionRequest(
        actor_id=request.actor_id or route.actor_id,
        environment_id=route.environment_id,
        process_id=route.process_id,
        thread_id=route.thread_id,
        branch_id=request.domain_branch_id or route.branch_id,
        projection_hash=request.domain_projection_hash or route.projection_hash,
        call_target=InvokeFunctionCallTarget(request.call_target.value),
        object_id=request.target_object_id,
        object_projection_graph_id=request.object_projection_graph_id,
        function_id=request.function_id,
        args=JsonArray(list(request.args)),
        kwargs=JsonObject(dict(request.kwargs)),
        expected_graph_hash_pre=request.expected_graph_hash_pre,
        expected_head_commit_id=request.expected_head_commit_id,
        commit=request.commit,
        publish=request.publish,
    )


def _meta_invoke_response(response: object) -> MetaGraphInvokeFunctionResponse:
    return MetaGraphInvokeFunctionResponse(
        status=str(getattr(response, "status")),
        actor_id=getattr(response, "actor_id", None),
        domain_branch_id=getattr(response, "branch_id", None),
        domain_projection_hash=getattr(response, "projection_hash", None),
        payload=getattr(response, "payload", None),
        error=getattr(response, "error", None),
        logs=list(getattr(response, "logs", ()) or ()),
        execution_time_ms=getattr(response, "execution_time_ms", None),
        root_object_id=getattr(response, "root_object_id", None),
        graph_hash_pre=getattr(response, "graph_hash_pre", None),
        graph_hash_post=getattr(response, "graph_hash_post", None),
        changes=JsonArray(list(getattr(response, "changes", ()) or ())),
        domain_commit_id=getattr(response, "commit_id", None),
        object_instance_graph_commit_id=getattr(
            response,
            "object_instance_graph_commit_id",
            None,
        ),
        function_call_id=getattr(response, "function_call_id", None),
        function_call_response_id=getattr(response, "function_call_response_id", None),
    )


def _meta_projection_response_from_ontology(
    response: object,
    *,
    request: MetaGraphResolveProjectionRequest,
    route: MetaSdkOntologyProjectionAuthorityRoute,
    actor_id: UUID | None,
) -> MetaGraphResolveProjectionResponse:
    status = str(getattr(response, "status", "failed"))
    error = getattr(response, "error", None)
    if status.strip().casefold() != "succeeded" and error is None:
        error = (
            "Ontology projection authority route failed projection resolution: "
            f"{route.describe()}"
        )
    return MetaGraphResolveProjectionResponse(
        status=status,
        actor_id=getattr(response, "actor_id", None) or actor_id,
        projection_name=getattr(response, "projection_name", request.projection_name),
        projection_hash=getattr(response, "projection_hash", request.projection_hash),
        object_projection_graph_id=getattr(
            response,
            "object_projection_graph_id",
            request.object_projection_graph_id,
        ),
        object_projection_graph_identity_id=getattr(
            response,
            "object_projection_graph_identity_id",
            None,
        ),
        object_config_graph_id=getattr(response, "object_config_graph_id", None),
        object_config_graph_identity_id=getattr(
            response,
            "object_config_graph_identity_id",
            None,
        ),
        language=getattr(response, "language", None),
        supports_virtual_build=getattr(response, "supports_virtual_build", None),
        matched_projection_hashes=list(
            getattr(response, "matched_projection_hashes", ()) or ()
        ),
        available_projection_names=list(
            getattr(response, "available_projection_names", ()) or ()
        ),
        error=error,
    )


def _required_uuid(value: object, *, field_name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if value is None:
        raise MetaSdkError(
            f"Environment-routed Meta SDK missing required UUID: {field_name}"
        )
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise MetaSdkError(
            f"Environment-routed Meta SDK invalid UUID for {field_name}: {value!r}"
        ) from exc


def _required_text(value: object, *, field_name: str) -> str:
    if value is None:
        raise MetaSdkError(
            f"Environment-routed Meta SDK missing required text: {field_name}"
        )
    text = str(value).strip()
    if not text:
        raise MetaSdkError(
            f"Environment-routed Meta SDK missing required text: {field_name}"
        )
    return text


def _clean(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "EnvironmentRoutedGeneratedApiClient",
    "EnvironmentRoutedMetaGeneratedApiClient",
    "MetaSdkEnvironmentRoute",
    "MetaSdkOntologyProjectionAuthorityRoute",
    "OntologyProjectionRoutedGeneratedApiClient",
    "build_environment_routed_meta_generated_api_client",
    "build_environment_routed_meta_sdk_client",
    "build_environment_routed_meta_sdk_client_for_aware_package_manifests",
    "build_environment_routed_meta_sdk_session_for_aware_package_manifests",
]
