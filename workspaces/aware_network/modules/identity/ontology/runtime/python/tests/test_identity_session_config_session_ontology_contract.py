from uuid import uuid4

import pytest

from ._paths import IDENTITY_AWARE_ROOT

IDENTITY_AWARE = IDENTITY_AWARE_ROOT


class _EmptyHandlerSession:
    def imap_get(self, *args: object, **kwargs: object) -> None:
        return None


def _read(relative_path: str) -> str:
    return (IDENTITY_AWARE / relative_path).read_text(encoding="utf-8")


def _attributes_block(source: str) -> str:
    return source.split("// Attributes", 1)[1].split("fn ", 1)[0]


def test_identity_session_sources_use_object_relationships() -> None:
    config_source = _read("session/session_config.aware")
    config_actor_source = _read("session/session_config_actor_config.aware")
    session_source = _read("session/session.aware")
    member_source = _read("session/session_member.aware")
    member_role_source = _read("session/session_member_actor_role.aware")
    provider_source = _read("session/session_provider.aware")
    provider_config_source = _read("session/session_provider_session_config.aware")
    provider_session_source = _read("session/session_provider_session.aware")

    assert "class SessionConfig" in config_source
    assert "actor_configs SessionConfigActorConfig[]" in config_source
    assert "sessions Session[]" in config_source
    assert "actor_config actor.ActorConfig key" in config_actor_source
    assert "class Session" in session_source
    assert "parent_session Session?" in session_source
    assert "created_by_actor actor.Actor?" in session_source
    assert "members SessionMember[]" in session_source
    assert "provider_sessions SessionProviderSession[]" in session_source
    assert 'parent_session_scope_key String key = "root"' in session_source
    assert "children[]" not in session_source
    assert "actor actor.Actor key" in member_source
    assert "session_actor_config SessionConfigActorConfig" in member_source
    assert "actor_roles SessionMemberActorRole[]" in member_source
    assert "actor_role actor.ActorRole key" in member_role_source
    assert "class SessionProvider" in provider_source
    assert (
        "session_provider_session_configs SessionProviderSessionConfig[]"
        in provider_source
    )
    assert "session_config SessionConfig key" in provider_config_source
    assert (
        "provider_session_config SessionProviderSessionConfig key"
        in provider_session_source
    )
    assert (
        "provider_object_instance_graph_identity aware_meta.graph.instance.ObjectInstanceGraphIdentity?"
        in provider_session_source
    )
    assert (
        "provider_class_instance_identity aware_meta.class.ClassInstanceIdentity?"
        in provider_session_source
    )
    assert (
        "provider_object_instance_graph_branch aware_meta.graph.instance.ObjectInstanceGraphBranch?"
        in provider_session_source
    )


def test_identity_session_sources_keep_domain_specific_state_out() -> None:
    source_paths = (
        "session/session_config.aware",
        "session/session_config_actor_config.aware",
        "session/session.aware",
        "session/session_member.aware",
        "session/session_member_actor_role.aware",
        "session/session_provider.aware",
        "session/session_provider_session_config.aware",
        "session/session_provider_session.aware",
    )
    forbidden_attribute_tokens = (
        "environment_",
        "experience_",
        "attention_",
        "process_",
        "thread_",
        "layout_",
        "branch_id",
        "projection_hash",
        "actor_role_ids",
        "role_config_ids",
    )

    for source_path in source_paths:
        attributes = _attributes_block(_read(source_path))
        for token in forbidden_attribute_tokens:
            assert token not in attributes, source_path


def test_identity_session_actor_role_edge_is_evidence_not_authority() -> None:
    source = _read("session/session_member_actor_role.aware")

    assert "ActorRole evidence" in source
    assert "Does not grant, revoke, scope, or expire permission" in source
    assert "ActorRole-owned" in source


