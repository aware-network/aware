import importlib

from aware_meta.runtime.graph_context import (
    build_meta_graph_runtime_context_for_aware_package_manifests,
)
from aware_environment.semantic_contract import (
    AWARE_ENVIRONMENT_SEMANTIC_CONTRACT,
    ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
    ENVIRONMENT_MANIFEST_RESOLUTION,
    ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE,
    ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS,
    ENVIRONMENT_MATERIALIZATION_RUNTIME,
    ENVIRONMENT_MATERIALIZATION_RUNTIME_CONTEXT,
    ENVIRONMENT_PACKAGE_ROLES,
    ENVIRONMENT_PROFILE_PROVIDER_OWNER,
    ENVIRONMENT_PROFILE_REQUIRED_PROJECTIONS,
    ENVIRONMENT_PROVIDER_OWNER,
)

from ._environment_runtime_test_paths import (
    ENVIRONMENT_AWARE,
    ENVIRONMENT_ONTOLOGY_ROOT,
    REPO_ROOT,
)


def _read(relative_path: str) -> str:
    return (ENVIRONMENT_AWARE / relative_path).read_text(encoding="utf-8")


def test_environment_config_package_is_active_profile_session_package_root() -> None:
    package_source = _read("environment/environment_config_package.aware")
    config_source = _read("environment/environment_config.aware")
    config_projection_source = _read("environment_config_projection.aware")
    profile_projection_source = _read("environment_profile_projection.aware")

    assert "class EnvironmentConfigPackage" in package_source
    assert "environment_config EnvironmentConfig unique" in package_source
    assert "class EnvironmentConfig" in config_source
    assert "profile_configs EnvironmentProfileConfig[]" in config_source
    assert "session_configs EnvironmentSessionConfig[]" in config_source
    assert "fn add_profile_config" in config_source
    assert "fn add_session_config" in config_source

    assert "projection EnvironmentConfigPackage is_branchable" in _read(
        "environment_config_package_projection.aware"
    )
    assert (
        "environment.EnvironmentConfig::profile_configs EnvironmentProfileConfig"
        in config_projection_source
    )
    assert (
        "environment.EnvironmentConfig::session_configs EnvironmentSessionConfig"
        in config_projection_source
    )
    assert (
        "environment.EnvironmentProfileConfig::environment_config"
        not in profile_projection_source
    )


def test_environment_thread_layout_is_thread_projection_member_not_standalone() -> None:
    profile_projection_source = _read("environment_profile_projection.aware")
    session_projection_source = _read("environment_session_projection.aware")

    assert "projection ThreadLayout" not in profile_projection_source
    assert "thread.Thread::thread_layouts\n" in profile_projection_source
    assert (
        "thread.ThreadLayout::layout aware_attention.Layout"
        in profile_projection_source
    )
    assert (
        "environment.EnvironmentSessionThread::thread_layout Thread"
        in session_projection_source
    )
    assert (
        "environment.EnvironmentSessionThread::thread_layout ThreadLayout"
        not in session_projection_source
    )


def test_environment_projection_runtime_context_derives_thread_layout_portals() -> None:
    manifest_paths = (
        REPO_ROOT
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=manifest_paths,
        workspace_root=REPO_ROOT,
        composite_name="Environment projection portal regression",
    )

    assert "environment-ontology" in context.source_graph_by_package_name
    assert "Thread" in context.projection_hash_by_name
    assert "EnvironmentSessionThread" in context.projection_hash_by_name
    assert "ThreadLayout" not in context.projection_hash_by_name


def test_environment_config_profile_session_edges_are_projection_portals() -> None:
    manifest_paths = (
        REPO_ROOT
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=manifest_paths,
        workspace_root=REPO_ROOT,
        composite_name="Environment config portal regression",
    )

    environment_hash = context.projection_hash_for_name("EnvironmentConfig")
    profile_hash = context.projection_hash_for_name("EnvironmentProfileConfig")
    session_hash = context.projection_hash_for_name("EnvironmentSessionConfig")
    portals = context.index.portal_index.portals_by_source_projection_hash.get(
        environment_hash,
        (),
    )
    portals_by_reference = {
        portal.reference_field_name: portal
        for portal in portals
        if portal.reference_field_name in {"profile_configs", "session_configs"}
    }

    assert (
        portals_by_reference["profile_configs"].target_projection_hash == profile_hash
    )
    assert (
        portals_by_reference["session_configs"].target_projection_hash == session_hash
    )


