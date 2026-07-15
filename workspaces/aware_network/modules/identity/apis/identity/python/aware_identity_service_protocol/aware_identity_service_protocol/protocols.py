# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

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

API_PACKAGE_NAME: Final[str] = "identity-service-api"
API_FQN_PREFIX: Final[str] = "aware_identity_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_identity_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_identity__assign_role__assign_role(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RoleAssignmentReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = RoleAssignmentRequest.model_validate(request)
    return await typed_handler.identity.assign_role.assign_role(typed_request)


IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF: Final[str] = "identity.assign_role.assign_role"
IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF,
        api_name="identity",
        capability_name="assign_role",
        endpoint_name="assign_role",
        request_type_ref="aware_identity_service_dto.role.RoleAssignmentRequest",
        response_type_ref="aware_identity_service_dto.role.RoleAssignmentReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__assign_role__assign_role,
    )
)


async def invoke_identity__attach_session_provider_session__attach_session_provider_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionProviderSessionAttachReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionProviderSessionAttachRequest.model_validate(request)
    return await typed_handler.identity.attach_session_provider_session.attach_session_provider_session(typed_request)


IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF: Final[str] = (
    "identity.attach_session_provider_session.attach_session_provider_session"
)
IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF,
    api_name="identity",
    capability_name="attach_session_provider_session",
    endpoint_name="attach_session_provider_session",
    request_type_ref="aware_identity_service_dto.session.SessionProviderSessionAttachRequest",
    response_type_ref="aware_identity_service_dto.session.SessionProviderSessionAttachReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__attach_session_provider_session__attach_session_provider_session,
)


async def invoke_identity__bind_session_config_actor_config__bind_session_config_actor_config(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionConfigActorConfigBindReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionConfigActorConfigBindRequest.model_validate(request)
    return await typed_handler.identity.bind_session_config_actor_config.bind_session_config_actor_config(typed_request)


IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.bind_session_config_actor_config.bind_session_config_actor_config"
)
IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF,
    api_name="identity",
    capability_name="bind_session_config_actor_config",
    endpoint_name="bind_session_config_actor_config",
    request_type_ref="aware_identity_service_dto.session.SessionConfigActorConfigBindRequest",
    response_type_ref="aware_identity_service_dto.session.SessionConfigActorConfigBindReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__bind_session_config_actor_config__bind_session_config_actor_config,
)


async def invoke_identity__bind_session_provider_config__bind_session_provider_config(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionProviderConfigBindReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionProviderConfigBindRequest.model_validate(request)
    return await typed_handler.identity.bind_session_provider_config.bind_session_provider_config(typed_request)


IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.bind_session_provider_config.bind_session_provider_config"
)
IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF,
    api_name="identity",
    capability_name="bind_session_provider_config",
    endpoint_name="bind_session_provider_config",
    request_type_ref="aware_identity_service_dto.session.SessionProviderConfigBindRequest",
    response_type_ref="aware_identity_service_dto.session.SessionProviderConfigBindReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__bind_session_provider_config__bind_session_provider_config,
)


async def invoke_identity__check_credential_readiness__check_credential_readiness(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> CredentialReadinessCheckReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = CredentialReadinessCheckRequest.model_validate(request)
    return await typed_handler.identity.check_credential_readiness.check_credential_readiness(typed_request)


IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF: Final[str] = (
    "identity.check_credential_readiness.check_credential_readiness"
)
IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF,
    api_name="identity",
    capability_name="check_credential_readiness",
    endpoint_name="check_credential_readiness",
    request_type_ref="aware_identity_service_dto.credential.CredentialReadinessCheckRequest",
    response_type_ref="aware_identity_service_dto.credential.CredentialReadinessCheckReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__check_credential_readiness__check_credential_readiness,
)


async def invoke_identity__describe_session__describe_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionDescribeResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionDescribeRequest.model_validate(request)
    return await typed_handler.identity.describe_session.describe_session(typed_request)


IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF: Final[str] = "identity.describe_session.describe_session"
IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
        api_name="identity",
        capability_name="describe_session",
        endpoint_name="describe_session",
        request_type_ref="aware_identity_service_dto.session.SessionDescribeRequest",
        response_type_ref="aware_identity_service_dto.session.SessionDescribeResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__describe_session__describe_session,
    )
)


async def invoke_identity__ensure_actor_commit__ensure_actor_commit(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActorCommitEnsureReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ActorCommitEnsureRequest.model_validate(request)
    return await typed_handler.identity.ensure_actor_commit.ensure_actor_commit(typed_request)


IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF: Final[str] = (
    "identity.ensure_actor_commit.ensure_actor_commit"
)
IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF,
        api_name="identity",
        capability_name="ensure_actor_commit",
        endpoint_name="ensure_actor_commit",
        request_type_ref="aware_identity_service_dto.actor.ActorCommitEnsureRequest",
        response_type_ref="aware_identity_service_dto.actor.ActorCommitEnsureReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__ensure_actor_commit__ensure_actor_commit,
    )
)


