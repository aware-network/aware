# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF,
    IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF,
    IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF,
    IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF,
    IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF,
    IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
    IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF,
    IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF,
    IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF,
    IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF,
    IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF,
    IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF,
    IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF,
    IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF,
    IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF,
    IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF,
    IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF,
    IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF,
    IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF,
    IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
    IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF,
    IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureReceipt,
    ActorCommitEnsureRequest,
    ActorCommitResolveRequest,
    ActorCommitResolveResult,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureReceipt,
    ActorSubscriptionEnsureRequest,
    ActorSubscriptionResolveRequest,
    ActorSubscriptionResolveResult,
)
from aware_identity_service_dto.credential.profile import (
    CredentialProfileSetupReceipt,
    CredentialProfileSetupRequest,
    CredentialReadinessCheckReceipt,
    CredentialReadinessCheckRequest,
)
from aware_identity_service_dto.identity.admission import IdentitySignupViaProfileRequest
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
from aware_identity_service_dto.role.assignment import (
    RoleAssignmentReceipt,
    RoleAssignmentRequest,
    RoleAssignmentResolveRequest,
    RoleAssignmentResolveResult,
    RoleUnassignmentReceipt,
    RoleUnassignmentRequest,
)
from aware_identity_service_dto.session.session import (
    ActorSessionsListRequest,
    ActorSessionsListResult,
    ChildSessionsListRequest,
    ChildSessionsListResult,
    SessionConfigActorConfigBindReceipt,
    SessionConfigActorConfigBindRequest,
    SessionConfigEnsureReceipt,
    SessionConfigEnsureRequest,
    SessionDescribeRequest,
    SessionDescribeResult,
    SessionJoinReceipt,
    SessionJoinRequest,
    SessionMemberActorRoleRecordReceipt,
    SessionMemberActorRoleRecordRequest,
    SessionMembersListRequest,
    SessionMembersListResult,
    SessionProviderConfigBindReceipt,
    SessionProviderConfigBindRequest,
    SessionProviderRegisterReceipt,
    SessionProviderRegisterRequest,
    SessionProviderSessionAttachReceipt,
    SessionProviderSessionAttachRequest,
    SessionStartReceipt,
    SessionStartRequest,
)


class IdentityAssignRoleCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def assign_role(self, request: RoleAssignmentRequest) -> RoleAssignmentReceipt:
        """Create or reuse one canonical actor-role binding over the class-instance-aware
        Identity role rail."""
        return cast(
            RoleAssignmentReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityAttachSessionProviderSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def attach_session_provider_session(
        self, request: SessionProviderSessionAttachRequest
    ) -> SessionProviderSessionAttachReceipt:
        """Attach one concrete provider session/capability to a shared Identity Session."""
        return cast(
            SessionProviderSessionAttachReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityBindSessionConfigActorConfigCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def bind_session_config_actor_config(
        self, request: SessionConfigActorConfigBindRequest
    ) -> SessionConfigActorConfigBindReceipt:
        """Bind one ActorConfig as eligible session participation policy without
        admitting an actor or granting roles."""
        return cast(
            SessionConfigActorConfigBindReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityBindSessionProviderConfigCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def bind_session_provider_config(
        self, request: SessionProviderConfigBindRequest
    ) -> SessionProviderConfigBindReceipt:
        """Bind one provider capability to an Identity SessionConfig without creating a
        concrete provider session."""
        return cast(
            SessionProviderConfigBindReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityCheckCredentialReadinessCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def check_credential_readiness(
        self, request: CredentialReadinessCheckRequest
    ) -> CredentialReadinessCheckReceipt:
        """Check resolver availability for one Identity credential profile and record a
        readiness receipt without carrying raw secret values."""
        return cast(
            CredentialReadinessCheckReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityDescribeSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_session(self, request: SessionDescribeRequest) -> SessionDescribeResult:
        """Read one Identity Session summary by stable id without resolving
        domain-specific provider state."""
        return cast(
            SessionDescribeResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityEnsureActorCommitCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_actor_commit(self, request: ActorCommitEnsureRequest) -> ActorCommitEnsureReceipt:
        """Create or reuse one Identity-owned ActorCommit personal-history record from
        an Environment lane commit fanout receipt."""
        return cast(
            ActorCommitEnsureReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityEnsureActorSubscriptionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_actor_subscription(
        self, request: ActorSubscriptionEnsureRequest
    ) -> ActorSubscriptionEnsureReceipt:
        """Create or reuse one canonical actor-subscription binding for an actor and a
        Reactivity-owned event-condition scope. ActorRole remains detached at this
        boundary; later ACL eligibility can compose role checks without making
        operation capability equal event willingness."""
        return cast(
            ActorSubscriptionEnsureReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityEnsureSessionConfigCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_session_config(self, request: SessionConfigEnsureRequest) -> SessionConfigEnsureReceipt:
        """Create or reuse one Identity-owned generic session participation policy."""
        return cast(
            SessionConfigEnsureReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityJoinSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def join_session(self, request: SessionJoinRequest) -> SessionJoinReceipt:
        """Join one Actor to an Identity Session under an explicit SessionConfigActorConfig."""
        return cast(
            SessionJoinReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityListActorSessionsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_actor_sessions(self, request: ActorSessionsListRequest) -> ActorSessionsListResult:
        """List Identity Sessions visible through membership for one Actor."""
        return cast(
            ActorSessionsListResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityListChildSessionsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_child_sessions(self, request: ChildSessionsListRequest) -> ChildSessionsListResult:
        """List direct child Identity Sessions for one parent Identity Session."""
        return cast(
            ChildSessionsListResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityListSessionMembersCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_session_members(self, request: SessionMembersListRequest) -> SessionMembersListResult:
        """List members and ActorRole evidence for one Identity Session."""
        return cast(
            SessionMembersListResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityRecordSessionMemberActorRoleCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_session_member_actor_role(
        self, request: SessionMemberActorRoleRecordRequest
    ) -> SessionMemberActorRoleRecordReceipt:
        """Record an existing ActorRole as evidence for one SessionMember without
        granting, revoking, scoping, or expiring permission."""
        return cast(
            SessionMemberActorRoleRecordReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityRegisterSessionProviderCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def register_session_provider(
        self, request: SessionProviderRegisterRequest
    ) -> SessionProviderRegisterReceipt:
        """Register one provider-neutral session capability descriptor."""
        return cast(
            SessionProviderRegisterReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityResolveActorCommitsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_actor_commits(self, request: ActorCommitResolveRequest) -> ActorCommitResolveResult:
        """Resolve ActorCommit personal-history records for one actor through the
        generated Identity service API boundary."""
        return cast(
            ActorCommitResolveResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityResolveActorSubscriptionsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_actor_subscriptions(
        self, request: ActorSubscriptionResolveRequest
    ) -> ActorSubscriptionResolveResult:
        """Resolve actor-subscription bridge configs from Identity-owned subscription
        lanes so Reactivity and downstream services can discover who is subscribed
        to a scoped event policy."""
        return cast(
            ActorSubscriptionResolveResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityResolveRoleAssignmentsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_role_assignments(self, request: RoleAssignmentResolveRequest) -> RoleAssignmentResolveResult:
        """Resolve canonical actor-role bindings for one actor and one graph scope on the
        public Identity service API boundary."""
        return cast(
            RoleAssignmentResolveResult,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentitySetupCredentialProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def setup_credential_profile(self, request: CredentialProfileSetupRequest) -> CredentialProfileSetupReceipt:
        """Create or reuse one Identity-owned credential profile and attach one external
        secret-material reference without carrying raw secret values."""
        return cast(
            CredentialProfileSetupReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentitySignupViaProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def signup_via_profile(self, request: IdentitySignupViaProfileRequest) -> IdentityAdmissionReceipt:
        """Create the first canonical remote Identity + Actor admission record for an
        Interface consumer using a public key and profile payload."""
        return cast(
            IdentityAdmissionReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityStartSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def start_session(self, request: SessionStartRequest) -> SessionStartReceipt:
        """Start one concrete Identity Session under a SessionConfig."""
        return cast(
            SessionStartReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityUnassignRoleCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def unassign_role(self, request: RoleUnassignmentRequest) -> RoleUnassignmentReceipt:
        """Remove one canonical actor-role binding over the class-instance-aware Identity
        role rail when the requested class-instance scope is unambiguous."""
        return cast(
            RoleUnassignmentReceipt,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class IdentityApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.assign_role = IdentityAssignRoleCapabilityClient(client)
        self.attach_session_provider_session = IdentityAttachSessionProviderSessionCapabilityClient(client)
        self.bind_session_config_actor_config = IdentityBindSessionConfigActorConfigCapabilityClient(client)
        self.bind_session_provider_config = IdentityBindSessionProviderConfigCapabilityClient(client)
        self.check_credential_readiness = IdentityCheckCredentialReadinessCapabilityClient(client)
        self.describe_session = IdentityDescribeSessionCapabilityClient(client)
        self.ensure_actor_commit = IdentityEnsureActorCommitCapabilityClient(client)
        self.ensure_actor_subscription = IdentityEnsureActorSubscriptionCapabilityClient(client)
        self.ensure_session_config = IdentityEnsureSessionConfigCapabilityClient(client)
        self.join_session = IdentityJoinSessionCapabilityClient(client)
        self.list_actor_sessions = IdentityListActorSessionsCapabilityClient(client)
        self.list_child_sessions = IdentityListChildSessionsCapabilityClient(client)
        self.list_session_members = IdentityListSessionMembersCapabilityClient(client)
        self.record_session_member_actor_role = IdentityRecordSessionMemberActorRoleCapabilityClient(client)
        self.register_session_provider = IdentityRegisterSessionProviderCapabilityClient(client)
        self.resolve_actor_commits = IdentityResolveActorCommitsCapabilityClient(client)
        self.resolve_actor_subscriptions = IdentityResolveActorSubscriptionsCapabilityClient(client)
        self.resolve_role_assignments = IdentityResolveRoleAssignmentsCapabilityClient(client)
        self.setup_credential_profile = IdentitySetupCredentialProfileCapabilityClient(client)
        self.signup_via_profile = IdentitySignupViaProfileCapabilityClient(client)
        self.start_session = IdentityStartSessionCapabilityClient(client)
        self.unassign_role = IdentityUnassignRoleCapabilityClient(client)


class AwareIdentityServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.identity = IdentityApiClient(client)


__all__ = [
    "AwareIdentityServiceApiClient",
    "IdentityApiClient",
    "IdentityAssignRoleCapabilityClient",
    "IdentityAttachSessionProviderSessionCapabilityClient",
    "IdentityBindSessionConfigActorConfigCapabilityClient",
    "IdentityBindSessionProviderConfigCapabilityClient",
    "IdentityCheckCredentialReadinessCapabilityClient",
    "IdentityDescribeSessionCapabilityClient",
    "IdentityEnsureActorCommitCapabilityClient",
    "IdentityEnsureActorSubscriptionCapabilityClient",
    "IdentityEnsureSessionConfigCapabilityClient",
    "IdentityJoinSessionCapabilityClient",
    "IdentityListActorSessionsCapabilityClient",
    "IdentityListChildSessionsCapabilityClient",
    "IdentityListSessionMembersCapabilityClient",
    "IdentityRecordSessionMemberActorRoleCapabilityClient",
    "IdentityRegisterSessionProviderCapabilityClient",
    "IdentityResolveActorCommitsCapabilityClient",
    "IdentityResolveActorSubscriptionsCapabilityClient",
    "IdentityResolveRoleAssignmentsCapabilityClient",
    "IdentitySetupCredentialProfileCapabilityClient",
    "IdentitySignupViaProfileCapabilityClient",
    "IdentityStartSessionCapabilityClient",
    "IdentityUnassignRoleCapabilityClient",
]
