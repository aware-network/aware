from __future__ import annotations

from typing import Protocol, cast
from uuid import UUID

from aware_meta.receipts.notifications import LaneCommitReceiptNotification
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_reactivity.subscription_contract import ActorSubscriptionBridgeConfig
from aware_utils.logging import logger


class ActorSubscriptionSource(Protocol):
    async def list_subscriptions(
        self,
        *,
        receipt: LaneCommitReceiptNotification | None = None,
        trigger_projection_hash: str | None = None,
    ) -> list[ActorSubscriptionBridgeConfig]: ...


class MetaRuntimeIndexProvider(Protocol):
    async def ensure_index(self) -> None: ...

    def get_index(self) -> MetaGraphRuntimeIndex: ...


def _as_str_object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    entries = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in entries.keys()):
        return None
    return cast("dict[str, object]", entries)


def _coerce_int(value: object, *, default: int) -> int:
    if value is None:
        return default
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            return int(value.strip() or str(default))
    except Exception:
        pass
    return default


def _coerce_uuid(value: object) -> UUID | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return UUID(text)
    except Exception:
        return None


def parse_actor_subscription_payload(
    payload: object,
) -> list[ActorSubscriptionBridgeConfig]:
    if not isinstance(payload, list):
        raise ValueError("subscription payload must be a JSON list")

    parsed: list[ActorSubscriptionBridgeConfig] = []
    for item in cast("list[object]", payload):
        item_config = _as_str_object_dict(item)
        if item_config is None:
            continue
        try:
            sub_id_raw = str(item_config.get("id") or "").strip()
            actor_id_raw = str(item_config.get("actor_id") or "").strip()
            scope_id_raw = str(
                item_config.get("event_config_condition_config_scope_id") or ""
            ).strip()
            ecc_id_raw = str(
                item_config.get("event_config_condition_config_id") or ""
            ).strip()
            oigi_id_raw = str(
                item_config.get("object_instance_graph_identity_id")
                or item_config.get("oig_branch_id")
                or ""
            ).strip()
            oigb_id_raw = str(
                item_config.get("object_instance_graph_branch_id") or ""
            ).strip()
            name = str(item_config.get("name") or "").strip()

            if (
                not sub_id_raw
                or not actor_id_raw
                or not scope_id_raw
                or not ecc_id_raw
                or not oigi_id_raw
                or not name
            ):
                continue

            status = str(item_config.get("status") or "active").strip().lower()
            is_enabled = bool(item_config.get("is_enabled", True))
            priority = _coerce_int(item_config.get("priority"), default=0)
            event_config_condition_config_id = UUID(ecc_id_raw)
            action_type = str(item_config.get("action_type") or "").strip() or None
            addressing_policy = (
                str(item_config.get("addressing_policy") or "any").strip().lower()
                or "any"
            )
            event_config_action_config_ids_raw = item_config.get(
                "event_config_action_config_ids"
            )
            event_config_action_config_ids: list[UUID] = []
            if isinstance(event_config_action_config_ids_raw, list):
                for raw_id in cast("list[object]", event_config_action_config_ids_raw):
                    parsed_id = _coerce_uuid(raw_id)
                    if parsed_id is not None:
                        event_config_action_config_ids.append(parsed_id)

            filter_config_raw = item_config.get("filter_config")
            filter_config: dict[str, object] | None
            if isinstance(filter_config_raw, dict):
                filter_config = _as_str_object_dict(cast("object", filter_config_raw))
            else:
                filter_config = None

            parsed.append(
                ActorSubscriptionBridgeConfig(
                    id=UUID(sub_id_raw),
                    actor_id=UUID(actor_id_raw),
                    event_config_condition_config_scope_id=UUID(scope_id_raw),
                    event_config_condition_config_id=event_config_condition_config_id,
                    object_instance_graph_identity_id=UUID(oigi_id_raw),
                    object_instance_graph_branch_id=(
                        UUID(oigb_id_raw) if oigb_id_raw else None
                    ),
                    name=name,
                    action_type=action_type,
                    event_config_action_config_ids=event_config_action_config_ids,
                    addressing_policy=addressing_policy,
                    is_enabled=is_enabled,
                    status=status,
                    priority=priority,
                    filter_config=filter_config,
                )
            )
        except Exception as exc:
            logger.warning(
                "[reactivity-bridge] invalid subscription entry skipped: %s",
                exc,
            )
            continue
    return parsed


class PrimaryFallbackActorSubscriptionSource:
    """Try primary source first, then fallback source only on primary failure."""

    def __init__(
        self,
        *,
        primary: ActorSubscriptionSource,
        fallback: ActorSubscriptionSource,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def list_subscriptions(
        self,
        *,
        receipt: LaneCommitReceiptNotification | None = None,
        trigger_projection_hash: str | None = None,
    ) -> list[ActorSubscriptionBridgeConfig]:
        try:
            return await self._primary.list_subscriptions(
                receipt=receipt,
                trigger_projection_hash=trigger_projection_hash,
            )
        except Exception as exc:
            logger.warning(
                "[reactivity-bridge] primary subscription source failed; "
                "using fallback: %s",
                exc,
            )
            return await self._fallback.list_subscriptions(
                receipt=receipt,
                trigger_projection_hash=trigger_projection_hash,
            )


class LaneMaterializedActorSubscriptionSource:
    """Clean-boundary placeholder for Meta-owned lane materialized subscriptions."""

    def __init__(
        self,
        *,
        manifest_path: str | None = None,
        projection_name: str = "actor_subscription",
        projection_hash_override: str | None = None,
        refresh_seconds: float = 1.0,
        index: MetaGraphRuntimeIndex | None = None,
        invoker: MetaRuntimeIndexProvider | None = None,
    ) -> None:
        self._manifest_path = manifest_path
        self._projection_name = projection_name.strip() or "actor_subscription"
        self._projection_hash_override = (
            projection_hash_override.strip() if projection_hash_override else None
        )
        self._refresh_seconds = max(float(refresh_seconds), 0.0)
        self._index = index
        self._invoker = invoker

    async def list_subscriptions(
        self,
        *,
        receipt: LaneCommitReceiptNotification | None = None,
        trigger_projection_hash: str | None = None,
    ) -> list[ActorSubscriptionBridgeConfig]:
        _ = receipt
        _ = trigger_projection_hash
        if self._index is not None or self._invoker is not None:
            raise RuntimeError(
                "LaneMaterializedActorSubscriptionSource needs the Meta-owned "
                "materialized subscription reader before it can use an injected "
                "runtime index."
            )
        raise RuntimeError(
            "LaneMaterializedActorSubscriptionSource no longer builds a legacy "
            "FunctionCallInvoker from manifest_path. Provide a clean "
            "Meta/Workspace materialized subscription source instead."
        )


__all__ = [
    "ActorSubscriptionSource",
    "LaneMaterializedActorSubscriptionSource",
    "MetaRuntimeIndexProvider",
    "PrimaryFallbackActorSubscriptionSource",
    "parse_actor_subscription_payload",
]
