from uuid import uuid4

import pytest


from ._environment_runtime_test_paths import ENVIRONMENT_AWARE


ENVIRONMENT_SOURCE = ENVIRONMENT_AWARE / "environment"
PROCESS_AWARE = ENVIRONMENT_AWARE / "process"
THREAD_AWARE = ENVIRONMENT_AWARE / "thread"
PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_projection.aware"
CONFIG_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_config_projection.aware"
SESSION_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_session_projection.aware"
NAVIGATION_PROJECTION_SOURCE = (
    ENVIRONMENT_AWARE / "environment_navigation_context_projection.aware"
)
PROFILE_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_profile_projection.aware"


def _read(relative_path: str) -> str:
    return (ENVIRONMENT_SOURCE / relative_path).read_text(encoding="utf-8")


def _read_process(relative_path: str) -> str:
    return (PROCESS_AWARE / relative_path).read_text(encoding="utf-8")


def _read_thread(relative_path: str) -> str:
    return (THREAD_AWARE / relative_path).read_text(encoding="utf-8")


def _relationships_block(source: str) -> str:
    return source.split("// Relationships", 1)[1].split("// Attributes", 1)[0]


def test_environment_session_owns_navigation_contexts_not_singleton_cursor() -> None:
    source = _read("environment_session.aware")
    relationships = _relationships_block(source)

    assert "navigation_contexts EnvironmentNavigationContext[]" in relationships
    assert "session_threads EnvironmentSessionThread[]" in relationships
    assert (
        "attention_sessions EnvironmentSessionAttentionSession[]" in relationships
    )
    assert "process process.Process" not in relationships
    assert "thread thread.Thread" not in relationships
    assert "active_session_thread" not in source
    assert "active_thread_layout" not in source
    assert "active_attention_session" not in source
    assert "fn create_navigation_context" in source
    assert "fn attach_attention_session" in source
    assert "fn resolve_thread" in source
    assert "shared tab/window-like OS pointer" in source


def test_environment_session_resolution_rows_are_pure_portals() -> None:
    session_thread_source = _read("environment_session_thread.aware")
    attention_session_source = _read("environment_session_attention_session.aware")

    session_thread_relationships = _relationships_block(session_thread_source)
    attention_session_relationships = _relationships_block(attention_session_source)

    assert "class EnvironmentSessionThread" in session_thread_source
    assert "navigation_context EnvironmentNavigationContext" not in session_thread_relationships
    assert "thread thread.Thread key" in session_thread_relationships
    assert "thread_layout thread.ThreadLayout key" in session_thread_relationships
    assert (
        "attention_session EnvironmentSessionAttentionSession?"
        in session_thread_relationships
    )
    assert "fn select_attention_session" in session_thread_source
    assert "fn select_layout" not in session_thread_source
    assert "active_" not in session_thread_source

    assert "class EnvironmentSessionAttentionSession" in attention_session_source
    assert (
        "attention_session aware_attention.session.AttentionSession key"
        in attention_session_relationships
    )
    assert "Layout" not in attention_session_relationships
    assert "Section" not in attention_session_relationships
    assert "Focus" not in attention_session_relationships
    assert "Binding" not in attention_session_source


def test_environment_navigation_context_points_to_session_thread_only() -> None:
    source = _read("environment_navigation_context.aware")
    relationships = _relationships_block(source)

    assert "class EnvironmentNavigationContext" in source
    assert "session_thread EnvironmentSessionThread" in relationships
    assert "process process.Process" not in relationships
    assert "thread thread.Thread" not in relationships
    assert "key String key" in source
    assert 'status String = "active"' in source
    assert "title String?" in source
    assert "is_default Bool = false" in source
    assert "selected_process_id UUID?" not in source
    assert "selected_thread_id UUID?" not in source
    assert "environment_session_id" not in source
    assert "session_thread_id UUID" in source
    assert "fn select_target" in source


