from __future__ import annotations

import pytest

from aware_experience_sdk import (
    ActivateExperienceLayoutGraphBindingRequest as SdkActivateExperienceLayoutGraphBindingRequest,
    AdmitExperienceActorConfigRequest as SdkAdmitExperienceActorConfigRequest,
    EnvironmentActorAdmissionReceipt as SdkEnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt as SdkEnvironmentSessionJoinReceipt,
    ExperienceSessionAttentionResolutionRequest as SdkExperienceSessionAttentionResolutionRequest,
    GetExperienceLayoutGraphBindingCatalogRequest as SdkGetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingStateRequest as SdkGetExperienceLayoutGraphBindingStateRequest,
    ResolveExperienceSessionContextRequest as SdkResolveExperienceSessionContextRequest,
    ResolveExperienceSessionViewFrameRequest as SdkResolveExperienceSessionViewFrameRequest,
    EnsureExperienceSessionHandoffRequest,
    ExperienceSessionIdentityEvidence as SdkExperienceSessionIdentityEvidence,
    GetExperienceSessionHandoffStatusRequest as SdkGetExperienceSessionHandoffStatusRequest,
    InvokeExperienceViewInvocationActionRequest as SdkInvokeExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionRequest as SdkRecordExperienceViewInvocationActionRequest,
    ResolveExperiencePackageProjectionOwnershipRequest as SdkResolveExperiencePackageProjectionOwnershipRequest,
    UpsertExperienceEnvironmentProfileRequest as SdkUpsertExperienceEnvironmentProfileRequest,
    WatchExperienceViewStateRequest as SdkWatchExperienceViewStateRequest,
)
from aware_experience_sdk import build_experience_sdk_client
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
)
from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ApplyExperienceViewEventTransitionRequest,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceSectionGraphBindingCatalogRequest,
    InvokeExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionRequest,
)
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    GetExperienceSessionHandoffStatusRequest,
)
from aware_experience_service_dto.experience.session_context.models import (
    ExperienceSessionAttentionResolutionRequest,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    MountExperienceSessionProfileRequest,
    StartExperienceSessionRequest,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)


class _FakeEnvironmentProfileCapability:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def upsert_experience_environment_profile(self, request: object) -> str:
        self.calls.append(("upsert", request))
        return "upserted"

    async def provision_experience_environment_profile(self, request: object) -> str:
        self.calls.append(("provision", request))
        return "provisioned"

    async def apply_experience_environment_profile_programs(
        self, request: object
    ) -> str:
        self.calls.append(("apply", request))
        return "applied"


class _FakeActorAdmissionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def admit_experience_actor_config(self, request: object) -> str:
        self.calls.append(request)
        return "admitted"


class _FakePackageMaterializationCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def resolve_experience_package_projection_ownership(
        self, request: object
    ) -> str:
        self.calls.append(request)
        return "projection-ownership"


class _FakeApplyViewEventTransitionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def apply_experience_view_event_transition(self, request: object) -> str:
        self.calls.append(request)
        return "transitioned"


class _FakeGetCatalogCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def get_experience_section_graph_binding_catalog(
        self, request: object
    ) -> str:
        self.calls.append(request)
        return "catalog"


class _FakeGetLayoutCatalogCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def get_experience_layout_graph_binding_catalog(self, request: object) -> str:
        self.calls.append(request)
        return "layout-catalog"


class _FakeGetLayoutStateCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def get_experience_layout_graph_binding_state(self, request: object) -> str:
        self.calls.append(request)
        return "layout-state"


class _FakeActivateLayoutCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def activate_experience_layout_graph_binding(self, request: object) -> str:
        self.calls.append(request)
        return "layout-activated"


class _FakeRecordViewInvocationActionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def record_experience_view_invocation_action(self, request: object) -> str:
        self.calls.append(request)
        return "recorded"


class _FakeInvokeViewInvocationActionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def invoke_experience_view_invocation_action(self, request: object) -> str:
        self.calls.append(request)
        return "invoked"


class _FakeSessionHandoffCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def ensure_experience_session_handoff(self, request: object) -> str:
        self.calls.append(request)
        return "handoff"

    async def get_experience_session_handoff_status(self, request: object) -> str:
        self.calls.append(request)
        return "handoff-status"


class _FakeSessionContextCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def resolve_experience_session_context(self, request: object) -> str:
        self.calls.append(request)
        return "session-context"


class _FakeSessionViewFrameCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def resolve_experience_session_view_frame(self, request: object) -> str:
        self.calls.append(request)
        return "session-view-frame"


class _FakeWatchExperienceViewStateCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def watch_experience_view_state(self, request: object) -> str:
        self.calls.append(request)
        return "view-state"


