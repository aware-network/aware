from __future__ import annotations

# pyright: reportMissingImports=false

from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from aware_api_runtime.package_ref_resolution import ApiRuntimePackageRef
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
    require_current_service_api_materialization_context,
)
from aware_service_runtime.contracts import ServiceOperationContext
from aware_skill.execution import (
    SkillInvocationContext,
    SkillRunHarnessRequest,
    SkillRunHarnessResult,
    SkillStepApiCallInput,
    invoke_skill_package,
)
from aware_skill.package_ref_resolution import SkillRuntimePackageRef
from aware_skill_service_dto.skill.service_operation import SkillApiPackageRef
from aware_skill_service_dto.skill.service_operation import SkillInvokeRequest
from aware_skill_service_dto.skill.service_operation import SkillInvokeResponse
from aware_skill_service_dto.skill.service_operation import SkillPackageRef


def build_aware_skill_service_protocol_handler() -> object:
    return _AwareSkillServiceProtocolHandler()


@dataclass(slots=True)
class _SkillProtocolSupport:
    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Skill service protocol requires an active Service API host context."
            )
        return host_context

    async def invoke_skill(self, *, request: SkillInvokeRequest) -> SkillInvokeResponse:
        host_context = self.host_context()
        materialization = require_current_service_api_materialization_context()
        operation_context = host_context.operation_context
        result = await invoke_skill_package(
            runtime=cast(Any, materialization.runtime),
            index=cast(MetaGraphRuntimeIndex, materialization.graph_context.index),
            context=_skill_invocation_context(
                operation_context=operation_context,
                skill_run_branch_id=materialization.target_lane.branch_id,
            ),
            skill_package_ref=_skill_package_ref(request.skill_package),
            api_package_refs=tuple(
                _api_package_ref(ref) for ref in request.api_packages
            ),
            request=SkillRunHarnessRequest(
                skill_config_id=request.skill_config_id,
                run_key=request.run_key,
                step_inputs=tuple(_step_input(item) for item in request.step_inputs),
                run_status=request.run_status,
                step_status=request.step_status,
                description=request.description,
            ),
            commit=request.commit,
            publish=request.publish,
        )
        return SkillInvokeResponse.model_validate(
            {
                "operation": "invoke",
                "request_id": request.request_id,
                "success": True,
                "result": _result_payload(result),
            }
        )


class _SkillInvokeCapabilityHandler:
    def __init__(self, *, support: _SkillProtocolSupport) -> None:
        self._support = support

    async def invoke(self, request: SkillInvokeRequest) -> SkillInvokeResponse:
        return await self._support.invoke_skill(request=request)


class _SkillApiHandler:
    def __init__(self, *, support: _SkillProtocolSupport) -> None:
        self.invoke = _SkillInvokeCapabilityHandler(support=support)


class _AwareSkillServiceProtocolHandler:
    def __init__(self) -> None:
        support = _SkillProtocolSupport()
        self.skill = _SkillApiHandler(support=support)


def _skill_invocation_context(
    *,
    operation_context: ServiceOperationContext,
    skill_run_branch_id: UUID,
) -> SkillInvocationContext:
    return SkillInvocationContext(
        actor_id=operation_context.actor_id,
        skill_run_branch_id=skill_run_branch_id,
    )


def _skill_package_ref(ref: SkillPackageRef) -> SkillRuntimePackageRef:
    return SkillRuntimePackageRef(
        family_key=ref.family_key,
        package_kind=ref.package_kind,
        package_name=ref.package_name,
        semantic_package_id=_uuid_text(ref.semantic_package_id),
        semantic_object_instance_graph_commit_id=_uuid_text(
            ref.semantic_object_instance_graph_commit_id
        ),
        semantic_branch_id=_uuid_text(ref.semantic_branch_id),
        semantic_root_kind=ref.semantic_root_kind,
        semantic_root_id=_uuid_text(ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=_uuid_text(
            ref.semantic_root_object_instance_graph_commit_id
        ),
        source_code_package_id=_uuid_text(ref.source_code_package_id),
    )


def _api_package_ref(ref: SkillApiPackageRef) -> ApiRuntimePackageRef:
    return ApiRuntimePackageRef(
        family_key=ref.family_key,
        package_kind=ref.package_kind,
        package_name=ref.package_name,
        semantic_package_id=_uuid_text(ref.semantic_package_id),
        semantic_object_instance_graph_commit_id=_uuid_text(
            ref.semantic_object_instance_graph_commit_id
        ),
        semantic_branch_id=_uuid_text(ref.semantic_branch_id),
        semantic_projection_name=ref.semantic_projection_name,
        semantic_root_kind=ref.semantic_root_kind,
        semantic_root_id=_uuid_text(ref.semantic_root_id),
        source_code_package_id=_uuid_text(ref.source_code_package_id),
    )


def _step_input(item: object) -> SkillStepApiCallInput:
    return SkillStepApiCallInput(
        skill_config_step_id=cast(Any, item).skill_config_step_id,
        request_payload=dict(cast(Any, item).request_payload),
        call_key=cast(Any, item).call_key,
        description=cast(Any, item).description,
    )


def _result_payload(result: SkillRunHarnessResult) -> dict[str, object]:
    return {
        "skill_config_id": result.skill_config_id,
        "skill_run_id": result.skill_run_id,
        "run_key": result.run_key,
        "status": result.status,
        "branch_id": result.branch_id,
        "projection_hash": result.projection_hash,
        "commit_id": result.commit_id,
        "head_commit_id": result.head_commit_id,
        "steps": [
            {
                "skill_config_step_id": step.skill_config_step_id,
                "skill_run_step_id": step.skill_run_step_id,
                "api_call": {
                    "skill_config_step_id": step.api_call.skill_config_step_id,
                    "api_call_id": step.api_call.api_call_id,
                    "api_capability_endpoint_id": step.api_call.api_capability_endpoint_id,
                    "call_key": step.api_call.call_key,
                    "request_hash": step.api_call.request_hash,
                    "request_model_id": step.api_call.request_model_id,
                    "request_class_config_id": step.api_call.request_class_config_id,
                    "branch_id": step.api_call.branch_id,
                    "projection_hash": step.api_call.projection_hash,
                    "commit_id": step.api_call.commit_id,
                    "head_commit_id": step.api_call.head_commit_id,
                },
                "status": step.status,
            }
            for step in result.steps
        ],
    }


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["build_aware_skill_service_protocol_handler"]
