from __future__ import annotations

from dataclasses import dataclass
import hashlib
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from aware_identity_sdk import IdentityAdmissionProfile, IdentitySdkClient
from aware_identity_service_api import AwareIdentityServiceApiClient
from aware_identity_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_identity_service_dto.session.session import (
    SessionConfigEnsureRequest,
    SessionMembersListRequest,
    SessionProviderConfigBindRequest,
    SessionProviderRegisterRequest,
    SessionProviderSessionAttachRequest,
)
from aware_identity_ontology_dto.stable_ids import (
    stable_actor_id,
    stable_identity_id,
)
from aware_sdk_network.testing.live import (
    LiveSdkEndpointProofRow,
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


IDENTITY_API_PACKAGE_NAME = "identity-service-api"


@dataclass(frozen=True, slots=True)
class IdentityLiveSdk:
    api: AwareIdentityServiceApiClient
    sdk: IdentitySdkClient
    actor_id: UUID
    public_key: str


IDENTITY_ENDPOINT_MATRIX: tuple[LiveSdkEndpointProofRow, ...] = (
    LiveSdkEndpointProofRow(
        "identity.assign_role.assign_role",
        "IdentitySdkClient.assign_role",
        3,
        "fixture_pending",
        "requires RoleConfig/ClassInstanceIdentity fixture and grant authority context",
    ),
    LiveSdkEndpointProofRow(
        "identity.attach_session_provider_session.attach_session_provider_session",
        "api.identity.attach_session_provider_session.attach_session_provider_session",
        3,
        "green",
        "attaches an opaque provider session to the live SDK session fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.bind_session_config_actor_config.bind_session_config_actor_config",
        "api.identity.bind_session_config_actor_config.bind_session_config_actor_config",
        3,
        "fixture_pending",
        "requires ActorConfig fixture from Identity runtime seed",
    ),
    LiveSdkEndpointProofRow(
        "identity.bind_session_provider_config.bind_session_provider_config",
        "api.identity.bind_session_provider_config.bind_session_provider_config",
        3,
        "green",
        "binds the registered provider to the live SDK SessionConfig fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.check_credential_readiness.check_credential_readiness",
        "IdentitySdkClient.check_credential_readiness",
        3,
        "fixture_pending",
        "requires credential profile and controlled resolver secret fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.describe_session.describe_session",
        "IdentitySdkClient.describe_session",
        1,
        "green",
        "read-back of the live session started by the SDK",
    ),
    LiveSdkEndpointProofRow(
        "identity.ensure_actor_commit.ensure_actor_commit",
        "api.identity.ensure_actor_commit.ensure_actor_commit",
        3,
        "fixture_pending",
        "requires Environment lane commit fanout fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.ensure_actor_subscription.ensure_actor_subscription",
        "api.identity.ensure_actor_subscription.ensure_actor_subscription",
        3,
        "fixture_pending",
        "requires Reactivity event-condition scope fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.ensure_session_config.ensure_session_config",
        "api.identity.ensure_session_config.ensure_session_config",
        2,
        "green",
        "idempotent SessionConfig setup for the live SDK session proof",
    ),
    LiveSdkEndpointProofRow(
        "identity.join_session.join_session",
        "api.identity.join_session.join_session",
        3,
        "fixture_pending",
        "requires SessionConfigActorConfig binding fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.list_actor_sessions.list_actor_sessions",
        "IdentitySdkClient.list_actor_sessions",
        1,
        "green",
        "safe actor-session read through live Identity provider refs",
    ),
    LiveSdkEndpointProofRow(
        "identity.list_child_sessions.list_child_sessions",
        "IdentitySdkClient.list_child_sessions",
        1,
        "green",
        "read-back of the live child session started by the SDK",
    ),
    LiveSdkEndpointProofRow(
        "identity.list_session_members.list_session_members",
        "api.identity.list_session_members.list_session_members",
        1,
        "green",
        "safe member read for the live session started by the SDK",
    ),
    LiveSdkEndpointProofRow(
        "identity.record_session_member_actor_role.record_session_member_actor_role",
        "api.identity.record_session_member_actor_role.record_session_member_actor_role",
        3,
        "fixture_pending",
        "requires joined session member and ActorRole fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.register_session_provider.register_session_provider",
        "api.identity.register_session_provider.register_session_provider",
        3,
        "green",
        "registers an isolated provider descriptor for the live SDK session fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.resolve_actor_commits.resolve_actor_commits",
        "IdentitySdkClient.resolve_actor_commits",
        1,
        "green",
        "safe actor commit history read for the admitted actor",
    ),
    LiveSdkEndpointProofRow(
        "identity.resolve_actor_subscriptions.resolve_actor_subscriptions",
        "IdentitySdkClient.resolve_actor_subscriptions",
        1,
        "green",
        "safe actor subscription read for the admitted actor",
    ),
    LiveSdkEndpointProofRow(
        "identity.resolve_role_assignments.resolve_role_assignments",
        "IdentitySdkClient.resolve_role_assignments",
        1,
        "fixture_pending",
        "requires class-instance identity fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.setup_credential_profile.setup_credential_profile",
        "IdentitySdkClient.setup_credential_profile",
        3,
        "fixture_pending",
        "requires controlled secret-reference fixture",
    ),
    LiveSdkEndpointProofRow(
        "identity.signup_via_profile.signup_via_profile",
        "IdentitySdkClient.admit_agent_identity",
        2,
        "green",
        "self-consistent Ed25519 public-key admission through live Identity provider refs",
    ),
    LiveSdkEndpointProofRow(
        "identity.start_session.start_session",
        "IdentitySdkClient.start_session",
        2,
        "green",
        "start one live Identity Session under the generated SessionConfig",
    ),
    LiveSdkEndpointProofRow(
        "identity.unassign_role.unassign_role",
        "IdentitySdkClient.unassign_role",
        3,
        "fixture_pending",
        "requires prior role assignment fixture",
    ),
)


def test_identity_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in IDENTITY_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(IDENTITY_ENDPOINT_MATRIX) == 22
    assert {row.status for row in IDENTITY_ENDPOINT_MATRIX} == {
        "fixture_pending",
        "green",
    }
    assert sum(row.status == "green" for row in IDENTITY_ENDPOINT_MATRIX) == 12
    assert (
        sum(row.status == "fixture_pending" for row in IDENTITY_ENDPOINT_MATRIX) == 10
    )


def test_live_services_advertise_generated_identity_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=IDENTITY_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest_asyncio.fixture()
async def identity_sdk(live_sdk_api_dependency_routes):
    suffix = uuid4().hex[:10]
    public_key = _live_public_key(suffix)
    identity_id = stable_identity_id(public_key=public_key, type="agent")
    actor_id = stable_actor_id(identity_id=identity_id)
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=IDENTITY_API_PACKAGE_NAME,
        actor_id=actor_id,
    )
    api_client = AwareIdentityServiceApiClient(api_invoker)
    try:
        yield IdentityLiveSdk(
            api=api_client,
            sdk=IdentitySdkClient(api_client=api_client),
            actor_id=actor_id,
            public_key=public_key,
        )
    finally:
        await close_live_api_client(api_invoker)


