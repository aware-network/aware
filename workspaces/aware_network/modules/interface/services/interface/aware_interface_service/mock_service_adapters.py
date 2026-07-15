from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from collections.abc import Mapping
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_environment_service_dto.environment.view import (
    EnvironmentNavigatorViewStateV1,
    EnvironmentProcessNavigationItemV1,
    EnvironmentThreadNavigationItemV1,
    ThreadLayoutCandidateViewStateV1,
    ThreadLayoutSectionViewStateV1,
    ThreadLayoutViewStateV1,
)
from aware_environment_sdk.view_state_providers import (
    ENVIRONMENT_NAVIGATOR_API_VIEW_REF,
    ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
    THREAD_LAYOUT_API_VIEW_REF,
    THREAD_LAYOUT_PROJECTION_VIEW_KEY,
)
from aware_api_service_dto.comms.models.api import (
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointResponse,
)
from aware_code.types import JsonObject
from aware_experience_service_dto.experience.section_graph_binding.models import (
    ExperienceSectionFocusTarget,
    ExperienceSectionGraphBindingDescriptor,
    ExperienceSectionGraphBindingState,
    ExperienceSectionViewResolution,
    ExperienceViewInvocationActionDescriptor,
    ExperienceViewInvocationActionReceipt,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceSectionGraphBindingResponse,
    GetExperienceSectionGraphBindingCatalogResponse,
    InvokeExperienceViewInvocationActionResponse,
)
from aware_interface import (
    InterfaceBackendState,
    InterfaceGateState,
    InterfaceGateStep,
    InterfaceMaterializedPaneState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedView,
    InterfaceRuntimePaneRenderSpecState,
    InterfaceRuntimeState,
    compose_interface_runtime_state,
)
from aware_interface.lifecycle.models import InterfaceResolvedPaneActionTarget
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfacePaneConfigBundle,
    InterfacePaneProjectionExperienceViewBundle,
    InterfacePaneViewInvocationActionBundle,
)
from aware_network_sdk.view_state_providers import (
    NetworkTerritoryDiscoveryV1ProviderInput,
    ViewProviderProvenanceV1 as NetworkViewProviderProvenanceV1,
    network_territory_discovery_view_state,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_interface.session_port import FocusScopeLane, SectionFocusScopeLane
from aware_interface_sdk.transport import (
    InterfaceTransportBindingState,
    InterfaceTransportProfile,
)
from aware_interface_service.models import InterfaceEnvironmentNavigationState


MOCK_IDENTITY_ADMISSION_ENDPOINT = "mock://identity_admission"

_PANE_WARNING = "interface_host_mock_identity_admission_adapter"
_NETWORK_PANE_WARNING = "interface_host_mock_network_territory_adapter"
_ENVIRONMENT_NAVIGATOR_WARNING = "interface_host_mock_environment_navigator_adapter"
_INTERFACE_PACKAGE_NAME = "aware-control-interface"
_PANE_CONFIG_ID = UUID("457b5175-ca99-536f-ab65-b072ca2ae9bd")
_PANE_PACKAGE_ID = UUID("a05f7fd9-4bf4-5f9f-aa30-fcf716174489")
_PANE_CONFIG_PROJECTION_EXPERIENCE_VIEW_ID = UUID(
    "c11c9806-d41e-57e2-b761-495d71d251d8"
)
_PROJECTION_EXPERIENCE_VIEW_ID = UUID("f843625b-9d43-56b9-9535-7cbae7e6d3d9")
_STATE_MODEL_ID = UUID("27dc7a7d-e719-5253-b72f-7e28158454c6")
_SDK_OPERATION_ID = UUID("5d8034d6-6b2f-5d43-9ea5-7acaae63c793")
_PROJECTION_EXPERIENCE_ID = UUID("d422a5b6-a671-5d42-b8fb-c00368af0394")
_PROJECTION_EXPERIENCE_SECTION_ID = UUID("d78b46e5-3811-5081-a737-db74194b18fd")
_PROJECTION_EXPERIENCE_SECTION_VIEW_ID = UUID("12b07545-9945-56b0-9686-94ec37643069")
_PROJECTION_EXPERIENCE_VIEW_INSTANCE_ID = UUID("b75772cc-f8c7-5c13-916c-52f0bff05166")
_PROJECTION_EXPERIENCE_SECTION_GRAPH_BINDING_ID = UUID(
    "80c1ba64-4506-521e-94a9-b0b185baf114"
)
_PROJECTION_EXPERIENCE_GRAPH_IDENTITY_ID = UUID("a77b1df1-3929-5d2d-ac8a-b9c6ff06a56d")
_OBJECT_PROJECTION_GRAPH_IDENTITY_ID = UUID("70874366-417b-5190-b837-52a8dce82253")

_WINDOW_KEY = "main"
_LAYOUT_KEY = "coordination_center"
_SECTION_KEY = "orchestration"
_PANE_KIND = "identity_admission"
_VIEW_REF = "aware_control_identity.identity.admission.v1"
_PROJECTION_VIEW_KEY = "identity.admission.v1"
_VIEW_ACTION_KEY = "admit_identity"
_EXPERIENCE_SECTION_GRAPH_BINDING_KEY = "identity_admission"
_EXPERIENCE_CATALOG_ENDPOINT_REF = (
    "experience.get_experience_section_graph_binding_catalog."
    "get_experience_section_graph_binding_catalog"
)
_EXPERIENCE_ACTIVATE_ENDPOINT_REF = (
    "experience.activate_experience_section_graph_binding."
    "activate_experience_section_graph_binding"
)
_EXPERIENCE_INVOKE_VIEW_ACTION_ENDPOINT_REF = (
    "experience.invoke_experience_view_invocation_action."
    "invoke_experience_view_invocation_action"
)

_NETWORK_PANE_CONFIG_ID = UUID("21bf30ef-e188-53ed-92d6-ebf065daadf4")
_NETWORK_PANE_PACKAGE_ID = UUID("4df05965-63a7-5a27-a54f-cf479cac2545")
_NETWORK_PROJECTION_EXPERIENCE_VIEW_ID = UUID("13daebd6-5f6a-516a-b315-8893c4bc43bd")
_NETWORK_STATE_MODEL_ID = UUID("583e274c-55db-533b-a147-98deed65c5a9")
_NETWORK_PANE_KIND = "network_territory"
_NETWORK_VIEW_REF = "aware_network.territory.discovery.v1"
_NETWORK_PROJECTION_VIEW_KEY = "territory.discovery.v1"
_NETWORK_ENDPOINT_REF = "network.discovery.discover_territory"
_NETWORK_MOCK_AUTHORITY_URL = "mock://network_territory"

_ENVIRONMENT_NAVIGATOR_PANE_STATE_KEY = (
    "shell:environment_navigation:environment_navigator"
)
_ENVIRONMENT_NAVIGATOR_WINDOW_KEY = "shell"
_ENVIRONMENT_NAVIGATOR_LAYOUT_KEY = "environment_navigation"
_ENVIRONMENT_NAVIGATOR_SECTION_KEY = "environment_navigator"
_ENVIRONMENT_NAVIGATOR_PANE_KIND = "environment_navigator"
_THREAD_LAYOUT_PANE_STATE_KEY = "shell:environment_navigation:thread_layout"
_THREAD_LAYOUT_WINDOW_KEY = "main"
_THREAD_LAYOUT_SECTION_KEY = "thread_layout"
_THREAD_LAYOUT_PANE_KIND = "thread_layout"
_ENVIRONMENT_NAVIGATOR_STATE_MODEL_REF = (
    "aware_environment_service_dto.environment.EnvironmentNavigatorViewStateV1"
)
_THREAD_LAYOUT_STATE_MODEL_REF = (
    "aware_environment_service_dto.environment.ThreadLayoutViewStateV1"
)

_ID_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://workspaces/aware_network/modules/interface/services/interface/mock-adapters",
)


def is_mock_service_endpoint(endpoint: str | None) -> bool:
    return (endpoint or "").strip().casefold() == MOCK_IDENTITY_ADMISSION_ENDPOINT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_uuid(*parts: str) -> UUID:
    seed = ":".join(part.strip() for part in parts if part.strip())
    return uuid5(_ID_NAMESPACE, seed)


