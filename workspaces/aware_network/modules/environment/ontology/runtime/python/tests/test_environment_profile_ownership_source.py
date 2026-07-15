from uuid import uuid4

import pytest


from ._environment_runtime_test_paths import (
    ENVIRONMENT_AWARE,
    ENVIRONMENT_RUNTIME_ROOT,
    ENVIRONMENT_SQL_ROOTS,
)


def _read(relative_path: str) -> str:
    return (ENVIRONMENT_AWARE / relative_path).read_text(encoding="utf-8")


class _EmptyHandlerSession:
    def imap_get(self, *_args, **_kwargs):
        return None


def test_environment_root_uses_profile_provider_rail_not_experience_mounts() -> None:
    environment_source = _read("environment/environment.aware")
    projection_source = _read("environment_projection.aware")
    config_projection_source = _read("environment_config_projection.aware")
    profile_projection_source = _read("environment_profile_projection.aware")
    nav_projection_source = _read("environment_navigation_context_projection.aware")

    assert "profiles EnvironmentProfile[]" in environment_source
    assert "sessions EnvironmentSession[]" in environment_source
    assert "fn apply_profile" in environment_source
    assert "fn start_session" in environment_source
    assert "ontologies EnvironmentOntology[]" in environment_source
    assert "fn attach_ontology" in environment_source
    assert (
        "object_instance_graphs aware_meta.graph.instance.ObjectInstanceGraph"
        not in environment_source
    )
    assert "ontology_object_instance_graph_commit" not in environment_source
    assert "experience_profile_mounts" not in environment_source
    assert "projection_experience_oigis" not in environment_source

    assert "environment.Environment::profiles" in projection_source
    assert "environment.Environment::ontologies" in projection_source
    assert (
        "environment.EnvironmentOntology::ontology aware_ontology.Ontology"
        in projection_source
    )
    assert "environment.Environment::object_instance_graphs" not in projection_source
    assert "ontology_object_instance_graph_commit" not in projection_source
    assert (
        "environment.EnvironmentProfileConfig::providers" in profile_projection_source
    )
    assert (
        "environment.EnvironmentProfileConfig::actor_configs"
        in profile_projection_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_projection_source
    )
    assert "environment.EnvironmentProfileConfig::session_configs" not in profile_projection_source
    assert (
        "environment.EnvironmentSession::identity_session aware_identity.Session"
        not in profile_projection_source
    )
    assert (
        "environment.EnvironmentSession::navigation_contexts"
        not in profile_projection_source
    )
    assert (
        "environment.EnvironmentNavigationContext::session_thread EnvironmentSessionThread"
        in nav_projection_source
    )
    assert "environment.EnvironmentNavigationContext::process" not in nav_projection_source
    assert "environment.EnvironmentNavigationContext::thread" not in nav_projection_source
    assert "environment.EnvironmentProvider::grants" in profile_projection_source
    assert "EnvironmentExperienceProfileMount" not in projection_source
    assert "ProjectionExperienceOIGI" not in projection_source


def test_process_and_thread_are_runtime_parented_without_experience_config_refs() -> (
    None
):
    profile_source = _read("environment/environment_profile.aware")
    process_source = _read("process/process.aware")
    process_config_source = _read("process/process_config.aware")
    thread_source = _read("thread/thread.aware")
    thread_config_source = _read("thread/thread_config.aware")

    assert "config aware_experience.process.ProcessConfig" not in process_source
    assert "fn create_config" not in process_source
    assert "processes process.Process[]" in profile_source
    assert "fn create_process" in profile_source
    assert "processes Process[]" not in process_config_source
    assert "fn create_process" not in process_config_source
    assert "process_config ProcessConfig key" in process_source

    assert "config aware_experience.thread.ThreadConfig" not in thread_source
    assert "fn create_config" not in thread_source
    assert "thread_config ThreadConfig key" in thread_source
    assert "threads thread.Thread[]" in process_source
    assert "fn create_thread" in process_source
    assert "threads Thread[]" not in thread_config_source
    assert "fn create_thread" not in thread_config_source
    assert "process_id UUID key" not in thread_config_source


