from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest
from aware_types import JsonObject

from aware_api_service_dto.comms.models.api import (
    ApiRequestStatus,
    InvokeApiEndpointResponse,
)
from aware_identity_ontology_dto.identity.identity import Identity
from aware_identity_ontology_dto.identity.identity_enums import (
    IdentityType as OntologyIdentityType,
)
from aware_identity_ontology_dto.identity.identity_profile import IdentityProfile
from aware_identity_sdk import (
    DEFAULT_IDENTITY_SDK_SOURCE,
    IdentityAdmission,
    IdentityAdmissionV1ProviderInput,
    IdentityAdmissionProfile,
    IdentityGateStatus,
    IdentitySdkClient,
    IdentitySdkError,
    RawOntologyDeltaV1,
    ViewProviderProvenanceV1,
    actor_commits_v1_provider_input_from_client,
    actor_commits_view_state_from_input,
    actor_commits_view_state_from_result,
    actor_roles_v1_provider_input_from_client,
    actor_roles_view_state_from_input,
    actor_roles_view_state_from_result,
    actor_subscriptions_v1_provider_input_from_client,
    actor_subscriptions_view_state_from_input,
    actor_subscriptions_view_state_from_result,
    build_identity_gate_snapshot,
    identity_admission_v1_provider_input,
    identity_admission_view_state,
    identity_admission_view_state_from_input,
)
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
from aware_identity_service_dto.actor.commit import ActorCommitRecord
from aware_identity_service_dto.actor.commit import ActorCommitResolveRequest
from aware_identity_service_dto.actor.commit import ActorCommitResolveResult
from aware_identity_service_dto.actor.subscription import ActorSubscriptionBridgeConfig
from aware_identity_service_dto.actor.subscription import ActorSubscriptionEnsureReceipt
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.subscription import ActorSubscriptionResolveResult
from aware_identity_service_dto.credential.profile import (
    CredentialReadinessCheckReceipt,
)
from aware_identity_service_dto.credential.profile import (
    CredentialReadinessCheckRequest,
)
from aware_identity_service_dto.credential.profile import CredentialProfileSetupReceipt
from aware_identity_service_dto.credential.profile import CredentialProfileSetupRequest
from aware_identity_service_dto.identity.admission import (
    IdentitySignupViaProfileRequest,
)
from aware_identity_service_dto.profile.requests import IdentityType
from aware_identity_service_dto.identity.view import IdentityAdmissionViewStateV1
from aware_identity_service_dto.role.assignment import RoleAssignmentBinding
from aware_identity_service_dto.role.assignment import RoleAssignmentReceipt
from aware_identity_service_dto.role.assignment import RoleAssignmentRequest
from aware_identity_service_dto.role.assignment import RoleAssignmentResolveRequest
from aware_identity_service_dto.role.assignment import RoleAssignmentResolveResult
from aware_identity_service_dto.role.assignment import RoleUnassignmentReceipt
from aware_identity_service_dto.role.assignment import RoleUnassignmentRequest
from aware_identity_service_dto.session.session import ActorSessionsListRequest
from aware_identity_service_dto.session.session import ActorSessionsListResult
from aware_identity_service_dto.session.session import ChildSessionsListRequest
from aware_identity_service_dto.session.session import ChildSessionsListResult
from aware_identity_service_dto.session.session import SessionDescribeRequest
from aware_identity_service_dto.session.session import SessionDescribeResult
from aware_identity_service_dto.session.session import SessionStartReceipt
from aware_identity_service_dto.session.session import SessionStartRequest
from aware_identity_service_dto.session.session import SessionSummary
from aware_identity_sdk.operation_dispatchers import dispatch_identity_admit_identity
from aware_service_service_dto.comms.models.service import RequestStatus


def test_identity_sdk_public_package_does_not_export_local_identity_helpers() -> None:
    import aware_identity_sdk

    assert not hasattr(aware_identity_sdk, "ensure_local_identity_admission")
    assert importlib.util.find_spec("aware_identity_sdk.local_identity") is None


class _RecordingSignupViaProfileClient:
    def __init__(self) -> None:
        self.requests: list[IdentitySignupViaProfileRequest] = []
        self.receipt = IdentityAdmissionReceipt(
            identity_id=uuid4(),
            actor_id=uuid4(),
            identity_profile_id=uuid4(),
            public_handle="luis",
            info="admitted",
        )

    async def signup_via_profile(
        self,
        request: IdentitySignupViaProfileRequest,
    ) -> IdentityAdmissionReceipt:
        self.requests.append(request)
        return self.receipt


class _RecordingSetupCredentialProfileClient:
    def __init__(self) -> None:
        self.requests: list[CredentialProfileSetupRequest] = []

    async def setup_credential_profile(
        self,
        request: CredentialProfileSetupRequest,
    ) -> CredentialProfileSetupReceipt:
        self.requests.append(request)
        return CredentialProfileSetupReceipt(
            request_id=request.request_id,
            identity_id=request.identity_id,
            credential_profile_id=uuid4(),
            secret_material_ref_id=uuid4(),
            profile_key=request.profile_key,
            target_kind=request.target_kind,
            secret_ref_key=request.secret_ref_key,
            resolver_kind=request.resolver_kind,
            secret_name=request.secret_name,
            raw_secret_stored=False,
            info="setup",
        )


