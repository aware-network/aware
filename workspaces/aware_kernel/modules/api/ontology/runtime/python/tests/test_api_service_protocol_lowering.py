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
from aware_api_runtime.ir import (  # noqa: E402
    build_api_compile_plan,
    emit_api_runtime_artifacts,
)
from aware_api_runtime.compile import (
    compile_api_workspace,
)  # noqa: E402
from aware_api_runtime.models import (
    ProjectionOwnedClassTruth,
)  # noqa: E402
from aware_api_runtime.packages import (  # noqa: E402
    build_api_service_protocol_lowering_handoff,
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


def test_emit_service_protocol_plan_artifact_and_build_lowering_handoff(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(toml_path=toml_path, repo_root=root)
    compile_plan = build_api_compile_plan(
        snapshot=result.snapshot, projection_truth_by_name=_projection_truth()
    )
    runtime_artifacts = emit_api_runtime_artifacts(
        plan=compile_plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )
    service_plan = build_api_service_protocol_plan(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        api_ontology=compile_plan.api_ontology,
    )

    assert runtime_artifacts.service_protocol_plan.path.exists()
    assert (
        runtime_artifacts.service_protocol_plan.relpath
        == "runtime/api.service_protocol_plan.json"
    )
    payload = runtime_artifacts.service_protocol_plan.path.read_text(encoding="utf-8")
    assert '"aware_package_kind": "api_service_protocol"' in payload
    assert '"endpoint_ref": "home_devices.lock_door.lock_door"' in payload
    assert '"fulfillment_bindings"' in payload
    assert '"graph_capability_function_name": "lock"' in payload
    assert '"graph_function_python_ref": "aware_home.home.Door.lock"' in payload
    assert '"graph_function_runtime_target": null' in payload

    handoff = build_api_service_protocol_lowering_handoff(
        plan=service_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        service_protocol_plan_artifact=runtime_artifacts.service_protocol_plan,
    )

    assert handoff.schema_version == 1
    assert handoff.package_name == "home-story-api"
    assert handoff.fqn_prefix == "aware_home_story_api"
    assert handoff.backend_handoff.materialization_source == MaterializationSource.api
    assert (
        handoff.backend_handoff.expected_renderer_profile
        == API_SERVICE_PROTOCOL_RENDERER_PROFILE
    )
    assert tuple(ref.kind for ref in handoff.runtime_artifacts) == (
        "api.interface_spec",
        "api.invocation_manifest",
        "api.public_package_plan",
        "api.service_protocol_plan",
    )
    assert tuple(ref.relpath for ref in handoff.runtime_artifacts) == (
        "runtime/api.interface_spec.json",
        "runtime/api.invocation_manifest.json",
        "runtime/api.public_package_plan.json",
        "runtime/api.service_protocol_plan.json",
    )
