from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel

from aware_meta.manifest.loader import load_aware_toml_spec
from aware_types import JsonArray, JsonObject
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization import (
    materialize_object_config_graph_package_leaf_from_manifest,
    stable_semantic_package_branch_id,
)
from aware_meta.materialization.artifact_lifecycle import (
    build_object_config_graph_package_language_lifecycle_receipts,
)
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphDomainCommitAppendRequest,
    MetaGraphCommitInvocationBackend,
)
from aware_meta.runtime.generated_handler_discovery import (
    build_meta_graph_generated_handler_provider_set,
    discover_meta_graph_generated_handler_provider_set,
)
from aware_meta.runtime.handler_executor import (
    build_meta_graph_generated_handler_executor,
    build_meta_graph_generated_language_handler_registry,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphGeneratedLanguageHandlerResolver,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphPreStateProviderResult,
    build_meta_graph_pre_state_index,
)
from aware_meta.runtime.graph_runtime import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
    MetaGraphRuntime,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.invocation_helpers import jsonify_invocation_payload
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta.runtime.read_model_provider import (
    MetaRuntimeReadModelRequest as MetaRuntimeReadModelProviderRequest,
    read_workspace_meta_runtime_read_model,
)
from aware_meta.semantic_analysis import analyze_meta_ocg_sources
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_package_id,
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
)
from .commit_events import (
    MetaCommitEventBus,
    MetaCommitEventStore,
    stable_meta_commit_event_id,
)
from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitActionMetadata,
    MetaCommitEventEnvelope,
    MetaCommitSubscriptionRequest,
    MetaCommitSubscriptionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetLaneHeadResponse,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphGetObjectInstanceGraphCommitResponse,
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
    MetaGraphInvokeTemporalFunctionRequest,
    MetaGraphInvokeTemporalFunctionResponse,
    MetaGraphResolveProjectionRequest,
    MetaGraphResolveProjectionResponse,
)
from aware_meta_service_dto.graph.view.graph_view import (
    MetaGraphResolveGraphViewRequest,
    MetaGraphResolveGraphViewResponse,
    MetaGraphSnapshot,
    MetaGraphSnapshotEdge,
    MetaGraphSnapshotNode,
    MetaGraphViewRef,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageDependencyRef,
    MetaObjectConfigGraphPackageEnsureRequest,
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeRequest,
    MetaCompletenessAnalyzeResponse,
    MetaCompletenessDiagnostic,
)
from aware_meta_service_dto.persistence.database_readiness import (
    MetaPersistenceEnsureDatabaseReadyRequest,
    MetaPersistenceEnsureDatabaseReadyResponse,
)
from aware_meta_service_dto.runtime.read_model import (
    MetaRuntimeReadModelGraphRef,
    MetaRuntimeReadModelPackageTiming,
    MetaRuntimeReadModelProjectionRef,
    MetaRuntimeReadModelRequest,
    MetaRuntimeReadModelResponse,
    MetaWorkspaceCommitTruthSummary,
)
from aware_meta_service_protocol.protocols import MetaCommitSubscribeStreamEvent
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.target_resolution import service_graph_catalog
from aware_service_runtime.contracts import (
    ServiceGraphCatalog,
    ServiceGraphContextLike,
)
from aware_utils.logging import logger

MetaObjectConfigGraphPackageCompilerBackend: Any | None = None
MetaDatabaseReadyConnectionFactory: (
    Callable[[str], Awaitable[_ClosableDBBootConnection]] | None
) = None
MetaRuntimeReadModelProviderBackend: (
    Callable[[MetaRuntimeReadModelProviderRequest], object] | None
) = None


class _ClosableDBBootConnection(Protocol):
    async def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class _ObjectConfigGraphPackageManifestIdentity:
    package_name: str | None = None
    fqn_prefix: str | None = None
    object_config_graph_package_id: UUID | None = None
    error: str | None = None


def build_aware_meta_service_protocol_handler(
    *,
    event_bus: MetaCommitEventBus | None = None,
    event_store: MetaCommitEventStore | None = None,
    commit_store: FSCommitStore | None = None,
    runtime: object | None = None,
    graph_context_provider: (
        Callable[[], Awaitable[ServiceGraphContextLike]] | None
    ) = None,
    generated_language_handler_resolver: (
        MetaGraphGeneratedLanguageHandlerResolver | None
    ) = None,
    generated_language_handler_module: (
        MetaGraphGeneratedLanguageHandlerModule | None
    ) = None,
) -> AwareMetaServiceProtocolHandler:
    return AwareMetaServiceProtocolHandler(
        event_bus=event_bus,
        event_store=event_store,
        commit_store=commit_store,
        runtime=runtime,
        graph_context_provider=graph_context_provider,
        generated_language_handler_resolver=generated_language_handler_resolver,
        generated_language_handler_module=generated_language_handler_module,
    )


@dataclass(slots=True)
class _MetaProtocolSupport:
    _event_bus: MetaCommitEventBus = field(default_factory=MetaCommitEventBus)
    _commit_store: FSCommitStore = field(default_factory=FSCommitStore)
    _runtime: object | None = None
    _graph_context_provider: Callable[[], Awaitable[ServiceGraphContextLike]] | None = (
        None
    )
    _generated_language_handler_resolver: (
        MetaGraphGeneratedLanguageHandlerResolver | None
    ) = None
    _generated_language_handler_module: (
        MetaGraphGeneratedLanguageHandlerModule | None
    ) = None

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Meta service protocol requires an active Service API host context."
            )
        return host_context

    def event_bus(self) -> MetaCommitEventBus:
        return self._event_bus

    def commit_store(self) -> FSCommitStore:
        return self._commit_store

    def handler_executor(
        self,
        *,
        graph_context: ServiceGraphContextLike | None = None,
        pre_state_provider: object | None = None,
    ) -> object | None:
        generated_language_handler_resolver = self._generated_language_handler_resolver
        empty_lane_bootstrap_resolver = None
        invocation_handler_resolver = None
        if generated_language_handler_resolver is None:
            generated_language_handler_module = self._generated_language_handler_module
            if generated_language_handler_module is not None:
                provider_set = build_meta_graph_generated_handler_provider_set(
                    modules=(generated_language_handler_module,),
                )
                if provider_set is not None:
                    generated_language_handler_resolver = provider_set.handler_resolver
                    empty_lane_bootstrap_resolver = (
                        provider_set.empty_lane_bootstrap_resolver
                    )
                    invocation_handler_resolver = (
                        provider_set.invocation_handler_resolver
                    )
                else:
                    generated_language_handler_resolver = (
                        build_meta_graph_generated_language_handler_registry(
                            module=generated_language_handler_module,
                        )
                    )
            elif graph_context is not None:
                provider_set = discover_meta_graph_generated_handler_provider_set(
                    index=_graph_catalog(graph_context),
                )
                if provider_set is not None:
                    generated_language_handler_resolver = provider_set.handler_resolver
                    empty_lane_bootstrap_resolver = (
                        provider_set.empty_lane_bootstrap_resolver
                    )
                    invocation_handler_resolver = (
                        provider_set.invocation_handler_resolver
                    )
        if generated_language_handler_resolver is None:
            return None
        return build_meta_graph_generated_handler_executor(
            handler_resolver=generated_language_handler_resolver,
            invocation_handler_resolver=invocation_handler_resolver,
            pre_state_provider=pre_state_provider,  # type: ignore[arg-type]
            empty_lane_bootstrap_resolver=empty_lane_bootstrap_resolver,
        )

    def runtime(
        self, *, graph_context: ServiceGraphContextLike | None = None
    ) -> object:
        cache_runtime = graph_context is None
        if self._runtime is None:
            handler_executor = self.handler_executor(graph_context=graph_context)
            runtime = MetaGraphRuntime(
                backend=MetaGraphCommitInvocationBackend(
                    handler_executor=handler_executor,  # type: ignore[arg-type]
                    implementation_policy=_graph_context_implementation_policy(
                        graph_context
                    ),
                )
            )
            if cache_runtime and handler_executor is not None:
                self._runtime = runtime
            else:
                return runtime
        return self._runtime

    async def graph_context(self) -> ServiceGraphContextLike:
        if self._graph_context_provider is not None:
            return await self._graph_context_provider()
        host_context = self.host_context()
        if host_context.materialization is not None:
            return host_context.materialization.graph_context
        if host_context.graph_context_provider is None:
            raise RuntimeError(
                "Meta service protocol requires a Service graph context provider."
            )
        return await host_context.graph_context_provider.resolve_graph_context()

    async def ensure_object_config_graph_package(
        self,
        request: MetaObjectConfigGraphPackageEnsureRequest,
    ) -> object:
        host_context = self.host_context()
        materialization = host_context.materialization
        if materialization is None:
            raise RuntimeError(
                "Meta package OCG compile requires an active Service API materialization context."
            )
        operation_context = host_context.operation_context
        workspace_root = _resolve_workspace_root(request.workspace_root)
        aware_toml_path = _resolve_aware_toml_path(
            workspace_root=workspace_root,
            aware_toml_path=request.aware_toml_path,
        )
        compiler_backend = cast(
            Any,
            MetaObjectConfigGraphPackageCompilerBackend
            or materialize_object_config_graph_package_leaf_from_manifest,
        )
        parent_branch_id = request.parent_branch_id or operation_context.branch_id
        package_branch_id = request.package_branch_id or parent_branch_id
        graph_catalog = _graph_catalog(materialization.graph_context)
        return await compiler_backend(
            runtime=materialization.runtime,
            index=graph_catalog,
            actor_id=request.actor_id or operation_context.actor_id,
            branch_id=package_branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            external_graphs=await _dependency_graphs_from_refs(
                request.dependency_refs,
                index=cast(
                    Any,
                    graph_catalog,
                ),
                parent_branch_id=parent_branch_id,
            ),
            source_code_package_id=request.source_code_package_id,
            object_config_graph_package_id=request.object_config_graph_package_id,
            collect_telemetry=request.collect_telemetry,
        )

    async def ensure_database_ready(
        self,
        request: MetaPersistenceEnsureDatabaseReadyRequest,
    ) -> MetaPersistenceEnsureDatabaseReadyResponse:
        operation_context = self.host_context().operation_context
        actor_id = request.actor_id or operation_context.actor_id
        return await _ensure_database_ready_response(
            request=request,
            actor_id=actor_id,
        )

    async def describe_workspace_read_model(
        self,
        request: MetaRuntimeReadModelRequest,
    ) -> MetaRuntimeReadModelResponse:
        host_context = self.host_context()
        operation_context = host_context.operation_context
        actor_id = request.actor_id or operation_context.actor_id
        workspace_root = _resolve_meta_runtime_read_model_workspace_root(request)
        repo_root = _resolve_meta_runtime_read_model_repo_root(
            request=request,
            workspace_root=workspace_root,
        )
        aware_root = _resolve_meta_runtime_read_model_aware_root(
            request=request,
            repo_root=repo_root,
        )
        provider_backend = (
            MetaRuntimeReadModelProviderBackend
            or _default_meta_runtime_read_model_provider_backend
        )
        read_model = provider_backend(
            MetaRuntimeReadModelProviderRequest(
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=tuple(request.required_projection_names),
                force_refresh=request.force_refresh,
                include_workspace_commit_truth=(request.include_workspace_commit_truth),
            )
        )
        return _meta_runtime_read_model_response(
            request=request,
            read_model=read_model,
            actor_id=actor_id,
            workspace_root=workspace_root,
            include_timings=request.include_timings,
            include_package_timings=request.include_package_timings,
        )

    async def analyze_object_config_graph_completeness(
        self,
        request: MetaCompletenessAnalyzeRequest,
    ) -> MetaCompletenessAnalyzeResponse:
        operation_context = self.host_context().operation_context
        actor_id = request.actor_id or operation_context.actor_id
        workspace_root = _resolve_workspace_root(request.workspace_root)
        package_root = _resolve_package_root(
            workspace_root=workspace_root,
            package_root=request.package_root,
        )
        aware_toml_path = _resolve_optional_aware_toml_path(
            package_root=package_root,
            aware_toml_path=request.aware_toml_path,
        )
        source_files = _resolve_meta_completeness_source_files(
            package_root=package_root,
            source_files=request.source_files,
        )
        parent_branch_id = operation_context.branch_id
        dependency_graphs = await _diagnostic_dependency_graphs_from_refs(
            request.dependency_refs,
            graph_context_provider=self.graph_context,
            parent_branch_id=parent_branch_id,
        )
        analysis = analyze_meta_ocg_sources(
            package_root=package_root,
            source_files=source_files,
            manifest_path=aware_toml_path,
            external_graphs=dependency_graphs,
            fail_on_error=False,
            completeness_diagnostics=request.completeness_diagnostics,
            completeness_diagnostic_severity=request.diagnostic_severity,
        )
        return _meta_completeness_analyze_response(
            request=request,
            analysis=analysis,
            actor_id=actor_id,
            workspace_root=workspace_root,
            package_root=package_root,
            aware_toml_path=aware_toml_path,
        )


