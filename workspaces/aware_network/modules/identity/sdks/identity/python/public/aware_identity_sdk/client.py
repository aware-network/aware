from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID

from aware_identity_service_dto.profile.requests import CreateProfileRequest
from aware_identity_service_dto.credential.profile import (
    CredentialReadinessCheckReceipt,
)
from aware_identity_service_dto.credential.profile import (
    CredentialReadinessCheckRequest,
)
from aware_identity_service_dto.credential.profile import CredentialProfileSetupReceipt
from aware_identity_service_dto.credential.profile import CredentialProfileSetupRequest
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
from aware_identity_service_dto.identity.admission import (
    IdentitySignupViaProfileRequest,
)
from aware_identity_service_dto.profile.requests import IdentityType
from aware_identity_service_dto.actor.commit import ActorCommitResolveRequest
from aware_identity_service_dto.actor.commit import ActorCommitResolveResult
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureReceipt,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.subscription import ActorSubscriptionResolveResult
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
from aware_types import JsonObject
from aware_types import JsonValue


DEFAULT_IDENTITY_SDK_SOURCE = "aware_identity_sdk"


class _IdentitySignupViaProfileCapabilityClient(Protocol):
    async def signup_via_profile(
        self,
        request: IdentitySignupViaProfileRequest,
    ) -> IdentityAdmissionReceipt: ...


class _IdentitySetupCredentialProfileCapabilityClient(Protocol):
    async def setup_credential_profile(
        self,
        request: CredentialProfileSetupRequest,
    ) -> CredentialProfileSetupReceipt: ...


class _IdentityCheckCredentialReadinessCapabilityClient(Protocol):
    async def check_credential_readiness(
        self,
        request: CredentialReadinessCheckRequest,
    ) -> CredentialReadinessCheckReceipt: ...


class _IdentityAssignRoleCapabilityClient(Protocol):
    async def assign_role(
        self,
        request: RoleAssignmentRequest,
    ) -> RoleAssignmentReceipt: ...


class _IdentityUnassignRoleCapabilityClient(Protocol):
    async def unassign_role(
        self,
        request: RoleUnassignmentRequest,
    ) -> RoleUnassignmentReceipt: ...


class _IdentityResolveRoleAssignmentsCapabilityClient(Protocol):
    async def resolve_role_assignments(
        self,
        request: RoleAssignmentResolveRequest,
    ) -> RoleAssignmentResolveResult: ...


class _IdentityResolveActorCommitsCapabilityClient(Protocol):
    async def resolve_actor_commits(
        self,
        request: ActorCommitResolveRequest,
    ) -> ActorCommitResolveResult: ...


class _IdentityEnsureActorSubscriptionCapabilityClient(Protocol):
    async def ensure_actor_subscription(
        self,
        request: ActorSubscriptionEnsureRequest,
    ) -> ActorSubscriptionEnsureReceipt: ...


class _IdentityResolveActorSubscriptionsCapabilityClient(Protocol):
    async def resolve_actor_subscriptions(
        self,
        request: ActorSubscriptionResolveRequest,
    ) -> ActorSubscriptionResolveResult: ...


class _IdentityStartSessionCapabilityClient(Protocol):
    async def start_session(
        self,
        request: SessionStartRequest,
    ) -> SessionStartReceipt: ...


class _IdentityDescribeSessionCapabilityClient(Protocol):
    async def describe_session(
        self,
        request: SessionDescribeRequest,
    ) -> SessionDescribeResult: ...


class _IdentityListChildSessionsCapabilityClient(Protocol):
    async def list_child_sessions(
        self,
        request: ChildSessionsListRequest,
    ) -> ChildSessionsListResult: ...


class _IdentityListActorSessionsCapabilityClient(Protocol):
    async def list_actor_sessions(
        self,
        request: ActorSessionsListRequest,
    ) -> ActorSessionsListResult: ...


