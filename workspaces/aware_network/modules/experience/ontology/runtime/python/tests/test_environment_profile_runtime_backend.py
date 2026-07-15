from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from ._experience_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "environment" / "python" / "aware_environment_service_dto",
    _REPO_ROOT / "apis" / "experience" / "python" / "aware_experience_service_dto",
    _REPO_ROOT / "libs" / "comms" / "python",
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "meta" / "runtime",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "environment" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_experience_service_dto.experience.program import (  # noqa: E402
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_environment_service_dto.environment.environment import (  # noqa: E402
    ProvisionEnvironmentProfileRequest,
    ProvisionEnvironmentProfileResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)
from aware_experience.environment_profile.materialization_runtime import (  # noqa: E402
    ApplyEnvironmentExperienceProgramsResponse,
)
from aware_experience.environment_profile.api_models import (  # noqa: E402
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ProvisionExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience.environment_profile.runtime_backend import (  # noqa: E402
    EnvironmentRuntimeExperienceProfileBackend,
)
from aware_experience.environment_profile import (  # noqa: E402
    materialization_runtime as environment_experience_materialization,
)


def _profile_payload() -> dict[str, object]:
    return {
        "key": "os.default",
        "events": [
            {
                "event_config_ref": "identity.admitted",
                "actions": [{"action_config_ref": "focus.actor_home"}],
            }
        ],
        "process_configs": [
            {
                "key": "control",
                "type": "continuous",
                "thread_configs": [],
            }
        ],
    }


@pytest.mark.asyncio
async def test_runtime_backend_prefers_environment_profile_api_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = object()
    profile_id = uuid4()
    upsert_requests: list[UpsertEnvironmentProfileRequest] = []
    provision_requests: list[ProvisionEnvironmentProfileRequest] = []

    async def _forbidden_upsert(runtime_resolver: object, request: object) -> object:
        _ = runtime_resolver, request
        raise AssertionError("local Experience profile materializer was used")

    monkeypatch.setattr(
        environment_experience_materialization,
        "upsert_environment_experience",
        _forbidden_upsert,
    )

    class _EnvironmentProfileApi:
        async def upsert_environment_profile(
            self,
            request: UpsertEnvironmentProfileRequest,
        ) -> UpsertEnvironmentProfileResponse:
            upsert_requests.append(request)
            return UpsertEnvironmentProfileResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash="EnvironmentProfile",
                status="succeeded",
                environment_profile_id=profile_id,
            )

        async def provision_environment_profile(self, request):  # type: ignore[no-untyped-def]
            provision_requests.append(request)
            return ProvisionEnvironmentProfileResponse(
                environment_id=request.environment_id,
                status="succeeded",
                environment_profile_id=request.environment_profile_id,
            )

    environment_api_client = SimpleNamespace(
        environment=SimpleNamespace(profile=_EnvironmentProfileApi()),
    )
    backend = EnvironmentRuntimeExperienceProfileBackend(
        resolver=resolver,
        environment_api_client=environment_api_client,
    )

    request = UpsertExperienceEnvironmentProfileRequest(
        request_id=uuid4(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="experience.environment_profile",
        experience_name="aware_control",
        profile=_profile_payload(),
        validate_only=False,
    )

    response = await backend.upsert_environment_profile(request=request)
    provision_response = await backend.provision_environment_profile(
        request=ProvisionExperienceEnvironmentProfileRequest(
            request_id=uuid4(),
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            experience_name="aware_control",
            profile_key="os.default",
            environment_experience_profile_id=profile_id,
            topology_seed_key="default",
            validate_only=False,
        )
    )

    assert len(upsert_requests) == 1
    assert upsert_requests[0].operation == "upsert_environment_profile"
    assert upsert_requests[0].profile.key == "os.default"
    assert len(provision_requests) == 1
    assert provision_requests[0].operation == "provision_environment_profile"
    assert response.status == "succeeded"
    assert response.environment_experience_profile_id == profile_id
    assert response.profile_key == "os.default"
    assert response.evidence["backend"] == "environment_api"
    assert response.evidence["topology_owner"] == "environment"
    assert provision_response.status == "succeeded"
    assert provision_response.environment_experience_profile_id == profile_id
    assert provision_response.evidence["backend"] == "environment_api"
    assert provision_response.evidence["topology_owner"] == "environment"


@pytest.mark.asyncio
async def test_runtime_backend_rejects_upsert_without_environment_api_client() -> None:
    resolver = object()
    backend = EnvironmentRuntimeExperienceProfileBackend(resolver=resolver)

    request = UpsertExperienceEnvironmentProfileRequest(
        request_id=uuid4(),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="experience.environment_profile",
        experience_name="aware_control",
        profile=_profile_payload(),
        validate_only=False,
    )

    with pytest.raises(RuntimeError, match="Environment API client"):
        await backend.upsert_environment_profile(request=request)


@pytest.mark.asyncio
async def test_runtime_backend_rejects_provision_without_environment_api_client_and_routes_apply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = object()
    backend = EnvironmentRuntimeExperienceProfileBackend(resolver=resolver)
    profile_id = uuid4()
    captured: dict[str, Any] = {}

    async def _fake_apply(
        runtime_resolver: object,
        request: object,
        *,
        submit_program_turn_op=None,  # noqa: ANN001
    ) -> object:
        captured["apply_resolver"] = runtime_resolver
        captured["apply_request"] = request
        captured["apply_submit_program_turn_op"] = submit_program_turn_op
        return ApplyEnvironmentExperienceProgramsResponse(
            environment_id=cast(Any, request).environment_id,
            status="succeeded",
            environment_experience_profile_id=profile_id,
            phase=cast(Any, request).phase,
            target_actor_id=cast(Any, request).target_actor_id,
        )

    monkeypatch.setattr(
        environment_experience_materialization,
        "apply_environment_experience_programs",
        _fake_apply,
    )

    environment_id = uuid4()
    target_actor_id = uuid4()
    with pytest.raises(RuntimeError, match="Environment API client"):
        await backend.provision_environment_profile(
            request=ProvisionExperienceEnvironmentProfileRequest(
                request_id=uuid4(),
                environment_id=environment_id,
                profile_key="os.default",
                topology_seed_key="default",
                validate_only=False,
            )
        )

    apply_response = await backend.apply_environment_profile_programs(
        request=ApplyExperienceEnvironmentProfileProgramsRequest(
            request_id=uuid4(),
            environment_id=environment_id,
            environment_experience_profile_id=profile_id,
            profile_key="os.default",
            phase="bootstrap",
            target_actor_id=target_actor_id,
            validate_only=False,
        )
    )

    assert captured["apply_resolver"] is resolver
    assert cast(Any, captured["apply_request"]).operation == (
        "apply_environment_experience_programs"
    )
    assert captured["apply_submit_program_turn_op"] is None
    assert apply_response.operation == "apply_experience_environment_profile_programs"
    assert apply_response.profile_key == "os.default"
    assert apply_response.phase == "bootstrap"
    assert apply_response.target_actor_id == target_actor_id


@pytest.mark.asyncio
async def test_runtime_backend_apply_uses_environment_api_submit_turn_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = object()
    profile_id = uuid4()
    environment_id = uuid4()
    actor_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    target_actor_id = uuid4()
    submitted_requests: list[SubmitProgramTurnRequest] = []
    captured: dict[str, Any] = {}

    class _ProgramTurnApi:
        async def submit_program_turn(
            self,
            request: SubmitProgramTurnRequest,
        ) -> SubmitProgramTurnResponse:
            submitted_requests.append(request)
            return SubmitProgramTurnResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="accepted",
                error=None,
                turn_id=uuid4(),
                mailbox_key=request.mailbox_key,
                deduped=False,
            )

    environment_api_client = SimpleNamespace(
        environment=SimpleNamespace(
            program_turn=_ProgramTurnApi(),
        )
    )
    backend = EnvironmentRuntimeExperienceProfileBackend(
        resolver=resolver,
        environment_api_client=environment_api_client,
    )

    async def _fake_apply(
        runtime_resolver: object,
        request: object,
        *,
        submit_program_turn_op=None,  # noqa: ANN001
    ) -> object:
        if not callable(submit_program_turn_op):
            raise AssertionError("submit_program_turn_op was not injected")
        submit_request = SubmitProgramTurnRequest(
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=None,
            projection_hash=None,
            target_actor_id=target_actor_id,
            program_ref="conversation_default:HumanConversationMessage_v1",
            symbols={},
            message="hello",
            turn_index=1,
            mailbox_key="mailbox:test",
            idempotency_key=None,
            max_attempts=1,
            wait_for_terminal=False,
        )
        captured["submit_response"] = await submit_program_turn_op(
            runtime_resolver,
            submit_request,
        )
        return ApplyEnvironmentExperienceProgramsResponse(
            environment_id=cast(Any, request).environment_id,
            status="succeeded",
            environment_experience_profile_id=profile_id,
            phase=cast(Any, request).phase,
            target_actor_id=cast(Any, request).target_actor_id,
        )

    monkeypatch.setattr(
        environment_experience_materialization,
        "apply_environment_experience_programs",
        _fake_apply,
    )

    apply_response = await backend.apply_environment_profile_programs(
        request=ApplyExperienceEnvironmentProfileProgramsRequest(
            request_id=uuid4(),
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            environment_experience_profile_id=profile_id,
            profile_key="os.default",
            phase="bootstrap",
            target_actor_id=target_actor_id,
            validate_only=False,
        )
    )

    assert len(submitted_requests) == 1
    assert submitted_requests[0].program_ref == (
        "conversation_default:HumanConversationMessage_v1"
    )
    assert isinstance(captured["submit_response"], SubmitProgramTurnResponse)
    assert apply_response.operation == "apply_experience_environment_profile_programs"
    assert apply_response.success is True