def test_identity_session_provider_contract_is_provider_neutral() -> None:
    provider_source = _read("session/session_provider.aware")
    provider_config_source = _read("session/session_provider_session_config.aware")
    provider_session_source = _read("session/session_provider_session.aware")

    joined = "\n".join(
        (
            provider_source,
            provider_config_source,
            provider_session_source,
        )
    )
    assert "Provider is not a Service, Environment, Conversation" in provider_source
    assert "not session ownership" in provider_session_source
    assert "many provider sessions may attach" in provider_session_source
    assert "Environment" not in _attributes_block(provider_source)
    assert "Conversation" not in _attributes_block(provider_source)
    assert "Workflow" not in _attributes_block(provider_source)
    assert "Workspace" not in _attributes_block(provider_source)
    assert "Attention" not in _attributes_block(provider_source)
    assert "provider_session_config SessionProviderSessionConfig?" not in joined


def test_identity_session_projections_are_declared() -> None:
    config_projection = _read("session_config_projection.aware")
    session_projection = _read("session_projection.aware")
    provider_projection = _read("session_provider_projection.aware")

    assert "projection SessionConfig" in config_projection
    assert "root session.SessionConfig" in config_projection
    assert (
        "session.SessionConfigActorConfig::actor_config ActorConfig"
        in config_projection
    )
    assert "session.SessionConfig::sessions Session" in config_projection
    assert "session.Session::created_by_actor Identity" not in config_projection
    assert "session.SessionMember::actor Identity" not in config_projection
    assert (
        "session.SessionMemberActorRole::actor_role Identity" not in config_projection
    )
    assert "session.Session::provider_sessions" not in config_projection
    assert (
        "session.SessionProviderSession::provider_session_config SessionProvider"
        not in (config_projection)
    )
    assert "projection Session" in session_projection
    assert "root session.Session" in session_projection
    assert "session.Session::parent_session Session" in session_projection
    assert "session.Session::created_by_actor Identity" in session_projection
    assert "session.SessionMember::actor Identity" in session_projection
    assert (
        "session.SessionMember::session_actor_config SessionConfig"
        in session_projection
    )
    assert "session.SessionMemberActorRole::actor_role Identity" in session_projection
    assert "session.Session::provider_sessions" in session_projection
    assert (
        "session.SessionProviderSession::provider_session_config SessionProvider"
        in (session_projection)
    )
    assert (
        "session.SessionProviderSession::provider_object_instance_graph_identity ObjectInstanceGraphIdentity"
        in (session_projection)
    )
    assert "projection SessionProvider" in provider_projection
    assert "root session.SessionProvider" in provider_projection
    assert (
        "session.SessionProviderSessionConfig::session_config SessionConfig"
        in provider_projection
    )