class _IdentityApiNamespaceClient(Protocol):
    @property
    def signup_via_profile(self) -> _IdentitySignupViaProfileCapabilityClient: ...

    @property
    def setup_credential_profile(
        self,
    ) -> _IdentitySetupCredentialProfileCapabilityClient: ...

    @property
    def check_credential_readiness(
        self,
    ) -> _IdentityCheckCredentialReadinessCapabilityClient: ...

    @property
    def assign_role(self) -> _IdentityAssignRoleCapabilityClient: ...

    @property
    def unassign_role(self) -> _IdentityUnassignRoleCapabilityClient: ...

    @property
    def resolve_role_assignments(
        self,
    ) -> _IdentityResolveRoleAssignmentsCapabilityClient: ...

    @property
    def resolve_actor_commits(self) -> _IdentityResolveActorCommitsCapabilityClient: ...

    @property
    def ensure_actor_subscription(
        self,
    ) -> _IdentityEnsureActorSubscriptionCapabilityClient: ...

    @property
    def resolve_actor_subscriptions(
        self,
    ) -> _IdentityResolveActorSubscriptionsCapabilityClient: ...

    @property
    def start_session(self) -> _IdentityStartSessionCapabilityClient: ...

    @property
    def describe_session(self) -> _IdentityDescribeSessionCapabilityClient: ...

    @property
    def list_child_sessions(self) -> _IdentityListChildSessionsCapabilityClient: ...

    @property
    def list_actor_sessions(self) -> _IdentityListActorSessionsCapabilityClient: ...


class IdentityApiClient(Protocol):
    @property
    def identity(self) -> _IdentityApiNamespaceClient: ...


class IdentitySdkError(RuntimeError):
    pass


class IdentityGateStatus(str, Enum):
    crossed = "crossed"
    missing_identity = "missing_identity"
    missing_actor = "missing_actor"
    unauthenticated = "unauthenticated"
    actor_mismatch = "actor_mismatch"


@dataclass(frozen=True, slots=True)
class IdentityAdmissionProfile:
    display_name: str
    public_handle: str
    full_name: str
    country_code: str
    language_code: str
    bio: str | None = None
    image_id: UUID | None = None
    image_sha: str | None = None
    image_mime_type: str | None = None
    image_size_bytes: int | None = None

    def to_create_profile_request(
        self,
        *,
        identity_type: IdentityType,
    ) -> CreateProfileRequest:
        return CreateProfileRequest(
            display_name=self.display_name,
            public_handle=self.public_handle,
            full_name=self.full_name,
            country_code=self.country_code,
            language_code=self.language_code,
            bio=self.bio,
            identity_type=identity_type,
            image_id=self.image_id,
            image_sha=self.image_sha,
            image_mime_type=self.image_mime_type,
            image_size_bytes=self.image_size_bytes,
        )


@dataclass(frozen=True, slots=True)
class IdentityAdmission:
    identity_id: UUID | None
    actor_id: UUID | None
    identity_profile_id: UUID | None
    public_handle: str | None
    identity_type: IdentityType
    info: str | None
    receipt: IdentityAdmissionReceipt

    @classmethod
    def from_receipt(
        cls,
        *,
        receipt: IdentityAdmissionReceipt,
        identity_type: IdentityType,
    ) -> "IdentityAdmission":
        return cls(
            identity_id=receipt.identity_id,
            actor_id=receipt.actor_id,
            identity_profile_id=receipt.identity_profile_id,
            public_handle=receipt.public_handle,
            identity_type=identity_type,
            info=receipt.info,
            receipt=receipt,
        )


@dataclass(frozen=True, slots=True)
class IdentityGateSnapshot:
    status: IdentityGateStatus
    identity_id: UUID | None
    expected_actor_id: UUID | None
    authenticated_actor_id: UUID | None
    admitted_actor_id: UUID | None = None
    identity_type: IdentityType | None = None
    public_handle: str | None = None
    reason: str | None = None

    @property
    def crossed(self) -> bool:
        return self.status is IdentityGateStatus.crossed


