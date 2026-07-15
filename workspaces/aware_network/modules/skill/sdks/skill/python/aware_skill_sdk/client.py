from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from aware_skill_service_dto.skill.service_operation import SkillApiPackageRef
from aware_skill_service_dto.skill.service_operation import SkillInvokeRequest
from aware_skill_service_dto.skill.service_operation import SkillInvokeResponse
from aware_skill_service_dto.skill.service_operation import SkillInvokeResult
from aware_skill_service_dto.skill.service_operation import SkillPackageRef
from aware_skill_service_dto.skill.service_operation import SkillStepApiCallInput


class _SkillInvokeCapabilityClient(Protocol):
    async def invoke(self, request: SkillInvokeRequest) -> SkillInvokeResponse: ...


class _SkillApiNamespaceClient(Protocol):
    @property
    def invoke(self) -> _SkillInvokeCapabilityClient: ...


class SkillApiClient(Protocol):
    @property
    def skill(self) -> _SkillApiNamespaceClient: ...


class SkillSdkError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SkillPackageSelection:
    package_name: str
    semantic_object_instance_graph_commit_id: UUID
    semantic_package_id: UUID | None = None
    semantic_branch_id: UUID | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: UUID | None = None
    semantic_root_object_instance_graph_commit_id: UUID | None = None
    source_code_package_id: UUID | None = None

    def to_ref(self) -> SkillPackageRef:
        return SkillPackageRef(
            package_name=_required_text(self.package_name, "skill package_name"),
            semantic_package_id=self.semantic_package_id,
            semantic_object_instance_graph_commit_id=self.semantic_object_instance_graph_commit_id,
            semantic_branch_id=self.semantic_branch_id,
            semantic_root_kind=self.semantic_root_kind,
            semantic_root_id=self.semantic_root_id,
            semantic_root_object_instance_graph_commit_id=(
                self.semantic_root_object_instance_graph_commit_id
            ),
            source_code_package_id=self.source_code_package_id,
        )


@dataclass(frozen=True, slots=True)
class SkillApiPackageSelection:
    package_name: str
    semantic_object_instance_graph_commit_id: UUID
    semantic_package_id: UUID | None = None
    semantic_branch_id: UUID | None = None
    semantic_projection_name: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: UUID | None = None
    source_code_package_id: UUID | None = None

    def to_ref(self) -> SkillApiPackageRef:
        return SkillApiPackageRef(
            package_name=_required_text(self.package_name, "api package_name"),
            semantic_package_id=self.semantic_package_id,
            semantic_object_instance_graph_commit_id=self.semantic_object_instance_graph_commit_id,
            semantic_branch_id=self.semantic_branch_id,
            semantic_projection_name=self.semantic_projection_name,
            semantic_root_kind=self.semantic_root_kind,
            semantic_root_id=self.semantic_root_id,
            source_code_package_id=self.source_code_package_id,
        )


@dataclass(frozen=True, slots=True)
class SkillStepInput:
    skill_config_step_id: UUID
    request_payload: Mapping[str, object] = field(default_factory=dict)
    call_key: UUID | None = None
    description: str | None = None

    def to_request_input(self) -> SkillStepApiCallInput:
        return SkillStepApiCallInput.model_validate(
            {
                "skill_config_step_id": self.skill_config_step_id,
                "request_payload": dict(self.request_payload),
                "call_key": self.call_key,
                "description": self.description,
            }
        )


@dataclass(frozen=True, slots=True)
class SkillInvocation:
    response: SkillInvokeResponse
    result: SkillInvokeResult

    @property
    def skill_run_id(self) -> UUID:
        return self.result.skill_run_id

    @property
    def status(self) -> str:
        return self.result.status

    @property
    def succeeded(self) -> bool:
        return self.response.success and self.result.status == "succeeded"

    @classmethod
    def from_response(cls, response: SkillInvokeResponse) -> "SkillInvocation":
        if not response.success:
            message = response.error or response.info or "Skill invocation failed."
            raise SkillSdkError(message)
        if response.result is None:
            raise SkillSdkError("Skill invoke response did not include a result.")
        return cls(response=response, result=response.result)


@dataclass(frozen=True, slots=True)
class SkillSdkClient:
    api_client: SkillApiClient

    async def invoke_skill(
        self,
        *,
        skill_package: SkillPackageSelection | SkillPackageRef,
        skill_config_id: UUID,
        run_key: str,
        api_packages: Sequence[SkillApiPackageSelection | SkillApiPackageRef] = (),
        step_inputs: Sequence[SkillStepInput | SkillStepApiCallInput] = (),
        request_id: UUID | None = None,
        run_status: str = "succeeded",
        step_status: str = "succeeded",
        description: str | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> SkillInvocation:
        response = await self.invoke_skill_raw(
            skill_package=skill_package,
            skill_config_id=skill_config_id,
            run_key=run_key,
            api_packages=api_packages,
            step_inputs=step_inputs,
            request_id=request_id,
            run_status=run_status,
            step_status=step_status,
            description=description,
            commit=commit,
            publish=publish,
        )
        return SkillInvocation.from_response(response)

    async def invoke_skill_raw(
        self,
        *,
        skill_package: SkillPackageSelection | SkillPackageRef,
        skill_config_id: UUID,
        run_key: str,
        api_packages: Sequence[SkillApiPackageSelection | SkillApiPackageRef] = (),
        step_inputs: Sequence[SkillStepInput | SkillStepApiCallInput] = (),
        request_id: UUID | None = None,
        run_status: str = "succeeded",
        step_status: str = "succeeded",
        description: str | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> SkillInvokeResponse:
        request = SkillInvokeRequest(
            request_id=request_id,
            skill_package=_skill_package_ref(skill_package),
            api_packages=[_api_package_ref(item) for item in api_packages],
            skill_config_id=skill_config_id,
            run_key=_required_text(run_key, "run_key"),
            step_inputs=[_step_input(item) for item in step_inputs],
            run_status=_required_text(run_status, "run_status"),
            step_status=_required_text(step_status, "step_status"),
            description=description,
            commit=commit,
            publish=publish,
        )
        return await self.api_client.skill.invoke.invoke(request)


def _skill_package_ref(value: SkillPackageSelection | SkillPackageRef) -> SkillPackageRef:
    if isinstance(value, SkillPackageRef):
        return value
    return value.to_ref()


def _api_package_ref(value: SkillApiPackageSelection | SkillApiPackageRef) -> SkillApiPackageRef:
    if isinstance(value, SkillApiPackageRef):
        return value
    return value.to_ref()


def _step_input(value: SkillStepInput | SkillStepApiCallInput) -> SkillStepApiCallInput:
    if isinstance(value, SkillStepApiCallInput):
        return value
    return value.to_request_input()


def _required_text(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise SkillSdkError(f"{field_name} must be non-empty.")
    return stripped