class _RecordingCheckCredentialReadinessClient:
    def __init__(self) -> None:
        self.requests: list[CredentialReadinessCheckRequest] = []

    async def check_credential_readiness(
        self,
        request: CredentialReadinessCheckRequest,
    ) -> CredentialReadinessCheckReceipt:
        self.requests.append(request)
        return CredentialReadinessCheckReceipt(
            request_id=request.request_id,
            identity_id=request.identity_id,
            credential_profile_id=request.credential_profile_id or uuid4(),
            readiness_receipt_id=uuid4(),
            profile_key=request.profile_key,
            target_kind=request.target_kind,
            receipt_key=request.receipt_key or "readiness",
            status="ready",
            available=True,
            resolver_kind=request.resolver_kind,
            secret_ref_key=request.secret_ref_key,
            secret_name=request.secret_name,
            checked_at_utc=request.checked_at_utc,
            missing_requirements=[],
            credential_handle=cast(
                JsonObject,
                {
                    "resolver_kind": request.resolver_kind,
                    "secret_ref_key": request.secret_ref_key,
                    "secret_name": request.secret_name,
                },
            ),
            raw_secret_returned=False,
            info="ready",
        )


class _RecordingAssignRoleClient:
    def __init__(self) -> None:
        self.requests: list[RoleAssignmentRequest] = []

    async def assign_role(
        self,
        request: RoleAssignmentRequest,
    ) -> RoleAssignmentReceipt:
        self.requests.append(request)
        return RoleAssignmentReceipt(
            request_id=request.request_id,
            binding=_role_assignment_binding(request),
            role_created=True,
            actor_role_created=True,
        )


class _RecordingUnassignRoleClient:
    def __init__(self) -> None:
        self.requests: list[RoleUnassignmentRequest] = []

    async def unassign_role(
        self,
        request: RoleUnassignmentRequest,
    ) -> RoleUnassignmentReceipt:
        self.requests.append(request)
        return RoleUnassignmentReceipt(
            request_id=request.request_id,
            binding=_role_assignment_binding(request),
            actor_role_removed=True,
        )


class _RecordingResolveRoleAssignmentsClient:
    def __init__(self) -> None:
        self.requests: list[RoleAssignmentResolveRequest] = []

    async def resolve_role_assignments(
        self,
        request: RoleAssignmentResolveRequest,
    ) -> RoleAssignmentResolveResult:
        self.requests.append(request)
        return RoleAssignmentResolveResult(
            request_id=request.request_id,
            bindings=[],
            info="resolved",
        )


class _RecordingResolveActorCommitsClient:
    def __init__(self) -> None:
        self.requests: list[ActorCommitResolveRequest] = []

    async def resolve_actor_commits(
        self,
        request: ActorCommitResolveRequest,
    ) -> ActorCommitResolveResult:
        self.requests.append(request)
        return ActorCommitResolveResult(
            request_id=request.request_id,
            actor_commits=[
                ActorCommitRecord(
                    actor_commit_id=uuid4(),
                    actor_id=request.actor_id,
                    domain_branch_id=request.domain_branch_id or uuid4(),
                    domain_projection_hash=(
                        request.domain_projection_hash or "sha256:test"
                    ),
                    domain_commit_id=request.domain_commit_id or uuid4(),
                    object_instance_graph_commit_id=uuid4(),
                    source=request.source or "test",
                )
            ],
            info="resolved",
        )


class _RecordingEnsureActorSubscriptionClient:
    def __init__(self) -> None:
        self.requests: list[ActorSubscriptionEnsureRequest] = []

    async def ensure_actor_subscription(
        self,
        request: ActorSubscriptionEnsureRequest,
    ) -> ActorSubscriptionEnsureReceipt:
        self.requests.append(request)
        return ActorSubscriptionEnsureReceipt(
            request_id=request.request_id,
            subscription=ActorSubscriptionBridgeConfig(
                id=uuid4(),
                actor_id=request.actor_id,
                event_config_condition_config_scope_id=(
                    request.event_config_condition_config_scope_id
                ),
                event_config_condition_config_id=uuid4(),
                object_instance_graph_identity_id=uuid4(),
                name=request.name,
                action_type=request.action_type,
                event_config_action_config_ids=list(
                    request.event_config_action_config_ids
                ),
                addressing_policy=request.addressing_policy,
                is_enabled=request.is_enabled,
                status=request.status,
                priority=request.priority,
                filter_config=request.filter_config,
            ),
            subscription_created=True,
            info="ensured",
        )


