from ._experience_runtime_test_paths import EXPERIENCE_AWARE_ROOT


def _read(relative_path: str) -> str:
    return (EXPERIENCE_AWARE_ROOT / relative_path).read_text(encoding="utf-8")


def test_environment_experience_root_exposes_config_and_applied_profiles() -> None:
    source = _read("environment/environment_experience.aware")

    assert "profile_configs EnvironmentExperienceProfileConfig[]" in source
    assert "profiles EnvironmentExperienceProfile[]" in source
    assert "fn create_profile_config" in source
    assert "fn create_profile (" in source
    assert "environment_profile_config_id UUID key" in source
    assert "profile_config_id UUID key" in source
    assert "environment_profile_id UUID key" in source


def test_topology_seed_targets_profile_config_not_applied_profile() -> None:
    source = _read("environment/environment_topology_seed.aware")

    assert (
        "environment_experience_profile_config EnvironmentExperienceProfileConfig key"
        in source
    )
    assert "environment_experience_profile_config_id UUID key" in source
    assert (
        "environment_experience_profile EnvironmentExperienceProfile key" not in source
    )
    assert "environment_experience_profile_id UUID key" not in source


def test_applied_profile_has_no_config_policy_children() -> None:
    source = _read("environment/environment_experience_profile.aware")

    forbidden = (
        "actors EnvironmentExperienceActorConfig[]",
        "experiences EnvironmentExperienceProjection[]",
        "events EnvironmentExperienceEvent[]",
        "view_event_transitions EnvironmentExperienceViewEventTransition[]",
        "process_configs EnvironmentExperienceProcessConfig[]",
        "fn add_process_config",
        "fn add_actor_config",
        "fn add_projection_experience",
        "fn add_event",
        "fn add_view_event_transition",
        "fn update_title",
        "fn update_picture",
    )

    for token in forbidden:
        assert token not in source


def test_profile_config_owns_config_policy_children() -> None:
    source = _read("environment/environment_experience_profile_config.aware")

    required = (
        "environment_profile_config aware_environment.environment.EnvironmentProfileConfig key",
        "actors EnvironmentExperienceActorConfig[]",
        "experiences EnvironmentExperienceProjection[]",
        "events EnvironmentExperienceEvent[]",
        "view_event_transitions EnvironmentExperienceViewEventTransition[]",
        "process_configs EnvironmentExperienceProcessConfig[]",
        "fn add_process_config",
        "fn add_actor_config",
        "fn add_projection_experience",
        "fn add_event",
        "fn add_view_event_transition",
        "fn update_title",
        "fn update_picture",
    )

    for token in required:
        assert token in source

    assert "set title = title" in source
    assert "fn update_details" not in source
