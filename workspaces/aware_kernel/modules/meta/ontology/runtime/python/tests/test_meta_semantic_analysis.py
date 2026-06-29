from __future__ import annotations

import sys
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
from aware_meta.semantic_analysis import (
    MetaOcgSemanticAnalysisResult,
    analyze_meta_ocg_code_package_delta,
    analyze_meta_ocg_semantic_capability,
    analyze_meta_ocg_sources,
)

_DEFAULT_NAMESPACE_LINES: tuple[str, ...] = ()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_aware_toml(
    root: Path,
    *,
    build_namespace_lines: tuple[str, ...] | None = _DEFAULT_NAMESPACE_LINES,
    dependency_package_names: tuple[str, ...] = (),
) -> Path:
    toml_path = root / "aware.toml"
    dependency_lines: list[str] = []
    for package_name in dependency_package_names:
        dependency_lines.extend(
            [
                "",
                "[[dependencies]]",
                f'package_name = "{package_name}"',
            ]
        )
    _write(
        toml_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                *(build_namespace_lines or ()),
                *dependency_lines,
            ]
        ),
    )
    return toml_path


def _class_source(class_name: str, attr_name: str) -> str:
    return "\n".join(
        [
            f"class {class_name} {{",
            f"    {attr_name} String",
            "}",
            "",
        ]
    )


def _class_with_relationship_source(
    class_name: str,
    relationship_name: str,
    target_class_name: str,
) -> str:
    return "\n".join(
        [
            f"class {class_name} {{",
            f"    {relationship_name} {target_class_name}[]",
            "}",
            "",
        ]
    )


def _code_package_delta_source() -> str:
    return "\n".join(
        [
            "class CodePackageDeltaPath : inline_value {",
            "    relative_path String",
            "}",
            "",
            "class CodePackageDelta : inline_value {",
            "    paths code.CodePackageDeltaPath[] = []",
            "}",
            "",
        ]
    )


def _code_semantic_contract_source() -> str:
    return "\n".join(
        [
            "class CodeSemanticContract : inline_value {",
            "    provider_key String",
            "    package_delta code.CodePackageDelta?",
            "}",
            "",
        ]
    )


def test_analyze_meta_ocg_sources_returns_ocg_semantic_preview(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_source("Room", "name"),
    )

    result = analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(Path("aware/home/room.aware"),),
        manifest_path=manifest_path,
    )

    assert isinstance(result, MetaOcgSemanticAnalysisResult)
    assert result.schema_version == 1
    assert result.source_files == ("home/room.aware",)
    assert result.diagnostics == ()
    assert result.object_config_graph is not None
    assert result.change_preview.changed_source_files == ("home/room.aware",)
    assert result.change_preview.affected_object_config_graph_keys == (
        "ocg:aware_demo",
        "ocg_package:demo-ontology",
    )
    assert result.change_preview.class_count == 1
    assert result.change_preview.node_count >= 1
    assert result.change_preview.required_materializations == (
        "meta_object_config_graph_plan",
        "meta_object_config_graph_package_plan",
    )
    assert tuple(
        delta.subject_type for delta in result.change_preview.semantic_deltas[:2]
    ) == (
        "aware_meta.ObjectConfigGraphPackage",
        "aware_meta.ObjectConfigGraph",
    )
    assert any(
        delta.subject_type == "aware_meta.ObjectConfigGraphNode"
        and (delta.after_payload or {}).get("entity_name") == "Room"
        for delta in result.change_preview.semantic_deltas
    )
    assert tuple(
        event.event_key for event in result.change_preview.semantic_events[:2]
    ) == (
        "aware_meta.object_config_graph_package.upserted",
        "aware_meta.object_config_graph.upserted",
    )


def test_analyze_meta_ocg_semantic_capability_reports_aware_toml_dependencies(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(
        tmp_path,
        dependency_package_names=("environment-api",),
    )
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_source("Room", "name"),
    )

    result = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("aware/home/room.aware"),),
            manifest_path=manifest_path,
        )
    )

    assert [
        dependency.evidence_payload()
        for dependency in result.change_preview.required_semantic_dependencies
    ] == [
        {
            "dependency_key": (
                "aware_meta.object_config_graph_package.dependency:"
                "demo-ontology:environment-api"
            ),
            "provider_key": "aware_meta",
            "package_name": "environment-api",
            "required_state": "materialized",
            "dependency_kind": "semantic_package",
            "source_refs": ("aware.toml",),
            "package_selector": {},
            "metadata": {
                "source_package_name": "demo-ontology",
                "source_fqn_prefix": "aware_demo",
                "dependency_package_name": "environment-api",
            },
            "semantic_owner": "aware_meta.object_config_graph",
            "manifest_kind": "aware_toml",
            "reason": "aware_toml_dependency",
        }
    ]