class _FakeStartExperienceSessionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def start_experience_session(self, request: object) -> str:
        self.calls.append(request)
        return "session-started"


class _FakeDescribeExperienceSessionCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def describe_experience_session(self, request: object) -> str:
        self.calls.append(request)
        return "session-described"


class _FakeMountExperienceSessionProfileCapability:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def mount_experience_session_profile(self, request: object) -> str:
        self.calls.append(request)
        return "profile-mounted"


class _FakeExperienceApi:
    def __init__(self) -> None:
        self.describe_experience_session = _FakeDescribeExperienceSessionCapability()
        self.start_experience_session = _FakeStartExperienceSessionCapability()
        self.mount_experience_session_profile = (
            _FakeMountExperienceSessionProfileCapability()
        )
        self.actor_admission = _FakeActorAdmissionCapability()
        self.environment_profile = _FakeEnvironmentProfileCapability()
        self.package_materialization = _FakePackageMaterializationCapability()
        self.apply_experience_view_event_transition = (
            _FakeApplyViewEventTransitionCapability()
        )
        self.get_experience_section_graph_binding_catalog = _FakeGetCatalogCapability()
        self.get_experience_layout_graph_binding_catalog = (
            _FakeGetLayoutCatalogCapability()
        )
        self.get_experience_layout_graph_binding_state = _FakeGetLayoutStateCapability()
        self.activate_experience_layout_graph_binding = _FakeActivateLayoutCapability()
        self.record_experience_view_invocation_action = (
            _FakeRecordViewInvocationActionCapability()
        )
        self.invoke_experience_view_invocation_action = (
            _FakeInvokeViewInvocationActionCapability()
        )
        self.session_handoff = _FakeSessionHandoffCapability()
        self.session_context = _FakeSessionContextCapability()
        self.session_view_frame = _FakeSessionViewFrameCapability()
        self.watch_experience_view_state = _FakeWatchExperienceViewStateCapability()


class _FakeApiClient:
    def __init__(self) -> None:
        self.experience = _FakeExperienceApi()


@pytest.mark.asyncio
async def test_experience_sdk_builds_separate_session_and_profile_mount_dtos() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.describe_experience_session(
            experience_session_id="711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
        )
        == "session-described"
    )
    describe_request = api_client.experience.describe_experience_session.calls[0]
    assert str(describe_request.experience_session_id) == (
        "711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
    )

    assert (
        await sdk.start_experience_session(
            environment_experience_id="53753d86-6a54-427d-9e36-951d5865c8a2",
            environment_id="f20e7f00-550c-4fd3-b17f-cdf09816d7d2",
            identity_session_id="ad7861a2-fc6e-4715-af72-ce9480ff4c36",
            environment_session_id="d7ca2013-db12-4333-9de4-7b01c81592fa",
        )
        == "session-started"
    )
    session_request = api_client.experience.start_experience_session.calls[0]
    assert isinstance(session_request, StartExperienceSessionRequest)
    assert str(session_request.environment_id) == "f20e7f00-550c-4fd3-b17f-cdf09816d7d2"
    assert session_request.state == "active"

    assert (
        await sdk.mount_experience_session_profile(
            experience_session_id="1b06843e-0049-467d-9176-230f77a9fa38",
            profile_id="5480f92b-45ef-4eec-bca0-c377c7fc7a65",
            metadata_json={"source": "sdk-test"},
        )
        == "profile-mounted"
    )
    mount_request = api_client.experience.mount_experience_session_profile.calls[0]
    assert isinstance(mount_request, MountExperienceSessionProfileRequest)
    assert mount_request.status == "active"
    assert mount_request.metadata_json == {"source": "sdk-test"}


class _EnvironmentSdkReceiptWrapper:
    def __init__(self, dto_receipt: EnvironmentActorAdmissionReceipt) -> None:
        self.dto_receipt = dto_receipt


