from __future__ import annotations

from aware_experience.environment_profile.api_models import (
    ExperienceEnvironmentProfileSpec,
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_types import JsonObject
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyActionConfigSpec,
    ReactivityPolicyBundleEnsureRequest,
    ReactivityPolicyBundleSpec,
    ReactivityPolicyConditionConfigSpec,
    ReactivityPolicyEventActionBindingSpec,
    ReactivityPolicyEventConditionBindingSpec,
    ReactivityPolicyEventConfigSpec,
)


_SEMANTIC_SOURCE_REF = "experience.environment_profile"
_SUBSCRIBER_ID = "experience.service"


def has_profile_reactivity_events(
    *,
    profile: ExperienceEnvironmentProfileSpec,
) -> bool:
    return bool(profile.events or [])


def build_environment_profile_reactivity_policy_bundle_request(
    *,
    request: UpsertExperienceEnvironmentProfileRequest,
    profile_key: str,
    validate_only: bool = False,
) -> ReactivityPolicyBundleEnsureRequest:
    profile = request.profile
    owner_ref = _owner_ref(
        experience_name=request.experience_name,
        profile_key=profile_key,
    )
    policy_key = f"environment_profile.{profile_key}"
    condition_names = _condition_names(profile=profile)
    event_names = _event_names(profile=profile)
    action_names = _action_names(profile=profile)

    return ReactivityPolicyBundleEnsureRequest(
        request_id=request.request_id,
        subscriber_id=_SUBSCRIBER_ID,
        validate_only=validate_only,
        bundle=ReactivityPolicyBundleSpec(
            owner_ref=owner_ref,
            policy_key=policy_key,
            version=1,
            semantic_source_ref=_SEMANTIC_SOURCE_REF,
            profile_key=profile_key,
            idempotency_key=(
                f"experience.environment_profile:{request.environment_id}:"
                f"{profile_key}:v1"
            ),
            condition_configs=[
                ReactivityPolicyConditionConfigSpec(
                    name=name,
                    description=f"Experience profile condition {name}.",
                    metadata=JsonObject(
                        {
                            "owner": "experience",
                            "profile_key": profile_key,
                        }
                    ),
                )
                for name in condition_names
            ],
            event_configs=[
                ReactivityPolicyEventConfigSpec(
                    name=name,
                    description=f"Experience profile event {name}.",
                    event_type="condition",
                    valid_sources=["environment_service_api_fanout"],
                    metadata=JsonObject(
                        {
                            "owner": "experience",
                            "profile_key": profile_key,
                        }
                    ),
                )
                for name in event_names
            ],
            action_configs=[
                ReactivityPolicyActionConfigSpec(
                    name=name,
                    description=f"Experience profile action {name}.",
                    action_type=name,
                    metadata=JsonObject(
                        {
                            "owner": "experience",
                            "profile_key": profile_key,
                        }
                    ),
                )
                for name in action_names
            ],
            event_condition_bindings=[
                ReactivityPolicyEventConditionBindingSpec(
                    event_config_name=event.event_config_ref,
                    condition_config_name=condition_name,
                )
                for event in (profile.events or [])
                for condition_name in _event_condition_names(event)
            ],
            event_action_bindings=[
                ReactivityPolicyEventActionBindingSpec(
                    event_config_name=event.event_config_ref,
                    action_config_name=action_name,
                )
                for event in (profile.events or [])
                for action in (event.actions or [])
                for action_name in [_action_name(action)]
                if action_name is not None
            ],
            metadata=JsonObject(
                {
                    "owner": "experience",
                    "source": _SEMANTIC_SOURCE_REF,
                    "profile_key": profile_key,
                    "event_count": len(profile.events or []),
                }
            ),
        ),
    )


def build_environment_profile_reactivity_policy_summary(
    *,
    profile: ExperienceEnvironmentProfileSpec,
) -> dict[str, object]:
    condition_names = _condition_names(profile=profile)
    event_names = _event_names(profile=profile)
    action_names = _action_names(profile=profile)
    return {
        "reactivity_condition_config_refs": condition_names,
        "reactivity_event_config_refs": event_names,
        "reactivity_action_config_refs": action_names,
        "reactivity_condition_config_count": len(condition_names),
        "reactivity_event_config_count": len(event_names),
        "reactivity_action_config_count": len(action_names),
        "reactivity_event_condition_binding_count": sum(
            len(_event_condition_names(event)) for event in (profile.events or [])
        ),
        "reactivity_event_action_binding_count": sum(
            1
            for event in (profile.events or [])
            for action in (event.actions or [])
            if _action_name(action) is not None
        ),
    }


def _owner_ref(*, experience_name: str | None, profile_key: str) -> str:
    owner = (experience_name or "").strip() or profile_key
    return f"experience:{owner}"


def _condition_names(*, profile: ExperienceEnvironmentProfileSpec) -> list[str]:
    names: set[str] = set()
    for event in profile.events or []:
        names.update(_event_condition_names(event))
    return sorted(names, key=str.casefold)


def _event_names(*, profile: ExperienceEnvironmentProfileSpec) -> list[str]:
    return sorted(
        {event.event_config_ref for event in (profile.events or [])},
        key=str.casefold,
    )


def _action_names(*, profile: ExperienceEnvironmentProfileSpec) -> list[str]:
    names = {
        action_name
        for event in (profile.events or [])
        for action in (event.actions or [])
        for action_name in [_action_name(action)]
        if action_name is not None
    }
    return sorted(names, key=str.casefold)


def _event_condition_names(event: object) -> tuple[str, ...]:
    condition_refs = tuple(getattr(event, "condition_config_refs", None) or ())
    return condition_refs or (getattr(event, "event_config_ref"),)


def _action_name(action: object) -> str | None:
    action_config_ref = _optional_text(getattr(action, "action_config_ref", None))
    if action_config_ref is not None:
        return action_config_ref
    program_ref = _optional_text(getattr(action, "program_ref", None))
    if program_ref is not None:
        return f"program:{program_ref}"
    action_experience_ref = _optional_text(
        getattr(action, "action_experience_ref", None)
    )
    if action_experience_ref is not None:
        return f"action_experience:{action_experience_ref}"
    return None


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "build_environment_profile_reactivity_policy_bundle_request",
    "build_environment_profile_reactivity_policy_summary",
    "has_profile_reactivity_events",
]
