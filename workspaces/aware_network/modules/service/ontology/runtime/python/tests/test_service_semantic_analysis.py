from __future__ import annotations

from pathlib import Path

from aware_code.semantic_capability import (
    SEMANTIC_ANALYSIS_CAPABILITY,
    SemanticAnalysisCapabilityRequest,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_service_runtime.semantic_analysis import (
    analyze_service_code_package_delta,
    analyze_service_semantic_capability,
    analyze_service_sources,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _service_source(*, service_name: str = "home_devices") -> str:
    return "\n".join(
        [
            f"service {service_name} {{",
            "    api home_devices;",
            "    experience home_story;",
            "",
            "    operation open_door {",
            "        endpoint home_devices.open_door.open_door;",
            "        settlement reserve_and_finalize;",
            "        price {",
            "            coin USD;",
            "            type fixed;",
            "            fixed_amount 2.50;",
            '            effective_from "2026-04-21T00:00:00Z";',
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def _delta(*, source: str) -> CodePackageDelta:
    return CodePackageDelta(
        package_name="aware-home-devices-service",
        package_root=".",
        sources_root="bindings",
        manifest_relative_path="aware.service.toml",
        authority_kind="workspace_sdk",
        source_revision_id="home-story-service-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="bindings/home.services.aware",
                kind=CodePackageDeltaKind.update,
                content_text=source,
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )


def _service_manifest() -> str:
    return "\n".join(
        [
            "aware_service = 1",
            "",
            "[service]",
            'package_name = "aware-home-devices-service"',
            'fqn_prefix = "aware_home_devices_service"',
            "version_number = 1",
            "",
            "[build]",
            'sources_dir = "bindings"',
            'include_paths = ["**/*.aware"]',
            "exclude_paths = []",
            "force_fresh_scan = true",
            'compilation_mode = "service_ontology"',
            "",
            "[host]",
            'service_surface = "service"',
            'activation_mode = "materialize_and_load_committed"',
            "materialize_on_start = true",
            "",
            "[[dependencies]]",
            'package_name = "home-devices-api"',
            "version_number = 1",
            'kind = "api_service_protocol"',
            "",
        ]
    )


def test_analyze_service_sources_returns_reusable_semantic_meaning(
    tmp_path: Path,
) -> None:
    source = _service_source()
    _write(tmp_path / "bindings" / "home.services.aware", source)

    result = analyze_service_sources(
        package_root=tmp_path,
        source_files=(Path("bindings/home.services.aware"),),
    )

    assert result.schema_version == 1
    assert result.source_files == ("bindings/home.services.aware",)
    assert result.diagnostics == ()
    assert len(result.service_ownership) == 1
    assert result.service_ownership[0].name == "home_devices"
    assert result.change_preview.service_count == 1
    assert result.change_preview.operation_count == 1
    assert result.change_preview.endpoint_count == 1
    assert result.change_preview.required_materializations == (
        "service_compile_plan",
        "service_ontology_plan",
    )


def test_analyze_service_code_package_delta_reports_change_preview(
    tmp_path: Path,
) -> None:
    source = _service_source()
    _write(tmp_path / "bindings" / "home.services.aware", source)

    result = analyze_service_code_package_delta(
        package_root=tmp_path,
        source_files=(Path("bindings/home.services.aware"),),
        code_package_delta=_delta(source=source),
    )

    assert result.change_preview.changed_source_files == (
        "bindings/home.services.aware",
    )
    assert result.change_preview.affected_service_names == ("home_devices",)
    assert result.change_preview.affected_operation_names == ("open_door",)
    assert tuple(
        event.event_key for event in result.change_preview.semantic_events
    ) == (
        "aware_service.service_config.upserted",
        "aware_service.service_config_api.upserted",
        "aware_service.service_config_experience.upserted",
        "aware_service.service_operation_config.upserted",
        "aware_service.service_operation_config_api_endpoint.upserted",
    )


def test_analyze_service_semantic_capability_returns_code_capability_result(
    tmp_path: Path,
) -> None:
    source = _service_source()
    _write(tmp_path / "bindings" / "home.services.aware", source)
    _write(tmp_path / "aware.service.toml", _service_manifest())

    result = analyze_service_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("bindings/home.services.aware"),),
            code_package_delta=_delta(source=source),
            manifest_path=tmp_path / "aware.service.toml",
            workspace_root=tmp_path,
        )
    )

    assert result.capability == SEMANTIC_ANALYSIS_CAPABILITY
    assert result.provider_key == "aware_service"
    assert result.semantic_owner == "aware_service.service"
    assert result.diagnostics == ()
    assert result.change_preview.changed_source_files == (
        "bindings/home.services.aware",
    )
    assert result.change_preview.affected_semantic_keys == ("home_devices",)
    dependencies_by_kind = {
        dependency.dependency_kind: dependency
        for dependency in result.change_preview.required_semantic_dependencies
    }
    api_dependency = dependencies_by_kind["api_service_protocol"]
    assert api_dependency.package_name == "home-devices-api"
    assert api_dependency.provider_key == "aware_api"
    assert api_dependency.required_state == "materialized"
    assert api_dependency.manifest_kind == "aware_api_toml"
    experience_dependency = dependencies_by_kind["ProjectionExperience"]
    assert experience_dependency.package_name == "home_story"
    assert experience_dependency.provider_key == "aware_experience"
    assert experience_dependency.required_state == "materialized"
    assert experience_dependency.manifest_kind == "aware_experience_toml"
    assert experience_dependency.package_selector == {
        "semantic_package_metadata": {"fqn_prefix": "home_story"}
    }
    assert result.change_preview.metadata["affected_operation_names"] == ("open_door",)
    assert result.code_package_delta is not None
