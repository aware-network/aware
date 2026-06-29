from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_API_RUNTIME_ROOT_STR = str(_REPO_ROOT / "modules" / "api" / "runtime")
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    focus_api_accessible_graphs,
    home_api_accessible_graphs,
    write_focus_api_dependency_runtime_artifacts,
    write_home_api_dependency_runtime_artifacts,
)
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: E402
    canonicalize_api_accessible_dependency_graph_artifact_payload,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)


def test_compile_api_service_protocol_emits_accessible_dependency_graph_artifact(
    tmp_path: Path,
) -> None:
    toml_path = _write_dependency_api_workspace(tmp_path)

    _ = compile_api_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        materialize_service_protocol=True,
        accessible_graphs=home_api_accessible_graphs(),
    )

    graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=(
            tmp_path / ".aware" / "api" / "runtime" / "dependency-proof-service-api"
        ),
    )

    assert [graph.name for graph in graphs] == ["home-ontology", "home-api"]
    home_graph = next(graph for graph in graphs if graph.name == "home-ontology")
    assert [opg.name for opg in home_graph.object_projection_graphs] == ["Home"]
    artifact_payload = json.loads(
        (
            tmp_path
            / ".aware"
            / "api"
            / "runtime"
            / "dependency-proof-service-api"
            / "api.accessible_dependency_graphs.json"
        ).read_text(encoding="utf-8")
    )
    assert _find_forbidden_runtime_reference_keys(artifact_payload) == []
    home_graph_payload = next(
        graph
        for graph in artifact_payload["graphs"]
        if graph["name"] == "home-ontology"
    )
    assert any(
        entry["package"] == "aware_home"
        and entry["fqn"] == "aware_home.home.Home"
        and entry["symbol"] == "Home"
        for entry in home_graph_payload["namespace_membership"]
    )


def test_compile_api_service_protocol_emits_graph_target_dependency_artifact(
    tmp_path: Path,
) -> None:
    toml_path = _write_graph_target_api_workspace(tmp_path)

    _ = compile_api_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        materialize_service_protocol=True,
        accessible_graphs=focus_api_accessible_graphs(),
    )

    graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=(
            tmp_path / ".aware" / "api" / "runtime" / "focus-service-api"
        ),
    )

    assert {graph.name for graph in graphs} == {
        "focus-ontology",
        "focus-service-dto",
    }
    focus_graph = next(graph for graph in graphs if graph.name == "focus-ontology")
    assert focus_graph.fqn_prefix == "aware_focus"
    assert [opg.name for opg in focus_graph.object_projection_graphs] == ["FocusScope"]
    dto_graph = next(graph for graph in graphs if graph.name == "focus-service-dto")
    assert dto_graph.object_config_graph_nodes
    artifact_payload = json.loads(
        (
            tmp_path
            / ".aware"
            / "api"
            / "runtime"
            / "focus-service-api"
            / "api.accessible_dependency_graphs.json"
        ).read_text(encoding="utf-8")
    )
    dto_graph_payload = next(
        graph
        for graph in artifact_payload["graphs"]
        if graph["name"] == "focus-service-dto"
    )
    assert any(
        entry["package"] == "aware_focus_service_dto"
        and entry["fqn"] == "aware_focus_service_dto.comms.models.GetFocusRequest"
        and entry["symbol"] == "GetFocusRequest"
        for entry in dto_graph_payload["namespace_membership"]
    )