def test_canonical_environment_topology_sources_do_not_import_experience() -> None:
    canonical_paths = [
        "environment/environment.aware",
        "environment/environment_profile.aware",
        "environment/environment_profile_actor_config.aware",
        "environment/environment_profile_config.aware",
        "environment/environment_provider.aware",
        "environment/environment_provider_grant.aware",
        "environment/environment_session_config.aware",
        "environment/environment_session.aware",
        "environment/environment_navigation_context.aware",
        "process/process.aware",
        "process/process_config.aware",
        "thread/thread.aware",
        "thread/thread_config.aware",
        "thread/thread_config_object_projection_graph.aware",
        "thread/thread_config_layout_config.aware",
        "thread/thread_config_layout_config_section.aware",
        "environment_projection.aware",
    ]

    for relative_path in canonical_paths:
        source = _read(relative_path)
        assert "aware_experience" not in source, relative_path


def test_generated_environment_sql_does_not_own_program_runtime() -> None:
    moved_tables = (
        "program",
        "program_actor",
        "program_branch",
        "program_layout",
        "program_turn",
        "program_turn_instruction",
    )

    for sql_root in ENVIRONMENT_SQL_ROOTS:
        assert not (sql_root / "program").exists()

        for sql_file in sql_root.rglob("*.sql"):
            if "_aware" in sql_file.parts:
                continue
            source = sql_file.read_text(encoding="utf-8")
            for table_name in moved_tables:
                assert f"CREATE TABLE {table_name}" not in source, sql_file


def test_thread_config_hosts_projection_graph_and_attention_layout_not_programs() -> (
    None
):
    thread_config_source = _read("thread/thread_config.aware")
    projection_graph_source = _read(
        "thread/thread_config_object_projection_graph.aware"
    )
    layout_source = _read("thread/thread_config_layout_config.aware")
    section_source = _read("thread/thread_config_layout_config_section.aware")

    assert (
        "object_projection_graphs ThreadConfigObjectProjectionGraph[]"
        in thread_config_source
    )
    assert "layout_configs ThreadConfigLayoutConfig[]" in thread_config_source
    assert "program_config_graphs" not in thread_config_source
    assert "projection_experiences" not in thread_config_source

    assert (
        "aware_meta.graph.projection.ObjectProjectionGraph key"
        in projection_graph_source
    )
    assert "aware_attention.layout.LayoutConfig key" in layout_source
    assert "aware_attention.layout.LayoutConfigSectionConfig key" in section_source
    assert "layout_config_section_config aware_attention.LayoutConfig" in _read(
        "environment_profile_projection.aware"
    )
    assert "ProjectionExperienceSectionGraphBinding" not in section_source


def test_environment_profile_declares_actor_config_eligibility_not_actor_grants() -> (
    None
):
    profile_source = _read("environment/environment_profile.aware")
    profile_config_source = _read("environment/environment_profile_config.aware")
    actor_config_source = _read("environment/environment_profile_actor_config.aware")
    projection_source = _read("environment_profile_projection.aware")

    assert "actor_configs EnvironmentProfileActorConfig[]" in profile_config_source
    assert "fn add_actor_config" in profile_config_source
    assert "actor_configs EnvironmentProfileActorConfig[]" not in profile_source
    assert "actor_config aware_identity.actor.ActorConfig key" in actor_config_source
    assert 'policy_key String key = "admit"' in actor_config_source
    assert 'requirement_kind String = "environment_actor_config"' in actor_config_source
    assert 'access_scope String = "profile"' in actor_config_source
    assert (
        "environment.EnvironmentProfileActorConfig::actor_config aware_identity.ActorConfig"
        in (projection_source)
    )

    assert "actor aware_identity.actor.Actor" not in profile_source
    assert "actor aware_identity.actor.Actor" not in actor_config_source
    assert "actors aware_identity.actor.Actor[]" not in profile_source
    assert "actor_role aware_identity.actor.ActorRole" not in actor_config_source
    assert "actor_roles aware_identity.actor.ActorRole[]" not in actor_config_source


