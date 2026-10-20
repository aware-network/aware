"""Neutral temporal authority for Goal Lane Phase lifecycle transitions.

The values in this module are runtime-neutral.  They neither parse Goal
Markdown nor infer time from Issues, Git, the filesystem, or the clock.  An
occurrence is immutable authority evidence; a ledger and its observation own
coverage/currentness; repository publication is a separate compound effect.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import TypeVar, cast

from .identity import fingerprint, required_token
from .phase_contracts import GoalLanePhase, GoalLanePhaseState, GoalPhaseCoordinate
from .phase_publication import (
    GoalPhaseProjectionRevisionV1,
    bind_goal_phase_publication,
)

GOAL_PHASE_OCCURRENCE_SCHEMA = "aware.goal.phase-transition-occurrence.v1"
GOAL_PHASE_SUPERSESSION_SCHEMA = "aware.goal.phase-transition-supersession.v1"
GOAL_PHASE_TEMPORAL_ORIGIN_SCHEMA = "aware.goal.phase-temporal-origin.v1"
GOAL_PHASE_TEMPORAL_LEDGER_SCHEMA = "aware.goal.phase-temporal-ledger.v1"
GOAL_PHASE_TEMPORAL_OBSERVATION_SCHEMA = "aware.goal.phase-temporal-observation.v1"
GOAL_PHASE_TEMPORAL_OBSERVATION_AUTHORITY_SCHEMA = (
    "aware.goal.phase-temporal-observation-authority.v1"
)
GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA = "aware.goal.phase-temporal-publication.v1"

_UTC = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    + r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$"
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_ACCEPTANCE = re.compile(r"^goal-phase-acceptance:sha256:[0-9a-f]{64}$")
_REPOSITORY_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class GoalPhaseTemporalError(ValueError):
    """Temporal input violates the O7 authority contract."""


class GoalPhaseHistoryCoverage(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


class GoalPhaseTransitionFactAvailability(StrEnum):
    PRESENT = "present"
    NOT_OCCURRED = "not_occurred"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


class GoalPhaseTransitionSelectorKind(StrEnum):
    BY_SLOT = "by_slot"
    FIRST_ENTRY = "first_entry"
    LATEST_ENTRY = "latest_entry"
    TERMINAL_ACCEPTANCE = "terminal_acceptance"


class GoalPhaseTemporalCurrentness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class GoalPhaseTemporalObservationAuthorityKind(StrEnum):
    H4 = "h4"
    ADMITTED_O7 = "admitted_o7"


class GoalPhaseTemporalPublicationState(StrEnum):
    REPOSITORY_PUBLISHED = "repository_published"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class GoalPhaseTemporalPublicationProfile(StrEnum):
    NORMAL_TRANSITION = "normal_transition"
    CORRECTION = "correction"


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, str]:
    _exact(value, GoalPhaseCoordinate, "coordinate")
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _coordinate(raw: object) -> GoalPhaseCoordinate:
    value = _mapping(raw, "coordinate")
    _keys(value, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        _string(value["goal_tag"], "goal_tag"),
        _string(value["lane_key"], "lane_key"),
        _string(value["phase_key"], "phase_key"),
    )


def _phase_binding(phase: GoalLanePhase) -> str:
    revision = GoalPhaseProjectionRevisionV1(
        repository_ref="refs/neutral/phase-binding",
        repository_commit="neutral:phase-binding",
        phase_blob_oid="neutral:phase-binding",
        source_sha256="sha256:" + "0" * 64,
    )
    binding = bind_goal_phase_publication(phase, projection_revision=revision)
    return fingerprint(
        {
            "schema_id": "aware.goal.phase-semantic-binding.v1",
            "coordinate": _coordinate_wire(phase.coordinate),
            "direction_digest": binding.direction_digest,
            "gate_digest": binding.gate_digest,
            "work_association_digest": binding.work_association_digest,
        }
    )


def goal_phase_temporal_phase_binding_digest(phase: GoalLanePhase) -> str:
    """Return the exact neutral Phase binding used by temporal authority."""

    _exact(phase, GoalLanePhase, "phase")
    return _phase_binding(phase)


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTransitionOccurrenceV1:
    coordinate: GoalPhaseCoordinate
    slot_ordinal: int
    predecessor_slot_ref: str | None
    from_state: GoalLanePhaseState
    to_state: GoalLanePhaseState
    effective_at: str
    recorded_at: str
    authority_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    transition_slot_ref: str = field(init=False)
    occurrence_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_OCCURRENCE_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTransitionOccurrenceV1:
            raise TypeError("occurrence type must be exact")
        if self.schema_id != GOAL_PHASE_OCCURRENCE_SCHEMA:
            raise GoalPhaseTemporalError("unsupported occurrence schema")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        ordinal = _nonnegative_int(self.slot_ordinal, "slot_ordinal")
        predecessor = _optional_domain(
            self.predecessor_slot_ref,
            "goal-phase-transition-slot",
            "predecessor_slot_ref",
        )
        _exact(self.from_state, GoalLanePhaseState, "from_state")
        _exact(self.to_state, GoalLanePhaseState, "to_state")
        if self.from_state is self.to_state:
            raise GoalPhaseTemporalError("transition must change Phase state")
        if self.from_state in (GoalLanePhaseState.ACCEPTED, GoalLanePhaseState.WITHDRAWN):
            raise GoalPhaseTemporalError("terminal Phase state cannot transition")
        permitted = {
            GoalLanePhaseState.PLANNED: {
                GoalLanePhaseState.ACTIVE,
                GoalLanePhaseState.WITHDRAWN,
            },
            GoalLanePhaseState.ACTIVE: {
                GoalLanePhaseState.HELD,
                GoalLanePhaseState.ACCEPTED,
                GoalLanePhaseState.WITHDRAWN,
            },
            GoalLanePhaseState.HELD: {
                GoalLanePhaseState.ACTIVE,
                GoalLanePhaseState.ACCEPTED,
                GoalLanePhaseState.WITHDRAWN,
            },
        }
        if self.to_state not in permitted[self.from_state]:
            raise GoalPhaseTemporalError("Phase lifecycle transition is not permitted")
        effective = _utc(self.effective_at, "effective_at")
        recorded = _utc(self.recorded_at, "recorded_at")
        if effective > recorded:
            raise GoalPhaseTemporalError("effective_at cannot follow recorded_at")
        authority = _tokens(self.authority_refs, "authority_refs", nonempty=True)
        source = _tokens(self.source_refs, "source_refs", nonempty=True)
        evidence = _tokens(self.evidence_refs, "evidence_refs", nonempty=True)
        if any(item.startswith("goal-phase-temporal-publication:") for item in authority):
            raise GoalPhaseTemporalError(
                "occurrence cannot include its post-publication receipt"
            )
        acceptance = tuple(item for item in authority if _ACCEPTANCE.fullmatch(item))
        if self.to_state is GoalLanePhaseState.ACCEPTED and len(acceptance) != 1:
            raise GoalPhaseTemporalError(
                "accepted transition requires one qualified acceptance receipt"
            )
        if self.to_state is not GoalLanePhaseState.ACCEPTED and acceptance:
            raise GoalPhaseTemporalError(
                "non-accepted transition cannot carry acceptance receipt"
            )
        slot_body = {
            "coordinate": _coordinate_wire(self.coordinate),
            "slot_ordinal": ordinal,
            "predecessor_slot_ref": predecessor,
        }
        slot_ref = "goal-phase-transition-slot:" + fingerprint(slot_body)
        body = {
            "schema_id": self.schema_id,
            **slot_body,
            "transition_slot_ref": slot_ref,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "effective_at": effective,
            "recorded_at": recorded,
            "authority_refs": list(authority),
            "source_refs": list(source),
            "evidence_refs": list(evidence),
        }
        object.__setattr__(self, "authority_refs", authority)
        object.__setattr__(self, "source_refs", source)
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "transition_slot_ref", slot_ref)
        object.__setattr__(self, "occurrence_ref", "goal-phase-occurrence:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "slot_ordinal": self.slot_ordinal,
            "predecessor_slot_ref": self.predecessor_slot_ref,
            "transition_slot_ref": self.transition_slot_ref,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "effective_at": self.effective_at,
            "recorded_at": self.recorded_at,
            "authority_refs": list(self.authority_refs),
            "source_refs": list(self.source_refs),
            "evidence_refs": list(self.evidence_refs),
            "occurrence_ref": self.occurrence_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTransitionSupersessionV1:
    superseded_occurrence_ref: str
    replacement: GoalLanePhaseTransitionOccurrenceV1
    reason: str
    admitted_at: str
    authority_refs: tuple[str, ...]
    downstream_revalidation_refs: tuple[str, ...] = ()
    supersession_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_SUPERSESSION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTransitionSupersessionV1:
            raise TypeError("supersession type must be exact")
        if self.schema_id != GOAL_PHASE_SUPERSESSION_SCHEMA:
            raise GoalPhaseTemporalError("unsupported supersession schema")
        old = _domain(self.superseded_occurrence_ref, "goal-phase-occurrence", "superseded_occurrence_ref")
        _exact(self.replacement, GoalLanePhaseTransitionOccurrenceV1, "replacement")
        if old == self.replacement.occurrence_ref:
            raise GoalPhaseTemporalError("supersession replacement must differ")
        reason = required_token(self.reason, "reason")
        admitted_at = _utc(self.admitted_at, "admitted_at")
        if admitted_at < self.replacement.recorded_at:
            raise GoalPhaseTemporalError(
                "supersession authority admission precedes replacement admission"
            )
        authority = _tokens(self.authority_refs, "authority_refs", nonempty=True)
        downstream = _tokens(self.downstream_revalidation_refs, "downstream_revalidation_refs")
        body = {
            "schema_id": self.schema_id,
            "superseded_occurrence_ref": old,
            "replacement_occurrence_ref": self.replacement.occurrence_ref,
            "transition_slot_ref": self.replacement.transition_slot_ref,
            "reason": reason,
            "admitted_at": admitted_at,
            "authority_refs": list(authority),
            "downstream_revalidation_refs": list(downstream),
        }
        object.__setattr__(self, "authority_refs", authority)
        object.__setattr__(self, "downstream_revalidation_refs", downstream)
        object.__setattr__(self, "supersession_ref", "goal-phase-supersession:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "superseded_occurrence_ref": self.superseded_occurrence_ref,
            "replacement": self.replacement.to_wire(),
            "reason": self.reason,
            "admitted_at": self.admitted_at,
            "authority_refs": list(self.authority_refs),
            "downstream_revalidation_refs": list(self.downstream_revalidation_refs),
            "supersession_ref": self.supersession_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTemporalOriginV1:
    coordinate: GoalPhaseCoordinate
    initial_state: GoalLanePhaseState
    phase_admission_receipt_ref: str
    admitted_at: str
    phase_binding_digest: str
    repository_revision_ref: str
    origin_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_ORIGIN_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTemporalOriginV1:
            raise TypeError("origin type must be exact")
        if self.schema_id != GOAL_PHASE_TEMPORAL_ORIGIN_SCHEMA:
            raise GoalPhaseTemporalError("unsupported temporal origin schema")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        _exact(self.initial_state, GoalLanePhaseState, "initial_state")
        receipt = required_token(self.phase_admission_receipt_ref, "phase_admission_receipt_ref")
        admitted = _utc(self.admitted_at, "admitted_at")
        binding = _sha256(self.phase_binding_digest, "phase_binding_digest")
        revision = required_token(self.repository_revision_ref, "repository_revision_ref")
        body = {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "initial_state": self.initial_state.value,
            "phase_admission_receipt_ref": receipt,
            "admitted_at": admitted,
            "phase_binding_digest": binding,
            "repository_revision_ref": revision,
        }
        object.__setattr__(self, "origin_ref", "goal-phase-temporal-origin:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "initial_state": self.initial_state.value,
            "phase_admission_receipt_ref": self.phase_admission_receipt_ref,
            "admitted_at": self.admitted_at,
            "phase_binding_digest": self.phase_binding_digest,
            "repository_revision_ref": self.repository_revision_ref,
            "origin_ref": self.origin_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTemporalBoundaryV1:
    phase_binding_digest: str
    ledger_revision: int
    publication_binding_ref: str

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTemporalBoundaryV1:
            raise TypeError("boundary type must be exact")
        object.__setattr__(self, "phase_binding_digest", _sha256(self.phase_binding_digest, "phase_binding_digest"))
        _ = _positive_int(self.ledger_revision, "ledger_revision")
        object.__setattr__(
            self,
            "publication_binding_ref",
            _domain(
                self.publication_binding_ref,
                "goal-phase-temporal-publication-binding",
                "publication_binding_ref",
            ),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "phase_binding_digest": self.phase_binding_digest,
            "ledger_revision": self.ledger_revision,
            "publication_binding_ref": self.publication_binding_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTemporalGapV1:
    first_ordinal: int
    last_ordinal: int
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        first = _nonnegative_int(self.first_ordinal, "first_ordinal")
        last = _nonnegative_int(self.last_ordinal, "last_ordinal")
        if last < first:
            raise GoalPhaseTemporalError("gap ordinal range is inverted")
        object.__setattr__(self, "reason", required_token(self.reason, "reason"))
        object.__setattr__(self, "evidence_refs", _tokens(self.evidence_refs, "evidence_refs"))

    def to_wire(self) -> dict[str, object]:
        return {
            "first_ordinal": self.first_ordinal,
            "last_ordinal": self.last_ordinal,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTemporalLedgerV1:
    coordinate: GoalPhaseCoordinate
    current_phase_binding_digest: str
    origin: GoalLanePhaseTemporalOriginV1
    occurrences: tuple[GoalLanePhaseTransitionOccurrenceV1, ...]
    supersessions: tuple[GoalLanePhaseTransitionSupersessionV1, ...]
    history_coverage: GoalPhaseHistoryCoverage
    coverage_through: GoalLanePhaseTemporalBoundaryV1
    gaps: tuple[GoalLanePhaseTemporalGapV1, ...]
    evidence_refs: tuple[str, ...]
    ledger_digest: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_LEDGER_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTemporalLedgerV1:
            raise TypeError("ledger type must be exact")
        if self.schema_id != GOAL_PHASE_TEMPORAL_LEDGER_SCHEMA:
            raise GoalPhaseTemporalError("unsupported temporal ledger schema")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        binding = _sha256(self.current_phase_binding_digest, "current_phase_binding_digest")
        _exact(self.origin, GoalLanePhaseTemporalOriginV1, "origin")
        _exact(self.history_coverage, GoalPhaseHistoryCoverage, "history_coverage")
        _exact(self.coverage_through, GoalLanePhaseTemporalBoundaryV1, "coverage_through")
        if self.origin.coordinate != self.coordinate:
            raise GoalPhaseTemporalError("origin coordinate differs from ledger")
        if self.coverage_through.phase_binding_digest != binding:
            raise GoalPhaseTemporalError("coverage boundary differs from current Phase")
        occurrences = _exact_tuple(self.occurrences, GoalLanePhaseTransitionOccurrenceV1, "occurrences")
        supersessions = _exact_tuple(self.supersessions, GoalLanePhaseTransitionSupersessionV1, "supersessions")
        gaps = _exact_tuple(self.gaps, GoalLanePhaseTemporalGapV1, "gaps")
        evidence = _tokens(self.evidence_refs, "evidence_refs")
        _validate_ledger_chain(
            coordinate=self.coordinate,
            origin=self.origin,
            occurrences=occurrences,
            supersessions=supersessions,
            coverage=self.history_coverage,
            gaps=gaps,
        )
        body = {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "current_phase_binding_digest": binding,
            "origin": self.origin.to_wire(),
            "occurrences": [item.to_wire() for item in occurrences],
            "supersessions": [item.to_wire() for item in supersessions],
            "history_coverage": self.history_coverage.value,
            "coverage_through": self.coverage_through.to_wire(),
            "gaps": [item.to_wire() for item in gaps],
            "evidence_refs": list(evidence),
        }
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(self, "ledger_digest", fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "current_phase_binding_digest": self.current_phase_binding_digest,
            "origin": self.origin.to_wire(),
            "occurrences": [item.to_wire() for item in self.occurrences],
            "supersessions": [item.to_wire() for item in self.supersessions],
            "history_coverage": self.history_coverage.value,
            "coverage_through": self.coverage_through.to_wire(),
            "gaps": [item.to_wire() for item in self.gaps],
            "evidence_refs": list(self.evidence_refs),
            "ledger_digest": self.ledger_digest,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseTransitionSelectorV1:
    kind: GoalPhaseTransitionSelectorKind
    transition_slot_ref: str | None = None
    target_state: GoalLanePhaseState | None = None

    def __post_init__(self) -> None:
        _exact(self.kind, GoalPhaseTransitionSelectorKind, "kind")
        slot = _optional_domain(self.transition_slot_ref, "goal-phase-transition-slot", "transition_slot_ref")
        if self.kind is GoalPhaseTransitionSelectorKind.BY_SLOT:
            if slot is None or self.target_state is not None:
                raise GoalPhaseTemporalError("by_slot requires only transition_slot_ref")
        elif self.kind in (GoalPhaseTransitionSelectorKind.FIRST_ENTRY, GoalPhaseTransitionSelectorKind.LATEST_ENTRY):
            if slot is not None or self.target_state is None:
                raise GoalPhaseTemporalError("entry selector requires only target_state")
            _exact(self.target_state, GoalLanePhaseState, "target_state")
        elif self.kind is GoalPhaseTransitionSelectorKind.TERMINAL_ACCEPTANCE:
            if slot is not None or self.target_state is not None:
                raise GoalPhaseTemporalError("terminal_acceptance takes no qualifier")

    def to_wire(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "transition_slot_ref": self.transition_slot_ref,
            "target_state": None if self.target_state is None else self.target_state.value,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseTransitionFactV1:
    selector: GoalPhaseTransitionSelectorV1
    availability: GoalPhaseTransitionFactAvailability
    occurrence: GoalLanePhaseTransitionOccurrenceV1 | None
    proof_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _exact(self.selector, GoalPhaseTransitionSelectorV1, "selector")
        _exact(self.availability, GoalPhaseTransitionFactAvailability, "availability")
        if self.availability is GoalPhaseTransitionFactAvailability.PRESENT:
            _exact(self.occurrence, GoalLanePhaseTransitionOccurrenceV1, "occurrence")
        elif self.occurrence is not None:
            raise GoalPhaseTemporalError("non-present fact cannot carry occurrence")
        object.__setattr__(self, "proof_refs", _tokens(self.proof_refs, "proof_refs"))

    def to_wire(self) -> dict[str, object]:
        return {
            "selector": self.selector.to_wire(),
            "availability": self.availability.value,
            "occurrence": None if self.occurrence is None else self.occurrence.to_wire(),
            "proof_refs": list(self.proof_refs),
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalObservationAuthorityV1:
    authority_kind: GoalPhaseTemporalObservationAuthorityKind
    coordinate: GoalPhaseCoordinate
    ledger_digest: str
    phase_binding_digest: str
    coverage_publication_binding_ref: str
    source_revision_ref: str
    snapshot_at: str
    snapshot_receipt_ref: str
    currentness: GoalPhaseTemporalCurrentness
    currentness_receipt_ref: str
    authority_admission_receipt_ref: str
    publication_receipt_ref: str | None
    authority_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_OBSERVATION_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseTemporalObservationAuthorityV1:
            raise TypeError("temporal observation authority type must be exact")
        if self.schema_id != GOAL_PHASE_TEMPORAL_OBSERVATION_AUTHORITY_SCHEMA:
            raise GoalPhaseTemporalError("unsupported observation authority schema")
        _exact(
            self.authority_kind,
            GoalPhaseTemporalObservationAuthorityKind,
            "authority_kind",
        )
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        _ = _sha256(self.ledger_digest, "ledger_digest")
        _ = _sha256(self.phase_binding_digest, "phase_binding_digest")
        binding = _domain(
            self.coverage_publication_binding_ref,
            "goal-phase-temporal-publication-binding",
            "coverage_publication_binding_ref",
        )
        source = _repository_commit_ref(
            self.source_revision_ref, "source_revision_ref"
        )
        snapshot_at = _utc(self.snapshot_at, "snapshot_at")
        snapshot_receipt = _domain(
            self.snapshot_receipt_ref,
            "goal-phase-temporal-snapshot",
            "snapshot_receipt_ref",
        )
        _exact(self.currentness, GoalPhaseTemporalCurrentness, "currentness")
        currentness_receipt = _domain(
            self.currentness_receipt_ref,
            "goal-phase-temporal-currentness",
            "currentness_receipt_ref",
        )
        admission_receipt = _domain(
            self.authority_admission_receipt_ref,
            "goal-temporal-observation-authority-admission",
            "authority_admission_receipt_ref",
        )
        expected_snapshot_receipt = derive_goal_phase_temporal_snapshot_receipt_ref(
            authority_kind=self.authority_kind,
            coordinate=self.coordinate,
            ledger_digest=self.ledger_digest,
            phase_binding_digest=self.phase_binding_digest,
            coverage_publication_binding_ref=binding,
            source_revision_ref=source,
            snapshot_at=snapshot_at,
            authority_admission_receipt_ref=admission_receipt,
        )
        if snapshot_receipt != expected_snapshot_receipt:
            raise GoalPhaseTemporalError(
                "snapshot receipt is not canonically scoped to its authority"
            )
        expected_currentness_receipt = (
            derive_goal_phase_temporal_currentness_receipt_ref(
                authority_kind=self.authority_kind,
                coordinate=self.coordinate,
                ledger_digest=self.ledger_digest,
                phase_binding_digest=self.phase_binding_digest,
                coverage_publication_binding_ref=binding,
                source_revision_ref=source,
                snapshot_receipt_ref=snapshot_receipt,
                currentness=self.currentness,
                authority_admission_receipt_ref=admission_receipt,
            )
        )
        if currentness_receipt != expected_currentness_receipt:
            raise GoalPhaseTemporalError(
                "currentness receipt is not canonically scoped to its authority"
            )
        publication_receipt = _optional_domain(
            self.publication_receipt_ref,
            "goal-phase-temporal-publication",
            "publication_receipt_ref",
        )
        if (
            self.currentness is GoalPhaseTemporalCurrentness.CURRENT
            and publication_receipt is None
        ):
            raise GoalPhaseTemporalError(
                "current observation authority requires publication receipt"
            )
        body = {
            "schema_id": self.schema_id,
            "authority_kind": self.authority_kind.value,
            "coordinate": _coordinate_wire(self.coordinate),
            "ledger_digest": self.ledger_digest,
            "phase_binding_digest": self.phase_binding_digest,
            "coverage_publication_binding_ref": binding,
            "source_revision_ref": source,
            "snapshot_at": snapshot_at,
            "snapshot_receipt_ref": snapshot_receipt,
            "currentness": self.currentness.value,
            "currentness_receipt_ref": currentness_receipt,
            "authority_admission_receipt_ref": admission_receipt,
            "publication_receipt_ref": publication_receipt,
        }
        object.__setattr__(
            self,
            "authority_ref",
            "goal-phase-temporal-observation-authority:" + fingerprint(body),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "authority_kind": self.authority_kind.value,
            "coordinate": _coordinate_wire(self.coordinate),
            "ledger_digest": self.ledger_digest,
            "phase_binding_digest": self.phase_binding_digest,
            "coverage_publication_binding_ref": self.coverage_publication_binding_ref,
            "source_revision_ref": self.source_revision_ref,
            "snapshot_at": self.snapshot_at,
            "snapshot_receipt_ref": self.snapshot_receipt_ref,
            "currentness": self.currentness.value,
            "currentness_receipt_ref": self.currentness_receipt_ref,
            "authority_admission_receipt_ref": self.authority_admission_receipt_ref,
            "publication_receipt_ref": self.publication_receipt_ref,
            "authority_ref": self.authority_ref,
        }


def derive_goal_phase_temporal_snapshot_receipt_ref(
    *,
    authority_kind: GoalPhaseTemporalObservationAuthorityKind,
    coordinate: GoalPhaseCoordinate,
    ledger_digest: str,
    phase_binding_digest: str,
    coverage_publication_binding_ref: str,
    source_revision_ref: str,
    snapshot_at: str,
    authority_admission_receipt_ref: str,
) -> str:
    """Derive an exact qualified temporal snapshot authority receipt."""

    _exact(
        authority_kind,
        GoalPhaseTemporalObservationAuthorityKind,
        "authority_kind",
    )
    body = {
        "schema_id": "aware.goal.phase-temporal-snapshot.v1",
        "authority_kind": authority_kind.value,
        "coordinate": _coordinate_wire(coordinate),
        "ledger_digest": _sha256(ledger_digest, "ledger_digest"),
        "phase_binding_digest": _sha256(
            phase_binding_digest, "phase_binding_digest"
        ),
        "coverage_publication_binding_ref": _domain(
            coverage_publication_binding_ref,
            "goal-phase-temporal-publication-binding",
            "coverage_publication_binding_ref",
        ),
        "source_revision_ref": _repository_commit_ref(
            source_revision_ref, "source_revision_ref"
        ),
        "snapshot_at": _utc(snapshot_at, "snapshot_at"),
        "authority_admission_receipt_ref": _domain(
            authority_admission_receipt_ref,
            "goal-temporal-observation-authority-admission",
            "authority_admission_receipt_ref",
        ),
    }
    return "goal-phase-temporal-snapshot:" + fingerprint(body)


def derive_goal_phase_temporal_currentness_receipt_ref(
    *,
    authority_kind: GoalPhaseTemporalObservationAuthorityKind,
    coordinate: GoalPhaseCoordinate,
    ledger_digest: str,
    phase_binding_digest: str,
    coverage_publication_binding_ref: str,
    source_revision_ref: str,
    snapshot_receipt_ref: str,
    currentness: GoalPhaseTemporalCurrentness,
    authority_admission_receipt_ref: str,
) -> str:
    """Derive currentness evidence scoped to one admitted temporal snapshot."""

    _exact(
        authority_kind,
        GoalPhaseTemporalObservationAuthorityKind,
        "authority_kind",
    )
    _exact(currentness, GoalPhaseTemporalCurrentness, "currentness")
    body = {
        "schema_id": "aware.goal.phase-temporal-currentness.v1",
        "authority_kind": authority_kind.value,
        "coordinate": _coordinate_wire(coordinate),
        "ledger_digest": _sha256(ledger_digest, "ledger_digest"),
        "phase_binding_digest": _sha256(
            phase_binding_digest, "phase_binding_digest"
        ),
        "coverage_publication_binding_ref": _domain(
            coverage_publication_binding_ref,
            "goal-phase-temporal-publication-binding",
            "coverage_publication_binding_ref",
        ),
        "source_revision_ref": _repository_commit_ref(
            source_revision_ref, "source_revision_ref"
        ),
        "snapshot_receipt_ref": _domain(
            snapshot_receipt_ref,
            "goal-phase-temporal-snapshot",
            "snapshot_receipt_ref",
        ),
        "currentness": currentness.value,
        "authority_admission_receipt_ref": _domain(
            authority_admission_receipt_ref,
            "goal-temporal-observation-authority-admission",
            "authority_admission_receipt_ref",
        ),
    }
    return "goal-phase-temporal-currentness:" + fingerprint(body)


@dataclass(frozen=True, slots=True)
class GoalLanePhaseTemporalObservationV1:
    coordinate: GoalPhaseCoordinate
    ledger_digest: str
    origin_ref: str
    phase_binding_digest: str
    ledger_revision: int
    coverage_publication_binding_ref: str
    source_revision_ref: str
    snapshot_at: str
    currentness: GoalPhaseTemporalCurrentness
    currentness_ref: str
    observation_authority_ref: str
    history_coverage: GoalPhaseHistoryCoverage
    gaps: tuple[GoalLanePhaseTemporalGapV1, ...]
    facts: tuple[GoalPhaseTransitionFactV1, ...]
    gap_count: int
    observation_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_OBSERVATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalLanePhaseTemporalObservationV1:
            raise TypeError("temporal observation type must be exact")
        if self.schema_id != GOAL_PHASE_TEMPORAL_OBSERVATION_SCHEMA:
            raise GoalPhaseTemporalError("unsupported temporal observation schema")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        _ = _sha256(self.ledger_digest, "ledger_digest")
        _ = _domain(self.origin_ref, "goal-phase-temporal-origin", "origin_ref")
        _ = _sha256(self.phase_binding_digest, "phase_binding_digest")
        _ = _positive_int(self.ledger_revision, "ledger_revision")
        object.__setattr__(
            self,
            "coverage_publication_binding_ref",
            _domain(
                self.coverage_publication_binding_ref,
                "goal-phase-temporal-publication-binding",
                "coverage_publication_binding_ref",
            ),
        )
        object.__setattr__(
            self,
            "source_revision_ref",
            _repository_commit_ref(
                self.source_revision_ref, "source_revision_ref"
            ),
        )
        _ = _utc(self.snapshot_at, "snapshot_at")
        _exact(self.currentness, GoalPhaseTemporalCurrentness, "currentness")
        object.__setattr__(
            self,
            "currentness_ref",
            _domain(
                self.currentness_ref,
                "goal-phase-temporal-currentness",
                "currentness_ref",
            ),
        )
        object.__setattr__(
            self,
            "observation_authority_ref",
            _domain(
                self.observation_authority_ref,
                "goal-phase-temporal-observation-authority",
                "observation_authority_ref",
            ),
        )
        _exact(self.history_coverage, GoalPhaseHistoryCoverage, "history_coverage")
        gaps = _exact_tuple(self.gaps, GoalLanePhaseTemporalGapV1, "gaps")
        facts = _exact_tuple(self.facts, GoalPhaseTransitionFactV1, "facts")
        _ = _nonnegative_int(self.gap_count, "gap_count")
        if self.gap_count != len(gaps):
            raise GoalPhaseTemporalError("gap_count is not freshly derived")
        body = {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "ledger_digest": self.ledger_digest,
            "origin_ref": self.origin_ref,
            "phase_binding_digest": self.phase_binding_digest,
            "ledger_revision": self.ledger_revision,
            "coverage_publication_binding_ref": self.coverage_publication_binding_ref,
            "source_revision_ref": self.source_revision_ref,
            "snapshot_at": self.snapshot_at,
            "currentness": self.currentness.value,
            "currentness_ref": self.currentness_ref,
            "observation_authority_ref": self.observation_authority_ref,
            "history_coverage": self.history_coverage.value,
            "gaps": [item.to_wire() for item in gaps],
            "facts": [item.to_wire() for item in facts],
            "gap_count": self.gap_count,
        }
        object.__setattr__(self, "observation_ref", "goal-phase-temporal-observation:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "ledger_digest": self.ledger_digest,
            "origin_ref": self.origin_ref,
            "phase_binding_digest": self.phase_binding_digest,
            "ledger_revision": self.ledger_revision,
            "coverage_publication_binding_ref": self.coverage_publication_binding_ref,
            "source_revision_ref": self.source_revision_ref,
            "snapshot_at": self.snapshot_at,
            "currentness": self.currentness.value,
            "currentness_ref": self.currentness_ref,
            "observation_authority_ref": self.observation_authority_ref,
            "history_coverage": self.history_coverage.value,
            "gaps": [item.to_wire() for item in self.gaps],
            "facts": [item.to_wire() for item in self.facts],
            "gap_count": self.gap_count,
            "observation_ref": self.observation_ref,
        }


def observe_goal_phase_temporal_facts(
    *,
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
    selectors: tuple[GoalPhaseTransitionSelectorV1, ...],
    authority: GoalPhaseTemporalObservationAuthorityV1,
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1 | None = None,
) -> GoalLanePhaseTemporalObservationV1:
    """Evaluate exact selectors without manufacturing missing history."""

    validate_goal_phase_temporal_ledger(phase=phase, ledger=ledger)
    _validate_temporal_observation_authority(
        phase=phase,
        ledger=ledger,
        authority=authority,
        publication_receipt=publication_receipt,
    )
    selections = _exact_tuple(selectors, GoalPhaseTransitionSelectorV1, "selectors")
    tips = _effective_occurrences(ledger.occurrences, ledger.supersessions)
    facts = tuple(_select_fact(ledger, tips, selector) for selector in selections)
    return GoalLanePhaseTemporalObservationV1(
        coordinate=ledger.coordinate,
        ledger_digest=ledger.ledger_digest,
        origin_ref=ledger.origin.origin_ref,
        phase_binding_digest=ledger.current_phase_binding_digest,
        ledger_revision=ledger.coverage_through.ledger_revision,
        coverage_publication_binding_ref=(
            ledger.coverage_through.publication_binding_ref
        ),
        source_revision_ref=authority.source_revision_ref,
        snapshot_at=authority.snapshot_at,
        currentness=authority.currentness,
        currentness_ref=authority.currentness_receipt_ref,
        observation_authority_ref=authority.authority_ref,
        history_coverage=ledger.history_coverage,
        gaps=ledger.gaps,
        facts=facts,
        gap_count=len(ledger.gaps),
    )


def _validate_temporal_observation_authority(
    *,
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
    authority: GoalPhaseTemporalObservationAuthorityV1,
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1 | None,
) -> None:
    _exact(
        authority,
        GoalPhaseTemporalObservationAuthorityV1,
        "observation_authority",
    )
    if (
        authority.coordinate != phase.coordinate
        or authority.ledger_digest != ledger.ledger_digest
        or authority.phase_binding_digest != _phase_binding(phase)
        or authority.coverage_publication_binding_ref
        != ledger.coverage_through.publication_binding_ref
    ):
        raise GoalPhaseTemporalError(
            "observation authority is detached from Phase or ledger"
        )
    if publication_receipt is not None:
        verify_goal_phase_temporal_publication_receipt(
            receipt=publication_receipt,
            phase=phase,
            ledger=ledger,
        )
        if (
            authority.publication_receipt_ref != publication_receipt.receipt_ref
            or authority.source_revision_ref
            != publication_receipt.repository_commit_ref
        ):
            raise GoalPhaseTemporalError(
                "observation authority source differs from publication receipt"
            )
    elif authority.currentness is GoalPhaseTemporalCurrentness.CURRENT:
        raise GoalPhaseTemporalError(
            "current observation requires independently supplied publication receipt"
        )


def validate_goal_phase_temporal_ledger(
    *, phase: GoalLanePhase, ledger: GoalLanePhaseTemporalLedgerV1
) -> None:
    """Bind one ledger to its supplied Phase and prove complete-chain state."""

    _exact(phase, GoalLanePhase, "phase")
    _exact(ledger, GoalLanePhaseTemporalLedgerV1, "ledger")
    if phase.coordinate != ledger.coordinate:
        raise GoalPhaseTemporalError("ledger coordinate differs from Phase")
    if ledger.current_phase_binding_digest != _phase_binding(phase):
        raise GoalPhaseTemporalError("ledger is detached from supplied Phase")
    if ledger.history_coverage is GoalPhaseHistoryCoverage.COMPLETE:
        tips = _effective_occurrences(ledger.occurrences, ledger.supersessions)
        final_state = ledger.origin.initial_state if not tips else tips[-1].to_state
        if final_state is not phase.state:
            raise GoalPhaseTemporalError(
                "complete ledger terminal state differs from supplied Phase"
            )


def derive_goal_phase_temporal_publication_binding(
    *,
    coordinate: GoalPhaseCoordinate,
    publication_profile: GoalPhaseTemporalPublicationProfile,
    phase_binding_digest: str,
    prior_ledger_digest: str,
    ledger_revision: int,
    appended_occurrence_refs: tuple[str, ...],
    appended_supersession_refs: tuple[str, ...],
    phase_path: str,
    ledger_path: str,
) -> str:
    """Derive the content-stable binding later resolved by a commit receipt."""

    _exact(coordinate, GoalPhaseCoordinate, "coordinate")
    _exact(
        publication_profile,
        GoalPhaseTemporalPublicationProfile,
        "publication_profile",
    )
    phase_digest = _sha256(phase_binding_digest, "phase_binding_digest")
    prior_digest = _sha256(prior_ledger_digest, "prior_ledger_digest")
    revision = _positive_int(ledger_revision, "ledger_revision")
    occurrence_refs = _domain_ref_sequence(
        appended_occurrence_refs,
        "goal-phase-occurrence",
        "appended_occurrence_refs",
    )
    supersession_refs = _domain_ref_sequence(
        appended_supersession_refs,
        "goal-phase-supersession",
        "appended_supersession_refs",
    )
    if not occurrence_refs:
        raise GoalPhaseTemporalError("publication binding needs occurrences")
    if (
        publication_profile is GoalPhaseTemporalPublicationProfile.CORRECTION
        and not supersession_refs
    ):
        raise GoalPhaseTemporalError("correction binding needs supersessions")
    normalized_phase_path = required_token(phase_path, "phase_path")
    normalized_ledger_path = required_token(ledger_path, "ledger_path")
    if normalized_phase_path == normalized_ledger_path:
        raise GoalPhaseTemporalError("publication binding requires two paths")
    body = {
        "schema_id": "aware.goal.phase-temporal-publication-binding.v1",
        "coordinate": _coordinate_wire(coordinate),
        "publication_profile": publication_profile.value,
        "phase_binding_digest": phase_digest,
        "prior_ledger_digest": prior_digest,
        "ledger_revision": revision,
        "appended_occurrence_refs": list(occurrence_refs),
        "appended_supersession_refs": list(supersession_refs),
        "phase_path": normalized_phase_path,
        "ledger_path": normalized_ledger_path,
    }
    return "goal-phase-temporal-publication-binding:" + fingerprint(body)


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalPublicationPlanV1:
    publication_profile: GoalPhaseTemporalPublicationProfile
    before_phase: GoalLanePhase
    after_phase: GoalLanePhase
    before_ledger: GoalLanePhaseTemporalLedgerV1
    after_ledger: GoalLanePhaseTemporalLedgerV1
    appended_occurrence_refs: tuple[str, ...]
    appended_supersession_refs: tuple[str, ...]
    publication_binding_ref: str
    expected_repository_revision_ref: str
    phase_path: str
    ledger_path: str
    evidence_refs: tuple[str, ...]
    semantic_intent_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA:
            raise GoalPhaseTemporalError("unsupported temporal publication schema")
        _validate_temporal_plan(self)
        body = _temporal_plan_body(self)
        object.__setattr__(self, "semantic_intent_ref", "goal-phase-temporal-intent:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {**_temporal_plan_body(self), "semantic_intent_ref": self.semantic_intent_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalPublicationReceiptV1:
    plan: GoalPhaseTemporalPublicationPlanV1
    repository_commit_receipt_ref: str
    repository_commit_ref: str
    publication_state: GoalPhaseTemporalPublicationState
    reconciliation_reason_codes: tuple[str, ...]
    receipt_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseTemporalPublicationReceiptV1:
            raise TypeError("temporal publication receipt type must be exact")
        if self.schema_id != GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA:
            raise GoalPhaseTemporalError("unsupported temporal publication schema")
        _exact(self.plan, GoalPhaseTemporalPublicationPlanV1, "plan")
        _validate_temporal_plan(self.plan)
        commit = required_token(self.repository_commit_ref, "repository_commit_ref")
        if _REPOSITORY_COMMIT.fullmatch(commit) is None:
            raise GoalPhaseTemporalError(
                "repository_commit_ref must be an exact Git object id"
            )
        commit_receipt = required_token(
            self.repository_commit_receipt_ref, "repository_commit_receipt_ref"
        )
        if commit_receipt != f"repository-commit:{commit}":
            raise GoalPhaseTemporalError(
                "repository commit receipt must resolve the exact committed revision"
            )
        _exact(self.publication_state, GoalPhaseTemporalPublicationState, "publication_state")
        reasons = _tokens(self.reconciliation_reason_codes, "reconciliation_reason_codes")
        if self.publication_state is GoalPhaseTemporalPublicationState.RECONCILIATION_REQUIRED and not reasons:
            raise GoalPhaseTemporalError("reconciliation_required needs typed reason")
        if self.publication_state is GoalPhaseTemporalPublicationState.REPOSITORY_PUBLISHED and reasons:
            raise GoalPhaseTemporalError("published receipt cannot carry reconciliation reasons")
        body = {
            "schema_id": self.schema_id,
            "plan_ref": self.plan.semantic_intent_ref,
            "publication_binding_ref": self.plan.publication_binding_ref,
            "phase_postimage_digest": _phase_binding(self.plan.after_phase),
            "ledger_postimage_digest": self.plan.after_ledger.ledger_digest,
            "repository_commit_receipt_ref": commit_receipt,
            "repository_commit_ref": commit,
            "changed_paths": list(_temporal_changed_paths(self.plan)),
            "publication_state": self.publication_state.value,
            "reconciliation_reason_codes": list(reasons),
        }
        object.__setattr__(self, "reconciliation_reason_codes", reasons)
        object.__setattr__(self, "receipt_ref", "goal-phase-temporal-publication:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "repository_publication",
            "plan_ref": self.plan.semantic_intent_ref,
            "publication_binding_ref": self.plan.publication_binding_ref,
            "phase_postimage_digest": _phase_binding(self.plan.after_phase),
            "ledger_postimage_digest": self.plan.after_ledger.ledger_digest,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "repository_commit_ref": self.repository_commit_ref,
            "changed_paths": list(_temporal_changed_paths(self.plan)),
            "publication_state": self.publication_state.value,
            "reconciliation_reason_codes": list(self.reconciliation_reason_codes),
            "receipt_ref": self.receipt_ref,
        }


def verify_goal_phase_temporal_publication_receipt(
    *,
    receipt: GoalPhaseTemporalPublicationReceiptV1,
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
) -> None:
    """Verify one external commit receipt resolves the content-stable binding."""

    _exact(receipt, GoalPhaseTemporalPublicationReceiptV1, "publication_receipt")
    _validate_temporal_plan(receipt.plan)
    validate_goal_phase_temporal_ledger(phase=phase, ledger=ledger)
    if receipt.plan.after_phase != phase or receipt.plan.after_ledger != ledger:
        raise GoalPhaseTemporalError(
            "publication receipt postimages differ from supplied authority"
        )
    if (
        receipt.plan.publication_binding_ref
        != ledger.coverage_through.publication_binding_ref
    ):
        raise GoalPhaseTemporalError(
            "publication receipt does not resolve coverage binding"
        )


def _temporal_changed_paths(
    plan: GoalPhaseTemporalPublicationPlanV1,
) -> tuple[str, ...]:
    """Return exact repository paths whose bytes change for this profile."""

    paths = [plan.ledger_path]
    if plan.before_phase != plan.after_phase:
        paths.append(plan.phase_path)
    return tuple(sorted(paths))


def encode_goal_phase_temporal_ledger(value: GoalLanePhaseTemporalLedgerV1) -> bytes:
    _exact(value, GoalLanePhaseTemporalLedgerV1, "ledger")
    return _canonical_json(value.to_wire())


def decode_goal_phase_temporal_ledger(
    payload: bytes, *, phase: GoalLanePhase
) -> GoalLanePhaseTemporalLedgerV1:
    raw = _json_object(payload, "ledger")
    value = _ledger_from_wire(raw)
    if not _exact_tree(raw, value.to_wire()):
        raise GoalPhaseTemporalError("ledger payload is not canonical")
    validate_goal_phase_temporal_ledger(phase=phase, ledger=value)
    return value


def encode_goal_phase_temporal_observation(value: GoalLanePhaseTemporalObservationV1) -> bytes:
    _exact(value, GoalLanePhaseTemporalObservationV1, "observation")
    return _canonical_json(value.to_wire())


def encode_goal_phase_temporal_observation_authority(
    value: GoalPhaseTemporalObservationAuthorityV1,
) -> bytes:
    _exact(value, GoalPhaseTemporalObservationAuthorityV1, "observation_authority")
    return _canonical_json(value.to_wire())


def decode_goal_phase_temporal_observation_authority(
    payload: bytes,
) -> GoalPhaseTemporalObservationAuthorityV1:
    raw = _json_object(payload, "observation_authority")
    _keys(
        raw,
        {
            "schema_id",
            "authority_kind",
            "coordinate",
            "ledger_digest",
            "phase_binding_digest",
            "coverage_publication_binding_ref",
            "source_revision_ref",
            "snapshot_at",
            "snapshot_receipt_ref",
            "currentness",
            "currentness_receipt_ref",
            "authority_admission_receipt_ref",
            "publication_receipt_ref",
            "authority_ref",
        },
        "observation_authority",
    )
    authority = GoalPhaseTemporalObservationAuthorityV1(
        authority_kind=GoalPhaseTemporalObservationAuthorityKind(
            _string(raw["authority_kind"], "authority_kind")
        ),
        coordinate=_coordinate(raw["coordinate"]),
        ledger_digest=_string(raw["ledger_digest"], "ledger_digest"),
        phase_binding_digest=_string(
            raw["phase_binding_digest"], "phase_binding_digest"
        ),
        coverage_publication_binding_ref=_string(
            raw["coverage_publication_binding_ref"],
            "coverage_publication_binding_ref",
        ),
        source_revision_ref=_string(
            raw["source_revision_ref"], "source_revision_ref"
        ),
        snapshot_at=_string(raw["snapshot_at"], "snapshot_at"),
        snapshot_receipt_ref=_string(
            raw["snapshot_receipt_ref"], "snapshot_receipt_ref"
        ),
        currentness=GoalPhaseTemporalCurrentness(
            _string(raw["currentness"], "currentness")
        ),
        currentness_receipt_ref=_string(
            raw["currentness_receipt_ref"], "currentness_receipt_ref"
        ),
        authority_admission_receipt_ref=_string(
            raw["authority_admission_receipt_ref"],
            "authority_admission_receipt_ref",
        ),
        publication_receipt_ref=_optional_string(
            raw["publication_receipt_ref"], "publication_receipt_ref"
        ),
    )
    if not _exact_tree(raw, authority.to_wire()):
        raise GoalPhaseTemporalError("observation authority is not canonical")
    return authority


def encode_goal_phase_temporal_publication_receipt(
    value: GoalPhaseTemporalPublicationReceiptV1,
) -> bytes:
    _exact(value, GoalPhaseTemporalPublicationReceiptV1, "publication_receipt")
    return _canonical_json(value.to_wire())


def decode_goal_phase_temporal_publication_receipt(
    payload: bytes, *, plan: GoalPhaseTemporalPublicationPlanV1
) -> GoalPhaseTemporalPublicationReceiptV1:
    raw = _json_object(payload, "publication_receipt")
    _keys(
        raw,
        {
            "schema_id",
            "effect_profile",
            "plan_ref",
            "publication_binding_ref",
            "phase_postimage_digest",
            "ledger_postimage_digest",
            "repository_commit_receipt_ref",
            "repository_commit_ref",
            "changed_paths",
            "publication_state",
            "reconciliation_reason_codes",
            "receipt_ref",
        },
        "publication_receipt",
    )
    receipt = GoalPhaseTemporalPublicationReceiptV1(
        plan=plan,
        repository_commit_receipt_ref=_string(
            raw["repository_commit_receipt_ref"],
            "repository_commit_receipt_ref",
        ),
        repository_commit_ref=_string(
            raw["repository_commit_ref"], "repository_commit_ref"
        ),
        publication_state=GoalPhaseTemporalPublicationState(
            _string(raw["publication_state"], "publication_state")
        ),
        reconciliation_reason_codes=_strings(
            raw["reconciliation_reason_codes"], "reconciliation_reason_codes"
        ),
    )
    if not _exact_tree(raw, receipt.to_wire()):
        raise GoalPhaseTemporalError(
            "publication receipt differs from plan or committed effect"
        )
    return receipt


def decode_goal_phase_temporal_observation(
    payload: bytes,
    *,
    phase: GoalLanePhase,
    ledger: GoalLanePhaseTemporalLedgerV1,
    authority: GoalPhaseTemporalObservationAuthorityV1,
    publication_receipt: GoalPhaseTemporalPublicationReceiptV1 | None = None,
) -> GoalLanePhaseTemporalObservationV1:
    raw = _json_object(payload, "observation")
    value = _observation_from_wire(raw)
    if not _exact_tree(raw, value.to_wire()):
        raise GoalPhaseTemporalError("observation payload is not canonical")
    selectors = tuple(item.selector for item in value.facts)
    canonical = observe_goal_phase_temporal_facts(
        phase=phase,
        ledger=ledger,
        selectors=selectors,
        authority=authority,
        publication_receipt=publication_receipt,
    )
    if value != canonical:
        raise GoalPhaseTemporalError(
            "observation facts are not derived from supplied temporal authority"
        )
    return canonical


def _validate_temporal_plan(plan: GoalPhaseTemporalPublicationPlanV1) -> None:
    if type(plan) is not GoalPhaseTemporalPublicationPlanV1:
        raise TypeError("temporal publication plan type must be exact")
    _exact(plan.before_phase, GoalLanePhase, "before_phase")
    _exact(plan.after_phase, GoalLanePhase, "after_phase")
    _exact(plan.before_ledger, GoalLanePhaseTemporalLedgerV1, "before_ledger")
    _exact(plan.after_ledger, GoalLanePhaseTemporalLedgerV1, "after_ledger")
    _exact(
        plan.publication_profile,
        GoalPhaseTemporalPublicationProfile,
        "publication_profile",
    )
    if not (plan.before_phase.coordinate == plan.after_phase.coordinate == plan.before_ledger.coordinate == plan.after_ledger.coordinate):
        raise GoalPhaseTemporalError("compound publication coordinates differ")
    if plan.before_ledger.current_phase_binding_digest != _phase_binding(plan.before_phase):
        raise GoalPhaseTemporalError("before ledger is detached from before Phase")
    if plan.after_ledger.current_phase_binding_digest != _phase_binding(plan.after_phase):
        raise GoalPhaseTemporalError("after ledger is detached from after Phase")
    if plan.publication_profile is GoalPhaseTemporalPublicationProfile.NORMAL_TRANSITION:
        if plan.before_phase.state is plan.after_phase.state:
            raise GoalPhaseTemporalError(
                "normal temporal publication must transition Phase state"
            )
        expected_after = replace(
            plan.before_phase,
            state=plan.after_phase.state,
            last_receipt_ref=plan.after_phase.last_receipt_ref,
        )
        if expected_after != plan.after_phase:
            raise GoalPhaseTemporalError(
                "compound publication may change only lifecycle state and receipt"
            )
        if (
            plan.after_phase.state is not GoalLanePhaseState.ACCEPTED
            and plan.after_phase.last_receipt_ref
            != plan.before_phase.last_receipt_ref
        ):
            raise GoalPhaseTemporalError(
                "non-acceptance transition cannot alter Phase receipt"
            )
    elif plan.before_phase != plan.after_phase:
        raise GoalPhaseTemporalError(
            "temporal correction cannot change the supplied final Phase"
        )
    if plan.after_ledger.origin != plan.before_ledger.origin:
        raise GoalPhaseTemporalError("compound publication cannot replace temporal origin")
    if plan.after_ledger.occurrences[: len(plan.before_ledger.occurrences)] != plan.before_ledger.occurrences:
        raise GoalPhaseTemporalError("occurrence history must be append-only")
    if plan.after_ledger.supersessions[: len(plan.before_ledger.supersessions)] != plan.before_ledger.supersessions:
        raise GoalPhaseTemporalError("supersession history must be append-only")
    new_occ = plan.after_ledger.occurrences[len(plan.before_ledger.occurrences):]
    new_sup = plan.after_ledger.supersessions[len(plan.before_ledger.supersessions):]
    if not new_occ and not new_sup:
        raise GoalPhaseTemporalError("compound publication must append temporal authority")
    appended_occurrence_refs = (
        *(item.occurrence_ref for item in new_occ),
        *(item.replacement.occurrence_ref for item in new_sup),
    )
    if appended_occurrence_refs != plan.appended_occurrence_refs:
        raise GoalPhaseTemporalError("appended occurrence refs are not canonical")
    if tuple(item.supersession_ref for item in new_sup) != plan.appended_supersession_refs:
        raise GoalPhaseTemporalError("appended supersession refs are not canonical")
    if plan.publication_profile is GoalPhaseTemporalPublicationProfile.NORMAL_TRANSITION:
        if not new_occ or new_sup:
            raise GoalPhaseTemporalError(
                "normal transition must append occurrences without corrections"
            )
        if (
            new_occ[-1].from_state is not plan.before_phase.state
            or new_occ[-1].to_state is not plan.after_phase.state
        ):
            raise GoalPhaseTemporalError(
                "appended occurrence does not bind Phase transition"
            )
    elif new_occ or not new_sup:
        raise GoalPhaseTemporalError(
            "correction publication must append supersessions and replacements"
        )
    validate_goal_phase_temporal_ledger(
        phase=plan.after_phase, ledger=plan.after_ledger
    )
    _ = required_token(plan.expected_repository_revision_ref, "expected_repository_revision_ref")
    phase_path = required_token(plan.phase_path, "phase_path")
    ledger_path = required_token(plan.ledger_path, "ledger_path")
    if phase_path == ledger_path:
        raise GoalPhaseTemporalError("compound publication requires two exact paths")
    _ = _tokens(plan.evidence_refs, "evidence_refs", nonempty=True)
    expected_publication_binding = derive_goal_phase_temporal_publication_binding(
        coordinate=plan.after_phase.coordinate,
        publication_profile=plan.publication_profile,
        phase_binding_digest=_phase_binding(plan.after_phase),
        prior_ledger_digest=plan.before_ledger.ledger_digest,
        ledger_revision=plan.after_ledger.coverage_through.ledger_revision,
        appended_occurrence_refs=plan.appended_occurrence_refs,
        appended_supersession_refs=plan.appended_supersession_refs,
        phase_path=plan.phase_path,
        ledger_path=plan.ledger_path,
    )
    if (
        plan.publication_binding_ref != expected_publication_binding
        or plan.after_ledger.coverage_through.publication_binding_ref
        != expected_publication_binding
    ):
        raise GoalPhaseTemporalError(
            "temporal publication binding is not canonically derived"
        )


def _temporal_plan_body(plan: GoalPhaseTemporalPublicationPlanV1) -> dict[str, object]:
    return {
        "schema_id": plan.schema_id,
        "publication_profile": plan.publication_profile.value,
        "coordinate": _coordinate_wire(plan.before_phase.coordinate),
        "before_phase_binding_digest": _phase_binding(plan.before_phase),
        "after_phase_binding_digest": _phase_binding(plan.after_phase),
        "before_ledger_digest": plan.before_ledger.ledger_digest,
        "after_ledger_digest": plan.after_ledger.ledger_digest,
        "appended_occurrence_refs": list(plan.appended_occurrence_refs),
        "appended_supersession_refs": list(plan.appended_supersession_refs),
        "publication_binding_ref": plan.publication_binding_ref,
        "expected_repository_revision_ref": plan.expected_repository_revision_ref,
        "phase_path": plan.phase_path,
        "ledger_path": plan.ledger_path,
        "evidence_refs": list(plan.evidence_refs),
    }


def _select_fact(
    ledger: GoalLanePhaseTemporalLedgerV1,
    tips: tuple[GoalLanePhaseTransitionOccurrenceV1, ...],
    selector: GoalPhaseTransitionSelectorV1,
) -> GoalPhaseTransitionFactV1:
    if ledger.history_coverage is GoalPhaseHistoryCoverage.UNSUPPORTED:
        return GoalPhaseTransitionFactV1(selector, GoalPhaseTransitionFactAvailability.UNSUPPORTED, None, ())
    if ledger.history_coverage is GoalPhaseHistoryCoverage.UNAVAILABLE:
        return GoalPhaseTransitionFactV1(selector, GoalPhaseTransitionFactAvailability.UNAVAILABLE, None, ())
    selected: GoalLanePhaseTransitionOccurrenceV1 | None = None
    proven = False
    if selector.kind is GoalPhaseTransitionSelectorKind.BY_SLOT:
        selected = next((item for item in tips if item.transition_slot_ref == selector.transition_slot_ref), None)
        proven = selected is not None
    elif selector.kind is GoalPhaseTransitionSelectorKind.TERMINAL_ACCEPTANCE:
        selected = next((item for item in reversed(tips) if item.to_state is GoalLanePhaseState.ACCEPTED), None)
        proven = selected is not None and any(_ACCEPTANCE.fullmatch(ref) for ref in selected.authority_refs)
    else:
        matches = [item for item in tips if item.to_state is selector.target_state]
        if matches:
            selected = matches[0] if selector.kind is GoalPhaseTransitionSelectorKind.FIRST_ENTRY else matches[-1]
            if ledger.history_coverage is GoalPhaseHistoryCoverage.COMPLETE:
                proven = True
            elif selector.kind is GoalPhaseTransitionSelectorKind.FIRST_ENTRY:
                proven = not any(gap.first_ordinal <= selected.slot_ordinal for gap in ledger.gaps)
            else:
                proven = not any(gap.last_ordinal >= selected.slot_ordinal for gap in ledger.gaps)
    if selected is not None and proven:
        return GoalPhaseTransitionFactV1(
            selector,
            GoalPhaseTransitionFactAvailability.PRESENT,
            selected,
            tuple(sorted((ledger.ledger_digest, selected.occurrence_ref))),
        )
    if ledger.history_coverage is GoalPhaseHistoryCoverage.COMPLETE:
        return GoalPhaseTransitionFactV1(
            selector,
            GoalPhaseTransitionFactAvailability.NOT_OCCURRED,
            None,
            (ledger.ledger_digest,),
        )
    return GoalPhaseTransitionFactV1(
        selector,
        GoalPhaseTransitionFactAvailability.UNAVAILABLE,
        None,
        (ledger.ledger_digest,),
    )


def _validate_ledger_chain(
    *,
    coordinate: GoalPhaseCoordinate,
    origin: GoalLanePhaseTemporalOriginV1,
    occurrences: tuple[GoalLanePhaseTransitionOccurrenceV1, ...],
    supersessions: tuple[GoalLanePhaseTransitionSupersessionV1, ...],
    coverage: GoalPhaseHistoryCoverage,
    gaps: tuple[GoalLanePhaseTemporalGapV1, ...],
) -> None:
    occurrence_refs: set[str] = set()
    slot_refs: set[str] = set()
    for item in occurrences:
        if item.coordinate != coordinate:
            raise GoalPhaseTemporalError("occurrence coordinate differs from ledger")
        if item.occurrence_ref in occurrence_refs or item.transition_slot_ref in slot_refs:
            raise GoalPhaseTemporalError("duplicate occurrence or transition slot")
        occurrence_refs.add(item.occurrence_ref)
        slot_refs.add(item.transition_slot_ref)
    if tuple(item.slot_ordinal for item in occurrences) != tuple(
        sorted(item.slot_ordinal for item in occurrences)
    ):
        raise GoalPhaseTemporalError("occurrences must be ordered by slot ordinal")
    gap_ranges = tuple((item.first_ordinal, item.last_ordinal) for item in gaps)
    if gap_ranges != tuple(sorted(gap_ranges)) or any(
        left[1] >= right[0] for left, right in zip(gap_ranges, gap_ranges[1:])
    ):
        raise GoalPhaseTemporalError("temporal gaps must be ordered and disjoint")
    replacement_refs: set[str] = set()
    superseded_refs: set[str] = set()
    by_ref = {item.occurrence_ref: item for item in occurrences}
    all_occurrence_revision_refs = set(by_ref)
    current_tip_by_slot = {
        item.transition_slot_ref: item.occurrence_ref for item in occurrences
    }
    prior_supersession_admitted_at: str | None = None
    for item in supersessions:
        if (
            prior_supersession_admitted_at is not None
            and item.admitted_at < prior_supersession_admitted_at
        ):
            raise GoalPhaseTemporalError(
                "supersession authority admission time must be nondecreasing"
            )
        previous = by_ref.get(item.superseded_occurrence_ref)
        if previous is None and item.superseded_occurrence_ref not in replacement_refs:
            raise GoalPhaseTemporalError("supersession target is absent")
        if item.superseded_occurrence_ref in superseded_refs:
            raise GoalPhaseTemporalError("occurrence has multiple supersession successors")
        if item.replacement.occurrence_ref in all_occurrence_revision_refs:
            raise GoalPhaseTemporalError(
                "supersession replacement reuses an occurrence revision"
            )
        if (
            current_tip_by_slot.get(item.replacement.transition_slot_ref)
            != item.superseded_occurrence_ref
        ):
            raise GoalPhaseTemporalError(
                "supersession must advance the unique effective slot tip"
            )
        if previous is not None and (
            previous.coordinate != item.replacement.coordinate
            or previous.slot_ordinal != item.replacement.slot_ordinal
            or previous.predecessor_slot_ref != item.replacement.predecessor_slot_ref
            or previous.transition_slot_ref != item.replacement.transition_slot_ref
        ):
            raise GoalPhaseTemporalError("supersession changed stable transition identity")
        if previous is not None and (
            previous.from_state != item.replacement.from_state
            or previous.to_state != item.replacement.to_state
        ):
            raise GoalPhaseTemporalError(
                "state-changing supersessions are unsupported in O7 V1"
            )
        if item.downstream_revalidation_refs:
            raise GoalPhaseTemporalError(
                "O7 V1 ordinary corrections cannot claim downstream revalidation"
            )
        if previous is not None and item.replacement.recorded_at < previous.recorded_at:
            raise GoalPhaseTemporalError("supersession replacement cannot be backdated")
        superseded_refs.add(item.superseded_occurrence_ref)
        replacement_refs.add(item.replacement.occurrence_ref)
        all_occurrence_revision_refs.add(item.replacement.occurrence_ref)
        current_tip_by_slot[item.replacement.transition_slot_ref] = (
            item.replacement.occurrence_ref
        )
        by_ref[item.replacement.occurrence_ref] = item.replacement
        prior_supersession_admitted_at = item.admitted_at
    tips = _effective_occurrences(occurrences, supersessions)
    for gap in gaps:
        if any(
            gap.first_ordinal <= item.slot_ordinal <= gap.last_ordinal
            for item in tips
        ):
            raise GoalPhaseTemporalError(
                "temporal gap overlaps a known effective transition slot"
            )
    tips_by_slot = {item.transition_slot_ref: item for item in tips}
    for item in tips:
        if item.predecessor_slot_ref is None:
            continue
        predecessor = tips_by_slot.get(item.predecessor_slot_ref)
        if predecessor is None:
            continue
        if (
            predecessor.slot_ordinal + 1 != item.slot_ordinal
            or predecessor.to_state is not item.from_state
            or predecessor.effective_at > item.effective_at
            or predecessor.recorded_at > item.recorded_at
        ):
            raise GoalPhaseTemporalError("known temporal chain segment is invalid")
    if coverage is GoalPhaseHistoryCoverage.COMPLETE:
        if gaps:
            raise GoalPhaseTemporalError("complete history cannot contain gaps")
        state = origin.initial_state
        predecessor_slot: str | None = None
        previous_effective = origin.admitted_at
        for ordinal, item in enumerate(tips):
            if (
                item.slot_ordinal != ordinal
                or item.predecessor_slot_ref != predecessor_slot
            ):
                raise GoalPhaseTemporalError("complete history chain is not contiguous")
            if item.from_state is not state or item.effective_at < previous_effective:
                raise GoalPhaseTemporalError("complete history state/time chain is invalid")
            state = item.to_state
            predecessor_slot = item.transition_slot_ref
            previous_effective = item.effective_at
        previous_recorded = origin.admitted_at
        for item in tips:
            if item.recorded_at < previous_recorded:
                raise GoalPhaseTemporalError(
                    "complete history authority-admission time is not monotonic"
                )
            previous_recorded = item.recorded_at
    elif coverage is GoalPhaseHistoryCoverage.PARTIAL:
        if not occurrences or not gaps:
            raise GoalPhaseTemporalError(
                "partial history requires known occurrences and explicit gaps"
            )
    elif coverage in (GoalPhaseHistoryCoverage.UNAVAILABLE, GoalPhaseHistoryCoverage.UNSUPPORTED):
        if occurrences or supersessions or gaps:
            raise GoalPhaseTemporalError("unavailable/unsupported history carries no facts")


def _effective_occurrences(
    occurrences: tuple[GoalLanePhaseTransitionOccurrenceV1, ...],
    supersessions: tuple[GoalLanePhaseTransitionSupersessionV1, ...],
) -> tuple[GoalLanePhaseTransitionOccurrenceV1, ...]:
    by_slot = {item.transition_slot_ref: item for item in occurrences}
    current_refs = {item.transition_slot_ref: item.occurrence_ref for item in occurrences}
    by_ref = {item.occurrence_ref: item for item in occurrences}
    for supersession in supersessions:
        current = current_refs.get(supersession.replacement.transition_slot_ref)
        if current != supersession.superseded_occurrence_ref:
            raise GoalPhaseTemporalError("supersession chain is not append-only linear")
        by_ref[supersession.replacement.occurrence_ref] = supersession.replacement
        current_refs[supersession.replacement.transition_slot_ref] = supersession.replacement.occurrence_ref
        by_slot[supersession.replacement.transition_slot_ref] = supersession.replacement
    return tuple(sorted(by_slot.values(), key=lambda item: item.slot_ordinal))


def _ledger_from_wire(raw: dict[str, object]) -> GoalLanePhaseTemporalLedgerV1:
    _keys(raw, {"schema_id", "coordinate", "current_phase_binding_digest", "origin", "occurrences", "supersessions", "history_coverage", "coverage_through", "gaps", "evidence_refs", "ledger_digest"}, "ledger")
    origin_raw = _mapping(raw["origin"], "origin")
    _keys(origin_raw, {"schema_id", "coordinate", "initial_state", "phase_admission_receipt_ref", "admitted_at", "phase_binding_digest", "repository_revision_ref", "origin_ref"}, "origin")
    origin = GoalLanePhaseTemporalOriginV1(
        coordinate=_coordinate(origin_raw["coordinate"]),
        initial_state=GoalLanePhaseState(_string(origin_raw["initial_state"], "initial_state")),
        phase_admission_receipt_ref=_string(origin_raw["phase_admission_receipt_ref"], "phase_admission_receipt_ref"),
        admitted_at=_string(origin_raw["admitted_at"], "admitted_at"),
        phase_binding_digest=_string(origin_raw["phase_binding_digest"], "phase_binding_digest"),
        repository_revision_ref=_string(origin_raw["repository_revision_ref"], "repository_revision_ref"),
    )
    boundary_raw = _mapping(raw["coverage_through"], "coverage_through")
    _keys(boundary_raw, {"phase_binding_digest", "ledger_revision", "publication_binding_ref"}, "coverage_through")
    return GoalLanePhaseTemporalLedgerV1(
        coordinate=_coordinate(raw["coordinate"]),
        current_phase_binding_digest=_string(raw["current_phase_binding_digest"], "current_phase_binding_digest"),
        origin=origin,
        occurrences=tuple(_occurrence_from_wire(item) for item in _list(raw["occurrences"], "occurrences")),
        supersessions=tuple(_supersession_from_wire(item) for item in _list(raw["supersessions"], "supersessions")),
        history_coverage=GoalPhaseHistoryCoverage(_string(raw["history_coverage"], "history_coverage")),
        coverage_through=GoalLanePhaseTemporalBoundaryV1(
            phase_binding_digest=_string(boundary_raw["phase_binding_digest"], "phase_binding_digest"),
            ledger_revision=_integer(boundary_raw["ledger_revision"], "ledger_revision"),
            publication_binding_ref=_string(boundary_raw["publication_binding_ref"], "publication_binding_ref"),
        ),
        gaps=tuple(_gap_from_wire(item) for item in _list(raw["gaps"], "gaps")),
        evidence_refs=_strings(raw["evidence_refs"], "evidence_refs"),
    )


def _occurrence_from_wire(raw: object) -> GoalLanePhaseTransitionOccurrenceV1:
    value = _mapping(raw, "occurrence")
    _keys(value, {"schema_id", "coordinate", "slot_ordinal", "predecessor_slot_ref", "transition_slot_ref", "from_state", "to_state", "effective_at", "recorded_at", "authority_refs", "source_refs", "evidence_refs", "occurrence_ref"}, "occurrence")
    return GoalLanePhaseTransitionOccurrenceV1(
        coordinate=_coordinate(value["coordinate"]),
        slot_ordinal=_integer(value["slot_ordinal"], "slot_ordinal"),
        predecessor_slot_ref=_optional_string(value["predecessor_slot_ref"], "predecessor_slot_ref"),
        from_state=GoalLanePhaseState(_string(value["from_state"], "from_state")),
        to_state=GoalLanePhaseState(_string(value["to_state"], "to_state")),
        effective_at=_string(value["effective_at"], "effective_at"),
        recorded_at=_string(value["recorded_at"], "recorded_at"),
        authority_refs=_strings(value["authority_refs"], "authority_refs"),
        source_refs=_strings(value["source_refs"], "source_refs"),
        evidence_refs=_strings(value["evidence_refs"], "evidence_refs"),
    )


def _supersession_from_wire(raw: object) -> GoalLanePhaseTransitionSupersessionV1:
    value = _mapping(raw, "supersession")
    _keys(value, {"schema_id", "superseded_occurrence_ref", "replacement", "reason", "admitted_at", "authority_refs", "downstream_revalidation_refs", "supersession_ref"}, "supersession")
    return GoalLanePhaseTransitionSupersessionV1(
        superseded_occurrence_ref=_string(value["superseded_occurrence_ref"], "superseded_occurrence_ref"),
        replacement=_occurrence_from_wire(value["replacement"]),
        reason=_string(value["reason"], "reason"),
        admitted_at=_string(value["admitted_at"], "admitted_at"),
        authority_refs=_strings(value["authority_refs"], "authority_refs"),
        downstream_revalidation_refs=_strings(value["downstream_revalidation_refs"], "downstream_revalidation_refs"),
    )


def _gap_from_wire(raw: object) -> GoalLanePhaseTemporalGapV1:
    value = _mapping(raw, "gap")
    _keys(value, {"first_ordinal", "last_ordinal", "reason", "evidence_refs"}, "gap")
    return GoalLanePhaseTemporalGapV1(
        first_ordinal=_integer(value["first_ordinal"], "first_ordinal"),
        last_ordinal=_integer(value["last_ordinal"], "last_ordinal"),
        reason=_string(value["reason"], "reason"),
        evidence_refs=_strings(value["evidence_refs"], "evidence_refs"),
    )


def _observation_from_wire(raw: dict[str, object]) -> GoalLanePhaseTemporalObservationV1:
    _keys(raw, {"schema_id", "coordinate", "ledger_digest", "origin_ref", "phase_binding_digest", "ledger_revision", "coverage_publication_binding_ref", "source_revision_ref", "snapshot_at", "currentness", "currentness_ref", "observation_authority_ref", "history_coverage", "gaps", "facts", "gap_count", "observation_ref"}, "observation")
    facts: list[GoalPhaseTransitionFactV1] = []
    for raw_fact in _list(raw["facts"], "facts"):
        fact = _mapping(raw_fact, "fact")
        _keys(fact, {"selector", "availability", "occurrence", "proof_refs"}, "fact")
        selector_raw = _mapping(fact["selector"], "selector")
        _keys(selector_raw, {"kind", "transition_slot_ref", "target_state"}, "selector")
        selector = GoalPhaseTransitionSelectorV1(
            kind=GoalPhaseTransitionSelectorKind(_string(selector_raw["kind"], "kind")),
            transition_slot_ref=_optional_string(selector_raw["transition_slot_ref"], "transition_slot_ref"),
            target_state=None if selector_raw["target_state"] is None else GoalLanePhaseState(_string(selector_raw["target_state"], "target_state")),
        )
        occurrence = None if fact["occurrence"] is None else _occurrence_from_wire(fact["occurrence"])
        facts.append(GoalPhaseTransitionFactV1(selector, GoalPhaseTransitionFactAvailability(_string(fact["availability"], "availability")), occurrence, _strings(fact["proof_refs"], "proof_refs")))
    return GoalLanePhaseTemporalObservationV1(
        coordinate=_coordinate(raw["coordinate"]),
        ledger_digest=_string(raw["ledger_digest"], "ledger_digest"),
        origin_ref=_string(raw["origin_ref"], "origin_ref"),
        phase_binding_digest=_string(raw["phase_binding_digest"], "phase_binding_digest"),
        ledger_revision=_integer(raw["ledger_revision"], "ledger_revision"),
        coverage_publication_binding_ref=_string(raw["coverage_publication_binding_ref"], "coverage_publication_binding_ref"),
        source_revision_ref=_string(raw["source_revision_ref"], "source_revision_ref"),
        snapshot_at=_string(raw["snapshot_at"], "snapshot_at"),
        currentness=GoalPhaseTemporalCurrentness(_string(raw["currentness"], "currentness")),
        currentness_ref=_string(raw["currentness_ref"], "currentness_ref"),
        observation_authority_ref=_string(raw["observation_authority_ref"], "observation_authority_ref"),
        history_coverage=GoalPhaseHistoryCoverage(_string(raw["history_coverage"], "history_coverage")),
        gaps=tuple(_gap_from_wire(item) for item in _list(raw["gaps"], "gaps")),
        facts=tuple(facts),
        gap_count=_integer(raw["gap_count"], "gap_count"),
    )


def _canonical_json(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _json_object(payload: bytes, field_name: str) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseTemporalError(f"{field_name} is not canonical JSON") from error
    return dict(_mapping(raw, field_name))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseTemporalError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_tree(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_map = cast(dict[object, object], left)
        right_map = cast(dict[object, object], right)
        return left_map.keys() == right_map.keys() and all(_exact_tree(left_map[key], right_map[key]) for key in left_map)
    if type(left) is list:
        left_items = cast(list[object], left)
        right_items = cast(list[object], right)
        return len(left_items) == len(right_items) and all(_exact_tree(a, b) for a, b in zip(left_items, right_items, strict=True))
    return left == right


def _utc(value: object, field_name: str) -> str:
    value = _string(value, field_name)
    match = _UTC.fullmatch(value)
    if match is None:
        raise GoalPhaseTemporalError(f"{field_name} must be canonical second UTC")
    year, month, day = (int(match.group(name)) for name in ("year", "month", "day"))
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    limits = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if day > limits[month - 1]:
        raise GoalPhaseTemporalError(f"{field_name} must be a real UTC instant")
    return value


def _tokens(values: object, field_name: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be exact tuple")
    result = tuple(required_token(item, field_name) for item in cast(tuple[object, ...], values))
    if result != tuple(sorted(set(result))):
        raise GoalPhaseTemporalError(f"{field_name} must be unique and sorted")
    if nonempty and not result:
        raise GoalPhaseTemporalError(f"{field_name} must not be empty")
    return result


def _domain_ref_sequence(
    values: object, domain: str, field_name: str
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be exact tuple")
    result = tuple(
        _domain(item, domain, field_name)
        for item in cast(tuple[object, ...], values)
    )
    if len(result) != len(set(result)):
        raise GoalPhaseTemporalError(f"{field_name} must be unique")
    return result


_T = TypeVar("_T")


def _exact_tuple(
    values: object, expected: type[_T], field_name: str
) -> tuple[_T, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be exact tuple")
    result = cast(tuple[object, ...], values)
    for item in result:
        _exact(item, expected, field_name)
    return cast(tuple[_T, ...], result)


def _mapping(value: object, field_name: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in cast(dict[object, object], value)):
        raise GoalPhaseTemporalError(f"{field_name} must be an object with text keys")
    return cast(dict[str, object], value)


def _keys(value: dict[str, object], expected: set[str], field_name: str) -> None:
    if set(value) != expected:
        raise GoalPhaseTemporalError(f"{field_name} keys differ from contract")


def _list(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseTemporalError(f"{field_name} must be an array")
    return cast(list[object], value)


def _strings(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_string(item, field_name) for item in _list(value, field_name))


def _string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise GoalPhaseTemporalError(f"{field_name} must be text")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    return None if value is None else _string(value, field_name)


def _integer(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise GoalPhaseTemporalError(f"{field_name} must be an integer")
    return value


def _positive_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 1:
        raise GoalPhaseTemporalError(f"{field_name} must be a positive integer")
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise GoalPhaseTemporalError(f"{field_name} must be nonnegative")
    return value


def _sha256(value: object, field_name: str) -> str:
    value = _string(value, field_name)
    if _SHA256.fullmatch(value) is None:
        raise GoalPhaseTemporalError(f"{field_name} must be lowercase SHA-256 ref")
    return value


def _domain(value: object, domain: str, field_name: str) -> str:
    value = _string(value, field_name)
    if re.fullmatch(rf"{re.escape(domain)}:sha256:[0-9a-f]{{64}}", value) is None:
        raise GoalPhaseTemporalError(f"{field_name} must use {domain} SHA-256 domain")
    return value


def _repository_commit_ref(value: object, field_name: str) -> str:
    value = _string(value, field_name)
    if _REPOSITORY_COMMIT.fullmatch(value) is None:
        raise GoalPhaseTemporalError(
            f"{field_name} must be an exact Git object id"
        )
    return value


def _optional_domain(value: object | None, domain: str, field_name: str) -> str | None:
    return None if value is None else _domain(value, domain, field_name)


def _exact(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{field_name} must be exact {expected.__name__}")


__all__ = [
    "GOAL_PHASE_OCCURRENCE_SCHEMA",
    "GOAL_PHASE_SUPERSESSION_SCHEMA",
    "GOAL_PHASE_TEMPORAL_LEDGER_SCHEMA",
    "GOAL_PHASE_TEMPORAL_OBSERVATION_SCHEMA",
    "GOAL_PHASE_TEMPORAL_OBSERVATION_AUTHORITY_SCHEMA",
    "GOAL_PHASE_TEMPORAL_ORIGIN_SCHEMA",
    "GOAL_PHASE_TEMPORAL_PUBLICATION_SCHEMA",
    "GoalLanePhaseTemporalBoundaryV1",
    "GoalLanePhaseTemporalGapV1",
    "GoalLanePhaseTemporalLedgerV1",
    "GoalLanePhaseTemporalObservationV1",
    "GoalLanePhaseTemporalOriginV1",
    "GoalLanePhaseTransitionOccurrenceV1",
    "GoalLanePhaseTransitionSupersessionV1",
    "GoalPhaseHistoryCoverage",
    "GoalPhaseTemporalCurrentness",
    "GoalPhaseTemporalError",
    "GoalPhaseTemporalObservationAuthorityKind",
    "GoalPhaseTemporalObservationAuthorityV1",
    "GoalPhaseTemporalPublicationPlanV1",
    "GoalPhaseTemporalPublicationProfile",
    "GoalPhaseTemporalPublicationReceiptV1",
    "GoalPhaseTemporalPublicationState",
    "GoalPhaseTransitionFactAvailability",
    "GoalPhaseTransitionFactV1",
    "GoalPhaseTransitionSelectorKind",
    "GoalPhaseTransitionSelectorV1",
    "decode_goal_phase_temporal_ledger",
    "decode_goal_phase_temporal_observation",
    "decode_goal_phase_temporal_observation_authority",
    "decode_goal_phase_temporal_publication_receipt",
    "derive_goal_phase_temporal_currentness_receipt_ref",
    "derive_goal_phase_temporal_publication_binding",
    "derive_goal_phase_temporal_snapshot_receipt_ref",
    "encode_goal_phase_temporal_ledger",
    "encode_goal_phase_temporal_observation",
    "encode_goal_phase_temporal_observation_authority",
    "encode_goal_phase_temporal_publication_receipt",
    "goal_phase_temporal_phase_binding_digest",
    "observe_goal_phase_temporal_facts",
    "validate_goal_phase_temporal_ledger",
    "verify_goal_phase_temporal_publication_receipt",
]
