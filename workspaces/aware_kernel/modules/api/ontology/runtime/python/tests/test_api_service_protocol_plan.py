from __future__ import annotations

from pathlib import Path
import sys

from aware_meta.materialization.schemas import (
    API_SERVICE_PROTOCOL_RENDERER_PROFILE,
    MaterializationSource,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    write_home_api_dependency_runtime_artifacts,
)
from aware_api_runtime.ir import (
    build_api_compile_plan,
)  # noqa: E402
from aware_api_runtime.compile import (
    compile_api_workspace,
)  # noqa: E402
from aware_api_runtime.models import (
    ProjectionOwnedClassTruth,
)  # noqa: E402
from aware_api_runtime.packages import (  # noqa: E402
    ApiPublicPackageRequestPlan,
    build_api_service_protocol_plan,
)


def _write_api_toml(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-story-api"',
                'fqn_prefix = "aware_home_story_api"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_api_type_package(root: Path) -> None:
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

    package_root = root / "apis" / "types" / "home"
    (package_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.toml").write_text(
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
    _ = (package_root / "aware" / "door" / "endpoints.aware").write_text(
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
                "class DoorSnapshot {",
                "    label String",
                "    is_locked Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "door" / "keys.aware").write_text(
        "\n".join(
            [
                "class DoorDevice {",
                "    device_id String",
                "    provider String",
                "    door_label String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "bindings.aware").write_text(
        "\n".join(
            [
                "binding aware_home_api aware_home {",
                "    map door_by_label door.DoorDevice home.Door.label {",
                "        template {",
                '            "{door_label}"',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    write_home_api_dependency_runtime_artifacts(root)


def _write_api_source(root: Path) -> None:
    _write_api_type_package(root)
    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "home.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability lock_door {",
                '        """Lock the front door."""',
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                '            """Lock command."""',
                "            response aware_home_api.door.LockDoorResult;",
                "            stream server {",
                '                """Server push state."""',
                "                event snapshot aware_home_api.door.DoorSnapshot;",
                "            }",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _projection_truth() -> dict[str, dict[str, ProjectionOwnedClassTruth]]:
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


def test_build_api_service_protocol_plan_from_api_ontology(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    compile_plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=_projection_truth()
    )

    service_plan = build_api_service_protocol_plan(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        api_ontology=compile_plan.api_ontology,
    )

    assert service_plan.schema_version == 1
    assert service_plan.package_name == "home-story-api"
    assert service_plan.fqn_prefix == "aware_home_story_api"
    assert (
        service_plan.backend_handoff.materialization_source == MaterializationSource.api
    )
    assert service_plan.backend_handoff.aware_package_kind == "api_service_protocol"
    assert (
        service_plan.backend_handoff.expected_renderer_profile
        == API_SERVICE_PROTOCOL_RENDERER_PROFILE
    )

    api_plan = service_plan.apis[0]
    assert api_plan.name == "home_devices"
    capability_plan = api_plan.capabilities[0]
    assert capability_plan.name == "lock_door"
    assert capability_plan.description == "Lock the front door."

    endpoint_plan = capability_plan.endpoints[0]
    assert endpoint_plan.endpoint_ref == "home_devices.lock_door.lock_door"
    assert endpoint_plan.discriminant == "home_devices.lock_door.lock_door"
    assert endpoint_plan.description == "Lock command."
    assert isinstance(endpoint_plan.request, ApiPublicPackageRequestPlan)
    assert endpoint_plan.request.class_ref == "aware_home_api.door.LockDoor"
    assert endpoint_plan.response is not None
    assert endpoint_plan.response.class_ref == "aware_home_api.door.LockDoorResult"
    assert endpoint_plan.stream is not None
    assert endpoint_plan.stream.stream_mode == "server"
    assert endpoint_plan.stream.description == "Server push state."
    assert endpoint_plan.stream.events[0].kind == "snapshot"
    assert (
        endpoint_plan.stream.events[0].class_ref == "aware_home_api.door.DoorSnapshot"
    )
    assert len(endpoint_plan.fulfillment_bindings) == 1
    assert endpoint_plan.fulfillment_bindings[0].name == "lock"
    assert endpoint_plan.fulfillment_bindings[0].graph_target == "aware_home"
    assert (
        endpoint_plan.fulfillment_bindings[0].graph_capability_function_name == "lock"
    )
    assert (
        endpoint_plan.fulfillment_bindings[0].graph_function_python_ref
        == "aware_home.home.Door.lock"
    )
    assert endpoint_plan.fulfillment_bindings[0].graph_function_runtime_target is None


def test_build_api_service_protocol_plan_requires_request_config(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    compile_plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=_projection_truth()
    )
    broken_plan = compile_plan.api_ontology[0]
    broken_plan = type(broken_plan)(
        api=broken_plan.api,
        capabilities=broken_plan.capabilities,
        capability_endpoints=broken_plan.capability_endpoints,
        capability_endpoint_request_configs=(),
        capability_endpoint_response_configs=broken_plan.capability_endpoint_response_configs,
        capability_endpoint_stream_configs=broken_plan.capability_endpoint_stream_configs,
        capability_endpoint_stream_event_configs=broken_plan.capability_endpoint_stream_event_configs,
        capability_endpoint_functions=broken_plan.capability_endpoint_functions,
        graphs=broken_plan.graphs,
        graph_functions=broken_plan.graph_functions,
        graph_projections=broken_plan.graph_projections,
        graph_capabilities=broken_plan.graph_capabilities,
        graph_capability_functions=broken_plan.graph_capability_functions,
    )

    try:
        _ = build_api_service_protocol_plan(
            package_name=compile_plan.package_name,
            fqn_prefix=compile_plan.fqn_prefix,
            api_ontology=(broken_plan,),
        )
    except RuntimeError as exc:
        assert "missing request config" in str(exc)
    else:
        raise AssertionError(
            "Expected missing request config to fail service protocol planning"
        )
