from __future__ import annotations

# pyright: reportMissingImports=false

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Protocol, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types import JsonObject
from pydantic import BaseModel, Field

from aware_identity.admission import (
    IdentityAdmissionOperationContext,
    IdentityAdmissionRuntimeContext,
    IdentityAdmissionRuntimeRequest,
    admit_identity_via_profile,
    resolve_identity_admission_runtime_context,
)
from aware_identity.credential import (
    CredentialReadinessCheckRuntimeRequest,
    CredentialProfileSetupRuntimeRequest,
    IdentityCredentialOperationContext,
    IdentityCredentialRuntimeContext,
    check_credential_readiness,
    resolve_identity_credential_runtime_context,
    setup_credential_profile,
)
from aware_identity.meta_runtime import IdentityMetaRuntimeLaneBinder
from aware_identity_service.admission_reactivity_policy import (
    ensure_identity_admission_reactivity_policy,
)
from aware_identity.session import (
    IdentitySessionOperationContext,
    IdentitySessionRuntimeContext,
    attach_session_provider_session as runtime_attach_session_provider_session,
    bind_session_config_actor_config as runtime_bind_session_config_actor_config,
    bind_session_provider_config as runtime_bind_session_provider_config,
    ensure_session_config as runtime_ensure_session_config,
    join_session as runtime_join_session,
    record_session_member_actor_role as runtime_record_session_member_actor_role,
    register_session_provider as runtime_register_session_provider,
    resolve_identity_session_runtime_context,
    start_session as runtime_start_session,
)
from aware_identity.actor.subscription import (
    ActorSubscriptionMaterializationContext,
    ensure_actor_subscription,
    resolve_actor_subscriptions,
)
from aware_identity.actor.commit import (
    ActorCommitMaterializationContext,
    ensure_actor_commit,
    resolve_actor_commits,
)
from aware_identity.role.assignment import (
    RoleAssignmentMaterializationContext,
    ensure_role_assignment,
    resolve_role_assignments,
    unassign_role,
)
from aware_identity_service_dto.role.assignment import (
    RoleAssignmentRequest as CanonicalRoleAssignmentRequest,
    RoleAssignmentResolveRequest as CanonicalRoleAssignmentResolveRequest,
    RoleUnassignmentRequest as CanonicalRoleUnassignmentRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureRequest as CanonicalActorSubscriptionEnsureRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest as CanonicalActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureRequest as CanonicalActorCommitEnsureRequest,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitResolveRequest as CanonicalActorCommitResolveRequest,
)
from aware_identity_ontology.identity.create_profile_request import (
    CreateProfileRequest as CanonicalCreateProfileRequest,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    ServiceApiMaterializationContext,
    current_service_api_host_context,
    require_current_service_api_materialization_context,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    require_service_ontology_replica_orm_session,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

from aware_identity_service_dto.actor.subscription import ActorSubscriptionEnsureReceipt
from aware_identity_service_dto.actor.subscription import ActorSubscriptionEnsureRequest
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.subscription import ActorSubscriptionResolveResult
from aware_identity_service_dto.actor.commit import ActorCommitEnsureReceipt
from aware_identity_service_dto.actor.commit import ActorCommitEnsureRequest
from aware_identity_service_dto.actor.commit import ActorCommitResolveRequest
from aware_identity_service_dto.actor.commit import ActorCommitResolveResult
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
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
    SessionConfigActorConfigSummary,
    SessionConfigEnsureReceipt,
    SessionConfigEnsureRequest,
    SessionConfigSummary,
    SessionDescribeRequest,
    SessionDescribeResult,
    SessionJoinReceipt,
    SessionJoinRequest,
    SessionMemberActorRoleRecordReceipt,
    SessionMemberActorRoleRecordRequest,
    SessionMemberActorRoleSummary,
    SessionMembersListRequest,
    SessionMembersListResult,
    SessionMemberSummary,
    SessionProviderConfigBindReceipt,
    SessionProviderConfigBindRequest,
    SessionProviderRegisterReceipt,
    SessionProviderRegisterRequest,
    SessionProviderSessionAttachReceipt,
    SessionProviderSessionAttachRequest,
    SessionProviderSessionConfigSummary,
    SessionProviderSessionSummary,
    SessionProviderSummary,
    SessionStartReceipt,
    SessionStartRequest,
    SessionSummary,
)