def _session_environment_admission_payload() -> dict[str, object]:
    actor_id = "53753d86-6a54-427d-9e36-951d5865c8a2"
    environment_id = "ad7861a2-fc6e-4715-af72-ce9480ff4c36"
    environment_profile_actor_config_id = "d7ca2013-db12-4333-9de4-7b01c81592fa"
    actor_config_role_config_id = "1b06843e-0049-467d-9176-230f77a9fa38"
    role_config_id = "5480f92b-45ef-4eec-bca0-c377c7fc7a65"
    class_instance_identity_id = "711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
    return {
        "accepted": True,
        "status": "admitted",
        "actor_id": actor_id,
        "environment_id": environment_id,
        "environment_profile_id": "f20e7f00-550c-4fd3-b17f-cdf09816d7d2",
        "environment_profile_actor_config_id": environment_profile_actor_config_id,
        "actor_config_id": "1f654643-c940-48e8-b1c5-0f904089b664",
        "class_instance_identity_id": class_instance_identity_id,
        "requested_role_config_names": ["aware.interface.environment.actor"],
        "bindings": [
            {
                "environment_profile_actor_config_id": (
                    environment_profile_actor_config_id
                ),
                "actor_config_role_config_id": actor_config_role_config_id,
                "role_config_id": role_config_id,
                "role_config_name": "aware.interface.environment.actor",
                "actor_id": actor_id,
                "role_id": "c1891295-150e-470b-b714-9f194da6f874",
                "actor_role_id": "9862bd10-68c3-4d71-96de-495a4a14c695",
                "role_class_instance_id": "18d12782-87b8-4b69-bc37-d9f6eb6b473c",
                "class_instance_identity_id": class_instance_identity_id,
                "role_config_class_config_id": "9118d0ff-3011-4575-868f-801794ebc7d5",
                "object_instance_graph_identity_id": (
                    "24c3d066-e758-46ea-a534-f451de3eac0d"
                ),
                "object_instance_graph_branch_key": "all",
            }
        ],
        "evidence": {"source": "environment-sdk"},
    }


def _session_environment_join_payload() -> dict[str, object]:
    actor_id = "53753d86-6a54-427d-9e36-951d5865c8a2"
    environment_id = "ad7861a2-fc6e-4715-af72-ce9480ff4c36"
    environment_profile_id = "f20e7f00-550c-4fd3-b17f-cdf09816d7d2"
    environment_session_id = "aee88dc5-14e7-4949-a236-a7e0b4a6cc94"
    identity_session_id = "ce49e484-e177-40e5-8f22-5d2a2bf26c1e"
    return {
        "accepted": True,
        "status": "joined",
        "actor_id": actor_id,
        "environment_id": environment_id,
        "environment_profile_id": environment_profile_id,
        "environment_session_id": environment_session_id,
        "environment_session_key": "environment-session:test",
        "identity_evidence": {
            "identity_session": {
                "session_id": identity_session_id,
                "session_config_id": "0bc7226c-ad34-4efb-9f5d-8bff6a47c932",
                "key": "environment-session:test",
                "status": "active",
                "member_count": 1,
            },
            "identity_member": {
                "session_member_id": "e367cf25-91f8-447b-b891-7727440c23db",
                "session_id": identity_session_id,
                "actor_id": actor_id,
                "session_actor_config_id": "e469a177-52b8-405b-a36b-84590e7428b8",
                "status": "active",
            },
            "identity_actor_roles": [],
            "evidence": {"source": "environment-session-sdk"},
        },
        "evidence": {"source": "environment-session-sdk"},
    }


def _experience_actor_admission_payload() -> dict[str, object]:
    actor_id = "53753d86-6a54-427d-9e36-951d5865c8a2"
    role_config_id = "c4323b60-19a7-4952-8053-0e45dc5c0bf6"
    return {
        "accepted": True,
        "status": "admitted",
        "experience_name": "aware_control_identity",
        "actor_id": actor_id,
        "actor_config_id": "f56e7633-e14a-4d0d-b0e0-ce75bcf034f3",
        "class_instance_identity_id": "a65da9a6-952d-470e-82f1-6e62521ddb87",
        "requested_role_config_ids": [role_config_id],
        "requested_role_config_names": ["aware.experience.participant"],
        "bindings": [
            {
                "actor_config_role_config_id": "8a14235d-392d-4af7-bcf8-f7620d6bef54",
                "role_config_id": role_config_id,
                "role_config_name": "aware.experience.participant",
                "actor_id": actor_id,
                "role_id": "d3069fb4-375d-49dc-b15f-819e453d9ab0",
                "actor_role_id": "f4659352-99bc-45aa-907d-214e4d7ba5d5",
                "role_class_instance_id": "ca377f48-5623-409f-a723-04a09e37a3aa",
                "class_instance_identity_id": "a65da9a6-952d-470e-82f1-6e62521ddb87",
                "role_config_class_config_id": "62fd49f2-391e-48de-b2ff-7351a37f7d12",
                "object_instance_graph_identity_id": "8b3505c0-565c-45b0-9234-91a5e72144e1",
                "object_instance_graph_branch_key": "all",
            }
        ],
        "evidence": {"source": "experience-actor-admission-sdk"},
    }


