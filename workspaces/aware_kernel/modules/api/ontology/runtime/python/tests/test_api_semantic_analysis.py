from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import pytest
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_API_RUNTIME_ROOT_STR = str(_REPO_ROOT / "modules" / "api" / "runtime")
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

from aware_api_runtime.ir import build_api_compile_plan  # noqa: E402
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.source.semantic_analysis import (  # noqa: E402
    APISemanticAnalysisResult,
    analyze_api_code_package_delta,
    analyze_api_semantic_capability,
    analyze_api_sources,
)
from aware_api_runtime.semantic_function_refs import (  # noqa: E402
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
)
from aware_code.semantic_capability import (  # noqa: E402
    SEMANTIC_ANALYSIS_CAPABILITY,
    SemanticAnalysisCapabilityRequest,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _api_source(api_name: str, capability_name: str, request_name: str) -> str:
    return "\n".join(
        [
            f"api {api_name} {{",
            f"    capability {capability_name} {{",
            f"        endpoint {capability_name} aware_demo_api.{request_name} {{",
            "            response aware_demo_api.DemoResponse;",
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def _write_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _write(
        toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "demo-api"',
                'fqn_prefix = "aware_demo_api"',
                "",
                "[build]",
                'sources_dir = "apis"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        ),
    )
    return toml_path


def _write_dependent_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _write(
        toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-devices-api"',
                'fqn_prefix = "aware_home_devices_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
    )
    return toml_path


def _write_home_api_dependency(root: Path) -> None:
    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    _write(
        ontology_root / "aware.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_home"',
                "",
            ]
        ),
    )
    _write(
        ontology_root / "aware" / "home" / "door.aware",
        "\n".join(
            [
                "class Door {",
                "    label String",
                "}",
                "",
            ]
        ),
    )

    package_root = root / "apis" / "types" / "home"
    _write(
        package_root / "aware.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-api"',
                'fqn_prefix = "aware_home_api"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_home_api"',
                "",
            ]
        ),
    )
    _write(
        package_root / "aware" / "bindings.aware",
        "\n".join(
            [
                "binding aware_home_api aware_home {",
                "    map door_by_label door.DoorByLabel home.Door.label {",
                "        template {",
                '            "{door_label}"',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    _write(
        package_root / "aware" / "door" / "endpoints.aware",
        "\n".join(
            [
                "class DoorByLabel {",
                "    label String",
                "}",
                "",
            ]
        ),
    )


def test_analyze_api_sources_returns_reusable_semantic_meaning(tmp_path: Path) -> None:
    _write(
        tmp_path / "apis" / "demo.aware",
        _api_source("demo", "read_demo", "ReadDemoRequest"),
    )

    result = analyze_api_sources(
        package_root=tmp_path,
        source_files=(Path("apis/demo.aware"),),
        binding_truth_by_ref={},
    )

    assert result.schema_version == 1
    assert result.source_files == ("apis/demo.aware",)
    assert result.diagnostics == ()
    assert len(result.api_ownership) == 1
    assert result.api_ownership[0].name == "demo"
    assert result.change_preview.api_count == 1
    assert result.change_preview.capability_count == 1
    assert result.change_preview.endpoint_count == 1
    assert result.change_preview.required_materializations == (
        "api_compile_plan",
        "api_ontology_plan",
    )


def test_analyze_api_code_package_delta_reports_change_preview(tmp_path: Path) -> None:
    _write(
        tmp_path / "apis" / "beta.aware",
        _api_source("beta", "read_beta", "ReadBetaRequest"),
    )
    delta = CodePackageDelta(
        package_name="demo-api",
        package_root=".",
        sources_root="apis",
        manifest_relative_path="aware.api.toml",
        authority_kind="workspace_sdk",
        source_revision_id="remote-change-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="apis/beta.aware",
                kind=CodePackageDeltaKind.update,
                content_text=_api_source("beta", "read_beta", "ReadBetaRequest"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_api_code_package_delta(
        package_root=tmp_path,
        source_files=(Path("apis/alpha.aware"), Path("apis/beta.aware")),
        code_package_delta=delta,
        binding_truth_by_ref={},
    )

    assert result.code_package_delta is delta
    assert result.change_preview.changed_source_files == ("apis/beta.aware",)
    assert result.change_preview.affected_api_names == ("beta",)
    assert result.change_preview.affected_capability_names == ("read_beta",)
    assert tuple(
        event.event_key for event in result.change_preview.semantic_events
    ) == (
        "aware_api.api.upserted",
        "aware_api.api_capability.upserted",
        "aware_api.api_capability_endpoint.upserted",
    )
    assert tuple(
        delta.semantic_key for delta in result.change_preview.semantic_deltas
    ) == (
        "api:beta",
        "api:beta/capability:read_beta",
        "api:beta/capability:read_beta/endpoint:read_beta",
    )
    endpoint_event = result.change_preview.semantic_events[-1]
    assert "function_call" not in endpoint_event.evidence_payload()
    assert endpoint_event.delta_keys == (
        "aware_api.api_capability_endpoint.upsert:"
        "api:beta/capability:read_beta/endpoint:read_beta",
    )
    endpoint_binding = result.change_preview.action_bindings[-1]
    assert endpoint_binding.event_key == "aware_api.api_capability_endpoint.upserted"
    assert endpoint_binding.function_call_binding is not None
    assert endpoint_binding.function_call_binding.argument_ref_bindings == {
        "request_class_config_id": "payload.request_class_ref",
    }
    assert result.change_preview.api_count == 1


def test_analyze_api_semantic_capability_returns_code_capability_result(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "apis" / "demo.aware",
        _api_source("demo", "read_demo", "ReadDemoRequest"),
    )
    delta = CodePackageDelta(
        package_name="demo-api",
        package_root=".",
        sources_root="apis",
        manifest_relative_path="aware.api.toml",
        authority_kind="workspace_sdk",
        source_revision_id="semantic-capability-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="apis/demo.aware",
                kind=CodePackageDeltaKind.update,
                content_text=_api_source("demo", "read_demo", "ReadDemoRequest"),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_api_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("apis/demo.aware"),),
            code_package_delta=delta,
        )
    )

    assert result.capability == SEMANTIC_ANALYSIS_CAPABILITY
    assert result.provider_key == "aware_api"
    assert result.semantic_owner == "aware_api.api"
    assert result.diagnostics == ()
    assert result.change_preview.changed_source_files == ("apis/demo.aware",)
    assert result.change_preview.affected_semantic_keys == ("demo",)
    endpoint_binding = result.change_preview.action_bindings[-1]
    assert endpoint_binding.function_call_binding is not None
    assert endpoint_binding.function_call_binding.evidence_payload() == {
        "binding_key": (
            "aware_api.api_capability_endpoint.upserted."
            "api_capability_create_endpoint"
        ),
        "event_key": "aware_api.api_capability_endpoint.upserted",
        "function_ref": API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
        "receiver_semantic_key_template": "payload.capability_semantic_key",
        "argument_bindings": {
            "name": "payload.name",
            "description": "payload.description",
        },
        "argument_ref_bindings": {
            "request_class_config_id": "payload.request_class_ref",
        },
        "constant_arguments": {},
        "result_semantic_key_template": "semantic_key",
        "metadata": {"argument_ref_resolution": "class_config_id"},
    }
    assert result.change_preview.metadata["affected_capability_names"] == ("read_demo",)
    assert result.code_package_delta is delta


def test_analyze_api_semantic_capability_blocks_manifest_only_delta(
    tmp_path: Path,
) -> None:
    manifest_path = _write_api_toml(tmp_path)
    _write(
        tmp_path / "apis" / "demo.aware",
        _api_source("demo", "read_demo", "ReadDemoRequest"),
    )
    generated_binding = tmp_path / "python" / "aware_demo_api" / "_bindings.py"
    _write(generated_binding, "api s {}\n")
    delta = CodePackageDelta(
        package_name="demo-api",
        package_root=".",
        sources_root="apis",
        manifest_relative_path="aware.api.toml",
        authority_kind="workspace_sdk",
        source_revision_id="manifest-change-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="aware.api.toml",
                kind=CodePackageDeltaKind.update,
                content_text=manifest_path.read_text(encoding="utf-8"),
                language=CodeLanguage.aware,
                is_structural=False,
            )
        ],
    )

    result = analyze_api_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(
                Path("aware.api.toml"),
                Path("python/aware_demo_api/_bindings.py"),
            ),
            manifest_path=manifest_path,
            workspace_root=tmp_path,
            code_package_delta=delta,
        )
    )

    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        "aware_api.semantic_analysis.invalid_delta_source",
    )
    assert "content-backed authored Aware source upsert" in (
        result.diagnostics[0].message
    )
    assert result.source_files == ()
    assert result.change_preview.changed_source_files == ()
    assert result.change_preview.affected_semantic_keys == ()


