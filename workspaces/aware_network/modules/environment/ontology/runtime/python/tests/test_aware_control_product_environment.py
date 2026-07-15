from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_environment.manifest.environment_loader import load_aware_environment_spec
from aware_environment.materialization.environment_source import (
    parse_environment_source_text,
)
from aware_environment.materialization.service import (
    _build_environment_config_snapshot,
    _dependency_object_config_graphs_for_package_spec,
    _discover_environment_semantic_package_specs,
    _load_environment_profile_session_sources,
    _meta_dependency_ref_from_object_config_graph,
    _semantic_catalog_external_dependency_package_names,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_config_id,
    stable_environment_profile_config_id,
    stable_environment_session_config_id,
    stable_process_config_id,
    stable_thread_config_id,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_workspace.materialization import build_workspace_bundle_materialization_plan
from aware_workspace.registry import load_aware_workspace_registry
from aware_identity_ontology.stable_ids import stable_session_config_id

from ._environment_runtime_test_paths import REPO_ROOT


_AWARE_CONTROL_ENVIRONMENT_TOML = (
    REPO_ROOT
    / "workspaces/aware_network/modules/interface/environments/aware_control/aware.environment.toml"
)
_AWARE_CONTROL_SOURCE = (
    REPO_ROOT
    / "workspaces/aware_network/modules/interface/environments/aware_control/aware/control.aware"
)
_AWARE_NETWORK_WORKSPACE_TOML = (
    REPO_ROOT / "workspaces/aware_network/aware.workspace.toml"
)
_AWARE_NETWORK_INTERFACE_MODULE_TOML = (
    REPO_ROOT / "workspaces/aware_network/modules/interface/aware.module.toml"
)
_AWARE_CONTROL_EXPERIENCE_TOML = (
    REPO_ROOT
    / "workspaces/aware_network/modules/interface/experiences/aware_control/aware.experience.toml"
)
_EXPERIENCE_AWARE = (
    REPO_ROOT / "workspaces/aware_network/modules/experience/ontology/structure/aware"
)
_KERNEL_ONTOLOGY_PACKAGE_NAMES = (
    "api-ontology",
    "code-ontology",
    "content-ontology",
    "history-ontology",
    "meta-ontology",
    "ontology-ontology",
    "reactivity-ontology",
    "sdk-ontology",
    "storage-ontology",
)


def test_aware_control_environment_manifest_is_product_environment() -> None:
    spec = load_aware_environment_spec(toml_path=_AWARE_CONTROL_ENVIRONMENT_TOML)

    assert spec.environment.handle == "aware-control"
    assert spec.environment.title == "Aware Control"
    assert spec.environment.canonical_language == "aware"
    assert spec.modules == (
        "identity",
        "attention",
        "environment",
        "experience",
        "economy",
        "service",
        "interface",
        "hub",
        "network",
    )
    assert spec.build is not None
    assert spec.build.sources_dir == "aware"
    assert spec.build.include_paths == ("**/*.aware",)
    assert spec.build.exclude_paths == ()

    module_source = _AWARE_NETWORK_INTERFACE_MODULE_TOML.read_text(encoding="utf-8")
    assert (
        'manifest = "environments/aware_control/aware.environment.toml"'
        in module_source
    )
    workspace_source = _AWARE_NETWORK_WORKSPACE_TOML.read_text(encoding="utf-8")
    assert "semantic_packages" not in workspace_source


def test_workspace_bundle_resolves_aware_control_environment_from_workspace_modules() -> (
    None
):
    registry = load_aware_workspace_registry(
        workspace_root=REPO_ROOT / "workspaces/aware_network",
        workspace_toml_path=_AWARE_NETWORK_WORKSPACE_TOML,
    )

    entries = [
        entry
        for entry in registry.semantic_package_entries
        if entry.manifest_path
        == "modules/interface/environments/aware_control/aware.environment.toml"
    ]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.code_package_name == "aware_control_environment"
    assert entry.workspace_manifest_kind == "environment"
    assert entry.manifest_path == (
        "modules/interface/environments/aware_control/aware.environment.toml"
    )
    assert entry.semantic_contract_role == (
        "aware_environment.environment_config.provider"
    )
    assert entry.code_package_manifest_kind == "aware_environment_toml"


def test_workspace_plan_exposes_aware_control_environment_as_semantic_package() -> None:
    workspace_root = REPO_ROOT / "workspaces/aware_network"
    plan = build_workspace_bundle_materialization_plan(
        workspace_root=workspace_root,
        workspace_toml_path=_AWARE_NETWORK_WORKSPACE_TOML,
    )

    environment_packages = [
        entry
        for entry in plan.semantic_package_entries
        if entry.code_package_name == "aware_control_environment"
    ]
    assert len(environment_packages) == 1
    environment_package = environment_packages[0]
    assert environment_package.workspace_manifest_kind == "environment"
    assert environment_package.manifest_path == (
        "modules/interface/environments/aware_control/aware.environment.toml"
    )
    assert environment_package.semantic_provider_key == "aware_environment"
    assert environment_package.semantic_package_family == "environment"
    assert environment_package.semantic_package_kind == "environment_config_package"
    assert environment_package.semantic_contract_role == (
        "aware_environment.environment_config.provider"
    )
    assert not hasattr(plan, "environment_entries")


def test_aware_control_modules_resolve_to_ontology_package_requirements() -> None:
    workspace_root = REPO_ROOT / "workspaces/aware_network"
    spec = load_aware_environment_spec(toml_path=_AWARE_CONTROL_ENVIRONMENT_TOML)
    external_dependency_names = _semantic_catalog_external_dependency_package_names(
        workspace_root=workspace_root,
        semantic_ontology_package_catalog=_kernel_ontology_package_catalog(),
    )

    assert set(external_dependency_names) == set(_KERNEL_ONTOLOGY_PACKAGE_NAMES)
    with pytest.raises(RuntimeError, match="missing canonical package dependencies"):
        _discover_environment_semantic_package_specs(
            workspace_root=workspace_root,
            module_names=spec.modules,
        )

    package_specs = _discover_environment_semantic_package_specs(
        workspace_root=workspace_root,
        module_names=spec.modules,
        available_dependency_package_names=external_dependency_names,
    )

    package_names = {package.package_name for package in package_specs}
    assert {
        "identity-ontology",
        "attention-ontology",
        "environment-ontology",
        "experience-ontology",
        "economy-ontology",
        "service-ontology",
        "interface-ontology",
        "hub-ontology",
        "network-ontology",
    }.issubset(package_names)
    identity_package = next(
        package
        for package in package_specs
        if package.package_name == "identity-ontology"
    )
    assert identity_package.ontology_manifest_path == (
        "modules/identity/ontology/aware.ontology.toml"
    )
    assert identity_package.source_manifest_path == (
        "modules/identity/ontology/structure/aware.toml"
    )


def _kernel_ontology_package_catalog() -> dict[str, object]:
    kernel_root = REPO_ROOT / "workspaces/aware_kernel"
    return {
        "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
        "entries": [
            {
                "package_name": package_name,
                "fqn_prefix": f"aware_{package_name.removesuffix('-ontology')}",
                "owner_root": kernel_root.as_posix(),
                "manifest_path": (
                    f"modules/{package_name.removesuffix('-ontology')}"
                    "/ontology/structure/aware.toml"
                ),
                "dependency_package_names": [],
            }
            for package_name in _KERNEL_ONTOLOGY_PACKAGE_NAMES
        ],
    }


def test_experience_runtime_thread_projection_targets_environment_thread() -> None:
    source = (_EXPERIENCE_AWARE / "thread_runtime_projection.aware").read_text(
        encoding="utf-8"
    )

    assert "thread.ThreadProgram::thread aware_environment.Thread" in source
    assert (
        "thread.ThreadProgram::thread aware_environment.EnvironmentProfileConfig"
        not in source
    )


def test_aware_control_source_lowers_profile_process_thread_session_tokens() -> None:
    bundle = parse_environment_source_text(
        source_text=_AWARE_CONTROL_SOURCE.read_text(encoding="utf-8"),
        source_path=_AWARE_CONTROL_SOURCE.relative_to(REPO_ROOT).as_posix(),
    )

    assert len(bundle.profiles) == 1
    profile = bundle.profiles[0]
    assert profile.key == "control.default"
    assert profile.is_default is True
    assert profile.title == "Aware Control"
    assert len(profile.processes) == 1
    process = profile.processes[0]
    assert process.key == "control"
    assert process.type == "continuous"
    assert process.is_default is True
    assert len(process.threads) == 1
    thread = process.threads[0]
    assert thread.key == "control.main"
    assert thread.workspace_view_key == "thread.workspace"
    assert thread.is_default is True
    assert len(profile.sessions) == 1
    session = profile.sessions[0]
    assert session.key == "control.default"
    assert session.default_process_key == "control"
    assert session.default_thread_key == "control.main"


def test_environment_config_snapshot_contains_aware_control_profile_and_session() -> (
    None
):
    workspace_root = REPO_ROOT / "workspaces/aware_network"
    environment_config_id = stable_environment_config_id(handle="aware-control")
    sources = _load_environment_profile_session_sources(
        workspace_root=workspace_root,
        environment_toml_path=_AWARE_CONTROL_ENVIRONMENT_TOML,
        spec=load_aware_environment_spec(toml_path=_AWARE_CONTROL_ENVIRONMENT_TOML),
    )

    environment_config = _build_environment_config_snapshot(
        environment_config_id=environment_config_id,
        handle="aware-control",
        title="Aware Control",
        canonical_language=CodeLanguage.aware,
        languages=(CodeLanguage.aware,),
        semantic_packages=(),
        environment_sources=sources,
        description=None,
        is_kernel=False,
    )

    assert environment_config.handle == "aware-control"
    assert len(environment_config.profile_configs) == 1
    assert len(environment_config.session_configs) == 1

    profile_config = environment_config.profile_configs[0]
    expected_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_config_id,
        key="control.default",
    )
    assert profile_config.id == expected_profile_config_id
    assert profile_config.environment_config_id == environment_config_id

    process_config = profile_config.process_configs[0]
    expected_process_config_id = stable_process_config_id(
        environment_profile_config_id=expected_profile_config_id,
        key="control",
    )
    assert process_config.id == expected_process_config_id
    assert process_config.is_default is True

    thread_config = process_config.thread_configs[0]
    expected_thread_config_id = stable_thread_config_id(
        process_config_id=expected_process_config_id,
        key="control.main",
    )
    assert thread_config.id == expected_thread_config_id
    assert thread_config.workspace_view_key == "thread.workspace"

    session_config = environment_config.session_configs[0]
    assert session_config.id == stable_environment_session_config_id(
        environment_config_id=environment_config_id,
        key="control.default",
    )
    assert session_config.identity_session_config_id == stable_session_config_id(
        key="control.default",
    )
    assert session_config.default_profile_config_id == expected_profile_config_id
    assert session_config.default_process_config_id == expected_process_config_id
    assert session_config.default_thread_config_id == expected_thread_config_id