class _MetaGraphCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse:
        try:
            graph_context = await self._support.graph_context()
            return _resolve_projection_response(
                index=cast(Any, _graph_catalog(graph_context)),
                request=request,
            )
        except Exception as exc:
            return MetaGraphResolveProjectionResponse(
                status="failed",
                actor_id=request.actor_id,
                error=str(exc),
            )

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse:
        try:
            head = await self._support.commit_store().head(
                branch_id=request.domain_branch_id,
                projection_hash=request.domain_projection_hash,
            )
            if head is None:
                return MetaGraphGetLaneHeadResponse(
                    status="empty",
                    actor_id=request.actor_id,
                    domain_branch_id=request.domain_branch_id,
                    domain_projection_hash=request.domain_projection_hash,
                )
            return MetaGraphGetLaneHeadResponse(
                status="succeeded",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                domain_commit_id=_json_optional_uuid(head.get("commit_id")),
                graph_hash_post=_json_optional_string(head.get("graph_hash_post")),
                object_instance_graph_id=_json_optional_uuid(
                    head.get("object_instance_graph_id")
                ),
                root_object_id=_json_optional_uuid(head.get("root_object_id")),
                head_version=_json_optional_int(head.get("v")),
            )
        except Exception as exc:
            return MetaGraphGetLaneHeadResponse(
                status="failed",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                error=str(exc),
            )

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse:
        try:
            domain_commit = await self._support.commit_store().get_commit(
                branch_id=request.domain_branch_id,
                projection_hash=request.domain_projection_hash,
                commit_id=request.domain_commit_id,
            )
            if domain_commit is None:
                return MetaGraphGetObjectInstanceGraphCommitResponse(
                    status="missing",
                    actor_id=request.actor_id,
                    domain_branch_id=request.domain_branch_id,
                    domain_projection_hash=request.domain_projection_hash,
                    domain_commit_id=request.domain_commit_id,
                )
            return _object_instance_graph_commit_response(
                request=request,
                domain_commit=domain_commit,
            )
        except Exception as exc:
            return MetaGraphGetObjectInstanceGraphCommitResponse(
                status="failed",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                domain_commit_id=request.domain_commit_id,
                error=str(exc),
            )

    async def resolve_graph_view(
        self,
        request: MetaGraphResolveGraphViewRequest,
    ) -> MetaGraphResolveGraphViewResponse:
        try:
            graph_context = await self._support.graph_context()
            graph_catalog = cast(Any, _graph_catalog(graph_context))
            opg = graph_catalog.opg_by_hash.get(request.domain_projection_hash)
            if opg is None:
                return _graph_view_response(
                    request=request,
                    status="not_found",
                    error=(
                        "Projection hash "
                        f"{request.domain_projection_hash!r} was not found"
                    ),
                )

            commit_store = self._support.commit_store()
            target_domain_commit_id = request.domain_commit_id
            if request.object_instance_graph_commit_id is not None:
                resolved_domain_commit_id = await commit_store.domain_commit_id_for_object_instance_graph_commit_id(
                    branch_id=request.domain_branch_id,
                    projection_hash=request.domain_projection_hash,
                    object_instance_graph_commit_id=(
                        request.object_instance_graph_commit_id
                    ),
                )
                if resolved_domain_commit_id is None:
                    return _graph_view_response(
                        request=request,
                        status="missing",
                        object_instance_graph_commit_id=(
                            request.object_instance_graph_commit_id
                        ),
                        error=(
                            "ObjectInstanceGraphCommit id "
                            f"{request.object_instance_graph_commit_id} was not found"
                        ),
                    )
                if (
                    target_domain_commit_id is not None
                    and target_domain_commit_id != resolved_domain_commit_id
                ):
                    return _graph_view_response(
                        request=request,
                        status="invalid_request",
                        domain_commit_id=target_domain_commit_id,
                        object_instance_graph_commit_id=(
                            request.object_instance_graph_commit_id
                        ),
                        error=(
                            "domain_commit_id does not match "
                            "object_instance_graph_commit_id"
                        ),
                    )
                target_domain_commit_id = resolved_domain_commit_id

            if target_domain_commit_id is None:
                head = await commit_store.head(
                    branch_id=request.domain_branch_id,
                    projection_hash=request.domain_projection_hash,
                )
                if head is None:
                    return _graph_view_response(
                        request=request,
                        status="empty",
                    )
                target_domain_commit_id = _json_optional_uuid(head.get("commit_id"))
                if target_domain_commit_id is None:
                    return _graph_view_response(
                        request=request,
                        status="empty",
                    )

            domain_commit = await commit_store.get_commit(
                branch_id=request.domain_branch_id,
                projection_hash=request.domain_projection_hash,
                commit_id=target_domain_commit_id,
            )
            if domain_commit is None:
                return _graph_view_response(
                    request=request,
                    status="missing",
                    domain_commit_id=target_domain_commit_id,
                    error=f"Domain commit {target_domain_commit_id} was not found",
                )

            oig, _ = await OIGMaterializer(commits=commit_store).get(
                branch_id=request.domain_branch_id,
                ocg=cast(ObjectConfigGraph, graph_catalog.ocg),
                opg=opg,
                commit_id=target_domain_commit_id,
                oig_id=domain_commit.object_instance_graph_id,
                attribute_configs_by_id=graph_catalog.attribute_configs_by_id,
                class_configs_by_id=graph_catalog.class_configs_by_id,
            )
            object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=(
                    domain_commit.object_instance_graph_identity_id
                ),
                commit_id=domain_commit.commit.id,
            )
            return _graph_view_response(
                request=request,
                status="succeeded",
                domain_commit_id=domain_commit.commit.id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
                object_instance_graph_id=domain_commit.object_instance_graph_id,
                object_instance_graph_identity_id=(
                    domain_commit.object_instance_graph_identity_id
                ),
                object_instance_graph_branch_id=stable_object_instance_graph_branch_id(
                    object_instance_graph_identity_id=(
                        domain_commit.object_instance_graph_identity_id
                    ),
                    branch_id=request.domain_branch_id,
                ),
                graph_catalog=graph_catalog,
                opg=opg,
                oig=oig,
                summary=(
                    f"{len(oig.class_instances)} nodes, "
                    f"{len(oig.class_instance_relationships)} edges"
                ),
            )
        except Exception as exc:
            return _graph_view_response(
                request=request,
                status="failed",
                error=str(exc),
            )

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        try:
            graph_context = await self._support.graph_context()
            graph_catalog = cast(Any, _graph_catalog(graph_context))
            receipt = await cast(
                Any,
                self._support.runtime(graph_context=graph_context),
            ).invoke_function(
                MetaGraphInvokeFunctionInput(
                    index=graph_catalog,
                    actor_id=request.actor_id,
                    function_id=request.function_id,
                    domain_branch_id=request.domain_branch_id,
                    domain_projection_hash=request.domain_projection_hash,
                    call_target=_to_runtime_call_target(request.call_target),
                    target_object_id=request.target_object_id,
                    object_projection_graph_id=request.object_projection_graph_id,
                    args=request.args,
                    kwargs=request.kwargs,
                    expected_graph_hash_pre=request.expected_graph_hash_pre,
                    expected_head_commit_id=request.expected_head_commit_id,
                    commit=request.commit,
                    publish=request.publish,
                )
            )
        except Exception as exc:
            return MetaGraphInvokeFunctionResponse(
                status="failed",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                error=str(exc),
            )
        commit_event = await _commit_event_from_receipt(
            request=request,
            receipt=cast(MetaGraphCommitReceipt, receipt),
            host_context=self._support.host_context(),
            commit_store=self._support.commit_store(),
        )
        response = _response_from_receipt(
            cast(MetaGraphCommitReceipt, receipt),
            commit_event=commit_event,
        )
        if response.commit_event is not None:
            await self._support.event_bus().publish(response.commit_event)
        return response

    async def invoke_temporal_function(
        self,
        request: MetaGraphInvokeTemporalFunctionRequest,
    ) -> MetaGraphInvokeTemporalFunctionResponse:
        try:
            graph_context = await self._support.graph_context()
            graph_catalog = cast(Any, _graph_catalog(graph_context))
            before_oig = ObjectInstanceGraph.model_validate(request.before_oig)
            pre_state_provider = _TemporalOverlayPreStateProvider(
                before_oig=before_oig,
                head_commit_id=request.expected_head_commit_id,
            )
            handler_executor = self._support.handler_executor(
                graph_context=graph_context,
                pre_state_provider=pre_state_provider,
            )
            backend = MetaGraphCommitInvocationBackend(
                handler_executor=handler_executor,  # type: ignore[arg-type]
                implementation_policy=_graph_context_implementation_policy(
                    graph_context
                ),
            )
            temporal_request = MetaGraphInvokeFunctionInput(
                index=graph_catalog,
                actor_id=request.actor_id,
                function_id=request.function_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                call_target=_to_runtime_call_target(request.call_target),
                target_object_id=request.target_object_id,
                object_projection_graph_id=request.object_projection_graph_id,
                args=request.args,
                kwargs=request.kwargs,
                expected_graph_hash_pre=request.expected_graph_hash_pre,
                expected_head_commit_id=request.expected_head_commit_id,
                commit=False,
                publish=False,
            )
            staged_call = backend.stage_function_call(temporal_request)
            staged_result = await backend.execute_staged_function_call(
                request=temporal_request,
                staged_call=staged_call,
            )
            staged_action = backend.stage_commit_action(staged_result)
            append_request = backend.build_domain_commit_append_request(
                staged_action,
            )
            after_oig = _temporal_after_oig_from_append_request(
                before_oig=before_oig,
                append_request=append_request,
                graph_catalog=graph_catalog,
            )
            return _temporal_response_from_staged_append(
                request=request,
                append_request=append_request,
                after_oig=after_oig,
            )
        except Exception as exc:
            return MetaGraphInvokeTemporalFunctionResponse(
                status="failed",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                before_oig=request.before_oig,
                error=str(exc),
            )