class _RecordingResolveActorSubscriptionsClient:
    def __init__(self) -> None:
        self.requests: list[ActorSubscriptionResolveRequest] = []

    async def resolve_actor_subscriptions(
        self,
        request: ActorSubscriptionResolveRequest,
    ) -> ActorSubscriptionResolveResult:
        self.requests.append(request)
        actor_id = request.actor_id or uuid4()
        object_instance_graph_identity_id = (
            request.object_instance_graph_identity_id or uuid4()
        )
        return ActorSubscriptionResolveResult(
            request_id=request.request_id,
            subscriptions=[
                ActorSubscriptionBridgeConfig(
                    id=uuid4(),
                    actor_id=actor_id,
                    event_config_condition_config_scope_id=uuid4(),
                    event_config_condition_config_id=(
                        request.event_config_condition_config_id or uuid4()
                    ),
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_branch_id=(
                        request.object_instance_graph_branch_id
                    ),
                    name="identity.actor.role.changed",
                    action_type="reactivity.trigger",
                )
            ],
            info="resolved",
        )


class _RecordingStartSessionClient:
    def __init__(self) -> None:
        self.requests: list[SessionStartRequest] = []

    async def start_session(
        self,
        request: SessionStartRequest,
    ) -> SessionStartReceipt:
        self.requests.append(request)
        return SessionStartReceipt(
            request_id=request.request_id,
            session=_session_summary_from_start_request(
                request=request,
                session_id=uuid4(),
            ),
            info="started",
        )


class _RecordingDescribeSessionClient:
    def __init__(self) -> None:
        self.requests: list[SessionDescribeRequest] = []

    async def describe_session(
        self,
        request: SessionDescribeRequest,
    ) -> SessionDescribeResult:
        self.requests.append(request)
        return SessionDescribeResult(
            request_id=request.request_id,
            session=None,
            info="described",
        )


class _RecordingListChildSessionsClient:
    def __init__(self) -> None:
        self.requests: list[ChildSessionsListRequest] = []

    async def list_child_sessions(
        self,
        request: ChildSessionsListRequest,
    ) -> ChildSessionsListResult:
        self.requests.append(request)
        return ChildSessionsListResult(
            request_id=request.request_id,
            parent_session_id=request.parent_session_id,
            sessions=[],
            info="listed",
        )


class _RecordingListActorSessionsClient:
    def __init__(self) -> None:
        self.requests: list[ActorSessionsListRequest] = []

    async def list_actor_sessions(
        self,
        request: ActorSessionsListRequest,
    ) -> ActorSessionsListResult:
        self.requests.append(request)
        return ActorSessionsListResult(
            request_id=request.request_id,
            actor_id=request.actor_id,
            sessions=[],
            info="listed",
        )


class _RecordingIdentityApiClient:
    def __init__(self) -> None:
        self.signup_via_profile = _RecordingSignupViaProfileClient()
        self.setup_credential_profile = _RecordingSetupCredentialProfileClient()
        self.check_credential_readiness = _RecordingCheckCredentialReadinessClient()
        self.assign_role = _RecordingAssignRoleClient()
        self.unassign_role = _RecordingUnassignRoleClient()
        self.resolve_role_assignments = _RecordingResolveRoleAssignmentsClient()
        self.resolve_actor_commits = _RecordingResolveActorCommitsClient()
        self.ensure_actor_subscription = _RecordingEnsureActorSubscriptionClient()
        self.resolve_actor_subscriptions = _RecordingResolveActorSubscriptionsClient()
        self.start_session = _RecordingStartSessionClient()
        self.describe_session = _RecordingDescribeSessionClient()
        self.list_child_sessions = _RecordingListChildSessionsClient()
        self.list_actor_sessions = _RecordingListActorSessionsClient()


class _RecordingGeneratedIdentityApiClient:
    def __init__(self) -> None:
        self.identity = _RecordingIdentityApiClient()


@pytest.mark.asyncio
async def test_admit_human_builds_generated_signup_request() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    request_id = uuid4()
    profile = IdentityAdmissionProfile(
        display_name="Luis",
        public_handle="luis",
        full_name="Luis",
        country_code="US",
        language_code="en",
        bio="workspace owner",
    )

    admission = await client.admit_human(
        public_key="public-key",
        profile=profile,
        request_id=request_id,
    )

    request = api_client.identity.signup_via_profile.requests[0]
    assert request.public_key == "public-key"
    assert request.request_id == request_id
    assert request.source == DEFAULT_IDENTITY_SDK_SOURCE
    assert request.create_profile_request.display_name == "Luis"
    assert request.create_profile_request.identity_type is IdentityType.human
    assert (
        admission.identity_id
        == api_client.identity.signup_via_profile.receipt.identity_id
    )
    assert admission.actor_id == api_client.identity.signup_via_profile.receipt.actor_id
    assert admission.identity_type is IdentityType.human
    assert admission.receipt is api_client.identity.signup_via_profile.receipt


@pytest.mark.asyncio
async def test_admit_agent_identity_keeps_agent_process_thread_out_of_identity_sdk() -> (
    None
):
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)

    admission = await client.admit_agent_identity(
        public_key="agent-public-key",
        profile=IdentityAdmissionProfile(
            display_name="Build Agent",
            public_handle="build-agent",
            full_name="Build Agent",
            country_code="US",
            language_code="en",
        ),
    )

    request = api_client.identity.signup_via_profile.requests[0]
    assert request.create_profile_request.identity_type is IdentityType.agent
    assert admission.identity_type is IdentityType.agent
    assert not hasattr(client, "create_agent_process_thread")


