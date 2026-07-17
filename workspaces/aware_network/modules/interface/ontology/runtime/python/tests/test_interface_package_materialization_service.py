from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import msgpack  # pyright: ignore[reportMissingTypeStubs]
import pytest

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
)
from aware_code.semantic_currentness import (
    SemanticMaterializationCurrentnessReplayRequest,
    resolve_semantic_materialization_currentness_replay_adapter,
)
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from _meta_runtime_support import (
    build_interface_meta_runtime,
    isolated_meta_aware_root,
)
from _interface_runtime_test_paths import REPO_ROOT
import aware_interface.materialization.workspace_provider as interface_workspace_provider
from aware_interface.semantic_contract import (
    INTERFACE_MATERIALIZATION_CAPABILITY_METADATA,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_linux_flutter_platform_fixture(*, workspace_root: Path) -> None:
    dart_root = workspace_root / "apps" / "aware_app" / "dart" / "aware_app"
    linux_root = dart_root / "linux"
    _write(
        dart_root / "pubspec.yaml",
        "\n".join(
            [
                "name: aware_app",
                "publish_to: none",
                "environment:",
                '  sdk: "^3.8.0"',
                "",
            ]
        ),
    )
    _write(dart_root / "lib" / "main.dart", "void main() {}\n")
    _write(
        dart_root / ".metadata",
        "\n".join(
            [
                "version:",
                '  revision: "test"',
                "migration:",
                "  platforms:",
                "    - platform: linux",
                "",
            ]
        ),
    )
    _write(
        linux_root / "CMakeLists.txt",
        "\n".join(
            [
                "cmake_minimum_required(VERSION 3.13)",
                "project(runner LANGUAGES CXX)",
                'set(BINARY_NAME "aware_app")',
                'set(APPLICATION_ID "org.aware.home")',
                'add_subdirectory("runner")',
                "add_dependencies(${BINARY_NAME} flutter_assemble)",
                "include(flutter/generated_plugins.cmake)",
                "",
            ]
        ),
    )
    _write(linux_root / "flutter" / "CMakeLists.txt", "# Flutter tool build rules.\n")
    _write(linux_root / "flutter" / "generated_plugin_registrant.cc", "// generated\n")
    _write(linux_root / "flutter" / "generated_plugin_registrant.h", "// generated\n")
    _write(linux_root / "flutter" / "generated_plugins.cmake", "# generated\n")
    _write(
        linux_root / "runner" / "CMakeLists.txt",
        "\n".join(
            [
                "add_executable(${BINARY_NAME}",
                '  "main.cc"',
                ")",
                "apply_standard_settings(${BINARY_NAME})",
                "target_link_libraries(${BINARY_NAME} PRIVATE flutter)",
                "target_link_libraries(${BINARY_NAME} PRIVATE PkgConfig::GTK)",
                "",
            ]
        ),
    )
    _write(linux_root / "runner" / "main.cc", "int main() { return 0; }\n")
    _write(linux_root / "runner" / "my_application.cc", "// app\n")
    _write(linux_root / "runner" / "my_application.h", "// app\n")


def _build_home_projection_identity_ocg() -> ObjectConfigGraph:
    object_config_graph_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-package-materialization/object-config-graph/home",
    )
    object_projection_graph_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-package-materialization/object-projection-graph/home",
    )
    object_projection_graph_identity_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-package-materialization/object-projection-graph-identity/home",
    )
    state_model_class_config_id = UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c")
    object_projection_graph_node_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface-package-materialization/object-projection-graph-node/aware_home.home.Door",
    )
    return ObjectConfigGraph.model_validate(
        {
            "id": str(object_config_graph_id),
            "name": "Interface Package Materialization Test Graph",
            "hash": "sha256:test-interface-package-materialization-projection",
            "fqn_prefix": "aware_home",
            "language": "aware",
            "object_config_graph_identity_id": str(object_config_graph_id),
            "object_config_graph_identity": {
                "id": str(object_config_graph_id),
                "key": "aware_home",
                "label": "Aware Home Test Graph",
                "object_projection_graph_identities": [
                    {
                        "id": str(object_projection_graph_identity_id),
                        "projection_name": "home",
                        "label": "opg:home",
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
                    "name": "home",
                    "projection_hash": "sha256:test-interface-package-materialization-projection",
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


def _interface_source_code_package_id(*, package_name: str) -> UUID:
    return stable_code_package_id(
        code_package_config_id=stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind="aware_interface_toml",
                surface="representation",
            )
        ),
        package_name=package_name,
        language="aware",
    )


def test_interface_semantic_contract_registers_currentness_replay_adapter() -> None:
    adapter = resolve_semantic_materialization_currentness_replay_adapter(
        capability_metadata=INTERFACE_MATERIALIZATION_CAPABILITY_METADATA,
    )

    assert adapter is interface_workspace_provider.resolve_currentness_replay


@pytest.mark.asyncio
async def test_interface_workspace_provider_reports_full_rebuild_fallback_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    pane_branches = (uuid4(), uuid4())
    pane_oig_commit_ids = (uuid4(), uuid4())
    semantic_projection_ocg = _build_home_projection_identity_ocg()
    explicit_projection_ocg = ObjectConfigGraph(
        id=uuid4(),
        name="explicit-projection-context",
        description=None,
        hash="sha256:explicit-projection-context",
        fqn_prefix="aware_explicit_projection_context",
        language=CodeLanguage.aware,
    )
    captured_kwargs: dict[str, object] = {}

    async def _fake_materialize_interface_package_from_manifest(**kwargs: object):
        captured_kwargs.update(kwargs)
        config_bundle_path = tmp_path / "interface.config.bundle.json"
        pane_materialization_path = tmp_path / "pane_render_specs.materialization.json"
        _write(config_bundle_path, '{"interface":"control"}\n')
        _write(pane_materialization_path, '{"render_specs":[]}\n')
        return SimpleNamespace(
            interface_toml_path=tmp_path / "aware.interface.toml",
            config_bundle_path=config_bundle_path,
            interface_config=SimpleNamespace(name="control", id=uuid4()),
            interface_package=SimpleNamespace(name="control-interface", id=uuid4()),
            pane_render_spec_materialization_result=SimpleNamespace(
                materialization_path=pane_materialization_path,
                materialization_commit_id=uuid4(),
                last_commit_id=uuid4(),
                last_head_commit_id=uuid4(),
                object_instance_graph_commit_id=pane_oig_commit_ids[-1],
                branch_id=uuid4(),
                projection_hash="sha256:pane-render-spec",
                pane_render_specs=tuple(
                    SimpleNamespace(
                        branch_id=branch_id,
                        object_instance_graph_commit_id=oig_commit_id,
                    )
                    for branch_id, oig_commit_id in zip(
                        pane_branches,
                        pane_oig_commit_ids,
                        strict=True,
                    )
                ),
            ),
            source_code_package_id=source_code_package_id,
            source_object_instance_graph_commit_id=uuid4(),
            source_projection_hash="sha256:code-package",
            interface_config_commit_id=uuid4(),
            interface_config_object_instance_graph_commit_id=uuid4(),
            interface_config_projection_hash="sha256:interface-config",
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            package_object_instance_graph_commit_id=uuid4(),
            package_projection_hash="sha256:interface-package",
            phase_timings_s={"commit_interface_package_snapshot_s": 1.25},
        )

    monkeypatch.setattr(
        interface_workspace_provider,
        "materialize_interface_package_from_manifest",
        _fake_materialize_interface_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.interface.toml",
        code_package_delta=CodePackageDelta(
            package_name="control-interface",
            paths=[
                CodePackageDeltaPath(
                    relative_path="interface/control.aware",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("control",)},
        context={
            "projection_identity_ocg": explicit_projection_ocg,
            "semantic_object_config_graphs": (semantic_projection_ocg,),
        },
    )

    result = await interface_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("control",)
    assert result.applied_semantic_keys == ("control",)
    assert result.fallback_reason is not None
    assert "not implemented delta materialization" in result.fallback_reason
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert captured_kwargs["prefer_snapshot_materialization"] is True
    assert captured_kwargs["projection_identity_ocg"] is explicit_projection_ocg
    assert captured_kwargs["projection_identity_ocgs"] == (semantic_projection_ocg,)
    assert "state_model_catalog" in captured_kwargs
    assert "api_endpoint_catalog" not in captured_kwargs
    bundle = result.bundle_packages[0]
    assert bundle.semantic_head_commit_id == package_head_commit_id
    assert bundle.semantic_object_instance_graph_commit_id is not None
    assert bundle.semantic_projection_hash == "sha256:interface-package"
    semantic_outputs = bundle.provider_replay_evidence["semantic_outputs"]
    assert isinstance(semantic_outputs, tuple)
    assert {item["role"] for item in semantic_outputs} == {
        "source_code_package",
        "interface_config",
        "pane_render_spec",
    }
    pane_outputs = [
        item for item in semantic_outputs if item["role"] == "pane_render_spec"
    ]
    assert [item["branch_id"] for item in pane_outputs] == list(pane_branches)
    assert [item["object_instance_graph_commit_id"] for item in pane_outputs] == list(
        pane_oig_commit_ids
    )
    assert result.details["phase_timings_s"] == {
        "commit_interface_package_snapshot_s": 1.25
    }


@pytest.mark.asyncio
async def test_interface_workspace_provider_replays_current_heads_and_artifacts(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / ".aware" / "interface.config.bundle.json"
    _write(artifact_path, '{"interface":"control"}\n')
    artifact_witness = interface_workspace_provider._interface_artifact_witness(
        workspace_root=tmp_path,
        path=artifact_path,
    )
    package_branch_id = uuid4()
    package_oig_commit_id = uuid4()
    source_oig_commit_id = uuid4()
    config_oig_commit_id = uuid4()
    heads = {
        (package_branch_id, "sha256:interface-package"): package_oig_commit_id,
        (package_branch_id, "sha256:code-package"): source_oig_commit_id,
        (package_branch_id, "sha256:interface-config"): config_oig_commit_id,
    }

    async def _read_head(*, branch_id: UUID, projection_hash: str):
        commit_id = heads.get((branch_id, projection_hash))
        return (
            None
            if commit_id is None
            else {"object_instance_graph_commit_id": str(commit_id)}
        )

    bundle = SemanticPackageMaterializationBundle(
        package_key="aware-control-interface",
        manifest_toml_path=tmp_path / "aware.interface.toml",
        semantic_package_id=uuid4(),
        semantic_root_id=uuid4(),
        semantic_branch_id=package_branch_id,
        semantic_projection_hash="sha256:interface-package",
        semantic_object_instance_graph_commit_id=package_oig_commit_id,
        provider_replay_evidence={
            "semantic_outputs": (
                {
                    "role": "source_code_package",
                    "branch_id": package_branch_id,
                    "projection_hash": "sha256:code-package",
                    "object_instance_graph_commit_id": source_oig_commit_id,
                    "artifact_refs": (),
                },
                {
                    "role": "interface_config",
                    "branch_id": package_branch_id,
                    "projection_hash": "sha256:interface-config",
                    "object_instance_graph_commit_id": config_oig_commit_id,
                    "artifact_refs": (artifact_witness,),
                },
            )
        },
    )
    request = SemanticMaterializationCurrentnessReplayRequest(
        provider_key="aware_interface",
        semantic_owner="aware_interface.provider",
        workspace_root=tmp_path,
        workspace_manifest_kind="interface",
        semantic_package_family="interface",
        semantic_package_kind="interface_package",
        input_proof={"kind": "declared_source_tree", "complete": True},
        bundles=(bundle,),
        read_head=_read_head,
    )

    result = await interface_workspace_provider.resolve_currentness_replay(request)

    assert result.status == "reused"
    assert result.reason == "interface_output_heads_and_artifacts_current"
    assert result.replay_kind == "previous_interface_output_bundles"

    artifact_path.write_text("stale\n", encoding="utf-8")
    stale_result = await interface_workspace_provider.resolve_currentness_replay(
        request
    )
    assert stale_result.status == "must_execute"
    assert stale_result.reason == "interface_artifact_witness_mismatch"

    _write(artifact_path, '{"interface":"control"}\n')
    heads[(package_branch_id, "sha256:interface-config")] = uuid4()
    stale_head_result = await interface_workspace_provider.resolve_currentness_replay(
        request
    )
    assert stale_head_result.status == "must_execute"
    assert stale_head_result.reason == "interface_config_live_head_mismatch"


@pytest.mark.asyncio
async def test_interface_workspace_provider_materializes_render_component_package_evidence(
    tmp_path: Path,
) -> None:
    from aware_interface_ontology.stable_ids import stable_render_component_package_id

    manifest_path = (
        tmp_path
        / "interfaces"
        / "render_components"
        / "aware_meta_graph_render_components"
        / "aware.render_component.toml"
    )
    _write(
        manifest_path,
        "\n".join(
            [
                "aware_render_component = 1",
                "",
                "[render_component]",
                'package_name = "aware-meta-graph-render-components"',
                'fqn_prefix = "aware_meta_graph_render_components"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
                "",
                "[dart]",
                'package_path = "dart/aware_meta_graph_render_components"',
                'package_name = "aware_meta_graph_render_components"',
                "",
            ]
        )
        + "\n",
    )
    source_code_package_id = uuid4()
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        code_package_delta=CodePackageDelta(
            package_name="aware-meta-graph-render-components",
            paths=[
                CodePackageDeltaPath(
                    relative_path="aware.render_component.toml",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("aware.meta.graph",)},
        context={
            "workspace_manifest_kind": "render_component",
            "semantic_package_name": "aware-meta-graph-render-components",
            "source_code_package_id": str(source_code_package_id),
        },
    )

    result = await interface_workspace_provider.materialize(request)

    expected_package_id = stable_render_component_package_id(
        name="aware-meta-graph-render-components"
    )
    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("aware.meta.graph",)
    assert result.applied_semantic_keys == ("aware.meta.graph",)
    assert result.fallback_reason is not None
    assert "Render component package provider" in result.fallback_reason
    assert result.details["render_component_package_name"] == (
        "aware-meta-graph-render-components"
    )
    assert result.details["render_component_package_id"] == str(expected_package_id)
    assert len(result.bundle_packages) == 1
    bundle = result.bundle_packages[0]
    assert bundle.package_key == "aware-meta-graph-render-components"
    assert bundle.semantic_package_id == expected_package_id
    assert bundle.semantic_root_id == expected_package_id
    assert bundle.source_code_package_id == source_code_package_id


@pytest.mark.asyncio
async def test_interface_workspace_provider_rejects_unresolved_app_experience_dependencies(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "apps" / "aware_app" / "aware.app.toml"
    _write(
        manifest_path,
        "\n".join(
            [
                "aware_app = 1",
                "",
                "[app]",
                'package_name = "aware-home-app"',
                'app_name = "aware-home"',
                'fqn_prefix = "aware_home_app"',
                'kind = "app"',
                "",
                "[dart]",
                'package_path = "apps/aware_app/dart/aware_app"',
                'package_name = "aware_app"',
                'entrypoint = "lib/main.dart"',
                "",
                "[factory]",
                'package_path = "libs/app_factory/dart/aware_app_factory"',
                'package_name = "aware_app_factory"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["app.aware"]',
                "exclude_paths = []",
                "",
                "[[dependencies]]",
                'package_name = "aware-control"',
                'kind = "experience_package"',
                'role = "control"',
                "",
                "[[dependencies]]",
                'package_name = "home-story"',
                'kind = "experience_package"',
                'role = "home"',
                "",
                "[control]",
                "requires_actor = true",
                'default_screen = "control"',
                'admitted_screen = "home"',
                "",
                "[launch]",
                "seed_color_value = 4281121023",
                'generated_manifest_path = "lib/aware_app_launch_manifest.g.dart"',
                "",
                "[[platforms]]",
                'target = "linux"',
                'runner_path = "apps/aware_app/dart/aware_app/linux"',
                'materializer = "flutter_create"',
                'binary_name = "aware_app"',
                'application_id = "org.aware.home"',
                "enabled = true",
                "",
                "[[interfaces]]",
                'package_name = "aware-control-interface"',
                'role = "control"',
                'runtime_import = "package:aware_control_interface/aware_control_interface.dart"',
                'runtime_import_alias = "aware_control_interface"',
                'runtime_factory = "buildInterfacePackageRuntime"',
                "",
                "[[interfaces]]",
                'package_name = "home-story-aware-app-interface"',
                'role = "home"',
                'runtime_import = "package:aware_home_story_interface/_aware/interface/pane_package_registrars.dart"',
                'runtime_import_alias = "home_story_interface"',
                'runtime_factory = "buildInterfacePackageRuntime"',
            ]
        )
        + "\n",
    )
    _write(
        manifest_path.parent / "app.aware",
        "\n".join(
            [
                "app aware_home {",
                '    title "Aware Home"',
                '    description "Control-first Home app."',
                "",
                "    screen control {",
                "        projection aware_control_identity layout personal",
                "    }",
                "",
                "    screen home {",
                "        projection home_story layout configuration_map",
                "    }",
                "}",
                "",
            ]
        ),
    )
    _write_linux_flutter_platform_fixture(workspace_root=tmp_path)
    source_code_package_id = uuid4()
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        code_package_delta=CodePackageDelta(
            package_name="aware-home-app",
            paths=[
                CodePackageDeltaPath(
                    relative_path="aware.app.toml",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("aware.home.app",)},
        context={
            "workspace_manifest_kind": "app",
            "semantic_package_name": "aware-home-app",
            "source_code_package_id": str(source_code_package_id),
        },
    )

    with pytest.raises(
        RuntimeError,
        match="missing committed ExperiencePackage dependencies",
    ):
        await interface_workspace_provider.materialize(request)


@pytest.mark.asyncio
async def test_interface_workspace_provider_rejects_missing_linux_platform_runner(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "apps" / "aware_app" / "aware.app.toml"
    _write(
        manifest_path,
        "\n".join(
            [
                "aware_app = 1",
                "",
                "[app]",
                'package_name = "aware-home-app"',
                'app_name = "aware-home"',
                'fqn_prefix = "aware_home_app"',
                'kind = "app"',
                "",
                "[dart]",
                'package_path = "apps/aware_app/dart/aware_app"',
                'package_name = "aware_app"',
                'entrypoint = "lib/main.dart"',
                "",
                "[factory]",
                'package_path = "libs/app_factory/dart/aware_app_factory"',
                'package_name = "aware_app_factory"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["app.aware"]',
                "exclude_paths = []",
                "",
                "[[platforms]]",
                'target = "linux"',
                'runner_path = "apps/aware_app/dart/aware_app/linux"',
                'materializer = "flutter_create"',
                'binary_name = "aware_app"',
                'application_id = "org.aware.home"',
                "enabled = true",
            ]
        )
        + "\n",
    )
    _write(
        manifest_path.parent / "app.aware",
        "\n".join(
            [
                "app aware_home {",
                "    screen home {",
                "        projection home_story layout configuration_map",
                "    }",
                "}",
                "",
            ]
        ),
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        code_package_delta=CodePackageDelta(
            package_name="aware-home-app",
            paths=[
                CodePackageDeltaPath(
                    relative_path="aware.app.toml",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("aware.home.app",)},
        context={
            "workspace_manifest_kind": "app",
            "semantic_package_name": "aware-home-app",
        },
    )

    with pytest.raises(
        interface_workspace_provider.AwareAppPlatformMaterializationError,
        match="Linux platform runner is not materialization-ready",
    ):
        await interface_workspace_provider.materialize(request)


def _write_interface_package_fixture(
    *, workspace_root: Path, interface_config_id: str
) -> Path:
    from aware_interface_ontology.stable_ids import stable_interface_package_id

    interface_package_id = str(
        stable_interface_package_id(name="aware-control-plane-interface")
    )
    interface_toml_path = (
        workspace_root / "interfaces" / "control_plane" / "aware.interface.toml"
    )
    _write(
        interface_toml_path,
        "\n".join(
            [
                "aware_interface = 1",
                "",
                "[interface]",
                'package_name = "aware-control-plane-interface"',
                'fqn_prefix = "aware_control_plane_interface"',
                "version_number = 11",
                'title = "Aware Control Plane"',
                'description = "Control plane interface package"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'exclude_paths = ["**/*.draft.aware"]',
                "force_fresh_scan = false",
                'config_bundle_path = "bundles/interface.config.bundle.json"',
                "",
                "[dart]",
                'package_path = "dart/aware_control_plane_interface"',
                'package_name = "aware_control_plane_interface"',
                "",
            ]
        )
        + "\n",
    )
    (workspace_root / "interfaces" / "control_plane" / "bindings").mkdir(
        parents=True,
        exist_ok=True,
    )
    _write(
        workspace_root
        / "interfaces"
        / "control_plane"
        / "bundles"
        / "interface.config.bundle.json",
        "\n".join(
            [
                "{",
                f'  "interface_package_id": "{interface_package_id}",',
                '  "interface_package_name": "aware-control-plane-interface",',
                f'  "interface_config_id": "{interface_config_id}",',
                '  "name": "aware-control-plane",',
                '  "description": "Demo control plane",',
                '  "apis": [],',
                '  "window_configs": [],',
                '  "pane_configs": []',
                "}",
            ]
        )
        + "\n",
    )
    return interface_toml_path


def _write_authored_interface_package_fixture(*, workspace_root: Path) -> Path:
    interface_root = workspace_root / "interfaces" / "aware_app"
    interface_toml_path = interface_root / "aware.interface.toml"
    _write(
        interface_toml_path,
        "\n".join(
            [
                "aware_interface = 1",
                "",
                "[interface]",
                'package_name = "aware-authored-interface"',
                'fqn_prefix = "aware_authored_interface"',
                "version_number = 3",
                'title = "Aware Authored Interface"',
                'description = "Authored interface package"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                'exclude_paths = ["*.draft.aware"]',
                "force_fresh_scan = false",
                'config_bundle_path = "bundles/interface.config.bundle.json"',
                'compilation_mode = "interface_ontology"',
                "",
                "[dart]",
                'package_path = "dart/aware_authored_interface"',
                'package_name = "aware_authored_interface"',
            ]
        )
        + "\n",
    )
    _write(
        interface_root / "home_story_app.aware",
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                "        layout workspace {",
                "            section main",
                "        }",
                "    }",
                "",
                "    pane door_control {",
                "        mount main.workspace.main",
                "        narrative security.control",
                "    }",
                "}",
                "",
            ]
        ),
    )
    pane_root = workspace_root / "panes" / "door_control"
    _write(
        pane_root / "aware.pane.toml",
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
                'package_name = "home-story-experience"',
                "version_number = 4",
                'kind = "experience_package"',
            ]
        )
        + "\n",
    )
    _write(
        pane_root / "door_control.aware",
        "\n".join(
            [
                "pane door_control {",
                "    kind door",
                "",
                "    view home_story.security.door default {",
                '        """Door state and operator actions."""',
                "    }",
                "}",
                "",
            ]
        ),
    )
    _write(workspace_root / "aware.workspace.toml", "aware_workspace = 1\n")
    experience_root = workspace_root / "experiences" / "home_story"
    _write(
        experience_root / "aware.experience.toml",
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
    )
    _write(
        experience_root / "home_story.aware",
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
    )
    api_runtime_dir = workspace_root / ".aware" / "api" / "runtime" / "home-devices-api"
    api_runtime_dir.mkdir(parents=True, exist_ok=True)
    api_view_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/package-materialization/api-view-capability-endpoint/home-devices/security-door/unlock-door",
    )
    api_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/interface/package-materialization/api-capability-endpoint/home-devices/unlock-door",
    )
    _write(
        api_runtime_dir / "api.compile_plan.json",
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
                                "state_model_id": (
                                    "0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"
                                ),
                            }
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
    )
    _write(
        workspace_root
        / ".aware"
        / "environment"
        / "runtime"
        / "environment.manifest.json",
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
    )
    module_runtime_dir = (
        workspace_root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    _write(
        module_runtime_dir / "environment.manifest.json",
        json.dumps({"ocg": {"snapshot": "ocg.snapshot.msgpack"}}, indent=2) + "\n",
    )
    (module_runtime_dir / "ocg.snapshot.msgpack").write_bytes(
        bytes(
            cast(
                bytes,
                msgpack.packb(
                    {
                        "fqn_prefix": "aware_home",
                        "object_config_graph_identity": {
                            "object_projection_graph_identities": [
                                {
                                    "id": "3218f237-bec9-5a90-a14e-4f9fdfce4ac1",
                                    "projection_name": "home",
                                }
                            ]
                        },
                        "object_config_graph_nodes": [
                            {
                                "class_config": {
                                    "id": "0b8e17ec-b168-5a3b-9fc7-d60037cfb51c",
                                    "class_fqn": "aware_home.home.Door",
                                    "name": "Door",
                                }
                            }
                        ],
                        "object_projection_graphs": [
                            {
                                "object_projection_graph_nodes": [
                                    {
                                        "class_config": {
                                            "id": "0b8e17ec-b168-5a3b-9fc7-d60037cfb51c",
                                            "class_fqn": "aware_home.home.Door",
                                            "name": "Door",
                                        }
                                    }
                                ]
                            }
                        ],
                    },
                    use_bin_type=True,
                ),
            )
        )
    )
    return interface_toml_path


def _write_authored_interface_config_bundle(*, workspace_root: Path) -> Path:
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_package_id,
    )

    bundle_path = (
        workspace_root
        / "interfaces"
        / "aware_app"
        / "bundles"
        / "interface.config.bundle.json"
    )
    _write(
        bundle_path,
        json.dumps(
            {
                "interface_package_id": str(
                    stable_interface_package_id(name="aware-authored-interface")
                ),
                "interface_package_name": "aware-authored-interface",
                "interface_config_id": str(
                    stable_interface_config_id(name="aware_app")
                ),
                "name": "aware_app",
                "description": "Compiled authored interface",
                "apis": [],
                "window_configs": [],
                "pane_configs": [],
            },
            indent=2,
        )
        + "\n",
    )
    return bundle_path


def _write_authored_interface_with_pane_render_fixture(
    *,
    workspace_root: Path,
) -> Path:
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root,
    )
    interface_source_path = (
        workspace_root / "interfaces" / "aware_app" / "home_story_app.aware"
    )
    _write(
        interface_source_path,
        "\n".join(
            [
                "interface aware_app {",
                "    window main {",
                "        layout workspace {",
                "            section main",
                "        }",
                "    }",
                "",
                "    pane door_control {",
                "        mount main.workspace.main",
                "        narrative security.control",
                "    }",
                "}",
                "",
            ]
        ),
    )
    pane_root = workspace_root / "panes" / "door_control"
    _write(
        pane_root / "aware.pane.toml",
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
                'package_name = "home-story-experience"',
                'kind = "experience_package"',
                "",
            ]
        )
        + "\n",
    )
    _write(
        pane_root / "door_control.aware",
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
    )
    return interface_toml_path


def test_resolve_interface_package_materialization_spec_reuses_fresh_interface_ontology_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_interface.materialization.service as materialization_service

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root,
    )
    bundle_path = _write_authored_interface_config_bundle(
        workspace_root=workspace_root,
    )
    source_path = workspace_root / "interfaces" / "aware_app" / "home_story_app.aware"
    os.utime(source_path, (1_000, 1_000))
    os.utime(bundle_path, (2_000, 2_000))

    def _unexpected_compile_interface_workspace(**kwargs: object) -> object:
        raise AssertionError(f"unexpected interface compile: {kwargs!r}")

    monkeypatch.setattr(
        materialization_service,
        "compile_interface_workspace",
        _unexpected_compile_interface_workspace,
    )

    spec = materialization_service.resolve_interface_package_materialization_spec(
        interface_toml_path=interface_toml_path,
        workspace_root=workspace_root,
    )

    assert spec.config_bundle_path == bundle_path.resolve()
    assert spec.config_bundle.name == "aware_app"


def test_interface_package_source_snapshot_includes_authored_manifest(
    tmp_path: Path,
) -> None:
    import aware_interface.materialization.service as materialization_service

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root,
    )
    _write_authored_interface_config_bundle(workspace_root=workspace_root)
    spec = materialization_service.resolve_interface_package_materialization_spec(
        interface_toml_path=interface_toml_path,
        workspace_root=workspace_root,
    )

    source_texts = materialization_service._interface_package_source_texts(spec=spec)

    assert set(source_texts) == {"aware.interface.toml", "home_story_app.aware"}