class _MetaCommitCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def subscribe(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> MetaCommitSubscriptionResponse:
        return MetaCommitSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
            resume_after_event_id=request.resume_after_event_id,
        )

    async def stream_subscribe(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> AsyncIterator[MetaCommitSubscribeStreamEvent]:
        subscription = self._support.event_bus().subscribe(request)
        yielded_event_ids: set[object] = set()
        try:
            for event in self._support.event_bus().replay(request):
                yielded_event_ids.add(event.event_id)
                yield cast(MetaCommitSubscribeStreamEvent, event)
            while True:
                event = await subscription.queue.get()
                if event.event_id in yielded_event_ids:
                    continue
                yielded_event_ids.add(event.event_id)
                yield cast(MetaCommitSubscribeStreamEvent, event)
        finally:
            self._support.event_bus().unsubscribe(subscription)


class _MetaPackageCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def ensure_object_config_graph_package(
        self,
        request: MetaObjectConfigGraphPackageEnsureRequest,
    ) -> MetaObjectConfigGraphPackageEnsureResponse:
        try:
            result = await self._support.ensure_object_config_graph_package(request)
            response = _object_config_graph_package_ensure_response(
                request=request,
                result=result,
            )
            commit_event = await _commit_event_from_package_ensure_response(
                request=request,
                response=response,
                host_context=self._support.host_context(),
                commit_store=self._support.commit_store(),
                graph_context=await self._support.graph_context(),
            )
            if commit_event is not None:
                await self._support.event_bus().publish(commit_event)
            return response
        except Exception as exc:
            return _object_config_graph_package_ensure_failed_response(
                request=request,
                exc=exc,
            )


class _MetaDiagnosticsCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def analyze_object_config_graph_completeness(
        self,
        request: MetaCompletenessAnalyzeRequest,
    ) -> MetaCompletenessAnalyzeResponse:
        try:
            return await self._support.analyze_object_config_graph_completeness(
                request,
            )
        except Exception as exc:
            return _meta_completeness_analyze_failed_response(
                request=request,
                actor_id=request.actor_id,
                error=str(exc),
            )


class _MetaPersistenceCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def ensure_database_ready(
        self,
        request: MetaPersistenceEnsureDatabaseReadyRequest,
    ) -> MetaPersistenceEnsureDatabaseReadyResponse:
        try:
            return await self._support.ensure_database_ready(request)
        except Exception as exc:
            return _database_ready_response(
                request=request,
                status="failed",
                actor_id=request.actor_id,
                error=str(exc),
            )


class _MetaRuntimeReadModelCapabilityHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self._support = support

    async def describe_workspace(
        self,
        request: MetaRuntimeReadModelRequest,
    ) -> MetaRuntimeReadModelResponse:
        try:
            return await self._support.describe_workspace_read_model(request)
        except Exception as exc:
            actor_id = request.actor_id
            if actor_id is None:
                try:
                    actor_id = self._support.host_context().operation_context.actor_id
                except RuntimeError:
                    actor_id = None
            return _meta_runtime_read_model_failed_response(
                request=request,
                actor_id=actor_id,
                error=str(exc),
            )


class _MetaApiServiceProtocolHandler:
    def __init__(self, *, support: _MetaProtocolSupport) -> None:
        self.commit = _MetaCommitCapabilityHandler(support=support)
        self.diagnostics = _MetaDiagnosticsCapabilityHandler(support=support)
        self.graph = _MetaGraphCapabilityHandler(support=support)
        self.package = _MetaPackageCapabilityHandler(support=support)
        self.persistence = _MetaPersistenceCapabilityHandler(support=support)
        self.runtime_read_model = _MetaRuntimeReadModelCapabilityHandler(
            support=support,
        )


class AwareMetaServiceProtocolHandler:
    def __init__(
        self,
        *,
        event_bus: MetaCommitEventBus | None = None,
        event_store: MetaCommitEventStore | None = None,
        commit_store: FSCommitStore | None = None,
        runtime: object | None = None,
        graph_context_provider: (
            Callable[[], Awaitable[ServiceGraphContextLike]] | None
        ) = None,
        generated_language_handler_resolver: (
            MetaGraphGeneratedLanguageHandlerResolver | None
        ) = None,
        generated_language_handler_module: (
            MetaGraphGeneratedLanguageHandlerModule | None
        ) = None,
    ) -> None:
        if (
            generated_language_handler_resolver is not None
            and generated_language_handler_module is not None
        ):
            raise ValueError(
                "generated_language_handler_resolver cannot be combined with "
                "generated_language_handler_module"
            )
        support = _MetaProtocolSupport(
            _event_bus=event_bus
            or MetaCommitEventBus(store=event_store or MetaCommitEventStore()),
            _commit_store=commit_store or FSCommitStore(),
            _runtime=runtime,
            _graph_context_provider=graph_context_provider,
            _generated_language_handler_resolver=(generated_language_handler_resolver),
            _generated_language_handler_module=generated_language_handler_module,
        )
        self.meta = _MetaApiServiceProtocolHandler(support=support)


def _default_meta_runtime_read_model_provider_backend(
    request: MetaRuntimeReadModelProviderRequest,
) -> object:
    return read_workspace_meta_runtime_read_model(
        repo_root=request.repo_root,
        aware_root=request.aware_root,
        required_projection_names=request.required_projection_names,
        force_refresh=request.force_refresh,
        include_workspace_commit_truth=request.include_workspace_commit_truth,
    )


def _graph_catalog(graph_context: ServiceGraphContextLike) -> ServiceGraphCatalog:
    return service_graph_catalog(graph_context)


def _graph_context_implementation_policy(graph_context: object | None) -> object | None:
    return getattr(graph_context, "implementation_policy", None)


def _meta_completeness_analyze_response(
    *,
    request: MetaCompletenessAnalyzeRequest,
    analysis: object,
    actor_id: UUID | None,
    workspace_root: Path,
    package_root: Path,
    aware_toml_path: Path,
) -> MetaCompletenessAnalyzeResponse:
    manifest_identity = _object_config_graph_package_manifest_identity(
        aware_toml_path=aware_toml_path,
    )
    preview = getattr(analysis, "change_preview", None)
    object_config_graph = getattr(analysis, "object_config_graph", None)
    return MetaCompletenessAnalyzeResponse(
        status="succeeded" if object_config_graph is not None else "failed",
        actor_id=actor_id,
        workspace_root=workspace_root.as_posix(),
        package_root=package_root.as_posix(),
        aware_toml_path=aware_toml_path.as_posix(),
        package_name=manifest_identity.package_name,
        fqn_prefix=manifest_identity.fqn_prefix,
        diagnostics=_meta_completeness_diagnostics(
            getattr(analysis, "diagnostics", ())
        ),
        changed_source_files=list(
            getattr(preview, "changed_source_files", ()) if preview is not None else ()
        ),
        affected_object_config_graph_keys=list(
            getattr(preview, "affected_object_config_graph_keys", ())
            if preview is not None
            else ()
        ),
        affected_node_keys=list(
            getattr(preview, "affected_node_keys", ()) if preview is not None else ()
        ),
        graph_count=_int_or_zero(getattr(preview, "graph_count", 0)),
        node_count=_int_or_zero(getattr(preview, "node_count", 0)),
        class_count=_int_or_zero(getattr(preview, "class_count", 0)),
        enum_count=_int_or_zero(getattr(preview, "enum_count", 0)),
        function_count=_int_or_zero(getattr(preview, "function_count", 0)),
        relationship_count=_int_or_zero(getattr(preview, "relationship_count", 0)),
        required_materializations=list(
            getattr(preview, "required_materializations", ())
            if preview is not None
            else ()
        ),
        object_config_graph=(
            _optional_json_object(
                _object_config_graph_transfer_payload(object_config_graph)
            )
            if request.include_object_config_graph and object_config_graph is not None
            else None
        ),
        error=(
            None
            if object_config_graph is not None
            else _first_error(getattr(analysis, "diagnostics", ()))
        ),
    )


def _meta_completeness_analyze_failed_response(
    *,
    request: MetaCompletenessAnalyzeRequest,
    actor_id: UUID | None,
    error: str,
) -> MetaCompletenessAnalyzeResponse:
    workspace_root = _path_text(request.workspace_root)
    package_root = _path_text(request.package_root)
    aware_toml_path = _path_text(request.aware_toml_path)
    return MetaCompletenessAnalyzeResponse(
        status="failed",
        actor_id=actor_id,
        workspace_root=workspace_root,
        package_root=package_root,
        aware_toml_path=aware_toml_path,
        error=error,
        diagnostics=[
            MetaCompletenessDiagnostic(
                severity="error",
                code="aware_meta.completeness.api_failed",
                message=error,
            )
        ],
    )


def _meta_completeness_diagnostics(
    diagnostics: object,
) -> list[MetaCompletenessDiagnostic]:
    result: list[MetaCompletenessDiagnostic] = []
    for diagnostic in diagnostics or ():
        result.append(
            MetaCompletenessDiagnostic(
                severity=str(getattr(diagnostic, "severity", "") or "warning"),
                code=str(getattr(diagnostic, "code", "") or "unknown"),
                message=str(getattr(diagnostic, "message", "") or ""),
                source_path=_optional_string(getattr(diagnostic, "source_path", None)),
            )
        )
    return result


def _first_error(diagnostics: object) -> str | None:
    for diagnostic in diagnostics or ():
        if str(getattr(diagnostic, "severity", "")).strip().lower() == "error":
            return str(getattr(diagnostic, "message", "") or "")
    return None


def _meta_runtime_read_model_response(
    *,
    request: MetaRuntimeReadModelRequest,
    read_model: object,
    actor_id: UUID | None,
    workspace_root: Path,
    include_timings: bool,
    include_package_timings: bool,
) -> MetaRuntimeReadModelResponse:
    context = getattr(read_model, "context", None)
    return MetaRuntimeReadModelResponse(
        status="succeeded",
        actor_id=actor_id,
        read_model_version=_optional_string(
            getattr(read_model, "read_model_version", None)
        ),
        workspace_root=workspace_root.as_posix(),
        repo_root=_path_text(getattr(read_model, "repo_root", None)),
        aware_root=_path_text(getattr(read_model, "aware_root", None)),
        required_projection_names=list(
            getattr(read_model, "required_projection_names", ())
        ),
        projections=_meta_runtime_read_model_projection_refs(read_model),
        runtime_graphs=_meta_runtime_read_model_graph_refs(
            graphs=tuple(getattr(context, "runtime_graphs", ()) or ()),
            graph_ids=tuple(getattr(read_model, "runtime_graph_ids", ()) or ()),
            package_graphs=getattr(context, "runtime_graph_by_package_name", {}),
            graph_role="runtime",
        ),
        source_graphs=_meta_runtime_read_model_graph_refs(
            graphs=tuple(getattr(context, "source_graphs", ()) or ()),
            graph_ids=tuple(getattr(read_model, "source_graph_ids", ()) or ()),
            package_graphs=getattr(context, "source_graph_by_package_name", {}),
            graph_role="source",
        ),
        cache_status=_optional_string(getattr(read_model, "cache_status", None)),
        provider_duration_s=(
            _optional_float(getattr(read_model, "provider_duration_s", None))
            if include_timings
            else None
        ),
        phase_timings_s=(
            _optional_json_object(
                dict(getattr(read_model, "phase_timings_s", {}) or {})
            )
            if include_timings
            else None
        ),
        package_timings=(
            _meta_runtime_read_model_package_timings(
                tuple(getattr(read_model, "package_timings", ()) or ())
            )
            if include_package_timings
            else []
        ),
        workspace_commit_truth=(
            _meta_workspace_commit_truth_summary(
                getattr(read_model, "workspace_commit_truth", None)
            )
            if request.include_workspace_commit_truth
            else None
        ),
    )


def _meta_runtime_read_model_failed_response(
    *,
    request: MetaRuntimeReadModelRequest,
    actor_id: UUID | None,
    error: str,
) -> MetaRuntimeReadModelResponse:
    return MetaRuntimeReadModelResponse(
        status="failed",
        actor_id=actor_id,
        workspace_root=request.workspace_root,
        repo_root=request.repo_root,
        aware_root=request.aware_root,
        required_projection_names=request.required_projection_names,
        error=error,
    )


def _meta_runtime_read_model_projection_refs(
    read_model: object,
) -> list[MetaRuntimeReadModelProjectionRef]:
    index = getattr(read_model, "index", None)
    opg_by_hash = getattr(index, "opg_by_hash", {}) if index is not None else {}
    projection_hash_by_name = getattr(read_model, "projection_hash_by_name", {}) or {}
    refs: list[MetaRuntimeReadModelProjectionRef] = []
    for projection_name in getattr(read_model, "required_projection_names", ()) or ():
        projection_hash = _optional_string(projection_hash_by_name.get(projection_name))
        opg = opg_by_hash.get(projection_hash) if projection_hash is not None else None
        object_projection_graph_identity_id = None
        if index is not None and projection_hash is not None:
            try:
                _, opgi = resolve_meta_graph_ocgi_opgi(
                    index=index,
                    projection_hash=projection_hash,
                )
                object_projection_graph_identity_id = (
                    opgi.id if opgi is not None else None
                )
            except Exception:
                object_projection_graph_identity_id = None
        refs.append(
            MetaRuntimeReadModelProjectionRef(
                projection_name=(
                    _optional_string(getattr(opg, "name", None)) or str(projection_name)
                ),
                projection_hash=projection_hash,
                object_projection_graph_id=_optional_uuid(
                    getattr(opg, "id", None) if opg is not None else None
                ),
                object_projection_graph_identity_id=(
                    object_projection_graph_identity_id
                ),
            )
        )
    return refs


def _meta_runtime_read_model_graph_refs(
    *,
    graphs: tuple[object, ...],
    graph_ids: tuple[object, ...],
    package_graphs: object,
    graph_role: str,
) -> list[MetaRuntimeReadModelGraphRef]:
    package_name_by_graph_id = _package_name_by_graph_id(package_graphs)
    refs: list[MetaRuntimeReadModelGraphRef] = []
    seen_graph_ids: set[UUID] = set()
    for graph in graphs:
        graph_id = _optional_uuid(getattr(graph, "id", None))
        if graph_id is None or graph_id in seen_graph_ids:
            continue
        seen_graph_ids.add(graph_id)
        refs.append(
            MetaRuntimeReadModelGraphRef(
                graph_id=graph_id,
                graph_role=graph_role,
                package_name=(
                    package_name_by_graph_id.get(graph_id)
                    or _optional_string(getattr(graph, "package_name", None))
                ),
                fqn_prefix=_optional_string(getattr(graph, "fqn_prefix", None)),
            )
        )
    for value in graph_ids:
        graph_id = _optional_uuid(value)
        if graph_id is None or graph_id in seen_graph_ids:
            continue
        seen_graph_ids.add(graph_id)
        refs.append(
            MetaRuntimeReadModelGraphRef(
                graph_id=graph_id,
                graph_role=graph_role,
                package_name=package_name_by_graph_id.get(graph_id),
            )
        )
    return refs


def _meta_runtime_read_model_package_timings(
    timings: tuple[object, ...],
) -> list[MetaRuntimeReadModelPackageTiming]:
    package_timings: list[MetaRuntimeReadModelPackageTiming] = []
    for timing in timings:
        package_timings.append(
            MetaRuntimeReadModelPackageTiming(
                package_name=str(getattr(timing, "package_name", "") or ""),
                manifest_path=str(getattr(timing, "manifest_path", "") or ""),
                cache_status=str(getattr(timing, "cache_status", "") or ""),
                cache_miss_reason=_optional_string(
                    getattr(timing, "cache_miss_reason", None)
                ),
                phase_timings_s=_optional_json_object(
                    dict(getattr(timing, "phase_timings_s", {}) or {})
                ),
            )
        )
    return package_timings


def _meta_workspace_commit_truth_summary(
    value: object,
) -> MetaWorkspaceCommitTruthSummary | None:
    if value is None:
        return None
    if isinstance(value, MetaWorkspaceCommitTruthSummary):
        return value
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if not isinstance(value, Mapping):
        return None
    payload = dict(value)
    return MetaWorkspaceCommitTruthSummary(
        summary_source=_optional_string(payload.get("summary_source")),
        revision_count=_json_optional_int(payload.get("revision_count")) or 0,
        compilation_count=_json_optional_int(payload.get("compilation_count")) or 0,
        materialization_count=(
            _json_optional_int(payload.get("materialization_count")) or 0
        ),
        build_count=_json_optional_int(payload.get("build_count")) or 0,
        latest_revision=_optional_json_object(payload.get("latest_revision")),
        latest_compilation=_optional_json_object(payload.get("latest_compilation")),
        latest_materialization=_optional_json_object(
            payload.get("latest_materialization")
        ),
        latest_successful_materialization=_optional_json_object(
            payload.get("latest_successful_materialization")
        ),
        latest_build=_optional_json_object(payload.get("latest_build")),
        latest_successful_build=_optional_json_object(
            payload.get("latest_successful_build")
        ),
    )


def _package_name_by_graph_id(package_graphs: object) -> dict[UUID, str]:
    if not isinstance(package_graphs, Mapping):
        return {}
    package_names: dict[UUID, str] = {}
    for package_name, graph in package_graphs.items():
        graph_id = _optional_uuid(getattr(graph, "id", None))
        if graph_id is not None and isinstance(package_name, str):
            package_names[graph_id] = package_name
    return package_names


def _resolve_meta_runtime_read_model_workspace_root(
    request: MetaRuntimeReadModelRequest,
) -> Path:
    return _resolve_workspace_root(request.workspace_root or request.repo_root)


def _resolve_meta_runtime_read_model_repo_root(
    *,
    request: MetaRuntimeReadModelRequest,
    workspace_root: Path,
) -> Path:
    if request.repo_root is not None and request.repo_root.strip():
        return Path(request.repo_root).expanduser().resolve()
    return workspace_root


def _resolve_meta_runtime_read_model_aware_root(
    *,
    request: MetaRuntimeReadModelRequest,
    repo_root: Path,
) -> Path | None:
    if request.aware_root is not None and request.aware_root.strip():
        return Path(request.aware_root).expanduser().resolve()
    return repo_root


def _path_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _int_or_zero(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"Expected float-compatible value, got {value!r}")
    if isinstance(value, (int, float, str)):
        return float(value)
    raise ValueError(f"Expected float-compatible value, got {value!r}")


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _to_runtime_call_target(
    call_target: MetaGraphFunctionCallTarget,
) -> MetaGraphCallTarget:
    return MetaGraphCallTarget(call_target.value)


def _response_from_receipt(
    receipt: MetaGraphCommitReceipt,
    *,
    commit_event: MetaCommitEventEnvelope | None = None,
) -> MetaGraphInvokeFunctionResponse:
    payload = _model_payload(receipt)
    payload["domain_commit_id"] = payload.pop("commit_id", None)
    if commit_event is not None:
        payload["commit_event"] = commit_event.model_dump(mode="json")
    return MetaGraphInvokeFunctionResponse.model_validate(payload)


@dataclass(frozen=True, slots=True)
class _TemporalOverlayPreStateProvider:
    before_oig: ObjectInstanceGraph
    head_commit_id: UUID | None = None

    async def read_pre_state(self, request: object) -> MetaGraphPreStateProviderResult:
        _ = request
        root_class_instance = getattr(self.before_oig, "root_class_instance", None)
        root_object_id = getattr(root_class_instance, "source_object_id", None)
        if not isinstance(root_object_id, UUID):
            root_object_id = getattr(root_class_instance, "id", None)
        if not isinstance(root_object_id, UUID):
            root_object_id = None
        return MetaGraphPreStateProviderResult(
            before_oig=self.before_oig,
            graph_hash_pre=self.before_oig.hash,
            head_commit_id=self.head_commit_id,
            root_object_id=root_object_id,
            oig_index=build_meta_graph_pre_state_index(self.before_oig),
        )


def _temporal_after_oig_from_append_request(
    *,
    before_oig: ObjectInstanceGraph,
    append_request: MetaGraphDomainCommitAppendRequest,
    graph_catalog: ServiceGraphCatalog,
) -> ObjectInstanceGraph:
    source_before_oig = append_request.before_oig or before_oig
    after_oig = source_before_oig.model_copy(deep=True)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=append_request.changes,
        attribute_configs_by_id=graph_catalog.attribute_configs_by_id,
        class_configs_by_id=graph_catalog.class_configs_by_id,
    )
    graph_hash_post = compute_hash(after_oig, index=build_index(after_oig))
    after_oig.hash = graph_hash_post
    expected_graph_hash_post = (append_request.graph_hash_post or "").strip()
    if expected_graph_hash_post and expected_graph_hash_post != graph_hash_post:
        raise ValueError(
            "Meta temporal overlay graph hash mismatch: "
            f"staged={expected_graph_hash_post} applied={graph_hash_post}"
        )
    return after_oig


