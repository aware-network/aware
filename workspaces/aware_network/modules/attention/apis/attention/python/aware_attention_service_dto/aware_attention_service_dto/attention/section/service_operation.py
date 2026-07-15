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

if TYPE_CHECKING:
    from aware_attention_service_dto.attention.section.models import AttentionEnvironmentRuntimeTarget
    from aware_attention_service_dto.attention.section.models import AttentionFocusScopeCommitPin
    from aware_attention_service_dto.attention.section.models import AttentionRuntimeMountLayoutRequest
    from aware_attention_service_dto.attention.section.models import AttentionRuntimeMountSnapshot
    from aware_attention_service_dto.attention.section.models import AttentionSectionFocusTarget
    from aware_attention_service_dto.attention.section.models import AttentionSectionSnapshot


class AttentionSectionServiceRequest(BaseModel):
    """
    Canonical request/response DTOs for the Attention section service boundary.
    These are transport-level service payloads. They do not replace SSOT graph state.
    SSOT: `attention-service-dto` generated from `workspaces/aware_network/modules/attention/apis/attention/dto`.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "get_attention_section_state": "aware_attention_service_dto.attention.section.service_operation.GetAttentionSectionStateRequest",
        "activate_attention_section_observable": "aware_attention_service_dto.attention.section.service_operation.ActivateAttentionSectionObservableRequest",
        "get_attention_focus_scope_commits": "aware_attention_service_dto.attention.section.service_operation.GetAttentionFocusScopeCommitsRequest",
        "get_attention_runtime_mount": "aware_attention_service_dto.attention.section.service_operation.GetAttentionRuntimeMountRequest",
        "watch_attention_runtime_mount": "aware_attention_service_dto.attention.section.service_operation.WatchAttentionRuntimeMountRequest",
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
            return UnknownAttentionSectionServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownAttentionSectionServiceRequest(AttentionSectionServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class AttentionSectionServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    snapshot: AttentionSectionSnapshot | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "get_attention_section_state": "aware_attention_service_dto.attention.section.service_operation.GetAttentionSectionStateResponse",
        "activate_attention_section_observable": "aware_attention_service_dto.attention.section.service_operation.ActivateAttentionSectionObservableResponse",
        "get_attention_focus_scope_commits": "aware_attention_service_dto.attention.section.service_operation.GetAttentionFocusScopeCommitsResponse",
        "get_attention_runtime_mount": "aware_attention_service_dto.attention.section.service_operation.GetAttentionRuntimeMountResponse",
        "watch_attention_runtime_mount": "aware_attention_service_dto.attention.section.service_operation.WatchAttentionRuntimeMountResponse",
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
            return UnknownAttentionSectionServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownAttentionSectionServiceResponse(AttentionSectionServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class GetAttentionSectionStateRequest(AttentionSectionServiceRequest):
    """Read the current Attention-owned section focus-scope state for one section key."""

    # Discriminator Tag
    operation: Literal["get_attention_section_state"] = "get_attention_section_state"

    # Attributes
    section_key: str
    default_observable_id: UUID | None = Field(default=None)
    default_rationale: str | None = Field(default=None)


class GetAttentionSectionStateResponse(AttentionSectionServiceResponse):
    # Discriminator Tag
    operation: Literal["get_attention_section_state"] = "get_attention_section_state"

    # Attributes
    snapshot: AttentionSectionSnapshot


class AttentionSectionActivationScope(BaseModel):
    # Attributes
    window_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    state_projection_hash: str | None = Field(default=None)
    focus_target: AttentionSectionFocusTarget | None = Field(default=None)


class ActivateAttentionSectionObservableRequest(AttentionSectionServiceRequest):
    """Activate one observable for one section-scoped focus scope."""

    # Discriminator Tag
    operation: Literal["activate_attention_section_observable"] = "activate_attention_section_observable"

    # Attributes
    section_key: str
    observable_id: UUID
    activation_scope: AttentionSectionActivationScope | None = Field(default=None)
    rationale: str | None = Field(default=None)
    section_title: str | None = Field(default=None)
    section_description: str | None = Field(default=None)
    focus_scope_title: str | None = Field(default=None)
    focus_scope_description: str | None = Field(default=None)


class ActivateAttentionSectionObservableResponse(AttentionSectionServiceResponse):
    # Discriminator Tag
    operation: Literal["activate_attention_section_observable"] = "activate_attention_section_observable"

    # Attributes
    snapshot: AttentionSectionSnapshot


class GetAttentionFocusScopeCommitsRequest(AttentionSectionServiceRequest):
    """List committed OIG commit pointers observed by one Attention focus scope."""

    # Discriminator Tag
    operation: Literal["get_attention_focus_scope_commits"] = "get_attention_focus_scope_commits"

    # Attributes
    focus_scope_id: UUID
    focus_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    limit: int | None = Field(default=None)


class GetAttentionFocusScopeCommitsResponse(AttentionSectionServiceResponse):
    # Discriminator Tag
    operation: Literal["get_attention_focus_scope_commits"] = "get_attention_focus_scope_commits"

    # Attributes
    focus_scope_id: UUID
    exists: bool = Field(default=False)
    commits: list[AttentionFocusScopeCommitPin] = Field(default_factory=list)


class GetAttentionRuntimeMountRequest(AttentionSectionServiceRequest):
    """Read Attention-owned section state for one Attention-selected runtime layout."""

    # Discriminator Tag
    operation: Literal["get_attention_runtime_mount"] = "get_attention_runtime_mount"

    # Attributes
    window_key: str | None = Field(default=None)
    environment_target: AttentionEnvironmentRuntimeTarget | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    preferred_layout_config_id: UUID | None = Field(default=None)
    preferred_layout_key: str | None = Field(default=None)
    preferred_section_key: str | None = Field(default=None)
    preferred_observable_id: UUID | None = Field(default=None)
    layouts: list[AttentionRuntimeMountLayoutRequest] = Field(default_factory=list)


class GetAttentionRuntimeMountResponse(AttentionSectionServiceResponse):
    # Discriminator Tag
    operation: Literal["get_attention_runtime_mount"] = "get_attention_runtime_mount"

    # Attributes
    runtime_mount: AttentionRuntimeMountSnapshot


class WatchAttentionRuntimeMountRequest(AttentionSectionServiceRequest):
    """Subscribe to streamed Attention-owned runtime mount updates for one mounted window/layout set."""

    # Discriminator Tag
    operation: Literal["watch_attention_runtime_mount"] = "watch_attention_runtime_mount"

    # Attributes
    window_key: str | None = Field(default=None)
    environment_target: AttentionEnvironmentRuntimeTarget | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    preferred_layout_config_id: UUID | None = Field(default=None)
    preferred_layout_key: str | None = Field(default=None)
    preferred_section_key: str | None = Field(default=None)
    preferred_observable_id: UUID | None = Field(default=None)
    poll_interval_ms: int = Field(default=1000)
    layouts: list[AttentionRuntimeMountLayoutRequest] = Field(default_factory=list)


class WatchAttentionRuntimeMountResponse(AttentionSectionServiceResponse):
    # Discriminator Tag
    operation: Literal["watch_attention_runtime_mount"] = "watch_attention_runtime_mount"

    # Attributes
    runtime_mount: AttentionRuntimeMountSnapshot
