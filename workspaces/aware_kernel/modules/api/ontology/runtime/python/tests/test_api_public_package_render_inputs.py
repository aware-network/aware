from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.schemas import (
    MaterializationProfileInputFormat,
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
    build_api_public_package_render_inputs,
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


def _build_render_job(root: Path):
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
    return render_job


def test_build_api_public_package_render_inputs_from_render_job(tmp_path: Path) -> None:
    render_job = _build_render_job(tmp_path)

    lowered = build_api_public_package_render_inputs(render_job=render_job)

    refs = lowered.materialization_config.profile_input_refs
    assert tuple(ref.key for ref in refs) == (
        "api.interface_spec",
        "api.invocation_manifest",
        "api.public_package_plan",
    )
    assert tuple(ref.path.as_posix() for ref in refs) == (
        "runtime/api.interface_spec.json",
        "runtime/api.invocation_manifest.json",
        "runtime/api.public_package_plan.json",
    )
    assert all(ref.format == MaterializationProfileInputFormat.json for ref in refs)
    assert all(ref.required is True for ref in refs)
    assert render_job.materialization_config.profile_input_refs == []


def test_build_api_public_package_render_inputs_fails_closed_on_missing_artifact(
    tmp_path: Path,
) -> None:
    render_job = _build_render_job(tmp_path)
    broken = replace(render_job, runtime_artifacts=render_job.runtime_artifacts[:-1])

    with pytest.raises(
        ValueError, match="Missing public API package runtime artifacts"
    ):
        build_api_public_package_render_inputs(render_job=broken)