def test_environment_default_topology_config_is_authored_on_config_layer() -> None:
    environment_config_source = _read("environment_config.aware")
    profile_config_source = _read("environment_profile_config.aware")
    session_config_source = _read("environment_session_config.aware")
    process_source = _read_process("process_config.aware")
    thread_source = _read_thread("thread_config.aware")
    session_source = _read("environment_session.aware")
    navigation_source = _read("environment_navigation_context.aware")

    assert "is_default Bool = false" in process_source
    assert "is_default Bool = false" in thread_source
    assert "is_default Bool = false" in navigation_source
    assert "profile_configs EnvironmentProfileConfig[]" in environment_config_source
    assert "session_configs EnvironmentSessionConfig[]" in environment_config_source
    assert "environment_config EnvironmentConfig key" not in profile_config_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_config_source
    assert "is_default" not in _relationships_block(profile_config_source)
    assert "is_default" not in _relationships_block(session_source)

    session_relationships = _relationships_block(session_config_source)
    assert "default_profile_config EnvironmentProfileConfig?" in session_relationships
    assert "default_process_config process.ProcessConfig?" in session_relationships
    assert "default_thread_config thread.ThreadConfig?" in session_relationships
    assert "default_profile_config_id UUID? = null" in session_config_source
    assert "default_process_config_id UUID? = null" in session_config_source
    assert "default_thread_config_id UUID? = null" in session_config_source


def test_navigation_history_is_commit_derived_not_custom_event() -> None:
    source = _read("environment_navigation_context.aware")
    session_source = _read("environment_session.aware")
    projection_source = PROJECTION_SOURCE.read_text(encoding="utf-8")

    assert "class EnvironmentNavigationEvent" not in source
    assert "EnvironmentNavigationEvent[]" not in session_source
    assert "EnvironmentNavigationEvent::" not in projection_source
    assert "commit replay" in source
    assert "no custom navigation-event object exists in v0" in session_source