def test_analyze_api_semantic_capability_resolves_dependency_binding_truth(
    tmp_path: Path,
) -> None:
    _write_dependent_api_toml(tmp_path)
    _write_home_api_dependency(tmp_path)
    source = "\n".join(
        [
            "api home_devices {",
            "    capability open_door {",
            "        endpoint open_door aware_home_api.door.DoorByLabel {",
            '            """Open a door by label."""',
            "        }",
            "    }",
            "",
            "    graph aware_home {",
            "        projection aware_home.Home {",
            "        }",
            "    }",
            "}",
            "",
        ]
    )
    _write(tmp_path / "bindings" / "home_devices.apis.aware", source)
    delta = CodePackageDelta(
        package_name="home-devices-api",
        package_root=".",
        sources_root="bindings",
        manifest_relative_path="aware.api.toml",
        authority_kind="workspace_sdk",
        source_revision_id="home-story-demo",
        paths=[
            CodePackageDeltaPath(
                relative_path="bindings/home_devices.apis.aware",
                kind=CodePackageDeltaKind.update,
                content_text=source,
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )

    result = analyze_api_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("bindings/home_devices.apis.aware"),),
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            code_package_delta=delta,
        )
    )

    assert result.diagnostics == ()
    assert result.change_preview.affected_semantic_keys == ("home_devices",)
    assert result.change_preview.metadata["api_count"] == 1
    assert result.change_preview.metadata["graph_count"] == 1


