from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageDependencyRef,
    MetaObjectConfigGraphPackageEnsureRequest,
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeRequest,
    MetaCompletenessAnalyzeResponse,
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
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_service_dto.persistence.database_readiness import (
    MetaDatabaseArtifactReceipt,
    MetaPersistenceEnsureDatabaseReadyRequest,
    MetaPersistenceEnsureDatabaseReadyResponse,
)
from aware_meta_service_dto.runtime.read_model import (
    MetaRuntimeReadModelRequest,
    MetaRuntimeReadModelResponse,
)
from aware_types import JsonArray, JsonObject, JsonValue

MetaGraphCallTarget = Literal["instance", "opg_constructor"]


class MetaSdkError(RuntimeError):
    pass


class _MetaGraphCapabilityClient(Protocol):
    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse: ...

    async def invoke_temporal_function(
        self,
        request: MetaGraphInvokeTemporalFunctionRequest,
    ) -> MetaGraphInvokeTemporalFunctionResponse: ...

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse: ...


class _MetaPackageCapabilityClient(Protocol):
    async def ensure_object_config_graph_package(
        self,
        request: MetaObjectConfigGraphPackageEnsureRequest,
    ) -> MetaObjectConfigGraphPackageEnsureResponse: ...


class _MetaDiagnosticsCapabilityClient(Protocol):
    async def analyze_object_config_graph_completeness(
        self,
        request: MetaCompletenessAnalyzeRequest,
    ) -> MetaCompletenessAnalyzeResponse: ...


class _MetaPersistenceCapabilityClient(Protocol):
    async def ensure_database_ready(
        self,
        request: MetaPersistenceEnsureDatabaseReadyRequest,
    ) -> MetaPersistenceEnsureDatabaseReadyResponse: ...


class _MetaRuntimeReadModelCapabilityClient(Protocol):
    async def describe_workspace(
        self,
        request: MetaRuntimeReadModelRequest,
    ) -> MetaRuntimeReadModelResponse: ...


class _MetaApiNamespaceClient(Protocol):
    @property
    def diagnostics(self) -> _MetaDiagnosticsCapabilityClient: ...

    @property
    def graph(self) -> _MetaGraphCapabilityClient: ...

    @property
    def package(self) -> _MetaPackageCapabilityClient: ...

    @property
    def persistence(self) -> _MetaPersistenceCapabilityClient: ...

    @property
    def runtime_read_model(self) -> _MetaRuntimeReadModelCapabilityClient: ...


