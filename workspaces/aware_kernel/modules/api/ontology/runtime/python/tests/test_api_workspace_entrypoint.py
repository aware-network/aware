from __future__ import annotations

from pathlib import Path
import sys

_RUNTIME_ROOT = Path(__file__).resolve().parents[1]
_RUNTIME_ROOT_STR = str(_RUNTIME_ROOT)
if _RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _RUNTIME_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    home_api_accessible_graphs,
    write_home_api_dependency_runtime_artifacts,
)
from aware_api_runtime.ir import (  # noqa: E402
    build_api_compile_plan,
    emit_api_compile_plan_artifact,
    emit_api_runtime_artifacts,
)
from aware_api_runtime.compile import (
    compile_api_workspace,
)  # noqa: E402
from aware_api_runtime.models import (
    ProjectionOwnedClassTruth,
)  # noqa: E402


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
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                "            response aware_home_api.door.LockDoorResult;",
                "            stream server {",
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


def test_compile_api_workspace_builds_snapshot(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    snapshot = result.snapshot
    assert snapshot.spec.api.package_name == "home-story-api"
    assert snapshot.spec.api.fqn_prefix == "aware_home_story_api"
    assert snapshot.source_files == (Path("apis/bindings/home.apis.aware"),)
    assert result.public_package_materialization is None
    assert result.service_protocol_materialization is None


def test_api_compile_plan_and_artifact_emit(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    projection_truth = {
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
    plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=projection_truth
    )
    assert plan.schema_version == 9
    assert plan.package_name == "home-story-api"
    assert plan.fqn_prefix == "aware_home_story_api"
    assert len(plan.api_ownership) == 1
    assert plan.api_ownership[0].name == "home_devices"
    assert len(plan.api_ownership[0].capabilities[0].endpoints[0].functions) == 1
    assert (
        plan.api_ownership[0].capabilities[0].endpoints[0].request_config.class_ref
        == "aware_home_api.door.LockDoor"
    )
    endpoint_function = plan.api_ownership[0].capabilities[0].endpoints[0].functions[0]
    assert endpoint_function.name == "lock"
    assert endpoint_function.graph_target == "aware_home"
    assert endpoint_function.graph_capability_function_name == "lock"
    assert len(plan.api_ontology) == 1

    artifact = emit_api_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )
    assert artifact.path.exists()
    assert artifact.relpath == "runtime/api.compile_plan.json"
    assert len(artifact.hash_sha256) == 64
    payload = artifact.path.read_text(encoding="utf-8")
    assert '"api_ownership"' in payload
    assert '"lock_door"' in payload
    assert '"capability_endpoint_request_configs"' in payload
    assert '"capability_endpoint_functions"' in payload
    assert '"capability_endpoint_projection_read_targets"' not in payload
    assert '"capability_endpoint_projection_read_target_functions"' not in payload
    assert '"lock"' in payload


def test_api_runtime_artifacts_emit_interface_spec(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    projection_truth = {
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
    plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=projection_truth
    )

    artifacts = emit_api_runtime_artifacts(
        plan=plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )

    assert artifacts.compile_plan.path.exists()
    assert artifacts.interface_spec.path.exists()
    assert artifacts.invocation_manifest.path.exists()
    assert artifacts.public_package_plan.path.exists()
    assert artifacts.service_protocol_plan.path.exists()
    assert artifacts.interface_spec.relpath == "runtime/api.interface_spec.json"
    assert (
        artifacts.invocation_manifest.relpath == "runtime/api.invocation_manifest.json"
    )
    assert (
        artifacts.public_package_plan.relpath == "runtime/api.public_package_plan.json"
    )
    assert (
        artifacts.service_protocol_plan.relpath
        == "runtime/api.service_protocol_plan.json"
    )
    interface_payload = artifacts.interface_spec.path.read_text(encoding="utf-8")
    invocation_payload = artifacts.invocation_manifest.path.read_text(encoding="utf-8")
    public_package_payload = artifacts.public_package_plan.path.read_text(
        encoding="utf-8"
    )
    service_protocol_payload = artifacts.service_protocol_plan.path.read_text(
        encoding="utf-8"
    )
    assert '"schema_version": 1' in interface_payload
    assert '"discriminant": "home_devices.lock_door.lock_door"' in interface_payload
    assert '"stream_mode": "server"' in interface_payload
    assert '"endpoint_ref": "home_devices.lock_door.lock_door"' in invocation_payload
    assert '"client_operation": "invoke_api_endpoint"' in invocation_payload
    assert '"aware_package_kind": "api_public_package"' in public_package_payload
    assert (
        '"discriminant": "home_devices.lock_door.lock_door"' in public_package_payload
    )
    assert '"aware_package_kind": "api_service_protocol"' in service_protocol_payload
    assert '"fulfillment_bindings"' in service_protocol_payload


def test_compile_api_workspace_materializes_service_protocol_with_public_package_dependency(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    spec_text = toml_path.read_text(encoding="utf-8")
    _ = toml_path.write_text(
        spec_text.replace(
            "[build]\n", '[build]\ncompilation_mode = "api_ontology"\n', 1
        ),
        encoding="utf-8",
    )

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
        accessible_graphs=home_api_accessible_graphs(),
    )

    assert result.compile_plan is not None
    assert result.runtime_artifacts is not None
    assert result.public_package_materialization is not None
    assert result.service_protocol_materialization is not None
    assert (
        result.service_protocol_materialization.public_package_materialization
        == result.public_package_materialization
    )
