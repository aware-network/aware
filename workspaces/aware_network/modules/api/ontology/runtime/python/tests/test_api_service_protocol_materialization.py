from __future__ import annotations

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    home_api_accessible_graphs,
    write_home_api_dependency_runtime_artifacts,
)
from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
import json  # noqa: E402


def _write_api_toml(
    root: Path,
    *,
    python_root_dir: str | None = None,
    public_package_package_dir: str | None = None,
    service_protocol_package_dir: str | None = None,
    public_package_root_dir: str | None = None,
    service_protocol_root_dir: str | None = None,
) -> Path:
    toml_path = root / "aware.api.toml"
    lines = [
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
    ]
    if python_root_dir is not None:
        lines.extend(
            [
                "[targets.python]",
                f'root_dir = "{python_root_dir}"',
                "",
            ]
        )
    if public_package_package_dir is not None:
        lines.extend(
            [
                "[targets.python.public_package]",
                f'package_dir = "{public_package_package_dir}"',
                "",
            ]
        )
    elif public_package_root_dir is not None:
        lines.extend(
            [
                "[targets.python.public_package]",
                f'root_dir = "{public_package_root_dir}"',
                "",
            ]
        )
    if service_protocol_package_dir is not None:
        lines.extend(
            [
                "[targets.python.service_protocol]",
                f'package_dir = "{service_protocol_package_dir}"',
                "",
            ]
        )
    elif service_protocol_root_dir is not None:
        lines.extend(
            [
                "[targets.python.service_protocol]",
                f'root_dir = "{service_protocol_root_dir}"',
                "",
            ]
        )
    lines.extend(
        [
            "[[dependencies]]",
            'package_name = "home-api"',
            "",
        ]
    )
    _ = toml_path.write_text("\n".join(lines), encoding="utf-8")
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
                "    map door_snapshot_by_label door.DoorSnapshot home.Door.label {",
                "        template {",
                '            "{label}"',
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


