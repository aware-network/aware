from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest


@dataclass(frozen=True, slots=True)
class _FakeOpg:
    name: str
    projection_hash: str


class _FakeIndex:
    def __init__(self) -> None:
        scope_opg = _FakeOpg(
            name="EventConfigConditionConfigScope",
            projection_hash="scope.hash",
        )
        identity_opg = _FakeOpg(
            name="Identity",
            projection_hash="actor_subscription.hash",
        )
        self.ocg = type(
            "FakeOcg",
            (),
            {"object_projection_graphs": [scope_opg, identity_opg]},
        )()
        self.opg_by_hash = {
            scope_opg.projection_hash: scope_opg,
            identity_opg.projection_hash: identity_opg,
        }


class _FakeLane:
    def __init__(self) -> None:
        self.activations: list[tuple[bool, bool]] = []

    def activate(self, *, commit: bool, publish: bool) -> object:
        self.activations.append((commit, publish))
        return self

    def __enter__(self) -> "_FakeLane":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)


class _FakeContext:
    def __init__(self) -> None:
        self.index = _FakeIndex()
        self.bound_lanes: list[tuple[str, UUID, _FakeLane]] = []

    def bind_lane(self, *, projection: str, branch_id: UUID) -> _FakeLane:
        lane = _FakeLane()
        self.bound_lanes.append((projection, branch_id, lane))
        return lane


def test_actor_subscription_uses_meta_runtime_readback_boundary() -> None:
    import aware_identity.actor.subscription as subscription_mod

    source = Path(subscription_mod.__file__).read_text(encoding="utf-8")

    assert "from aware_runtime.index" not in source
    assert "AwareRuntimeIndex" not in source
    assert "hydrate_orm_graph_from_oig" not in source
    assert "from aware_runtime.function_call.decoder import" not in source
    assert "decode_attribute_value" not in source
    assert "decode_oig_attribute_value" in source
    assert (
        "from aware_runtime.materialization import MaterializationRuntimeContext"
        not in source
    )


@pytest.mark.asyncio
async def test_actor_subscription_runtime_ensure_creates_against_existing_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    import aware_identity.actor.subscription as subscription_mod
    from aware_identity_service_dto.actor.subscription import (
        ActorSubscriptionBridgeConfig,
    )
    from aware_identity_service_dto.actor.subscription import (
        ActorSubscriptionEnsureRequest,
    )
    from aware_identity_ontology.stable_ids import stable_actor_subscription_id

    actor_id = uuid4()
    scope_id = uuid4()
    event_config_condition_config_id = uuid4()
    oigi_id = uuid4()
    action_config_id = uuid4()
    expected_subscription_id = stable_actor_subscription_id(
        actor_id=actor_id,
        event_config_condition_config_scope_id=scope_id,
        name="conversation.message.created",
    )
    context = _FakeContext()
    add_calls: list[ActorSubscriptionEnsureRequest] = []
    resolve_calls = 0

    class _FakeCommitStore:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, UUID] | None:
            if branch_id == scope_id and projection_hash == "scope.hash":
                return {"commit_id": uuid4()}
            if (
                branch_id == expected_subscription_id
                and projection_hash == "actor_subscription.hash"
            ):
                return None
            raise AssertionError((branch_id, projection_hash))

    async def _resolve_subscription_by_id(
        *,
        context: object,
        subscription_id: UUID,
    ) -> ActorSubscriptionBridgeConfig | None:
        nonlocal resolve_calls
        assert context is context_fake
        assert subscription_id == expected_subscription_id
        resolve_calls += 1
        if resolve_calls == 1:
            return None
        return ActorSubscriptionBridgeConfig(
            id=expected_subscription_id,
            actor_id=actor_id,
            event_config_condition_config_scope_id=scope_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=oigi_id,
            name="conversation.message.created",
            action_type="agent.turn.execute",
            event_config_action_config_ids=[action_config_id],
            addressing_policy="any",
            is_enabled=True,
            status="active",
            priority=7,
            filter_config={"mode": "all"},
        )

    async def _add_actor_subscription_on_identity_lane(
        *,
        context: object,
        request: ActorSubscriptionEnsureRequest,
    ) -> None:
        assert context is context_fake
        add_calls.append(request)

    context_fake = context
    monkeypatch.setattr(subscription_mod, "FSCommitStore", _FakeCommitStore)
    monkeypatch.setattr(
        subscription_mod, "_resolve_subscription_by_id", _resolve_subscription_by_id
    )
    monkeypatch.setattr(
        subscription_mod,
        "_add_actor_subscription_on_identity_lane",
        _add_actor_subscription_on_identity_lane,
    )

    receipt = await subscription_mod.ensure_actor_subscription(
        request=ActorSubscriptionEnsureRequest(
            actor_id=actor_id,
            event_config_condition_config_scope_id=scope_id,
            name="conversation.message.created",
            action_type="agent.turn.execute",
            event_config_action_config_ids=[action_config_id],
            priority=7,
            filter_config={"mode": "all"},
            request_id=uuid4(),
        ),
        context=cast(Any, context),
    )

    assert receipt.subscription_created is True
    assert receipt.subscription.id == expected_subscription_id
    assert receipt.subscription.event_config_condition_config_id == (
        event_config_condition_config_id
    )
    assert receipt.info == "identity actor-subscription ensured"
    assert len(add_calls) == 1
    assert add_calls[0].actor_id == actor_id
    assert add_calls[0].event_config_condition_config_scope_id == scope_id
    assert add_calls[0].action_type == "agent.turn.execute"
    assert add_calls[0].priority == 7


