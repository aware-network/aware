from __future__ import annotations

from uuid import uuid4

from aware_experience.environment_profile.api_models import (
    ExperienceEnvironmentProfileSpec,
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience.environment_profile.reactivity_policy import (
    build_environment_profile_reactivity_policy_bundle_request,
)


def test_build_environment_profile_reactivity_policy_bundle_request() -> None:
    environment_id = uuid4()
    request = UpsertExperienceEnvironmentProfileRequest(
        request_id=uuid4(),
        environment_id=environment_id,
        experience_name="aware_control",
        profile=ExperienceEnvironmentProfileSpec.model_validate(
            {
                "key": "os.default",
                "events": [
                    {
                        "event_config_ref": "identity.admitted",
                        "condition_config_refs": ["identity.profile.created"],
                        "actions": [
                            {"action_config_ref": "focus.actor_home"},
                            {"program_ref": "aware_control:hydrate_actor_home"},
                        ],
                    }
                ],
            }
        ),
    )

    ensure_request = build_environment_profile_reactivity_policy_bundle_request(
        request=request,
        profile_key="os.default",
    )

    bundle = ensure_request.bundle
    assert ensure_request.subscriber_id == "experience.service"
    assert bundle.owner_ref == "experience:aware_control"
    assert bundle.policy_key == "environment_profile.os.default"
    assert bundle.semantic_source_ref == "experience.environment_profile"
    assert bundle.profile_key == "os.default"
    assert (
        bundle.idempotency_key
        == f"experience.environment_profile:{environment_id}:os.default:v1"
    )
    assert [item.name for item in bundle.condition_configs] == [
        "identity.profile.created"
    ]
    assert [item.name for item in bundle.event_configs] == ["identity.admitted"]
    assert [item.name for item in bundle.action_configs] == [
        "focus.actor_home",
        "program:aware_control:hydrate_actor_home",
    ]
    assert bundle.event_condition_bindings[0].event_config_name == "identity.admitted"
    assert (
        bundle.event_condition_bindings[0].condition_config_name
        == "identity.profile.created"
    )
    assert bundle.event_action_bindings[0].action_config_name == "focus.actor_home"
    assert (
        bundle.event_action_bindings[1].action_config_name
        == "program:aware_control:hydrate_actor_home"
    )
