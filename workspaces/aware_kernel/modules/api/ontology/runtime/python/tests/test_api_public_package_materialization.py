from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from typing import cast
from unittest.mock import patch

import msgpack
import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from _api_runtime_test_paths import REPO_ROOT as _REPO_ROOT

_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from api_runtime_fixture_artifacts import (  # noqa: E402
    write_home_api_dependency_runtime_artifacts,
)
from aware_utils.pydantic.package_bootstrap import (
    bootstrap_pydantic_package_from_artifacts,
)  # noqa: E402
from aware_api_runtime.compile import (
    compile_api_product_runtime_from_compile_plan_payload,
    compile_api_workspace as _compile_api_workspace,
    refresh_api_workspace_from_runtime_artifacts,
)  # noqa: E402
from aware_api_runtime.compile_materialization import (  # noqa: E402
    build_generated_api_compile_plan_accessible_graphs,
)
from aware_api_runtime.packages.materialization import (  # noqa: E402
    _AccessibleDependencyPackage,
    _build_accessible_dependency_packages,
    _dart_public_package_path_dependencies,
    _python_distribution_name_for_dependency_package,
    materialize_api_dto_packages,
)
from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: E402
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from aware_api_runtime.workspace import APIWorkspace  # noqa: E402


def compile_api_workspace(**kwargs: object):
    kwargs.setdefault("dependency_graph_mode", "meta_runtime")
    kwargs.setdefault("kernel_repo_root", _REPO_ROOT)
    repo_root = Path(cast(Path | str, kwargs["repo_root"])).resolve()
    kwargs.setdefault("repo_root", repo_root)
    previous_aware_root = os.environ.get("AWARE_ROOT")
    os.environ.setdefault("AWARE_ROOT", str(repo_root / ".aware-root"))
    try:
        return _compile_api_workspace(**kwargs)
    finally:
        if previous_aware_root is None:
            os.environ.pop("AWARE_ROOT", None)
        else:
            os.environ["AWARE_ROOT"] = previous_aware_root


def _accessible_graphs_from_compile_result(
    result: object,
) -> tuple[ObjectConfigGraph, ...]:
    runtime_artifacts = getattr(result, "runtime_artifacts", None)
    assert runtime_artifacts is not None
    return load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=runtime_artifacts.compile_plan.path.parent,
    )


