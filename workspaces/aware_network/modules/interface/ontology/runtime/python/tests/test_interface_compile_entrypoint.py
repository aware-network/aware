from __future__ import annotations

import json
from pathlib import Path
import shutil
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
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "ontology" / "runtime" / "python"
)
if _INTERFACE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _INTERFACE_RUNTIME_ROOT_STR)
_ATTENTION_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "attention" / "ontology" / "runtime" / "python"
)
if _ATTENTION_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _ATTENTION_RUNTIME_ROOT_STR)
_NETWORK_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "network" / "ontology" / "runtime" / "python"
)
if _NETWORK_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _NETWORK_RUNTIME_ROOT_STR)
_IDENTITY_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "identity" / "ontology" / "runtime" / "python"
)
if _IDENTITY_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _IDENTITY_RUNTIME_ROOT_STR)
_ENVIRONMENT_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "environment" / "ontology" / "runtime" / "python"
)
if _ENVIRONMENT_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _ENVIRONMENT_RUNTIME_ROOT_STR)
_SESSION_LIB_ROOT_STR = str(_REPO_ROOT / "libs" / "session" / "python")
if _SESSION_LIB_ROOT_STR not in sys.path:
    sys.path.insert(0, _SESSION_LIB_ROOT_STR)
_ENVIRONMENT_LIB_ROOT_STR = str(_REPO_ROOT / "libs" / "environment")
if _ENVIRONMENT_LIB_ROOT_STR not in sys.path:
    sys.path.insert(0, _ENVIRONMENT_LIB_ROOT_STR)

from aware_interface.compile import compile_interface_workspace  # noqa: E402
from aware_interface.builder import (  # noqa: E402
    ApiViewStateTruth,
    build_state_model_catalog_from_ocg,
    _resolve_projection_identity_catalog,
)
from aware_interface.workspace import InterfaceWorkspace  # noqa: E402
from aware_attention.compile import (  # noqa: E402
    compile_attention_workspace,  # pyright: ignore[reportMissingImports]
)
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)  # noqa: E402
from aware_meta_ontology.stable_ids import (  # noqa: E402
    stable_class_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_identity_id,
    stable_object_config_graph_node_id,
    stable_object_projection_graph_id,
    stable_object_projection_graph_identity_id,
    stable_object_projection_graph_node_id,
)


def _write_interface_toml(root: Path, *, compilation_mode: str = "raw_xor") -> Path:
    return _write_interface_toml_with_dependencies(
        root,
        compilation_mode=compilation_mode,
        dependencies=(),
    )