@pytest.mark.asyncio
async def test_identity_admit_operation_dispatcher_uses_generated_api_client() -> None:
    request_id = uuid4()
    receipt_payload: dict[str, object] = {
        "identity_id": str(uuid4()),
        "actor_id": str(uuid4()),
        "identity_profile_id": str(uuid4()),
        "public_handle": "codex",
        "info": "admitted",
    }

    class _RawApiClient:
        def __init__(self) -> None:
            self.invocations: list[tuple[str, dict[str, object]]] = []

        async def invoke_api_endpoint_raw(
            self,
            *,
            endpoint_ref: str,
            discriminant: str,
            request_payload: dict[str, object],
            timeout_s: float | None = None,
        ) -> InvokeApiEndpointResponse:
            _ = discriminant, timeout_s
            self.invocations.append((endpoint_ref, dict(request_payload)))
            return InvokeApiEndpointResponse(
                status=ApiRequestStatus.succeeded,
                response_payload=receipt_payload,
            )

    raw_client = _RawApiClient()

    response = await dispatch_identity_admit_identity(
        api_client=raw_client,
        operation_ref="identity_sdk.admit_identity",
        discriminant="identity_sdk.admit_identity",
        request_payload={
            "public_key": "ed25519:public-key",
            "request_id": str(request_id),
            "source": "interface_test",
            "create_profile_request": {
                "display_name": "Codex",
                "public_handle": "codex",
                "full_name": "Codex Agent",
                "country_code": "US",
                "language_code": "en",
                "identity_type": "agent",
            },
        },
    )

    assert response.status is RequestStatus.succeeded
    assert response.response_payload == {
        "identity_id": receipt_payload["identity_id"],
        "actor_id": receipt_payload["actor_id"],
        "identity_profile_id": receipt_payload["identity_profile_id"],
        "public_handle": "codex",
        "identity_type": "agent",
        "info": "admitted",
        "receipt": receipt_payload,
    }
    assert raw_client.invocations[0][0] == (
        "identity.signup_via_profile.signup_via_profile"
    )
    signup_payload = raw_client.invocations[0][1]
    assert signup_payload["public_key"] == "ed25519:public-key"
    assert signup_payload["request_id"] == str(request_id)
    assert signup_payload["source"] == "interface_test"
    assert signup_payload["create_profile_request"] == {
        "display_name": "Codex",
        "public_handle": "codex",
        "full_name": "Codex Agent",
        "country_code": "US",
        "language_code": "en",
        "identity_type": "agent",
    }


@pytest.mark.asyncio
async def test_credential_profile_helper_forwards_secret_ref_metadata_only() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    identity_id = uuid4()
    request_id = uuid4()

    receipt = await client.setup_credential_profile(
        identity_id=identity_id,
        profile_key="pypi.publish",
        target_kind="test_pypi",
        display_name="TestPyPI publisher",
        target_name="aware-api-client",
        secret_ref_key="twine-password",
        resolver_kind="env_var",
        secret_name="TWINE_PASSWORD",
        username_hint="__token__",
        request_id=request_id,
    )

    request = api_client.identity.setup_credential_profile.requests[0]
    assert request.identity_id == identity_id
    assert request.profile_key == "pypi.publish"
    assert request.target_kind == "test_pypi"
    assert request.secret_ref_key == "twine-password"
    assert request.secret_name == "TWINE_PASSWORD"
    assert request.source == DEFAULT_IDENTITY_SDK_SOURCE
    assert not hasattr(request, "secret_value")
    assert receipt.request_id == request_id
    assert receipt.raw_secret_stored is False


@pytest.mark.asyncio
async def test_credential_readiness_helper_forwards_non_secret_handle() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    identity_id = uuid4()
    request_id = uuid4()

    receipt = await client.check_credential_readiness(
        identity_id=identity_id,
        profile_key="pypi.publish",
        target_kind="test_pypi",
        receipt_key="testpypi-local",
        secret_ref_key="twine-password",
        resolver_kind="env_var",
        secret_name="TWINE_PASSWORD",
        checked_at_utc="2026-04-30T07:58:00Z",
        request_id=request_id,
    )

    request = api_client.identity.check_credential_readiness.requests[0]
    assert request.identity_id == identity_id
    assert request.profile_key == "pypi.publish"
    assert request.target_kind == "test_pypi"
    assert request.secret_ref_key == "twine-password"
    assert request.secret_name == "TWINE_PASSWORD"
    assert request.source == DEFAULT_IDENTITY_SDK_SOURCE
    assert not hasattr(request, "secret_value")
    assert receipt.request_id == request_id
    assert receipt.status == "ready"
    assert receipt.available is True
    assert receipt.raw_secret_returned is False