def _canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _request_field(
    request_payload: object, field_name: str, default: object = None
) -> object:
    if isinstance(request_payload, Mapping):
        return request_payload.get(field_name, default)
    return getattr(request_payload, field_name, default)


def _uuid_request_field(request_payload: object, field_name: str) -> UUID | None:
    value = _request_field(request_payload, field_name, None)
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _request_payload_mapping(request_payload: object) -> dict[str, object]:
    if isinstance(request_payload, Mapping):
        return dict(request_payload)
    model_dump = getattr(request_payload, "model_dump", None)
    if callable(model_dump):
        return cast(dict[str, object], model_dump(mode="python", exclude_none=True))
    return {}


def _section_token(section_key: str) -> str:
    return section_key.strip().casefold() or "section"


@dataclass(slots=True)
class MockIdentityAdmissionServiceAdapter:
    namespace: str
    host_label: str
    endpoint: str
    repository_root: Path
    state_home: Path
    interface_config_bundle: InterfaceConfigBundle | None = None
    identity_admission_enabled: bool = True
    network_territory_enabled: bool = False
    actor_id: UUID = field(init=False)
    interface_id: UUID = field(init=False)
    interface_session_id: UUID = field(init=False)
    focus_scope_id: UUID = field(init=False)
    branch_id: UUID = field(init=False)
    network_branch_id: UUID = field(init=False)
    layout_id: UUID = field(init=False)
    window_id: UUID = field(init=False)
    layout_section_id: UUID = field(init=False)
    section_focus_scope_id: UUID = field(init=False)
    projection_hash: str = field(init=False)
    network_projection_hash: str = field(init=False)
    head_commit_id: str = field(init=False)
    network_head_commit_id: str = field(init=False)
    graph_hash_post: str = field(init=False)
    network_graph_hash_post: str = field(init=False)
    environment_id: UUID = field(init=False)
    environment_session_id: UUID = field(init=False)
    environment_navigation_context_id: UUID = field(init=False)
    selected_process_id: UUID = field(init=False)
    selected_thread_id: UUID = field(init=False)
    display_name: str = field(init=False)
    public_handle: str = field(init=False)
    bio: str = field(init=False)
    status: str = field(init=False)
    receipt_summary: str = field(init=False)
    action_count: int = field(init=False)
    transport_session: "MockInterfaceTransportSession" = field(init=False)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.state_home = self.state_home.resolve()
        self.actor_id = _stable_uuid(self.namespace, "actor")
        self.interface_id = _stable_uuid(self.namespace, "interface")
        self.interface_session_id = _stable_uuid(self.namespace, "interface-session")
        self.focus_scope_id = _stable_uuid(self.namespace, "focus-scope")
        self.branch_id = _stable_uuid(self.namespace, "branch")
        self.network_branch_id = _stable_uuid(
            self.namespace,
            "network-territory-branch",
        )
        self.environment_id = _stable_uuid(self.namespace, "environment")
        self.environment_session_id = _stable_uuid(
            self.namespace,
            "environment-session",
        )
        self.environment_navigation_context_id = _stable_uuid(
            self.namespace,
            "environment-navigation-context",
        )
        self.selected_process_id = _stable_uuid(
            self.namespace,
            "environment-process",
            "coordination",
        )
        self.selected_thread_id = _stable_uuid(
            self.namespace,
            "environment-thread",
            "coordination",
            "conversation",
        )
        self.layout_id = _stable_uuid(self.namespace, "layout")
        self.window_id = _stable_uuid(self.namespace, "window")
        self.layout_section_id = _stable_uuid(self.namespace, "layout-section")
        self.section_focus_scope_id = _stable_uuid(
            self.namespace,
            "section-focus-scope",
        )
        self.projection_hash = "mock-identity-admission-v0"
        self.network_projection_hash = "mock-network-territory-v0"
        self.head_commit_id = str(_stable_uuid(self.namespace, "head-commit"))
        self.network_head_commit_id = str(
            _stable_uuid(self.namespace, "network-territory-head-commit")
        )
        self.graph_hash_post = "mock-identity-admission-graph-v0"
        self.network_graph_hash_post = "mock-network-territory-graph-v0"
        self.display_name = "Luis"
        self.public_handle = "@luis"
        self.bio = "Builder of Aware"
        self.status = "ready"
        self.receipt_summary = ""
        self.action_count = 0
        self.transport_session = MockInterfaceTransportSession(adapter=self)

    async def ensure_boot_interface_graph(self) -> UUID:
        return self.branch_id

    async def snapshot(self) -> InterfaceRuntimeState:
        return self.runtime_state()

    async def resolve_focus_scope_lane(self, *, window_key: str) -> FocusScopeLane:
        return FocusScopeLane(
            interface_id=self.interface_id,
            window_key=window_key,
            window_id=self.window_id,
            focus_scope_id=self.focus_scope_id,
            branch_id=self.branch_id,
            projection_hash=self.projection_hash,
        )

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> SectionFocusScopeLane:
        return SectionFocusScopeLane(
            interface_id=self.interface_id,
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            window_id=self.window_id,
            layout_id=self.layout_id,
            section_id=self._layout_section_id_for_section(section_key),
            layout_section_id=self._layout_section_id_for_section(section_key),
            section_focus_scope_id=self._section_focus_scope_id_for_section(
                section_key
            ),
            focus_scope_id=self.focus_scope_id,
            branch_id=self._branch_id_for_section(section_key),
            projection_hash=self._projection_hash_for_section(section_key),
        )

    def _layout_section_id_for_section(self, section_key: str) -> UUID:
        return _stable_uuid(
            self.namespace,
            "layout-section",
            _section_token(section_key),
        )

    def _section_focus_scope_id_for_section(self, section_key: str) -> UUID:
        return _stable_uuid(
            self.namespace,
            "section-focus-scope",
            _section_token(section_key),
        )

    def _branch_id_for_section(self, section_key: str) -> UUID:
        if (
            self.network_territory_enabled
            and _section_token(section_key) == "inspector"
        ):
            return self.network_branch_id
        return self.branch_id

    def _projection_hash_for_section(self, section_key: str) -> str:
        if (
            self.network_territory_enabled
            and _section_token(section_key) == "inspector"
        ):
            return self.network_projection_hash
        return self.projection_hash

    async def load_pane_render_spec_runtime_states(
        self,
        *,
        interface_config_bundle: InterfaceConfigBundle | None = None,
    ) -> tuple[InterfaceRuntimePaneRenderSpecState, ...]:
        _ = interface_config_bundle
        if not self.identity_admission_enabled:
            return ()
        payload = self.render_spec_payload()
        return (
            InterfaceRuntimePaneRenderSpecState(
                source_kind="interface_host_mock_adapter",
                branch_id=self.branch_id,
                projection_hash=self.projection_hash,
                last_commit_id=_stable_uuid(self.namespace, "render-spec-commit"),
                object_instance_graph_commit_id=_stable_uuid(
                    self.namespace,
                    "render-spec-oig-commit",
                ),
                pane_render_spec_id=UUID(str(payload["spec_id"])),
                pane_config_id=(_PANE_CONFIG_PROJECTION_EXPERIENCE_VIEW_ID),
                render_spec_content_hash_sha256=_canonical_json_sha256(payload),
                payload=cast(dict[str, object], payload),
            ),
        )

    async def invoke_api_endpoint(
        self,
        *,
        endpoint_ref: str,
        request_payload: object,
        **_unused: object,
    ) -> object:
        normalized_endpoint = endpoint_ref.strip()
        if normalized_endpoint == _EXPERIENCE_CATALOG_ENDPOINT_REF:
            return self._experience_section_graph_binding_catalog_response(
                request_payload=request_payload,
            )
        if normalized_endpoint == _EXPERIENCE_ACTIVATE_ENDPOINT_REF:
            return self._activate_experience_section_graph_binding_response(
                request_payload=request_payload,
            )
        if normalized_endpoint == _EXPERIENCE_INVOKE_VIEW_ACTION_ENDPOINT_REF:
            return self._invoke_experience_view_action_response(
                request_payload=request_payload,
            )
        raise AttributeError(
            "Mock Interface transport does not implement typed API endpoint: "
            + normalized_endpoint
        )

    async def invoke_api(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        _ = discriminant, invocation_context
        normalized_endpoint = endpoint_ref.strip()
        if normalized_endpoint == _NETWORK_ENDPOINT_REF:
            if not self.network_territory_enabled:
                return ServiceOperationResponse(
                    status=RequestStatus.failed,
                    error="Network territory mock adapter is not enabled.",
                    response_payload={
                        "source_kind": "interface_host_mock_adapter",
                        "endpoint_ref": normalized_endpoint,
                    },
                    stream_lifecycle=StreamLifecycle.auto_close,
                )
            return ServiceOperationResponse(
                status=RequestStatus.succeeded,
                response_payload=self._mock_network_territory_receipt(),
                stream_lifecycle=StreamLifecycle.auto_close,
            )
        if normalized_endpoint == "identity.signup_via_profile.signup_via_profile":
            if not self.identity_admission_enabled:
                return ServiceOperationResponse(
                    status=RequestStatus.failed,
                    error="Identity admission mock adapter is not enabled.",
                    stream_lifecycle=StreamLifecycle.auto_close,
                )
            self._apply_profile_payload(dict(request_payload))
            return ServiceOperationResponse(
                status=RequestStatus.succeeded,
                response_payload={
                    "status": self.status,
                    "status_tone": self._status_tone(),
                    "actor_id": str(self.actor_id),
                    "display_name": self.display_name,
                    "public_handle": self.public_handle,
                },
                stream_lifecycle=StreamLifecycle.auto_close,
            )
        if (
            normalized_endpoint
            == "identity.check_credential_readiness.check_credential_readiness"
        ):
            return ServiceOperationResponse(
                status=RequestStatus.succeeded,
                response_payload={
                    "status": self.status,
                    "status_tone": self._status_tone(),
                    "ready": self.status == "admitted",
                },
                stream_lifecycle=StreamLifecycle.auto_close,
            )
        return ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload={
                "status": "mocked",
                "endpoint_ref": normalized_endpoint,
                "discriminant": discriminant,
            },
            stream_lifecycle=StreamLifecycle.auto_close,
        )

    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
        timeout_s: float | None = None,
    ) -> InvokeApiEndpointResponse:
        _ = timeout_s
        response = await self.invoke_api(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            invocation_context=invocation_context,
        )
        return InvokeApiEndpointResponse(
            status=(
                ApiRequestStatus.succeeded
                if response.status is RequestStatus.succeeded
                else ApiRequestStatus.failed
            ),
            error=response.error,
            response_payload=cast(dict[str, object], response.response_payload or {}),
            stream_lifecycle=ApiStreamLifecycle.auto_close,
        )

    def _experience_section_graph_binding_catalog_response(
        self,
        *,
        request_payload: object,
    ) -> GetExperienceSectionGraphBindingCatalogResponse:
        descriptor = self._experience_section_graph_binding_descriptor()
        requested_binding_keys = tuple(
            str(item).strip()
            for item in _request_field(request_payload, "binding_keys", ()) or ()
            if str(item).strip()
        )
        requested_section_keys = tuple(
            str(item).strip()
            for item in _request_field(request_payload, "section_keys", ()) or ()
            if str(item).strip()
        )
        include_descriptor = True
        if requested_binding_keys:
            include_descriptor = descriptor.binding_key in requested_binding_keys
        if requested_section_keys:
            include_descriptor = descriptor.section_key in requested_section_keys
        return GetExperienceSectionGraphBindingCatalogResponse(
            request_id=_request_field(request_payload, "request_id", None),
            success=True,
            experience_name=str(
                _request_field(request_payload, "experience_name", "aware_control")
            ),
            catalog_revision=f"mock-experience-catalog:{self.namespace}",
            bindings=[descriptor] if include_descriptor else [],
        )

    def _activate_experience_section_graph_binding_response(
        self,
        *,
        request_payload: object,
    ) -> ActivateExperienceSectionGraphBindingResponse:
        experience_name = str(
            _request_field(request_payload, "experience_name", "aware_control")
        )
        return ActivateExperienceSectionGraphBindingResponse(
            request_id=_request_field(request_payload, "request_id", None),
            success=True,
            info="mock_experience_section_graph_binding_activated",
            experience_name=experience_name,
            catalog_revision=f"mock-experience-catalog:{self.namespace}",
            state=self._experience_section_graph_binding_state(
                request_payload=request_payload,
            ),
        )

    def _invoke_experience_view_action_response(
        self,
        *,
        request_payload: object,
    ) -> InvokeExperienceViewInvocationActionResponse:
        action = self._experience_view_action_for_config_id(
            _request_field(request_payload, "view_invocation_action_config_id", None)
        )
        if action is not None and action.action_key == _VIEW_ACTION_KEY:
            self._apply_profile_payload(
                _request_payload_mapping(
                    _request_field(request_payload, "request_payload", {})
                )
            )
        view_action_config_id = _uuid_request_field(
            request_payload,
            "view_invocation_action_config_id",
        )
        view_instance_id = _uuid_request_field(
            request_payload,
            "projection_experience_view_instance_id",
        )
        experience_name = str(
            _request_field(request_payload, "experience_name", "aware_control")
        )
        invocation_key = _uuid_request_field(request_payload, "invocation_key")
        receipt = ExperienceViewInvocationActionReceipt(
            projection_experience_view_instance_id=(
                view_instance_id or _PROJECTION_EXPERIENCE_VIEW_INSTANCE_ID
            ),
            view_invocation_action_config_id=(
                view_action_config_id
                or (
                    action.view_invocation_action_config_id
                    if action is not None
                    else _stable_uuid(self.namespace, "view-action", "unknown")
                )
            ),
            experience_invocation_action_config_id=(
                action.experience_invocation_action_config_id
                if action is not None
                else _stable_uuid(
                    self.namespace,
                    "experience-invocation-action-config",
                    "unknown",
                )
            ),
            experience_invocation_action_id=_stable_uuid(
                self.namespace,
                "experience-invocation-action",
                str(invocation_key or "unknown"),
            ),
            projection_experience_view_invocation_action_id=_stable_uuid(
                self.namespace,
                "projection-experience-view-invocation-action",
                str(invocation_key or "unknown"),
            ),
            invocation_key=(
                invocation_key
                or _stable_uuid(self.namespace, "experience-view-action-invocation")
            ),
            actor_id=_uuid_request_field(request_payload, "actor_id"),
            request_ref=_text_or_none(_request_field(request_payload, "request_ref")),
            receipt_ref=_text_or_none(_request_field(request_payload, "receipt_ref")),
            status="succeeded",
        )
        return InvokeExperienceViewInvocationActionResponse(
            request_id=_request_field(request_payload, "request_id", None),
            success=True,
            info="mock_experience_view_action_invoked",
            experience_name=experience_name,
            receipt=receipt,
            response_payload={
                "status": self.status,
                "status_tone": self._status_tone(),
                "actor_id": str(self.actor_id),
                "display_name": self.display_name,
                "public_handle": self.public_handle,
                "source_kind": "interface_host_mock_adapter",
            },
        )

    def _experience_section_graph_binding_descriptor(
        self,
    ) -> ExperienceSectionGraphBindingDescriptor:
        _, view = self._identity_pane_config_and_view()
        return ExperienceSectionGraphBindingDescriptor(
            binding_key=(
                view.section_graph_binding_key or _EXPERIENCE_SECTION_GRAPH_BINDING_KEY
            ),
            section_key=_SECTION_KEY,
            projection_observable_id=(
                view.object_projection_graph_observable_id
                or _stable_uuid(self.namespace, "identity", "observable")
            ),
            projection_experience_graph_identity_id=(
                view.projection_experience_graph_identity_id
                or _PROJECTION_EXPERIENCE_GRAPH_IDENTITY_ID
            ),
            object_projection_graph_identity_id=(
                view.object_projection_graph_identity_id
                or _OBJECT_PROJECTION_GRAPH_IDENTITY_ID
            ),
            view_ref=view.view_ref,
            graph_identity_ref="aware_control_identity.identity.admission",
        )

    def _experience_section_graph_binding_state(
        self,
        *,
        request_payload: object,
    ) -> ExperienceSectionGraphBindingState:
        descriptor = self._experience_section_graph_binding_descriptor()
        _, view = self._identity_pane_config_and_view()
        activation_scope = _request_field(request_payload, "activation_scope", None)
        focus_scope_id = _uuid_request_field(activation_scope, "focus_scope_id")
        focus_id = _uuid_request_field(activation_scope, "focus_id")
        focus_target = ExperienceSectionFocusTarget(
            kind="constructor",
            focus_id=focus_id,
            focus_scope_id=focus_scope_id,
            projection_experience_graph_identity_id=(
                descriptor.projection_experience_graph_identity_id
            ),
            object_projection_graph_identity_id=(
                descriptor.object_projection_graph_identity_id
            ),
            target_type="projection_experience_graph_identity",
            target_id=descriptor.projection_experience_graph_identity_id,
            description=descriptor.graph_identity_ref,
        )
        return ExperienceSectionGraphBindingState(
            binding=descriptor,
            exists=True,
            is_active=True,
            focus_scope_id=focus_scope_id,
            focus_id=focus_id,
            projection_observable_id=descriptor.projection_observable_id,
            observable_id=descriptor.projection_observable_id,
            projection_experience_graph_identity_id=(
                descriptor.projection_experience_graph_identity_id
            ),
            focus_target=focus_target,
            section_view=ExperienceSectionViewResolution(
                projection_experience_id=_PROJECTION_EXPERIENCE_ID,
                section_id=self.layout_section_id,
                object_projection_graph_observable_id=(
                    descriptor.projection_observable_id
                ),
                projection_experience_section_id=_PROJECTION_EXPERIENCE_SECTION_ID,
                projection_experience_section_view_id=(
                    _PROJECTION_EXPERIENCE_SECTION_VIEW_ID
                ),
                projection_experience_view_instance_id=(
                    _PROJECTION_EXPERIENCE_VIEW_INSTANCE_ID
                ),
                projection_experience_view_id=view.projection_experience_view_id,
                section_graph_binding_id=(
                    _PROJECTION_EXPERIENCE_SECTION_GRAPH_BINDING_ID
                ),
                view_ref=view.view_ref,
                view_instance_key=f"{self.namespace}:{_SECTION_KEY}:{_PANE_KIND}",
                section_key=_SECTION_KEY,
                status="active",
                actions=list(self._experience_view_actions()),
            ),
        )

    def _experience_view_actions(
        self,
    ) -> tuple[ExperienceViewInvocationActionDescriptor, ...]:
        _, view = self._identity_pane_config_and_view()
        actions = tuple(view.invocation_actions) or (
            InterfacePaneViewInvocationActionBundle(
                projection_experience_view_invocation_action_id=_stable_uuid(
                    _PANE_KIND,
                    "view-action",
                    _VIEW_ACTION_KEY,
                ),
                action_key=_VIEW_ACTION_KEY,
                action_kind="view",
                target_ref=_VIEW_ACTION_KEY,
                label="Admit identity",
                receipt_policy="show_receipt",
            ),
        )
        return tuple(
            ExperienceViewInvocationActionDescriptor(
                action_id=action.projection_experience_view_invocation_action_id,
                view_invocation_action_config_id=(
                    action.projection_experience_view_invocation_action_id
                ),
                experience_invocation_action_config_id=_stable_uuid(
                    self.namespace,
                    "experience-invocation-action-config",
                    action.action_key,
                ),
                api_view_capability_endpoint_id=(
                    action.api_capability_endpoint_id
                    or _stable_uuid(
                        self.namespace,
                        "api-view-capability-endpoint",
                        action.action_key,
                    )
                ),
                action_key=action.action_key,
                target_kind=action.action_kind,
                endpoint_ref=action.target_ref,
                label=action.label,
                receipt_policy=action.receipt_policy,
                confirmation_policy=action.confirmation_policy,
                optimistic_policy=action.optimistic_policy,
                api_capability_endpoint_id=action.api_capability_endpoint_id,
                sdk_operation_id=action.sdk_operation_id,
            )
            for action in actions
        )

    def _experience_view_action_for_config_id(
        self,
        view_invocation_action_config_id: object,
    ) -> ExperienceViewInvocationActionDescriptor | None:
        if view_invocation_action_config_id is None:
            return None
        try:
            normalized_id = UUID(str(view_invocation_action_config_id))
        except ValueError:
            return None
        return next(
            (
                action
                for action in self._experience_view_actions()
                if action.view_invocation_action_config_id == normalized_id
            ),
            None,
        )

    def select_environment_navigation_target(
        self,
        *,
        environment_navigation_context_id: UUID | None = None,
        selected_process_id: UUID | None = None,
        selected_thread_id: UUID | None = None,
        reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> InterfaceEnvironmentNavigationState:
        _ = environment_navigation_context_id, evidence
        resolved_process_id = selected_process_id
        resolved_thread_id = selected_thread_id
        if resolved_thread_id is not None:
            matching = self._process_id_for_thread(resolved_thread_id)
            if matching is not None:
                resolved_process_id = matching
        if resolved_process_id is not None:
            self.selected_process_id = resolved_process_id
            if resolved_thread_id is None:
                resolved_thread_id = self._default_thread_id_for_process(
                    resolved_process_id
                )
        if resolved_thread_id is not None:
            self.selected_thread_id = resolved_thread_id
        return self.environment_navigation_state(
            reason=reason or "interface_mock_select_environment_navigation_target"
        )

    def environment_navigation_state(
        self,
        *,
        reason: str | None = None,
    ) -> InterfaceEnvironmentNavigationState:
        return InterfaceEnvironmentNavigationState(
            status="active",
            accepted=True,
            actor_id=self.actor_id,
            environment_id=self.environment_id,
            environment_session_id=self.environment_session_id,
            environment_navigation_context_id=self.environment_navigation_context_id,
            key="mock_environment_navigation",
            process_id=self.selected_process_id,
            thread_id=self.selected_thread_id,
            branch_id=self.branch_id,
            projection_hash="mock-environment-navigator-v0",
            root_object_id=self.environment_id,
            commit_id=_stable_uuid(self.namespace, "environment-navigation-commit"),
            object_instance_graph_commit_id=_stable_uuid(
                self.namespace,
                "environment-navigation-oig-commit",
            ),
            reason=reason,
            updated_at=_utc_now_iso(),
            evidence={
                "source": "interface_host_mock_environment_navigator_adapter",
            },
        )

    def runtime_state(self) -> InterfaceRuntimeState:
        interface_package_id = (
            self.interface_config_bundle.interface_package_id
            if self.interface_config_bundle is not None
            else None
        )
        materialized_pane_states: list[InterfaceMaterializedPaneState] = [
            self._environment_navigator_materialized_pane_state(),
            self._thread_layout_materialized_pane_state(),
        ]
        resolved_panes: list[InterfaceResolvedPaneDescriptor] = []
        warnings: list[str] = [_ENVIRONMENT_NAVIGATOR_WARNING]
        if self.identity_admission_enabled:
            resolved_panes.append(self._identity_resolved_pane_descriptor())
            materialized_pane_states.append(self._materialized_pane_state())
            warnings.append(_PANE_WARNING)
        if self.network_territory_enabled:
            resolved_panes.append(self._network_territory_resolved_pane_descriptor())
            materialized_pane_states.append(
                self._network_territory_materialized_pane_state()
            )
            warnings.append(_NETWORK_PANE_WARNING)
        return compose_interface_runtime_state(
            backend=InterfaceBackendState(
                available=True,
                manifest_path=None,
                registry_path=None,
                database_path=None,
                database_exists=False,
                environment_id=None,
                opg_count=0,
                projection_bundle_available=self.interface_config_bundle is not None,
                projection_plan_count=1,
                table_count=0,
                reason="interface_host_mock_adapter",
            ),
            gate_state=InterfaceGateState(
                destination_key="identity_admission",
                active_step_key="identity_profile",
                blocked=False,
                steps=(
                    InterfaceGateStep(
                        key="identity_profile",
                        status="ready",
                        title="Identity profile",
                    ),
                ),
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware_control",
                interface_package_id=interface_package_id,
                interface_package_name=_INTERFACE_PACKAGE_NAME,
                projection_view_id=_PROJECTION_VIEW_KEY,
                host_payload={
                    "source_kind": "interface_host_mock_adapter",
                    "action_count": self.action_count,
                },
            ),
            materialized_pane_states=tuple(materialized_pane_states),
            resolved_panes=tuple(resolved_panes),
            dynamic_pane_render_specs=(),
            warnings=tuple(warnings),
        )

    def _environment_navigator_materialized_pane_state(
        self,
    ) -> InterfaceMaterializedPaneState:
        view_state = self._environment_navigator_view_state()
        return InterfaceMaterializedPaneState(
            pane_state_key=_ENVIRONMENT_NAVIGATOR_PANE_STATE_KEY,
            window_key=_ENVIRONMENT_NAVIGATOR_WINDOW_KEY,
            layout_key=_ENVIRONMENT_NAVIGATOR_LAYOUT_KEY,
            section_key=_ENVIRONMENT_NAVIGATOR_SECTION_KEY,
            pane_kind=_ENVIRONMENT_NAVIGATOR_PANE_KIND,
            branch_id=self.branch_id,
            projection_view_id=ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
            projection_hash="mock-environment-navigator-v0",
            status=view_state.status,
            head_commit_id=str(
                _stable_uuid(self.namespace, "environment-navigation-head")
            ),
            materialized_at=_utc_now_iso(),
            state=view_state.model_dump(mode="json"),
            provenance={
                "source": "interface_host_mock_environment_navigator_adapter",
                "view_ref": ENVIRONMENT_NAVIGATOR_API_VIEW_REF,
                "projection_view_key": ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
                "state_model_ref": _ENVIRONMENT_NAVIGATOR_STATE_MODEL_REF,
            },
        )

    def _environment_navigator_view_state(self) -> EnvironmentNavigatorViewStateV1:
        processes = (
            self._environment_process(
                process_key="coordination",
                title="Coordination",
                threads=(
                    ("conversation", "Conversation"),
                    ("goals", "Goals"),
                    ("issues", "Issues"),
                ),
            ),
            self._environment_process(
                process_key="workspace",
                title="Workspace",
                threads=(("materializations", "Materializations"),),
            ),
        )
        return EnvironmentNavigatorViewStateV1(
            environment_id=str(self.environment_id),
            title="Dogfood Environment",
            status="ready",
            ready=True,
            selected_process_id=str(self.selected_process_id),
            selected_thread_id=str(self.selected_thread_id),
            processes=list(processes),
            empty_message="No mock environment threads available.",
            provenance={
                "source": "interface_host_mock_environment_navigator_adapter",
            },
        )

    def _thread_layout_materialized_pane_state(self) -> InterfaceMaterializedPaneState:
        view_state = self._thread_layout_view_state()
        layout_key = view_state.active_layout_key or "thread_layout"
        return InterfaceMaterializedPaneState(
            pane_state_key=_THREAD_LAYOUT_PANE_STATE_KEY,
            window_key=_THREAD_LAYOUT_WINDOW_KEY,
            layout_key=layout_key,
            section_key=_THREAD_LAYOUT_SECTION_KEY,
            pane_kind=_THREAD_LAYOUT_PANE_KIND,
            branch_id=self.branch_id,
            projection_view_id=THREAD_LAYOUT_PROJECTION_VIEW_KEY,
            projection_hash="mock-thread-layout-v0",
            status=view_state.status,
            head_commit_id=str(_stable_uuid(self.namespace, "thread-layout-head")),
            materialized_at=_utc_now_iso(),
            state=view_state.model_dump(mode="json"),
            provenance={
                "source": "interface_host_mock_environment_navigator_adapter",
                "view_ref": THREAD_LAYOUT_API_VIEW_REF,
                "projection_view_key": THREAD_LAYOUT_PROJECTION_VIEW_KEY,
                "state_model_ref": _THREAD_LAYOUT_STATE_MODEL_REF,
            },
        )

    def _thread_layout_view_state(self) -> ThreadLayoutViewStateV1:
        descriptor = self._selected_thread_descriptor()
        process_key = descriptor["process_key"]
        thread_key = descriptor["thread_key"]
        title = descriptor["title"]
        sections = self._thread_layout_sections(
            process_key=process_key,
            thread_key=thread_key,
        )
        layout_id = _stable_uuid(
            self.namespace,
            "thread-layout",
            process_key,
            thread_key,
        )
        layout_key = f"{process_key}_{thread_key}"
        return ThreadLayoutViewStateV1(
            environment_id=str(self.environment_id),
            process_id=str(self.selected_process_id),
            process_key=process_key,
            thread_id=str(self.selected_thread_id),
            thread_key=thread_key,
            title=title,
            status="ready",
            active_layout_id=str(layout_id),
            active_layout_key=layout_key,
            layouts=[
                ThreadLayoutCandidateViewStateV1(
                    layout_id=str(layout_id),
                    layout_key=layout_key,
                    title=title,
                    is_active=True,
                    sections=sections,
                )
            ],
            sections=sections,
            empty_message="" if sections else "No mock thread layout sections.",
            provenance={
                "source": "interface_host_mock_environment_navigator_adapter",
                "selected_process_id": str(self.selected_process_id),
                "selected_thread_id": str(self.selected_thread_id),
            },
        )

    def _selected_thread_descriptor(self) -> dict[str, str]:
        for process_key, process_title, threads in self._mock_environment_topology():
            process_id = _stable_uuid(
                self.namespace,
                "environment-process",
                process_key,
            )
            for thread_key, thread_title in threads:
                thread_id = _stable_uuid(
                    self.namespace,
                    "environment-thread",
                    process_key,
                    thread_key,
                )
                if thread_id == self.selected_thread_id:
                    return {
                        "process_key": process_key,
                        "process_title": process_title,
                        "thread_key": thread_key,
                        "title": thread_title,
                    }
            if process_id == self.selected_process_id:
                first_thread_key, first_thread_title = threads[0]
                return {
                    "process_key": process_key,
                    "process_title": process_title,
                    "thread_key": first_thread_key,
                    "title": first_thread_title,
                }
        return {
            "process_key": "environment",
            "process_title": "Environment",
            "thread_key": "home",
            "title": "Environment Home",
        }

    def _thread_layout_sections(
        self,
        *,
        process_key: str,
        thread_key: str,
    ) -> list[ThreadLayoutSectionViewStateV1]:
        if process_key == "coordination" and thread_key == "conversation":
            return [
                ThreadLayoutSectionViewStateV1(
                    section_key="conversation",
                    title="Conversation",
                    description="Shared coordination conversation.",
                    order=0,
                    flex=1.0,
                    pane_key="conversation",
                    view_ref="aware_coordination.conversation.v1",
                    view_key="conversation.v1",
                )
            ]
        if process_key == "coordination" and thread_key == "goals":
            return [
                ThreadLayoutSectionViewStateV1(
                    section_key="goal",
                    title="Goal / Lane / Issue",
                    description="Shared goal structure for the selected coordination thread.",
                    order=0,
                    flex=2.4,
                    pane_key="goal",
                    view_ref="aware_goals.workflow.goal.v1",
                    view_key="aware_goals.workflow.goal.v1",
                ),
                ThreadLayoutSectionViewStateV1(
                    section_key="work_item",
                    title="Work Item",
                    description="Selected issue or work unit for the active goal focus.",
                    order=1,
                    flex=1.2,
                    pane_key="issue",
                    view_ref="aware_coordination.issue.v1",
                    view_key="issue.v1",
                ),
            ]
        if process_key == "coordination" and thread_key == "issues":
            return [
                ThreadLayoutSectionViewStateV1(
                    section_key="work_item",
                    title="Work Item",
                    description="Issue-focused coordination work surface.",
                    order=0,
                    flex=1.0,
                    pane_key="issue",
                    view_ref="aware_coordination.issue.v1",
                    view_key="issue.v1",
                )
            ]
        if process_key == "workspace":
            return [
                ThreadLayoutSectionViewStateV1(
                    section_key="workspace",
                    title="Workspace",
                    description="Workspace materialization and semantic package surface.",
                    order=0,
                    flex=1.0,
                    pane_key="workspace",
                    view_ref="aware_workspace.workspace.v1",
                    view_key="workspace.v1",
                )
            ]
        return [
            ThreadLayoutSectionViewStateV1(
                section_key="environment_home",
                title="Environment Home",
                description="Default Environment home surface.",
                order=0,
                flex=1.0,
                pane_key="environment_home",
                view_ref="aware_environment.home.v1",
                view_key="environment.home.v1",
            )
        ]

    def _mock_environment_topology(
        self,
    ) -> tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]:
        return (
            (
                "coordination",
                "Coordination",
                (
                    ("conversation", "Conversation"),
                    ("goals", "Goals"),
                    ("issues", "Issues"),
                ),
            ),
            (
                "workspace",
                "Workspace",
                (("materializations", "Materializations"),),
            ),
        )

    def _environment_process(
        self,
        *,
        process_key: str,
        title: str,
        threads: tuple[tuple[str, str], ...],
    ) -> EnvironmentProcessNavigationItemV1:
        process_id = _stable_uuid(
            self.namespace,
            "environment-process",
            process_key,
        )
        return EnvironmentProcessNavigationItemV1(
            process_id=str(process_id),
            process_key=process_key,
            title=title,
            thread_count=len(threads),
            is_selected=process_id == self.selected_process_id,
            threads=[
                EnvironmentThreadNavigationItemV1(
                    thread_id=str(
                        _stable_uuid(
                            self.namespace,
                            "environment-thread",
                            process_key,
                            thread_key,
                        )
                    ),
                    thread_key=thread_key,
                    title=thread_title,
                    is_selected=(
                        _stable_uuid(
                            self.namespace,
                            "environment-thread",
                            process_key,
                            thread_key,
                        )
                        == self.selected_thread_id
                    ),
                )
                for thread_key, thread_title in threads
            ],
        )

    def _process_id_for_thread(self, thread_id: UUID) -> UUID | None:
        for process_key, thread_keys in {
            "coordination": ("conversation", "goals", "issues"),
            "workspace": ("materializations",),
        }.items():
            for thread_key in thread_keys:
                if (
                    _stable_uuid(
                        self.namespace,
                        "environment-thread",
                        process_key,
                        thread_key,
                    )
                    == thread_id
                ):
                    return _stable_uuid(
                        self.namespace,
                        "environment-process",
                        process_key,
                    )
        return None

    def _default_thread_id_for_process(self, process_id: UUID) -> UUID | None:
        for process_key, thread_key in {
            "coordination": "conversation",
            "workspace": "materializations",
        }.items():
            if (
                _stable_uuid(self.namespace, "environment-process", process_key)
                == process_id
            ):
                return _stable_uuid(
                    self.namespace,
                    "environment-thread",
                    process_key,
                    thread_key,
                )
        return None

    def render_spec_payload(self) -> dict[str, Any]:
        status_attr_id = _stable_uuid("identity_admission", "attr", "status")
        status_tone_attr_id = _stable_uuid(
            "identity_admission",
            "attr",
            "status_tone",
        )
        display_name_attr_id = _stable_uuid(
            "identity_admission",
            "attr",
            "display_name",
        )
        public_handle_attr_id = _stable_uuid(
            "identity_admission",
            "attr",
            "public_handle",
        )
        bio_attr_id = _stable_uuid("identity_admission", "attr", "bio")
        provenance_attr_id = _stable_uuid(
            "identity_admission",
            "attr",
            "provenance",
        )
        return {
            "spec_id": str(_stable_uuid("identity_admission", "render-spec", "0.1.0")),
            "name": "identity_admission_default",
            "spec_version": "0.1.0",
            "pane_name": _PANE_KIND,
            "pane_kind": _PANE_KIND,
            "view_ref": _VIEW_REF,
            "projection_view_key": _PROJECTION_VIEW_KEY,
            "pane_config_id": str(_PANE_CONFIG_PROJECTION_EXPERIENCE_VIEW_ID),
            "projection_experience_view_id": str(_PROJECTION_EXPERIENCE_VIEW_ID),
            "state_model_id": str(_STATE_MODEL_ID),
            "root_node_key": "root",
            "renderer_requirements": (
                {
                    "capability_kind": "node_kind",
                    "capability_key": "column",
                    "is_required": True,
                },
                {
                    "capability_kind": "node_kind",
                    "capability_key": "text_input",
                    "is_required": True,
                },
                {
                    "capability_kind": "action_binding",
                    "capability_key": "view_action",
                    "is_required": True,
                },
            ),
            "nodes": (
                {
                    "node_key": "root",
                    "node_kind": "column",
                    "semantic_role": "pane",
                    "style_tokens": (
                        {
                            "token_key": "density",
                            "token_value": "compact",
                        },
                    ),
                },
                {
                    "node_key": "title",
                    "parent_node_key": "root",
                    "node_kind": "text",
                    "semantic_role": "heading",
                    "order": 0,
                    "text": "Identity admission",
                    "style_tokens": (
                        {
                            "token_key": "emphasis",
                            "token_value": "primary",
                        },
                    ),
                },
                {
                    "node_key": "status",
                    "parent_node_key": "root",
                    "node_kind": "status",
                    "semantic_role": "status",
                    "order": 1,
                    "state_bindings": (
                        {
                            "binding_key": "status_text",
                            "target_property": "text",
                            "json_path": "$.status",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(status_attr_id),
                            "transform": "text",
                            "fallback_value": "ready",
                        },
                        {
                            "binding_key": "status_tone",
                            "target_property": "tone",
                            "json_path": "$.status_tone",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(status_tone_attr_id),
                            "transform": "text",
                        },
                    ),
                },
                {
                    "node_key": "display_name",
                    "parent_node_key": "root",
                    "node_kind": "text",
                    "semantic_role": "paragraph",
                    "order": 2,
                    "state_bindings": (
                        {
                            "binding_key": "display_name_text",
                            "target_property": "text",
                            "json_path": "$.display_name",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(display_name_attr_id),
                            "transform": "text",
                            "fallback_value": "No display name configured",
                        },
                    ),
                },
                {
                    "node_key": "public_handle",
                    "parent_node_key": "root",
                    "node_kind": "text",
                    "semantic_role": "paragraph",
                    "order": 3,
                    "state_bindings": (
                        {
                            "binding_key": "public_handle_text",
                            "target_property": "text",
                            "json_path": "$.public_handle",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(public_handle_attr_id),
                            "transform": "text",
                            "fallback_value": "No public handle configured",
                        },
                    ),
                },
                self._text_input_node(
                    node_key="display_name_input",
                    order=4,
                    label="Display name",
                    json_path="$.display_name",
                    attribute_config_id=display_name_attr_id,
                ),
                self._text_input_node(
                    node_key="public_handle_input",
                    order=5,
                    label="Public handle",
                    json_path="$.public_handle",
                    attribute_config_id=public_handle_attr_id,
                ),
                self._text_input_node(
                    node_key="bio_input",
                    order=6,
                    label="Bio",
                    json_path="$.bio",
                    attribute_config_id=bio_attr_id,
                ),
                {
                    "node_key": "submit",
                    "parent_node_key": "root",
                    "node_kind": "button",
                    "semantic_role": "action",
                    "order": 7,
                    "label": "Admit identity",
                    "style_tokens": (
                        {
                            "token_key": "emphasis",
                            "token_value": "primary",
                        },
                    ),
                    "action_bindings": (
                        {
                            "binding_key": "admit_identity",
                            "event": "activate",
                            "action_key": _VIEW_ACTION_KEY,
                            "action_kind": "view_action",
                            "view_action_key": _VIEW_ACTION_KEY,
                            "projection_experience_view_invocation_action_id": str(
                                _stable_uuid(
                                    _PANE_KIND,
                                    "view-action",
                                    _VIEW_ACTION_KEY,
                                )
                            ),
                            "label": "Admit identity",
                            "receipt_policy": "show_receipt",
                            "input_bindings": (
                                {
                                    "payload_path": "profile.display_name",
                                    "source_node_key": "display_name_input",
                                },
                                {
                                    "payload_path": "profile.public_handle",
                                    "source_node_key": "public_handle_input",
                                },
                                {
                                    "payload_path": "profile.bio",
                                    "source_node_key": "bio_input",
                                },
                            ),
                        },
                    ),
                },
                {
                    "node_key": "receipt",
                    "parent_node_key": "root",
                    "node_kind": "receipt",
                    "semantic_role": "receipt",
                    "order": 8,
                    "style_tokens": (
                        {
                            "token_key": "tone",
                            "token_value": "receipt",
                        },
                    ),
                    "state_bindings": (
                        {
                            "binding_key": "source_receipt",
                            "target_property": "text",
                            "json_path": "$.receipt.summary",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(provenance_attr_id),
                            "transform": "text",
                        },
                        {
                            "binding_key": "source_receipt_visible",
                            "target_property": "visible",
                            "json_path": "$.receipt.summary",
                            "state_model_id": str(_STATE_MODEL_ID),
                            "state_attribute_config_id": str(provenance_attr_id),
                            "transform": "not_empty",
                        },
                    ),
                },
            ),
        }

    def _text_input_node(
        self,
        *,
        node_key: str,
        order: int,
        label: str,
        json_path: str,
        attribute_config_id: UUID,
    ) -> dict[str, Any]:
        return {
            "node_key": node_key,
            "parent_node_key": "root",
            "node_kind": "text_input",
            "semantic_role": "input",
            "order": order,
            "label": label,
            "state_bindings": (
                {
                    "binding_key": f"{node_key}_value",
                    "target_property": "value",
                    "json_path": json_path,
                    "state_model_id": str(_STATE_MODEL_ID),
                    "state_attribute_config_id": str(attribute_config_id),
                    "transform": "text",
                },
            ),
        }

    def _apply_profile_payload(self, payload: dict[str, Any]) -> None:
        profile = payload.get("profile")
        if not isinstance(profile, dict):
            profile = payload.get("create_profile_request")
        if not isinstance(profile, dict):
            profile = payload
        display_name = _text_or_none(profile.get("display_name"))
        public_handle = _text_or_none(profile.get("public_handle"))
        bio = _text_or_none(profile.get("bio"))
        if display_name is not None:
            self.display_name = display_name
        if public_handle is not None:
            self.public_handle = public_handle
        if bio is not None:
            self.bio = bio
        self.status = "admitted"
        self.action_count += 1
        self.receipt_summary = f"mock admission accepted for {self.display_name}"

    def _status_tone(self) -> str:
        if self.status == "admitted":
            return "success"
        return "neutral"

    def _materialized_pane_state(self) -> InterfaceMaterializedPaneState:
        pane_config, view = self._identity_pane_config_and_view()
        window_key, layout_key, section_key = self._pane_view_default_mount_location(
            view,
            fallback_section_key=_SECTION_KEY,
        )
        state: dict[str, object] = {
            "status": self.status,
            "status_tone": self._status_tone(),
            "display_name": self.display_name,
            "public_handle": self.public_handle,
            "bio": self.bio,
            "provenance": {
                "source_kind": "interface_host_mock_adapter",
                "scene_key": "identity_admission",
                "action_count": self.action_count,
            },
            "receipt": {
                "summary": self.receipt_summary,
                "action_count": self.action_count,
            },
        }
        return InterfaceMaterializedPaneState(
            pane_state_key=":".join(
                [
                    window_key,
                    layout_key,
                    section_key,
                    pane_config.pane_kind or _PANE_KIND,
                    str(pane_config.pane_config_id),
                    "",
                ]
            ),
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            pane_kind=pane_config.pane_kind or _PANE_KIND,
            pane_config_id=pane_config.pane_config_id,
            pane_package_id=pane_config.pane_package_id,
            focus_scope_id=None,
            branch_id=None,
            projection_experience_view_id=view.projection_experience_view_id,
            projection_view_id=view.projection_view_key,
            state_model_id=view.state_model_id,
            projection_hash=None,
            status="materialized",
            head_commit_id=None,
            graph_hash_post=None,
            materialized_at=_utc_now_iso(),
            state=state,
            provenance={
                "source_kind": "interface_host_mock_adapter",
                "scene_key": "identity_admission",
            },
        )

    def _identity_resolved_pane_descriptor(self) -> InterfaceResolvedPaneDescriptor:
        pane_config, view = self._identity_pane_config_and_view()
        window_key, layout_key, section_key = self._pane_view_default_mount_location(
            view,
            fallback_section_key=_SECTION_KEY,
        )
        actions = self._experience_view_actions()
        action_targets = tuple(
            InterfaceResolvedPaneActionTarget(
                action_key=action.action_key,
                action_kind=action.target_kind,
                target_ref=action.endpoint_ref,
                view_invocation_action_config_id=action.view_invocation_action_config_id,
                label=action.label,
                receipt_policy=action.receipt_policy,
            )
            for action in actions
        )
        return InterfaceResolvedPaneDescriptor(
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            pane_kind=pane_config.pane_kind or _PANE_KIND,
            pane_config_id=pane_config.pane_config_id,
            pane_package_id=pane_config.pane_package_id,
            pane_package_name=pane_config.pane_package_name,
            object_projection_graph_observable_id=(
                view.object_projection_graph_observable_id
            ),
            projection_experience_graph_identity_id=(
                view.projection_experience_graph_identity_id
            ),
            object_projection_graph_identity_id=view.object_projection_graph_identity_id,
            section_graph_binding_key=(
                view.section_graph_binding_key or _EXPERIENCE_SECTION_GRAPH_BINDING_KEY
            ),
            projection_experience_view_instance_id=(
                _PROJECTION_EXPERIENCE_VIEW_INSTANCE_ID
            ),
            projection_experience_view_id=view.projection_experience_view_id,
            projection_view_id=view.projection_view_key,
            view_ref=view.view_ref,
            projection_view_key=view.projection_view_key,
            state_model_id=view.state_model_id,
            state_source_kind="host_pane_contribution",
            action_keys=tuple(action.action_key for action in actions),
            action_targets=action_targets,
        )

    def _network_territory_resolved_pane_descriptor(
        self,
    ) -> InterfaceResolvedPaneDescriptor:
        pane_config, view = self._network_territory_pane_config_and_view()
        window_key, layout_key, section_key = self._pane_view_default_mount_location(
            view,
            fallback_section_key="inspector",
        )
        return InterfaceResolvedPaneDescriptor(
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            pane_kind=pane_config.pane_kind or _NETWORK_PANE_KIND,
            pane_config_id=pane_config.pane_config_id,
            pane_package_id=pane_config.pane_package_id,
            pane_package_name=pane_config.pane_package_name,
            object_projection_graph_observable_id=(
                view.object_projection_graph_observable_id
            ),
            projection_experience_graph_identity_id=(
                view.projection_experience_graph_identity_id
            ),
            object_projection_graph_identity_id=view.object_projection_graph_identity_id,
            section_graph_binding_key=view.section_graph_binding_key,
            projection_experience_view_id=view.projection_experience_view_id,
            projection_view_id=view.projection_view_key,
            view_ref=view.view_ref,
            projection_view_key=view.projection_view_key,
            state_model_id=view.state_model_id,
            state_source_kind="host_pane_contribution",
            action_keys=("discover_territory",),
            action_targets=(
                InterfaceResolvedPaneActionTarget(
                    action_key="discover_territory",
                    action_kind="api",
                    target_ref=_NETWORK_ENDPOINT_REF,
                ),
            ),
        )

    def _network_territory_materialized_pane_state(
        self,
    ) -> InterfaceMaterializedPaneState:
        pane_config, view = self._network_territory_pane_config_and_view()
        window_key, layout_key, section_key = self._pane_view_default_mount_location(
            view,
            fallback_section_key="inspector",
        )
        state = self._network_territory_state_payload()
        return InterfaceMaterializedPaneState(
            pane_state_key=":".join(
                [
                    window_key,
                    layout_key,
                    section_key,
                    _NETWORK_PANE_KIND,
                    str(pane_config.pane_config_id),
                    "",
                ]
            ),
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            pane_kind=_NETWORK_PANE_KIND,
            pane_config_id=pane_config.pane_config_id,
            pane_package_id=pane_config.pane_package_id,
            focus_scope_id=None,
            branch_id=None,
            projection_experience_view_id=view.projection_experience_view_id,
            projection_view_id=view.projection_view_key,
            state_model_id=view.state_model_id,
            projection_hash=None,
            status="materialized",
            head_commit_id=None,
            graph_hash_post=None,
            materialized_at=_utc_now_iso(),
            state=state,
            provenance={
                "source_kind": "interface_host_mock_network_territory_adapter",
                "scene_key": "network_territory",
                "authority_source_url": _NETWORK_MOCK_AUTHORITY_URL,
                "state_provider_ref": (
                    "aware_network_sdk.view_state_providers."
                    "network_territory_discovery_view_state"
                ),
            },
        )

    def _network_territory_state_payload(self) -> dict[str, object]:
        view_state = network_territory_discovery_view_state(
            provider_input=NetworkTerritoryDiscoveryV1ProviderInput(
                receipt=self._mock_network_territory_receipt(),
                authority_source_url=_NETWORK_MOCK_AUTHORITY_URL,
                provenance=NetworkViewProviderProvenanceV1(
                    source_kind="interface_host_mock_network_territory_adapter",
                    authority_source_url=_NETWORK_MOCK_AUTHORITY_URL,
                    request_id=str(
                        _stable_uuid(
                            self.namespace,
                            "network-territory-request",
                        )
                    ),
                ),
            )
        )
        return cast(
            dict[str, object],
            view_state.model_dump(mode="json", exclude_none=True),
        )

    def _mock_network_territory_receipt(self) -> dict[str, object]:
        node_id = str(_stable_uuid(self.namespace, "network-node"))
        environment_id = str(_stable_uuid(self.namespace, "environment"))
        service_id = str(_stable_uuid(self.namespace, "environment-service"))
        peer_node_id = str(_stable_uuid(self.namespace, "kernel-services-node"))
        return {
            "request_id": str(
                _stable_uuid(self.namespace, "network-territory-request")
            ),
            "success": True,
            "summary": "1 nodes, 1 environments, 1 hosted services",
            "nodes": [
                {
                    "node": {
                        "node_id": node_id,
                        "public_key": f"mock:{self.namespace}:node",
                        "hostname": f"{self.namespace}-local-node",
                        "port": 8913,
                        "base_url": "mock://network_territory/local-node",
                        "status": "mocked",
                        "last_seen_at": _utc_now_iso(),
                    },
                    "environments": [
                        {
                            "node_id": node_id,
                            "environment_id": environment_id,
                            "environment_key": "home-story",
                            "environment_title": "Home Story Environment",
                            "role": "primary",
                            "is_active": True,
                            "priority": 0,
                            "status": "mocked",
                            "experience_names": ["aware_home.story"],
                            "environment_config_key": "home.story",
                        }
                    ],
                    "hosted_services": [
                        {
                            "service_id": service_id,
                            "service_name": "aware_environment",
                            "service_package_names": ["aware_environment"],
                            "endpoint_refs": ["environment.ready.ensure_ready"],
                            "stream_endpoint_refs": [],
                            "host_id": f"{self.namespace}-environment-host",
                            "host_version": "mock",
                            "protocol_version": "mock-v0",
                            "supports_stream_events": False,
                        }
                    ],
                    "peers": [
                        {
                            "edge_id": str(
                                _stable_uuid(self.namespace, "network-peer-edge")
                            ),
                            "source_node_id": node_id,
                            "target_node_id": peer_node_id,
                            "peer_node_id": peer_node_id,
                            "peer_base_url": "mock://network_territory/kernel-services",
                            "direction": "outgoing",
                            "status": "mocked",
                            "trust_score": 1.0,
                            "connected_at": _utc_now_iso(),
                        }
                    ],
                }
            ],
        }

    def _network_territory_pane_config_and_view(
        self,
    ) -> tuple[InterfacePaneConfigBundle, InterfacePaneProjectionExperienceViewBundle]:
        pane_config = self._pane_config_by_name(_NETWORK_PANE_KIND)
        view = self._default_projection_view(
            pane_config,
            fallback_view_ref=_NETWORK_VIEW_REF,
            fallback_projection_view_key=_NETWORK_PROJECTION_VIEW_KEY,
            fallback_projection_experience_view_id=(
                _NETWORK_PROJECTION_EXPERIENCE_VIEW_ID
            ),
            fallback_state_model_id=_NETWORK_STATE_MODEL_ID,
        )
        return pane_config, view

    def _identity_pane_config_and_view(
        self,
    ) -> tuple[InterfacePaneConfigBundle, InterfacePaneProjectionExperienceViewBundle]:
        pane_config = self._pane_config_by_name(_PANE_KIND)
        view = self._default_projection_view(
            pane_config,
            fallback_view_ref=_VIEW_REF,
            fallback_projection_view_key=_PROJECTION_VIEW_KEY,
            fallback_projection_experience_view_id=_PROJECTION_EXPERIENCE_VIEW_ID,
            fallback_state_model_id=_STATE_MODEL_ID,
        )
        return pane_config, view

    def _pane_config_by_name(self, pane_name: str) -> InterfacePaneConfigBundle:
        if self.interface_config_bundle is not None:
            for pane_config in self.interface_config_bundle.pane_configs:
                if pane_config.name == pane_name:
                    return pane_config
        if pane_name == _PANE_KIND:
            return InterfacePaneConfigBundle(
                pane_config_id=_PANE_CONFIG_ID,
                pane_package_id=_PANE_PACKAGE_ID,
                pane_package_name="aware-identity-admission-pane",
                name=_PANE_KIND,
                pane_kind=_PANE_KIND,
            )
        return InterfacePaneConfigBundle(
            pane_config_id=_NETWORK_PANE_CONFIG_ID,
            pane_package_id=_NETWORK_PANE_PACKAGE_ID,
            pane_package_name="aware-network-territory-pane",
            name=_NETWORK_PANE_KIND,
            pane_kind=_NETWORK_PANE_KIND,
        )

    @staticmethod
    def _default_projection_view(
        pane_config: InterfacePaneConfigBundle,
        *,
        fallback_view_ref: str,
        fallback_projection_view_key: str,
        fallback_projection_experience_view_id: UUID,
        fallback_state_model_id: UUID,
    ) -> InterfacePaneProjectionExperienceViewBundle:
        return next(
            (
                view
                for view in pane_config.projection_experience_views
                if view.is_default
            ),
            next(iter(pane_config.projection_experience_views), None),
        ) or InterfacePaneProjectionExperienceViewBundle(
            binding_id=_stable_uuid(_NETWORK_PANE_KIND, "view-binding"),
            projection_experience_view_id=fallback_projection_experience_view_id,
            state_model_id=fallback_state_model_id,
            view_ref=fallback_view_ref,
            projection_view_key=fallback_projection_view_key,
            is_default=True,
        )

    def _pane_view_default_mount_location(
        self,
        view: InterfacePaneProjectionExperienceViewBundle,
        *,
        fallback_section_key: str,
    ) -> tuple[str, str, str]:
        mount = (
            next(iter(view.section_mounts), None)
            if len(view.section_mounts) == 1
            else None
        )
        if self.interface_config_bundle is not None and mount is not None:
            for window in self.interface_config_bundle.window_configs:
                for layout in window.layout_configs:
                    for section in layout.sections:
                        if (
                            section.layout_config_section_config_id
                            == mount.layout_config_section_config_id
                        ):
                            return window.key, layout.key, section.key
        return _WINDOW_KEY, _LAYOUT_KEY, fallback_section_key


