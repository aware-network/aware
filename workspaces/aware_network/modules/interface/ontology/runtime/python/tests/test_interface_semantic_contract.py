from __future__ import annotations

from pathlib import Path
import tomllib
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_materialization import (
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_interface.manifest import (
    load_aware_app_source_specs,
    load_aware_app_toml_spec,
)
from aware_interface.semantic_contract import (
    AWARE_INTERFACE_SEMANTIC_CONTRACT,
    INTERFACE_MANIFEST_RESOLUTION,
    INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS,
    INTERFACE_MATERIALIZATION_RUNTIME,
    INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT,
    INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    INTERFACE_PROVIDER_OWNER,
)


_RUNTIME_CONTEXT_CONTRACT = (
    "Interface-owned Workspace semantic materialization runtime context"
)
_INTERFACE_MODULE_ROOT = Path(__file__).resolve().parents[4]
_HOME_MODULE_ROOT = (
    _INTERFACE_MODULE_ROOT.parents[2] / "aware_home" / "modules" / "home"
)


def _bootstrap_interface_module_plugin() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(_INTERFACE_MODULE_ROOT,),
    )


def test_interface_provider_covers_interface_pane_and_render_component_manifests() -> (
    None
):
    provider_role = AWARE_INTERFACE_SEMANTIC_CONTRACT.package_role_for(
        role=INTERFACE_PROVIDER_OWNER,
    )

    assert provider_role is not None
    assert provider_role.contract == "aware.semantic_provider"
    assert provider_role.owns_manifest_kinds == (
        "aware_interface_toml",
        "aware_pane_toml",
        "aware_render_component_toml",
        "aware_app_toml",
    )

    descriptor_by_manifest_kind = {
        descriptor.manifest_kind: descriptor
        for descriptor in INTERFACE_MANIFEST_RESOLUTION
    }

    assert set(descriptor_by_manifest_kind) == {
        "aware_interface_toml",
        "aware_pane_toml",
        "aware_render_component_toml",
        "aware_app_toml",
    }
    assert (
        descriptor_by_manifest_kind["aware_interface_toml"].workspace_manifest_kind
        == "interface"
    )
    assert (
        descriptor_by_manifest_kind["aware_pane_toml"].workspace_manifest_kind == "pane"
    )
    assert (
        descriptor_by_manifest_kind[
            "aware_render_component_toml"
        ].workspace_manifest_kind
        == "render_component"
    )
    assert (
        descriptor_by_manifest_kind["aware_render_component_toml"].semantic_package_kind
        == "render_component_package"
    )
    assert (
        descriptor_by_manifest_kind[
            "aware_render_component_toml"
        ].semantic_projection_name
        == "RenderComponentPackage"
    )
    app_descriptor = descriptor_by_manifest_kind["aware_app_toml"]
    assert app_descriptor.workspace_manifest_kind == "app"
    assert app_descriptor.semantic_package_kind == "app_package"
    assert app_descriptor.semantic_projection_name == "AppPackage"
    assert app_descriptor.semantic_root_kind == "app_package"
    assert app_descriptor.code_package_surface == "app"
    assert app_descriptor.loader_name == "load_aware_app_toml_spec"
    assert app_descriptor.semantic_package_metadata == {
        "package_section_name": "app",
        "dependency_attribute_name": "dependencies",
        "metadata_resolver_module": "aware_interface.manifest.app_metadata",
        "metadata_resolver_name": "resolve_aware_app_manifest_metadata",
        "workspace_materialization_runtime_index": "workspace_experience",
    }
    assert app_descriptor.workspace_materialization_branch == "semantic"
    assert app_descriptor.workspace_materialization_commit is True


