from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import statistics
import time
from typing import TypeAlias, cast


JsonScalar: TypeAlias = str | int | float | bool | None
JsonObject: TypeAlias = dict[str, object]


@dataclass(frozen=True, slots=True)
class CommitPerfTraceEvent:
    phase: str
    duration_ms: float
    category: str = "meta.commit"
    metadata: Mapping[str, JsonScalar] = field(default_factory=dict)

    def as_json(self) -> JsonObject:
        payload: JsonObject = {
            "category": self.category,
            "phase": self.phase,
            "duration_ms": round(self.duration_ms, 3),
        }
        if self.metadata:
            payload["metadata"] = dict(sorted(self.metadata.items()))
        return payload


class CommitPerfTraceRecorder:
    def __init__(self, *, default_category: str = "meta.commit") -> None:
        self._default_category = default_category
        self._events: list[CommitPerfTraceEvent] = []

    def clear(self) -> None:
        self._events.clear()

    def record_elapsed(
        self,
        *,
        phase: str,
        started: float,
        ended: float | None = None,
        category: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        stop = time.perf_counter() if ended is None else ended
        self.record(
            phase=phase,
            duration_ms=max((stop - started) * 1000, 0.0),
            category=category,
            metadata=metadata,
        )

    def record(
        self,
        *,
        phase: str,
        duration_ms: float,
        category: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        self._events.append(
            CommitPerfTraceEvent(
                phase=phase,
                duration_ms=max(float(duration_ms), 0.0),
                category=category or self._default_category,
                metadata=_coerce_metadata(metadata or {}),
            )
        )

    @contextmanager
    def span(
        self,
        *,
        phase: str,
        category: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self.record_elapsed(
                phase=phase,
                started=started,
                category=category,
                metadata=metadata,
            )

    def snapshot(self) -> tuple[CommitPerfTraceEvent, ...]:
        return tuple(self._events)

    def snapshot_json(self) -> tuple[JsonObject, ...]:
        return tuple(event.as_json() for event in self._events)


_ACTIVE_COMMIT_PERF_TRACE: ContextVar[CommitPerfTraceRecorder | None] = ContextVar(
    "aware_oig_commit_perf_trace",
    default=None,
)


@contextmanager
def active_commit_perf_trace(
    recorder: CommitPerfTraceRecorder,
) -> Iterator[CommitPerfTraceRecorder]:
    token = _ACTIVE_COMMIT_PERF_TRACE.set(recorder)
    try:
        yield recorder
    finally:
        _ACTIVE_COMMIT_PERF_TRACE.reset(token)


def current_commit_perf_trace() -> CommitPerfTraceRecorder | None:
    return _ACTIVE_COMMIT_PERF_TRACE.get()


@contextmanager
def commit_perf_span(
    *,
    phase: str,
    category: str = "meta.commit",
    metadata: Mapping[str, object] | None = None,
) -> Iterator[None]:
    recorder = _ACTIVE_COMMIT_PERF_TRACE.get()
    if recorder is None:
        yield
        return
    with recorder.span(phase=phase, category=category, metadata=metadata):
        yield


def record_commit_perf_elapsed(
    *,
    phase: str,
    started: float,
    ended: float | None = None,
    category: str = "meta.commit",
    metadata: Mapping[str, object] | None = None,
) -> None:
    recorder = _ACTIVE_COMMIT_PERF_TRACE.get()
    if recorder is None:
        return
    recorder.record_elapsed(
        phase=phase,
        started=started,
        ended=ended,
        category=category,
        metadata=metadata,
    )


def summarize_commit_perf_events(
    events: Iterable[CommitPerfTraceEvent | Mapping[str, object]],
) -> dict[str, dict[str, float | int]]:
    values_by_phase: dict[str, list[float]] = defaultdict(list)
    for event in events:
        payload = _event_payload(event)
        phase = payload.get("phase")
        duration_ms = payload.get("duration_ms")
        if not isinstance(phase, str):
            continue
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int | float):
            continue
        values_by_phase[phase].append(float(duration_ms))
    return {
        phase: {
            "count": len(values),
            "total_ms": round(sum(values), 3),
            "mean_ms": round(statistics.fmean(values), 3),
            "max_ms": round(max(values), 3),
        }
        for phase, values in sorted(values_by_phase.items())
        if values
    }


def summarize_commit_perf_profiles(
    profiles: Iterable[Mapping[str, object]],
) -> dict[str, dict[str, float | int]]:
    values_by_name: dict[str, list[float]] = defaultdict(list)
    for profile in profiles:
        for name, raw_value in profile.items():
            if isinstance(raw_value, bool) or not isinstance(raw_value, int | float):
                continue
            values_by_name[name].append(float(raw_value))
    return {
        name: {
            "total": _whole_number_or_round(sum(values)),
            "mean": round(statistics.fmean(values), 3),
            "max": _whole_number_or_round(max(values)),
        }
        for name, values in sorted(values_by_name.items())
        if values
    }


def _event_payload(
    event: CommitPerfTraceEvent | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(event, CommitPerfTraceEvent):
        return event.as_json()
    return event


def _coerce_metadata(metadata: Mapping[str, object]) -> Mapping[str, JsonScalar]:
    out: dict[str, JsonScalar] = {}
    for key, value in metadata.items():
        if isinstance(value, str | int | float | bool) or value is None:
            out[str(key)] = cast(JsonScalar, value)
        else:
            out[str(key)] = str(value)
    return out


def _whole_number_or_round(value: float) -> float | int:
    return int(value) if value.is_integer() else round(value, 3)
