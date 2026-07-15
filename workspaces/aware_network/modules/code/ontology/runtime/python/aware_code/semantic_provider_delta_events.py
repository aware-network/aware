from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.provider-delta-event-report.v1"
)
SEMANTIC_PROVIDER_DELTA_EVENT_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.provider-delta-event.v1"
)
SEMANTIC_PROVIDER_DELTA_READABLE_EVENT_CHAIN_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.provider-delta-readable-event-chain.v1"
)


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaEvent:
    provider_key: str
    event_key: str | None = None
    provider_event_kind: str | None = None
    provider_event_contract_version: str | None = None
    event_type: str | None = None
    semantic_key: str | None = None
    operation: str | None = None
    semantic_subject_type: str | None = None
    ontology_subject_kind: str | None = None
    subject_label: str | None = None
    summary: str = "Semantic materialization event"
    narrative: str = "Semantic materialization event"
    source: str | None = None
    source_refs: tuple[str, ...] = ()
    delta_keys: tuple[str, ...] = ()
    condition_keys: tuple[str, ...] = ()
    baseline: Mapping[str, object] = field(default_factory=dict)
    current: Mapping[str, object] = field(default_factory=dict)
    head_refs: Mapping[str, object] = field(default_factory=dict)
    current_delta_fingerprint: str | None = None
    provider_operation_type: str | None = None
    would_dispatch: bool = False
    did_dispatch: bool = False
    event_dispatch_wired: bool = False
    would_execute: bool = False
    did_execute: bool = False
    would_persist: bool = False
    did_persist: bool = False
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        provider_key: str,
    ) -> "SemanticProviderDeltaEvent | None":
        event_key = _optional_text(payload.get("event_key"))
        semantic_key = _optional_text(payload.get("semantic_key"))
        summary = (
            _optional_text(payload.get("summary"))
            or _optional_text(payload.get("narrative"))
            or _optional_text(payload.get("world_change"))
        )
        if event_key is None and semantic_key is None and summary is None:
            return None
        narrative = _optional_text(payload.get("narrative")) or summary
        operation = _optional_text(payload.get("verb")) or _optional_text(
            payload.get("operation_family")
        )
        return cls(
            provider_key=_optional_text(payload.get("provider_key")) or provider_key,
            event_key=event_key,
            provider_event_kind=_optional_text(payload.get("event_kind")),
            provider_event_contract_version=_optional_text(
                payload.get("contract_version")
            ),
            event_type=_optional_text(payload.get("event_type")),
            semantic_key=semantic_key,
            operation=operation,
            semantic_subject_type=_optional_text(payload.get("subject_type")),
            ontology_subject_kind=_optional_text(
                payload.get("ontology_subject_kind")
            ),
            subject_label=_optional_text(payload.get("subject_label")),
            summary=summary or "Semantic materialization event",
            narrative=narrative or summary or "Semantic materialization event",
            source=_optional_text(payload.get("source")),
            source_refs=_tuple_text(payload.get("source_refs")),
            delta_keys=_tuple_text(payload.get("delta_keys")),
            condition_keys=_tuple_text(payload.get("condition_keys")),
            baseline=_mapping_value(payload.get("baseline")),
            current=_mapping_value(payload.get("current")),
            head_refs=_mapping_value(payload.get("head_refs")),
            current_delta_fingerprint=_optional_text(
                payload.get("current_delta_fingerprint")
            ),
            provider_operation_type=_optional_text(
                payload.get("provider_operation_type")
            ),
            would_dispatch=payload.get("would_dispatch") is True,
            did_dispatch=payload.get("did_dispatch") is True,
            event_dispatch_wired=payload.get("event_dispatch_wired") is True,
            would_execute=payload.get("would_execute") is True,
            did_execute=payload.get("did_execute") is True,
            would_persist=payload.get("would_persist") is True,
            did_persist=payload.get("did_persist") is True,
            provider_payload={str(key): value for key, value in payload.items()},
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "event_kind": "semantic_provider_delta_event",
            "contract_version": SEMANTIC_PROVIDER_DELTA_EVENT_CONTRACT_VERSION,
            "provider_key": self.provider_key,
            "event_key": self.event_key,
            "provider_event_kind": self.provider_event_kind,
            "provider_event_contract_version": (
                self.provider_event_contract_version
            ),
            "event_type": self.event_type,
            "semantic_key": self.semantic_key,
            "operation": self.operation,
            "semantic_subject_type": self.semantic_subject_type,
            "ontology_subject_kind": self.ontology_subject_kind,
            "subject_label": self.subject_label,
            "summary": self.summary,
            "narrative": self.narrative,
            "source": self.source,
            "source_refs": self.source_refs,
            "delta_keys": self.delta_keys,
            "condition_keys": self.condition_keys,
            "baseline": dict(self.baseline),
            "current": dict(self.current),
            "head_refs": dict(self.head_refs),
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "provider_operation_type": self.provider_operation_type,
            "would_dispatch": self.would_dispatch,
            "did_dispatch": self.did_dispatch,
            "event_dispatch_wired": self.event_dispatch_wired,
            "would_execute": self.would_execute,
            "did_execute": self.did_execute,
            "would_persist": self.would_persist,
            "did_persist": self.did_persist,
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaReadableEventChain:
    status: str | None = None
    reason: str | None = None
    provider_key: str | None = None
    provider_chain_kind: str | None = None
    provider_chain_contract_version: str | None = None
    source_event_count: int = 0
    event_count: int = 0
    line_count: int = 0
    lines: tuple[str, ...] = ()
    markdown: str = ""
    plain_text: str = ""
    available: bool = False
    blocked: bool = False
    blockers: tuple[str, ...] = ()
    would_dispatch: bool = False
    did_dispatch: bool = False
    event_dispatch_wired: bool = False
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        provider_key: str | None = None,
    ) -> "SemanticProviderDeltaReadableEventChain":
        lines = _tuple_text(payload.get("lines"))
        markdown = _optional_text(payload.get("markdown")) or "\n".join(lines)
        blocked = payload.get("blocked") is True
        available = payload.get("available") is True or (
            bool(lines) and not blocked
        )
        return cls(
            status=_optional_text(payload.get("status")),
            reason=_optional_text(payload.get("reason")),
            provider_key=_optional_text(payload.get("provider_key")) or provider_key,
            provider_chain_kind=_optional_text(payload.get("chain_kind")),
            provider_chain_contract_version=_optional_text(
                payload.get("contract_version")
            ),
            source_event_count=_int_value(payload.get("source_event_count")),
            event_count=_int_value(payload.get("event_count")) or len(lines),
            line_count=_int_value(payload.get("line_count")) or len(lines),
            lines=lines,
            markdown=markdown,
            plain_text=_optional_text(payload.get("plain_text")) or "\n".join(lines),
            available=available,
            blocked=blocked,
            blockers=_tuple_text(payload.get("blockers")),
            would_dispatch=payload.get("would_dispatch") is True,
            did_dispatch=payload.get("did_dispatch") is True,
            event_dispatch_wired=payload.get("event_dispatch_wired") is True,
            provider_payload={str(key): value for key, value in payload.items()},
        )

    @classmethod
    def empty(cls, *, provider_key: str | None = None) -> "SemanticProviderDeltaReadableEventChain":
        return cls(
            status="readable_semantic_event_chain_empty",
            reason="readable_semantic_event_chain_missing",
            provider_key=provider_key,
            blocked=True,
            blockers=("readable_semantic_event_chain_missing",),
        )

    def evidence_payload(self) -> dict[str, object]:
        payload = {str(key): value for key, value in self.provider_payload.items()}
        payload.setdefault("chain_kind", "semantic_provider_delta_readable_event_chain")
        payload.setdefault(
            "contract_version",
            self.provider_chain_contract_version
            or SEMANTIC_PROVIDER_DELTA_READABLE_EVENT_CHAIN_CONTRACT_VERSION,
        )
        payload.setdefault("status", self.status)
        payload.setdefault("reason", self.reason)
        payload.setdefault("provider_key", self.provider_key)
        payload.setdefault("source_event_count", self.source_event_count)
        payload.setdefault("event_count", self.event_count)
        payload.setdefault("line_count", self.line_count)
        payload.setdefault("lines", self.lines)
        payload.setdefault("markdown", self.markdown)
        payload.setdefault("plain_text", self.plain_text)
        payload.setdefault("available", self.available)
        payload.setdefault("blocked", self.blocked)
        payload.setdefault("blockers", self.blockers)
        payload.setdefault("would_dispatch", self.would_dispatch)
        payload.setdefault("did_dispatch", self.did_dispatch)
        payload.setdefault("event_dispatch_wired", self.event_dispatch_wired)
        return payload


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaEventReport:
    provider_key: str
    status: str | None = None
    reason: str | None = None
    provider_report_kind: str | None = None
    provider_report_contract_version: str | None = None
    provider_report_source: str | None = None
    semantic_dirty_diff_status: str | None = None
    semantic_dirty_diff_reason: str | None = None
    typed_operation_status: str | None = None
    current_delta_fingerprint: str | None = None
    baseline_refs: Mapping[str, object] = field(default_factory=dict)
    head_refs: Mapping[str, object] = field(default_factory=dict)
    events: tuple[SemanticProviderDeltaEvent, ...] = ()
    readable_event_chain: SemanticProviderDeltaReadableEventChain = field(
        default_factory=SemanticProviderDeltaReadableEventChain
    )
    natural_language_summaries: tuple[str, ...] = ()
    available: bool = False
    blocked: bool = False
    blockers: tuple[str, ...] = ()
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaEventReport":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            raise ValueError("Semantic provider delta event report must be a mapping.")
        return cls.from_payload(value)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
        *,
        provider_key: str | None = None,
    ) -> "SemanticProviderDeltaEventReport":
        resolved_provider_key = (
            _optional_text(payload.get("provider_key"))
            or provider_key
            or "unknown"
        )
        events = _events_from_payload(
            payload=payload,
            provider_key=resolved_provider_key,
        )
        chain_payload = _readable_chain_payload(payload)
        chain = (
            SemanticProviderDeltaReadableEventChain.from_payload(
                chain_payload,
                provider_key=resolved_provider_key,
            )
            if chain_payload
            else SemanticProviderDeltaReadableEventChain.empty(
                provider_key=resolved_provider_key
            )
        )
        blockers = _tuple_text(payload.get("blockers"))
        status = _optional_text(payload.get("status"))
        blocked = (
            payload.get("blocked") is True
            or bool(blockers)
            or _status_is_blocked(status)
        )
        available = payload.get("available") is True or (
            status is not None and not blocked
        )
        natural_language_summaries = _tuple_text(
            payload.get("natural_language_summaries")
        ) or tuple(event.summary for event in events if event.summary)
        return cls(
            provider_key=resolved_provider_key,
            status=status,
            reason=_optional_text(payload.get("reason")),
            provider_report_kind=_optional_text(payload.get("report_kind")),
            provider_report_contract_version=_optional_text(
                payload.get("contract_version")
            ),
            provider_report_source=_optional_text(payload.get("source")),
            semantic_dirty_diff_status=_optional_text(
                payload.get("semantic_dirty_diff_status")
            ),
            semantic_dirty_diff_reason=_optional_text(
                payload.get("semantic_dirty_diff_reason")
            ),
            typed_operation_status=(
                _optional_text(payload.get("provider_delta_typed_operation_status"))
                or _optional_text(payload.get("typed_operation_plan_status"))
            ),
            current_delta_fingerprint=_optional_text(
                payload.get("current_delta_fingerprint")
            ),
            baseline_refs=_mapping_value(payload.get("baseline_refs")),
            head_refs=_mapping_value(payload.get("head_refs")),
            events=events,
            readable_event_chain=chain,
            natural_language_summaries=natural_language_summaries,
            available=available,
            blocked=blocked,
            blockers=blockers,
            provider_payload={str(key): value for key, value in payload.items()},
        )

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def ready(self) -> bool:
        return self.available and not self.blocked

    def evidence_payload(self) -> dict[str, object]:
        return {
            "report_kind": "semantic_provider_delta_event_report",
            "contract_version": SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION,
            "provider_key": self.provider_key,
            "status": self.status,
            "reason": self.reason,
            "provider_report_kind": self.provider_report_kind,
            "provider_report_contract_version": self.provider_report_contract_version,
            "provider_report_source": self.provider_report_source,
            "semantic_dirty_diff_status": self.semantic_dirty_diff_status,
            "semantic_dirty_diff_reason": self.semantic_dirty_diff_reason,
            "typed_operation_status": self.typed_operation_status,
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "baseline_refs": dict(self.baseline_refs),
            "head_refs": dict(self.head_refs),
            "event_count": self.event_count,
            "events": tuple(event.evidence_payload() for event in self.events),
            "readable_semantic_event_chain": (
                self.readable_event_chain.evidence_payload()
            ),
            "natural_language_summaries": self.natural_language_summaries,
            "available": self.available,
            "blocked": self.blocked,
            "blockers": self.blockers,
            "provider_payload": dict(self.provider_payload),
        }


