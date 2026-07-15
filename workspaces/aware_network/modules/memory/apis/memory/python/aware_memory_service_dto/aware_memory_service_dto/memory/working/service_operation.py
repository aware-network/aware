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

# Reactivity Service Dto
from aware_reactivity_service_dto.reactivity.event_meaning import ReactivityEventMeaningResolutionResult

if TYPE_CHECKING:
    from aware_memory_service_dto.memory.working.models import AttentionTransitionValidationEvidence
    from aware_memory_service_dto.memory.working.models import MemoryActorContextEvidence
    from aware_memory_service_dto.memory.working.models import MemoryActorContextFrame
    from aware_memory_service_dto.memory.working.models import MemoryActorContextSnapshot
    from aware_memory_service_dto.memory.working.models import MemoryEventActionProvenanceEvidence
    from aware_memory_service_dto.memory.working.models import MemoryResolvedEventMeaningEvidence
    from aware_memory_service_dto.memory.working.models import MemoryWorkingCommitReceipt
    from aware_memory_service_dto.memory.working.models import MemoryWorkingItemEvidence
    from aware_memory_service_dto.memory.working.models import MemoryWorkingItemPin
    from aware_memory_service_dto.memory.working.models import MemoryWorkingPin


class MemoryWorkingServiceRequest(BaseModel):
    """
    Request/response DTOs for Memory Working service operations.
    V0 is intentionally scoped to working memory. Semantic, episodic,
    procedural search, event subscription, and Actor-Action models are later
    lanes.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ensure_memory_working": "aware_memory_service_dto.memory.working.service_operation.EnsureMemoryWorkingRequest",
        "describe_memory_working": "aware_memory_service_dto.memory.working.service_operation.DescribeMemoryWorkingRequest",
        "list_memory_working_items": "aware_memory_service_dto.memory.working.service_operation.ListMemoryWorkingItemsRequest",
        "validate_memory_working_item": "aware_memory_service_dto.memory.working.service_operation.ValidateMemoryWorkingItemRequest",
        "resolve_memory_context": "aware_memory_service_dto.memory.working.service_operation.ResolveMemoryContextRequest",
        "resolve_actor_memory_context": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextRequest",
        "watch_actor_memory_context": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextRequest",
        "resolve_actor_memory_context_frame": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextFrameRequest",
        "watch_actor_memory_context_frame": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextFrameRequest",
        "remember_attention_transition": "aware_memory_service_dto.memory.working.service_operation.RememberAttentionTransitionRequest",
        "remember_content": "aware_memory_service_dto.memory.working.service_operation.RememberContentRequest",
        "remember_event": "aware_memory_service_dto.memory.working.service_operation.RememberEventRequest",
        "record_resolved_event_meaning": "aware_memory_service_dto.memory.working.service_operation.RecordResolvedEventMeaningRequest",
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
            return UnknownMemoryWorkingServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownMemoryWorkingServiceRequest(MemoryWorkingServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class MemoryWorkingServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ensure_memory_working": "aware_memory_service_dto.memory.working.service_operation.EnsureMemoryWorkingResponse",
        "describe_memory_working": "aware_memory_service_dto.memory.working.service_operation.DescribeMemoryWorkingResponse",
        "list_memory_working_items": "aware_memory_service_dto.memory.working.service_operation.ListMemoryWorkingItemsResponse",
        "validate_memory_working_item": "aware_memory_service_dto.memory.working.service_operation.ValidateMemoryWorkingItemResponse",
        "resolve_memory_context": "aware_memory_service_dto.memory.working.service_operation.ResolveMemoryContextResponse",
        "resolve_actor_memory_context": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextResponse",
        "watch_actor_memory_context": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextResponse",
        "resolve_actor_memory_context_frame": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextFrameResponse",
        "watch_actor_memory_context_frame": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextFrameResponse",
        "remember_attention_transition": "aware_memory_service_dto.memory.working.service_operation.RememberAttentionTransitionResponse",
        "remember_content": "aware_memory_service_dto.memory.working.service_operation.RememberContentResponse",
        "remember_event": "aware_memory_service_dto.memory.working.service_operation.RememberEventResponse",
        "record_resolved_event_meaning": "aware_memory_service_dto.memory.working.service_operation.RecordResolvedEventMeaningResponse",
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
            return UnknownMemoryWorkingServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownMemoryWorkingServiceResponse(MemoryWorkingServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class EnsureMemoryWorkingRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["ensure_memory_working"] = "ensure_memory_working"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")


class EnsureMemoryWorkingResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["ensure_memory_working"] = "ensure_memory_working"

    # Attributes
    memory_working: MemoryWorkingPin
    receipt: MemoryWorkingCommitReceipt | None = Field(default=None)


class DescribeMemoryWorkingRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["describe_memory_working"] = "describe_memory_working"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")


class DescribeMemoryWorkingResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_memory_working"] = "describe_memory_working"

    # Attributes
    exists: bool = Field(default=False)
    memory_working: MemoryWorkingPin | None = Field(default=None)


class ListMemoryWorkingItemsRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["list_memory_working_items"] = "list_memory_working_items"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)


class ListMemoryWorkingItemsResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["list_memory_working_items"] = "list_memory_working_items"

    # Attributes
    memory_working: MemoryWorkingPin | None = Field(default=None)
    items: list[MemoryWorkingItemPin] = Field(default_factory=list)


class ValidateMemoryWorkingItemRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["validate_memory_working_item"] = "validate_memory_working_item"

    # Attributes
    memory_working_item_id: UUID
    expected_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_sources: bool = Field(default=True)


class ValidateMemoryWorkingItemResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_memory_working_item"] = "validate_memory_working_item"

    # Attributes
    evidence: MemoryWorkingItemEvidence | None = Field(default=None)


class ResolveMemoryContextRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_memory_context"] = "resolve_memory_context"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    expected_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_sources: bool = Field(default=True)
    include_unusable: bool = Field(default=True)


class ResolveMemoryContextResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_memory_context"] = "resolve_memory_context"

    # Attributes
    exists: bool = Field(default=False)
    memory_working: MemoryWorkingPin | None = Field(default=None)
    items: list[MemoryWorkingItemEvidence] = Field(default_factory=list)
    usable_item_count: int = Field(default=0)
    unresolved_item_count: int = Field(default=0)


class ResolveActorMemoryContextRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_actor_memory_context"] = "resolve_actor_memory_context"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    parent_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_identity: bool = Field(default=True)
    validate_sources: bool = Field(default=True)
    include_unusable: bool = Field(default=True)


class ResolveActorMemoryContextResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_actor_memory_context"] = "resolve_actor_memory_context"

    # Attributes
    actor_context: MemoryActorContextEvidence
    exists: bool = Field(default=False)
    memory_working: MemoryWorkingPin | None = Field(default=None)
    items: list[MemoryWorkingItemEvidence] = Field(default_factory=list)
    usable_item_count: int = Field(default=0)
    unresolved_item_count: int = Field(default=0)


class WatchActorMemoryContextRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["watch_actor_memory_context"] = "watch_actor_memory_context"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    parent_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_identity: bool = Field(default=True)
    validate_sources: bool = Field(default=True)
    include_unusable: bool = Field(default=True)
    known_cursor: str | None = Field(default=None)
    known_digest: str | None = Field(default=None)


class WatchActorMemoryContextResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["watch_actor_memory_context"] = "watch_actor_memory_context"

    # Attributes
    snapshot: MemoryActorContextSnapshot
    changed: bool = Field(default=True)


class ResolveActorMemoryContextFrameRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_actor_memory_context_frame"] = "resolve_actor_memory_context_frame"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    parent_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_identity: bool = Field(default=True)
    validate_sources: bool = Field(default=True)
    include_unusable: bool = Field(default=True)


class ResolveActorMemoryContextFrameResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_actor_memory_context_frame"] = "resolve_actor_memory_context_frame"

    # Attributes
    frame: MemoryActorContextFrame
    changed: bool = Field(default=True)


class WatchActorMemoryContextFrameRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["watch_actor_memory_context_frame"] = "watch_actor_memory_context_frame"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    parent_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    validate_identity: bool = Field(default=True)
    validate_sources: bool = Field(default=True)
    include_unusable: bool = Field(default=True)
    known_cursor: str | None = Field(default=None)
    known_digest: str | None = Field(default=None)


class WatchActorMemoryContextFrameResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["watch_actor_memory_context_frame"] = "watch_actor_memory_context_frame"

    # Attributes
    frame: MemoryActorContextFrame
    changed: bool = Field(default=True)


class RememberAttentionTransitionRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["remember_attention_transition"] = "remember_attention_transition"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    attention_focus_transition_id: UUID
    expected_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class RememberAttentionTransitionResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["remember_attention_transition"] = "remember_attention_transition"

    # Attributes
    memory_working: MemoryWorkingPin
    item: MemoryWorkingItemPin | None = Field(default=None)
    attention_validation: AttentionTransitionValidationEvidence
    receipt: MemoryWorkingCommitReceipt | None = Field(default=None)


class RememberContentRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["remember_content"] = "remember_content"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    content_id: UUID
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class RememberContentResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["remember_content"] = "remember_content"

    # Attributes
    memory_working: MemoryWorkingPin
    item: MemoryWorkingItemPin | None = Field(default=None)
    receipt: MemoryWorkingCommitReceipt | None = Field(default=None)


class RememberEventRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["remember_event"] = "remember_event"

    # Attributes
    memory_working_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    event_id: UUID
    event_config_id: UUID | None = Field(default=None)
    event_activation_id: UUID | None = Field(default=None)
    event_type: str | None = Field(default=None)
    event_source: str | None = Field(default=None)
    event_status: str | None = Field(default=None)
    commit_branch_id: UUID | None = Field(default=None)
    commit_projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    intent_key: str | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_execution_key: str | None = Field(default=None)
    api_call_key: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_experience_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_event_id: UUID | None = Field(default=None)
    invocation_config_id: UUID | None = Field(default=None)
    endpoint_id: UUID | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class RememberEventResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["remember_event"] = "remember_event"

    # Attributes
    memory_working: MemoryWorkingPin
    memory_working_item_id: UUID | None = Field(default=None)
    item: MemoryWorkingItemPin | None = Field(default=None)
    event_action_provenance: MemoryEventActionProvenanceEvidence | None = Field(default=None)
    receipt: MemoryWorkingCommitReceipt | None = Field(default=None)


class RecordResolvedEventMeaningRequest(MemoryWorkingServiceRequest):
    # Discriminator Tag
    operation: Literal["record_resolved_event_meaning"] = "record_resolved_event_meaning"

    # Attributes
    actor_id: UUID | None = Field(default=None)
    memory_working_item_id: UUID
    resolved_meaning: ReactivityEventMeaningResolutionResult
    resolver_status: str
    resolver_endpoint_ref: str
    resolver_discriminant: str
    resolver_program_impl_instruction_intent_id: UUID
    resolver_action_config_id: UUID
    resolver_api_capability_endpoint_id: UUID
    resolver_api_call_id: UUID
    resolver_api_call_key: UUID
    resolver_request_model_id: UUID
    resolver_api_call_outcome_id: UUID
    resolver_response_model_id: UUID
    resolver_response_class_config_id: UUID
    resolver_service_operation_id: UUID
    resolver_service_operation_config_id: UUID
    resolver_service_operation_commit_id: UUID
    resolver_service_operation_head_commit_id: UUID
    resolver_service_operation_branch_id: UUID
    resolver_service_operation_projection_hash: str
    resolver_api_call_outcome_commit_id: UUID
    resolver_api_call_outcome_head_commit_id: UUID
    resolver_api_call_outcome_branch_id: UUID
    resolver_api_call_outcome_projection_hash: str


class RecordResolvedEventMeaningResponse(MemoryWorkingServiceResponse):
    # Discriminator Tag
    operation: Literal["record_resolved_event_meaning"] = "record_resolved_event_meaning"

    # Attributes
    memory_working: MemoryWorkingPin | None = Field(default=None)
    item: MemoryWorkingItemPin | None = Field(default=None)
    resolved_event_meaning: MemoryResolvedEventMeaningEvidence
    receipt: MemoryWorkingCommitReceipt | None = Field(default=None)