@pytest.mark.asyncio
async def test_role_helpers_forward_generated_identity_role_requests() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    actor_id = uuid4()
    class_instance_identity_id = uuid4()
    role_config_id = uuid4()
    request_id = uuid4()

    assignment = await client.assign_role(
        actor_id=actor_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_id=role_config_id,
        object_instance_graph_branch_key="main",
        request_id=request_id,
        reason="mount identity pane",
    )
    await client.unassign_role(
        actor_id=actor_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_name="viewer",
    )
    resolved = await client.resolve_role_assignments(
        actor_id=actor_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_name="viewer",
    )

    assign_request = api_client.identity.assign_role.requests[0]
    assert assign_request.actor_id == actor_id
    assert assign_request.role_config_id == role_config_id
    assert assign_request.class_instance_identity_id == class_instance_identity_id
    assert assign_request.object_instance_graph_branch_key == "main"
    assert assign_request.source_service == DEFAULT_IDENTITY_SDK_SOURCE
    assert assignment.request_id == request_id
    assert assignment.binding.actor_id == actor_id
    unassign_request = api_client.identity.unassign_role.requests[0]
    assert unassign_request.role_config_name == "viewer"
    resolve_request = api_client.identity.resolve_role_assignments.requests[0]
    assert resolve_request.role_config_name == "viewer"
    assert resolved.info == "resolved"


@pytest.mark.asyncio
async def test_actor_read_helpers_forward_generated_identity_requests() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    actor_id = uuid4()
    branch_id = uuid4()
    domain_commit_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    subscription_condition_id = uuid4()
    request_id = uuid4()

    commits = await client.resolve_actor_commits(
        actor_id=actor_id,
        domain_branch_id=branch_id,
        domain_projection_hash="sha256:identity",
        domain_commit_id=domain_commit_id,
        source="identity_actor_view",
        limit=25,
        request_id=request_id,
    )
    subscriptions = await client.resolve_actor_subscriptions(
        actor_id=actor_id,
        event_config_condition_config_id=subscription_condition_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        include_inactive=True,
        include_disabled=True,
        request_id=request_id,
    )

    commit_request = api_client.identity.resolve_actor_commits.requests[0]
    assert commit_request.actor_id == actor_id
    assert commit_request.domain_branch_id == branch_id
    assert commit_request.domain_projection_hash == "sha256:identity"
    assert commit_request.domain_commit_id == domain_commit_id
    assert commit_request.source == "identity_actor_view"
    assert commit_request.limit == 25
    assert commit_request.request_id == request_id
    assert commits.actor_commits[0].actor_id == actor_id

    subscription_request = api_client.identity.resolve_actor_subscriptions.requests[0]
    assert subscription_request.actor_id == actor_id
    assert (
        subscription_request.event_config_condition_config_id
        == subscription_condition_id
    )
    assert (
        subscription_request.object_instance_graph_identity_id
        == object_instance_graph_identity_id
    )
    assert subscription_request.include_inactive is True
    assert subscription_request.include_disabled is True
    assert subscription_request.request_id == request_id
    assert subscriptions.subscriptions[0].actor_id == actor_id


@pytest.mark.asyncio
async def test_actor_subscription_ensure_helper_forwards_generated_request() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    actor_id = uuid4()
    scope_id = uuid4()
    action_config_id = uuid4()
    request_id = uuid4()
    filter_config = cast(
        JsonObject,
        {
            "event_type": "conversation.message.created",
            "conversation_id": str(uuid4()),
        },
    )

    receipt = await client.ensure_actor_subscription(
        request_id=request_id,
        actor_id=actor_id,
        event_config_condition_config_scope_id=scope_id,
        name="conversation.message.created",
        description="Wake the agent when a conversation message is created.",
        action_type="agent.turn.execute",
        event_config_action_config_ids=(action_config_id,),
        addressing_policy="any",
        is_enabled=True,
        status="active",
        filter_mode="all_instances",
        filter_config=filter_config,
        priority=50,
        batch_mode=True,
        batch_window_ms=250,
        max_batch_size=25,
        require_read_access=False,
        check_ownership=False,
        rate_limit_per_minute=12,
        rate_limit_per_hour=120,
    )

    request = api_client.identity.ensure_actor_subscription.requests[0]
    assert request.request_id == request_id
    assert request.actor_id == actor_id
    assert request.event_config_condition_config_scope_id == scope_id
    assert request.name == "conversation.message.created"
    assert request.description == (
        "Wake the agent when a conversation message is created."
    )
    assert request.action_type == "agent.turn.execute"
    assert request.event_config_action_config_ids == [action_config_id]
    assert request.addressing_policy == "any"
    assert request.is_enabled is True
    assert request.status == "active"
    assert request.filter_mode == "all_instances"
    assert request.filter_config == filter_config
    assert request.priority == 50
    assert request.batch_mode is True
    assert request.batch_window_ms == 250
    assert request.max_batch_size == 25
    assert request.require_read_access is False
    assert request.check_ownership is False
    assert request.rate_limit_per_minute == 12
    assert request.rate_limit_per_hour == 120
    assert receipt.request_id == request_id
    assert receipt.subscription.actor_id == actor_id
    assert receipt.subscription.event_config_condition_config_scope_id == scope_id
    assert receipt.subscription.action_type == "agent.turn.execute"