_ModelT = TypeVar("_ModelT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class _IdentityServiceMaterializationRuntimeContext:
    materialization: ServiceApiMaterializationContext
    actor_id: UUID | None

    @property
    def runtime(self) -> object:
        return self.materialization.runtime

    def projection_hash_for_name(self, projection_name: str) -> str:
        resolver = getattr(
            self.materialization.graph_context,
            "projection_hash_for_name",
            None,
        )
        if callable(resolver):
            return cast(str, resolver(projection_name))
        projection_hash_by_name = getattr(
            self.materialization.graph_context,
            "projection_hash_by_name",
            None,
        )
        if isinstance(projection_hash_by_name, Mapping):
            projection_hash = projection_hash_by_name.get(projection_name)
            if isinstance(projection_hash, str) and projection_hash.strip():
                return projection_hash
        raise ValueError(
            f"Projection {projection_name!r} was not found in Identity materialization context."
        )

    def bind_lane(
        self,
        *,
        projection: str,
        branch_id: UUID,
    ) -> object:
        bind = getattr(self.runtime, "bind", None)
        if not callable(bind):
            raise RuntimeError(
                "Identity service materialization runtime cannot bind lanes."
            )
        return bind(
            projection=projection,
            branch_id=branch_id,
            actor_id=self.actor_id,
        )


def _require_identity_service_materialization_context(
    *,
    actor_id: UUID | None,
) -> _IdentityServiceMaterializationRuntimeContext:
    return _IdentityServiceMaterializationRuntimeContext(
        materialization=require_current_service_api_materialization_context(),
        actor_id=actor_id,
    )


def _require_service_actor_id(*, operation_context: object) -> UUID:
    actor_id = getattr(operation_context, "actor_id", None)
    if isinstance(actor_id, UUID):
        return actor_id
    raise RuntimeError("Identity service protocol requires actor_id.")


_EXPERIENCE_SERVICE_API_PACKAGE_NAME = "experience-service-api"
_PERSONAL_LAYOUT_ROLE_CONFIG_NAME = "aware.interface.layout.personal.actor"
_PERSONAL_LAYOUT_ROLE_CLASS_INSTANCE_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://identity/personal-interface-layout/v0",
)


def build_aware_identity_service_protocol_handler(
    *,
    role_grant_authority_backend: "IdentityRoleGrantAuthorityBackend | None" = None,
) -> object:
    return _AwareIdentityServiceProtocolHandler(
        role_grant_authority_backend=role_grant_authority_backend,
    )


class IdentityRoleGrantAuthorityRequest(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID
    role_config_id: UUID | None = None
    role_config_name: str | None = None
    class_instance_identity_id: UUID
    source_service: str | None = None
    grant_authority_kind: str
    grant_authority_id: UUID
    grant_context_kind: str
    grant_context_id: UUID
    grant_context_ref: str | None = None
    grant_evidence: JsonObject = Field(default_factory=JsonObject)


class IdentityRoleGrantAuthorityDecision(BaseModel):
    accepted: bool = False
    reason: str | None = None
    evidence: JsonObject = Field(default_factory=JsonObject)


class IdentityRoleGrantAuthorityBackend(Protocol):
    async def authorize_role_assignment_grant(
        self,
        *,
        request: IdentityRoleGrantAuthorityRequest,
    ) -> IdentityRoleGrantAuthorityDecision: ...


class _IdentityProtocolSupport:
    def __init__(
        self,
        *,
        role_grant_authority_backend: IdentityRoleGrantAuthorityBackend | None = None,
    ) -> None:
        self._role_grant_authority_backend = role_grant_authority_backend

    def host_context(self) -> ServiceApiHostContext:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Identity service protocol requires an active Service API host context."
            )
        return host_context

    async def runtime_context(self) -> IdentityAdmissionRuntimeContext:
        return resolve_identity_admission_runtime_context(
            lane_binder=self._meta_runtime_lane_binder(),
        )

    async def credential_runtime_context(self) -> IdentityCredentialRuntimeContext:
        return resolve_identity_credential_runtime_context(
            lane_binder=self._meta_runtime_lane_binder(),
        )

    async def session_runtime_context(self) -> IdentitySessionRuntimeContext:
        return resolve_identity_session_runtime_context(
            lane_binder=self._meta_runtime_lane_binder(),
        )

    def session_operation_context(self) -> IdentitySessionOperationContext:
        operation_context = self.host_context().operation_context
        return IdentitySessionOperationContext(
            actor_id=_require_service_actor_id(operation_context=operation_context),
        )

    def _meta_runtime_lane_binder(self) -> IdentityMetaRuntimeLaneBinder:
        host_context = self.host_context()
        materialization = host_context.materialization
        runtime = None if materialization is None else materialization.runtime
        if not callable(getattr(runtime, "bind", None)):
            raise RuntimeError(
                "Identity service protocol requires an active Meta runtime lane binder."
            )
        return cast(IdentityMetaRuntimeLaneBinder, runtime)

    async def read_identity_from_ontology_replica(
        self,
        *,
        identity_id: UUID,
    ) -> object | None:
        _ = require_service_ontology_replica_orm_session()
        from aware_identity.identity_read import (  # noqa: PLC0415
            read_identity_from_identity_replica,
        )

        return await read_identity_from_identity_replica(identity_id=identity_id)

    async def list_actor_sessions_from_ontology_replica(
        self,
        *,
        request: ActorSessionsListRequest,
    ) -> ActorSessionsListResult:
        _ = require_service_ontology_replica_orm_session()
        from aware_identity.session_read import (  # noqa: PLC0415
            list_actor_sessions_from_identity_replica,
        )

        return await list_actor_sessions_from_identity_replica(
            request=request,
        )

    async def describe_session_from_ontology_replica(
        self,
        *,
        request: SessionDescribeRequest,
    ) -> SessionDescribeResult:
        _ = require_service_ontology_replica_orm_session()
        from aware_identity.session_read import (  # noqa: PLC0415
            describe_session_from_identity_replica,
        )

        return await describe_session_from_identity_replica(
            request=request,
        )

    async def list_child_sessions_from_ontology_replica(
        self,
        *,
        request: ChildSessionsListRequest,
    ) -> ChildSessionsListResult:
        _ = require_service_ontology_replica_orm_session()
        from aware_identity.session_read import (  # noqa: PLC0415
            list_child_sessions_from_identity_replica,
        )

        return await list_child_sessions_from_identity_replica(
            request=request,
        )

    async def list_session_members_from_ontology_replica(
        self,
        *,
        request: SessionMembersListRequest,
    ) -> SessionMembersListResult:
        _ = require_service_ontology_replica_orm_session()
        from aware_identity.session_read import (  # noqa: PLC0415
            list_session_members_from_identity_replica,
        )

        return await list_session_members_from_identity_replica(
            request=request,
        )

    async def build_role_assignment_context(
        self,
        *,
        actor_id: UUID | None,
    ) -> RoleAssignmentMaterializationContext:
        return cast(
            RoleAssignmentMaterializationContext,
            _require_identity_service_materialization_context(actor_id=actor_id),
        )

    async def authorize_role_assignment_grant(
        self,
        *,
        request: RoleAssignmentRequest,
    ) -> IdentityRoleGrantAuthorityDecision:
        authority_request = _grant_authority_request_from_assignment(request=request)
        backend = self._role_grant_authority_backend
        if backend is None:
            raise RuntimeError("identity_role_grant_authority_backend_unavailable")
        decision = await backend.authorize_role_assignment_grant(
            request=authority_request,
        )
        if not decision.accepted:
            raise PermissionError(
                decision.reason or "identity_role_grant_authority_denied"
            )
        return decision

    async def build_actor_subscription_context(
        self,
        *,
        actor_id: UUID | None,
    ) -> ActorSubscriptionMaterializationContext:
        return cast(
            ActorSubscriptionMaterializationContext,
            _require_identity_service_materialization_context(actor_id=actor_id),
        )

    async def build_actor_commit_context(
        self,
        *,
        actor_id: UUID | None,
    ) -> ActorCommitMaterializationContext:
        return cast(
            ActorCommitMaterializationContext,
            _require_identity_service_materialization_context(actor_id=actor_id),
        )

