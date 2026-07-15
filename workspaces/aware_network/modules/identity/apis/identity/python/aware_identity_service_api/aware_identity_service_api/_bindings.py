# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "identity-service-api"
API_FQN_PREFIX: Final[str] = "aware_identity_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Create or reuse one canonical "
                                "actor-role binding over the "
                                "class-instance-aware\n"
                                "            Identity role rail.",
                                "discriminant": "identity.assign_role.assign_role",
                                "name": "assign_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "assign_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Attach one concrete provider "
                                "session/capability to a shared "
                                "Identity Session.",
                                "discriminant": "identity.attach_session_provider_session.attach_session_provider_session",
                                "name": "attach_session_provider_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderSessionAttachRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderSessionAttachReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "attach_session_provider_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Bind one ActorConfig as eligible "
                                "session participation policy without\n"
                                "            admitting an actor or "
                                "granting roles.",
                                "discriminant": "identity.bind_session_config_actor_config.bind_session_config_actor_config",
                                "name": "bind_session_config_actor_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigActorConfigBindRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigActorConfigBindReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "bind_session_config_actor_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Bind one provider capability to an "
                                "Identity SessionConfig without "
                                "creating a\n"
                                "            concrete provider session.",
                                "discriminant": "identity.bind_session_provider_config.bind_session_provider_config",
                                "name": "bind_session_provider_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderConfigBindRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderConfigBindReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "bind_session_provider_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Check resolver availability for one "
                                "Identity credential profile and record "
                                "a\n"
                                "            readiness receipt without "
                                "carrying raw secret values.",
                                "discriminant": "identity.check_credential_readiness.check_credential_readiness",
                                "name": "check_credential_readiness",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialReadinessCheckRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialReadinessCheckReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "check_credential_readiness",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one Identity Session summary by "
                                "stable id without resolving\n"
                                "            domain-specific provider "
                                "state.",
                                "discriminant": "identity.describe_session.describe_session",
                                "name": "describe_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionDescribeRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionDescribeResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "describe_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create or reuse one Identity-owned "
                                "ActorCommit personal-history record "
                                "from\n"
                                "            an Environment lane commit "
                                "fanout receipt.",
                                "discriminant": "identity.ensure_actor_commit.ensure_actor_commit",
                                "name": "ensure_actor_commit",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_actor_commit",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create or reuse one canonical "
                                "actor-subscription binding for an "
                                "actor and a\n"
                                "            Reactivity-owned "
                                "event-condition scope. ActorRole "
                                "remains detached at this\n"
                                "            boundary; later ACL "
                                "eligibility can compose role checks "
                                "without making\n"
                                "            operation capability equal "
                                "event willingness.",
                                "discriminant": "identity.ensure_actor_subscription.ensure_actor_subscription",
                                "name": "ensure_actor_subscription",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_actor_subscription",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create or reuse one Identity-owned "
                                "generic session participation policy.",
                                "discriminant": "identity.ensure_session_config.ensure_session_config",
                                "name": "ensure_session_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_session_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Join one Actor to an Identity Session "
                                "under an explicit "
                                "SessionConfigActorConfig.",
                                "discriminant": "identity.join_session.join_session",
                                "name": "join_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionJoinRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionJoinReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "join_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List Identity Sessions visible through " "membership for one Actor.",
                                "discriminant": "identity.list_actor_sessions.list_actor_sessions",
                                "name": "list_actor_sessions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.ActorSessionsListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.ActorSessionsListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_actor_sessions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List direct child Identity Sessions "
                                "for one parent Identity Session.",
                                "discriminant": "identity.list_child_sessions.list_child_sessions",
                                "name": "list_child_sessions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.ChildSessionsListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.ChildSessionsListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_child_sessions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List members and ActorRole evidence " "for one Identity Session.",
                                "discriminant": "identity.list_session_members.list_session_members",
                                "name": "list_session_members",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMembersListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMembersListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_session_members",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Record an existing ActorRole as "
                                "evidence for one SessionMember "
                                "without\n"
                                "            granting, revoking, "
                                "scoping, or expiring permission.",
                                "discriminant": "identity.record_session_member_actor_role.record_session_member_actor_role",
                                "name": "record_session_member_actor_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMemberActorRoleRecordRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMemberActorRoleRecordReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "record_session_member_actor_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Register one provider-neutral session " "capability descriptor.",
                                "discriminant": "identity.register_session_provider.register_session_provider",
                                "name": "register_session_provider",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderRegisterRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderRegisterReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "register_session_provider",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve ActorCommit personal-history "
                                "records for one actor through the\n"
                                "            generated Identity service "
                                "API boundary.",
                                "discriminant": "identity.resolve_actor_commits.resolve_actor_commits",
                                "name": "resolve_actor_commits",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_commits",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve actor-subscription bridge "
                                "configs from Identity-owned "
                                "subscription\n"
                                "            lanes so Reactivity and "
                                "downstream services can discover who "
                                "is subscribed\n"
                                "            to a scoped event policy.",
                                "discriminant": "identity.resolve_actor_subscriptions.resolve_actor_subscriptions",
                                "name": "resolve_actor_subscriptions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_subscriptions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve canonical actor-role bindings "
                                "for one actor and one graph scope on "
                                "the\n"
                                "            public Identity service "
                                "API boundary.",
                                "discriminant": "identity.resolve_role_assignments.resolve_role_assignments",
                                "name": "resolve_role_assignments",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_role_assignments",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create or reuse one Identity-owned "
                                "credential profile and attach one "
                                "external\n"
                                "            secret-material reference "
                                "without carrying raw secret values.",
                                "discriminant": "identity.setup_credential_profile.setup_credential_profile",
                                "name": "setup_credential_profile",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialProfileSetupRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialProfileSetupReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "setup_credential_profile",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create the first canonical remote "
                                "Identity + Actor admission record for "
                                "an\n"
                                "            Interface consumer using a "
                                "public key and profile payload.",
                                "discriminant": "identity.signup_via_profile.signup_via_profile",
                                "name": "signup_via_profile",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.identity.IdentityAdmissionReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "signup_via_profile",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Start one concrete Identity Session " "under a SessionConfig.",
                                "discriminant": "identity.start_session.start_session",
                                "name": "start_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionStartRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionStartReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "start_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Remove one canonical actor-role "
                                "binding over the class-instance-aware "
                                "Identity\n"
                                "            role rail when the "
                                "requested class-instance scope is "
                                "unambiguous.",
                                "discriminant": "identity.unassign_role.unassign_role",
                                "name": "unassign_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleUnassignmentRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleUnassignmentReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "unassign_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                ],
                "name": "identity",
                "source_path": "bindings/identity.apis.aware",
            }
        ],
        "fqn_prefix": "aware_identity_service_api",
        "package_name": "identity-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create or reuse one canonical "
                                "actor-role binding over the "
                                "class-instance-aware\n"
                                "            Identity role rail.",
                                "discriminant": "identity.assign_role.assign_role",
                                "endpoint_ref": "identity.assign_role.assign_role",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "assign_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentRequest",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleAssignmentRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentReceipt",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleAssignmentReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "assign_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Attach one concrete provider "
                                "session/capability to a shared "
                                "Identity Session.",
                                "discriminant": "identity.attach_session_provider_session.attach_session_provider_session",
                                "endpoint_ref": "identity.attach_session_provider_session.attach_session_provider_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "attach_session_provider_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderSessionAttachRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderSessionAttachRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderSessionAttachReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderSessionAttachReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "attach_session_provider_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Bind one ActorConfig as eligible "
                                "session participation policy without\n"
                                "            admitting an actor or "
                                "granting roles.",
                                "discriminant": "identity.bind_session_config_actor_config.bind_session_config_actor_config",
                                "endpoint_ref": "identity.bind_session_config_actor_config.bind_session_config_actor_config",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "bind_session_config_actor_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigActorConfigBindRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionConfigActorConfigBindRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigActorConfigBindReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionConfigActorConfigBindReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "bind_session_config_actor_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Bind one provider capability to an "
                                "Identity SessionConfig without "
                                "creating a\n"
                                "            concrete provider session.",
                                "discriminant": "identity.bind_session_provider_config.bind_session_provider_config",
                                "endpoint_ref": "identity.bind_session_provider_config.bind_session_provider_config",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "bind_session_provider_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderConfigBindRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderConfigBindRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderConfigBindReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderConfigBindReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "bind_session_provider_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Check resolver availability for one "
                                "Identity credential profile and record "
                                "a\n"
                                "            readiness receipt without "
                                "carrying raw secret values.",
                                "discriminant": "identity.check_credential_readiness.check_credential_readiness",
                                "endpoint_ref": "identity.check_credential_readiness.check_credential_readiness",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "check_credential_readiness",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialReadinessCheckRequest",
                                    "python_model_ref": "aware_identity_service_dto.credential.profile.CredentialReadinessCheckRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialReadinessCheckReceipt",
                                    "python_model_ref": "aware_identity_service_dto.credential.profile.CredentialReadinessCheckReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "check_credential_readiness",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one Identity Session summary by "
                                "stable id without resolving\n"
                                "            domain-specific provider "
                                "state.",
                                "discriminant": "identity.describe_session.describe_session",
                                "endpoint_ref": "identity.describe_session.describe_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionDescribeRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionDescribeRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionDescribeResult",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionDescribeResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "describe_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create or reuse one Identity-owned "
                                "ActorCommit personal-history record "
                                "from\n"
                                "            an Environment lane commit "
                                "fanout receipt.",
                                "discriminant": "identity.ensure_actor_commit.ensure_actor_commit",
                                "endpoint_ref": "identity.ensure_actor_commit.ensure_actor_commit",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_actor_commit",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitEnsureRequest",
                                    "python_model_ref": "aware_identity_service_dto.actor.commit.ActorCommitEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitEnsureReceipt",
                                    "python_model_ref": "aware_identity_service_dto.actor.commit.ActorCommitEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_actor_commit",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create or reuse one canonical "
                                "actor-subscription binding for an "
                                "actor and a\n"
                                "            Reactivity-owned "
                                "event-condition scope. ActorRole "
                                "remains detached at this\n"
                                "            boundary; later ACL "
                                "eligibility can compose role checks "
                                "without making\n"
                                "            operation capability equal "
                                "event willingness.",
                                "discriminant": "identity.ensure_actor_subscription.ensure_actor_subscription",
                                "endpoint_ref": "identity.ensure_actor_subscription.ensure_actor_subscription",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_actor_subscription",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionEnsureRequest",
                                    "python_model_ref": "aware_identity_service_dto.actor.subscription.ActorSubscriptionEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionEnsureReceipt",
                                    "python_model_ref": "aware_identity_service_dto.actor.subscription.ActorSubscriptionEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_actor_subscription",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create or reuse one Identity-owned "
                                "generic session participation policy.",
                                "discriminant": "identity.ensure_session_config.ensure_session_config",
                                "endpoint_ref": "identity.ensure_session_config.ensure_session_config",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_session_config",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigEnsureRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionConfigEnsureRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionConfigEnsureReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionConfigEnsureReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "ensure_session_config",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Join one Actor to an Identity Session "
                                "under an explicit "
                                "SessionConfigActorConfig.",
                                "discriminant": "identity.join_session.join_session",
                                "endpoint_ref": "identity.join_session.join_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "join_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionJoinRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionJoinRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionJoinReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionJoinReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "join_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List Identity Sessions visible through " "membership for one Actor.",
                                "discriminant": "identity.list_actor_sessions.list_actor_sessions",
                                "endpoint_ref": "identity.list_actor_sessions.list_actor_sessions",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_actor_sessions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.ActorSessionsListRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.ActorSessionsListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.ActorSessionsListResult",
                                    "python_model_ref": "aware_identity_service_dto.session.session.ActorSessionsListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_actor_sessions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List direct child Identity Sessions "
                                "for one parent Identity Session.",
                                "discriminant": "identity.list_child_sessions.list_child_sessions",
                                "endpoint_ref": "identity.list_child_sessions.list_child_sessions",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_child_sessions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.ChildSessionsListRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.ChildSessionsListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.ChildSessionsListResult",
                                    "python_model_ref": "aware_identity_service_dto.session.session.ChildSessionsListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_child_sessions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List members and ActorRole evidence " "for one Identity Session.",
                                "discriminant": "identity.list_session_members.list_session_members",
                                "endpoint_ref": "identity.list_session_members.list_session_members",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_session_members",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMembersListRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionMembersListRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMembersListResult",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionMembersListResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "list_session_members",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Record an existing ActorRole as "
                                "evidence for one SessionMember "
                                "without\n"
                                "            granting, revoking, "
                                "scoping, or expiring permission.",
                                "discriminant": "identity.record_session_member_actor_role.record_session_member_actor_role",
                                "endpoint_ref": "identity.record_session_member_actor_role.record_session_member_actor_role",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_session_member_actor_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMemberActorRoleRecordRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionMemberActorRoleRecordRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionMemberActorRoleRecordReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionMemberActorRoleRecordReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "record_session_member_actor_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Register one provider-neutral session " "capability descriptor.",
                                "discriminant": "identity.register_session_provider.register_session_provider",
                                "endpoint_ref": "identity.register_session_provider.register_session_provider",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "register_session_provider",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderRegisterRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderRegisterRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionProviderRegisterReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionProviderRegisterReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "register_session_provider",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve ActorCommit personal-history "
                                "records for one actor through the\n"
                                "            generated Identity service "
                                "API boundary.",
                                "discriminant": "identity.resolve_actor_commits.resolve_actor_commits",
                                "endpoint_ref": "identity.resolve_actor_commits.resolve_actor_commits",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_actor_commits",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitResolveRequest",
                                    "python_model_ref": "aware_identity_service_dto.actor.commit.ActorCommitResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorCommitResolveResult",
                                    "python_model_ref": "aware_identity_service_dto.actor.commit.ActorCommitResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_commits",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve actor-subscription bridge "
                                "configs from Identity-owned "
                                "subscription\n"
                                "            lanes so Reactivity and "
                                "downstream services can discover who "
                                "is subscribed\n"
                                "            to a scoped event policy.",
                                "discriminant": "identity.resolve_actor_subscriptions.resolve_actor_subscriptions",
                                "endpoint_ref": "identity.resolve_actor_subscriptions.resolve_actor_subscriptions",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_actor_subscriptions",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionResolveRequest",
                                    "python_model_ref": "aware_identity_service_dto.actor.subscription.ActorSubscriptionResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.actor.ActorSubscriptionResolveResult",
                                    "python_model_ref": "aware_identity_service_dto.actor.subscription.ActorSubscriptionResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_subscriptions",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve canonical actor-role bindings "
                                "for one actor and one graph scope on "
                                "the\n"
                                "            public Identity service "
                                "API boundary.",
                                "discriminant": "identity.resolve_role_assignments.resolve_role_assignments",
                                "endpoint_ref": "identity.resolve_role_assignments.resolve_role_assignments",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_role_assignments",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentResolveRequest",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleAssignmentResolveRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleAssignmentResolveResult",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleAssignmentResolveResult",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "resolve_role_assignments",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create or reuse one Identity-owned "
                                "credential profile and attach one "
                                "external\n"
                                "            secret-material reference "
                                "without carrying raw secret values.",
                                "discriminant": "identity.setup_credential_profile.setup_credential_profile",
                                "endpoint_ref": "identity.setup_credential_profile.setup_credential_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "setup_credential_profile",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialProfileSetupRequest",
                                    "python_model_ref": "aware_identity_service_dto.credential.profile.CredentialProfileSetupRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.credential.CredentialProfileSetupReceipt",
                                    "python_model_ref": "aware_identity_service_dto.credential.profile.CredentialProfileSetupReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "setup_credential_profile",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create the first canonical remote "
                                "Identity + Actor admission record for "
                                "an\n"
                                "            Interface consumer using a "
                                "public key and profile payload.",
                                "discriminant": "identity.signup_via_profile.signup_via_profile",
                                "endpoint_ref": "identity.signup_via_profile.signup_via_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "signup_via_profile",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
                                    "python_model_ref": "aware_identity_service_dto.identity.admission.IdentitySignupViaProfileRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.identity.IdentityAdmissionReceipt",
                                    "python_model_ref": "aware_identity_service_dto.identity.models.IdentityAdmissionReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "signup_via_profile",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Start one concrete Identity Session " "under a SessionConfig.",
                                "discriminant": "identity.start_session.start_session",
                                "endpoint_ref": "identity.start_session.start_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "start_session",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.session.SessionStartRequest",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionStartRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.session.SessionStartReceipt",
                                    "python_model_ref": "aware_identity_service_dto.session.session.SessionStartReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "start_session",
                        "source_path": "bindings/identity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Remove one canonical actor-role "
                                "binding over the class-instance-aware "
                                "Identity\n"
                                "            role rail when the "
                                "requested class-instance scope is "
                                "unambiguous.",
                                "discriminant": "identity.unassign_role.unassign_role",
                                "endpoint_ref": "identity.unassign_role.unassign_role",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "unassign_role",
                                "request": {
                                    "class_ref": "aware_identity_service_dto.role.RoleUnassignmentRequest",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleUnassignmentRequest",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_identity_service_dto.role.RoleUnassignmentReceipt",
                                    "python_model_ref": "aware_identity_service_dto.role.assignment.RoleUnassignmentReceipt",
                                    "source_path": "bindings/identity.apis.aware",
                                },
                                "source_path": "bindings/identity.apis.aware",
                            }
                        ],
                        "name": "unassign_role",
                        "source_path": "bindings/identity.apis.aware",
                    },
                ],
                "name": "identity",
                "source_path": "bindings/identity.apis.aware",
            }
        ],
        "fqn_prefix": "aware_identity_service_api",
        "package_name": "identity-service-api",
        "schema_version": 1,
    }
)

IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF: Final[str] = "identity.assign_role.assign_role"
IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF: Final[str] = (
    "identity.attach_session_provider_session.attach_session_provider_session"
)
IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.bind_session_config_actor_config.bind_session_config_actor_config"
)
IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.bind_session_provider_config.bind_session_provider_config"
)
IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF: Final[str] = (
    "identity.check_credential_readiness.check_credential_readiness"
)
IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF: Final[str] = "identity.describe_session.describe_session"
IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF: Final[str] = (
    "identity.ensure_actor_commit.ensure_actor_commit"
)
IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF: Final[str] = (
    "identity.ensure_actor_subscription.ensure_actor_subscription"
)
IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF: Final[str] = (
    "identity.ensure_session_config.ensure_session_config"
)
IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF: Final[str] = "identity.join_session.join_session"
IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF: Final[str] = (
    "identity.list_actor_sessions.list_actor_sessions"
)
IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF: Final[str] = (
    "identity.list_child_sessions.list_child_sessions"
)
IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF: Final[str] = (
    "identity.list_session_members.list_session_members"
)
IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF: Final[str] = (
    "identity.record_session_member_actor_role.record_session_member_actor_role"
)
IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF: Final[str] = (
    "identity.register_session_provider.register_session_provider"
)
IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_actor_commits.resolve_actor_commits"
)
IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_actor_subscriptions.resolve_actor_subscriptions"
)
IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF: Final[str] = (
    "identity.resolve_role_assignments.resolve_role_assignments"
)
IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF: Final[str] = (
    "identity.setup_credential_profile.setup_credential_profile"
)
IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF: Final[str] = (
    "identity.signup_via_profile.signup_via_profile"
)
IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF: Final[str] = "identity.start_session.start_session"
IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF: Final[str] = "identity.unassign_role.unassign_role"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "identity.assign_role.assign_role": IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF,
    "identity.attach_session_provider_session.attach_session_provider_session": IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF,
    "identity.bind_session_config_actor_config.bind_session_config_actor_config": IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF,
    "identity.bind_session_provider_config.bind_session_provider_config": IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF,
    "identity.check_credential_readiness.check_credential_readiness": IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF,
    "identity.describe_session.describe_session": IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
    "identity.ensure_actor_commit.ensure_actor_commit": IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF,
    "identity.ensure_actor_subscription.ensure_actor_subscription": IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF,
    "identity.ensure_session_config.ensure_session_config": IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF,
    "identity.join_session.join_session": IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF,
    "identity.list_actor_sessions.list_actor_sessions": IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF,
    "identity.list_child_sessions.list_child_sessions": IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF,
    "identity.list_session_members.list_session_members": IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF,
    "identity.record_session_member_actor_role.record_session_member_actor_role": IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF,
    "identity.register_session_provider.register_session_provider": IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF,
    "identity.resolve_actor_commits.resolve_actor_commits": IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF,
    "identity.resolve_actor_subscriptions.resolve_actor_subscriptions": IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF,
    "identity.resolve_role_assignments.resolve_role_assignments": IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF,
    "identity.setup_credential_profile.setup_credential_profile": IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF,
    "identity.signup_via_profile.signup_via_profile": IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF,
    "identity.start_session.start_session": IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF,
    "identity.unassign_role.unassign_role": IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "IDENTITY__ASSIGN_ROLE__ASSIGN_ROLE_ENDPOINT_REF",
    "IDENTITY__ATTACH_SESSION_PROVIDER_SESSION__ATTACH_SESSION_PROVIDER_SESSION_ENDPOINT_REF",
    "IDENTITY__BIND_SESSION_CONFIG_ACTOR_CONFIG__BIND_SESSION_CONFIG_ACTOR_CONFIG_ENDPOINT_REF",
    "IDENTITY__BIND_SESSION_PROVIDER_CONFIG__BIND_SESSION_PROVIDER_CONFIG_ENDPOINT_REF",
    "IDENTITY__CHECK_CREDENTIAL_READINESS__CHECK_CREDENTIAL_READINESS_ENDPOINT_REF",
    "IDENTITY__DESCRIBE_SESSION__DESCRIBE_SESSION_ENDPOINT_REF",
    "IDENTITY__ENSURE_ACTOR_COMMIT__ENSURE_ACTOR_COMMIT_ENDPOINT_REF",
    "IDENTITY__ENSURE_ACTOR_SUBSCRIPTION__ENSURE_ACTOR_SUBSCRIPTION_ENDPOINT_REF",
    "IDENTITY__ENSURE_SESSION_CONFIG__ENSURE_SESSION_CONFIG_ENDPOINT_REF",
    "IDENTITY__JOIN_SESSION__JOIN_SESSION_ENDPOINT_REF",
    "IDENTITY__LIST_ACTOR_SESSIONS__LIST_ACTOR_SESSIONS_ENDPOINT_REF",
    "IDENTITY__LIST_CHILD_SESSIONS__LIST_CHILD_SESSIONS_ENDPOINT_REF",
    "IDENTITY__LIST_SESSION_MEMBERS__LIST_SESSION_MEMBERS_ENDPOINT_REF",
    "IDENTITY__RECORD_SESSION_MEMBER_ACTOR_ROLE__RECORD_SESSION_MEMBER_ACTOR_ROLE_ENDPOINT_REF",
    "IDENTITY__REGISTER_SESSION_PROVIDER__REGISTER_SESSION_PROVIDER_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ACTOR_COMMITS__RESOLVE_ACTOR_COMMITS_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ACTOR_SUBSCRIPTIONS__RESOLVE_ACTOR_SUBSCRIPTIONS_ENDPOINT_REF",
    "IDENTITY__RESOLVE_ROLE_ASSIGNMENTS__RESOLVE_ROLE_ASSIGNMENTS_ENDPOINT_REF",
    "IDENTITY__SETUP_CREDENTIAL_PROFILE__SETUP_CREDENTIAL_PROFILE_ENDPOINT_REF",
    "IDENTITY__SIGNUP_VIA_PROFILE__SIGNUP_VIA_PROFILE_ENDPOINT_REF",
    "IDENTITY__START_SESSION__START_SESSION_ENDPOINT_REF",
    "IDENTITY__UNASSIGN_ROLE__UNASSIGN_ROLE_ENDPOINT_REF",
]