@pytest.mark.asyncio
async def test_identity_admission_and_session_live_sdk(
    identity_sdk: IdentityLiveSdk,
) -> None:
    suffix = identity_sdk.public_key[-10:]
    admission = await identity_sdk.sdk.admit_agent_identity(
        public_key=identity_sdk.public_key,
        profile=IdentityAdmissionProfile(
            display_name=f"Live SDK Agent {suffix}",
            public_handle=f"live-sdk-{suffix}",
            full_name=f"Live SDK Agent {suffix}",
            country_code="US",
            language_code="en",
            bio="Identity SDK live readiness proof",
        ),
    )
    expected_identity_id = stable_identity_id(
        public_key=identity_sdk.public_key,
        type="agent",
    )
    assert admission.identity_id == expected_identity_id
    assert admission.actor_id == identity_sdk.actor_id
    assert admission.identity_profile_id is not None
    assert admission.public_handle == f"live-sdk-{suffix}"

    config = (
        await identity_sdk.api.identity.ensure_session_config.ensure_session_config(
            SessionConfigEnsureRequest(
                key=f"identity-live-sdk-session-{suffix}",
                title="Identity live SDK session",
                purpose="live-sdk-readiness",
            )
        )
    )
    assert config.session_config.session_config_id is not None
    assert config.session_config.key == f"identity-live-sdk-session-{suffix}"

    session = await identity_sdk.sdk.start_session(
        session_config_id=config.session_config.session_config_id,
        key=f"identity-live-sdk-root-{suffix}",
        title="Identity live SDK root session",
        created_by_actor_id=admission.actor_id,
    )
    assert session.session.session_id is not None
    assert session.session.session_config_id == config.session_config.session_config_id
    assert session.session.key == f"identity-live-sdk-root-{suffix}"
    assert session.session.created_by_actor_id == admission.actor_id

    child_session = await identity_sdk.sdk.start_child_session(
        parent_session_id=session.session.session_id,
        session_config_id=config.session_config.session_config_id,
        key=f"identity-live-sdk-child-{suffix}",
        title="Identity live SDK child session",
        created_by_actor_id=admission.actor_id,
    )
    assert child_session.session.session_id is not None
    assert child_session.session.parent_session_id == session.session.session_id
    assert child_session.session.key == f"identity-live-sdk-child-{suffix}"

    described = await identity_sdk.sdk.describe_session(
        session_id=session.session.session_id,
    )
    assert described.session is not None
    assert described.session.session_id == session.session.session_id

    actor_sessions = await identity_sdk.sdk.list_actor_sessions(
        actor_id=admission.actor_id,
    )
    assert actor_sessions.actor_id == admission.actor_id
    assert isinstance(actor_sessions.sessions, list)

    child_sessions = await identity_sdk.sdk.list_child_sessions(
        parent_session_id=session.session.session_id,
    )
    assert child_sessions.parent_session_id == session.session.session_id
    assert [item.session_id for item in child_sessions.sessions] == [
        child_session.session.session_id
    ]

    members = await identity_sdk.api.identity.list_session_members.list_session_members(
        SessionMembersListRequest(session_id=session.session.session_id)
    )
    assert members.session_id == session.session.session_id
    assert isinstance(members.members, list)

    commits = await identity_sdk.sdk.resolve_actor_commits(
        actor_id=admission.actor_id,
        limit=5,
    )
    assert isinstance(commits.actor_commits, list)

    subscriptions = await identity_sdk.sdk.resolve_actor_subscriptions(
        actor_id=admission.actor_id,
    )
    assert isinstance(subscriptions.subscriptions, list)


