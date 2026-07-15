from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

PANE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[8]
INTERFACE_RUNTIME_ROOT = (
    REPO_ROOT / "workspaces/aware_network/modules/interface/ontology/runtime/python"
)
ECONOMY_DTO_ROOT = (
    REPO_ROOT
    / "workspaces/aware_network/modules/economy/apis/economy/python/aware_economy_service_dto"
)

for source_root in (INTERFACE_RUNTIME_ROOT, ECONOMY_DTO_ROOT):
    source_root_text = str(source_root)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)

from aware_economy_service_dto.economy.view import (  # noqa: E402
    EconomyWalletCapitalViewStateV1,
)
from aware_interface.pane_render import (  # noqa: E402
    lower_pane_render_spec_to_payload,
    parse_pane_render_specs,
)
from aware_interface.renderers.html import render_pane_source_html  # noqa: E402

PANE_SOURCE = PANE_ROOT / "wallet_capital.aware"
SAMPLE_STATE = PANE_ROOT / "samples" / "wallet_capital_view_state.sample.json"
EXPERIENCE_VIEW_REF = "aware_economy.home.wallet_capital.v1"


def _nodes_by_key(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        cast(str, node["node_key"]): node
        for node in cast(list[dict[str, object]], payload["nodes"])
    }


def _action_view_keys(nodes: dict[str, dict[str, object]]) -> dict[str, str]:
    action_keys: dict[str, str] = {}
    for node_key, node in nodes.items():
        for action in cast(list[dict[str, object]], node.get("action_bindings", [])):
            action_keys[node_key] = cast(str, action["view_action_key"])
            assert action["action_kind"] == "view_action"
            assert action["input_bindings"] == []
    return action_keys


def _state_attribute_refs(nodes: dict[str, dict[str, object]]) -> set[str]:
    refs: set[str] = set()
    for node in nodes.values():
        for binding in cast(list[dict[str, object]], node.get("state_bindings", [])):
            refs.add(cast(str, binding["state_attribute_ref"]))
    return refs


def test_wallet_capital_pane_parses_and_lowers_view_action_bindings() -> None:
    source = PANE_SOURCE.read_text(encoding="utf-8")

    specs = parse_pane_render_specs(source)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.pane_name == "wallet_capital"
    assert spec.view == EXPERIENCE_VIEW_REF

    payload = lower_pane_render_spec_to_payload(spec)
    nodes = _nodes_by_key(payload)

    assert payload["name"] == "wallet_capital_default"
    assert payload["view_ref"] == EXPERIENCE_VIEW_REF
    assert payload["root_node_key"] == "root"
    assert _action_view_keys(nodes) == {
        "root.actions.refresh": "refresh_wallet_capital",
        "root.actions.fund": "fund_wallet",
    }

    assert {
        "status",
        "status_tone",
        "wallet_public_id",
        "finance_entity_id",
        "coin_id",
        "balances",
        "funding_providers",
        "pending_funding_intents",
        "activity",
        "blockers",
        "empty_message",
    }.issubset(_state_attribute_refs(nodes))


def test_wallet_capital_sample_state_validates_and_renders_html_preview(
    tmp_path: Path,
) -> None:
    source = PANE_SOURCE.read_text(encoding="utf-8")
    state = cast(dict[str, Any], json.loads(SAMPLE_STATE.read_text(encoding="utf-8")))
    validated = EconomyWalletCapitalViewStateV1.model_validate(state)

    html = render_pane_source_html(
        source,
        state=validated.model_dump(mode="json"),
        render_name="default",
    )

    assert "Wallet capital" in html
    assert "wallet-public:finance-primary" in html
    assert "Stripe wallet funding" in html
    assert "external_capital_provider_route" in html
    assert "Wallet funding intent prepared before external provider settlement." in html
    assert "Refresh" in html
    assert "Fund wallet" in html

    preview_path = tmp_path / "wallet_capital.preview.html"
    preview_path.write_text(html, encoding="utf-8")
    assert preview_path.stat().st_size > 1000