def test_interface_materialization_resolves_source_catalog_from_aware_repo(
    tmp_path: Path,
) -> None:
    import aware_interface.materialization.service as materialization_service

    repo_root = tmp_path / "repo"
    workspace_root = repo_root / "workspaces" / "aware_agent"
    workspace_root.mkdir(parents=True)
    _ = (repo_root / "aware.repo.toml").write_text("aware = 1\n", encoding="utf-8")

    assert (
        materialization_service._resolve_interface_source_repo_root(
            workspace_root=workspace_root,
        )
        == repo_root.resolve()
    )
    standalone_root = tmp_path / "standalone"
    standalone_root.mkdir()
    assert (
        materialization_service._resolve_interface_source_repo_root(
            workspace_root=standalone_root,
        )
        == standalone_root.resolve()
    )


def test_resolve_interface_package_materialization_spec_compiles_when_authored_source_is_newer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_interface.materialization.service as materialization_service

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root,
    )
    bundle_path = _write_authored_interface_config_bundle(
        workspace_root=workspace_root,
    )
    source_path = workspace_root / "interfaces" / "aware_app" / "home_story_app.aware"
    os.utime(bundle_path, (1_000, 1_000))
    os.utime(source_path, (2_000, 2_000))
    compile_calls: list[dict[str, object]] = []

    def _fake_compile_interface_workspace(**kwargs: object) -> object:
        compile_calls.append(dict(kwargs))
        snapshot = materialization_service.InterfaceWorkspace.from_toml(
            toml_path=interface_toml_path,
            repo_root=workspace_root,
        ).build_snapshot()
        return SimpleNamespace(
            snapshot=snapshot,
            render_spec_materialization_artifact=None,
        )

    monkeypatch.setattr(
        materialization_service,
        "compile_interface_workspace",
        _fake_compile_interface_workspace,
    )

    spec = materialization_service.resolve_interface_package_materialization_spec(
        interface_toml_path=interface_toml_path,
        workspace_root=workspace_root,
    )

    assert spec.config_bundle_path == bundle_path.resolve()
    assert len(compile_calls) == 1
    assert compile_calls[0]["emit_config_bundle"] is True


