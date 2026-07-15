from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

import msgpack  # pyright: ignore[reportMissingTypeStubs]
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[8]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_INTERFACE_RUNTIME_ROOT_STR = str(
    _REPO_ROOT
    / "workspaces"
    / "aware_network"
    / "modules"
    / "interface"
    / "ontology"
    / "runtime"
    / "python"
)
if _INTERFACE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _INTERFACE_RUNTIME_ROOT_STR)

from aware_interface.builder import (  # noqa: E402
    PaneRenderSpecCompatibilityWarning,
    _load_workspace_api_view_state_catalog,
    _load_workspace_state_attribute_catalog,
    _load_workspace_state_model_catalog,
    build_interface_compile_plan,
    build_interface_config_bundle,
    build_projection_identity_catalog_from_ocg,
    emit_interface_dart_pane_registrar_bundle_artifact,
    emit_interface_pane_render_spec_materialization_artifact,
)
from aware_interface.compile import compile_interface_workspace  # noqa: E402
from aware_interface.workspace import InterfaceWorkspace  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)  # noqa: E402


def _write_interface_toml(
    root: Path,
    *,
    dependencies: tuple[tuple[str, str], ...] = (),
) -> Path:
    toml_path = root / "aware.interface.toml"
    lines = [
        "aware_interface = 1",
        "",
        "[interface]",
        'package_name = "home-story-interface"',
        'fqn_prefix = "aware_home_story_interface"',
        "",
        "[build]",
        'sources_dir = "."',
        'include_paths = ["*.aware"]',
        'exclude_paths = ["**/*.example.aware"]',
        'config_bundle_path = "bundles/interface.config.bundle.json"',
        'compilation_mode = "interface_ontology"',
        "",
        "[dart]",
        'package_path = "dart/aware_home_story_interface"',
        'package_name = "aware_home_story_interface"',
    ]
    for package_name, kind in dependencies:
        lines.extend(
            [
                "",
                "[[dependencies]]",
                f'package_name = "{package_name}"',
                f'kind = "{kind}"',
            ]
        )
    _ = toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return toml_path