def test_environment_projection_exposes_navigation_context_refs() -> None:
    environment_source = PROJECTION_SOURCE.read_text(encoding="utf-8")
    config_source = CONFIG_PROJECTION_SOURCE.read_text(encoding="utf-8")
    session_source = SESSION_PROJECTION_SOURCE.read_text(encoding="utf-8")
    navigation_source = NAVIGATION_PROJECTION_SOURCE.read_text(encoding="utf-8")
    profile_source = PROFILE_PROJECTION_SOURCE.read_text(encoding="utf-8")

    assert "environment.Environment::sessions EnvironmentSession" in environment_source
    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_source
    )
    assert "projection EnvironmentSessionConfig" in config_source
    assert (
        "environment.EnvironmentSessionConfig::identity_session_config aware_identity.SessionConfig"
        in config_source
    )
    assert "environment.EnvironmentSession::navigation_contexts" in session_source
    assert (
        "environment.EnvironmentSession::session_threads EnvironmentSessionThread"
        in session_source
    )
    assert (
        "environment.EnvironmentSession::attention_sessions EnvironmentSessionAttentionSession"
        in session_source
    )
    assert "projection EnvironmentSessionThread" in session_source
    assert "environment.EnvironmentSessionThread::navigation_context" not in session_source
    assert "environment.EnvironmentSessionThread::thread Thread" in session_source
    assert (
        "environment.EnvironmentSessionThread::thread_layout ThreadLayout"
        in session_source
    )
    assert (
        "environment.EnvironmentSessionThread::attention_session EnvironmentSessionAttentionSession"
        in session_source
    )
    assert "projection EnvironmentSessionAttentionSession" in session_source
    assert (
        "environment.EnvironmentSessionAttentionSession::attention_session aware_attention.AttentionSession"
        in session_source
    )
    assert "session.AttentionSession::layouts" not in session_source
    assert "session.AttentionSessionLayout::sections" not in session_source
    assert (
        "environment.EnvironmentNavigationContext::session_thread EnvironmentSessionThread"
        in navigation_source
    )
    assert "environment.EnvironmentNavigationContext::process" not in navigation_source
    assert "environment.EnvironmentNavigationContext::thread" not in navigation_source
    assert "projection EnvironmentProfileConfig" in profile_source
    assert "environment.EnvironmentProfileConfig::environment_config" not in profile_source
    assert "environment.EnvironmentProfileConfig::process_configs" in profile_source
    assert "environment.EnvironmentProfileConfig::providers" in profile_source
    assert "environment.EnvironmentProfileConfig::actor_configs" in profile_source
    assert "environment.EnvironmentProfileConfig::session_configs" not in profile_source
    assert "projection EnvironmentProfile" in profile_source
    assert (
        "environment.EnvironmentProfile::profile_config EnvironmentProfileConfig"
        in profile_source
    )
    assert "environment.EnvironmentProfile::sessions EnvironmentSession" not in profile_source
    assert "environment.EnvironmentProfile::processes Process" in profile_source
    assert "environment.EnvironmentProfile::process_configs" not in profile_source
    assert "process.ProcessConfig::thread_configs" in profile_source
    assert "process.ProcessConfig::processes" not in profile_source
    assert "thread.ThreadConfig::layout_configs" in profile_source
    assert "thread.ThreadConfig::threads" not in profile_source
    assert "projection Process {" in profile_source
    assert "root process.Process" in profile_source
    assert "process.Process::process_config EnvironmentProfileConfig" in profile_source
    assert "process.Process::threads Thread" in profile_source
    assert "projection Thread {" in profile_source
    assert "root thread.Thread" in profile_source
    assert "thread.Thread::thread_config EnvironmentProfileConfig" in profile_source
    assert "thread.Thread::thread_layouts ThreadLayout" in profile_source
    assert "projection ThreadLayout" in profile_source
    assert "thread.ThreadLayout::layout aware_attention.Layout" in profile_source
    assert "thread.Thread::thread_focus_scopes" not in profile_source
    assert "thread.Thread::active_thread_layout" not in profile_source
    assert "environment.EnvironmentSession::process" not in environment_source
    assert "environment.EnvironmentSession::thread" not in environment_source


def test_environment_projection_portals_profile_not_profile_topology() -> None:
    environment_source = PROJECTION_SOURCE.read_text(encoding="utf-8")
    config_source = CONFIG_PROJECTION_SOURCE.read_text(encoding="utf-8")
    profile_source = PROFILE_PROJECTION_SOURCE.read_text(encoding="utf-8")

    assert "projection Environment {" in environment_source
    assert "environment.Environment::profiles EnvironmentProfile" in environment_source
    assert "environment.Environment::sessions EnvironmentSession" in environment_source
    assert "environment.EnvironmentProfile::process_configs" not in environment_source
    assert "process.ProcessConfig::thread_configs" not in environment_source
    assert "thread.ThreadConfig::threads" not in environment_source

    assert "projection EnvironmentProfile {" in profile_source
    assert "root environment.EnvironmentProfile" in profile_source
    assert (
        "environment.EnvironmentProfile::profile_config EnvironmentProfileConfig"
        in profile_source
    )
    assert "environment.EnvironmentProfile::sessions EnvironmentSession" not in profile_source
    assert "environment.EnvironmentProfile::processes Process" in profile_source
    assert "environment.EnvironmentProfile::process_configs" not in profile_source
    assert "environment.EnvironmentProfile::providers" not in profile_source
    assert "environment.EnvironmentProfile::actor_configs" not in profile_source
    assert "environment.EnvironmentProfile::session_configs" not in profile_source
    assert "projection EnvironmentProfileConfig {" in profile_source
    assert "root environment.EnvironmentProfileConfig" in profile_source
    assert "environment.EnvironmentProfileConfig::environment_config" not in profile_source
    assert "environment.EnvironmentProfileConfig::process_configs" in profile_source
    assert "environment.EnvironmentProfileConfig::providers" in profile_source
    assert "environment.EnvironmentProfileConfig::actor_configs" in profile_source
    assert "environment.EnvironmentProfileConfig::session_configs" not in profile_source
    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_source
    )
    assert "environment.EnvironmentSessionConfig::sessions EnvironmentSession" not in config_source