def test_resolve_interface_package_materialization_spec_honors_force_fresh_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_interface.materialization.service as materialization_service

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root,
    )
    interface_toml_path.write_text(
        interface_toml_path.read_text(encoding="utf-8").replace(
            "force_fresh_scan = false",
            "force_fresh_scan = true",
        ),
        encoding="utf-8",
    )
    bundle_path = _write_authored_interface_config_bundle(
        workspace_root=workspace_root,
    )
    source_path = workspace_root / "interfaces" / "aware_app" / "home_story_app.aware"
    os.utime(source_path, (1_000, 1_000))
    os.utime(bundle_path, (2_000, 2_000))
    compile_calls: list[dict[str, object]] = []

    def _fake_compile_interface_workspace(**kwargs: object) -> object:
        compile_calls.append(dict(kwargs))
        snapshot = materialization_service.InterfaceWorkspace.from_toml(
            toml_path=interface_toml_path,
            repo_root=workspace_root,
        ).build_snapshot()
        return SimpleNamespace(
            snapshot=snapshot,
            render_spec_materialization_artifact=None,
        )

    monkeypatch.setattr(
        materialization_service,
        "compile_interface_workspace",
        _fake_compile_interface_workspace,
    )

    _ = materialization_service.resolve_interface_package_materialization_spec(
        interface_toml_path=interface_toml_path,
        workspace_root=workspace_root,
    )

    assert len(compile_calls) == 1
    assert compile_calls[0]["artifact_root"] == workspace_root.resolve()


