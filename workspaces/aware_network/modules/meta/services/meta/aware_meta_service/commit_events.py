from __future__ import annotations

# pyright: reportMissingImports=false

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias, cast
from uuid import UUID, NAMESPACE_URL, uuid5

from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitEventEnvelope,
)
from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitSubscriptionRequest,
)

JsonObject: TypeAlias = dict[str, object]
_VOLATILE_REPLAY_FIELDS = frozenset(
    {
        "emitted_at_unix_ms",
    }
)


def stable_meta_commit_event_id(
    *,
    domain_commit_id: UUID,
    object_instance_graph_commit_id: UUID,
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        "aware.meta.commit_event:"
        + f"{domain_commit_id}:{object_instance_graph_commit_id}",
    )


def _default_event_store_root() -> Path:
    raw = os.environ.get("AWARE_META_SERVICE_EVENT_STORE_ROOT")
    if raw is not None and raw.strip():
        return Path(raw).expanduser().resolve()
    raise RuntimeError(
        "MetaCommitEventStore requires root_path or "
        "AWARE_META_SERVICE_EVENT_STORE_ROOT; public kernel runtime must not "
        "discover repository roots"
    )


def _dump_json(payload: JsonObject) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_handle:
        _ = file_handle.write(data)
        file_handle.flush()
        os.fsync(file_handle.fileno())
    _ = tmp.replace(path)


def _event_payload(event: MetaCommitEventEnvelope) -> JsonObject:
    return cast(
        JsonObject,
        event.model_dump(mode="json", exclude_none=True),
    )


def _stable_replay_payload(payload: JsonObject) -> JsonObject:
    stable_payload = dict(payload)
    for field_name in _VOLATILE_REPLAY_FIELDS:
        stable_payload.pop(field_name, None)
    return stable_payload


def _is_stable_replay_equivalent(
    *,
    existing: JsonObject,
    incoming: JsonObject,
) -> bool:
    return _stable_replay_payload(existing) == _stable_replay_payload(incoming)


def _stable_replay_diff_fields(
    *,
    existing: JsonObject,
    incoming: JsonObject,
) -> tuple[str, ...]:
    stable_existing = _stable_replay_payload(existing)
    stable_incoming = _stable_replay_payload(incoming)
    keys = set(stable_existing) | set(stable_incoming)
    return tuple(
        sorted(
            key
            for key in keys
            if stable_existing.get(key) != stable_incoming.get(key)
        )
    )