def test_experience_sdk_exports_generated_request_dtos() -> None:
    assert SdkAdmitExperienceActorConfigRequest is AdmitExperienceActorConfigRequest
    assert SdkEnvironmentActorAdmissionReceipt is EnvironmentActorAdmissionReceipt
    assert SdkEnvironmentSessionJoinReceipt is EnvironmentSessionJoinReceipt
    assert SdkExperienceSessionIdentityEvidence is not None
    assert (
        SdkUpsertExperienceEnvironmentProfileRequest
        is UpsertExperienceEnvironmentProfileRequest
    )
    assert (
        SdkGetExperienceSessionHandoffStatusRequest
        is GetExperienceSessionHandoffStatusRequest
    )
    assert (
        SdkResolveExperienceSessionContextRequest
        is ResolveExperienceSessionContextRequest
    )
    assert (
        SdkResolveExperienceSessionViewFrameRequest
        is ResolveExperienceSessionViewFrameRequest
    )
    assert SdkWatchExperienceViewStateRequest is WatchExperienceViewStateRequest
    assert (
        SdkExperienceSessionAttentionResolutionRequest
        is ExperienceSessionAttentionResolutionRequest
    )
    assert (
        SdkRecordExperienceViewInvocationActionRequest
        is RecordExperienceViewInvocationActionRequest
    )
    assert (
        SdkInvokeExperienceViewInvocationActionRequest
        is InvokeExperienceViewInvocationActionRequest
    )
    assert (
        SdkResolveExperiencePackageProjectionOwnershipRequest
        is ResolveExperiencePackageProjectionOwnershipRequest
    )
    assert (
        SdkGetExperienceLayoutGraphBindingCatalogRequest
        is GetExperienceLayoutGraphBindingCatalogRequest
    )
    assert (
        SdkGetExperienceLayoutGraphBindingStateRequest
        is GetExperienceLayoutGraphBindingStateRequest
    )
    assert (
        SdkActivateExperienceLayoutGraphBindingRequest
        is ActivateExperienceLayoutGraphBindingRequest
    )


@pytest.mark.asyncio
async def test_experience_sdk_routes_environment_profile_facade_methods() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert await sdk.upsert_environment_profile({"profile": "p"}) == "upserted"
    assert await sdk.provision_environment_profile({"seed": "default"}) == "provisioned"
    assert (
        await sdk.apply_environment_profile_programs({"phase": "bootstrap"})
        == "applied"
    )

    assert api_client.experience.environment_profile.calls == [
        ("upsert", {"profile": "p"}),
        ("provision", {"seed": "default"}),
        ("apply", {"phase": "bootstrap"}),
    ]


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_environment_profile_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.upsert_environment_profile(
            environment_id="53753d86-6a54-427d-9e36-951d5865c8a2",
            experience_name="aware_control",
            profile={
                "key": "os.default",
                "events": [
                    {
                        "event_config_ref": "identity.admitted",
                        "actions": [
                            {"action_config_ref": "experience.focus.actor_home"}
                        ],
                    }
                ],
            },
            validate_only=True,
        )
        == "upserted"
    )

    _, request = api_client.experience.environment_profile.calls[0]
    assert isinstance(request, UpsertExperienceEnvironmentProfileRequest)
    assert request.experience_name == "aware_control"
    assert request.profile.key == "os.default"
    assert request.validate_only is True


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_actor_config_admission_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.admit_actor_config(
            experience_name="aware_coordination",
            actor_id="53753d86-6a54-427d-9e36-951d5865c8a2",
            actor_config_id="1f654643-c940-48e8-b1c5-0f904089b664",
            class_instance_identity_id="711e6e1c-58cd-44b7-bfb3-68a12b7437fb",
            requested_role_config_names=["aware.conversation.participant"],
            reason="conversation admission",
            evidence={"source": "sdk-test"},
        )
        == "admitted"
    )

    request = api_client.experience.actor_admission.calls[0]
    assert isinstance(request, AdmitExperienceActorConfigRequest)
    assert request.experience_name == "aware_coordination"
    assert str(request.actor_id) == "53753d86-6a54-427d-9e36-951d5865c8a2"
    assert str(request.actor_config_id) == "1f654643-c940-48e8-b1c5-0f904089b664"
    assert str(request.class_instance_identity_id) == (
        "711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
    )
    assert request.requested_role_config_names == ["aware.conversation.participant"]
    assert request.reason == "conversation admission"
    assert request.evidence == {"source": "sdk-test"}


@pytest.mark.asyncio
async def test_experience_sdk_builds_package_projection_ownership_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.resolve_package_projection_ownership(
            workspace_root="/repo",
            experience_toml_path="/repo/workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml",
            package_name="aware-control",
            experience_name="aware_control",
        )
        == "projection-ownership"
    )

    request = api_client.experience.package_materialization.calls[0]
    assert isinstance(request, ResolveExperiencePackageProjectionOwnershipRequest)
    assert request.workspace_root == "/repo"
    assert (
        request.experience_toml_path
        == "/repo/workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml"
    )
    assert request.package_name == "aware-control"
    assert request.experience_name == "aware_control"
    assert request.validate_only is True


