from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_reactivity_sdk.service_host import (
    AgentReactivityBridgeService,
    ReactivityEventDispatcherService,
    get_local_lane_materialized_actor_subscription_source_class,
    get_local_primary_fallback_actor_subscription_source_class,
    get_local_reactivity_event_dispatcher_service_class,
    parse_actor_subscription_payload,
)


SDK_ROOT = Path(__file__).resolve().parents[1]
SERVICE_HOST_SOURCE = SDK_ROOT / "aware_reactivity_sdk" / "service_host.py"
SDK_PYPROJECT = SDK_ROOT / "pyproject.toml"


def test_local_service_host_has_no_deprecated_runtime_package_reference() -> None:
    assert "aware_" + "runtime" not in SERVICE_HOST_SOURCE.read_text(encoding="utf-8")
    assert "aware-" + "runtime" not in SDK_PYPROJECT.read_text(encoding="utf-8")


def test_local_reactivity_dispatcher_from_env_disabled(monkeypatch) -> None:
    monkeypatch.delenv("AWARE_REACTIVITY_DISPATCHER_ENABLED", raising=False)
    monkeypatch.delenv("AWARE_NODE_AGENT_REACTIVITY_BRIDGE_ENABLED", raising=False)

    assert AgentReactivityBridgeService.from_env() is None


def test_local_reactivity_dispatcher_constructor_stays_disabled_without_runtime() -> (
    None
):
    service = ReactivityEventDispatcherService(enabled=False)

    assert service.__class__.__name__ == "_RetiredLocalReactivityEventDispatcherService"
    assert callable(getattr(service, "start", None))
    assert callable(getattr(service, "stop", None))


def test_local_reactivity_dispatcher_enabled_path_names_clean_blocker() -> None:
    with pytest.raises(RuntimeError, match="deprecated local dispatcher"):
        ReactivityEventDispatcherService(enabled=True)


def test_local_reactivity_classes_resolve_lazily() -> None:
    assert (
        get_local_reactivity_event_dispatcher_service_class().__name__
        == "_RetiredLocalReactivityEventDispatcherService"
    )
    assert (
        get_local_lane_materialized_actor_subscription_source_class().__name__
        == "LaneMaterializedActorSubscriptionSource"
    )
    assert (
        get_local_primary_fallback_actor_subscription_source_class().__name__
        == "PrimaryFallbackActorSubscriptionSource"
    )


def test_parse_actor_subscription_payload_delegates_to_local_reactivity_parser() -> (
    None
):
    subscription_id = uuid4()
    actor_id = uuid4()
    scope_id = uuid4()
    condition_id = uuid4()
    identity_id = uuid4()
    branch_id = uuid4()

    parsed = parse_actor_subscription_payload(
        [
            {
                "id": str(subscription_id),
                "actor_id": str(actor_id),
                "event_config_condition_config_scope_id": str(scope_id),
                "event_config_condition_config_id": str(condition_id),
                "object_instance_graph_identity_id": str(identity_id),
                "object_instance_graph_branch_id": str(branch_id),
                "name": "subscription",
                "status": "active",
                "is_enabled": True,
                "priority": 7,
            }
        ]
    )

    assert len(parsed) == 1
    assert parsed[0].id == subscription_id
    assert parsed[0].actor_id == actor_id
    assert parsed[0].event_config_condition_config_id == condition_id
