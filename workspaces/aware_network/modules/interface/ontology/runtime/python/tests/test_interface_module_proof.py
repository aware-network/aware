from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_interface.stable_ids import stable_window_id, stable_window_key_id
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_config_pane_config_id,
    stable_interface_config_pane_config_section_config_id,
    stable_interface_environment_id,
    stable_interface_id,
    stable_interface_window_id,
    stable_interface_window_navigation_context_id,
    stable_pane_config_id,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_interface_config_interface_pane_and_window_lanes_materialize_current_contract(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface import Interface
        from aware_interface_ontology.interface.interface_config import InterfaceConfig
        from aware_interface_ontology.interface.interface_enums import InterfaceOs
        from aware_interface_ontology.interface.pane_config import PaneConfig
        from aware_interface_ontology.window.window import Window

        ns = uuid5(NAMESPACE_URL, "aware://tests/interface/current-contract/v1")
        environment_id = uuid4()
        environment_navigation_context_id = uuid4()
        actor_id = uuid4()

        interface_config_name = "aware-control-plane"
        interface_config_id = stable_interface_config_id(
            name=interface_config_name,
        )
        interface_id = stable_interface_id(
            interface_config_id=interface_config_id,
            os="linux",
            version="0.0.0-test",
        )

        pane_config_name = "identity"
        pane_kind = "identity"
        projection_experience_view_id = uuid5(
            ns,
            "projection-experience-view:identity.default",
        )
        pane_config_id = stable_pane_config_id(
            projection_experience_view_id=projection_experience_view_id,
            name=pane_config_name,
        )
        interface_config_pane_config_id = stable_interface_config_pane_config_id(
            interface_config_id=interface_config_id,
            pane_config_id=pane_config_id,
        )
        layout_config_section_config_id = uuid5(
            ns,
            "layout-section:left.identity",
        )
        section_mount_id = stable_interface_config_pane_config_section_config_id(
            interface_config_pane_config_id=interface_config_pane_config_id,
            layout_config_section_config_id=layout_config_section_config_id,
        )

        window_key_id = stable_window_key_id(
            interface_id=interface_id,
            window_key="execution",
        )
        window_id = stable_window_id(window_id=window_key_id)
        interface_window_id = stable_interface_window_id(
            interface_id=interface_id,
            window_id=window_id,
        )
        interface_environment_id = stable_interface_environment_id(
            interface_id=interface_id,
            environment_id=environment_id,
        )
        interface_window_navigation_context_id = (
            stable_interface_window_navigation_context_id(
                interface_window_id=interface_window_id,
                interface_environment_id=interface_environment_id,
                environment_navigation_context_id=environment_navigation_context_id,
            )
        )

        pane_lane = runtime.bind(
            branch_id=pane_config_id,
            projection="PaneConfig",
            actor_id=actor_id,
        )
        with pane_lane.activate(commit=True, publish=False):
            pane_config = await PaneConfig.build(
                name=pane_config_name,
                projection_experience_view_id=projection_experience_view_id,
                pane_kind=pane_kind,
                view_ref="identity.default",
                description="Identity admission pane",
            )

        config_lane = runtime.bind(
            branch_id=interface_config_id,
            projection="InterfaceConfig",
            actor_id=actor_id,
        )
        with config_lane.activate(commit=True, publish=False):
            interface_config = await InterfaceConfig.build(
                name=interface_config_name,
                description="Interface control plane",
            )
            interface_config_pane_config = await interface_config.attach_pane_config(
                pane_config_id=pane_config_id,
                narrative_key="identity.story",
            )
            await interface_config_pane_config.add_section_mount(
                layout_config_section_config_id=layout_config_section_config_id,
            )

        window_lane = runtime.bind(
            branch_id=window_id,
            projection="Window",
            actor_id=actor_id,
        )
        with window_lane.activate(commit=True, publish=False):
            await Window.build(window_id=window_key_id)

        interface_lane = runtime.bind(
            branch_id=interface_id,
            projection="Interface",
            actor_id=actor_id,
        )
        with interface_lane.activate(commit=True, publish=False):
            interface = await Interface.build_via_interface_config(
                interface_config_id=interface_config_id,
                os=InterfaceOs.linux,
                version="0.0.0-test",
            )
            await interface.set_active_window_navigation_context(
                window_id=window_id,
                environment_id=environment_id,
                environment_navigation_context_id=environment_navigation_context_id,
            )

        committed_pane_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=pane_config_id,
            projection_name="PaneConfig",
            root_id=pane_config_id,
            root_type=PaneConfig,
        )
        committed_interface_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_config_id,
            projection_name="InterfaceConfig",
            root_id=interface_config_id,
            root_type=InterfaceConfig,
        )
        committed_window = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=window_id,
            projection_name="Window",
            root_id=window_id,
            root_type=Window,
        )
        committed_interface = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_id,
            projection_name="Interface",
            root_id=interface_id,
            root_type=Interface,
        )

        assert committed_pane_config.id == pane_config_id
        assert committed_pane_config.name == pane_config_name
        assert committed_pane_config.pane_kind == pane_kind
        assert (
            committed_pane_config.projection_experience_view_id
            == projection_experience_view_id
        )
        assert committed_pane_config.view_ref == "identity.default"

        assert committed_interface_config.id == interface_config_id
        assert committed_interface_config.name == interface_config_name
        assert tuple(item.id for item in committed_interface_config.interfaces) == ()
        assert tuple(
            item.id for item in committed_interface_config.interface_config_pane_configs
        ) == (interface_config_pane_config_id,)
        config_pane = committed_interface_config.interface_config_pane_configs[0]
        assert config_pane.pane_config_id == pane_config_id
        assert config_pane.narrative_key == "identity.story"
        assert tuple(item.id for item in config_pane.section_mounts) == (
            section_mount_id,
        )
        section_mount = config_pane.section_mounts[0]
        assert (
            section_mount.layout_config_section_config_id
            == layout_config_section_config_id
        )

        assert committed_window.id == window_id
        assert committed_window.window_id == window_key_id

        assert committed_interface.id == interface_id
        assert committed_interface.interface_config_id == interface_config_id
        assert committed_interface.os == InterfaceOs.linux
        assert committed_interface.version == "0.0.0-test"
        assert tuple(item.id for item in committed_interface.interface_windows) == (
            interface_window_id,
        )
        assert tuple(item.id for item in committed_interface.environments) == (
            interface_environment_id,
        )
        interface_window = committed_interface.interface_windows[0]
        assert interface_window.window_id == window_id
        assert (
            interface_window.active_navigation_context_id
            == interface_window_navigation_context_id
        )
        assert tuple(
            item.id for item in interface_window.window_navigation_contexts
        ) == (interface_window_navigation_context_id,)
        interface_window_navigation_context = (
            interface_window.window_navigation_contexts[0]
        )
        assert (
            interface_window_navigation_context.interface_environment_id
            == interface_environment_id
        )
        assert (
            interface_window_navigation_context.environment_navigation_context_id
            == environment_navigation_context_id
        )
