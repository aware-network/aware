from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    JsonObject,
    JsonValue,
)

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.actor_admission.models import ExperienceActorConfigRoleAdmissionBinding
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceInvocationActionAdmissionPreflight,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceInvocationActionRolePolicyResolution,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceLayoutGraphBindingDescriptor,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceLayoutGraphBindingState
    from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionFocusTarget
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceSectionGraphBindingDescriptor,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionGraphBindingState
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceSectionGraphBindingStateSnapshot,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionViewResolution
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceViewInvocationActionApiDispatchReceipt,
    )
    from aware_experience_service_dto.experience.section_graph_binding.models import (
        ExperienceViewInvocationActionReceipt,
    )


class ExperienceSectionGraphBindingServiceRequest(BaseModel):
    """
    Canonical request/response DTOs for the Experience section-graph-binding service boundary.
    These are transport-level DTOs over Experience-owned section-graph-binding semantics.
    They do not replace ontology truth and they do not authorize direct Attention mutation.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "get_experience_section_graph_binding_catalog": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingCatalogRequest",
        "get_experience_layout_graph_binding_catalog": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingCatalogRequest",
        "get_experience_section_graph_binding_state": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingStateRequest",
        "get_experience_layout_graph_binding_state": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingStateRequest",
        "activate_experience_section_graph_binding": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceSectionGraphBindingRequest",
        "activate_experience_layout_graph_binding": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceLayoutGraphBindingRequest",
        "apply_experience_view_event_transition": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ApplyExperienceViewEventTransitionRequest",
        "record_experience_view_invocation_action": "aware_experience_service_dto.experience.section_graph_binding.service_operation.RecordExperienceViewInvocationActionRequest",
        "invoke_experience_view_invocation_action": "aware_experience_service_dto.experience.section_graph_binding.service_operation.InvokeExperienceViewInvocationActionRequest",
        "resolve_experience_invocation_action_role_policy": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ResolveExperienceInvocationActionRolePolicyRequest",
        "watch_experience_section_graph_bindings": "aware_experience_service_dto.experience.section_graph_binding.service_operation.WatchExperienceSectionGraphBindingsRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownExperienceSectionGraphBindingServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSectionGraphBindingServiceRequest(ExperienceSectionGraphBindingServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceSectionGraphBindingServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    state: ExperienceSectionGraphBindingState | None = Field(default=None)
    snapshot: ExperienceSectionGraphBindingStateSnapshot | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "get_experience_section_graph_binding_catalog": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingCatalogResponse",
        "get_experience_layout_graph_binding_catalog": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingCatalogResponse",
        "get_experience_section_graph_binding_state": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceSectionGraphBindingStateResponse",
        "get_experience_layout_graph_binding_state": "aware_experience_service_dto.experience.section_graph_binding.service_operation.GetExperienceLayoutGraphBindingStateResponse",
        "activate_experience_section_graph_binding": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceSectionGraphBindingResponse",
        "activate_experience_layout_graph_binding": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ActivateExperienceLayoutGraphBindingResponse",
        "apply_experience_view_event_transition": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ApplyExperienceViewEventTransitionResponse",
        "record_experience_view_invocation_action": "aware_experience_service_dto.experience.section_graph_binding.service_operation.RecordExperienceViewInvocationActionResponse",
        "invoke_experience_view_invocation_action": "aware_experience_service_dto.experience.section_graph_binding.service_operation.InvokeExperienceViewInvocationActionResponse",
        "resolve_experience_invocation_action_role_policy": "aware_experience_service_dto.experience.section_graph_binding.service_operation.ResolveExperienceInvocationActionRolePolicyResponse",
        "watch_experience_section_graph_bindings": "aware_experience_service_dto.experience.section_graph_binding.service_operation.WatchExperienceSectionGraphBindingsResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownExperienceSectionGraphBindingServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSectionGraphBindingServiceResponse(ExperienceSectionGraphBindingServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class GetExperienceSectionGraphBindingCatalogRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["get_experience_section_graph_binding_catalog"] = "get_experience_section_graph_binding_catalog"

    # Attributes
    experience_name: str
    section_keys: list[str] = Field(default_factory=list)
    binding_keys: list[str] = Field(default_factory=list)


class GetExperienceSectionGraphBindingCatalogResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["get_experience_section_graph_binding_catalog"] = "get_experience_section_graph_binding_catalog"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    bindings: list[ExperienceSectionGraphBindingDescriptor] = Field(default_factory=list)


class GetExperienceLayoutGraphBindingCatalogRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["get_experience_layout_graph_binding_catalog"] = "get_experience_layout_graph_binding_catalog"

    # Attributes
    experience_name: str
    layout_binding_keys: list[str] = Field(default_factory=list)


class GetExperienceLayoutGraphBindingCatalogResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["get_experience_layout_graph_binding_catalog"] = "get_experience_layout_graph_binding_catalog"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    bindings: list[ExperienceLayoutGraphBindingDescriptor] = Field(default_factory=list)


class GetExperienceSectionGraphBindingStateRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["get_experience_section_graph_binding_state"] = "get_experience_section_graph_binding_state"

    # Attributes
    experience_name: str
    binding_key: str


class GetExperienceSectionGraphBindingStateResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["get_experience_section_graph_binding_state"] = "get_experience_section_graph_binding_state"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    state: ExperienceSectionGraphBindingState


class GetExperienceLayoutGraphBindingStateRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["get_experience_layout_graph_binding_state"] = "get_experience_layout_graph_binding_state"

    # Attributes
    experience_name: str
    layout_binding_key: str


class GetExperienceLayoutGraphBindingStateResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["get_experience_layout_graph_binding_state"] = "get_experience_layout_graph_binding_state"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    state: ExperienceLayoutGraphBindingState


class ExperienceSectionGraphBindingActivationScope(BaseModel):
    # Attributes
    window_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    state_projection_hash: str | None = Field(default=None)
    focus_target: ExperienceSectionFocusTarget | None = Field(default=None)


class ActivateExperienceSectionGraphBindingRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["activate_experience_section_graph_binding"] = "activate_experience_section_graph_binding"

    # Attributes
    experience_name: str
    binding_key: str
    activation_scope: ExperienceSectionGraphBindingActivationScope | None = Field(default=None)
    rationale: str | None = Field(default=None)
    section_title: str | None = Field(default=None)
    section_description: str | None = Field(default=None)
    focus_scope_title: str | None = Field(default=None)
    focus_scope_description: str | None = Field(default=None)


class ActivateExperienceSectionGraphBindingResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["activate_experience_section_graph_binding"] = "activate_experience_section_graph_binding"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    state: ExperienceSectionGraphBindingState


class ActivateExperienceLayoutGraphBindingRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["activate_experience_layout_graph_binding"] = "activate_experience_layout_graph_binding"

    # Attributes
    experience_name: str
    layout_binding_key: str
    activation_scope: ExperienceSectionGraphBindingActivationScope | None = Field(default=None)
    rationale: str | None = Field(default=None)
    section_title: str | None = Field(default=None)
    section_description: str | None = Field(default=None)
    focus_scope_title: str | None = Field(default=None)
    focus_scope_description: str | None = Field(default=None)


class ActivateExperienceLayoutGraphBindingResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["activate_experience_layout_graph_binding"] = "activate_experience_layout_graph_binding"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    state: ExperienceLayoutGraphBindingState


class ExperienceViewEventTransitionTrigger(BaseModel):
    # Attributes
    source_view_ref: str | None = Field(default=None)
    event_id: UUID | None = Field(default=None)
    event_type: str
    action_intent_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)


class ExperienceViewEventTransitionTarget(BaseModel):
    # Attributes
    target_view_ref: str
    target_binding_key: str
    target_section_key: str | None = Field(default=None)
    target_graph_identity_ref: str | None = Field(default=None)
    section_view: ExperienceSectionViewResolution | None = Field(default=None)


class ExperienceViewEventTransitionReceipt(BaseModel):
    # Attributes
    transition_key: str
    experience_name: str
    trigger: ExperienceViewEventTransitionTrigger
    target: ExperienceViewEventTransitionTarget
    state: ExperienceSectionGraphBindingState
    info: str | None = Field(default=None)


class ApplyExperienceViewEventTransitionRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["apply_experience_view_event_transition"] = "apply_experience_view_event_transition"

    # Attributes
    experience_name: str
    profile_key: str | None = Field(default=None)
    transition_key: str
    source_view_ref: str | None = Field(default=None)
    event_id: UUID | None = Field(default=None)
    event_type: str
    action_intent_id: UUID | None = Field(default=None)
    action_type: str | None = Field(default=None)
    target_view_ref: str | None = Field(default=None)
    target_binding_key: str | None = Field(default=None)
    target_section_key: str | None = Field(default=None)
    target_graph_identity_ref: str | None = Field(default=None)
    activation_scope: ExperienceSectionGraphBindingActivationScope | None = Field(default=None)
    rationale: str | None = Field(default=None)
    section_title: str | None = Field(default=None)
    section_description: str | None = Field(default=None)
    focus_scope_title: str | None = Field(default=None)
    focus_scope_description: str | None = Field(default=None)


class ApplyExperienceViewEventTransitionResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["apply_experience_view_event_transition"] = "apply_experience_view_event_transition"

    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    receipt: ExperienceViewEventTransitionReceipt
    state: ExperienceSectionGraphBindingState


class RecordExperienceViewInvocationActionRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["record_experience_view_invocation_action"] = "record_experience_view_invocation_action"

    # Attributes
    experience_name: str
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class RecordExperienceViewInvocationActionResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["record_experience_view_invocation_action"] = "record_experience_view_invocation_action"

    # Attributes
    experience_name: str
    receipt: ExperienceViewInvocationActionReceipt


class InvokeExperienceViewInvocationActionRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["invoke_experience_view_invocation_action"] = "invoke_experience_view_invocation_action"

    # Attributes
    experience_name: str
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    admitted_actor_role_bindings: list[ExperienceActorConfigRoleAdmissionBinding] = Field(default_factory=list)
    admission_evidence: JsonObject = Field(default_factory=JsonObject)
    request_payload: JsonObject = Field(default_factory=JsonObject)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)


class InvokeExperienceViewInvocationActionResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["invoke_experience_view_invocation_action"] = "invoke_experience_view_invocation_action"

    # Attributes
    experience_name: str
    receipt: ExperienceViewInvocationActionReceipt | None = Field(default=None)
    admission_preflight: ExperienceInvocationActionAdmissionPreflight | None = Field(default=None)
    api_dispatch_receipt: ExperienceViewInvocationActionApiDispatchReceipt | None = Field(default=None)
    response_payload: JsonValue | None = Field(default=None)


class ResolveExperienceInvocationActionRolePolicyRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_experience_invocation_action_role_policy"] = (
        "resolve_experience_invocation_action_role_policy"
    )

    # Attributes
    experience_name: str
    experience_invocation_action_config_id: UUID
    action_key: str | None = Field(default=None)


class ResolveExperienceInvocationActionRolePolicyResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_experience_invocation_action_role_policy"] = (
        "resolve_experience_invocation_action_role_policy"
    )

    # Attributes
    experience_name: str
    accepted: bool = Field(default=False)
    status: str
    resolution: ExperienceInvocationActionRolePolicyResolution


class WatchExperienceSectionGraphBindingsRequest(ExperienceSectionGraphBindingServiceRequest):
    # Discriminator Tag
    operation: Literal["watch_experience_section_graph_bindings"] = "watch_experience_section_graph_bindings"

    # Attributes
    experience_name: str
    section_keys: list[str] = Field(default_factory=list)
    binding_keys: list[str] = Field(default_factory=list)
    poll_interval_ms: int = Field(default=1000)


class WatchExperienceSectionGraphBindingsResponse(ExperienceSectionGraphBindingServiceResponse):
    # Discriminator Tag
    operation: Literal["watch_experience_section_graph_bindings"] = "watch_experience_section_graph_bindings"

    # Attributes
    experience_name: str
    snapshot: ExperienceSectionGraphBindingStateSnapshot
