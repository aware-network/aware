"""Provider-neutral Goal pursuit receipts and currentness.

The caller supplies one already-resolved direction snapshot. This module does
not parse Markdown, resolve Issue authority, select a Goal, dispatch work, or
mutate any authority. Filesystem and canonical providers may both implement
the structural snapshot protocols and share these exact receipt semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Protocol


class GoalPursuitRowSnapshot(Protocol):
    @property
    def row_key(self) -> str: ...

    @property
    def step(self) -> int: ...

    @property
    def timestamp(self) -> str: ...

    @property
    def tick(self) -> str: ...

    @property
    def issue_ref(self) -> str: ...

    @property
    def gate(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def owner(self) -> str: ...

    @property
    def receipt_ref(self) -> str: ...


class GoalLanePursuitSnapshot(Protocol):
    @property
    def lane_key(self) -> str: ...

    @property
    def owner(self) -> str: ...

    @property
    def lane_status(self) -> str: ...

    @property
    def pursuit_state(self) -> str: ...

    @property
    def suggested_action(self) -> str: ...

    @property
    def completion_gate(self) -> str | None: ...

    @property
    def pursuit_directive(self) -> str | None: ...

    @property
    def pursuit_directive_source(self) -> str: ...

    @property
    def pursuit_row(self) -> GoalPursuitRowSnapshot | None: ...

    @property
    def drift(self) -> tuple[str, ...]: ...


class GoalDirectionSnapshot(Protocol):
    @property
    def tag(self) -> str: ...

    @property
    def sha256(self) -> str: ...

    @property
    def lanes(self) -> Mapping[str, GoalLanePursuitSnapshot]: ...


@dataclass(frozen=True, slots=True)
class GoalPursuitReceipt:
    schema_id: str
    pursuit_ref: str
    effect_profile: str
    goal_tag: str
    goal_sha256: str
    lane_key: str
    lane_status: str
    lane_owner: str
    row_key: str
    step: int
    row_timestamp: str
    tick: str
    issue_ref: str
    gate: str
    completion_gate: str
    row_status: str
    row_owner: str
    row_receipt_ref: str
    pursuit_state: str
    suggested_action: str
    pursuit_directive: str | None
    pursuit_directive_source: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoalPursuitCurrentnessReceipt:
    schema_id: str
    effect_profile: str
    status: str
    expected_pursuit_ref: str
    observed_pursuit_ref: str | None
    expected_goal_sha256: str
    observed_goal_sha256: str
    goal_tag: str
    lane_key: str
    row_key: str
    reasons: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoalPursuitProjectionV1:
    """Committed projection coordinates retained by a V1 pursuit."""

    goal_sha256: str
    repository_ref: str
    repository_commit: str
    goal_blob_oid: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoalPursuitDirectionBindingV1:
    """Provider-supplied semantic binding for one exact Goal row.

    Digest producers must use typed semantic projections. In particular,
    dependency digests must exclude incidental evaluator or presentation
    lineage while preserving authored definitions and qualified evidence state.
    """

    goal_tag: str
    lane_key: str
    row_key: str
    goal_global_digest: str
    lane_digest: str
    row_digest: str
    incident_dependency_set_digest: str
    incoming_dependency_gate_digest: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoalPursuitReceiptV1:
    """Integrity-bound direction evidence plus committed projection lineage."""

    schema_id: str
    pursuit_ref: str
    direction_ref: str
    effect_profile: str
    projection: GoalPursuitProjectionV1
    direction_binding: GoalPursuitDirectionBindingV1
    goal_tag: str
    lane_key: str
    lane_status: str
    lane_owner: str
    row_key: str
    step: int
    row_timestamp: str
    tick: str
    issue_ref: str
    gate: str
    completion_gate: str
    row_status: str
    row_owner: str
    row_receipt_ref: str
    pursuit_state: str
    suggested_action: str
    pursuit_directive: str | None
    pursuit_directive_source: str

    def to_json(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GoalPursuitCurrentnessReceiptV1:
    """Independent semantic-direction and committed-projection currentness."""

    schema_id: str
    effect_profile: str
    direction_currentness: str
    projection_currentness: str
    replay_disposition: str
    expected_pursuit_ref: str
    expected_direction_ref: str
    observed_direction_ref: str | None
    expected_goal_sha256: str
    observed_goal_sha256: str
    expected_repository_commit: str
    observed_repository_commit: str
    goal_tag: str
    lane_key: str
    row_key: str
    reasons: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return asdict(self)


class GoalIssueReconciliationAction(StrEnum):
    """Explicit decision after Issue and Goal-row projections diverge."""

    COMPLETE_ROW = "complete_row"
    CONTINUE_WITH_SUCCESSOR = "continue_with_successor"
    SPLIT_SUCCESSOR_ROW = "split_successor_row"
    PROJECTION_ONLY = "projection_only"


class GoalCheckpointKind(StrEnum):
    """Authored evidence category without Goal lifecycle authority."""

    READINESS = "readiness"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    HANDOFF = "handoff"
    ACCEPTANCE = "acceptance"


class GoalExecutionReadiness(StrEnum):
    """Execution evidence state, independent from row lifecycle."""

    READY = "ready"
    AWAITING_INPUTS = "awaiting_inputs"
    BLOCKED = "blocked"
    ACCEPTED = "accepted"


class GoalSuccessorSemantics(StrEnum):
    UNCHANGED_GATE = "unchanged_gate"
    DISTINCT_GATE = "distinct_gate"


class GoalReconciliationRecommendation(StrEnum):
    HOLD = "hold"
    COMPLETE_ROW = "complete_row"
    CONTINUE_WITH_SUCCESSOR = "continue_with_successor"
    SPLIT_SUCCESSOR_ROW = "split_successor_row"
    PROJECTION_ONLY = "projection_only"


@dataclass(frozen=True, slots=True)
class GoalReconciliationAssessmentInput:
    goal_tag: str
    lane_key: str
    row_key: str
    current_issue_ref: str
    current_issue_status: str
    checkpoint_ref: str | None = None
    checkpoint_readiness: GoalExecutionReadiness | None = None
    gate_evidence_refs: tuple[str, ...] = ()
    successor_issue_ref: str | None = None
    successor_issue_status: str | None = None
    successor_semantics: GoalSuccessorSemantics | None = None
    projection_repair_receipt_ref: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "goal_tag",
            "lane_key",
            "row_key",
            "current_issue_ref",
            "current_issue_status",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty text.")
        if (self.checkpoint_ref is None) != (self.checkpoint_readiness is None):
            raise ValueError("checkpoint ref and readiness must be supplied together.")
        successor_values = (
            self.successor_issue_ref,
            self.successor_issue_status,
            self.successor_semantics,
        )
        if any(value is not None for value in successor_values) and not all(
            value is not None for value in successor_values
        ):
            raise ValueError("successor evidence must be complete.")
        if any(not item.strip() for item in self.gate_evidence_refs):
            raise ValueError("gate_evidence_refs must contain non-empty text.")

    def to_json(self) -> dict[str, object]:
        payload = asdict(self)
        if self.checkpoint_readiness is not None:
            payload["checkpoint_readiness"] = self.checkpoint_readiness.value
        if self.successor_semantics is not None:
            payload["successor_semantics"] = self.successor_semantics.value
        return payload


@dataclass(frozen=True, slots=True)
class GoalReconciliationAssessmentReceipt:
    schema_id: str
    assessment_ref: str
    effect_profile: str
    recommendation: GoalReconciliationRecommendation
    reasons: tuple[str, ...]
    observed: GoalReconciliationAssessmentInput

    def to_json(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "assessment_ref": self.assessment_ref,
            "effect_profile": self.effect_profile,
            "recommendation": self.recommendation.value,
            "reasons": list(self.reasons),
            "observed": self.observed.to_json(),
        }


def assess_goal_issue_reconciliation(
    observed: GoalReconciliationAssessmentInput,
) -> GoalReconciliationAssessmentReceipt:
    """Recommend one explicit recovery action from supplied exact evidence."""

    recommendation = GoalReconciliationRecommendation.HOLD
    reasons: tuple[str, ...]
    if observed.projection_repair_receipt_ref is not None:
        recommendation = GoalReconciliationRecommendation.PROJECTION_ONLY
        reasons = ("published_semantics_projection_stale",)
    elif observed.current_issue_status.casefold() != "closed":
        reasons = ("current_issue_not_closed",)
    elif observed.successor_issue_ref is not None:
        assert observed.successor_issue_status is not None
        assert observed.successor_semantics is not None
        if observed.successor_issue_status.casefold() != "in progress":
            reasons = ("successor_issue_not_in_progress",)
        elif observed.successor_semantics is GoalSuccessorSemantics.UNCHANGED_GATE:
            recommendation = GoalReconciliationRecommendation.CONTINUE_WITH_SUCCESSOR
            reasons = ("closed_issue_same_gate_successor_active",)
        elif not observed.gate_evidence_refs:
            reasons = ("predecessor_gate_evidence_required",)
        else:
            recommendation = GoalReconciliationRecommendation.SPLIT_SUCCESSOR_ROW
            reasons = ("settled_predecessor_distinct_gate_successor_active",)
    elif (
        observed.checkpoint_readiness is GoalExecutionReadiness.ACCEPTED
        and observed.gate_evidence_refs
    ):
        recommendation = GoalReconciliationRecommendation.COMPLETE_ROW
        reasons = ("closed_issue_gate_evidence_accepted",)
    else:
        reasons = ("completion_evidence_not_accepted",)
    body = {
        "observed": observed.to_json(),
        "recommendation": recommendation.value,
        "reasons": list(reasons),
    }
    return GoalReconciliationAssessmentReceipt(
        schema_id="aware.goal.reconciliation_assessment.receipt.v1",
        assessment_ref="goal-reconciliation-assessment:sha256:"
        + _canonical_digest(body),
        effect_profile="read_only_non_authorizing",
        recommendation=recommendation,
        reasons=reasons,
        observed=observed,
    )


@dataclass(frozen=True, slots=True)
class GoalCheckpointIntent:
    goal_tag: str
    lane_key: str
    row_key: str
    pursuit_ref: str
    kind: GoalCheckpointKind
    readiness: GoalExecutionReadiness
    evidence_refs: tuple[str, ...]
    summary: str
    timestamp: str

    def __post_init__(self) -> None:
        for field in (
            "goal_tag",
            "lane_key",
            "row_key",
            "pursuit_ref",
            "summary",
            "timestamp",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty text.")
        if not isinstance(self.kind, GoalCheckpointKind):
            raise TypeError("kind must be GoalCheckpointKind.")
        if not isinstance(self.readiness, GoalExecutionReadiness):
            raise TypeError("readiness must be GoalExecutionReadiness.")
        if not self.evidence_refs or any(
            not item.strip() for item in self.evidence_refs
        ):
            raise ValueError("Goal checkpoint requires explicit evidence_refs.")

    def to_json(self) -> dict[str, object]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["readiness"] = self.readiness.value
        return payload


@dataclass(frozen=True, slots=True)
class GoalCheckpointReceipt:
    schema_id: str
    checkpoint_ref: str
    effect_profile: str
    recommended_action: str
    intent: GoalCheckpointIntent

    def to_json(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "checkpoint_ref": self.checkpoint_ref,
            "effect_profile": self.effect_profile,
            "recommended_action": self.recommended_action,
            "intent": self.intent.to_json(),
        }


def issue_goal_checkpoint_receipt(
    intent: GoalCheckpointIntent,
) -> GoalCheckpointReceipt:
    """Bind evidence/readiness without authorizing a row transition."""

    recommended_action = (
        "evaluate_complete_row"
        if intent.readiness is GoalExecutionReadiness.ACCEPTED
        else (
            "continue_issue"
            if intent.readiness is GoalExecutionReadiness.READY
            else "hold"
        )
    )
    return GoalCheckpointReceipt(
        schema_id="aware.goal.checkpoint.receipt.v1",
        checkpoint_ref="goal-checkpoint:sha256:"
        + _canonical_digest(intent.to_json()),
        effect_profile="evidence_only_non_authorizing",
        recommended_action=recommended_action,
        intent=intent,
    )


@dataclass(frozen=True, slots=True)
class GoalIssueReconciliationIntent:
    goal_tag: str
    lane_key: str
    row_key: str
    authority_issue_ref: str
    action: GoalIssueReconciliationAction
    evidence_refs: tuple[str, ...]
    successor_issue_ref: str | None = None
    successor_row_key: str | None = None

    def __post_init__(self) -> None:
        for field in ("goal_tag", "lane_key", "row_key", "authority_issue_ref"):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty text.")
        if not isinstance(self.action, GoalIssueReconciliationAction):
            raise TypeError("action must be GoalIssueReconciliationAction.")
        if not self.evidence_refs or any(
            not item.strip() for item in self.evidence_refs
        ):
            raise ValueError(
                "Goal-Issue reconciliation requires explicit evidence_refs."
            )
        requires_successor = self.action in {
            GoalIssueReconciliationAction.CONTINUE_WITH_SUCCESSOR,
            GoalIssueReconciliationAction.SPLIT_SUCCESSOR_ROW,
        }
        if requires_successor != (self.successor_issue_ref is not None):
            raise ValueError(
                "successor_issue_ref does not match reconciliation action."
            )
        if (self.action is GoalIssueReconciliationAction.SPLIT_SUCCESSOR_ROW) != (
            self.successor_row_key is not None
        ):
            raise ValueError("successor_row_key does not match reconciliation action.")
        if self.successor_issue_ref == self.authority_issue_ref:
            raise ValueError("successor Issue must differ from the authority Issue.")

    def to_json(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action"] = self.action.value
        return payload


@dataclass(frozen=True, slots=True)
class GoalIssueReconciliationReceipt:
    schema_id: str
    reconciliation_ref: str
    effect_profile: str
    intent: GoalIssueReconciliationIntent

    def to_json(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "reconciliation_ref": self.reconciliation_ref,
            "effect_profile": self.effect_profile,
            "intent": self.intent.to_json(),
        }


def issue_goal_issue_reconciliation_receipt(
    intent: GoalIssueReconciliationIntent,
) -> GoalIssueReconciliationReceipt:
    """Bind one non-authorizing reconciliation decision without applying it."""

    body = intent.to_json()
    return GoalIssueReconciliationReceipt(
        schema_id="aware.goal.issue_reconciliation.receipt.v1",
        reconciliation_ref="goal-issue-reconciliation:sha256:"
        + _canonical_digest(body),
        effect_profile="direction_only_non_authorizing",
        intent=intent,
    )


def issue_goal_pursuit_receipt(
    *,
    snapshot: GoalDirectionSnapshot,
    lane_key: str,
    row_key: str,
    expected_goal_sha256: str,
) -> GoalPursuitReceipt:
    """Issue one deterministic, read-only receipt for an exact ready row."""

    expected = _normalize_sha256(expected_goal_sha256)
    if snapshot.sha256 != expected:
        raise ValueError(
            f"Goal authority digest mismatch: expected {expected!r}, "
            + f"observed {snapshot.sha256!r}."
        )
    return _build_goal_pursuit_receipt(
        snapshot=snapshot,
        lane_key=lane_key,
        row_key=row_key,
    )


def verify_goal_pursuit_currentness(
    *,
    snapshot: GoalDirectionSnapshot,
    lane_key: str,
    row_key: str,
    expected_goal_sha256: str,
    pursuit_ref: str,
) -> GoalPursuitCurrentnessReceipt:
    """Classify a retained pursuit receipt against one fresh supplied read."""

    expected = _normalize_sha256(expected_goal_sha256)
    normalized_pursuit_ref = _normalize_pursuit_ref(pursuit_ref)
    reasons: list[str] = []
    observed_pursuit_ref: str | None = None
    if snapshot.sha256 != expected:
        reasons.append("goal_digest_changed")
    else:
        try:
            observed = _build_goal_pursuit_receipt(
                snapshot=snapshot,
                lane_key=lane_key,
                row_key=row_key,
            )
        except ValueError:
            reasons.append("pursuit_unavailable")
        else:
            observed_pursuit_ref = observed.pursuit_ref
            if observed_pursuit_ref != normalized_pursuit_ref:
                reasons.append("pursuit_receipt_changed")

    return GoalPursuitCurrentnessReceipt(
        schema_id="aware.goal.pursuit.currentness.v0",
        effect_profile="read_only_non_authorizing",
        status="current" if not reasons else "stale",
        expected_pursuit_ref=normalized_pursuit_ref,
        observed_pursuit_ref=observed_pursuit_ref,
        expected_goal_sha256=expected,
        observed_goal_sha256=snapshot.sha256,
        goal_tag=snapshot.tag,
        lane_key=lane_key,
        row_key=row_key,
        reasons=tuple(reasons),
    )


def issue_goal_pursuit_receipt_v1(
    *,
    snapshot: GoalDirectionSnapshot,
    lane_key: str,
    row_key: str,
    expected_goal_sha256: str,
    projection: GoalPursuitProjectionV1,
    direction_binding: GoalPursuitDirectionBindingV1,
) -> GoalPursuitReceiptV1:
    """Issue additive V1 direction evidence for one committed projection."""

    legacy = issue_goal_pursuit_receipt(
        snapshot=snapshot,
        lane_key=lane_key,
        row_key=row_key,
        expected_goal_sha256=expected_goal_sha256,
    )
    normalized_projection = _normalize_projection_v1(projection)
    normalized_binding = _normalize_direction_binding_v1(direction_binding)
    if normalized_projection.goal_sha256 != legacy.goal_sha256:
        raise ValueError("projection goal_sha256 differs from the Goal snapshot.")
    if (
        normalized_binding.goal_tag != legacy.goal_tag
        or normalized_binding.lane_key != legacy.lane_key
        or normalized_binding.row_key != legacy.row_key
    ):
        raise ValueError("direction binding coordinates differ from the pursuit row.")

    direction_ref = _direction_ref_v1(normalized_binding)
    provisional = GoalPursuitReceiptV1(
        schema_id="aware.goal.pursuit.receipt.v1",
        pursuit_ref="",
        direction_ref=direction_ref,
        effect_profile=legacy.effect_profile,
        projection=normalized_projection,
        direction_binding=normalized_binding,
        goal_tag=legacy.goal_tag,
        lane_key=legacy.lane_key,
        lane_status=legacy.lane_status,
        lane_owner=legacy.lane_owner,
        row_key=legacy.row_key,
        step=legacy.step,
        row_timestamp=legacy.row_timestamp,
        tick=legacy.tick,
        issue_ref=legacy.issue_ref,
        gate=legacy.gate,
        completion_gate=legacy.completion_gate,
        row_status=legacy.row_status,
        row_owner=legacy.row_owner,
        row_receipt_ref=legacy.row_receipt_ref,
        pursuit_state=legacy.pursuit_state,
        suggested_action=legacy.suggested_action,
        pursuit_directive=legacy.pursuit_directive,
        pursuit_directive_source=legacy.pursuit_directive_source,
    )
    return replace(provisional, pursuit_ref=_pursuit_ref_v1(provisional))


def validate_goal_pursuit_receipt_v1(receipt: GoalPursuitReceiptV1) -> None:
    """Reject tampering or coordinate drift in one retained V1 receipt."""

    if receipt.schema_id != "aware.goal.pursuit.receipt.v1":
        raise ValueError("unsupported Goal pursuit receipt V1 schema_id.")
    if receipt.effect_profile != "read_only_non_authorizing":
        raise ValueError("Goal pursuit receipt V1 effect_profile is invalid.")
    projection = _normalize_projection_v1(receipt.projection)
    binding = _normalize_direction_binding_v1(receipt.direction_binding)
    if (
        receipt.goal_tag != binding.goal_tag
        or receipt.lane_key != binding.lane_key
        or receipt.row_key != binding.row_key
    ):
        raise ValueError("Goal pursuit receipt V1 coordinates are inconsistent.")
    if _normalize_sha256(projection.goal_sha256) != projection.goal_sha256:
        raise ValueError("Goal pursuit projection digest is not canonical.")
    if receipt.direction_ref != _direction_ref_v1(binding):
        raise ValueError("Goal pursuit receipt V1 direction_ref is invalid.")
    if receipt.pursuit_ref != _pursuit_ref_v1(receipt):
        raise ValueError("Goal pursuit receipt V1 pursuit_ref is invalid.")


def verify_goal_pursuit_currentness_v1(
    *,
    receipt: GoalPursuitReceiptV1,
    observed_projection: GoalPursuitProjectionV1,
    observed_direction_binding: GoalPursuitDirectionBindingV1 | None,
    observed_descends_from_expected: bool | None,
) -> GoalPursuitCurrentnessReceiptV1:
    """Classify V1 direction separately from committed projection lineage."""

    validate_goal_pursuit_receipt_v1(receipt)
    projection = _normalize_projection_v1(observed_projection)
    reasons: list[str] = []

    if projection.repository_commit == receipt.projection.repository_commit:
        if projection != receipt.projection:
            raise ValueError(
                "equal repository commits must retain identical projection coordinates."
            )
        projection_currentness = "current"
        reasons.append("projection_unchanged")
    elif observed_descends_from_expected is True:
        projection_currentness = "advanced"
    else:
        projection_currentness = "unknown"
        reasons.append("projection_lineage_unproven")

    observed_direction_ref: str | None = None
    direction_currentness = "ambiguous"
    if observed_direction_binding is None:
        reasons.append("semantic_projection_ambiguous")
    else:
        binding = _normalize_direction_binding_v1(observed_direction_binding)
        observed_direction_ref = _direction_ref_v1(binding)
        if (
            binding.goal_tag != receipt.goal_tag
            or binding.lane_key != receipt.lane_key
            or binding.row_key != receipt.row_key
        ):
            direction_currentness = "stale"
            reasons.append("goal_identity_changed")
        else:
            changed = _direction_change_reasons(
                expected=receipt.direction_binding,
                observed=binding,
            )
            reasons.extend(changed)
            direction_currentness = "current" if not changed else "stale"

    if projection_currentness == "unknown":
        direction_currentness = "ambiguous"
    if direction_currentness == "current":
        if projection_currentness == "current":
            replay_disposition = "exact"
        else:
            replay_disposition = "replayable"
            reasons.append("projection_advanced_direction_unchanged")
    else:
        replay_disposition = "refuse"

    return GoalPursuitCurrentnessReceiptV1(
        schema_id="aware.goal.pursuit.currentness.v1",
        effect_profile="read_only_non_authorizing",
        direction_currentness=direction_currentness,
        projection_currentness=projection_currentness,
        replay_disposition=replay_disposition,
        expected_pursuit_ref=receipt.pursuit_ref,
        expected_direction_ref=receipt.direction_ref,
        observed_direction_ref=observed_direction_ref,
        expected_goal_sha256=receipt.projection.goal_sha256,
        observed_goal_sha256=projection.goal_sha256,
        expected_repository_commit=receipt.projection.repository_commit,
        observed_repository_commit=projection.repository_commit,
        goal_tag=receipt.goal_tag,
        lane_key=receipt.lane_key,
        row_key=receipt.row_key,
        reasons=tuple(reasons),
    )


def _build_goal_pursuit_receipt(
    *,
    snapshot: GoalDirectionSnapshot,
    lane_key: str,
    row_key: str,
) -> GoalPursuitReceipt:
    lane = snapshot.lanes.get(lane_key)
    if lane is None:
        available = ", ".join(sorted(snapshot.lanes)) or "none"
        raise ValueError(
            f"Unknown Goal lane {lane_key!r}; available lanes: {available}."
        )
    if lane.pursuit_state != "ready":
        reasons = ", ".join(lane.drift) or lane.pursuit_state
        raise ValueError(
            f"Goal lane {lane_key!r} cannot issue a ready pursuit receipt: {reasons}."
        )
    row = lane.pursuit_row
    if row is None:
        raise ValueError(
            f"Goal lane {lane_key!r} has no pursuit row; plan a row first."
        )
    if row.row_key != row_key:
        raise ValueError(
            f"Goal pursuit row mismatch: expected {row_key!r}, actual {row.row_key!r}."
        )
    if lane.completion_gate != row.gate:
        raise ValueError("Goal pursuit completion gate differs from its row gate.")

    provisional = GoalPursuitReceipt(
        schema_id="aware.goal.pursuit.receipt.v0",
        pursuit_ref="",
        effect_profile="read_only_non_authorizing",
        goal_tag=snapshot.tag,
        goal_sha256=snapshot.sha256,
        lane_key=lane.lane_key,
        lane_status=lane.lane_status,
        lane_owner=lane.owner,
        row_key=row.row_key,
        step=row.step,
        row_timestamp=row.timestamp,
        tick=row.tick,
        issue_ref=row.issue_ref,
        gate=row.gate,
        completion_gate=row.gate,
        row_status=row.status,
        row_owner=row.owner,
        row_receipt_ref=row.receipt_ref,
        pursuit_state=lane.pursuit_state,
        suggested_action=lane.suggested_action,
        pursuit_directive=lane.pursuit_directive,
        pursuit_directive_source=lane.pursuit_directive_source,
    )
    receipt_body = provisional.to_json()
    del receipt_body["pursuit_ref"]
    receipt_digest = hashlib.sha256(
        json.dumps(
            receipt_body,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return replace(
        provisional,
        pursuit_ref=f"goal-pursuit:sha256:{receipt_digest}",
    )


def _normalize_sha256(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized.startswith("sha256:"):
        normalized = normalized.removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise ValueError("expected_goal_sha256 must be a SHA-256 digest.")
    return normalized


def _normalize_pursuit_ref(value: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"goal-pursuit:sha256:[0-9a-f]{64}", normalized):
        raise ValueError(
            "pursuit_ref must be 'goal-pursuit:sha256:' followed by a SHA-256 digest."
        )
    return normalized


def _normalize_projection_v1(
    value: GoalPursuitProjectionV1,
) -> GoalPursuitProjectionV1:
    goal_sha256 = _normalize_sha256(value.goal_sha256)
    repository_ref = value.repository_ref.strip()
    if not repository_ref.startswith("refs/") or any(
        character.isspace() for character in repository_ref
    ):
        raise ValueError("repository_ref must be one canonical refs/* name.")
    repository_commit = _normalize_git_oid(
        value.repository_commit, field="repository_commit"
    )
    goal_blob_oid = _normalize_git_oid(value.goal_blob_oid, field="goal_blob_oid")
    return GoalPursuitProjectionV1(
        goal_sha256=goal_sha256,
        repository_ref=repository_ref,
        repository_commit=repository_commit,
        goal_blob_oid=goal_blob_oid,
    )


def _normalize_direction_binding_v1(
    value: GoalPursuitDirectionBindingV1,
) -> GoalPursuitDirectionBindingV1:
    coordinates = {
        "goal_tag": value.goal_tag.strip(),
        "lane_key": value.lane_key.strip(),
        "row_key": value.row_key.strip(),
    }
    for field, coordinate in coordinates.items():
        if not coordinate:
            raise ValueError(f"{field} must be non-empty text.")
    return GoalPursuitDirectionBindingV1(
        **coordinates,
        goal_global_digest=_normalize_prefixed_sha256(
            value.goal_global_digest, field="goal_global_digest"
        ),
        lane_digest=_normalize_prefixed_sha256(value.lane_digest, field="lane_digest"),
        row_digest=_normalize_prefixed_sha256(value.row_digest, field="row_digest"),
        incident_dependency_set_digest=_normalize_prefixed_sha256(
            value.incident_dependency_set_digest,
            field="incident_dependency_set_digest",
        ),
        incoming_dependency_gate_digest=_normalize_prefixed_sha256(
            value.incoming_dependency_gate_digest,
            field="incoming_dependency_gate_digest",
        ),
    )


def _direction_ref_v1(binding: GoalPursuitDirectionBindingV1) -> str:
    return "goal-pursuit-direction:sha256:" + _canonical_digest(binding.to_json())


def _pursuit_ref_v1(receipt: GoalPursuitReceiptV1) -> str:
    body = receipt.to_json()
    del body["pursuit_ref"]
    return "goal-pursuit:sha256:" + _canonical_digest(body)


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _normalize_prefixed_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", normalized):
        raise ValueError(f"{field} must be 'sha256:' plus a SHA-256 digest.")
    return normalized


def _normalize_git_oid(value: str, *, field: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", normalized):
        raise ValueError(f"{field} must be a full Git object id.")
    return normalized


def _direction_change_reasons(
    *,
    expected: GoalPursuitDirectionBindingV1,
    observed: GoalPursuitDirectionBindingV1,
) -> tuple[str, ...]:
    fields = (
        ("goal_global_digest", "goal_global_direction_changed"),
        ("lane_digest", "lane_direction_changed"),
        ("row_digest", "row_direction_changed"),
        ("incident_dependency_set_digest", "incident_dependency_set_changed"),
        ("incoming_dependency_gate_digest", "incoming_dependency_gate_changed"),
    )
    return tuple(
        reason
        for field, reason in fields
        if getattr(expected, field) != getattr(observed, field)
    )
