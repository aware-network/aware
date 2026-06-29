from __future__ import annotations

from pathlib import Path
import sys

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
from aware_api_runtime.invocation.builder import (  # noqa: E402
    build_api_invocation_manifest,
    emit_api_invocation_manifest_artifact,
)
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


def test_build_api_invocation_manifest_from_compile_plan(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=_projection_truth()
    )

    manifest = build_api_invocation_manifest(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ownership=plan.api_ownership,
    )

    assert manifest.schema_version == 1
    assert manifest.package_name == "home-story-api"
    assert manifest.fqn_prefix == "aware_home_story_api"
    assert len(manifest.apis) == 1
    endpoint = manifest.apis[0].capabilities[0].endpoints[0]
    assert endpoint.endpoint_ref == "home_devices.lock_door.lock_door"
    assert endpoint.discriminant == "home_devices.lock_door.lock_door"
    assert endpoint.invocation_kind == "shared_client_endpoint"
    assert endpoint.client_backend == "aware_api.invoker.AwareApiEndpointInvoker"
    assert endpoint.client_operation == "invoke_api_endpoint"
    assert endpoint.addressing_strategy == "session_bound"
    assert endpoint.request.class_ref == "aware_home_api.door.LockDoor"
    assert endpoint.request.python_model_ref is None
    assert endpoint.response is not None
    assert endpoint.response.class_ref == "aware_home_api.door.LockDoorResult"
    assert endpoint.response.python_model_ref is None
    assert endpoint.stream is not None
    assert endpoint.stream.stream_mode == "server"
    assert endpoint.stream.events[0].python_model_ref is None
    assert len(endpoint.fulfillment_bindings) == 1
    binding = endpoint.fulfillment_bindings[0]
    assert binding.name == "lock"
    assert binding.graph_target == "aware_home"
    assert binding.graph_capability_function_name == "lock"


def test_emit_api_invocation_manifest_artifact(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=_projection_truth()
    )
    manifest = build_api_invocation_manifest(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ownership=plan.api_ownership,
    )

    artifact = emit_api_invocation_manifest_artifact(
        manifest=manifest,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )

    assert artifact.path.exists()
    assert artifact.relpath == "runtime/api.invocation_manifest.json"
    assert len(artifact.hash_sha256) == 64
    payload = artifact.path.read_text(encoding="utf-8")
    assert '"endpoint_ref"' in payload
    assert '"invoke_api_endpoint"' in payload
    assert '"graph_capability_function_name": "lock"' in payload
