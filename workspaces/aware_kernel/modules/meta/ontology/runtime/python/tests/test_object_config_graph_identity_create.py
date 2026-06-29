from __future__ import annotations

import pytest

from aware_meta.handlers.impl.config.object_config_graph_identity import (
    create,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_identity_id


@pytest.mark.asyncio
async def test_create_returns_identity_instance() -> None:
    key = "aware_identity"
    ocgi = await create(
        key=key,
        label="ocg:aware_identity",
    )

    assert ocgi.id == stable_object_config_graph_identity_id(key=key)
    assert ocgi.key == key
    assert ocgi.label == "ocg:aware_identity"
