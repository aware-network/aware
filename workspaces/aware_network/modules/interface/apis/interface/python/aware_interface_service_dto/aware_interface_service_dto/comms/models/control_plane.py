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
    SerializeAsAny,
    field_validator,
    model_validator,
)

# Environment Service Dto
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
    EnvironmentSessionView,
)

# Experience Service Dto
from aware_experience_service_dto.experience.actor_admission.models import ExperienceActorConfigAdmissionReceipt

# Types
from aware_types import (
    JsonObject,
    JsonValue,
)

if TYPE_CHECKING:
    from aware_interface_service_dto.comms.models.hosted_interface_namespace import HostedInterfaceNamespace
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceAppScreenState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceEnvironmentAdmissionState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceEnvironmentNavigationState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceEnvironmentSessionState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceExperienceLensState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceHostState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceHostViewStateCursorState
    from aware_interface_service_dto.comms.models.interface_host_state import InterfaceRendererCapabilitiesState


class InterfaceControlPlaneOperation(BaseModel):
    """
    Canonical local control-plane DTOs for the Interface daemon.
    This package is local-machine scoped:
    - not a remote API rail
    - not graph/ORM SSOT
    - generated from `.aware` so `services/interface`, textual clients, and
    future CLI clients share one request/response vocabulary
    """

    # Attributes
    request: SerializeAsAny[InterfaceControlPlaneRequest] | None = Field(default=None)
    response: SerializeAsAny[InterfaceControlPlaneResponse] | None = Field(default=None)
    notification: SerializeAsAny[InterfaceControlPlaneNotification] | None = Field(default=None)

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):
        if v is None:
            return None
        return InterfaceControlPlaneRequest.parse(v)

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):
        if v is None:
            return None
        return InterfaceControlPlaneResponse.parse(v)

    @field_validator("notification", mode="before")
    @classmethod
    def _parse_notification(cls, v):
        if v is None:
            return None
        return InterfaceControlPlaneNotification.parse(v)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                    self.notification,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response, notification must be set")
        return self