class _IdentityAssignRoleCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def assign_role(
        self,
        request: RoleAssignmentRequest,
    ) -> RoleAssignmentReceipt:
        grant_decision = await self._support.authorize_role_assignment_grant(
            request=request,
        )
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalRoleAssignmentRequest,
        )
        context = await self._support.build_role_assignment_context(
            actor_id=request.actor_id,
        )
        session = require_service_ontology_replica_orm_session()
        receipt = await ensure_role_assignment(
            session=session,
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            receipt,
            model_cls=RoleAssignmentReceipt,
        )
        grant_update = _grant_receipt_update_from_request(
            request=request,
            decision=grant_decision,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-role assignment ensured",
                **grant_update.receipt_update,
                "binding": validated.binding.model_copy(
                    update=grant_update.binding_update,
                ),
            }
        )


class _IdentityResolveRoleAssignmentsCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def resolve_role_assignments(
        self,
        request: RoleAssignmentResolveRequest,
    ) -> RoleAssignmentResolveResult:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalRoleAssignmentResolveRequest,
        )
        context = await self._support.build_role_assignment_context(
            actor_id=request.actor_id,
        )
        session = require_service_ontology_replica_orm_session()
        result = await resolve_role_assignments(
            request=canonical_request,
            session=session,
            context=context,
        )
        validated = _convert_model(
            result,
            model_cls=RoleAssignmentResolveResult,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-role assignments resolved",
            }
        )


class _IdentityUnassignRoleCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def unassign_role(
        self,
        request: RoleUnassignmentRequest,
    ) -> RoleUnassignmentReceipt:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalRoleUnassignmentRequest,
        )
        context = await self._support.build_role_assignment_context(
            actor_id=request.actor_id,
        )
        session = require_service_ontology_replica_orm_session()
        receipt = await unassign_role(
            session=session,
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            receipt,
            model_cls=RoleUnassignmentReceipt,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-role assignment unassigned",
            }
        )


class _IdentityEnsureActorSubscriptionCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def ensure_actor_subscription(
        self,
        request: ActorSubscriptionEnsureRequest,
    ) -> ActorSubscriptionEnsureReceipt:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalActorSubscriptionEnsureRequest,
        )
        context = await self._support.build_actor_subscription_context(
            actor_id=request.actor_id,
        )
        receipt = await ensure_actor_subscription(
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            receipt,
            model_cls=ActorSubscriptionEnsureReceipt,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-subscription ensured",
            }
        )


class _IdentityResolveActorSubscriptionsCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def resolve_actor_subscriptions(
        self,
        request: ActorSubscriptionResolveRequest,
    ) -> ActorSubscriptionResolveResult:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalActorSubscriptionResolveRequest,
        )
        context = await self._support.build_actor_subscription_context(
            actor_id=request.actor_id,
        )
        result = await resolve_actor_subscriptions(
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            result,
            model_cls=ActorSubscriptionResolveResult,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-subscriptions resolved",
            }
        )


class _IdentityEnsureActorCommitCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def ensure_actor_commit(
        self,
        request: ActorCommitEnsureRequest,
    ) -> ActorCommitEnsureReceipt:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalActorCommitEnsureRequest,
        )
        context = await self._support.build_actor_commit_context(
            actor_id=request.actor_id,
        )
        receipt = await ensure_actor_commit(
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            receipt,
            model_cls=ActorCommitEnsureReceipt,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-commit ensured",
            }
        )


class _IdentityResolveActorCommitsCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def resolve_actor_commits(
        self,
        request: ActorCommitResolveRequest,
    ) -> ActorCommitResolveResult:
        canonical_request = _convert_model(
            request,
            model_cls=CanonicalActorCommitResolveRequest,
        )
        context = await self._support.build_actor_commit_context(
            actor_id=request.actor_id,
        )
        result = await resolve_actor_commits(
            request=canonical_request,
            context=context,
        )
        validated = _convert_model(
            result,
            model_cls=ActorCommitResolveResult,
        )
        return validated.model_copy(
            update={
                "request_id": validated.request_id or request.request_id,
                "info": "identity actor-commits resolved",
            }
        )


class _IdentitySignupViaProfileCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def signup_via_profile(
        self,
        request: IdentitySignupViaProfileRequest,
    ) -> IdentityAdmissionReceipt:
        runtime_context = await self._support.runtime_context()
        host_context = self._support.host_context()
        operation_context = host_context.operation_context
        canonical_profile_request = _convert_model(
            request.create_profile_request,
            model_cls=CanonicalCreateProfileRequest,
        )
        await ensure_identity_admission_reactivity_policy(
            host_context=host_context,
            request=request,
            actor_id=operation_context.actor_id,
        )
        receipt = await admit_identity_via_profile(
            runtime_context=runtime_context,
            operation_context=IdentityAdmissionOperationContext(
                actor_id=_require_service_actor_id(
                    operation_context=operation_context,
                ),
            ),
            request=IdentityAdmissionRuntimeRequest(
                public_key=request.public_key,
                create_profile_request=canonical_profile_request,
            ),
        )
        if _should_request_layout_transition(
            host_context=host_context,
        ):
            await _request_layout_transition_after_admission(
                host_context=host_context,
                request=request,
                identity_id=receipt.identity_id,
                actor_id=receipt.actor_id,
            )
        return IdentityAdmissionReceipt(
            identity_id=receipt.identity_id,
            actor_id=receipt.actor_id,
            identity_profile_id=receipt.identity_profile_id,
            public_handle=receipt.public_handle,
            info=receipt.info,
        )


async def _request_layout_transition_after_admission(
    *,
    host_context: ServiceApiHostContext,
    request: IdentitySignupViaProfileRequest,
    identity_id: UUID,
    actor_id: UUID,
) -> None:
    namespace = _interface_namespace_from_invocation_context(
        host_context.invocation_context
    )
    if namespace is None:
        return

    from aware_experience_service_api import AwareExperienceServiceApiClient
    from aware_experience_service_dto.experience.layout_transition.models import (
        ExperienceLayoutActorRoleGate,
    )
    from aware_experience_service_dto.experience.layout_transition.service_operation import (
        RequestExperienceLayoutTransitionRequest,
    )

    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_EXPERIENCE_SERVICE_API_PACKAGE_NAME,
        actor_id=actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        raise RuntimeError(
            "Identity admission layout transition requires a Service API "
            "dependency route for experience-service-api."
        )
    client = AwareExperienceServiceApiClient(invoker)
    capability = client.experience.request_experience_layout_transition
    await capability.request_experience_layout_transition(
        RequestExperienceLayoutTransitionRequest(
            request_id=request.request_id,
            namespace=namespace,
            actor_id=actor_id,
            identity_id=identity_id,
            intent_key="identity.admission",
            role_gate=ExperienceLayoutActorRoleGate(
                actor_id=actor_id,
                role_config_name=_PERSONAL_LAYOUT_ROLE_CONFIG_NAME,
                class_instance_identity_id=_layout_role_class_instance_identity_id(
                    actor_id=actor_id,
                ),
            ),
            reason="identity admission accepted",
            idempotency_key=_layout_transition_idempotency_key(
                namespace=namespace,
                actor_id=actor_id,
                request_id=request.request_id,
            ),
        )
    )


def _should_request_layout_transition(
    *,
    host_context: ServiceApiHostContext,
) -> bool:
    return _layout_transition_enabled(host_context.invocation_context)


