from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
import tomllib
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api.invocation import ApiInvocationIndex, LoadedApiInvocationManifest
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
    decode_api_endpoint_response_payload,
    decode_api_stream_event_payload,
    resolve_api_endpoint_model_class,
)
from aware_meta_service_api import AwareMetaServiceApiClient
from aware_meta_service_protocol.protocols import ENDPOINT_BINDINGS
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiMaterializationContext,
    service_api_host_context,
)
from aware_service_runtime.contracts import (
    ServiceGraphContextProvider,
    ServiceGraphGateway,
    ServiceOperationContext,
)
from pydantic import BaseModel

from .api_service_protocol import build_aware_meta_service_protocol_handler


DEFAULT_META_LOCAL_API_ENDPOINT = "aware-meta-service://local"
DEFAULT_META_SERVICE_NAME = "aware_meta"
DEFAULT_META_LOCAL_PROJECTION_HASH = "meta.sdk.local"


@dataclass(frozen=True, slots=True)
class LocalMetaServiceApiConfig:
    endpoint: str = DEFAULT_META_LOCAL_API_ENDPOINT
    request_timeout_s: float = 10.0
    service_name: str = DEFAULT_META_SERVICE_NAME


@dataclass(frozen=True, slots=True)
class _UnsupportedRawMetaTransport:
    endpoint: str

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        _ = (invocation, timeout_s)
        raise NotImplementedError(
            "Local Meta service API client routes generated endpoint calls "
            "through the Meta service protocol; raw transport invocation is "
            "intentionally unavailable."
        )


class LocalMetaServiceAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker over one in-process Meta service protocol handler."""

    def __init__(
        self,
        *,
        handler: object | None = None,
        operation_context: ServiceOperationContext | None = None,
        graph_gateway: ServiceGraphGateway | None = None,
        graph_context_provider: ServiceGraphContextProvider | None = None,
        materialization: ServiceApiMaterializationContext | None = None,
        endpoint: str = DEFAULT_META_LOCAL_API_ENDPOINT,
        request_timeout_s: float = 10.0,
        service_name: str = DEFAULT_META_SERVICE_NAME,
        invocation_context: Mapping[str, object] | None = None,
        event_bus: object | None = None,
        event_store: object | None = None,
        commit_store: object | None = None,
        runtime: object | None = None,
        generated_language_handler_resolver: object | None = None,
        generated_language_handler_module: object | None = None,
    ) -> None:
        self._handler = handler or build_aware_meta_service_protocol_handler(
            event_bus=event_bus,  # type: ignore[arg-type]
            event_store=event_store,  # type: ignore[arg-type]
            commit_store=commit_store,  # type: ignore[arg-type]
            runtime=runtime,
            generated_language_handler_resolver=(
                generated_language_handler_resolver  # type: ignore[arg-type]
            ),
            generated_language_handler_module=(
                generated_language_handler_module  # type: ignore[arg-type]
            ),
        )
        self._operation_context = operation_context
        self._graph_gateway = graph_gateway
        self._graph_context_provider = graph_context_provider
        self._materialization = materialization
        self._invocation_context = invocation_context
        self._local_config = LocalMetaServiceApiConfig(
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
        )
        super().__init__(_UnsupportedRawMetaTransport(endpoint=endpoint))

    @property
    def local_config(self) -> LocalMetaServiceApiConfig:
        return self._local_config

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        _ = timeout_s or self._local_config.request_timeout_s
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        request = _typed_request_from_prepared(
            class_ref=prepared.request_python_model_ref or prepared.request_class_ref,
            payload=prepared.request_payload,
        )
        response = await dispatch_meta_service_protocol_endpoint(
            handler=self._handler,
            endpoint_ref=prepared.endpoint.endpoint_ref,
            request=request,
            operation_context=self._operation_context,
            graph_gateway=self._graph_gateway,
            graph_context_provider=self._graph_context_provider,
            materialization=self._materialization,
            service_name=self._local_config.service_name,
            invocation_context=self._invocation_context,
        )
        return decode_api_endpoint_response_payload(
            prepared=prepared,
            response_payload=response,
        )

    async def stream_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> AsyncIterator[Any]:
        _ = timeout_s or self._local_config.request_timeout_s
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        if prepared.stream_mode is None:
            raise ValueError(
                "Meta API endpoint does not declare a stream contract: "
                f"{prepared.endpoint.endpoint_ref!r}."
            )
        request = _typed_request_from_prepared(
            class_ref=prepared.request_python_model_ref or prepared.request_class_ref,
            payload=prepared.request_payload,
        )
        async for event in dispatch_meta_service_protocol_stream_endpoint(
            handler=self._handler,
            endpoint_ref=prepared.endpoint.endpoint_ref,
            request=request,
            operation_context=self._operation_context,
            graph_gateway=self._graph_gateway,
            graph_context_provider=self._graph_context_provider,
            materialization=self._materialization,
            service_name=self._local_config.service_name,
            invocation_context=self._invocation_context,
        ):
            yield decode_api_stream_event_payload(
                prepared=prepared,
                event_payload=event,
            )


async def dispatch_meta_service_protocol_endpoint(
    *,
    handler: object,
    endpoint_ref: str,
    request: BaseModel,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    graph_context_provider: ServiceGraphContextProvider | None = None,
    materialization: ServiceApiMaterializationContext | None = None,
    service_name: str = DEFAULT_META_SERVICE_NAME,
    invocation_context: Mapping[str, object] | None = None,
) -> object:
    binding = _binding_for_endpoint(endpoint_ref)
    with service_api_host_context(
        operation_context=operation_context or _default_operation_context(request),
        graph_gateway=graph_gateway,
        graph_context_provider=graph_context_provider,
        service_name=service_name,
        invocation_context=invocation_context,
        materialization=materialization,
    ):
        return await binding.invoke(handler, request)


async def dispatch_meta_service_protocol_stream_endpoint(
    *,
    handler: object,
    endpoint_ref: str,
    request: BaseModel,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    graph_context_provider: ServiceGraphContextProvider | None = None,
    materialization: ServiceApiMaterializationContext | None = None,
    service_name: str = DEFAULT_META_SERVICE_NAME,
    invocation_context: Mapping[str, object] | None = None,
) -> AsyncIterator[object]:
    binding = _binding_for_endpoint(endpoint_ref)
    if binding.stream_invoke is None:
        raise ValueError(
            "Meta service protocol endpoint does not expose a stream: "
            f"{endpoint_ref!r}."
        )
    with service_api_host_context(
        operation_context=operation_context or _default_operation_context(request),
        graph_gateway=graph_gateway,
        graph_context_provider=graph_context_provider,
        service_name=service_name,
        invocation_context=invocation_context,
        materialization=materialization,
    ):
        async for event in binding.stream_invoke(handler, request):
            yield event


@dataclass(frozen=True, slots=True)
class LocalMetaServiceApiSession:
    api_client: AwareMetaServiceApiClient
    local_client: LocalMetaServiceAwareApiClient


@dataclass(frozen=True, slots=True)
class LocalMetaAwarePackageManifestResolver:
    runtime: object
    runtime_context: object

    @property
    def graph_context(self) -> object:
        return self.runtime_context

    @property
    def graph_catalog(self) -> object:
        return getattr(self.runtime_context, "index")

    def projection_hash(self, projection_name: str) -> str:
        resolver = getattr(self.runtime_context, "projection_hash_for_name", None)
        if callable(resolver):
            return str(resolver(projection_name))
        target = projection_name.strip()
        projection_hash_by_name = getattr(
            self.runtime_context,
            "projection_hash_by_name",
            {},
        )
        projection_hash = projection_hash_by_name.get(target)
        if projection_hash is None:
            raise ValueError(
                f"Projection {projection_name!r} was not found in local Meta session."
            )
        return str(projection_hash)

    def object_projection_graph_id(self, projection_name: str) -> UUID:
        projection_hash = self.projection_hash(projection_name)
        opg = self.object_projection_graph_for_projection_hash(projection_hash)
        return UUID(str(getattr(opg, "id")))

    def object_projection_graph_for_projection_hash(
        self,
        projection_hash: str,
    ) -> object:
        opg = getattr(self.graph_catalog, "opg_by_hash", {}).get(projection_hash)
        if opg is None:
            raise ValueError(
                "ObjectProjectionGraph was not found for projection hash "
                f"{projection_hash!r}."
            )
        return opg

    def object_projection_graphs_for_class_config_id(
        self,
        class_config_id: UUID,
    ) -> tuple[object, ...]:
        opgs: list[object] = []
        for opg in getattr(self.graph_catalog, "opg_by_id", {}).values():
            for node in getattr(opg, "object_projection_graph_nodes", ()) or ():
                if getattr(node, "class_config_id", None) == class_config_id:
                    opgs.append(opg)
                    break
        return tuple(opgs)

    def function_id(
        self,
        *,
        class_name: str,
        function_name: str,
        is_constructor: bool | None = None,
    ) -> UUID:
        class_config = self.class_config(class_name)
        matches = []
        for edge in getattr(class_config, "class_config_function_configs", ()) or ():
            function_config = getattr(edge, "function_config", None)
            if function_config is None:
                continue
            if getattr(function_config, "name", None) != function_name:
                continue
            if (
                is_constructor is not None
                and bool(getattr(edge, "is_constructor", False)) is not is_constructor
            ):
                continue
            matches.append(function_config)
        if len(matches) != 1:
            raise ValueError(
                "Expected exactly one local Meta function: "
                f"class_name={class_name!r} function_name={function_name!r} "
                f"is_constructor={is_constructor!r} matches={len(matches)}"
            )
        return UUID(str(getattr(matches[0], "id")))

    def class_config(self, class_name: str) -> object:
        matches = [
            class_config
            for class_config in getattr(
                self.graph_catalog,
                "class_configs_by_id",
                {},
            ).values()
            if getattr(class_config, "name", None) == class_name
        ]
        if len(matches) != 1:
            raise ValueError(
                "Expected exactly one local Meta class config: "
                f"class_name={class_name!r} matches={len(matches)}"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class LocalMetaAwarePackageManifestApiSession:
    api_client: AwareMetaServiceApiClient
    local_client: LocalMetaServiceAwareApiClient
    resolver: LocalMetaAwarePackageManifestResolver
    operation_context: ServiceOperationContext
    materialization: ServiceApiMaterializationContext

    def projection_hash(self, projection_name: str) -> str:
        return self.resolver.projection_hash(projection_name)

    def object_projection_graph_id(self, projection_name: str) -> UUID:
        return self.resolver.object_projection_graph_id(projection_name)

    def function_id(
        self,
        *,
        class_name: str,
        function_name: str,
        is_constructor: bool | None = None,
    ) -> UUID:
        return self.resolver.function_id(
            class_name=class_name,
            function_name=function_name,
            is_constructor=is_constructor,
        )


def build_local_meta_service_api_session(
    *,
    handler: object | None = None,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    graph_context_provider: ServiceGraphContextProvider | None = None,
    materialization: ServiceApiMaterializationContext | None = None,
    endpoint: str = DEFAULT_META_LOCAL_API_ENDPOINT,
    request_timeout_s: float = 10.0,
    service_name: str = DEFAULT_META_SERVICE_NAME,
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    runtime: object | None = None,
    generated_language_handler_resolver: object | None = None,
    generated_language_handler_module: object | None = None,
) -> LocalMetaServiceApiSession:
    """Build a generated Meta API client plus explicit local client handle."""

    local_client = LocalMetaServiceAwareApiClient(
        handler=handler,
        operation_context=operation_context,
        graph_gateway=graph_gateway,
        graph_context_provider=graph_context_provider,
        materialization=materialization,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
        invocation_context=invocation_context,
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        runtime=runtime,
        generated_language_handler_resolver=generated_language_handler_resolver,
        generated_language_handler_module=generated_language_handler_module,
    )
    return LocalMetaServiceApiSession(
        api_client=AwareMetaServiceApiClient(client=local_client),
        local_client=local_client,
    )


def build_local_meta_service_api_client(
    *,
    handler: object | None = None,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    graph_context_provider: ServiceGraphContextProvider | None = None,
    materialization: ServiceApiMaterializationContext | None = None,
    endpoint: str = DEFAULT_META_LOCAL_API_ENDPOINT,
    request_timeout_s: float = 10.0,
    service_name: str = DEFAULT_META_SERVICE_NAME,
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    runtime: object | None = None,
    generated_language_handler_resolver: object | None = None,
    generated_language_handler_module: object | None = None,
) -> AwareMetaServiceApiClient:
    """Build a generated Meta API client backed by the local protocol."""

    return build_local_meta_service_api_session(
        handler=handler,
        operation_context=operation_context,
        graph_gateway=graph_gateway,
        graph_context_provider=graph_context_provider,
        materialization=materialization,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
        invocation_context=invocation_context,
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        runtime=runtime,
        generated_language_handler_resolver=generated_language_handler_resolver,
        generated_language_handler_module=generated_language_handler_module,
    ).api_client


def build_local_meta_service_api_session_for_aware_package_manifests(
    *,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None = None,
    aware_root: Path | None = None,
    environment_config_id: UUID | None = None,
    composite_name: str = "Aware Local Meta Service Package Session",
    projection_name: str | None = None,
    actor_id: UUID | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    branch_id: UUID | None = None,
    endpoint: str = DEFAULT_META_LOCAL_API_ENDPOINT,
    request_timeout_s: float = 10.0,
    service_name: str = DEFAULT_META_SERVICE_NAME,
    invocation_context: Mapping[str, object] | None = None,
    event_bus: object | None = None,
    event_store: object | None = None,
    commit_store: object | None = None,
    generated_language_handler_module: object | None = None,
    generated_language_handler_modules: Sequence[object] = (),
    generated_language_handler_resolver: object | None = None,
    strict_package_graph_cache: bool = False,
    source_analysis_allowed_manifest_paths: Iterable[Path] = (),
) -> LocalMetaAwarePackageManifestApiSession:
    """Build a local Meta service API session from package manifests.

    This is the service-side bridge used by SDK consumers that want local,
    in-process Meta execution without importing Meta runtime APIs directly.
    """

    from aware_meta.materialization.contracts import (  # noqa: WPS433
        MaterializationLaneContext,
    )
    from aware_meta.runtime import (  # noqa: WPS433
        build_meta_graph_runtime_for_aware_package_manifests,
    )

    resolved_package_manifest_paths = tuple(package_manifest_paths)
    generated_modules = tuple(generated_language_handler_modules)
    if generated_language_handler_module is not None:
        generated_modules = (generated_language_handler_module, *generated_modules)
    if generated_modules and generated_language_handler_resolver is not None:
        raise ValueError(
            "Pass generated_language_handler_module(s) or "
            "generated_language_handler_resolver, not both."
        )
    if not generated_modules and generated_language_handler_resolver is None:
        generated_modules = _load_local_meta_generated_handler_modules(
            package_manifest_paths=resolved_package_manifest_paths,
            workspace_root=workspace_root,
        )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=resolved_package_manifest_paths,
        workspace_root=workspace_root,
        aware_root=aware_root,
        composite_name=composite_name,
        handler_modules=generated_modules,
        bootstrap_modules=generated_modules,
        handler_resolver=generated_language_handler_resolver,  # type: ignore[arg-type]
        strict_package_graph_cache=strict_package_graph_cache,
        source_analysis_allowed_manifest_paths=tuple(
            source_analysis_allowed_manifest_paths
        ),
    )
    runtime_context = getattr(runtime, "context", None)
    if runtime_context is None:
        raise RuntimeError("Local Meta package session requires runtime.context.")
    resolver = LocalMetaAwarePackageManifestResolver(
        runtime=runtime,
        runtime_context=runtime_context,
    )
    projection_hash = (
        resolver.projection_hash(projection_name)
        if projection_name is not None and projection_name.strip()
        else _default_projection_hash(resolver)
    )
    operation_context = ServiceOperationContext(
        actor_id=actor_id or _stable_uuid("actor"),
        environment_id=environment_id or _stable_uuid("environment"),
        process_id=process_id or _stable_uuid("process"),
        thread_id=thread_id or _stable_uuid("thread"),
        branch_id=branch_id or _stable_uuid("branch"),
        projection_hash=projection_hash,
    )
    materialization = ServiceApiMaterializationContext(
        runtime=runtime,
        graph_context=resolver.graph_context,
        target_lane=MaterializationLaneContext(
            branch_id=operation_context.branch_id,
            projection_hash=operation_context.projection_hash,
        ),
    )
    api_session = build_local_meta_service_api_session(
        operation_context=operation_context,
        materialization=materialization,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
        invocation_context=invocation_context,
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        runtime=runtime,
    )
    return LocalMetaAwarePackageManifestApiSession(
        api_client=api_session.api_client,
        local_client=api_session.local_client,
        resolver=resolver,
        operation_context=operation_context,
        materialization=materialization,
    )


def build_local_meta_service_api_client_for_aware_package_manifests(
    **kwargs: Any,
) -> AwareMetaServiceApiClient:
    """Build a local Meta service API client from package manifests."""

    return build_local_meta_service_api_session_for_aware_package_manifests(
        **kwargs
    ).api_client


def object_instance_graph_commit_from_payload(payload: Mapping[str, object]) -> object:
    """Rehydrate a Meta OIG commit model from a service DTO payload."""

    from aware_meta_ontology.graph.instance.object_instance_graph_commit import (  # noqa: WPS433
        ObjectInstanceGraphCommit,
    )

    return ObjectInstanceGraphCommit.model_validate(dict(payload))


def read_local_meta_runtime_read_model(**kwargs: Any) -> object:
    """Read the local Meta runtime read model behind the Meta service boundary."""

    from aware_meta.runtime.read_model_provider import (  # noqa: WPS433
        read_workspace_meta_runtime_read_model,
    )

    return read_workspace_meta_runtime_read_model(**kwargs)


def read_local_meta_api_activation_read_model(**kwargs: Any) -> object:
    """Read the compact local Meta API activation read model behind the service boundary."""

    from aware_meta.runtime.read_model_provider import (  # noqa: WPS433
        read_workspace_meta_api_activation_read_model,
    )

    return read_workspace_meta_api_activation_read_model(**kwargs)


def build_local_meta_commit_store(*, root_dir: Path | None = None) -> object:
    """Build the local Meta commit store behind the Meta service boundary."""

    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore

    return FSCommitStore(root_dir=root_dir)


def build_local_meta_snapshot_store(*, root_dir: Path | None = None) -> object:
    """Build the local Meta snapshot store behind the Meta service boundary."""

    from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore

    return FSSnapshotStore(root_dir=root_dir)


def build_local_meta_oig_materializer(
    *,
    commits: object | None = None,
    snapshots: object | None = None,
    root_dir: Path | None = None,
) -> object:
    """Build the local Meta object-instance materializer."""

    from aware_meta.graph.instance.commit.materializer import (  # noqa: WPS433
        OIGMaterializer,
    )

    resolved_commits = commits
    if resolved_commits is None:
        resolved_commits = build_local_meta_commit_store(root_dir=root_dir)
    resolved_snapshots = snapshots
    if resolved_snapshots is None:
        resolved_snapshots = build_local_meta_snapshot_store(root_dir=root_dir)
    return OIGMaterializer(commits=resolved_commits, snaps=resolved_snapshots)


async def load_local_meta_graph_context(
    *,
    package_manifest_paths: Iterable[Path] = (),
    repo_root: Path | None = None,
) -> object:
    """Load local Meta graph context behind the Meta service boundary."""

    from aware_meta.runtime import (  # noqa: WPS433
        build_meta_graph_runtime_for_aware_package_manifests,
    )

    resolved_repo_root = _resolve_local_meta_repo_root(repo_root)
    package_manifest_paths = _local_meta_graph_context_package_manifest_paths(
        package_manifest_paths=package_manifest_paths,
        repo_root=resolved_repo_root,
    )
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=resolved_repo_root,
        composite_name="Aware Local Meta Graph Context",
    )
    runtime_context = getattr(runtime, "context", None)
    if runtime_context is None:
        raise RuntimeError("Local Meta graph context requires runtime.context.")
    return runtime_context


def _local_meta_graph_context_package_manifest_paths(
    *,
    package_manifest_paths: Iterable[Path],
    repo_root: Path,
) -> tuple[Path, ...]:
    resolved_package_manifest_paths = tuple(package_manifest_paths)
    if resolved_package_manifest_paths:
        return _dedupe_paths(
            [
                path if path.is_absolute() else repo_root / path
                for path in resolved_package_manifest_paths
            ]
        )

    raise RuntimeError(
        "Local Meta graph context requires explicit package manifest paths "
        "supplied by a caller-owned artifact ref rail."
    )


def _resolve_local_meta_repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    raw_repo_root = (os.environ.get("AWARE_REPO_ROOT") or "").strip()
    if raw_repo_root:
        return Path(raw_repo_root).expanduser().resolve()
    raise RuntimeError(
        "Local Meta graph context requires explicit repo_root or AWARE_REPO_ROOT; "
        "public kernel runtime must not discover repository roots"
    )


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(resolved)
    return tuple(result)


async def materialize_local_meta_lane_oig(
    *,
    branch_id: UUID,
    ocg: object,
    opg: object,
    commit_id: UUID | None,
    oig_id: UUID | None = None,
    attribute_configs_by_id: Mapping[UUID, object] | None = None,
    class_configs_by_id: Mapping[UUID, object] | None = None,
    timings: object | None = None,
    commits: object | None = None,
    snapshots: object | None = None,
    materializer: object | None = None,
) -> object:
    """Materialize a local Meta lane through the service-owned runtime helper."""

    from aware_meta.graph.instance.commit.materialization_cache import (  # noqa: WPS433
        CachedLaneMaterializer,
    )

    lane_materializer = CachedLaneMaterializer(
        commits=commits,
        snaps=snapshots,
        materializer=materializer,
    )
    return await lane_materializer.get(
        branch_id=branch_id,
        ocg=ocg,
        opg=opg,
        commit_id=commit_id,
        oig_id=oig_id,
        attribute_configs_by_id=attribute_configs_by_id,
        class_configs_by_id=class_configs_by_id,
        timings=timings,
    )


def _load_local_meta_generated_handler_modules(
    *,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None,
) -> tuple[object, ...]:
    modules: list[object] = []
    for raw_manifest_path in package_manifest_paths:
        provider_path = _local_meta_generated_handler_provider_path(
            raw_manifest_path=raw_manifest_path,
            workspace_root=workspace_root,
        )
        if provider_path is None or not provider_path.is_file():
            continue
        modules.append(_load_module_from_path(provider_path))
    return tuple(modules)


def _default_projection_hash(
    resolver: LocalMetaAwarePackageManifestResolver,
) -> str:
    opg_by_hash = getattr(resolver.graph_catalog, "opg_by_hash", {}) or {}
    if not opg_by_hash:
        return DEFAULT_META_LOCAL_PROJECTION_HASH
    candidates = sorted(
        (
            str(getattr(opg, "name", "") or ""),
            str(projection_hash),
        )
        for projection_hash, opg in opg_by_hash.items()
    )
    return candidates[0][1]


def _local_meta_generated_handler_provider_path(
    *,
    raw_manifest_path: Path,
    workspace_root: Path | None,
) -> Path | None:
    manifest_path = Path(raw_manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = (workspace_root or Path.cwd()) / manifest_path
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        return None
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    package = manifest.get("package", {})
    if not isinstance(package, Mapping):
        return None
    fqn_prefix = package.get("fqn_prefix")
    if not isinstance(fqn_prefix, str) or not fqn_prefix.strip():
        return None
    package_root = manifest_path.parent.parent
    return (
        package_root
        / "runtime"
        / "python"
        / fqn_prefix.strip()
        / "handlers"
        / "_generated"
        / "meta_handlers.py"
    )


def _load_module_from_path(path: Path) -> object:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^0-9A-Za-z_]+", "_", path.stem).strip("_") or "module"
    module_name = f"_aware_meta_local_{stem}_{digest}"
    _ = sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load local Meta generated handler: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _typed_request_from_prepared(
    *,
    class_ref: str,
    payload: Mapping[str, object],
) -> BaseModel:
    request_model = resolve_api_endpoint_model_class(class_ref)
    return request_model.model_validate(dict(payload))


def _binding_for_endpoint(endpoint_ref: str) -> Any:
    binding = ENDPOINT_BINDINGS.get(endpoint_ref)
    if binding is None:
        raise ValueError(
            f"Unsupported Meta service protocol endpoint ref: {endpoint_ref!r}."
        )
    return binding


def _default_operation_context(request: object) -> ServiceOperationContext:
    actor_id = _optional_uuid(getattr(request, "actor_id", None)) or _stable_uuid(
        "actor"
    )
    return ServiceOperationContext(
        actor_id=actor_id,
        environment_id=_stable_uuid("environment"),
        process_id=_stable_uuid("process"),
        thread_id=_stable_uuid("thread"),
        branch_id=_stable_uuid("branch"),
        projection_hash=DEFAULT_META_LOCAL_PROJECTION_HASH,
    )


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _stable_uuid(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:meta-service:local:{name}")


__all__ = [
    "DEFAULT_META_LOCAL_API_ENDPOINT",
    "DEFAULT_META_LOCAL_PROJECTION_HASH",
    "DEFAULT_META_SERVICE_NAME",
    "LocalMetaServiceApiConfig",
    "LocalMetaAwarePackageManifestApiSession",
    "LocalMetaAwarePackageManifestResolver",
    "LocalMetaServiceApiSession",
    "LocalMetaServiceAwareApiClient",
    "build_local_meta_service_api_client_for_aware_package_manifests",
    "build_local_meta_service_api_session_for_aware_package_manifests",
    "build_local_meta_commit_store",
    "build_local_meta_oig_materializer",
    "build_local_meta_service_api_client",
    "build_local_meta_service_api_session",
    "build_local_meta_snapshot_store",
    "dispatch_meta_service_protocol_endpoint",
    "dispatch_meta_service_protocol_stream_endpoint",
    "load_local_meta_graph_context",
    "materialize_local_meta_lane_oig",
    "object_instance_graph_commit_from_payload",
    "read_local_meta_api_activation_read_model",
    "read_local_meta_runtime_read_model",
]