def test_interface_workspace_ignores_undeclared_and_revision_history_manifests(
    tmp_path: Path,
) -> None:
    from aware_interface.workspace import InterfaceWorkspace

    repo_root = tmp_path / "repo"
    workspace_root = repo_root / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root
    )

    # Competing repo-level manifests should not win over authored workspace-local ones.
    _write(
        repo_root / "experiences" / "repo_home_story" / "aware.experience.toml",
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "home-story-experience"',
                'fqn_prefix = "repo_home_story_experience"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["*.aware"]',
                "exclude_paths = []",
            ]
        )
        + "\n",
    )
    _write(
        repo_root / "experiences" / "repo_home_story" / "repo_home_story.aware",
        "\n".join(
            [
                "experience repo_home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default state aware_home.home.Door {",
                '            """Repo-level fallback view."""',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    revision_experience_root = (
        repo_root
        / ".aware"
        / "workspace"
        / "revision-filesystem-roots"
        / "old-revision"
        / "deployment-1"
        / "experiences"
        / "home_story"
    )
    authored_experience_root = workspace_root / "experiences" / "home_story"
    _write(
        revision_experience_root / "aware.experience.toml",
        (authored_experience_root / "aware.experience.toml").read_text(
            encoding="utf-8"
        ),
    )
    _write(
        revision_experience_root / "home_story.aware",
        (authored_experience_root / "home_story.aware").read_text(encoding="utf-8"),
    )

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=repo_root,
    ).build_snapshot()

    assert snapshot.experience_packages == ()
    assert len(snapshot.pane_packages) == 1
    assert len(snapshot.pane_packages[0].experience_packages) == 1
    assert (
        snapshot.pane_packages[0].experience_packages[0].package_root
        == (workspace_root / "experiences" / "home_story").resolve()
    )


@pytest.mark.asyncio
async def test_materialize_interface_package_from_manifest_creates_package_and_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "ontology"
            / "runtime"
            / "python"
        )
    )

    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.materialization import (
        materialize_interface_package_from_manifest,
    )
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_package_id,
    )

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_interface_package_fixture(
        workspace_root=workspace_root,
        interface_config_id=str(stable_interface_config_id(name="aware-control-plane")),
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        branch_id = uuid4()

        result = await materialize_interface_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
        )

        expected_interface_config_id = stable_interface_config_id(
            name="aware-control-plane"
        )
        expected_interface_package_id = stable_interface_package_id(
            name="aware-control-plane-interface"
        )
        expected_source_code_package_id = _interface_source_code_package_id(
            package_name="aware-control-plane-interface",
        )

        assert result.interface_toml_path == interface_toml_path.resolve()
        assert result.workspace_root == workspace_root.resolve()
        assert (
            result.config_bundle_path
            == (
                workspace_root
                / "interfaces"
                / "control_plane"
                / "bundles"
                / "interface.config.bundle.json"
            ).resolve()
        )
        assert result.interface_config.id == expected_interface_config_id
        assert result.interface_config.name == "aware-control-plane"
        assert result.interface_package.id == expected_interface_package_id
        assert result.interface_package.name == "aware-control-plane-interface"
        assert (
            result.interface_package.interface_config_id == expected_interface_config_id
        )
        assert result.source_code_package_id == expected_source_code_package_id
        assert (
            result.interface_package.source_code_package_id
            == expected_source_code_package_id
        )
        assert result.interface_package.fqn_prefix == "aware_control_plane_interface"
        assert result.interface_package.version_number == 11
        assert result.interface_package.title == "Aware Control Plane"
        assert result.interface_package.description == "Control plane interface package"
        assert result.interface_package.aware_interface_version == 1
        assert (
            result.interface_package.manifest_relative_path
            == "interfaces/control_plane/aware.interface.toml"
        )
        assert result.interface_package.package_root == "interfaces/control_plane"
        assert (
            result.interface_package.sources_root == "interfaces/control_plane/bindings"
        )
        assert result.interface_package.config_bundle_path == (
            "interfaces/control_plane/bundles/interface.config.bundle.json"
        )
        assert list(result.interface_package.include_paths) == ["**/*.aware"]
        assert list(result.interface_package.exclude_paths) == ["**/*.draft.aware"]
        assert result.interface_package.force_fresh_scan is False
        assert result.interface_package.compilation_mode == "raw_xor"
        assert list(result.interface_package.dependencies) == []
        assert dict(result.interface_package.dart) == {
            "package_path": "dart/aware_control_plane_interface",
            "package_name": "aware_control_plane_interface",
        }
        assert result.interface_config_commit_id is not None
        assert result.interface_config_head_commit_id is not None
        assert result.interface_config_object_instance_graph_commit_id is not None
        assert (
            result.interface_package.interface_config_object_instance_graph_commit_id
            == result.interface_config_object_instance_graph_commit_id
        )
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None

        interface_toml_path.write_text(
            interface_toml_path.read_text(encoding="utf-8")
            .replace("version_number = 11", "version_number = 12")
            .replace(
                'title = "Aware Control Plane"', 'title = "Aware Control Plane Updated"'
            ),
            encoding="utf-8",
        )
        rerun = await materialize_interface_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
        )
        assert rerun.interface_package.id == expected_interface_package_id
        assert rerun.source_code_package_id == expected_source_code_package_id
        assert rerun.interface_package.version_number == 12
        assert rerun.interface_package.title == "Aware Control Plane Updated"
        assert (
            rerun.interface_package.sources_root == "interfaces/control_plane/bindings"
        )
        assert dict(rerun.interface_package.dart) == {
            "package_path": "dart/aware_control_plane_interface",
            "package_name": "aware_control_plane_interface",
        }
        assert rerun.interface_config_head_commit_id is not None
        assert rerun.interface_config_object_instance_graph_commit_id is not None
        assert (
            rerun.interface_package.interface_config_object_instance_graph_commit_id
            == rerun.interface_config_object_instance_graph_commit_id
        )


