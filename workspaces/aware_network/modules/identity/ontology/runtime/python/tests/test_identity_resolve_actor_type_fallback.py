from __future__ import annotations

from pathlib import Path

import aware_identity.read.actor_type_resolver as actor_type_resolver


def test_actor_type_resolver_uses_meta_runtime_boundary() -> None:
    source = Path(actor_type_resolver.__file__).read_text(encoding="utf-8")

    assert "from aware_runtime" not in source
    assert "AwareRuntimeIndex" not in source
    assert "hydrate_orm_graph_from_oig" not in source


def test_actor_type_resolver_has_no_orm_cache_fallback() -> None:
    source = Path(actor_type_resolver.__file__).read_text(encoding="utf-8")
    removed_helpers = ("get_by_id" + "_sync", "get_by_id" + "_cached")

    assert "execute_query" not in source
    assert "by_id_cached" not in source
    assert all(helper not in source for helper in removed_helpers)