def _temporal_response_from_staged_append(
    *,
    request: MetaGraphInvokeTemporalFunctionRequest,
    append_request: MetaGraphDomainCommitAppendRequest,
    after_oig: ObjectInstanceGraph,
) -> MetaGraphInvokeTemporalFunctionResponse:
    staged_result = append_request.staged_action.staged_result
    execution_result = staged_result.execution_result
    staged_call = staged_result.staged_call
    response = staged_result.function_call_response
    return MetaGraphInvokeTemporalFunctionResponse(
        status="succeeded" if execution_result.success else "failed",
        actor_id=request.actor_id,
        domain_branch_id=staged_call.lane_scope.domain_branch_id,
        domain_projection_hash=staged_call.lane_scope.domain_projection_hash,
        payload=execution_result.payload,
        error=execution_result.error_message,
        logs=[],
        execution_time_ms=execution_result.execution_time_ms,
        root_object_id=execution_result.root_object_id or append_request.root_object_id,
        graph_hash_pre=append_request.graph_hash_pre,
        graph_hash_post=after_oig.hash,
        changes=JsonArray(
            [jsonify_invocation_payload(change) for change in append_request.changes]
        ),
        before_oig=JsonObject(append_request.before_oig.model_dump(mode="json")),
        after_oig=JsonObject(after_oig.model_dump(mode="json")),
        function_call_id=staged_call.function_call.id,
        function_call_response_id=response.id,
    )


async def _commit_event_from_receipt(
    *,
    request: MetaGraphInvokeFunctionRequest,
    receipt: MetaGraphCommitReceipt,
    host_context: ServiceApiHostContext,
    commit_store: FSCommitStore,
) -> MetaCommitEventEnvelope | None:
    if (
        receipt.status != "succeeded"
        or receipt.commit_id is None
        or receipt.domain_branch_id is None
        or receipt.domain_projection_hash is None
    ):
        return None

    domain_commit = await commit_store.get_commit(
        branch_id=receipt.domain_branch_id,
        projection_hash=receipt.domain_projection_hash,
        commit_id=receipt.commit_id,
    )
    if domain_commit is None:
        return None

    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=domain_commit.object_instance_graph_identity_id,
        commit_id=domain_commit.commit.id,
    )
    if (
        receipt.object_instance_graph_commit_id is not None
        and receipt.object_instance_graph_commit_id != object_instance_graph_commit_id
    ):
        raise ValueError(
            "Meta graph receipt object_instance_graph_commit_id mismatch: "
            + f"receipt={receipt.object_instance_graph_commit_id} "
            + f"expected={object_instance_graph_commit_id}"
        )

    return MetaCommitEventEnvelope(
        event_id=stable_meta_commit_event_id(
            domain_commit_id=domain_commit.commit.id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        ),
        emitted_at_unix_ms=int(domain_commit.commit.created_at.timestamp() * 1000),
        meta_authority_id=host_context.service_name or "aware_meta",
        actor_id=request.actor_id,
        domain_branch_id=receipt.domain_branch_id,
        domain_projection_hash=receipt.domain_projection_hash,
        domain_commit_id=domain_commit.commit.id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=domain_commit.object_instance_graph_id,
        object_instance_graph_identity_id=(
            domain_commit.object_instance_graph_identity_id
        ),
        object_instance_graph_branch_id=stable_object_instance_graph_branch_id(
            object_instance_graph_identity_id=(
                domain_commit.object_instance_graph_identity_id
            ),
            branch_id=receipt.domain_branch_id,
        ),
        graph_hash_pre=domain_commit.graph_hash_pre or None,
        graph_hash_post=domain_commit.graph_hash_post,
        root_object_id=domain_commit.root_source_object_id,
        head_version=1,
        commit_action=_commit_action_metadata_from_receipt(
            request=request,
            receipt=receipt,
        ),
        metadata=JsonObject({"source": "services.meta.graph.invoke_function"}),
    )


def _commit_action_metadata_from_receipt(
    *,
    request: MetaGraphInvokeFunctionRequest,
    receipt: MetaGraphCommitReceipt,
) -> MetaCommitActionMetadata:
    action = receipt.commit_action
    if action is None:
        return MetaCommitActionMetadata(
            call_target=request.call_target,
            function_id=request.function_id,
            operation_label="meta.graph.invoke_function",
            object_id=request.target_object_id,
        )

    return MetaCommitActionMetadata(
        call_target=MetaGraphFunctionCallTarget(action.call_target),
        function_id=action.function_id,
        operation_label=action.operation_label,
        object_id=action.object_id,
        source_class_instance_identity_id=action.class_instance_identity_id,
    )


async def _commit_event_from_package_ensure_response(
    *,
    request: MetaObjectConfigGraphPackageEnsureRequest,
    response: MetaObjectConfigGraphPackageEnsureResponse,
    host_context: ServiceApiHostContext,
    commit_store: FSCommitStore,
    graph_context: ServiceGraphContextLike,
) -> MetaCommitEventEnvelope | None:
    if response.status != "succeeded":
        return None
    if (
        response.package_branch_id is None
        or response.object_config_graph_package_head_commit_id is None
        or response.object_config_graph_package_object_instance_graph_commit_id is None
    ):
        return None
    try:
        projection_hash = find_meta_graph_projection_hash_by_name(
            index=cast(Any, _graph_catalog(graph_context)),
            projection_name="ObjectConfigGraphPackage",
        )
    except Exception:
        logger.debug(
            "Meta package ensure commit event skipped: ObjectConfigGraphPackage "
            "projection is unavailable in the active graph context."
        )
        return None

    domain_commit = await commit_store.get_commit(
        branch_id=response.package_branch_id,
        projection_hash=projection_hash,
        commit_id=response.object_config_graph_package_head_commit_id,
    )
    if domain_commit is None:
        return None

    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=domain_commit.object_instance_graph_identity_id,
        commit_id=domain_commit.commit.id,
    )
    if (
        response.object_config_graph_package_object_instance_graph_commit_id
        != object_instance_graph_commit_id
    ):
        raise ValueError(
            "Meta package ensure object_config_graph_package_object_instance_graph_commit_id mismatch: "
            + f"response={response.object_config_graph_package_object_instance_graph_commit_id} "
            + f"expected={object_instance_graph_commit_id}"
        )

    metadata = JsonObject(
        {
            "source": "services.meta.package.ensure_object_config_graph_package",
        }
    )
    if response.package_name:
        metadata["package_name"] = response.package_name
        metadata["package"] = response.package_name
    if response.fqn_prefix:
        metadata["fqn_prefix"] = response.fqn_prefix
    if response.object_config_graph_package_id is not None:
        metadata["package_id"] = str(response.object_config_graph_package_id)
    if response.object_config_graph_id is not None:
        metadata["object_config_graph_id"] = str(response.object_config_graph_id)

    return MetaCommitEventEnvelope(
        event_id=stable_meta_commit_event_id(
            domain_commit_id=domain_commit.commit.id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        ),
        emitted_at_unix_ms=int(domain_commit.commit.created_at.timestamp() * 1000),
        meta_authority_id=host_context.service_name or "aware_meta",
        actor_id=resolve_meta_author_id(
            request.actor_id
            or response.actor_id
            or host_context.operation_context.actor_id
            or domain_commit.commit.author_id
        ),
        domain_branch_id=response.package_branch_id,
        domain_projection_hash=projection_hash,
        domain_commit_id=domain_commit.commit.id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=domain_commit.object_instance_graph_id,
        object_instance_graph_identity_id=(
            domain_commit.object_instance_graph_identity_id
        ),
        object_instance_graph_branch_id=stable_object_instance_graph_branch_id(
            object_instance_graph_identity_id=(
                domain_commit.object_instance_graph_identity_id
            ),
            branch_id=response.package_branch_id,
        ),
        graph_hash_pre=domain_commit.graph_hash_pre or None,
        graph_hash_post=domain_commit.graph_hash_post,
        root_object_id=domain_commit.root_source_object_id,
        head_version=1,
        commit_action=MetaCommitActionMetadata(
            operation_label="meta.package.ensure_object_config_graph_package",
            object_id=response.object_config_graph_package_id,
        ),
        metadata=metadata,
    )


def _object_config_graph_package_ensure_response(
    *,
    request: MetaObjectConfigGraphPackageEnsureRequest,
    result: object,
) -> MetaObjectConfigGraphPackageEnsureResponse:
    response_started_at = perf_counter()
    code_package = getattr(result, "code_package", None)
    object_config_graph = getattr(result, "object_config_graph", None)
    object_config_graph_package = getattr(
        result,
        "object_config_graph_package",
        None,
    )
    telemetry: dict[str, object] = {
        "semantic_commit_strategy": getattr(
            result,
            "semantic_commit_strategy",
            None,
        ),
        "semantic_commit_fallback_reset": getattr(
            result,
            "semantic_commit_fallback_reset",
            None,
        ),
    }
    lifecycle_receipts = _object_config_graph_package_lifecycle_receipts(
        request=request,
        result=result,
        code_package=code_package,
        object_config_graph_package=object_config_graph_package,
    )
    telemetry["lifecycle_receipts"] = tuple(
        receipt.payload for receipt in lifecycle_receipts
    )
    telemetry["artifact_ownership_receipts"] = tuple(
        receipt.ownership_receipt for receipt in lifecycle_receipts
    )
    if request.collect_telemetry:
        telemetry.update(
            {
                "code_package_build_runtime_telemetry": _json_safe(
                    getattr(result, "code_package_build_runtime_telemetry", {})
                ),
                "code_package_build_invoke_perf_ms": _json_safe(
                    getattr(result, "code_package_build_invoke_perf_ms", {})
                ),
                "code_package_upsert_runtime_telemetry": _json_safe(
                    getattr(result, "code_package_upsert_runtime_telemetry", {})
                ),
                "code_package_upsert_invoke_perf_ms": _json_safe(
                    getattr(result, "code_package_upsert_invoke_perf_ms", {})
                ),
            }
        )
    timings = {
        "phase_timings_s": _json_safe(getattr(result, "phase_timings_s", {})),
        "semantic_commit_phase_timings_s": _json_safe(
            getattr(result, "semantic_commit_phase_timings_s", {})
        ),
    }
    object_config_graph_payload: JsonObject | None = None
    if request.include_object_config_graph and object_config_graph is not None:
        payload_started_at = perf_counter()
        cached_payload = getattr(result, "object_config_graph_payload", None)
        object_config_graph_payload = (
            _optional_json_object(cached_payload)
            if cached_payload is not None
            else _optional_json_object(
                _object_config_graph_transfer_payload(object_config_graph)
            )
        )
        logger.info(
            "Meta package ensure response OCG payload built: package=%s nodes=%d "
            "duration=%.3fs",
            getattr(object_config_graph_package, "package_name", None),
            len(getattr(object_config_graph, "object_config_graph_nodes", ())),
            perf_counter() - payload_started_at,
        )
    model_started_at = perf_counter()
    response = MetaObjectConfigGraphPackageEnsureResponse(
        status="succeeded",
        actor_id=request.actor_id,
        workspace_root=request.workspace_root,
        aware_toml_path=str(getattr(result, "aware_toml_path", "")) or None,
        package_name=getattr(object_config_graph_package, "package_name", None),
        fqn_prefix=(
            getattr(object_config_graph_package, "fqn_prefix", None)
            or getattr(object_config_graph, "fqn_prefix", None)
        ),
        package_branch_id=getattr(result, "package_branch_id", None),
        source_code_package_id=getattr(code_package, "id", None),
        code_package_commit_id=getattr(result, "code_package_commit_id", None),
        code_package_head_commit_id=getattr(
            result,
            "code_package_head_commit_id",
            None,
        ),
        code_package_object_instance_graph_commit_id=getattr(
            result,
            "code_package_object_instance_graph_commit_id",
            None,
        ),
        object_config_graph_id=getattr(object_config_graph, "id", None),
        object_config_graph_hash=getattr(object_config_graph, "hash", None),
        object_config_graph_commit_id=getattr(
            result,
            "object_config_graph_commit_id",
            None,
        ),
        object_config_graph_head_commit_id=getattr(
            result,
            "object_config_graph_head_commit_id",
            None,
        ),
        object_config_graph_object_instance_graph_commit_id=getattr(
            result,
            "object_config_graph_object_instance_graph_commit_id",
            None,
        ),
        object_config_graph_package_id=getattr(
            object_config_graph_package,
            "id",
            None,
        ),
        object_config_graph_package_commit_id=getattr(
            result,
            "object_config_graph_package_commit_id",
            None,
        ),
        object_config_graph_package_head_commit_id=getattr(
            result,
            "object_config_graph_package_head_commit_id",
            None,
        ),
        object_config_graph_package_object_instance_graph_commit_id=getattr(
            result,
            "object_config_graph_package_object_instance_graph_commit_id",
            None,
        ),
        owned_file_paths=list(getattr(result, "owned_file_paths", ())),
        dependency_refs=request.dependency_refs,
        object_config_graph=object_config_graph_payload,
        timings=_json_object(timings),
        telemetry=_json_object(telemetry),
    )
    logger.info(
        "Meta package ensure response model built: package=%s duration=%.3fs total=%.3fs",
        getattr(object_config_graph_package, "package_name", None),
        perf_counter() - model_started_at,
        perf_counter() - response_started_at,
    )
    return response


