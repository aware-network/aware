from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import SemanticScopeRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_service_runtime.dependency_scope import load_service_dependency_scope
from aware_service_runtime.semantic_scope import (
    SERVICE_SEMANTIC_SCOPE_KEY,
    register_semantic_scope_providers,
)


def _write_api_package(
    root: Path,
    *,
    package_dir: str = "home_devices",
    package_name: str = "home-devices-api",
    fqn_prefix: str = "aware_home_devices",
    api_name: str = "home_devices",
    capability_name: str = "open_door",
    endpoint_name: str = "open_door",
) -> Path:
    package_root = root / "apis" / package_dir
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "aware.api.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                "",
                "[build]",
                'sources_dir = "apis"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    source_path = package_root / "apis" / "demo" / "root.aware"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "\n".join(
            [
                f"api {api_name} {{",
                f"    capability {capability_name} {{",
                f"        endpoint {endpoint_name} demo.api.Request;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_service_manifest(
    root: Path,
    *,
    package_dir: str = "home_story",
    package_name: str = "home-story-service",
    fqn_prefix: str = "aware_home_story_service",
    dependency_lines: tuple[str, ...] = (),
) -> Path:
    package_root = root / "services" / package_dir
    package_root.mkdir(parents=True, exist_ok=True)
    manifest_path = package_root / "aware.service.toml"
    manifest_lines = [
        "aware_service = 1",
        "",
        "[service]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        "",
        "[build]",
        'sources_dir = "services"',
        'include_paths = ["**/*.aware"]',
        "exclude_paths = []",
        "",
    ]
    manifest_path.write_text(
        "\n".join([*manifest_lines, *dependency_lines]), encoding="utf-8"
    )
    return manifest_path


def _write_service_protocol_plan(
    root: Path,
    *,
    package_name: str,
    endpoint_ref: str,
) -> tuple[Path, str]:
    payload = {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "endpoint_ref": endpoint_ref,
                            }
                        ]
                    }
                ]
            }
        ]
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()
    plan_path = (
        root
        / ".aware"
        / "api"
        / "runtime"
        / package_name
        / "api.service_protocol_plan.json"
    ).resolve()
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return plan_path, digest


def test_load_service_dependency_scope_prefers_service_protocol_artifact(
    tmp_path: Path,
) -> None:
    _write_api_package(
        tmp_path,
        endpoint_name="open_door_manifest",
    )
    _write_service_protocol_plan(
        tmp_path,
        package_name="home-devices-api",
        endpoint_ref="home_devices.open_door.open_door_protocol",
    )
    manifest_path = _write_service_manifest(
        tmp_path,
        dependency_lines=(
            "[[dependencies]]",
            'package_name = "home-devices-api"',
            'kind = "api_service_protocol"',
            "",
        ),
    )

    scope = load_service_dependency_scope(manifest_path=manifest_path)

    assert scope.service_package_name == "home-story-service"
    assert scope.declared_api_package_names == ("home-devices-api",)
    assert scope.resolved_api_package_names == ("home-devices-api",)
    assert scope.api_catalog["home_devices"].endpoint_refs == frozenset(
        {"home_devices.open_door.open_door_protocol"}
    )


def test_load_service_dependency_scope_falls_back_to_declared_api_manifest(
    tmp_path: Path,
) -> None:
    _write_api_package(
        tmp_path,
        endpoint_name="open_door_manifest",
    )
    manifest_path = _write_service_manifest(
        tmp_path,
        dependency_lines=(
            "[[dependencies]]",
            'package_name = "home-devices-api"',
            "",
        ),
    )

    scope = load_service_dependency_scope(manifest_path=manifest_path)

    assert scope.declared_api_package_names == ("home-devices-api",)
    assert scope.resolved_api_package_names == ("home-devices-api",)
    assert scope.api_catalog["home_devices"].endpoint_refs == frozenset(
        {"home_devices.open_door.open_door_manifest"}
    )


def test_load_service_dependency_scope_falls_back_to_workspace_apis_when_undeclared(
    tmp_path: Path,
) -> None:
    _write_api_package(
        tmp_path,
        package_name="home-devices-api",
        endpoint_name="open_door_workspace",
    )
    manifest_path = _write_service_manifest(tmp_path)

    scope = load_service_dependency_scope(manifest_path=manifest_path)

    assert scope.declared_api_package_names == ()
    assert scope.resolved_api_package_names == ("home-devices-api",)
    assert scope.api_catalog["home_devices"].endpoint_refs == frozenset(
        {"home_devices.open_door.open_door_workspace"}
    )


def test_load_service_dependency_scope_preserves_workspace_fallback_when_declared_package_missing(
    tmp_path: Path,
) -> None:
    _write_api_package(
        tmp_path,
        package_name="workspace-home-devices-api",
        endpoint_name="open_door_workspace",
    )
    manifest_path = _write_service_manifest(
        tmp_path,
        dependency_lines=(
            "[[dependencies]]",
            'package_name = "missing-home-devices-api"',
            "",
        ),
    )

    scope = load_service_dependency_scope(manifest_path=manifest_path)

    assert scope.declared_api_package_names == ("missing-home-devices-api",)
    assert scope.resolved_api_package_names == ("workspace-home-devices-api",)
    assert scope.api_catalog["home_devices"].endpoint_refs == frozenset(
        {"home_devices.open_door.open_door_workspace"}
    )


def test_service_semantic_scope_emits_experience_materialization_dependency(
    tmp_path: Path,
) -> None:
    _write_api_package(tmp_path)
    manifest_path = _write_service_manifest(
        tmp_path,
        dependency_lines=(
            "[[dependencies]]",
            'package_name = "home-devices-api"',
            "",
        ),
    )
    service_source = manifest_path.parent / "services" / "home.services.aware"
    service_source.parent.mkdir(parents=True, exist_ok=True)
    service_source.write_text(
        "\n".join(
            [
                "service home_story {",
                "    api home_devices;",
                "    experience home_story;",
                "",
                "    operation open_door {",
                "        endpoint home_devices.open_door.open_door;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    register_semantic_scope_providers()

    resolutions = SemanticScopeRegistry.resolve(
        CodePackageInfo(
            name="home-story-service",
            root_path=manifest_path.parent.relative_to(tmp_path),
            manifest_path=manifest_path.relative_to(tmp_path),
            language=CodeLanguage.aware,
            metadata={"manifest_kind": "aware_service_toml"},
        ),
        workspace_root=tmp_path,
        provider_keys=("aware_service",),
    )

    assert len(resolutions) == 1
    assert resolutions[0].scope_key == SERVICE_SEMANTIC_SCOPE_KEY
    dependencies_by_kind = {
        dependency.dependency_kind: dependency
        for dependency in resolutions[0].materialization_dependencies
    }
    assert dependencies_by_kind["api_service_protocol"].package_name == (
        "home-devices-api"
    )
    experience_dependency = dependencies_by_kind["ProjectionExperience"]
    assert experience_dependency.package_name == "home_story"
    assert experience_dependency.provider_key == "aware_experience"
    assert experience_dependency.semantic_package_family == "experience"
    assert experience_dependency.semantic_package_kind == "experience_package"
