from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_api_runtime import compile as api_compile
from aware_api_runtime.compile_materialization import (
    service as api_materialization_service,
)
from aware_api_runtime.compile import (
    compile_api_workspace,
    refresh_api_workspace_from_runtime_artifacts,
)
from aware_api_runtime.packages import materialization as api_product_materialization
from aware_api_runtime.dependencies import runtime_resolution as api_runtime_resolution
from aware_api_runtime.dependencies.runtime_resolution import (
    API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME,
    dump_api_accessible_dependency_graph_artifact_payload,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from _api_runtime_test_paths import KERNEL_WORKSPACE_ROOT as _KERNEL_WORKSPACE_ROOT


def test_resolve_api_package_spec_uses_runtime_graph_artifact_without_artifact_rebuild(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    home_api_graph = _test_object_config_graph(
        package_name="home-api",
        fqn_prefix="aware_home_api",
        class_fqns=(
            "aware_home_api.default.door.LockDoor",
            "aware_home_api.default.door.LockDoorResult",
        ),
    )
    for node in home_api_graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        if class_config.name == "LockDoor":
            class_config.id = request_class_config_id
        elif class_config.name == "LockDoorResult":
            class_config.id = response_class_config_id
    artifact_graphs = (
        _test_object_config_graph(
            package_name="home-ontology",
            fqn_prefix="aware_home",
            class_fqns=("aware_home.default.home.Door",),
        ),
        home_api_graph,
    )
    runtime_package_dir = (
        tmp_path / ".aware" / "api" / "runtime" / "dependency-proof-service-api"
    )
    runtime_package_dir.mkdir(parents=True)
    (runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "graphs": [
                    dump_api_accessible_dependency_graph_artifact_payload(graph=graph)
                    for graph in artifact_graphs
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    def _artifact_rebuild_should_not_run(**_: object) -> tuple[ObjectConfigGraph, ...]:
        raise AssertionError("dependency graph artifact rebuild should not run")

    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graphs",
        _artifact_rebuild_should_not_run,
    )
    phase_timings_s: dict[str, float] = {}

    spec = api_materialization_service.resolve_api_package_materialization_spec(
        api_toml_path=toml_path,
        workspace_root=tmp_path,
        phase_timings_s=phase_timings_s,
    )

    assert (
        spec.dependency_graph_context_source
        == "runtime_accessible_dependency_graphs_artifact"
    )
    assert len(spec.dependency_accessible_graphs) == 2
    assert (
        "resolve_api_package_materialization_spec."
        "load_accessible_dependency_graphs_runtime_artifact"
    ) in phase_timings_s
    assert (
        "resolve_api_package_materialization_spec."
        "load_accessible_dependency_graphs_from_dependency_artifacts"
    ) not in phase_timings_s
    ontology_payload = spec.compile_plan_payload["api_ontology"][0]
    request_configs = ontology_payload["capability_endpoint_request_configs"]
    response_configs = ontology_payload["capability_endpoint_response_configs"]
    assert request_configs[0]["class_config_id"] == str(request_class_config_id)
    assert response_configs[0]["class_config_id"] == str(response_class_config_id)


def test_runtime_graph_artifact_loader_reuses_hydrated_graphs_by_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "cache-proof-api"
    runtime_package_dir.mkdir(parents=True)
    graph = _test_object_config_graph(
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_fqns=("aware_home.default.home.Door",),
    )
    (runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "graphs": [
                    dump_api_accessible_dependency_graph_artifact_payload(graph=graph)
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    first_load = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=runtime_package_dir,
    )

    def _json_load_should_not_run(_payload: object) -> object:
        raise AssertionError("cached graph artifact should not parse JSON again")

    monkeypatch.setattr(api_runtime_resolution.json, "loads", _json_load_should_not_run)

    second_load = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=runtime_package_dir,
    )

    assert second_load is first_load


def test_public_package_refresh_uses_supplied_accessible_graphs_without_artifact_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(
        tmp_path,
        include_dart_target=True,
    )
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / ".aware-root"))
    accessible_graphs = (
        _test_object_config_graph(
            package_name="home-ontology",
            fqn_prefix="aware_home",
            class_fqns=("aware_home.default.home.Door",),
        ),
        _test_object_config_graph(
            package_name="home-api",
            fqn_prefix="aware_home_api",
            class_fqns=(
                "aware_home_api.default.door.LockDoor",
                "aware_home_api.default.door.LockDoorResult",
            ),
        ),
    )
    initial = compile_api_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        materialize_public_package=True,
        accessible_graphs=accessible_graphs,
    )
    assert initial.public_package_materialization is not None
    runtime_package_dir = (
        tmp_path / ".aware" / "api" / "runtime" / "dependency-proof-service-api"
    )
    (runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "graphs": [
                    dump_api_accessible_dependency_graph_artifact_payload(graph=graph)
                    for graph in accessible_graphs
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assert accessible_graphs

    def _artifact_loader_should_not_run(**_: object) -> tuple[ObjectConfigGraph, ...]:
        raise AssertionError("supplied accessible graphs should avoid artifact reload")

    monkeypatch.setattr(
        api_product_materialization,
        "load_api_accessible_dependency_graphs_from_runtime_artifact",
        _artifact_loader_should_not_run,
    )

    refreshed = refresh_api_workspace_from_runtime_artifacts(
        toml_path=toml_path,
        repo_root=tmp_path,
        refresh_public_package=True,
        public_package_target_language=CodeLanguage.dart,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=(_KERNEL_WORKSPACE_ROOT,),
    )

    assert refreshed.public_package_materialization is not None
    assert (
        refreshed.public_package_materialization.render_job.target.target_language
        == CodeLanguage.dart
    )
    assert (
        tmp_path / "dart" / "aware_dependency_proof_service_api" / "lib" / "client.dart"
    ).exists()


def test_product_runtime_materializer_passes_compile_plan_graphs_to_dart_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_graph = _test_object_config_graph(
        package_name="source-context",
        fqn_prefix="aware_source_context",
        class_fqns=("aware_source_context.default.proof.SourceProof",),
    )
    product_runtime_graph = _test_object_config_graph(
        package_name="product-runtime-context",
        fqn_prefix="aware_product_runtime_context",
        class_fqns=("aware_product_runtime_context.default.proof.ProductProof",),
    )
    observed: dict[str, object] = {}

    def _fake_build_generated_graphs(**kwargs: object) -> tuple[ObjectConfigGraph, ...]:
        observed["compile_plan_builder_accessible_graphs"] = kwargs["accessible_graphs"]
        return (product_runtime_graph,)

    def _fake_compile_product_runtime(**kwargs: object) -> object:
        observed["compile_accessible_graphs"] = kwargs["accessible_graphs"]
        return SimpleNamespace()

    def _fake_refresh_workspace(**kwargs: object) -> object:
        observed["refresh_accessible_graphs"] = kwargs["accessible_graphs"]
        return SimpleNamespace(
            public_package_materialization=SimpleNamespace(
                materialization_result=SimpleNamespace(post_step_receipts=()),
            ),
        )

    def _manifest_compile_should_not_run(**_: object) -> object:
        raise AssertionError("compile-plan path should not rebuild from manifest")

    monkeypatch.setattr(
        api_materialization_service,
        "build_generated_api_compile_plan_accessible_graphs",
        _fake_build_generated_graphs,
    )
    monkeypatch.setattr(
        api_compile,
        "compile_api_product_runtime_from_compile_plan_payload",
        _fake_compile_product_runtime,
    )
    monkeypatch.setattr(
        api_compile,
        "refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh_workspace,
    )
    monkeypatch.setattr(
        api_compile,
        "compile_api_workspace",
        _manifest_compile_should_not_run,
    )

    api_materialization_service._materialize_api_product_runtime_artifacts_for_language_packages(
        api_toml_path=tmp_path / "aware.api.toml",
        workspace_root=tmp_path,
        snapshot=SimpleNamespace(
            spec=SimpleNamespace(targets=SimpleNamespace(dart=object())),
        ),
        runtime_compile_plan_payload={"package_name": "proof-api"},
        accessible_graphs=(input_graph,),
        dependency_repo_roots=(),
        phase_timings_s={},
        post_step_tool_env_by_tool_id=None,
        post_step_executable_overrides_by_tool_id=None,
    )

    assert observed["compile_plan_builder_accessible_graphs"] == (input_graph,)
    assert observed["compile_accessible_graphs"] == (product_runtime_graph,)
    assert observed["refresh_accessible_graphs"] == (product_runtime_graph,)


def _write_dependency_class_config_workspace(
    root: Path,
    *,
    include_dart_target: bool = False,
) -> Path:
    target_lines: list[str] = []
    if include_dart_target:
        target_lines = [
            "",
            "[targets.dart]",
            'root_dir = "dart"',
            "",
            "[targets.dart.public_package]",
            'package_dir = "aware_dependency_proof_service_api"',
        ]
    toml_path = root / "aware.api.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "dependency-proof-service-api"',
                'fqn_prefix = "aware_dependency_proof_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                *target_lines,
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "service.apis.aware").write_text(
        "\n".join(
            [
                "api dependency_proof {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                "            response aware_home_api.door.LockDoorResult;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    (ontology_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    (ontology_root / "aware.toml").write_text(
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
        encoding="utf-8",
    )
    (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "types" / "home"
    (api_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    (api_root / "aware.toml").write_text(
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
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (api_root / "aware" / "door" / "endpoints.aware").write_text(
        "\n".join(
            [
                "class LockDoor {",
                "    label String",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _test_object_config_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    class_fqns: tuple[str, ...],
) -> ObjectConfigGraph:
    graph_id = uuid4()
    nodes: list[ObjectConfigGraphNode] = []
    for class_fqn in class_fqns:
        class_name = class_fqn.rsplit(".", 1)[-1]
        class_config = ClassConfig.model_construct(
            id=uuid4(),
            class_fqn=class_fqn,
            name=class_name,
            class_config_attribute_configs=[],
            class_config_function_configs=[],
            class_config_relationships=[],
        )
        node = ObjectConfigGraphNode.model_construct(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key=class_fqn,
            object_config_graph_id=graph_id,
            class_config=class_config,
            layouts=[],
        )
        class_config.object_config_graph_node_id = node.id
        nodes.append(node)
    return ObjectConfigGraph.model_construct(
        id=graph_id,
        name=package_name,
        hash=f"sha256:{package_name}",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_annotations=[],
        object_config_graph_mirrors=[],
        object_config_graph_nodes=nodes,
        object_config_graph_overlays=[],
        object_config_graph_bindings=[],
        object_config_graph_relationships=[],
        object_projection_graph_declarations=[],
        object_projection_graphs=[],
    )