@pytest.mark.asyncio
async def test_session_hierarchy_helpers_forward_generated_identity_requests() -> None:
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    root_config_id = uuid4()
    child_config_id = uuid4()
    parent_session_id = uuid4()
    actor_id = uuid4()
    request_id = uuid4()

    root_receipt = await client.start_session(
        request_id=request_id,
        session_config_id=root_config_id,
        key="environment-root",
        title="Environment Root",
        created_by_actor_id=actor_id,
        metadata_json=cast(JsonObject, {"scope": "root"}),
    )
    child_receipt = await client.start_child_session(
        request_id=request_id,
        parent_session_id=parent_session_id,
        session_config_id=child_config_id,
        key="experience-child",
        title="Experience Child",
        source_kind="experience",
    )
    described = await client.describe_session(
        request_id=request_id,
        session_id=parent_session_id,
    )
    children = await client.list_child_sessions(
        request_id=request_id,
        parent_session_id=parent_session_id,
        session_config_id=child_config_id,
        status="active",
    )
    actor_sessions = await client.list_actor_sessions(
        request_id=request_id,
        actor_id=actor_id,
        parent_session_id=parent_session_id,
        include_inactive=True,
    )

    root_request = api_client.identity.start_session.requests[0]
    child_request = api_client.identity.start_session.requests[1]
    assert root_request.parent_session_id is None
    assert not hasattr(root_request, "parent_session_scope_key")
    assert root_receipt.session.parent_session_id is None
    assert child_request.parent_session_id == parent_session_id
    assert not hasattr(child_request, "parent_session_scope_key")
    assert child_receipt.session.parent_session_id == parent_session_id

    describe_request = api_client.identity.describe_session.requests[0]
    assert describe_request.session_id == parent_session_id
    assert describe_request.request_id == request_id
    assert described.info == "described"

    child_list_request = api_client.identity.list_child_sessions.requests[0]
    assert child_list_request.parent_session_id == parent_session_id
    assert child_list_request.session_config_id == child_config_id
    assert child_list_request.status == "active"
    assert children.parent_session_id == parent_session_id

    actor_sessions_request = api_client.identity.list_actor_sessions.requests[0]
    assert actor_sessions_request.actor_id == actor_id
    assert actor_sessions_request.parent_session_id == parent_session_id
    assert actor_sessions_request.include_inactive is True
    assert actor_sessions.actor_id == actor_id


@pytest.mark.asyncio
async def test_actor_view_provider_inputs_call_identity_sdk_client() -> None:
    _ensure_aware_actor_contract_path()
    api_client = _RecordingGeneratedIdentityApiClient()
    client = IdentitySdkClient(api_client=api_client)
    actor_id = uuid4()
    class_instance_identity_id = uuid4()
    request_id = uuid4()

    roles_input = await actor_roles_v1_provider_input_from_client(
        client=client,
        actor_id=actor_id,
        class_instance_identity_id=class_instance_identity_id,
        request_id=request_id,
    )
    commits_input = await actor_commits_v1_provider_input_from_client(
        client=client,
        actor_id=actor_id,
        request_id=request_id,
    )
    subscriptions_input = await actor_subscriptions_v1_provider_input_from_client(
        client=client,
        actor_id=actor_id,
        request_id=request_id,
    )

    assert roles_input.result is not None
    assert commits_input.result is not None
    assert subscriptions_input.result is not None
    assert api_client.identity.resolve_role_assignments.requests[0].actor_id == actor_id
    assert api_client.identity.resolve_actor_commits.requests[0].actor_id == actor_id
    assert (
        api_client.identity.resolve_actor_subscriptions.requests[0].actor_id == actor_id
    )

    assert actor_roles_view_state_from_input(roles_input).status == "empty"
    assert actor_commits_view_state_from_input(commits_input).entries[0].actor_commit_id
    assert (
        actor_subscriptions_view_state_from_input(subscriptions_input)
        .entries[0]
        .actor_subscription_id
    )