def _write_api_toml(
    root: Path,
    *,
    api_dto_semantic_export: bool = False,
    include_api_dependency: bool = True,
    python_root_dir: str | None = None,
    public_package_package_dir: str | None = None,
    public_package_root_dir: str | None = None,
    dart_root_dir: str | None = None,
    dart_public_package_package_dir: str | None = None,
    dart_public_package_root_dir: str | None = None,
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
    if dart_root_dir is not None:
        lines.extend(
            [
                "[targets.dart]",
                f'root_dir = "{dart_root_dir}"',
                "",
            ]
        )
    if dart_public_package_package_dir is not None:
        lines.extend(
            [
                "[targets.dart.public_package]",
                f'package_dir = "{dart_public_package_package_dir}"',
                "",
            ]
        )
    elif dart_public_package_root_dir is not None:
        lines.extend(
            [
                "[targets.dart.public_package]",
                f'root_dir = "{dart_public_package_root_dir}"',
                "",
            ]
        )
    if include_api_dependency:
        lines.extend(
            [
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        )
    if api_dto_semantic_export:
        lines.extend(
            [
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "home-api"',
                'manifest_path = "apis/types/home/aware.toml"',
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
                "enum HomeStatus {",
                "    ready",
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
                "    context door.LockDoorContext",
                "    mode door.DoorMode",
                "}",
                "",
                "class LockDoorContext {",
                "    actor_label String",
                "    status_ref aware_home.home.HomeStatus",
                "}",
                "",
                "enum DoorMode {",
                "    open",
                "    class",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted String",
                "}",
                "",
                "class DoorSnapshot {",
                "    label String",
                "    is_locked String",
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


def _write_home_ontology_python_stub(root: Path) -> Path:
    package_root = root / "python" / "aware_home_ontology"
    import_root = package_root / "aware_home_ontology"
    home_root = import_root / "home"
    home_root.mkdir(parents=True, exist_ok=True)
    (import_root / "__init__.py").write_text("", encoding="utf-8")
    (home_root / "__init__.py").write_text("", encoding="utf-8")
    (home_root / "home.py").write_text(
        "\n".join(
            [
                "from enum import Enum",
                "",
                "",
                "class HomeStatus(str, Enum):",
                '    ready = "ready"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return package_root


def _write_cross_api_dto_dependency_source(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "hub-service-api"',
                'fqn_prefix = "aware_hub_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "api_ontology"',
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_hub_service_api"',
                "",
                "[targets.python.service_protocol]",
                'package_dir = "aware_hub_service_protocol"',
                "",
                "[[dependencies]]",
                'package_name = "hub-service-dto"',
                "",
                "[[dependencies]]",
                'package_name = "code-service-dto"',
                "",
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "hub-service-dto"',
                'manifest_path = "dto/aware.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    hub_root = root / "dto"
    (hub_root / "aware" / "hub").mkdir(parents=True, exist_ok=True)
    (hub_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "hub-service-dto"',
                'fqn_prefix = "aware_hub_service_dto"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_hub_service_dto"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (hub_root / "aware" / "hub" / "artifact.aware").write_text(
        "\n".join(
            [
                "class PublishHubArtifactRequest {",
                "    artifact_key String",
                "}",
                "",
                "class PublishHubArtifactResponse {",
                "    artifact_key String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    code_root = root / "apis" / "code" / "dto"
    (code_root / "aware" / "code").mkdir(parents=True, exist_ok=True)
    (code_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "code-service-dto"',
                'fqn_prefix = "aware_code_service_dto"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_code_service_dto"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (code_root / "aware" / "code" / "package_distribution.aware").write_text(
        "\n".join(
            [
                "class DescribeCodePackageRequest {",
                "    package_name String",
                "}",
                "",
                "class DescribeCodePackageResponse {",
                "    package_name String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "hub.apis.aware").write_text(
        "\n".join(
            [
                "api hub {",
                "    capability artifact {",
                "        endpoint publish aware_hub_service_dto.hub.PublishHubArtifactRequest {",
                "            response aware_hub_service_dto.hub.PublishHubArtifactResponse;",
                "        }",
                "    }",
                "    capability code_package {",
                "        endpoint describe aware_code_service_dto.code.DescribeCodePackageRequest {",
                "            response aware_code_service_dto.code.DescribeCodePackageResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_multi_capability_dart_api_source(root: Path) -> None:
    _write_api_type_package(root)

    ontology_door = (
        root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / "aware"
        / "home"
        / "door.aware"
    )
    _ = ontology_door.write_text(
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
                "",
                "    fn unlock(",
                "        force Bool = false",
                "    ) -> Bool {",
                '        """Unlock this door."""',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "types" / "home" / "aware" / "door"
    _ = (api_root / "context.aware").write_text(
        "\n".join(
            [
                "class LockDoorContext {",
                "    actor_label String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (api_root / "endpoints.aware").write_text(
        "\n".join(
            [
                "class LockDoor {",
                "    label String",
                "    context door.LockDoorContext",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted Bool",
                "}",
                "",
                "class UnlockDoor {",
                "    label String",
                "}",
                "",
                "class UnlockDoorResult {",
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
                "        }",
                "    }",
                "    capability unlock_door {",
                '        """Unlock the front door."""',
                "        endpoint unlock_door aware_home_api.door.UnlockDoor {",
                '            """Unlock command."""',
                "            response aware_home_api.door.UnlockDoorResult;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability lock_door {",
                "            function lock aware_home.home.Door.lock;",
                "        }",
                "        capability unlock_door {",
                "            function unlock aware_home.home.Door.unlock;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_augmented_dart_api_source(root: Path) -> None:
    _write_api_type_package(root)

    api_root = root / "apis" / "types" / "home" / "aware" / "door"
    _ = (api_root / "endpoints.aware").write_text(
        "\n".join(
            [
                "class DoorSnapshot {",
                "    label String",
                "    is_locked String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (api_root / "service_operation.aware").write_text(
        "\n".join(
            [
                "class HomeDeviceRequest {",
                "    request_id UUID?",
                "}",
                "",
                "class HomeDeviceResponse {",
                "    success Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (api_root / "action.aware").write_text(
        "\n".join(
            [
                "class LockDoor augment door.HomeDeviceRequest {",
                "    label String",
                "}",
                "",
                "class LockDoorResult augment door.HomeDeviceResponse {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

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


def _write_placeholder_dart_part_files(*, pkg_root: Path, **_: object) -> None:
    part_re = re.compile(
        r"""^\s*part\s+['"]([^'"]+\.(?:g|freezed)\.dart)['"]\s*;""", re.MULTILINE
    )
    for source in (pkg_root / "lib").rglob("*.dart"):
        if source.name.endswith((".g.dart", ".freezed.dart")):
            continue
        for part in part_re.findall(source.read_text(encoding="utf-8")):
            part_path = source.parent / part
            part_path.write_text("// test placeholder\n", encoding="utf-8")


def _write_placeholder_dart_part_files_for_assertion(
    *,
    package_root: Path,
) -> None:
    _write_placeholder_dart_part_files(pkg_root=package_root)


def test_compile_api_workspace_materializes_public_package_for_api_ontology_mode(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )

    assert result.compile_plan is not None
    assert result.runtime_artifacts is not None
    assert result.public_package_materialization is not None

    runtime_package_dir = root / ".aware" / "api" / "runtime" / "home-story-api"
    assert (
        result.public_package_materialization.runtime_package_dir == runtime_package_dir
    )
    assert (runtime_package_dir / "api.manifest.json").exists()
    assert (runtime_package_dir / "api.compile_plan.json").exists()
    assert (runtime_package_dir / "api.interface_spec.json").exists()
    assert (runtime_package_dir / "api.invocation_manifest.json").exists()
    assert (runtime_package_dir / "api.public_package_plan.json").exists()

    package_root = root / "python" / "aware_home_story_api"
    import_root = package_root / "aware_home_story_api"
    assert (import_root / "client.py").exists()
    assert (import_root / "_bindings.py").exists()
    assert (import_root / "models" / "lock_door.py").exists()
    assert (import_root / "models" / "lock_door_result.py").exists()
    assert (import_root / "models" / "door_snapshot.py").exists()
    assert (import_root / "__init__.py").exists()
    assert (import_root / "_aware" / "python.bootstrap.json").exists()

    runtime_import_root = (
        runtime_package_dir
        / "public_package"
        / "python"
        / "package"
        / "aware_home_story_api"
    )
    assert (runtime_import_root / "client.py").exists()
    assert (runtime_import_root / "_bindings.py").exists()
    assert (runtime_import_root / "models" / "lock_door.py").exists()
    assert (runtime_import_root / "models" / "lock_door_result.py").exists()
    assert (runtime_import_root / "models" / "door_snapshot.py").exists()
    assert (runtime_import_root / "__init__.py").exists()
    assert (runtime_import_root / "_aware" / "python.bootstrap.json").exists()

    client_text = (import_root / "client.py").read_text(encoding="utf-8")
    assert "from aware_api import AwareApiEndpointInvoker" in client_text
    assert "class AwareHomeStoryApiClient:" in client_text
    assert "def __init__(self, client: AwareApiEndpointInvoker) -> None:" in client_text
    assert "from .models.lock_door import LockDoor" in client_text
    assert (
        "from .aware_home_story_api.models.lock_door import LockDoor" not in client_text
    )

    bindings_text = (import_root / "_bindings.py").read_text(encoding="utf-8")
    assert "HOME_DEVICES__LOCK_DOOR__LOCK_DOOR_ENDPOINT_REF" in bindings_text
    assert "home_devices.lock_door.lock_door" in bindings_text

    pyproject_text = (package_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "aware_home_story_api"' in pyproject_text
    assert '"aware-api-client"' in pyproject_text
    assert '"aware-types"' in pyproject_text

    materialization_result = (
        result.public_package_materialization.materialization_result
    )
    assert (
        materialization_result.package_outcomes[0].package_name
        == "aware_home_story_api"
    )

    sys_path_snapshot = list(sys.path)
    try:
        sys.path.insert(0, str(package_root))
        bootstrap_pydantic_package_from_artifacts(
            package_prefix="aware_home_story_api",
            strict_imports=True,
        )
    finally:
        sys.path[:] = sys_path_snapshot


def test_compile_plan_product_runtime_manifest_preserves_source_api_toml_path(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, public_package_root_dir="python/custom_public")
    _write_api_source(root)

    baseline = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
    )
    assert baseline.runtime_artifacts is not None
    compile_plan_path = baseline.runtime_artifacts.compile_plan.path
    compile_plan_payload = json.loads(compile_plan_path.read_text(encoding="utf-8"))
    snapshot = APIWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=_accessible_graphs_from_compile_result(baseline),
    )
    accessible_graphs = build_generated_api_compile_plan_accessible_graphs(
        compile_plan_payload=compile_plan_payload,
        accessible_graphs=tuple(package.graph for package in dependency_packages),
    )

    compile_result = compile_api_product_runtime_from_compile_plan_payload(
        compile_plan_payload=compile_plan_payload,
        repo_root=root,
        compile_plan_path=compile_plan_path,
        source_api_toml_path=toml_path,
        accessible_graphs=accessible_graphs,
    )

    assert compile_result.public_package_materialization is not None
    assert (
        compile_result.public_package_materialization.render_job.target.package_root
        == (root / "python" / "custom_public").resolve()
    )
    assert (
        root / "python" / "custom_public" / "aware_home_story_api" / "client.py"
    ).exists()

    runtime_manifest_path = (
        root / ".aware" / "api" / "runtime" / "home-story-api" / "api.manifest.json"
    )
    runtime_manifest = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    assert runtime_manifest["api_toml_path"] == toml_path.resolve().as_posix()
    assert runtime_manifest["api_toml_relpath"] == "aware.api.toml"
    assert runtime_manifest["public_package_package_root_relpath"] == (
        "python/custom_public"
    )
    assert runtime_manifest["compile_plan_artifact_relpath"] == (
        ".aware/api/runtime/home-story-api/api.compile_plan.json"
    )


def test_compile_api_workspace_materializes_api_dto_python_package_from_semantic_export(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, api_dto_semantic_export=True)
    _write_api_source(root)
    api_source_path = root / "apis" / "bindings" / "home.apis.aware"
    api_source_path.write_text(
        api_source_path.read_text(encoding="utf-8").replace(
            "aware_home_api.door.",
            "aware_home_api.default.door.",
        ),
        encoding="utf-8",
    )

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
    )

    assert len(result.api_dto_package_materializations) == 1
    dto_result = result.api_dto_package_materializations[0]
    assert dto_result.semantic_package_export.package_name == "home-api"
    assert dto_result.import_root == "aware_home_api"

    package_root = root / "python" / "aware_home_api"
    import_root = package_root / "aware_home_api"
    assert dto_result.package_root == package_root
    endpoints_path = import_root / "door" / "endpoints.py"
    assert endpoints_path.exists()
    assert (import_root / "_aware" / "python.models.json").exists()
    assert (import_root / "py.typed").exists()

    endpoints_text = endpoints_path.read_text(encoding="utf-8")
    enum_text = endpoints_text
    assert 'class_ = "class"' in enum_text
    lock_context_text = endpoints_text
    assert "import HomeStatus" in lock_context_text
    assert "status_ref: HomeStatus" in lock_context_text

    models_manifest = json.loads(
        (import_root / "_aware" / "python.models.json").read_text(encoding="utf-8")
    )
    class_refs = {
        entry["name"]: entry["aware_class_ref"] for entry in models_manifest["classes"]
    }
    assert class_refs["LockDoor"] == "aware_home_api.door.LockDoor"

    pyproject_text = (package_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "aware_home_api"' in pyproject_text
    assert '"aware-types"' in pyproject_text
    assert '"aware-utils"' in pyproject_text
    assert '"pydantic>=2.8.0,<3.0.0"' in pyproject_text

    init_text = (import_root / "__init__.py").read_text(encoding="utf-8")
    assert "DTO-only packages do NOT install ORM runtime artifacts" in init_text

    public_import_root = (
        root / "python" / "aware_home_story_api" / "aware_home_story_api"
    )
    assert (public_import_root / "client.py").exists()
    assert not (public_import_root / "models").exists()
    assert not (public_import_root / "_aware" / "python.models.json").exists()

    client_text = (public_import_root / "client.py").read_text(encoding="utf-8")
    assert (
        "from aware_home_api.door.endpoints import DoorSnapshot, LockDoor, LockDoorResult"
        in client_text
    )
    assert "aware_home_api.default" not in client_text
    assert "from .models.lock_door import LockDoor" not in client_text

    bindings_text = (public_import_root / "_bindings.py").read_text(encoding="utf-8")
    assert '"class_ref": "aware_home_api.door.LockDoor"' in bindings_text
    assert (
        '"python_model_ref": "aware_home_api.door.endpoints.LockDoor"' in bindings_text
    )
    assert "aware_home_story_api.models" not in bindings_text

    service_protocol_root = (
        root / "python" / "aware_home_story_protocol" / "aware_home_story_protocol"
    )
    protocol_text = (service_protocol_root / "protocols.py").read_text(encoding="utf-8")
    assert (
        "from aware_home_api.door.endpoints import DoorSnapshot, LockDoor, LockDoorResult"
        in protocol_text
    )
    assert "aware_home_api.default" not in protocol_text
    assert "aware_home_story_api.models" not in protocol_text

    protocol_pyproject_text = (
        service_protocol_root.parent / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert '"aware_home_api"' in protocol_pyproject_text
    assert '"aware_home_story_api"' not in protocol_pyproject_text


def test_api_dto_export_external_type_index_uses_source_layout_modules(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, api_dto_semantic_export=True)
    _write_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
    )

    assert len(result.api_dto_package_materializations) == 1
    import_root = root / "python" / "aware_home_api" / "aware_home_api"
    endpoints_path = import_root / "door" / "endpoints.py"
    assert endpoints_path.exists()
    assert not (import_root / "default" / "lock_door.py").exists()

    runtime_dir = root / ".aware" / "api" / "runtime" / "home-story-api"
    external_index = json.loads(
        (runtime_dir / "api.external_python_type_index.json").read_text(
            encoding="utf-8"
        )
    )
    modules_by_class_ref = {
        entry["class_ref"]: entry["module"]
        for entry in external_index["classes"].values()
        if "class_ref" in entry
    }
    assert modules_by_class_ref["aware_home_api.door.LockDoor"] == (
        "aware_home_api.door.endpoints"
    )
    assert modules_by_class_ref["aware_home_api.door.LockDoorResult"] == (
        "aware_home_api.door.endpoints"
    )

    public_import_root = (
        root / "python" / "aware_home_story_api" / "aware_home_story_api"
    )
    client_text = (public_import_root / "client.py").read_text(encoding="utf-8")
    assert (
        "from aware_home_api.door.endpoints import DoorSnapshot, LockDoor, LockDoorResult"
        in client_text
    )
    assert "aware_home_api.default" not in client_text

    protocol_root = (
        root / "python" / "aware_home_story_protocol" / "aware_home_story_protocol"
    )
    protocol_text = (protocol_root / "protocols.py").read_text(encoding="utf-8")
    assert (
        "from aware_home_api.door.endpoints import DoorSnapshot, LockDoor, LockDoorResult"
        in protocol_text
    )
    assert "aware_home_api.default" not in protocol_text


def test_api_dto_export_public_package_uses_declared_api_dto_dependencies(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_cross_api_dto_dependency_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
    )

    assert len(result.api_dto_package_materializations) == 1
    assert (
        result.api_dto_package_materializations[0].semantic_package_export.package_name
        == "hub-service-dto"
    )

    runtime_dir = root / ".aware" / "api" / "runtime" / "hub-service-api"
    external_index = json.loads(
        (runtime_dir / "api.external_python_type_index.json").read_text(
            encoding="utf-8"
        )
    )
    class_refs = {
        entry["class_ref"]
        for entry in external_index["classes"].values()
        if "class_ref" in entry
    }
    assert "aware_hub_service_dto.hub.PublishHubArtifactRequest" in class_refs
    assert "aware_code_service_dto.code.DescribeCodePackageRequest" in class_refs

    public_import_root = (
        root / "python" / "aware_hub_service_api" / "aware_hub_service_api"
    )
    client_text = (public_import_root / "client.py").read_text(encoding="utf-8")
    assert (
        "from aware_code_service_dto.code.package_distribution "
        "import DescribeCodePackageRequest"
    ) in client_text
    assert "from .models.describe_code_package_request" not in client_text

    public_pyproject = (
        root / "python" / "aware_hub_service_api" / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert '"aware_code_service_dto"' in public_pyproject
    assert '"aware_hub_service_dto"' in public_pyproject

    service_protocol_root = (
        root / "python" / "aware_hub_service_protocol" / "aware_hub_service_protocol"
    )
    protocol_text = (service_protocol_root / "protocols.py").read_text(encoding="utf-8")
    assert (
        "from aware_code_service_dto.code.package_distribution "
        "import DescribeCodePackageRequest"
    ) in protocol_text

    protocol_pyproject = (service_protocol_root.parent / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert '"aware_code_service_dto"' in protocol_pyproject
    assert '"aware_hub_service_dto"' in protocol_pyproject
    assert '"aware_hub_service_api"' not in protocol_pyproject


def test_compile_api_workspace_materializes_api_dto_export_without_dependency(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        api_dto_semantic_export=True,
        include_api_dependency=False,
    )
    _write_api_type_package(root)
    (root / "apis" / "bindings").mkdir(parents=True, exist_ok=True)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )

    assert len(result.api_dto_package_materializations) == 1
    dto_result = result.api_dto_package_materializations[0]
    assert dto_result.semantic_package_export.package_name == "home-api"
    assert dto_result.dependency_package.package_name == "home-api"

    package_root = root / "python" / "aware_home_api"
    import_root = package_root / "aware_home_api"
    assert dto_result.package_root == package_root
    assert (import_root / "door" / "endpoints.py").exists()
    assert not (import_root / "default" / "lock_door.py").exists()
    assert (package_root / "pyproject.toml").exists()


def test_api_dto_dependency_distribution_resolves_sibling_python_package(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "apis" / "code" / "dto"
    pyproject_path = (
        package_root.parent / "python" / "aware_code_service_dto" / "pyproject.toml"
    )
    pyproject_path.parent.mkdir(parents=True)
    pyproject_path.write_text(
        "\n".join(
            [
                "[project]",
                'name = "aware_code_service_dto"',
                'version = "0.1.0"',
            ]
        ),
        encoding="utf-8",
    )

    package = _AccessibleDependencyPackage(
        package_name="code-service-dto",
        package_kind="api",
        package_root=package_root,
        import_root="aware_code_service_dto",
        graph=cast(ObjectConfigGraph, object()),
    )

    assert (
        _python_distribution_name_for_dependency_package(package=package)
        == "aware_code_service_dto"
    )


def test_api_dto_materialization_uses_artifact_layout_with_precompiled_graph(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, api_dto_semantic_export=True)
    _write_api_source(root)
    baseline = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=_accessible_graphs_from_compile_result(baseline),
    )
    accessible_graphs = []
    for package in dependency_packages:
        graph = package.graph.model_copy(deep=True)
        if package.package_name == "home-api":
            for node in graph.object_config_graph_nodes:
                node.layouts = []
        accessible_graphs.append(graph)

    results = materialize_api_dto_packages(
        snapshot=snapshot,
        runtime_package_dir=root / ".aware" / "api" / "runtime" / "home-story-api",
        repo_root=root,
        accessible_graphs=tuple(accessible_graphs),
    )

    assert len(results) == 1
    package_root = root / "python" / "aware_home_api"
    import_root = package_root / "aware_home_api"
    lock_door_path = import_root / "default" / "lock_door.py"
    door_mode_path = import_root / "default" / "door_mode.py"
    assert lock_door_path.exists()
    assert door_mode_path.exists()
    assert not (import_root / "door" / "endpoints.py").exists()
    assert "class LockDoor(" in lock_door_path.read_text(encoding="utf-8")
    assert "class DoorMode(" in door_mode_path.read_text(encoding="utf-8")
    models_manifest = json.loads(
        (import_root / "_aware" / "python.models.json").read_text(encoding="utf-8")
    )
    class_refs = {
        entry["name"]: entry["aware_class_ref"] for entry in models_manifest["classes"]
    }
    assert class_refs["LockDoor"] == "aware_home_api.door.LockDoor"
    dependency_graph_cache = json.loads(
        (
            root
            / ".aware"
            / "api"
            / "runtime"
            / "home-story-api"
            / "api.accessible_dependency_graphs.json"
        ).read_text(encoding="utf-8")
    )
    assert dependency_graph_cache["dependency_source_digests"].keys() == {
        "home-api",
        "home-ontology",
    }
    assert {graph["fqn_prefix"] for graph in dependency_graph_cache["graphs"]} >= {
        "aware_home",
        "aware_home_api",
    }


def test_compile_api_workspace_honors_authored_public_package_root_dir(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, public_package_root_dir="python/custom_public")
    _write_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )

    assert result.public_package_materialization is not None
    package_root = root / "python" / "custom_public"
    import_root = package_root / "aware_home_story_api"
    assert (
        result.public_package_materialization.render_job.target.package_root
        == package_root
    )
    assert (import_root / "client.py").exists()


def test_compile_api_workspace_honors_python_language_root_and_product_package_dir(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        python_root_dir="generated/python",
        public_package_package_dir="custom_public",
    )
    _write_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )

    assert result.public_package_materialization is not None
    package_root = root / "generated" / "python" / "custom_public"
    import_root = package_root / "aware_home_story_api"
    assert (
        result.public_package_materialization.render_job.target.package_root
        == package_root
    )
    assert (import_root / "client.py").exists()


def test_compile_api_workspace_materializes_dart_public_package_when_requested(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_home_story_api",
    )
    _write_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
        public_package_target_language=CodeLanguage.dart,
        dependency_repo_roots=(_REPO_ROOT,),
    )

    assert result.public_package_materialization is not None
    package_root = root / "dart" / "aware_home_story_api"
    lib_root = package_root / "lib"
    assert (
        result.public_package_materialization.render_job.target.package_root
        == package_root
    )
    assert (
        result.public_package_materialization.render_job.target.target_language
        == CodeLanguage.dart
    )
    assert (lib_root / "bindings.dart").exists()
    assert (lib_root / "client.dart").exists()
    assert (lib_root / "aware_home_story_api.dart").exists()

    client_text = (lib_root / "client.dart").read_text(encoding="utf-8")
    assert "class AwareHomeStoryApiClient {" in client_text
    assert (
        "AwareHomeStoryApiClient(AwareApiClient client) : _client = client"
        not in client_text
    )
    assert (
        "  final AwareApiClient _client;\n  final Map<String, Object?> interfaceSpecPayload"
        not in client_text
    )
    assert "class HomeDevicesLockDoorCapabilityClient {" in client_text
    assert "import 'door/endpoints.dart' as doorEndpoints_" in client_text
    assert "Future<doorEndpoints_" in client_text
    assert ".LockDoorResult> lockDoor(" in client_text

    bindings_text = (lib_root / "bindings.dart").read_text(encoding="utf-8")
    assert "homeDevicesLockDoorLockDoorEndpointRef" in bindings_text
    assert "apiInterfaceSpecPayload" in bindings_text


def test_dart_public_package_includes_api_dto_export_only_classes(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        api_dto_semantic_export=True,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_home_story_api",
    )
    _write_api_source(root)
    descriptor_source = (
        root / "apis" / "types" / "home" / "aware" / "door" / "descriptor.aware"
    )
    descriptor_source.write_text(
        "\n".join(
            [
                "class BundleReleaseIdentity {",
                "    artifact_id String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with patch(
        "aware_api_runtime.packages.materialization._assert_dart_part_files_exist",
        side_effect=_write_placeholder_dart_part_files_for_assertion,
    ):
        result = compile_api_workspace(
            toml_path=toml_path,
            repo_root=root,
            materialize_public_package=True,
            public_package_target_language=CodeLanguage.dart,
            dependency_repo_roots=(_REPO_ROOT,),
        )

    assert result.public_package_materialization is not None
    class_fqns = {
        node.class_config.class_fqn
        for node in result.public_package_materialization.dto_graph.object_config_graph_nodes
        if node.class_config is not None
    }
    assert "aware_home_api.default.door.BundleReleaseIdentity" in class_fqns

    lib_root = root / "dart" / "aware_home_story_api" / "lib"
    rendered_models = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(lib_root.rglob("*.dart"))
        if not path.name.endswith((".g.dart", ".freezed.dart"))
    )
    assert "class BundleReleaseIdentity" in rendered_models


def test_dart_public_package_path_dependencies_scan_dependency_workspace_root(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "aware_kernel"
    kernel_root.mkdir(parents=True)
    toml_path = _write_api_toml(
        kernel_root,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_home_story_api",
    )
    _write_api_source(kernel_root)
    model_helpers_root = (
        kernel_root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    )
    model_helpers_root.mkdir(parents=True)
    (kernel_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'codes = ["libs/model_helpers/dart/aware_model_helpers/pubspec.yaml"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (model_helpers_root / "pubspec.yaml").write_text(
        "name: aware_model_helpers\n", encoding="utf-8"
    )
    network_root = tmp_path / "aware_network"
    api_module_root = network_root / "modules" / "api"
    aware_api_dart_root = api_module_root / "libs" / "api" / "dart"
    aware_api_dart_root.mkdir(parents=True)
    (network_root / "aware.workspace.toml").write_text("aware = 1\n", encoding="utf-8")
    (api_module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "ontology/runtime/python"',
                "",
                "[[packages]]",
                'id = "api_client_dart"',
                'kind = "code"',
                'manifest = "libs/api/dart/pubspec.yaml"',
                'visibility = "module"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (aware_api_dart_root / "pubspec.yaml").write_text(
        "name: aware_api\n", encoding="utf-8"
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=toml_path,
        repo_root=kernel_root,
    ).build_snapshot()

    assert _dart_public_package_path_dependencies(
        snapshot=snapshot,
        dependency_repo_roots=(network_root,),
    ) == (
        ("aware_api", aware_api_dart_root.resolve()),
        ("aware_model_helpers", model_helpers_root.resolve()),
    )


def test_dart_public_package_path_dependencies_scan_workspace_module_and_codes(
    tmp_path: Path,
) -> None:
    network_root = tmp_path / "aware_network"
    api_module_root = network_root / "modules" / "api"
    aware_api_dart_root = api_module_root / "libs" / "api" / "dart"
    model_helpers_root = (
        network_root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    )
    attention_api_root = network_root / "modules" / "attention" / "apis" / "attention"
    attention_api_root.mkdir(parents=True)
    (attention_api_root / "apis" / "bindings").mkdir(parents=True)
    aware_api_dart_root.mkdir(parents=True)
    model_helpers_root.mkdir(parents=True)
    (network_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'codes = ["libs/model_helpers/dart/aware_model_helpers/pubspec.yaml"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (api_module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "ontology/runtime/python"',
                "",
                "[[packages]]",
                'id = "api_client_dart"',
                'kind = "code"',
                'manifest = "libs/api/dart/pubspec.yaml"',
                'visibility = "module"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (aware_api_dart_root / "pubspec.yaml").write_text(
        "name: aware_api\n", encoding="utf-8"
    )
    (model_helpers_root / "pubspec.yaml").write_text(
        "name: aware_model_helpers\n", encoding="utf-8"
    )
    toml_path = _write_api_toml(
        attention_api_root,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_attention_service_api",
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=toml_path,
        repo_root=network_root,
    ).build_snapshot()

    assert _dart_public_package_path_dependencies(snapshot=snapshot) == (
        ("aware_api", aware_api_dart_root.resolve()),
        ("aware_model_helpers", model_helpers_root.resolve()),
    )


def test_precompiled_dependency_graphs_resolve_dependency_workspace_root(
    tmp_path: Path,
) -> None:
    network_root = tmp_path / "aware_network"
    network_root.mkdir(parents=True)
    api_toml_path = _write_api_toml(network_root)
    bindings = network_root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "home.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
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

    kernel_root = tmp_path / "aware_kernel"
    _write_api_type_package(kernel_root)

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=network_root,
    ).build_snapshot()
    baseline = compile_api_workspace(
        toml_path=api_toml_path,
        repo_root=network_root,
        materialize_service_protocol=True,
        dependency_repo_roots=(kernel_root,),
    )
    dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=_accessible_graphs_from_compile_result(baseline),
        dependency_repo_roots=(kernel_root,),
    )
    accessible_graphs = tuple(package.graph for package in dependency_packages)

    rebuilt_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=(kernel_root,),
    )

    home_api_package = next(
        package for package in rebuilt_packages if package.package_name == "home-api"
    )
    assert (
        home_api_package.package_root
        == (kernel_root / "apis" / "types" / "home").resolve()
    )

    assert baseline.runtime_artifacts is not None
    compile_plan_path = baseline.runtime_artifacts.compile_plan.path
    compile_plan_payload = json.loads(compile_plan_path.read_text(encoding="utf-8"))
    product_runtime_graphs = build_generated_api_compile_plan_accessible_graphs(
        compile_plan_payload=compile_plan_payload,
        accessible_graphs=accessible_graphs,
    )

    compile_result = compile_api_product_runtime_from_compile_plan_payload(
        compile_plan_payload=compile_plan_payload,
        repo_root=network_root,
        compile_plan_path=compile_plan_path,
        source_api_toml_path=api_toml_path,
        accessible_graphs=product_runtime_graphs,
        dependency_repo_roots=(kernel_root,),
    )

    assert compile_result.service_protocol_materialization is not None


def test_precompiled_dependency_graphs_require_complete_artifact_context(
    tmp_path: Path,
) -> None:
    network_root = tmp_path / "aware_network"
    network_root.mkdir(parents=True)
    api_toml_path = _write_api_toml(network_root)
    bindings = network_root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "home.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
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

    kernel_root = tmp_path / "aware_kernel"
    _write_api_type_package(kernel_root)

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=network_root,
    ).build_snapshot()
    baseline = compile_api_workspace(
        toml_path=api_toml_path,
        repo_root=network_root,
        materialize_service_protocol=True,
        dependency_repo_roots=(kernel_root,),
    )
    dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=_accessible_graphs_from_compile_result(baseline),
        dependency_repo_roots=(kernel_root,),
    )
    home_ontology_package = next(
        package
        for package in dependency_packages
        if package.package_name == "home-ontology"
    )

    with pytest.raises(RuntimeError, match="requires an accessible ObjectConfigGraph"):
        _build_accessible_dependency_packages(
            snapshot=snapshot,
            accessible_graphs=(home_ontology_package.graph,),
            dependency_repo_roots=(kernel_root,),
        )


def test_precompiled_dependency_graphs_load_missing_transitive_ontology_artifact(
    tmp_path: Path,
) -> None:
    network_root = tmp_path / "aware_network"
    network_root.mkdir(parents=True)
    api_toml_path = _write_api_toml(network_root)
    bindings = network_root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "home.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
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

    kernel_root = tmp_path / "aware_kernel"
    _write_api_type_package(kernel_root)

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=network_root,
    ).build_snapshot()
    baseline = compile_api_workspace(
        toml_path=api_toml_path,
        repo_root=network_root,
        materialize_service_protocol=True,
        dependency_repo_roots=(kernel_root,),
    )
    dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=_accessible_graphs_from_compile_result(baseline),
        dependency_repo_roots=(kernel_root,),
    )
    home_api_package = next(
        package for package in dependency_packages if package.package_name == "home-api"
    )
    home_ontology_package = next(
        package
        for package in dependency_packages
        if package.package_name == "home-ontology"
    )
    ontology_runtime_root = (
        kernel_root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / ".aware"
        / "ontology"
        / "runtime"
    )
    ontology_runtime_root.mkdir(parents=True, exist_ok=True)
    (ontology_runtime_root / "ontology.runtime.manifest.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    runtime_snapshot_payload = home_ontology_package.graph.model_dump(
        mode="json", exclude_none=True
    )
    (ontology_runtime_root / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(runtime_snapshot_payload, use_bin_type=True)
    )

    rebuilt_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=(home_api_package.graph,),
        dependency_repo_roots=(kernel_root,),
    )
    package_names = {package.package_name for package in rebuilt_packages}

    assert {"home-api", "home-ontology"}.issubset(package_names)


def test_compile_api_workspace_materializes_dart_public_package_with_multi_capability_client_and_relative_model_imports(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_home_story_api",
    )
    _write_multi_capability_dart_api_source(root)

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
        public_package_target_language=CodeLanguage.dart,
        dependency_repo_roots=(_REPO_ROOT,),
    )

    assert result.public_package_materialization is not None
    lib_root = root / "dart" / "aware_home_story_api" / "lib"

    client_text = (lib_root / "client.dart").read_text(encoding="utf-8")
    assert "class HomeDevicesApiClient {" in client_text
    assert ": lockDoor = HomeDevicesLockDoorCapabilityClient(client)," in client_text
    assert "unlockDoor = HomeDevicesUnlockDoorCapabilityClient(client);" in client_text
    assert (
        ": unlockDoor = HomeDevicesUnlockDoorCapabilityClient(client)"
        not in client_text
    )
    assert "class AwareHomeStoryApiClient {" in client_text
    assert (
        "AwareHomeStoryApiClient(AwareApiClient client) : _client = client"
        not in client_text
    )
    assert (
        "  final AwareApiClient _client;\n  final Map<String, Object?> interfaceSpecPayload"
        not in client_text
    )

    endpoints_text = (lib_root / "door" / "endpoints_model.dart").read_text(
        encoding="utf-8"
    )
    assert "import 'context_model.dart';" in endpoints_text
    assert "import 'door/context_model.dart';" not in endpoints_text


def test_compile_api_workspace_materializes_dart_public_package_variant_client_imports_parent_barrel(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(
        root,
        dart_root_dir="dart",
        dart_public_package_package_dir="aware_home_story_api",
    )
    _write_augmented_dart_api_source(root)

    with patch(
        "aware_api_runtime.packages.materialization._assert_dart_part_files_exist",
        side_effect=_write_placeholder_dart_part_files_for_assertion,
    ):
        result = compile_api_workspace(
            toml_path=toml_path,
            repo_root=root,
            materialize_public_package=True,
            public_package_target_language=CodeLanguage.dart,
            dependency_repo_roots=(_REPO_ROOT,),
        )

    assert result.public_package_materialization is not None
    lib_root = root / "dart" / "aware_home_story_api" / "lib"

    client_text = (lib_root / "client.dart").read_text(encoding="utf-8")
    assert (
        "import 'door/service_operation.dart' as doorServiceOperation_" in client_text
    )
    assert "import 'door/action.dart'" not in client_text
    assert "Future<doorServiceOperation_" in client_text
    assert ".LockDoorResult>" in client_text
    barrel_text = (lib_root / "aware_home_story_api.dart").read_text(encoding="utf-8")
    assert "export 'door/service_operation.dart';" in barrel_text
    assert "export 'door/action.dart';" not in barrel_text


def test_refresh_api_workspace_from_runtime_artifacts_rerenders_public_package_without_compile_plan_rebuild(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    initial = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )
    assert initial.public_package_materialization is not None

    package_root = initial.public_package_materialization.render_job.target.package_root
    import_root = package_root / "aware_home_story_api"
    client_path = import_root / "client.py"
    client_path.unlink()
    assert not client_path.exists()

    with patch(
        "aware_api_runtime.compile.build_api_compile_plan",
        side_effect=AssertionError(
            "narrow refresh must not rebuild the API compile plan"
        ),
    ):
        refreshed = refresh_api_workspace_from_runtime_artifacts(
            toml_path=toml_path,
            repo_root=root,
            refresh_public_package=True,
        )

    assert refreshed.compile_plan is None
    assert refreshed.public_package_materialization is not None
    assert client_path.exists()

    sys_path_snapshot = list(sys.path)
    try:
        sys.path.insert(0, str(package_root))
        bootstrap_pydantic_package_from_artifacts(
            package_prefix="aware_home_story_api",
            strict_imports=True,
        )
    finally:
        sys.path[:] = sys_path_snapshot


def test_refresh_api_workspace_from_runtime_artifacts_prunes_public_package_dto_graph_from_class_refs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root)
    _write_api_source(root)

    initial = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_public_package=True,
    )
    assert initial.public_package_materialization is not None

    with patch(
        "aware_api_runtime.compile.build_api_compile_plan",
        side_effect=AssertionError(
            "delta refresh must not rebuild the API compile plan"
        ),
    ):
        refreshed = refresh_api_workspace_from_runtime_artifacts(
            toml_path=toml_path,
            repo_root=root,
            refresh_public_package=True,
            public_package_candidate_paths=(Path("models/lock_door.py"),),
            public_package_render_input_class_refs=("aware_home_api.door.LockDoor",),
        )

    assert refreshed.compile_plan is None
    assert refreshed.public_package_materialization is not None
    class_fqns = {
        node.class_config.class_fqn
        for node in refreshed.public_package_materialization.dto_graph.object_config_graph_nodes
        if node.class_config is not None
    }
    assert class_fqns == {
        "aware_home_api.default.door.LockDoor",
        "aware_home_api.default.door.LockDoorContext",
    }


def test_refresh_api_workspace_from_runtime_artifacts_rerenders_service_protocol_without_compile_plan_rebuild(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_api_toml(root, api_dto_semantic_export=True)
    _write_api_source(root)
    ontology_package_root = _write_home_ontology_python_stub(root)

    initial = compile_api_workspace(
        toml_path=toml_path,
        repo_root=root,
        materialize_service_protocol=True,
    )
    assert initial.service_protocol_materialization is not None

    package_root = (
        initial.service_protocol_materialization.render_job.target.package_root
    )
    import_root = package_root / "aware_home_story_protocol"
    init_path = import_root / "__init__.py"
    init_path.unlink()
    assert not init_path.exists()

    with patch(
        "aware_api_runtime.compile.build_api_compile_plan",
        side_effect=AssertionError(
            "narrow refresh must not rebuild the API compile plan"
        ),
    ):
        refreshed = refresh_api_workspace_from_runtime_artifacts(
            toml_path=toml_path,
            repo_root=root,
            refresh_service_protocol=True,
        )

    assert refreshed.compile_plan is None
    assert refreshed.service_protocol_materialization is not None
    assert init_path.exists()

    sys_path_snapshot = list(sys.path)
    try:
        sys.path.insert(0, str(ontology_package_root))
        sys.path.insert(0, str(root / "python" / "aware_home_api"))
        sys.path.insert(0, str(package_root))
        bootstrap_pydantic_package_from_artifacts(
            package_prefix="aware_home_story_protocol",
            strict_imports=True,
        )
    finally:
        sys.path[:] = sys_path_snapshot