class InterfaceControlPlaneRequest(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    protocol_version: int = Field(default=1)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ping": "aware_interface_service_dto.comms.models.control_plane.PingRequest",
        "namespace_ensure": "aware_interface_service_dto.comms.models.control_plane.NamespaceEnsureRequest",
        "namespace_list": "aware_interface_service_dto.comms.models.control_plane.NamespaceListRequest",
        "interface_status": "aware_interface_service_dto.comms.models.control_plane.InterfaceStatusRequest",
        "interface_admit_environment_actor": "aware_interface_service_dto.comms.models.control_plane.InterfaceAdmitEnvironmentActorRequest",
        "interface_join_environment_session": "aware_interface_service_dto.comms.models.control_plane.InterfaceJoinEnvironmentSessionRequest",
        "interface_select_environment_navigation_target": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectEnvironmentNavigationTargetRequest",
        "interface_enter_environment": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterEnvironmentRequest",
        "interface_resolve_experience_lens": "aware_interface_service_dto.comms.models.control_plane.InterfaceResolveExperienceLensRequest",
        "interface_action": "aware_interface_service_dto.comms.models.control_plane.InterfaceActionRequest",
        "interface_select_step": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectStepRequest",
        "interface_select_profile": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectProfileRequest",
        "interface_select_runtime_layout": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectRuntimeLayoutRequest",
        "interface_activate_runtime_focus": "aware_interface_service_dto.comms.models.control_plane.InterfaceActivateRuntimeFocusRequest",
        "interface_request_window_layout": "aware_interface_service_dto.comms.models.control_plane.InterfaceRequestWindowLayoutRequest",
        "interface_apply_attention_layout_transition": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTransitionRequest",
        "interface_apply_attention_layout_topology_transition": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
        "interface_report_renderer_capabilities": "aware_interface_service_dto.comms.models.control_plane.InterfaceReportRendererCapabilitiesRequest",
        "interface_sync_view_state_cursor": "aware_interface_service_dto.comms.models.control_plane.InterfaceSyncViewStateCursorRequest",
        "interface_follow": "aware_interface_service_dto.comms.models.control_plane.InterfaceFollowRequest",
        "interface_invoke_api": "aware_interface_service_dto.comms.models.control_plane.InterfaceInvokeApiRequest",
        "interface_stream_api": "aware_interface_service_dto.comms.models.control_plane.InterfaceStreamApiRequest",
        "interface_stop": "aware_interface_service_dto.comms.models.control_plane.InterfaceStopRequest",
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
            return UnknownInterfaceControlPlaneRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownInterfaceControlPlaneRequest(InterfaceControlPlaneRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class InterfaceControlPlaneResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    protocol_version: int = Field(default=1)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ping": "aware_interface_service_dto.comms.models.control_plane.PingResponse",
        "namespace_ensure": "aware_interface_service_dto.comms.models.control_plane.NamespaceEnsureResponse",
        "namespace_list": "aware_interface_service_dto.comms.models.control_plane.NamespaceListResponse",
        "interface_status": "aware_interface_service_dto.comms.models.control_plane.InterfaceStatusResponse",
        "interface_admit_environment_actor": "aware_interface_service_dto.comms.models.control_plane.InterfaceAdmitEnvironmentActorResponse",
        "interface_join_environment_session": "aware_interface_service_dto.comms.models.control_plane.InterfaceJoinEnvironmentSessionResponse",
        "interface_select_environment_navigation_target": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectEnvironmentNavigationTargetResponse",
        "interface_enter_environment": "aware_interface_service_dto.comms.models.control_plane.InterfaceEnterEnvironmentResponse",
        "interface_resolve_experience_lens": "aware_interface_service_dto.comms.models.control_plane.InterfaceResolveExperienceLensResponse",
        "interface_action": "aware_interface_service_dto.comms.models.control_plane.InterfaceActionResponse",
        "interface_select_step": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectStepResponse",
        "interface_select_profile": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectProfileResponse",
        "interface_select_runtime_layout": "aware_interface_service_dto.comms.models.control_plane.InterfaceSelectRuntimeLayoutResponse",
        "interface_activate_runtime_focus": "aware_interface_service_dto.comms.models.control_plane.InterfaceActivateRuntimeFocusResponse",
        "interface_request_window_layout": "aware_interface_service_dto.comms.models.control_plane.InterfaceRequestWindowLayoutResponse",
        "interface_apply_attention_layout_transition": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTransitionResponse",
        "interface_apply_attention_layout_topology_transition": "aware_interface_service_dto.comms.models.control_plane.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
        "interface_report_renderer_capabilities": "aware_interface_service_dto.comms.models.control_plane.InterfaceReportRendererCapabilitiesResponse",
        "interface_sync_view_state_cursor": "aware_interface_service_dto.comms.models.control_plane.InterfaceSyncViewStateCursorResponse",
        "interface_follow": "aware_interface_service_dto.comms.models.control_plane.InterfaceFollowResponse",
        "interface_invoke_api": "aware_interface_service_dto.comms.models.control_plane.InterfaceInvokeApiResponse",
        "interface_stream_api": "aware_interface_service_dto.comms.models.control_plane.InterfaceStreamApiResponse",
        "interface_stop": "aware_interface_service_dto.comms.models.control_plane.InterfaceStopResponse",
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
            return UnknownInterfaceControlPlaneResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownInterfaceControlPlaneResponse(InterfaceControlPlaneResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class InterfaceControlPlaneNotification(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    notification_id: UUID | None = Field(default=None)
    protocol_version: int = Field(default=1)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "interface_state": "aware_interface_service_dto.comms.models.control_plane.InterfaceStateNotification",
        "interface_api_event": "aware_interface_service_dto.comms.models.control_plane.InterfaceApiEventNotification",
        "interface_api_stream_closed": "aware_interface_service_dto.comms.models.control_plane.InterfaceApiStreamClosedNotification",
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
            return UnknownInterfaceControlPlaneNotification.model_validate(v)
        return cls.model_validate(v)


class UnknownInterfaceControlPlaneNotification(InterfaceControlPlaneNotification):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class PingRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["ping"] = "ping"


class PingResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["ping"] = "ping"

    # Attributes
    service: str = Field(default="aware_interface_service")
    status: str = Field(default="ok")
    socket_path: str | None = Field(default=None)
    daemon_instance_id: UUID | None = Field(default=None)
    daemon_started_at: str | None = Field(default=None)
    daemon_source_fingerprint: str | None = Field(default=None)
    repository_root: str | None = Field(default=None)
    state_home: str | None = Field(default=None)
    default_endpoint: str | None = Field(default=None)
    expected_source_fingerprint: str | None = Field(default=None)
    restart_recommended: bool = Field(default=False)
    restart_reason: str | None = Field(default=None)
    namespaces: list[HostedInterfaceNamespace] = Field(default_factory=list)


class NamespaceEnsureRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["namespace_ensure"] = "namespace_ensure"

    # Attributes
    namespace: str
    host_label: str | None = Field(default=None)
    endpoint: str | None = Field(default=None)
    auth_token: str | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)


class NamespaceEnsureResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["namespace_ensure"] = "namespace_ensure"

    # Attributes
    namespace: str
    host_state: InterfaceHostState


class NamespaceListRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["namespace_list"] = "namespace_list"


class NamespaceListResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["namespace_list"] = "namespace_list"

    # Attributes
    namespaces: list[HostedInterfaceNamespace] = Field(default_factory=list)


class InterfaceStatusRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_status"] = "interface_status"

    # Attributes
    namespace: str


class InterfaceStatusResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_status"] = "interface_status"

    # Attributes
    namespace: str
    host_state: InterfaceHostState


class InterfaceSessionStartRequest(InterfaceControlPlaneRequest):
    # Attributes
    operation: str = Field(default="interface_session_start")
    interface_id: UUID
    identity_session_id: UUID
    name: str
    state: str = Field(default="active")


class InterfaceSessionStartResponse(InterfaceControlPlaneResponse):
    # Attributes
    operation: str = Field(default="interface_session_start")
    interface_session_id: UUID | None = Field(default=None)
    interface_id: UUID
    identity_session_id: UUID
    name: str
    state: str
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class InterfaceSessionDescribeRequest(InterfaceControlPlaneRequest):
    # Attributes
    operation: str = Field(default="interface_session_describe")
    interface_session_id: UUID


class InterfaceSessionExperienceSessionView(BaseModel):
    # Attributes
    interface_session_experience_session_id: UUID
    experience_session_id: UUID
    status: str
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    domain_commit_id: UUID


class InterfaceSessionView(BaseModel):
    # Attributes
    interface_session_id: UUID
    interface_id: UUID
    identity_session_id: UUID
    name: str
    state: str
    domain_commit_id: UUID
    experience_sessions: list[InterfaceSessionExperienceSessionView] = Field(default_factory=list)


class InterfaceSessionDescribeResponse(InterfaceControlPlaneResponse):
    # Attributes
    operation: str = Field(default="interface_session_describe")
    status: str
    session: InterfaceSessionView | None = Field(default=None)


class InterfaceExperienceSessionMountRequest(InterfaceControlPlaneRequest):
    # Attributes
    operation: str = Field(default="interface_experience_session_mount")
    interface_session_id: UUID
    experience_session_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class InterfaceExperienceSessionMountResponse(InterfaceControlPlaneResponse):
    # Attributes
    operation: str = Field(default="interface_experience_session_mount")
    interface_session_experience_session_id: UUID
    interface_session_id: UUID
    experience_session_id: UUID
    status: str
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)


class InterfaceAdmitEnvironmentActorRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_admit_environment_actor"] = "interface_admit_environment_actor"

    # Attributes
    namespace: str
    environment_id: UUID | None = Field(default=None)
    environment_profile_id: UUID
    actor_config_id: UUID
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceAdmitEnvironmentActorResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_admit_environment_actor"] = "interface_admit_environment_actor"

    # Attributes
    namespace: str
    environment_admission: InterfaceEnvironmentAdmissionState | None = Field(default=None)
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceJoinEnvironmentSessionRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_join_environment_session"] = "interface_join_environment_session"

    # Attributes
    namespace: str
    environment_session_id: UUID
    environment_profile_id: UUID | None = Field(default=None)
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceJoinEnvironmentSessionResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_join_environment_session"] = "interface_join_environment_session"

    # Attributes
    namespace: str
    environment_session: EnvironmentSessionView | None = Field(default=None)
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = Field(default=None)
    environment_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = Field(default=None)
    environment_session_state: InterfaceEnvironmentSessionState | None = Field(default=None)
    environment_navigation_state: InterfaceEnvironmentNavigationState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceSelectEnvironmentNavigationTargetRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_select_environment_navigation_target"] = (
        "interface_select_environment_navigation_target"
    )

    # Attributes
    namespace: str
    environment_navigation_context_id: UUID | None = Field(default=None)
    selected_process_id: UUID | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceSelectEnvironmentNavigationTargetResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_select_environment_navigation_target"] = (
        "interface_select_environment_navigation_target"
    )

    # Attributes
    namespace: str
    environment_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    environment_navigation_receipt: EnvironmentNavigationCommitReceipt | None = Field(default=None)
    environment_navigation_state: InterfaceEnvironmentNavigationState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceEnterEnvironmentRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_enter_environment"] = "interface_enter_environment"

    # Attributes
    namespace: str
    environment_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    actor_config_id: UUID | None = Field(default=None)
    class_instance_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    environment_session_config_id: UUID | None = Field(default=None)
    session_key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceEnterEnvironmentResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_enter_environment"] = "interface_enter_environment"

    # Attributes
    namespace: str
    environment_admission: InterfaceEnvironmentAdmissionState | None = Field(default=None)
    environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    environment_session: EnvironmentSessionView | None = Field(default=None)
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = Field(default=None)
    environment_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    default_navigation_receipt: EnvironmentNavigationCommitReceipt | None = Field(default=None)
    environment_session_state: InterfaceEnvironmentSessionState | None = Field(default=None)
    environment_navigation_state: InterfaceEnvironmentNavigationState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceResolveExperienceLensRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_resolve_experience_lens"] = "interface_resolve_experience_lens"

    # Attributes
    namespace: str
    environment_session_join_receipt: EnvironmentSessionJoinReceipt | None = Field(default=None)
    environment_navigation_context: EnvironmentNavigationContextView | None = Field(default=None)
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = Field(default=None)
    experience_identity_session_config_id: UUID | None = Field(default=None)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceResolveExperienceLensResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_resolve_experience_lens"] = "interface_resolve_experience_lens"

    # Attributes
    namespace: str
    environment_session: InterfaceEnvironmentSessionState | None = Field(default=None)
    environment_navigation: InterfaceEnvironmentNavigationState | None = Field(default=None)
    experience_lens: InterfaceExperienceLensState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceEnterAppScreenRequest(InterfaceControlPlaneRequest):
    # Attributes
    operation: str = Field(default="interface_enter_app_screen")
    namespace: str
    app_package_id: UUID
    app_package_branch_id: UUID
    app_package_object_instance_graph_commit_id: UUID
    app_config_screen_config_id: UUID
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class InterfaceEnterAppScreenResponse(InterfaceControlPlaneResponse):
    # Attributes
    operation: str = Field(default="interface_enter_app_screen")
    namespace: str
    app_screen: InterfaceAppScreenState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceActionRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_action"] = "interface_action"

    # Attributes
    namespace: str
    pane_ref: str | None = Field(default=None)
    action_key: str
    action_kind: str | None = Field(default=None)
    operation_ref: str | None = Field(default=None)
    sdk_operation_id: str | None = Field(default=None)
    pane_config_sdk_operation_id: str | None = Field(default=None)
    endpoint_ref: str | None = Field(default=None)
    api_capability_endpoint_id: str | None = Field(default=None)
    pane_config_api_capability_endpoint_id: str | None = Field(default=None)
    payload: JsonObject = Field(default_factory=JsonObject)


class InterfaceActionResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_action"] = "interface_action"

    # Attributes
    namespace: str
    pane_ref: str | None = Field(default=None)
    action_key: str
    host_state: InterfaceHostState


class InterfaceSelectStepRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_select_step"] = "interface_select_step"

    # Attributes
    namespace: str
    step_id: str | None = Field(default=None)


class InterfaceSelectStepResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_select_step"] = "interface_select_step"

    # Attributes
    namespace: str
    step_id: str | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceSelectProfileRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_select_profile"] = "interface_select_profile"

    # Attributes
    namespace: str
    profile_id: str


class InterfaceSelectProfileResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_select_profile"] = "interface_select_profile"

    # Attributes
    namespace: str
    profile_id: str
    host_state: InterfaceHostState


class InterfaceSelectRuntimeLayoutRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_select_runtime_layout"] = "interface_select_runtime_layout"

    # Attributes
    namespace: str
    layout_config_id: UUID | None = Field(default=None)


class InterfaceSelectRuntimeLayoutResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_select_runtime_layout"] = "interface_select_runtime_layout"

    # Attributes
    namespace: str
    layout_config_id: UUID | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceActivateRuntimeFocusRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_activate_runtime_focus"] = "interface_activate_runtime_focus"

    # Attributes
    namespace: str
    representation_id: UUID | None = Field(default=None)


class InterfaceActivateRuntimeFocusResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_activate_runtime_focus"] = "interface_activate_runtime_focus"

    # Attributes
    namespace: str
    representation_id: UUID | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceRequestWindowLayoutRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_request_window_layout"] = "interface_request_window_layout"

    # Attributes
    namespace: str
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    window_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    representation_id: UUID | None = Field(default=None)
    requested_by_service: str | None = Field(default=None)
    requested_by_operation: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class InterfaceRequestWindowLayoutResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_request_window_layout"] = "interface_request_window_layout"

    # Attributes
    namespace: str
    interface_package_id: UUID | None = Field(default=None)
    interface_package_name: str | None = Field(default=None)
    window_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    representation_id: UUID | None = Field(default=None)
    requested_by_service: str | None = Field(default=None)
    requested_by_operation: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceAttentionLayoutTransitionSectionIntent(BaseModel):
    """One stable-id row in a complete shared-layout transition intent."""

    # Attributes
    layout_config_section_config_id: UUID
    order: int
    weight_micros: int
    is_visible: bool = Field(default=True)
    is_collapsed: bool = Field(default=False)


class InterfaceApplyAttentionLayoutTransitionRequest(InterfaceControlPlaneRequest):
    """
    Commit one complete renderer-neutral layout vector through Interface Host.
    Pixels, viewport dimensions, and floating geometry are intentionally absent.
    """

    # Discriminator Tag
    operation: Literal["interface_apply_attention_layout_transition"] = "interface_apply_attention_layout_transition"

    # Attributes
    namespace: str
    client_intent_id: str
    expected_previous_layout_transition_id: UUID | None = Field(default=None)
    topology_transition_id: UUID | None = Field(default=None)
    section_states: list[InterfaceAttentionLayoutTransitionSectionIntent] = Field(default_factory=list)