async def invoke_identity__ensure_actor_subscription__ensure_actor_subscription(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActorSubscriptionEnsureReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ActorSubscriptionEnsureRequest.model_validate(request)
    return await typed_handler.identity.ensure_actor_subscription.ensure_actor_subscription(typed_request)


IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF: Final[str] = (
    "identity.ensure_actor_subscription.ensure_actor_subscription"
)
IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF,
    api_name="identity",
    capability_name="ensure_actor_subscription",
    endpoint_name="ensure_actor_subscription",
    request_type_ref="aware_identity_service_dto.actor.ActorSubscriptionEnsureRequest",
    response_type_ref="aware_identity_service_dto.actor.ActorSubscriptionEnsureReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__ensure_actor_subscription__ensure_actor_subscription,
)


async def invoke_identity__ensure_session_config__ensure_session_config(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionConfigEnsureReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionConfigEnsureRequest.model_validate(request)
    return await typed_handler.identity.ensure_session_config.ensure_session_config(typed_request)


IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.ensure_session_config.ensure_session_config"
)
IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF,
        api_name="identity",
        capability_name="ensure_session_config",
        endpoint_name="ensure_session_config",
        request_type_ref="aware_identity_service_dto.session.SessionConfigEnsureRequest",
        response_type_ref="aware_identity_service_dto.session.SessionConfigEnsureReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__ensure_session_config__ensure_session_config,
    )
)


async def invoke_identity__join_session__join_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionJoinReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionJoinRequest.model_validate(request)
    return await typed_handler.identity.join_session.join_session(typed_request)


IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF: Final[str] = "identity.join_session.join_session"
IDENTITY__JOIN_SESSION__JOIN_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF,
        api_name="identity",
        capability_name="join_session",
        endpoint_name="join_session",
        request_type_ref="aware_identity_service_dto.session.SessionJoinRequest",
        response_type_ref="aware_identity_service_dto.session.SessionJoinReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__join_session__join_session,
    )
)


async def invoke_identity__list_actor_sessions__list_actor_sessions(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActorSessionsListResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ActorSessionsListRequest.model_validate(request)
    return await typed_handler.identity.list_actor_sessions.list_actor_sessions(typed_request)


IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF: Final[str] = (
    "identity.list_actor_sessions.list_actor_sessions"
)
IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF,
        api_name="identity",
        capability_name="list_actor_sessions",
        endpoint_name="list_actor_sessions",
        request_type_ref="aware_identity_service_dto.session.ActorSessionsListRequest",
        response_type_ref="aware_identity_service_dto.session.ActorSessionsListResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__list_actor_sessions__list_actor_sessions,
    )
)


async def invoke_identity__list_child_sessions__list_child_sessions(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ChildSessionsListResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ChildSessionsListRequest.model_validate(request)
    return await typed_handler.identity.list_child_sessions.list_child_sessions(typed_request)


IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF: Final[str] = (
    "identity.list_child_sessions.list_child_sessions"
)
IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF,
        api_name="identity",
        capability_name="list_child_sessions",
        endpoint_name="list_child_sessions",
        request_type_ref="aware_identity_service_dto.session.ChildSessionsListRequest",
        response_type_ref="aware_identity_service_dto.session.ChildSessionsListResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__list_child_sessions__list_child_sessions,
    )
)


async def invoke_identity__list_session_members__list_session_members(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionMembersListResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionMembersListRequest.model_validate(request)
    return await typed_handler.identity.list_session_members.list_session_members(typed_request)


IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF: Final[str] = (
    "identity.list_session_members.list_session_members"
)
IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF,
        api_name="identity",
        capability_name="list_session_members",
        endpoint_name="list_session_members",
        request_type_ref="aware_identity_service_dto.session.SessionMembersListRequest",
        response_type_ref="aware_identity_service_dto.session.SessionMembersListResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__list_session_members__list_session_members,
    )
)


async def invoke_identity__record_session_member_actor_role__record_session_member_actor_role(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionMemberActorRoleRecordReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionMemberActorRoleRecordRequest.model_validate(request)
    return await typed_handler.identity.record_session_member_actor_role.record_session_member_actor_role(typed_request)


IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF: Final[str] = (
    "identity.record_session_member_actor_role.record_session_member_actor_role"
)
IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF,
    api_name="identity",
    capability_name="record_session_member_actor_role",
    endpoint_name="record_session_member_actor_role",
    request_type_ref="aware_identity_service_dto.session.SessionMemberActorRoleRecordRequest",
    response_type_ref="aware_identity_service_dto.session.SessionMemberActorRoleRecordReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__record_session_member_actor_role__record_session_member_actor_role,
)


