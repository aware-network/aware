from ._environment_runtime_test_paths import ENVIRONMENT_AWARE


def _read(relative_path: str) -> str:
    return (ENVIRONMENT_AWARE / relative_path).read_text(encoding="utf-8")


def test_environment_profile_config_owns_reusable_topology() -> None:
    environment_config_source = _read("environment/environment_config.aware")
    environment_source = _read("environment/environment.aware")
    profile_config_source = _read("environment/environment_profile_config.aware")
    profile_source = _read("environment/environment_profile.aware")
    config_projection_source = _read("environment_config_projection.aware")
    projection_source = _read("environment_profile_projection.aware")

    assert "class EnvironmentConfig" in environment_config_source
    assert "profile_configs EnvironmentProfileConfig[]" in environment_config_source
    assert "fn add_profile_config" in environment_config_source
    assert "session_configs EnvironmentSessionConfig[]" in environment_config_source
    assert "fn add_session_config" in environment_config_source

    assert "class EnvironmentProfileConfig" in profile_config_source
    assert "Parent constructor is EnvironmentConfig" in profile_config_source
    assert "environment_config EnvironmentConfig key" not in profile_config_source
    assert "environment_config_id UUID key" not in profile_config_source
    assert "process_configs process.ProcessConfig[]" in profile_config_source
    assert "actor_configs EnvironmentProfileActorConfig[]" in profile_config_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_config_source
    assert "fn create_process_config" in profile_config_source
    assert "fn add_session_config" not in profile_config_source

    assert "profile_config EnvironmentProfileConfig key" in profile_source
    assert "sessions EnvironmentSession[]" not in profile_source
    assert "process_configs process.ProcessConfig[]" not in profile_source
    assert "session_configs EnvironmentSessionConfig[]" not in profile_source
    assert "sessions EnvironmentSession[]" in environment_source
    assert "fn start_session" in environment_source

    assert "projection EnvironmentSessionConfig" in config_projection_source
    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_projection_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_projection_source
    )
    assert "projection EnvironmentProfileConfig" in projection_source
    assert "projection EnvironmentProfile" in projection_source
    assert "environment.EnvironmentProfileConfig::environment_config" not in projection_source
    assert "environment.EnvironmentProfileConfig::process_configs" in projection_source
    assert "environment.EnvironmentProfileConfig::session_configs" not in projection_source
    assert (
        "environment.EnvironmentProfile::profile_config EnvironmentProfileConfig"
        in projection_source
    )