class InterfaceApplyAttentionLayoutTransitionResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_apply_attention_layout_transition"] = "interface_apply_attention_layout_transition"

    # Attributes
    namespace: str
    outcome: str
    conflict_reason: str | None = Field(default=None)
    active_layout_transition_id: UUID | None = Field(default=None)
    active_topology_transition_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceAttentionLayoutTopologyTransitionSectionIntent(BaseModel):
    """One stable admitted config-section anchor in a complete topology intent."""

    # Attributes
    layout_config_section_config_id: UUID
    order: int


class InterfaceApplyAttentionLayoutTopologyTransitionRequest(InterfaceControlPlaneRequest):
    """Commit one complete active-membership/order vector through Attention."""

    # Discriminator Tag
    operation: Literal["interface_apply_attention_layout_topology_transition"] = (
        "interface_apply_attention_layout_topology_transition"
    )

    # Attributes
    namespace: str
    client_intent_id: str
    expected_previous_topology_transition_id: UUID | None = Field(default=None)
    section_states: list[InterfaceAttentionLayoutTopologyTransitionSectionIntent] = Field(default_factory=list)


class InterfaceApplyAttentionLayoutTopologyTransitionResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_apply_attention_layout_topology_transition"] = (
        "interface_apply_attention_layout_topology_transition"
    )

    # Attributes
    namespace: str
    outcome: str
    conflict_reason: str | None = Field(default=None)
    active_topology_transition_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceReportRendererCapabilitiesRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_report_renderer_capabilities"] = "interface_report_renderer_capabilities"

    # Attributes
    namespace: str
    renderer_capabilities: InterfaceRendererCapabilitiesState


class InterfaceReportRendererCapabilitiesResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_report_renderer_capabilities"] = "interface_report_renderer_capabilities"

    # Attributes
    namespace: str
    host_state: InterfaceHostState


class InterfaceSyncViewStateCursorRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_sync_view_state_cursor"] = "interface_sync_view_state_cursor"

    # Attributes
    namespace: str
    renderer_id: str | None = Field(default=None)
    known_cursor: str | None = Field(default=None)
    known_digest: str | None = Field(default=None)


class InterfaceSyncViewStateCursorResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_sync_view_state_cursor"] = "interface_sync_view_state_cursor"

    # Attributes
    namespace: str
    changed: bool = Field(default=True)
    view_state_cursor: InterfaceHostViewStateCursorState | None = Field(default=None)
    host_state: InterfaceHostState


class InterfaceFollowRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_follow"] = "interface_follow"

    # Attributes
    namespace: str
    poll_interval_ms: int = Field(default=1000)


class InterfaceFollowResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_follow"] = "interface_follow"

    # Attributes
    namespace: str
    host_state: InterfaceHostState


class InterfaceInvokeApiRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_invoke_api"] = "interface_invoke_api"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject = Field(default_factory=JsonObject)


class InterfaceInvokeApiResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_invoke_api"] = "interface_invoke_api"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str
    service_status: str | None = Field(default=None)
    response_payload: JsonValue | None = Field(default=None)


class InterfaceStreamApiRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_stream_api"] = "interface_stream_api"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject = Field(default_factory=JsonObject)


class InterfaceStreamApiResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_stream_api"] = "interface_stream_api"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str


class InterfaceStopRequest(InterfaceControlPlaneRequest):
    # Discriminator Tag
    operation: Literal["interface_stop"] = "interface_stop"

    # Attributes
    namespace: str


class InterfaceStopResponse(InterfaceControlPlaneResponse):
    # Discriminator Tag
    operation: Literal["interface_stop"] = "interface_stop"

    # Attributes
    namespace: str
    hosted_namespace: HostedInterfaceNamespace


class InterfaceStateNotification(InterfaceControlPlaneNotification):
    # Discriminator Tag
    operation: Literal["interface_state"] = "interface_state"

    # Attributes
    namespace: str
    host_state: InterfaceHostState


class InterfaceApiEventNotification(InterfaceControlPlaneNotification):
    # Discriminator Tag
    operation: Literal["interface_api_event"] = "interface_api_event"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str
    event_kind: str
    sequence: int
    item_key: str
    payload: JsonValue | None = Field(default=None)


class InterfaceApiStreamClosedNotification(InterfaceControlPlaneNotification):
    # Discriminator Tag
    operation: Literal["interface_api_stream_closed"] = "interface_api_stream_closed"

    # Attributes
    namespace: str
    endpoint_ref: str
    discriminant: str
    service_status: str | None = Field(default=None)
    response_payload: JsonValue | None = Field(default=None)
    error: str | None = Field(default=None)