async def invoke_identity__register_session_provider__register_session_provider(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionProviderRegisterReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionProviderRegisterRequest.model_validate(request)
    return await typed_handler.identity.register_session_provider.register_session_provider(typed_request)


IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF: Final[str] = (
    "identity.register_session_provider.register_session_provider"
)
IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF,
    api_name="identity",
    capability_name="register_session_provider",
    endpoint_name="register_session_provider",
    request_type_ref="aware_identity_service_dto.session.SessionProviderRegisterRequest",
    response_type_ref="aware_identity_service_dto.session.SessionProviderRegisterReceipt",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__register_session_provider__register_session_provider,
)


async def invoke_identity__resolve_actor_commits__resolve_actor_commits(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActorCommitResolveResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ActorCommitResolveRequest.model_validate(request)
    return await typed_handler.identity.resolve_actor_commits.resolve_actor_commits(typed_request)


IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_actor_commits.resolve_actor_commits"
)
IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF,
        api_name="identity",
        capability_name="resolve_actor_commits",
        endpoint_name="resolve_actor_commits",
        request_type_ref="aware_identity_service_dto.actor.ActorCommitResolveRequest",
        response_type_ref="aware_identity_service_dto.actor.ActorCommitResolveResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__resolve_actor_commits__resolve_actor_commits,
    )
)


async def invoke_identity__resolve_actor_subscriptions__resolve_actor_subscriptions(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActorSubscriptionResolveResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = ActorSubscriptionResolveRequest.model_validate(request)
    return await typed_handler.identity.resolve_actor_subscriptions.resolve_actor_subscriptions(typed_request)


IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_actor_subscriptions.resolve_actor_subscriptions"
)
IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF,
    api_name="identity",
    capability_name="resolve_actor_subscriptions",
    endpoint_name="resolve_actor_subscriptions",
    request_type_ref="aware_identity_service_dto.actor.ActorSubscriptionResolveRequest",
    response_type_ref="aware_identity_service_dto.actor.ActorSubscriptionResolveResult",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_identity__resolve_actor_subscriptions__resolve_actor_subscriptions,
)


async def invoke_identity__resolve_role_assignments__resolve_role_assignments(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RoleAssignmentResolveResult:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = RoleAssignmentResolveRequest.model_validate(request)
    return await typed_handler.identity.resolve_role_assignments.resolve_role_assignments(typed_request)


IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_role_assignments.resolve_role_assignments"
)
IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF,
        api_name="identity",
        capability_name="resolve_role_assignments",
        endpoint_name="resolve_role_assignments",
        request_type_ref="aware_identity_service_dto.role.RoleAssignmentResolveRequest",
        response_type_ref="aware_identity_service_dto.role.RoleAssignmentResolveResult",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__resolve_role_assignments__resolve_role_assignments,
    )
)


async def invoke_identity__setup_credential_profile__setup_credential_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> CredentialProfileSetupReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = CredentialProfileSetupRequest.model_validate(request)
    return await typed_handler.identity.setup_credential_profile.setup_credential_profile(typed_request)


IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF: Final[str] = (
    "identity.setup_credential_profile.setup_credential_profile"
)
IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF,
        api_name="identity",
        capability_name="setup_credential_profile",
        endpoint_name="setup_credential_profile",
        request_type_ref="aware_identity_service_dto.credential.CredentialProfileSetupRequest",
        response_type_ref="aware_identity_service_dto.credential.CredentialProfileSetupReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__setup_credential_profile__setup_credential_profile,
    )
)


async def invoke_identity__signup_via_profile__signup_via_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> IdentityAdmissionReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = IdentitySignupViaProfileRequest.model_validate(request)
    return await typed_handler.identity.signup_via_profile.signup_via_profile(typed_request)


IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF: Final[str] = (
    "identity.signup_via_profile.signup_via_profile"
)
IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
        api_name="identity",
        capability_name="signup_via_profile",
        endpoint_name="signup_via_profile",
        request_type_ref="aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
        response_type_ref="aware_identity_service_dto.identity.IdentityAdmissionReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__signup_via_profile__signup_via_profile,
    )
)


async def invoke_identity__start_session__start_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SessionStartReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = SessionStartRequest.model_validate(request)
    return await typed_handler.identity.start_session.start_session(typed_request)


IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF: Final[str] = "identity.start_session.start_session"
IDENTITY__START_SESSION__START_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF,
        api_name="identity",
        capability_name="start_session",
        endpoint_name="start_session",
        request_type_ref="aware_identity_service_dto.session.SessionStartRequest",
        response_type_ref="aware_identity_service_dto.session.SessionStartReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__start_session__start_session,
    )
)