@pytest.mark.asyncio
async def test_experience_sdk_routes_view_event_transition() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.apply_view_event_transition({"transition_key": "identity.actor_home"})
        == "transitioned"
    )

    capability = api_client.experience.apply_experience_view_event_transition
    assert capability.calls == [{"transition_key": "identity.actor_home"}]


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_transition_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.apply_view_event_transition(
            experience_name="aware_control_identity",
            profile_key="os.default",
            transition_key="identity_admission.actor_home",
            source_view_ref="aware_control_identity.identity.admission.v1",
            event_type="identity.admitted",
            action_type="experience.focus.actor_home",
            focus_scope_title="Actor home",
        )
        == "transitioned"
    )

    capability = api_client.experience.apply_experience_view_event_transition
    request = capability.calls[0]
    assert isinstance(request, ApplyExperienceViewEventTransitionRequest)
    assert request.experience_name == "aware_control_identity"
    assert request.profile_key == "os.default"
    assert request.transition_key == "identity_admission.actor_home"
    assert request.event_type == "identity.admitted"
    assert request.target_binding_key is None
    assert request.focus_scope_title == "Actor home"


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_catalog_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.get_section_graph_binding_catalog(
            experience_name="aware_control_identity",
            binding_keys=["actor.home"],
        )
        == "catalog"
    )

    capability = api_client.experience.get_experience_section_graph_binding_catalog
    request = capability.calls[0]
    assert isinstance(request, GetExperienceSectionGraphBindingCatalogRequest)
    assert request.experience_name == "aware_control_identity"
    assert request.binding_keys == ["actor.home"]


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_layout_catalog_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.get_layout_graph_binding_catalog(
            experience_name="aware_home",
            layout_binding_keys=["home.configuration_map"],
        )
        == "layout-catalog"
    )

    capability = api_client.experience.get_experience_layout_graph_binding_catalog
    request = capability.calls[0]
    assert isinstance(request, GetExperienceLayoutGraphBindingCatalogRequest)
    assert request.experience_name == "aware_home"
    assert request.layout_binding_keys == ["home.configuration_map"]


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_layout_state_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.get_layout_graph_binding_state(
            experience_name="aware_home",
            layout_binding_key="home.configuration_map",
        )
        == "layout-state"
    )

    capability = api_client.experience.get_experience_layout_graph_binding_state
    request = capability.calls[0]
    assert isinstance(request, GetExperienceLayoutGraphBindingStateRequest)
    assert request.experience_name == "aware_home"
    assert request.layout_binding_key == "home.configuration_map"


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_layout_activation_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.activate_layout_graph_binding(
            experience_name="aware_home",
            layout_binding_key="home.configuration_map",
            activation_scope={
                "window_key": "main",
                "layout_key": "configuration_map",
            },
            rationale="enter home",
        )
        == "layout-activated"
    )

    capability = api_client.experience.activate_experience_layout_graph_binding
    request = capability.calls[0]
    assert isinstance(request, ActivateExperienceLayoutGraphBindingRequest)
    assert request.experience_name == "aware_home"
    assert request.layout_binding_key == "home.configuration_map"
    assert request.activation_scope is not None
    assert request.activation_scope.window_key == "main"
    assert request.activation_scope.layout_key == "configuration_map"
    assert request.rationale == "enter home"


@pytest.mark.asyncio
async def test_experience_sdk_routes_view_invocation_action_provenance() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.record_view_invocation_action(
            {"experience_name": "aware_control_identity"}
        )
        == "recorded"
    )

    capability = api_client.experience.record_experience_view_invocation_action
    assert capability.calls == [{"experience_name": "aware_control_identity"}]


