from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from uuid import UUID

from aware_interface.manifest.app_spec import (
    AwareAppTomlDependencySpec,
    AwareAppTomlInterfaceSpec,
    AwareAppTomlSpec,
)


_AWARE_APP_LAUNCH_SCHEMA = "aware.app.launch.v0"


@dataclass(frozen=True, slots=True)
class AwareAppCommittedScreenEvidence:
    app_config_screen_config_id: UUID
    screen_key: str
    projection_experience_id: UUID
    projection_experience_layout_graph_binding_id: UUID


@dataclass(frozen=True, slots=True)
class AwareAppPackageLaunchEvidence:
    package_name: str
    app_package_id: UUID
    branch_id: UUID
    object_instance_graph_commit_id: UUID


@dataclass(frozen=True, slots=True)
class AwareAppLaunchDescriptor:
    app_id: str
    display_name: str
    app_package: AwareAppPackageLaunchEvidence
    default_screen_key: str
    screens: tuple[AwareAppCommittedScreenEvidence, ...]
    schema: str = _AWARE_APP_LAUNCH_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != _AWARE_APP_LAUNCH_SCHEMA:
            raise ValueError(f"App launch descriptor schema must be {_AWARE_APP_LAUNCH_SCHEMA!r}")
        if not self.app_id.strip() or not self.display_name.strip():
            raise ValueError("App launch descriptor app identity is required")
        if not self.app_package.package_name.strip():
            raise ValueError("App launch descriptor package_name is required")
        default_screen_key = self.default_screen_key.strip()
        if not default_screen_key:
            raise ValueError("App launch descriptor default_screen_key is required")
        screen_keys: set[str] = set()
        for screen in self.screens:
            screen_key = screen.screen_key.strip()
            if not screen_key:
                raise ValueError("App launch descriptor screen_key is required")
            if screen_key in screen_keys:
                raise ValueError(f"App launch descriptor has duplicate screen_key {screen_key!r}")
            screen_keys.add(screen_key)
        if default_screen_key not in screen_keys:
            raise ValueError(
                "App launch descriptor default screen is not committed: " f"screen_key={default_screen_key!r}"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "app_id": self.app_id,
            "display_name": self.display_name,
            "app_package": {
                "package_name": self.app_package.package_name,
                "app_package_id": str(self.app_package.app_package_id),
                "branch_id": str(self.app_package.branch_id),
                "object_instance_graph_commit_id": str(self.app_package.object_instance_graph_commit_id),
            },
            "default_screen_key": self.default_screen_key,
            "screens": [
                {
                    "screen_key": screen.screen_key,
                    "app_config_screen_config_id": str(screen.app_config_screen_config_id),
                    "projection_experience_id": str(screen.projection_experience_id),
                    "projection_experience_layout_graph_binding_id": str(
                        screen.projection_experience_layout_graph_binding_id
                    ),
                }
                for screen in self.screens
            ],
        }


def build_aware_app_launch_selection_payload(
    *,
    spec: AwareAppTomlSpec,
) -> dict[str, object]:
    return {
        "app_id": spec.app.app_name,
        "display_name": spec.app.title or spec.app.app_name,
        "requires_actor": spec.control.requires_actor,
        "default_screen": spec.control.default_screen,
        "admitted_screen": spec.control.admitted_screen,
        "dependencies": tuple(_dependency_payload(dependency) for dependency in spec.dependencies),
        "interface_packages": tuple(
            {
                "package_name": interface.package_name,
                "role": interface.role,
            }
            for interface in spec.interfaces
        ),
        "seed_color_value": spec.launch.seed_color_value,
        "generated_manifest_path": spec.launch.generated_manifest_path,
    }


