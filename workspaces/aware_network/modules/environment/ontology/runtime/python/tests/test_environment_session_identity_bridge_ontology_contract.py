from ._environment_runtime_test_paths import ENVIRONMENT_AWARE


ENVIRONMENT_SOURCE = ENVIRONMENT_AWARE / "environment"
PROFILE_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_profile_projection.aware"
SESSION_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_session_projection.aware"
CONFIG_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_config_projection.aware"
ENVIRONMENT_PROJECTION_SOURCE = ENVIRONMENT_AWARE / "environment_projection.aware"


def _read(relative_path: str) -> str:
    return (ENVIRONMENT_SOURCE / relative_path).read_text(encoding="utf-8")


def _relationships_block(source: str) -> str:
    return source.split("// Relationships", 1)[1].split("// Attributes", 1)[0]


def test_environment_config_owns_profile_and_session_configs_environment_owns_sessions() -> None:
    environment_config_source = _read("environment_config.aware")
    environment_source = _read("environment.aware")
    profile_source = _read("environment_profile.aware")
    profile_relationships = _relationships_block(profile_source)
    profile_config_source = _read("environment_profile_config.aware")
    profile_config_relationships = _relationships_block(profile_config_source)

    assert "profile_configs EnvironmentProfileConfig[]" in environment_config_source
    assert "session_configs EnvironmentSessionConfig[]" in environment_config_source
    assert "sessions EnvironmentSession[]" in environment_source
    assert "fn add_profile_config" in environment_config_source
    assert "fn add_session_config" in environment_config_source
    assert "fn start_session" in environment_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_config_relationships
    assert "environment_config EnvironmentConfig" not in profile_config_relationships
    assert "sessions EnvironmentSession[]" not in profile_relationships
    assert "session_configs EnvironmentSessionConfig[]" not in profile_relationships
    assert "fn add_session_config" not in profile_config_source
    assert "fn start_session" not in profile_source


def test_environment_session_config_portals_to_identity_session_config() -> None:
    source = _read("environment_session_config.aware")
    relationships = _relationships_block(source)

    assert (
        "identity_session_config aware_identity.session.SessionConfig" in relationships
    )
    assert "default_profile_config EnvironmentProfileConfig?" in relationships
    assert "default_process_config process.ProcessConfig?" in relationships
    assert "default_thread_config thread.ThreadConfig?" in relationships
    assert "sessions EnvironmentSession[]" not in relationships
    assert "identity_session_config_id UUID" in source
    assert "default_profile_config_id UUID? = null" in source
    assert "must not be inferred from keys" in source
    assert "This object never owns actor membership" in source
    assert "Runtime EnvironmentSession instances are Environment-owned" in source


def test_environment_session_wraps_identity_session_without_members() -> None:
    source = _read("environment_session.aware")
    relationships = _relationships_block(source)

    assert "session_config EnvironmentSessionConfig?" in relationships
    assert "identity_session aware_identity.session.Session key" in relationships
    assert "members EnvironmentSessionMember[]" not in relationships
    assert "created_by_actor aware_identity.actor.Actor" not in relationships
    assert "fn join_actor" not in source
    assert "identity_session_id UUID key" in source
    assert (
        "Actor membership, ActorRole evidence, and provider sessions live on" in source
    )


def test_environment_projection_declares_identity_session_portals() -> None:
    profile_source = PROFILE_PROJECTION_SOURCE.read_text(encoding="utf-8")
    session_source = SESSION_PROJECTION_SOURCE.read_text(encoding="utf-8")
    config_source = CONFIG_PROJECTION_SOURCE.read_text(encoding="utf-8")
    environment_source = ENVIRONMENT_PROJECTION_SOURCE.read_text(encoding="utf-8")

    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_source
    )
    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_source
    )
    assert "projection EnvironmentSessionConfig" in config_source
    assert (
        "environment.EnvironmentSessionConfig::identity_session_config aware_identity.SessionConfig"
        in config_source
    )
    assert (
        "environment.EnvironmentSessionConfig::default_profile_config EnvironmentProfileConfig"
        in config_source
    )
    assert "environment.EnvironmentSessionConfig::sessions" not in config_source
    assert "environment.EnvironmentProfileConfig::environment_config" not in profile_source
    assert "environment.EnvironmentProfileConfig::session_configs" not in profile_source
    assert "environment.EnvironmentProfile::sessions" not in profile_source
    assert "environment.Environment::sessions EnvironmentSession" in environment_source
    assert (
        "environment.EnvironmentSession::session_config EnvironmentSessionConfig"
        in session_source
    )
    assert (
        "environment.EnvironmentSession::identity_session aware_identity.Session"
        in session_source
    )
    assert "environment.EnvironmentSession::members" not in session_source
    assert "environment.EnvironmentSessionMember::actor_roles" not in session_source
