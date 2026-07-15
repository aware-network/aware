from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from aware_api_runtime.invocation import ApiInvocationIR
from aware_api_runtime.invocation import ResolvedApiInvocationEnvelope
from aware_api_runtime.request_hash import compute_api_request_hash_from_mapping
from aware_api_runtime.service_protocol.runtime import (
    ApiServiceDispatchPlan,
    ApiServiceProtocolExecution,
    ApiServiceProtocolEndpointBinding,
    LoadedApiServiceProtocolPackage,
)
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_service_runtime import implementation_package


class _ProofReadModelRequest(BaseModel):
    value: str


async def _proof_invoke(
    _handler: object,
    _request: BaseModel,
    _execution: ApiServiceProtocolExecution | None = None,
) -> object | None:
    return {"ok": True}


def _proof_deferred_plan(
    *,
    request_payload: dict[str, object],
    request_class_config_id: UUID,
    projection_hash: str,
    endpoint_binding: ApiServiceProtocolEndpointBinding,
) -> ApiServiceDispatchPlan:
    request_object = _ProofReadModelRequest.model_validate(request_payload)
    call_key = uuid4()
    api_capability_endpoint_id = uuid4()
    api_call_id = stable_api_call_id(
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=call_key,
    )
    request_model_id = stable_inline_value_instance_id(
        class_config_id=request_class_config_id,
        owner_key=call_key,
    )
    envelope = ResolvedApiInvocationEnvelope(
        api_call_id=api_call_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=call_key,
        request_hash=compute_api_request_hash_from_mapping(
            payload=request_payload,
        ),
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash=projection_hash,
        api_name="workspace",
        capability_name="materialize",
        endpoint_name="materialize",
        endpoint_ref="workspace.materialize.materialize",
        discriminant="workspace.materialize.materialize",
        source_path="workspace.services.aware",
        request_model_id=request_model_id,
        request_class_config_id=request_class_config_id,
        request_class_ref="aware_workspace_service_dto.WorkspaceMaterializeRequest",
        request_source_path="workspace/service_operation.aware",
        response_class_ref=(
            "aware_workspace_service_dto.WorkspaceMaterializeResponse"
        ),
        response_source_path="workspace/service_operation.aware",
        stream=None,
        fulfillment_bindings=(),
        description="Materialize Workspace deltas.",
        deferred_api_call=True,
    )
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root="aware_workspace_service_api",
        service_protocol_import_root="aware_workspace_service_protocol",
        endpoint_ref=envelope.endpoint_ref,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        request_type_ref=endpoint_binding.request_type_ref,
        response_type_ref=endpoint_binding.response_type_ref,
        stream_event_type_refs=endpoint_binding.stream_event_type_refs,
        execution_protocol_ref=endpoint_binding.execution_protocol_ref,
        build_execution=endpoint_binding.build_execution,
        stream_invoke=endpoint_binding.stream_invoke,
        fulfillment_bindings=(),
        request_object=request_object,
        invoke=endpoint_binding.invoke,
    )


def _proof_invocation_ir(
    *,
    request_payload: dict[str, object],
    request_class_config_id: UUID,
) -> ApiInvocationIR:
    return ApiInvocationIR(
        api_name="workspace",
        capability_name="delta_preview",
        endpoint_name="preview",
        endpoint_ref="workspace.delta_preview.preview",
        discriminant="workspace.delta_preview.preview",
        source_path="workspace.services.aware",
        request_payload=request_payload,
        request_class_ref="aware_workspace_service_dto.WorkspaceDeltaPreviewRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="workspace/service_operation.aware",
        response_class_ref=(
            "aware_workspace_service_dto.WorkspaceDeltaPreviewResponse"
        ),
        response_source_path="workspace/service_operation.aware",
        stream=None,
        fulfillment_bindings=(),
        description="Preview Workspace source deltas.",
    )