def _object_config_graph_package_ensure_failed_response(
    *,
    request: MetaObjectConfigGraphPackageEnsureRequest,
    exc: Exception,
) -> MetaObjectConfigGraphPackageEnsureResponse:
    workspace_root = _resolve_workspace_root(request.workspace_root)
    aware_toml_path = _resolve_aware_toml_path(
        workspace_root=workspace_root,
        aware_toml_path=request.aware_toml_path,
    )
    manifest_identity = _object_config_graph_package_manifest_identity(
        aware_toml_path=aware_toml_path,
    )
    telemetry: dict[str, object] = {
        "failure_phase": "object_config_graph_package_ensure",
        "error_type": type(exc).__name__,
        "manifest_identity_source": (
            "aware_toml" if manifest_identity.error is None else "unavailable"
        ),
    }
    if manifest_identity.error is not None:
        telemetry["manifest_identity_error"] = manifest_identity.error
    return MetaObjectConfigGraphPackageEnsureResponse(
        status="failed",
        actor_id=request.actor_id,
        workspace_root=workspace_root.as_posix(),
        aware_toml_path=aware_toml_path.as_posix(),
        package_name=manifest_identity.package_name,
        fqn_prefix=manifest_identity.fqn_prefix,
        package_branch_id=request.package_branch_id or request.parent_branch_id,
        source_code_package_id=request.source_code_package_id,
        object_config_graph_package_id=(
            request.object_config_graph_package_id
            or manifest_identity.object_config_graph_package_id
        ),
        dependency_refs=request.dependency_refs,
        telemetry=_json_object(telemetry),
        error=str(exc),
    )


def _object_config_graph_package_manifest_identity(
    *,
    aware_toml_path: Path,
) -> _ObjectConfigGraphPackageManifestIdentity:
    try:
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        object_config_graph_package_id = stable_object_config_graph_package_id(
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
        return _ObjectConfigGraphPackageManifestIdentity(
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
            object_config_graph_package_id=object_config_graph_package_id,
        )
    except Exception as exc:
        return _ObjectConfigGraphPackageManifestIdentity(
            error=f"{type(exc).__name__}: {exc}",
        )


def _object_config_graph_package_lifecycle_receipts(
    *,
    request: MetaObjectConfigGraphPackageEnsureRequest,
    result: object,
    code_package: object | None,
    object_config_graph_package: object | None,
):
    if code_package is None or object_config_graph_package is None:
        raise RuntimeError(
            "Meta package ensure cannot emit language lifecycle receipts without "
            "CodePackage and ObjectConfigGraphPackage evidence."
        )
    raw_package_name = getattr(object_config_graph_package, "package_name", None)
    package_name = raw_package_name.strip() if isinstance(raw_package_name, str) else ""
    if not package_name:
        raise RuntimeError(
            "Meta package ensure cannot emit language lifecycle receipts without "
            "ObjectConfigGraphPackage.package_name."
        )
    raw_aware_toml_path = (
        getattr(result, "aware_toml_path", None) or request.aware_toml_path
    )
    if raw_aware_toml_path is None:
        raise RuntimeError(
            "Meta package ensure cannot emit language lifecycle receipts without "
            "aware_toml_path."
        )
    workspace_root = _resolve_workspace_root(request.workspace_root)
    aware_toml_path = Path(raw_aware_toml_path).expanduser()
    if not aware_toml_path.is_absolute():
        aware_toml_path = workspace_root / aware_toml_path
    return build_object_config_graph_package_language_lifecycle_receipts(
        aware_root=workspace_root,
        aware_toml_path=aware_toml_path.resolve(),
        package_name=package_name,
        source_code_package_id=getattr(code_package, "id", None),
        object_config_graph_package_id=getattr(object_config_graph_package, "id", None),
        object_config_graph_commit_id=(
            getattr(result, "object_config_graph_object_instance_graph_commit_id", None)
        ),
        source_object_instance_graph_commit_id=(
            getattr(result, "code_package_object_instance_graph_commit_id", None)
        ),
        input_object_instance_graph_commit_id=(
            getattr(result, "object_config_graph_object_instance_graph_commit_id", None)
        ),
    )


def _database_ready_response(
    *,
    request: MetaPersistenceEnsureDatabaseReadyRequest,
    status: str,
    actor_id: UUID | None,
    error: str | None = None,
    installed: bool = False,
    migrated: bool = False,
    marker_ocg_hash: str | None = None,
    marker_head_commit_id: UUID | None = None,
    sql_root_count: int = 0,
    step_count: int = 0,
    seeded_ocg_config: bool = False,
    hydrated_domain_lanes: Sequence[str] = (),
) -> MetaPersistenceEnsureDatabaseReadyResponse:
    receipt = request.database_artifact_receipt
    return MetaPersistenceEnsureDatabaseReadyResponse(
        status=status,
        error=error,
        actor_id=actor_id,
        meta_package_id=receipt.meta_package_id,
        ocg_id=receipt.ocg_id,
        ocg_hash=receipt.ocg_hash,
        db_schema_hash=receipt.db_schema_hash,
        db_schema_registry_hash=receipt.db_schema_registry_ref.hash,
        installed=installed,
        migrated=migrated,
        marker_ocg_hash=marker_ocg_hash,
        marker_head_commit_id=marker_head_commit_id,
        sql_root_count=sql_root_count,
        step_count=step_count,
        seeded_ocg_config=seeded_ocg_config,
        hydrated_domain_lanes=list(hydrated_domain_lanes),
    )


async def _ensure_database_ready_response(
    *,
    request: MetaPersistenceEnsureDatabaseReadyRequest,
    actor_id: UUID | None,
) -> MetaPersistenceEnsureDatabaseReadyResponse:
    receipt = request.database_artifact_receipt
    sql_roots = _validate_database_ready_request(request)
    database_url = _resolve_database_url(request.database_url_ref)
    connection = await _connect_database(database_url)
    migrated = False
    try:
        boot_result, migrated = await _ensure_database_schema_ready(
            connection=connection,
            sql_roots=sql_roots,
            environment_config_id=receipt.meta_package_id or receipt.ocg_id,
            db_schema_hash=receipt.db_schema_hash,
            ocg_head_commit_id=receipt.ocg_head_commit_id,
            ocg_lane_index_ref_path=(
                receipt.ocg_lane_index_ref.path
                if receipt.ocg_lane_index_ref is not None
                else None
            ),
            boot_policy=request.boot_policy,
        )
    finally:
        await connection.close()

    return _database_ready_response(
        request=request,
        status="succeeded",
        actor_id=actor_id,
        installed=boot_result.installed,
        migrated=migrated,
        marker_ocg_hash=boot_result.ocg_hash,
        marker_head_commit_id=boot_result.ocg_head_commit_id,
        sql_root_count=len(boot_result.sql_roots),
        step_count=boot_result.step_count,
    )


def _validate_database_ready_request(
    request: MetaPersistenceEnsureDatabaseReadyRequest,
) -> list[Path]:
    receipt = request.database_artifact_receipt
    if receipt.db_backend_target != "postgres":
        raise RuntimeError(
            "Meta DB readiness currently supports only postgres backend "
            f"(got {receipt.db_backend_target!r})."
        )
    if receipt.db_package_kind != "ontology":
        raise RuntimeError(
            "Meta DB readiness currently supports only ontology package kind "
            f"(got {receipt.db_package_kind!r})."
        )
    if not receipt.ocg_hash.strip():
        raise RuntimeError("Meta DB readiness requires receipt.ocg_hash.")
    if not receipt.db_schema_hash.strip():
        raise RuntimeError("Meta DB readiness requires receipt.db_schema_hash.")
    if not receipt.db_schema_registry_ref.hash.strip():
        raise RuntimeError(
            "Meta DB readiness requires receipt.db_schema_registry_ref.hash."
        )
    if request.boot_policy not in {"fail", "migrate", "rebuild"}:
        raise RuntimeError(
            "Unsupported Meta DB readiness boot_policy="
            f"{request.boot_policy!r} (expected fail, migrate, or rebuild)."
        )
    sql_roots = [Path(value).expanduser().resolve() for value in receipt.sql_roots]
    if not sql_roots:
        raise RuntimeError("Meta DB readiness requires at least one SQL root.")
    return sql_roots


def _resolve_database_url(database_url_ref: str | None) -> str:
    if database_url_ref is not None and database_url_ref.strip():
        raw_ref = database_url_ref.strip()
        if raw_ref.startswith("env:"):
            env_name = raw_ref.removeprefix("env:").strip()
            value = os.environ.get(env_name)
            if value:
                return value
            raise RuntimeError(f"Database URL env ref is unset: {raw_ref}")
        if "://" not in raw_ref and raw_ref in os.environ:
            value = os.environ.get(raw_ref)
            if value:
                return value
        return raw_ref

    value = os.environ.get("DATABASE_URL")
    if value:
        return value
    raise RuntimeError(
        "Meta DB readiness requires DATABASE_URL or request.database_url_ref."
    )


async def _connect_database(database_url: str) -> _ClosableDBBootConnection:
    factory = MetaDatabaseReadyConnectionFactory
    if factory is not None:
        return await factory(database_url)
    try:
        import asyncpg  # pyright: ignore[reportMissingTypeStubs]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "asyncpg is required for Meta DB readiness against Postgres."
        ) from exc
    connect = cast(
        Callable[[str], Awaitable[_ClosableDBBootConnection]],
        asyncpg.connect,
    )
    return await connect(database_url)


async def _ensure_database_schema_ready(
    *,
    connection: object,
    sql_roots: Sequence[Path],
    environment_config_id: UUID,
    db_schema_hash: str,
    ocg_head_commit_id: UUID | None,
    ocg_lane_index_ref_path: str | None,
    boot_policy: str,
) -> tuple[Any, bool]:
    from aware_orm.db.boot import (
        DBBootExecutionError,
        ensure_db_schema_installed_multi,
    )

    try:
        return (
            await ensure_db_schema_installed_multi(
                connection=connection,
                sql_roots=tuple(sql_roots),
                environment_id=environment_config_id,
                ocg_hash=db_schema_hash,
                ocg_head_commit_id=ocg_head_commit_id,
            ),
            False,
        )
    except DBBootExecutionError as exc:
        if boot_policy == "migrate":
            if ocg_lane_index_ref_path is None:
                raise RuntimeError(
                    "Meta DB readiness boot_policy=migrate requires "
                    "receipt.ocg_lane_index_ref."
                ) from exc
            lane_json_path = Path(ocg_lane_index_ref_path).expanduser().resolve()
            if not lane_json_path.is_file():
                raise RuntimeError(
                    "Meta DB readiness boot_policy=migrate requires existing "
                    f"OCG lane index at {lane_json_path}."
                ) from exc
            from aware_orm.runtime.ocg_migrations import apply_ocg_sql_migrations

            migration = await apply_ocg_sql_migrations(
                connection=connection,
                lane_json_path=lane_json_path,
                environment_id=environment_config_id,
                desired_ocg_hash=db_schema_hash,
                sql_roots=tuple(sql_roots),
            )
            result = await ensure_db_schema_installed_multi(
                connection=connection,
                sql_roots=tuple(sql_roots),
                environment_id=environment_config_id,
                ocg_hash=db_schema_hash,
                ocg_head_commit_id=ocg_head_commit_id,
            )
            return result, bool(getattr(migration, "applied", False))
        if boot_policy == "rebuild":
            raise RuntimeError(
                "Meta DB readiness detected DB schema drift and "
                "boot_policy=rebuild. Automatic rebuild is not performed at "
                "service runtime; rebuild from committed graph truth."
            ) from exc
        raise


