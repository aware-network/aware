from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from aware_meta_sdk import AwareMetaSdk, MetaSdkClient, MetaSdkError
from aware_meta_sdk import client as meta_sdk_client
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeResponse,
    MetaCompletenessDiagnostic,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadResponse,
    MetaGraphInvokeFunctionResponse,
    MetaGraphInvokeTemporalFunctionResponse,
    MetaGraphResolveProjectionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_service_dto.runtime.read_model import MetaRuntimeReadModelResponse


@pytest.mark.asyncio
async def test_meta_sdk_routes_graph_and_package_calls_through_generated_api() -> None:
    api = _FakeGeneratedMetaApi()
    sdk = MetaSdkClient(api_client=api)
    actor_id = uuid4()
    branch_id = uuid4()
    function_id = uuid4()
    opg_id = uuid4()

    ensure_response = await sdk.ensure_object_config_graph_package(
        actor_id=actor_id,
        workspace_root="/repo",
        aware_toml_path="workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        include_object_config_graph=True,
    )
    assert ensure_response.status == "succeeded"
    assert api.meta.package.requests[0].aware_toml_path.endswith("aware.toml")
    assert api.meta.package.requests[0].include_object_config_graph is True

    diagnostics_response = await sdk.analyze_object_config_graph_completeness(
        actor_id=actor_id,
        workspace_root="/repo",
        package_root="workspaces/aware_kernel/modules/storage/ontology/structure",
        source_files=("aware/storage/blob.aware",),
    )
    assert diagnostics_response.status == "succeeded"
    assert diagnostics_response.diagnostics[0].code == (
        "aware_meta.completeness.class_missing_constructor"
    )
    assert api.meta.diagnostics.requests[0].source_files == ["aware/storage/blob.aware"]

    projection = await sdk.resolve_projection(
        actor_id=actor_id,
        projection_name="StorageBlob",
    )
    assert projection.projection_hash == "projection:storage_blob"

    response = await sdk.invoke_function(
        actor_id=actor_id,
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection.projection_hash,
        call_target="opg_constructor",
        object_projection_graph_id=opg_id,
        args=("sha",),
        kwargs={"mime_type": "application/octet-stream"},
        commit=True,
        publish=False,
    )

    invoke_request = api.meta.graph.invoke_requests[0]
    assert response.status == "succeeded"
    assert invoke_request.call_target == MetaGraphFunctionCallTarget.opg_constructor
    assert invoke_request.args == ["sha"]
    assert invoke_request.kwargs["mime_type"] == "application/octet-stream"
    assert invoke_request.object_projection_graph_id == opg_id

    temporal_response = await sdk.invoke_temporal_function(
        actor_id=actor_id,
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection.projection_hash or "",
        before_oig={"hash": "hash:pre"},
        target_object_id=uuid4(),
        args=("delta",),
        kwargs={"field": "title"},
        expected_graph_hash_pre="hash:pre",
    )

    temporal_request = api.meta.graph.temporal_requests[0]
    assert temporal_response.status == "succeeded"
    assert temporal_request.before_oig == {"hash": "hash:pre"}
    assert temporal_request.args == ["delta"]
    assert temporal_request.kwargs["field"] == "title"
    assert temporal_request.expected_graph_hash_pre == "hash:pre"

    lane_head = await sdk.get_lane_head(
        actor_id=actor_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection.projection_hash or "",
    )
    assert lane_head.root_object_id == response.root_object_id

    read_model = await sdk.describe_workspace(
        actor_id=actor_id,
        workspace_root="/repo",
        required_projection_names=("StorageBlob",),
    )
    assert read_model.required_projection_names == ["StorageBlob"]


@pytest.mark.asyncio
async def test_meta_sdk_raises_on_rejected_generated_response() -> None:
    api = _FakeGeneratedMetaApi()
    api.meta.graph.invoke_status = "failed"
    sdk = AwareMetaSdk(api_client=api)

    with pytest.raises(MetaSdkError, match="invoke_function"):
        await sdk.invoke_function(actor_id=uuid4(), function_id=uuid4())


def test_meta_sdk_import_boundary_stays_outside_meta_runtime() -> None:
    source = inspect.getsource(meta_sdk_client)
    forbidden_tokens = (
        "aware_meta.runtime",
        "aware_runtime",
        "services.meta",
        "MetaGraphRuntime",
        "handler_modules",
        "bootstrap_modules",
    )
    for token in forbidden_tokens:
        assert token not in source