@pytest.mark.asyncio
async def test_identity_session_provider_fixture_live_sdk(
    identity_sdk: IdentityLiveSdk,
) -> None:
    suffix = identity_sdk.public_key[-10:]
    admission = await identity_sdk.sdk.admit_agent_identity(
        public_key=identity_sdk.public_key,
        profile=IdentityAdmissionProfile(
            display_name=f"Live SDK Provider Agent {suffix}",
            public_handle=f"live-sdk-provider-{suffix}",
            full_name=f"Live SDK Provider Agent {suffix}",
            country_code="US",
            language_code="en",
            bio="Identity SDK session provider fixture proof",
        ),
    )

    config = (
        await identity_sdk.api.identity.ensure_session_config.ensure_session_config(
            SessionConfigEnsureRequest(
                key=f"identity-live-sdk-provider-session-{suffix}",
                title="Identity live SDK provider session",
                purpose="live-sdk-session-provider-fixture",
            )
        )
    )
    session = await identity_sdk.sdk.start_session(
        session_config_id=config.session_config.session_config_id,
        key=f"identity-live-sdk-provider-root-{suffix}",
        title="Identity live SDK provider root session",
        created_by_actor_id=admission.actor_id,
    )

    provider_key = f"identity-live-sdk-provider-{suffix}"
    provider = await identity_sdk.api.identity.register_session_provider.register_session_provider(
        SessionProviderRegisterRequest(
            provider_key=provider_key,
            provider_kind="sdk_live_fixture",
            title="Identity live SDK provider",
            contract_ref="aware.identity.sdk.live.provider.v1",
            metadata_json={"fixture": "identity-session-provider"},
        )
    )
    assert provider.provider.session_provider_id is not None
    assert provider.provider.provider_key == provider_key
    assert provider.provider.provider_kind == "sdk_live_fixture"
    assert provider.provider.contract_ref == "aware.identity.sdk.live.provider.v1"

    provider_again = await identity_sdk.api.identity.register_session_provider.register_session_provider(
        SessionProviderRegisterRequest(
            provider_key=provider_key,
            provider_kind="sdk_live_fixture",
            title="Identity live SDK provider",
            contract_ref="aware.identity.sdk.live.provider.v1",
            metadata_json={"fixture": "identity-session-provider"},
        )
    )
    assert (
        provider_again.provider.session_provider_id
        == provider.provider.session_provider_id
    )

    provider_config_key = f"default-{suffix}"
    binding = await identity_sdk.api.identity.bind_session_provider_config.bind_session_provider_config(
        SessionProviderConfigBindRequest(
            session_provider_id=provider.provider.session_provider_id,
            config_key=provider_config_key,
            session_config_id=config.session_config.session_config_id,
            title="Identity live SDK provider binding",
            provider_contract_ref="aware.identity.sdk.live.provider.v1",
            selection_policy="contract_required",
            metadata_json={"fixture": "identity-session-provider-config"},
        )
    )
    assert binding.binding.session_provider_session_config_id is not None
    assert binding.binding.session_provider_id == provider.provider.session_provider_id
    assert binding.binding.config_key == provider_config_key
    assert binding.binding.session_config_id == config.session_config.session_config_id
    assert (
        binding.binding.provider_contract_ref == "aware.identity.sdk.live.provider.v1"
    )

    binding_again = await identity_sdk.api.identity.bind_session_provider_config.bind_session_provider_config(
        SessionProviderConfigBindRequest(
            session_provider_id=provider.provider.session_provider_id,
            config_key=provider_config_key,
            session_config_id=config.session_config.session_config_id,
            title="Identity live SDK provider binding",
            provider_contract_ref="aware.identity.sdk.live.provider.v1",
            selection_policy="contract_required",
            metadata_json={"fixture": "identity-session-provider-config"},
        )
    )
    assert (
        binding_again.binding.session_provider_session_config_id
        == binding.binding.session_provider_session_config_id
    )

    provider_session_key = f"provider-session-{suffix}"
    attached = await identity_sdk.api.identity.attach_session_provider_session.attach_session_provider_session(
        SessionProviderSessionAttachRequest(
            session_id=session.session.session_id,
            provider_session_config_id=binding.binding.session_provider_session_config_id,
            provider_session_key=provider_session_key,
            provider_session_ref=f"fixture://identity/{provider_session_key}",
            metadata_json={"fixture": "identity-session-provider-session"},
        )
    )
    assert attached.provider_session.session_provider_session_id is not None
    assert attached.provider_session.session_id == session.session.session_id
    assert (
        attached.provider_session.provider_session_config_id
        == binding.binding.session_provider_session_config_id
    )
    assert attached.provider_session.provider_session_key == provider_session_key
    assert (
        attached.provider_session.provider_session_ref
        == f"fixture://identity/{provider_session_key}"
    )

    described = await identity_sdk.sdk.describe_session(
        session_id=session.session.session_id,
    )
    assert described.session is not None
    assert [
        item.session_provider_session_id
        for item in described.session.provider_sessions
        if item.provider_session_key == provider_session_key
    ] == [attached.provider_session.session_provider_session_id]


def _live_public_key(suffix: str) -> str:
    digest = hashlib.sha256(f"identity-live-sdk-{suffix}".encode()).hexdigest()
    return f"ed25519:{digest[:64]}"