@pytest.mark.asyncio
async def test_experience_sdk_routes_view_invocation_action_execution() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.invoke_view_invocation_action(
            {"experience_name": "aware_control_identity"}
        )
        == "invoked"
    )

    capability = api_client.experience.invoke_experience_view_invocation_action
    assert capability.calls == [{"experience_name": "aware_control_identity"}]


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_view_invocation_action_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.record_view_invocation_action(
            experience_name="aware_control_identity",
            projection_experience_view_instance_id=(
                "53753d86-6a54-427d-9e36-951d5865c8a2"
            ),
            view_invocation_action_config_id="1f654643-c940-48e8-b1c5-0f904089b664",
            invocation_key="711e6e1c-58cd-44b7-bfb3-68a12b7437fb",
            actor_id="2a061ce8-9788-4c3d-8338-3116d3d70515",
            api_call_id="6e27df81-c7df-451d-a8ed-5e69d43c4744",
            sdk_operation_call_id="49d469f0-f551-4268-9a4f-0eb6780306e5",
            request_ref="interface.identity_admission.submit",
            receipt_ref="api_call.identity.admit",
            status="succeeded",
        )
        == "recorded"
    )

    capability = api_client.experience.record_experience_view_invocation_action
    request = capability.calls[0]
    assert isinstance(request, RecordExperienceViewInvocationActionRequest)
    assert request.experience_name == "aware_control_identity"
    assert str(request.projection_experience_view_instance_id) == (
        "53753d86-6a54-427d-9e36-951d5865c8a2"
    )
    assert str(request.view_invocation_action_config_id) == (
        "1f654643-c940-48e8-b1c5-0f904089b664"
    )
    assert str(request.invocation_key) == "711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
    assert str(request.actor_id) == "2a061ce8-9788-4c3d-8338-3116d3d70515"
    assert str(request.api_call_id) == "6e27df81-c7df-451d-a8ed-5e69d43c4744"
    assert str(request.sdk_operation_call_id) == (
        "49d469f0-f551-4268-9a4f-0eb6780306e5"
    )
    assert request.request_ref == "interface.identity_admission.submit"
    assert request.receipt_ref == "api_call.identity.admit"
    assert request.status == "succeeded"


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_view_invocation_execution_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.invoke_view_invocation_action(
            experience_name="aware_control_identity",
            projection_experience_view_instance_id=(
                "53753d86-6a54-427d-9e36-951d5865c8a2"
            ),
            view_invocation_action_config_id="1f654643-c940-48e8-b1c5-0f904089b664",
            invocation_key="711e6e1c-58cd-44b7-bfb3-68a12b7437fb",
            actor_id="2a061ce8-9788-4c3d-8338-3116d3d70515",
            request_payload={"profile": {"display_name": "Luis"}},
            request_ref="interface.identity_admission.submit",
            receipt_ref="api_call.identity.signup",
        )
        == "invoked"
    )

    capability = api_client.experience.invoke_experience_view_invocation_action
    request = capability.calls[0]
    assert isinstance(request, InvokeExperienceViewInvocationActionRequest)
    assert request.experience_name == "aware_control_identity"
    assert str(request.projection_experience_view_instance_id) == (
        "53753d86-6a54-427d-9e36-951d5865c8a2"
    )
    assert str(request.view_invocation_action_config_id) == (
        "1f654643-c940-48e8-b1c5-0f904089b664"
    )
    assert str(request.invocation_key) == "711e6e1c-58cd-44b7-bfb3-68a12b7437fb"
    assert str(request.actor_id) == "2a061ce8-9788-4c3d-8338-3116d3d70515"
    assert request.request_payload == {"profile": {"display_name": "Luis"}}
    assert request.request_ref == "interface.identity_admission.submit"
    assert request.receipt_ref == "api_call.identity.signup"


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_session_handoff_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.ensure_session_handoff(
            session_scope={
                "namespace": "codex",
                "experience_name": "aware_control_identity",
                "environment_id": "ad7861a2-fc6e-4715-af72-ce9480ff4c36",
                "environment_session_id": "aee88dc5-14e7-4949-a236-a7e0b4a6cc94",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
                "process_id": "1f7d08c2-848c-4c7b-814a-81de0690179b",
                "thread_id": "60ea423c-e42b-47d0-8d26-bd1af8f01bbd",
                "branch_id": "d2adf578-8062-49d6-b79d-6a7dc9d2ada8",
                "projection_hash": "experience.session.feature",
                "view_ref": "aware_control_identity.identity.admission.v1",
                "window_key": "main",
                "section_key": "identity_admission",
                "observable_id": "1f654643-c940-48e8-b1c5-0f904089b664",
            },
            actor_context={
                "status": "ready",
                "kind": "human_identity",
                "source": "interface_runtime_focus",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
            },
            environment_admission=_session_environment_admission_payload(),
            environment_session_join=_session_environment_join_payload(),
            experience_actor_admission=_experience_actor_admission_payload(),
            experience_identity_session_config_id=(
                "42e0d1e1-4a30-43c0-80f8-28fef7abf625"
            ),
            feature={
                "feature_key": "reactivity_transition_dispatch",
                "reason": "interface_runtime_focus",
            },
            idempotency_key="interface-experience-session:test",
        )
        == "handoff"
    )

    capability = api_client.experience.session_handoff
    request = capability.calls[0]
    assert isinstance(request, EnsureExperienceSessionHandoffRequest)
    assert request.session_scope.experience_name == "aware_control_identity"
    assert request.actor_context is not None
    assert request.actor_context.kind == "human_identity"
    assert request.environment_admission is not None
    assert request.environment_admission.status == "admitted"
    assert request.environment_admission.bindings
    assert request.environment_session_join is not None
    assert request.environment_session_join.status == "joined"
    assert request.environment_session_join.identity_evidence is not None
    assert request.experience_actor_admission is not None
    assert request.experience_actor_admission.status == "admitted"
    assert request.experience_identity_session_config_id is not None
    assert str(request.environment_admission.environment_id) == (
        "ad7861a2-fc6e-4715-af72-ce9480ff4c36"
    )
    assert str(request.session_scope.environment_session_id) == (
        "aee88dc5-14e7-4949-a236-a7e0b4a6cc94"
    )
    assert not hasattr(request.environment_admission, "process_id")
    assert request.feature.feature_key == "reactivity_transition_dispatch"