@pytest.mark.asyncio
async def test_identity_session_constructor_handlers_preserve_stable_reference_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_identity.handlers.impl.session import session as session_impl
    from aware_identity.handlers.impl.session import (
        session_config as session_config_impl,
    )
    from aware_identity.handlers.impl.session import (
        session_config_actor_config as policy_impl,
    )
    from aware_identity.handlers.impl.session import session_member as member_impl
    from aware_identity.handlers.impl.session import (
        session_member_actor_role as member_actor_role_impl,
    )
    from aware_identity.handlers.impl.session import session_provider as provider_impl
    from aware_identity.handlers.impl.session import (
        session_provider_session as provider_session_impl,
    )
    from aware_identity.handlers.impl.session import (
        session_provider_session_config as provider_config_impl,
    )
    from aware_identity_ontology.stable_ids import (
        stable_session_config_actor_config_id,
        stable_session_config_id,
        stable_session_id,
        stable_session_member_actor_role_id,
        stable_session_member_id,
        stable_session_provider_id,
        stable_session_provider_session_config_id,
        stable_session_provider_session_id,
    )

    fake_session = _EmptyHandlerSession()
    for module in (
        session_config_impl,
        policy_impl,
        session_impl,
        member_impl,
        member_actor_role_impl,
        provider_impl,
        provider_config_impl,
        provider_session_impl,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: fake_session)

    session_config = await session_config_impl.create(key="Goal Run")
    assert session_config.id == stable_session_config_id(key="Goal Run")
    assert session_config.key == "Goal Run"

    actor_config_id = uuid4()
    policy = await policy_impl.create_via_session_config(
        session_config_id=session_config.id,
        actor_config_id=actor_config_id,
    )
    assert policy.id == stable_session_config_actor_config_id(
        session_config_id=session_config.id,
        actor_config_id=actor_config_id,
    )
    assert policy.session_config_id == session_config.id
    assert policy.actor_config_id == actor_config_id

    created_by_actor_id = uuid4()
    session = await session_impl.build_via_session_config(
        session_config_id=session_config.id,
        key="daily-standup",
        created_by_actor_id=created_by_actor_id,
    )
    assert session.id == stable_session_id(
        session_config_id=session_config.id,
        parent_session_scope_key="root",
        key="daily-standup",
    )
    assert session.session_config_id == session_config.id
    assert session.parent_session_scope_key == "root"
    assert session.parent_session_id is None
    assert session.created_by_actor_id == created_by_actor_id

    child_session = await session_impl.build_via_session_config(
        session_config_id=session_config.id,
        parent_session_scope_key=str(session.id),
        key="software-dev",
        parent_session_id=session.id,
    )
    assert child_session.id == stable_session_id(
        session_config_id=session_config.id,
        parent_session_scope_key=str(session.id),
        key="software-dev",
    )
    assert child_session.session_config_id == session_config.id
    assert child_session.parent_session_id == session.id
    assert child_session.parent_session_scope_key == str(session.id)
    assert child_session.id != session.id

    actor_id = uuid4()
    member = await member_impl.create_via_session(
        session_id=session.id,
        actor_id=actor_id,
        session_actor_config_id=policy.id,
    )
    assert member.id == stable_session_member_id(
        session_id=session.id,
        actor_id=actor_id,
    )
    assert member.session_id == session.id
    assert member.actor_id == actor_id
    assert member.session_actor_config_id == policy.id

    actor_role_id = uuid4()
    role_edge = await member_actor_role_impl.create_via_session_member(
        session_member_id=member.id,
        actor_role_id=actor_role_id,
    )
    assert role_edge.id == stable_session_member_actor_role_id(
        session_member_id=member.id,
        actor_role_id=actor_role_id,
    )
    assert role_edge.session_member_id == member.id
    assert role_edge.actor_role_id == actor_role_id
    assert role_edge.source_kind == "identity_session"

    provider = await provider_impl.register(
        provider_key="coordination.conversation",
        provider_kind="conversation",
    )
    assert provider.id == stable_session_provider_id(
        provider_key="coordination.conversation",
    )
    assert provider.provider_key == "coordination.conversation"

    provider_config = await provider_config_impl.create_via_session_provider(
        session_provider_id=provider.id,
        config_key="conversation",
        session_config_id=session_config.id,
    )
    assert provider_config.id == stable_session_provider_session_config_id(
        session_provider_id=provider.id,
        config_key="conversation",
        session_config_id=session_config.id,
    )
    assert provider_config.session_provider_id == provider.id
    assert provider_config.session_config_id == session_config.id

    provider_oigi_id = uuid4()
    provider_class_instance_id = uuid4()
    provider_branch_id = uuid4()
    attachment = await provider_session_impl.create_via_session(
        session_id=session.id,
        provider_session_config_id=provider_config.id,
        provider_session_key="conversation-main",
        provider_session_ref="conversation://main",
        provider_object_instance_graph_identity_id=provider_oigi_id,
        provider_class_instance_identity_id=provider_class_instance_id,
        provider_object_instance_graph_branch_id=provider_branch_id,
    )
    assert attachment.id == stable_session_provider_session_id(
        session_id=session.id,
        provider_session_config_id=provider_config.id,
        provider_session_key="conversation-main",
    )
    assert attachment.session_id == session.id
    assert attachment.provider_session_config_id == provider_config.id
    assert attachment.provider_object_instance_graph_identity_id == provider_oigi_id
    assert attachment.provider_class_instance_identity_id == provider_class_instance_id
    assert attachment.provider_object_instance_graph_branch_id == provider_branch_id