async def invoke_identity__unassign_role__unassign_role(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RoleUnassignmentReceipt:
    typed_handler = cast(AwareIdentityServiceProtocol, handler)
    typed_request = RoleUnassignmentRequest.model_validate(request)
    return await typed_handler.identity.unassign_role.unassign_role(typed_request)


IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF: Final[str] = "identity.unassign_role.unassign_role"
IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF,
        api_name="identity",
        capability_name="unassign_role",
        endpoint_name="unassign_role",
        request_type_ref="aware_identity_service_dto.role.RoleUnassignmentRequest",
        response_type_ref="aware_identity_service_dto.role.RoleUnassignmentReceipt",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_identity__unassign_role__unassign_role,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF: IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_PROTOCOL_BINDING,
    IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF: IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_PROTOCOL_BINDING,
    IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF: IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_PROTOCOL_BINDING,
    IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF: IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_PROTOCOL_BINDING,
    IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF: IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_PROTOCOL_BINDING,
    IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF: IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING,
    IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF: IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_PROTOCOL_BINDING,
    IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF: IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_PROTOCOL_BINDING,
    IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF: IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_PROTOCOL_BINDING,
    IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF: IDENTITY__JOIN_SESSION__JOIN_SESSION_PROTOCOL_BINDING,
    IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF: IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_PROTOCOL_BINDING,
    IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF: IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_PROTOCOL_BINDING,
    IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF: IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_PROTOCOL_BINDING,
    IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF: IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_PROTOCOL_BINDING,
    IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF: IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_PROTOCOL_BINDING,
    IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF: IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_PROTOCOL_BINDING,
    IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF: IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_PROTOCOL_BINDING,
    IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF: IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_PROTOCOL_BINDING,
    IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF: IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_PROTOCOL_BINDING,
    IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF: IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_PROTOCOL_BINDING,
    IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF: IDENTITY__START_SESSION__START_SESSION_PROTOCOL_BINDING,
    IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF: IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_PROTOCOL_BINDING,
}


class IdentityAssignRoleCapabilityServiceProtocol(Protocol):

    async def assign_role(self, request: RoleAssignmentRequest) -> RoleAssignmentReceipt: ...


class IdentityAttachSessionProviderSessionCapabilityServiceProtocol(Protocol):

    async def attach_session_provider_session(
        self, request: SessionProviderSessionAttachRequest
    ) -> SessionProviderSessionAttachReceipt: ...


class IdentityBindSessionConfigActorConfigCapabilityServiceProtocol(Protocol):

    async def bind_session_config_actor_config(
        self, request: SessionConfigActorConfigBindRequest
    ) -> SessionConfigActorConfigBindReceipt: ...


class IdentityBindSessionProviderConfigCapabilityServiceProtocol(Protocol):

    async def bind_session_provider_config(
        self, request: SessionProviderConfigBindRequest
    ) -> SessionProviderConfigBindReceipt: ...


class IdentityCheckCredentialReadinessCapabilityServiceProtocol(Protocol):

    async def check_credential_readiness(
        self, request: CredentialReadinessCheckRequest
    ) -> CredentialReadinessCheckReceipt: ...


class IdentityDescribeSessionCapabilityServiceProtocol(Protocol):

    async def describe_session(self, request: SessionDescribeRequest) -> SessionDescribeResult: ...


class IdentityEnsureActorCommitCapabilityServiceProtocol(Protocol):

    async def ensure_actor_commit(self, request: ActorCommitEnsureRequest) -> ActorCommitEnsureReceipt: ...


class IdentityEnsureActorSubscriptionCapabilityServiceProtocol(Protocol):

    async def ensure_actor_subscription(
        self, request: ActorSubscriptionEnsureRequest
    ) -> ActorSubscriptionEnsureReceipt: ...


class IdentityEnsureSessionConfigCapabilityServiceProtocol(Protocol):

    async def ensure_session_config(self, request: SessionConfigEnsureRequest) -> SessionConfigEnsureReceipt: ...


class IdentityJoinSessionCapabilityServiceProtocol(Protocol):

    async def join_session(self, request: SessionJoinRequest) -> SessionJoinReceipt: ...


class IdentityListActorSessionsCapabilityServiceProtocol(Protocol):

    async def list_actor_sessions(self, request: ActorSessionsListRequest) -> ActorSessionsListResult: ...


class IdentityListChildSessionsCapabilityServiceProtocol(Protocol):

    async def list_child_sessions(self, request: ChildSessionsListRequest) -> ChildSessionsListResult: ...


class IdentityListSessionMembersCapabilityServiceProtocol(Protocol):

    async def list_session_members(self, request: SessionMembersListRequest) -> SessionMembersListResult: ...


class IdentityRecordSessionMemberActorRoleCapabilityServiceProtocol(Protocol):

    async def record_session_member_actor_role(
        self, request: SessionMemberActorRoleRecordRequest
    ) -> SessionMemberActorRoleRecordReceipt: ...


class IdentityRegisterSessionProviderCapabilityServiceProtocol(Protocol):

    async def register_session_provider(
        self, request: SessionProviderRegisterRequest
    ) -> SessionProviderRegisterReceipt: ...


class IdentityResolveActorCommitsCapabilityServiceProtocol(Protocol):

    async def resolve_actor_commits(self, request: ActorCommitResolveRequest) -> ActorCommitResolveResult: ...


class IdentityResolveActorSubscriptionsCapabilityServiceProtocol(Protocol):

    async def resolve_actor_subscriptions(
        self, request: ActorSubscriptionResolveRequest
    ) -> ActorSubscriptionResolveResult: ...