def semantic_provider_delta_events_from_payloads(
    payloads: object,
    *,
    provider_key: str,
) -> tuple[SemanticProviderDeltaEvent, ...]:
    events: list[SemanticProviderDeltaEvent] = []
    for payload in _sequence(payloads):
        if not isinstance(payload, Mapping):
            continue
        event = SemanticProviderDeltaEvent.from_payload(
            payload,
            provider_key=provider_key,
        )
        if event is not None:
            events.append(event)
    return tuple(events)


def _events_from_payload(
    *,
    payload: Mapping[str, object],
    provider_key: str,
) -> tuple[SemanticProviderDeltaEvent, ...]:
    for field_name in (
        "semantic_world_change_events",
        "events",
        "materialization_events",
    ):
        events = semantic_provider_delta_events_from_payloads(
            payload.get(field_name),
            provider_key=provider_key,
        )
        if events:
            return events
    return ()


def _readable_chain_payload(payload: Mapping[str, object]) -> dict[str, object]:
    for field_name in (
        "readable_semantic_event_chain",
        "minimal_readable_semantic_event_chain",
        "readable_materialization_event_chain",
    ):
        value = payload.get(field_name)
        if isinstance(value, Mapping):
            return {str(key): item for key, item in value.items()}
    return {}


def _status_is_blocked(status: str | None) -> bool:
    if status is None:
        return False
    return status.endswith("_blocked") or status.endswith("_failed")


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    return ()


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        return ()
    items: list[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            items.append(text)
    return tuple(items)


def _optional_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0


__all__ = [
    "SEMANTIC_PROVIDER_DELTA_EVENT_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_READABLE_EVENT_CHAIN_CONTRACT_VERSION",
    "SemanticProviderDeltaEvent",
    "SemanticProviderDeltaEventReport",
    "SemanticProviderDeltaReadableEventChain",
    "semantic_provider_delta_events_from_payloads",
]