@pytest.mark.asyncio
async def test_experience_sdk_extracts_environment_sdk_wrapper_dto_receipt() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)
    dto_receipt = EnvironmentActorAdmissionReceipt.model_validate(
        _session_environment_admission_payload()
    )

    assert (
        await sdk.ensure_session_handoff(
            session_scope={
                "namespace": "codex",
                "experience_name": "aware_control_identity",
                "environment_id": "ad7861a2-fc6e-4715-af72-ce9480ff4c36",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
            },
            environment_admission=_EnvironmentSdkReceiptWrapper(dto_receipt),
            feature={
                "feature_key": "reactivity_transition_dispatch",
            },
        )
        == "handoff"
    )

    request = api_client.experience.session_handoff.calls[0]
    assert isinstance(request, EnsureExperienceSessionHandoffRequest)
    assert request.environment_admission == dto_receipt


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_session_handoff_status_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.get_session_handoff_status(
            session_scope={
                "experience_name": "aware_control_identity",
                "profile_key": "os.default",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
            },
            feature_key="reactivity_transition_dispatch",
            lease_key="interface-experience-session:test",
            include_health=False,
        )
        == "handoff-status"
    )

    capability = api_client.experience.session_handoff
    request = capability.calls[0]
    assert isinstance(request, GetExperienceSessionHandoffStatusRequest)
    assert request.session_scope.experience_name == "aware_control_identity"
    assert request.feature_key == "reactivity_transition_dispatch"
    assert request.lease_key == "interface-experience-session:test"
    assert request.include_health is False


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_session_context_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.resolve_session_context(
            session_scope={
                "namespace": "codex",
                "experience_name": "aware_control_identity",
                "environment_id": "ad7861a2-fc6e-4715-af72-ce9480ff4c36",
                "environment_session_id": "aee88dc5-14e7-4949-a236-a7e0b4a6cc94",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
                "process_id": "1f7d08c2-848c-4c7b-814a-81de0690179b",
                "thread_id": "60ea423c-e42b-47d0-8d26-bd1af8f01bbd",
                "branch_id": "d2adf578-8062-49d6-b79d-6a7dc9d2ada8",
                "projection_hash": "ThreadLayout",
                "view_ref": "aware_control_identity.identity.admission.v1",
                "section_key": "identity_admission",
            },
            actor_context={
                "status": "ready",
                "kind": "human_identity",
                "source": "interface_runtime_focus",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
            },
            environment_admission=_session_environment_admission_payload(),
            environment_session_join=_session_environment_join_payload(),
            experience_actor_admission=_experience_actor_admission_payload(),
            experience_identity_session_config_id=(
                "42e0d1e1-4a30-43c0-80f8-28fef7abf625"
            ),
            environment_attention={
                "environment_navigation_context_id": (
                    "b7f06b13-c8df-4a07-9caf-00a3813f5b58"
                ),
                "expected_attention_session_id": (
                    "bf612f0d-ad88-40cb-8d7d-61ae7e0baf43"
                ),
                "expected_projection_hash": "ThreadLayout",
                "include_transition_list": True,
                "transition_limit": 5,
            },
            idempotency_key="interface-experience-session-context:test",
        )
        == "session-context"
    )

    capability = api_client.experience.session_context
    request = capability.calls[0]
    assert isinstance(request, ResolveExperienceSessionContextRequest)
    assert request.session_scope.experience_name == "aware_control_identity"
    assert str(request.session_scope.environment_session_id) == (
        "aee88dc5-14e7-4949-a236-a7e0b4a6cc94"
    )
    assert request.environment_admission is not None
    assert request.environment_admission.status == "admitted"
    assert request.environment_session_join is not None
    assert request.environment_session_join.status == "joined"
    assert request.experience_actor_admission is not None
    assert request.experience_actor_admission.status == "admitted"
    assert request.environment_attention is not None
    assert str(request.environment_attention.expected_attention_session_id) == (
        "bf612f0d-ad88-40cb-8d7d-61ae7e0baf43"
    )
    assert request.environment_attention.include_transition_list is True
    assert request.environment_attention.transition_limit == 5


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_session_view_frame_dto() -> None:
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.resolve_session_view_frame(
            session_scope={
                "namespace": "codex",
                "experience_name": "aware_control_identity",
                "environment_id": "ad7861a2-fc6e-4715-af72-ce9480ff4c36",
                "environment_session_id": "aee88dc5-14e7-4949-a236-a7e0b4a6cc94",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
                "thread_id": "60ea423c-e42b-47d0-8d26-bd1af8f01bbd",
                "branch_id": "d2adf578-8062-49d6-b79d-6a7dc9d2ada8",
                "projection_hash": "ThreadLayout",
                "view_ref": "aware_control_identity.identity.admission.v1",
                "projection_view_key": "identity.admission.v1",
                "section_graph_binding_key": "identity_admission.actor_home",
                "section_key": "identity_admission",
            },
            actor_context={
                "status": "ready",
                "kind": "human_identity",
                "source": "interface_runtime_focus",
                "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
            },
            environment_admission=_session_environment_admission_payload(),
            environment_session_join=_session_environment_join_payload(),
            experience_actor_admission=_experience_actor_admission_payload(),
            experience_identity_session_config_id=(
                "42e0d1e1-4a30-43c0-80f8-28fef7abf625"
            ),
            environment_attention={
                "expected_projection_hash": "ThreadLayout",
                "include_transition_list": True,
                "transition_limit": 5,
            },
            idempotency_key="interface-experience-session-view-frame:test",
        )
        == "session-view-frame"
    )

    capability = api_client.experience.session_view_frame
    request = capability.calls[0]
    assert isinstance(request, ResolveExperienceSessionViewFrameRequest)
    assert request.session_scope.experience_name == "aware_control_identity"
    assert request.session_scope.projection_view_key == "identity.admission.v1"
    assert request.session_scope.section_graph_binding_key == (
        "identity_admission.actor_home"
    )
    assert request.environment_admission is not None
    assert request.environment_session_join is not None
    assert request.experience_actor_admission is not None
    assert request.environment_attention is not None
    assert request.environment_attention.include_transition_list is True
    assert request.environment_attention.transition_limit == 5


