from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest

from aware_meta.handlers.impl.config import object_config_graph_package as handler
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id


class _FakeSession:
    def __init__(self, objects: dict[tuple[type[object], UUID], object]) -> None:
        self._objects = objects

    def imap_get(self, model_type: type[object], object_id: UUID | None) -> Any:
        if object_id is None:
            return None
        return self._objects.get((model_type, object_id))


@pytest.mark.asyncio
async def test_object_config_graph_package_build_advances_graph_commit_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = UUID("11111111-1111-4111-8111-111111111111")
    old_commit_id = UUID("22222222-2222-4222-8222-222222222222")
    new_commit_id = UUID("33333333-3333-4333-8333-333333333333")
    existing = ObjectConfigGraphPackage(
        id=package_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        object_config_graph_id=graph_id,
        object_config_graph_object_instance_graph_commit_id=old_commit_id,
    )
    fake_session = _FakeSession({(ObjectConfigGraphPackage, package_id): existing})
    monkeypatch.setattr(handler, "current_handler_session", lambda: fake_session)

    result = await handler.build(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        object_config_graph_id=graph_id,
        object_config_graph_object_instance_graph_commit_id=new_commit_id,
    )

    assert result is existing
    assert result.object_config_graph_object_instance_graph_commit_id == new_commit_id


@pytest.mark.asyncio
async def test_object_config_graph_package_attach_advances_graph_commit_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_id = UUID("44444444-4444-4444-8444-444444444444")
    graph_id = UUID("55555555-5555-4555-8555-555555555555")
    old_commit_id = UUID("66666666-6666-4666-8666-666666666666")
    new_commit_id = UUID("77777777-7777-4777-8777-777777777777")
    package = ObjectConfigGraphPackage(
        id=package_id,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        object_config_graph_id=graph_id,
        object_config_graph_object_instance_graph_commit_id=old_commit_id,
    )
    monkeypatch.setattr(handler, "current_handler_session", lambda: _FakeSession({}))

    result = await handler.attach_object_config_graph(
        object_config_graph_package=package,
        object_config_graph_id=graph_id,
        object_config_graph_object_instance_graph_commit_id=new_commit_id,
    )

    assert result is True
    assert package.object_config_graph_object_instance_graph_commit_id == new_commit_id
