from __future__ import annotations

from uuid import UUID

from aware_interface.lifecycle.window_layout import _select_layout_config
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
)


_WINDOW_CONFIG_ID = UUID("0d4bbcb6-ad68-5b92-b52e-34fbfd1ed305")
_WINDOW_JOIN_ID = UUID("b70784ac-b222-54c3-9fef-b772a12d6351")
_PRIMARY_LAYOUT_ID = UUID("3377fbc6-7c1d-5f58-ad77-7cbfd6df413f")
_SECONDARY_LAYOUT_ID = UUID("d2f54884-02e1-53dc-afd1-b0bce8e25fcc")


def _layout(*, layout_id: UUID, key: str) -> InterfaceWindowConfigLayoutBundle:
    return InterfaceWindowConfigLayoutBundle(
        window_config_layout_config_id=UUID(
            "175783ca-0452-5ea6-aa52-1ed659d99588"
            if layout_id == _PRIMARY_LAYOUT_ID
            else "c771f614-3c31-5d02-9e54-347cd63f53dd"
        ),
        layout_config_id=layout_id,
        key=key,
    )


def _window(*layouts: InterfaceWindowConfigLayoutBundle) -> InterfaceWindowConfigBundle:
    return InterfaceWindowConfigBundle(
        interface_config_window_config_id=_WINDOW_JOIN_ID,
        window_config_id=_WINDOW_CONFIG_ID,
        key="main",
        layout_configs=list(layouts),
    )


def test_multiple_layouts_require_committed_preference() -> None:
    primary = _layout(
        layout_id=_PRIMARY_LAYOUT_ID,
        key="coordination_center",
    )
    secondary = _layout(
        layout_id=_SECONDARY_LAYOUT_ID,
        key="conversation_focus",
    )
    window = _window(primary, secondary)

    assert (
        _select_layout_config(
            window_config=window,
            preferred_layout_config_id=None,
            preferred_layout_key=None,
        )
        is None
    )
    assert (
        _select_layout_config(
            window_config=window,
            preferred_layout_config_id=_SECONDARY_LAYOUT_ID,
            preferred_layout_key=None,
        )
        == secondary
    )
    assert (
        _select_layout_config(
            window_config=window,
            preferred_layout_config_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            preferred_layout_key="coordination_center",
        )
        is None
    )


def test_single_layout_is_unambiguous_without_interface_default() -> None:
    only_layout = _layout(
        layout_id=_PRIMARY_LAYOUT_ID,
        key="coordination_center",
    )

    assert (
        _select_layout_config(
            window_config=_window(only_layout),
            preferred_layout_config_id=None,
            preferred_layout_key=None,
        )
        == only_layout
    )
