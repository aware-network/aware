from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_attention_ontology.stable_ids import (
    stable_layout_id,
    stable_layout_section_id,
    stable_section_focus_scope_id,
    stable_section_id,
)
from aware_identity_ontology.stable_ids import (
    stable_actor_focus_scope_id,
    stable_actor_id,
    stable_identity_id,
)
from aware_interface.stable_ids import stable_window_id, stable_window_key_id
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_id,
    stable_interface_window_id,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_window_focus_scope_chain_proof(tmp_path: Path) -> None:
    """
    Cross-module proof (interface + attention + identity):

    - FocusScope is a commit-backed attention resource.
    - Window resolves active layout via Window.active_layout_id.
    - Interface attaches to Window via InterfaceWindow.
    - Actor joins FocusScope via ActorFocusScope.

    The test uses the Meta runtime facade only. It does not rely on the legacy
    legacy harness/assertion path.
    """

    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_attention_ontology.focus.focus_scope import FocusScope
        from aware_identity_ontology.actor.actor import Actor
        from aware_identity_ontology.identity.identity import Identity
        from aware_interface_ontology.interface.interface import Interface
        from aware_interface_ontology.interface.interface_config import InterfaceConfig
        from aware_interface_ontology.interface.interface_enums import InterfaceOs
        from aware_interface_ontology.window.window import Window

        ids = _runtime_ids()
        ns = uuid5(NAMESPACE_URL, "aware://tests/window-focus-scope/meta/v1")

        interface_config_name = "window-focus-scope"
        interface_config_id = stable_interface_config_id(name=interface_config_name)
        interface_id = stable_interface_id(
            interface_config_id=interface_config_id,
            os="linux",
            version="0.0.0-test",
        )

        window_key = "execution"
        window_key_id = stable_window_key_id(
            interface_id=interface_id,
            window_key=window_key,
        )
        window_id = stable_window_id(window_id=window_key_id)
        interface_window_id = stable_interface_window_id(
            interface_id=interface_id,
            window_id=window_id,
        )

        layout_id = stable_layout_id(key="execution")
        section_id = stable_section_id(key="workspace")
        focus_scope_seed_id = stable_layout_section_id(
            layout_id=layout_id,
            section_id=section_id,
        )
        focus_scope_id = stable_section_focus_scope_id(
            section_id=section_id,
            focus_scope_id=focus_scope_seed_id,
        )

        public_key = "ed25519:" + ("11" * 32)
        expected_identity_id = stable_identity_id(public_key=public_key, type="human")
        expected_actor_id = stable_actor_id(
            identity_id=expected_identity_id,
            key="default",
        )
        identity_branch_id = uuid5(ns, "identity-branch")
        expected_actor_focus_scope_id = stable_actor_focus_scope_id(
            actor_id=expected_actor_id,
            focus_scope_id=focus_scope_id,
        )

        focus_lane = runtime.bind(
            branch_id=focus_scope_id,
            projection="FocusScope",
            actor_id=ids["actor_id"],
        )
        with focus_lane.activate(commit=True, publish=False):
            await FocusScope.build(
                title="Execution",
                description="Personal execution scope",
                expires_at=None,
                is_active=True,
                last_accessed=None,
            )

        window_lane = runtime.bind(
            branch_id=window_id,
            projection="Window",
            actor_id=ids["actor_id"],
        )
        with window_lane.activate(commit=True, publish=False):
            window = await Window.build(window_id=window_key_id)
            await window.set_active_layout(layout_id=layout_id)

        config_lane = runtime.bind(
            branch_id=interface_config_id,
            projection="InterfaceConfig",
            actor_id=ids["actor_id"],
        )
        with config_lane.activate(commit=True, publish=False):
            await InterfaceConfig.build(
                name=interface_config_name,
                description="Window focus scope proof interface",
            )

        interface_lane = runtime.bind(
            branch_id=interface_id,
            projection="Interface",
            actor_id=ids["actor_id"],
        )
        with interface_lane.activate(commit=True, publish=False):
            interface = await Interface.build_via_interface_config(
                interface_config_id=interface_config_id,
                os=InterfaceOs.linux,
                version="0.0.0-test",
            )
            await interface.attach_window(window_id=window_id)

        identity_lane = runtime.bind(
            branch_id=identity_branch_id,
            projection="Identity",
            actor_id=expected_actor_id,
        )
        with identity_lane.activate(commit=True, publish=False):
            identity = await Identity.signup(public_key=public_key)
            actor = await identity.ensure_actor()
            assert actor.id == expected_actor_id
            actor_focus_scope = await actor.join_focus_scope(focus_scope_id)
            assert actor_focus_scope.id == expected_actor_focus_scope_id

        committed_focus_scope = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=focus_scope_id,
            projection_name="FocusScope",
            root_id=focus_scope_id,
            root_type=FocusScope,
        )
        committed_window = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=window_id,
            projection_name="Window",
            root_id=window_id,
            root_type=Window,
        )
        committed_interface_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_config_id,
            projection_name="InterfaceConfig",
            root_id=interface_config_id,
            root_type=InterfaceConfig,
        )
        committed_interface = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_id,
            projection_name="Interface",
            root_id=interface_id,
            root_type=Interface,
        )
        committed_actor = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=identity_branch_id,
            projection_name="Identity",
            root_id=expected_actor_id,
            root_type=Actor,
        )

        assert committed_focus_scope.id == focus_scope_id
        assert committed_focus_scope.title == "Execution"
        assert committed_focus_scope.description == "Personal execution scope"
        assert committed_focus_scope.is_active is True

        assert committed_window.id == window_id
        assert committed_window.window_id == window_key_id
        assert committed_window.active_layout_id == layout_id
        assert tuple(committed_window.layouts) == ()

        assert committed_interface_config.id == interface_config_id
        assert committed_interface_config.name == interface_config_name
        assert committed_interface_config.description == (
            "Window focus scope proof interface"
        )

        assert committed_interface.id == interface_id
        assert committed_interface.interface_config_id == interface_config_id
        assert committed_interface.os == InterfaceOs.linux
        assert committed_interface.version == "0.0.0-test"
        assert tuple(item.id for item in committed_interface.interface_windows) == (
            interface_window_id,
        )
        interface_window = committed_interface.interface_windows[0]
        assert interface_window.window_id == window_id

        assert committed_actor.id == expected_actor_id
        assert committed_actor.identity_id == expected_identity_id
        assert tuple(item.id for item in committed_actor.actor_focus_scopes) == (
            expected_actor_focus_scope_id,
        )
        actor_focus_scope = committed_actor.actor_focus_scopes[0]
        assert actor_focus_scope.actor_id == expected_actor_id
        assert actor_focus_scope.focus_scope_id == focus_scope_id


def _runtime_ids() -> dict[str, object]:
    return {
        "environment_id": uuid4(),
        "process_id": uuid4(),
        "thread_id": uuid4(),
        "actor_id": uuid4(),
    }
