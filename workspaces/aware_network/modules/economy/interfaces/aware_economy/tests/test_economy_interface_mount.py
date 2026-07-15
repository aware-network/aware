from __future__ import annotations

from pathlib import Path
import sys
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[7]
INTERFACE_RUNTIME_ROOT = (
    REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/runtime/python"
)
INTERFACE_DTO_ROOT = (
    REPO_ROOT
    / "workspaces/aware_network/modules/interface/apis/interface/python/aware_interface_service_dto"
)

for source_root in (INTERFACE_RUNTIME_ROOT, INTERFACE_DTO_ROOT):
    source_root_text = str(source_root)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)

from aware_interface import (  # noqa: E402
    InterfaceResolvedSectionStateAddress,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
    resolve_bundle_backed_pane_descriptors,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (  # noqa: E402
    InterfaceConfigBundle,
)

INTERFACE_ROOT = (
    REPO_ROOT / "workspaces/aware_network/modules/economy/interfaces/aware_economy"
)
CONFIG_BUNDLE = INTERFACE_ROOT / "bundles/interface.config.bundle.json"


def _load_bundle() -> InterfaceConfigBundle:
    assert CONFIG_BUNDLE.exists(), (
        "Economy Interface config bundle is missing; run Workspace materialize "
        "for package aware-economy-interface."
    )
    return InterfaceConfigBundle.model_validate_json(
        CONFIG_BUNDLE.read_text(encoding="utf-8")
    )


def _section_id(bundle: InterfaceConfigBundle, section_key: str) -> UUID:
    for window in bundle.window_configs:
        if window.key != "main":
            continue
        for layout in window.layout_configs:
            if layout.key != "coordination_center":
                continue
            for section in layout.sections:
                if section.key == section_key:
                    return section.layout_config_section_config_id
    raise AssertionError(f"missing section {section_key!r} in Economy Interface bundle")


def test_economy_interface_bundle_mounts_wallet_capital_view_state() -> None:
    bundle = _load_bundle()

    assert bundle.interface_package_name == "aware-economy-interface"
    assert bundle.name == "aware_economy"
    assert len(bundle.pane_configs) == 1

    pane_config = bundle.pane_configs[0]
    assert pane_config.name == "wallet_capital"
    assert pane_config.pane_kind == "wallet_capital"
    assert pane_config.pane_package_name == "aware-economy-wallet-capital-pane"
    assert pane_config.narrative_key == "economy.wallet_capital"

    assert len(pane_config.projection_experience_views) == 1
    view = pane_config.projection_experience_views[0]
    assert view.view_ref == "aware_economy.home.wallet_capital.v1"
    assert view.projection_view_key == "home.wallet_capital.v1"
    assert view.state_model_id is not None
    assert view.section_mounts[0].layout_config_section_config_id == _section_id(
        bundle,
        "primary",
    )
    assert {action.action_key for action in view.invocation_actions} == {
        "fund_wallet",
        "refresh_wallet_capital",
    }


def test_economy_interface_mount_resolves_as_experience_view_state() -> None:
    bundle = _load_bundle()
    primary_section_id = _section_id(bundle, "primary")

    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key="main",
        layout_key="coordination_center",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="primary",
                layout_config_section_config_id=primary_section_id,
                title="Capital",
                is_visible=True,
            ),
        ),
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=bundle,
        projection_view_id_fallback=None,
        section_state_addresses={
            "primary": InterfaceResolvedSectionStateAddress(
                section_key="primary",
            ),
        },
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "section_focus_scope_lane",
        summary_for_section=lambda _section_key, _projection_view_id: None,
        action_keys_for_section=lambda _section_key: (),
    )

    assert len(descriptors) == 1
    descriptor = descriptors[0]
    assert descriptor.window_key == "main"
    assert descriptor.layout_key == "coordination_center"
    assert descriptor.section_key == "primary"
    assert descriptor.pane_kind == "wallet_capital"
    assert descriptor.pane_package_name == "aware-economy-wallet-capital-pane"
    assert descriptor.view_ref == "aware_economy.home.wallet_capital.v1"
    assert descriptor.projection_view_key == "home.wallet_capital.v1"
    assert descriptor.state_model_id is not None
    assert descriptor.state_source_kind == "experience_view_state"
    assert set(descriptor.action_keys) == {"fund_wallet", "refresh_wallet_capital"}