@dataclass(frozen=True, slots=True)
class IdentitySdkClient:
    api_client: IdentityApiClient

    async def admit_identity_via_profile(
        self,
        *,
        public_key: str,
        profile: IdentityAdmissionProfile,
        identity_type: IdentityType | str,
        request_id: UUID | None = None,
        source: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> IdentityAdmission:
        resolved_identity_type = _coerce_identity_type(identity_type)
        receipt = await self.api_client.identity.signup_via_profile.signup_via_profile(
            IdentitySignupViaProfileRequest(
                public_key=public_key,
                create_profile_request=profile.to_create_profile_request(
                    identity_type=resolved_identity_type,
                ),
                request_id=request_id,
                source=source,
            )
        )
        return IdentityAdmission.from_receipt(
            receipt=receipt,
            identity_type=resolved_identity_type,
        )

    async def admit_human(
        self,
        *,
        public_key: str,
        profile: IdentityAdmissionProfile,
        request_id: UUID | None = None,
        source: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> IdentityAdmission:
        return await self.admit_identity_via_profile(
            public_key=public_key,
            profile=profile,
            identity_type=IdentityType.human,
            request_id=request_id,
            source=source,
        )

    async def admit_agent_identity(
        self,
        *,
        public_key: str,
        profile: IdentityAdmissionProfile,
        request_id: UUID | None = None,
        source: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> IdentityAdmission:
        return await self.admit_identity_via_profile(
            public_key=public_key,
            profile=profile,
            identity_type=IdentityType.agent,
            request_id=request_id,
            source=source,
        )

    async def setup_credential_profile(
        self,
        *,
        identity_id: UUID,
        profile_key: str,
        secret_ref_key: str,
        secret_name: str,
        target_kind: str = "aware_api",
        credential_kind: str = "api_key",
        status: str = "planned",
        display_name: str | None = None,
        target_name: str | None = None,
        issuer: str | None = None,
        audience: str | None = None,
        external_subject: str | None = None,
        created_at_utc: str | None = None,
        updated_at_utc: str | None = None,
        expires_at_utc: str | None = None,
        metadata: JsonObject | None = None,
        resolver_kind: str = "env_var",
        locator: str | None = None,
        username_hint: str | None = None,
        material_hint: str | None = None,
        fingerprint_sha256: str | None = None,
        secret_created_at_utc: str | None = None,
        secret_rotated_at_utc: str | None = None,
        secret_metadata: JsonObject | None = None,
        request_id: UUID | None = None,
        source: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> CredentialProfileSetupReceipt:
        return await self.api_client.identity.setup_credential_profile.setup_credential_profile(
            CredentialProfileSetupRequest(
                identity_id=identity_id,
                profile_key=profile_key,
                target_kind=target_kind,
                credential_kind=credential_kind,
                status=status,
                display_name=display_name,
                target_name=target_name,
                issuer=issuer,
                audience=audience,
                external_subject=external_subject,
                created_at_utc=created_at_utc,
                updated_at_utc=updated_at_utc,
                expires_at_utc=expires_at_utc,
                metadata=metadata,
                secret_ref_key=secret_ref_key,
                resolver_kind=resolver_kind,
                secret_name=secret_name,
                locator=locator,
                username_hint=username_hint,
                material_hint=material_hint,
                fingerprint_sha256=fingerprint_sha256,
                secret_created_at_utc=secret_created_at_utc,
                secret_rotated_at_utc=secret_rotated_at_utc,
                secret_metadata=secret_metadata,
                request_id=request_id,
                source=source,
            )
        )

    async def check_credential_readiness(
        self,
        *,
        identity_id: UUID,
        secret_ref_key: str,
        credential_profile_id: UUID | None = None,
        profile_key: str | None = None,
        target_kind: str = "aware_api",
        receipt_key: str | None = None,
        resolver_kind: str = "env_var",
        secret_name: str | None = None,
        checked_at_utc: str | None = None,
        require_non_empty: bool = True,
        details: JsonObject | None = None,
        request_id: UUID | None = None,
        source: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> CredentialReadinessCheckReceipt:
        readiness_client = self.api_client.identity.check_credential_readiness
        return await readiness_client.check_credential_readiness(
            CredentialReadinessCheckRequest(
                identity_id=identity_id,
                credential_profile_id=credential_profile_id,
                profile_key=profile_key,
                target_kind=target_kind,
                receipt_key=receipt_key,
                resolver_kind=resolver_kind,
                secret_ref_key=secret_ref_key,
                secret_name=secret_name,
                checked_at_utc=checked_at_utc,
                require_non_empty=require_non_empty,
                details=details,
                request_id=request_id,
                source=source,
            )
        )

    async def assign_role(
        self,
        *,
        actor_id: UUID,
        class_instance_identity_id: UUID,
        role_config_id: UUID | None = None,
        role_config_name: str | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        request_id: UUID | None = None,
        reason: str | None = None,
        source_service: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> RoleAssignmentReceipt:
        _ensure_role_selector(
            role_config_id=role_config_id,
            role_config_name=role_config_name,
        )
        return await self.api_client.identity.assign_role.assign_role(
            RoleAssignmentRequest(
                actor_id=actor_id,
                role_config_id=role_config_id,
                role_config_name=role_config_name,
                class_instance_identity_id=class_instance_identity_id,
                object_instance_graph_branch_key=object_instance_graph_branch_key,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                request_id=request_id,
                reason=reason,
                source_service=source_service,
            )
        )

    async def unassign_role(
        self,
        *,
        actor_id: UUID,
        class_instance_identity_id: UUID,
        role_config_id: UUID | None = None,
        role_config_name: str | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        request_id: UUID | None = None,
        reason: str | None = None,
        source_service: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
    ) -> RoleUnassignmentReceipt:
        _ensure_role_selector(
            role_config_id=role_config_id,
            role_config_name=role_config_name,
        )
        return await self.api_client.identity.unassign_role.unassign_role(
            RoleUnassignmentRequest(
                actor_id=actor_id,
                role_config_id=role_config_id,
                role_config_name=role_config_name,
                class_instance_identity_id=class_instance_identity_id,
                object_instance_graph_branch_key=object_instance_graph_branch_key,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                request_id=request_id,
                reason=reason,
                source_service=source_service,
            )
        )

    async def resolve_role_assignments(
        self,
        *,
        class_instance_identity_id: UUID,
        actor_id: UUID | None = None,
        role_config_id: UUID | None = None,
        role_config_name: str | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> RoleAssignmentResolveResult:
        return await self.api_client.identity.resolve_role_assignments.resolve_role_assignments(
            RoleAssignmentResolveRequest(
                actor_id=actor_id,
                role_config_id=role_config_id,
                role_config_name=role_config_name,
                class_instance_identity_id=class_instance_identity_id,
                object_instance_graph_branch_key=object_instance_graph_branch_key,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                request_id=request_id,
            )
        )

    async def resolve_actor_commits(
        self,
        *,
        actor_id: UUID,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        domain_commit_id: UUID | None = None,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        receipt_actor_id: UUID | None = None,
        function_id: UUID | None = None,
        object_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_id: UUID | None = None,
        root_object_id: UUID | None = None,
        source: str | None = None,
        limit: int = 100,
        request_id: UUID | None = None,
    ) -> ActorCommitResolveResult:
        return (
            await self.api_client.identity.resolve_actor_commits.resolve_actor_commits(
                ActorCommitResolveRequest(
                    request_id=request_id,
                    actor_id=actor_id,
                    domain_branch_id=domain_branch_id,
                    domain_projection_hash=domain_projection_hash,
                    domain_commit_id=domain_commit_id,
                    environment_id=environment_id,
                    process_id=process_id,
                    thread_id=thread_id,
                    receipt_actor_id=receipt_actor_id,
                    function_id=function_id,
                    object_id=object_id,
                    class_instance_identity_id=class_instance_identity_id,
                    object_instance_graph_id=object_instance_graph_id,
                    root_object_id=root_object_id,
                    source=source,
                    limit=limit,
                )
            )
        )

    async def ensure_actor_subscription(
        self,
        *,
        actor_id: UUID,
        event_config_condition_config_scope_id: UUID,
        name: str,
        description: str | None = None,
        action_type: str | None = None,
        event_config_action_config_ids: Sequence[UUID] | None = None,
        addressing_policy: str = "any",
        is_enabled: bool = True,
        status: str = "active",
        filter_mode: str = "all_instances",
        filter_config: JsonValue | None = None,
        priority: int = 0,
        batch_mode: bool = False,
        batch_window_ms: int = 1000,
        max_batch_size: int = 100,
        require_read_access: bool = True,
        check_ownership: bool = True,
        rate_limit_per_minute: int | None = None,
        rate_limit_per_hour: int | None = None,
        request_id: UUID | None = None,
    ) -> ActorSubscriptionEnsureReceipt:
        subscription_client = self.api_client.identity.ensure_actor_subscription
        return await subscription_client.ensure_actor_subscription(
            ActorSubscriptionEnsureRequest(
                request_id=request_id,
                actor_id=actor_id,
                event_config_condition_config_scope_id=(
                    event_config_condition_config_scope_id
                ),
                name=name,
                description=description,
                action_type=action_type,
                event_config_action_config_ids=list(
                    event_config_action_config_ids or ()
                ),
                addressing_policy=addressing_policy,
                is_enabled=is_enabled,
                status=status,
                filter_mode=filter_mode,
                filter_config=filter_config,
                priority=priority,
                batch_mode=batch_mode,
                batch_window_ms=batch_window_ms,
                max_batch_size=max_batch_size,
                require_read_access=require_read_access,
                check_ownership=check_ownership,
                rate_limit_per_minute=rate_limit_per_minute,
                rate_limit_per_hour=rate_limit_per_hour,
            )
        )

    async def resolve_actor_subscriptions(
        self,
        *,
        actor_id: UUID | None = None,
        event_config_condition_config_id: UUID | None = None,
        object_instance_graph_identity_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        include_inactive: bool = False,
        include_disabled: bool = False,
        request_id: UUID | None = None,
    ) -> ActorSubscriptionResolveResult:
        subscription_client = self.api_client.identity.resolve_actor_subscriptions
        return await subscription_client.resolve_actor_subscriptions(
            ActorSubscriptionResolveRequest(
                request_id=request_id,
                actor_id=actor_id,
                event_config_condition_config_id=event_config_condition_config_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                include_inactive=include_inactive,
                include_disabled=include_disabled,
            )
        )

    async def start_session(
        self,
        *,
        session_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        parent_session_id: UUID | None = None,
        created_by_actor_id: UUID | None = None,
        source_kind: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = None,
        request_id: UUID | None = None,
    ) -> SessionStartReceipt:
        return await self.api_client.identity.start_session.start_session(
            SessionStartRequest(
                request_id=request_id,
                session_config_id=session_config_id,
                key=key,
                title=title,
                description=description,
                purpose=purpose,
                status=status,
                parent_session_id=parent_session_id,
                created_by_actor_id=created_by_actor_id,
                source_kind=source_kind,
                source_ref=source_ref,
                metadata_json=metadata_json or JsonObject(),
            )
        )

    async def start_child_session(
        self,
        *,
        parent_session_id: UUID,
        session_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        created_by_actor_id: UUID | None = None,
        source_kind: str | None = DEFAULT_IDENTITY_SDK_SOURCE,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = None,
        request_id: UUID | None = None,
    ) -> SessionStartReceipt:
        return await self.start_session(
            request_id=request_id,
            session_config_id=session_config_id,
            key=key,
            title=title,
            description=description,
            purpose=purpose,
            status=status,
            parent_session_id=parent_session_id,
            created_by_actor_id=created_by_actor_id,
            source_kind=source_kind,
            source_ref=source_ref,
            metadata_json=metadata_json,
        )

    async def describe_session(
        self,
        *,
        session_id: UUID,
        request_id: UUID | None = None,
    ) -> SessionDescribeResult:
        return await self.api_client.identity.describe_session.describe_session(
            SessionDescribeRequest(
                request_id=request_id,
                session_id=session_id,
            )
        )

    async def list_child_sessions(
        self,
        *,
        parent_session_id: UUID,
        session_config_id: UUID | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        request_id: UUID | None = None,
    ) -> ChildSessionsListResult:
        return await self.api_client.identity.list_child_sessions.list_child_sessions(
            ChildSessionsListRequest(
                request_id=request_id,
                parent_session_id=parent_session_id,
                session_config_id=session_config_id,
                status=status,
                include_inactive=include_inactive,
            )
        )

    async def list_actor_sessions(
        self,
        *,
        actor_id: UUID,
        parent_session_id: UUID | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        request_id: UUID | None = None,
    ) -> ActorSessionsListResult:
        return await self.api_client.identity.list_actor_sessions.list_actor_sessions(
            ActorSessionsListRequest(
                request_id=request_id,
                actor_id=actor_id,
                parent_session_id=parent_session_id,
                status=status,
                include_inactive=include_inactive,
            )
        )

    def build_gate_snapshot(
        self,
        *,
        admission: IdentityAdmission | None = None,
        identity_id: UUID | None = None,
        expected_actor_id: UUID | None = None,
        authenticated_actor_id: UUID | None = None,
        authenticated: bool = True,
        identity_type: IdentityType | str | None = None,
        public_handle: str | None = None,
    ) -> IdentityGateSnapshot:
        return build_identity_gate_snapshot(
            admission=admission,
            identity_id=identity_id,
            expected_actor_id=expected_actor_id,
            authenticated_actor_id=authenticated_actor_id,
            authenticated=authenticated,
            identity_type=identity_type,
            public_handle=public_handle,
        )


def build_identity_gate_snapshot(
    *,
    admission: IdentityAdmission | None = None,
    identity_id: UUID | None = None,
    expected_actor_id: UUID | None = None,
    authenticated_actor_id: UUID | None = None,
    authenticated: bool = True,
    identity_type: IdentityType | str | None = None,
    public_handle: str | None = None,
) -> IdentityGateSnapshot:
    resolved_identity_id = identity_id or (
        admission.identity_id if admission is not None else None
    )
    admitted_actor_id = admission.actor_id if admission is not None else None
    resolved_expected_actor_id = expected_actor_id or admitted_actor_id
    resolved_identity_type = (
        _coerce_identity_type(identity_type)
        if identity_type is not None
        else admission.identity_type if admission is not None else None
    )
    resolved_public_handle = public_handle or (
        admission.public_handle if admission is not None else None
    )

    if resolved_identity_id is None:
        status = IdentityGateStatus.missing_identity
        reason = "Identity admission has not produced an identity_id."
    elif resolved_expected_actor_id is None:
        status = IdentityGateStatus.missing_actor
        reason = "Identity admission has not produced an actor_id."
    elif not authenticated or authenticated_actor_id is None:
        status = IdentityGateStatus.unauthenticated
        reason = "No authenticated actor is available for the gate check."
    elif authenticated_actor_id != resolved_expected_actor_id:
        status = IdentityGateStatus.actor_mismatch
        reason = "Authenticated actor does not match the expected Identity actor."
    else:
        status = IdentityGateStatus.crossed
        reason = None

    return IdentityGateSnapshot(
        status=status,
        identity_id=resolved_identity_id,
        expected_actor_id=resolved_expected_actor_id,
        authenticated_actor_id=authenticated_actor_id,
        admitted_actor_id=admitted_actor_id,
        identity_type=resolved_identity_type,
        public_handle=resolved_public_handle,
        reason=reason,
    )


def _coerce_identity_type(identity_type: IdentityType | str) -> IdentityType:
    if isinstance(identity_type, IdentityType):
        return identity_type
    try:
        return IdentityType(identity_type)
    except ValueError as exc:
        valid_values = ", ".join(member.value for member in IdentityType)
        raise IdentitySdkError(
            f"Unknown IdentityType {identity_type!r}; expected one of: {valid_values}."
        ) from exc


def _ensure_role_selector(
    *,
    role_config_id: UUID | None,
    role_config_name: str | None,
) -> None:
    if role_config_id is None and not role_config_name:
        raise IdentitySdkError(
            "A role_config_id or role_config_name is required for role mutation."
        )
