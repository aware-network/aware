# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportImplicitOverride=false
"""Migration-only Gate evaluation authority for definition-only native Phases.

The trusted entrance verifies independently supplied committed authority and
derives observations.  It does not publish a Goal or accept caller-authored
observations, evaluator identities, or outcomes.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import ClassVar, cast

from .identity import fingerprint, normalize_goal_tag, required_text
from .phase_codec import goal_phase_bundle_to_wire
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseGateOutcome,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
)
from .phase_document import GoalPhaseUnresolvedDependencyV1
from .phase_frontier import (
    GoalPhaseDependencyObservationV2,
    goal_phase_dependency_digest,
    observe_goal_phase_dependency,
    observe_unresolved_goal_phase_dependency,
)

EVALUATOR_PROFILE = (
    "aware.goal.migrated-phase-gate-evaluator/migration-qualification-v1"
)
PROPOSAL_SCHEMA = "aware.goal.migrated-phase-qualification-proposal.v1"
ACCEPTANCE_SCHEMA = "aware.goal.migrated-phase-qualification-acceptance.v1"
BUNDLE_SCHEMA = "aware.goal.migrated-phase-qualification-evidence.v1"
EVALUATION_SCHEMA = "aware.goal.migrated-phase-qualification-evaluation.v1"


class MigratedPhaseGateEvaluationError(ValueError):
    """M14 input or authority violates the accepted contract."""


class DependencyState(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    PENDING = "pending"
    SATISFIED = "satisfied"
    STALE = "stale"
    UNRESOLVED = "unresolved"
    REJECTED = "rejected"


class EvaluationResult(StrEnum):
    SATISFIED = "satisfied"
    STALE = "stale"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class SourceCurrentness(StrEnum):
    EQUAL = "equal"
    DESCENDANT_UNCHANGED = "descendant_unchanged"
    STALE = "stale"
    UNPROVEN = "unproven"


class ReasonCode(StrEnum):
    COORDINATOR_REVOKED = "coordinator_revoked"
    GOAL_AUTHORITY_MISMATCH = "goal_authority_mismatch"
    DEFINITION_QUALIFICATION_STALE = "definition_qualification_stale"
    IMPLEMENTATION_PUBLICATION_STALE = "implementation_publication_stale"
    INDEPENDENT_ACCEPTANCE_REJECTED = "independent_acceptance_rejected"
    INDEPENDENT_ACCEPTANCE_STALE = "independent_acceptance_stale"
    IMPLEMENTATION_CLOSEOUT_STALE = "implementation_closeout_stale"
    DEPENDENCY_PENDING = "dependency_pending"
    DEPENDENCY_REJECTED = "dependency_rejected"
    DEPENDENCY_STALE = "dependency_stale"
    DEPENDENCY_UNRESOLVED = "dependency_unresolved"
    DEPENDENCY_NOT_EVALUATED = "dependency_not_evaluated"
    REPOSITORY_AUTHORITY_UNAVAILABLE = "repository_authority_unavailable"
    PROVIDER_AUTHORITY_UNAVAILABLE = "provider_authority_unavailable"
    LINEAGE_UNPROVEN = "lineage_unproven"


def _text(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be exact str")
    result = required_text(value, name)
    if result != value:
        raise MigratedPhaseGateEvaluationError(f"{name} must be canonical text")
    return result


def _token(value: object, name: str) -> str:
    result = _text(value, name)
    if any(char.isspace() for char in result) or "|" in result:
        raise MigratedPhaseGateEvaluationError(f"{name} must be one token")
    return result


def _tokens(values: object, name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be exact tuple")
    result = tuple(_token(item, name) for item in values)
    if result != tuple(sorted(set(result))):
        raise MigratedPhaseGateEvaluationError(f"{name} must be sorted and unique")
    return result


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be exact dict")
    return value


def _fields(value: Mapping[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise MigratedPhaseGateEvaluationError(f"{name} fields are not canonical")


def _array(value: object, name: str) -> tuple[object, ...]:
    if type(value) is not list:
        raise TypeError(f"{name} must be exact list")
    return tuple(value)


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be exact bool")
    return value


def _exact_authority(
    expected: Mapping[str, object], actual: Mapping[str, object], name: str
) -> None:
    if type(actual) is not dict or actual != expected:
        raise MigratedPhaseGateEvaluationError(f"{name} authority mismatch")


def _coord_wire(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


@dataclass(frozen=True, slots=True)
class SourceEpochV1:
    repository_ref: str
    source_commit: str
    observed_head: str
    path: str
    blob: str
    currentness: SourceCurrentness
    protected_paths: tuple[str, ...]
    epoch_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SourceEpochV1:
            raise TypeError("source epoch type must be exact")
        for name in (
            "repository_ref",
            "source_commit",
            "observed_head",
            "path",
            "blob",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        if type(self.currentness) is not SourceCurrentness:
            raise TypeError("currentness must be SourceCurrentness")
        object.__setattr__(
            self, "protected_paths", _tokens(self.protected_paths, "protected_paths")
        )
        object.__setattr__(
            self,
            "epoch_ref",
            "goal-migrated-phase-source-epoch:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "repository_ref": self.repository_ref,
            "source_commit": self.source_commit,
            "observed_head": self.observed_head,
            "path": self.path,
            "blob": self.blob,
            "currentness": self.currentness.value,
            "protected_paths": list(self.protected_paths),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "epoch_ref": self.epoch_ref}


@dataclass(frozen=True, slots=True)
class IssueAuthorityV1:
    issue_path: str
    issue_blob: str
    owner_execution_id: str
    status: str
    scope_digest: str

    def __post_init__(self) -> None:
        if type(self) is not IssueAuthorityV1:
            raise TypeError("issue authority type must be exact")
        for name in ("issue_path", "issue_blob", "owner_execution_id", "scope_digest"):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        if self.status not in {"In Progress", "Closed"}:
            raise MigratedPhaseGateEvaluationError("unsupported Issue status")

    def to_wire(self) -> dict[str, str]:
        return {
            "issue_path": self.issue_path,
            "issue_blob": self.issue_blob,
            "owner_execution_id": self.owner_execution_id,
            "status": self.status,
            "scope_digest": self.scope_digest,
        }


@dataclass(frozen=True, slots=True)
class EvidenceBase:
    role: str
    role_key: str
    source_epoch: SourceEpochV1
    evidence_ref: str = field(init=False)
    schema_id: ClassVar[str]

    def _validate(self, body: Mapping[str, object]) -> None:
        object.__setattr__(self, "role", _token(self.role, "role"))
        object.__setattr__(self, "role_key", _token(self.role_key, "role_key"))
        if type(self.source_epoch) is not SourceEpochV1:
            raise TypeError("source_epoch must be SourceEpochV1")
        self.source_epoch.__post_init__()
        object.__setattr__(
            self,
            "evidence_ref",
            "goal-migrated-phase-evidence:"
            + fingerprint({"schema_id": self.schema_id, **body}),
        )

    def authority_wire(self) -> dict[str, object]:
        return self.to_wire()

    def to_wire(self) -> dict[str, object]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DefinitionQualificationEvidenceV1(EvidenceBase):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.definition-qualification.v1"
    )
    m13_publication_receipt_ref: str = ""
    reconciliation_receipt_ref: str = ""
    goal_path: str = ""
    goal_tag: str = ""
    coordinate: GoalPhaseCoordinate | None = None
    before_document_ref: str = ""
    after_document_ref: str = ""
    before_definition_ref: str = ""
    after_definition_ref: str = ""
    proposal_publication_ref: str = ""
    acceptance_publication_ref: str = ""
    publication_commit: str = ""
    goal_blob: str = ""
    repository_commit_receipt_ref: str = ""

    def __post_init__(self) -> None:
        if (
            self.role != "definition_qualification"
            or self.role_key != "definition_qualification"
        ):
            raise MigratedPhaseGateEvaluationError("definition evidence role mismatch")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        for name in (
            "m13_publication_receipt_ref",
            "reconciliation_receipt_ref",
            "goal_path",
            "before_document_ref",
            "after_document_ref",
            "before_definition_ref",
            "after_definition_ref",
            "proposal_publication_ref",
            "acceptance_publication_ref",
            "publication_commit",
            "goal_blob",
            "repository_commit_receipt_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        self._validate(self.body())

    def body(self) -> dict[str, object]:
        coordinate = cast(GoalPhaseCoordinate, self.coordinate)
        return {
            "role": self.role,
            "role_key": self.role_key,
            "m13_publication_receipt_ref": self.m13_publication_receipt_ref,
            "reconciliation_receipt_ref": self.reconciliation_receipt_ref,
            "goal_path": self.goal_path,
            "goal_tag": self.goal_tag,
            "coordinate": _coord_wire(coordinate),
            "before_document_ref": self.before_document_ref,
            "after_document_ref": self.after_document_ref,
            "before_definition_ref": self.before_definition_ref,
            "after_definition_ref": self.after_definition_ref,
            "proposal_publication_ref": self.proposal_publication_ref,
            "acceptance_publication_ref": self.acceptance_publication_ref,
            "publication_commit": self.publication_commit,
            "goal_blob": self.goal_blob,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "source_epoch": self.source_epoch.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **self.body(),
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class ImplementationPublicationEvidenceV1(EvidenceBase):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.implementation-publication.v1"
    )
    coordinate: GoalPhaseCoordinate | None = None
    definition_ref: str = ""
    gate_digest: str = ""
    issue_authority: IssueAuthorityV1 | None = None
    parent_commit: str = ""
    implementation_commit: str = ""
    changed_paths: tuple[str, ...] = ()
    tree_entry_oids: tuple[str, ...] = ()
    repository_commit_receipt_ref: str = ""

    def __post_init__(self) -> None:
        if (
            self.role != "implementation_publication"
            or self.role_key != "implementation_publication"
        ):
            raise MigratedPhaseGateEvaluationError(
                "implementation evidence role mismatch"
            )
        if (
            type(self.coordinate) is not GoalPhaseCoordinate
            or type(self.issue_authority) is not IssueAuthorityV1
        ):
            raise TypeError("implementation authority types are invalid")
        if self.issue_authority.status != "In Progress":
            raise MigratedPhaseGateEvaluationError(
                "implementation Issue must be In Progress at publication"
            )
        for name in (
            "definition_ref",
            "gate_digest",
            "parent_commit",
            "implementation_commit",
            "repository_commit_receipt_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        object.__setattr__(
            self, "changed_paths", _tokens(self.changed_paths, "changed_paths")
        )
        object.__setattr__(
            self, "tree_entry_oids", _tokens(self.tree_entry_oids, "tree_entry_oids")
        )
        if (
            len(self.changed_paths) != len(self.tree_entry_oids)
            or not self.changed_paths
        ):
            raise MigratedPhaseGateEvaluationError(
                "implementation paths and OIDs must align"
            )
        self._validate(self.body())

    def body(self) -> dict[str, object]:
        coordinate = cast(GoalPhaseCoordinate, self.coordinate)
        issue = cast(IssueAuthorityV1, self.issue_authority)
        return {
            "role": self.role,
            "role_key": self.role_key,
            "coordinate": _coord_wire(coordinate),
            "definition_ref": self.definition_ref,
            "gate_digest": self.gate_digest,
            "issue_authority": issue.to_wire(),
            "parent_commit": self.parent_commit,
            "implementation_commit": self.implementation_commit,
            "changed_paths": list(self.changed_paths),
            "tree_entry_oids": list(self.tree_entry_oids),
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "source_epoch": self.source_epoch.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **self.body(),
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class IndependentAcceptanceEvidenceV1(EvidenceBase):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.independent-acceptance.v1"
    )
    verdict: str = ""
    reviewer_execution_id: str = ""
    reviewed_implementation_commit: str = ""
    changed_path_digest: str = ""
    coordinate: GoalPhaseCoordinate | None = None
    definition_ref: str = ""
    gate_digest: str = ""
    validation_evidence_refs: tuple[str, ...] = ()
    review_issue_authority: IssueAuthorityV1 | None = None
    artifact_path: str = ""
    artifact_blob: str = ""
    publication_commit: str = ""
    repository_commit_receipt_ref: str = ""

    def __post_init__(self) -> None:
        if (
            self.role != "independent_acceptance"
            or self.role_key != "independent_acceptance"
        ):
            raise MigratedPhaseGateEvaluationError("review evidence role mismatch")
        if self.verdict not in {"accepted", "rejected"}:
            raise MigratedPhaseGateEvaluationError(
                "verdict must be accepted or rejected"
            )
        if (
            type(self.coordinate) is not GoalPhaseCoordinate
            or type(self.review_issue_authority) is not IssueAuthorityV1
        ):
            raise TypeError("review authority types are invalid")
        for name in (
            "reviewer_execution_id",
            "reviewed_implementation_commit",
            "changed_path_digest",
            "definition_ref",
            "gate_digest",
            "artifact_path",
            "artifact_blob",
            "publication_commit",
            "repository_commit_receipt_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        object.__setattr__(
            self,
            "validation_evidence_refs",
            _tokens(self.validation_evidence_refs, "validation_evidence_refs"),
        )
        self._validate(self.body())

    def body(self) -> dict[str, object]:
        coordinate = cast(GoalPhaseCoordinate, self.coordinate)
        issue = cast(IssueAuthorityV1, self.review_issue_authority)
        return {
            "role": self.role,
            "role_key": self.role_key,
            "verdict": self.verdict,
            "reviewer_execution_id": self.reviewer_execution_id,
            "reviewed_implementation_commit": self.reviewed_implementation_commit,
            "changed_path_digest": self.changed_path_digest,
            "coordinate": _coord_wire(coordinate),
            "definition_ref": self.definition_ref,
            "gate_digest": self.gate_digest,
            "validation_evidence_refs": list(self.validation_evidence_refs),
            "review_issue_authority": issue.to_wire(),
            "artifact_path": self.artifact_path,
            "artifact_blob": self.artifact_blob,
            "publication_commit": self.publication_commit,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "source_epoch": self.source_epoch.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **self.body(),
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class ImplementationCloseoutEvidenceV1(EvidenceBase):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.implementation-closeout.v1"
    )
    issue_path: str = ""
    owner_execution_id: str = ""
    scope_digest: str = ""
    before_issue_blob: str = ""
    after_issue_blob: str = ""
    implementation_commit: str = ""
    independent_verdict_ref: str = ""
    closeout_commit: str = ""
    repository_commit_receipt_ref: str = ""

    def __post_init__(self) -> None:
        if (
            self.role != "implementation_closeout"
            or self.role_key != "implementation_closeout"
        ):
            raise MigratedPhaseGateEvaluationError("closeout evidence role mismatch")
        for name in (
            "issue_path",
            "owner_execution_id",
            "scope_digest",
            "before_issue_blob",
            "after_issue_blob",
            "implementation_commit",
            "independent_verdict_ref",
            "closeout_commit",
            "repository_commit_receipt_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        self._validate(self.body())

    def body(self) -> dict[str, object]:
        return {
            "role": self.role,
            "role_key": self.role_key,
            "issue_path": self.issue_path,
            "owner_execution_id": self.owner_execution_id,
            "scope_digest": self.scope_digest,
            "before_issue_blob": self.before_issue_blob,
            "after_issue_blob": self.after_issue_blob,
            "implementation_commit": self.implementation_commit,
            "independent_verdict_ref": self.independent_verdict_ref,
            "closeout_commit": self.closeout_commit,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "source_epoch": self.source_epoch.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **self.body(),
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class DependencyEvidenceV1(EvidenceBase):
    dependency_key: str = ""
    dependency_digest: str = ""
    relation: str = ""
    dependent: GoalPhaseCoordinate | None = None
    prerequisite: GoalPhaseCoordinate | None = None
    dependent_source_revision_ref: str = ""
    prerequisite_source_revision_ref: str = ""
    required_gate_digest: str = ""
    state: DependencyState = DependencyState.NOT_EVALUATED
    authority_ref: str = ""

    def _dependency_validate(self, relation: str) -> None:
        if (
            self.role != f"dependency:{self.dependency_key}"
            or self.role_key != self.dependency_key
        ):
            raise MigratedPhaseGateEvaluationError("dependency evidence role mismatch")
        if self.relation != relation:
            raise MigratedPhaseGateEvaluationError(
                "dependency evidence relation mismatch"
            )
        if (
            type(self.dependent) is not GoalPhaseCoordinate
            or type(self.prerequisite) is not GoalPhaseCoordinate
        ):
            raise TypeError("dependency coordinates must be GoalPhaseCoordinate")
        if type(self.state) is not DependencyState:
            raise TypeError("state must be DependencyState")
        for name in (
            "dependency_key",
            "dependency_digest",
            "dependent_source_revision_ref",
            "prerequisite_source_revision_ref",
            "required_gate_digest",
            "authority_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        self._validate(self.body())

    def body(self) -> dict[str, object]:
        dependent = cast(GoalPhaseCoordinate, self.dependent)
        prerequisite = cast(GoalPhaseCoordinate, self.prerequisite)
        return {
            "role": self.role,
            "role_key": self.role_key,
            "dependency_key": self.dependency_key,
            "dependency_digest": self.dependency_digest,
            "relation": self.relation,
            "dependent": _coord_wire(dependent),
            "prerequisite": _coord_wire(prerequisite),
            "dependent_source_revision_ref": self.dependent_source_revision_ref,
            "prerequisite_source_revision_ref": self.prerequisite_source_revision_ref,
            "required_gate_digest": self.required_gate_digest,
            "state": self.state.value,
            "authority_ref": self.authority_ref,
            "source_epoch": self.source_epoch.to_wire(),
        }

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **self.body(),
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class DependencyCompletionEvidenceV1(DependencyEvidenceV1):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.dependency-completion.v1"
    )

    def __post_init__(self) -> None:
        self._dependency_validate("requires_completion")


@dataclass(frozen=True, slots=True)
class DependencyAcceptanceEvidenceV1(DependencyEvidenceV1):
    schema_id: ClassVar[str] = (
        "aware.goal.migrated-phase-evidence.dependency-acceptance.v1"
    )

    def __post_init__(self) -> None:
        self._dependency_validate("requires_acceptance")


Evidence = (
    DefinitionQualificationEvidenceV1
    | ImplementationPublicationEvidenceV1
    | IndependentAcceptanceEvidenceV1
    | ImplementationCloseoutEvidenceV1
    | DependencyCompletionEvidenceV1
    | DependencyAcceptanceEvidenceV1
)


@dataclass(frozen=True, slots=True)
class EvidenceBundleV1:
    entries: tuple[Evidence, ...]
    bundle_ref: str = field(init=False)
    schema_id: str = field(init=False, default=BUNDLE_SCHEMA)

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple or not all(
            type(item) in _EVIDENCE_TYPES for item in self.entries
        ):
            raise TypeError("entries must be exact M14 evidence variants")
        identities = tuple((item.role, item.role_key) for item in self.entries)
        if identities != tuple(sorted(set(identities))):
            raise MigratedPhaseGateEvaluationError(
                "evidence identities must be sorted and unique"
            )
        refs = tuple(item.evidence_ref for item in self.entries)
        if len(refs) != len(set(refs)):
            raise MigratedPhaseGateEvaluationError("evidence refs must be unique")
        object.__setattr__(
            self,
            "bundle_ref",
            "goal-migrated-phase-evidence-bundle:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "schema_id": BUNDLE_SCHEMA,
            "entries": [item.to_wire() for item in self.entries],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "bundle_ref": self.bundle_ref}


_EVIDENCE_TYPES = {
    DefinitionQualificationEvidenceV1,
    ImplementationPublicationEvidenceV1,
    IndependentAcceptanceEvidenceV1,
    ImplementationCloseoutEvidenceV1,
    DependencyCompletionEvidenceV1,
    DependencyAcceptanceEvidenceV1,
}


@dataclass(frozen=True, slots=True)
class DependencyBindingV1:
    dependency_key: str
    dependency_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "dependency_key", _token(self.dependency_key, "dependency_key")
        )
        object.__setattr__(
            self,
            "dependency_digest",
            _token(self.dependency_digest, "dependency_digest"),
        )

    def to_wire(self) -> dict[str, str]:
        return {
            "dependency_key": self.dependency_key,
            "dependency_digest": self.dependency_digest,
        }


@dataclass(frozen=True, slots=True)
class QualificationProposalV1:
    proposal_ref: str
    goal_path: str
    goal_tag: str
    coordinate: GoalPhaseCoordinate
    document_ref: str
    source_revision_ref: str
    definition_ref: str
    gate_digest: str
    evaluator_profile: str
    dependency_bindings: tuple[DependencyBindingV1, ...]
    evidence_role_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        for name in (
            "proposal_ref",
            "goal_path",
            "document_ref",
            "source_revision_ref",
            "definition_ref",
            "gate_digest",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        if self.evaluator_profile != EVALUATOR_PROFILE:
            raise MigratedPhaseGateEvaluationError("wrong evaluator profile")
        if type(self.dependency_bindings) is not tuple or not all(
            type(item) is DependencyBindingV1 for item in self.dependency_bindings
        ):
            raise TypeError(
                "dependency_bindings must be exact DependencyBindingV1 tuple"
            )
        bindings = tuple(
            sorted(self.dependency_bindings, key=lambda item: item.dependency_key)
        )
        if self.dependency_bindings != bindings or len(
            {item.dependency_key for item in bindings}
        ) != len(bindings):
            raise MigratedPhaseGateEvaluationError(
                "dependency bindings must be key-sorted and unique"
            )
        object.__setattr__(
            self,
            "evidence_role_keys",
            _tokens(self.evidence_role_keys, "evidence_role_keys"),
        )
        object.__setattr__(
            self,
            "proposal_ref",
            "goal-migrated-phase-proposal:"
            + fingerprint(
                {
                    "goal_path": self.goal_path,
                    "goal_tag": self.goal_tag,
                    "coordinate": _coord_wire(self.coordinate),
                    "document_ref": self.document_ref,
                    "source_revision_ref": self.source_revision_ref,
                    "definition_ref": self.definition_ref,
                    "gate_digest": self.gate_digest,
                    "evaluator_profile": self.evaluator_profile,
                    "dependency_bindings": [
                        item.to_wire() for item in self.dependency_bindings
                    ],
                    "evidence_role_keys": list(self.evidence_role_keys),
                }
            ),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": PROPOSAL_SCHEMA,
            "proposal_ref": self.proposal_ref,
            "goal_path": self.goal_path,
            "goal_tag": self.goal_tag,
            "coordinate": _coord_wire(self.coordinate),
            "document_ref": self.document_ref,
            "source_revision_ref": self.source_revision_ref,
            "definition_ref": self.definition_ref,
            "gate_digest": self.gate_digest,
            "evaluator_profile": self.evaluator_profile,
            "dependency_bindings": [
                item.to_wire() for item in self.dependency_bindings
            ],
            "evidence_role_keys": list(self.evidence_role_keys),
        }


@dataclass(frozen=True, slots=True)
class QualificationAcceptanceV1:
    acceptance_ref: str
    proposal_ref: str
    accepting_execution_id: str
    acceptance_issue_authority: IssueAuthorityV1
    coordinator_authority_ref: str
    coordinator_current: bool
    decision: str
    evidence_bundle_ref: str

    def __post_init__(self) -> None:
        for name in (
            "acceptance_ref",
            "proposal_ref",
            "accepting_execution_id",
            "coordinator_authority_ref",
            "evidence_bundle_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        if type(self.acceptance_issue_authority) is not IssueAuthorityV1:
            raise TypeError("acceptance_issue_authority must be IssueAuthorityV1")
        if type(self.coordinator_current) is not bool:
            raise TypeError("coordinator_current must be exact bool")
        if self.decision not in {"authorize_evaluation", "reject_evaluation"}:
            raise MigratedPhaseGateEvaluationError("invalid acceptance decision")
        if (
            self.accepting_execution_id
            != self.acceptance_issue_authority.owner_execution_id
        ):
            raise MigratedPhaseGateEvaluationError(
                "accepting execution differs from Issue owner"
            )
        object.__setattr__(
            self,
            "acceptance_ref",
            "goal-migrated-phase-acceptance:"
            + fingerprint(
                {
                    "proposal_ref": self.proposal_ref,
                    "accepting_execution_id": self.accepting_execution_id,
                    "acceptance_issue_authority": self.acceptance_issue_authority.to_wire(),
                    "coordinator_authority_ref": self.coordinator_authority_ref,
                    "coordinator_current": self.coordinator_current,
                    "decision": self.decision,
                    "evidence_bundle_ref": self.evidence_bundle_ref,
                }
            ),
        )

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_id": ACCEPTANCE_SCHEMA,
            "acceptance_ref": self.acceptance_ref,
            "proposal_ref": self.proposal_ref,
            "accepting_execution_id": self.accepting_execution_id,
            "acceptance_issue_authority": self.acceptance_issue_authority.to_wire(),
            "coordinator_authority_ref": self.coordinator_authority_ref,
            "coordinator_current": self.coordinator_current,
            "decision": self.decision,
            "evidence_bundle_ref": self.evidence_bundle_ref,
        }


@dataclass(frozen=True, slots=True, order=True)
class EvaluationReason:
    code: ReasonCode
    role_key: str

    def __post_init__(self) -> None:
        if type(self.code) is not ReasonCode:
            raise TypeError("code must be ReasonCode")
        object.__setattr__(self, "role_key", _token(self.role_key, "role_key"))

    def to_wire(self) -> dict[str, str]:
        return {"code": self.code.value, "role_key": self.role_key}


@dataclass(frozen=True, slots=True)
class MigratedPhaseGateEvaluationV1:
    proposal_ref: str
    acceptance_ref: str
    evidence_bundle_ref: str
    evaluator_ref: str
    result: EvaluationResult
    reasons: tuple[EvaluationReason, ...]
    source_epoch_ref: str
    dependency_set_digest: str
    gate_observation_ref: str | None
    dependency_observation_refs: tuple[str, ...]
    currentness_ref: str
    evaluation_ref: str = field(init=False)
    schema_id: str = field(init=False, default=EVALUATION_SCHEMA)

    def __post_init__(self) -> None:
        if type(self.result) is not EvaluationResult:
            raise TypeError("result must be EvaluationResult")
        if type(self.reasons) is not tuple or not all(
            type(item) is EvaluationReason for item in self.reasons
        ):
            raise TypeError("reasons must be exact EvaluationReason tuple")
        if self.reasons != tuple(sorted(set(self.reasons))):
            raise MigratedPhaseGateEvaluationError("reasons must be sorted and unique")
        object.__setattr__(
            self,
            "dependency_observation_refs",
            _tokens(self.dependency_observation_refs, "dependency_observation_refs"),
        )
        for name in (
            "proposal_ref",
            "acceptance_ref",
            "evidence_bundle_ref",
            "evaluator_ref",
            "source_epoch_ref",
            "dependency_set_digest",
            "currentness_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        if self.result is EvaluationResult.SATISFIED:
            if self.reasons or self.gate_observation_ref is None:
                raise MigratedPhaseGateEvaluationError(
                    "satisfied evaluation requires observation and no reasons"
                )
            object.__setattr__(
                self,
                "gate_observation_ref",
                _token(self.gate_observation_ref, "gate_observation_ref"),
            )
        elif self.gate_observation_ref is not None:
            raise MigratedPhaseGateEvaluationError(
                "non-satisfied evaluation cannot carry Gate observation"
            )
        object.__setattr__(
            self,
            "evaluation_ref",
            "goal-migrated-phase-evaluation:" + fingerprint(self.body()),
        )

    def body(self) -> dict[str, object]:
        return {
            "schema_id": EVALUATION_SCHEMA,
            "proposal_ref": self.proposal_ref,
            "acceptance_ref": self.acceptance_ref,
            "evidence_bundle_ref": self.evidence_bundle_ref,
            "evaluator_ref": self.evaluator_ref,
            "result": self.result.value,
            "reasons": [item.to_wire() for item in self.reasons],
            "source_epoch_ref": self.source_epoch_ref,
            "dependency_set_digest": self.dependency_set_digest,
            "gate_observation_ref": self.gate_observation_ref,
            "dependency_observation_refs": list(self.dependency_observation_refs),
            "currentness_ref": self.currentness_ref,
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.body(), "evaluation_ref": self.evaluation_ref}


@dataclass(frozen=True, slots=True)
class _VerificationToken:
    nonce: object = field(default_factory=object)


@dataclass(frozen=True, slots=True, init=False)
class VerifiedMigratedPhaseGateAuthoritySourcesV1:
    proposal_wire: Mapping[str, object]
    acceptance_wire: Mapping[str, object]
    evidence_wires: Mapping[str, Mapping[str, object]]
    source_epoch_wires: Mapping[tuple[str, str, str, str], Mapping[str, object]]
    role_currentness: Mapping[str, str]
    coordinator_wire: Mapping[str, object]
    dependency_authorities: Mapping[str, Mapping[str, object]]
    verification_ref: str
    verifier_token: object


@dataclass(frozen=True, slots=True, init=False)
class VerifiedMigratedPhaseGateAuthorityV1:
    proposal: QualificationProposalV1
    acceptance: QualificationAcceptanceV1
    bundle: EvidenceBundleV1
    role_currentness: tuple[tuple[str, SourceCurrentness], ...]
    dependency_states: tuple[tuple[str, DependencyState], ...]
    unresolved_dependency_digests: tuple[tuple[str, str], ...]
    dependency_observations: tuple[GoalPhaseDependencyObservationV2, ...]
    coordinator_current: bool
    verification_ref: str
    verifier_token: object


_VERIFICATION_REGISTRY_LIMIT = 128
_VERIFICATION_REGISTRY: OrderedDict[_VerificationToken, str] = OrderedDict()


def goal_phase_unresolved_dependency_digest(
    declaration: GoalPhaseUnresolvedDependencyV1,
) -> str:
    """Bind an authored unresolved edge without inventing a Gate digest."""

    if type(declaration) is not GoalPhaseUnresolvedDependencyV1:
        raise TypeError("unresolved declaration type must be exact")
    declaration.__post_init__()
    return fingerprint(
        {
            "schema_id": "aware.goal.phase-unresolved-dependency.v1",
            "owner_goal_tag": declaration.owner_goal_tag,
            "dependency_key": declaration.dependency_key,
            "dependent": _coord_wire(declaration.dependent),
            "prerequisite": _coord_wire(declaration.prerequisite),
            "relation": declaration.relation.value,
            "reason": declaration.reason,
            "evidence_refs": list(declaration.evidence_refs),
            "resolution_state": declaration.resolution_state,
            "eligibility_effect": declaration.eligibility_effect,
        }
    )


def _dependency_authority_body(value: Mapping[str, object]) -> dict[str, object]:
    declaration = value.get("declaration")
    if type(declaration) is GoalPhaseUnresolvedDependencyV1:
        declaration.__post_init__()
        return {
            "availability": value.get("availability"),
            "declaration_digest": goal_phase_unresolved_dependency_digest(declaration),
            "source_document_ref": value.get("source_document_ref"),
            "evaluator_ref": value.get("evaluator_ref"),
            "currentness_ref": value.get("currentness_ref"),
        }
    if type(declaration) is not GoalPhaseDependency:
        raise MigratedPhaseGateEvaluationError("dependency declaration is unavailable")
    prerequisite = value.get("prerequisite_phase")
    phase_body: object = None
    if prerequisite is not None:
        if type(prerequisite) is not GoalLanePhase:
            raise MigratedPhaseGateEvaluationError(
                "dependency prerequisite authority has wrong type"
            )
        prerequisite.__post_init__()
        bundle = GoalPhaseContractBundleV1(phases=(prerequisite,), dependencies=())
        phase_body = goal_phase_bundle_to_wire(bundle)
    return {
        "dependency_digest": goal_phase_dependency_digest(declaration),
        "availability": value.get("availability"),
        "dependent_source_revision_ref": value.get("dependent_source_revision_ref"),
        "prerequisite_source_revision_ref": value.get(
            "prerequisite_source_revision_ref"
        ),
        "evaluator_ref": value.get("evaluator_ref"),
        "currentness_ref": value.get("currentness_ref"),
        "authority_ref": value.get("authority_ref"),
        "evidence_schema_id": value.get("evidence_schema_id"),
        "prerequisite_phase": phase_body,
    }


def _authority_sources_body(
    value: VerifiedMigratedPhaseGateAuthoritySourcesV1,
) -> dict[str, object]:
    return {
        "proposal_wire": dict(value.proposal_wire),
        "acceptance_wire": dict(value.acceptance_wire),
        "evidence_wires": {
            key: dict(item) for key, item in sorted(value.evidence_wires.items())
        },
        "source_epoch_wires": [
            {"coordinate": list(key), "wire": dict(item)}
            for key, item in sorted(value.source_epoch_wires.items())
        ],
        "role_currentness": dict(sorted(value.role_currentness.items())),
        "coordinator_wire": dict(value.coordinator_wire),
        "dependency_authorities": {
            key: _dependency_authority_body(item)
            for key, item in sorted(value.dependency_authorities.items())
        },
    }


def _seal_migrated_phase_gate_authority_sources(  # pyright: ignore[reportUnusedFunction]
    *,
    proposal_wire: Mapping[str, object],
    acceptance_wire: Mapping[str, object],
    evidence_wires: Mapping[str, Mapping[str, object]],
    source_epoch_wires: Mapping[tuple[str, str, str, str], Mapping[str, object]],
    role_currentness: Mapping[str, str],
    coordinator_wire: Mapping[str, object],
    dependency_authorities: Mapping[str, Mapping[str, object]],
) -> VerifiedMigratedPhaseGateAuthoritySourcesV1:
    """Provider-only entrance; public evaluation never accepts resolver callbacks."""

    value = object.__new__(VerifiedMigratedPhaseGateAuthoritySourcesV1)
    object.__setattr__(value, "proposal_wire", dict(proposal_wire))
    object.__setattr__(value, "acceptance_wire", dict(acceptance_wire))
    object.__setattr__(
        value,
        "evidence_wires",
        {key: dict(item) for key, item in evidence_wires.items()},
    )
    object.__setattr__(
        value,
        "source_epoch_wires",
        {key: dict(item) for key, item in source_epoch_wires.items()},
    )
    object.__setattr__(value, "coordinator_wire", dict(coordinator_wire))
    object.__setattr__(value, "role_currentness", dict(role_currentness))
    object.__setattr__(
        value,
        "dependency_authorities",
        {key: dict(item) for key, item in dependency_authorities.items()},
    )
    body = _authority_sources_body(value)
    object.__setattr__(
        value,
        "verification_ref",
        "goal-migrated-phase-authority-sources:" + fingerprint(body),
    )
    object.__setattr__(value, "verifier_token", _register_verified(body))
    return value


def _require_authority_sources(
    value: VerifiedMigratedPhaseGateAuthoritySourcesV1,
) -> None:
    if type(value) is not VerifiedMigratedPhaseGateAuthoritySourcesV1 or not hasattr(
        value, "verifier_token"
    ):
        raise MigratedPhaseGateEvaluationError("authority sources are not sealed")
    token = value.verifier_token
    if type(token) is not _VerificationToken:
        raise MigratedPhaseGateEvaluationError("authority sources are not sealed")
    retained = _VERIFICATION_REGISTRY.get(token)
    if retained is None or retained != fingerprint(_authority_sources_body(value)):
        raise MigratedPhaseGateEvaluationError(
            "authority sources were forged or mutated"
        )


def _verified_body(value: VerifiedMigratedPhaseGateAuthorityV1) -> dict[str, object]:
    return {
        "proposal": value.proposal.to_wire(),
        "acceptance": value.acceptance.to_wire(),
        "bundle": value.bundle.to_wire(),
        "role_currentness": [
            [reference, state.value] for reference, state in value.role_currentness
        ],
        "dependency_states": [list(item) for item in value.dependency_states],
        "unresolved_dependency_digests": [
            list(item) for item in value.unresolved_dependency_digests
        ],
        "dependency_observations": [
            item.to_wire() for item in value.dependency_observations
        ],
        "coordinator_current": value.coordinator_current,
    }


def _register_verified(body: Mapping[str, object]) -> object:
    token = _VerificationToken()
    _VERIFICATION_REGISTRY[token] = fingerprint(dict(body))
    while len(_VERIFICATION_REGISTRY) > _VERIFICATION_REGISTRY_LIMIT:
        _ = _VERIFICATION_REGISTRY.popitem(last=False)
    return token


def _require_verified(value: VerifiedMigratedPhaseGateAuthorityV1) -> None:
    if type(value) is not VerifiedMigratedPhaseGateAuthorityV1 or not hasattr(
        value, "verifier_token"
    ):
        raise MigratedPhaseGateEvaluationError("authority verification is not sealed")
    token = value.verifier_token
    if type(token) is not _VerificationToken:
        raise MigratedPhaseGateEvaluationError("authority verification is not sealed")
    retained = _VERIFICATION_REGISTRY.get(token)
    if retained is None or retained != fingerprint(_verified_body(value)):
        raise MigratedPhaseGateEvaluationError(
            "authority verification was forged or mutated"
        )


def verify_migrated_phase_gate_authority(
    proposal: QualificationProposalV1,
    acceptance: QualificationAcceptanceV1,
    bundle: EvidenceBundleV1,
    *,
    authority_sources: VerifiedMigratedPhaseGateAuthoritySourcesV1,
) -> VerifiedMigratedPhaseGateAuthorityV1:
    """Join committed authority and seal the complete M14 evidence graph."""

    if (
        type(proposal) is not QualificationProposalV1
        or type(acceptance) is not QualificationAcceptanceV1
        or type(bundle) is not EvidenceBundleV1
    ):
        raise TypeError("proposal, acceptance and bundle must be exact M14 values")
    proposal.__post_init__()
    acceptance.__post_init__()
    bundle.__post_init__()
    _require_authority_sources(authority_sources)
    _exact_authority(proposal.to_wire(), authority_sources.proposal_wire, "proposal")
    _exact_authority(
        acceptance.to_wire(),
        authority_sources.acceptance_wire,
        "acceptance",
    )
    if (
        acceptance.proposal_ref != proposal.proposal_ref
        or acceptance.evidence_bundle_ref != bundle.bundle_ref
    ):
        raise MigratedPhaseGateEvaluationError("acceptance binding mismatch")

    expected_roles = {
        "definition_qualification",
        "implementation_publication",
        "independent_acceptance",
        "implementation_closeout",
        *(f"dependency:{item.dependency_key}" for item in proposal.dependency_bindings),
    }
    if {item.role for item in bundle.entries} != expected_roles or set(
        proposal.evidence_role_keys
    ) != expected_roles:
        raise MigratedPhaseGateEvaluationError("evidence role set mismatch")

    definition = next(
        (
            item
            for item in bundle.entries
            if type(item) is DefinitionQualificationEvidenceV1
        ),
        None,
    )
    implementation = next(
        (
            item
            for item in bundle.entries
            if type(item) is ImplementationPublicationEvidenceV1
        ),
        None,
    )
    review = next(
        (
            item
            for item in bundle.entries
            if type(item) is IndependentAcceptanceEvidenceV1
        ),
        None,
    )
    closeout = next(
        (
            item
            for item in bundle.entries
            if type(item) is ImplementationCloseoutEvidenceV1
        ),
        None,
    )
    if not (
        isinstance(definition, DefinitionQualificationEvidenceV1)
        and isinstance(implementation, ImplementationPublicationEvidenceV1)
        and isinstance(review, IndependentAcceptanceEvidenceV1)
        and isinstance(closeout, ImplementationCloseoutEvidenceV1)
    ):
        raise MigratedPhaseGateEvaluationError("core evidence roles missing")

    role_currentness: list[tuple[str, SourceCurrentness]] = []
    if set(authority_sources.role_currentness) != {
        item.evidence_ref for item in bundle.entries
    }:
        raise MigratedPhaseGateEvaluationError(
            "provider role currentness set is incomplete"
        )
    for item in bundle.entries:
        item.__post_init__()
        epoch_key = (
            item.source_epoch.repository_ref,
            item.source_epoch.source_commit,
            item.source_epoch.observed_head,
            item.source_epoch.path,
        )
        resolved_epoch = authority_sources.source_epoch_wires.get(epoch_key)
        if resolved_epoch is None:
            raise MigratedPhaseGateEvaluationError("source epoch authority is absent")
        _exact_authority(item.source_epoch.to_wire(), resolved_epoch, "source epoch")
        provider_state = authority_sources.role_currentness.get(item.evidence_ref)
        if type(provider_state) is not str:
            raise MigratedPhaseGateEvaluationError(
                "provider role currentness is not typed"
            )
        try:
            state = SourceCurrentness(provider_state)
        except ValueError as exc:
            raise MigratedPhaseGateEvaluationError(
                "provider role currentness is not canonical"
            ) from exc
        if state is SourceCurrentness.UNPROVEN:
            raise MigratedPhaseGateEvaluationError(
                "unproven role authority cannot be sealed"
            )
        role_currentness.append((item.evidence_ref, state))
        resolved_evidence = authority_sources.evidence_wires.get(item.evidence_ref)
        if resolved_evidence is None:
            raise MigratedPhaseGateEvaluationError("evidence authority is absent")
        _exact_authority(
            item.authority_wire(),
            resolved_evidence,
            item.role,
        )

    if (
        definition.goal_path != proposal.goal_path
        or definition.goal_tag != proposal.goal_tag
        or definition.coordinate != proposal.coordinate
        or definition.after_document_ref != proposal.document_ref
        or definition.after_definition_ref != proposal.definition_ref
        or definition.source_epoch.observed_head != proposal.source_revision_ref
    ):
        raise MigratedPhaseGateEvaluationError(
            "definition qualification differs from proposal authority"
        )
    if (
        implementation.coordinate != proposal.coordinate
        or implementation.definition_ref != proposal.definition_ref
        or implementation.gate_digest != proposal.gate_digest
    ):
        raise MigratedPhaseGateEvaluationError(
            "implementation publication differs from proposal authority"
        )
    if (
        review.coordinate != proposal.coordinate
        or review.definition_ref != proposal.definition_ref
        or review.gate_digest != proposal.gate_digest
        or review.reviewed_implementation_commit != implementation.implementation_commit
    ):
        raise MigratedPhaseGateEvaluationError(
            "independent review differs from implementation authority"
        )
    implementation_path_digest = fingerprint(
        {
            "changed_paths": list(implementation.changed_paths),
            "tree_entry_oids": list(implementation.tree_entry_oids),
        }
    )
    if review.changed_path_digest != implementation_path_digest:
        raise MigratedPhaseGateEvaluationError(
            "review changed-path digest differs from implementation publication"
        )
    implementation_issue = cast(IssueAuthorityV1, implementation.issue_authority)
    review_issue = cast(IssueAuthorityV1, review.review_issue_authority)
    if review.reviewer_execution_id != review_issue.owner_execution_id:
        raise MigratedPhaseGateEvaluationError("foreign reviewer substitution")
    if review_issue.owner_execution_id == implementation_issue.owner_execution_id:
        raise MigratedPhaseGateEvaluationError("implementer self-review")
    if (
        closeout.issue_path != implementation_issue.issue_path
        or closeout.owner_execution_id != implementation_issue.owner_execution_id
        or closeout.scope_digest != implementation_issue.scope_digest
        or closeout.before_issue_blob != implementation_issue.issue_blob
        or closeout.implementation_commit != implementation.implementation_commit
        or closeout.independent_verdict_ref != review.evidence_ref
    ):
        raise MigratedPhaseGateEvaluationError(
            "implementation closeout differs from implementation or review authority"
        )

    coordinator = authority_sources.coordinator_wire
    expected_coordinator = {
        "goal_tag": proposal.goal_tag,
        "execution_id": acceptance.accepting_execution_id,
        "current": acceptance.coordinator_current,
        "authority_ref": acceptance.coordinator_authority_ref,
    }
    _exact_authority(expected_coordinator, coordinator, "coordinator")

    digest_by_key = {
        item.dependency_key: item.dependency_digest
        for item in proposal.dependency_bindings
    }
    dependency_states: list[tuple[str, DependencyState]] = []
    dependency_observations: list[GoalPhaseDependencyObservationV2] = []
    for item in bundle.entries:
        if not isinstance(item, DependencyEvidenceV1):
            continue
        authority = authority_sources.dependency_authorities.get(item.dependency_key)
        if authority is None:
            raise MigratedPhaseGateEvaluationError("dependency authority is absent")
        declaration = authority.get("declaration")
        if type(declaration) is not GoalPhaseDependency:
            raise MigratedPhaseGateEvaluationError(
                "dependency declaration is unavailable"
            )
        declaration.__post_init__()
        digest = goal_phase_dependency_digest(declaration)
        if (
            digest_by_key.get(item.dependency_key) != digest
            or item.dependency_digest != digest
            or item.dependent != declaration.dependent
            or item.prerequisite != declaration.prerequisite
            or item.required_gate_digest != declaration.required_gate_digest
            or item.relation != declaration.relation.value
            or item.dependent_source_revision_ref
            != authority.get("dependent_source_revision_ref")
            or item.prerequisite_source_revision_ref
            != authority.get("prerequisite_source_revision_ref")
            or item.authority_ref != authority.get("authority_ref")
            or item.schema_id != authority.get("evidence_schema_id")
        ):
            raise MigratedPhaseGateEvaluationError(
                "dependency evidence differs from committed declaration"
            )
        availability = authority.get("availability")
        if availability == "not_evaluated":
            derived_state = DependencyState.NOT_EVALUATED
        elif availability == "unresolved":
            observation = observe_unresolved_goal_phase_dependency(
                declaration,
                evaluator_ref=_text(authority.get("evaluator_ref"), "evaluator_ref"),
                currentness_ref=_text(
                    authority.get("currentness_ref"), "currentness_ref"
                ),
            )
            dependency_observations.append(observation)
            derived_state = DependencyState(observation.outcome.value)
        elif availability in {"resolved", "stale"}:
            prerequisite_phase = authority.get("prerequisite_phase")
            if type(prerequisite_phase) is not GoalLanePhase:
                raise MigratedPhaseGateEvaluationError(
                    "resolved dependency lacks prerequisite Phase authority"
                )
            observation = observe_goal_phase_dependency(
                declaration,
                dependent_source_revision_ref=_text(
                    authority.get("dependent_source_revision_ref"),
                    "dependent_source_revision_ref",
                ),
                prerequisite_source_revision_ref=_text(
                    authority.get("prerequisite_source_revision_ref"),
                    "prerequisite_source_revision_ref",
                ),
                prerequisite_phase=prerequisite_phase,
                evaluator_ref=_text(authority.get("evaluator_ref"), "evaluator_ref"),
                currentness_ref=_text(
                    authority.get("currentness_ref"), "currentness_ref"
                ),
            )
            historical_state = DependencyState(observation.outcome.value)
            if availability == "stale":
                if item.state is not historical_state:
                    raise MigratedPhaseGateEvaluationError(
                        "stale dependency evidence differs from verified source state"
                    )
                observation = replace(
                    observation,
                    outcome=GoalLanePhaseGateOutcome.STALE,
                )
            dependency_observations.append(observation)
            derived_state = DependencyState(observation.outcome.value)
        else:
            raise MigratedPhaseGateEvaluationError(
                "dependency availability is not canonical"
            )
        if availability != "stale" and item.state is not derived_state:
            raise MigratedPhaseGateEvaluationError(
                "caller dependency outcome differs from canonical evaluation"
            )
        dependency_states.append((item.dependency_key, derived_state))

    unresolved_digests: list[tuple[str, str]] = []
    for key, authority in authority_sources.dependency_authorities.items():
        if key in digest_by_key:
            continue
        declaration = authority.get("declaration")
        if (
            authority.get("availability") != "unresolved_native"
            or type(declaration) is not GoalPhaseUnresolvedDependencyV1
            or declaration.dependency_key != key
            or declaration.dependent != proposal.coordinate
            or declaration.owner_goal_tag != proposal.goal_tag
            or authority.get("source_document_ref") != proposal.document_ref
        ):
            raise MigratedPhaseGateEvaluationError(
                "unresolved dependency authority is not canonical"
            )
        unresolved_digests.append(
            (key, goal_phase_unresolved_dependency_digest(declaration))
        )
        dependency_states.append((key, DependencyState.UNRESOLVED))

    value = object.__new__(VerifiedMigratedPhaseGateAuthorityV1)
    object.__setattr__(value, "proposal", proposal)
    object.__setattr__(value, "acceptance", acceptance)
    object.__setattr__(value, "bundle", bundle)
    object.__setattr__(value, "role_currentness", tuple(sorted(role_currentness)))
    object.__setattr__(value, "dependency_states", tuple(sorted(dependency_states)))
    object.__setattr__(
        value, "unresolved_dependency_digests", tuple(sorted(unresolved_digests))
    )
    object.__setattr__(
        value,
        "dependency_observations",
        tuple(sorted(dependency_observations, key=lambda item: item.dependency_key)),
    )
    object.__setattr__(value, "coordinator_current", bool(coordinator["current"]))
    body = _verified_body(value)
    object.__setattr__(
        value,
        "verification_ref",
        "goal-migrated-phase-authority-verification:" + fingerprint(body),
    )
    object.__setattr__(value, "verifier_token", _register_verified(body))
    return value


def evaluate_migrated_phase_gate(
    verified: VerifiedMigratedPhaseGateAuthorityV1,
) -> MigratedPhaseGateEvaluationV1:
    """Reduce only sealed, independently verified M14 authority."""

    _require_verified(verified)
    proposal = verified.proposal
    acceptance = verified.acceptance
    bundle = verified.bundle
    reasons: list[EvaluationReason] = []
    epochs: list[str] = []
    currentness_by_ref = dict(verified.role_currentness)
    for item in bundle.entries:
        item.__post_init__()
        state = currentness_by_ref[item.evidence_ref]
        epochs.append(
            fingerprint(
                {"epoch_ref": item.source_epoch.epoch_ref, "currentness": state.value}
            )
        )
        if state is SourceCurrentness.STALE:
            reasons.append(EvaluationReason(_stale_code(item), item.role_key))
    review = next(
        item for item in bundle.entries if type(item) is IndependentAcceptanceEvidenceV1
    )
    if review.verdict == "rejected":
        reasons.append(
            EvaluationReason(
                ReasonCode.INDEPENDENT_ACCEPTANCE_REJECTED, review.role_key
            )
        )
    if not verified.coordinator_current or acceptance.decision == "reject_evaluation":
        reasons.append(
            EvaluationReason(ReasonCode.COORDINATOR_REVOKED, "goal_governance")
        )
    for dependency_key, state in verified.dependency_states:
        mapped = _dependency_reason(state)
        if mapped is not None:
            reasons.append(EvaluationReason(mapped, dependency_key))

    ordered_reasons = tuple(sorted(set(reasons)))
    result = _result_for(ordered_reasons)
    dependency_set_body: dict[str, object] = {
        "dependencies": [item.to_wire() for item in proposal.dependency_bindings]
    }
    if verified.unresolved_dependency_digests:
        dependency_set_body["unresolved_dependencies"] = [
            {"dependency_key": key, "declaration_digest": digest}
            for key, digest in verified.unresolved_dependency_digests
        ]
    dependency_set_digest = fingerprint(dependency_set_body)
    evaluator_ref = "goal-migrated-phase-evaluator:" + fingerprint(
        {
            "profile": EVALUATOR_PROFILE,
            "proposal_ref": proposal.proposal_ref,
            "acceptance_ref": acceptance.acceptance_ref,
            "bundle_ref": bundle.bundle_ref,
            "source_epochs": sorted(epochs),
            "dependency_set_digest": dependency_set_digest,
        }
    )
    gate_ref = (
        None
        if result is not EvaluationResult.SATISFIED
        else "goal-phase-gate-observation:"
        + fingerprint(
            {
                "evaluator_ref": evaluator_ref,
                "gate_digest": proposal.gate_digest,
                "bundle_ref": bundle.bundle_ref,
            }
        )
    )
    currentness_ref = "goal-migrated-phase-evaluation-currentness:" + fingerprint(
        {
            "evaluator_ref": evaluator_ref,
            "result": result.value,
            "source_epochs": sorted(epochs),
        }
    )
    return MigratedPhaseGateEvaluationV1(
        proposal_ref=proposal.proposal_ref,
        acceptance_ref=acceptance.acceptance_ref,
        evidence_bundle_ref=bundle.bundle_ref,
        evaluator_ref=evaluator_ref,
        result=result,
        reasons=ordered_reasons,
        source_epoch_ref=fingerprint({"source_epochs": sorted(epochs)}),
        dependency_set_digest=dependency_set_digest,
        gate_observation_ref=gate_ref,
        dependency_observation_refs=tuple(
            sorted(item.observation_ref for item in verified.dependency_observations)
        ),
        currentness_ref=currentness_ref,
    )


def _dependency_reason(state: DependencyState) -> ReasonCode | None:
    return {
        DependencyState.SATISFIED: None,
        DependencyState.PENDING: ReasonCode.DEPENDENCY_PENDING,
        DependencyState.REJECTED: ReasonCode.DEPENDENCY_REJECTED,
        DependencyState.STALE: ReasonCode.DEPENDENCY_STALE,
        DependencyState.UNRESOLVED: ReasonCode.DEPENDENCY_UNRESOLVED,
        DependencyState.NOT_EVALUATED: ReasonCode.DEPENDENCY_NOT_EVALUATED,
    }[state]


def _stale_code(item: Evidence) -> ReasonCode:
    return {
        DefinitionQualificationEvidenceV1: ReasonCode.DEFINITION_QUALIFICATION_STALE,
        ImplementationPublicationEvidenceV1: ReasonCode.IMPLEMENTATION_PUBLICATION_STALE,
        IndependentAcceptanceEvidenceV1: ReasonCode.INDEPENDENT_ACCEPTANCE_STALE,
        ImplementationCloseoutEvidenceV1: ReasonCode.IMPLEMENTATION_CLOSEOUT_STALE,
        DependencyCompletionEvidenceV1: ReasonCode.DEPENDENCY_STALE,
        DependencyAcceptanceEvidenceV1: ReasonCode.DEPENDENCY_STALE,
    }[type(item)]


def _result_for(reasons: tuple[EvaluationReason, ...]) -> EvaluationResult:
    codes = {item.code for item in reasons}
    if codes & {
        ReasonCode.COORDINATOR_REVOKED,
        ReasonCode.INDEPENDENT_ACCEPTANCE_REJECTED,
        ReasonCode.DEPENDENCY_PENDING,
        ReasonCode.DEPENDENCY_REJECTED,
    }:
        return EvaluationResult.REJECTED
    if codes & {
        ReasonCode.DEFINITION_QUALIFICATION_STALE,
        ReasonCode.IMPLEMENTATION_PUBLICATION_STALE,
        ReasonCode.INDEPENDENT_ACCEPTANCE_STALE,
        ReasonCode.IMPLEMENTATION_CLOSEOUT_STALE,
        ReasonCode.DEPENDENCY_STALE,
    }:
        return EvaluationResult.STALE
    if codes:
        return EvaluationResult.UNAVAILABLE
    return EvaluationResult.SATISFIED


def decode_qualification_proposal(raw: object) -> QualificationProposalV1:
    values = _mapping(raw, "proposal")
    _fields(
        values,
        {
            "schema_id",
            "proposal_ref",
            "goal_path",
            "goal_tag",
            "coordinate",
            "document_ref",
            "source_revision_ref",
            "definition_ref",
            "gate_digest",
            "evaluator_profile",
            "dependency_bindings",
            "evidence_role_keys",
        },
        "proposal",
    )
    if values["schema_id"] != PROPOSAL_SCHEMA:
        raise MigratedPhaseGateEvaluationError("unsupported proposal schema")
    result = QualificationProposalV1(
        proposal_ref=_text(values["proposal_ref"], "proposal_ref"),
        goal_path=_text(values["goal_path"], "goal_path"),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        coordinate=_decode_coordinate(values["coordinate"]),
        document_ref=_text(values["document_ref"], "document_ref"),
        source_revision_ref=_text(values["source_revision_ref"], "source_revision_ref"),
        definition_ref=_text(values["definition_ref"], "definition_ref"),
        gate_digest=_text(values["gate_digest"], "gate_digest"),
        evaluator_profile=_text(values["evaluator_profile"], "evaluator_profile"),
        dependency_bindings=tuple(
            _decode_dependency_binding(item)
            for item in _array(values["dependency_bindings"], "dependency_bindings")
        ),
        evidence_role_keys=tuple(
            _text(item, "evidence_role_key")
            for item in _array(values["evidence_role_keys"], "evidence_role_keys")
        ),
    )
    if values["proposal_ref"] != result.proposal_ref:
        raise MigratedPhaseGateEvaluationError("proposal ref mismatch")
    return result


def decode_qualification_acceptance(raw: object) -> QualificationAcceptanceV1:
    values = _mapping(raw, "acceptance")
    _fields(
        values,
        {
            "schema_id",
            "acceptance_ref",
            "proposal_ref",
            "accepting_execution_id",
            "acceptance_issue_authority",
            "coordinator_authority_ref",
            "coordinator_current",
            "decision",
            "evidence_bundle_ref",
        },
        "acceptance",
    )
    if values["schema_id"] != ACCEPTANCE_SCHEMA:
        raise MigratedPhaseGateEvaluationError("unsupported acceptance schema")
    result = QualificationAcceptanceV1(
        acceptance_ref=_text(values["acceptance_ref"], "acceptance_ref"),
        proposal_ref=_text(values["proposal_ref"], "proposal_ref"),
        accepting_execution_id=_text(
            values["accepting_execution_id"], "accepting_execution_id"
        ),
        acceptance_issue_authority=_decode_issue(values["acceptance_issue_authority"]),
        coordinator_authority_ref=_text(
            values["coordinator_authority_ref"], "coordinator_authority_ref"
        ),
        coordinator_current=_boolean(
            values["coordinator_current"], "coordinator_current"
        ),
        decision=_text(values["decision"], "decision"),
        evidence_bundle_ref=_text(values["evidence_bundle_ref"], "evidence_bundle_ref"),
    )
    if values["acceptance_ref"] != result.acceptance_ref:
        raise MigratedPhaseGateEvaluationError("acceptance ref mismatch")
    return result


def decode_evidence_bundle(raw: object) -> EvidenceBundleV1:
    values = _mapping(raw, "evidence bundle")
    _fields(values, {"schema_id", "entries", "bundle_ref"}, "evidence bundle")
    if values["schema_id"] != BUNDLE_SCHEMA:
        raise MigratedPhaseGateEvaluationError("unsupported evidence bundle schema")
    entries = tuple(
        _decode_evidence(item) for item in _array(values["entries"], "entries")
    )
    result = EvidenceBundleV1(entries=entries)
    if values["bundle_ref"] != result.bundle_ref:
        raise MigratedPhaseGateEvaluationError("evidence bundle ref mismatch")
    return result


def decode_migrated_phase_gate_evaluation(raw: object) -> MigratedPhaseGateEvaluationV1:
    values = _mapping(raw, "evaluation")
    _fields(
        values,
        {
            "schema_id",
            "proposal_ref",
            "acceptance_ref",
            "evidence_bundle_ref",
            "evaluator_ref",
            "result",
            "reasons",
            "source_epoch_ref",
            "dependency_set_digest",
            "gate_observation_ref",
            "dependency_observation_refs",
            "currentness_ref",
            "evaluation_ref",
        },
        "evaluation",
    )
    if values["schema_id"] != EVALUATION_SCHEMA:
        raise MigratedPhaseGateEvaluationError("unsupported evaluation schema")
    result = MigratedPhaseGateEvaluationV1(
        proposal_ref=_text(values["proposal_ref"], "proposal_ref"),
        acceptance_ref=_text(values["acceptance_ref"], "acceptance_ref"),
        evidence_bundle_ref=_text(values["evidence_bundle_ref"], "evidence_bundle_ref"),
        evaluator_ref=_text(values["evaluator_ref"], "evaluator_ref"),
        result=EvaluationResult(_text(values["result"], "result")),
        reasons=tuple(
            _decode_reason(item) for item in _array(values["reasons"], "reasons")
        ),
        source_epoch_ref=_text(values["source_epoch_ref"], "source_epoch_ref"),
        dependency_set_digest=_text(
            values["dependency_set_digest"], "dependency_set_digest"
        ),
        gate_observation_ref=None
        if values["gate_observation_ref"] is None
        else _text(values["gate_observation_ref"], "gate_observation_ref"),
        dependency_observation_refs=tuple(
            _text(item, "dependency_observation_ref")
            for item in _array(
                values["dependency_observation_refs"], "dependency_observation_refs"
            )
        ),
        currentness_ref=_text(values["currentness_ref"], "currentness_ref"),
    )
    if values["evaluation_ref"] != result.evaluation_ref:
        raise MigratedPhaseGateEvaluationError("evaluation ref mismatch")
    return result


def _decode_coordinate(raw: object) -> GoalPhaseCoordinate:
    values = _mapping(raw, "coordinate")
    _fields(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        lane_key=_text(values["lane_key"], "lane_key"),
        phase_key=_text(values["phase_key"], "phase_key"),
    )


def _decode_dependency_binding(raw: object) -> DependencyBindingV1:
    values = _mapping(raw, "dependency binding")
    _fields(
        values,
        {"dependency_key", "dependency_digest"},
        "dependency binding",
    )
    return DependencyBindingV1(
        dependency_key=_text(values["dependency_key"], "dependency_key"),
        dependency_digest=_text(values["dependency_digest"], "dependency_digest"),
    )


def _decode_issue(raw: object) -> IssueAuthorityV1:
    values = _mapping(raw, "Issue authority")
    _fields(
        values,
        {"issue_path", "issue_blob", "owner_execution_id", "status", "scope_digest"},
        "Issue authority",
    )
    return IssueAuthorityV1(
        issue_path=_text(values["issue_path"], "issue_path"),
        issue_blob=_text(values["issue_blob"], "issue_blob"),
        owner_execution_id=_text(values["owner_execution_id"], "owner_execution_id"),
        status=_text(values["status"], "status"),
        scope_digest=_text(values["scope_digest"], "scope_digest"),
    )


def _decode_epoch(raw: object) -> SourceEpochV1:
    values = _mapping(raw, "source epoch")
    _fields(
        values,
        {
            "repository_ref",
            "source_commit",
            "observed_head",
            "path",
            "blob",
            "currentness",
            "protected_paths",
            "epoch_ref",
        },
        "source epoch",
    )
    result = SourceEpochV1(
        repository_ref=_text(values["repository_ref"], "repository_ref"),
        source_commit=_text(values["source_commit"], "source_commit"),
        observed_head=_text(values["observed_head"], "observed_head"),
        path=_text(values["path"], "path"),
        blob=_text(values["blob"], "blob"),
        currentness=SourceCurrentness(_text(values["currentness"], "currentness")),
        protected_paths=tuple(
            _text(item, "protected_path")
            for item in _array(values["protected_paths"], "protected_paths")
        ),
    )
    if values["epoch_ref"] != result.epoch_ref:
        raise MigratedPhaseGateEvaluationError("source epoch ref mismatch")
    return result


def _decode_reason(raw: object) -> EvaluationReason:
    values = _mapping(raw, "reason")
    _fields(values, {"code", "role_key"}, "reason")
    return EvaluationReason(
        code=ReasonCode(_text(values["code"], "code")),
        role_key=_text(values["role_key"], "role_key"),
    )


def _decode_evidence(raw: object) -> Evidence:
    values = _mapping(raw, "evidence")
    schema = _text(values.get("schema_id"), "schema_id")
    common = {"schema_id", "role", "role_key", "source_epoch", "evidence_ref"}
    role = _text(values.get("role"), "role")
    role_key = _text(values.get("role_key"), "role_key")
    epoch = _decode_epoch(values.get("source_epoch"))
    if schema == DefinitionQualificationEvidenceV1.schema_id:
        fields = common | {
            "m13_publication_receipt_ref",
            "reconciliation_receipt_ref",
            "goal_path",
            "goal_tag",
            "coordinate",
            "before_document_ref",
            "after_document_ref",
            "before_definition_ref",
            "after_definition_ref",
            "proposal_publication_ref",
            "acceptance_publication_ref",
            "publication_commit",
            "goal_blob",
            "repository_commit_receipt_ref",
        }
        _fields(values, fields, "definition evidence")
        result: Evidence = DefinitionQualificationEvidenceV1(
            role=role,
            role_key=role_key,
            source_epoch=epoch,
            m13_publication_receipt_ref=_text(
                values["m13_publication_receipt_ref"], "m13_publication_receipt_ref"
            ),
            reconciliation_receipt_ref=_text(
                values["reconciliation_receipt_ref"], "reconciliation_receipt_ref"
            ),
            goal_path=_text(values["goal_path"], "goal_path"),
            goal_tag=_text(values["goal_tag"], "goal_tag"),
            coordinate=_decode_coordinate(values["coordinate"]),
            before_document_ref=_text(
                values["before_document_ref"], "before_document_ref"
            ),
            after_document_ref=_text(
                values["after_document_ref"], "after_document_ref"
            ),
            before_definition_ref=_text(
                values["before_definition_ref"], "before_definition_ref"
            ),
            after_definition_ref=_text(
                values["after_definition_ref"], "after_definition_ref"
            ),
            proposal_publication_ref=_text(
                values["proposal_publication_ref"], "proposal_publication_ref"
            ),
            acceptance_publication_ref=_text(
                values["acceptance_publication_ref"], "acceptance_publication_ref"
            ),
            publication_commit=_text(
                values["publication_commit"], "publication_commit"
            ),
            goal_blob=_text(values["goal_blob"], "goal_blob"),
            repository_commit_receipt_ref=_text(
                values["repository_commit_receipt_ref"], "repository_commit_receipt_ref"
            ),
        )
    elif schema == ImplementationPublicationEvidenceV1.schema_id:
        fields = common | {
            "coordinate",
            "definition_ref",
            "gate_digest",
            "issue_authority",
            "parent_commit",
            "implementation_commit",
            "changed_paths",
            "tree_entry_oids",
            "repository_commit_receipt_ref",
        }
        _fields(values, fields, "implementation evidence")
        result = ImplementationPublicationEvidenceV1(
            role=role,
            role_key=role_key,
            source_epoch=epoch,
            coordinate=_decode_coordinate(values["coordinate"]),
            definition_ref=_text(values["definition_ref"], "definition_ref"),
            gate_digest=_text(values["gate_digest"], "gate_digest"),
            issue_authority=_decode_issue(values["issue_authority"]),
            parent_commit=_text(values["parent_commit"], "parent_commit"),
            implementation_commit=_text(
                values["implementation_commit"], "implementation_commit"
            ),
            changed_paths=tuple(
                _text(item, "changed_path")
                for item in _array(values["changed_paths"], "changed_paths")
            ),
            tree_entry_oids=tuple(
                _text(item, "tree_entry_oid")
                for item in _array(values["tree_entry_oids"], "tree_entry_oids")
            ),
            repository_commit_receipt_ref=_text(
                values["repository_commit_receipt_ref"], "repository_commit_receipt_ref"
            ),
        )
    elif schema == IndependentAcceptanceEvidenceV1.schema_id:
        fields = common | {
            "verdict",
            "reviewer_execution_id",
            "reviewed_implementation_commit",
            "changed_path_digest",
            "coordinate",
            "definition_ref",
            "gate_digest",
            "validation_evidence_refs",
            "review_issue_authority",
            "artifact_path",
            "artifact_blob",
            "publication_commit",
            "repository_commit_receipt_ref",
        }
        _fields(values, fields, "review evidence")
        result = IndependentAcceptanceEvidenceV1(
            role=role,
            role_key=role_key,
            source_epoch=epoch,
            verdict=_text(values["verdict"], "verdict"),
            reviewer_execution_id=_text(
                values["reviewer_execution_id"], "reviewer_execution_id"
            ),
            reviewed_implementation_commit=_text(
                values["reviewed_implementation_commit"],
                "reviewed_implementation_commit",
            ),
            changed_path_digest=_text(
                values["changed_path_digest"], "changed_path_digest"
            ),
            coordinate=_decode_coordinate(values["coordinate"]),
            definition_ref=_text(values["definition_ref"], "definition_ref"),
            gate_digest=_text(values["gate_digest"], "gate_digest"),
            validation_evidence_refs=tuple(
                _text(item, "validation_evidence_ref")
                for item in _array(
                    values["validation_evidence_refs"], "validation_evidence_refs"
                )
            ),
            review_issue_authority=_decode_issue(values["review_issue_authority"]),
            artifact_path=_text(values["artifact_path"], "artifact_path"),
            artifact_blob=_text(values["artifact_blob"], "artifact_blob"),
            publication_commit=_text(
                values["publication_commit"], "publication_commit"
            ),
            repository_commit_receipt_ref=_text(
                values["repository_commit_receipt_ref"], "repository_commit_receipt_ref"
            ),
        )
    elif schema == ImplementationCloseoutEvidenceV1.schema_id:
        fields = common | {
            "issue_path",
            "owner_execution_id",
            "scope_digest",
            "before_issue_blob",
            "after_issue_blob",
            "implementation_commit",
            "independent_verdict_ref",
            "closeout_commit",
            "repository_commit_receipt_ref",
        }
        _fields(values, fields, "closeout evidence")
        result = ImplementationCloseoutEvidenceV1(
            role=role,
            role_key=role_key,
            source_epoch=epoch,
            issue_path=_text(values["issue_path"], "issue_path"),
            owner_execution_id=_text(
                values["owner_execution_id"], "owner_execution_id"
            ),
            scope_digest=_text(values["scope_digest"], "scope_digest"),
            before_issue_blob=_text(values["before_issue_blob"], "before_issue_blob"),
            after_issue_blob=_text(values["after_issue_blob"], "after_issue_blob"),
            implementation_commit=_text(
                values["implementation_commit"], "implementation_commit"
            ),
            independent_verdict_ref=_text(
                values["independent_verdict_ref"], "independent_verdict_ref"
            ),
            closeout_commit=_text(values["closeout_commit"], "closeout_commit"),
            repository_commit_receipt_ref=_text(
                values["repository_commit_receipt_ref"], "repository_commit_receipt_ref"
            ),
        )
    elif schema in {
        DependencyCompletionEvidenceV1.schema_id,
        DependencyAcceptanceEvidenceV1.schema_id,
    }:
        fields = common | {
            "dependency_key",
            "dependency_digest",
            "relation",
            "dependent",
            "prerequisite",
            "dependent_source_revision_ref",
            "prerequisite_source_revision_ref",
            "required_gate_digest",
            "state",
            "authority_ref",
        }
        _fields(values, fields, "dependency evidence")
        cls = (
            DependencyCompletionEvidenceV1
            if schema == DependencyCompletionEvidenceV1.schema_id
            else DependencyAcceptanceEvidenceV1
        )
        result = cls(
            role=role,
            role_key=role_key,
            source_epoch=epoch,
            dependency_key=_text(values["dependency_key"], "dependency_key"),
            dependency_digest=_text(values["dependency_digest"], "dependency_digest"),
            relation=_text(values["relation"], "relation"),
            dependent=_decode_coordinate(values["dependent"]),
            prerequisite=_decode_coordinate(values["prerequisite"]),
            dependent_source_revision_ref=_text(
                values["dependent_source_revision_ref"], "dependent_source_revision_ref"
            ),
            prerequisite_source_revision_ref=_text(
                values["prerequisite_source_revision_ref"],
                "prerequisite_source_revision_ref",
            ),
            required_gate_digest=_text(
                values["required_gate_digest"], "required_gate_digest"
            ),
            state=DependencyState(_text(values["state"], "state")),
            authority_ref=_text(values["authority_ref"], "authority_ref"),
        )
    else:
        raise MigratedPhaseGateEvaluationError("unsupported evidence schema")
    if values["evidence_ref"] != result.evidence_ref:
        raise MigratedPhaseGateEvaluationError("evidence ref mismatch")
    return result