class IdentityResolveRoleAssignmentsCapabilityServiceProtocol(Protocol):

    async def resolve_role_assignments(self, request: RoleAssignmentResolveRequest) -> RoleAssignmentResolveResult: ...


class IdentitySetupCredentialProfileCapabilityServiceProtocol(Protocol):

    async def setup_credential_profile(
        self, request: CredentialProfileSetupRequest
    ) -> CredentialProfileSetupReceipt: ...


class IdentitySignupViaProfileCapabilityServiceProtocol(Protocol):

    async def signup_via_profile(self, request: IdentitySignupViaProfileRequest) -> IdentityAdmissionReceipt: ...


class IdentityStartSessionCapabilityServiceProtocol(Protocol):

    async def start_session(self, request: SessionStartRequest) -> SessionStartReceipt: ...


class IdentityUnassignRoleCapabilityServiceProtocol(Protocol):

    async def unassign_role(self, request: RoleUnassignmentRequest) -> RoleUnassignmentReceipt: ...


class IdentityApiServiceProtocol(Protocol):
    assign_role: IdentityAssignRoleCapabilityServiceProtocol
    attach_session_provider_session: IdentityAttachSessionProviderSessionCapabilityServiceProtocol
    bind_session_config_actor_config: IdentityBindSessionConfigActorConfigCapabilityServiceProtocol
    bind_session_provider_config: IdentityBindSessionProviderConfigCapabilityServiceProtocol
    check_credential_readiness: IdentityCheckCredentialReadinessCapabilityServiceProtocol
    describe_session: IdentityDescribeSessionCapabilityServiceProtocol
    ensure_actor_commit: IdentityEnsureActorCommitCapabilityServiceProtocol
    ensure_actor_subscription: IdentityEnsureActorSubscriptionCapabilityServiceProtocol
    ensure_session_config: IdentityEnsureSessionConfigCapabilityServiceProtocol
    join_session: IdentityJoinSessionCapabilityServiceProtocol
    list_actor_sessions: IdentityListActorSessionsCapabilityServiceProtocol
    list_child_sessions: IdentityListChildSessionsCapabilityServiceProtocol
    list_session_members: IdentityListSessionMembersCapabilityServiceProtocol
    record_session_member_actor_role: IdentityRecordSessionMemberActorRoleCapabilityServiceProtocol
    register_session_provider: IdentityRegisterSessionProviderCapabilityServiceProtocol
    resolve_actor_commits: IdentityResolveActorCommitsCapabilityServiceProtocol
    resolve_actor_subscriptions: IdentityResolveActorSubscriptionsCapabilityServiceProtocol
    resolve_role_assignments: IdentityResolveRoleAssignmentsCapabilityServiceProtocol
    setup_credential_profile: IdentitySetupCredentialProfileCapabilityServiceProtocol
    signup_via_profile: IdentitySignupViaProfileCapabilityServiceProtocol
    start_session: IdentityStartSessionCapabilityServiceProtocol
    unassign_role: IdentityUnassignRoleCapabilityServiceProtocol