def test_environment_profile_package_is_retired_from_active_semantic_contract() -> None:
    contract = AWARE_ENVIRONMENT_SEMANTIC_CONTRACT

    assert contract.provider_key == "aware_environment"
    assert ENVIRONMENT_PROVIDER_OWNER == ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER
    assert ENVIRONMENT_PROFILE_PROVIDER_OWNER not in (
        ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE
    )
    assert ENVIRONMENT_PROFILE_REQUIRED_PROJECTIONS == ()

    assert ENVIRONMENT_MATERIALIZATION_OWNER_SEQUENCE == (
        ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER,
    )
    assert "EnvironmentConfigPackage" in (
        ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert "EnvironmentConfig" in ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    assert "EnvironmentProfileConfig" in (
        ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert "EnvironmentSessionConfig" in (
        ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert "EnvironmentProfilePackage" not in (
        ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    )

    assert {
        role.role: role.owns_manifest_kinds for role in ENVIRONMENT_PACKAGE_ROLES
    } == {ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER: ("aware_environment_toml",)}

    manifests_by_kind = {
        manifest.manifest_kind: manifest for manifest in ENVIRONMENT_MANIFEST_RESOLUTION
    }
    assert set(manifests_by_kind) == {"aware_environment_toml"}
    environment_manifest = manifests_by_kind["aware_environment_toml"]
    assert (
        environment_manifest.semantic_owner
        == ENVIRONMENT_ENVIRONMENT_CONFIG_PROVIDER_OWNER
    )
    assert environment_manifest.filename == "aware.environment.toml"
    assert environment_manifest.workspace_manifest_kind == "environment"
    assert environment_manifest.semantic_package_kind == "environment_config_package"
    assert environment_manifest.semantic_projection_name == "EnvironmentConfigPackage"
    assert environment_manifest.semantic_root_kind == "environment_config"
    assert environment_manifest.workspace_materialization_commit is True

    assert len(ENVIRONMENT_MATERIALIZATION_RUNTIME) == 1
    runtime = ENVIRONMENT_MATERIALIZATION_RUNTIME[0]
    assert runtime.lane_projection_name == "EnvironmentConfigPackage"
    assert runtime.required_projection_names == (
        ENVIRONMENT_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert runtime.runtime_projection_packages[0].projection_names == (
        "EnvironmentConfigPackage",
        "EnvironmentConfig",
        "EnvironmentProfileConfig",
        "EnvironmentSessionConfig",
    )
    assert "EnvironmentProfilePackage" not in (
        runtime.runtime_projection_packages[0].projection_names
    )

    assert len(ENVIRONMENT_MATERIALIZATION_RUNTIME_CONTEXT) == 1
    assert contract.manifest_resolution == ENVIRONMENT_MANIFEST_RESOLUTION
    assert contract.materialization_runtime == ENVIRONMENT_MATERIALIZATION_RUNTIME


def test_environment_sources_do_not_depend_on_structure_ontology() -> None:
    assert not (
        ENVIRONMENT_AWARE / "environment/environment_config_container_template.aware"
    ).exists()

    for source_path in ENVIRONMENT_AWARE.rglob("*.aware"):
        if not source_path.is_file():
            continue
        source = source_path.read_text(encoding="utf-8")
        assert "aware_structure." not in source, source_path.as_posix()

    for manifest_path in (
        ENVIRONMENT_ONTOLOGY_ROOT / "aware.ontology.toml",
        ENVIRONMENT_AWARE.parent / "aware.toml",
    ):
        manifest = manifest_path.read_text(encoding="utf-8")
        assert 'package_name = "structure-ontology"' not in manifest


def test_environment_manifest_loaders_and_providers_are_importable() -> None:
    policies_by_owner = {
        policy.semantic_owner: policy
        for policy in AWARE_ENVIRONMENT_SEMANTIC_CONTRACT.capability_execution_policy
    }
    for manifest in ENVIRONMENT_MANIFEST_RESOLUTION:
        loader_module = importlib.import_module(manifest.loader_module)
        policy = policies_by_owner[manifest.semantic_owner]
        assert policy.callable_module is not None
        assert policy.callable_name is not None
        provider_module = importlib.import_module(policy.callable_module)

        assert hasattr(loader_module, manifest.loader_name)
        assert hasattr(provider_module, policy.callable_name)


def test_aware_environment_profile_toml_is_bridge_only_not_active_package_manifest() -> (
    None
):
    profile_manifest_path = (
        REPO_ROOT / "environment/profiles/control/aware.environment.profile.toml"
    )
    profile_source_path = REPO_ROOT / "environment/profiles/control/aware/control.aware"

    assert profile_manifest_path.exists()
    assert profile_source_path.exists()

    active_filenames = {
        manifest.filename for manifest in ENVIRONMENT_MANIFEST_RESOLUTION
    }
    active_manifest_kinds = {
        manifest.manifest_kind for manifest in ENVIRONMENT_MANIFEST_RESOLUTION
    }
    assert "aware.environment.profile.toml" not in active_filenames
    assert "aware_environment_profile_toml" not in active_manifest_kinds
    assert all(
        runtime.lane_projection_name != "EnvironmentProfilePackage"
        for runtime in ENVIRONMENT_MATERIALIZATION_RUNTIME
    )