def _graph_view_response(
    *,
    request: MetaGraphResolveGraphViewRequest,
    status: str,
    domain_commit_id: UUID | None = None,
    object_instance_graph_commit_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    graph_catalog: Any | None = None,
    opg: Any | None = None,
    oig: ObjectInstanceGraph | None = None,
    summary: str | None = None,
    error: str | None = None,
) -> MetaGraphResolveGraphViewResponse:
    snapshot = (
        _graph_snapshot_from_oig(
            oig=oig,
            graph_catalog=graph_catalog,
            request=request,
        )
        if oig is not None and graph_catalog is not None
        else MetaGraphSnapshot(
            summary=summary,
            metadata=_json_object(
                {
                    "view_key": request.view_key,
                    "projection_hash": request.domain_projection_hash,
                }
            ),
        )
    )
    if summary is None:
        summary = snapshot.summary
    return MetaGraphResolveGraphViewResponse(
        status=status,
        actor_id=request.actor_id,
        domain_branch_id=request.domain_branch_id,
        domain_projection_hash=request.domain_projection_hash,
        domain_commit_id=domain_commit_id or request.domain_commit_id,
        object_instance_graph_commit_id=(
            object_instance_graph_commit_id or request.object_instance_graph_commit_id
        ),
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        object_config_graph_ref=(
            _object_config_graph_view_ref(index=graph_catalog)
            if graph_catalog is not None
            else None
        ),
        object_projection_graph_ref=(
            _object_projection_graph_view_ref(index=graph_catalog, opg=opg)
            if graph_catalog is not None and opg is not None
            else None
        ),
        object_instance_graph_ref=(
            MetaGraphViewRef(
                graph_kind="object_instance_graph",
                id=str(object_instance_graph_id),
                stable_identity=(
                    str(object_instance_graph_identity_id)
                    if object_instance_graph_identity_id is not None
                    else None
                ),
                label=getattr(oig, "name", None) if oig is not None else None,
                metadata=_json_object(
                    {"hash": getattr(oig, "hash", None)} if oig is not None else {}
                ),
            )
            if object_instance_graph_id is not None
            else None
        ),
        object_instance_graph_branch_ref=(
            MetaGraphViewRef(
                graph_kind="object_instance_graph_branch",
                id=str(object_instance_graph_branch_id),
                stable_identity=str(object_instance_graph_branch_id),
                label=str(request.domain_branch_id),
                metadata=_json_object(
                    {"domain_branch_id": str(request.domain_branch_id)}
                ),
            )
            if object_instance_graph_branch_id is not None
            else None
        ),
        object_instance_graph_commit_ref=(
            MetaGraphViewRef(
                graph_kind="object_instance_graph_commit",
                id=str(object_instance_graph_commit_id),
                stable_identity=str(object_instance_graph_commit_id),
                label=str(domain_commit_id or request.domain_commit_id or ""),
                metadata=_json_object(
                    {
                        "domain_commit_id": (
                            str(domain_commit_id)
                            if domain_commit_id is not None
                            else None
                        ),
                    }
                ),
            )
            if object_instance_graph_commit_id is not None
            else None
        ),
        graph_snapshot=snapshot,
        summary=summary,
        provenance=_json_object(
            {
                "source": "aware_meta_service.graph.resolve_graph_view",
                "view_key": request.view_key,
                "projection_name": request.projection_name,
            }
        ),
        error=error,
    )


def _object_config_graph_view_ref(*, index: Any) -> MetaGraphViewRef | None:
    ocg = getattr(index, "ocg", None)
    if ocg is None:
        return None
    ocgi = getattr(ocg, "object_config_graph_identity", None)
    return MetaGraphViewRef(
        graph_kind="object_config_graph",
        id=_optional_string(getattr(ocg, "id", None)),
        stable_identity=_optional_string(getattr(ocgi, "id", None)),
        fqn=_optional_string(getattr(ocg, "fqn_prefix", None)),
        label=(
            _optional_string(getattr(ocg, "name", None))
            or _optional_string(getattr(ocg, "fqn_prefix", None))
        ),
        metadata=_json_object(
            {
                "hash": _optional_string(getattr(ocg, "hash", None)),
                "package": _optional_string(getattr(ocg, "name", None)),
            }
        ),
    )


def _object_projection_graph_view_ref(
    *,
    index: Any,
    opg: Any,
) -> MetaGraphViewRef:
    projection_hash = _optional_string(getattr(opg, "projection_hash", None))
    stable_identity = None
    if projection_hash is not None:
        try:
            _, opgi = resolve_meta_graph_ocgi_opgi(
                index=index,
                projection_hash=projection_hash,
            )
            stable_identity = _optional_string(getattr(opgi, "id", None))
        except Exception:
            stable_identity = None
    namespace, symbol = _namespace_symbol(_optional_string(getattr(opg, "name", None)))
    return MetaGraphViewRef(
        graph_kind="object_projection_graph",
        id=_optional_string(getattr(opg, "id", None)),
        stable_identity=stable_identity,
        fqn=_optional_string(getattr(opg, "name", None)),
        namespace=namespace,
        symbol=symbol,
        label=_optional_string(getattr(opg, "name", None)),
        metadata=_json_object({"projection_hash": projection_hash}),
    )


def _graph_snapshot_from_oig(
    *,
    oig: ObjectInstanceGraph,
    graph_catalog: Any,
    request: MetaGraphResolveGraphViewRequest,
) -> MetaGraphSnapshot:
    all_instances = _graph_view_class_instances(oig=oig)
    max_nodes = request.max_nodes
    selected_instances = (
        all_instances[: max(max_nodes, 0)] if max_nodes is not None else all_instances
    )
    selected_node_ids = {
        str(getattr(instance, "id", ""))
        for instance in selected_instances
        if getattr(instance, "id", None) is not None
    }
    nodes = [
        _graph_snapshot_node_from_class_instance(
            class_instance=instance,
            graph_catalog=graph_catalog,
            include_attributes=request.include_attributes,
            is_root=instance is getattr(oig, "root_class_instance", None),
        )
        for instance in selected_instances
    ]
    edges = [
        _graph_snapshot_edge_from_relationship(
            relationship=relationship,
            graph_catalog=graph_catalog,
        )
        for relationship in getattr(oig, "class_instance_relationships", ()) or ()
        if str(getattr(relationship, "source_class_instance_id", ""))
        in selected_node_ids
        and str(getattr(relationship, "target_class_instance_id", ""))
        in selected_node_ids
    ]
    truncated = len(selected_instances) < len(all_instances)
    return MetaGraphSnapshot(
        nodes=nodes,
        edges=edges,
        root_identity=_optional_string(
            getattr(getattr(oig, "root_class_instance", None), "source_object_id", None)
        ),
        summary=f"{len(nodes)} nodes, {len(edges)} edges",
        metadata=_json_object(
            {
                "view_key": request.view_key,
                "projection_hash": request.domain_projection_hash,
                "object_instance_graph_id": _optional_string(getattr(oig, "id", None)),
                "hash": _optional_string(getattr(oig, "hash", None)),
                "total_nodes": len(all_instances),
                "total_edges": len(
                    getattr(oig, "class_instance_relationships", ()) or ()
                ),
                "truncated": truncated,
            }
        ),
    )


def _graph_view_class_instances(*, oig: ObjectInstanceGraph) -> list[Any]:
    instances: list[Any] = []
    seen_ids: set[object] = set()

    def add(instance: Any | None) -> None:
        if instance is None:
            return
        instance_id = getattr(instance, "id", None)
        if instance_id is not None:
            if instance_id in seen_ids:
                return
            seen_ids.add(instance_id)
        instances.append(instance)

    add(getattr(oig, "root_class_instance", None))
    for instance in getattr(oig, "class_instances", ()) or ():
        add(instance)
    return instances


def _graph_snapshot_node_from_class_instance(
    *,
    class_instance: Any,
    graph_catalog: Any,
    include_attributes: bool,
    is_root: bool,
) -> MetaGraphSnapshotNode:
    class_config = getattr(class_instance, "class_config", None)
    if class_config is None:
        class_config = getattr(graph_catalog, "class_configs_by_id", {}).get(
            getattr(class_instance, "class_config_id", None)
        )
    class_fqn = _optional_string(getattr(class_config, "class_fqn", None))
    namespace, symbol = _namespace_symbol(class_fqn)
    label = (
        _optional_string(getattr(class_config, "name", None))
        or symbol
        or _optional_string(getattr(class_instance, "source_object_id", None))
        or _optional_string(getattr(class_instance, "id", None))
        or "object"
    )
    metadata: dict[str, object] = {
        "class_config_id": _optional_string(
            getattr(class_instance, "class_config_id", None)
        ),
        "source_object_id": _optional_string(
            getattr(class_instance, "source_object_id", None)
        ),
        "root": is_root,
    }
    if include_attributes:
        metadata["attributes"] = [
            _class_instance_attribute_metadata(edge)
            for edge in getattr(class_instance, "class_instance_attributes", ()) or ()
        ]
    return MetaGraphSnapshotNode(
        id=str(getattr(class_instance, "id")),
        label=label,
        fqn=class_fqn,
        namespace=namespace,
        symbol=symbol,
        object_kind="class_instance",
        stable_identity=_optional_string(
            getattr(class_instance, "source_object_id", None)
        ),
        metadata=_json_object(metadata),
    )


def _graph_snapshot_edge_from_relationship(
    *,
    relationship: Any,
    graph_catalog: Any,
) -> MetaGraphSnapshotEdge:
    config_relationship = getattr(relationship, "class_config_relationship", None)
    if config_relationship is None:
        config_relationship = getattr(graph_catalog, "relationships_by_id", {}).get(
            getattr(relationship, "class_config_relationship_id", None)
        )
    relationship_kind = _source_language_text(
        getattr(config_relationship, "relationship_type", None)
    )
    label = _optional_string(getattr(config_relationship, "relationship_key", None))
    return MetaGraphSnapshotEdge(
        id=str(getattr(relationship, "id")),
        source_node_id=str(getattr(relationship, "source_class_instance_id")),
        target_node_id=str(getattr(relationship, "target_class_instance_id")),
        relationship_kind=relationship_kind,
        label=label,
        metadata=_json_object(
            {
                "class_config_relationship_id": _optional_string(
                    getattr(relationship, "class_config_relationship_id", None)
                ),
                "class_instance_relationship_identity_id": _optional_string(
                    getattr(
                        relationship,
                        "class_instance_relationship_identity_id",
                        None,
                    )
                ),
            }
        ),
    )


def _class_instance_attribute_metadata(edge: Any) -> dict[str, object]:
    attribute = getattr(edge, "attribute", None)
    return {
        "attribute_id": _optional_string(getattr(edge, "attribute_id", None)),
        "attribute_config_id": _optional_string(
            getattr(attribute, "attribute_config_id", None)
        ),
        "value_root_id": _optional_string(getattr(attribute, "value_root_id", None)),
    }


def _namespace_symbol(fqn: str | None) -> tuple[str | None, str | None]:
    if fqn is None:
        return None, None
    namespace, _, symbol = fqn.rpartition(".")
    return namespace or None, symbol or fqn


def _object_instance_graph_commit_response(
    *,
    request: MetaGraphGetObjectInstanceGraphCommitRequest,
    domain_commit: ObjectInstanceGraphCommit,
) -> MetaGraphGetObjectInstanceGraphCommitResponse:
    return MetaGraphGetObjectInstanceGraphCommitResponse(
        status="succeeded",
        actor_id=request.actor_id,
        domain_branch_id=request.domain_branch_id,
        domain_projection_hash=request.domain_projection_hash,
        domain_commit_id=domain_commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=(
                domain_commit.object_instance_graph_identity_id
            ),
            commit_id=domain_commit.commit.id,
        ),
        object_instance_graph_id=domain_commit.object_instance_graph_id,
        object_instance_graph_identity_id=(
            domain_commit.object_instance_graph_identity_id
        ),
        root_object_id=domain_commit.root_source_object_id,
        graph_hash_pre=domain_commit.graph_hash_pre or None,
        graph_hash_post=domain_commit.graph_hash_post,
        source_language=_source_language_text(domain_commit.source_language),
        commit_author_id=domain_commit.commit.author_id,
        commit_created_at_unix_ms=int(
            domain_commit.commit.created_at.timestamp() * 1000
        ),
        commit=_json_object(_model_payload(domain_commit)),
    )