def test_environment_profile_package_manifest_kind_is_not_active_metadata() -> None:
    module_source = (
        REPO_ROOT / "workspaces/aware_network/modules/environment/aware.module.toml"
    ).read_text(encoding="utf-8")
    ontology_source = (
        REPO_ROOT
        / "workspaces/aware_network/modules/environment/ontology/aware.ontology.toml"
    ).read_text(encoding="utf-8")
    experience_source = _AWARE_CONTROL_EXPERIENCE_TOML.read_text(encoding="utf-8")

    assert "aware_environment_profile_toml" not in module_source
    assert "aware_environment_profile_toml" not in ontology_source
    assert 'environment_handle = "aware-control"' in experience_source


def test_environment_package_compile_resolves_external_dependency_graphs() -> None:
    dependency_graph = _test_object_config_graph(
        name="reactivity-ontology",
        fqn_prefix="aware_reactivity",
    )
    package_spec = SimpleNamespace(
        package_name="identity-ontology",
        dependency_package_names=("reactivity-ontology",),
    )

    dependency_names, dependency_graphs = (
        _dependency_object_config_graphs_for_package_spec(
            package_spec=package_spec,
            local_object_config_graphs_by_package_name={},
            external_object_config_graphs_by_package_name={
                "reactivity-ontology": dependency_graph,
            },
        )
    )

    assert dependency_names == ["reactivity-ontology"]
    assert dependency_graphs == [dependency_graph]

    dependency_ref = _meta_dependency_ref_from_object_config_graph(
        package_name="reactivity-ontology",
        graph=dependency_graph,
    )
    assert dependency_ref.object_config_graph is not None
    assert dependency_ref.object_config_graph["fqn_prefix"] == "aware_reactivity"


def test_environment_package_compile_fails_closed_without_dependency_graphs() -> None:
    package_spec = SimpleNamespace(
        package_name="identity-ontology",
        dependency_package_names=("reactivity-ontology",),
    )

    with pytest.raises(
        RuntimeError,
        match="identity-ontology -> reactivity-ontology",
    ):
        _dependency_object_config_graphs_for_package_spec(
            package_spec=package_spec,
            local_object_config_graphs_by_package_name={},
            external_object_config_graphs_by_package_name={},
        )


def _test_object_config_graph(*, name: str, fqn_prefix: str) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=uuid4(),
        name=name,
        description=None,
        hash=f"{name}:hash",
        layout_hash=None,
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_identity_id=None,
    )