class MockInterfaceTransportSession:
    def __init__(self, *, adapter: MockIdentityAdmissionServiceAdapter) -> None:
        self.adapter = adapter
        self.client = adapter
        self.profile = InterfaceTransportProfile.create(
            interface_id=adapter.interface_id,
            interface_session_id=adapter.interface_session_id,
            session_label=adapter.host_label,
            capabilities=(
                "interface_control_plane",
                "pane_render_spec",
                "mock_service_adapter",
            ),
        )
        self.binding: InterfaceTransportBindingState | None = None

    async def ensure_registered(self) -> InterfaceTransportBindingState:
        self.binding = self._binding(last_seen_at=_utc_now_iso())
        return self.binding

    async def login_with_token(self, *, token: str) -> object:
        _ = token
        self.binding = self._binding(last_seen_at=_utc_now_iso())
        return SimpleNamespace(actor_id=self.adapter.actor_id)

    async def heartbeat(self, *, timestamp: str | None = None) -> object:
        self.binding = self._binding(last_seen_at=timestamp or _utc_now_iso())
        return SimpleNamespace(last_seen_at=self.binding.last_seen_at)

    async def close(self) -> None:
        self.binding = None

    def _binding(self, *, last_seen_at: str) -> InterfaceTransportBindingState:
        return InterfaceTransportBindingState(
            actor_id=self.adapter.actor_id,
            interface_id=self.adapter.interface_id,
            interface_session_id=self.adapter.interface_session_id,
            session_label=self.adapter.host_label,
            capabilities=self.profile.capabilities,
            protocol_version=self.profile.protocol_version,
            last_seen_at=last_seen_at,
        )


__all__ = [
    "MOCK_IDENTITY_ADMISSION_ENDPOINT",
    "MockIdentityAdmissionServiceAdapter",
    "MockInterfaceTransportSession",
    "is_mock_service_endpoint",
]