def test_actor_view_providers_map_identity_api_results_to_experience_contracts() -> (
    None
):
    _ensure_aware_actor_contract_path()
    from aware_identity_service_dto.actor.view import (  # noqa: WPS433
        ActorCommitsViewStateV1,
        ActorRolesViewStateV1,
        ActorSubscriptionsViewStateV1,
    )

    actor_id = uuid4()
    role_config_id = uuid4()
    commit_id = uuid4()
    subscription_id = uuid4()

    roles = actor_roles_view_state_from_result(
        RoleAssignmentResolveResult(
            request_id=uuid4(),
            bindings=[
                RoleAssignmentBinding(
                    actor_id=actor_id,
                    role_config_id=role_config_id,
                    role_id=uuid4(),
                    actor_role_id=uuid4(),
                    role_class_instance_id=uuid4(),
                    class_instance_identity_id=uuid4(),
                    role_config_class_config_id=uuid4(),
                    object_instance_graph_identity_id=uuid4(),
                    object_instance_graph_branch_key="actor.home",
                )
            ],
        ),
        actor_id=actor_id,
        actor_display_name="Luis",
        provenance={"state_provider_ref": "sdk:identity.actor.roles.v1"},
    )
    commits = actor_commits_view_state_from_result(
        ActorCommitResolveResult(
            request_id=uuid4(),
            actor_commits=[
                ActorCommitRecord(
                    actor_commit_id=uuid4(),
                    actor_id=actor_id,
                    domain_branch_id=uuid4(),
                    domain_projection_hash="sha256:identity",
                    domain_commit_id=commit_id,
                    object_instance_graph_commit_id=uuid4(),
                    operation_label="assign role",
                    call_target="identity.assign_role",
                    created_at_unix_ms=1_765_000_000_000,
                )
            ],
        ),
        actor_id=actor_id,
    )
    subscriptions = actor_subscriptions_view_state_from_result(
        ActorSubscriptionResolveResult(
            request_id=uuid4(),
            subscriptions=[
                ActorSubscriptionBridgeConfig(
                    id=subscription_id,
                    actor_id=actor_id,
                    event_config_condition_config_scope_id=uuid4(),
                    event_config_condition_config_id=uuid4(),
                    object_instance_graph_identity_id=uuid4(),
                    name="identity.actor.role.changed",
                    action_type="reactivity.trigger",
                    status="active",
                )
            ],
        ),
        actor_id=actor_id,
    )

    assert isinstance(roles, ActorRolesViewStateV1)
    assert roles.status == "ready"
    assert roles.actor_id == actor_id
    assert roles.actor_display_name == "Luis"
    assert roles.entries[0].role_config_id == role_config_id
    assert roles.entries[0].scope == "actor.home"
    assert roles.provenance["state_provider_ref"] == "sdk:identity.actor.roles.v1"
    assert roles.provenance["view_ref"] == "identity.actor_roles"

    assert isinstance(commits, ActorCommitsViewStateV1)
    assert commits.entries[0].commit_id == commit_id
    assert commits.entries[0].summary == "assign role"
    assert commits.entries[0].target_kind == "identity.assign_role"
    assert commits.entries[0].authored_at is not None

    assert isinstance(subscriptions, ActorSubscriptionsViewStateV1)
    assert subscriptions.entries[0].actor_subscription_id == subscription_id
    assert subscriptions.entries[0].event_kind == "reactivity.trigger"
    assert subscriptions.entries[0].event_label == "identity.actor.role.changed"


def test_actor_view_provider_boundary_stays_out_of_experience_package() -> None:
    contract_root = _aware_actor_contract_root()
    assert not (contract_root / "aware_actor" / "view_state_providers").exists()


@pytest.mark.asyncio
async def test_role_mutations_require_a_role_selector() -> None:
    client = IdentitySdkClient(api_client=_RecordingGeneratedIdentityApiClient())

    with pytest.raises(IdentitySdkError, match="role_config_id or role_config_name"):
        await client.assign_role(
            actor_id=uuid4(),
            class_instance_identity_id=uuid4(),
        )


def test_gate_snapshot_crosses_only_for_matching_identity_actor() -> None:
    actor_id = uuid4()
    admission = _admission(actor_id=actor_id)

    crossed = build_identity_gate_snapshot(
        admission=admission,
        authenticated_actor_id=actor_id,
    )
    mismatched = build_identity_gate_snapshot(
        admission=admission,
        authenticated_actor_id=uuid4(),
    )
    unauthenticated = build_identity_gate_snapshot(
        admission=admission,
        authenticated_actor_id=None,
    )
    missing_identity = build_identity_gate_snapshot(
        identity_id=None,
        expected_actor_id=actor_id,
        authenticated_actor_id=actor_id,
    )

    assert crossed.crossed is True
    assert crossed.status is IdentityGateStatus.crossed
    assert crossed.expected_actor_id == actor_id
    assert mismatched.status is IdentityGateStatus.actor_mismatch
    assert unauthenticated.status is IdentityGateStatus.unauthenticated
    assert missing_identity.status is IdentityGateStatus.missing_identity


def test_identity_admission_view_state_provider_resolves_typed_identity_snapshot() -> (
    None
):
    provider_input = IdentityAdmissionV1ProviderInput(
        latest=_identity_snapshot(),
        raw_deltas=[
            RawOntologyDeltaV1(
                delta_id="delta-1",
                commit_id="commit-1",
                kind="object_instance_graph_delta",
                payload={"class": "IdentityProfile", "field": "display_name"},
            )
        ],
        provenance=ViewProviderProvenanceV1(
            branch_id="branch-1",
            head_commit_id="commit-1",
            graph_hash_post="hash-1",
            view_ref="identity.identity_admission",
        ),
    )

    state = identity_admission_view_state_from_input(provider_input)

    assert isinstance(state, IdentityAdmissionViewStateV1)
    assert state.admitted is True
    assert state.status == "admitted"
    assert state.display_name == "Luis"
    assert state.public_handle == "luis"
    assert state.bio == "Build canonical panes."
    assert state.provenance["branch_id"] == "branch-1"
    assert state.provenance["raw_delta_count"] == 1
    assert state.model_dump(mode="json")["display_name"] == "Luis"