def test_analyze_meta_ocg_semantic_capability_reports_dependencies_on_error(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(
        tmp_path,
        dependency_package_names=("environment-api",),
    )
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        "\n".join(
            [
                "class Room {",
                "    environment_config aware_environment_api.default.environment.EnvironmentConfig?",
                "}",
                "",
            ]
        ),
    )

    result = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("aware/home/room.aware"),),
            manifest_path=manifest_path,
        )
    )

    assert result.diagnostics
    assert [
        dependency.package_name
        for dependency in result.change_preview.required_semantic_dependencies
    ] == ["environment-api"]


def test_analyze_meta_ocg_sources_derives_namespace_without_namespace_spec(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path, build_namespace_lines=())
    _write(
        tmp_path / "aware" / "code" / "features" / "semantic_contract.aware",
        _class_source("CodeSemanticContract", "provider_key"),
    )

    result = analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(Path("aware/code/features/semantic_contract.aware"),),
        manifest_path=manifest_path,
    )

    assert "ocg:aware_demo/node:aware_demo.code.features.CodeSemanticContract" in (
        result.change_preview.affected_node_keys
    )


def test_analyze_meta_ocg_sources_uses_namespace_path_mapping(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(
        tmp_path,
        build_namespace_lines=(
            "[build.namespace]",
            '"code/**/*.aware" = "code"',
            "",
        ),
    )
    _write(
        tmp_path / "aware" / "code" / "features" / "package_delta.aware",
        _code_package_delta_source(),
    )
    _write(
        tmp_path / "aware" / "code" / "features" / "semantic_contract.aware",
        _code_semantic_contract_source(),
    )

    result = analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(
            Path("aware/code/features/package_delta.aware"),
            Path("aware/code/features/semantic_contract.aware"),
        ),
        manifest_path=manifest_path,
    )

    assert result.diagnostics == ()
    assert {
        "ocg:aware_demo/node:aware_demo.code.CodePackageDelta",
        "ocg:aware_demo/node:aware_demo.code.CodePackageDeltaPath",
        "ocg:aware_demo/node:aware_demo.code.CodeSemanticContract",
    }.issubset(set(result.change_preview.affected_node_keys))
    assert not any(
        ".code.features." in node_key
        for node_key in result.change_preview.affected_node_keys
    )


def test_analyze_meta_ocg_sources_matches_root_namespace_without_nested_overlap(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "home_projection.aware",
        _class_source("HomeProjectionConfig", "name"),
    )
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_source("Room", "name"),
    )

    result = analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(
            Path("aware/home_projection.aware"),
            Path("aware/home/room.aware"),
        ),
        manifest_path=manifest_path,
    )

    assert result.diagnostics == ()
    assert {
        "ocg:aware_demo/node:aware_demo.HomeProjectionConfig",
        "ocg:aware_demo/node:aware_demo.home.Room",
    }.issubset(set(result.change_preview.affected_node_keys))


def test_analyze_meta_ocg_sources_derives_deep_layout_namespace(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "code" / "features" / "semantic_contract.aware",
        _class_source("CodeSemanticContract", "provider_key"),
    )

    result = analyze_meta_ocg_sources(
        package_root=tmp_path,
        source_files=(Path("aware/code/features/semantic_contract.aware"),),
        manifest_path=manifest_path,
    )

    assert result.diagnostics == ()
    assert "ocg:aware_demo/node:aware_demo.code.features.CodeSemanticContract" in (
        result.change_preview.affected_node_keys
    )


def test_analyze_meta_ocg_semantic_capability_expands_package_context_for_scoped_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_with_relationship_source("Room", "doors", "Door"),
    )
    _write(
        tmp_path / "aware" / "home" / "door.aware",
        _class_source("Door", "label"),
    )
    delta = CodePackageDelta(
        package_name="demo-ontology",
        package_root=".",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        authority_kind="workspace_sdk",
        source_revision_id="meta-semantic-capability-scoped-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="home/room.aware",
                kind=CodePackageDeltaKind.update,
                content_text=_class_with_relationship_source("Room", "doors", "Door"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("aware/home/room.aware"),),
            manifest_path=manifest_path,
            code_package_delta=delta,
        )
    )

    assert result.diagnostics == ()
    assert set(result.source_files) == {
        "home/door.aware",
        "home/room.aware",
    }
    assert result.change_preview.changed_source_files == ("home/room.aware",)
    assert result.change_preview.metadata["class_count"] == 2
    assert result.change_preview.metadata["relationship_count"] >= 1