def _resolve_projection_response(
    *,
    index: Any,
    request: MetaGraphResolveProjectionRequest,
) -> MetaGraphResolveProjectionResponse:
    available_projection_names = (
        _available_projection_names(index=index) if request.include_available else []
    )
    selectors = [
        value is not None and str(value).strip() != ""
        for value in (
            request.projection_name,
            request.projection_hash,
            request.object_projection_graph_id,
        )
    ]
    if sum(1 for selected in selectors if selected) != 1:
        return MetaGraphResolveProjectionResponse(
            status="invalid_request",
            actor_id=request.actor_id,
            available_projection_names=available_projection_names,
            error=(
                "Meta graph projection resolution requires exactly one selector: "
                "projection_name, projection_hash, or object_projection_graph_id"
            ),
        )

    if request.projection_hash is not None and request.projection_hash.strip():
        projection_hash = request.projection_hash.strip()
        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            return MetaGraphResolveProjectionResponse(
                status="not_found",
                actor_id=request.actor_id,
                projection_hash=projection_hash,
                available_projection_names=available_projection_names,
                error=f"Projection hash {projection_hash!r} was not found",
            )
        return _projection_response_from_opg(
            index=index,
            request=request,
            opg=opg,
            available_projection_names=available_projection_names,
        )

    if request.object_projection_graph_id is not None:
        matches = [
            opg
            for opg in _object_projection_graphs(index=index)
            if getattr(opg, "id", None) == request.object_projection_graph_id
        ]
        if not matches:
            return MetaGraphResolveProjectionResponse(
                status="not_found",
                actor_id=request.actor_id,
                object_projection_graph_id=request.object_projection_graph_id,
                available_projection_names=available_projection_names,
                error=(
                    "ObjectProjectionGraph id "
                    f"{request.object_projection_graph_id} was not found"
                ),
            )
        return _projection_response_from_opg(
            index=index,
            request=request,
            opg=matches[0],
            available_projection_names=available_projection_names,
        )

    projection_name = str(request.projection_name or "").strip()
    matches = [
        opg
        for opg in _object_projection_graphs(index=index)
        if str(getattr(opg, "name", "") or "").strip().casefold()
        == projection_name.casefold()
    ]
    if not matches:
        return MetaGraphResolveProjectionResponse(
            status="not_found",
            actor_id=request.actor_id,
            projection_name=projection_name,
            available_projection_names=available_projection_names,
            error=f"Projection name {projection_name!r} was not found",
        )
    if len(matches) > 1:
        matched_hashes = sorted(
            str(getattr(opg, "projection_hash", "") or "").strip()
            for opg in matches
            if str(getattr(opg, "projection_hash", "") or "").strip()
        )
        return MetaGraphResolveProjectionResponse(
            status="ambiguous",
            actor_id=request.actor_id,
            projection_name=projection_name,
            matched_projection_hashes=matched_hashes,
            available_projection_names=available_projection_names,
            error=(
                f"Projection name {projection_name!r} matched multiple projection hashes"
            ),
        )
    return _projection_response_from_opg(
        index=index,
        request=request,
        opg=matches[0],
        available_projection_names=available_projection_names,
    )


def _projection_response_from_opg(
    *,
    index: Any,
    request: MetaGraphResolveProjectionRequest,
    opg: Any,
    available_projection_names: list[str],
) -> MetaGraphResolveProjectionResponse:
    projection_hash = str(getattr(opg, "projection_hash", "") or "").strip()
    ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    return MetaGraphResolveProjectionResponse(
        status="succeeded",
        actor_id=request.actor_id,
        projection_name=str(getattr(opg, "name", "") or "").strip() or None,
        projection_hash=projection_hash or None,
        object_projection_graph_id=getattr(opg, "id", None),
        object_projection_graph_identity_id=(opgi.id if opgi is not None else None),
        object_config_graph_id=getattr(getattr(index, "ocg", None), "id", None),
        object_config_graph_identity_id=(ocgi.id if ocgi is not None else None),
        language=_source_language_text(getattr(opg, "language", None)),
        supports_virtual_build=getattr(opg, "supports_virtual_build", None),
        matched_projection_hashes=([projection_hash] if projection_hash else []),
        available_projection_names=available_projection_names,
    )


def _object_projection_graphs(*, index: Any) -> list[Any]:
    ocg = getattr(index, "ocg", None)
    graphs = getattr(ocg, "object_projection_graphs", None)
    if isinstance(graphs, list):
        return graphs
    return list(getattr(index, "opg_by_hash", {}).values())


def _available_projection_names(*, index: Any) -> list[str]:
    return sorted(
        {
            name
            for name in (
                str(getattr(opg, "name", "") or "").strip()
                for opg in _object_projection_graphs(index=index)
            )
            if name
        }
    )


def _resolve_workspace_root(value: str | None) -> Path:
    if value is not None and value.strip():
        return Path(value).expanduser().resolve()
    host_context = current_service_api_host_context()
    if host_context is not None and host_context.workspace_root is not None:
        return host_context.workspace_root.expanduser().resolve()
    raise RuntimeError(
        "Meta service API request requires workspace_root or a hosted "
        "Service API workspace_root context."
    )


def _resolve_package_root(*, workspace_root: Path, package_root: str) -> Path:
    path = Path(package_root).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return path.resolve()


def _resolve_aware_toml_path(*, workspace_root: Path, aware_toml_path: str) -> Path:
    path = Path(aware_toml_path).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return path.resolve()


def _resolve_optional_aware_toml_path(
    *,
    package_root: Path,
    aware_toml_path: str | None,
) -> Path:
    if aware_toml_path is None or not aware_toml_path.strip():
        return (package_root / "aware.toml").resolve()
    path = Path(aware_toml_path).expanduser()
    if not path.is_absolute():
        path = package_root / path
    return path.resolve()


def _resolve_meta_completeness_source_files(
    *,
    package_root: Path,
    source_files: Sequence[str],
) -> tuple[Path, ...]:
    if source_files:
        resolved: list[Path] = []
        for source_file in source_files:
            path = Path(source_file).expanduser()
            if not path.is_absolute():
                path = package_root / path
            resolved.append(path.resolve())
        return tuple(resolved)
    return tuple(sorted((package_root / "aware").rglob("*.aware")))


async def _dependency_graphs_from_refs(
    dependency_refs: list[MetaObjectConfigGraphPackageDependencyRef],
    *,
    index: Any,
    parent_branch_id: UUID | None,
) -> list[ObjectConfigGraph]:
    graphs: list[ObjectConfigGraph] = []
    unresolved: list[str] = []
    for ref in dependency_refs:
        graph = await _dependency_graph_from_ref(
            ref,
            index=index,
            parent_branch_id=parent_branch_id,
        )
        if graph is None:
            unresolved.append(ref.package_name or ref.fqn_prefix or "<anonymous>")
            continue
        if (
            ref.object_config_graph_id is not None
            and graph.id != ref.object_config_graph_id
        ):
            raise ValueError(
                "Dependency ObjectConfigGraph id mismatch: "
                + f"ref={ref.object_config_graph_id} payload={graph.id}"
            )
        graphs.append(graph)
    if unresolved:
        raise RuntimeError(
            "Meta package OCG compile could not hydrate dependency ObjectConfigGraph refs: "
            + ", ".join(unresolved)
        )
    return graphs


async def _diagnostic_dependency_graphs_from_refs(
    dependency_refs: list[MetaObjectConfigGraphPackageDependencyRef],
    *,
    graph_context_provider: Callable[[], Awaitable[Any]],
    parent_branch_id: UUID | None,
) -> list[ObjectConfigGraph]:
    if not dependency_refs:
        return []
    if all(ref.object_config_graph is not None for ref in dependency_refs):
        return [
            _object_config_graph_from_dependency_payload(
                cast(JsonObject, ref.object_config_graph),
            )
            for ref in dependency_refs
        ]
    return await _dependency_graphs_from_refs(
        dependency_refs,
        index=_graph_catalog(await graph_context_provider()),
        parent_branch_id=parent_branch_id,
    )


async def _dependency_graph_from_ref(
    ref: MetaObjectConfigGraphPackageDependencyRef,
    *,
    index: Any,
    parent_branch_id: UUID | None,
) -> ObjectConfigGraph | None:
    if ref.object_config_graph is not None:
        return _object_config_graph_from_dependency_payload(ref.object_config_graph)

    if parent_branch_id is None or ref.object_config_graph_id is None:
        return None
    package_name = (ref.package_name or "").strip()
    fqn_prefix = (ref.fqn_prefix or "").strip()
    if not package_name or not fqn_prefix:
        return None

    object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ObjectConfigGraph",
    )
    package_branch_id = stable_semantic_package_branch_id(
        parent_branch_id=parent_branch_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    return await _hydrate_object_config_graph_from_head(
        index=index,
        branch_id=package_branch_id,
        projection_hash=object_config_graph_projection_hash,
        root_id=ref.object_config_graph_id,
    )


async def _hydrate_object_config_graph_from_head(
    *,
    index: Any,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
) -> ObjectConfigGraph | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Meta package OCG compile missing dependency projection hash: "
            + projection_hash
        )

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=ObjectConfigGraph,
        root_id=root_id,
        branch_id=branch_id,
    )


def _object_config_graph_from_dependency_payload(
    payload: JsonObject,
) -> ObjectConfigGraph:
    normalized_payload = _normalize_object_config_graph_dependency_payload(payload)
    try:
        return ObjectConfigGraph.model_validate(normalized_payload)
    except Exception:
        data = dict(normalized_payload)
        raw_id = data.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            data["id"] = UUID(raw_id)
        return ObjectConfigGraph.model_construct(**data)


def _normalize_object_config_graph_dependency_payload(
    payload: JsonObject,
) -> dict[str, object]:
    return dict(payload)


def _object_config_graph_transfer_payload(
    object_config_graph: object,
) -> dict[str, object]:
    if _is_object_config_graph_like(object_config_graph):
        return _compact_object_config_graph_payload(object_config_graph)
    payload = _json_safe(object_config_graph)
    if not isinstance(payload, dict):
        raise TypeError(
            "Expected ObjectConfigGraph-compatible payload, got "
            f"{type(object_config_graph)!r}"
        )
    return cast(dict[str, object], payload)


def _is_object_config_graph_like(value: object) -> bool:
    return isinstance(value, ObjectConfigGraph) or value.__class__.__name__ == (
        "ObjectConfigGraph"
    )


def _compact_object_config_graph_payload(graph: object) -> dict[str, object]:
    started_at = perf_counter()
    payload = _compact_fields(
        graph,
        (
            "id",
            "name",
            "description",
            "hash",
            "layout_hash",
            "domain_hierarchy_signature",
            "fqn_prefix",
            "language",
            "object_config_graph_identity_id",
        ),
    )
    payload["object_config_graph_annotations"] = [
        _compact_object_config_graph_annotation_payload(annotation)
        for annotation in getattr(graph, "object_config_graph_annotations", ())
    ]
    payload["object_config_graph_mirrors"] = [
        _compact_object_config_graph_mirror_payload(mirror)
        for mirror in getattr(graph, "object_config_graph_mirrors", ())
    ]
    nodes = list(getattr(graph, "object_config_graph_nodes", ()))
    payload["object_config_graph_nodes"] = [
        _compact_object_config_graph_node_payload(node) for node in nodes
    ]
    namespace_membership = build_namespace_membership_payload_from_ocg_identity(
        ocg=cast(ObjectConfigGraph, graph),
    )
    if namespace_membership:
        payload["namespace_membership"] = [
            dict(entry) for entry in namespace_membership
        ]
    payload["object_config_graph_bindings"] = [
        _compact_object_config_graph_binding_payload(binding)
        for binding in getattr(graph, "object_config_graph_bindings", ())
    ]
    payload["object_config_graph_relationships"] = [
        _compact_object_config_graph_relationship_payload(relationship)
        for relationship in getattr(graph, "object_config_graph_relationships", ())
    ]
    payload["object_projection_graph_declarations"] = [
        _compact_object_projection_graph_declaration_payload(declaration)
        for declaration in getattr(graph, "object_projection_graph_declarations", ())
    ]
    payload["object_projection_graphs"] = [
        _compact_object_projection_graph_payload(opg)
        for opg in getattr(graph, "object_projection_graphs", ())
    ]
    logger.info(
        "Meta OCG compact transfer finished: graph=%s nodes=%d duration=%.3fs",
        getattr(graph, "name", None),
        len(nodes),
        perf_counter() - started_at,
    )
    return payload


def _compact_object_config_graph_mirror_payload(mirror: object) -> dict[str, object]:
    return _compact_fields(
        mirror,
        (
            "id",
            "fqn_prefix",
            "namespace",
            "target_text",
            "layout_kind",
            "relative_path",
            "source_position",
            "target_kind",
            "object_config_graph_id",
            "source_object_config_graph_id",
            "class_config_id",
            "enum_config_id",
            "code_section_mirror_id",
        ),
    )


def _compact_object_config_graph_node_payload(node: object) -> dict[str, object]:
    payload = _compact_fields(
        node,
        (
            "id",
            "type",
            "node_key",
            "object_config_graph_id",
            "class_config_relationship_id",
        ),
    )
    class_config = getattr(node, "class_config", None)
    if class_config is not None:
        payload["class_config"] = _compact_class_config_payload(class_config)
    relationship = getattr(node, "class_config_relationship", None)
    if relationship is not None:
        payload["class_config_relationship"] = (
            _compact_class_config_relationship_payload(relationship)
        )
    enum_config = getattr(node, "enum_config", None)
    if enum_config is not None:
        payload["enum_config"] = _compact_enum_config_payload(enum_config)
    layouts = [
        _compact_object_config_graph_node_layout_payload(layout)
        for layout in getattr(node, "layouts", ())
    ]
    if layouts:
        payload["layouts"] = layouts
    return payload


def _compact_object_config_graph_node_layout_payload(
    layout: object,
) -> dict[str, object]:
    return _compact_fields(
        layout,
        (
            "id",
            "layout_kind",
            "object_config_graph_node_id",
            "relative_path",
            "source_position",
        ),
    )


def _compact_class_config_payload(class_config: object) -> dict[str, object]:
    payload = _compact_fields(
        class_config,
        (
            "id",
            "class_fqn",
            "description",
            "name",
            "is_base",
            "is_edge",
            "value_mode",
            "identity_mode",
            "object_config_graph_node_id",
            "parent_class_id",
            "code_section_class_id",
        ),
    )
    payload["class_config_attribute_configs"] = [
        _compact_class_config_attribute_config_payload(link)
        for link in getattr(class_config, "class_config_attribute_configs", ())
    ]
    payload["class_config_function_configs"] = [
        _compact_class_config_function_config_payload(link)
        for link in getattr(class_config, "class_config_function_configs", ())
    ]
    payload["class_config_relationships"] = [
        _compact_class_config_relationship_payload(relationship)
        for relationship in getattr(class_config, "class_config_relationships", ())
    ]
    return payload


