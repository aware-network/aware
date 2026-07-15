from __future__ import annotations

from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_capability import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SemanticAnalysisCapabilityRequest,
)
from aware_experience.semantic_analysis import (
    analyze_experience_code_package_delta,
    analyze_experience_semantic_capability,
    analyze_experience_sources,
)
from ._experience_runtime_test_paths import EXPERIENCE_MODULE_ROOT


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _experience_source() -> str:
    return "\n".join(
        [
            "experience home_story on aware_home.home.Home {",
            "    observable overview {",
            "        view home default api_view root.home {",
            '            """Global home state view."""',
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def _delta(*, source: str) -> CodePackageDelta:
    return CodePackageDelta(
        package_name="home-story",
        package_root=".",
        sources_root=".",
        manifest_relative_path="aware.experience.toml",
        authority_kind="workspace_sdk",
        source_revision_id="home-story-experience-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="experiences.aware",
                kind=CodePackageDeltaKind.update,
                content_text=source,
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )


def _bootstrap_experience_module_plugin() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(EXPERIENCE_MODULE_ROOT,),
    )


def test_analyze_experience_sources_returns_ocg_dependency_preview(
    tmp_path: Path,
) -> None:
    source = _experience_source()
    _write(tmp_path / "experiences.aware", source)

    result = analyze_experience_sources(
        package_root=tmp_path,
        source_files=(Path("experiences.aware"),),
    )

    assert result.schema_version == 1
    assert result.source_files == ("experiences.aware",)
    assert result.diagnostics == ()
    assert result.change_preview.affected_experience_names == ("home_story",)
    assert result.change_preview.required_materializations == (
        "experience_compile_plan",
        "experience_package_ontology_plan",
        "projection_experience_ontology_plan",
    )
    dependencies = result.change_preview.required_semantic_dependencies
    assert len(dependencies) == 1
    dependency = dependencies[0]
    assert dependency.dependency_kind == "object_config_graph"
    assert dependency.provider_key == "aware_meta"
    assert dependency.package_name == "aware_home"
    assert dependency.required_state == "materialized"
    assert dependency.semantic_owner == "aware_meta.provider"
    assert dependency.manifest_kind == "aware_toml"
    assert dependency.package_selector == {
        "semantic_package_metadata": {"fqn_prefix": "aware_home"}
    }
    assert dependency.metadata == {
        "projection_key": "home",
        "projection_ref": "aware_home.home.Home",
        "experience_name": "home_story",
    }


def test_analyze_experience_code_package_delta_reports_changed_sources(
    tmp_path: Path,
) -> None:
    source = _experience_source()
    _write(tmp_path / "experiences.aware", source)

    result = analyze_experience_code_package_delta(
        package_root=tmp_path,
        source_files=(Path("experiences.aware"),),
        code_package_delta=_delta(source=source),
    )

    assert result.change_preview.changed_source_files == ("experiences.aware",)
    assert result.change_preview.affected_experience_names == ("home_story",)
    assert result.code_package_delta is not None


def test_analyze_experience_semantic_capability_returns_code_capability_result(
    tmp_path: Path,
) -> None:
    source = _experience_source()
    _write(tmp_path / "experiences.aware", source)

    result = analyze_experience_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("experiences.aware"),),
            code_package_delta=_delta(source=source),
            manifest_path=tmp_path / "aware.experience.toml",
            workspace_root=tmp_path,
        )
    )

    assert result.capability == SEMANTIC_ANALYSIS_CAPABILITY
    assert result.provider_key == "aware_experience"
    assert result.semantic_owner == "aware_experience.provider"
    assert result.diagnostics == ()
    assert result.change_preview.affected_semantic_keys == ("home_story",)
    dependency = result.change_preview.required_semantic_dependencies[0]
    assert dependency.provider_key == "aware_meta"
    assert dependency.manifest_kind == "aware_toml"
    assert dependency.package_selector == {
        "semantic_package_metadata": {"fqn_prefix": "aware_home"}
    }
    assert result.change_preview.metadata["affected_experience_names"] == (
        "home_story",
    )
    assert result.code_package_delta is not None


def test_experience_semantic_analysis_provider_resolves_from_contract() -> None:
    _bootstrap_experience_module_plugin()
    try:
        providers = AwareModulePluginRegistry.resolve_language_service_capability_execution_providers(
            capability=SEMANTIC_ANALYSIS_CAPABILITY,
            module_provider_keys=("aware_experience",),
        )
    finally:
        AwareModulePluginRegistry.clear()

    assert tuple(provider.descriptor.provider_key for provider in providers) == (
        "aware_experience.provider",
    )
    assert providers[0].provider is not None