class AwareIdentityServiceProtocol(Protocol):
    identity: IdentityApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:735d62c70d1979f3f66b0a8a80f5582eee20b1164a5519aa4324ea32ab215b93",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 94,'
    '  "sections": ['
    "    {"
    '      "line_count": 22,'
    '      "rendered_text_digest": "sha256:2931715b775d5a6b028751c52c714fad1ba9dd7a73afc62dacdcea3d2fdbf412",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.assign_role.assign_role",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.attach_session_provider_session.attach_session_provider_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.bind_session_config_actor_config.bind_session_config_actor_config",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.bind_session_provider_config.bind_session_provider_config",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.check_credential_readiness.check_credential_readiness",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.describe_session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.ensure_actor_commit.ensure_actor_commit",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.ensure_actor_subscription.ensure_actor_subscription",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.ensure_session_config.ensure_session_config",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.join_session.join_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.list_actor_sessions.list_actor_sessions",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.list_child_sessions.list_child_sessions",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.list_session_members.list_session_members",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.record_session_member_actor_role.record_session_member_actor_role",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.register_session_provider.register_session_provider",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.resolve_actor_commits.resolve_actor_commits",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.resolve_actor_subscriptions.resolve_actor_subscriptions",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.resolve_role_assignments.resolve_role_assignments",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.setup_credential_profile.setup_credential_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.signup_via_profile.signup_via_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.start_session.start_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:identity.unassign_role.unassign_role",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c9e122ef290e69f02bd1a662932fb6a46f131fd57458857052104e48d12e291e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.assign_role.assign_role",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:70bbfa4b1a542c66ec84f63d92eddab8c99bc336886e023dd93a0a44e7458638",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.assign_role.assign_role",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e9b641319d30c6f30dcbba9a2ec657a22440f0819007af75de9a949012431054",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.attach_session_provider_session.attach_session_provider_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d377c8ba2dd2e8818b464012de0ee22b76c2c4b911b3184325569aa646dffdb6",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.attach_session_provider_session.attach_session_provider_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e5bb8b3e0362924ae99f1cc7e7beaa908d950cc388ab785861c025907a8b6378",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.bind_session_config_actor_config.bind_session_config_actor_config",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8b11fd9a71f2cfe001564ad78b46b7e601ee34013ac55037881a7bee1a745673",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.bind_session_config_actor_config.bind_session_config_actor_config",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:bb0048ce6b61b53f13221ae59bff15b3059efbbd60b81c495550768d6b1a6a4c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.bind_session_provider_config.bind_session_provider_config",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d1d6c64d5e9c12807e15840873d98d3884032b588299a08a4a0095eda8f540aa",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.bind_session_provider_config.bind_session_provider_config",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e290ce654a22f15a7d0a3f91e86078668a4605ee77ecf3497e3faf3db38deb03",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.check_credential_readiness.check_credential_readiness",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e7e47d8abde1f8f0af79d90d4b2bd81454e3996c5590bd638724368afb9eda1b",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.check_credential_readiness.check_credential_readiness",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d65b567d233e94b8c2813bd99cb2b4db7a97943035b500924cc5fcfb31db50f8",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.describe_session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d6f4c3e48b4473fe32620d5fcd229f3056ecb6e5bd382e1510457cee16e32be5",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.describe_session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e49d2711f3d4edeec8622cf3df320ff7f269740854d48d3bf3b871462c069a33",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.ensure_actor_commit.ensure_actor_commit",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:140d0fa95565d9db67b0aaf2de04545e2c3e2225f93e2312d65a600bb626c196",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.ensure_actor_commit.ensure_actor_commit",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:96f5fbb7d0b8c76076faff92d3fba65d8bb797109255f6151d20c39d07a40c76",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.ensure_actor_subscription.ensure_actor_subscription",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:47e20601cbc2dcfe4b3a15dbf3aec877fef1c90084954a5ad7f1cc700f0aa6ef",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.ensure_actor_subscription.ensure_actor_subscription",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dec653c91b68357120f2beaf2642d2e2db41b3e8f8c8c97e485d1f680b77bfd4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.ensure_session_config.ensure_session_config",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e1a4cff93b0d645e1fc418ecc4ccb51fcee09ec7ec3730e6cad7cada92487134",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.ensure_session_config.ensure_session_config",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:36c75c3a67e5efc2d4e4e1d8c033efcc17cb0630e96cc492b1916d546933edf9",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.join_session.join_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c4d869c9e04b3201e42ce7c7a366afde2ae70c9b00e059eeaef0614d8d5739db",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.join_session.join_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ce73dc0581995a735af4a12d1d725eb7e295bd58923c5bc88027995b4c3b64ae",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.list_actor_sessions.list_actor_sessions",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:395fc151c44c7ce66565966d2361cc91cfe26583fe5629ed931e91b2cca6678c",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.list_actor_sessions.list_actor_sessions",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a3254aefb4f03ad84ae3244995cc7e3086f8f7434e01e45c26914c5a60c8e447",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.list_child_sessions.list_child_sessions",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:9f3eee98ef9172068f25c599dcb541fe9be49ef300013eeb7a9767b931d21ccb",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.list_child_sessions.list_child_sessions",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:468a9dbc1a96bf0202efc3fb1c86c819dbbd009b6f3276683cf976cd7bee8526",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.list_session_members.list_session_members",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c9e1fc0d0f2a9f624302fd8b0c704a2d070b307fb7d69cc0d9ed515e278c358c",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.list_session_members.list_session_members",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:26bffd91772af37ca7505f1a6169d1def0ab577546a88c3addb9be4b9b19822b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.record_session_member_actor_role.record_session_member_actor_role",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:74569428ab20de3ef4270d5648598b5fbbbb8dcef6f7526f837f037f13d93f94",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.record_session_member_actor_role.record_session_member_actor_role",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:8b6f6088e6fc32d7e3a281a25279a124b7310786285125f997ed21bc9c2ca7a7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.register_session_provider.register_session_provider",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b11a6c923971e208b2ce31dc2cbb4508c1948d11cd4bcea2ca34edb502d5495e",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.register_session_provider.register_session_provider",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:bd3f5476ec89d35bab05ba208aa6e9f0c911e41de63d3be67aae032603c1cc8a",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.resolve_actor_commits.resolve_actor_commits",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:13339aad5f578724a4a316310a98eedbc16ea3ec56ea43fff4365d69d244a675",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.resolve_actor_commits.resolve_actor_commits",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d54f5d6888f87894b2a54c4495bbef0cc6f534635ed9f57ca864ceb918089604",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.resolve_actor_subscriptions.resolve_actor_subscriptions",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:80ecca48f8a7bb4eb4447b5def9acd7f51c8fab6c5029ba755ecdb3ab85cc68b",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.resolve_actor_subscriptions.resolve_actor_subscriptions",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2d5d4ff8a7d440864ec8cdf4e5f2953c4b05318496f1b6311959982908c664e6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.resolve_role_assignments.resolve_role_assignments",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2dc0df17e4296a99c1b3c97e3257a884bf94e2adb17072801397c7a9f4733689",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.resolve_role_assignments.resolve_role_assignments",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:42fc077a19132fd795410b45f4ec58dd9ca0f961496182c26791513e5f3ea33b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.setup_credential_profile.setup_credential_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:4a71be8d33bc52db0e18aa55907b2e9264899bdad1d7330f8b8aa98a9b78febd",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.setup_credential_profile.setup_credential_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:685c6b32b086546ebb64aabfe172321d97393735cb6aaf1fa9d65231824c90bb",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.signup_via_profile.signup_via_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:fbd96b5b4dcc177e7e41cede84722414a27055c2e4539915b9d5b0d5c67352c2",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.signup_via_profile.signup_via_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:76bdebfa69eafe254a6bf565d5dae0a7181796743817c4a9609b91c460a1569f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.start_session.start_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e9f427408b33fcb4c754de24ddfd0dd5680b7e0f94cf58ce03012a3b72c1d0c2",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.start_session.start_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:478c123a57b472a9cbd29f57cab5fa7935cea0833ea55663e172c500d12630a4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:identity.unassign_role.unassign_role",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2c304845013c0ced3a52ac702c676310663a638fe7036632928e810b1c81f1cb",'
    '      "section_key": "api.service_protocol.endpoint_binding:identity.unassign_role.unassign_role",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 25,'
    '      "rendered_text_digest": "sha256:38b2c7de6e0fffd0c959e71945aae33f16fa69a9f4ea3d1028ec246164df4215",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d78c9fad490147a086f0566fdb951463f0b84dca04cea64d8fa9f5a83f3dc5a4",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.assign_role",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 69'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c42878bfe73ce17628f4c140d58027a51938863abc24a8e206929a9a657917a6",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.attach_session_provider_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 70'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d92eb602ab03a122a914867da9580db4e08b24b097247c9ccf4f2f094aaeae81",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.bind_session_config_actor_config",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 71'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6b85568533ce3f90d44bc153634101cbac446076e8464d355bbc15215b5a91f7",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.bind_session_provider_config",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 72'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:0eff4d7fff4453cb2c0bd8e6a826b8c6a2466124fbfe30c5420a9ea4180198d9",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.check_credential_readiness",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 73'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e632eeb29138f100e2ec888a0c95c0da96e52935c0fb85d3d938e8c19e0f7489",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.describe_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 74'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:7495dd937fec1bea8cce62d980e424b43706f7e80179f44d54e9baf8ba971ac8",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.ensure_actor_commit",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 75'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:02ea4bb485965ef46d0beb61c64b592d1cecb0e4890cf9daa797367f8094703c",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.ensure_actor_subscription",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 76'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d5b219a17af14dfa2c1686d327aa07a2b7b9ba5babcc7348e3b0ff9e4f885d3d",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.ensure_session_config",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 77'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2b51937fc4911f90d56332d3673e51d8323957ee7adf6c4896280bde1bcee9a4",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.join_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 78'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:0c5647cbd573b957797a7e6fc6b0941a20448fabb677f5ba474325c3d7a0e7f1",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.list_actor_sessions",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 79'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c6eedd91410362cbab1d1b6542c6c512a12bb22b9fac29e80b25c7625d3970fe",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.list_child_sessions",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 80'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:0778c546c4b0d6837a71c4917cbd3c3215d2653fc0a1a831f0b8d91d1586bc6f",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.list_session_members",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 81'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c3ff6a097910c0bebfc06f6fdaa6c456420c9be78d60dd75289712e34c30481e",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.record_session_member_actor_role",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 82'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:7d9689c2a5ff44fe1c66de95a3fe70130d4af2e8e59fc81a38530996f52bc90f",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.register_session_provider",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 83'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:98cff2940bf007316dbcb41fac2f477b730671b0fe9d51d6992e6461c10b9151",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.resolve_actor_commits",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 84'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:dab8b9661e3eee01be6c6d6b5a93479c552ec24520899b1c02b22a6a8f20ebc6",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.resolve_actor_subscriptions",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 85'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6571f0da62f9eea2492144d6f1bf6ed83e2bf020a2008dec29c1cf53a8c4e8bb",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.resolve_role_assignments",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 86'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:9b833f383fe0f27c18ff3588915dd6dc2a91f5c0b2b4de4f14219275b95527a6",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.setup_credential_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 87'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:4c04069fde1453863b76378b8f4caaf39db08167dad17fbc14ec61978f73a019",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.signup_via_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 88'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:de58ad52432518c8962972b332de07aae47e6ac1402eb9b1f67f319890b26e28",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.start_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 89'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:3ceab9c2d2b8c6d84e06bc015622b16af2497bee3485fdf500e2b8ce8b947b14",'
    '      "section_key": "api.service_protocol.capability_protocol:identity.unassign_role",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 90'
    "    },"
    "    {"
    '      "line_count": 24,'
    '      "rendered_text_digest": "sha256:a1302ef654bc88b58a82c89c89557a31b0e3d71c31ec103788882b8ff32bccc4",'
    '      "section_key": "api.service_protocol.api_protocol:identity",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 91'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:a3d0352b99ebc3c30ccadd7207f3825c5e3a415a013e2f27c08fd1e3f7ee9aee",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 92'
    "    },"
    "    {"
    '      "line_count": 104,'
    '      "rendered_text_digest": "sha256:3ac25b6a3e85503d7c18c06768cf22c925dfa2a054fdc7085d24f3d8af97a46f",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 93'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareIdentityServiceProtocol",
    "IdentityApiServiceProtocol",
    "IdentityAssignRoleCapabilityServiceProtocol",
    "IdentityAttachSessionProviderSessionCapabilityServiceProtocol",
    "IdentityBindSessionConfigActorConfigCapabilityServiceProtocol",
    "IdentityBindSessionProviderConfigCapabilityServiceProtocol",
    "IdentityCheckCredentialReadinessCapabilityServiceProtocol",
    "IdentityDescribeSessionCapabilityServiceProtocol",
    "IdentityEnsureActorCommitCapabilityServiceProtocol",
    "IdentityEnsureActorSubscriptionCapabilityServiceProtocol",
    "IdentityEnsureSessionConfigCapabilityServiceProtocol",
    "IdentityJoinSessionCapabilityServiceProtocol",
    "IdentityListActorSessionsCapabilityServiceProtocol",
    "IdentityListChildSessionsCapabilityServiceProtocol",
    "IdentityListSessionMembersCapabilityServiceProtocol",
    "IdentityRecordSessionMemberActorRoleCapabilityServiceProtocol",
    "IdentityRegisterSessionProviderCapabilityServiceProtocol",
    "IdentityResolveActorCommitsCapabilityServiceProtocol",
    "IdentityResolveActorSubscriptionsCapabilityServiceProtocol",
    "IdentityResolveRoleAssignmentsCapabilityServiceProtocol",
    "IdentitySetupCredentialProfileCapabilityServiceProtocol",
    "IdentitySignupViaProfileCapabilityServiceProtocol",
    "IdentityStartSessionCapabilityServiceProtocol",
    "IdentityUnassignRoleCapabilityServiceProtocol",
    "IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF",
    "IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_PROTOCOL_BINDING",
    "invoke_identity__assign_role__assign_role",
    "IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF",
    "IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_PROTOCOL_BINDING",
    "invoke_identity__attach_session_provider_session__attach_session_provider_session",
    "IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF",
    "IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_PROTOCOL_BINDING",
    "invoke_identity__bind_session_config_actor_config__bind_session_config_actor_config",
    "IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF",
    "IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_PROTOCOL_BINDING",
    "invoke_identity__bind_session_provider_config__bind_session_provider_config",
    "IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF",
    "IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_PROTOCOL_BINDING",
    "invoke_identity__check_credential_readiness__check_credential_readiness",
    "IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF",
    "IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING",
    "invoke_identity__describe_session__describe_session",
    "IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF",
    "IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_PROTOCOL_BINDING",
    "invoke_identity__ensure_actor_commit__ensure_actor_commit",
    "IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF",
    "IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_PROTOCOL_BINDING",
    "invoke_identity__ensure_actor_subscription__ensure_actor_subscription",
    "IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF",
    "IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_PROTOCOL_BINDING",
    "invoke_identity__ensure_session_config__ensure_session_config",
    "IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF",
    "IDENTITY__JOIN_SESSION__JOIN_SESSION_PROTOCOL_BINDING",
    "invoke_identity__join_session__join_session",
    "IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF",
    "IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_PROTOCOL_BINDING",
    "invoke_identity__list_actor_sessions__list_actor_sessions",
    "IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF",
    "IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_PROTOCOL_BINDING",
    "invoke_identity__list_child_sessions__list_child_sessions",
    "IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF",
    "IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_PROTOCOL_BINDING",
    "invoke_identity__list_session_members__list_session_members",
    "IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF",
    "IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_PROTOCOL_BINDING",
    "invoke_identity__record_session_member_actor_role__record_session_member_actor_role",
    "IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF",
    "IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_PROTOCOL_BINDING",
    "invoke_identity__register_session_provider__register_session_provider",
    "IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_PROTOCOL_BINDING",
    "invoke_identity__resolve_actor_commits__resolve_actor_commits",
    "IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_PROTOCOL_BINDING",
    "invoke_identity__resolve_actor_subscriptions__resolve_actor_subscriptions",
    "IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_PROTOCOL_BINDING",
    "invoke_identity__resolve_role_assignments__resolve_role_assignments",
    "IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF",
    "IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_PROTOCOL_BINDING",
    "invoke_identity__setup_credential_profile__setup_credential_profile",
    "IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF",
    "IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_PROTOCOL_BINDING",
    "invoke_identity__signup_via_profile__signup_via_profile",
    "IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF",
    "IDENTITY__START_SESSION__START_SESSION_PROTOCOL_BINDING",
    "invoke_identity__start_session__start_session",
    "IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF",
    "IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_PROTOCOL_BINDING",
    "invoke_identity__unassign_role__unassign_role",
]
