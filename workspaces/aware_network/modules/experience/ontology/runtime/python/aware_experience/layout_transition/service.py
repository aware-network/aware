from __future__ import annotations

from aware_code.types import JsonObject
from aware_experience.layout_transition.api_models import (
    ExperienceInterfaceWindowLayoutTarget,
    ExperienceLayoutActorRoleGate,
    ExperienceLayoutTransitionReceipt,
    RequestExperienceLayoutTransitionRequest,
    RequestExperienceLayoutTransitionResponse,
)
from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceSectionGraphBindingRequest,
    ExperienceSectionGraphBindingActivationScope,
)
from aware_experience.section_graph_binding.service import (
    activate_section_graph_binding,
)
from aware_experience.thread_layout_resolution.api_models import (
    ExperienceThreadLayoutAccessRequirement,
    ExperienceThreadLayoutIntentResolution,
    ExperienceThreadLayoutSectionViewMapping,
    ResolveExperienceThreadLayoutIntentRequest,
)
from aware_experience.thread_layout_resolution.service import (
    resolve_thread_layout_intent,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext

_DEFAULT_EXPERIENCE_NAME = "aware_control_identity"
_IDENTITY_ADMISSION_INTENT_KEY = "identity.admission"
_DEFAULT_INTERFACE_PACKAGE_NAME = "aware-control-interface"
_DEFAULT_WINDOW_KEY = "main"
_DEFAULT_LAYOUT_KEY = "personal"
_PERSONAL_ACCESS_SCOPE = "personal"


async def request_layout_transition(
    *,
    request: RequestExperienceLayoutTransitionRequest,
    host_context: ServiceApiHostContext,
) -> RequestExperienceLayoutTransitionResponse:
    namespace = _normalize_required_text(request.namespace, label="namespace")
    experience_name = (
        _normalize_optional_text(request.experience_name) or _DEFAULT_EXPERIENCE_NAME
    )
    intent_key = (
        _normalize_optional_text(request.intent_key) or _IDENTITY_ADMISSION_INTENT_KEY
    )
    resolution_response = await resolve_thread_layout_intent(
        request=ResolveExperienceThreadLayoutIntentRequest(
            request_id=request.request_id,
            intent_key=intent_key,
            experience_name=experience_name,
            request_context=JsonObject(
                {
                    "operation": "request_experience_layout_transition",
                    "namespace": namespace,
                }
            ),
        ),
        host_context=host_context,
    )
    target = _resolved_target(
        request.target,
        resolution=resolution_response.resolution,
    )
    role_gate = _require_layout_role_gate(
        request.role_gate,
        access_requirement=resolution_response.resolution.access_requirement,
    )
    section_graph_binding = _require_section_graph_binding_mapping(
        resolution=resolution_response.resolution,
        target=target,
    )
    activation_response = await activate_section_graph_binding(
        request=ActivateExperienceSectionGraphBindingRequest(
            request_id=request.request_id,
            experience_name=resolution_response.resolution.experience_name,
            binding_key=section_graph_binding.section_graph_binding_key,
            activation_scope=ExperienceSectionGraphBindingActivationScope(
                window_key=target.window_key,
                layout_key=target.layout_key,
                section_key=(
                    _normalize_optional_text(target.section_key)
                    or _normalize_optional_text(section_graph_binding.section_key)
                ),
            ),
            rationale=(
                _normalize_optional_text(request.reason)
                or f"experience_layout_transition:{intent_key}"
            ),
        ),
        host_context=host_context,
    )
    interface_idempotency_key = _normalize_optional_text(
        request.idempotency_key
    ) or _layout_transition_idempotency_key(
        namespace=namespace,
        actor_id=str(request.actor_id),
        experience_name=experience_name,
        intent_key=intent_key,
        layout_key=target.layout_key,
    )
    receipt = ExperienceLayoutTransitionReceipt(
        namespace=namespace,
        actor_id=request.actor_id,
        identity_id=request.identity_id,
        experience_name=resolution_response.resolution.experience_name,
        intent_key=resolution_response.resolution.intent_key,
        target=target,
        role_gate=role_gate,
        section_graph_binding_key=section_graph_binding.section_graph_binding_key,
        attention_state=activation_response.state,
        interface_idempotency_key=interface_idempotency_key,
        info=(
            "experience layout transition activated Attention section graph "
            "binding; Interface owns window layout application"
        ),
    )
    return RequestExperienceLayoutTransitionResponse(
        request_id=request.request_id,
        success=True,
        info=receipt.info,
        receipt=receipt,
    )


def _resolved_target(
    target: ExperienceInterfaceWindowLayoutTarget | None,
    *,
    resolution: ExperienceThreadLayoutIntentResolution,
) -> ExperienceInterfaceWindowLayoutTarget:
    if target is None:
        resolved = resolution.target
        return ExperienceInterfaceWindowLayoutTarget(
            interface_package_id=resolved.interface_package_id,
            interface_package_name=(
                _normalize_optional_text(resolved.interface_package_name)
                or _DEFAULT_INTERFACE_PACKAGE_NAME
            ),
            window_key=_normalize_optional_text(resolved.window_key)
            or _DEFAULT_WINDOW_KEY,
            layout_config_id=resolved.layout_config_id,
            layout_key=_normalize_optional_text(resolved.layout_key)
            or _DEFAULT_LAYOUT_KEY,
            section_key=_normalize_optional_text(resolution.default_section_key),
        )
    layout_key = _normalize_required_text(target.layout_key, label="layout_key")
    return target.model_copy(
        update={
            "interface_package_name": (
                _normalize_optional_text(target.interface_package_name)
                or _DEFAULT_INTERFACE_PACKAGE_NAME
            ),
            "window_key": (
                _normalize_optional_text(target.window_key) or _DEFAULT_WINDOW_KEY
            ),
            "layout_key": layout_key,
            "section_key": (
                _normalize_optional_text(target.section_key)
                or _normalize_optional_text(resolution.default_section_key)
            ),
        }
    )


def _require_layout_role_gate(
    role_gate: ExperienceLayoutActorRoleGate,
    *,
    access_requirement: ExperienceThreadLayoutAccessRequirement | None,
) -> ExperienceLayoutActorRoleGate:
    required_access_scope = _PERSONAL_ACCESS_SCOPE
    required_role_config_name: str | None = None
    if access_requirement is not None:
        required_access_scope = (
            _normalize_optional_text(access_requirement.access_scope)
            or _PERSONAL_ACCESS_SCOPE
        )
        required_role_config_name = _normalize_optional_text(
            access_requirement.role_config_name
        )
    access_scope = (
        _normalize_optional_text(role_gate.access_scope) or required_access_scope
    )
    if access_scope != required_access_scope:
        raise ValueError(
            "request_experience_layout_transition requires "
            + f"role_gate.access_scope={required_access_scope!r}."
        )
    role_config_name = (
        _normalize_optional_text(role_gate.role_config_name)
        or required_role_config_name
    )
    if role_gate.role_config_id is None and role_config_name is None:
        raise ValueError(
            "request_experience_layout_transition requires "
            "role_gate.role_config_id or role_gate.role_config_name."
        )
    return role_gate.model_copy(
        update={
            "access_scope": access_scope,
            "role_config_name": role_config_name,
        }
    )


def _require_section_graph_binding_mapping(
    *,
    resolution: ExperienceThreadLayoutIntentResolution,
    target: ExperienceInterfaceWindowLayoutTarget,
) -> ExperienceThreadLayoutSectionViewMapping:
    sections = tuple(resolution.sections or ())
    if not sections:
        raise ValueError(
            "request_experience_layout_transition requires resolved section "
            "graph binding mappings."
        )
    target_section_key = _normalize_optional_text(target.section_key)
    default_section_key = _normalize_optional_text(resolution.default_section_key)
    for section in sections:
        section_key = _normalize_optional_text(section.section_key)
        if target_section_key is not None and section_key == target_section_key:
            return _require_section_graph_binding_key(section)
    for section in sections:
        section_key = _normalize_optional_text(section.section_key)
        if default_section_key is not None and section_key == default_section_key:
            return _require_section_graph_binding_key(section)
    for section in sections:
        if bool(getattr(section, "is_default", False)):
            return _require_section_graph_binding_key(section)
    return _require_section_graph_binding_key(sections[0])


def _require_section_graph_binding_key(
    section: ExperienceThreadLayoutSectionViewMapping,
) -> ExperienceThreadLayoutSectionViewMapping:
    if not _normalize_optional_text(section.section_graph_binding_key):
        raise ValueError(
            "request_experience_layout_transition requires resolved section "
            "mapping section_graph_binding_key."
        )
    return section


def _layout_transition_idempotency_key(
    *,
    namespace: str,
    actor_id: str,
    experience_name: str,
    intent_key: str,
    layout_key: str,
) -> str:
    return ":".join(
        (
            "experience-layout-transition",
            namespace,
            actor_id,
            experience_name,
            intent_key,
            layout_key,
        )
    )


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
    "request_layout_transition",
]
