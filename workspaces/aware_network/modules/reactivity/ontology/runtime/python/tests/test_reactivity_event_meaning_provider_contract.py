from __future__ import annotations

from uuid import uuid4

import pytest

from aware_reactivity.handlers.impl.event.event_config import (
    add_meaning_resolver_config,
)
from aware_reactivity.handlers.impl.event.event_config import (
    create as create_event_config,
)
from aware_reactivity.handlers.impl.event.event_config_meaning_resolver_config import (
    create_via_event_config,
)
from aware_reactivity_ontology.stable_ids import (
    stable_event_config_meaning_resolver_config_id,
)


@pytest.mark.asyncio
async def test_event_config_registers_meaning_resolver_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "aware_reactivity_ontology.event.event_config_meaning_resolver_config."
        "EventConfigMeaningResolverConfig.create_via_event_config",
        create_via_event_config,
    )
    event_config = await create_event_config(
        name="conversation.message.created",
        description="Conversation message creation.",
    )
    action_config_id = uuid4()

    first = await add_meaning_resolver_config(
        event_config,
        action_config_id=action_config_id,
        resolver_key=" Primary ",
    )
    second = await add_meaning_resolver_config(
        event_config,
        action_config_id=action_config_id,
        resolver_key="primary",
    )

    assert first is second
    assert len(event_config.event_config_meaning_resolver_configs) == 1
    assert first.resolver_key == "primary"
    assert first.id == stable_event_config_meaning_resolver_config_id(
        event_config_id=event_config.id,
        action_config_id=action_config_id,
        resolver_key="primary",
    )


@pytest.mark.asyncio
async def test_meaning_resolver_constructor_preserves_typed_policy() -> None:
    event_config_id = uuid4()
    action_config_id = uuid4()

    resolver = await create_via_event_config(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        resolver_key="default",
        priority=7,
        is_enabled=False,
    )

    assert resolver.event_config_id == event_config_id
    assert resolver.action_config_id == action_config_id
    assert resolver.resolver_key == "default"
    assert resolver.priority == 7
    assert resolver.is_enabled is False