def test_interface_owns_factory_and_home_owns_product_app() -> None:
    module_spec = tomllib.loads(
        (_INTERFACE_MODULE_ROOT / "aware.module.toml").read_text(encoding="utf-8")
    )

    runtime_package = next(
        package for package in module_spec["packages"] if package.get("id") == "runtime"
    )
    semantic_contract = runtime_package["semantic_contract"]
    assert "aware_app_toml" in semantic_contract["owns_manifest_kinds"]

    package_by_id = {
        package["id"]: package
        for package in module_spec["packages"]
        if isinstance(package, dict) and "id" in package
    }
    assert package_by_id["interface_app_factory_dart"] == {
        "id": "interface_app_factory_dart",
        "kind": "code",
        "manifest": "libs/app_factory/dart/aware_app_factory/pubspec.yaml",
        "visibility": "module",
    }
    assert "aware_app" not in package_by_id

    home_module_spec = tomllib.loads(
        (_HOME_MODULE_ROOT / "aware.module.toml").read_text(encoding="utf-8")
    )
    home_package_by_id = {
        package["id"]: package
        for package in home_module_spec["packages"]
        if isinstance(package, dict) and "id" in package
    }
    assert home_package_by_id["aware_home_app"] == {
        "id": "aware_home_app",
        "kind": "app",
        "manifest": "apps/aware_home/aware.app.toml",
        "visibility": "module",
    }


def test_aware_app_manifest_declares_dart_factory_control_and_linux() -> None:
    spec = load_aware_app_toml_spec(
        toml_path=_HOME_MODULE_ROOT / "apps" / "aware_home" / "aware.app.toml"
    )

    assert spec.app.package_name == "aware-home-app"
    assert spec.app.app_name == "aware-home"
    assert spec.app.fqn_prefix == "aware_home_app"
    assert spec.dart.package_path == "apps/aware_home/dart/aware_home_app"
    assert spec.dart.package_name == "aware_home_app"
    assert spec.dart.entrypoint == "lib/main.dart"
    assert spec.factory.package_name == "aware_app_factory"
    assert spec.factory.package_path is None
    assert spec.build.sources_dir == "."
    assert spec.build.include_paths == ("app.aware",)
    assert spec.control.requires_actor is True
    assert spec.control.default_screen == "control"
    assert spec.control.admitted_screen == "home"
    assert {
        (dependency.package_name, dependency.kind, dependency.role)
        for dependency in spec.dependencies
    } == {
        ("aware-control", "experience_package", "control"),
        ("home-story", "experience_package", "home"),
    }
    assert spec.launch.generated_manifest_path == "lib/aware_app_launch_manifest.g.dart"
    assert spec.launch.seed_color_value == 0xFF2CB8FF
    assert [
        (
            platform.target,
            platform.runner_path,
            platform.materializer,
            platform.binary_name,
            platform.application_id,
        )
        for platform in spec.platforms
    ] == [
        (
            "linux",
            "apps/aware_home/dart/aware_home_app/linux",
            "flutter_create",
            "aware_home_app",
            "org.aware.home",
        )
    ]
    assert [interface.package_name for interface in spec.interfaces] == [
        "aware-control-interface",
        "home-story-aware-app-interface",
    ]
    home_interface = next(
        interface
        for interface in spec.interfaces
        if interface.package_name == "home-story-aware-app-interface"
    )
    assert (
        home_interface.runtime_import
        == "package:aware_home_story_interface/_aware/interface/pane_package_registrars.dart"
    )
    assert home_interface.runtime_import_alias == "home_story_interface"


def test_aware_app_source_declares_control_and_home_screens() -> None:
    package_root = _HOME_MODULE_ROOT / "apps" / "aware_home"
    apps = load_aware_app_source_specs(
        package_root=package_root,
        source_files=(Path("app.aware"),),
    )

    assert len(apps) == 1
    app = apps[0]
    assert app.name == "aware_home"
    assert [
        (
            screen.screen_key,
            screen.projection_experience,
            screen.projection_experience_layout,
        )
        for screen in app.screens
    ] == [
        ("control", "aware_control_identity", "personal"),
        ("home", "home_story", "configuration_map"),
    ]


