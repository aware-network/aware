from __future__ import annotations

from aware_interface.lifecycle.window_layout import (
    resolve_bootstrap_window_layout_state,
)


def test_resolve_bootstrap_window_layout_state_returns_grid_layout() -> None:
    state = resolve_bootstrap_window_layout_state(
        active=True,
        projection_view_id="entry.control-plane",
        has_target_statuses=True,
        has_logs=False,
        resolved_at="2026-04-02T13:30:00Z",
    )

    assert state is not None
    assert state.source_kind == "interface_bootstrap"
    assert state.window_key == "bootstrap"
    assert state.layout_key == "bootstrap.control-plane"
    assert state.frame_mode == "grid"
    assert state.resolved_at == "2026-04-02T13:30:00Z"
    assert [section.section_key for section in state.sections if section.is_visible] == [
        "overview",
        "actions",
        "targets",
        "activity",
        "context",
    ]


def test_resolve_bootstrap_window_layout_state_returns_none_when_inactive() -> None:
    assert (
        resolve_bootstrap_window_layout_state(
            active=False,
            projection_view_id=None,
            has_target_statuses=False,
            has_logs=False,
        )
        is None
    )
