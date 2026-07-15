from __future__ import annotations

import base64
from dataclasses import dataclass, field
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_identity.context import (
    IdentityInvocationContext,
    scoped_identity_invocation_context,
)
from aware_meta_sdk import FunctionCallProof, OigCommitExpectation
from aware_meta_service.local_sdk import (
    build_local_meta_sdk_session_for_aware_package_manifests,
)
from ._paths import REPO_ROOT


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get(
                "AWARE_PERSISTENCE_BACKEND",
            ),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "AWARE_META_SERVICE_EVENT_STORE_ROOT": os.environ.get(
                "AWARE_META_SERVICE_EVENT_STORE_ROOT",
            ),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        os.environ["AWARE_META_SERVICE_EVENT_STORE_ROOT"] = str(
            root / ".aware" / "meta_commit_events"
        )
        os.environ.pop("DATABASE_URL", None)
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for key, previous in self._env_overrides.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _identity_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        repo_root / path
        for path in (
            "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
            "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        )
    )


def _record_by_function(records, *, function_name: str):
    matches = [record for record in records if record.function_name == function_name]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.asyncio
async def test_auth_token_issue_via_meta_sdk_uses_identity_invocation_context(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _identity_package_manifest_paths(repo_root)

    from aware_identity.auth.public_key.generator import (  # noqa: WPS433
        canonicalize_ed25519_public_key,
    )
    from aware_identity.handlers._generated import (  # noqa: WPS433
        meta_handlers as identity_meta_handlers,
    )
    from aware_identity_ontology.auth.auth_token_registry import (  # noqa: WPS433
        AuthTokenRegistry,
    )
    from aware_identity_ontology.identity.identity_enums import (  # noqa: WPS433
        IdentityType,
    )
    from aware_identity_ontology.stable_ids import (  # noqa: WPS433
        stable_actor_id,
        stable_auth_token_registry_id,
        stable_identity_id,
    )

    public_key, _ = canonicalize_ed25519_public_key("ed25519:" + ("22" * 32))
    identity_id = stable_identity_id(
        public_key=public_key,
        type=IdentityType.agent.value,
    )
    actor_id = stable_actor_id(identity_id=identity_id)
    registry_id = stable_auth_token_registry_id()
    environment_id = uuid5(NAMESPACE_URL, "aware://tests/identity/meta-sdk/env")
    process_id = uuid5(NAMESPACE_URL, "aware://tests/identity/meta-sdk/process")
    thread_id = uuid5(NAMESPACE_URL, "aware://tests/identity/meta-sdk/thread")
    token_id = uuid5(NAMESPACE_URL, "aware://tests/identity/meta-sdk/token")
    secret_b64url = (
        base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode("ascii")
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name="Aware Identity Local Meta SDK Context Proof",
            projection_name="AuthToken",
            actor_id=actor_id,
            branch_id=registry_id,
            generated_language_handler_module=identity_meta_handlers,
        )
        lane = meta_session.bind(
            projection="AuthToken",
            actor_id=actor_id,
            branch_id=registry_id,
        )
        with lane.activate(commit=True, publish=False):
            registry = await AuthTokenRegistry.ensure_registry()
            with scoped_identity_invocation_context(
                IdentityInvocationContext(
                    actor_id=actor_id,
                    branch_id=registry_id,
                    environment_id=environment_id,
                    process_id=process_id,
                    thread_id=thread_id,
                )
            ):
                payload = await registry.issue_apt_token(
                    actor_id=actor_id,
                    public_key=public_key,
                    context_environment_id=environment_id,
                    context_process_id=process_id,
                    context_thread_id=thread_id,
                    label="meta-sdk-context-proof",
                    scopes=["agent:turn.execute"],
                    token_id=token_id,
                    secret_b64url=secret_b64url,
                )

    assert isinstance(payload, dict)
    assert payload["token_id"] == str(token_id)
    assert payload["token"] == f"aware_apt_{token_id}.{secret_b64url}"
    assert payload["actor_id"] == str(actor_id)
    assert payload["context_environment_id"] == str(environment_id)
    assert payload["context_process_id"] == str(process_id)
    assert payload["context_thread_id"] == str(thread_id)
    assert lane.last_response is not None
    assert lane.last_response.status == "succeeded"


@pytest.mark.asyncio
async def test_signup_via_profile_meta_sdk_preserves_constructor_write_context(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _identity_package_manifest_paths(repo_root)

    from aware_identity.auth.public_key.generator import (  # noqa: WPS433
        canonicalize_ed25519_public_key,
    )
    from aware_identity.handlers._generated import (  # noqa: WPS433
        meta_handlers as identity_meta_handlers,
    )
    from aware_identity_ontology.identity.create_profile_request import (  # noqa: WPS433
        CreateProfileRequest,
    )
    from aware_identity_ontology.identity.identity import Identity  # noqa: WPS433
    from aware_identity_ontology.identity.identity_enums import (  # noqa: WPS433
        IdentityType,
    )
    from aware_identity_ontology.stable_ids import (  # noqa: WPS433
        stable_actor_id,
        stable_identity_id,
    )

    public_key, _ = canonicalize_ed25519_public_key("ed25519:" + ("33" * 32))
    identity_id = stable_identity_id(
        public_key=public_key,
        type=IdentityType.human.value,
    )
    actor_id = stable_actor_id(identity_id=identity_id)

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name="Aware Identity Signup Meta SDK Context Proof",
            projection_name="Identity",
            actor_id=actor_id,
            branch_id=identity_id,
            generated_language_handler_module=identity_meta_handlers,
        )
        lane = meta_session.bind(
            projection="Identity",
            actor_id=actor_id,
            branch_id=identity_id,
        )
        with lane.activate(commit=True, publish=False):
            identity = await Identity.signup_via_profile(
                public_key=public_key,
                create_profile_request=CreateProfileRequest(
                    display_name="Meta SDK Signup Proof",
                    public_handle="meta-sdk-signup-proof",
                    full_name="Meta SDK Signup Proof",
                    country_code="TW",
                    language_code="en",
                    bio="constructor write context proof",
                    identity_type=IdentityType.human,
                ),
                type=IdentityType.human,
            )

    assert identity.id == identity_id
    assert identity.identity_profile_id is not None
    assert identity.human_id is not None
    assert lane.last_response is not None
    assert lane.last_response.status == "succeeded"
    assert lane.last_response.root_object_id == identity_id
    assert lane.last_response.domain_commit_id is not None
    assert lane.last_response.object_instance_graph_commit_id is not None


@pytest.mark.asyncio
async def test_identity_session_config_session_via_meta_sdk_commits(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_manifest_paths = _identity_package_manifest_paths(repo_root)

    from aware_identity.handlers._generated import (  # noqa: WPS433
        meta_handlers as identity_meta_handlers,
    )
    from aware_identity_ontology.session.session import Session  # noqa: WPS433
    from aware_identity_ontology.session.session_config import (  # noqa: WPS433
        SessionConfig,
    )
    from aware_identity_ontology.session.session_config_actor_config import (  # noqa: WPS433
        SessionConfigActorConfig,
    )
    from aware_identity_ontology.session.session_member import (  # noqa: WPS433
        SessionMember,
    )
    from aware_identity_ontology.session.session_member_actor_role import (  # noqa: WPS433
        SessionMemberActorRole,
    )
    from aware_identity_ontology.session.session_provider import (  # noqa: WPS433
        SessionProvider,
    )
    from aware_identity_ontology.session.session_provider_session import (  # noqa: WPS433
        SessionProviderSession,
    )
    from aware_identity_ontology.session.session_provider_session_config import (  # noqa: WPS433
        SessionProviderSessionConfig,
    )
    from aware_identity_ontology.stable_ids import (  # noqa: WPS433
        stable_session_config_actor_config_id,
        stable_session_config_id,
        stable_session_id,
        stable_session_member_actor_role_id,
        stable_session_member_id,
        stable_session_provider_id,
        stable_session_provider_session_config_id,
        stable_session_provider_session_id,
    )

    session_config_key = "meta-sdk-session-proof"
    session_key = "daily-sync"
    provider_key = "coordination.conversation"
    provider_config_key = "conversation"
    provider_session_key = "conversation-main"
    branch_id = uuid5(NAMESPACE_URL, "aware://tests/identity/session/meta-sdk/branch")
    actor_id = uuid5(NAMESPACE_URL, "aware://tests/identity/session/meta-sdk/actor")
    actor_config_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/actor-config",
    )
    actor_role_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/actor-role",
    )
    provider_oigi_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/provider-oigi",
    )
    provider_class_instance_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/provider-class-instance",
    )
    provider_branch_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/provider-branch",
    )
    created_by_actor_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/session/meta-sdk/created-by",
    )

    expected_session_config_id = stable_session_config_id(key=session_config_key)
    expected_policy_id = stable_session_config_actor_config_id(
        session_config_id=expected_session_config_id,
        actor_config_id=actor_config_id,
    )
    expected_session_id = stable_session_id(
        session_config_id=expected_session_config_id,
        key=session_key,
    )
    expected_member_id = stable_session_member_id(
        session_id=expected_session_id,
        actor_id=actor_id,
    )
    expected_role_edge_id = stable_session_member_actor_role_id(
        session_member_id=expected_member_id,
        actor_role_id=actor_role_id,
    )
    expected_provider_id = stable_session_provider_id(provider_key=provider_key)
    expected_provider_config_id = stable_session_provider_session_config_id(
        session_provider_id=expected_provider_id,
        config_key=provider_config_key,
        session_config_id=expected_session_config_id,
    )
    expected_provider_session_id = stable_session_provider_session_id(
        session_id=expected_session_id,
        provider_session_config_id=expected_provider_config_id,
        provider_session_key=provider_session_key,
    )
    function_proofs = (
        FunctionCallProof(
            function_key="SessionConfig.create",
            commit_expectation=OigCommitExpectation(
                label="SessionConfig.create",
                expected_domain_branch_id=expected_session_config_id,
                expected_root_object_id=expected_session_config_id,
            ),
        ),
        FunctionCallProof(
            function_key="SessionConfig.add_actor_config",
            commit_expectation=OigCommitExpectation(
                label="SessionConfig.add_actor_config",
                expected_domain_branch_id=expected_session_config_id,
                expected_root_object_id=expected_session_config_id,
            ),
        ),
        FunctionCallProof(
            function_key="SessionConfig.start_session",
            commit_expectation=OigCommitExpectation(
                label="SessionConfig.start_session",
                require_domain_commit_id=False,
                require_object_instance_graph_commit_id=False,
                require_graph_hash_post=False,
                expected_domain_branch_id=expected_session_config_id,
                expected_root_object_id=expected_session_config_id,
            ),
        ),
        FunctionCallProof(
            function_key="Session.build_via_session_config",
            commit_expectation=OigCommitExpectation(
                label="Session.build_via_session_config",
                expected_domain_branch_id=expected_session_id,
                expected_root_object_id=expected_session_id,
            ),
        ),
        FunctionCallProof(
            function_key="Session.join_actor",
            commit_expectation=OigCommitExpectation(
                label="Session.join_actor",
                expected_domain_branch_id=expected_session_id,
                expected_root_object_id=expected_session_id,
            ),
        ),
        FunctionCallProof(
            function_key="SessionMember.add_actor_role",
            commit_expectation=OigCommitExpectation(
                label="SessionMember.add_actor_role",
                expected_domain_branch_id=expected_session_id,
                expected_root_object_id=expected_session_id,
            ),
        ),
        FunctionCallProof(
            function_key="SessionProvider.register",
            commit_expectation=OigCommitExpectation(
                label="SessionProvider.register",
                expected_domain_branch_id=expected_provider_id,
                expected_root_object_id=expected_provider_id,
            ),
        ),
        FunctionCallProof(
            function_key="SessionProvider.bind_session_config",
            commit_expectation=OigCommitExpectation(
                label="SessionProvider.bind_session_config",
                expected_domain_branch_id=expected_provider_id,
                expected_root_object_id=expected_provider_id,
            ),
        ),
        FunctionCallProof(
            function_key="Session.attach_provider_session",
            commit_expectation=OigCommitExpectation(
                label="Session.attach_provider_session",
                expected_domain_branch_id=expected_session_id,
                expected_root_object_id=expected_session_id,
            ),
        ),
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=aware_root,
            composite_name="Aware Identity Session Meta SDK Commit Proof",
            projection_name="SessionConfig",
            actor_id=actor_id,
            branch_id=branch_id,
            generated_language_handler_module=identity_meta_handlers,
        )
        config_lane = meta_session.bind(
            projection="SessionConfig",
            actor_id=actor_id,
            branch_id=expected_session_config_id,
        )
        with config_lane.activate(commit=True, publish=False):
            session_config = await SessionConfig.create(
                key=session_config_key,
                title="Meta SDK Session Proof",
            )
            policy = await session_config.add_actor_config(
                actor_config_id=actor_config_id,
                purpose="proof",
            )
            session = await session_config.start_session(
                key=session_key,
                created_by_actor_id=created_by_actor_id,
                source_kind="pytest",
            )
        session_lane = meta_session.bind(
            projection="Session",
            actor_id=actor_id,
            branch_id=expected_session_id,
        )
        with session_lane.activate(commit=True, publish=False):
            session = await Session.build_via_session_config(
                session_config_id=session_config.id,
                key=session_key,
                created_by_actor_id=created_by_actor_id,
                source_kind="pytest",
            )
            member = await session.join_actor(
                actor_id=actor_id,
                session_actor_config_id=policy.id,
            )
            role_edge = await member.add_actor_role(
                actor_role_id=actor_role_id,
                source_kind="identity_session",
            )
        provider_lane = meta_session.bind(
            projection="SessionProvider",
            actor_id=actor_id,
            branch_id=expected_provider_id,
        )
        with provider_lane.activate(commit=True, publish=False):
            provider = await SessionProvider.register(
                provider_key=provider_key,
                provider_kind="conversation",
                title="Conversation",
                contract_ref="provider://coordination/conversation",
            )
            provider_config = await provider.bind_session_config(
                config_key=provider_config_key,
                session_config_id=session_config.id,
                provider_contract_ref="provider://coordination/conversation/session",
            )
        with session_lane.activate(commit=True, publish=False):
            provider_session = await session.attach_provider_session(
                provider_session_config_id=provider_config.id,
                provider_session_key=provider_session_key,
                provider_session_ref="conversation://session/main",
                provider_object_instance_graph_identity_id=provider_oigi_id,
                provider_class_instance_identity_id=provider_class_instance_id,
                provider_object_instance_graph_branch_id=provider_branch_id,
            )

        assert isinstance(session_config, SessionConfig)
        assert session_config.id == expected_session_config_id
        assert isinstance(policy, SessionConfigActorConfig)
        assert policy.id == expected_policy_id
        assert policy.actor_config_id == actor_config_id
        assert isinstance(session, Session)
        assert session.id == expected_session_id
        assert session.created_by_actor_id == created_by_actor_id
        assert isinstance(member, SessionMember)
        assert member.id == expected_member_id
        assert member.session_actor_config_id == expected_policy_id
        assert isinstance(role_edge, SessionMemberActorRole)
        assert role_edge.id == expected_role_edge_id
        assert role_edge.actor_role_id == actor_role_id
        assert isinstance(provider, SessionProvider)
        assert provider.id == expected_provider_id
        assert provider.provider_key == provider_key
        assert isinstance(provider_config, SessionProviderSessionConfig)
        assert provider_config.id == expected_provider_config_id
        assert provider_config.session_provider_id == expected_provider_id
        assert provider_config.session_config_id == expected_session_config_id
        assert isinstance(provider_session, SessionProviderSession)
        assert provider_session.id == expected_provider_session_id
        assert provider_session.session_id == expected_session_id
        assert (
            provider_session.provider_session_config_id == expected_provider_config_id
        )
        assert (
            provider_session.provider_object_instance_graph_identity_id
            == provider_oigi_id
        )
        assert (
            provider_session.provider_class_instance_identity_id
            == provider_class_instance_id
        )
        assert (
            provider_session.provider_object_instance_graph_branch_id
            == provider_branch_id
        )

        records = [
            *config_lane.records,
            *session_lane.records,
            *provider_lane.records,
        ]
        for function_proof in function_proofs:
            record = _record_by_function(
                records,
                function_name=function_proof.function_key.split(".", 1)[1],
            )
            function_proof.assert_matches(record.response)

        config_head = await config_lane.get_head()
        assert config_head.status == "succeeded"
        assert config_head.root_object_id == expected_session_config_id
        session_head = await session_lane.get_head()
        assert session_head.status == "succeeded"
        assert session_head.root_object_id == expected_session_id
        provider_head = await provider_lane.get_head()
        assert provider_head.status == "succeeded"
        assert provider_head.root_object_id == expected_provider_id