@pytest.mark.asyncio
async def test_experience_sdk_builds_generated_view_state_watch_dto_over_session_frame() -> (
    None
):
    api_client = _FakeApiClient()
    sdk = build_experience_sdk_client(api_client)

    assert (
        await sdk.watch_experience_view_state(
            experience_name="aware_control_identity",
            session_view_frame_request={
                "session_scope": {
                    "namespace": "codex",
                    "experience_name": "aware_control_identity",
                    "environment_session_id": ("aee88dc5-14e7-4949-a236-a7e0b4a6cc94"),
                    "actor_id": "53753d86-6a54-427d-9e36-951d5865c8a2",
                    "thread_id": "60ea423c-e42b-47d0-8d26-bd1af8f01bbd",
                    "view_ref": "aware_control_identity.identity.admission.v1",
                    "projection_view_key": "identity.admission.v1",
                    "section_graph_binding_key": "identity_admission.actor_home",
                    "section_key": "identity_admission",
                },
                "environment_attention": {
                    "expected_projection_hash": "ThreadLayout",
                    "include_transition_list": True,
                    "transition_limit": 5,
                },
                "evidence": {"source": "sdk-view-state-watch"},
            },
            provider_context={"workspace_ref": "aware_network"},
            known_digest="old-digest",
        )
        == "view-state"
    )

    capability = api_client.experience.watch_experience_view_state
    request = capability.calls[0]
    assert isinstance(request, WatchExperienceViewStateRequest)
    assert request.experience_name == "aware_control_identity"
    assert request.session_view_frame_request is not None
    assert isinstance(
        request.session_view_frame_request,
        ResolveExperienceSessionViewFrameRequest,
    )
    assert request.session_view_frame_request.session_scope.view_ref == (
        "aware_control_identity.identity.admission.v1"
    )
    assert request.session_view_frame_request.session_scope.projection_view_key == (
        "identity.admission.v1"
    )
    assert (
        request.session_view_frame_request.session_scope.section_graph_binding_key
        == "identity_admission.actor_home"
    )
    assert request.session_view_frame_request.environment_attention is not None
    assert (
        request.session_view_frame_request.environment_attention.include_transition_list
        is True
    )
    assert request.provider_context == {"workspace_ref": "aware_network"}
    assert request.known_digest == "old-digest"
