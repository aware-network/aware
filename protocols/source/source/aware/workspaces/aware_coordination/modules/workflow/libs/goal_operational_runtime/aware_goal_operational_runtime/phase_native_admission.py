"""Canonical admission of one Phase into an existing native Goal document."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .identity import fingerprint, required_token
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)
from .phase_document import (
    GoalLanePhaseDefinitionV1,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
)

GOAL_PHASE_NATIVE_ADMISSION_PLAN_SCHEMA = "aware.goal.phase-native-admission-plan.v1"
GOAL_PHASE_NATIVE_ADMISSION_RECEIPT_SCHEMA = (
    "aware.goal.phase-native-admission-publication-receipt.v1"
)


class GoalPhaseNativeAdmissionError(ValueError):
    """A native Phase admission request or publication is invalid."""


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeAdmissionPlanV1:
    before_document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2
    after_document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2
    definition: GoalLanePhaseDefinitionV1
    phase: GoalLanePhase
    dependencies: tuple[GoalPhaseDependency, ...]
    evidence_refs: tuple[str, ...]
    semantic_intent_ref: str
    source_refs: tuple[str, ...] = ()
    schema_id: str = GOAL_PHASE_NATIVE_ADMISSION_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_ADMISSION_PLAN_SCHEMA:
            raise GoalPhaseNativeAdmissionError("unsupported admission-plan schema")
        if type(self.before_document) not in {
            GoalPhaseNativeDocumentV1,
            GoalPhaseNativeDocumentV2,
        }:
            raise TypeError("before_document must be a native Goal document")
        if type(self.after_document) is not type(self.before_document):
            raise TypeError("after_document must preserve the native document version")
        if type(self.definition) is not GoalLanePhaseDefinitionV1:
            raise TypeError("definition must be GoalLanePhaseDefinitionV1")
        if type(self.phase) is not GoalLanePhase:
            raise TypeError("phase must be GoalLanePhase")
        _ = required_token(self.semantic_intent_ref, "semantic_intent_ref")
        if type(self.before_document) is GoalPhaseNativeDocumentV2:
            _ = _tokens(self.source_refs, "source_refs")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "before_document_ref": self.before_document.document_ref,
            "after_document_ref": self.after_document.document_ref,
            "coordinate": _coordinate_wire(self.phase.coordinate),
            "definition_ref": self.definition.definition_ref,
            "gate_digest": self.phase.gate.gate_digest,
            "initial_issue_ref": self.phase.work_associations[0].issue_ref,
            "work_association_ref": self.phase.work_associations[0].association_ref,
            "work_admission_receipt_ref": self.phase.work_associations[0].receipt_ref,
            "dependency_keys": [item.dependency_key for item in self.dependencies],
            "evidence_refs": list(self.evidence_refs),
            "semantic_intent_ref": self.semantic_intent_ref,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeAdmissionPublicationReceiptV1:
    plan_ref: str
    before_document_ref: str
    after_document_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    changed_path: str
    receipt_ref: str = field(init=False)
    schema_id: str = GOAL_PHASE_NATIVE_ADMISSION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_PHASE_NATIVE_ADMISSION_RECEIPT_SCHEMA:
            raise GoalPhaseNativeAdmissionError("unsupported admission receipt schema")
        for name, value in (
            ("plan_ref", self.plan_ref),
            ("before_document_ref", self.before_document_ref),
            ("after_document_ref", self.after_document_ref),
            ("repository_commit_ref", self.repository_commit_ref),
            ("repository_commit_receipt_ref", self.repository_commit_receipt_ref),
            ("changed_path", self.changed_path),
        ):
            if type(value) is not str:
                raise TypeError(f"{name} must be exact str")
            _ = required_token(value, name)
        body = self.to_wire(include_ref=False)
        object.__setattr__(
            self,
            "receipt_ref",
            "goal-phase-native-admission-publication:" + fingerprint(body),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "plan_ref": self.plan_ref,
            "before_document_ref": self.before_document_ref,
            "after_document_ref": self.after_document_ref,
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "changed_path": self.changed_path,
        }
        if include_ref:
            body["receipt_ref"] = self.receipt_ref
        return body


def plan_goal_phase_native_admission(
    *,
    document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2,
    coordinate: GoalPhaseCoordinate,
    ordinal: int,
    title: str,
    intent: str,
    gate: GoalLanePhaseGate,
    issue_ref: str,
    work_role: GoalLanePhaseWorkRole,
    admitted_at: str,
    work_evidence_refs: tuple[str, ...],
    dependencies: tuple[GoalPhaseDependency, ...],
    evidence_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> GoalPhaseNativeAdmissionPlanV1:
    """Plan one exact definition/Phase/Work/dependency native postimage."""

    if type(document) not in {GoalPhaseNativeDocumentV1, GoalPhaseNativeDocumentV2}:
        raise TypeError("document must be a native Goal document")
    if type(coordinate) is not GoalPhaseCoordinate:
        raise TypeError("coordinate must be GoalPhaseCoordinate")
    if coordinate.goal_tag != document.goal_tag:
        raise GoalPhaseNativeAdmissionError("coordinate belongs to another Goal")
    if type(ordinal) is not int or ordinal < 1:
        raise GoalPhaseNativeAdmissionError("ordinal must be a positive integer")
    if any(item.coordinate == coordinate for item in document.definitions):
        raise GoalPhaseNativeAdmissionError("Phase definition already exists")
    if any(
        item.coordinate == coordinate for item in document.operational_bundle.phases
    ):
        raise GoalPhaseNativeAdmissionError("operational Phase already exists")
    if type(work_role) is not GoalLanePhaseWorkRole:
        raise TypeError("work_role must be GoalLanePhaseWorkRole")
    work_evidence = _tokens(work_evidence_refs, "work_evidence_refs")
    evidence = _tokens(evidence_refs, "evidence_refs")
    new_source_refs = _tokens(source_refs, "source_refs")
    if not work_evidence or not evidence or not new_source_refs:
        raise GoalPhaseNativeAdmissionError("admission requires explicit evidence")
    if work_evidence != evidence:
        raise GoalPhaseNativeAdmissionError(
            "V1 uses one exact evidence set for Work and admission"
        )
    issue = required_token(issue_ref, "issue_ref")
    definition = GoalLanePhaseDefinitionV1(
        coordinate=coordinate,
        ordinal=ordinal,
        gate=gate,
        title=title,
        intent=intent,
    )
    association_ref, work_receipt_ref = _derive_work_refs(
        coordinate=coordinate,
        issue_ref=issue,
        role=work_role,
        admitted_at=admitted_at,
        evidence_refs=work_evidence,
    )
    work = GoalLanePhaseWork(
        association_ref=association_ref,
        issue_ref=issue,
        role=work_role,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at=admitted_at,
        receipt_ref=work_receipt_ref,
    )
    phase = GoalLanePhase(
        coordinate=coordinate,
        title=title,
        ordinal=ordinal,
        intent=intent,
        state=GoalLanePhaseState.ACTIVE,
        gate=gate,
        work_associations=(work,),
    )
    if type(dependencies) is not tuple:
        raise TypeError("dependencies must be exact tuple")
    dependency_keys = tuple(item.dependency_key for item in dependencies)
    if dependency_keys != tuple(sorted(set(dependency_keys))):
        raise GoalPhaseNativeAdmissionError(
            "dependencies must have unique sorted identities"
        )
    for dependency in dependencies:
        if type(dependency) is not GoalPhaseDependency:
            raise TypeError("dependencies contain invalid value")
        if dependency.dependent != coordinate:
            raise GoalPhaseNativeAdmissionError(
                "every admitted dependency must target the new Phase"
            )
    after_bundle = GoalPhaseContractBundleV1(
        phases=document.operational_bundle.phases + (phase,),
        dependencies=document.operational_bundle.dependencies + dependencies,
    )
    if type(document) is GoalPhaseNativeDocumentV2:
        after_document = replace(
            document,
            definitions=document.definitions + (definition,),
            operational_bundle=after_bundle,
            source_refs=document.source_refs,
        )
    else:
        after_document = replace(
            document,
            definitions=document.definitions + (definition,),
            operational_bundle=after_bundle,
            source_refs=tuple(sorted(set(document.source_refs + new_source_refs))),
        )
    body = {
        "schema_id": GOAL_PHASE_NATIVE_ADMISSION_PLAN_SCHEMA,
        "before_document_ref": document.document_ref,
        "after_document_ref": after_document.document_ref,
        "coordinate": _coordinate_wire(coordinate),
        "definition_ref": definition.definition_ref,
        "gate_digest": gate.gate_digest,
        "work": _work_wire(work),
        "dependencies": [_dependency_wire(item) for item in dependencies],
        "work_evidence_refs": list(work_evidence),
        "evidence_refs": list(evidence),
        "source_refs": list(new_source_refs),
    }
    return GoalPhaseNativeAdmissionPlanV1(
        before_document=document,
        after_document=after_document,
        definition=definition,
        phase=phase,
        dependencies=dependencies,
        evidence_refs=evidence,
        semantic_intent_ref="goal-phase-native-admission-intent:" + fingerprint(body),
        source_refs=new_source_refs if type(document) is GoalPhaseNativeDocumentV2 else (),
    )


def issue_goal_phase_native_admission_publication_receipt(
    *,
    plan: GoalPhaseNativeAdmissionPlanV1,
    repository_commit_ref: str,
    repository_commit_receipt_ref: str,
    changed_path: str,
) -> GoalPhaseNativeAdmissionPublicationReceiptV1:
    if type(plan) is not GoalPhaseNativeAdmissionPlanV1:
        raise TypeError("plan must be GoalPhaseNativeAdmissionPlanV1")
    _validate_plan(plan)
    return GoalPhaseNativeAdmissionPublicationReceiptV1(
        plan_ref=plan.semantic_intent_ref,
        before_document_ref=plan.before_document.document_ref,
        after_document_ref=plan.after_document.document_ref,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=repository_commit_receipt_ref,
        changed_path=changed_path,
    )


def _validate_plan(plan: GoalPhaseNativeAdmissionPlanV1) -> None:
    before = plan.before_document
    if type(before) is GoalPhaseNativeDocumentV2:
        new_source_refs = plan.source_refs
    else:
        new_source_refs = tuple(
            item for item in plan.after_document.source_refs if item not in before.source_refs
        )
    canonical = plan_goal_phase_native_admission(
        document=before,
        coordinate=plan.phase.coordinate,
        ordinal=plan.phase.ordinal,
        title=plan.phase.title,
        intent=plan.phase.intent,
        gate=plan.phase.gate,
        issue_ref=plan.phase.work_associations[0].issue_ref,
        work_role=plan.phase.work_associations[0].role,
        admitted_at=plan.phase.work_associations[0].admitted_at,
        work_evidence_refs=_recover_work_evidence(plan),
        dependencies=plan.dependencies,
        evidence_refs=plan.evidence_refs,
        source_refs=new_source_refs,
    )
    if canonical.after_document != plan.after_document:
        raise GoalPhaseNativeAdmissionError("admission postimage is not canonical")
    if canonical.definition != plan.definition or canonical.phase != plan.phase:
        raise GoalPhaseNativeAdmissionError("admission values are not canonical")
    if canonical.semantic_intent_ref == plan.semantic_intent_ref:
        return
    if type(before) is GoalPhaseNativeDocumentV2:
        raise GoalPhaseNativeAdmissionError("semantic intent is not canonical")
    # The repository publisher intentionally supplies the governed Goal path
    # alongside the new commit coordinate. A native document already carries
    # that path, so it disappears from the set-based postimage and cannot be
    # recovered by a simple before/after difference. Reproduce that one
    # semantically redundant, authority-qualified input explicitly; no other
    # pre-existing source reference is eligible for this compatibility case.
    repeated_repository_paths = tuple(
        item for item in before.source_refs if item.startswith("repository-path:")
    )
    if repeated_repository_paths:
        canonical_with_path = plan_goal_phase_native_admission(
            document=before,
            coordinate=plan.phase.coordinate,
            ordinal=plan.phase.ordinal,
            title=plan.phase.title,
            intent=plan.phase.intent,
            gate=plan.phase.gate,
            issue_ref=plan.phase.work_associations[0].issue_ref,
            work_role=plan.phase.work_associations[0].role,
            admitted_at=plan.phase.work_associations[0].admitted_at,
            work_evidence_refs=_recover_work_evidence(plan),
            dependencies=plan.dependencies,
            evidence_refs=plan.evidence_refs,
            source_refs=tuple(sorted(new_source_refs + repeated_repository_paths)),
        )
        if canonical_with_path.semantic_intent_ref == plan.semantic_intent_ref:
            return
    raise GoalPhaseNativeAdmissionError("semantic intent is not canonical")


def _recover_work_evidence(plan: GoalPhaseNativeAdmissionPlanV1) -> tuple[str, ...]:
    # Work evidence is intentionally the admission evidence in V1. Keeping one
    # evidence set makes the derived association independently reproducible.
    return plan.evidence_refs


def _derive_work_refs(
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
    return association_ref, "goal-phase-work-admission:" + fingerprint(
        {**body, "association_ref": association_ref}
    )


def _tokens(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be exact tuple")
    result = tuple(required_token(item, name) for item in values)
    if result != tuple(sorted(set(result))):
        raise GoalPhaseNativeAdmissionError(f"{name} must be unique and sorted")
    return result


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


def _work_wire(value: GoalLanePhaseWork) -> dict[str, object]:
    return {
        "association_ref": value.association_ref,
        "issue_ref": value.issue_ref,
        "role": value.role.value,
        "disposition": value.disposition.value,
        "admitted_at": value.admitted_at,
        "receipt_ref": value.receipt_ref,
    }


def _dependency_wire(value: GoalPhaseDependency) -> dict[str, object]:
    return {
        "owner_goal_tag": value.owner_goal_tag,
        "dependency_key": value.dependency_key,
        "dependent": _coordinate_wire(value.dependent),
        "prerequisite": _coordinate_wire(value.prerequisite),
        "required_gate_digest": value.required_gate_digest,
        "relation": value.relation.value,
        "reason": value.reason,
        "evidence_refs": list(value.evidence_refs),
    }


__all__ = [
    "GOAL_PHASE_NATIVE_ADMISSION_PLAN_SCHEMA",
    "GOAL_PHASE_NATIVE_ADMISSION_RECEIPT_SCHEMA",
    "GoalPhaseNativeAdmissionError",
    "GoalPhaseNativeAdmissionPlanV1",
    "GoalPhaseNativeAdmissionPublicationReceiptV1",
    "issue_goal_phase_native_admission_publication_receipt",
    "plan_goal_phase_native_admission",
]