def test_environment_profile_declares_identity_session_bridge_not_membership() -> None:
    environment_config_source = _read("environment/environment_config.aware")
    environment_source = _read("environment/environment.aware")
    profile_source = _read("environment/environment_profile.aware")
    profile_config_source = _read("environment/environment_profile_config.aware")
    session_config_source = _read("environment/environment_session_config.aware")
    session_source = _read("environment/environment_session.aware")
    config_projection_source = _read("environment_config_projection.aware")
    profile_projection_source = _read("environment_profile_projection.aware")
    nav_projection_source = _read("environment_navigation_context_projection.aware")

    assert "session_configs EnvironmentSessionConfig[]" in environment_config_source
    assert "profile_configs EnvironmentProfileConfig[]" in environment_config_source
    assert "fn add_profile_config" in environment_config_source
    assert "fn add_session_config" in environment_config_source
    assert "environment_config EnvironmentConfig key" not in profile_config_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_config_source
    assert "fn add_session_config" not in profile_config_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_source
    assert "sessions EnvironmentSession[]" not in profile_source
    assert "sessions EnvironmentSession[]" in environment_source
    assert "fn start_session" in environment_source
    assert "fn start_session" not in profile_source

    assert (
        "identity_session_config aware_identity.session.SessionConfig"
        in session_config_source
    )
    assert "identity_session_config_id UUID" in session_config_source
    assert "identity_session aware_identity.session.Session key" in session_source
    assert "identity_session_id UUID key" in session_source
    assert "navigation_contexts EnvironmentNavigationContext[]" in session_source
    assert "fn create_navigation_context" in session_source
    assert "process process.Process" not in session_source
    assert "thread thread.Thread" not in session_source
    assert "EnvironmentSessionMember" not in session_source
    assert "fn join_actor" not in session_source

    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_projection_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_projection_source
    )
    assert (
        "environment.EnvironmentSessionConfig::identity_session_config aware_identity.SessionConfig"
        in config_projection_source
    )
    assert "environment.EnvironmentProfileConfig::session_configs" not in profile_projection_source
    assert "environment.EnvironmentProfileConfig::environment_config" not in profile_projection_source
    assert (
        "environment.EnvironmentSession::identity_session aware_identity.Session"
        not in profile_projection_source
    )
    assert (
        "environment.EnvironmentSession::navigation_contexts"
        not in profile_projection_source
    )
    assert (
        "environment.EnvironmentNavigationContext::session_thread EnvironmentSessionThread"
        in nav_projection_source
    )
    assert "environment.EnvironmentNavigationContext::process" not in nav_projection_source
    assert "environment.EnvironmentNavigationContext::thread" not in nav_projection_source


def test_canonical_generated_thread_handler_does_not_import_experience_thread_config() -> (
    None
):
    handler_source = (
        ENVIRONMENT_RUNTIME_ROOT / "aware_environment/handlers/impl/thread/thread.py"
    ).read_text(encoding="utf-8")

    assert "aware_experience_ontology.thread.thread_config" not in handler_source


