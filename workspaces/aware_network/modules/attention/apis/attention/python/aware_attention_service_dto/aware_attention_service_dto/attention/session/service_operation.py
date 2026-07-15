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
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_service_dto.attention.session.models import AttentionFocusTransitionPin
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTopologyTransitionPin
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTopologyTransitionSectionInput
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTransitionPin
    from aware_attention_service_dto.attention.session.models import AttentionLayoutTransitionSectionInput
    from aware_attention_service_dto.attention.session.models import AttentionSessionLayoutPin
    from aware_attention_service_dto.attention.session.models import AttentionSessionPin
    from aware_attention_service_dto.attention.session.models import AttentionSessionSectionPin
    from aware_attention_service_dto.attention.session.models import AttentionTransitionValidationResult


class AttentionSessionServiceRequest(BaseModel):
    """
    Request/response DTOs for Attention session transition reads.
    These operations expose read/validation value over existing Attention
    ontology truth. They do not authorize actors and do not persist frames.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "start_attention_session": "aware_attention_service_dto.attention.session.service_operation.StartAttentionSessionRequest",
        "mount_attention_session_layout": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionLayoutRequest",
        "mount_attention_session_section": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionSectionRequest",
        "describe_attention_session": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionSessionRequest",
        "apply_attention_session_layout_topology_transition": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTopologyTransitionRequest",
        "apply_attention_session_layout_transition": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTransitionRequest",
        "describe_attention_transition": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionTransitionRequest",
        "list_attention_transitions": "aware_attention_service_dto.attention.session.service_operation.ListAttentionTransitionsRequest",
        "validate_attention_transition": "aware_attention_service_dto.attention.session.service_operation.ValidateAttentionTransitionRequest",
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
            return UnknownAttentionSessionServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownAttentionSessionServiceRequest(AttentionSessionServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class AttentionSessionServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "start_attention_session": "aware_attention_service_dto.attention.session.service_operation.StartAttentionSessionResponse",
        "mount_attention_session_layout": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionLayoutResponse",
        "mount_attention_session_section": "aware_attention_service_dto.attention.session.service_operation.MountAttentionSessionSectionResponse",
        "describe_attention_session": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionSessionResponse",
        "apply_attention_session_layout_topology_transition": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTopologyTransitionResponse",
        "apply_attention_session_layout_transition": "aware_attention_service_dto.attention.session.service_operation.ApplyAttentionSessionLayoutTransitionResponse",
        "describe_attention_transition": "aware_attention_service_dto.attention.session.service_operation.DescribeAttentionTransitionResponse",
        "list_attention_transitions": "aware_attention_service_dto.attention.session.service_operation.ListAttentionTransitionsResponse",
        "validate_attention_transition": "aware_attention_service_dto.attention.session.service_operation.ValidateAttentionTransitionResponse",
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
            return UnknownAttentionSessionServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownAttentionSessionServiceResponse(AttentionSessionServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class StartAttentionSessionRequest(AttentionSessionServiceRequest):
    """Construct one AttentionSession over an already committed Identity Session."""

    # Discriminator Tag
    operation: Literal["start_attention_session"] = "start_attention_session"

    # Attributes
    identity_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class StartAttentionSessionResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["start_attention_session"] = "start_attention_session"

    # Attributes
    attention_session_id: UUID
    identity_session_id: UUID
    status: str
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class MountAttentionSessionLayoutRequest(AttentionSessionServiceRequest):
    """Mount one Attention-owned Layout on an existing AttentionSession lane."""

    # Discriminator Tag
    operation: Literal["mount_attention_session_layout"] = "mount_attention_session_layout"

    # Attributes
    attention_session_id: UUID
    layout_id: UUID
    layout_config_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class MountAttentionSessionLayoutResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["mount_attention_session_layout"] = "mount_attention_session_layout"

    # Attributes
    attention_session_id: UUID
    attention_session_layout_id: UUID
    layout_id: UUID
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class MountAttentionSessionSectionRequest(AttentionSessionServiceRequest):
    """Mount one Attention-owned Section anchor on an existing session layout."""

    # Discriminator Tag
    operation: Literal["mount_attention_session_section"] = "mount_attention_session_section"

    # Attributes
    attention_session_id: UUID
    attention_session_layout_id: UUID
    layout_section_id: UUID
    section_id: UUID
    section_key: str | None = Field(default=None)
    order: int = Field(default=0)
    is_active: bool = Field(default=True)


class MountAttentionSessionSectionResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["mount_attention_session_section"] = "mount_attention_session_section"

    # Attributes
    attention_session_id: UUID
    attention_session_layout_id: UUID
    attention_session_section_id: UUID
    layout_section_id: UUID
    section_id: UUID
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class DescribeAttentionSessionRequest(AttentionSessionServiceRequest):
    # Discriminator Tag
    operation: Literal["describe_attention_session"] = "describe_attention_session"

    # Attributes
    attention_session_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)


class DescribeAttentionSessionResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_attention_session"] = "describe_attention_session"

    # Attributes
    session: AttentionSessionPin | None = Field(default=None)
    layouts: list[AttentionSessionLayoutPin] = Field(default_factory=list)
    active_layout: AttentionSessionLayoutPin | None = Field(default=None)
    active_section: AttentionSessionSectionPin | None = Field(default=None)
    active_transition: AttentionFocusTransitionPin | None = Field(default=None)
    active_layout_transition: AttentionLayoutTransitionPin | None = Field(default=None)
    active_layout_topology_transition: AttentionLayoutTopologyTransitionPin | None = Field(default=None)


class ApplyAttentionSessionLayoutTopologyTransitionRequest(AttentionSessionServiceRequest):
    """
    Commit one complete active-membership/order vector over stable admitted
    AttentionSessionSection anchors.
    """

    # Discriminator Tag
    operation: Literal["apply_attention_session_layout_topology_transition"] = (
        "apply_attention_session_layout_topology_transition"
    )

    # Attributes
    attention_session_id: UUID
    attention_session_layout_id: UUID
    client_intent_id: str
    expected_previous_topology_transition_id: UUID | None = Field(default=None)
    section_states: list[AttentionLayoutTopologyTransitionSectionInput] = Field(default_factory=list)
    transition_kind: str = Field(default="topology")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class ApplyAttentionSessionLayoutTopologyTransitionResponse(AttentionSessionServiceResponse):
    """`outcome` is one of `committed`, `idempotent`, or `conflict`."""

    # Discriminator Tag
    operation: Literal["apply_attention_session_layout_topology_transition"] = (
        "apply_attention_session_layout_topology_transition"
    )

    # Attributes
    outcome: str
    conflict_reason: str | None = Field(default=None)
    transition: AttentionLayoutTopologyTransitionPin | None = Field(default=None)
    latest_transition: AttentionLayoutTopologyTransitionPin | None = Field(default=None)


class ApplyAttentionSessionLayoutTransitionRequest(AttentionSessionServiceRequest):
    """Commit one complete shared-layout vector through AttentionSessionLayout."""

    # Discriminator Tag
    operation: Literal["apply_attention_session_layout_transition"] = "apply_attention_session_layout_transition"

    # Attributes
    attention_session_id: UUID
    attention_session_layout_id: UUID
    client_intent_id: str
    expected_previous_layout_transition_id: UUID | None = Field(default=None)
    topology_transition_id: UUID | None = Field(default=None)
    section_states: list[AttentionLayoutTransitionSectionInput] = Field(default_factory=list)
    transition_kind: str = Field(default="layout")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class ApplyAttentionSessionLayoutTransitionResponse(AttentionSessionServiceResponse):
    """
    `outcome` is one of `committed`, `idempotent`, or `conflict`.
    Conflict responses fail closed and include the latest committed transition
    so clients can reconcile without a hidden retry.
    """

    # Discriminator Tag
    operation: Literal["apply_attention_session_layout_transition"] = "apply_attention_session_layout_transition"

    # Attributes
    outcome: str
    conflict_reason: str | None = Field(default=None)
    transition: AttentionLayoutTransitionPin | None = Field(default=None)
    latest_transition: AttentionLayoutTransitionPin | None = Field(default=None)
    latest_topology_transition: AttentionLayoutTopologyTransitionPin | None = Field(default=None)


class DescribeAttentionTransitionRequest(AttentionSessionServiceRequest):
    # Discriminator Tag
    operation: Literal["describe_attention_transition"] = "describe_attention_transition"

    # Attributes
    attention_focus_transition_id: UUID


class DescribeAttentionTransitionResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["describe_attention_transition"] = "describe_attention_transition"

    # Attributes
    exists: bool = Field(default=False)
    transition: AttentionFocusTransitionPin | None = Field(default=None)


class ListAttentionTransitionsRequest(AttentionSessionServiceRequest):
    # Discriminator Tag
    operation: Literal["list_attention_transitions"] = "list_attention_transitions"

    # Attributes
    attention_session_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    attention_session_section_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    transition_kind: str | None = Field(default=None)
    limit: int | None = Field(default=None)


class ListAttentionTransitionsResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["list_attention_transitions"] = "list_attention_transitions"

    # Attributes
    transitions: list[AttentionFocusTransitionPin] = Field(default_factory=list)


class ValidateAttentionTransitionRequest(AttentionSessionServiceRequest):
    # Discriminator Tag
    operation: Literal["validate_attention_transition"] = "validate_attention_transition"

    # Attributes
    attention_focus_transition_id: UUID
    expected_identity_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)


class ValidateAttentionTransitionResponse(AttentionSessionServiceResponse):
    # Discriminator Tag
    operation: Literal["validate_attention_transition"] = "validate_attention_transition"

    # Attributes
    validation: AttentionTransitionValidationResult