@dataclass(slots=True)
class MetaCommitEventStore:
    root_path: Path = field(default_factory=_default_event_store_root)

    def __post_init__(self) -> None:
        self.root_path = Path(self.root_path).expanduser().resolve()

    def put(self, event: MetaCommitEventEnvelope) -> bool:
        path = self._event_path(event.event_id)
        payload = _event_payload(event)
        if path.exists():
            existing = cast(JsonObject, json.loads(path.read_text(encoding="utf-8")))
            if existing != payload:
                if not _is_stable_replay_equivalent(
                    existing=existing,
                    incoming=payload,
                ):
                    diff_fields = ", ".join(
                        _stable_replay_diff_fields(
                            existing=existing,
                            incoming=payload,
                        )
                    )
                    raise ValueError(
                        "Existing Meta commit event differs: "
                        f"{event.event_id}; fields={diff_fields}"
                    )
            return False
        _atomic_write(path, _dump_json(payload))
        return True

    def iter_events(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> tuple[MetaCommitEventEnvelope, ...]:
        event_dir = self.root_path / "events"
        if not event_dir.exists():
            return ()

        events: list[tuple[MetaCommitEventEnvelope, int]] = []
        for entry in sorted(event_dir.glob("*.json")):
            try:
                event = MetaCommitEventEnvelope.model_validate_json(
                    entry.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            if _matches_subscription(event=event, request=request):
                events.append((event, entry.stat().st_mtime_ns))

        events.sort(
            key=lambda item: (
                item[0].emitted_at_unix_ms,
                item[1],
                str(item[0].event_id),
            )
        )
        ordered_events = [event for event, _mtime_ns in events]
        return tuple(_events_after_resume(events=ordered_events, request=request))

    def _event_path(self, event_id: UUID) -> Path:
        return self.root_path / "events" / f"{event_id}.json"


@dataclass(slots=True)
class MetaCommitEventBus:
    store: MetaCommitEventStore = field(default_factory=MetaCommitEventStore)
    _subscribers: set["_MetaCommitSubscription"] = field(default_factory=set)

    async def publish(self, event: MetaCommitEventEnvelope) -> None:
        created = self.store.put(event)
        if not created:
            return
        stale: list[_MetaCommitSubscription] = []
        for subscription in tuple(self._subscribers):
            if subscription.closed:
                stale.append(subscription)
                continue
            if _matches_subscription(event=event, request=subscription.request):
                await subscription.queue.put(
                    _event_for_request(event=event, request=subscription.request)
                )
        for subscription in stale:
            self._subscribers.discard(subscription)

    def replay(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> tuple[MetaCommitEventEnvelope, ...]:
        return tuple(
            _event_for_request(event=event, request=request)
            for event in self.store.iter_events(request)
        )

    def subscribe(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> "_MetaCommitSubscription":
        subscription = _MetaCommitSubscription(request=request)
        self._subscribers.add(subscription)
        return subscription

    def unsubscribe(self, subscription: "_MetaCommitSubscription") -> None:
        subscription.closed = True
        self._subscribers.discard(subscription)


@dataclass(eq=False, slots=True)
class _MetaCommitSubscription:
    request: MetaCommitSubscriptionRequest
    queue: asyncio.Queue[MetaCommitEventEnvelope] = field(default_factory=asyncio.Queue)
    closed: bool = False


def _events_after_resume(
    *,
    events: list[MetaCommitEventEnvelope],
    request: MetaCommitSubscriptionRequest,
) -> list[MetaCommitEventEnvelope]:
    if request.resume_after_event_id is None:
        return events
    for index, event in enumerate(events):
        if event.event_id == request.resume_after_event_id:
            return events[index + 1:]
    return []


def _event_for_request(
    *,
    event: MetaCommitEventEnvelope,
    request: MetaCommitSubscriptionRequest,
) -> MetaCommitEventEnvelope:
    updates: dict[str, object] = {}
    if not request.include_artifact_refs:
        updates["artifact_refs"] = []
    if not updates:
        return event
    return event.model_copy(update=updates)


def _matches_subscription(
    *,
    event: MetaCommitEventEnvelope,
    request: MetaCommitSubscriptionRequest,
) -> bool:
    if request.event_families and event.event_family not in request.event_families:
        return False
    if request.branch_filters and event.domain_branch_id not in request.branch_filters:
        return False
    if (
        request.projection_hash_filters
        and event.domain_projection_hash not in request.projection_hash_filters
    ):
        return False
    if (
        request.object_instance_graph_identity_filters
        and event.object_instance_graph_identity_id
        not in request.object_instance_graph_identity_filters
    ):
        return False
    if request.package_filters and not _matches_package_filter(
        event=event,
        package_filters=request.package_filters,
    ):
        return False
    return True


def _matches_package_filter(
    *,
    event: MetaCommitEventEnvelope,
    package_filters: list[str],
) -> bool:
    package_values: set[str] = set()
    for key in ("package", "package_name", "package_ref", "package_id"):
        value = event.metadata.get(key)
        if isinstance(value, str):
            package_values.add(value)
        elif isinstance(value, list):
            package_values.update(item for item in value if isinstance(item, str))
    return any(package_filter in package_values for package_filter in package_filters)


__all__ = [
    "MetaCommitEventBus",
    "MetaCommitEventStore",
    "stable_meta_commit_event_id",
]
