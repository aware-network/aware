from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_interface.stable_ids import stable_window_id, stable_window_layout_id
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_window_set_active_layout_is_link_only_and_mutates_self_only(tmp_path: Path) -> None:
    """
    `Window.set_active_layout` is the canonical window selector.

    Canonical v0:
    - WindowLayout is explicit compatibility/override state.
    - Active selection is represented by a direct Attention Layout pointer (`Window.active_layout_id`).
    - `Window.set_active_layout` updates Window state and does not create WindowLayout rows.
    """

    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.window.window import Window

        ns = uuid5(NAMESPACE_URL, "aware://tests/interface/window/set-active-layout/v1")
        window_key_id = uuid5(ns, "window")
        window_id = stable_window_id(window_id=window_key_id)
        layout_a_id = uuid5(ns, "layout_a")
        layout_b_id = uuid5(ns, "layout_b")
        window_layout_a_id = stable_window_layout_id(
            window_id=window_id,
            layout_id=layout_a_id,
        )

        lane = runtime.bind(
            branch_id=window_id,
            projection="Window",
            actor_id=uuid4(),
        )
        with lane.activate(commit=True, publish=False):
            window = await Window.build(window_id=window_key_id)
            await window.add_layout(layout_id=layout_a_id)
            await window.set_active_layout(layout_id=layout_b_id)
            await window.set_active_layout(layout_id=layout_a_id)

        committed_window = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=window_id,
            projection_name="Window",
            root_id=window_id,
            root_type=Window,
        )

        assert committed_window.id == window_id
        assert committed_window.active_layout_id == layout_a_id
        assert tuple(layout.id for layout in committed_window.layouts) == (
            window_layout_a_id,
        )
        assert tuple(layout.layout_id for layout in committed_window.layouts) == (
            layout_a_id,
        )