def _compact_class_config_relationship_payload(
    relationship: object,
) -> dict[str, object]:
    payload = _compact_fields(
        relationship,
        (
            "id",
            "relationship_key",
            "relationship_type",
            "identity_rail",
            "forward_required",
            "forward_loading_strategy",
            "reverse_loading_strategy",
            "reified_role",
            "class_config_id",
            "target_class_config_id",
            "reified_from_relationship_id",
        ),
    )
    payload["class_config_relationship_attributes"] = [
        _compact_fields(
            attribute,
            (
                "id",
                "direction",
                "role",
                "class_config_relationship_id",
                "attribute_config_id",
            ),
        )
        for attribute in getattr(
            relationship,
            "class_config_relationship_attributes",
            (),
        )
    ]
    association_edge = getattr(
        relationship,
        "class_config_relationship_association_edge",
        None,
    )
    if association_edge is not None:
        payload["class_config_relationship_association_edge"] = _compact_fields(
            association_edge,
            (
                "id",
                "class_config_id",
                "class_config_relationship_id",
                "forward_loading_strategy",
                "reverse_loading_strategy",
            ),
        )
    return payload


def _compact_class_config_attribute_config_payload(link: object) -> dict[str, object]:
    payload = _compact_fields(
        link,
        (
            "id",
            "position",
            "is_identity_key",
            "class_config_id",
            "attribute_config_id",
        ),
    )
    payload["attribute_config"] = _compact_attribute_config_payload(
        getattr(link, "attribute_config")
    )
    return payload


def _compact_class_config_function_config_payload(link: object) -> dict[str, object]:
    payload = _compact_fields(
        link,
        (
            "id",
            "is_public",
            "is_constructor",
            "position",
            "class_config_id",
            "function_config_id",
        ),
    )
    payload["function_config"] = _compact_function_config_payload(
        getattr(link, "function_config")
    )
    return payload


def _compact_function_config_payload(function_config: object) -> dict[str, object]:
    payload = _compact_fields(
        function_config,
        (
            "id",
            "owner_key",
            "name",
            "description",
            "verb",
            "is_async",
            "kind",
            "code_section_function_id",
        ),
    )
    payload["function_config_attribute_configs"] = [
        _compact_function_config_attribute_config_payload(link)
        for link in getattr(function_config, "function_config_attribute_configs", ())
    ]
    return payload


def _compact_function_config_attribute_config_payload(
    link: object,
) -> dict[str, object]:
    payload = _compact_fields(
        link,
        (
            "id",
            "name",
            "position",
            "type",
            "is_identity_key",
            "identity_key_origin",
            "function_config_id",
            "attribute_config_id",
        ),
    )
    payload["attribute_config"] = _compact_attribute_config_payload(
        getattr(link, "attribute_config")
    )
    return payload


def _compact_attribute_config_payload(attribute_config: object) -> dict[str, object]:
    payload = _compact_fields(
        attribute_config,
        (
            "id",
            "owner_key",
            "name",
            "description",
            "default_value",
            "is_primary",
            "is_public",
            "is_required",
            "is_unique",
            "is_virtual",
            "exclude_serialization",
            "type_descriptor_id",
            "code_section_attribute_id",
        ),
    )
    payload["type_descriptor"] = _compact_attribute_type_descriptor_payload(
        getattr(attribute_config, "type_descriptor"),
        seen_descriptor_ids=set(),
    )
    return payload


def _compact_attribute_type_descriptor_payload(
    descriptor: object,
    *,
    seen_descriptor_ids: set[object],
) -> dict[str, object]:
    payload = _compact_fields(
        descriptor,
        (
            "id",
            "collection_kind",
            "kind",
            "class_config_id",
            "enum_config_id",
            "primitive_config_id",
        ),
    )
    descriptor_id = getattr(descriptor, "id", None)
    descriptor_key = descriptor_id if descriptor_id is not None else id(descriptor)
    if descriptor_key in seen_descriptor_ids:
        payload["child_links"] = []
        return payload
    child_seen_descriptor_ids = {*seen_descriptor_ids, descriptor_key}
    enum_config = getattr(descriptor, "enum_config", None)
    if enum_config is not None:
        payload["enum_config"] = _compact_enum_config_payload(enum_config)
    primitive_config = getattr(descriptor, "primitive_config", None)
    if primitive_config is not None:
        payload["primitive_config"] = _compact_primitive_config_payload(
            primitive_config
        )
    payload["child_links"] = [
        _compact_attribute_type_descriptor_link_payload(
            link,
            seen_descriptor_ids=child_seen_descriptor_ids,
        )
        for link in getattr(descriptor, "child_links", ())
    ]
    return payload


def _compact_attribute_type_descriptor_link_payload(
    link: object,
    *,
    seen_descriptor_ids: set[object],
) -> dict[str, object]:
    payload = _compact_fields(
        link,
        (
            "id",
            "role",
            "position",
            "attribute_type_descriptor_id",
            "child_id",
        ),
    )
    payload["child"] = _compact_attribute_type_descriptor_payload(
        getattr(link, "child"),
        seen_descriptor_ids=seen_descriptor_ids,
    )
    return payload


def _compact_primitive_config_payload(primitive_config: object) -> dict[str, object]:
    payload = _compact_fields(
        primitive_config,
        (
            "id",
            "primitive_type_id",
        ),
    )
    primitive_type = getattr(primitive_config, "primitive_type", None)
    if primitive_type is not None:
        payload["primitive_type"] = _compact_code_primitive_type_payload(primitive_type)
    return payload


def _compact_code_primitive_type_payload(primitive_type: object) -> dict[str, object]:
    return _compact_fields(
        primitive_type,
        (
            "id",
            "signature",
            "base_type",
            "constraints",
            "item_type_id",
            "key_type_id",
            "value_type_id",
        ),
    )


def _compact_enum_config_payload(enum_config: object) -> dict[str, object]:
    payload = _compact_fields(
        enum_config,
        (
            "id",
            "enum_fqn",
            "name",
            "description",
            "object_config_graph_node_id",
            "code_section_enum_id",
        ),
    )
    payload["enum_options"] = [
        _compact_fields(
            option,
            (
                "id",
                "value",
                "label",
                "description",
                "position",
                "enum_config_id",
            ),
        )
        for option in getattr(enum_config, "enum_options", ())
    ]
    return payload


def _compact_object_config_graph_annotation_payload(
    annotation: object,
) -> dict[str, object]:
    payload = _compact_fields(
        annotation,
        (
            "id",
            "kind",
            "object_config_graph_id",
            "code_section_annotation_discriminate_id",
            "code_section_annotation_load_id",
            "code_section_annotation_overlay_id",
            "code_section_annotation_override_id",
            "code_section_annotation_oneof_id",
            "code_section_annotation_identity_id",
            "code_section_annotation_reference_id",
            "code_section_annotation_index_id",
        ),
    )
    for field_name in (
        "code_section_annotation_discriminate",
        "code_section_annotation_load",
        "code_section_annotation_overlay",
        "code_section_annotation_override",
        "code_section_annotation_oneof",
        "code_section_annotation_identity",
        "code_section_annotation_reference",
        "code_section_annotation_index",
    ):
        value = getattr(annotation, field_name, None)
        if value is not None:
            payload[field_name] = _compact_annotation_view_payload(value)
    return payload


def _compact_annotation_view_payload(value: object) -> dict[str, object]:
    if not isinstance(value, BaseModel):
        raise TypeError(f"Expected annotation view model, got {type(value)!r}")
    payload = _compact_fields(value, tuple(value.model_fields.keys()))
    payload.pop("code_section_annotation", None)
    return payload


def _compact_object_config_graph_binding_payload(binding: object) -> dict[str, object]:
    payload = _compact_fields(
        binding,
        (
            "id",
            "object_config_graph_id",
            "target_object_config_graph_id",
        ),
    )
    payload["object_config_graph_binding_classes"] = [
        _compact_fields(
            binding_class,
            (
                "id",
                "name",
                "description",
                "object_config_graph_binding_id",
                "source_class_id",
                "source_attr_id",
                "target_class_id",
                "target_attribute_id",
            ),
        )
        for binding_class in getattr(binding, "object_config_graph_binding_classes", ())
    ]
    return payload


def _compact_object_config_graph_relationship_payload(
    relationship: object,
) -> dict[str, object]:
    payload = _compact_fields(
        relationship,
        (
            "id",
            "object_config_graph_id",
            "target_object_config_graph_id",
        ),
    )
    payload["object_config_graph_relationship_classes"] = [
        _compact_fields(
            relationship_class,
            (
                "id",
                "object_config_graph_relationship_id",
                "class_config_id",
            ),
        )
        for relationship_class in getattr(
            relationship,
            "object_config_graph_relationship_classes",
            (),
        )
    ]
    payload["class_config_relationships"] = [
        _compact_class_config_relationship_payload(class_config_relationship)
        for class_config_relationship in getattr(
            relationship,
            "class_config_relationships",
            (),
        )
    ]
    return payload


def _compact_object_projection_graph_declaration_payload(
    declaration: object,
) -> dict[str, object]:
    payload = _compact_fields(
        declaration,
        (
            "id",
            "key",
            "projection_name",
            "label",
            "description",
            "is_branchable",
            "object_config_graph_id",
        ),
    )
    payload["object_projection_graph_bindings"] = [
        _compact_fields(
            binding,
            (
                "id",
                "fqn_prefix",
                "namespace",
                "class_name",
                "attribute_name",
                "target_projection_name",
                "side",
                "object_projection_graph_declaration_id",
            ),
        )
        for binding in getattr(declaration, "object_projection_graph_bindings", ())
    ]
    return payload


def _compact_object_projection_graph_payload(opg: object) -> dict[str, object]:
    payload = _compact_fields(
        opg,
        (
            "id",
            "name",
            "description",
            "language",
            "projection_hash",
            "supports_virtual_build",
            "object_config_graph_id",
        ),
    )
    payload["object_projection_graph_nodes"] = [
        _compact_object_projection_graph_node_payload(node)
        for node in getattr(opg, "object_projection_graph_nodes", ())
    ]
    payload["object_projection_graph_edges"] = [
        _compact_object_projection_graph_edge_payload(edge)
        for edge in getattr(opg, "object_projection_graph_edges", ())
    ]
    payload["object_projection_graph_constructors"] = [
        _compact_object_projection_graph_constructor_payload(constructor)
        for constructor in getattr(opg, "object_projection_graph_constructors", ())
    ]
    payload["object_projection_graph_relationships"] = [
        _compact_object_projection_graph_relationship_payload(relationship)
        for relationship in getattr(opg, "object_projection_graph_relationships", ())
    ]
    return payload


def _compact_object_projection_graph_node_payload(node: object) -> dict[str, object]:
    return _compact_fields(
        node,
        (
            "id",
            "object_projection_graph_id",
            "class_config_id",
            "is_root",
            "required_for_validity",
            "selection",
            "top_n",
            "selector_condition_id",
            "policy_refs",
        ),
    )


def _compact_object_projection_graph_edge_payload(edge: object) -> dict[str, object]:
    return _compact_fields(
        edge,
        (
            "id",
            "object_projection_graph_id",
            "class_config_relationship_id",
            "include",
            "multiplicity",
            "traversal_direction",
            "depth_limit",
            "attribute_role",
            "loading_override",
        ),
    )


def _compact_object_projection_graph_constructor_payload(
    constructor: object,
) -> dict[str, object]:
    return _compact_fields(
        constructor,
        (
            "id",
            "object_projection_graph_id",
            "root_node_id",
            "function_constructor_id",
        ),
    )


def _compact_object_projection_graph_relationship_payload(
    relationship: object,
) -> dict[str, object]:
    return _compact_fields(
        relationship,
        (
            "id",
            "object_projection_graph_id",
            "target_object_projection_graph_id",
            "class_config_relationship_id",
            "source_object_projection_graph_node_id",
            "target_object_projection_graph_node_id",
        ),
    )


def _compact_fields(value: object, field_names: tuple[str, ...]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in field_names:
        try:
            field_value = getattr(value, field_name)
        except AttributeError:
            continue
        if field_value is None:
            continue
        payload[field_name] = _json_scalar(field_value)
    return payload


def _json_scalar(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, Enum):
        return _json_scalar(value.value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return [_json_scalar(item) for item in value]
    if isinstance(value, list):
        return [_json_scalar(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_scalar(item) for key, item in value.items()}
    if isinstance(value, BaseModel):
        raise TypeError(
            "Compact ObjectConfigGraph transfer encountered an unhandled model field: "
            f"{type(value)!r}"
        )
    return value


def _optional_json_object(value: object | None) -> JsonObject | None:
    if value is None:
        return None
    return _json_object(value)


def _json_object(value: object) -> JsonObject:
    if isinstance(value, JsonObject):
        return value
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object payload, got {type(value)!r}")
    return JsonObject(cast(dict[str, Any], value))


def _model_payload(value: object) -> dict[str, object]:
    if isinstance(value, BaseModel):
        return cast(dict[str, object], value.model_dump(mode="json"))
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: _json_safe(getattr(value, key))
            for key in cast(Any, value).__dataclass_fields__
        }
    raise TypeError(f"Unsupported Meta service payload type: {type(value)!r}")


def _json_optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    raise ValueError(f"Expected UUID-compatible value, got {value!r}")


def _json_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _json_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"Expected int-compatible value, got {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    raise ValueError(f"Expected int-compatible value, got {value!r}")


def _source_language_text(value: object) -> str | None:
    if value is None:
        return None
    raw_value = getattr(value, "value", value)
    return str(raw_value)


def _json_safe(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


__all__ = [
    "AwareMetaServiceProtocolHandler",
    "MetaCommitEventBus",
    "MetaCommitEventStore",
    "MetaObjectConfigGraphPackageCompilerBackend",
    "MetaRuntimeReadModelProviderBackend",
    "build_aware_meta_service_protocol_handler",
]
