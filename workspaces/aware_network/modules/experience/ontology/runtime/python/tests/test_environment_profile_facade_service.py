from __future__ import annotations

from uuid import uuid4

import pytest

from aware_experience.environment_profile.api_models import (
    ProvisionExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience.environment_profile.service import (
    provision_experience_environment_profile,
    upsert_experience_environment_profile,
)


def _profile_payload() -> dict[str, object]:
    return {
        "key": "os.default",
        "roles": [
            {
                "name": "aware.interface.layout.personal.actor",
                "capabilities": ["Environment.create_process"],
            }
        ],
        "actors": [
            {
                "key": "primary",
                "role_names": ["aware.interface.layout.personal.actor"],
            }
        ],
        "events": [
            {
                "event_config_ref": "conversation.message.created",
                "actions": [
                    {
                        "action_config_ref": "conversation.react",
                        "program_ref": "conversation_default:react_to_message",
                    }
                ],
            }
        ],
        "programs": [
            {"program_ref": "conversation_default:react_to_message"},
        ],
        "program_applies": [
            {
                "key": "conversation.reactivity.bootstrap",
                "program_ref": "conversation_default:react_to_message",
            }
        ],
        "process_configs": [
            {
                "key": "control",
                "type": "continuous",
                "thread_configs": [
                    {
                        "key": "control.main",
                        "projection_identities": [
                            {
                                "projection_identity_key": "aware_identity:identity",
                                "is_default": True,
                            }
                        ],
                        "layout_configs": [{"layout_key": "personal"}],
                    }
                ],
            }
        ],
    }


def _topology_seed_payload() -> dict[str, object]:
    return {
        "key": "default",
        "process_seeds": [
            {
                "process_config_key": "control",
                "process_key": "control",
                "thread_seeds": [
                    {
                        "thread_config_key": "control.main",
                        "thread_key": "control.main",
                        "layout_seeds": [
                            {
                                "layout_key": "personal",
                                "activate_on_seed": True,
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_upsert_environment_profile_validate_only_resolves_contract() -> None:
    request = UpsertExperienceEnvironmentProfileRequest(
        environment_id=uuid4(),
        experience_name="aware_control",
        profile=_profile_payload(),
        topology_seeds=[_topology_seed_payload()],
        validate_only=True,
    )

    response = await upsert_experience_environment_profile(request=request)

    assert response.success is True
    assert response.status == "planned"
    assert response.profile_key == "os.default"
    assert response.evidence["owner"] == "experience"
    assert response.evidence["runtime_mutation"] is False
    assert response.evidence["profile_event_count"] == 1
    assert response.evidence["reactivity_policy_setup"] == "planned"


@pytest.mark.asyncio
async def test_upsert_environment_profile_rejects_unknown_program_apply_ref() -> None:
    profile = _profile_payload()
    profile["program_applies"] = [
        {
            "key": "missing",
            "program_ref": "conversation_default:missing",
        }
    ]
    request = UpsertExperienceEnvironmentProfileRequest(
        environment_id=uuid4(),
        profile=profile,
        validate_only=True,
    )

    with pytest.raises(ValueError, match="program_applies"):
        await upsert_experience_environment_profile(request=request)


@pytest.mark.asyncio
async def test_provision_environment_profile_validate_only_is_experience_owned() -> (
    None
):
    environment_id = uuid4()
    profile_id = uuid4()
    request = ProvisionExperienceEnvironmentProfileRequest(
        environment_id=environment_id,
        environment_experience_profile_id=profile_id,
        topology_seed_key="default",
        validate_only=True,
    )

    response = await provision_experience_environment_profile(request=request)

    assert response.success is True
    assert response.status == "planned"
    assert response.environment_id == environment_id
    assert response.environment_experience_profile_id == profile_id
    assert response.evidence["owner"] == "experience"
    assert response.evidence["topology_seed_key"] == "default"


@pytest.mark.asyncio
async def test_provision_environment_profile_commit_path_fails_closed_until_cutover() -> (
    None
):
    request = ProvisionExperienceEnvironmentProfileRequest(
        environment_id=uuid4(),
        topology_seed_key="default",
        validate_only=False,
    )

    response = await provision_experience_environment_profile(request=request)

    assert response.success is False
    assert response.status == "not_enabled"
    assert "runtime materialization is not enabled" in (response.error or "")


@pytest.mark.asyncio
async def test_upsert_environment_profile_events_fail_without_reactivity_backend() -> (
    None
):
    calls: list[str] = []

    class _RuntimeBackend:
        async def upsert_environment_profile(self, *, request, host_context=None):  # type: ignore[no-untyped-def]
            calls.append("runtime")
            return UpsertExperienceEnvironmentProfileResponse(
                request_id=request.request_id,
                success=True,
                status="succeeded",
                environment_id=request.environment_id,
                profile_key=request.profile.key,
                evidence={"owner": "experience"},
            )

    request = UpsertExperienceEnvironmentProfileRequest(
        environment_id=uuid4(),
        experience_name="aware_control",
        profile=_profile_payload(),
        validate_only=False,
    )

    response = await upsert_experience_environment_profile(
        request=request,
        runtime_backend=_RuntimeBackend(),
    )

    assert response.success is False
    assert response.status == "reactivity_not_configured"
    assert response.evidence["reactivity_policy_setup"] == "missing_backend"
    assert calls == []


@pytest.mark.asyncio
async def test_upsert_environment_profile_events_ensure_reactivity_policy() -> None:
    calls: list[str] = []

    class _RuntimeBackend:
        async def upsert_environment_profile(self, *, request, host_context=None):  # type: ignore[no-untyped-def]
            calls.append("runtime")
            return UpsertExperienceEnvironmentProfileResponse(
                request_id=request.request_id,
                success=True,
                status="succeeded",
                environment_id=request.environment_id,
                profile_key=request.profile.key,
                evidence={"owner": "experience"},
            )

    class _ReactivityBackend:
        async def ensure_environment_profile_policy_bundle(  # type: ignore[no-untyped-def]
            self,
            *,
            request,
            profile_key,
            validate_only=False,
            host_context=None,
        ):
            calls.append("reactivity")
            assert profile_key == "os.default"
            assert validate_only is False
            return {
                "status": "ensured",
                "policy_key": f"environment_profile.{profile_key}",
                "event_config_count": len(request.profile.events or []),
            }

    request = UpsertExperienceEnvironmentProfileRequest(
        environment_id=uuid4(),
        experience_name="aware_control",
        profile=_profile_payload(),
        validate_only=False,
    )

    response = await upsert_experience_environment_profile(
        request=request,
        runtime_backend=_RuntimeBackend(),
        reactivity_policy_backend=_ReactivityBackend(),
    )

    assert response.success is True
    assert response.status == "succeeded"
    assert response.evidence["reactivity_policy_setup"] == "ensured"
    assert response.evidence["reactivity_policy"]["policy_key"] == (
        "environment_profile.os.default"
    )
    assert calls == ["reactivity", "runtime"]