def test_identity_admission_view_state_provider_accepts_typed_input_only() -> None:
    provider_input = IdentityAdmissionV1ProviderInput(
        latest=_identity_snapshot(),
        provenance=ViewProviderProvenanceV1(branch_id="branch-2"),
    )

    state = identity_admission_view_state(provider_input=provider_input)

    assert state.status == "admitted"
    assert state.display_name == "Luis"
    assert state.provenance["branch_id"] == "branch-2"


def test_identity_admission_view_state_provider_waits_without_typed_snapshot() -> None:
    state = identity_admission_view_state(
        provider_input=IdentityAdmissionV1ProviderInput(
            provenance=ViewProviderProvenanceV1(branch_id="branch-3"),
        )
    )

    assert state.admitted is False
    assert state.status == "pending"
    assert state.provenance["branch_id"] == "branch-3"


def test_identity_admission_provider_input_resolver_uses_host_context() -> None:
    provider_context = SimpleNamespace(
        provenance={
            "branch_id": "branch-4",
            "projection_view_key": "identity.admission.v1",
        },
        latest_ontology=lambda model: (
            _identity_snapshot() if model is Identity else None
        ),
        raw_ontology_deltas=lambda: [
            {
                "delta_id": "delta-2",
                "commit_id": "commit-2",
                "kind": "object_instance_graph_change_tree",
                "payload": {"changed": True},
            }
        ],
    )

    provider_input = identity_admission_v1_provider_input(provider_context)
    state = identity_admission_view_state(provider_input=provider_input)

    assert provider_input.latest is not None
    assert len(provider_input.raw_deltas) == 1
    assert state.status == "admitted"
    assert state.provenance["branch_id"] == "branch-4"
    assert state.provenance["projection_view_key"] == "identity.admission.v1"
    assert state.provenance["raw_delta_count"] == 1


def test_identity_admission_provider_exposes_input_resolver() -> None:
    assert (
        getattr(identity_admission_view_state, "provider_input_resolver")
        is identity_admission_v1_provider_input
    )


def test_identity_view_provider_boundary_avoids_raw_graph_and_orm_ontology() -> None:
    provider_source = (
        Path(__file__).parents[1] / "aware_identity_sdk" / "view_state_providers.py"
    ).read_text(encoding="utf-8")

    assert "aware_identity_ontology." not in provider_source
    assert "materialized_lane" not in provider_source
    assert "class_instances" not in provider_source


def _admission(*, actor_id: UUID) -> IdentityAdmission:
    receipt = IdentityAdmissionReceipt(
        identity_id=uuid4(),
        actor_id=actor_id,
        identity_profile_id=uuid4(),
        public_handle="luis",
    )
    return IdentityAdmission.from_receipt(
        receipt=receipt,
        identity_type=IdentityType.human,
    )


def _identity_snapshot() -> Identity:
    return Identity(
        public_key="identity-public-key",
        type=OntologyIdentityType.human,
        identity_profile=IdentityProfile(
            public_handle="luis",
            display_name="Luis",
            full_name="Luis F",
            country_code="US",
            language_code="en",
            bio="Build canonical panes.",
        ),
    )


def _ensure_aware_actor_contract_path() -> None:
    contract_root = _aware_actor_contract_root()
    contract_root_text = str(contract_root)
    if contract_root_text not in sys.path:
        sys.path.insert(0, contract_root_text)


def _aware_actor_contract_root() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return (
        repo_root
        / "experiences"
        / "aware-actor"
        / "languages"
        / "python"
        / "aware_actor"
    )


def _role_assignment_binding(
    request: RoleAssignmentRequest | RoleUnassignmentRequest,
) -> RoleAssignmentBinding:
    return RoleAssignmentBinding(
        actor_id=request.actor_id,
        role_config_id=request.role_config_id or uuid4(),
        role_id=uuid4(),
        actor_role_id=uuid4(),
        role_class_instance_id=uuid4(),
        class_instance_identity_id=request.class_instance_identity_id,
        role_config_class_config_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_branch_key=request.object_instance_graph_branch_key,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
    )


def _session_summary_from_start_request(
    *,
    request: SessionStartRequest,
    session_id: UUID,
) -> SessionSummary:
    return SessionSummary(
        session_id=session_id,
        session_config_id=request.session_config_id,
        parent_session_id=request.parent_session_id,
        key=request.key,
        title=request.title,
        description=request.description,
        purpose=request.purpose,
        status=request.status,
        created_by_actor_id=request.created_by_actor_id,
        source_kind=request.source_kind,
        source_ref=request.source_ref,
        metadata_json=request.metadata_json,
        provider_sessions=[],
        member_count=0,
    )
