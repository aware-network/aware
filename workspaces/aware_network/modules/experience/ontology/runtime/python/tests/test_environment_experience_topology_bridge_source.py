from ._experience_runtime_test_paths import (
    EXPERIENCE_AWARE_ROOT,
    EXPERIENCE_ONTOLOGY_RUNTIME_ROOT,
)

EXPERIENCE_RUNTIME_IMPL = (
    EXPERIENCE_ONTOLOGY_RUNTIME_ROOT / "aware_experience" / "handlers" / "impl"
)


def _read(relative_path: str) -> str:
    return (EXPERIENCE_AWARE_ROOT / relative_path).read_text(encoding="utf-8")


def test_experience_profile_config_bridges_to_environment_environment_profile_config() -> (
    None
):
    source = _read("environment/environment_experience_profile_config.aware")

    assert (
        "environment_profile_config aware_environment.environment.EnvironmentProfileConfig key"
        in source
    )
    assert (
        "environment_provider_grant aware_environment.environment.EnvironmentProviderGrant?"
        in source
    )
    assert "process_configs EnvironmentExperienceProcessConfig[]" in source
    assert "process_configs process.ProcessConfig[]" not in source
    assert "fn create_process_config" not in source
    assert "fn add_process_config" in source


def test_applied_experience_profile_is_minimal_bridge() -> None:
    source = _read("environment/environment_experience_profile.aware")

    assert "class EnvironmentExperienceProfile" in source
    assert "profile_config EnvironmentExperienceProfileConfig key" in source
    assert (
        "environment_profile aware_environment.environment.EnvironmentProfile key"
        in source
    )
    assert "process_configs EnvironmentExperienceProcessConfig[]" not in source
    assert "actors EnvironmentExperienceActorConfig[]" not in source
    assert "events EnvironmentExperienceEvent[]" not in source
    assert (
        "view_event_transitions EnvironmentExperienceViewEventTransition[]"
        not in source
    )
    assert "fn add_process_config" not in source
    assert "fn add_actor_config" not in source
    assert "fn add_event" not in source


def test_experience_process_and_thread_config_are_bridge_objects_only() -> None:
    process_source = _read("environment/environment_experience_process_config.aware")
    thread_source = _read("environment/environment_experience_thread_config.aware")

    assert "class EnvironmentExperienceProcessConfig" in process_source
    assert "process_config aware_environment.process.ProcessConfig key" in (
        process_source
    )
    assert "thread_configs EnvironmentExperienceThreadConfig[]" in process_source
    assert "fn add_thread_config" in process_source
    assert "fn create_thread_config" not in process_source

    assert "class EnvironmentExperienceThreadConfig" in thread_source
    assert "thread_config aware_environment.thread.ThreadConfig key" in thread_source
    assert "programs EnvironmentExperienceProgram[]" in thread_source
    assert "program_applies EnvironmentExperienceProgramApply[]" in thread_source
    assert "fn add_program" in thread_source
    assert "fn add_program_apply" in thread_source
    assert "construct ThreadConfig" not in thread_source


def test_experience_no_longer_declares_topology_config_classes() -> None:
    retired_paths = [
        "process/process_config.aware",
        "thread/thread_config.aware",
        "thread/thread_config_projection_experience.aware",
        "thread/thread_config_program_config_graph.aware",
        "thread/thread_config_layout_config.aware",
        "thread/thread_config_layout_config_section.aware",
        "process_config_projection.aware",
        "thread_config_projection.aware",
    ]

    for relative_path in retired_paths:
        assert not (EXPERIENCE_AWARE_ROOT / relative_path).exists(), relative_path

    all_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in EXPERIENCE_AWARE_ROOT.rglob("*.aware")
        if path.is_file()
    )

    assert "class ProcessConfig" not in all_sources
    assert "class ThreadConfig" not in all_sources
    assert "ThreadConfigProjectionExperience" not in all_sources
    assert "ThreadConfigProgramConfigGraph" not in all_sources
    assert "ThreadConfigLayoutConfig" not in all_sources


def test_environment_experience_projection_is_portal_root_only() -> None:
    projection_source = _read("environment_experience_projection.aware")

    assert "projection EnvironmentExperience {" in projection_source
    assert "root environment.EnvironmentExperience" in projection_source
    assert (
        "environment.EnvironmentExperience::profile_configs EnvironmentExperienceProfileConfig"
        in projection_source
    )
    assert (
        "environment.EnvironmentExperience::profiles EnvironmentExperienceProfile"
        in projection_source
    )
    assert (
        "environment.EnvironmentExperience::topology_seeds EnvironmentTopologySeed"
        in projection_source
    )
    assert "environment.EnvironmentExperienceProfile::" not in projection_source
    assert "environment.EnvironmentExperienceProcessConfig::" not in projection_source
    assert "environment.EnvironmentExperienceThreadConfig::" not in projection_source
    assert "environment.EnvironmentTopologyProcessSeed::" not in projection_source
    assert "environment.EnvironmentTopologyThreadSeed::" not in projection_source