def test_analyze_meta_ocg_code_package_delta_filters_changed_source(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_source("Room", "name"),
    )
    _write(
        tmp_path / "aware" / "device" / "sensor.aware",
        _class_source("Sensor", "label"),
    )
    delta = CodePackageDelta(
        package_name="demo-ontology",
        package_root=".",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        authority_kind="workspace_sdk",
        source_revision_id="meta-semantic-analysis-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="device/sensor.aware",
                kind=CodePackageDeltaKind.update,
                content_text=_class_source("Sensor", "label"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_meta_ocg_code_package_delta(
        package_root=tmp_path,
        source_files=(
            Path("aware/home/room.aware"),
            Path("aware/device/sensor.aware"),
        ),
        manifest_path=manifest_path,
        code_package_delta=delta,
    )

    assert result.code_package_delta is delta
    assert result.change_preview.changed_source_files == ("device/sensor.aware",)
    node_deltas = tuple(
        delta
        for delta in result.change_preview.semantic_deltas
        if delta.subject_type == "aware_meta.ObjectConfigGraphNode"
    )
    assert node_deltas
    assert {
        (delta.after_payload or {}).get("entity_name") for delta in node_deltas
    } == {"Sensor"}
    assert all(delta.source_refs == ("device/sensor.aware",) for delta in node_deltas)


def test_analyze_meta_ocg_semantic_capability_returns_code_capability_result(
    tmp_path: Path,
) -> None:
    manifest_path = _write_aware_toml(tmp_path)
    _write(
        tmp_path / "aware" / "home" / "room.aware",
        _class_source("Room", "name"),
    )
    delta = CodePackageDelta(
        package_name="demo-ontology",
        package_root=".",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        authority_kind="workspace_sdk",
        source_revision_id="meta-semantic-capability-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="home/room.aware",
                kind=CodePackageDeltaKind.update,
                content_text=_class_source("Room", "name"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("aware/home/room.aware"),),
            manifest_path=manifest_path,
            code_package_delta=delta,
        )
    )

    assert result.capability == SEMANTIC_ANALYSIS_CAPABILITY
    assert result.provider_key == "aware_meta"
    assert result.semantic_owner == "aware_meta.object_config_graph"
    assert result.diagnostics == ()
    assert result.change_preview.changed_source_files == ("home/room.aware",)
    assert result.change_preview.affected_semantic_keys == (
        "ocg:aware_demo",
        "ocg_package:demo-ontology",
    )
    assert result.change_preview.required_materializations == (
        "meta_object_config_graph_plan",
        "meta_object_config_graph_package_plan",
    )
    assert result.change_preview.metadata["class_count"] == 1
    assert (
        result.change_preview.metadata["function_call_policy"]
        == "pending_runtime_ocg_node_mutation_functions"
    )
    assert result.change_preview.metadata["semantic_truth_graph"] == "runtime_ocg"
    assert result.change_preview.metadata["source_graph_role"] == "compiler_ir"
    assert result.change_preview.metadata["runtime_graph_role"] == "runtime_ocg"
    assert result.code_package_delta is delta


def test_analyze_home_story_ontology_package_without_structure_materializer() -> None:
    package_root = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "home_story_ontology"
    )
    source_files = tuple(
        sorted(
            path.relative_to(package_root)
            for path in (package_root / "aware").rglob("*.aware")
        )
    )

    before_imports = set(sys.modules)
    result = analyze_meta_ocg_sources(
        package_root=package_root,
        source_files=source_files,
        manifest_path=package_root / "aware.toml",
    )
    newly_imported_modules = set(sys.modules) - before_imports

    assert result.diagnostics == ()
    assert result.source_object_config_graph is not None
    assert result.object_config_graph is not None
    assert result.runtime_derivation is not None
    assert result.object_config_graph is result.runtime_derivation.runtime_graph
    assert result.source_object_config_graph is result.runtime_derivation.source_graph
    assert result.source_object_config_graph.hash != result.object_config_graph.hash
    assert result.change_preview.changed_source_files == (
        "home/door.aware",
        "home/home.aware",
        "home/tv.aware",
        "home/tv_channel.aware",
        "home_projection.aware",
    )
    assert result.change_preview.affected_object_config_graph_keys == (
        "ocg:aware_home",
        "ocg_package:home-ontology",
    )
    assert result.change_preview.class_count == 4
    assert result.change_preview.relationship_count == 4
    assert result.change_preview.required_materializations == (
        "meta_object_config_graph_plan",
        "meta_object_config_graph_package_plan",
    )
    assert "ocg:aware_home/node:aware_home.home.Home" in (
        result.change_preview.affected_node_keys
    )
    forbidden_materializer_prefixes = (
        "aware_environment_artifacts",
        "aware_structure.materialization",
        "aware_structure.repository",
        "aware_structure.setup_language_plugins",
    )
    assert not any(
        module_name.startswith(forbidden_materializer_prefixes)
        for module_name in newly_imported_modules
    )
