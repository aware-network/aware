from __future__ import annotations

from pathlib import Path
from typing import cast

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from _skill_runtime_test_paths import prepend_repo_paths, register_skill_module_plugins


def _write_skill_package(root: Path) -> Path:
    package_root = root / "skills" / "door_control"
    sources_root = package_root / "skills"
    sources_root.mkdir(parents=True, exist_ok=True)
    (package_root / "aware.skill.toml").write_text(
        """
aware_skill = 1

[skill]
package_name = "door-control-skill"
fqn_prefix = "door_control_skill"

[build]
sources_dir = "skills"
compilation_mode = "skill_ontology"

[[dependencies]]
package_name = "home-devices-api"
kind = "api_package"
""",
        encoding="utf-8",
    )
    (sources_root / "door_control.aware").write_text(
        '''\
skill door_control {
    "Reusable door control skill."

    api home_devices;

    endpoint open_door home_devices.door.open {
        "Open one door."
    }

    step 1 open_door {
        """
        Read the requested door state before acting.
        """
    }
}
''',
        encoding="utf-8",
    )
    return package_root / "aware.skill.toml"


def _prepend_skill_runtime(monkeypatch) -> None:
    prepend_repo_paths(
        monkeypatch,
        (
            "workspaces/aware_network/modules/skill/ontology/runtime/python",
            "workspaces/aware_kernel/modules/api/ontology/runtime/python",
            "workspaces/aware_kernel/modules/code/ontology/runtime/python",
            "workspaces/aware_network/modules/skill/ontology/structure/python/orm_runtime",
            "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
            "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        ),
    )


def test_skill_semantic_analysis_resolves_through_module_plugin_registry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)

    from aware_code.module_plugin_registry import AwareModulePluginRegistry
    from aware_code.semantic_capability import (
        SEMANTIC_ANALYSIS_CAPABILITY,
        SemanticAnalysisCapabilityRequest,
        SemanticAnalysisCapabilityResult,
    )

    skill_toml_path = _write_skill_package(tmp_path)
    delta = CodePackageDelta(
        package_name="door-control-skill",
        package_root="skills/door_control",
        sources_root="skills",
        manifest_relative_path="skills/door_control/aware.skill.toml",
        authority_kind="workspace_sdk",
        source_revision_id="skill-semantic-analysis-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="skills/door_control/skills/door_control.aware",
                kind=CodePackageDeltaKind.update,
                content_text=(
                    tmp_path
                    / "skills"
                    / "door_control"
                    / "skills"
                    / "door_control.aware"
                ).read_text(encoding="utf-8"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    AwareModulePluginRegistry.clear()
    try:
        register_skill_module_plugins(AwareModulePluginRegistry)
        provider = AwareModulePluginRegistry.language_service_capability_provider(
            capability=SEMANTIC_ANALYSIS_CAPABILITY,
            provider_key="aware_skill.skill_config",
        )

        assert callable(provider)
        result = cast(
            SemanticAnalysisCapabilityResult,
            provider(
                SemanticAnalysisCapabilityRequest(
                    package_root=skill_toml_path.parent,
                    source_files=(Path("skills/door_control.aware"),),
                    manifest_path=skill_toml_path,
                    workspace_root=tmp_path,
                    code_package_delta=delta,
                )
            ),
        )
    finally:
        AwareModulePluginRegistry.clear()

    assert isinstance(result, SemanticAnalysisCapabilityResult)
    assert result.capability == SEMANTIC_ANALYSIS_CAPABILITY
    assert result.provider_key == "aware_skill"
    assert result.semantic_owner == "aware_skill.skill_config"
    assert result.diagnostics == ()
    assert result.change_preview.changed_source_files == ("skills/door_control.aware",)
    assert result.change_preview.affected_semantic_keys == ("door_control",)
    assert result.change_preview.required_materializations == (
        "skill_compile_plan",
        "skill_ontology_plan",
        "skill_package",
    )
    assert tuple(
        dependency.evidence_payload()
        for dependency in result.change_preview.required_semantic_dependencies
    ) == (
        {
            "dependency_key": "aware_skill.api_package:home-devices-api",
            "provider_key": "aware_api",
            "package_name": "home-devices-api",
            "required_state": "materialized",
            "dependency_kind": "api_package",
            "source_refs": ("skills/door_control/aware.skill.toml",),
            "package_selector": {},
            "metadata": {
                "version_number": None,
                "expected_hash_sha256": None,
            },
            "semantic_owner": "aware_api.provider",
            "manifest_kind": "aware_api_toml",
            "reason": (
                "Skill package materialization requires API semantic package "
                "truth before SkillConfig API endpoints can resolve "
                "ApiCapabilityEndpoint refs."
            ),
        },
    )
    assert tuple(
        event.event_key for event in result.change_preview.semantic_events
    ) == (
        "aware_skill.skill_config.upserted",
        "aware_skill.skill_config_api.upserted",
        "aware_skill.skill_config_api_endpoint.upserted",
        "aware_skill.skill_config_step.upserted",
    )
    assert tuple(
        delta.semantic_key for delta in result.change_preview.semantic_deltas
    ) == (
        "skill:door_control",
        "skill:door_control/api:home_devices",
        "skill:door_control/endpoint:open_door",
        "skill:door_control/step:1",
    )
    assert result.change_preview.metadata == {
        "affected_api_refs": ("home_devices",),
        "affected_endpoint_names": ("open_door",),
        "skill_count": 1,
        "api_count": 1,
        "endpoint_count": 1,
        "step_count": 1,
    }
    assert result.code_package_delta is delta


def test_skill_semantic_package_and_scope_register_from_runtime_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepend_skill_runtime(monkeypatch)

    from aware_code.module_plugin_registry import AwareModulePluginRegistry
    from aware_code.package.schemas import CodePackageInfo
    from aware_code.semantic_package.registry import SemanticPackageRegistry
    from aware_code.semantic_scope.registry import SemanticScopeRegistry

    skill_toml_path = _write_skill_package(tmp_path)
    code_package = CodePackageInfo(
        name="door-control-skill",
        root_path=Path("skills/door_control"),
        manifest_path=Path("skills/door_control/aware.skill.toml"),
        language=CodeLanguage.aware,
        metadata={
            "manifest_kind": "aware_skill_toml",
            "package_kind": "skill",
            "fqn_prefix": "door_control_skill",
        },
    )

    AwareModulePluginRegistry.clear()
    SemanticPackageRegistry.clear()
    SemanticScopeRegistry.clear()
    try:
        register_skill_module_plugins(AwareModulePluginRegistry)
        SemanticPackageRegistry.ensure_builtin_providers_registered()
        SemanticScopeRegistry.ensure_builtin_providers_registered()

        assert "aware_skill" in SemanticPackageRegistry.get_provider_keys()
        assert "aware_skill" in SemanticScopeRegistry.get_provider_keys()

        descriptors = SemanticPackageRegistry.resolve(code_package)
        assert len(descriptors) == 1
        descriptor = descriptors[0]
        assert descriptor.provider_key == "aware_skill"
        assert descriptor.family == "skill"
        assert descriptor.semantic_kind == "skill_package"
        assert descriptor.package_name == "door-control-skill"
        assert descriptor.metadata["semantic_projection_name"] == "SkillPackage"
        assert descriptor.metadata["semantic_root_kind"] == "skill_config"
        assert descriptor.semantic_scope_keys == ("aware_skill.semantic_scope",)
        assert {
            (item.capability, item.semantic_owner)
            for item in descriptor.capability_participation
        } >= {
            ("semantic_analysis", "aware_skill.skill_config"),
            ("materialize", "aware_skill.provider"),
        }

        scopes = SemanticScopeRegistry.resolve(
            code_package,
            workspace_root=tmp_path,
            scope_keys=("aware_skill.semantic_scope",),
        )
        assert len(scopes) == 1
        scope = scopes[0]
        assert scope.scope_key == "aware_skill.semantic_scope"
        assert scope.provider_key == "aware_skill"
        assert scope.payload["skillPackageName"] == "door-control-skill"
        assert scope.payload["manifestRelativePath"] == (
            "skills/door_control/aware.skill.toml"
        )
        assert scope.payload["declaredApiPackageNames"] == ["home-devices-api"]
        assert len(scope.materialization_dependencies) == 1
        dependency = scope.materialization_dependencies[0]
        assert dependency.package_name == "home-devices-api"
        assert dependency.provider_key == "aware_api"
        assert dependency.semantic_owner == "aware_api.provider"
        assert dependency.manifest_kind == "aware_api_toml"
        assert dependency.dependency_kind == "api_package"
        assert dependency.required_state == "materialized"
        assert dependency.semantic_package_family == "api"
        assert dependency.semantic_package_kind == "api_package"
        assert dependency.semantic_package_name == "home-devices-api"
        assert dependency.source_refs == ("skills/door_control/aware.skill.toml",)
        assert skill_toml_path.is_file()
    finally:
        AwareModulePluginRegistry.clear()
        SemanticPackageRegistry.clear()
        SemanticScopeRegistry.clear()