def test_environment_experience_profile_config_projection_owns_policy_path() -> None:
    projection_source = _read("environment_experience_profile_config_projection.aware")
    thread_runtime_projection_source = _read("thread_runtime_projection.aware")

    assert "projection EnvironmentExperienceProfileConfig {" in projection_source
    assert "root environment.EnvironmentExperienceProfileConfig" in projection_source
    assert (
        "environment.EnvironmentExperienceProfileConfig::environment_profile_config "
        "aware_environment.EnvironmentProfileConfig"
    ) in projection_source
    assert (
        "environment.EnvironmentExperienceProfileConfig::environment_provider_grant "
        "aware_environment.EnvironmentProfileConfig"
    ) in projection_source
    assert "environment.EnvironmentExperienceProfileConfig::process_configs" in (
        projection_source
    )
    assert (
        "environment.EnvironmentExperienceProcessConfig::process_config "
        "aware_environment.EnvironmentProfileConfig"
    ) in projection_source
    assert "environment.EnvironmentExperienceProcessConfig::thread_configs" in (
        projection_source
    )
    assert (
        "environment.EnvironmentExperienceThreadConfig::thread_config "
        "aware_environment.EnvironmentProfileConfig"
    ) in projection_source
    assert "environment.EnvironmentExperienceProfileConfig::actors" in (
        projection_source
    )
    assert "environment.EnvironmentExperienceProfileConfig::events" in projection_source
    assert "environment.EnvironmentExperienceThreadConfig::programs" in (
        projection_source
    )
    assert "environment.EnvironmentExperienceThreadConfig::program_applies" in (
        projection_source
    )
    assert "environment.EnvironmentExperienceProfileConfig::programs" not in (
        projection_source
    )
    assert "environment.EnvironmentExperienceProfileConfig::program_applies" not in (
        projection_source
    )
    assert (
        "thread.ThreadProgram::thread aware_environment.EnvironmentProfile"
        in thread_runtime_projection_source
    )


def test_environment_experience_profile_projection_is_applied_bridge_only() -> None:
    projection_source = _read("environment_experience_profile_projection.aware")

    assert "projection EnvironmentExperienceProfile {" in projection_source
    assert "root environment.EnvironmentExperienceProfile" in projection_source
    assert (
        "environment.EnvironmentExperienceProfile::profile_config "
        "EnvironmentExperienceProfileConfig"
    ) in projection_source
    assert (
        "environment.EnvironmentExperienceProfile::environment_profile "
        "aware_environment.EnvironmentProfile"
    ) in projection_source
    assert (
        "environment.EnvironmentExperienceProfile::process_configs"
        not in projection_source
    )
    assert "environment.EnvironmentExperienceProcessConfig::" not in projection_source
    assert "environment.EnvironmentExperienceThreadConfig::" not in projection_source
    assert "environment.EnvironmentExperienceProfile::actors" not in projection_source
    assert "environment.EnvironmentExperienceProfile::events" not in projection_source


def test_environment_topology_seed_projection_is_own_branch() -> None:
    projection_source = _read("environment_topology_seed_projection.aware")

    assert "projection EnvironmentTopologySeed {" in projection_source
    assert "root environment.EnvironmentTopologySeed" in projection_source
    assert (
        "environment.EnvironmentTopologySeed::environment_experience_profile_config "
        "EnvironmentExperienceProfileConfig"
    ) in projection_source
    assert "environment.EnvironmentTopologySeed::process_seeds" in projection_source
    assert (
        "environment.EnvironmentTopologyProcessSeed::process_config "
        "aware_environment.EnvironmentProfile"
    ) in projection_source
    assert (
        "environment.EnvironmentTopologyProcessSeed::thread_seeds" in projection_source
    )
    assert (
        "environment.EnvironmentTopologyThreadSeed::thread_config "
        "aware_environment.EnvironmentProfile"
    ) in projection_source
    assert (
        "environment.EnvironmentTopologyThreadSeed::layout_seeds" in projection_source
    )
    assert (
        "environment.EnvironmentTopologyThreadLayoutSeed::layout_config "
        "aware_attention.LayoutConfig"
    ) in projection_source
    assert (
        "environment.EnvironmentExperienceProfileConfig::actors"
        not in projection_source
    )
    assert "environment.EnvironmentExperienceThreadConfig::programs" not in (
        projection_source
    )


def test_experience_runtime_impl_no_longer_exposes_retired_topology_handlers() -> None:
    retired_paths = [
        "process/process_config.py",
        "thread/thread_config.py",
        "thread/thread_config_projection_experience.py",
        "thread/thread_config_program_config_graph.py",
        "thread/thread_config_layout_config.py",
        "thread/thread_config_layout_config_section.py",
    ]

    for relative_path in retired_paths:
        assert not (EXPERIENCE_RUNTIME_IMPL / relative_path).exists(), relative_path

    impl_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in EXPERIENCE_RUNTIME_IMPL.rglob("*.py")
        if path.is_file()
    )

    assert "aware_experience_ontology.process.process_config" not in impl_sources
    assert "aware_experience_ontology.thread.thread_config" not in impl_sources
    assert "ThreadConfigProjectionExperience" not in impl_sources
    assert "ThreadConfigProgramConfigGraph" not in impl_sources