@dataclass(slots=True)
class _FakeGraphApi:
    invoke_status: str = "succeeded"
    root_object_id: UUID = field(default_factory=uuid4)
    invoke_requests: list[object] = field(default_factory=list)
    temporal_requests: list[object] = field(default_factory=list)

    async def resolve_projection(
        self, request: object
    ) -> MetaGraphResolveProjectionResponse:
        return MetaGraphResolveProjectionResponse(
            status="resolved",
            actor_id=getattr(request, "actor_id"),
            projection_name=getattr(request, "projection_name"),
            projection_hash="projection:storage_blob",
            object_projection_graph_id=uuid4(),
        )

    async def invoke_function(self, request: object) -> MetaGraphInvokeFunctionResponse:
        self.invoke_requests.append(request)
        return MetaGraphInvokeFunctionResponse(
            status=self.invoke_status,
            actor_id=getattr(request, "actor_id"),
            root_object_id=self.root_object_id,
            domain_branch_id=getattr(request, "domain_branch_id"),
            domain_projection_hash=getattr(request, "domain_projection_hash"),
            payload={"value": {"id": str(self.root_object_id)}},
            error="boom" if self.invoke_status == "failed" else None,
        )

    async def invoke_temporal_function(
        self,
        request: object,
    ) -> MetaGraphInvokeTemporalFunctionResponse:
        self.temporal_requests.append(request)
        return MetaGraphInvokeTemporalFunctionResponse(
            status=self.invoke_status,
            actor_id=getattr(request, "actor_id"),
            root_object_id=self.root_object_id,
            domain_branch_id=getattr(request, "domain_branch_id"),
            domain_projection_hash=getattr(request, "domain_projection_hash"),
            payload={"value": "ok"},
            before_oig=getattr(request, "before_oig"),
            after_oig={"hash": "hash:post"},
            graph_hash_pre=getattr(request, "expected_graph_hash_pre"),
            graph_hash_post="hash:post",
            error="boom" if self.invoke_status == "failed" else None,
        )

    async def get_lane_head(self, request: object) -> MetaGraphGetLaneHeadResponse:
        return MetaGraphGetLaneHeadResponse(
            status="available",
            actor_id=getattr(request, "actor_id"),
            domain_branch_id=getattr(request, "domain_branch_id"),
            domain_projection_hash=getattr(request, "domain_projection_hash"),
            root_object_id=self.root_object_id,
        )

    async def get_object_instance_graph_commit(self, request: object) -> object:
        raise AssertionError("not used in this test")


@dataclass(slots=True)
class _FakePackageApi:
    requests: list[object] = field(default_factory=list)

    async def ensure_object_config_graph_package(
        self,
        request: object,
    ) -> MetaObjectConfigGraphPackageEnsureResponse:
        self.requests.append(request)
        return MetaObjectConfigGraphPackageEnsureResponse(
            status="succeeded",
            actor_id=getattr(request, "actor_id"),
            workspace_root=getattr(request, "workspace_root"),
            aware_toml_path=getattr(request, "aware_toml_path"),
            package_name="storage-ontology",
        )


@dataclass(slots=True)
class _FakeDiagnosticsApi:
    requests: list[object] = field(default_factory=list)

    async def analyze_object_config_graph_completeness(
        self,
        request: object,
    ) -> MetaCompletenessAnalyzeResponse:
        self.requests.append(request)
        return MetaCompletenessAnalyzeResponse(
            status="succeeded",
            actor_id=getattr(request, "actor_id"),
            workspace_root=getattr(request, "workspace_root"),
            package_root=getattr(request, "package_root"),
            diagnostics=[
                MetaCompletenessDiagnostic(
                    severity="warning",
                    code="aware_meta.completeness.class_missing_constructor",
                    message="constructor missing",
                    source_path="aware/storage/blob.aware",
                )
            ],
        )


@dataclass(slots=True)
class _FakeRuntimeReadModelApi:
    async def describe_workspace(self, request: object) -> MetaRuntimeReadModelResponse:
        return MetaRuntimeReadModelResponse(
            status="available",
            actor_id=getattr(request, "actor_id"),
            workspace_root=getattr(request, "workspace_root"),
            required_projection_names=list(
                getattr(request, "required_projection_names")
            ),
        )


@dataclass(slots=True)
class _FakePersistenceApi:
    pass


@dataclass(slots=True)
class _FakeMetaNamespace:
    diagnostics: _FakeDiagnosticsApi = field(default_factory=_FakeDiagnosticsApi)
    graph: _FakeGraphApi = field(default_factory=_FakeGraphApi)
    package: _FakePackageApi = field(default_factory=_FakePackageApi)
    persistence: _FakePersistenceApi = field(default_factory=_FakePersistenceApi)
    runtime_read_model: _FakeRuntimeReadModelApi = field(
        default_factory=_FakeRuntimeReadModelApi
    )


@dataclass(slots=True)
class _FakeGeneratedMetaApi:
    meta: _FakeMetaNamespace = field(default_factory=_FakeMetaNamespace)