@pytest.mark.asyncio
async def test_config_parent_constructor_handlers_assign_parent_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_environment.handlers.impl.process import process as process_impl
    from aware_environment.handlers.impl.process import (
        process_config as process_config_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_config as environment_config_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_profile_actor_config as profile_actor_config_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_session as environment_session_impl,
    )
    from aware_environment.handlers.impl.environment import (
        environment_session_config as environment_session_config_impl,
    )
    from aware_environment.handlers.impl.thread import thread as thread_impl
    from aware_environment.handlers.impl.thread import (
        thread_config as thread_config_impl,
    )

    session = _EmptyHandlerSession()
    for module in (
        process_impl,
        process_config_impl,
        environment_config_impl,
        profile_actor_config_impl,
        environment_session_impl,
        environment_session_config_impl,
        thread_impl,
        thread_config_impl,
    ):
        monkeypatch.setattr(
            module,
            "current_handler_session",
            lambda: session,
            raising=False,
        )

    environment_profile_config_id = uuid4()
    environment_config_id = uuid4()
    environment_id = uuid4()
    actor_config_id = uuid4()
    identity_session_config_id = uuid4()
    identity_session_id = uuid4()
    environment_profile_id = uuid4()
    process_config_id = uuid4()
    thread_config_id = uuid4()
    process_id = uuid4()

    async def _build_profile_config(
        *,
        environment_config_id,
        key,
        title=None,
        description=None,
        narrative=None,
    ):
        return type(
            "ProfileConfig",
            (),
            {
                "id": uuid4(),
                "environment_config_id": environment_config_id,
                "key": key,
                "title": title,
                "description": description,
                "narrative": narrative,
            },
        )()

    monkeypatch.setattr(
        environment_config_impl.EnvironmentProfileConfig,
        "build_via_environment_config",
        staticmethod(_build_profile_config),
    )

    environment_config = type(
        "EnvironmentConfig",
        (),
        {
            "id": environment_config_id,
            "profile_configs": [],
            "session_configs": [],
        },
    )()
    profile_config = await environment_config_impl.add_profile_config(
        environment_config=environment_config,
        key="control.default",
        title="Control",
    )
    assert profile_config.environment_config_id == environment_config_id
    assert profile_config.key == "control.default"
    assert environment_config.profile_configs == [profile_config]

    process_config = await process_config_impl.build_via_environment_profile_config(
        environment_profile_config_id=environment_profile_config_id,
        type="workspace",
        key="workspace.main",
        title="Workspace",
    )
    assert process_config.environment_profile_config_id == environment_profile_config_id
    assert process_config.key == "workspace.main"

    actor_policy = (
        await profile_actor_config_impl.create_via_environment_profile_config(
            environment_profile_config_id=environment_profile_config_id,
            actor_config_id=actor_config_id,
            policy_key="admit",
        )
    )
    assert actor_policy.environment_profile_config_id == environment_profile_config_id
    assert actor_policy.actor_config_id == actor_config_id
    assert actor_policy.policy_key == "admit"
    assert actor_policy.requirement_kind == "environment_actor_config"
    assert actor_policy.access_scope == "profile"

    environment_session_config = (
        await environment_session_config_impl.build_via_environment_config(
            environment_config_id=environment_config_id,
            key="exam",
            identity_session_config_id=identity_session_config_id,
            default_profile_config_id=environment_profile_config_id,
            title="Exam",
        )
    )
    assert environment_session_config.environment_config_id == environment_config_id
    assert (
        environment_session_config.default_profile_config_id
        == environment_profile_config_id
    )
    assert environment_session_config.identity_session_config_id == (
        identity_session_config_id
    )
    assert environment_session_config.key == "exam"

    environment_session = (
        await environment_session_impl.build_via_environment(
            environment_id=environment_id,
            identity_session_id=identity_session_id,
            session_config_id=environment_session_config.id,
            key="exam.1",
            title="Exam 1",
        )
    )
    assert environment_session.environment_id == environment_id
    assert environment_session.session_config_id == environment_session_config.id
    assert environment_session.identity_session_id == identity_session_id
    assert environment_session.key == "exam.1"

    process = await process_impl.build_via_environment_profile(
        environment_profile_id=environment_profile_id,
        process_config_id=process_config_id,
        key="workspace.run.1",
        title="Workspace Run 1",
    )
    assert process.environment_profile_id == environment_profile_id
    assert process.process_config_id == process_config_id
    assert process.key == "workspace.run.1"

    thread_config = await thread_config_impl.build_via_process_config(
        process_config_id=process_config_id,
        key="thread.main",
        title="Main Thread",
    )
    assert thread_config.process_config_id == process_config_id
    assert thread_config.key == "thread.main"

    first_thread = await thread_impl.build_via_process(
        process_id=process_id,
        thread_config_id=thread_config_id,
        key="thread.run.1",
        title="Thread Run 1",
    )
    second_thread = await thread_impl.build_via_process(
        process_id=process_id,
        thread_config_id=thread_config_id,
        key="thread.run.2",
        title="Thread Run 2",
    )

    assert first_thread.thread_config_id == thread_config_id
    assert second_thread.thread_config_id == thread_config_id
    assert first_thread.process_id == process_id
    assert second_thread.process_id == process_id
    assert first_thread.key != second_thread.key