def _write_ontology_python_type_metadata(root: Path) -> None:
    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    metadata_root = ontology_root / "python" / "aware_home_ontology" / "_aware"
    metadata_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "language": "python",
        "classes": [
            {
                "class_config_id": "test-door-id",
                "module": "aware_home_ontology.home.door",
                "name": "Door",
            },
            {
                "class_config_id": "test-home-id",
                "module": "aware_home_ontology.home.home",
                "name": "Home",
            },
        ],
        "enums": [],
    }
    _ = (metadata_root / "python.models.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_compile_api_workspace_materializes_service_protocol_and_public_package_for_api_ontology_mode(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)
    _write_ontology_python_type_metadata(root)

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

    runtime_package_dir = root / ".aware" / "api" / "runtime" / "home-story-api"
    assert (
        result.service_protocol_materialization.runtime_package_dir
        == runtime_package_dir
    )
    assert (runtime_package_dir / "api.manifest.json").exists()
    assert (runtime_package_dir / "api.compile_plan.json").exists()
    assert (runtime_package_dir / "api.interface_spec.json").exists()
    assert (runtime_package_dir / "api.invocation_manifest.json").exists()
    assert (runtime_package_dir / "api.public_package_plan.json").exists()
    assert (runtime_package_dir / "api.service_protocol_plan.json").exists()

    public_package_root = root / "python" / "aware_home_story_api"
    public_import_root = public_package_root / "aware_home_story_api"
    assert (public_import_root / "client.py").exists()
    assert (public_import_root / "_bindings.py").exists()
    assert (public_import_root / "models" / "lock_door.py").exists()
    assert (public_import_root / "_aware" / "python.bootstrap.json").exists()
    public_models_payload = json.loads(
        (public_import_root / "_aware" / "python.models.json").read_text(
            encoding="utf-8"
        )
    )
    assert {item["module"] for item in public_models_payload["classes"]} == {
        "aware_home_story_api.models.door_snapshot",
        "aware_home_story_api.models.lock_door",
        "aware_home_story_api.models.lock_door_result",
    }
    public_node_paths_payload = json.loads(
        (public_import_root / "_aware" / "ocg.node_paths.python.json").read_text(
            encoding="utf-8"
        )
    )
    assert {item["relative_path"] for item in public_node_paths_payload["nodes"]} == {
        "models/door_snapshot.py",
        "models/lock_door.py",
        "models/lock_door_result.py",
    }

    runtime_public_import_root = (
        runtime_package_dir
        / "public_package"
        / "python"
        / "package"
        / "aware_home_story_api"
    )
    assert (runtime_public_import_root / "client.py").exists()
    assert (runtime_public_import_root / "_bindings.py").exists()
    assert (runtime_public_import_root / "models" / "lock_door.py").exists()
    assert (runtime_public_import_root / "_aware" / "python.bootstrap.json").exists()
    runtime_public_models_payload = json.loads(
        (runtime_public_import_root / "_aware" / "python.models.json").read_text(
            encoding="utf-8"
        )
    )
    assert {item["module"] for item in runtime_public_models_payload["classes"]} == {
        "aware_home_story_api.models.door_snapshot",
        "aware_home_story_api.models.lock_door",
        "aware_home_story_api.models.lock_door_result",
    }

    service_package_root = root / "python" / "aware_home_story_protocol"
    service_import_root = service_package_root / "aware_home_story_protocol"
    assert (service_import_root / "protocols.py").exists()
    assert (service_import_root / "__init__.py").exists()
    assert not (service_import_root / "models").exists()
    assert not (service_import_root / "_aware" / "python.models.json").exists()
    assert not (service_import_root / "_aware" / "ocg.node_paths.python.json").exists()
    bootstrap_payload = json.loads(
        (service_import_root / "_aware" / "python.bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert bootstrap_payload["package_prefix"] == "aware_home_story_protocol"
    assert bootstrap_payload["dependency_import_roots"] == ["aware_home_api"]

    runtime_service_import_root = (
        runtime_package_dir
        / "service_protocol"
        / "python"
        / "package"
        / "aware_home_story_protocol"
    )
    assert (runtime_service_import_root / "protocols.py").exists()
    assert (runtime_service_import_root / "__init__.py").exists()
    assert not (runtime_service_import_root / "_aware" / "python.models.json").exists()
    assert not (
        runtime_service_import_root / "_aware" / "ocg.node_paths.python.json"
    ).exists()
    runtime_bootstrap_payload = json.loads(
        (runtime_service_import_root / "_aware" / "python.bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert runtime_bootstrap_payload["package_prefix"] == "aware_home_story_protocol"
    assert runtime_bootstrap_payload["dependency_import_roots"] == ["aware_home_api"]

    protocols_text = (service_import_root / "protocols.py").read_text(encoding="utf-8")
    assert (
        "from aware_home_api.door.endpoints import DoorSnapshot, LockDoor, LockDoorResult"
        in protocols_text
    )
    assert "aware_home_story_api.models" not in protocols_text
    assert (
        "class HomeDevicesLockDoorLockDoorExecution(ServiceProtocolExecution, Protocol):"
        in protocols_text
    )
    assert "class HomeDevicesLockDoorLockDoorLockRequest(BaseModel):" in protocols_text
    assert "class HomeDevicesLockDoorLockDoorLockResponse(BaseModel):" in protocols_text
    assert "async def lock(" in protocols_text
    assert "request: HomeDevicesLockDoorLockDoorLockRequest" in protocols_text
    assert (
        'execution_protocol_ref="protocols.HomeDevicesLockDoorLockDoorExecution"'
        in protocols_text
    )
    assert 'graph_function_python_ref="aware_home.home.Door.lock"' in protocols_text
    assert "class AwareHomeStoryServiceProtocol(Protocol):" in protocols_text
    assert "HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_PROTOCOL_BINDING" in protocols_text
    assert "async def invoke_home_devices__lock_door__lock_door(" in protocols_text
    assert "request: BaseModel" in protocols_text
    assert "execution: ServiceProtocolExecution | None = None" in protocols_text
    assert "typed_request = LockDoor.model_validate(request)" in protocols_text
    assert "def stream_invoke_home_devices__lock_door__lock_door(" in protocols_text
    assert "typed_request = LockDoor.model_validate(request)" in protocols_text
    assert "def stream_lock_door(" in protocols_text
    assert (
        "self, request: LockDoor, execution: HomeDevicesLockDoorLockDoorExecution"
        in protocols_text
    )
    assert "-> AsyncIterator[HomeDevicesLockDoorLockDoorStreamEvent]" in protocols_text
    assert (
        "stream_invoke=stream_invoke_home_devices__lock_door__lock_door,"
        in protocols_text
    )
    assert "invoke=invoke_home_devices__lock_door__lock_door," in protocols_text
    assert (
        "def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:"
        in protocols_text
    )
    assert "required_fields = [" in protocols_text
    assert "field_name = required_fields[0]" in protocols_text
    assert (
        "return HomeDevicesLockDoorLockDoorLockResponse.model_validate("
        in protocols_text
    )
    assert "_coerce_model_payload(" in protocols_text
    assert "model_cls=HomeDevicesLockDoorLockDoorLockResponse" in protocols_text

    pyproject_text = (service_package_root / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'name = "aware_home_story_protocol"' in pyproject_text
    assert '"aware_home_story_api"' not in pyproject_text
    assert '"aware_home_api"' in pyproject_text
    assert '"aware_home_ontology"' in pyproject_text

    public_result = result.public_package_materialization.materialization_result
    assert public_result.package_outcomes[0].package_name == "aware_home_story_api"

    service_result = result.service_protocol_materialization.materialization_result
    assert (
        service_result.package_outcomes[0].package_name == "aware_home_story_protocol"
    )

    for stale_root in (service_import_root, runtime_service_import_root):
        stale_artifacts_dir = stale_root / "_aware"
        (stale_artifacts_dir / "python.models.json").write_text(
            '{"language": "python", "classes": [], "enums": []}\n',
            encoding="utf-8",
        )
        (stale_artifacts_dir / "ocg.node_paths.python.json").write_text(
            '{"language": "python", "nodes": []}\n',
            encoding="utf-8",
        )

    rerun = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
        accessible_graphs=home_api_accessible_graphs(),
    )
    assert rerun.service_protocol_materialization is not None
    assert not (service_import_root / "_aware" / "python.models.json").exists()
    assert not (service_import_root / "_aware" / "ocg.node_paths.python.json").exists()
    assert not (runtime_service_import_root / "_aware" / "python.models.json").exists()
    assert not (
        runtime_service_import_root / "_aware" / "ocg.node_paths.python.json"
    ).exists()


def test_compile_api_workspace_honors_authored_python_target_root_dirs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        public_package_root_dir="python/custom_public",
        service_protocol_root_dir="python/custom_protocol",
    )
    _write_api_source(root)
    _write_ontology_python_type_metadata(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
        accessible_graphs=home_api_accessible_graphs(),
    )

    assert result.public_package_materialization is not None
    assert result.service_protocol_materialization is not None
    assert result.public_package_materialization.render_job.target.package_root == (
        root / "python" / "custom_public"
    )
    assert result.service_protocol_materialization.render_job.target.package_root == (
        root / "python" / "custom_protocol"
    )
    assert (
        root / "python" / "custom_public" / "aware_home_story_api" / "client.py"
    ).exists()
    assert (
        root
        / "python"
        / "custom_protocol"
        / "aware_home_story_protocol"
        / "protocols.py"
    ).exists()


def test_compile_api_workspace_honors_python_language_root_and_product_package_dirs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        python_root_dir="generated/python",
        public_package_package_dir="custom_public",
        service_protocol_package_dir="custom_protocol",
    )
    _write_api_source(root)
    _write_ontology_python_type_metadata(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
        accessible_graphs=home_api_accessible_graphs(),
    )

    assert result.public_package_materialization is not None
    assert result.service_protocol_materialization is not None
    assert result.public_package_materialization.render_job.target.package_root == (
        root / "generated" / "python" / "custom_public"
    )
    assert result.service_protocol_materialization.render_job.target.package_root == (
        root / "generated" / "python" / "custom_protocol"
    )
    assert (
        root
        / "generated"
        / "python"
        / "custom_public"
        / "aware_home_story_api"
        / "client.py"
    ).exists()
    assert (
        root
        / "generated"
        / "python"
        / "custom_protocol"
        / "aware_home_story_protocol"
        / "protocols.py"
    ).exists()
