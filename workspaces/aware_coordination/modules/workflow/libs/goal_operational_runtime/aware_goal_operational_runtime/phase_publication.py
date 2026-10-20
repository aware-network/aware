"""Repository-publication semantics for native Goal Lane Phases.

The module is provider neutral.  It plans deterministic Phase mutations and
binds their semantic and repository currentness without parsing Markdown,
touching Git, transitioning Issues, or granting execution authority.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import cast

from .identity import fingerprint, required_token
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)
from .phase_document import GoalPhaseNativeDocumentV2

GOAL_PHASE_PUBLICATION_BINDING_SCHEMA = "aware.goal.phase-publication-binding.v1"
GOAL_PHASE_MUTATION_PLAN_SCHEMA = "aware.goal.phase-mutation-plan.v1"
GOAL_PHASE_PUBLICATION_RECEIPT_SCHEMA = "aware.goal.phase-publication-receipt.v1"
GOAL_PHASE_RECONCILIATION_RECEIPT_SCHEMA = (
    "aware.goal.phase-projection-reconciliation.v1"
)

_SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
_ACCEPTANCE_REF = re.compile(r"^goal-phase-acceptance:sha256:[0-9a-f]{64}$")
_WORK_ASSOCIATION_REF = re.compile(r"^goal-phase-work:sha256:[0-9a-f]{64}$")
_WORK_ADMISSION_REF = re.compile(
    r"^goal-phase-work-admission:sha256:[0-9a-f]{64}$"
)


class GoalPhaseDigestCurrentness(StrEnum):
    CURRENT = "current"
    STALE = "stale"


class GoalPhaseWorkCurrentness(StrEnum):
    CURRENT = "current"
    ADVANCED = "advanced"
    STALE = "stale"


class GoalPhaseProjectionCurrentness(StrEnum):
    CURRENT = "current"
    ADVANCED = "advanced"
    UNKNOWN = "unknown"


class GoalPhaseProjectionRelation(StrEnum):
    EXACT = "exact"
    ANCESTOR = "ancestor"
    DIVERGENT = "divergent"
    UNKNOWN = "unknown"


class GoalPhaseReplayDisposition(StrEnum):
    EXACT = "exact"
    REPLAYABLE = "replayable"
    REFUSE = "refuse"


class GoalPhaseMutationKind(StrEnum):
    CONTINUE_WORK = "continue_work"
    ACCEPT_PHASE = "accept_phase"


class GoalPhasePublicationState(StrEnum):
    REPOSITORY_PUBLISHED = "repository_published"
    RECONCILIATION_REQUIRED = "reconciliation_required"


@dataclass(frozen=True, slots=True)
class GoalPhaseProjectionRevisionV1:
    repository_ref: str
    repository_commit: str
    phase_blob_oid: str
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseProjectionRevisionV1:
            raise TypeError("projection revision type must be exact")
        object.__setattr__(
            self,
            "repository_ref",
            required_token(self.repository_ref, "repository_ref"),
        )
        object.__setattr__(
            self,
            "repository_commit",
            required_token(self.repository_commit, "repository_commit"),
        )
        object.__setattr__(
            self,
            "phase_blob_oid",
            required_token(self.phase_blob_oid, "phase_blob_oid"),
        )
        object.__setattr__(
            self,
            "source_sha256",
            _sha256_ref(self.source_sha256, "source_sha256"),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "repository_ref": self.repository_ref,
            "repository_commit": self.repository_commit,
            "phase_blob_oid": self.phase_blob_oid,
            "source_sha256": self.source_sha256,
        }


@dataclass(frozen=True, slots=True)
class GoalPhasePublicationBindingV1:
    coordinate: GoalPhaseCoordinate
    direction_digest: str
    gate_digest: str
    work_association_digest: str
    projection_revision: GoalPhaseProjectionRevisionV1
    schema_id: str = GOAL_PHASE_PUBLICATION_BINDING_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhasePublicationBindingV1:
            raise TypeError("publication binding type must be exact")
        if self.schema_id != GOAL_PHASE_PUBLICATION_BINDING_SCHEMA:
            raise ValueError("unsupported Phase publication binding schema")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        _exact(
            self.projection_revision,
            GoalPhaseProjectionRevisionV1,
            "projection_revision",
        )
        object.__setattr__(
            self,
            "direction_digest",
            _sha256_ref(self.direction_digest, "direction_digest"),
        )
        object.__setattr__(
            self, "gate_digest", _sha256_ref(self.gate_digest, "gate_digest")
        )
        object.__setattr__(
            self,
            "work_association_digest",
            _sha256_ref(self.work_association_digest, "work_association_digest"),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "coordinate": _coordinate_wire(self.coordinate),
            "direction_digest": self.direction_digest,
            "gate_digest": self.gate_digest,
            "work_association_digest": self.work_association_digest,
            "projection_revision": self.projection_revision.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class GoalPhasePublicationCurrentnessV1:
    expected: GoalPhasePublicationBindingV1
    observed: GoalPhasePublicationBindingV1
    direction_currentness: GoalPhaseDigestCurrentness
    gate_currentness: GoalPhaseDigestCurrentness
    work_currentness: GoalPhaseWorkCurrentness
    projection_currentness: GoalPhaseProjectionCurrentness
    replay_disposition: GoalPhaseReplayDisposition
    reasons: tuple[str, ...]
    receipt_ref: str

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": "aware.goal.phase-publication-currentness.v1",
            "effect_profile": "read_only_non_authorizing",
            "expected": self.expected.to_wire(),
            "observed": self.observed.to_wire(),
            "direction_currentness": self.direction_currentness.value,
            "gate_currentness": self.gate_currentness.value,
            "work_currentness": self.work_currentness.value,
            "projection_currentness": self.projection_currentness.value,
            "replay_disposition": self.replay_disposition.value,
            "reasons": list(self.reasons),
            "receipt_ref": self.receipt_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseMutationPlanV1:
    operation: GoalPhaseMutationKind
    before: GoalLanePhase
    after: GoalLanePhase
    expected_binding: GoalPhasePublicationBindingV1
    evidence_refs: tuple[str, ...]
    semantic_intent_ref: str
    acceptance_receipt_ref: str | None = None
    schema_id: str = GOAL_PHASE_MUTATION_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMutationPlanV1:
            raise TypeError("mutation plan type must be exact")
        if self.schema_id != GOAL_PHASE_MUTATION_PLAN_SCHEMA:
            raise ValueError("unsupported Phase mutation plan schema")
        _exact(self.operation, GoalPhaseMutationKind, "operation")
        _exact(self.before, GoalLanePhase, "before")
        _exact(self.after, GoalLanePhase, "after")
        _exact(self.expected_binding, GoalPhasePublicationBindingV1, "expected_binding")
        if self.before.coordinate != self.after.coordinate:
            raise ValueError("Phase mutation cannot change coordinate")
        if type(self.evidence_refs) is not tuple:
            raise TypeError("evidence_refs must be exact tuple")
        evidence = tuple(
            required_token(item, "evidence_ref") for item in self.evidence_refs
        )
        if evidence != tuple(sorted(set(evidence))):
            raise ValueError("evidence_refs must be unique and sorted")
        object.__setattr__(self, "evidence_refs", evidence)
        object.__setattr__(
            self,
            "semantic_intent_ref",
            _domain_sha256(
                self.semantic_intent_ref,
                "goal-phase-intent",
                "semantic_intent_ref",
            ),
        )
        if self.acceptance_receipt_ref is not None:
            if _ACCEPTANCE_REF.fullmatch(self.acceptance_receipt_ref) is None:
                raise ValueError("acceptance_receipt_ref is not qualified")
        _validate_mutation_plan(self)


@dataclass(frozen=True, slots=True)
class GoalPhasePublicationReceiptV1:
    plan_ref: str
    operation: GoalPhaseMutationKind
    coordinate: GoalPhaseCoordinate
    before_binding: GoalPhasePublicationBindingV1
    after_binding: GoalPhasePublicationBindingV1
    repository_commit_receipt_ref: str
    changed_paths: tuple[str, ...]
    receipt_ref: str
    schema_id: str = GOAL_PHASE_PUBLICATION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhasePublicationReceiptV1:
            raise TypeError("publication receipt type must be exact")
        if self.schema_id != GOAL_PHASE_PUBLICATION_RECEIPT_SCHEMA:
            raise ValueError("unsupported Phase publication receipt schema")
        object.__setattr__(
            self,
            "plan_ref",
            _domain_sha256(self.plan_ref, "goal-phase-intent", "plan_ref"),
        )
        _exact(self.operation, GoalPhaseMutationKind, "operation")
        _exact(self.coordinate, GoalPhaseCoordinate, "coordinate")
        _exact(self.before_binding, GoalPhasePublicationBindingV1, "before_binding")
        _exact(self.after_binding, GoalPhasePublicationBindingV1, "after_binding")
        object.__setattr__(
            self,
            "repository_commit_receipt_ref",
            required_token(
                self.repository_commit_receipt_ref, "repository_commit_receipt_ref"
            ),
        )
        expected_commit_receipt = (
            "repository-commit:"
            + self.after_binding.projection_revision.repository_commit
        )
        if self.repository_commit_receipt_ref != expected_commit_receipt:
            raise ValueError(
                "repository_commit_receipt_ref must bind the after projection commit"
            )
        if type(self.changed_paths) is not tuple or len(self.changed_paths) != 1:
            raise ValueError("Phase publication must change exactly one path")
        object.__setattr__(
            self,
            "changed_paths",
            (required_token(self.changed_paths[0], "changed_path"),),
        )
        object.__setattr__(
            self,
            "receipt_ref",
            _domain_sha256(
                self.receipt_ref,
                "goal-phase-publication",
                "receipt_ref",
            ),
        )
        body = {
            "schema_id": self.schema_id,
            "plan_ref": self.plan_ref,
            "operation": self.operation.value,
            "coordinate": _coordinate_wire(self.coordinate),
            "before_binding": self.before_binding.to_wire(),
            "after_binding": self.after_binding.to_wire(),
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "changed_paths": list(self.changed_paths),
        }
        if self.receipt_ref != "goal-phase-publication:" + fingerprint(body):
            raise ValueError("Phase publication receipt digest is invalid")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "repository_publication",
            "plan_ref": self.plan_ref,
            "operation": self.operation.value,
            "coordinate": _coordinate_wire(self.coordinate),
            "before_binding": self.before_binding.to_wire(),
            "after_binding": self.after_binding.to_wire(),
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "changed_paths": list(self.changed_paths),
            "receipt_ref": self.receipt_ref,
        }


def decode_goal_phase_publication_receipt(
    payload: bytes,
) -> GoalPhasePublicationReceiptV1:
    """Strictly decode and authenticate one Phase publication receipt."""

    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = cast(
            object,
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_object),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Phase publication receipt is not JSON") from error
    values = _wire_mapping(raw, "publication_receipt")
    _wire_keys(
        values,
        {
            "schema_id",
            "effect_profile",
            "plan_ref",
            "operation",
            "coordinate",
            "before_binding",
            "after_binding",
            "repository_commit_receipt_ref",
            "changed_paths",
            "receipt_ref",
        },
        "publication_receipt",
    )
    if _wire_text(values["effect_profile"], "effect_profile") != (
        "repository_publication"
    ):
        raise ValueError("unsupported Phase publication effect profile")
    changed_paths = _wire_list(values["changed_paths"], "changed_paths")
    if len(changed_paths) != 1:
        raise ValueError("Phase publication must change exactly one path")
    return GoalPhasePublicationReceiptV1(
        schema_id=_wire_text(values["schema_id"], "schema_id"),
        plan_ref=_wire_text(values["plan_ref"], "plan_ref"),
        operation=GoalPhaseMutationKind(
            _wire_text(values["operation"], "operation")
        ),
        coordinate=_decode_coordinate(values["coordinate"]),
        before_binding=_decode_publication_binding(values["before_binding"]),
        after_binding=_decode_publication_binding(values["after_binding"]),
        repository_commit_receipt_ref=_wire_text(
            values["repository_commit_receipt_ref"],
            "repository_commit_receipt_ref",
        ),
        changed_paths=(_wire_text(changed_paths[0], "changed_path"),),
        receipt_ref=_wire_text(values["receipt_ref"], "receipt_ref"),
    )


@dataclass(frozen=True, slots=True)
class GoalPhaseProjectionReconciliationReceiptV1:
    publication_receipt: GoalPhasePublicationReceiptV1
    worktree_current: bool
    index_current: bool
    publication_state: GoalPhasePublicationState
    reason_codes: tuple[str, ...]
    receipt_ref: str
    schema_id: str = GOAL_PHASE_RECONCILIATION_RECEIPT_SCHEMA

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "effect_profile": "projection_reconciliation_only",
            "publication_receipt": self.publication_receipt.to_wire(),
            "worktree_current": self.worktree_current,
            "index_current": self.index_current,
            "publication_state": self.publication_state.value,
            "reason_codes": list(self.reason_codes),
            "receipt_ref": self.receipt_ref,
        }


def goal_phase_direction_digest(phase: GoalLanePhase) -> str:
    """Digest Phase meaning and lifecycle, excluding Gate and work history."""

    _exact(phase, GoalLanePhase, "phase")
    return fingerprint(
        {
            "schema_id": "aware.goal.phase-direction.v1",
            "coordinate": _coordinate_wire(phase.coordinate),
            "title": phase.title,
            "ordinal": phase.ordinal,
            "ordinal_semantics": "presentation_only",
            "intent": phase.intent,
            "state": phase.state.value,
            "gate_observations": [
                {
                    "observation_ref": item.observation_ref,
                    "gate_digest": item.gate_digest,
                    "outcome": item.outcome.value,
                    "evaluator_ref": item.evaluator_ref,
                    "evidence_refs": list(item.evidence_refs),
                    "source_revision_refs": list(item.source_revision_refs),
                    "evaluated_at": item.evaluated_at,
                    "currentness_ref": item.currentness_ref,
                }
                for item in phase.gate_observations
            ],
            "pursuit_directive": phase.pursuit_directive,
            "last_receipt_ref": phase.last_receipt_ref,
        }
    )


def goal_phase_work_association_digest(phase: GoalLanePhase) -> str:
    _exact(phase, GoalLanePhase, "phase")
    return fingerprint(
        {
            "schema_id": "aware.goal.phase-work-associations.v1",
            "coordinate": _coordinate_wire(phase.coordinate),
            "work_associations": [_work_wire(item) for item in phase.work_associations],
        }
    )


def bind_goal_phase_publication(
    phase: GoalLanePhase,
    *,
    projection_revision: GoalPhaseProjectionRevisionV1,
) -> GoalPhasePublicationBindingV1:
    _exact(phase, GoalLanePhase, "phase")
    _exact(projection_revision, GoalPhaseProjectionRevisionV1, "projection_revision")
    return GoalPhasePublicationBindingV1(
        coordinate=phase.coordinate,
        direction_digest=goal_phase_direction_digest(phase),
        gate_digest=phase.gate.gate_digest,
        work_association_digest=goal_phase_work_association_digest(phase),
        projection_revision=projection_revision,
    )


def assess_goal_phase_publication_currentness(
    *,
    expected: GoalPhasePublicationBindingV1,
    observed: GoalPhasePublicationBindingV1,
    projection_relation: GoalPhaseProjectionRelation,
    expected_phase: GoalLanePhase,
    observed_phase: GoalLanePhase,
) -> GoalPhasePublicationCurrentnessV1:
    _exact(expected, GoalPhasePublicationBindingV1, "expected")
    _exact(observed, GoalPhasePublicationBindingV1, "observed")
    _exact(projection_relation, GoalPhaseProjectionRelation, "projection_relation")
    _exact(expected_phase, GoalLanePhase, "expected_phase")
    _exact(observed_phase, GoalLanePhase, "observed_phase")
    _require_binding(expected_phase, expected)
    _require_binding(observed_phase, observed)
    reasons: list[str] = []
    if expected.coordinate != observed.coordinate:
        reasons.append("coordinate_changed")
    direction = (
        GoalPhaseDigestCurrentness.CURRENT
        if expected.direction_digest == observed.direction_digest
        else GoalPhaseDigestCurrentness.STALE
    )
    if direction is GoalPhaseDigestCurrentness.STALE:
        reasons.append("direction_changed")
    gate = (
        GoalPhaseDigestCurrentness.CURRENT
        if expected.gate_digest == observed.gate_digest
        else GoalPhaseDigestCurrentness.STALE
    )
    if gate is GoalPhaseDigestCurrentness.STALE:
        reasons.append("gate_changed")
    if expected.work_association_digest == observed.work_association_digest:
        work = GoalPhaseWorkCurrentness.CURRENT
    elif _work_history_is_prefix(expected_phase, observed_phase):
        work = GoalPhaseWorkCurrentness.ADVANCED
        reasons.append("work_associations_advanced")
    else:
        work = GoalPhaseWorkCurrentness.STALE
        reasons.append("work_associations_conflict")
    if (
        expected.projection_revision.repository_ref
        != observed.projection_revision.repository_ref
    ):
        projection = GoalPhaseProjectionCurrentness.UNKNOWN
        reasons.append("repository_ref_changed")
    elif projection_relation is GoalPhaseProjectionRelation.EXACT:
        projection = GoalPhaseProjectionCurrentness.CURRENT
    elif projection_relation is GoalPhaseProjectionRelation.ANCESTOR:
        projection = GoalPhaseProjectionCurrentness.ADVANCED
        reasons.append("projection_advanced")
    else:
        projection = GoalPhaseProjectionCurrentness.UNKNOWN
        reasons.append("projection_lineage_unknown")
    semantic_current = (
        not reasons or set(reasons) <= {"projection_advanced"}
    )
    if not semantic_current or work is not GoalPhaseWorkCurrentness.CURRENT:
        replay = GoalPhaseReplayDisposition.REFUSE
    elif projection is GoalPhaseProjectionCurrentness.CURRENT:
        replay = GoalPhaseReplayDisposition.EXACT
    elif projection is GoalPhaseProjectionCurrentness.ADVANCED:
        replay = GoalPhaseReplayDisposition.REPLAYABLE
    else:
        replay = GoalPhaseReplayDisposition.REFUSE
    body = {
        "schema_id": "aware.goal.phase-publication-currentness.v1",
        "expected": expected.to_wire(),
        "observed": observed.to_wire(),
        "direction_currentness": direction.value,
        "gate_currentness": gate.value,
        "work_currentness": work.value,
        "projection_currentness": projection.value,
        "replay_disposition": replay.value,
        "reasons": reasons,
    }
    return GoalPhasePublicationCurrentnessV1(
        expected=expected,
        observed=observed,
        direction_currentness=direction,
        gate_currentness=gate,
        work_currentness=work,
        projection_currentness=projection,
        replay_disposition=replay,
        reasons=tuple(reasons),
        receipt_ref="goal-phase-currentness:" + fingerprint(body),
    )


def plan_goal_phase_same_gate_successor(
    *,
    phase: GoalLanePhase,
    expected_binding: GoalPhasePublicationBindingV1,
    expected_current_issue_ref: str,
    successor_issue_ref: str,
    successor_role: GoalLanePhaseWorkRole,
    timestamp: str,
    evidence_refs: tuple[str, ...],
) -> GoalPhaseMutationPlanV1:
    _require_binding(phase, expected_binding)
    if phase.state not in (GoalLanePhaseState.ACTIVE, GoalLanePhaseState.HELD):
        raise ValueError("same-Gate succession requires active or held Phase")
    _exact(successor_role, GoalLanePhaseWorkRole, "successor_role")
    expected_issue = required_token(
        expected_current_issue_ref, "expected_current_issue_ref"
    )
    successor_issue = required_token(successor_issue_ref, "successor_issue_ref")
    if expected_issue == successor_issue:
        raise ValueError("successor Issue must differ from current Issue")
    current = tuple(
        item
        for item in phase.work_associations
        if item.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    if len(current) != 1 or current[0].issue_ref != expected_issue:
        raise ValueError("expected current Issue association is not exact")
    if successor_issue in {item.issue_ref for item in phase.work_associations}:
        raise ValueError("successor Issue is already associated")
    timestamp = required_token(timestamp, "timestamp")
    evidence = _evidence(evidence_refs)
    if not evidence:
        raise ValueError("same-Gate succession requires publication evidence")
    association_ref, receipt_ref = _derive_work_admission_refs(
        coordinate=phase.coordinate,
        issue_ref=successor_issue,
        role=successor_role,
        admitted_at=timestamp,
        evidence_refs=evidence,
    )
    retired = tuple(
        replace(
            item,
            disposition=GoalLanePhaseWorkDisposition.RETIRED,
            retired_at=timestamp,
        )
        if item.association_ref == current[0].association_ref
        else item
        for item in phase.work_associations
    )
    successor = GoalLanePhaseWork(
        association_ref=association_ref,
        issue_ref=successor_issue,
        role=successor_role,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at=timestamp,
        receipt_ref=receipt_ref,
    )
    after = replace(phase, work_associations=(*retired, successor))
    if goal_phase_direction_digest(after) != expected_binding.direction_digest:
        raise AssertionError("same-Gate succession changed Phase direction")
    if after.gate.gate_digest != expected_binding.gate_digest:
        raise AssertionError("same-Gate succession changed Gate")
    intent = {
        "schema_id": GOAL_PHASE_MUTATION_PLAN_SCHEMA,
        "operation": GoalPhaseMutationKind.CONTINUE_WORK.value,
        "expected_binding": expected_binding.to_wire(),
        "expected_current_issue_ref": expected_issue,
        "successor": _work_wire(successor),
        "evidence_refs": list(evidence),
    }
    return GoalPhaseMutationPlanV1(
        operation=GoalPhaseMutationKind.CONTINUE_WORK,
        before=phase,
        after=after,
        expected_binding=expected_binding,
        evidence_refs=evidence,
        semantic_intent_ref="goal-phase-intent:" + fingerprint(intent),
    )


def apply_goal_phase_mutation_to_native_document(
    *,
    document: GoalPhaseNativeDocumentV2,
    plan: GoalPhaseMutationPlanV1,
) -> GoalPhaseNativeDocumentV2:
    """Apply one canonical Phase mutation inside an exact V2 carrier.

    This is deliberately only a carrier substitution.  The Phase planner owns
    transition semantics; this function proves that the surrounding native
    graph and execution authority are preserved exactly.
    """

    _exact(document, GoalPhaseNativeDocumentV2, "document")
    document.__post_init__()
    _exact(plan, GoalPhaseMutationPlanV1, "plan")
    _validate_mutation_plan(plan)
    matches = tuple(
        item
        for item in document.operational_bundle.phases
        if item.coordinate == plan.before.coordinate
    )
    if len(matches) != 1 or matches[0] != plan.before:
        raise ValueError("native carrier Phase preimage is absent or advanced")
    after_bundle = GoalPhaseContractBundleV1(
        phases=tuple(
            plan.after if item.coordinate == plan.before.coordinate else item
            for item in document.operational_bundle.phases
        ),
        dependencies=document.operational_bundle.dependencies,
    )
    after = GoalPhaseNativeDocumentV2(
        goal_tag=document.goal_tag,
        compatibility_projection_sha256=document.compatibility_projection_sha256,
        compatibility_projection_byte_count=(
            document.compatibility_projection_byte_count
        ),
        definitions=document.definitions,
        operational_bundle=after_bundle,
        unresolved_dependencies=document.unresolved_dependencies,
        source_refs=document.source_refs,
        execution_authority=document.execution_authority,
    )
    if after.definitions != document.definitions:
        raise AssertionError("native carrier definitions changed")
    if after.operational_bundle.dependencies != document.operational_bundle.dependencies:
        raise AssertionError("native carrier dependencies changed")
    if after.unresolved_dependencies != document.unresolved_dependencies:
        raise AssertionError("native carrier unresolved dependencies changed")
    if after.execution_authority != document.execution_authority:
        raise AssertionError("native carrier execution authority changed")
    return after


def verify_goal_phase_publication_transition(
    *,
    before_document: GoalPhaseNativeDocumentV2,
    after_document: GoalPhaseNativeDocumentV2,
    publication_receipt: GoalPhasePublicationReceiptV1,
) -> None:
    """Independently verify the receipt operation over complete V2 carriers."""

    _exact(before_document, GoalPhaseNativeDocumentV2, "before_document")
    _exact(after_document, GoalPhaseNativeDocumentV2, "after_document")
    _exact(
        publication_receipt,
        GoalPhasePublicationReceiptV1,
        "publication_receipt",
    )
    before_document.__post_init__()
    after_document.__post_init__()
    publication_receipt.__post_init__()
    if (
        before_document.goal_tag != after_document.goal_tag
        or before_document.compatibility_projection_sha256
        != after_document.compatibility_projection_sha256
        or before_document.compatibility_projection_byte_count
        != after_document.compatibility_projection_byte_count
        or before_document.definitions != after_document.definitions
        or before_document.operational_bundle.dependencies
        != after_document.operational_bundle.dependencies
        or before_document.unresolved_dependencies
        != after_document.unresolved_dependencies
        or before_document.source_refs != after_document.source_refs
        or before_document.execution_authority != after_document.execution_authority
    ):
        raise ValueError("Phase publication changed protected carrier authority")

    coordinate = publication_receipt.coordinate
    before_matches = tuple(
        phase
        for phase in before_document.operational_bundle.phases
        if phase.coordinate == coordinate
    )
    after_matches = tuple(
        phase
        for phase in after_document.operational_bundle.phases
        if phase.coordinate == coordinate
    )
    if len(before_matches) != 1 or len(after_matches) != 1:
        raise ValueError("Phase publication coordinate is absent or ambiguous")
    before_phase = before_matches[0]
    after_phase = after_matches[0]
    if tuple(
        phase
        for phase in before_document.operational_bundle.phases
        if phase.coordinate != coordinate
    ) != tuple(
        phase
        for phase in after_document.operational_bundle.phases
        if phase.coordinate != coordinate
    ):
        raise ValueError("Phase publication changed an unrelated Phase")
    if len(before_document.operational_bundle.phases) != len(
        after_document.operational_bundle.phases
    ):
        raise ValueError("Phase publication changed the operational Phase set")
    if bind_goal_phase_publication(
        before_phase,
        projection_revision=publication_receipt.before_binding.projection_revision,
    ) != publication_receipt.before_binding:
        raise ValueError("Phase publication before binding differs")
    if bind_goal_phase_publication(
        after_phase,
        projection_revision=publication_receipt.after_binding.projection_revision,
    ) != publication_receipt.after_binding:
        raise ValueError("Phase publication after binding differs")

    if publication_receipt.operation is GoalPhaseMutationKind.CONTINUE_WORK:
        _verify_continue_work_transition(before_phase, after_phase)
        return
    if publication_receipt.operation is GoalPhaseMutationKind.ACCEPT_PHASE:
        _verify_accept_phase_transition(before_phase, after_phase)
        return
    raise ValueError("unsupported Phase publication operation")


def plan_goal_phase_acceptance(
    *,
    phase: GoalLanePhase,
    expected_binding: GoalPhasePublicationBindingV1,
    gate_observation_ref: str,
    evidence_refs: tuple[str, ...],
) -> GoalPhaseMutationPlanV1:
    _require_binding(phase, expected_binding)
    if phase.state not in (GoalLanePhaseState.ACTIVE, GoalLanePhaseState.HELD):
        raise ValueError("only active or held Phase may be accepted")
    observation_ref = required_token(gate_observation_ref, "gate_observation_ref")
    matching = tuple(
        item
        for item in phase.gate_observations
        if item.observation_ref == observation_ref
    )
    if len(matching) != 1:
        raise ValueError("exact Gate observation is absent")
    observation = matching[0]
    if (
        observation.gate_digest != phase.gate.gate_digest
        or observation.outcome is not GoalLanePhaseGateOutcome.SATISFIED
    ):
        raise ValueError("Phase acceptance requires satisfied current-Gate observation")
    evidence = _evidence(evidence_refs)
    if not evidence:
        raise ValueError("Phase acceptance requires publication evidence")
    acceptance_body = {
        "schema_id": "aware.goal.phase-acceptance.v1",
        "coordinate": _coordinate_wire(phase.coordinate),
        "expected_binding": expected_binding.to_wire(),
        "gate_observation_ref": observation_ref,
        "evidence_refs": list(evidence),
    }
    acceptance_ref = "goal-phase-acceptance:" + fingerprint(acceptance_body)
    after = replace(
        phase,
        state=GoalLanePhaseState.ACCEPTED,
        last_receipt_ref=acceptance_ref,
    )
    intent = {
        "schema_id": GOAL_PHASE_MUTATION_PLAN_SCHEMA,
        "operation": GoalPhaseMutationKind.ACCEPT_PHASE.value,
        **acceptance_body,
        "acceptance_receipt_ref": acceptance_ref,
    }
    return GoalPhaseMutationPlanV1(
        operation=GoalPhaseMutationKind.ACCEPT_PHASE,
        before=phase,
        after=after,
        expected_binding=expected_binding,
        evidence_refs=evidence,
        semantic_intent_ref="goal-phase-intent:" + fingerprint(intent),
        acceptance_receipt_ref=acceptance_ref,
    )


def issue_goal_phase_publication_receipt(
    *,
    plan: GoalPhaseMutationPlanV1,
    after_projection_revision: GoalPhaseProjectionRevisionV1,
    repository_commit_receipt_ref: str,
    changed_path: str,
) -> GoalPhasePublicationReceiptV1:
    _exact(plan, GoalPhaseMutationPlanV1, "plan")
    _validate_mutation_plan(plan)
    after_binding = bind_goal_phase_publication(
        plan.after, projection_revision=after_projection_revision
    )
    commit_receipt = required_token(
        repository_commit_receipt_ref, "repository_commit_receipt_ref"
    )
    normalized_path = required_token(changed_path, "changed_path")
    body = {
        "schema_id": GOAL_PHASE_PUBLICATION_RECEIPT_SCHEMA,
        "plan_ref": plan.semantic_intent_ref,
        "operation": plan.operation.value,
        "coordinate": _coordinate_wire(plan.after.coordinate),
        "before_binding": plan.expected_binding.to_wire(),
        "after_binding": after_binding.to_wire(),
        "repository_commit_receipt_ref": commit_receipt,
        "changed_paths": [normalized_path],
    }
    return GoalPhasePublicationReceiptV1(
        plan_ref=plan.semantic_intent_ref,
        operation=plan.operation,
        coordinate=plan.after.coordinate,
        before_binding=plan.expected_binding,
        after_binding=after_binding,
        repository_commit_receipt_ref=commit_receipt,
        changed_paths=(normalized_path,),
        receipt_ref="goal-phase-publication:" + fingerprint(body),
    )


def reconcile_goal_phase_projection(
    *,
    publication_receipt: GoalPhasePublicationReceiptV1,
    worktree_current: bool,
    index_current: bool,
    reason_codes: tuple[str, ...] = (),
) -> GoalPhaseProjectionReconciliationReceiptV1:
    _exact(publication_receipt, GoalPhasePublicationReceiptV1, "publication_receipt")
    reasons = _evidence(reason_codes)
    state = (
        GoalPhasePublicationState.REPOSITORY_PUBLISHED
        if worktree_current and index_current
        else GoalPhasePublicationState.RECONCILIATION_REQUIRED
    )
    if state is GoalPhasePublicationState.RECONCILIATION_REQUIRED and not reasons:
        raise ValueError("reconciliation_required needs a typed reason")
    body = {
        "schema_id": GOAL_PHASE_RECONCILIATION_RECEIPT_SCHEMA,
        "publication_receipt_ref": publication_receipt.receipt_ref,
        "worktree_current": worktree_current,
        "index_current": index_current,
        "publication_state": state.value,
        "reason_codes": list(reasons),
    }
    return GoalPhaseProjectionReconciliationReceiptV1(
        publication_receipt=publication_receipt,
        worktree_current=worktree_current,
        index_current=index_current,
        publication_state=state,
        reason_codes=reasons,
        receipt_ref="goal-phase-reconciliation:" + fingerprint(body),
    )


def _require_binding(
    phase: GoalLanePhase, binding: GoalPhasePublicationBindingV1
) -> None:
    _exact(phase, GoalLanePhase, "phase")
    _exact(binding, GoalPhasePublicationBindingV1, "expected_binding")
    if binding.coordinate != phase.coordinate:
        raise ValueError("binding coordinate differs from Phase")
    if binding.direction_digest != goal_phase_direction_digest(phase):
        raise ValueError("Phase direction is stale")
    if binding.gate_digest != phase.gate.gate_digest:
        raise ValueError("Phase Gate is stale")
    if binding.work_association_digest != goal_phase_work_association_digest(phase):
        raise ValueError("Phase work associations are stale")


def _validate_mutation_plan(plan: GoalPhaseMutationPlanV1) -> None:
    """Recompute every public mutation-plan invariant and semantic intent."""

    _require_binding(plan.before, plan.expected_binding)
    if plan.before.coordinate != plan.after.coordinate:
        raise ValueError("Phase mutation cannot change coordinate")
    if not plan.evidence_refs:
        raise ValueError("Phase mutation requires publication evidence")
    if plan.operation is GoalPhaseMutationKind.CONTINUE_WORK:
        _validate_continue_work_plan(plan)
        return
    if plan.operation is GoalPhaseMutationKind.ACCEPT_PHASE:
        _validate_accept_phase_plan(plan)
        return
    raise ValueError("unsupported Phase mutation operation")


def _validate_continue_work_plan(plan: GoalPhaseMutationPlanV1) -> None:
    if plan.acceptance_receipt_ref is not None:
        raise ValueError("work continuation cannot carry acceptance receipt")
    if plan.before.state not in (
        GoalLanePhaseState.ACTIVE,
        GoalLanePhaseState.HELD,
    ):
        raise ValueError("same-Gate succession requires active or held Phase")
    if replace(plan.before, work_associations=plan.after.work_associations) != plan.after:
        raise ValueError("work continuation may change only work associations")
    before_work = plan.before.work_associations
    after_work = plan.after.work_associations
    if len(after_work) != len(before_work) + 1:
        raise ValueError("work continuation must append exactly one association")
    current = tuple(
        item
        for item in before_work
        if item.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    if len(current) != 1 or not _work_history_is_prefix(plan.before, plan.after):
        raise ValueError("work continuation does not preserve exact history")
    successor = after_work[-1]
    retired = after_work[len(before_work) - 1]
    expected_association_ref, expected_receipt_ref = _derive_work_admission_refs(
        coordinate=plan.before.coordinate,
        issue_ref=successor.issue_ref,
        role=successor.role,
        admitted_at=successor.admitted_at,
        evidence_refs=plan.evidence_refs,
    )
    if (
        successor.disposition is not GoalLanePhaseWorkDisposition.CURRENT
        or successor.issue_ref == current[0].issue_ref
        or successor.issue_ref in {item.issue_ref for item in before_work}
        or retired.association_ref != current[0].association_ref
        or retired.retired_at != successor.admitted_at
        or successor.association_ref != expected_association_ref
        or successor.receipt_ref != expected_receipt_ref
    ):
        raise ValueError("work continuation successor is not canonical")
    intent = {
        "schema_id": GOAL_PHASE_MUTATION_PLAN_SCHEMA,
        "operation": GoalPhaseMutationKind.CONTINUE_WORK.value,
        "expected_binding": plan.expected_binding.to_wire(),
        "expected_current_issue_ref": current[0].issue_ref,
        "successor": _work_wire(successor),
        "evidence_refs": list(plan.evidence_refs),
    }
    expected_ref = "goal-phase-intent:" + fingerprint(intent)
    if plan.semantic_intent_ref != expected_ref:
        raise ValueError("work continuation semantic intent is not canonical")


def _verify_continue_work_transition(
    before: GoalLanePhase, after: GoalLanePhase
) -> None:
    if before.state not in (GoalLanePhaseState.ACTIVE, GoalLanePhaseState.HELD):
        raise ValueError("work continuation requires active or held Phase")
    if goal_phase_direction_digest(before) != goal_phase_direction_digest(after):
        raise ValueError("continue_work changed Phase direction")
    if before.gate != after.gate:
        raise ValueError("continue_work changed Phase Gate")
    if replace(before, work_associations=after.work_associations) != after:
        raise ValueError("continue_work changed non-Work Phase authority")
    before_work = before.work_associations
    after_work = after.work_associations
    if len(after_work) != len(before_work) + 1:
        raise ValueError("continue_work must append exactly one Work association")
    current = tuple(
        item
        for item in before_work
        if item.disposition is GoalLanePhaseWorkDisposition.CURRENT
    )
    if len(current) != 1 or not _work_history_is_prefix(before, after):
        raise ValueError("continue_work does not preserve exact Work history")
    retired = after_work[len(before_work) - 1]
    successor = after_work[-1]
    if (
        retired.association_ref != current[0].association_ref
        or retired.issue_ref != current[0].issue_ref
        or retired.disposition is not GoalLanePhaseWorkDisposition.RETIRED
        or retired.retired_at != successor.admitted_at
        or successor.disposition is not GoalLanePhaseWorkDisposition.CURRENT
        or successor.issue_ref == current[0].issue_ref
        or successor.issue_ref in {item.issue_ref for item in before_work}
        or _WORK_ASSOCIATION_REF.fullmatch(successor.association_ref) is None
        or _WORK_ADMISSION_REF.fullmatch(successor.receipt_ref) is None
    ):
        raise ValueError("continue_work successor is not canonical")


def _verify_accept_phase_transition(
    before: GoalLanePhase, after: GoalLanePhase
) -> None:
    if before.state not in (GoalLanePhaseState.ACTIVE, GoalLanePhaseState.HELD):
        raise ValueError("accept_phase requires active or held Phase")
    acceptance_ref = after.last_receipt_ref
    if acceptance_ref is None or _ACCEPTANCE_REF.fullmatch(acceptance_ref) is None:
        raise ValueError("accept_phase lacks qualified acceptance authority")
    if replace(
        before,
        state=GoalLanePhaseState.ACCEPTED,
        last_receipt_ref=acceptance_ref,
    ) != after:
        raise ValueError("accept_phase has noncanonical Phase postimage")
    if before.gate != after.gate or before.work_associations != after.work_associations:
        raise ValueError("accept_phase changed Gate or Work authority")
    if not any(
        observation.gate_digest == before.gate.gate_digest
        and observation.outcome is GoalLanePhaseGateOutcome.SATISFIED
        for observation in before.gate_observations
    ):
        raise ValueError("accept_phase lacks satisfied current-Gate evidence")


def _validate_accept_phase_plan(plan: GoalPhaseMutationPlanV1) -> None:
    if plan.before.state not in (
        GoalLanePhaseState.ACTIVE,
        GoalLanePhaseState.HELD,
    ):
        raise ValueError("only active or held Phase may be accepted")
    if plan.acceptance_receipt_ref is None:
        raise ValueError("acceptance plan requires acceptance receipt")
    if plan.acceptance_receipt_ref != plan.after.last_receipt_ref:
        raise ValueError("acceptance plan receipt differs from Phase receipt")
    if replace(
        plan.before,
        state=GoalLanePhaseState.ACCEPTED,
        last_receipt_ref=plan.acceptance_receipt_ref,
    ) != plan.after:
        raise ValueError("acceptance plan has noncanonical Phase postimage")
    matching_intents: list[str] = []
    for observation in plan.before.gate_observations:
        if (
            observation.gate_digest != plan.before.gate.gate_digest
            or observation.outcome is not GoalLanePhaseGateOutcome.SATISFIED
        ):
            continue
        acceptance_body = {
            "schema_id": "aware.goal.phase-acceptance.v1",
            "coordinate": _coordinate_wire(plan.before.coordinate),
            "expected_binding": plan.expected_binding.to_wire(),
            "gate_observation_ref": observation.observation_ref,
            "evidence_refs": list(plan.evidence_refs),
        }
        acceptance_ref = "goal-phase-acceptance:" + fingerprint(acceptance_body)
        if acceptance_ref != plan.acceptance_receipt_ref:
            continue
        intent = {
            "schema_id": GOAL_PHASE_MUTATION_PLAN_SCHEMA,
            "operation": GoalPhaseMutationKind.ACCEPT_PHASE.value,
            **acceptance_body,
            "acceptance_receipt_ref": acceptance_ref,
        }
        matching_intents.append("goal-phase-intent:" + fingerprint(intent))
    if matching_intents != [plan.semantic_intent_ref]:
        raise ValueError("acceptance plan evidence or semantic intent is not canonical")


def _work_history_is_prefix(before: GoalLanePhase, after: GoalLanePhase) -> bool:
    before_items = before.work_associations
    after_items = after.work_associations
    if len(after_items) < len(before_items):
        return False
    for index, item in enumerate(before_items):
        candidate = after_items[index]
        if item == candidate:
            continue
        if (
            index == len(before_items) - 1
            and item.disposition is GoalLanePhaseWorkDisposition.CURRENT
            and candidate.association_ref == item.association_ref
            and candidate.issue_ref == item.issue_ref
            and candidate.role is item.role
            and candidate.admitted_at == item.admitted_at
            and candidate.receipt_ref == item.receipt_ref
            and candidate.disposition is GoalLanePhaseWorkDisposition.RETIRED
            and candidate.retired_at is not None
        ):
            continue
        return False
    return True


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _derive_work_admission_refs(
    *,
    coordinate: GoalPhaseCoordinate,
    issue_ref: str,
    role: GoalLanePhaseWorkRole,
    admitted_at: str,
    evidence_refs: tuple[str, ...],
) -> tuple[str, str]:
    body = {
        "coordinate": _coordinate_wire(coordinate),
        "issue_ref": issue_ref,
        "role": role.value,
        "admitted_at": admitted_at,
        "evidence_refs": list(evidence_refs),
    }
    association_ref = "goal-phase-work:" + fingerprint(body)
    receipt_ref = "goal-phase-work-admission:" + fingerprint(
        {**body, "association_ref": association_ref}
    )
    return association_ref, receipt_ref


def _work_wire(value: GoalLanePhaseWork) -> dict[str, object]:
    return {
        "association_ref": value.association_ref,
        "issue_ref": value.issue_ref,
        "role": value.role.value,
        "disposition": value.disposition.value,
        "admitted_at": value.admitted_at,
        "retired_at": value.retired_at,
        "receipt_ref": value.receipt_ref,
    }


def _evidence(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError("evidence must be exact tuple")
    result = tuple(required_token(item, "evidence_ref") for item in values)
    if result != tuple(sorted(set(result))):
        raise ValueError("evidence must be unique and sorted")
    return result


def _exact(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{field_name} must be exact {expected.__name__}")


def _sha256_ref(value: str, field_name: str) -> str:
    value = required_token(value, field_name)
    if _SHA256_REF.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be exact lowercase SHA-256 ref")
    return value


def _domain_sha256(value: str, domain: str, field_name: str) -> str:
    value = required_token(value, field_name)
    if re.fullmatch(rf"{re.escape(domain)}:sha256:[0-9a-f]{{64}}", value) is None:
        raise ValueError(f"{field_name} must use {domain} SHA-256 domain")
    return value


def _unique_json_object(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _wire_mapping(value: object, field_name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{field_name} must be an exact JSON object")
    return cast(dict[str, object], value)


def _wire_list(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{field_name} must be an exact JSON array")
    return cast(list[object], value)


def _wire_text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exact JSON text")
    return value


def _wire_keys(
    values: dict[str, object], expected: set[str], field_name: str
) -> None:
    if set(values) != expected:
        raise ValueError(f"{field_name} fields are noncanonical")


def _decode_coordinate(value: object) -> GoalPhaseCoordinate:
    values = _wire_mapping(value, "coordinate")
    _wire_keys(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        goal_tag=_wire_text(values["goal_tag"], "goal_tag"),
        lane_key=_wire_text(values["lane_key"], "lane_key"),
        phase_key=_wire_text(values["phase_key"], "phase_key"),
    )


def _decode_projection_revision(value: object) -> GoalPhaseProjectionRevisionV1:
    values = _wire_mapping(value, "projection_revision")
    _wire_keys(
        values,
        {"repository_ref", "repository_commit", "phase_blob_oid", "source_sha256"},
        "projection_revision",
    )
    return GoalPhaseProjectionRevisionV1(
        repository_ref=_wire_text(values["repository_ref"], "repository_ref"),
        repository_commit=_wire_text(
            values["repository_commit"], "repository_commit"
        ),
        phase_blob_oid=_wire_text(values["phase_blob_oid"], "phase_blob_oid"),
        source_sha256=_wire_text(values["source_sha256"], "source_sha256"),
    )


def _decode_publication_binding(value: object) -> GoalPhasePublicationBindingV1:
    values = _wire_mapping(value, "publication_binding")
    _wire_keys(
        values,
        {
            "schema_id",
            "coordinate",
            "direction_digest",
            "gate_digest",
            "work_association_digest",
            "projection_revision",
        },
        "publication_binding",
    )
    return GoalPhasePublicationBindingV1(
        schema_id=_wire_text(values["schema_id"], "schema_id"),
        coordinate=_decode_coordinate(values["coordinate"]),
        direction_digest=_wire_text(values["direction_digest"], "direction_digest"),
        gate_digest=_wire_text(values["gate_digest"], "gate_digest"),
        work_association_digest=_wire_text(
            values["work_association_digest"], "work_association_digest"
        ),
        projection_revision=_decode_projection_revision(
            values["projection_revision"]
        ),
    )


__all__ = [
    "GOAL_PHASE_MUTATION_PLAN_SCHEMA",
    "GOAL_PHASE_PUBLICATION_BINDING_SCHEMA",
    "GOAL_PHASE_PUBLICATION_RECEIPT_SCHEMA",
    "GOAL_PHASE_RECONCILIATION_RECEIPT_SCHEMA",
    "GoalPhaseDigestCurrentness",
    "GoalPhaseMutationKind",
    "GoalPhaseMutationPlanV1",
    "GoalPhaseProjectionCurrentness",
    "GoalPhaseProjectionReconciliationReceiptV1",
    "GoalPhaseProjectionRelation",
    "GoalPhaseProjectionRevisionV1",
    "GoalPhasePublicationBindingV1",
    "GoalPhasePublicationCurrentnessV1",
    "GoalPhasePublicationReceiptV1",
    "GoalPhasePublicationState",
    "GoalPhaseReplayDisposition",
    "GoalPhaseWorkCurrentness",
    "assess_goal_phase_publication_currentness",
    "bind_goal_phase_publication",
    "decode_goal_phase_publication_receipt",
    "goal_phase_direction_digest",
    "goal_phase_work_association_digest",
    "issue_goal_phase_publication_receipt",
    "plan_goal_phase_acceptance",
    "plan_goal_phase_same_gate_successor",
    "reconcile_goal_phase_projection",
    "verify_goal_phase_publication_transition",
]
