from __future__ import annotations

from uuid import uuid4

import pytest
from aware_reactivity.subscription_contract import ActorSubscriptionBridgeConfig
from aware_reactivity.subscription_sources import (
    LaneMaterializedActorSubscriptionSource,
    PrimaryFallbackActorSubscriptionSource,
    parse_actor_subscription_payload,
)


def test_parse_actor_subscription_payload_parses_valid_entry() -> None:
    sub_id = uuid4()
    actor_id = uuid4()
    scope_id = uuid4()
    condition_id = uuid4()
    oigi_id = uuid4()
    oigb_id = uuid4()
    action_id = uuid4()
    branch_filter_id = uuid4()

    parsed = parse_actor_subscription_payload(
        [
            {
                "id": str(sub_id),
                "actor_id": str(actor_id),
                "event_config_condition_config_scope_id": str(scope_id),
                "event_config_condition_config_id": str(condition_id),
                "object_instance_graph_identity_id": str(oigi_id),
                "object_instance_graph_branch_id": str(oigb_id),
                "name": "sub",
                "status": "ACTIVE",
                "is_enabled": True,
                "priority": "3",
                "action_type": "agent.turn.execute",
                "addressing_policy": "ANY",
                "event_config_action_config_ids": [str(action_id), "not-a-uuid"],
                "filter_config": {"branch_ids": [str(branch_filter_id)]},
            },
            {"id": "missing-required-fields"},
            "not-a-dict",
        ]
    )

    assert len(parsed) == 1
    sub = parsed[0]
    assert sub.id == sub_id
    assert sub.actor_id == actor_id
    assert sub.event_config_condition_config_scope_id == scope_id
    assert sub.event_config_condition_config_id == condition_id
    assert sub.object_instance_graph_identity_id == oigi_id
    assert sub.object_instance_graph_branch_id == oigb_id
    assert sub.status == "active"
    assert sub.addressing_policy == "any"
    assert sub.priority == 3
    assert sub.event_config_action_config_ids == [action_id]
    assert sub.filter_config == {"branch_ids": [str(branch_filter_id)]}


def test_parse_actor_subscription_payload_accepts_oig_branch_id_alias() -> None:
    sub_id = uuid4()
    actor_id = uuid4()
    scope_id = uuid4()
    condition_id = uuid4()
    oigi_alias_id = uuid4()
    payload = [
        {
            "id": str(sub_id),
            "actor_id": str(actor_id),
            "event_config_condition_config_scope_id": str(scope_id),
            "event_config_condition_config_id": str(condition_id),
            "oig_branch_id": str(oigi_alias_id),
            "name": "sub",
        }
    ]

    parsed = parse_actor_subscription_payload(payload)
    assert len(parsed) == 1
    assert parsed[0].id == sub_id
    assert parsed[0].actor_id == actor_id
    assert parsed[0].event_config_condition_config_scope_id == scope_id
    assert parsed[0].event_config_condition_config_id == condition_id
    assert parsed[0].object_instance_graph_identity_id == oigi_alias_id


class _PrimaryFailSource:
    async def list_subscriptions(
        self, **_kwargs: object
    ) -> list[ActorSubscriptionBridgeConfig]:
        raise RuntimeError("primary failed")


class _FallbackSource:
    def __init__(self, item: ActorSubscriptionBridgeConfig) -> None:
        self.item = item

    async def list_subscriptions(
        self, **_kwargs: object
    ) -> list[ActorSubscriptionBridgeConfig]:
        return [self.item]


@pytest.mark.asyncio
async def test_primary_fallback_actor_subscription_source_uses_fallback_on_error() -> (
    None
):
    expected = ActorSubscriptionBridgeConfig(
        id=uuid4(),
        actor_id=uuid4(),
        event_config_condition_config_scope_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
        name="fallback",
        action_type=None,
        event_config_action_config_ids=[],
        addressing_policy="any",
        is_enabled=True,
        status="active",
        priority=0,
        filter_config=None,
    )
    source = PrimaryFallbackActorSubscriptionSource(
        primary=_PrimaryFailSource(),
        fallback=_FallbackSource(expected),
    )

    out = await source.list_subscriptions(receipt=None, trigger_projection_hash=None)
    assert out == [expected]


@pytest.mark.asyncio
async def test_lane_materialized_source_names_clean_meta_blocker() -> None:
    source = LaneMaterializedActorSubscriptionSource(
        manifest_path="legacy-runtime-manifest.json"
    )

    with pytest.raises(RuntimeError, match="clean Meta/Workspace materialized"):
        await source.list_subscriptions()
