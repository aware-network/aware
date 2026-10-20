"""One exact, additive dependency in an operational native Goal document."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .identity import fingerprint, required_token
from .phase_contracts import (
    GoalPhaseContractBundleV1,
    GoalPhaseDependency,
    GoalLanePhaseState,
)
from .phase_document import GoalPhaseNativeDocumentV2

PLAN_SCHEMA = "aware.goal.phase-native-dependency-addition-plan.v1"
RECEIPT_SCHEMA = "aware.goal.phase-native-dependency-addition-publication-receipt.v1"


class GoalPhaseNativeDependencyAdditionError(ValueError):
    """The requested one-edge transition does not preserve native authority."""


def _dependency_wire(value: GoalPhaseDependency) -> dict[str, object]:
    return {
        "owner_goal_tag": value.owner_goal_tag,
        "dependency_key": value.dependency_key,
        "dependent": {
            "goal_tag": value.dependent.goal_tag,
            "lane_key": value.dependent.lane_key,
            "phase_key": value.dependent.phase_key,
        },
        "prerequisite": {
            "goal_tag": value.prerequisite.goal_tag,
            "lane_key": value.prerequisite.lane_key,
            "phase_key": value.prerequisite.phase_key,
        },
        "required_gate_digest": value.required_gate_digest,
        "relation": value.relation.value,
        "reason": value.reason,
        "evidence_refs": list(value.evidence_refs),
    }


def _postimage(
    *, document: GoalPhaseNativeDocumentV2, dependency: GoalPhaseDependency
) -> GoalPhaseNativeDocumentV2:
    if type(document) is not GoalPhaseNativeDocumentV2:
        raise TypeError("dependency addition requires exact V2 authority")
    if type(dependency) is not GoalPhaseDependency:
        raise TypeError("dependency must be exact GoalPhaseDependency")
    document.__post_init__()
    dependency.__post_init__()
    definitions = {item.coordinate: item for item in document.definitions}
    if dependency.owner_goal_tag != document.goal_tag:
        raise GoalPhaseNativeDependencyAdditionError("dependency belongs to another Goal")
    if dependency.dependent not in definitions:
        raise GoalPhaseNativeDependencyAdditionError("dependent Phase is not defined")
    operational_dependent = next(
        (
            phase for phase in document.operational_bundle.phases
            if phase.coordinate == dependency.dependent
        ),
        None,
    )
    if operational_dependent is not None and operational_dependent.state in {
        GoalLanePhaseState.ACCEPTED,
        GoalLanePhaseState.WITHDRAWN,
    }:
        raise GoalPhaseNativeDependencyAdditionError(
            "accepted or withdrawn dependent cannot gain a new prerequisite"
        )
    prerequisite = definitions.get(dependency.prerequisite)
    if prerequisite is None:
        raise GoalPhaseNativeDependencyAdditionError(
            "prerequisite Phase must be defined in the same Goal"
        )
    if dependency.required_gate_digest != prerequisite.gate.gate_digest:
        raise GoalPhaseNativeDependencyAdditionError("prerequisite Gate digest is stale")
    if any(
        existing.dependency_key == dependency.dependency_key
        for existing in document.operational_bundle.dependencies
    ) or any(
        existing.dependency_key == dependency.dependency_key
        for existing in document.unresolved_dependencies
    ):
        raise GoalPhaseNativeDependencyAdditionError("dependency identity already exists")
    # The bundle's complete graph validator rejects duplicate edges and cycles.
    bundle = GoalPhaseContractBundleV1(
        phases=document.operational_bundle.phases,
        dependencies=document.operational_bundle.dependencies + (dependency,),
    )
    return replace(document, operational_bundle=bundle)


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDependencyAdditionPlanV1:
    before_document: GoalPhaseNativeDocumentV2
    after_document: GoalPhaseNativeDocumentV2
    dependency: GoalPhaseDependency
    semantic_intent_ref: str
    schema_id: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != PLAN_SCHEMA:
            raise GoalPhaseNativeDependencyAdditionError("invalid addition-plan schema")
        expected = _postimage(document=self.before_document, dependency=self.dependency)
        if self.after_document != expected:
            raise GoalPhaseNativeDependencyAdditionError("postimage is not one exact edge")
        expected_ref = "goal-phase-native-dependency-addition-intent:" + fingerprint(
            {
                "schema_id": PLAN_SCHEMA,
                "before_document_ref": self.before_document.document_ref,
                "after_document_ref": expected.document_ref,
                "dependency": _dependency_wire(self.dependency),
            }
        )
        if self.semantic_intent_ref != expected_ref:
            raise GoalPhaseNativeDependencyAdditionError("semantic intent is not canonical")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "schema_id": self.schema_id,
            "before_document_ref": self.before_document.document_ref,
            "after_document_ref": self.after_document.document_ref,
            "dependency": _dependency_wire(self.dependency),
            "semantic_intent_ref": self.semantic_intent_ref,
        }


def plan_goal_phase_native_dependency_addition(
    *, document: GoalPhaseNativeDocumentV2, dependency: GoalPhaseDependency
) -> GoalPhaseNativeDependencyAdditionPlanV1:
    after = _postimage(document=document, dependency=dependency)
    intent_ref = "goal-phase-native-dependency-addition-intent:" + fingerprint(
        {
            "schema_id": PLAN_SCHEMA,
            "before_document_ref": document.document_ref,
            "after_document_ref": after.document_ref,
            "dependency": _dependency_wire(dependency),
        }
    )
    return GoalPhaseNativeDependencyAdditionPlanV1(
        before_document=document,
        after_document=after,
        dependency=dependency,
        semantic_intent_ref=intent_ref,
    )


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeDependencyAdditionPublicationReceiptV1:
    semantic_intent_ref: str
    before_document_ref: str
    after_document_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    changed_path: str
    publication_issue_path: str
    publication_issue_blob_oid: str
    receipt_ref: str = field(init=False)
    schema_id: str = RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != RECEIPT_SCHEMA:
            raise GoalPhaseNativeDependencyAdditionError("invalid publication schema")
        for name, value in (
            ("semantic_intent_ref", self.semantic_intent_ref),
            ("before_document_ref", self.before_document_ref),
            ("after_document_ref", self.after_document_ref),
            ("repository_commit_ref", self.repository_commit_ref),
            ("repository_commit_receipt_ref", self.repository_commit_receipt_ref),
            ("changed_path", self.changed_path),
            ("publication_issue_path", self.publication_issue_path),
            ("publication_issue_blob_oid", self.publication_issue_blob_oid),
        ):
            if type(value) is not str:
                raise TypeError(f"{name} must be exact str")
            _ = required_token(value, name)
        if self.repository_commit_receipt_ref != (
            "repository-commit:" + self.repository_commit_ref
        ):
            raise GoalPhaseNativeDependencyAdditionError("repository receipt/commit mismatch")
        object.__setattr__(
            self, "receipt_ref",
            "goal-phase-native-dependency-addition-publication:"
            + fingerprint(self.to_wire(include_ref=False)),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "semantic_intent_ref": self.semantic_intent_ref,
            "before_document_ref": self.before_document_ref,
            "after_document_ref": self.after_document_ref,
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "changed_path": self.changed_path,
            "publication_issue_path": self.publication_issue_path,
            "publication_issue_blob_oid": self.publication_issue_blob_oid,
        }
        if include_ref:
            body["receipt_ref"] = self.receipt_ref
        return body


def issue_goal_phase_native_dependency_addition_receipt(
    *, plan: GoalPhaseNativeDependencyAdditionPlanV1,
    repository_commit_ref: str, changed_path: str,
    publication_issue_path: str, publication_issue_blob_oid: str,
) -> GoalPhaseNativeDependencyAdditionPublicationReceiptV1:
    if type(plan) is not GoalPhaseNativeDependencyAdditionPlanV1:
        raise TypeError("plan must be exact GoalPhaseNativeDependencyAdditionPlanV1")
    plan.__post_init__()
    return GoalPhaseNativeDependencyAdditionPublicationReceiptV1(
        semantic_intent_ref=plan.semantic_intent_ref,
        before_document_ref=plan.before_document.document_ref,
        after_document_ref=plan.after_document.document_ref,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref="repository-commit:" + repository_commit_ref,
        changed_path=changed_path,
        publication_issue_path=publication_issue_path,
        publication_issue_blob_oid=publication_issue_blob_oid,
    )
