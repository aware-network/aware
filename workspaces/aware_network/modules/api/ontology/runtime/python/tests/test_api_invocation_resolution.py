from __future__ import annotations

from pathlib import Path
import sys
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from _api_runtime_test_paths import (  # noqa: E402
    API_RUNTIME_ROOT,
    REPO_ROOT as _REPO_ROOT,
)

_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_API_RUNTIME_ROOT_STR = str(API_RUNTIME_ROOT)
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    write_home_api_dependency_runtime_artifacts,
)
from aware_api_runtime.ir import build_api_compile_plan  # noqa: E402
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.invocation import (  # noqa: E402
    MaterializedApiCallBinding,
    build_api_invocation_resolution_index,
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.models import ProjectionOwnedClassTruth  # noqa: E402


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
                "class DoorDelta {",
                "    changed_field String",
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
                '            """Locks the selected door."""',
                "            response aware_home_api.door.LockDoorResult;",
                "            stream server {",
                '                """Door updates."""',
                "                event snapshot aware_home_api.door.DoorSnapshot;",
                "                event delta aware_home_api.door.DoorDelta;",
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


def _dependency_class_config_ids() -> dict[str, UUID]:
    class_refs = (
        "aware_home_api.door.LockDoor",
        "aware_home_api.door.LockDoorResult",
        "aware_home_api.door.DoorSnapshot",
        "aware_home_api.door.DoorDelta",
    )
    return {
        class_ref: uuid5(NAMESPACE_URL, f"aware-api-invocation-test:{class_ref}")
        for class_ref in class_refs
    }


def _plan(tmp_path: Path):
    toml_path = _write_api_toml(tmp_path)
    _write_api_source(tmp_path)
    result = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path)
    return build_api_compile_plan(
        snapshot=result.snapshot,
        projection_truth_by_name=_projection_truth(),
        dependency_class_config_ids=_dependency_class_config_ids(),
    )


def test_resolve_api_invocation_ir_by_endpoint_ref(tmp_path: Path) -> None:
    plan = _plan(tmp_path)

    ir = resolve_api_invocation_ir(
        api_ownership=plan.api_ownership,
        endpoint_ref="home_devices.lock_door.lock_door",
        request_payload={"label": "front-door"},
    )

    assert ir.endpoint_ref == "home_devices.lock_door.lock_door"
    assert ir.discriminant == "home_devices.lock_door.lock_door"
    assert ir.request_class_ref == "aware_home_api.door.LockDoor"
    assert ir.request_class_config_id is not None
    assert dict(ir.request_payload) == {"label": "front-door"}
    assert ir.response_class_ref == "aware_home_api.door.LockDoorResult"
    assert ir.stream is not None
    assert ir.stream.stream_mode == "server"
    assert [event.kind for event in ir.stream.events] == ["delta", "snapshot"]
    assert len(ir.fulfillment_bindings) == 1
    assert ir.fulfillment_bindings[0].graph_target == "aware_home"
    assert ir.fulfillment_bindings[0].graph_capability_function_name == "lock"


def test_build_resolved_api_invocation_envelope_from_materialized_call(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    ir = resolve_api_invocation_ir(
        api_ownership=plan.api_ownership,
        discriminant="home_devices.lock_door.lock_door",
        request_payload={"label": "front-door"},
    )
    binding = MaterializedApiCallBinding(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:test-request",
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:test-api-call",
    )

    envelope = build_resolved_api_invocation_envelope(ir=ir, materialized_call=binding)

    assert envelope.api_call_id == binding.api_call_id
    assert envelope.api_capability_endpoint_id == binding.api_capability_endpoint_id
    assert envelope.request_hash == "sha256:test-request"
    assert envelope.commit_id == binding.commit_id
    assert envelope.head_commit_id == binding.head_commit_id
    assert envelope.branch_id == binding.branch_id
    assert envelope.projection_hash == "sha256:test-api-call"
    assert envelope.request_model_id == binding.request_model_id
    assert envelope.request_class_config_id == binding.request_class_config_id
    assert envelope.request_class_ref == "aware_home_api.door.LockDoor"
    assert envelope.endpoint_ref == "home_devices.lock_door.lock_door"
    assert envelope.description == "Locks the selected door."


def test_build_resolved_api_invocation_envelope_fails_closed_without_commit_locator(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    ir = resolve_api_invocation_ir(
        api_ownership=plan.api_ownership,
        discriminant="home_devices.lock_door.lock_door",
        request_payload={"label": "front-door"},
    )
    binding = MaterializedApiCallBinding(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:test-request",
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
    )

    with pytest.raises(RuntimeError, match="commit-backed ApiCall handoff"):
        build_resolved_api_invocation_envelope(ir=ir, materialized_call=binding)


def test_api_invocation_resolution_fails_closed_for_lookup_contract(
    tmp_path: Path,
) -> None:
    plan = _plan(tmp_path)
    index = build_api_invocation_resolution_index(api_ownership=plan.api_ownership)

    with pytest.raises(KeyError, match="Unknown endpoint ref"):
        index.require_endpoint_by_ref("home_devices.lock_door.missing")

    with pytest.raises(ValueError, match="Exactly one endpoint locator is required"):
        resolve_api_invocation_ir(
            api_ownership=plan.api_ownership,
            endpoint_ref="home_devices.lock_door.lock_door",
            discriminant="home_devices.lock_door.lock_door",
        )