def test_interface_materialization_runtime_uses_ontology_package_names() -> None:
    assert len(INTERFACE_MATERIALIZATION_RUNTIME) == 1
    descriptor = INTERFACE_MATERIALIZATION_RUNTIME[0]

    assert descriptor.semantic_owner == INTERFACE_PROVIDER_OWNER
    assert (
        descriptor.runtime_ontology_package_names
        == INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert descriptor.lane_projection_name == "InterfacePackage"
    assert descriptor.required_projection_names == (
        INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    assert "AppConfig" in descriptor.required_projection_names
    assert "AppPackage" in descriptor.required_projection_names
    assert "InterfaceConfig" in descriptor.required_projection_names
    assert "InterfacePackage" in descriptor.required_projection_names
    assert "PanePackage" in descriptor.required_projection_names
    assert "PaneRenderSpec" in descriptor.required_projection_names
    assert descriptor.include_package_dependency_closure is True


def test_interface_declares_provider_owned_runtime_context() -> None:
    assert len(INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT) == 1
    descriptor = INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT[0]

    assert descriptor.semantic_owner == INTERFACE_PROVIDER_OWNER
    assert descriptor.callable_module == (
        "aware_interface.materialization.runtime_context"
    )
    assert descriptor.callable_name == (
        "build_interface_workspace_materialization_runtime_context"
    )
    assert descriptor.required is True
    assert descriptor.provider_payload == {
        "contract": _RUNTIME_CONTEXT_CONTRACT,
        "runtime_ontology_package_names": (
            INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
    }


def test_interface_runtime_context_resolves_through_registry() -> None:
    _bootstrap_interface_module_plugin()
    descriptors = AwareModulePluginRegistry.semantic_materialization_runtime_context_for_provider_key(
        provider_key="aware_interface",
        semantic_owner=INTERFACE_PROVIDER_OWNER,
    )

    assert descriptors == INTERFACE_MATERIALIZATION_RUNTIME_CONTEXT


def test_interface_module_declares_runtime_handler_import_root() -> None:
    module_spec = tomllib.loads(
        (_INTERFACE_MODULE_ROOT / "aware.module.toml").read_text(encoding="utf-8")
    )

    assert module_spec["runtime"] == {
        "project_name": "aware-interface",
        "import_root": "aware_interface",
    }


def test_interface_runtime_context_callable_resolves_through_registry() -> None:
    _bootstrap_interface_module_plugin()
    resolvers = AwareModulePluginRegistry.resolve_semantic_materialization_runtime_context_resolvers(
        provider_key="aware_interface",
        semantic_owner=INTERFACE_PROVIDER_OWNER,
    )

    assert len(resolvers) == 1
    resolver = resolvers[0]
    assert resolver.provider_key == "aware_interface"
    assert resolver.semantic_owner == INTERFACE_PROVIDER_OWNER
    assert resolver.callable_module == (
        "aware_interface.materialization.runtime_context"
    )
    assert resolver.callable_name == (
        "build_interface_workspace_materialization_runtime_context"
    )
    assert resolver.required is True


def test_interface_runtime_context_delegates_graph_body_policy_to_meta(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_interface.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    interface_manifest_path = (
        workspace_root
        / "modules"
        / "coordination"
        / "interfaces"
        / "aware_coordination"
        / "aware.interface.toml"
    )
    workspace_root.mkdir()
    repo_root.mkdir()
    captured: dict[str, object] = {}
    actor_id = uuid4()
    expected_context = SimpleNamespace(actor_id=actor_id)

    def _build_context(
        request: SemanticPackageMaterializationRuntimeContextRequest,
    ) -> object:
        captured["request"] = request
        return expected_context

    monkeypatch.setattr(
        runtime_context,
        "build_meta_workspace_materialization_runtime_context",
        _build_context,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_interface",
        semantic_owner=INTERFACE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=interface_manifest_path,
        context={
            "required_projection_names": (
                INTERFACE_MATERIALIZATION_REQUIRED_PROJECTIONS
            ),
        },
        actor_id=actor_id,
        demand="read_only_preflight",
    )

    resolved = (
        runtime_context.build_interface_workspace_materialization_runtime_context(
            request
        )
    )

    assert resolved is expected_context
    assert captured["request"] is request
    assert request.demand == "read_only_preflight"