@pytest.mark.asyncio
async def test_read_model_dispatch_plan_cache_reuses_static_template_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package._clear_service_api_read_model_dispatch_plan_cache()
    request_class_config_id = uuid4()
    endpoint_binding = ApiServiceProtocolEndpointBinding(
        endpoint_ref="workspace.delta_preview.preview",
        request_type_ref=("aware_workspace_service_dto.WorkspaceDeltaPreviewRequest"),
        response_type_ref=("aware_workspace_service_dto.WorkspaceDeltaPreviewResponse"),
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=_proof_invoke,
    )
    loaded_package = LoadedApiServiceProtocolPackage(
        runtime_package_dir=tmp_path,
        public_package_root=tmp_path / "public",
        service_protocol_package_root=tmp_path / "protocol",
        public_package_import_root="aware_workspace_service_api",
        service_protocol_import_root="aware_workspace_service_protocol",
        endpoint_bindings={"workspace.delta_preview.preview": endpoint_binding},
        runtime_fulfillment_bindings={},
    )
    dependency = SimpleNamespace(
        runtime_package_dir=tmp_path,
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )
    counts = {
        "manifest": 0,
        "ir": 0,
        "protocol_package": 0,
        "request_model": 0,
    }

    def _fake_manifest(**_: object) -> object:
        counts["manifest"] += 1
        return object()

    def _fake_ir(**kwargs: object) -> ApiInvocationIR:
        counts["ir"] += 1
        return _proof_invocation_ir(
            request_payload=dict(cast(dict[str, object], kwargs["request_payload"])),
            request_class_config_id=request_class_config_id,
        )

    def _fake_loaded_package(**_: object) -> LoadedApiServiceProtocolPackage:
        counts["protocol_package"] += 1
        return loaded_package

    def _fake_request_model(**_: object) -> type[BaseModel]:
        counts["request_model"] += 1
        return _ProofReadModelRequest

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        _fake_manifest,
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        _fake_ir,
    )
    monkeypatch.setattr(
        implementation_package,
        "load_api_service_protocol_package",
        _fake_loaded_package,
    )
    monkeypatch.setattr(
        implementation_package,
        "_resolve_generated_request_model_class",
        _fake_request_model,
    )

    activated = cast(
        Any,
        SimpleNamespace(
            prepared=object(),
            api_reference_branch_ids_by_api_name={},
        ),
    )
    index = cast(Any, SimpleNamespace(class_configs_by_id={}))
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )

    first = await implementation_package.build_activated_service_api_read_model_dispatch_plan_from_ingress(
        activated=activated,
        index=index,
        api_call_lane=api_call_lane,
        service_name="aware_workspace",
        endpoint_ref="workspace.delta_preview.preview",
        discriminant="workspace.delta_preview.preview",
        request_payload={"value": "first"},
    )
    second = await implementation_package.build_activated_service_api_read_model_dispatch_plan_from_ingress(
        activated=activated,
        index=index,
        api_call_lane=api_call_lane,
        service_name="aware_workspace",
        endpoint_ref="workspace.delta_preview.preview",
        discriminant="workspace.delta_preview.preview",
        request_payload={"value": "second"},
    )

    assert counts == {
        "manifest": 1,
        "ir": 1,
        "protocol_package": 1,
        "request_model": 1,
    }
    assert first.request_object == _ProofReadModelRequest(value="first")
    assert second.request_object == _ProofReadModelRequest(value="second")
    assert first.envelope.api_call_id != second.envelope.api_call_id
    assert first.envelope.request_hash != second.envelope.request_hash
    assert first.envelope.request_hash.endswith("first") is False
    assert first.endpoint_ref == "workspace.delta_preview.preview"
    assert second.endpoint_ref == "workspace.delta_preview.preview"

    implementation_package._clear_service_api_read_model_dispatch_plan_cache()


@pytest.mark.asyncio
async def test_deferred_dispatch_plan_cache_reuses_static_template_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package._clear_service_api_deferred_dispatch_plan_cache()
    request_class_config_id = uuid4()
    endpoint_binding = ApiServiceProtocolEndpointBinding(
        endpoint_ref="workspace.materialize.materialize",
        request_type_ref=("aware_workspace_service_dto.WorkspaceMaterializeRequest"),
        response_type_ref=("aware_workspace_service_dto.WorkspaceMaterializeResponse"),
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=_proof_invoke,
    )
    dependency = SimpleNamespace(
        runtime_package_dir=tmp_path,
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )
    counts = {
        "manifest": 0,
        "ir": 0,
        "deferred_plan": 0,
    }

    def _fake_manifest(**_: object) -> object:
        counts["manifest"] += 1
        return object()

    def _fake_ir(**kwargs: object) -> ApiInvocationIR:
        counts["ir"] += 1
        return ApiInvocationIR(
            api_name="workspace",
            capability_name="materialize",
            endpoint_name="materialize",
            endpoint_ref="workspace.materialize.materialize",
            discriminant="workspace.materialize.materialize",
            source_path="workspace.services.aware",
            request_payload=dict(
                cast(dict[str, object], kwargs["request_payload"])
            ),
            request_class_ref=(
                "aware_workspace_service_dto.WorkspaceMaterializeRequest"
            ),
            request_class_config_id=request_class_config_id,
            request_source_path="workspace/service_operation.aware",
            response_class_ref=(
                "aware_workspace_service_dto.WorkspaceMaterializeResponse"
            ),
            response_source_path="workspace/service_operation.aware",
            stream=None,
            fulfillment_bindings=(),
            description="Materialize Workspace deltas.",
        )

    def _fake_deferred_plan(**kwargs: object) -> ApiServiceDispatchPlan:
        counts["deferred_plan"] += 1
        ir = cast(ApiInvocationIR, kwargs["ir"])
        return _proof_deferred_plan(
            request_payload=dict(ir.request_payload),
            request_class_config_id=request_class_config_id,
            projection_hash=cast(str, kwargs["projection_hash"]),
            endpoint_binding=endpoint_binding,
        )

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        _fake_manifest,
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        _fake_ir,
    )
    monkeypatch.setattr(
        implementation_package,
        "build_api_service_dispatch_plan_from_invocation_ir",
        _fake_deferred_plan,
    )
    monkeypatch.setattr(
        implementation_package,
        "should_use_compact_api_receipt_payload",
        lambda **_: True,
    )

    activated = cast(
        Any,
        SimpleNamespace(
            prepared=object(),
            api_reference_branch_ids_by_api_name={},
        ),
    )
    index = cast(Any, SimpleNamespace(class_configs_by_id={}))
    api_source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-source",
    )
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )

    first = await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
        activated=activated,
        runtime=cast(Any, object()),
        index=index,
        actor_id=None,
        api_source_lane=api_source_lane,
        api_call_lane=api_call_lane,
        service_name="aware_workspace",
        endpoint_ref="workspace.materialize.materialize",
        discriminant="workspace.materialize.materialize",
        request_payload={"value": "first"},
    )
    second = await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
        activated=activated,
        runtime=cast(Any, object()),
        index=index,
        actor_id=None,
        api_source_lane=api_source_lane,
        api_call_lane=api_call_lane,
        service_name="aware_workspace",
        endpoint_ref="workspace.materialize.materialize",
        discriminant="workspace.materialize.materialize",
        request_payload={"value": "second"},
    )

    assert counts == {
        "manifest": 1,
        "ir": 1,
        "deferred_plan": 1,
    }
    assert first.request_object == _ProofReadModelRequest(value="first")
    assert second.request_object == _ProofReadModelRequest(value="second")
    assert first.envelope.api_call_id != second.envelope.api_call_id
    assert first.envelope.call_key != second.envelope.call_key
    assert first.envelope.request_model_id != second.envelope.request_model_id
    assert first.envelope.request_hash != second.envelope.request_hash
    assert first.envelope.deferred_api_call is True
    assert second.envelope.deferred_api_call is True

    implementation_package._clear_service_api_deferred_dispatch_plan_cache()


