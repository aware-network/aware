from __future__ import annotations

from pathlib import Path
import sys

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.schemas import (
    API_PUBLIC_PACKAGE_KIND,
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
    ApiPublicPackageRenderTarget,
    build_api_public_package_lowering_handoff,
    build_api_public_package_plan,
    build_api_public_package_render_job,
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


def test_build_api_public_package_render_job_from_lowering_handoff(
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
    public_plan = build_api_public_package_plan(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        api_ontology=compile_plan.api_ontology,
    )
    handoff = build_api_public_package_lowering_handoff(
        plan=public_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
    )

    render_job = build_api_public_package_render_job(
        handoff=handoff,
        target=ApiPublicPackageRenderTarget(
            target_language=CodeLanguage.python,
            source_aware_toml_path=toml_path,
            target_output_dir=root / "render" / "python",
            package_root=root / "sdk" / "python",
            package_name="aware_home_story_sdk",
            import_root="aware_home_story_sdk",
            description="Generated public API package test package.",
        ),
    )

    assert render_job.schema_version == 1
    assert render_job.package_name == "home-story-api"
    assert render_job.fqn_prefix == "aware_home_story_api"
    assert (
        render_job.backend_handoff.materialization_source == MaterializationSource.api
    )
    assert render_job.target.target_language == CodeLanguage.python

    materialization_config = render_job.materialization_config
    assert materialization_config.name == "api-public-package-python"
    assert materialization_config.source == MaterializationSource.api
    assert materialization_config.source_package_name == "home-story-api"
    assert materialization_config.source_aware_toml_path == toml_path
    assert materialization_config.target_output_dir == root / "render" / "python"
    assert materialization_config.import_root == "aware_home_story_sdk"
    assert len(materialization_config.packages) == 1

    package_spec = materialization_config.packages[0]
    assert package_spec.name == "aware_home_story_sdk"
    assert package_spec.package_name == "aware_home_story_sdk"
    assert package_spec.package_root == root / "sdk" / "python"
    assert package_spec.import_root == "aware_home_story_sdk"
    assert package_spec.dependencies == [
        "aware-api-client",
        "aware-types",
        "aware-utils",
        "pydantic>=2.8.0,<3.0.0",
    ]
    assert package_spec.metadata == {
        "aware_package_kind": API_PUBLIC_PACKAGE_KIND,
        "root_export_refs": ["client.AwareHomeStorySdkClient"],
    }

    assert tuple(ref.kind for ref in render_job.runtime_artifacts) == (
        "api.interface_spec",
        "api.invocation_manifest",
        "api.public_package_plan",
    )


def test_build_api_public_package_render_job_for_dart_target(tmp_path: Path) -> None:
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
    public_plan = build_api_public_package_plan(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        api_ontology=compile_plan.api_ontology,
    )
    handoff = build_api_public_package_lowering_handoff(
        plan=public_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
    )
    aware_api_dart_root = root / "modules" / "api" / "libs" / "api" / "dart"
    model_helpers_root = (
        root / "libs" / "model_helpers" / "dart" / "aware_model_helpers"
    )

    render_job = build_api_public_package_render_job(
        handoff=handoff,
        target=ApiPublicPackageRenderTarget(
            target_language=CodeLanguage.dart,
            source_aware_toml_path=toml_path,
            target_output_dir=root / "render" / "dart",
            package_root=root / "sdk" / "dart",
            package_name="aware_home_story_api",
            repo_root=root,
            path_dependencies=(
                ("aware_api", aware_api_dart_root),
                ("aware_model_helpers", model_helpers_root),
            ),
            import_root=None,
            description="Generated public API package Dart test package.",
        ),
    )

    materialization_config = render_job.materialization_config
    assert materialization_config.name == "api-public-package-dart"
    assert materialization_config.target_language == CodeLanguage.dart
    assert materialization_config.target_output_dir == root / "render" / "dart"
    assert materialization_config.import_root is None
    assert len(materialization_config.packages) == 1

    package_spec = materialization_config.packages[0]
    assert package_spec.package_name == "aware_home_story_api"
    assert package_spec.package_root == root / "sdk" / "dart"
    assert package_spec.import_root is None
    assert package_spec.dependencies == []
    assert package_spec.metadata == {
        "aware_package_kind": API_PUBLIC_PACKAGE_KIND,
        "repo_root": root.resolve().as_posix(),
        "path_dependencies": {
            "aware_api": "modules/api/libs/api/dart",
            "aware_model_helpers": "libs/model_helpers/dart/aware_model_helpers",
        },
    }
