from __future__ import annotations

from typing import cast

from aware_code.types import JsonObject, JsonValue
from aware_experience.thread_layout_resolution.api_models import (
    ExperienceThreadLayoutAccessRequirement,
    ExperienceThreadLayoutEnvironmentActivation,
    ExperienceThreadLayoutConfigTarget,
    ExperienceThreadLayoutEnvironmentTarget,
    ExperienceThreadLayoutIntentResolution,
    ExperienceThreadLayoutSectionViewMapping,
    ResolveExperienceThreadLayoutIntentRequest,
    ResolveExperienceThreadLayoutIntentResponse,
)
from aware_experience.environment_profile.api_models import (
    ExperienceEnvironmentProfileLayoutConfigSpec,
    ExperienceEnvironmentProfileProcessSpec,
    ExperienceEnvironmentProfileSpec,
    ExperienceEnvironmentProfileThreadSpec,
    ExperienceEnvironmentProfileTopologyLayoutSeedSpec,
    ExperienceEnvironmentProfileTopologyProcessSeedSpec,
    ExperienceEnvironmentProfileTopologySeedSpec,
    ExperienceEnvironmentProfileTopologyThreadSeedSpec,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext

_IDENTITY_ADMISSION_INTENT_KEY = "identity.admission"
_DEFAULT_EXPERIENCE_NAME = "aware_control_identity"
_DEFAULT_PROFILE_KEY = "os.default"
_DEFAULT_ENVIRONMENT_SELECTOR = "current"
_DEFAULT_PROCESS_KEY = "control"
_DEFAULT_THREAD_KEY = "control.main"
_DEFAULT_LAYOUT_KEY = "personal"
_DEFAULT_INTERFACE_PACKAGE_NAME = "aware-control-interface"
_DEFAULT_WINDOW_KEY = "main"
_DEFAULT_SECTION_KEY = "identity_admission"
_DEFAULT_VIEW_KEY = "admission.v1"
_DEFAULT_VIEW_REF = "aware_control_identity.identity.admission.v1"
_DEFAULT_SECTION_GRAPH_BINDING_KEY = "identity.admission"
_DEFAULT_PROCESS_TITLE = "Control"
_DEFAULT_PROCESS_NARRATIVE = (
    "Continuous control process for kernel bootstrap and operator handoff."
)
_DEFAULT_THREAD_TITLE = "Control Main"
_DEFAULT_THREAD_NARRATIVE = (
    "Primary control thread for identity admission and host readiness."
)
_DEFAULT_PROFILE_TITLE = "Aware Control OS"
_DEFAULT_PROFILE_DESCRIPTION = (
    "Canonical default experience profile for the Aware Control environment."
)
_DEFAULT_PROFILE_NARRATIVE = (
    "Admit identity, observe kernel services, and select target environments."
)
_PERSONAL_ACCESS_SCOPE = "personal"
_PERSONAL_ROLE_CONFIG_NAME = "aware.interface.layout.personal.actor"
_EXPERIENCE_NAME_ALIASES = {
    "aware_control": _DEFAULT_EXPERIENCE_NAME,
    "aware_control.personal": _DEFAULT_EXPERIENCE_NAME,
}


async def resolve_thread_layout_intent(
    *,
    request: ResolveExperienceThreadLayoutIntentRequest,
    host_context: ServiceApiHostContext,
) -> ResolveExperienceThreadLayoutIntentResponse:
    _ = host_context
    intent_key = _normalize_required_text(request.intent_key, label="intent_key")
    if intent_key != _IDENTITY_ADMISSION_INTENT_KEY:
        raise ValueError(f"Unsupported Experience thread-layout intent: {intent_key!r}")

    experience_name = _normalize_experience_name(request.experience_name)
    profile_key = _normalize_optional_text(request.profile_key) or _DEFAULT_PROFILE_KEY
    environment = ExperienceThreadLayoutEnvironmentTarget(
        environment_id=request.environment_id,
        environment_handle=_normalize_optional_text(request.environment_handle),
        environment_selector=(
            _normalize_optional_text(request.environment_selector)
            or _DEFAULT_ENVIRONMENT_SELECTOR
        ),
    )
    resolution = ExperienceThreadLayoutIntentResolution(
        experience_name=experience_name,
        profile_key=profile_key,
        intent_key=intent_key,
        environment=environment,
        target=ExperienceThreadLayoutConfigTarget(
            process_key=_DEFAULT_PROCESS_KEY,
            thread_key=_DEFAULT_THREAD_KEY,
            layout_key=_DEFAULT_LAYOUT_KEY,
            interface_package_name=_DEFAULT_INTERFACE_PACKAGE_NAME,
            window_key=_DEFAULT_WINDOW_KEY,
        ),
        sections=[
            ExperienceThreadLayoutSectionViewMapping(
                section_key=_DEFAULT_SECTION_KEY,
                projection_experience_name=_DEFAULT_EXPERIENCE_NAME,
                view_key=_DEFAULT_VIEW_KEY,
                view_ref=_DEFAULT_VIEW_REF,
                section_graph_binding_key=_DEFAULT_SECTION_GRAPH_BINDING_KEY,
                is_default=True,
                intent=intent_key,
            )
        ],
        default_section_key=_DEFAULT_SECTION_KEY,
        access_requirement=ExperienceThreadLayoutAccessRequirement(
            access_scope=_PERSONAL_ACCESS_SCOPE,
            role_config_name=_PERSONAL_ROLE_CONFIG_NAME,
            class_instance_identity_required=True,
            role_assignment_binding_required=False,
        ),
        environment_activation=_identity_admission_environment_activation(
            profile_key=profile_key,
            topology_seed_key=intent_key,
        ),
        evidence=_identity_admission_evidence(
            request=request,
            experience_name=experience_name,
            profile_key=profile_key,
        ),
    )
    return ResolveExperienceThreadLayoutIntentResponse(
        request_id=request.request_id,
        success=True,
        info="experience thread-layout intent resolved without runtime mutation",
        resolution=resolution,
    )


def _identity_admission_environment_activation(
    *,
    profile_key: str,
    topology_seed_key: str,
) -> ExperienceThreadLayoutEnvironmentActivation:
    return ExperienceThreadLayoutEnvironmentActivation(
        profile=ExperienceEnvironmentProfileSpec(
            key=profile_key,
            title=_DEFAULT_PROFILE_TITLE,
            description=_DEFAULT_PROFILE_DESCRIPTION,
            narrative=_DEFAULT_PROFILE_NARRATIVE,
            process_configs=[
                ExperienceEnvironmentProfileProcessSpec(
                    key=_DEFAULT_PROCESS_KEY,
                    type="continuous",
                    title=_DEFAULT_PROCESS_TITLE,
                    narrative=_DEFAULT_PROCESS_NARRATIVE,
                    intent="control",
                    thread_configs=[
                        ExperienceEnvironmentProfileThreadSpec(
                            key=_DEFAULT_THREAD_KEY,
                            title=_DEFAULT_THREAD_TITLE,
                            narrative=_DEFAULT_THREAD_NARRATIVE,
                            workspace_view_key="thread.workspace",
                            layout_configs=[
                                ExperienceEnvironmentProfileLayoutConfigSpec(
                                    layout_key=_DEFAULT_LAYOUT_KEY,
                                    key=_DEFAULT_LAYOUT_KEY,
                                )
                            ],
                        )
                    ],
                )
            ],
        ),
        topology_seed_key=topology_seed_key,
        topology_seeds=[
            ExperienceEnvironmentProfileTopologySeedSpec(
                key=topology_seed_key,
                title="Identity Admission",
                process_seeds=[
                    ExperienceEnvironmentProfileTopologyProcessSeedSpec(
                        process_config_key=_DEFAULT_PROCESS_KEY,
                        process_key=_DEFAULT_PROCESS_KEY,
                        title=_DEFAULT_PROCESS_TITLE,
                        thread_seeds=[
                            ExperienceEnvironmentProfileTopologyThreadSeedSpec(
                                thread_config_key=_DEFAULT_THREAD_KEY,
                                thread_key=_DEFAULT_THREAD_KEY,
                                title=_DEFAULT_THREAD_TITLE,
                                is_main=True,
                                layout_seeds=[
                                    ExperienceEnvironmentProfileTopologyLayoutSeedSpec(
                                        layout_key=_DEFAULT_LAYOUT_KEY,
                                        key=_DEFAULT_LAYOUT_KEY,
                                        activate_on_seed=True,
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def _identity_admission_evidence(
    *,
    request: ResolveExperienceThreadLayoutIntentRequest,
    experience_name: str,
    profile_key: str,
) -> JsonObject:
    context = cast(JsonObject, dict(request.request_context or {}))
    return JsonObject(
        cast(
            dict[str, JsonValue],
            {
                "resolver": (
                    "aware_experience.thread_layout_resolution."
                    "identity_admission.v0"
                ),
                "intent_key": _IDENTITY_ADMISSION_INTENT_KEY,
                "experience_name": experience_name,
                "profile_key": profile_key,
                "process_key": _DEFAULT_PROCESS_KEY,
                "thread_key": _DEFAULT_THREAD_KEY,
                "layout_key": _DEFAULT_LAYOUT_KEY,
                "default_section_key": _DEFAULT_SECTION_KEY,
                "runtime_mutation": False,
                "environment_activation_owner": "environment-sdk",
                "attention_application_owner": "attention-service",
                "interface_window_owner": "interface-service",
                "request_context": context,
            },
        )
    )


def _normalize_experience_name(value: str | None) -> str:
    normalized = _normalize_optional_text(value) or _DEFAULT_EXPERIENCE_NAME
    return _EXPERIENCE_NAME_ALIASES.get(normalized, normalized)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_required_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


__all__ = [
    "resolve_thread_layout_intent",
]