@pytest.mark.asyncio
async def test_deferred_dispatch_plan_cache_hit_still_guards_payload_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package._clear_service_api_deferred_dispatch_plan_cache()
    request_class_config_id = uuid4()
    endpoint_binding = ApiServiceProtocolEndpointBinding(
        endpoint_ref="workspace.materialize.materialize",
        request_type_ref=("aware_workspace_service_dto.WorkspaceMaterializeRequest"),
        response_type_ref=("aware_workspace_service_dto.WorkspaceMaterializeResponse"),
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=_proof_invoke,
    )
    dependency = SimpleNamespace(
        runtime_package_dir=tmp_path,
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )
    counts = {"deferred_plan": 0}

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        lambda **kwargs: _proof_invocation_ir(
            request_payload=dict(
                cast(dict[str, object], kwargs["request_payload"])
            ),
            request_class_config_id=request_class_config_id,
        ),
    )

    def _fake_deferred_plan(**kwargs: object) -> ApiServiceDispatchPlan:
        counts["deferred_plan"] += 1
        ir = cast(ApiInvocationIR, kwargs["ir"])
        return _proof_deferred_plan(
            request_payload=dict(ir.request_payload),
            request_class_config_id=request_class_config_id,
            projection_hash=cast(str, kwargs["projection_hash"]),
            endpoint_binding=endpoint_binding,
        )

    monkeypatch.setattr(
        implementation_package,
        "build_api_service_dispatch_plan_from_invocation_ir",
        _fake_deferred_plan,
    )
    monkeypatch.setattr(
        implementation_package,
        "should_use_compact_api_receipt_payload",
        lambda **_: True,
    )

    activated = cast(
        Any,
        SimpleNamespace(
            prepared=object(),
            api_reference_branch_ids_by_api_name={},
        ),
    )
    index = cast(Any, SimpleNamespace(class_configs_by_id={}))
    api_source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-source",
    )
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )

    await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
        activated=activated,
        runtime=cast(Any, object()),
        index=index,
        actor_id=None,
        api_source_lane=api_source_lane,
        api_call_lane=api_call_lane,
        service_name="aware_workspace",
        endpoint_ref="workspace.materialize.materialize",
        discriminant="workspace.materialize.materialize",
        request_payload={"value": "first"},
    )
    with pytest.raises(RuntimeError, match="dropped_fields"):
        await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
            activated=activated,
            runtime=cast(Any, object()),
            index=index,
            actor_id=None,
            api_source_lane=api_source_lane,
            api_call_lane=api_call_lane,
            service_name="aware_workspace",
            endpoint_ref="workspace.materialize.materialize",
            discriminant="workspace.materialize.materialize",
            request_payload={"value": "second", "unexpected": "blocked"},
        )

    assert counts == {"deferred_plan": 1}

    implementation_package._clear_service_api_deferred_dispatch_plan_cache()