@pytest.mark.asyncio
async def test_navigation_context_handlers_assign_parent_and_select_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_environment.handlers.impl.environment import (
        environment_navigation_context as context_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_session as session_impl,
    )

    environment_session_id = uuid4()
    session_thread_id = uuid4()

    class _DummyHandlerSession:
        @staticmethod
        def imap_get(*_args, **_kwargs):
            return None

    monkeypatch.setattr(
        context_impl,
        "current_handler_session",
        lambda: _DummyHandlerSession(),
    )

    context = await context_impl.build_via_environment_session(
        environment_session_id=environment_session_id,
        key="main",
        title="Main",
        session_thread_id=session_thread_id,
        is_default=True,
    )

    assert context.environment_session_id == environment_session_id
    assert context.key == "main"
    assert context.session_thread_id == session_thread_id
    assert context.is_default is True
    assert context.status == "active"

    next_session_thread_id = uuid4()
    selected = await context_impl.select_target(
        environment_navigation_context=context,
        session_thread_id=next_session_thread_id,
    )
    assert selected is context
    assert context.session_thread_id == next_session_thread_id

    session = type(
        "Session",
        (),
        {
            "id": environment_session_id,
            "navigation_contexts": [],
        },
    )()

    created = await session_impl.create_navigation_context(
        environment_session=session,
        key="secondary",
        title="Secondary",
        session_thread_id=session_thread_id,
        is_default=True,
    )
    assert created.environment_session_id == environment_session_id
    assert created.key == "secondary"
    assert created.session_thread_id == session_thread_id
    assert created.is_default is True
    assert session.navigation_contexts == [created]


@pytest.mark.asyncio
async def test_environment_session_thread_attention_handlers_are_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_environment.handlers.impl.environment import (
        environment_session_attention_session as attention_row_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_session_thread as session_thread_impl,
    )
    from aware_environment_ontology.stable_ids import (
        stable_environment_session_attention_session_id,
        stable_environment_session_thread_id,
    )

    environment_session_id = uuid4()
    attention_session_id = uuid4()
    thread_id = uuid4()
    thread_layout_id = uuid4()

    class _DummyHandlerSession:
        def __init__(self) -> None:
            self.rows = {}

        def imap_get(self, _type, object_id):
            return self.rows.get(object_id)

    handler_session = _DummyHandlerSession()
    monkeypatch.setattr(
        attention_row_impl,
        "current_handler_session",
        lambda: handler_session,
    )
    monkeypatch.setattr(
        session_thread_impl,
        "current_handler_session",
        lambda: handler_session,
    )

    attention_row = await attention_row_impl.build_via_environment_session(
        environment_session_id=environment_session_id,
        attention_session_id=attention_session_id,
        key="shared",
        title="Shared Attention",
    )
    expected_attention_row_id = stable_environment_session_attention_session_id(
        environment_session_id=environment_session_id,
        attention_session_id=attention_session_id,
    )
    assert attention_row.id == expected_attention_row_id
    assert attention_row.environment_session_id == environment_session_id
    assert attention_row.attention_session_id == attention_session_id
    assert attention_row.key == "shared"

    handler_session.rows[attention_row.id] = attention_row
    replayed_attention_row = await attention_row_impl.build_via_environment_session(
        environment_session_id=environment_session_id,
        attention_session_id=attention_session_id,
        key="ignored",
    )
    assert replayed_attention_row is attention_row

    session_thread = await session_thread_impl.build_via_environment_session(
        environment_session_id=environment_session_id,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
        attention_session_id=attention_row.id,
        key="main",
    )
    expected_session_thread_id = stable_environment_session_thread_id(
        environment_session_id=environment_session_id,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
    )
    assert session_thread.id == expected_session_thread_id
    assert session_thread.environment_session_id == environment_session_id
    assert session_thread.thread_id == thread_id
    assert session_thread.thread_layout_id == thread_layout_id
    assert session_thread.attention_session_id == attention_row.id

    selected = await session_thread_impl.select_attention_session(
        environment_session_thread=session_thread,
        attention_session_id=None,
    )
    assert selected is session_thread
    assert session_thread.thread_layout_id == thread_layout_id
    assert session_thread.attention_session_id is None
    assert session_thread.attention_session is None


