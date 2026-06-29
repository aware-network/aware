from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from aware_api_runtime.ir import (
    build_api_compile_plan,
)  # noqa: E402
from aware_api_runtime.compile import (
    compile_api_workspace,
)  # noqa: E402
from aware_api_runtime.ontology_graph.ontology import (  # noqa: E402
    decode_api_ontology_plan_payload,
    encode_api_ontology_plan_payload,
)
from aware_api_runtime.models import (
    ProjectionOwnedClassTruth,
)  # noqa: E402
from api_runtime_fixture_artifacts import (  # noqa: E402
    write_ontology_dependency_runtime_artifacts,
    write_python_models_manifest_for_refs,
)


def _write_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "api-anchor"',
                'fqn_prefix = "aware_api_anchor"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                "",
                "[[dependencies]]",
                'package_name = "api-anchor-types"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_api_source(root: Path) -> None:
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
    _ = (ontology_root / "aware" / "home" / "home.aware").write_text(
        "\n".join(
            [
                "class Home {",
                "    name String key",
                "    doors Door[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "    is_locked Bool = false",
                "",
                "    fn lock(",
                "        force Bool = false",
                "    ) -> Bool {",
                '        """Lock this door."""',
                "    }",
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

    types_root = root / "apis" / "types" / "anchor"
    (types_root / "aware" / "projection").mkdir(parents=True, exist_ok=True)
    _ = (types_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "api-anchor-types"',
                'fqn_prefix = "aware_api_anchor"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_api_anchor"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (types_root / "aware" / "projection" / "resolve_projection.aware").write_text(
        "\n".join(
            [
                "class ResolveProjection {",
                "    name String",
                "}",
                "",
                "class ResolveProjectionResult {",
                "    accepted Bool",
                "}",
                "",
                "class ResolveProjectionSnapshot {",
                "    name String",
                "}",
                "",
                "class ResolveProjectionDelta {",
                "    changed_field String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "anchor.apis.aware").write_text(
        "\n".join(
            [
                "api api_anchor {",
                "    capability projection_resolution {",
                "        endpoint projection_resolution aware_api_anchor.projection.ResolveProjection {",
                "            response aware_api_anchor.projection.ResolveProjectionResult;",
                "            stream server {",
                "                event snapshot aware_api_anchor.projection.ResolveProjectionSnapshot;",
                "                event delta aware_api_anchor.projection.ResolveProjectionDelta;",
                "            }",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability projection_resolution {",
                "            function resolve aware_home.home.Door.lock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_home_ontology_runtime_artifacts(root)
    _write_dependency_python_models(root)


def _write_dependency_python_models(root: Path) -> None:
    write_python_models_manifest_for_refs(
        package_root=root / "apis" / "types" / "anchor",
        class_refs=(
            "aware_api_anchor.projection.ResolveProjection",
            "aware_api_anchor.projection.ResolveProjectionResult",
            "aware_api_anchor.projection.ResolveProjectionSnapshot",
            "aware_api_anchor.projection.ResolveProjectionDelta",
        ),
    )


def _write_home_ontology_runtime_artifacts(root: Path) -> None:
    write_ontology_dependency_runtime_artifacts(
        package_root=root / "modules" / "home" / "structure" / "ontology",
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_refs=("aware_home.home.Home", "aware_home.home.Door"),
        projection_names=("Home",),
    )


def _projection_truth_for_api_anchor() -> (
    dict[str, dict[str, ProjectionOwnedClassTruth]]
):
    return {
        "aware_home.Home": {
            "Home": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Home",
                attributes=frozenset({"doors"}),
                identity_key_attributes=frozenset({"name"}),
                relationship_targets=(("doors", "Door"),),
            ),
            "Door": ProjectionOwnedClassTruth(
                class_fqn="aware_home_ontology.home.home.Door",
                attributes=frozenset({"label", "is_locked"}),
                identity_key_attributes=frozenset({"label"}),
            ),
        }
    }


def test_api_compile_plan_contains_api_ontology_ir(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    plan = build_api_compile_plan(
        snapshot=result.snapshot,
        projection_truth_by_name=_projection_truth_for_api_anchor(),
    )

    assert plan.schema_version == 9
    assert len(plan.api_ownership) == 1
    assert len(plan.api_ontology) == 1

    ownership = plan.api_ownership[0]
    assert ownership.name == "api_anchor"
    assert len(ownership.capabilities) == 1
    assert ownership.capabilities[0].name == "projection_resolution"
    assert len(ownership.capabilities[0].endpoints) == 1
    assert ownership.capabilities[0].endpoints[0].name == "projection_resolution"
    assert (
        ownership.capabilities[0].endpoints[0].request_config.class_ref
        == "aware_api_anchor.projection.ResolveProjection"
    )
    assert (
        ownership.capabilities[0].endpoints[0].request_config.response_config
        is not None
    )
    assert (
        ownership.capabilities[0].endpoints[0].request_config.response_config.class_ref
        == "aware_api_anchor.projection.ResolveProjectionResult"
    )
    assert (
        ownership.capabilities[0].endpoints[0].request_config.stream_config is not None
    )
    assert (
        ownership.capabilities[0].endpoints[0].request_config.stream_config.stream_mode
        == "server"
    )

    ontology_plan = plan.api_ontology[0]
    assert ontology_plan.api.name == "api_anchor"
    assert len(ontology_plan.capabilities) == 1
    assert ontology_plan.capabilities[0].name == "projection_resolution"
    assert len(ontology_plan.capability_endpoints) == 1
    assert (
        ontology_plan.capability_endpoints[0].capability_name == "projection_resolution"
    )
    assert ontology_plan.capability_endpoints[0].name == "projection_resolution"
    assert len(ontology_plan.capability_endpoint_request_configs) == 1
    assert (
        ontology_plan.capability_endpoint_request_configs[0].endpoint_name
        == "projection_resolution"
    )
    assert (
        ontology_plan.capability_endpoint_request_configs[0].class_ref
        == "aware_api_anchor.projection.ResolveProjection"
    )
    assert len(ontology_plan.capability_endpoint_response_configs) == 1
    assert (
        ontology_plan.capability_endpoint_response_configs[0].class_ref
        == "aware_api_anchor.projection.ResolveProjectionResult"
    )
    assert len(ontology_plan.capability_endpoint_stream_configs) == 1
    assert ontology_plan.capability_endpoint_stream_configs[0].stream_mode == "server"
    assert len(ontology_plan.capability_endpoint_stream_event_configs) == 2
    assert tuple(
        (row.kind, row.class_ref)
        for row in ontology_plan.capability_endpoint_stream_event_configs
    ) == (
        ("delta", "aware_api_anchor.projection.ResolveProjectionDelta"),
        ("snapshot", "aware_api_anchor.projection.ResolveProjectionSnapshot"),
    )
    assert len(ontology_plan.capability_endpoint_functions) == 1
    assert (
        ontology_plan.capability_endpoint_functions[0].capability_name
        == "projection_resolution"
    )
    assert (
        ontology_plan.capability_endpoint_functions[0].endpoint_name
        == "projection_resolution"
    )
    assert ontology_plan.capability_endpoint_functions[0].name == "resolve"
    assert ontology_plan.capability_endpoint_functions[0].graph_target == "aware_home"
    assert (
        ontology_plan.capability_endpoint_functions[0].graph_capability_function_name
        == "resolve"
    )
    assert not hasattr(ontology_plan, "capability_endpoint_projection_read_targets")
    assert not hasattr(
        ontology_plan, "capability_endpoint_projection_read_target_functions"
    )
    assert len(ontology_plan.graphs) == 1
    assert ontology_plan.graphs[0].target == "aware_home"
    assert len(ontology_plan.graph_projections) == 1
    assert ontology_plan.graph_projections[0].target == "aware_home.Home"
    assert len(ontology_plan.graph_capabilities) == 1
    assert (
        ontology_plan.graph_capabilities[0].capability_name == "projection_resolution"
    )
    assert len(ontology_plan.graph_capability_functions) == 1
    assert ontology_plan.graph_capability_functions[0].name == "resolve"
    assert (
        ontology_plan.graph_capability_functions[0].target
        == "aware_home.home.Door.lock"
    )
    assert len(ontology_plan.graph_functions) == 1
    assert ontology_plan.graph_functions[0].target == "aware_home.home.Door.lock"


def test_api_compile_plan_keeps_projection_graph_ir_without_read_target(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)
    _ = (root / "apis" / "bindings" / "anchor.apis.aware").write_text(
        "\n".join(
            [
                "api api_anchor {",
                "    capability territory {",
                "        endpoint discover aware_api_anchor.projection.ResolveProjection {",
                "            response aware_api_anchor.projection.ResolveProjectionResult;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability territory {",
                "            function discover aware_home.home.Home.discover;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    plan = build_api_compile_plan(
        snapshot=result.snapshot,
        projection_truth_by_name=_projection_truth_for_api_anchor(),
    )
    ontology_plan = plan.api_ontology[0]

    assert not hasattr(ontology_plan, "capability_endpoint_projection_read_targets")
    assert not hasattr(
        ontology_plan, "capability_endpoint_projection_read_target_functions"
    )
    assert len(ontology_plan.graph_projections) == 1
    assert ontology_plan.graph_projections[0].target == "aware_home.Home"
    assert len(ontology_plan.graph_capability_functions) == 1
    assert ontology_plan.graph_capability_functions[0].name == "discover"

    decoded = decode_api_ontology_plan_payload(
        payload=encode_api_ontology_plan_payload(plans=(ontology_plan,))
    )
    assert not hasattr(decoded[0], "capability_endpoint_projection_read_targets")
    assert not hasattr(
        decoded[0], "capability_endpoint_projection_read_target_functions"
    )


def test_decode_api_ontology_rejects_graph_capability_function_api_name_mismatch() -> (
    None
):
    payload = [
        {
            "api": {
                "name": "api_anchor",
                "description": None,
                "source_path": "apis/bindings/anchor.apis.aware",
            },
            "capabilities": [],
            "capability_endpoints": [],
            "capability_endpoint_request_configs": [],
            "capability_endpoint_response_configs": [],
            "capability_endpoint_stream_configs": [],
            "capability_endpoint_stream_event_configs": [],
            "capability_endpoint_functions": [],
            "graphs": [],
            "graph_functions": [],
            "graph_projections": [],
            "graph_capabilities": [],
            "graph_capability_functions": [
                {
                    "api_name": "other_api",
                    "graph_target": "aware_api",
                    "capability_name": "projection_resolution",
                    "name": "create_api",
                    "target": "aware_api.api.Api.create",
                    "source_path": "apis/bindings/anchor.apis.aware",
                }
            ],
        }
    ]

    with pytest.raises(ValueError, match="graph_capability_function.api_name"):
        _ = decode_api_ontology_plan_payload(payload=payload)


def test_decode_api_ontology_rejects_capability_endpoint_function_api_name_mismatch() -> (
    None
):
    payload = [
        {
            "api": {
                "name": "api_anchor",
                "description": None,
                "source_path": "apis/bindings/anchor.apis.aware",
            },
            "capabilities": [],
            "capability_endpoints": [],
            "capability_endpoint_request_configs": [],
            "capability_endpoint_response_configs": [],
            "capability_endpoint_stream_configs": [],
            "capability_endpoint_stream_event_configs": [],
            "capability_endpoint_functions": [
                {
                    "api_name": "other_api",
                    "capability_name": "projection_resolution",
                    "endpoint_name": "projection_resolution",
                    "name": "create_api",
                    "graph_target": "aware_api",
                    "graph_capability_function_name": "create_api",
                    "source_path": "apis/bindings/anchor.apis.aware",
                }
            ],
            "graphs": [],
            "graph_functions": [],
            "graph_projections": [],
            "graph_capabilities": [],
            "graph_capability_functions": [],
        }
    ]

    with pytest.raises(ValueError, match="capability_endpoint_function.api_name"):
        _ = decode_api_ontology_plan_payload(payload=payload)