@pytest.mark.asyncio
async def test_actor_subscription_runtime_resolve_filters_bridge_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    import aware_identity.actor.subscription as subscription_mod
    from aware_identity_service_dto.actor.subscription import (
        ActorSubscriptionBridgeConfig,
    )
    from aware_identity_service_dto.actor.subscription import (
        ActorSubscriptionResolveRequest,
    )

    actor_id = uuid4()
    other_actor_id = uuid4()
    event_config_condition_config_id = uuid4()
    oigi_id = uuid4()
    context = _FakeContext()

    async def _list_subscriptions(
        *, context: object
    ) -> list[ActorSubscriptionBridgeConfig]:
        assert context is context_fake
        return [
            ActorSubscriptionBridgeConfig(
                id=uuid4(),
                actor_id=actor_id,
                event_config_condition_config_scope_id=uuid4(),
                event_config_condition_config_id=event_config_condition_config_id,
                object_instance_graph_identity_id=oigi_id,
                name="match",
                is_enabled=True,
                status="active",
                priority=9,
            ),
            ActorSubscriptionBridgeConfig(
                id=uuid4(),
                actor_id=other_actor_id,
                event_config_condition_config_scope_id=uuid4(),
                event_config_condition_config_id=event_config_condition_config_id,
                object_instance_graph_identity_id=oigi_id,
                name="other actor",
                is_enabled=True,
                status="active",
                priority=20,
            ),
            ActorSubscriptionBridgeConfig(
                id=uuid4(),
                actor_id=actor_id,
                event_config_condition_config_scope_id=uuid4(),
                event_config_condition_config_id=event_config_condition_config_id,
                object_instance_graph_identity_id=oigi_id,
                name="disabled",
                is_enabled=False,
                status="active",
                priority=30,
            ),
            ActorSubscriptionBridgeConfig(
                id=uuid4(),
                actor_id=actor_id,
                event_config_condition_config_scope_id=uuid4(),
                event_config_condition_config_id=event_config_condition_config_id,
                object_instance_graph_identity_id=oigi_id,
                name="inactive",
                is_enabled=True,
                status="inactive",
                priority=40,
            ),
        ]

    context_fake = context
    monkeypatch.setattr(subscription_mod, "_list_subscriptions", _list_subscriptions)

    result = await subscription_mod.resolve_actor_subscriptions(
        request=ActorSubscriptionResolveRequest(
            actor_id=actor_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=oigi_id,
        ),
        context=cast(Any, context),
    )

    assert [subscription.name for subscription in result.subscriptions] == ["match"]
    assert result.info == "identity actor-subscriptions resolved"

    disabled_result = await subscription_mod.resolve_actor_subscriptions(
        request=ActorSubscriptionResolveRequest(
            actor_id=actor_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=oigi_id,
            include_disabled=True,
        ),
        context=cast(Any, context),
    )
    assert [subscription.name for subscription in disabled_result.subscriptions] == [
        "disabled",
        "match",
    ]

    inactive_result = await subscription_mod.resolve_actor_subscriptions(
        request=ActorSubscriptionResolveRequest(
            actor_id=actor_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=oigi_id,
            include_inactive=True,
        ),
        context=cast(Any, context),
    )
    assert [subscription.name for subscription in inactive_result.subscriptions] == [
        "inactive",
        "match",
    ]

    all_result = await subscription_mod.resolve_actor_subscriptions(
        request=ActorSubscriptionResolveRequest(
            actor_id=actor_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=oigi_id,
            include_disabled=True,
            include_inactive=True,
        ),
        context=cast(Any, context),
    )
    assert [subscription.name for subscription in all_result.subscriptions] == [
        "inactive",
        "disabled",
        "match",
    ]
