"""Migration-only publication of one evaluated operational Phase in a V2 Goal."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from typing import cast

from .identity import fingerprint, required_token
from .phase_codec import goal_phase_bundle_to_wire
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)
from .phase_document import GoalLanePhaseDefinitionV1, GoalPhaseNativeDocumentV2
from .phase_migrated_definition_qualification import (
    GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1,
)
from .phase_migrated_gate_evaluation import (
    EvaluationResult,
    MigratedPhaseGateEvaluationV1,
    VerifiedMigratedPhaseGateAuthorityV1,
    evaluate_migrated_phase_gate,
)

PLAN_SCHEMA = "aware.goal.migrated-phase-qualification-plan.v1"
RECEIPT_SCHEMA = "aware.goal.migrated-phase-qualification-publication-receipt.v1"
RECONCILIATION_SCHEMA = "aware.goal.migrated-phase-projection-reconciliation.v1"
_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class GoalPhaseMigratedQualificationError(ValueError):
    """The requested migrated-Phase publication lacks exact authority."""


def _coordinate(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _phase_wire(value: GoalLanePhase) -> dict[str, object]:
    bundle = GoalPhaseContractBundleV1(phases=(value,), dependencies=())
    phases = cast(list[object], goal_phase_bundle_to_wire(bundle)["phases"])
    return cast(dict[str, object], phases[0])


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _derive(
    *,
    document: GoalPhaseNativeDocumentV2,
    m13_receipt: GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1,
    verified: VerifiedMigratedPhaseGateAuthorityV1,
    issue_ref: str,
    admitted_at: str,
    evaluated_at: str,
) -> tuple[
    GoalPhaseNativeDocumentV2,
    GoalLanePhase,
    MigratedPhaseGateEvaluationV1,
    GoalLanePhaseDefinitionV1,
]:
    if type(document) is not GoalPhaseNativeDocumentV2:
        raise TypeError("migrated qualification requires exact V2 document")
    document.__post_init__()
    if type(m13_receipt) is not GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1:
        raise TypeError("M13 receipt must be exact")
    m13_receipt.__post_init__()
    evaluation = evaluate_migrated_phase_gate(verified)
    proposal = verified.proposal
    if evaluation.result is not EvaluationResult.SATISFIED:
        raise GoalPhaseMigratedQualificationError("M14 evaluation is not satisfied")
    if any(
        item.coordinate == proposal.coordinate
        for item in document.operational_bundle.phases
    ):
        raise GoalPhaseMigratedQualificationError("target Phase is already operational")
    if proposal.goal_tag != document.goal_tag or proposal.document_ref != document.document_ref:
        raise GoalPhaseMigratedQualificationError("M14 source document differs")
    if m13_receipt.after_document_ref != document.document_ref:
        raise GoalPhaseMigratedQualificationError("M13-qualified document differs")
    if m13_receipt.changed_path != proposal.goal_path:
        raise GoalPhaseMigratedQualificationError("M13 Goal path differs")
    matches = tuple(
        item for item in document.definitions if item.coordinate == proposal.coordinate
    )
    if len(matches) != 1:
        raise GoalPhaseMigratedQualificationError("target definition is not unique")
    definition = matches[0]
    if definition.title is None or definition.intent is None:
        raise GoalPhaseMigratedQualificationError("target definition is incomplete")
    if (
        definition.definition_ref != proposal.definition_ref
        or definition.definition_ref != m13_receipt.after_definition_ref
        or definition.gate.gate_digest != proposal.gate_digest
    ):
        raise GoalPhaseMigratedQualificationError("qualified definition or Gate differs")
    if "invariant:legacy-lifecycle-is-source-snapshot" not in definition.gate.invariant_refs:
        raise GoalPhaseMigratedQualificationError("migration provenance is absent")
    incoming = tuple(
        sorted(
            (
                item.dependency_key
                for item in document.operational_bundle.dependencies
                if item.dependent == proposal.coordinate
            )
        )
    )
    if incoming != tuple(item.dependency_key for item in proposal.dependency_bindings):
        raise GoalPhaseMigratedQualificationError("incoming dependency set differs")
    issue = required_token(issue_ref, "issue_ref")
    if evaluation.gate_observation_ref is None:
        raise GoalPhaseMigratedQualificationError("satisfied Gate observation is absent")
    evidence = tuple(
        sorted(
            {
                m13_receipt.receipt_ref,
                evaluation.evaluation_ref,
                verified.acceptance.acceptance_ref,
                verified.bundle.bundle_ref,
            }
        )
    )
    observation = GoalLanePhaseGateObservation(
        observation_ref=evaluation.gate_observation_ref,
        gate_digest=definition.gate.gate_digest,
        outcome=GoalLanePhaseGateOutcome.SATISFIED,
        evaluator_ref=evaluation.evaluator_ref,
        evidence_refs=evidence,
        source_revision_refs=(proposal.source_revision_ref,),
        evaluated_at=evaluated_at,
        currentness_ref=evaluation.currentness_ref,
    )
    work_body = {
        "coordinate": _coordinate(proposal.coordinate),
        "issue_ref": issue,
        "role": GoalLanePhaseWorkRole.ACCEPTANCE.value,
        "admitted_at": admitted_at,
        "evidence_refs": list(evidence),
    }
    association_ref = "goal-phase-work:" + fingerprint(work_body)
    work = GoalLanePhaseWork(
        association_ref=association_ref,
        issue_ref=issue,
        role=GoalLanePhaseWorkRole.ACCEPTANCE,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at=admitted_at,
        receipt_ref="goal-phase-work-admission:"
        + fingerprint({**work_body, "association_ref": association_ref}),
    )
    acceptance_body = {
        "schema_id": "aware.goal.migrated-phase-acceptance.v1",
        "before_document_ref": document.document_ref,
        "coordinate": _coordinate(proposal.coordinate),
        "definition_ref": definition.definition_ref,
        "gate_digest": definition.gate.gate_digest,
        "gate_observation_ref": observation.observation_ref,
        "work_association_ref": association_ref,
        "m13_receipt_ref": m13_receipt.receipt_ref,
        "m14_evaluation_ref": evaluation.evaluation_ref,
    }
    phase = GoalLanePhase(
        coordinate=definition.coordinate,
        title=definition.title,
        ordinal=definition.ordinal,
        intent=definition.intent,
        state=GoalLanePhaseState.ACCEPTED,
        gate=definition.gate,
        gate_observations=(observation,),
        work_associations=(work,),
        last_receipt_ref="goal-phase-acceptance:" + fingerprint(acceptance_body),
    )
    bundle = GoalPhaseContractBundleV1(
        phases=document.operational_bundle.phases + (phase,),
        dependencies=document.operational_bundle.dependencies,
    )
    successor = replace(document, operational_bundle=bundle)
    return successor, phase, evaluation, definition


@dataclass(frozen=True, slots=True)
class GoalPhaseMigratedQualificationPlanV1:
    before_document: GoalPhaseNativeDocumentV2
    after_document: GoalPhaseNativeDocumentV2
    phase: GoalLanePhase
    m13_receipt: GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1
    verified_m14: VerifiedMigratedPhaseGateAuthorityV1
    evaluation: MigratedPhaseGateEvaluationV1
    issue_ref: str
    admitted_at: str
    evaluated_at: str
    semantic_intent_ref: str = field(init=False)
    schema_id: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMigratedQualificationPlanV1 or self.schema_id != PLAN_SCHEMA:
            raise GoalPhaseMigratedQualificationError("wrong qualification plan schema")
        successor, phase, evaluation, _ = _derive(
            document=self.before_document,
            m13_receipt=self.m13_receipt,
            verified=self.verified_m14,
            issue_ref=self.issue_ref,
            admitted_at=self.admitted_at,
            evaluated_at=self.evaluated_at,
        )
        if self.after_document != successor or self.phase != phase or self.evaluation != evaluation:
            raise GoalPhaseMigratedQualificationError("qualification plan is not canonical")
        body = self.body()
        object.__setattr__(
            self,
            "semantic_intent_ref",
            "goal-migrated-phase-qualification-intent:" + fingerprint(body),
        )

    def body(self) -> dict[str, object]:
        return {
            "schema_id": PLAN_SCHEMA,
            "before_document_ref": self.before_document.document_ref,
            "after_document_ref": self.after_document.document_ref,
            "coordinate": _coordinate(self.phase.coordinate),
            "phase": _phase_wire(self.phase),
            "m13_receipt_ref": self.m13_receipt.receipt_ref,
            "m14_evaluation_ref": self.evaluation.evaluation_ref,
            "issue_ref": self.issue_ref,
            "admitted_at": self.admitted_at,
            "evaluated_at": self.evaluated_at,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "semantic_intent_ref": self.semantic_intent_ref}


def plan_goal_phase_migrated_qualification(
    *,
    document: GoalPhaseNativeDocumentV2,
    m13_receipt: GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1,
    verified_m14: VerifiedMigratedPhaseGateAuthorityV1,
    issue_ref: str,
    admitted_at: str,
    evaluated_at: str,
) -> GoalPhaseMigratedQualificationPlanV1:
    """Plan only the canonical accepted-Phase addition from sealed M14 evidence."""

    after, phase, evaluation, _ = _derive(
        document=document,
        m13_receipt=m13_receipt,
        verified=verified_m14,
        issue_ref=issue_ref,
        admitted_at=admitted_at,
        evaluated_at=evaluated_at,
    )
    return GoalPhaseMigratedQualificationPlanV1(
        before_document=document,
        after_document=after,
        phase=phase,
        m13_receipt=m13_receipt,
        verified_m14=verified_m14,
        evaluation=evaluation,
        issue_ref=issue_ref,
        admitted_at=admitted_at,
        evaluated_at=evaluated_at,
    )


@dataclass(frozen=True, slots=True)
class GoalPhaseMigratedQualificationPublicationReceiptV1:
    semantic_intent_ref: str
    before_document_ref: str
    after_document_ref: str
    phase_digest: str
    m13_receipt_ref: str
    before_definition_ref: str
    after_definition_ref: str
    m14_evaluation_ref: str
    m14_verification_ref: str
    gate_digest: str
    gate_observation_ref: str
    dependency_observation_refs: tuple[str, ...]
    work_association_ref: str
    acceptance_ref: str
    execution_authority_ref: str
    publication_issue_authority_ref: str
    repository_parent_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    changed_path: str
    receipt_ref: str = field(init=False)
    schema_id: str = RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMigratedQualificationPublicationReceiptV1 or self.schema_id != RECEIPT_SCHEMA:
            raise GoalPhaseMigratedQualificationError("wrong publication receipt schema")
        for name in (
            "semantic_intent_ref", "before_document_ref", "after_document_ref",
            "phase_digest", "m13_receipt_ref", "before_definition_ref",
            "after_definition_ref", "m14_evaluation_ref", "m14_verification_ref",
            "gate_digest", "gate_observation_ref", "work_association_ref",
            "acceptance_ref", "execution_authority_ref",
            "publication_issue_authority_ref", "changed_path",
        ):
            _ = required_token(cast(object, getattr(self, name)), name)
        if type(self.dependency_observation_refs) is not tuple or self.dependency_observation_refs != tuple(sorted(set(self.dependency_observation_refs))):
            raise GoalPhaseMigratedQualificationError("dependency observations are not canonical")
        for reference in self.dependency_observation_refs:
            _ = required_token(reference, "dependency_observation_ref")
        for name in ("repository_parent_ref", "repository_commit_ref"):
            if _OID.fullmatch(required_token(cast(object, getattr(self, name)), name)) is None:
                raise GoalPhaseMigratedQualificationError(f"{name} is not a Git OID")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.repository_commit_ref}":
            raise GoalPhaseMigratedQualificationError("repository receipt differs")
        object.__setattr__(
            self,
            "receipt_ref",
            "goal-migrated-phase-qualification-publication:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "schema_id": RECEIPT_SCHEMA,
            "semantic_intent_ref": self.semantic_intent_ref,
            "before_document_ref": self.before_document_ref,
            "after_document_ref": self.after_document_ref,
            "phase_digest": self.phase_digest,
            "m13_receipt_ref": self.m13_receipt_ref,
            "before_definition_ref": self.before_definition_ref,
            "after_definition_ref": self.after_definition_ref,
            "m14_evaluation_ref": self.m14_evaluation_ref,
            "m14_verification_ref": self.m14_verification_ref,
            "gate_digest": self.gate_digest,
            "gate_observation_ref": self.gate_observation_ref,
            "dependency_observation_refs": list(self.dependency_observation_refs),
            "work_association_ref": self.work_association_ref,
            "acceptance_ref": self.acceptance_ref,
            "execution_authority_ref": self.execution_authority_ref,
            "publication_issue_authority_ref": self.publication_issue_authority_ref,
            "repository_parent_ref": self.repository_parent_ref,
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "changed_path": self.changed_path,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "receipt_ref": self.receipt_ref}


def issue_goal_phase_migrated_qualification_publication_receipt(
    *,
    plan: GoalPhaseMigratedQualificationPlanV1,
    publication_issue_authority_ref: str,
    repository_parent_ref: str,
    repository_commit_ref: str,
    changed_path: str,
) -> GoalPhaseMigratedQualificationPublicationReceiptV1:
    plan.__post_init__()
    if changed_path != plan.verified_m14.proposal.goal_path:
        raise GoalPhaseMigratedQualificationError("publication Goal path differs")
    return GoalPhaseMigratedQualificationPublicationReceiptV1(
        semantic_intent_ref=plan.semantic_intent_ref,
        before_document_ref=plan.before_document.document_ref,
        after_document_ref=plan.after_document.document_ref,
        phase_digest=fingerprint({"phase": _phase_wire(plan.phase)}),
        m13_receipt_ref=plan.m13_receipt.receipt_ref,
        before_definition_ref=plan.m13_receipt.before_definition_ref,
        after_definition_ref=plan.m13_receipt.after_definition_ref,
        m14_evaluation_ref=plan.evaluation.evaluation_ref,
        m14_verification_ref=plan.verified_m14.verification_ref,
        gate_digest=plan.phase.gate.gate_digest,
        gate_observation_ref=plan.phase.gate_observations[0].observation_ref,
        dependency_observation_refs=plan.evaluation.dependency_observation_refs,
        work_association_ref=plan.phase.work_associations[0].association_ref,
        acceptance_ref=cast(str, plan.phase.last_receipt_ref),
        execution_authority_ref=plan.before_document.execution_authority.authority_ref,
        publication_issue_authority_ref=publication_issue_authority_ref,
        repository_parent_ref=repository_parent_ref,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=f"repository-commit:{repository_commit_ref}",
        changed_path=changed_path,
    )


def decode_goal_phase_migrated_qualification_publication_receipt(
    payload: bytes,
) -> GoalPhaseMigratedQualificationPublicationReceiptV1:
    if type(payload) is not bytes:
        raise TypeError("receipt payload must be exact bytes")
    try:
        raw = cast(object, json.loads(payload.decode("utf-8"), object_pairs_hook=_unique))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseMigratedQualificationError("receipt is not JSON") from error
    if type(raw) is not dict:
        raise GoalPhaseMigratedQualificationError("receipt fields differ")
    values = cast(dict[str, object], raw)
    if set(values) != set(GoalPhaseMigratedQualificationPublicationReceiptV1.__dataclass_fields__):
        raise GoalPhaseMigratedQualificationError("receipt fields differ")
    if values.pop("schema_id") != RECEIPT_SCHEMA:
        raise GoalPhaseMigratedQualificationError("receipt schema differs")
    supplied_ref = values.pop("receipt_ref")
    references = values.get("dependency_observation_refs")
    if type(references) is not list:
        raise GoalPhaseMigratedQualificationError("dependency observations differ")
    reference_items = cast(list[object], references)
    if any(type(item) is not str for item in reference_items):
        raise GoalPhaseMigratedQualificationError("dependency observations differ")

    def field_text(name: str) -> str:
        value = values[name]
        if type(value) is not str:
            raise GoalPhaseMigratedQualificationError(f"{name} must be exact text")
        return value

    receipt = GoalPhaseMigratedQualificationPublicationReceiptV1(
        semantic_intent_ref=field_text("semantic_intent_ref"),
        before_document_ref=field_text("before_document_ref"),
        after_document_ref=field_text("after_document_ref"),
        phase_digest=field_text("phase_digest"),
        m13_receipt_ref=field_text("m13_receipt_ref"),
        before_definition_ref=field_text("before_definition_ref"),
        after_definition_ref=field_text("after_definition_ref"),
        m14_evaluation_ref=field_text("m14_evaluation_ref"),
        m14_verification_ref=field_text("m14_verification_ref"),
        gate_digest=field_text("gate_digest"),
        gate_observation_ref=field_text("gate_observation_ref"),
        dependency_observation_refs=tuple(cast(list[str], reference_items)),
        work_association_ref=field_text("work_association_ref"),
        acceptance_ref=field_text("acceptance_ref"),
        execution_authority_ref=field_text("execution_authority_ref"),
        publication_issue_authority_ref=field_text("publication_issue_authority_ref"),
        repository_parent_ref=field_text("repository_parent_ref"),
        repository_commit_ref=field_text("repository_commit_ref"),
        repository_commit_receipt_ref=field_text("repository_commit_receipt_ref"),
        changed_path=field_text("changed_path"),
    )
    if supplied_ref != receipt.receipt_ref or payload != _canonical(receipt.to_wire()):
        raise GoalPhaseMigratedQualificationError("receipt is not canonical")
    return receipt


@dataclass(frozen=True, slots=True)
class GoalPhaseMigratedQualificationReconciliationV1:
    publication_receipt: GoalPhaseMigratedQualificationPublicationReceiptV1
    authoritative_commit: str
    authoritative_goal_sha256: str
    worktree_disposition: str
    receipt_ref: str = field(init=False)
    schema_id: str = RECONCILIATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMigratedQualificationReconciliationV1 or self.schema_id != RECONCILIATION_SCHEMA:
            raise GoalPhaseMigratedQualificationError("wrong reconciliation schema")
        if type(self.publication_receipt) is not GoalPhaseMigratedQualificationPublicationReceiptV1:
            raise GoalPhaseMigratedQualificationError("reconciliation publication receipt is not exact")
        original_publication_ref = self.publication_receipt.receipt_ref
        self.publication_receipt.__post_init__()
        if self.publication_receipt.receipt_ref != original_publication_ref:
            raise GoalPhaseMigratedQualificationError("publication receipt changed before reconciliation")
        if _OID.fullmatch(required_token(self.authoritative_commit, "authoritative_commit")) is None:
            raise GoalPhaseMigratedQualificationError("reconciliation commit is not a Git OID")
        if _SHA256.fullmatch(required_token(self.authoritative_goal_sha256, "authoritative_goal_sha256")) is None:
            raise GoalPhaseMigratedQualificationError("reconciliation Goal digest differs")
        if self.worktree_disposition not in {"planned", "clear", "required"}:
            raise GoalPhaseMigratedQualificationError("reconciliation worktree disposition differs")
        object.__setattr__(
            self,
            "receipt_ref",
            "goal-migrated-phase-projection-reconciliation:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "schema_id": RECONCILIATION_SCHEMA,
            "publication_receipt": self.publication_receipt.to_wire(),
            "authoritative_commit": self.authoritative_commit,
            "authoritative_goal_sha256": self.authoritative_goal_sha256,
            "index_current": True,
            "worktree_disposition": self.worktree_disposition,
            "repository_commit_created": False,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "receipt_ref": self.receipt_ref}


def decode_goal_phase_migrated_qualification_reconciliation(
    payload: bytes,
) -> GoalPhaseMigratedQualificationReconciliationV1:
    if type(payload) is not bytes:
        raise TypeError("reconciliation payload must be exact bytes")
    try:
        raw = cast(object, json.loads(payload.decode("utf-8"), object_pairs_hook=_unique))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseMigratedQualificationError("reconciliation is not JSON") from error
    if type(raw) is not dict:
        raise GoalPhaseMigratedQualificationError("reconciliation fields differ")
    values = cast(dict[str, object], raw)
    if set(values) != {
        "schema_id", "publication_receipt", "authoritative_commit",
        "authoritative_goal_sha256", "index_current", "worktree_disposition",
        "repository_commit_created", "receipt_ref",
    }:
        raise GoalPhaseMigratedQualificationError("reconciliation fields differ")
    if values["schema_id"] != RECONCILIATION_SCHEMA or values["index_current"] is not True or values["repository_commit_created"] is not False:
        raise GoalPhaseMigratedQualificationError("reconciliation authority fields differ")
    publication_payload = _canonical(values["publication_receipt"])
    publication = decode_goal_phase_migrated_qualification_publication_receipt(publication_payload)
    for name in ("authoritative_commit", "authoritative_goal_sha256", "worktree_disposition"):
        if type(values[name]) is not str:
            raise GoalPhaseMigratedQualificationError(f"{name} must be exact text")
    result = GoalPhaseMigratedQualificationReconciliationV1(
        publication_receipt=publication,
        authoritative_commit=cast(str, values["authoritative_commit"]),
        authoritative_goal_sha256=cast(str, values["authoritative_goal_sha256"]),
        worktree_disposition=cast(str, values["worktree_disposition"]),
    )
    if values["receipt_ref"] != result.receipt_ref or payload != _canonical(result.to_wire()):
        raise GoalPhaseMigratedQualificationError("reconciliation is not canonical")
    return result


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseMigratedQualificationError("duplicate JSON key")
        result[key] = value
    return result