def test_runtime_dependency_graph_artifact_loader_flattens_embedded_graph_refs(
    tmp_path: Path,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "nested-proof-api"
    runtime_package_dir.mkdir(parents=True)
    source_graph_id = "00000000-0000-4000-8000-000000000001"
    target_graph_id = "00000000-0000-4000-8000-000000000002"
    payload = {
        "schema_version": 1,
        "graphs": [
            {
                "id": source_graph_id,
                "name": "source-api",
                "hash": "sha256:source",
                "fqn_prefix": "aware_source_api",
                "language": "aware",
                "object_config_graph_bindings": [
                    {
                        "object_config_graph_id": source_graph_id,
                        "target_object_config_graph_id": target_graph_id,
                        "target_object_config_graph": {
                            "id": target_graph_id,
                            "name": "target-ontology",
                            "hash": "sha256:target",
                            "fqn_prefix": "aware_target",
                            "language": "aware",
                        },
                    }
                ],
            }
        ],
    }
    _ = (runtime_package_dir / "api.accessible_dependency_graphs.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=runtime_package_dir,
    )

    assert len(graphs) == 1
    [binding] = graphs[0].object_config_graph_bindings
    assert str(binding.target_object_config_graph_id) == target_graph_id
    assert binding.target_object_config_graph is None


def test_runtime_dependency_graph_artifact_loader_rejects_namespace_less_graph_nodes(
    tmp_path: Path,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "broken-api"
    runtime_package_dir.mkdir(parents=True)
    graph_id = "00000000-0000-4000-8000-000000000101"
    node_id = "00000000-0000-4000-8000-000000000102"
    class_id = "00000000-0000-4000-8000-000000000103"
    payload = {
        "schema_version": 1,
        "graphs": [
            {
                "id": graph_id,
                "name": "broken-dto",
                "hash": "sha256:broken",
                "fqn_prefix": "aware_broken",
                "language": "aware",
                "object_config_graph_nodes": [
                    {
                        "id": node_id,
                        "type": "class",
                        "node_key": "aware_broken.comms.models.Broken",
                        "object_config_graph_id": graph_id,
                        "class_config": {
                            "id": class_id,
                            "class_fqn": "aware_broken.comms.models.Broken",
                            "name": "Broken",
                        },
                    }
                ],
            }
        ],
    }
    _ = (runtime_package_dir / "api.accessible_dependency_graphs.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="namespace evidence"):
        load_api_accessible_dependency_graphs_from_runtime_artifact(
            runtime_package_dir=runtime_package_dir,
        )


def test_accessible_dependency_graph_artifact_payload_canonicalizes_identity_lists() -> (
    None
):
    payload = {
        "object_config_graph_nodes": [
            {
                "id": "00000000-0000-4000-8000-000000000002",
                "node_key": "aware_demo.B",
                "class_config": {
                    "class_config_attribute_configs": [
                        {
                            "attribute_config_id": (
                                "00000000-0000-4000-8000-000000000022"
                            ),
                            "attribute_config": {
                                "name": "second",
                                "type_descriptor": {
                                    "child_links": [
                                        {"name": "zeta"},
                                        {"name": "alpha"},
                                    ],
                                },
                            },
                        },
                        {
                            "attribute_config_id": (
                                "00000000-0000-4000-8000-000000000021"
                            ),
                            "attribute_config": {"name": "first"},
                        },
                    ]
                },
            },
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "node_key": "aware_demo.A",
            },
        ],
        "namespace_membership": [
            {
                "package": "aware_demo",
                "namespace": "demo.models",
                "entity_kind": "class",
                "symbol": "B",
            },
            {
                "package": "aware_demo",
                "namespace": "demo.models",
                "entity_kind": "class",
                "symbol": "A",
            },
        ],
        "object_config_graph_overlays": [
            {
                "id": "00000000-0000-4000-8000-000000000042",
                "name": "zeta",
            },
            {
                "id": "00000000-0000-4000-8000-000000000041",
                "name": "alpha",
            },
        ],
        "object_projection_graph_declarations": [
            {
                "id": "00000000-0000-4000-8000-000000000052",
                "name": "Feed",
            },
            {
                "id": "00000000-0000-4000-8000-000000000051",
                "name": "Conversation",
            },
        ],
    }

    canonical = canonicalize_api_accessible_dependency_graph_artifact_payload(
        payload=payload
    )

    assert isinstance(canonical, dict)
    assert [item["node_key"] for item in canonical["object_config_graph_nodes"]] == [
        "aware_demo.A",
        "aware_demo.B",
    ]
    class_config = canonical["object_config_graph_nodes"][1]["class_config"]
    assert [
        item["attribute_config_id"]
        for item in class_config["class_config_attribute_configs"]
    ] == [
        "00000000-0000-4000-8000-000000000021",
        "00000000-0000-4000-8000-000000000022",
    ]
    child_links = class_config["class_config_attribute_configs"][1]["attribute_config"][
        "type_descriptor"
    ]["child_links"]
    assert [item["name"] for item in child_links] == ["alpha", "zeta"]
    assert [item["symbol"] for item in canonical["namespace_membership"]] == [
        "A",
        "B",
    ]
    assert [item["name"] for item in canonical["object_config_graph_overlays"]] == [
        "alpha",
        "zeta",
    ]
    assert [
        item["name"] for item in canonical["object_projection_graph_declarations"]
    ] == [
        "Conversation",
        "Feed",
    ]


def _find_forbidden_runtime_reference_keys(payload: object) -> list[str]:
    forbidden = {
        "code_section_annotation_discriminate_id",
        "code_section_annotation_id",
        "code_section_annotation_identity_id",
        "code_section_annotation_load_id",
        "code_section_annotation_oneof_id",
        "code_section_annotation_overlay_id",
        "code_section_annotation_override_id",
        "code_section_annotation_reference_id",
        "code_section_attribute_id",
        "code_section_class_id",
        "code_section_enum_id",
        "code_section_function_id",
        "domain_relationships",
        "target_object_config_graph",
    }
    matches: list[str] = []

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if key in forbidden:
                    matches.append(child_path)
                    continue
                walk(child, child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "")
    return matches


def _write_dependency_api_workspace(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
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
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_dependency_proof_service_api"',
                "",
                "[targets.python.service_protocol]",
                'package_dir = "aware_dependency_proof_service_protocol"',
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
    _ = (bindings / "service.apis.aware").write_text(
        "\n".join(
            [
                "api dependency_proof {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                "            response aware_home_api.door.LockDoorResult;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
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
    _ = (ontology_root / "aware.toml").write_text(
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
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String key",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "home.aware").write_text(
        "\n".join(
            [
                "class Home {",
                "    doors Door[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home_projection.aware").write_text(
        "\n".join(
            [
                "projection Home {",
                "    root home.Home",
                "    home.Home::doors",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "types" / "home"
    (api_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (api_root / "aware.toml").write_text(
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
    _ = (api_root / "aware" / "door" / "endpoints.aware").write_text(
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
    _ = (api_root / "aware" / "bindings.aware").write_text(
        "\n".join(
            [
                "binding aware_home_api aware_home {",
                "    map door_by_label door.LockDoor home.Door.label {",
                "        template {",
                '            "label::{label}"',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_home_api_dependency_runtime_artifacts(root)
    return toml_path


def _write_graph_target_api_workspace(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "focus-service-api"',
                'fqn_prefix = "aware_focus_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_focus_service_api"',
                "",
                "[targets.python.service_protocol]",
                'package_dir = "aware_focus_service_protocol"',
                "",
                "[[dependencies]]",
                'package_name = "focus-service-dto"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "focus.apis.aware").write_text(
        "\n".join(
            [
                "api focus {",
                "    capability get_focus {",
                "        endpoint get_focus aware_focus_service_dto.comms.models.GetFocusRequest {",
                "            response aware_focus_service_dto.comms.models.GetFocusResponse;",
                "        }",
                "    }",
                "    graph aware_focus {",
                "        projection aware_focus.FocusScope {",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ontology_root = root / "modules" / "focus" / "structure" / "ontology"
    (ontology_root / "aware" / "focus").mkdir(parents=True, exist_ok=True)
    _ = (ontology_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "focus-ontology"',
                'fqn_prefix = "aware_focus"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_focus"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "focus" / "focus_scope.aware").write_text(
        "\n".join(
            [
                "class FocusScope {",
                "    key String key",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "focus_projection.aware").write_text(
        "\n".join(
            [
                "projection FocusScope {",
                "    root focus.FocusScope",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    dto_root = root / "apis" / "focus" / "dto"
    (dto_root / "aware" / "section").mkdir(parents=True, exist_ok=True)
    _ = (dto_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "focus-service-dto"',
                'fqn_prefix = "aware_focus_service_dto"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_focus_service_dto"',
                "",
                "[build.namespace]",
                '"section/**/*.aware" = "comms.models"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (dto_root / "aware" / "section" / "models.aware").write_text(
        "\n".join(
            [
                "class FocusOperation {",
                "    request FocusOperationRequest?",
                "    response FocusOperationResponse?",
                "}",
                "",
                "ann comms.models.FocusOperation oneof request response",
                "",
                "class FocusOperationRequest {",
                "    operation String",
                "}",
                "",
                "class FocusOperationResponse {",
                "    operation String",
                "}",
                "",
                "class GetFocusRequest augment comms.models.FocusOperationRequest {",
                '    operation String = "get_focus"',
                "    key String",
                "}",
                "",
                "class GetFocusResponse augment comms.models.FocusOperationResponse {",
                '    operation String = "get_focus"',
                "    key String",
                "}",
                "",
                "ann comms.models.FocusOperationRequest::operation discriminate key",
                'ann comms.models.GetFocusRequest::operation discriminate tag "get_focus"',
                "",
                "ann comms.models.FocusOperationResponse::operation discriminate key",
                'ann comms.models.GetFocusResponse::operation discriminate tag "get_focus"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_focus_api_dependency_runtime_artifacts(root)
    return toml_path