@pytest.mark.asyncio
async def test_materialize_interface_package_from_authored_pane_render_commits_render_oig(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "ontology"
            / "runtime"
            / "python"
        )
    )

    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.materialization import (
        materialize_interface_package_from_manifest,
    )
    from aware_interface.ontology.materialization import (
        load_pane_render_spec_runtime_payloads_from_oig_head,
    )

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_with_pane_render_fixture(
        workspace_root=workspace_root
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        result = await materialize_interface_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
            projection_identity_ocg=_build_home_projection_identity_ocg(),
            state_model_catalog={
                "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
            },
        )

        render_result = result.pane_render_spec_materialization_result
        assert render_result is not None
        assert render_result.last_commit_id is not None
        assert render_result.last_head_commit_id is not None
        assert render_result.object_instance_graph_commit_id is not None
        assert len(render_result.pane_render_specs) == 1
        assert len(render_result.runtime_payloads) == 1

        materialized = render_result.pane_render_specs[0]
        pane_render_spec = materialized.pane_render_spec
        assert materialized.source_kind == "authored_aware"
        assert pane_render_spec.name == "door_control_default"
        assert pane_render_spec.view_ref == "home_story.security.door"
        assert pane_render_spec.projection_view_key == "security.door"
        assert pane_render_spec.root_node_key == "root"
        assert sorted(node.node_key for node in pane_render_spec.nodes) == [
            "root",
            "title",
            "unlock",
        ]

        materialized_payload = render_result.runtime_payloads[0]
        assert materialized_payload.source_kind == "materialized_oig"
        assert materialized_payload.payload["pane_name"] == "door_control"
        assert materialized_payload.payload["pane_kind"] == "door"
        assert materialized_payload.payload["view_ref"] == "home_story.security.door"

        committed_payloads = await load_pane_render_spec_runtime_payloads_from_oig_head(
            index=index,
            branch_id=render_result.branch_id,
            pane_render_spec_ids=(pane_render_spec.id,),
            pane_kind_by_pane_config_id={
                pane_render_spec.pane_config_id: "door",
            },
            pane_name_by_pane_config_id={
                pane_render_spec.pane_config_id: ("door_control"),
            },
        )
        assert len(committed_payloads) == 1
        committed_payload = committed_payloads[0]
        assert committed_payload.source_kind == "committed_oig"
        assert committed_payload.payload["spec_id"] == str(pane_render_spec.id)
        assert committed_payload.payload["pane_name"] == "door_control"
        nodes = committed_payload.payload["nodes"]
        assert isinstance(nodes, list)
        unlock = next(node for node in nodes if node["node_key"] == "unlock")
        assert unlock["label"] == "Unlock"
        actions = unlock["action_bindings"]
        assert isinstance(actions, list)
        assert actions[0]["action_kind"] == "view_action"
        assert actions[0]["view_action_key"] == "unlock_door"


