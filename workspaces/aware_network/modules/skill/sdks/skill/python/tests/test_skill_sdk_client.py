from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_skill_sdk import (
    SkillApiPackageSelection,
    SkillInvocation,
    SkillPackageSelection,
    SkillSdkClient,
    SkillSdkError,
    SkillStepInput,
)
from aware_skill_service_dto.skill.service_operation import SkillApiCallReceipt
from aware_skill_service_dto.skill.service_operation import SkillInvokeRequest
from aware_skill_service_dto.skill.service_operation import SkillInvokeResponse
from aware_skill_service_dto.skill.service_operation import SkillInvokeResult
from aware_skill_service_dto.skill.service_operation import SkillRunStepReceipt


class _RecordingSkillInvokeClient:
    def __init__(self, *, response: SkillInvokeResponse | None = None) -> None:
        self.requests: list[SkillInvokeRequest] = []
        self.response = response

    async def invoke(self, request: SkillInvokeRequest) -> SkillInvokeResponse:
        self.requests.append(request)
        if self.response is not None:
            return self.response
        return SkillInvokeResponse(
            request_id=request.request_id,
            result=_skill_invoke_result(
                skill_config_id=request.skill_config_id,
                run_key=request.run_key,
            ),
        )


class _RecordingSkillApiNamespace:
    def __init__(self, *, response: SkillInvokeResponse | None = None) -> None:
        self.invoke = _RecordingSkillInvokeClient(response=response)


class _RecordingGeneratedSkillApiClient:
    def __init__(self, *, response: SkillInvokeResponse | None = None) -> None:
        self.skill = _RecordingSkillApiNamespace(response=response)


@pytest.mark.asyncio
async def test_invoke_skill_builds_generated_skill_request() -> None:
    api_client = _RecordingGeneratedSkillApiClient()
    client = SkillSdkClient(api_client=api_client)
    request_id = uuid4()
    skill_commit_id = uuid4()
    api_commit_id = uuid4()
    skill_config_id = uuid4()
    step_id = uuid4()
    call_key = uuid4()

    invocation = await client.invoke_skill(
        request_id=request_id,
        skill_package=SkillPackageSelection(
            package_name="demo-skill",
            semantic_object_instance_graph_commit_id=skill_commit_id,
        ),
        api_packages=[
            SkillApiPackageSelection(
                package_name="demo-api",
                semantic_object_instance_graph_commit_id=api_commit_id,
                semantic_projection_name="api",
            )
        ],
        skill_config_id=skill_config_id,
        run_key=" run-001 ",
        step_inputs=[
            SkillStepInput(
                skill_config_step_id=step_id,
                request_payload={
                    "target": UUID("00000000-0000-0000-0000-000000000001")
                },
                call_key=call_key,
                description="first step",
            )
        ],
        description="SDK proof",
        commit=True,
        publish=False,
    )

    request = api_client.skill.invoke.requests[0]
    assert request.request_id == request_id
    assert request.skill_package.package_name == "demo-skill"
    assert (
        request.skill_package.semantic_object_instance_graph_commit_id
        == skill_commit_id
    )
    assert request.api_packages[0].package_name == "demo-api"
    assert (
        request.api_packages[0].semantic_object_instance_graph_commit_id
        == api_commit_id
    )
    assert request.api_packages[0].semantic_projection_name == "api"
    assert request.skill_config_id == skill_config_id
    assert request.run_key == "run-001"
    assert request.step_inputs[0].skill_config_step_id == step_id
    assert request.step_inputs[0].request_payload["target"] == (
        "00000000-0000-0000-0000-000000000001"
    )
    assert request.step_inputs[0].call_key == call_key
    assert request.step_inputs[0].description == "first step"
    assert request.description == "SDK proof"
    assert request.commit is True
    assert request.publish is False

    assert isinstance(invocation, SkillInvocation)
    assert invocation.response.success is True
    assert invocation.result.skill_config_id == skill_config_id
    assert invocation.result.run_key == "run-001"
    assert invocation.status == "succeeded"
    assert invocation.succeeded is True


@pytest.mark.asyncio
async def test_invoke_skill_surfaces_generated_failure_response() -> None:
    client = SkillSdkClient(
        api_client=_RecordingGeneratedSkillApiClient(
            response=SkillInvokeResponse(
                success=False,
                error="skill runtime unavailable",
            )
        )
    )

    with pytest.raises(SkillSdkError, match="skill runtime unavailable"):
        await client.invoke_skill(
            skill_package=SkillPackageSelection(
                package_name="demo-skill",
                semantic_object_instance_graph_commit_id=uuid4(),
            ),
            skill_config_id=uuid4(),
            run_key="run-001",
        )


@pytest.mark.asyncio
async def test_invoke_skill_raw_returns_generated_response_without_result_requirement() -> (
    None
):
    response = SkillInvokeResponse(success=True, info="accepted")
    client = SkillSdkClient(
        api_client=_RecordingGeneratedSkillApiClient(response=response)
    )

    raw_response = await client.invoke_skill_raw(
        skill_package=SkillPackageSelection(
            package_name="demo-skill",
            semantic_object_instance_graph_commit_id=uuid4(),
        ),
        skill_config_id=uuid4(),
        run_key="run-001",
    )

    assert raw_response is response


@pytest.mark.asyncio
async def test_skill_sdk_rejects_empty_run_key_before_api_call() -> None:
    client = SkillSdkClient(api_client=_RecordingGeneratedSkillApiClient())

    with pytest.raises(SkillSdkError, match="run_key"):
        await client.invoke_skill_raw(
            skill_package=SkillPackageSelection(
                package_name="demo-skill",
                semantic_object_instance_graph_commit_id=uuid4(),
            ),
            skill_config_id=uuid4(),
            run_key=" ",
        )


def test_skill_sdk_does_not_import_runtime_or_service_internals() -> None:
    source = (Path(__file__).parents[1] / "aware_skill_sdk" / "client.py").read_text(
        encoding="utf-8"
    )

    forbidden_imports = (
        "from aware_skill ",
        "from aware_skill.",
        "import aware_skill\n",
        "from aware_skill_service ",
        "from aware_skill_service.",
        "import aware_skill_service\n",
        "aware_skill_service_protocol",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source


def _skill_invoke_result(
    *,
    skill_config_id: UUID,
    run_key: str,
) -> SkillInvokeResult:
    skill_config_step_id = uuid4()
    api_call = SkillApiCallReceipt(
        skill_config_step_id=skill_config_step_id,
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:test",
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="api_call",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
    )
    return SkillInvokeResult(
        skill_config_id=skill_config_id,
        skill_run_id=uuid4(),
        run_key=run_key,
        status="succeeded",
        branch_id=uuid4(),
        projection_hash="skill_run",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        steps=[
            SkillRunStepReceipt(
                skill_config_step_id=skill_config_step_id,
                skill_run_step_id=uuid4(),
                api_call=api_call,
                status="succeeded",
            )
        ],
    )
