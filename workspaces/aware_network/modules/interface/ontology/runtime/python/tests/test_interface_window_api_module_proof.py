from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_attention_ontology.stable_ids import stable_layout_config_id
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_config_window_config_id,
    stable_interface_package_id,
    stable_interface_package_pane_package_id,
    stable_pane_config_id,
    stable_pane_package_id,
    stable_window_config_id,
    stable_window_config_layout_config_id,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_interface_config_window_chain(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_config import InterfaceConfig
        from aware_interface_ontology.interface.window_config import WindowConfig

        ids = _runtime_ids()
        interface_config_name = "aware-app"
        layout_key = "scene_view"
        window_key = "main"

        interface_config_id = stable_interface_config_id(name=interface_config_name)
        layout_config_id = stable_layout_config_id(key=layout_key)
        window_config_id = stable_window_config_id(key=window_key)
        interface_config_window_config_id = stable_interface_config_window_config_id(
            interface_config_id=interface_config_id,
            window_config_id=window_config_id,
        )
        window_config_layout_config_id = stable_window_config_layout_config_id(
            window_config_id=window_config_id,
            layout_config_id=layout_config_id,
        )

        window_lane = runtime.bind(
            branch_id=window_config_id,
            projection="WindowConfig",
            actor_id=ids["actor_id"],
        )
        with window_lane.activate(commit=True, publish=False):
            window_config = await WindowConfig.build(
                key=window_key,
                description="Main interface window",
            )
            await window_config.attach_layout_config(
                layout_config_id=layout_config_id,
                description="Territory layout",
            )

        config_lane = runtime.bind(
            branch_id=interface_config_id,
            projection="InterfaceConfig",
            actor_id=ids["actor_id"],
        )
        with config_lane.activate(commit=True, publish=False):
            interface_config = await InterfaceConfig.build(
                name=interface_config_name,
                description="Aware app interface",
            )
            await interface_config.attach_window_config(
                window_config_id=window_config_id,
            )

        committed_window_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=window_config_id,
            projection_name="WindowConfig",
            root_id=window_config_id,
            root_type=WindowConfig,
        )
        committed_interface_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_config_id,
            projection_name="InterfaceConfig",
            root_id=interface_config_id,
            root_type=InterfaceConfig,
        )

        assert committed_window_config.id == window_config_id
        assert committed_window_config.key == window_key
        assert tuple(item.id for item in committed_window_config.layout_configs) == (window_config_layout_config_id,)
        window_layout = committed_window_config.layout_configs[0]
        assert window_layout.window_config_id == window_config_id
        assert window_layout.layout_config_id == layout_config_id
        assert window_layout.description == "Territory layout"

        assert committed_interface_config.id == interface_config_id
        assert committed_interface_config.name == interface_config_name
        assert tuple(item.id for item in committed_interface_config.interface_config_window_configs) == (
            interface_config_window_config_id,
        )
        interface_window = committed_interface_config.interface_config_window_configs[0]
        assert interface_window.interface_config_id == interface_config_id
        assert interface_window.window_config_id == window_config_id


@pytest.mark.asyncio
async def test_interface_package_attaches_pane_package(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_package import InterfacePackage
        from aware_interface_ontology.interface.pane_config import PaneConfig
        from aware_interface_ontology.interface.pane_package import PanePackage

        ids = _runtime_ids()
        interface_name = "aware-app"
        pane_name = "door_control"
        interface_config_id = stable_interface_config_id(name=interface_name)
        interface_package_id = stable_interface_package_id(name=interface_name)
        projection_experience_view_id = uuid4()
        pane_config_id = stable_pane_config_id(
            projection_experience_view_id=projection_experience_view_id,
            name=pane_name,
        )
        pane_package_id = stable_pane_package_id(name=pane_name)
        interface_package_pane_package_id = stable_interface_package_pane_package_id(
            interface_package_id=interface_package_id,
            pane_package_id=pane_package_id,
        )

        pane_config_lane = runtime.bind(
            branch_id=pane_config_id,
            projection="PaneConfig",
            actor_id=ids["actor_id"],
        )
        with pane_config_lane.activate(commit=True, publish=False):
            await PaneConfig.build(
                name=pane_name,
                projection_experience_view_id=projection_experience_view_id,
                pane_kind="door",
                view_ref="door.default",
                description="Door pane",
            )

        pane_package_lane = runtime.bind(
            branch_id=pane_package_id,
            projection="PanePackage",
            actor_id=ids["actor_id"],
        )
        with pane_package_lane.activate(commit=True, publish=False):
            await PanePackage.build(
                name=pane_name,
                pane_config_id=pane_config_id,
            )

        interface_package_lane = runtime.bind(
            branch_id=interface_package_id,
            projection="InterfacePackage",
            actor_id=ids["actor_id"],
        )
        with interface_package_lane.activate(commit=True, publish=False):
            interface_package = await InterfacePackage.build(
                name=interface_name,
                interface_config_id=interface_config_id,
            )
            await interface_package.attach_pane_package(
                pane_package_id=pane_package_id,
                description="Authored pane import",
            )

        committed_pane_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=pane_config_id,
            projection_name="PaneConfig",
            root_id=pane_config_id,
            root_type=PaneConfig,
        )
        committed_pane_package = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=pane_package_id,
            projection_name="PanePackage",
            root_id=pane_package_id,
            root_type=PanePackage,
        )
        committed_interface_package = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_package_id,
            projection_name="InterfacePackage",
            root_id=interface_package_id,
            root_type=InterfacePackage,
        )

        assert committed_pane_config.id == pane_config_id
        assert committed_pane_config.name == pane_name
        assert committed_pane_config.pane_kind == "door"
        assert committed_pane_package.id == pane_package_id
        assert committed_pane_package.pane_config_id == pane_config_id
        assert tuple(item.id for item in committed_interface_package.pane_packages) == (
            interface_package_pane_package_id,
        )
        pane_binding = committed_interface_package.pane_packages[0]
        assert pane_binding.interface_package_id == interface_package_id
        assert pane_binding.pane_package_id == pane_package_id
        assert pane_binding.description == "Authored pane import"


def _runtime_ids() -> dict[str, UUID]:
    return {
        "environment_id": uuid4(),
        "process_id": uuid4(),
        "thread_id": uuid4(),
        "actor_id": uuid4(),
    }