def _layout_transition_enabled(
    invocation_context: Mapping[str, object] | None,
) -> bool:
    if invocation_context is None:
        return False
    for key in (
        "layout_transition",
        "identity_admission_layout_transition",
    ):
        if invocation_context.get(key) is True:
            return True
    for key in ("experience", "interface"):
        nested = invocation_context.get(key)
        if isinstance(nested, Mapping):
            if nested.get("layout_transition") is True:
                return True
    return False


def _interface_namespace_from_invocation_context(
    invocation_context: Mapping[str, object] | None,
) -> str | None:
    if invocation_context is None:
        return None
    interface_context = invocation_context.get("interface")
    if isinstance(interface_context, Mapping):
        namespace = _normalize_optional_text(interface_context.get("namespace"))
        if namespace is not None:
            return namespace
    for key in ("interface_namespace", "namespace"):
        namespace = _normalize_optional_text(invocation_context.get(key))
        if namespace is not None:
            return namespace
    return None


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return cast(JsonObject, dict(host_context.invocation_context))


def _layout_role_class_instance_identity_id(*, actor_id: UUID) -> UUID:
    return uuid5(
        _PERSONAL_LAYOUT_ROLE_CLASS_INSTANCE_NAMESPACE,
        f"actor:{actor_id}",
    )


def _layout_transition_idempotency_key(
    *,
    namespace: str,
    actor_id: UUID,
    request_id: UUID | None,
) -> str:
    request_part = str(request_id) if request_id is not None else "no-request-id"
    return f"identity-layout-transition:{namespace}:{actor_id}:{request_part}"


def _normalize_optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


class _IdentitySetupCredentialProfileCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def setup_credential_profile(
        self,
        request: CredentialProfileSetupRequest,
    ) -> CredentialProfileSetupReceipt:
        runtime_context = await self._support.credential_runtime_context()
        operation_context = self._support.host_context().operation_context
        receipt = await setup_credential_profile(
            runtime_context=runtime_context,
            operation_context=IdentityCredentialOperationContext(
                actor_id=_require_service_actor_id(
                    operation_context=operation_context,
                ),
            ),
            request=CredentialProfileSetupRuntimeRequest(
                identity_id=request.identity_id,
                profile_key=request.profile_key,
                target_kind=request.target_kind,
                credential_kind=request.credential_kind,
                status=request.status,
                display_name=request.display_name,
                target_name=request.target_name,
                issuer=request.issuer,
                audience=request.audience,
                external_subject=request.external_subject,
                created_at_utc=request.created_at_utc,
                updated_at_utc=request.updated_at_utc,
                expires_at_utc=request.expires_at_utc,
                metadata=request.metadata,
                secret_ref_key=request.secret_ref_key,
                resolver_kind=request.resolver_kind,
                secret_name=request.secret_name,
                locator=request.locator,
                username_hint=request.username_hint,
                material_hint=request.material_hint,
                fingerprint_sha256=request.fingerprint_sha256,
                secret_created_at_utc=request.secret_created_at_utc,
                secret_rotated_at_utc=request.secret_rotated_at_utc,
                secret_metadata=request.secret_metadata,
                request_id=request.request_id,
            ),
        )
        return CredentialProfileSetupReceipt(
            request_id=receipt.request_id,
            identity_id=receipt.identity_id,
            credential_profile_id=receipt.credential_profile_id,
            secret_material_ref_id=receipt.secret_material_ref_id,
            profile_key=receipt.profile_key,
            target_kind=receipt.target_kind,
            secret_ref_key=receipt.secret_ref_key,
            resolver_kind=receipt.resolver_kind,
            secret_name=receipt.secret_name,
            raw_secret_stored=receipt.raw_secret_stored,
            info=receipt.info,
        )


class _IdentityCheckCredentialReadinessCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def check_credential_readiness(
        self,
        request: CredentialReadinessCheckRequest,
    ) -> CredentialReadinessCheckReceipt:
        runtime_context = await self._support.credential_runtime_context()
        operation_context = self._support.host_context().operation_context
        receipt = await check_credential_readiness(
            runtime_context=runtime_context,
            operation_context=IdentityCredentialOperationContext(
                actor_id=_require_service_actor_id(
                    operation_context=operation_context,
                ),
            ),
            request=CredentialReadinessCheckRuntimeRequest(
                identity_id=request.identity_id,
                credential_profile_id=request.credential_profile_id,
                profile_key=request.profile_key,
                target_kind=request.target_kind,
                receipt_key=request.receipt_key,
                resolver_kind=request.resolver_kind,
                secret_ref_key=request.secret_ref_key,
                secret_name=request.secret_name,
                checked_at_utc=request.checked_at_utc,
                require_non_empty=request.require_non_empty,
                details=request.details,
                request_id=request.request_id,
            ),
        )
        return CredentialReadinessCheckReceipt(
            request_id=receipt.request_id,
            identity_id=receipt.identity_id,
            credential_profile_id=receipt.credential_profile_id,
            readiness_receipt_id=receipt.readiness_receipt_id,
            profile_key=receipt.profile_key,
            target_kind=receipt.target_kind,
            receipt_key=receipt.receipt_key,
            status=receipt.status,
            available=receipt.available,
            resolver_kind=receipt.resolver_kind,
            secret_ref_key=receipt.secret_ref_key,
            secret_name=receipt.secret_name,
            checked_at_utc=receipt.checked_at_utc,
            missing_requirements=receipt.missing_requirements,
            credential_handle=receipt.credential_handle,
            raw_secret_returned=receipt.raw_secret_returned,
            info=receipt.info,
        )


class _IdentityEnsureSessionConfigCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def ensure_session_config(
        self,
        request: SessionConfigEnsureRequest,
    ) -> SessionConfigEnsureReceipt:
        runtime_context = await self._support.session_runtime_context()
        session_config_id = await runtime_ensure_session_config(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            key=request.key,
            title=request.title,
            description=request.description,
            purpose=request.purpose,
            status=request.status,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionConfigEnsureReceipt(
            request_id=request.request_id,
            session_config=SessionConfigSummary(
                session_config_id=session_config_id,
                key=request.key,
                title=request.title,
                description=request.description,
                purpose=request.purpose,
                status=request.status,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
            ),
            info="identity session config ensured",
        )


class _IdentityBindSessionConfigActorConfigCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def bind_session_config_actor_config(
        self,
        request: SessionConfigActorConfigBindRequest,
    ) -> SessionConfigActorConfigBindReceipt:
        runtime_context = await self._support.session_runtime_context()
        binding_id = await runtime_bind_session_config_actor_config(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_config_id=request.session_config_id,
            actor_config_id=request.actor_config_id,
            status=request.status,
            purpose=request.purpose,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionConfigActorConfigBindReceipt(
            request_id=request.request_id,
            binding=SessionConfigActorConfigSummary(
                session_config_actor_config_id=binding_id,
                session_config_id=request.session_config_id,
                actor_config_id=request.actor_config_id,
                status=request.status,
                purpose=request.purpose,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
            ),
            info="identity session config actor policy bound",
        )


class _IdentityRegisterSessionProviderCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def register_session_provider(
        self,
        request: SessionProviderRegisterRequest,
    ) -> SessionProviderRegisterReceipt:
        runtime_context = await self._support.session_runtime_context()
        provider_id = await runtime_register_session_provider(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            provider_key=request.provider_key,
            provider_kind=request.provider_kind,
            title=request.title,
            status=request.status,
            contract_ref=request.contract_ref,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionProviderRegisterReceipt(
            request_id=request.request_id,
            provider=SessionProviderSummary(
                session_provider_id=provider_id,
                provider_key=request.provider_key,
                provider_kind=request.provider_kind,
                title=request.title,
                status=request.status,
                contract_ref=request.contract_ref,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
            ),
            info="identity session provider registered",
        )


class _IdentityBindSessionProviderConfigCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def bind_session_provider_config(
        self,
        request: SessionProviderConfigBindRequest,
    ) -> SessionProviderConfigBindReceipt:
        runtime_context = await self._support.session_runtime_context()
        binding_id = await runtime_bind_session_provider_config(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_provider_id=request.session_provider_id,
            config_key=request.config_key,
            session_config_id=request.session_config_id,
            title=request.title,
            status=request.status,
            provider_contract_ref=request.provider_contract_ref,
            selection_policy=request.selection_policy,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionProviderConfigBindReceipt(
            request_id=request.request_id,
            binding=SessionProviderSessionConfigSummary(
                session_provider_session_config_id=binding_id,
                session_provider_id=request.session_provider_id,
                config_key=request.config_key,
                session_config_id=request.session_config_id,
                title=request.title,
                status=request.status,
                provider_contract_ref=request.provider_contract_ref,
                selection_policy=request.selection_policy,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
            ),
            info="identity session provider config bound",
        )


class _IdentityStartSessionCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def start_session(
        self,
        request: SessionStartRequest,
    ) -> SessionStartReceipt:
        runtime_context = await self._support.session_runtime_context()
        session_id = await runtime_start_session(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_config_id=request.session_config_id,
            key=request.key,
            title=request.title,
            description=request.description,
            purpose=request.purpose,
            status=request.status,
            parent_session_id=request.parent_session_id,
            parent_session_scope_key=(
                str(request.parent_session_id)
                if request.parent_session_id is not None
                else "root"
            ),
            created_by_actor_id=request.created_by_actor_id,
            source_kind=request.source_kind,
            source_ref=request.source_ref,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionStartReceipt(
            request_id=request.request_id,
            session=SessionSummary(
                session_id=session_id,
                session_config_id=request.session_config_id,
                key=request.key,
                title=request.title,
                description=request.description,
                purpose=request.purpose,
                status=request.status,
                parent_session_id=request.parent_session_id,
                created_by_actor_id=request.created_by_actor_id,
                source_kind=request.source_kind,
                source_ref=request.source_ref,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
                provider_sessions=[],
                member_count=0,
            ),
            info="identity session started",
        )


class _IdentityJoinSessionCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def join_session(
        self,
        request: SessionJoinRequest,
    ) -> SessionJoinReceipt:
        runtime_context = await self._support.session_runtime_context()
        member_id = await runtime_join_session(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_id=request.session_id,
            actor_id=request.actor_id,
            session_actor_config_id=request.session_actor_config_id,
            status=request.status,
            joined_at_unix_ms=request.joined_at_unix_ms,
            left_at_unix_ms=request.left_at_unix_ms,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionJoinReceipt(
            request_id=request.request_id,
            member=SessionMemberSummary(
                session_member_id=member_id,
                session_id=request.session_id,
                actor_id=request.actor_id,
                session_actor_config_id=request.session_actor_config_id,
                status=request.status,
                joined_at_unix_ms=request.joined_at_unix_ms,
                left_at_unix_ms=request.left_at_unix_ms,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
                actor_roles=[],
            ),
            info="identity session actor joined",
        )


class _IdentityRecordSessionMemberActorRoleCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def record_session_member_actor_role(
        self,
        request: SessionMemberActorRoleRecordRequest,
    ) -> SessionMemberActorRoleRecordReceipt:
        runtime_context = await self._support.session_runtime_context()
        edge_id = await runtime_record_session_member_actor_role(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_id=request.session_id,
            session_member_id=request.session_member_id,
            actor_role_id=request.actor_role_id,
            source_kind=request.source_kind,
            status=request.status,
            evidence_json=cast(JsonObject, dict(request.evidence_json)),
        )
        return SessionMemberActorRoleRecordReceipt(
            request_id=request.request_id,
            actor_role=SessionMemberActorRoleSummary(
                session_member_actor_role_id=edge_id,
                session_member_id=request.session_member_id,
                actor_role_id=request.actor_role_id,
                source_kind=request.source_kind,
                status=request.status,
                evidence_json=cast(JsonObject, dict(request.evidence_json)),
            ),
            info="identity session member actor-role evidence recorded",
        )


class _IdentityAttachSessionProviderSessionCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def attach_session_provider_session(
        self,
        request: SessionProviderSessionAttachRequest,
    ) -> SessionProviderSessionAttachReceipt:
        runtime_context = await self._support.session_runtime_context()
        attachment_id = await runtime_attach_session_provider_session(
            runtime_context=runtime_context,
            operation_context=self._support.session_operation_context(),
            session_id=request.session_id,
            provider_session_config_id=request.provider_session_config_id,
            provider_session_key=request.provider_session_key,
            provider_session_ref=request.provider_session_ref,
            provider_object_instance_graph_identity_id=(
                request.provider_object_instance_graph_identity_id
            ),
            provider_class_instance_identity_id=(
                request.provider_class_instance_identity_id
            ),
            provider_object_instance_graph_branch_id=(
                request.provider_object_instance_graph_branch_id
            ),
            status=request.status,
            metadata_json=cast(JsonObject, dict(request.metadata_json)),
        )
        return SessionProviderSessionAttachReceipt(
            request_id=request.request_id,
            provider_session=SessionProviderSessionSummary(
                session_provider_session_id=attachment_id,
                session_id=request.session_id,
                provider_session_config_id=request.provider_session_config_id,
                provider_session_key=request.provider_session_key,
                provider_session_ref=request.provider_session_ref,
                provider_object_instance_graph_identity_id=(
                    request.provider_object_instance_graph_identity_id
                ),
                provider_class_instance_identity_id=(
                    request.provider_class_instance_identity_id
                ),
                provider_object_instance_graph_branch_id=(
                    request.provider_object_instance_graph_branch_id
                ),
                status=request.status,
                metadata_json=cast(JsonObject, dict(request.metadata_json)),
            ),
            info="identity session provider session attached",
        )


class _IdentityListActorSessionsCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def list_actor_sessions(
        self,
        request: ActorSessionsListRequest,
    ) -> ActorSessionsListResult:
        return await self._support.list_actor_sessions_from_ontology_replica(
            request=request,
        )


class _IdentityDescribeSessionCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def describe_session(
        self,
        request: SessionDescribeRequest,
    ) -> SessionDescribeResult:
        return await self._support.describe_session_from_ontology_replica(
            request=request,
        )


class _IdentityListChildSessionsCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def list_child_sessions(
        self,
        request: ChildSessionsListRequest,
    ) -> ChildSessionsListResult:
        return await self._support.list_child_sessions_from_ontology_replica(
            request=request,
        )


class _IdentityListSessionMembersCapabilityHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support

    async def list_session_members(
        self,
        request: SessionMembersListRequest,
    ) -> SessionMembersListResult:
        return await self._support.list_session_members_from_ontology_replica(
            request=request,
        )


class _IdentityApiServiceProtocolHandler:
    def __init__(self, *, support: _IdentityProtocolSupport) -> None:
        self._support = support
        self.attach_session_provider_session = (
            _IdentityAttachSessionProviderSessionCapabilityHandler(support=support)
        )
        self.bind_session_config_actor_config = (
            _IdentityBindSessionConfigActorConfigCapabilityHandler(support=support)
        )
        self.bind_session_provider_config = (
            _IdentityBindSessionProviderConfigCapabilityHandler(support=support)
        )
        self.check_credential_readiness = (
            _IdentityCheckCredentialReadinessCapabilityHandler(support=support)
        )
        self.describe_session = _IdentityDescribeSessionCapabilityHandler(
            support=support
        )
        self.assign_role = _IdentityAssignRoleCapabilityHandler(support=support)
        self.unassign_role = _IdentityUnassignRoleCapabilityHandler(support=support)
        self.resolve_role_assignments = (
            _IdentityResolveRoleAssignmentsCapabilityHandler(support=support)
        )
        self.ensure_actor_subscription = (
            _IdentityEnsureActorSubscriptionCapabilityHandler(support=support)
        )
        self.resolve_actor_subscriptions = (
            _IdentityResolveActorSubscriptionsCapabilityHandler(support=support)
        )
        self.ensure_actor_commit = _IdentityEnsureActorCommitCapabilityHandler(
            support=support
        )
        self.resolve_actor_commits = _IdentityResolveActorCommitsCapabilityHandler(
            support=support
        )
        self.ensure_session_config = _IdentityEnsureSessionConfigCapabilityHandler(
            support=support
        )
        self.join_session = _IdentityJoinSessionCapabilityHandler(support=support)
        self.list_actor_sessions = _IdentityListActorSessionsCapabilityHandler(
            support=support
        )
        self.list_child_sessions = _IdentityListChildSessionsCapabilityHandler(
            support=support
        )
        self.list_session_members = _IdentityListSessionMembersCapabilityHandler(
            support=support
        )
        self.record_session_member_actor_role = (
            _IdentityRecordSessionMemberActorRoleCapabilityHandler(support=support)
        )
        self.signup_via_profile = _IdentitySignupViaProfileCapabilityHandler(
            support=support
        )
        self.setup_credential_profile = (
            _IdentitySetupCredentialProfileCapabilityHandler(support=support)
        )
        self.register_session_provider = (
            _IdentityRegisterSessionProviderCapabilityHandler(support=support)
        )
        self.start_session = _IdentityStartSessionCapabilityHandler(support=support)

    async def _read_identity_from_ontology_replica(
        self,
        *,
        identity_id: UUID,
    ) -> object | None:
        return await self._support.read_identity_from_ontology_replica(
            identity_id=identity_id,
        )


class _AwareIdentityServiceProtocolHandler:
    def __init__(
        self,
        *,
        role_grant_authority_backend: IdentityRoleGrantAuthorityBackend | None = None,
    ) -> None:
        support = _IdentityProtocolSupport(
            role_grant_authority_backend=role_grant_authority_backend,
        )
        self.identity = _IdentityApiServiceProtocolHandler(support=support)


@dataclass(frozen=True)
class _GrantReceiptUpdate:
    binding_update: dict[str, object]
    receipt_update: dict[str, object]


def _convert_model(
    value: BaseModel,
    *,
    model_cls: type[_ModelT],
) -> _ModelT:
    return model_cls.model_validate(value.model_dump(mode="json", exclude_none=False))


def _grant_authority_request_from_assignment(
    *,
    request: RoleAssignmentRequest,
) -> IdentityRoleGrantAuthorityRequest:
    if not request.grant_authority_kind:
        raise PermissionError("identity_role_grant_authority_kind_required")
    if request.grant_authority_id is None:
        raise PermissionError("identity_role_grant_authority_id_required")
    if not request.grant_context_kind:
        raise PermissionError("identity_role_grant_context_kind_required")
    if request.grant_context_id is None:
        raise PermissionError("identity_role_grant_context_id_required")
    return IdentityRoleGrantAuthorityRequest(
        request_id=request.request_id,
        actor_id=request.actor_id,
        role_config_id=request.role_config_id,
        role_config_name=request.role_config_name,
        class_instance_identity_id=request.class_instance_identity_id,
        source_service=request.source_service,
        grant_authority_kind=request.grant_authority_kind,
        grant_authority_id=request.grant_authority_id,
        grant_context_kind=request.grant_context_kind,
        grant_context_id=request.grant_context_id,
        grant_context_ref=request.grant_context_ref,
        grant_evidence=cast(JsonObject, dict(request.grant_evidence)),
    )


def _grant_receipt_update_from_request(
    *,
    request: RoleAssignmentRequest,
    decision: IdentityRoleGrantAuthorityDecision,
) -> _GrantReceiptUpdate:
    grant_evidence = cast(
        JsonObject,
        {
            **dict(request.grant_evidence),
            **dict(decision.evidence),
        },
    )
    update: dict[str, object] = {
        "grant_authority_kind": request.grant_authority_kind,
        "grant_authority_id": request.grant_authority_id,
        "grant_context_kind": request.grant_context_kind,
        "grant_context_id": request.grant_context_id,
        "grant_context_ref": request.grant_context_ref,
        "grant_evidence": grant_evidence,
    }
    return _GrantReceiptUpdate(
        binding_update=update,
        receipt_update=update,
    )


__all__ = [
    "IdentityRoleGrantAuthorityBackend",
    "IdentityRoleGrantAuthorityDecision",
    "IdentityRoleGrantAuthorityRequest",
    "build_aware_identity_service_protocol_handler",
]