@pytest.mark.asyncio
async def test_materialize_interface_package_snapshot_path_without_runtime_bind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "ontology"
            / "runtime"
            / "python"
        )
    )

    import aware_code_ontology  # noqa: F401
    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.materialization import (
        materialize_interface_package_from_manifest,
    )
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_package_id,
    )

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_interface_package_fixture(
        workspace_root=workspace_root,
        interface_config_id=str(stable_interface_config_id(name="aware-control-plane")),
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        branch_id = uuid4()

        result = await materialize_interface_package_from_manifest(
            runtime=object(),
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=branch_id,
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
            prefer_snapshot_materialization=True,
        )

        assert result.interface_config.id == stable_interface_config_id(
            name="aware-control-plane"
        )
        assert result.interface_package.id == stable_interface_package_id(
            name="aware-control-plane-interface"
        )
        assert result.source_code_package_id == _interface_source_code_package_id(
            package_name="aware-control-plane-interface",
        )
        assert result.interface_config_commit_id is not None
        assert result.interface_config_object_instance_graph_commit_id is not None
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None
        assert (
            result.interface_package.interface_config_object_instance_graph_commit_id
            == result.interface_config_object_instance_graph_commit_id
        )


@pytest.mark.asyncio
async def test_materialize_interface_package_snapshot_path_commits_authored_pane_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "ontology"
            / "runtime"
            / "python"
        )
    )

    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.materialization import (
        materialize_interface_package_from_manifest,
    )
    from aware_interface.ontology.materialization import (
        load_pane_render_spec_runtime_payloads_from_oig_head,
    )

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_with_pane_render_fixture(
        workspace_root=workspace_root,
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        branch_id = uuid4()

        result = await materialize_interface_package_from_manifest(
            runtime=object(),
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=branch_id,
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
            projection_identity_ocg=_build_home_projection_identity_ocg(),
            state_model_catalog={
                "aware_home.home.Door": UUID("0b8e17ec-b168-5a3b-9fc7-d60037cfb51c"),
            },
            prefer_snapshot_materialization=True,
        )

        render_result = result.pane_render_spec_materialization_result
        assert render_result is not None
        assert render_result.last_commit_id is not None
        assert render_result.last_head_commit_id is not None
        assert render_result.object_instance_graph_commit_id is not None
        assert len(render_result.pane_render_specs) == 1
        pane_render_spec = render_result.pane_render_specs[0].pane_render_spec
        assert pane_render_spec.name == "door_control_default"

        committed_payloads = await load_pane_render_spec_runtime_payloads_from_oig_head(
            index=index,
            branch_id=render_result.branch_id,
            pane_render_spec_ids=(pane_render_spec.id,),
            pane_kind_by_pane_config_id={
                pane_render_spec.pane_config_id: "door",
            },
            pane_name_by_pane_config_id={
                pane_render_spec.pane_config_id: "door_control",
            },
        )
        assert len(committed_payloads) == 1
        committed_payload = committed_payloads[0]
        assert committed_payload.source_kind == "committed_oig"
        assert committed_payload.payload["name"] == "door_control_default"
        assert committed_payload.payload["pane_name"] == "door_control"
        assert committed_payload.payload["view_ref"] == "home_story.security.door"


@pytest.mark.asyncio
async def test_materialize_interface_package_from_authored_source_compiles_bundle_with_pane_experience_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "ontology"
            / "runtime"
            / "python"
        )
    )

    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.materialization import (
        materialize_interface_package_from_manifest,
    )
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_package_id,
    )

    workspace_root = tmp_path / "workspace"
    interface_toml_path = _write_authored_interface_package_fixture(
        workspace_root=workspace_root
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        result = await materialize_interface_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            interface_toml_path=interface_toml_path,
            projection_identity_ocg=_build_home_projection_identity_ocg(),
        )

        expected_interface_config_id = stable_interface_config_id(name="aware_app")
        expected_interface_package_id = stable_interface_package_id(
            name="aware-authored-interface"
        )
        expected_source_code_package_id = _interface_source_code_package_id(
            package_name="aware-authored-interface",
        )
        assert result.config_bundle_path.exists()
        assert result.interface_config.id == expected_interface_config_id
        assert result.interface_package.id == expected_interface_package_id
        assert (
            result.interface_package.interface_config_id == expected_interface_config_id
        )
        assert result.source_code_package_id == expected_source_code_package_id
        assert (
            result.interface_package.source_code_package_id
            == expected_source_code_package_id
        )
        assert result.interface_package.fqn_prefix == "aware_authored_interface"
        assert result.interface_package.version_number == 3
        assert result.interface_package.title == "Aware Authored Interface"
        assert result.interface_package.description == "Authored interface package"
        assert result.interface_package.aware_interface_version == 1
        assert (
            result.interface_package.manifest_relative_path
            == "interfaces/aware_app/aware.interface.toml"
        )
        assert result.interface_package.package_root == "interfaces/aware_app"
        assert result.interface_package.sources_root == "interfaces/aware_app"
        assert (
            result.interface_package.config_bundle_path
            == "interfaces/aware_app/bundles/interface.config.bundle.json"
        )
        assert list(result.interface_package.include_paths) == ["*.aware"]
        assert list(result.interface_package.exclude_paths) == ["*.draft.aware"]
        assert result.interface_package.force_fresh_scan is False
        assert result.interface_package.compilation_mode == "interface_ontology"
        assert list(result.interface_package.dependencies) == []
        assert dict(result.interface_package.dart) == {
            "package_path": "dart/aware_authored_interface",
            "package_name": "aware_authored_interface",
        }
        assert len(result.interface_config_window_configs) == 1
        assert result.interface_package_experience_packages == ()
        assert result.config_bundle.apis == []
        assert result.config_bundle.window_configs[0].key == "main"
        assert result.config_bundle.pane_configs[0].name == "door_control"
        assert (
            result.config_bundle.pane_configs[0].projection_experience_views[0].view_ref
            == "home_story.security.door"
        )
        assert result.interface_config_commit_id is not None
        assert result.interface_config_head_commit_id is not None
        assert result.interface_config_object_instance_graph_commit_id is not None
        assert (
            result.interface_package.interface_config_object_instance_graph_commit_id
            == result.interface_config_object_instance_graph_commit_id
        )
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None