def _write_interface_toml_with_dependencies(
    root: Path,
    *,
    compilation_mode: str = "raw_xor",
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
        f'compilation_mode = "{compilation_mode}"',
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
                "        layout scene_view default {",
                "            section scene",
                "            section overlay_left",
                "        }",
                "    }",
                "",
                "    pane door_control {",
                "        mount main.scene_view.overlay_left",
                "        narrative security.control",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_attention_backed_interface_source(root: Path, *, layout_key: str = "scene_view") -> None:
    _ = (root / "home_story_app.aware").write_text(
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                f"        layout {layout_key} default {{}}",
                "    }",
                "",
                "    pane door_control {",
                f"        mount main.{layout_key}.overlay_left",
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
            'package_name = "home-story-experience"',
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


def _write_render_component_package(root: Path) -> None:
    component_root = root / "render_components" / "aware-content-render-components"
    component_root.mkdir(parents=True, exist_ok=True)
    _ = (component_root / "aware.render_component.toml").write_text(
        "\n".join(
            [
                "aware_render_component = 1",
                "",
                "[render_component]",
                'package_name = "aware-content-render-components"',
                'fqn_prefix = "aware_content_render_components"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                "",
                "[dart]",
                'package_path = "dart/aware_content_render_components"',
                'package_name = "aware_content_render_components"',
                "",
                "[dart.flutter]",
                'library = "package:aware_content_render_components/aware_content_render_components.dart"',
                'symbol = "registerRenderComponents"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_sdk_package(root: Path, *, include_operation_dependency: bool = False) -> Path:
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
    source_lines = [
        "sdk home_sdk {",
        "    api home_devices;",
        "",
        "    operation unlock_door {",
        "        endpoint home_devices.unlock_door.unlock_door;",
        "    }",
        "}",
        "",
    ]
    if include_operation_dependency:
        source_lines.extend(
            [
                "sdk home_dev_sdk {",
                "    api home_devices;",
                "",
                "    operation status {",
                "        operation home_sdk.unlock_door;",
                "    }",
                "}",
                "",
            ]
        )
    _ = (sdk_root / "home_sdk.aware").write_text(
        "\n".join(source_lines),
        encoding="utf-8",
    )
    return toml_path


def _write_attention_compile_artifact(
    root: Path,
    *,
    package_name: str = "home-shell-attention",
    layout_key: str = "scene_view",
    section_key: str = "overlay_left",
) -> Path:
    artifact_path = root / ".aware" / "attention" / "runtime" / package_name / "attention.compile_plan.json"
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


def _compile_repo_attention_workspace_shell(*, repo_root: Path) -> None:
    compile_attention_workspace(
        toml_path=repo_root
        / "workspaces"
        / "aware_workspace"
        / "attentions"
        / "aware_workspace_shell"
        / "aware.attention.toml",
        repo_root=repo_root,
        emit_compile_plan=True,
    )


def _compile_home_story_sample_attention_workspace_shell(*, repo_root: Path) -> None:
    compile_attention_workspace(
        toml_path=(
            repo_root
            / "modules"
            / "experience"
            / "runtime"
            / "samples"
            / "e2e"
            / "home_story_workspace"
            / "attentions"
            / "aware_workspace_shell"
            / "aware.attention.toml"
        ),
        repo_root=repo_root,
        emit_compile_plan=True,
    )


def _write_workspace_truth(root: Path) -> None:
    _ = (root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "home_story_workspace"',
                "environments = []",
                'apis = ["apis/home_devices/aware.api.toml"]',
                "sdks = []",
                "services = []",
                'experiences = ["experiences/home_story/aware.experience.toml"]',
                "attentions = []",
                'panes = ["panes/door_control/aware.pane.toml"]',
                "interfaces = []",
                "nodes = []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "home_devices"
    api_root.mkdir(parents=True, exist_ok=True)
    _ = (api_root / "aware.api.toml").write_text(
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
    _ = (api_root / "bindings" / "home_devices.apis.aware").parent.mkdir(parents=True, exist_ok=True)
    _ = (api_root / "bindings" / "home_devices.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability unlock_door {",
                "        endpoint unlock_door",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_runtime_dir = root / ".aware" / "api" / "runtime" / "home-devices-api"
    api_runtime_dir.mkdir(parents=True, exist_ok=True)
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

    experience_root = root / "experiences" / "home_story"
    experience_root.mkdir(parents=True, exist_ok=True)
    _ = (experience_root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "home-story-experience"',
                'fqn_prefix = "aware_home_story_experience"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (experience_root / "home_story.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default api_view home_devices.security_door {",
                '            """Door state view."""',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    workspace_runtime_dir = root / ".aware" / "environment" / "runtime"
    workspace_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (workspace_runtime_dir / "environment.manifest.json").write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "manifest_path": (
                            "modules/home/structure/ontology/.aware/environment/runtime/" "environment.manifest.json"
                        )
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    module_runtime_dir = root / "modules" / "home" / "structure" / "ontology" / ".aware" / "environment" / "runtime"
    module_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (module_runtime_dir / "environment.manifest.json").write_text(
        json.dumps({"ocg": {"snapshot": "ocg.snapshot.msgpack"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    object_config_graph_id = stable_object_config_graph_id(fqn_prefix="aware_home", language="aware")
    object_config_graph_identity_id = stable_object_config_graph_identity_id(key="aware_home")
    object_projection_graph_id = stable_object_projection_graph_id(
        object_config_graph_id=object_config_graph_id,
        name="home",
    )
    projection_identity_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=object_config_graph_identity_id,
        object_projection_graph_id=object_projection_graph_id,
    )
    class_fqn = "aware_home.home.Door"
    object_config_graph_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type="class",
        node_key=class_fqn,
    )
    state_model_class_config_id = stable_class_config_id(
        object_config_graph_node_id=object_config_graph_node_id,
        class_fqn=class_fqn,
    )
    api_view_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/api-view-capability-endpoint/home-devices/security-door/unlock-door",
    )
    api_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/api-capability-endpoint/home-devices/unlock-door",
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
                                "state_model_ref": class_fqn,
                                "state_model_id": str(state_model_class_config_id),
                                "observable_ref": "home.security",
                            }
                        ],
                        "view_capability_endpoints": [
                            {
                                "view_name": "security_door",
                                "action_key": "unlock_door",
                                "api_view_capability_endpoint_id": str(api_view_capability_endpoint_id),
                                "api_capability_endpoint_id": str(api_capability_endpoint_id),
                                "endpoint_ref": ("home_devices.unlock_door.unlock_door"),
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
    object_projection_graph_node_id = stable_object_projection_graph_node_id(
        object_projection_graph_id=object_projection_graph_id,
        class_config_id=state_model_class_config_id,
    )
    ocg_payload = {
        "fqn_prefix": "aware_home",
        "object_config_graph_identity": {
            "id": str(object_config_graph_identity_id),
            "key": "aware_home",
            "object_projection_graph_identities": [
                {
                    "id": str(projection_identity_id),
                    "projection_name": "home",
                    "object_projection_graph_id": str(object_projection_graph_id),
                }
            ],
        },
        "object_config_graph_nodes": [],
        "object_projection_graphs": [
            {
                "id": str(object_projection_graph_id),
                "object_config_graph_id": str(object_config_graph_id),
                "name": "home",
                "projection_hash": "sha256:test-interface-projection",
                "language": "aware",
                "object_projection_graph_nodes": [
                    {
                        "id": str(object_projection_graph_node_id),
                        "object_projection_graph_id": str(object_projection_graph_id),
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
    _ = (module_runtime_dir / "ocg.snapshot.msgpack").write_bytes(
        bytes(
            cast(
                bytes,
                msgpack.packb(
                    ocg_payload,
                    use_bin_type=True,
                ),
            )
        )
    )


def _write_workspace_manifest_with_sdk(root: Path) -> None:
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
    _ = (root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "home_story_workspace"',
                'environments = ["aware.environment.toml"]',
                "apis = []",
                'sdks = ["sdks/home/aware/aware.sdk.toml"]',
                "services = []",
                "experiences = []",
                "attentions = []",
                'panes = ["panes/door_control/aware.pane.toml"]',
                "interfaces = []",
                "nodes = []",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _build_projection_identity_ocg(*, projection_name: str = "home") -> ObjectConfigGraph:
    object_config_graph_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compile/object-config-graph/{projection_name}",
    )
    object_projection_graph_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compile/object-projection-graph/{projection_name}",
    )
    object_projection_graph_identity_id = uuid5(
        NAMESPACE_URL,
        f"aware://tests/interface-compile/object-projection-graph-identity/{projection_name}",
    )
    state_model_class_config_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/class-config/aware_home.home.Door",
    )
    object_projection_graph_node_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/object-projection-graph-node/aware_home.home.Door",
    )
    return ObjectConfigGraph.model_validate(
        {
            "id": str(object_config_graph_id),
            "name": "Interface Override Graph",
            "hash": "sha256:test-interface-projection-override",
            "fqn_prefix": "aware_test.interface_override",
            "language": "aware",
            "object_config_graph_identity_id": str(object_config_graph_id),
            "object_config_graph_identity": {
                "id": str(object_config_graph_id),
                "key": "aware_test.interface_override",
                "label": "Interface Override Graph",
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
                    "projection_hash": "sha256:test-interface-projection",
                    "language": "aware",
                    "object_projection_graph_nodes": [
                        {
                            "id": str(object_projection_graph_node_id),
                            "object_projection_graph_id": str(object_projection_graph_id),
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


def _home_devices_api_view_catalog() -> dict[str, ApiViewStateTruth]:
    return {
        "home_devices.security_door": ApiViewStateTruth(
            view_ref="home_devices.security_door",
            state_model_ref="aware_home.home.Door",
            state_model_id=uuid5(
                NAMESPACE_URL,
                "aware://tests/interface-compile/class-config/aware_home.home.Door",
            ),
        )
    }


def _home_story_state_model_catalog() -> dict[str, UUID]:
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix="aware_home",
        language="aware",
    )
    catalog: dict[str, UUID] = {}
    for class_fqn in (
        "aware_home.home.Home",
        "aware_home.home.Door",
        "aware_home.home.Tv",
    ):
        object_config_graph_node_id = stable_object_config_graph_node_id(
            object_config_graph_id=object_config_graph_id,
            type="class",
            node_key=class_fqn,
        )
        catalog[class_fqn] = stable_class_config_id(
            object_config_graph_node_id=object_config_graph_node_id,
            class_fqn=class_fqn,
        )
    return catalog


def test_state_model_catalog_accepts_implicit_default_domain_refs() -> None:
    class_config_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/class-config/aware_home.default.home.Home",
    )
    object_config_graph_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-compile/object-config-graph/default-domain",
    )
    graph = ObjectConfigGraph.model_validate(
        {
            "id": str(object_config_graph_id),
            "name": "Home Graph",
            "hash": "sha256:test-home-graph",
            "fqn_prefix": "aware_home",
            "language": "aware",
            "object_config_graph_nodes": [
                {
                    "id": str(
                        uuid5(
                            NAMESPACE_URL,
                            "aware://tests/interface-compile/object-config-graph-node/home",
                        )
                    ),
                    "object_config_graph_id": str(object_config_graph_id),
                    "class_config_id": str(class_config_id),
                    "type": "class",
                    "node_key": "aware_home.default.home.Home",
                    "class_config": {
                        "id": str(class_config_id),
                        "class_fqn": "aware_home.default.home.Home",
                        "name": "Home",
                    },
                }
            ],
        }
    )

    catalog = build_state_model_catalog_from_ocg(ocg=graph)

    assert catalog["aware_home.default.home.home"] == class_config_id
    assert catalog["aware_home.home.home"] == class_config_id


def test_compile_interface_workspace_returns_snapshot_only_for_raw_xor(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_interface_toml(root, compilation_mode="raw_xor")
    _write_interface_source(root)
    _write_pane_package(root, include_experience_dependency=False)

    result = compile_interface_workspace(toml_path=toml_path, repo_root=root)

    assert result.snapshot.spec.interface.package_name == "home-story-interface"
    assert result.snapshot.source_files == (Path("home_story_app.aware"),)
    assert result.snapshot.pane_source_files == (Path("panes/door_control/door_control.aware"),)
    assert result.compile_plan is None
    assert result.compile_plan_artifact is None
    assert result.dart_registrar_bundle_artifact is None


def test_interface_projection_catalog_uses_declared_workspace_dependency_index(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    network_root = repo_root / "workspaces" / "aware_network"
    kernel_root = repo_root / "workspaces" / "aware_kernel"
    interface_root = network_root / "interfaces" / "aware_control"
    interface_root.mkdir(parents=True, exist_ok=True)
    kernel_root.mkdir(parents=True, exist_ok=True)

    _ = (kernel_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "aware_kernel"',
                "interfaces = []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (network_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "aware_network"',
                "interfaces = []",
                "",
                "[[workspace.dependencies]]",
                'id = "aware_kernel"',
                'kind = "workspace"',
                'source = "workspace://aware_kernel"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    code_ontology_root = kernel_root / "modules" / "code" / "ontology"
    code_projection_root = code_ontology_root / "structure" / "aware"
    code_projection_root.mkdir(parents=True, exist_ok=True)
    _ = (code_ontology_root / "aware.ontology.toml").write_text(
        "\n".join(
            [
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "code-ontology"',
                'fqn_prefix = "aware_code"',
                'package_root = "."',
                'sources_root = "structure/aware"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (code_projection_root / "code_package_projection.aware").write_text(
        "\n".join(
            [
                "projection CodePackage {",
                "    root aware_code.package.CodePackage",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    provider_projection_identity_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/provider-backed-codepackage-opgi",
    )
    package_index_path = kernel_root / ".aware" / "meta" / "runtime" / "package_projection_index.v1.json"
    package_index_path.parent.mkdir(parents=True, exist_ok=True)
    code_manifest_path = code_ontology_root / "structure" / "aware.toml"
    _ = package_index_path.write_text(
        json.dumps(
            {
                "schema": "aware.meta.runtime.package_projection_index.v1",
                "version": 1,
                "catalog_signature": "test-interface-dependency-index",
                "packages": [
                    {
                        "module_id": "code",
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "manifest_path": str(code_manifest_path),
                        "dependency_package_names": [],
                        "projection_names": ["CodePackage"],
                    }
                ],
                "projections": [
                    {
                        "projection_name": "CodePackage",
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "manifest_path": str(code_manifest_path),
                        "object_projection_graph_identity_id": str(provider_projection_identity_id),
                    }
                ],
                "semantic_objects": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    interface_toml_path = interface_root / "aware.interface.toml"
    _ = interface_toml_path.write_text(
        "\n".join(
            [
                "aware_interface = 1",
                "",
                "[interface]",
                'package_name = "aware-control-interface"',
                'fqn_prefix = "aware_control_interface"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                'config_bundle_path = "bundles/interface.config.bundle.json"',
                'compilation_mode = "raw_xor"',
                "",
                "[dart]",
                'package_path = "dart/aware_control_interface"',
                'package_name = "aware_control_interface"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (interface_root / "aware_control.aware").write_text(
        "interface aware_control {}\n",
        encoding="utf-8",
    )

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=network_root,
    ).build_snapshot()

    assert (
        kernel_root.resolve(),
        "declared_workspace_dependency_artifact_root",
    ) in tuple((root.root, root.source_kind) for root in snapshot.dependency_catalog_roots)

    projection_catalog = _resolve_projection_identity_catalog(snapshot=snapshot)

    assert projection_catalog["codepackage"].object_projection_graph_identity_id == provider_projection_identity_id


def test_compile_interface_workspace_emits_plan_for_interface_ontology(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.compile_plan is not None
    assert result.compile_plan_artifact is not None
    assert result.dart_registrar_bundle_artifact is not None
    assert result.compile_plan_artifact.relpath == (
        ".aware/interface/runtime/home-story-interface/interface.compile_plan.json"
    )
    assert result.dart_registrar_bundle_artifact.relpath == (
        "dart/aware_home_story_interface/lib/_aware/interface/pane_package_registrars.dart"
    )
    payload = result.compile_plan_artifact.path.read_text(encoding="utf-8")
    assert '"pane_ownership"' in payload
    assert '"interface_ownership"' in payload
    assert '"home_story.security.door"' in payload
    assert '"home_devices.unlock_door"' not in payload
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "import 'package:aware_pane_runtime/aware_pane_runtime.dart';" in dart_payload
    assert "import 'package:aware_door_control_pane/aware_door_control_pane.dart'" in dart_payload
    assert "void registerPanePackages(PanePackageRegistry registry)" in dart_payload
    assert ".registerPanePackage(registry);" in dart_payload
    assert "apiPackages:" not in dart_payload
    assert "apiClientFactories:" not in dart_payload
    assert "import 'package:aware_api/aware_api.dart';" not in dart_payload
    assert "aware_home_devices_service_api" not in dart_payload
    assert "_buildAwareHomeDevicesServiceApiClient" not in dart_payload


def test_compile_interface_workspace_emits_render_component_registrars(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(
            ("home-story-experience", "experience_package"),
            (
                "aware-content-render-components",
                "render_component_package",
            ),
        ),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    _write_render_component_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.dart_registrar_bundle_artifact is not None
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "package:aware_content_render_components/" "aware_content_render_components.dart" in dart_payload
    assert "void registerRenderComponents(RenderComponentRegistryBuilder registry)" in dart_payload
    assert ".registerRenderComponents(registry);" in dart_payload


def test_compile_interface_workspace_ignores_experience_view_model_decoder_registry(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)
    registry_dir = root / "experiences" / "home_story" / "languages" / "dart" / "aware_home_story_experience" / "lib"
    registry_dir.mkdir(parents=True, exist_ok=True)
    _ = (registry_dir / "view_model_registry.dart").write_text(
        "final awareHomeStoryExperienceViewModelDecoders = <String, Object>{};\n",
        encoding="utf-8",
    )
    _ = (registry_dir / "aware_home_story_experience.dart").write_text(
        "export 'view_model_registry.dart';\n",
        encoding="utf-8",
    )

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.dart_registrar_bundle_artifact is not None
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "import 'package:aware_home_story_experience/aware_home_story_experience.dart'" not in dart_payload
    assert "viewStateDecoderRegistry:" not in dart_payload
    assert "<Map<String, InterfaceViewStateDecoder>>[" not in dart_payload
    assert "aware_home_story_experience.awareHomeStoryExperienceViewModelDecoders" not in dart_payload


def test_compile_interface_workspace_emits_config_bundle_for_interface_ontology(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.compile_plan is not None
    assert result.compile_plan_artifact is not None
    assert result.config_bundle_artifact is not None
    assert result.dart_registrar_bundle_artifact is not None
    assert result.config_bundle_artifact.relpath == "bundles/interface.config.bundle.json"

    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    assert payload["name"] == "aware_app"
    assert "apis" not in payload
    assert payload["window_configs"][0]["key"] == "main"
    assert payload["window_configs"][0]["layout_configs"][0]["key"] == "scene_view"
    assert payload["window_configs"][0]["layout_configs"][0]["sections"] == [
        {
            "key": "scene",
            "layout_config_section_config_id": (
                payload["window_configs"][0]["layout_configs"][0]["sections"][0]["layout_config_section_config_id"]
            ),
        },
        {
            "key": "overlay_left",
            "layout_config_section_config_id": (
                payload["window_configs"][0]["layout_configs"][0]["sections"][1]["layout_config_section_config_id"]
            ),
        },
    ]
    assert payload["pane_configs"][0]["name"] == "door_control"
    assert payload["pane_configs"][0]["pane_package_name"] == "home-story-door-control-pane"
    assert payload["pane_configs"][0]["pane_package_id"] is not None
    assert payload["pane_configs"][0]["pane_kind"] == "door"
    assert payload["pane_configs"][0]["projection_experience_views"][0]["view_ref"] == "home_story.security.door"
    assert payload["pane_configs"][0]["projection_experience_views"][0]["projection_view_key"] == "security.door"
    assert "api_capability_endpoints" not in payload["pane_configs"][0]
    assert "sdk_operations" not in payload["pane_configs"][0]


def test_compile_interface_workspace_ignores_workspace_sdk_catalog(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    _write_workspace_manifest_with_sdk(root)
    _write_sdk_package(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.config_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    pane_payload = payload["pane_configs"][0]
    assert "api_capability_endpoints" not in pane_payload
    assert "sdk_operations" not in pane_payload


def test_compile_interface_workspace_does_not_resolve_sdk_operation_dependencies(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    _write_workspace_manifest_with_sdk(root)
    _write_sdk_package(root, include_operation_dependency=True)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.config_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    assert "sdk_operations" not in payload["pane_configs"][0]


def test_compile_interface_workspace_accepts_projection_identity_ocg_override(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    shutil.rmtree(root / ".aware" / "environment")
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    try:
        _ = compile_interface_workspace(
            toml_path=toml_path,
            repo_root=root,
            emit_config_bundle=True,
        )
    except ValueError as exc:
        assert "without workspace OPG identity truth" in str(exc)
    else:
        raise AssertionError("Expected compile_interface_workspace to require projection identity truth")

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.config_bundle_artifact is not None
    assert result.dart_registrar_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    assert payload["pane_configs"][0]["projection_experience_views"][0]["view_ref"] == "home_story.security.door"
    assert payload["pane_configs"][0]["projection_experience_views"][0]["projection_view_key"] == "security.door"
    assert payload["pane_configs"][0]["projection_experience_views"][0]["state_model_id"] == str(
        uuid5(
            NAMESPACE_URL,
            "aware://tests/interface-compile/class-config/aware_home.home.Door",
        )
    )
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "sectionRepresentations: const <InterfacePackageRuntimeSectionRepresentation>[" in dart_payload
    assert "projectionViewKey: 'security.door'" in dart_payload


def test_compile_interface_workspace_accepts_projection_identity_ocgs(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    shutil.rmtree(root / ".aware" / "environment")
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        emit_config_bundle=True,
        projection_identity_ocgs=(_build_projection_identity_ocg(),),
    )

    assert result.config_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    view_payload = payload["pane_configs"][0]["projection_experience_views"][0]
    assert view_payload["view_ref"] == "home_story.security.door"
    assert view_payload["projection_view_key"] == "security.door"
    assert view_payload["state_model_id"] == str(
        uuid5(
            NAMESPACE_URL,
            "aware://tests/interface-compile/class-config/aware_home.home.Door",
        )
    )


def test_compile_interface_workspace_ignores_api_endpoint_catalog_override(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    shutil.rmtree(root / ".aware" / "api")
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-story-experience", "experience_package"),),
    )
    _write_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
        api_view_catalog=_home_devices_api_view_catalog(),
    )

    assert result.config_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    assert "api_capability_endpoints" not in payload["pane_configs"][0]


def test_compile_interface_workspace_emits_attention_backed_layout_sections(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    _write_attention_compile_artifact(root)
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(
            ("home-story-experience", "experience_package"),
            ("home-shell-attention", "attention_package"),
        ),
    )
    _write_attention_backed_interface_source(root)
    _write_pane_package(root)

    result = compile_interface_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
        emit_config_bundle=True,
        projection_identity_ocg=_build_projection_identity_ocg(),
    )

    assert result.config_bundle_artifact is not None
    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    layout = payload["window_configs"][0]["layout_configs"][0]
    assert layout["key"] == "scene_view"
    assert layout["layout_config_id"] == "3377fbc6-7c1d-5f58-ad77-7cbfd6df413f"
    assert layout["sections"] == [
        {
            "key": "overlay_left",
            "layout_config_section_config_id": "8741f7e0-4e72-5be3-a49c-51c6f181f8af",
        }
    ]
    assert payload["pane_configs"][0]["projection_experience_views"][0]["section_mounts"] == [
        {
            "layout_config_section_config_id": "8741f7e0-4e72-5be3-a49c-51c6f181f8af",
            "mount_id": payload["pane_configs"][0]["projection_experience_views"][0]["section_mounts"][0]["mount_id"],
            "is_default": False,
        }
    ]


def test_compile_interface_workspace_fails_when_attention_layout_truth_is_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_workspace_truth(root)
    _write_attention_compile_artifact(root, layout_key="other_layout")
    toml_path = _write_interface_toml_with_dependencies(
        root,
        compilation_mode="interface_ontology",
        dependencies=(("home-shell-attention", "attention_package"),),
    )
    _write_attention_backed_interface_source(root, layout_key="scene_view")
    _write_pane_package(root)

    try:
        _ = compile_interface_workspace(
            toml_path=toml_path,
            repo_root=root,
            emit_config_bundle=True,
        )
    except ValueError as exc:
        assert "missing Attention-backed layout truth" in str(exc)
    else:
        raise AssertionError("Expected compile_interface_workspace to require Attention-backed layout truth")


def test_root_aware_app_interface_workspace_snapshot_exposes_authored_sources() -> None:
    repo_root = _REPO_ROOT
    interface_toml_path = repo_root / "interfaces" / "aware_app" / "aware.interface.toml"

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=repo_root,
    ).build_snapshot()

    assert snapshot.spec.interface.package_name == "aware-app-interface"
    assert snapshot.source_files == ()
    assert tuple(package.spec.pane.pane_name for package in snapshot.pane_packages) == (
        "hub_package_selector",
        "identity_admission",
        "interface_admission",
        "interface_mount_status",
        "network_territory",
        "node_session_status",
        "terminal",
    )
    assert snapshot.pane_source_files == (
        Path(
            "workspaces/aware_network/modules/hub/interfaces/panes/" "hub_package_selector/hub_package_selector.aware"
        ),
        Path(
            "workspaces/aware_network/modules/identity/interfaces/panes/" "identity_admission/identity_admission.aware"
        ),
        Path(
            "workspaces/aware_network/modules/interface/interfaces/panes/"
            "interface_admission/interface_admission.aware"
        ),
        Path(
            "workspaces/aware_network/modules/interface/interfaces/panes/"
            "interface_mount_status/interface_mount_status.aware"
        ),
        Path("workspaces/aware_network/modules/network/interfaces/panes/" "network_territory/network_territory.aware"),
        Path("workspaces/aware_network/modules/node/interfaces/panes/" "node_session_status/node_session_status.aware"),
        Path("panes/terminal/terminal.aware"),
    )
    assert (
        snapshot.config_bundle_path
        == (repo_root / "interfaces" / "aware_app" / "bundles" / "interface.config.bundle.json").resolve()
    )


def test_home_story_sample_interface_package_compiles_authored_source() -> None:
    repo_root = _REPO_ROOT / "workspaces" / "aware_home"
    interface_toml_path = repo_root / "modules" / "home" / "interfaces" / "aware_app" / "aware.interface.toml"

    result = compile_interface_workspace(
        toml_path=interface_toml_path,
        repo_root=repo_root,
        emit_compile_plan=True,
        state_model_catalog=_home_story_state_model_catalog(),
    )

    assert result.compile_plan is not None
    assert result.compile_plan_artifact is not None
    assert result.snapshot.source_files == (Path("home_story_app.aware"),)
    assert tuple(package.spec.pane.pane_name for package in result.snapshot.pane_packages) == (
        "door_control",
        "home_overview",
        "tv_status",
    )
    assert result.snapshot.pane_source_files == (
        Path("modules/home/panes/door_control/door_control.aware"),
        Path("modules/home/panes/home_overview/home_overview.aware"),
        Path("modules/home/panes/tv_status/tv_status.aware"),
    )
    assert result.dart_registrar_bundle_artifact is not None
    assert len(result.compile_plan.pane_ownership) == 3
    assert tuple(pane.name for pane in result.compile_plan.pane_ownership) == (
        "door_control",
        "home_overview",
        "tv_status",
    )
    assert len(result.compile_plan.interface_ownership) == 1
    interface = result.compile_plan.interface_ownership[0]
    assert interface.name == "aware_app"
    assert not hasattr(interface, "api_refs")
    assert len(interface.windows) == 1
    assert interface.windows[0].key == "main"
    assert tuple(layout.key for layout in interface.windows[0].layouts) == (
        "configuration_map",
        "scene_view",
    )
    assert tuple(pane.pane_name for pane in interface.panes) == (
        "home_overview",
        "door_control",
        "tv_status",
    )
    dart_payload = result.dart_registrar_bundle_artifact.path.read_text(encoding="utf-8")
    assert "No pane-package Dart registrars declared for this interface package." in dart_payload
    assert "package:aware_home_overview_pane/aware_home_overview_pane.dart" not in dart_payload
    assert "package:aware_door_control_pane/aware_door_control_pane.dart" not in dart_payload
    assert "package:aware_tv_status_pane/aware_tv_status_pane.dart" not in dart_payload
    assert ".registerPanePackage(registry);" not in dart_payload


def test_home_story_sample_interface_package_emits_config_bundle() -> None:
    repo_root = _REPO_ROOT / "workspaces" / "aware_home"
    interface_toml_path = repo_root / "modules" / "home" / "interfaces" / "aware_app" / "aware.interface.toml"

    result = compile_interface_workspace(
        toml_path=interface_toml_path,
        repo_root=repo_root,
        emit_config_bundle=True,
        state_model_catalog=_home_story_state_model_catalog(),
    )

    assert result.config_bundle_artifact is not None
    assert result.dart_registrar_bundle_artifact is not None
    assert result.config_bundle_artifact.path == interface_toml_path.parent / "bundles" / "interface.config.bundle.json"

    payload = json.loads(result.config_bundle_artifact.path.read_text(encoding="utf-8"))
    assert payload["name"] == "aware_app"
    assert "apis" not in payload
    assert tuple(window["key"] for window in payload["window_configs"]) == ("main",)
    assert tuple(layout["key"] for layout in payload["window_configs"][0]["layout_configs"]) == (
        "configuration_map",
        "scene_view",
    )
    assert tuple(section["key"] for section in payload["window_configs"][0]["layout_configs"][1]["sections"]) == (
        "scene",
        "overlay_left",
        "overlay_right",
        "inspector",
    )
    assert tuple(pane["name"] for pane in payload["pane_configs"]) == (
        "home_overview",
        "door_control",
        "tv_status",
    )
    assert tuple(pane["pane_package_name"] for pane in payload["pane_configs"]) == (
        "home-story-home-overview-pane",
        "home-story-door-control-pane",
        "home-story-tv-status-pane",
    )
    assert all(pane["pane_package_id"] for pane in payload["pane_configs"])
    assert payload["pane_configs"][0]["projection_experience_views"][0]["view_ref"] == "home_story.overview.home"
    assert payload["pane_configs"][0]["projection_experience_views"][0]["projection_view_key"] == "overview.home"
    assert payload["pane_configs"][1]["projection_experience_views"][0]["view_ref"] == "home_story.security.door"
    assert payload["pane_configs"][1]["projection_experience_views"][0]["projection_view_key"] == "security.door"
    assert payload["pane_configs"][2]["projection_experience_views"][0]["view_ref"] == "home_story.entertainment.tv"
    assert payload["pane_configs"][2]["projection_experience_views"][0]["projection_view_key"] == "entertainment.tv"
    pane_by_name = {pane["name"]: pane for pane in payload["pane_configs"]}
    assert "api_capability_endpoints" not in pane_by_name["door_control"]
    assert "sdk_operations" not in pane_by_name["door_control"]
    assert {
        action["target_ref"]
        for action in pane_by_name["door_control"]["projection_experience_views"][0]["invocation_actions"]
    } == {
        "home_devices.unlock_door.unlock_door",
        "home_devices.lock_door.lock_door",
        "home_devices.open_door.open_door",
        "home_devices.close_door.close_door",
    }


def test_home_story_sample_aware_workspace_interface_package_is_absent() -> None:
    repo_root = _REPO_ROOT
    interface_toml_path = (
        repo_root
        / "modules"
        / "experience"
        / "runtime"
        / "samples"
        / "e2e"
        / "home_story_workspace"
        / "interfaces"
        / "aware_workspace"
        / "aware.interface.toml"
    )

    assert not interface_toml_path.exists()


def test_root_aware_coordination_interface_package_rejects_multi_view_panes() -> None:
    repo_root = _REPO_ROOT
    interface_toml_path = (
        repo_root
        / "workspaces"
        / "aware_coordination"
        / "modules"
        / "coordination"
        / "interfaces"
        / "aware_coordination"
        / "aware.interface.toml"
    )

    with pytest.raises(ValueError, match="must declare exactly one view"):
        _ = compile_interface_workspace(
            toml_path=interface_toml_path,
            repo_root=repo_root,
            emit_compile_plan=True,
        )