@pytest.mark.asyncio
async def test_environment_session_appends_thread_attention_resolution_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_environment.handlers.impl.environment import (
        environment_session as session_impl,
    )
    from aware_environment_ontology.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology.environment.environment_session_thread import (
        EnvironmentSessionThread,
    )
    from aware_environment_ontology.stable_ids import (
        stable_environment_session_attention_session_id,
        stable_environment_session_thread_id,
    )

    environment_session_id = uuid4()
    attention_session_id = uuid4()
    thread_id = uuid4()
    thread_layout_id = uuid4()

    async def _build_attention_row(
        *,
        environment_session_id,
        attention_session_id,
        key=None,
        title=None,
        status="active",
        metadata_json=None,
    ):
        return EnvironmentSessionAttentionSession(
            id=stable_environment_session_attention_session_id(
                environment_session_id=environment_session_id,
                attention_session_id=attention_session_id,
            ),
            environment_session_id=environment_session_id,
            attention_session_id=attention_session_id,
            key=key,
            title=title,
            status=status,
            metadata_json=metadata_json,
        )

    async def _build_session_thread(
        *,
        environment_session_id,
        thread_id,
        thread_layout_id,
        attention_session_id=None,
        key=None,
        title=None,
        status="active",
        metadata_json=None,
    ):
        return EnvironmentSessionThread(
            id=stable_environment_session_thread_id(
                environment_session_id=environment_session_id,
                thread_id=thread_id,
                thread_layout_id=thread_layout_id,
            ),
            environment_session_id=environment_session_id,
            thread_id=thread_id,
            thread_layout_id=thread_layout_id,
            attention_session_id=attention_session_id,
            key=key,
            title=title,
            status=status,
            metadata_json=metadata_json,
        )

    monkeypatch.setattr(
        session_impl.EnvironmentSessionAttentionSession,
        "build_via_environment_session",
        staticmethod(_build_attention_row),
    )
    monkeypatch.setattr(
        session_impl.EnvironmentSessionThread,
        "build_via_environment_session",
        staticmethod(_build_session_thread),
    )

    session = type(
        "Session",
        (),
        {
            "id": environment_session_id,
            "attention_sessions": [],
            "session_threads": [],
        },
    )()

    attention_row = await session_impl.attach_attention_session(
        environment_session=session,
        attention_session_id=attention_session_id,
        key="shared",
    )
    assert session.attention_sessions == [attention_row]

    replayed_attention_row = await session_impl.attach_attention_session(
        environment_session=session,
        attention_session_id=attention_session_id,
        key="ignored",
    )
    assert replayed_attention_row is attention_row
    assert session.attention_sessions == [attention_row]

    session_thread = await session_impl.resolve_thread(
        environment_session=session,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
        attention_session_id=attention_row.id,
        key="main",
    )
    assert session.session_threads == [session_thread]
    assert session_thread.thread_layout_id == thread_layout_id
    assert session_thread.attention_session_id == attention_row.id

    replayed_session_thread = await session_impl.resolve_thread(
        environment_session=session,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
        key="ignored",
    )
    assert replayed_session_thread is session_thread
    assert session.session_threads == [session_thread]