def _write_interface_source(root: Path) -> None:
    _ = (root / "home_story_app.aware").write_text(
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                "        layout configuration_map default {",
                "            section workspace",
                "            section inspector",
                "        }",
                "",
                "        layout scene_view {",
                "            section scene",
                "            section overlay_left",
                "        }",
                "    }",
                "",
                "    pane door_control {",
                "        mount main.configuration_map.workspace",
                "        mount main.scene_view.overlay_left",
                "        narrative security.control",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_interface_source_with_duplicate_section_mount(root: Path) -> None:
    _ = (root / "home_story_app.aware").write_text(
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                "        layout configuration_map default {",
                "            section workspace",
                "        }",
                "    }",
                "",
                "    pane door_control {",
                "        mount main.configuration_map.workspace",
                "        mount main.configuration_map.workspace",
                "        narrative security.control",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_pane_package(
    root: Path,
    *,
    include_experience_dependency: bool = True,
) -> None:
    pane_root = root / "panes" / "door_control"
    pane_root.mkdir(parents=True, exist_ok=True)
    dependency_lines = (
        [
            "",
            "[[dependencies]]",
            'package_name = "home-shell-experience"',
            'kind = "experience_package"',
        ]
        if include_experience_dependency
        else []
    )
    _ = (pane_root / "aware.pane.toml").write_text(
        "\n".join(
            [
                "aware_pane = 1",
                "",
                "[pane]",
                'package_name = "home-story-door-control-pane"',
                'fqn_prefix = "aware_home_story_door_control_pane"',
                'pane_name = "door_control"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                *dependency_lines,
                "",
                "[python]",
                'package_path = "python/aware_door_control_pane"',
                'import_root = "aware_door_control_pane"',
                "",
                "[dart]",
                'package_path = "dart/aware_door_control_pane"',
                'package_name = "aware_door_control_pane"',
                "",
                "[dart.flutter]",
                'library = "package:aware_door_control_pane/aware_door_control_pane.dart"',
                'symbol = "registerPanePackage"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (pane_root / "door_control.aware").write_text(
        "\n".join(
            [
                "pane door_control {",
                "    kind door",
                "",
                "    view home_story.security.door default {",
                '        """Door state and operator actions."""',
                "    }",
                "",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_pane_package_with_authored_render(root: Path) -> None:
    _write_pane_package(root)
    _ = (root / "panes" / "door_control" / "door_control.aware").write_text(
        "\n".join(
            [
                "pane door_control {",
                "    kind door",
                "",
                "    view home_story.security.door default {",
                '        """Door state and operator actions."""',
                "    }",
                "",
                "    render default {",
                "        view home_story.security.door;",
                '        version "0.1.0";',
                "        root root;",
                "        require node_kind column;",
                "        require action_binding view_action;",
                "",
                "        node root column role pane;",
                "",
                "        node title text parent root order 0 role heading {",
                '            text "Door control";',
                "        }",
                "",
                "        node unlock button parent root order 1 role action {",
                '            label "Unlock";',
                "            action activate view unlock_door {",
                "                receipt show_receipt;",
                "            }",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_json_render_spec(root: Path, *, name: str = "door_control_json") -> None:
    render_spec_root = root / "panes" / "door_control" / "render_specs"
    render_spec_root.mkdir(parents=True, exist_ok=True)
    _ = (render_spec_root / "door_control.render_spec.json").write_text(
        json.dumps(
            {
                "name": name,
                "pane_name": "door_control",
                "spec_version": "0.1.0",
                "view_ref": "home_story.security.door",
                "root_node_key": "root",
                "nodes": [
                    {
                        "node_key": "root",
                        "node_kind": "column",
                        "semantic_role": "pane",
                    },
                    {
                        "node_key": "title",
                        "node_kind": "text",
                        "parent_node_key": "root",
                        "semantic_role": "heading",
                        "text": "Door control JSON",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_multi_view_pane_package(root: Path) -> None:
    pane_root = root / "panes" / "door_control"
    pane_root.mkdir(parents=True, exist_ok=True)
    _ = (pane_root / "aware.pane.toml").write_text(
        "\n".join(
            [
                "aware_pane = 1",
                "",
                "[pane]",
                'package_name = "home-story-door-control-pane"',
                'fqn_prefix = "aware_home_story_door_control_pane"',
                'pane_name = "door_control"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                "",
                "[[dependencies]]",
                'package_name = "home-shell-experience"',
                'kind = "experience_package"',
                "",
                "[python]",
                'package_path = "python/aware_door_control_pane"',
                'import_root = "aware_door_control_pane"',
                "",
                "[dart]",
                'package_path = "dart/aware_door_control_pane"',
                'package_name = "aware_door_control_pane"',
                "",
                "[dart.flutter]",
                'library = "package:aware_door_control_pane/aware_door_control_pane.dart"',
                'symbol = "registerPanePackage"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (pane_root / "door_control.aware").write_text(
        "\n".join(
            [
                "pane door_control {",
                "    kind door",
                "",
                "    view home_story.security.door default {",
                '        """Door state and operator actions."""',
                "    }",
                "",
                "    view home_story.security.detail {",
                '        """Detailed door state and history."""',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_attention_compile_artifact(
    root: Path,
    *,
    package_name: str = "home-shell-attention",
    layout_key: str = "scene_view",
    section_key: str = "overlay_left",
) -> Path:
    artifact_path = (
        root
        / ".aware"
        / "attention"
        / "runtime"
        / package_name
        / "attention.compile_plan.json"
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    _ = artifact_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": package_name,
                "source_files": ["attention/home_shell.anchor.toml"],
                "layout_ontology": [
                    {
                        "layout_config_id": "3377fbc6-7c1d-5f58-ad77-7cbfd6df413f",
                        "layout_key": layout_key,
                        "title": "Scene View",
                        "description": None,
                        "frame_mode": "vertical",
                        "sections": [
                            {
                                "layout_config_section_config_id": "8741f7e0-4e72-5be3-a49c-51c6f181f8af",
                                "section_config_id": "3870f38f-c655-5224-a88a-92bd4a55874b",
                                "section_key": section_key,
                                "title": "Overlay Left",
                                "description": None,
                                "order": 0,
                                "flex": 1.0,
                                "is_visible": True,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return artifact_path


def _write_attention_package(
    root: Path, *, package_name: str = "home-shell-attention"
) -> Path:
    attention_root = root / "attentions" / package_name
    attention_root.mkdir(parents=True, exist_ok=True)
    toml_path = attention_root / "aware.attention.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_attention = 1",
                "",
                "[attention]",
                f'package_name = "{package_name}"',
                'fqn_prefix = "aware_home_shell_attention"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return toml_path


def _write_workspace_manifest(
    root: Path,
    *,
    attentions: tuple[str, ...] = (),
    sdks: tuple[str, ...] = (),
) -> Path:
    _ = (root / "aware.environment.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[environment]",
                'handle = "home_story_workspace"',
                'modules = ["home_devices"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    workspace_toml_path = root / "aware.workspace.toml"
    _ = workspace_toml_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "home_story_workspace"',
                'environments = ["aware.environment.toml"]',
                "apis = []",
                f"sdks = {list(sdks)!r}",
                "services = []",
                "experiences = []",
                f"attentions = {list(attentions)!r}",
                'panes = ["panes/door_control/aware.pane.toml"]',
                "interfaces = []",
                "nodes = []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace_toml_path


def _ensure_workspace_manifest_for_fixture(root: Path) -> None:
    workspace_toml_path = root / "aware.workspace.toml"
    if workspace_toml_path.is_file():
        payload = workspace_toml_path.read_text(encoding="utf-8")
        if "[workspace]" in payload:
            return
    _write_workspace_manifest(root)


def _write_sdk_package(root: Path) -> Path:
    sdk_root = root / "sdks" / "home" / "aware"
    sdk_root.mkdir(parents=True, exist_ok=True)
    toml_path = sdk_root / "aware.sdk.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_sdk = 1",
                "",
                "[sdk]",
                'package_name = "home-sdk"',
                'fqn_prefix = "aware_home_sdk"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                'compilation_mode = "sdk_ontology"',
                "",
                "[[dependencies]]",
                'kind = "api_package"',
                'package_name = "home-devices-api"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (sdk_root / "home_sdk.aware").write_text(
        "\n".join(
            [
                "sdk home_sdk {",
                "    api home_devices;",
                "",
                "    operation unlock_door {",
                "        endpoint home_devices.unlock_door.unlock_door;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_experience_package(
    root: Path,
    *,
    package_name: str = "home-shell-experience",
    experience_name: str = "home_story",
    observable_key: str = "security",
    view_key: str = "door",
    api_view_ref: str | None = None,
    additional_view_keys: tuple[str, ...] = (),
) -> Path:
    experience_root = root / "experiences" / package_name
    experience_root.mkdir(parents=True, exist_ok=True)
    toml_path = experience_root / "aware.experience.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                f'package_name = "{package_name}"',
                'fqn_prefix = "aware_home_shell_experience"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    view_header = f"        view {view_key} default api_view {api_view_ref or 'home_devices.security_door'} {{"
    action_lines: list[str] = []
    _ = (experience_root / "home_shell.aware").write_text(
        "\n".join(
            [
                f"experience {experience_name} on aware_home.home.Home {{",
                f"    observable {observable_key} {{",
                view_header,
                '            """Door state view."""',
                *action_lines,
                "        }",
                *[
                    line
                    for extra_view_key in additional_view_keys
                    for line in (
                        f"        view {extra_view_key} api_view home_devices.{extra_view_key} {{",
                        '            """Alternate experience view."""',
                        "        }",
                    )
                ],
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_api_package(root: Path) -> Path:
    api_root = root / "apis" / "home_devices"
    api_root.mkdir(parents=True, exist_ok=True)
    toml_path = api_root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-devices-api"',
                'fqn_prefix = "aware_home_devices_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_home_devices_service_api"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (api_root / "bindings" / "home_devices.apis.aware").parent.mkdir(
        parents=True, exist_ok=True
    )
    _ = (api_root / "bindings" / "home_devices.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability unlock_door {",
                "        endpoint unlock_door",
                "    }",
                "    capability lock_door {",
                "        endpoint lock_door",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_runtime_dir = root / ".aware" / "api" / "runtime" / "home-devices-api"
    api_runtime_dir.mkdir(parents=True, exist_ok=True)
    api_view_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/api-view-capability-endpoint/home-devices/security-door/unlock-door",
    )
    api_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/api-capability-endpoint/home-devices/unlock-door",
    )
    _ = (api_runtime_dir / "api.interface_spec.json").write_text(
        json.dumps(
            {
                "apis": [
                    {
                        "name": "home_devices",
                        "capabilities": [
                            {
                                "name": "unlock_door",
                                "endpoints": [{"name": "unlock_door"}],
                            },
                            {
                                "name": "lock_door",
                                "endpoints": [{"name": "lock_door"}],
                            },
                        ],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps(
            {
                "api_ontology": [
                    {
                        "api": {"name": "home_devices"},
                        "views": [
                            {
                                "name": "security_door",
                                "view_ref": "home_devices.security_door",
                                "state_model_ref": "aware_home.home.Door",
                                "state_model_id": "0b8e17ec-b168-5a3b-9fc7-d60037cfb51c",
                                "observable_ref": "Home.security",
                            },
                            {
                                "name": "detail",
                                "view_ref": "home_devices.detail",
                                "state_model_ref": "aware_home.home.Door",
                                "state_model_id": "0b8e17ec-b168-5a3b-9fc7-d60037cfb51c",
                                "observable_ref": "Home.security",
                            },
                        ],
                        "view_capability_endpoints": [
                            {
                                "view_name": "security_door",
                                "action_key": "unlock_door",
                                "api_view_capability_endpoint_id": str(
                                    api_view_capability_endpoint_id
                                ),
                                "api_capability_endpoint_id": str(
                                    api_capability_endpoint_id
                                ),
                                "endpoint_ref": (
                                    "home_devices.unlock_door.unlock_door"
                                ),
                            }
                        ],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return toml_path


def _write_projection_identity_truth(
    root: Path, *, projection_name: str = "Home"
) -> None:
    _ensure_workspace_manifest_for_fixture(root)
    environment_runtime_dir = root / ".aware" / "environment" / "runtime"
    environment_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (environment_runtime_dir / "environment.manifest.json").write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "manifest_path": (
                            "modules/home/structure/ontology/.aware/environment/runtime/"
                            "environment.manifest.json"
                        )
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    module_runtime_dir = (
        root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    module_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (module_runtime_dir / "environment.manifest.json").write_text(
        json.dumps({"ocg": {"snapshot": "ocg.snapshot.msgpack"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    (module_runtime_dir / "ocg.snapshot.msgpack").write_bytes(
        cast(
            bytes,
            msgpack.packb(
                {
                    "object_config_graph_identity": {
                        "object_projection_graph_identities": [
                            {
                                "id": "3218f237-bec9-5a90-a14e-4f9fdfce4ac1",
                                "projection_name": projection_name,
                            }
                        ]
                    }
                },
                use_bin_type=True,
            ),
        )
    )


def _write_deploy_projection_identity_truth(
    root: Path,
    *,
    projection_name: str = "Home",
) -> None:
    _ensure_workspace_manifest_for_fixture(root)
    bundle_root = (
        root / ".aware" / "deploy" / "environment-runtime" / "home-story" / "stable"
    )
    environment_runtime_dir = bundle_root / ".aware" / "environment" / "runtime"
    environment_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (environment_runtime_dir / "environment.manifest.json").write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "manifest_path": (
                            "modules/home/structure/ontology/.aware/environment/runtime/"
                            "environment.manifest.json"
                        )
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    module_runtime_dir = (
        bundle_root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    module_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (module_runtime_dir / "environment.manifest.json").write_text(
        json.dumps({"ocg": {"snapshot": "ocg.snapshot.msgpack"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    (module_runtime_dir / "ocg.snapshot.msgpack").write_bytes(
        cast(
            bytes,
            msgpack.packb(
                {
                    "object_config_graph_identity": {
                        "object_projection_graph_identities": [
                            {
                                "id": "3218f237-bec9-5a90-a14e-4f9fdfce4ac1",
                                "projection_name": projection_name,
                            }
                        ]
                    }
                },
                use_bin_type=True,
            ),
        )
    )


def _build_projection_identity_ocg(
    *, projection_name: str = "home"
) -> ObjectConfigGraph:
    object_config_graph_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compiler/object-config-graph/{projection_name}",
    )
    object_projection_graph_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compiler/object-projection-graph/{projection_name}",
    )
    object_projection_graph_identity_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compiler/object-projection-graph-identity/{projection_name}",
    )
    state_model_class_config_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/class-config/aware_home.home.Door",
    )
    object_projection_graph_node_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compiler/object-projection-graph-node/aware_home.home.Door",
    )
    return ObjectConfigGraph.model_validate(
        {
            "id": str(object_config_graph_id),
            "name": "Interface Compiler Test Graph",
            "hash": "sha256:test-interface-compiler-projection",
            "fqn_prefix": "aware_test.interface_compiler",
            "language": "aware",
            "object_config_graph_identity_id": str(object_config_graph_id),
            "object_config_graph_identity": {
                "id": str(object_config_graph_id),
                "key": "aware_test.interface_compiler",
                "label": "Interface Compiler Test Graph",
                "object_projection_graph_identities": [
                    {
                        "id": str(object_projection_graph_identity_id),
                        "projection_name": projection_name,
                        "label": f"opg:{projection_name}",
                        "is_branchable": True,
                        "object_config_graph_identity_id": str(object_config_graph_id),
                        "object_projection_graph_id": str(object_projection_graph_id),
                    }
                ],
            },
            "object_projection_graphs": [
                {
                    "id": str(object_projection_graph_id),
                    "object_config_graph_id": str(object_config_graph_id),
                    "name": projection_name,
                    "projection_hash": "sha256:test-interface-compiler-projection",
                    "language": "aware",
                    "object_projection_graph_nodes": [
                        {
                            "id": str(object_projection_graph_node_id),
                            "object_projection_graph_id": str(
                                object_projection_graph_id
                            ),
                            "class_config_id": str(state_model_class_config_id),
                            "is_root": True,
                            "class_config": {
                                "id": str(state_model_class_config_id),
                                "class_fqn": "aware_home.home.Door",
                                "name": "Door",
                            },
                        }
                    ],
                }
            ],
        }
    )


def _projection_catalog():
    return build_projection_identity_catalog_from_ocg(
        ocg=_build_projection_identity_ocg()
    )


def test_build_interface_compile_plan_parses_authored_interface_source(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    _write_experience_package(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)

    assert snapshot.source_files == (Path("home_story_app.aware"),)
    assert tuple(package.spec.pane.pane_name for package in snapshot.pane_packages) == (
        "door_control",
    )
    assert snapshot.pane_packages[0].spec.dart is not None
    assert snapshot.pane_packages[0].spec.dart.flutter is not None
    assert (
        snapshot.pane_packages[0].experience_packages[0].spec.experience.package_name
        == "home-shell-experience"
    )
    assert snapshot.pane_source_files == (
        Path("panes/door_control/door_control.aware"),
    )
    assert plan.schema_version == 1
    assert plan.package_name == "home-story-interface"
    assert plan.fqn_prefix == "aware_home_story_interface"
    assert plan.source_files == (
        "home_story_app.aware",
        "panes/door_control/door_control.aware",
    )
    assert len(plan.dependencies) == 1
    assert plan.dependencies[0].package_name == "home-shell-experience"
    assert plan.dependencies[0].kind == "experience_package"

    assert len(plan.pane_ownership) == 1
    pane = plan.pane_ownership[0]
    assert pane.name == "door_control"
    assert pane.pane_kind == "door"
    assert pane.views[0].ref == "home_story.security.door"
    assert pane.views[0].is_default is True

    assert len(plan.interface_ownership) == 1
    interface = plan.interface_ownership[0]
    assert interface.name == "aware_app"
    assert len(interface.windows) == 1
    assert interface.windows[0].key == "main"
    assert tuple(layout.key for layout in interface.windows[0].layouts) == (
        "configuration_map",
        "scene_view",
    )
    assert tuple(
        section.key for section in interface.windows[0].layouts[0].sections
    ) == (
        "workspace",
        "inspector",
    )
    assert tuple(
        section.key for section in interface.windows[0].layouts[1].sections
    ) == (
        "scene",
        "overlay_left",
    )

    assert len(interface.panes) == 1
    pane_mounts = interface.panes[0]
    assert pane_mounts.pane_name == "door_control"
    assert pane_mounts.narrative_key == "security.control"
    assert tuple(
        (
            mount.window_key,
            mount.layout_key,
            mount.section_key,
        )
        for mount in pane_mounts.mounts
    ) == (
        ("main", "configuration_map", "workspace"),
        ("main", "scene_view", "overlay_left"),
    )


def test_emit_dart_runtime_registry_reads_authored_pane_render_spec(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package_with_authored_render(root)
    _write_api_package(root)
    _write_experience_package(root, api_view_ref="home_devices.security_door")
    _write_deploy_projection_identity_truth(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)
    assert snapshot.pane_source_files == (
        Path("panes/door_control/door_control.aware"),
    )

    artifact = emit_interface_dart_pane_registrar_bundle_artifact(
        snapshot=snapshot,
        plan=plan,
        dart_package_dir=root / "dart" / "aware_home_story_interface",
        repo_root=root,
        projection_catalog=_projection_catalog(),
        state_model_catalog={
            "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
        },
    )

    generated = artifact.path.read_text(encoding="utf-8")
    assert "PaneRenderSpec.fromJson(" in generated
    assert '"name": "door_control_default"' in generated
    assert '"pane_name": "door_control"' in generated
    assert '"source_path"' not in generated
    assert '"action_kind": "api"' in generated
    assert '"view_action_key": "unlock_door"' in generated
    assert '"target_ref": "home_devices.unlock_door.unlock_door"' in generated
    assert '"endpoint_ref": "home_devices.unlock_door.unlock_door"' in generated
    assert '"capability_kind": "node_kind"' in generated


def test_interface_state_catalog_loads_api_accessible_dependency_graphs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    namespace = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/api-accessible-dependency-graph-state",
    )
    class_config_id = uuid5(namespace, "DoorControlViewStateV1")
    status_attribute_id = uuid5(namespace, "DoorControlViewStateV1.status")
    summary_attribute_id = uuid5(namespace, "DoorControlViewStateV1.summary")
    api_runtime_dir = root / ".aware" / "api" / "runtime" / "home-devices-api"
    api_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (api_runtime_dir / "api.accessible_dependency_graphs.json").write_text(
        json.dumps(
            {
                "graphs": [
                    {
                        "fqn_prefix": "aware_home_devices_dto",
                        "object_config_graph_nodes": [
                            {
                                "type": "class",
                                "class_config": {
                                    "id": str(class_config_id),
                                    "class_fqn": (
                                        "aware_home_devices_dto.home."
                                        "DoorControlViewStateV1"
                                    ),
                                    "class_config_attribute_configs": [
                                        {
                                            "attribute_config": {
                                                "id": str(status_attribute_id),
                                                "name": "status",
                                            }
                                        },
                                        {
                                            "attribute_config": {
                                                "id": str(summary_attribute_id),
                                                "name": "summary",
                                            }
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    model_catalog = _load_workspace_state_model_catalog(workspace_root=root)
    attribute_catalog = _load_workspace_state_attribute_catalog(workspace_root=root)

    model_ref = "aware_home_devices_dto.home.DoorControlViewStateV1".casefold()
    assert model_catalog[model_ref] == class_config_id
    assert attribute_catalog[model_ref]["status"] == status_attribute_id
    assert attribute_catalog[model_ref]["summary"] == summary_attribute_id


def test_interface_api_view_catalog_loads_view_capability_endpoint_actions(
    tmp_path: Path,
) -> None:
    root = tmp_path
    state_model_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/api-view/home-devices/security-door/state-model",
    )
    api_view_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/api-view/home-devices/security-door/open-door",
    )
    api_runtime_dir = root / ".aware" / "api" / "runtime" / "home-devices-api"
    api_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps(
            {
                "api_ontology": [
                    {
                        "api": {"name": "home_devices"},
                        "views": [
                            {
                                "name": "security_door",
                                "view_ref": "home_devices.security_door",
                                "state_model_ref": (
                                    "aware_home_devices_dto.home."
                                    "DoorControlViewStateV1"
                                ),
                                "state_model_id": str(state_model_id),
                            }
                        ],
                        "view_capability_endpoints": [
                            {
                                "view_name": "security_door",
                                "action_key": "open_door",
                                "api_view_capability_endpoint_id": str(
                                    api_view_capability_endpoint_id
                                ),
                                "endpoint_ref": "home_devices.open_door.open_door",
                            }
                        ],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    catalog = _load_workspace_api_view_state_catalog(workspace_root=root)
    truth = catalog["home_devices.security_door"]

    assert truth.state_model_id == state_model_id
    assert (
        truth.action_endpoints_by_key["open_door"].endpoint_ref
        == "home_devices.open_door.open_door"
    )
    assert (
        truth.action_endpoints_by_key["open_door"].api_view_capability_endpoint_id
        == api_view_capability_endpoint_id
    )


def test_compile_interface_workspace_materializes_authored_pane_render_specs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package_with_authored_render(root)
    _write_api_package(root)
    _write_experience_package(root, api_view_ref="home_devices.security_door")
    _write_deploy_projection_identity_truth(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
        state_model_catalog={
            "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
        },
    )

    assert result.render_spec_materialization_artifact is not None
    materialized = json.loads(
        result.render_spec_materialization_artifact.path.read_text(encoding="utf-8")
    )
    assert materialized["schema_version"] == 2
    assert (
        materialized["materialization_kind"]
        == "aware.interface.pane-render-spec.materialization.v1"
    )
    assert len(materialized["materialization_commit_id"]) == 36
    assert len(materialized["materialization_content_hash_sha256"]) == 64
    assert materialized["render_spec_count"] == 1
    render_spec = materialized["render_specs"][0]
    assert render_spec["source_kind"] == "authored_aware"
    assert (
        render_spec["source_path"]
        == "panes/door_control/door_control.aware#render:default"
    )
    assert render_spec["render_spec_id"] == render_spec["payload"]["spec_id"]
    assert len(render_spec["render_spec_content_hash_sha256"]) == 64
    assert (
        render_spec["semantic_object_ids"]["pane_render_spec_id"]
        == render_spec["payload"]["spec_id"]
    )
    assert set(render_spec["semantic_object_ids"]["pane_render_node_ids_by_key"]) == {
        "root",
        "title",
        "unlock",
    }
    assert set(
        render_spec["semantic_object_ids"][
            "pane_renderer_capability_requirement_ids_by_ref"
        ]
    ) == {
        "node_kind:column",
        "action_binding:view_action",
    }
    assert render_spec["payload"]["name"] == "door_control_default"
    assert render_spec["payload"]["pane_kind"] == "door"
    assert render_spec["payload"]["nodes"][0]["node_key"] == "root"

    rerun = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
        state_model_catalog={
            "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
        },
    )
    assert rerun.render_spec_materialization_artifact is not None
    rerun_materialized = json.loads(
        rerun.render_spec_materialization_artifact.path.read_text(encoding="utf-8")
    )
    assert (
        rerun_materialized["materialization_commit_id"]
        == materialized["materialization_commit_id"]
    )
    assert (
        rerun_materialized["materialization_content_hash_sha256"]
        == materialized["materialization_content_hash_sha256"]
    )

    assert result.dart_registrar_bundle_artifact is not None
    generated = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert '"name": "door_control_default"' in generated
    assert '"source_path"' not in generated


def test_dart_runtime_registry_prefers_materialized_render_specs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package_with_authored_render(root)
    _write_api_package(root)
    _write_experience_package(root, api_view_ref="home_devices.security_door")
    _write_deploy_projection_identity_truth(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)
    state_model_catalog = {
        "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
    }
    materialization_artifact = emit_interface_pane_render_spec_materialization_artifact(
        snapshot=snapshot,
        plan=plan,
        runtime_package_dir=root
        / ".aware"
        / "interface"
        / "runtime"
        / "home-story-interface",
        repo_root=root,
        projection_catalog=_projection_catalog(),
        state_model_catalog=state_model_catalog,
    )

    source_path = root / "panes" / "door_control" / "door_control.aware"
    source_path.write_text(
        source_path.read_text(encoding="utf-8").replace(
            '            label "Unlock";',
            '            label "Source changed";',
        ),
        encoding="utf-8",
    )

    artifact = emit_interface_dart_pane_registrar_bundle_artifact(
        snapshot=snapshot,
        plan=plan,
        dart_package_dir=root / "dart" / "aware_home_story_interface",
        repo_root=root,
        projection_catalog=_projection_catalog(),
        state_model_catalog=state_model_catalog,
        render_spec_materialization_path=materialization_artifact.path,
    )

    generated = artifact.path.read_text(encoding="utf-8")
    assert '"label": "Unlock"' in generated
    assert "Source changed" not in generated
    assert '"name": "door_control_default"' in generated


def test_emit_dart_runtime_registry_falls_back_to_json_render_spec_with_warning(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    _write_json_render_spec(root)
    _write_api_package(root)
    _write_experience_package(root)
    _write_deploy_projection_identity_truth(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)
    assert snapshot.pane_render_spec_files == (
        Path("panes/door_control/render_specs/door_control.render_spec.json"),
    )

    with pytest.warns(
        PaneRenderSpecCompatibilityWarning, match="compatibility JSON render specs"
    ):
        artifact = emit_interface_dart_pane_registrar_bundle_artifact(
            snapshot=snapshot,
            plan=plan,
            dart_package_dir=root / "dart" / "aware_home_story_interface",
            repo_root=root,
            projection_catalog=_projection_catalog(),
            state_model_catalog={
                "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
            },
        )

    generated = artifact.path.read_text(encoding="utf-8")
    assert '"name": "door_control_json"' in generated
    assert '"text": "Door control JSON"' in generated


def test_interface_workspace_snapshot_loads_declared_attention_package_artifact(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-attention", "attention_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root, include_experience_dependency=False)
    artifact_path = _write_attention_compile_artifact(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    assert len(snapshot.attention_packages) == 1
    attention_package = snapshot.attention_packages[0]
    assert attention_package.package_name == "home-shell-attention"
    assert attention_package.runtime_artifact_path == artifact_path.resolve()
    assert len(attention_package.layouts) == 1
    assert attention_package.layouts[0].layout_key == "scene_view"
    assert attention_package.layouts[0].sections[0].section_key == "overlay_left"


def test_interface_workspace_snapshot_loads_workspace_attention_manifest_when_dependency_is_undeclared(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(),
    )
    _write_interface_source(root)
    _write_pane_package(root, include_experience_dependency=False)
    _write_attention_package(root)
    _write_attention_compile_artifact(root)
    _write_workspace_manifest(
        root,
        attentions=("attentions/home-shell-attention/aware.attention.toml",),
    )

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    assert len(snapshot.attention_packages) == 1


def test_interface_workspace_snapshot_does_not_load_workspace_sdk_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(root)
    _write_interface_source(root)
    _write_pane_package(root, include_experience_dependency=False)
    _write_sdk_package(root)
    _write_workspace_manifest(
        root,
        sdks=("sdks/home/aware/aware.sdk.toml",),
    )

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    assert not hasattr(snapshot, "sdk_packages")
    assert not hasattr(snapshot, "sdk_source_files")
    assert snapshot.pane_source_files == (
        Path("panes/door_control/door_control.aware"),
    )


def test_interface_workspace_snapshot_loads_declared_experience_package_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    experience_toml_path = _write_experience_package(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    assert len(snapshot.experience_packages) == 1
    experience_package = snapshot.experience_packages[0]
    assert experience_package.spec_path == experience_toml_path.resolve()
    assert experience_package.package_root == experience_toml_path.parent.resolve()
    assert experience_package.spec.experience.package_name == "home-shell-experience"
    assert experience_package.source_files == (Path("home_shell.aware"),)


def test_build_interface_compile_plan_requires_declared_pane_experience_package_for_pane_views(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root, include_experience_dependency=False)
    _write_experience_package(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    with pytest.raises(
        ValueError,
        match="outside the declared pane experience_package dependency scope",
    ):
        _ = build_interface_compile_plan(snapshot=snapshot)


def test_build_interface_compile_plan_does_not_require_interface_experience_dependency_for_pane_views(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(root, dependencies=())
    _write_interface_source(root)
    _write_pane_package(root)
    _write_experience_package(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    plan = build_interface_compile_plan(snapshot=snapshot)

    assert plan.package_name == "home-story-interface"


def test_build_interface_config_bundle_resolves_projection_identity_from_deploy_bundle(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    _write_api_package(root)
    _write_experience_package(root)
    _write_deploy_projection_identity_truth(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_interface_compile_plan(snapshot=snapshot)
    bundle = build_interface_config_bundle(
        snapshot=snapshot,
        plan=plan,
        projection_catalog=_projection_catalog(),
        state_model_catalog={
            "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
        },
    )

    assert bundle.name == "aware_app"
    assert bundle.pane_configs[0].projection_experience_views[0].view_ref == (
        "home_story.security.door"
    )
    assert bundle.pane_configs[0].projection_experience_views[
        0
    ].projection_view_key == ("security.door")


def test_build_interface_config_bundle_rejects_multi_view_pane_before_section_mount(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_multi_view_pane_package(root)
    _write_api_package(root)
    _write_experience_package(root, additional_view_keys=("detail",))
    _write_projection_identity_truth(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    with pytest.raises(
        ValueError,
        match=r"must declare exactly one view",
    ):
        _ = build_interface_compile_plan(snapshot=snapshot)


def test_build_interface_compile_plan_rejects_duplicate_section_mount(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(
        root,
        dependencies=(("home-shell-experience", "experience_package"),),
    )
    _write_interface_source_with_duplicate_section_mount(root)
    _write_pane_package(root)
    _write_api_package(root)
    _write_experience_package(root)

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()

    with pytest.raises(
        ValueError,
        match=r"duplicates mount 'main\.configuration_map\.workspace'",
    ):
        _ = build_interface_compile_plan(snapshot=snapshot)
