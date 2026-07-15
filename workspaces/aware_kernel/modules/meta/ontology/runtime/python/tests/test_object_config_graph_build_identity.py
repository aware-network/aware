from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.handlers.impl.config import object_config_graph as handler
from aware_meta.graph.config.stable_ids import stable_object_config_graph_identity_id
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)


class _FakeSession:
    def __init__(self, objects: dict[tuple[type[object], UUID], object]) -> None:
        self._objects = objects

    def imap_get(self, model_type: type[object], object_id: UUID | None) -> Any:
        if object_id is None:
            return None
        return self._objects.get((model_type, object_id))


@pytest.mark.asyncio
async def test_object_config_graph_build_synthesizes_deterministic_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fqn_prefix = "aware_content"
    identity_key = f"{fqn_prefix}:aware"
    identity_id = stable_object_config_graph_identity_id(key=identity_key)
    monkeypatch.setattr(handler, "current_handler_session", lambda: _FakeSession({}))

    graph = await handler.build(
        name="content",
        hash="sha256:content",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_identity_id=identity_id,
    )

    assert graph.object_config_graph_identity_id == identity_id
    assert graph.object_config_graph_identity is not None
    assert graph.object_config_graph_identity.id == identity_id
    assert graph.object_config_graph_identity.key == identity_key


@pytest.mark.asyncio
async def test_object_config_graph_build_rejects_mismatched_identity_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(handler, "current_handler_session", lambda: _FakeSession({}))

    with pytest.raises(RuntimeError, match="object_config_graph_identity_id"):
        await handler.build(
            name="content",
            hash="sha256:content",
            fqn_prefix="aware_content",
            language=CodeLanguage.aware,
            object_config_graph_identity_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_object_config_graph_build_reuses_session_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fqn_prefix = "aware_content"
    identity_key = f"{fqn_prefix}:aware"
    identity_id = stable_object_config_graph_identity_id(key=identity_key)
    identity = ObjectConfigGraphIdentity(
        id=identity_id,
        key=identity_key,
        label="Existing identity",
    )
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession({(ObjectConfigGraphIdentity, identity_id): identity}),
    )

    graph = await handler.build(
        name="content",
        hash="sha256:content",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_identity_id=identity_id,
    )

    assert graph.object_config_graph_identity is identity