def render_aware_app_launch_descriptor_json(
    descriptor: AwareAppLaunchDescriptor,
) -> str:
    return (
        json.dumps(
            descriptor.to_payload(),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_aware_app_launch_manifest_dart(
    *,
    spec: AwareAppTomlSpec,
    source_manifest_path: Path,
    descriptor: AwareAppLaunchDescriptor,
) -> str:
    imports = tuple(_runtime_import_line(interface) for interface in spec.interfaces)
    registrations = "\n".join(_render_runtime_registration(interface) for interface in spec.interfaces)
    screens = "\n".join(_render_committed_screen(screen) for screen in descriptor.screens)
    source_path = source_manifest_path.as_posix()
    package = descriptor.app_package
    return (
        "// GENERATED CODE - DO NOT EDIT.\n"
        f"// Source: {source_path}\n"
        "\n"
        "import 'package:aware_app_factory/aware_app_factory.dart';\n"
        f"{''.join(imports)}"
        "\n"
        "AwareAppLaunchManifest buildAwareAppLaunchManifest() {\n"
        "  return AwareAppLaunchManifest(\n"
        "    appPackage: const AwareAppPackageEvidence(\n"
        f"      packageName: {_dart_string(package.package_name)},\n"
        f"      appPackageId: {_dart_string(str(package.app_package_id))},\n"
        f"      branchId: {_dart_string(str(package.branch_id))},\n"
        "      objectInstanceGraphCommitId: "
        f"{_dart_string(str(package.object_instance_graph_commit_id))},\n"
        "    ),\n"
        f"    defaultScreenKey: {_dart_string(descriptor.default_screen_key)},\n"
        "    composition: const AwareAppComposition(\n"
        f"      appId: {_dart_string(descriptor.app_id)},\n"
        f"      displayName: {_dart_string(descriptor.display_name)},\n"
        f"      seedColorValue: 0x{spec.launch.seed_color_value:08X},\n"
        "      controlPolicy: AwareAppControlPolicy(\n"
        f"        requiresActor: {_dart_bool(spec.control.requires_actor)},\n"
        f"        defaultScreenKey: {_dart_string(spec.control.default_screen)},\n"
        "        admittedScreenKey: "
        f"{_dart_optional_string(spec.control.admitted_screen)},\n"
        "      ),\n"
        "    ),\n"
        "    catalog: AwareAppRuntimeCatalog(\n"
        "      registrations: [\n"
        f"{registrations}\n"
        "      ],\n"
        "    ),\n"
        "    committedScreens: const [\n"
        f"{screens}\n"
        "    ],\n"
        "  );\n"
        "}\n"
    )


def _dependency_payload(dependency: AwareAppTomlDependencySpec) -> dict[str, object]:
    return {
        "package_name": dependency.package_name,
        "kind": dependency.kind,
        "role": dependency.role,
    }


def _runtime_import_line(interface: AwareAppTomlInterfaceSpec) -> str:
    runtime_import = interface.runtime_import
    alias = interface.runtime_import_alias
    if not runtime_import or not alias:
        raise ValueError(
            "aware.app.toml launch generation requires runtime_import and "
            f"runtime_import_alias for interface {interface.package_name!r}"
        )
    import_expr = _dart_string(runtime_import)
    if len(f"import {import_expr} as {alias};") > 88:
        return f"import {import_expr}\n    as {alias};\n"
    return f"import {import_expr} as {alias};\n"


def _render_runtime_registration(interface: AwareAppTomlInterfaceSpec) -> str:
    alias = interface.runtime_import_alias
    runtime_factory = interface.runtime_factory
    if not alias:
        raise ValueError(f"runtime_import_alias is required for {interface.package_name!r}")
    return (
        "        AwareInterfaceRuntimeRegistration(\n"
        f"          interfacePackageId: {_dart_string(_interface_package_id(interface))},\n"
        f"          interfacePackageName: {_dart_string(interface.package_name)},\n"
        f"          buildRuntime: {alias}.{runtime_factory},\n"
        "        ),"
    )


def _render_committed_screen(screen: AwareAppCommittedScreenEvidence) -> str:
    return (
        "      AwareAppCommittedScreen(\n"
        "        appConfigScreenConfigId: "
        f"{_dart_string(str(screen.app_config_screen_config_id))},\n"
        f"        screenKey: {_dart_string(screen.screen_key)},\n"
        "        projectionExperienceId: "
        f"{_dart_string(str(screen.projection_experience_id))},\n"
        "        projectionExperienceLayoutGraphBindingId: "
        f"{_dart_string(str(screen.projection_experience_layout_graph_binding_id))},\n"
        "      ),"
    )


def _interface_package_id(interface: AwareAppTomlInterfaceSpec) -> str:
    return interface.package_name


def _dart_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _dart_bool(value: bool) -> str:
    return "true" if value else "false"


def _dart_optional_string(value: str | None) -> str:
    return "null" if value is None else _dart_string(value)


__all__ = [
    "AwareAppCommittedScreenEvidence",
    "AwareAppLaunchDescriptor",
    "AwareAppPackageLaunchEvidence",
    "build_aware_app_launch_selection_payload",
    "render_aware_app_launch_descriptor_json",
    "render_aware_app_launch_manifest_dart",
]