def test_build_api_compile_plan_consumes_semantic_analysis_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_api_toml(tmp_path)
    _write(
        tmp_path / "apis" / "demo.aware",
        _api_source("demo", "read_demo", "ReadDemoRequest"),
    )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    analysis = analyze_api_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        binding_truth_by_ref={},
    )
    calls: list[tuple[Path, tuple[Path, ...]]] = []

    def _fake_analyze_api_sources(**kwargs: object) -> APISemanticAnalysisResult:
        calls.append(
            (
                cast(Path, kwargs["package_root"]),
                cast(tuple[Path, ...], kwargs["source_files"]),
            )
        )
        return APISemanticAnalysisResult(
            schema_version=analysis.schema_version,
            package_root=analysis.package_root,
            source_files=analysis.source_files,
            api_ownership=analysis.api_ownership,
            diagnostics=analysis.diagnostics,
            change_preview=analysis.change_preview,
        )

    monkeypatch.setattr(
        "aware_api_runtime.ir.compile_plan.analyze_api_sources",
        _fake_analyze_api_sources,
    )

    plan = build_api_compile_plan(snapshot=snapshot)

    assert calls == [(snapshot.package_root, snapshot.source_files)]
    assert plan.api_ownership == analysis.api_ownership
    assert plan.api_ontology
