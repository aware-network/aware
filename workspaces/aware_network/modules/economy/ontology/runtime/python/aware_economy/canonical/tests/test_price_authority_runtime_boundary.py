from __future__ import annotations

import ast
from pathlib import Path


PRICE_ROOT = Path(__file__).resolve().parents[1] / "price"
ECONOMY_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = PRICE_ROOT / "authority.py"
PRICE_RESERVATION_SETTLEMENT_PATH = ECONOMY_ROOT / "price_reservation_settlement.py"


def _import_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return tuple(modules)


def _import_roots(path: Path) -> set[str]:
    return {module.split(".", 1)[0] for module in _import_modules(path)}


def test_price_authority_uses_meta_portal_lane_resolver_facade() -> None:
    imports = _import_modules(AUTHORITY_PATH)
    source = AUTHORITY_PATH.read_text(encoding="utf-8")

    assert "aware_runtime" not in _import_roots(AUTHORITY_PATH)
    assert "aware_economy.canonical.price.relationship_lane" not in imports
    assert "aware_meta.runtime.portal_lane_resolution" in imports
    assert "aware_meta.runtime.oigb_relationship_lane" not in imports
    assert "attach_oigb_relationship" not in source
    assert "iter_lane_heads_by_projection" not in source


def test_price_reservation_settlement_uses_meta_runtime_contracts() -> None:
    source = PRICE_RESERVATION_SETTLEMENT_PATH.read_text(encoding="utf-8")

    assert "aware_runtime" not in _import_roots(PRICE_RESERVATION_SETTLEMENT_PATH)
    assert "AwareRuntimeIndex" not in source
    assert "FunctionCallInvoker" not in source
    assert "hydrate_orm_graph_from_oig" not in source
    assert "ocg_support" not in source
    assert "bind_runtime_lane" not in source
    assert "ApiInvocationRuntimeProtocol" in source
    assert "MetaGraphRuntimeIndex" in source
    assert "reify_oig_session" in source