class MetaGeneratedApiClient(Protocol):
    @property
    def meta(self) -> _MetaApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class MetaSdkClient:
    api_client: MetaGeneratedApiClient

    async def analyze_object_config_graph_completeness(
        self,
        *,
        package_root: str,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        aware_toml_path: str | None = None,
        source_files: Sequence[str] = (),
        dependency_refs: Sequence[MetaObjectConfigGraphPackageDependencyRef] = (),
        completeness_diagnostics: bool = True,
        diagnostic_severity: str = "warning",
        include_object_config_graph: bool = False,
    ) -> MetaCompletenessAnalyzeResponse:
        response = await self.api_client.meta.diagnostics.analyze_object_config_graph_completeness(
            MetaCompletenessAnalyzeRequest(
                actor_id=actor_id,
                workspace_root=workspace_root,
                package_root=package_root,
                aware_toml_path=aware_toml_path,
                source_files=list(source_files),
                dependency_refs=list(dependency_refs),
                completeness_diagnostics=completeness_diagnostics,
                diagnostic_severity=diagnostic_severity,
                include_object_config_graph=include_object_config_graph,
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="analyze_object_config_graph_completeness",
        )
        return response

    async def ensure_object_config_graph_package(
        self,
        *,
        aware_toml_path: str,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        parent_branch_id: UUID | None = None,
        package_branch_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        object_config_graph_package_id: UUID | None = None,
        dependency_refs: Sequence[MetaObjectConfigGraphPackageDependencyRef] = (),
        include_object_config_graph: bool = False,
        collect_telemetry: bool = True,
    ) -> MetaObjectConfigGraphPackageEnsureResponse:
        response = (
            await self.api_client.meta.package.ensure_object_config_graph_package(
                MetaObjectConfigGraphPackageEnsureRequest(
                    actor_id=actor_id,
                    workspace_root=workspace_root,
                    aware_toml_path=aware_toml_path,
                    parent_branch_id=parent_branch_id,
                    package_branch_id=package_branch_id,
                    source_code_package_id=source_code_package_id,
                    object_config_graph_package_id=object_config_graph_package_id,
                    dependency_refs=list(dependency_refs),
                    include_object_config_graph=include_object_config_graph,
                    collect_telemetry=collect_telemetry,
                )
            )
        )
        _raise_if_failed(response.status, response.error, operation="ensure_package")
        return response

    async def ensure_database_ready(
        self,
        *,
        database_artifact_receipt: MetaDatabaseArtifactReceipt,
        actor_id: UUID | None = None,
        database_url_ref: str | None = None,
        boot_policy: str = "migrate",
    ) -> MetaPersistenceEnsureDatabaseReadyResponse:
        response = await self.api_client.meta.persistence.ensure_database_ready(
            MetaPersistenceEnsureDatabaseReadyRequest(
                actor_id=actor_id,
                database_artifact_receipt=database_artifact_receipt,
                database_url_ref=database_url_ref,
                boot_policy=boot_policy,
            )
        )
        _raise_if_failed(
            response.status, response.error, operation="ensure_database_ready"
        )
        return response

    async def describe_workspace(
        self,
        *,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        repo_root: str | None = None,
        aware_root: str | None = None,
        required_projection_names: Sequence[str] = (),
        force_refresh: bool = False,
        include_timings: bool = True,
        include_package_timings: bool = True,
        include_workspace_commit_truth: bool = False,
    ) -> MetaRuntimeReadModelResponse:
        response = await self.api_client.meta.runtime_read_model.describe_workspace(
            MetaRuntimeReadModelRequest(
                actor_id=actor_id,
                workspace_root=workspace_root,
                repo_root=repo_root,
                aware_root=aware_root,
                required_projection_names=list(required_projection_names),
                force_refresh=force_refresh,
                include_timings=include_timings,
                include_package_timings=include_package_timings,
                include_workspace_commit_truth=include_workspace_commit_truth,
            )
        )
        _raise_if_failed(
            response.status, response.error, operation="describe_workspace"
        )
        return response

    async def get_lane_head(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        actor_id: UUID | None = None,
    ) -> MetaGraphGetLaneHeadResponse:
        response = await self.api_client.meta.graph.get_lane_head(
            MetaGraphGetLaneHeadRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
            )
        )
        _raise_if_failed(response.status, response.error, operation="get_lane_head")
        return response

    async def get_object_instance_graph_commit(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        actor_id: UUID | None = None,
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse:
        response = await self.api_client.meta.graph.get_object_instance_graph_commit(
            MetaGraphGetObjectInstanceGraphCommitRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                domain_commit_id=domain_commit_id,
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="get_object_instance_graph_commit",
        )
        return response

    async def resolve_projection(
        self,
        *,
        actor_id: UUID | None = None,
        projection_name: str | None = None,
        projection_hash: str | None = None,
        object_projection_graph_id: UUID | None = None,
        include_available: bool = False,
    ) -> MetaGraphResolveProjectionResponse:
        response = await self.api_client.meta.graph.resolve_projection(
            MetaGraphResolveProjectionRequest(
                actor_id=actor_id,
                projection_name=projection_name,
                projection_hash=projection_hash,
                object_projection_graph_id=object_projection_graph_id,
                include_available=include_available,
            )
        )
        _raise_if_failed(
            response.status, response.error, operation="resolve_projection"
        )
        return response

    async def invoke_function(
        self,
        *,
        actor_id: UUID,
        function_id: UUID,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        call_target: MetaGraphCallTarget | MetaGraphFunctionCallTarget = "instance",
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: Sequence[JsonValue] = (),
        kwargs: Mapping[str, JsonValue] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> MetaGraphInvokeFunctionResponse:
        response = await self.api_client.meta.graph.invoke_function(
            MetaGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                call_target=_call_target(call_target),
                target_object_id=target_object_id,
                object_projection_graph_id=object_projection_graph_id,
                function_id=function_id,
                args=JsonArray(list(args)),
                kwargs=JsonObject(dict(kwargs or {})),
                expected_graph_hash_pre=expected_graph_hash_pre,
                expected_head_commit_id=expected_head_commit_id,
                commit=commit,
                publish=publish,
            )
        )
        _raise_if_failed(response.status, response.error, operation="invoke_function")
        return response

    async def invoke_temporal_function(
        self,
        *,
        actor_id: UUID,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        before_oig: Mapping[str, JsonValue],
        function_id: UUID,
        call_target: MetaGraphCallTarget | MetaGraphFunctionCallTarget = "instance",
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: Sequence[JsonValue] = (),
        kwargs: Mapping[str, JsonValue] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
    ) -> MetaGraphInvokeTemporalFunctionResponse:
        response = await self.api_client.meta.graph.invoke_temporal_function(
            MetaGraphInvokeTemporalFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                call_target=_call_target(call_target),
                target_object_id=target_object_id,
                object_projection_graph_id=object_projection_graph_id,
                function_id=function_id,
                before_oig=JsonObject(dict(before_oig)),
                args=JsonArray(list(args)),
                kwargs=JsonObject(dict(kwargs or {})),
                expected_graph_hash_pre=expected_graph_hash_pre,
                expected_head_commit_id=expected_head_commit_id,
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="invoke_temporal_function",
        )
        return response


def _call_target(
    value: MetaGraphCallTarget | MetaGraphFunctionCallTarget,
) -> MetaGraphFunctionCallTarget:
    if isinstance(value, MetaGraphFunctionCallTarget):
        return value
    try:
        return MetaGraphFunctionCallTarget(value)
    except ValueError as exc:
        raise MetaSdkError(f"Unsupported Meta call target: {value!r}") from exc


def _raise_if_failed(
    status: str,
    error: str | None,
    *,
    operation: str,
) -> None:
    if status.strip().lower() in {
        "ok",
        "ready",
        "resolved",
        "succeeded",
        "available",
        "empty",
        "missing",
    }:
        return
    raise MetaSdkError(
        f"Meta SDK operation failed: operation={operation!r} "
        f"status={status!r} error={error!r}"
    )
