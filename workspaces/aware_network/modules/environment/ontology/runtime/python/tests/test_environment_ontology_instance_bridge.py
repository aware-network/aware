from __future__ import annotations

from uuid import uuid4

import pytest

from aware_environment.handlers.impl.environment import (
    environment as environment_impl,
)
from aware_environment.handlers.impl.environment import (
    environment_ontology as environment_ontology_impl,
)
from aware_environment_ontology.environment.environment import Environment
from aware_environment_ontology.stable_ids import stable_environment_ontology_id


class _EmptyHandlerSession:
    def imap_get(self, *_args, **_kwargs):
        return None


@pytest.mark.asyncio
async def test_environment_ontology_bridge_assigns_environment_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _EmptyHandlerSession()
    monkeypatch.setattr(
        environment_ontology_impl,
        "current_handler_session",
        lambda: session,
    )

    environment_id = uuid4()
    ontology_id = uuid4()

    bridge = await environment_ontology_impl.build_via_environment(
        environment_id=environment_id,
        ontology_id=ontology_id,
        role="primary",
        status="active",
        title="Kernel",
        description="Kernel ontology authority",
    )

    assert bridge.id == stable_environment_ontology_id(
        environment_id=environment_id,
        ontology_id=ontology_id,
    )
    assert bridge.environment_id == environment_id
    assert bridge.ontology_id == ontology_id
    assert not hasattr(bridge, "ontology_object_instance_graph_commit_id")
    assert bridge.role == "primary"
    assert bridge.status == "active"
    assert bridge.ontology is None


@pytest.mark.asyncio
async def test_environment_attach_ontology_mutates_only_environment_membership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _EmptyHandlerSession()
    monkeypatch.setattr(
        environment_ontology_impl,
        "current_handler_session",
        lambda: session,
    )

    environment_id = uuid4()
    ontology_id = uuid4()
    created_bridge = await environment_ontology_impl.build_via_environment(
        environment_id=environment_id,
        ontology_id=ontology_id,
    )

    async def _fake_build_via_environment(**kwargs):
        assert kwargs["environment_id"] == environment_id
        assert kwargs["ontology_id"] == ontology_id
        return created_bridge

    monkeypatch.setattr(
        environment_impl.EnvironmentOntology,
        "build_via_environment",
        _fake_build_via_environment,
    )

    environment = Environment(
        id=environment_id,
        config_id=uuid4(),
        key="kernel",
        title="Kernel",
        ontologies=[],
    )

    result = await environment_impl.attach_ontology(
        environment,
        ontology_id=ontology_id,
    )

    assert result is created_bridge
    assert environment.ontologies == [created_bridge]
