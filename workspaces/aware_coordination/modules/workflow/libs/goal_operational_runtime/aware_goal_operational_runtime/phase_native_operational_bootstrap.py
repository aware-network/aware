"""Evidence-qualified whole-Goal Phase-native operational bootstrap.

The module is deliberately runtime neutral.  Structural decoding, authority
verification, pure planning, and repository publication are separate steps.
"""
# pyright: reportUnusedCallResult=false, reportUnsupportedDunderAll=false

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

from .phase_codec import decode_goal_phase_bundle, goal_phase_bundle_to_wire
from .phase_contracts import (
    GoalLanePhase,
    GoalLanePhaseState,
    GoalLanePhaseWorkDisposition,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)
from .phase_document import (
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
)
from .identity import fingerprint

PROPOSAL_SCHEMA = "aware.goal.phase-native-operational-bootstrap-proposal.v1"
EVIDENCE_SCHEMA = "aware.goal.phase-native-operational-bootstrap-evidence.v1"
COORDINATOR_ACCEPTANCE_SCHEMA = (
    "aware.goal.phase-native-operational-bootstrap-coordinator-acceptance.v1"
)
COORDINATOR_AUTHORITY_SCHEMA = "aware.goal.coordinator-authority.v1"
GOAL_OWNER_AUTHORITY_PUBLICATION_SCHEMA = "aware.goal.owner-coordinator-authority-publication.v1"
COORDINATOR_ACCEPTANCE_PUBLICATION_SCHEMA = "aware.goal.coordinator-acceptance-publication.v1"
BOOTSTRAP_PLAN_SCHEMA = "aware.goal.phase-native-operational-bootstrap-plan.v1"
BOOTSTRAP_RECEIPT_SCHEMA = "aware.goal.phase-native-operational-bootstrap-publication.v1"
BOOTSTRAP_CURRENTNESS_SCHEMA = "aware.goal.phase-native-operational-bootstrap-currentness.v1"
BOOTSTRAP_REPOSITORY_EVIDENCE_SCHEMA = "aware.goal.phase-native-operational-bootstrap-repository-evidence.v1"

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_UTC = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$")
_KEY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class GoalPhaseNativeOperationalBootstrapError(ValueError):
    """The proposed bootstrap is malformed or lacks qualified authority."""


class GoalPhaseBootstrapClassification(StrEnum):
    DEFINITION_ONLY_HISTORICAL = "definition_only_historical"
    DEFINITION_ONLY_FUTURE = "definition_only_future"
    OPERATIONAL_ACTIVE = "operational_active"
    OPERATIONAL_HELD = "operational_held"
    OPERATIONAL_ACCEPTED = "operational_accepted"
    ALREADY_OPERATIONAL = "already_operational"


@dataclass(frozen=True, slots=True)
class GoalPhaseExecutionAuthorityTransitionV1:
    source_execution_authority_profile: str
    parity_ref: str
    target_execution_authority_profile: str = "phase_native_operational_v1"
    legacy_execution_disposition: str = "retired"

    def __post_init__(self) -> None:
        if self.source_execution_authority_profile not in {
            "legacy_goal_lane_row_v1", "hybrid_legacy_row_phase_native_v1"
        }:
            raise GoalPhaseNativeOperationalBootstrapError("invalid source execution authority")
        if self.target_execution_authority_profile != "phase_native_operational_v1":
            raise GoalPhaseNativeOperationalBootstrapError("invalid target execution authority")
        if self.legacy_execution_disposition != "retired":
            raise GoalPhaseNativeOperationalBootstrapError("legacy execution must retire")
        _ref(self.parity_ref, "parity_ref", "goal-phase-native-compatibility-parity")


@dataclass(frozen=True, slots=True)
class CommittedIssueAuthorityEvidenceV1:
    evidence_key: str
    phase_coordinate: GoalPhaseCoordinate
    issue_ref: str
    repository_revision_ref: str
    issue_blob_oid: str
    expected_owner_execution_id: str
    expected_scope_digest: str
    phase_association_ref: str
    work_role: str
    authority_admitted_at: str
    evidence_ref: str = field(init=False)
    expected_status: str = "in_progress"

    def __post_init__(self) -> None:
        _evidence_common(self.evidence_key, self.phase_coordinate)
        _text(self.issue_ref, "issue_ref")
        _git(self.repository_revision_ref, "repository_revision_ref")
        _git(self.issue_blob_oid, "issue_blob_oid")
        if self.expected_status != "in_progress":
            raise GoalPhaseNativeOperationalBootstrapError("Issue evidence must be in_progress")
        _text(self.expected_owner_execution_id, "expected_owner_execution_id")
        _sha(self.expected_scope_digest, "expected_scope_digest")
        _text(self.phase_association_ref, "phase_association_ref")
        _text(self.work_role, "work_role")
        _utc(self.authority_admitted_at, "authority_admitted_at")
        object.__setattr__(self, "evidence_ref", _content_ref("goal-phase-bootstrap-issue-authority", _issue_body(self)))


@dataclass(frozen=True, slots=True)
class GoalPhaseHoldAuthorityEvidenceV1:
    evidence_key: str
    phase_coordinate: GoalPhaseCoordinate
    current_issue_evidence_key: str
    hold_receipt_ref: str
    publication_receipt_ref: str
    repository_commit_ref: str
    source_currentness_ref: str
    evidence_ref: str = field(init=False)

    def __post_init__(self) -> None:
        _evidence_common(self.evidence_key, self.phase_coordinate)
        _key(self.current_issue_evidence_key, "current_issue_evidence_key")
        _ref(self.hold_receipt_ref, "hold_receipt_ref", "goal-phase-hold")
        _ref(self.publication_receipt_ref, "publication_receipt_ref", "goal-publication")
        _git(self.repository_commit_ref, "repository_commit_ref")
        _qualified(self.source_currentness_ref, "source_currentness_ref")
        object.__setattr__(self, "evidence_ref", _content_ref("goal-phase-bootstrap-hold-authority", _hold_body(self)))


@dataclass(frozen=True, slots=True)
class GoalPhaseAcceptanceAuthorityEnvelopeV1:
    evidence_key: str
    phase_coordinate: GoalPhaseCoordinate
    definition_ref: str
    gate_digest: str
    acceptance_ref: str
    accepted_phase: GoalLanePhase
    phase_publication_receipt_ref: str
    repository_commit_ref: str
    changed_authority_path: str
    source_currentness_ref: str
    evidence_ref: str = field(init=False)
    accepted_phase_digest: str = field(init=False)

    def __post_init__(self) -> None:
        _evidence_common(self.evidence_key, self.phase_coordinate)
        _ref(self.definition_ref, "definition_ref", "goal-phase-definition")
        _sha(self.gate_digest, "gate_digest")
        _ref(self.acceptance_ref, "acceptance_ref", "goal-phase-acceptance")
        if type(self.accepted_phase) is not GoalLanePhase:
            raise TypeError("accepted_phase must be GoalLanePhase")
        self.accepted_phase.__post_init__()
        if self.accepted_phase.coordinate != self.phase_coordinate or self.accepted_phase.state is not GoalLanePhaseState.ACCEPTED:
            raise GoalPhaseNativeOperationalBootstrapError("acceptance envelope must contain its exact accepted Phase")
        _ref(self.phase_publication_receipt_ref, "phase_publication_receipt_ref", "goal-phase-publication")
        _git(self.repository_commit_ref, "repository_commit_ref")
        _text(self.changed_authority_path, "changed_authority_path")
        _qualified(self.source_currentness_ref, "source_currentness_ref")
        phase_digest = _digest(_canonical(_phase_wire(self.accepted_phase)))
        object.__setattr__(self, "accepted_phase_digest", phase_digest)
        object.__setattr__(self, "evidence_ref", _content_ref("goal-phase-bootstrap-acceptance-authority", _acceptance_authority_body(self)))


@dataclass(frozen=True, slots=True)
class GoalPhaseTemporalAuthorityEvidenceV1:
    evidence_key: str
    phase_coordinate: GoalPhaseCoordinate
    temporal_ledger_ref: str
    temporal_publication_receipt_ref: str
    snapshot_authority_ref: str
    source_repository_revision_ref: str
    coverage_boundary_ref: str
    currentness_ref: str
    evidence_ref: str = field(init=False)

    def __post_init__(self) -> None:
        _evidence_common(self.evidence_key, self.phase_coordinate)
        for value, name in (
            (self.temporal_ledger_ref, "temporal_ledger_ref"),
            (self.temporal_publication_receipt_ref, "temporal_publication_receipt_ref"),
            (self.snapshot_authority_ref, "snapshot_authority_ref"),
            (self.coverage_boundary_ref, "coverage_boundary_ref"),
            (self.currentness_ref, "currentness_ref"),
        ):
            _qualified(value, name)
        _git(self.source_repository_revision_ref, "source_repository_revision_ref")
        object.__setattr__(self, "evidence_ref", _content_ref("goal-phase-bootstrap-temporal-authority", _temporal_body(self)))


Evidence = CommittedIssueAuthorityEvidenceV1 | GoalPhaseHoldAuthorityEvidenceV1 | GoalPhaseAcceptanceAuthorityEnvelopeV1 | GoalPhaseTemporalAuthorityEvidenceV1


@dataclass(frozen=True, slots=True)
class GoalPhaseBootstrapEvidenceBundleV1:
    issue_authorities: tuple[CommittedIssueAuthorityEvidenceV1, ...] = ()
    hold_authorities: tuple[GoalPhaseHoldAuthorityEvidenceV1, ...] = ()
    acceptance_authorities: tuple[GoalPhaseAcceptanceAuthorityEnvelopeV1, ...] = ()
    temporal_authorities: tuple[GoalPhaseTemporalAuthorityEvidenceV1, ...] = ()
    schema_id: str = EVIDENCE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != EVIDENCE_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported evidence schema")
        all_items: tuple[Evidence, ...] = self.all_items()
        keys = tuple(item.evidence_key for item in all_items)
        for collection in (self.issue_authorities, self.hold_authorities, self.acceptance_authorities, self.temporal_authorities):
            collection_keys = tuple(item.evidence_key for item in collection)
            if collection_keys != tuple(sorted(collection_keys)):
                raise GoalPhaseNativeOperationalBootstrapError("evidence collections must be sorted")
        if len(keys) != len(set(keys)):
            raise GoalPhaseNativeOperationalBootstrapError("evidence keys must be globally unique")
        refs = tuple(item.evidence_ref for item in all_items)
        if len(refs) != len(set(refs)):
            raise GoalPhaseNativeOperationalBootstrapError("evidence refs must be unique")
        issues = {item.evidence_key: item for item in self.issue_authorities}
        for hold in self.hold_authorities:
            issue = issues.get(hold.current_issue_evidence_key)
            if issue is None or issue.phase_coordinate != hold.phase_coordinate:
                raise GoalPhaseNativeOperationalBootstrapError("hold authority lacks matching Issue authority")

    def all_items(self) -> tuple[Evidence, ...]:
        return self.issue_authorities + self.hold_authorities + self.acceptance_authorities + self.temporal_authorities


@dataclass(frozen=True, slots=True)
class GoalPhaseBootstrapEntryV1:
    coordinate: GoalPhaseCoordinate
    definition_ref: str
    gate_digest: str
    classification: GoalPhaseBootstrapClassification
    evidence_keys: tuple[str, ...]
    desired_phase: GoalLanePhase | None

    def __post_init__(self) -> None:
        _ref(self.definition_ref, "definition_ref", "goal-phase-definition")
        _sha(self.gate_digest, "gate_digest")
        if type(self.classification) is not GoalPhaseBootstrapClassification:
            raise TypeError("classification must be exact")
        _keys_tuple(self.evidence_keys, "evidence_keys")
        if self.classification in {GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, GoalPhaseBootstrapClassification.DEFINITION_ONLY_FUTURE}:
            if self.desired_phase is not None:
                raise GoalPhaseNativeOperationalBootstrapError("definition-only entry cannot contain a Phase")
        elif type(self.desired_phase) is not GoalLanePhase or self.desired_phase.coordinate != self.coordinate:
            raise GoalPhaseNativeOperationalBootstrapError("operational entry requires its exact Phase")


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeOperationalBootstrapProposalV1:
    goal_tag: str
    source_document_ref: str
    source_goal_sha256: str
    source_repository_revision_ref: str
    requested_execution_authority_transition: GoalPhaseExecutionAuthorityTransitionV1
    evidence_bundle: GoalPhaseBootstrapEvidenceBundleV1
    entries: tuple[GoalPhaseBootstrapEntryV1, ...]
    aggregate_ref: str = field(init=False)
    schema_id: str = PROPOSAL_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != PROPOSAL_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported proposal schema")
        _text(self.goal_tag, "goal_tag")
        _ref(self.source_document_ref, "source_document_ref", "goal-phase-document")
        _sha(self.source_goal_sha256, "source_goal_sha256")
        _git(self.source_repository_revision_ref, "source_repository_revision_ref")
        if type(self.requested_execution_authority_transition) is not GoalPhaseExecutionAuthorityTransitionV1:
            raise TypeError("requested transition must be exact")
        self.evidence_bundle.__post_init__()
        coordinates = tuple(entry.coordinate for entry in self.entries)
        if coordinates != tuple(sorted(coordinates, key=_coordinate_sort)) or len(coordinates) != len(set(coordinates)):
            raise GoalPhaseNativeOperationalBootstrapError("proposal entries must be coordinate-sorted and unique")
        if any(item.coordinate.goal_tag != self.goal_tag for item in self.entries):
            raise GoalPhaseNativeOperationalBootstrapError("proposal entry belongs to another Goal")
        cited = tuple(key for entry in self.entries for key in entry.evidence_keys)
        available = {item.evidence_key for item in self.evidence_bundle.all_items()}
        if set(cited) != available or len(cited) != len(set(cited)):
            raise GoalPhaseNativeOperationalBootstrapError("evidence must be cited exactly once")
        object.__setattr__(self, "aggregate_ref", _content_ref("goal-phase-native-operational-bootstrap-proposal", _proposal_body(self)))


@dataclass(frozen=True, slots=True)
class GoalCoordinatorAuthorityV1:
    goal_tag: str
    goal_doc_path: str
    authority_profile: str
    coordinator_execution_id: str
    source_repository_revision_ref: str
    source_goal_sha256: str
    source_goal_blob_oid: str
    authority_source_ref: str
    authority_repository_path: str
    authority_repository_revision_ref: str
    authority_blob_oid: str
    currentness_ref: str
    authority_ref: str = field(init=False)
    revocation_state: str = "clear"
    schema_id: str = COORDINATOR_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != COORDINATOR_AUTHORITY_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported coordinator authority schema")
        if self.authority_profile != "committed_goal_owner_v1":
            raise GoalPhaseNativeOperationalBootstrapError(
                "M7 requires committed Goal-owner authority; delegation is not yet typed"
            )
        for value, name in ((self.goal_tag, "goal_tag"), (self.goal_doc_path, "goal_doc_path"), (self.coordinator_execution_id, "coordinator_execution_id"), (self.authority_source_ref, "authority_source_ref"), (self.authority_repository_path, "authority_repository_path")):
            _text(value, name)
        _git(self.source_repository_revision_ref, "source_repository_revision_ref")
        _sha(self.source_goal_sha256, "source_goal_sha256")
        _git(self.source_goal_blob_oid, "source_goal_blob_oid")
        _git(self.authority_repository_revision_ref, "authority_repository_revision_ref")
        _git(self.authority_blob_oid, "authority_blob_oid")
        if self.revocation_state != "clear":
            raise GoalPhaseNativeOperationalBootstrapError("coordinator authority is revoked")
        _ref(self.currentness_ref, "currentness_ref", "goal-coordinator-authority-currentness")
        object.__setattr__(self, "authority_ref", _content_ref("goal-coordinator-authority", _coordinator_authority_body(self)))


@dataclass(frozen=True, slots=True)
class GoalOwnerCoordinatorAuthorityPublicationV1:
    goal_tag: str
    goal_doc_path: str
    goal_owner_execution_id: str
    coordinator_execution_id: str
    coordinator_authority_ref: str
    authority_source_ref: str
    authority_declaration_path: str
    authority_declaration_commit_ref: str
    authority_declaration_blob_oid: str
    issuance_issue_ref: str
    issuance_issue_blob_oid: str
    repository_commit_receipt_ref: str
    published_at: str
    receipt_ref: str = field(init=False)
    schema_id: str = GOAL_OWNER_AUTHORITY_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != GOAL_OWNER_AUTHORITY_PUBLICATION_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError(
                "unsupported Goal-owner authority publication"
            )
        for value, name in (
            (self.goal_tag, "goal_tag"),
            (self.goal_doc_path, "goal_doc_path"),
            (self.goal_owner_execution_id, "goal_owner_execution_id"),
            (self.coordinator_execution_id, "coordinator_execution_id"),
            (self.authority_declaration_path, "authority_declaration_path"),
            (self.issuance_issue_ref, "issuance_issue_ref"),
        ):
            _text(value, name)
        _ref(
            self.coordinator_authority_ref,
            "coordinator_authority_ref",
            "goal-coordinator-authority",
        )
        _ref(
            self.authority_source_ref,
            "authority_source_ref",
            "goal-owner-authority-intent",
        )
        _git(self.authority_declaration_commit_ref, "authority_declaration_commit_ref")
        _git(self.authority_declaration_blob_oid, "authority_declaration_blob_oid")
        _git(self.issuance_issue_blob_oid, "issuance_issue_blob_oid")
        if self.repository_commit_receipt_ref != (
            f"repository-commit:{self.authority_declaration_commit_ref}"
        ):
            raise GoalPhaseNativeOperationalBootstrapError(
                "Goal-owner authority publication receipt differs from commit"
            )
        _utc(self.published_at, "published_at")
        object.__setattr__(
            self,
            "receipt_ref",
            _content_ref(
                "goal-owner-coordinator-authority-publication",
                _goal_owner_authority_publication_body(self),
            ),
        )


@dataclass(frozen=True, slots=True)
class GoalCoordinatorAcceptancePublicationV1:
    proposal_aggregate_ref: str
    coordinator_acceptance_ref: str
    coordinator_execution_id: str
    acceptance_path: str
    acceptance_commit_ref: str
    acceptance_blob_oid: str
    issuance_issue_ref: str
    issuance_issue_blob_oid: str
    repository_commit_receipt_ref: str
    published_at: str
    receipt_ref: str = field(init=False)
    schema_id: str = COORDINATOR_ACCEPTANCE_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != COORDINATOR_ACCEPTANCE_PUBLICATION_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError(
                "unsupported coordinator-acceptance publication"
            )
        _ref(
            self.proposal_aggregate_ref,
            "proposal_aggregate_ref",
            "goal-phase-native-operational-bootstrap-proposal",
        )
        _ref(
            self.coordinator_acceptance_ref,
            "coordinator_acceptance_ref",
            "goal-phase-native-operational-bootstrap-coordinator-acceptance",
        )
        for value, name in (
            (self.coordinator_execution_id, "coordinator_execution_id"),
            (self.acceptance_path, "acceptance_path"),
            (self.issuance_issue_ref, "issuance_issue_ref"),
        ):
            _text(value, name)
        _git(self.acceptance_commit_ref, "acceptance_commit_ref")
        _git(self.acceptance_blob_oid, "acceptance_blob_oid")
        _git(self.issuance_issue_blob_oid, "issuance_issue_blob_oid")
        if self.repository_commit_receipt_ref != (
            f"repository-commit:{self.acceptance_commit_ref}"
        ):
            raise GoalPhaseNativeOperationalBootstrapError(
                "coordinator acceptance publication receipt differs from commit"
            )
        _utc(self.published_at, "published_at")
        object.__setattr__(
            self,
            "receipt_ref",
            _content_ref(
                "goal-coordinator-acceptance-publication",
                _coordinator_acceptance_publication_body(self),
            ),
        )


@dataclass(frozen=True, slots=True)
class GoalPhaseBootstrapCoordinatorAcceptanceV1:
    proposal_aggregate_ref: str
    goal_tag: str
    source_document_ref: str
    source_goal_sha256: str
    source_repository_revision_ref: str
    coordinator_execution_id: str
    coordinator_authority_ref: str
    accepted_at: str
    evidence_refs: tuple[str, ...]
    receipt_ref: str = field(init=False)
    decision: str = "accepted"
    schema_id: str = COORDINATOR_ACCEPTANCE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != COORDINATOR_ACCEPTANCE_SCHEMA or self.decision != "accepted":
            raise GoalPhaseNativeOperationalBootstrapError("coordinator acceptance is not accepted")
        _ref(self.proposal_aggregate_ref, "proposal_aggregate_ref", "goal-phase-native-operational-bootstrap-proposal")
        _text(self.goal_tag, "goal_tag")
        _ref(self.source_document_ref, "source_document_ref", "goal-phase-document")
        _sha(self.source_goal_sha256, "source_goal_sha256")
        _git(self.source_repository_revision_ref, "source_repository_revision_ref")
        _text(self.coordinator_execution_id, "coordinator_execution_id")
        _ref(self.coordinator_authority_ref, "coordinator_authority_ref", "goal-coordinator-authority")
        _utc(self.accepted_at, "accepted_at")
        _tokens(self.evidence_refs, "evidence_refs")
        object.__setattr__(self, "receipt_ref", _content_ref("goal-phase-native-operational-bootstrap-coordinator-acceptance", _coordinator_acceptance_body(self)))


@dataclass(frozen=True, slots=True)
class GoalBootstrapPublicationIssueAuthorityV1:
    issue_ref: str
    owner_execution_id: str
    goal_doc_path: str
    repository_revision_ref: str
    issue_blob_oid: str
    scope_digest: str
    status: str = "in_progress"

    def __post_init__(self) -> None:
        if self.status != "in_progress":
            raise GoalPhaseNativeOperationalBootstrapError("publication Issue must be In Progress")
        for value, name in ((self.issue_ref, "issue_ref"), (self.owner_execution_id, "owner_execution_id"), (self.goal_doc_path, "goal_doc_path")):
            _text(value, name)
        _git(self.repository_revision_ref, "repository_revision_ref")
        _git(self.issue_blob_oid, "issue_blob_oid")
        _sha(self.scope_digest, "scope_digest")


@dataclass(frozen=True, slots=True, init=False)
class VerifiedGoalPhaseBootstrapEvidenceV1:
    evidence_ref: str
    evidence_key: str
    phase_coordinate: GoalPhaseCoordinate
    verification_ref: str
    verifier_token: object


@dataclass(frozen=True, slots=True, init=False)
class VerifiedGoalCoordinatorAcceptanceV1:
    acceptance_ref: str
    proposal_aggregate_ref: str
    publication_head: str
    coordinator_authority_ref: str
    coordinator_acceptance_publication_ref: str
    publication_issue_ref: str
    publication_issue_authority_digest: str
    verification_ref: str
    verifier_token: object


@dataclass(frozen=True, slots=True)
class _VerificationToken:
    nonce: object = field(default_factory=object)


_VERIFICATION_REGISTRY_LIMIT = 256
_VERIFICATION_REGISTRY: OrderedDict[_VerificationToken, str] = OrderedDict()


def _register_verified(body: Mapping[str, object]) -> object:
    token = _VerificationToken()
    _VERIFICATION_REGISTRY[token] = _digest(_canonical(dict(body)))
    while len(_VERIFICATION_REGISTRY) > _VERIFICATION_REGISTRY_LIMIT:
        _VERIFICATION_REGISTRY.popitem(last=False)
    return token


def _require_registered(token: object, body: Mapping[str, object], name: str) -> None:
    if type(token) is not _VerificationToken:
        raise GoalPhaseNativeOperationalBootstrapError(
            f"{name} verifier output lacks a live session"
        )
    retained = _VERIFICATION_REGISTRY.get(token)
    observed = _digest(_canonical(dict(body)))
    if retained is None or retained != observed:
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} verifier output was mutated")


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeOperationalBootstrapPlanV1:
    source_document: GoalPhaseNativeDocumentV1
    proposal: GoalPhaseNativeOperationalBootstrapProposalV1
    coordinator_acceptance: GoalPhaseBootstrapCoordinatorAcceptanceV1
    verified_coordinator_acceptance: VerifiedGoalCoordinatorAcceptanceV1
    verified_evidence: tuple[VerifiedGoalPhaseBootstrapEvidenceV1, ...]
    target_document: GoalPhaseNativeDocumentV2
    semantic_intent_ref: str = field(init=False)
    schema_id: str = BOOTSTRAP_PLAN_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != BOOTSTRAP_PLAN_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported bootstrap plan")
        if type(self.source_document) is not GoalPhaseNativeDocumentV1:
            raise TypeError("source_document must be V1")
        if type(self.proposal) is not GoalPhaseNativeOperationalBootstrapProposalV1:
            raise TypeError("proposal must be exact")
        if type(self.coordinator_acceptance) is not GoalPhaseBootstrapCoordinatorAcceptanceV1:
            raise TypeError("coordinator_acceptance must be exact")
        if type(self.verified_coordinator_acceptance) is not VerifiedGoalCoordinatorAcceptanceV1:
            raise TypeError("coordinator acceptance must be independently verified")
        if type(self.verified_evidence) is not tuple or any(type(item) is not VerifiedGoalPhaseBootstrapEvidenceV1 for item in self.verified_evidence):
            raise TypeError("verified_evidence must contain verifier outputs")
        self.source_document.__post_init__()
        self.proposal.__post_init__()
        self.coordinator_acceptance.__post_init__()
        if type(self.target_document) is not GoalPhaseNativeDocumentV2:
            raise TypeError("target_document must be V2")
        self.target_document.__post_init__()
        expected = _build_bootstrap_target(
            source_document=self.source_document,
            proposal=self.proposal,
            coordinator_acceptance=self.coordinator_acceptance,
            verified_coordinator_acceptance=self.verified_coordinator_acceptance,
            verified_evidence=self.verified_evidence,
        )
        if expected != self.target_document:
            raise GoalPhaseNativeOperationalBootstrapError("plan target is not canonical")
        object.__setattr__(self, "semantic_intent_ref", _content_ref("goal-phase-native-operational-bootstrap-intent", _plan_body(self)))

    @property
    def source_document_ref(self) -> str:
        return self.source_document.document_ref

    @property
    def proposal_aggregate_ref(self) -> str:
        return self.proposal.aggregate_ref

    @property
    def coordinator_acceptance_ref(self) -> str:
        return self.coordinator_acceptance.receipt_ref


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeOperationalBootstrapPublicationReceiptV1:
    semantic_intent_ref: str
    source_document_ref: str
    target_document_ref: str
    execution_authority_ref: str
    proposal_aggregate_ref: str
    coordinator_acceptance_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    changed_path: str
    receipt_ref: str = field(init=False)
    schema_id: str = BOOTSTRAP_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != BOOTSTRAP_RECEIPT_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported publication receipt")
        for value, name, prefix in (
            (self.semantic_intent_ref, "semantic_intent_ref", "goal-phase-native-operational-bootstrap-intent"),
            (self.source_document_ref, "source_document_ref", "goal-phase-document"),
            (self.target_document_ref, "target_document_ref", "goal-phase-document"),
            (self.execution_authority_ref, "execution_authority_ref", "goal-phase-execution-authority"),
            (self.proposal_aggregate_ref, "proposal_aggregate_ref", "goal-phase-native-operational-bootstrap-proposal"),
            (self.coordinator_acceptance_ref, "coordinator_acceptance_ref", "goal-phase-native-operational-bootstrap-coordinator-acceptance"),
        ):
            _ref(value, name, prefix)
        _git(self.repository_commit_ref, "repository_commit_ref")
        if not re.fullmatch(r"repository-commit:(?:[0-9a-f]{40}|[0-9a-f]{64})", self.repository_commit_receipt_ref):
            raise GoalPhaseNativeOperationalBootstrapError("repository_commit_receipt_ref must bind the exact commit")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.repository_commit_ref}":
            raise GoalPhaseNativeOperationalBootstrapError("repository commit receipt differs from commit")
        _text(self.changed_path, "changed_path")
        object.__setattr__(self, "receipt_ref", _content_ref("goal-phase-native-operational-bootstrap-publication", _publication_receipt_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {**_publication_receipt_body(self), "receipt_ref": self.receipt_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseNativeOperationalBootstrapCurrentnessV1:
    publication_receipt_ref: str
    publication_revision_ref: str
    observed_revision_ref: str
    status: str
    projection_currentness: str
    replay_disposition: str
    reasons: tuple[str, ...]
    currentness_ref: str = field(init=False)
    schema_id: str = BOOTSTRAP_CURRENTNESS_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != BOOTSTRAP_CURRENTNESS_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported bootstrap currentness")
        _ref(self.publication_receipt_ref, "publication_receipt_ref", "goal-phase-native-operational-bootstrap-publication")
        _git(self.publication_revision_ref, "publication_revision_ref")
        _git(self.observed_revision_ref, "observed_revision_ref")
        if self.status not in {"current", "stale", "ambiguous"}:
            raise GoalPhaseNativeOperationalBootstrapError("invalid currentness status")
        if self.projection_currentness not in {"exact", "advanced", "changed", "unproven"}:
            raise GoalPhaseNativeOperationalBootstrapError("invalid projection currentness")
        if self.replay_disposition not in {"exact", "reobserved_unchanged", "refuse"}:
            raise GoalPhaseNativeOperationalBootstrapError("invalid replay disposition")
        _tokens(self.reasons, "reasons")
        if (self.status == "current") != (not self.reasons and self.replay_disposition != "refuse"):
            raise GoalPhaseNativeOperationalBootstrapError("currentness outcome and reasons disagree")
        object.__setattr__(self, "currentness_ref", _content_ref("goal-phase-native-operational-bootstrap-currentness", _bootstrap_currentness_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {**_bootstrap_currentness_body(self), "currentness_ref": self.currentness_ref}


@dataclass(frozen=True, slots=True, init=False)
class GoalPhaseBootstrapRepositoryEvidenceV1:
    publication_revision_ref: str
    observed_revision_ref: str
    lineage: str
    protected_paths: tuple[str, ...]
    changed_paths: tuple[str, ...]
    evidence_ref: str = field(init=False)
    verifier_token: object
    schema_id: str = BOOTSTRAP_REPOSITORY_EVIDENCE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_id != BOOTSTRAP_REPOSITORY_EVIDENCE_SCHEMA:
            raise GoalPhaseNativeOperationalBootstrapError("unsupported repository evidence")
        _git(self.publication_revision_ref, "publication_revision_ref")
        _git(self.observed_revision_ref, "observed_revision_ref")
        if self.lineage not in {"equal", "descendant", "unproven"}:
            raise GoalPhaseNativeOperationalBootstrapError("invalid repository lineage")
        if (self.publication_revision_ref == self.observed_revision_ref) != (self.lineage == "equal"):
            raise GoalPhaseNativeOperationalBootstrapError("repository lineage contradicts revisions")
        _tokens(self.protected_paths, "protected_paths")
        _tokens(self.changed_paths, "changed_paths")
        if not set(self.changed_paths).issubset(self.protected_paths):
            raise GoalPhaseNativeOperationalBootstrapError("changed path is not protected")
        body = {
            "schema_id": self.schema_id,
            "publication_revision_ref": self.publication_revision_ref,
            "observed_revision_ref": self.observed_revision_ref,
            "lineage": self.lineage,
            "protected_paths": list(self.protected_paths),
            "changed_paths": list(self.changed_paths),
        }
        object.__setattr__(self, "evidence_ref", _content_ref("goal-phase-bootstrap-repository-evidence", body))


def verify_goal_phase_bootstrap_repository_evidence(
    *,
    publication_revision_ref: str,
    observed_revision_ref: str,
    protected_paths: tuple[str, ...],
    repository_resolver: Callable[[str, str, tuple[str, ...]], Mapping[str, object]],
) -> GoalPhaseBootstrapRepositoryEvidenceV1:
    """Derive currentness evidence through an explicit repository authority boundary."""

    resolved = repository_resolver(
        publication_revision_ref, observed_revision_ref, protected_paths
    )
    if set(resolved) != {"lineage", "changed_paths"}:
        raise GoalPhaseNativeOperationalBootstrapError(
            "repository evidence fields differ"
        )
    lineage = _text(resolved["lineage"], "lineage")
    changed_paths = _strings(resolved["changed_paths"], "changed_paths")
    value = object.__new__(GoalPhaseBootstrapRepositoryEvidenceV1)
    object.__setattr__(value, "publication_revision_ref", publication_revision_ref)
    object.__setattr__(value, "observed_revision_ref", observed_revision_ref)
    object.__setattr__(value, "lineage", lineage)
    object.__setattr__(value, "protected_paths", protected_paths)
    object.__setattr__(value, "changed_paths", changed_paths)
    object.__setattr__(value, "schema_id", BOOTSTRAP_REPOSITORY_EVIDENCE_SCHEMA)
    value.__post_init__()
    object.__setattr__(
        value,
        "verifier_token",
        _register_verified(_repository_evidence_verification_body(value)),
    )
    return value


def issue_goal_phase_native_operational_bootstrap_publication_receipt(
    *,
    plan: GoalPhaseNativeOperationalBootstrapPlanV1,
    repository_commit_ref: str,
    repository_commit_receipt_ref: str,
    changed_path: str,
) -> GoalPhaseNativeOperationalBootstrapPublicationReceiptV1:
    # Re-run plan invariants so a mutated/forged public plan cannot issue evidence.
    plan.__post_init__()
    return GoalPhaseNativeOperationalBootstrapPublicationReceiptV1(
        semantic_intent_ref=plan.semantic_intent_ref,
        source_document_ref=plan.source_document_ref,
        target_document_ref=plan.target_document.document_ref,
        execution_authority_ref=plan.target_document.execution_authority.authority_ref,
        proposal_aggregate_ref=plan.proposal_aggregate_ref,
        coordinator_acceptance_ref=plan.coordinator_acceptance_ref,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=repository_commit_receipt_ref,
        changed_path=changed_path,
    )


def observe_goal_phase_native_operational_bootstrap_currentness(
    *,
    publication_receipt: GoalPhaseNativeOperationalBootstrapPublicationReceiptV1,
    repository_evidence: GoalPhaseBootstrapRepositoryEvidenceV1,
) -> GoalPhaseNativeOperationalBootstrapCurrentnessV1:
    publication_receipt.__post_init__()
    if (
        type(repository_evidence) is not GoalPhaseBootstrapRepositoryEvidenceV1
        or not hasattr(repository_evidence, "verifier_token")
    ):
        raise GoalPhaseNativeOperationalBootstrapError(
            "repository currentness evidence is not independently verified"
        )
    repository_evidence.__post_init__()
    _require_registered(
        repository_evidence.verifier_token,
        _repository_evidence_verification_body(repository_evidence),
        "repository evidence",
    )
    if publication_receipt.repository_commit_receipt_ref != f"repository-commit:{publication_receipt.repository_commit_ref}":
        raise GoalPhaseNativeOperationalBootstrapError("repository commit receipt differs from commit")
    if repository_evidence.publication_revision_ref != publication_receipt.repository_commit_ref:
        raise GoalPhaseNativeOperationalBootstrapError("repository evidence is for another publication")
    observed_revision_ref = repository_evidence.observed_revision_ref
    equal = publication_receipt.repository_commit_ref == observed_revision_ref
    changed = set(repository_evidence.changed_paths)
    if repository_evidence.lineage == "unproven":
        status, projection, replay, reasons = "ambiguous", "unproven", "refuse", ("revision_lineage_unproven",)
    elif publication_receipt.changed_path in changed:
        status, projection, replay, reasons = "stale", "changed", "refuse", ("goal_path_advanced",)
    elif changed:
        status, projection, replay, reasons = "ambiguous", "advanced", "refuse", ("authority_inputs_advanced",)
    else:
        status, projection, replay, reasons = "current", ("exact" if equal else "advanced"), ("exact" if equal else "reobserved_unchanged"), ()
    return GoalPhaseNativeOperationalBootstrapCurrentnessV1(
        publication_receipt_ref=publication_receipt.receipt_ref,
        publication_revision_ref=publication_receipt.repository_commit_ref,
        observed_revision_ref=observed_revision_ref,
        status=status,
        projection_currentness=projection,
        replay_disposition=replay,
        reasons=reasons,
    )


def verify_committed_issue_authority_evidence(
    evidence: CommittedIssueAuthorityEvidenceV1,
    committed_issue_resolver: Callable[[str, str], Mapping[str, object]],
    exact_source_revision: str,
) -> VerifiedGoalPhaseBootstrapEvidenceV1:
    evidence.__post_init__()
    _git(exact_source_revision, "exact_source_revision")
    if evidence.repository_revision_ref != exact_source_revision:
        raise GoalPhaseNativeOperationalBootstrapError("Issue evidence source revision differs")
    resolved = committed_issue_resolver(evidence.issue_ref, exact_source_revision)
    expected = {
        "blob_oid": evidence.issue_blob_oid,
        "status": evidence.expected_status,
        "owner_execution_id": evidence.expected_owner_execution_id,
        "scope_digest": evidence.expected_scope_digest,
        "phase_association_ref": evidence.phase_association_ref,
    }
    _exact_mapping(resolved, expected, "committed Issue authority")
    return _verified(evidence)


def verify_goal_phase_hold_authority(
    evidence: GoalPhaseHoldAuthorityEvidenceV1,
    verified_issue_authority: VerifiedGoalPhaseBootstrapEvidenceV1,
    committed_goal_resolver: Callable[[str], Mapping[str, object]],
) -> VerifiedGoalPhaseBootstrapEvidenceV1:
    evidence.__post_init__()
    _require_verified_evidence(verified_issue_authority)
    if evidence.current_issue_evidence_key != verified_issue_authority.evidence_key or evidence.phase_coordinate != verified_issue_authority.phase_coordinate:
        raise GoalPhaseNativeOperationalBootstrapError("hold and Issue authority differ")
    _exact_mapping(committed_goal_resolver(evidence.repository_commit_ref), {
        "hold_receipt_ref": evidence.hold_receipt_ref,
        "publication_receipt_ref": evidence.publication_receipt_ref,
        "source_currentness_ref": evidence.source_currentness_ref,
    }, "hold authority")
    return _verified(evidence)


def verify_goal_phase_acceptance_authority_envelope(
    evidence: GoalPhaseAcceptanceAuthorityEnvelopeV1,
    exact_source_document: GoalPhaseNativeDocumentV1,
    committed_goal_resolver: Callable[[str, str], Mapping[str, object]],
) -> VerifiedGoalPhaseBootstrapEvidenceV1:
    evidence.__post_init__()
    exact_source_document.__post_init__()
    definitions = {item.coordinate: item for item in exact_source_document.definitions}
    definition = definitions.get(evidence.phase_coordinate)
    if definition is None or definition.definition_ref != evidence.definition_ref or definition.gate.gate_digest != evidence.gate_digest:
        raise GoalPhaseNativeOperationalBootstrapError("acceptance authority differs from source definition")
    _exact_mapping(committed_goal_resolver(evidence.repository_commit_ref, evidence.changed_authority_path), {
        "phase_publication_receipt_ref": evidence.phase_publication_receipt_ref,
        "accepted_phase_digest": evidence.accepted_phase_digest,
        "acceptance_ref": evidence.acceptance_ref,
        "source_currentness_ref": evidence.source_currentness_ref,
    }, "acceptance authority")
    return _verified(evidence)


def verify_goal_phase_temporal_authority_evidence(
    evidence: GoalPhaseTemporalAuthorityEvidenceV1,
    admitted_temporal_authority_resolver: Callable[[str], Mapping[str, object]],
) -> VerifiedGoalPhaseBootstrapEvidenceV1:
    evidence.__post_init__()
    _exact_mapping(admitted_temporal_authority_resolver(evidence.temporal_ledger_ref), {
        "temporal_publication_receipt_ref": evidence.temporal_publication_receipt_ref,
        "snapshot_authority_ref": evidence.snapshot_authority_ref,
        "source_repository_revision_ref": evidence.source_repository_revision_ref,
        "coverage_boundary_ref": evidence.coverage_boundary_ref,
        "currentness_ref": evidence.currentness_ref,
    }, "temporal authority")
    return _verified(evidence)


def verify_goal_coordinator_acceptance(
    acceptance: GoalPhaseBootstrapCoordinatorAcceptanceV1,
    acceptance_publication: GoalCoordinatorAcceptancePublicationV1,
    proposal: GoalPhaseNativeOperationalBootstrapProposalV1,
    coordinator_authority: GoalCoordinatorAuthorityV1,
    publication_issue_authority: GoalBootstrapPublicationIssueAuthorityV1,
    committed_goal_resolver: Callable[[str, str], Mapping[str, object]],
    coordinator_authority_resolver: Callable[[str, str], Mapping[str, object]],
    coordinator_acceptance_authority_resolver: Callable[[str, str], Mapping[str, object]],
    publication_issue_authority_resolver: Callable[[str, str], Mapping[str, object]],
    publication_head: str,
) -> VerifiedGoalCoordinatorAcceptanceV1:
    acceptance.__post_init__()
    acceptance_publication.__post_init__()
    proposal.__post_init__()
    coordinator_authority.__post_init__()
    publication_issue_authority.__post_init__()
    _git(publication_head, "publication_head")
    if (acceptance.proposal_aggregate_ref, acceptance.goal_tag, acceptance.source_document_ref, acceptance.source_goal_sha256, acceptance.source_repository_revision_ref) != (proposal.aggregate_ref, proposal.goal_tag, proposal.source_document_ref, proposal.source_goal_sha256, proposal.source_repository_revision_ref):
        raise GoalPhaseNativeOperationalBootstrapError("acceptance source differs from proposal")
    if acceptance.coordinator_authority_ref != coordinator_authority.authority_ref or acceptance.coordinator_execution_id != coordinator_authority.coordinator_execution_id:
        raise GoalPhaseNativeOperationalBootstrapError("coordinator identity lacks authority")
    if (
        acceptance_publication.proposal_aggregate_ref != proposal.aggregate_ref
        or acceptance_publication.coordinator_acceptance_ref != acceptance.receipt_ref
        or acceptance_publication.coordinator_execution_id
        != coordinator_authority.coordinator_execution_id
    ):
        raise GoalPhaseNativeOperationalBootstrapError(
            "coordinator acceptance lacks its exact publication authority"
        )
    if coordinator_authority.goal_tag != proposal.goal_tag or coordinator_authority.source_repository_revision_ref != proposal.source_repository_revision_ref or coordinator_authority.source_goal_sha256 != proposal.source_goal_sha256:
        raise GoalPhaseNativeOperationalBootstrapError("coordinator authority is for another source")
    goal_state = committed_goal_resolver(proposal.source_repository_revision_ref, publication_head)
    _exact_mapping(goal_state, {"goal_tag": proposal.goal_tag, "goal_sha256": proposal.source_goal_sha256, "lineage": "equal" if publication_head == proposal.source_repository_revision_ref else "descendant"}, "Goal currentness")
    authority_state = coordinator_authority_resolver(coordinator_authority.authority_ref, publication_head)
    _exact_mapping(authority_state, {
        "goal_tag": coordinator_authority.goal_tag,
        "goal_doc_path": coordinator_authority.goal_doc_path,
        "coordinator_execution_id": acceptance.coordinator_execution_id,
        "authority_source_ref": coordinator_authority.authority_source_ref,
        "authority_repository_path": coordinator_authority.authority_repository_path,
        "authority_repository_revision_ref": coordinator_authority.authority_repository_revision_ref,
        "authority_blob_oid": coordinator_authority.authority_blob_oid,
        "revocation_state": "clear",
        "currentness_ref": coordinator_authority.currentness_ref,
    }, "coordinator authority currentness")
    acceptance_authority_state = coordinator_acceptance_authority_resolver(
        acceptance_publication.receipt_ref, publication_head
    )
    _exact_mapping(
        acceptance_authority_state,
        {
            "proposal_aggregate_ref": proposal.aggregate_ref,
            "coordinator_acceptance_ref": acceptance.receipt_ref,
            "coordinator_execution_id": coordinator_authority.coordinator_execution_id,
            "acceptance_path": acceptance_publication.acceptance_path,
            "acceptance_commit_ref": acceptance_publication.acceptance_commit_ref,
            "acceptance_blob_oid": acceptance_publication.acceptance_blob_oid,
            "issuance_issue_ref": acceptance_publication.issuance_issue_ref,
            "issuance_issue_blob_oid": acceptance_publication.issuance_issue_blob_oid,
            "repository_commit_receipt_ref": acceptance_publication.repository_commit_receipt_ref,
        },
        "coordinator acceptance publication authority",
    )
    if publication_issue_authority.goal_doc_path != coordinator_authority.goal_doc_path:
        raise GoalPhaseNativeOperationalBootstrapError("publication Issue does not own Goal path")
    issue_state = publication_issue_authority_resolver(
        publication_issue_authority.issue_ref, publication_head
    )
    expected_issue_state = {
        "issue_ref": publication_issue_authority.issue_ref,
        "owner_execution_id": publication_issue_authority.owner_execution_id,
        "goal_doc_path": publication_issue_authority.goal_doc_path,
        "authority_repository_revision_ref": publication_issue_authority.repository_revision_ref,
        "observed_repository_revision_ref": publication_head,
        "issue_blob_oid": publication_issue_authority.issue_blob_oid,
        "scope_digest": publication_issue_authority.scope_digest,
        "status": publication_issue_authority.status,
    }
    _exact_mapping(issue_state, expected_issue_state, "publication Issue authority")
    issue_authority_digest = _digest(_canonical(expected_issue_state))
    value = object.__new__(VerifiedGoalCoordinatorAcceptanceV1)
    object.__setattr__(value, "acceptance_ref", acceptance.receipt_ref)
    object.__setattr__(value, "proposal_aggregate_ref", proposal.aggregate_ref)
    object.__setattr__(value, "publication_head", publication_head)
    object.__setattr__(value, "coordinator_authority_ref", coordinator_authority.authority_ref)
    object.__setattr__(
        value,
        "coordinator_acceptance_publication_ref",
        acceptance_publication.receipt_ref,
    )
    object.__setattr__(value, "publication_issue_ref", publication_issue_authority.issue_ref)
    object.__setattr__(value, "publication_issue_authority_digest", issue_authority_digest)
    object.__setattr__(value, "verification_ref", _content_ref("goal-phase-bootstrap-coordinator-verification", {"acceptance_ref": acceptance.receipt_ref, "acceptance_publication_ref": acceptance_publication.receipt_ref, "authority_ref": coordinator_authority.authority_ref, "issue_ref": publication_issue_authority.issue_ref, "issue_authority_digest": issue_authority_digest, "publication_head": publication_head}))
    object.__setattr__(
        value,
        "verifier_token",
        _register_verified(_verified_coordinator_body(value)),
    )
    return value


def _build_bootstrap_target(
    *,
    source_document: GoalPhaseNativeDocumentV1,
    proposal: GoalPhaseNativeOperationalBootstrapProposalV1,
    coordinator_acceptance: GoalPhaseBootstrapCoordinatorAcceptanceV1,
    verified_coordinator_acceptance: VerifiedGoalCoordinatorAcceptanceV1,
    verified_evidence: tuple[VerifiedGoalPhaseBootstrapEvidenceV1, ...],
) -> GoalPhaseNativeDocumentV2:

    source_document.__post_init__()
    proposal.__post_init__()
    coordinator_acceptance.__post_init__()
    _require_verified_coordinator(
        verified_coordinator_acceptance,
        acceptance=coordinator_acceptance,
        proposal=proposal,
    )
    for verified in verified_evidence:
        _require_verified_evidence(verified)

    if source_document.document_ref != proposal.source_document_ref or source_document.goal_tag != proposal.goal_tag:
        raise GoalPhaseNativeOperationalBootstrapError("proposal differs from source document")
    if verified_coordinator_acceptance.acceptance_ref != coordinator_acceptance.receipt_ref or verified_coordinator_acceptance.proposal_aggregate_ref != proposal.aggregate_ref:
        raise GoalPhaseNativeOperationalBootstrapError("coordinator acceptance is unverified")
    verified_by_key = {item.evidence_key: item for item in verified_evidence}
    if len(verified_by_key) != len(verified_evidence):
        raise GoalPhaseNativeOperationalBootstrapError("duplicate verified evidence")
    evidence_by_key = {item.evidence_key: item for item in proposal.evidence_bundle.all_items()}
    for key, evidence in evidence_by_key.items():
        verified = verified_by_key.get(key)
        if verified is None or verified.evidence_ref != evidence.evidence_ref or verified.phase_coordinate != evidence.phase_coordinate:
            raise GoalPhaseNativeOperationalBootstrapError("proposal evidence is not independently verified")
    if set(verified_by_key) != set(evidence_by_key):
        raise GoalPhaseNativeOperationalBootstrapError("unreferenced verified evidence")

    definitions = {item.coordinate: item for item in source_document.definitions}
    entries = {item.coordinate: item for item in proposal.entries}
    if set(definitions) != set(entries):
        raise GoalPhaseNativeOperationalBootstrapError("proposal must classify every definition exactly once")
    source_phases = {item.coordinate: item for item in source_document.operational_bundle.phases}
    desired: list[GoalLanePhase] = []
    current_issues: set[str] = set()
    for coordinate in sorted(definitions, key=_coordinate_sort):
        definition = definitions[coordinate]
        entry = entries[coordinate]
        if entry.definition_ref != definition.definition_ref or entry.gate_digest != definition.gate.gate_digest:
            raise GoalPhaseNativeOperationalBootstrapError("entry differs from definition or Gate")
        existing = source_phases.get(coordinate)
        if existing is not None:
            if entry.classification is not GoalPhaseBootstrapClassification.ALREADY_OPERATIONAL or entry.desired_phase != existing or entry.evidence_keys:
                raise GoalPhaseNativeOperationalBootstrapError("existing operational Phase must remain exactly already_operational")
            desired.append(existing)
            continue
        if entry.classification is GoalPhaseBootstrapClassification.ALREADY_OPERATIONAL:
            raise GoalPhaseNativeOperationalBootstrapError("already_operational Phase is absent")
        if entry.classification in {GoalPhaseBootstrapClassification.DEFINITION_ONLY_HISTORICAL, GoalPhaseBootstrapClassification.DEFINITION_ONLY_FUTURE}:
            if entry.evidence_keys:
                raise GoalPhaseNativeOperationalBootstrapError("definition-only classification cannot consume authority evidence")
            continue
        phase = entry.desired_phase
        assert phase is not None
        if (phase.title, phase.intent, phase.ordinal, phase.gate) != (definition.title, definition.intent, definition.ordinal, definition.gate):
            raise GoalPhaseNativeOperationalBootstrapError("desired Phase changes structural definition")
        cited = [evidence_by_key[key] for key in entry.evidence_keys]
        _validate_classification(entry.classification, phase, cited)
        for work in phase.work_associations:
            if work.disposition is GoalLanePhaseWorkDisposition.CURRENT:
                if work.issue_ref in current_issues:
                    raise GoalPhaseNativeOperationalBootstrapError("Issue is current in multiple Phases")
                current_issues.add(work.issue_ref)
        desired.append(phase)

    target_bundle = GoalPhaseContractBundleV1(
        phases=tuple(sorted(desired, key=lambda item: _coordinate_sort(item.coordinate))),
        dependencies=source_document.operational_bundle.dependencies,
    )
    execution = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile=proposal.requested_execution_authority_transition.source_execution_authority_profile,
        parity_ref=proposal.requested_execution_authority_transition.parity_ref,
        proposal_aggregate_ref=proposal.aggregate_ref,
        coordinator_acceptance_ref=coordinator_acceptance.receipt_ref,
    )
    target = GoalPhaseNativeDocumentV2(
        goal_tag=source_document.goal_tag,
        compatibility_projection_sha256=source_document.compatibility_projection_sha256,
        compatibility_projection_byte_count=source_document.compatibility_projection_byte_count,
        definitions=source_document.definitions,
        operational_bundle=target_bundle,
        unresolved_dependencies=source_document.unresolved_dependencies,
        source_refs=source_document.source_refs,
        execution_authority=execution,
    )
    return target


def plan_goal_phase_native_operational_bootstrap(
    *,
    source_document: GoalPhaseNativeDocumentV1,
    proposal: GoalPhaseNativeOperationalBootstrapProposalV1,
    coordinator_acceptance: GoalPhaseBootstrapCoordinatorAcceptanceV1,
    verified_coordinator_acceptance: VerifiedGoalCoordinatorAcceptanceV1,
    verified_evidence: tuple[VerifiedGoalPhaseBootstrapEvidenceV1, ...],
) -> GoalPhaseNativeOperationalBootstrapPlanV1:
    """Construct the exact V2 postimage without performing any effect."""

    target = _build_bootstrap_target(
        source_document=source_document,
        proposal=proposal,
        coordinator_acceptance=coordinator_acceptance,
        verified_coordinator_acceptance=verified_coordinator_acceptance,
        verified_evidence=verified_evidence,
    )
    return GoalPhaseNativeOperationalBootstrapPlanV1(
        source_document=source_document,
        proposal=proposal,
        coordinator_acceptance=coordinator_acceptance,
        verified_coordinator_acceptance=verified_coordinator_acceptance,
        verified_evidence=verified_evidence,
        target_document=target,
    )


def encode_goal_phase_native_operational_bootstrap_proposal(value: GoalPhaseNativeOperationalBootstrapProposalV1) -> bytes:
    value.__post_init__()
    return _canonical({**_proposal_body(value), "aggregate_ref": value.aggregate_ref})


def decode_goal_phase_native_operational_bootstrap_proposal(payload: bytes) -> GoalPhaseNativeOperationalBootstrapProposalV1:
    values = _decode_object(payload, "proposal")
    _fields(values, {"schema_id", "goal_tag", "source_document_ref", "source_goal_sha256", "source_repository_revision_ref", "requested_execution_authority_transition", "evidence_bundle", "entries", "aggregate_ref"}, "proposal")
    proposal = GoalPhaseNativeOperationalBootstrapProposalV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        source_document_ref=_text(values["source_document_ref"], "source_document_ref"),
        source_goal_sha256=_text(values["source_goal_sha256"], "source_goal_sha256"),
        source_repository_revision_ref=_text(values["source_repository_revision_ref"], "source_repository_revision_ref"),
        requested_execution_authority_transition=_decode_transition(values["requested_execution_authority_transition"]),
        evidence_bundle=_decode_evidence_bundle(values["evidence_bundle"]),
        entries=tuple(_decode_entry(item) for item in _array(values["entries"], "entries")),
    )
    if _text(values["aggregate_ref"], "aggregate_ref") != proposal.aggregate_ref or not _exact_json_equal({**_proposal_body(proposal), "aggregate_ref": proposal.aggregate_ref}, values):
        raise GoalPhaseNativeOperationalBootstrapError("proposal aggregate or canonical form differs")
    return proposal


def encode_goal_phase_bootstrap_coordinator_acceptance(value: GoalPhaseBootstrapCoordinatorAcceptanceV1) -> bytes:
    value.__post_init__()
    return _canonical({**_coordinator_acceptance_body(value), "receipt_ref": value.receipt_ref})


def decode_goal_phase_bootstrap_coordinator_acceptance(payload: bytes) -> GoalPhaseBootstrapCoordinatorAcceptanceV1:
    values = _decode_object(payload, "coordinator acceptance")
    _fields(values, {"schema_id", "proposal_aggregate_ref", "goal_tag", "source_document_ref", "source_goal_sha256", "source_repository_revision_ref", "coordinator_execution_id", "coordinator_authority_ref", "decision", "accepted_at", "evidence_refs", "receipt_ref"}, "coordinator acceptance")
    acceptance = GoalPhaseBootstrapCoordinatorAcceptanceV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        proposal_aggregate_ref=_text(values["proposal_aggregate_ref"], "proposal_aggregate_ref"),
        goal_tag=_text(values["goal_tag"], "goal_tag"),
        source_document_ref=_text(values["source_document_ref"], "source_document_ref"),
        source_goal_sha256=_text(values["source_goal_sha256"], "source_goal_sha256"),
        source_repository_revision_ref=_text(values["source_repository_revision_ref"], "source_repository_revision_ref"),
        coordinator_execution_id=_text(values["coordinator_execution_id"], "coordinator_execution_id"),
        coordinator_authority_ref=_text(values["coordinator_authority_ref"], "coordinator_authority_ref"),
        decision=_text(values["decision"], "decision"),
        accepted_at=_text(values["accepted_at"], "accepted_at"),
        evidence_refs=_strings(values["evidence_refs"], "evidence_refs"),
    )
    if _text(values["receipt_ref"], "receipt_ref") != acceptance.receipt_ref or not _exact_json_equal({**_coordinator_acceptance_body(acceptance), "receipt_ref": acceptance.receipt_ref}, values):
        raise GoalPhaseNativeOperationalBootstrapError("coordinator acceptance is not canonical")
    return acceptance


def encode_goal_coordinator_authority(value: GoalCoordinatorAuthorityV1) -> bytes:
    value.__post_init__()
    return _canonical({**_coordinator_authority_body(value), "authority_ref": value.authority_ref})


def decode_goal_coordinator_authority(payload: bytes) -> GoalCoordinatorAuthorityV1:
    values = _decode_object(payload, "coordinator authority")
    _fields(values, {"schema_id", "goal_tag", "goal_doc_path", "authority_profile", "coordinator_execution_id", "source_repository_revision_ref", "source_goal_sha256", "source_goal_blob_oid", "authority_source_ref", "authority_repository_path", "authority_repository_revision_ref", "authority_blob_oid", "revocation_state", "currentness_ref", "authority_ref"}, "coordinator authority")
    authority = GoalCoordinatorAuthorityV1(**{key: _text(values[key], key) for key in values if key != "authority_ref"})
    if _text(values["authority_ref"], "authority_ref") != authority.authority_ref or not _exact_json_equal({**_coordinator_authority_body(authority), "authority_ref": authority.authority_ref}, values):
        raise GoalPhaseNativeOperationalBootstrapError("coordinator authority is not canonical")
    return authority


def encode_goal_owner_coordinator_authority_publication(
    value: GoalOwnerCoordinatorAuthorityPublicationV1,
) -> bytes:
    value.__post_init__()
    return _canonical(
        {**_goal_owner_authority_publication_body(value), "receipt_ref": value.receipt_ref}
    )


def decode_goal_owner_coordinator_authority_publication(
    payload: bytes,
) -> GoalOwnerCoordinatorAuthorityPublicationV1:
    values = _decode_object(payload, "Goal-owner authority publication")
    fields = {
        "schema_id", "goal_tag", "goal_doc_path", "goal_owner_execution_id",
        "coordinator_execution_id", "coordinator_authority_ref",
        "authority_source_ref",
        "authority_declaration_path", "authority_declaration_commit_ref",
        "authority_declaration_blob_oid", "issuance_issue_ref",
        "issuance_issue_blob_oid", "repository_commit_receipt_ref",
        "published_at", "receipt_ref",
    }
    _fields(values, fields, "Goal-owner authority publication")
    publication = GoalOwnerCoordinatorAuthorityPublicationV1(
        **{
            key: _text(values[key], key)
            for key in fields
            if key != "receipt_ref"
        }
    )
    canonical = {
        **_goal_owner_authority_publication_body(publication),
        "receipt_ref": publication.receipt_ref,
    }
    if (
        _text(values["receipt_ref"], "receipt_ref") != publication.receipt_ref
        or not _exact_json_equal(canonical, values)
    ):
        raise GoalPhaseNativeOperationalBootstrapError(
            "Goal-owner authority publication is not canonical"
        )
    return publication


def encode_goal_coordinator_acceptance_publication(
    value: GoalCoordinatorAcceptancePublicationV1,
) -> bytes:
    value.__post_init__()
    return _canonical(
        {
            **_coordinator_acceptance_publication_body(value),
            "receipt_ref": value.receipt_ref,
        }
    )


def decode_goal_coordinator_acceptance_publication(
    payload: bytes,
) -> GoalCoordinatorAcceptancePublicationV1:
    values = _decode_object(payload, "coordinator acceptance publication")
    fields = {
        "schema_id", "proposal_aggregate_ref", "coordinator_acceptance_ref",
        "coordinator_execution_id", "acceptance_path", "acceptance_commit_ref",
        "acceptance_blob_oid", "issuance_issue_ref", "issuance_issue_blob_oid",
        "repository_commit_receipt_ref", "published_at", "receipt_ref",
    }
    _fields(values, fields, "coordinator acceptance publication")
    publication = GoalCoordinatorAcceptancePublicationV1(
        **{
            key: _text(values[key], key)
            for key in fields
            if key != "receipt_ref"
        }
    )
    canonical = {
        **_coordinator_acceptance_publication_body(publication),
        "receipt_ref": publication.receipt_ref,
    }
    if (
        _text(values["receipt_ref"], "receipt_ref") != publication.receipt_ref
        or not _exact_json_equal(canonical, values)
    ):
        raise GoalPhaseNativeOperationalBootstrapError(
            "coordinator acceptance publication is not canonical"
        )
    return publication


def _validate_classification(classification: GoalPhaseBootstrapClassification, phase: GoalLanePhase, evidence: list[Evidence]) -> None:
    issues = [item for item in evidence if type(item) is CommittedIssueAuthorityEvidenceV1]
    holds = [item for item in evidence if type(item) is GoalPhaseHoldAuthorityEvidenceV1]
    acceptances = [item for item in evidence if type(item) is GoalPhaseAcceptanceAuthorityEnvelopeV1]
    if any(item.phase_coordinate != phase.coordinate for item in evidence):
        raise GoalPhaseNativeOperationalBootstrapError("cross-Phase evidence")
    if classification is GoalPhaseBootstrapClassification.OPERATIONAL_ACTIVE:
        if phase.state is not GoalLanePhaseState.ACTIVE or len(issues) != 1 or holds or acceptances:
            raise GoalPhaseNativeOperationalBootstrapError("active classification lacks exact Issue authority")
    elif classification is GoalPhaseBootstrapClassification.OPERATIONAL_HELD:
        if phase.state is not GoalLanePhaseState.HELD or len(issues) != 1 or len(holds) != 1 or acceptances:
            raise GoalPhaseNativeOperationalBootstrapError("held classification lacks exact hold authority")
    elif classification is GoalPhaseBootstrapClassification.OPERATIONAL_ACCEPTED:
        if phase.state is not GoalLanePhaseState.ACCEPTED or issues or holds or len(acceptances) != 1 or acceptances[0].accepted_phase != phase:
            raise GoalPhaseNativeOperationalBootstrapError("accepted classification lacks publication-qualified acceptance")
    else:
        raise GoalPhaseNativeOperationalBootstrapError("unexpected operational classification")
    if classification in {GoalPhaseBootstrapClassification.OPERATIONAL_ACTIVE, GoalPhaseBootstrapClassification.OPERATIONAL_HELD}:
        issue = issues[0]
        current = tuple(item for item in phase.work_associations if item.disposition is GoalLanePhaseWorkDisposition.CURRENT)
        if (
            len(current) != 1
            or len(phase.work_associations) != 1
            or phase.gate_observations
            or phase.pursuit_directive is not None
        ):
            raise GoalPhaseNativeOperationalBootstrapError(
                "active or held Phase may contain only its verified current Work"
            )
        work = current[0]
        body = {"coordinate": _coordinate_wire(phase.coordinate), "issue_ref": issue.issue_ref, "role": issue.work_role, "admitted_at": issue.authority_admitted_at, "evidence_refs": [issue.evidence_ref]}
        association_ref = "goal-phase-work:" + fingerprint(body)
        receipt_ref = "goal-phase-work-admission:" + fingerprint({**body, "association_ref": association_ref})
        expected_last_receipt = receipt_ref if classification is GoalPhaseBootstrapClassification.OPERATIONAL_ACTIVE else holds[0].hold_receipt_ref
        if (
            work.retired_at is not None
            or (work.issue_ref, work.role.value, work.admitted_at, work.association_ref, work.receipt_ref)
            != (issue.issue_ref, issue.work_role, issue.authority_admitted_at, association_ref, receipt_ref)
            or phase.last_receipt_ref != expected_last_receipt
        ):
            raise GoalPhaseNativeOperationalBootstrapError("current Work is not canonically derived from Issue authority")


def _verified(evidence: Evidence) -> VerifiedGoalPhaseBootstrapEvidenceV1:
    value = object.__new__(VerifiedGoalPhaseBootstrapEvidenceV1)
    object.__setattr__(value, "evidence_ref", evidence.evidence_ref)
    object.__setattr__(value, "evidence_key", evidence.evidence_key)
    object.__setattr__(value, "phase_coordinate", evidence.phase_coordinate)
    object.__setattr__(value, "verification_ref", _content_ref("goal-phase-bootstrap-evidence-verification", {"evidence_ref": evidence.evidence_ref}))
    object.__setattr__(
        value,
        "verifier_token",
        _register_verified(_verified_evidence_body(value)),
    )
    return value


def _require_verified_evidence(value: VerifiedGoalPhaseBootstrapEvidenceV1) -> None:
    if type(value) is not VerifiedGoalPhaseBootstrapEvidenceV1 or not hasattr(value, "verifier_token"):
        raise GoalPhaseNativeOperationalBootstrapError("evidence verifier output is not sealed")
    expected = _content_ref(
        "goal-phase-bootstrap-evidence-verification",
        {"evidence_ref": value.evidence_ref},
    )
    if value.verification_ref != expected:
        raise GoalPhaseNativeOperationalBootstrapError("evidence verification reference differs")
    _require_registered(
        value.verifier_token,
        _verified_evidence_body(value),
        "evidence",
    )


def _require_verified_coordinator(
    value: VerifiedGoalCoordinatorAcceptanceV1,
    *,
    acceptance: GoalPhaseBootstrapCoordinatorAcceptanceV1,
    proposal: GoalPhaseNativeOperationalBootstrapProposalV1,
) -> None:
    if type(value) is not VerifiedGoalCoordinatorAcceptanceV1 or not hasattr(value, "verifier_token"):
        raise GoalPhaseNativeOperationalBootstrapError("coordinator verifier output is not sealed")
    if value.acceptance_ref != acceptance.receipt_ref or value.proposal_aggregate_ref != proposal.aggregate_ref:
        raise GoalPhaseNativeOperationalBootstrapError("coordinator verifier output differs")
    expected = _content_ref(
        "goal-phase-bootstrap-coordinator-verification",
        {
            "acceptance_ref": value.acceptance_ref,
            "acceptance_publication_ref": value.coordinator_acceptance_publication_ref,
            "authority_ref": value.coordinator_authority_ref,
            "issue_ref": value.publication_issue_ref,
            "issue_authority_digest": value.publication_issue_authority_digest,
            "publication_head": value.publication_head,
        },
    )
    if value.verification_ref != expected:
        raise GoalPhaseNativeOperationalBootstrapError("coordinator verification reference differs")
    _require_registered(
        value.verifier_token,
        _verified_coordinator_body(value),
        "coordinator",
    )


def _verified_evidence_body(
    value: VerifiedGoalPhaseBootstrapEvidenceV1,
) -> dict[str, object]:
    return {
        "evidence_ref": value.evidence_ref,
        "evidence_key": value.evidence_key,
        "phase_coordinate": _coordinate_wire(value.phase_coordinate),
        "verification_ref": value.verification_ref,
    }


def _verified_coordinator_body(
    value: VerifiedGoalCoordinatorAcceptanceV1,
) -> dict[str, object]:
    return {
        "acceptance_ref": value.acceptance_ref,
        "proposal_aggregate_ref": value.proposal_aggregate_ref,
        "publication_head": value.publication_head,
        "coordinator_authority_ref": value.coordinator_authority_ref,
        "coordinator_acceptance_publication_ref": value.coordinator_acceptance_publication_ref,
        "publication_issue_ref": value.publication_issue_ref,
        "publication_issue_authority_digest": value.publication_issue_authority_digest,
        "verification_ref": value.verification_ref,
    }


def _proposal_body(value: GoalPhaseNativeOperationalBootstrapProposalV1) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "goal_tag": value.goal_tag,
        "source_document_ref": value.source_document_ref,
        "source_goal_sha256": value.source_goal_sha256,
        "source_repository_revision_ref": value.source_repository_revision_ref,
        "requested_execution_authority_transition": _transition_wire(value.requested_execution_authority_transition),
        "evidence_bundle": _evidence_bundle_wire(value.evidence_bundle),
        "entries": [_entry_wire(item) for item in value.entries],
    }


def _plan_body(value: GoalPhaseNativeOperationalBootstrapPlanV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "source_document_ref": value.source_document_ref, "target_document_ref": value.target_document.document_ref, "proposal_aggregate_ref": value.proposal_aggregate_ref, "coordinator_acceptance_ref": value.coordinator_acceptance_ref}


def _publication_receipt_body(value: GoalPhaseNativeOperationalBootstrapPublicationReceiptV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "semantic_intent_ref": value.semantic_intent_ref, "source_document_ref": value.source_document_ref, "target_document_ref": value.target_document_ref, "execution_authority_ref": value.execution_authority_ref, "proposal_aggregate_ref": value.proposal_aggregate_ref, "coordinator_acceptance_ref": value.coordinator_acceptance_ref, "repository_commit_ref": value.repository_commit_ref, "repository_commit_receipt_ref": value.repository_commit_receipt_ref, "changed_path": value.changed_path}


def _bootstrap_currentness_body(value: GoalPhaseNativeOperationalBootstrapCurrentnessV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "publication_receipt_ref": value.publication_receipt_ref, "publication_revision_ref": value.publication_revision_ref, "observed_revision_ref": value.observed_revision_ref, "status": value.status, "projection_currentness": value.projection_currentness, "replay_disposition": value.replay_disposition, "reasons": list(value.reasons)}


def _repository_evidence_verification_body(
    value: GoalPhaseBootstrapRepositoryEvidenceV1,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "publication_revision_ref": value.publication_revision_ref,
        "observed_revision_ref": value.observed_revision_ref,
        "lineage": value.lineage,
        "protected_paths": list(value.protected_paths),
        "changed_paths": list(value.changed_paths),
        "evidence_ref": value.evidence_ref,
    }


def _transition_wire(value: GoalPhaseExecutionAuthorityTransitionV1) -> dict[str, object]:
    return {"source_execution_authority_profile": value.source_execution_authority_profile, "target_execution_authority_profile": value.target_execution_authority_profile, "legacy_execution_disposition": value.legacy_execution_disposition, "parity_ref": value.parity_ref}


def _entry_wire(value: GoalPhaseBootstrapEntryV1) -> dict[str, object]:
    return {"coordinate": _coordinate_wire(value.coordinate), "definition_ref": value.definition_ref, "gate_digest": value.gate_digest, "classification": value.classification.value, "evidence_keys": list(value.evidence_keys), "desired_phase": None if value.desired_phase is None else _phase_wire(value.desired_phase)}


def _evidence_bundle_wire(value: GoalPhaseBootstrapEvidenceBundleV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "issue_authorities": [_issue_wire(item) for item in value.issue_authorities], "hold_authorities": [_hold_wire(item) for item in value.hold_authorities], "acceptance_authorities": [_acceptance_authority_wire(item) for item in value.acceptance_authorities], "temporal_authorities": [_temporal_wire(item) for item in value.temporal_authorities]}


def _issue_body(value: CommittedIssueAuthorityEvidenceV1) -> dict[str, object]:
    return {"evidence_key": value.evidence_key, "phase_coordinate": _coordinate_wire(value.phase_coordinate), "issue_ref": value.issue_ref, "repository_revision_ref": value.repository_revision_ref, "issue_blob_oid": value.issue_blob_oid, "expected_status": value.expected_status, "expected_owner_execution_id": value.expected_owner_execution_id, "expected_scope_digest": value.expected_scope_digest, "phase_association_ref": value.phase_association_ref, "work_role": value.work_role, "authority_admitted_at": value.authority_admitted_at}


def _issue_wire(value: CommittedIssueAuthorityEvidenceV1) -> dict[str, object]:
    return {**_issue_body(value), "evidence_ref": value.evidence_ref}


def _hold_body(value: GoalPhaseHoldAuthorityEvidenceV1) -> dict[str, object]:
    return {"evidence_key": value.evidence_key, "phase_coordinate": _coordinate_wire(value.phase_coordinate), "current_issue_evidence_key": value.current_issue_evidence_key, "hold_receipt_ref": value.hold_receipt_ref, "publication_receipt_ref": value.publication_receipt_ref, "repository_commit_ref": value.repository_commit_ref, "source_currentness_ref": value.source_currentness_ref}


def _hold_wire(value: GoalPhaseHoldAuthorityEvidenceV1) -> dict[str, object]:
    return {**_hold_body(value), "evidence_ref": value.evidence_ref}


def _acceptance_authority_body(value: GoalPhaseAcceptanceAuthorityEnvelopeV1) -> dict[str, object]:
    return {"evidence_key": value.evidence_key, "phase_coordinate": _coordinate_wire(value.phase_coordinate), "definition_ref": value.definition_ref, "gate_digest": value.gate_digest, "acceptance_ref": value.acceptance_ref, "accepted_phase": _phase_wire(value.accepted_phase), "accepted_phase_digest": value.accepted_phase_digest, "phase_publication_receipt_ref": value.phase_publication_receipt_ref, "repository_commit_ref": value.repository_commit_ref, "changed_authority_path": value.changed_authority_path, "source_currentness_ref": value.source_currentness_ref}


def _acceptance_authority_wire(value: GoalPhaseAcceptanceAuthorityEnvelopeV1) -> dict[str, object]:
    return {**_acceptance_authority_body(value), "evidence_ref": value.evidence_ref}


def _temporal_body(value: GoalPhaseTemporalAuthorityEvidenceV1) -> dict[str, object]:
    return {"evidence_key": value.evidence_key, "phase_coordinate": _coordinate_wire(value.phase_coordinate), "temporal_ledger_ref": value.temporal_ledger_ref, "temporal_publication_receipt_ref": value.temporal_publication_receipt_ref, "snapshot_authority_ref": value.snapshot_authority_ref, "source_repository_revision_ref": value.source_repository_revision_ref, "coverage_boundary_ref": value.coverage_boundary_ref, "currentness_ref": value.currentness_ref}


def _temporal_wire(value: GoalPhaseTemporalAuthorityEvidenceV1) -> dict[str, object]:
    return {**_temporal_body(value), "evidence_ref": value.evidence_ref}


def _coordinator_authority_body(value: GoalCoordinatorAuthorityV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "goal_tag": value.goal_tag, "goal_doc_path": value.goal_doc_path, "authority_profile": value.authority_profile, "coordinator_execution_id": value.coordinator_execution_id, "source_repository_revision_ref": value.source_repository_revision_ref, "source_goal_sha256": value.source_goal_sha256, "source_goal_blob_oid": value.source_goal_blob_oid, "authority_source_ref": value.authority_source_ref, "authority_repository_path": value.authority_repository_path, "authority_repository_revision_ref": value.authority_repository_revision_ref, "authority_blob_oid": value.authority_blob_oid, "revocation_state": value.revocation_state, "currentness_ref": value.currentness_ref}


def _goal_owner_authority_publication_body(
    value: GoalOwnerCoordinatorAuthorityPublicationV1,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "goal_tag": value.goal_tag,
        "goal_doc_path": value.goal_doc_path,
        "goal_owner_execution_id": value.goal_owner_execution_id,
        "coordinator_execution_id": value.coordinator_execution_id,
        "coordinator_authority_ref": value.coordinator_authority_ref,
        "authority_source_ref": value.authority_source_ref,
        "authority_declaration_path": value.authority_declaration_path,
        "authority_declaration_commit_ref": value.authority_declaration_commit_ref,
        "authority_declaration_blob_oid": value.authority_declaration_blob_oid,
        "issuance_issue_ref": value.issuance_issue_ref,
        "issuance_issue_blob_oid": value.issuance_issue_blob_oid,
        "repository_commit_receipt_ref": value.repository_commit_receipt_ref,
        "published_at": value.published_at,
    }


def _coordinator_acceptance_publication_body(
    value: GoalCoordinatorAcceptancePublicationV1,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "proposal_aggregate_ref": value.proposal_aggregate_ref,
        "coordinator_acceptance_ref": value.coordinator_acceptance_ref,
        "coordinator_execution_id": value.coordinator_execution_id,
        "acceptance_path": value.acceptance_path,
        "acceptance_commit_ref": value.acceptance_commit_ref,
        "acceptance_blob_oid": value.acceptance_blob_oid,
        "issuance_issue_ref": value.issuance_issue_ref,
        "issuance_issue_blob_oid": value.issuance_issue_blob_oid,
        "repository_commit_receipt_ref": value.repository_commit_receipt_ref,
        "published_at": value.published_at,
    }


def _coordinator_acceptance_body(value: GoalPhaseBootstrapCoordinatorAcceptanceV1) -> dict[str, object]:
    return {"schema_id": value.schema_id, "proposal_aggregate_ref": value.proposal_aggregate_ref, "goal_tag": value.goal_tag, "source_document_ref": value.source_document_ref, "source_goal_sha256": value.source_goal_sha256, "source_repository_revision_ref": value.source_repository_revision_ref, "coordinator_execution_id": value.coordinator_execution_id, "coordinator_authority_ref": value.coordinator_authority_ref, "decision": value.decision, "accepted_at": value.accepted_at, "evidence_refs": list(value.evidence_refs)}


def _decode_transition(raw: object) -> GoalPhaseExecutionAuthorityTransitionV1:
    values = _mapping(raw, "execution authority transition")
    _fields(values, {"source_execution_authority_profile", "target_execution_authority_profile", "legacy_execution_disposition", "parity_ref"}, "execution authority transition")
    return GoalPhaseExecutionAuthorityTransitionV1(**{key: _text(value, key) for key, value in values.items()})


def _decode_entry(raw: object) -> GoalPhaseBootstrapEntryV1:
    values = _mapping(raw, "entry")
    _fields(values, {"coordinate", "definition_ref", "gate_digest", "classification", "evidence_keys", "desired_phase"}, "entry")
    desired_raw = values["desired_phase"]
    desired = None if desired_raw is None else _decode_phase(desired_raw)
    return GoalPhaseBootstrapEntryV1(coordinate=_decode_coordinate(values["coordinate"]), definition_ref=_text(values["definition_ref"], "definition_ref"), gate_digest=_text(values["gate_digest"], "gate_digest"), classification=GoalPhaseBootstrapClassification(_text(values["classification"], "classification")), evidence_keys=_strings(values["evidence_keys"], "evidence_keys"), desired_phase=desired)


def _decode_evidence_bundle(raw: object) -> GoalPhaseBootstrapEvidenceBundleV1:
    values = _mapping(raw, "evidence bundle")
    _fields(values, {"schema_id", "issue_authorities", "hold_authorities", "acceptance_authorities", "temporal_authorities"}, "evidence bundle")
    return GoalPhaseBootstrapEvidenceBundleV1(
        schema_id=_text(values["schema_id"], "schema_id"),
        issue_authorities=tuple(_decode_issue(item) for item in _array(values["issue_authorities"], "issue_authorities")),
        hold_authorities=tuple(_decode_hold(item) for item in _array(values["hold_authorities"], "hold_authorities")),
        acceptance_authorities=tuple(_decode_acceptance_authority(item) for item in _array(values["acceptance_authorities"], "acceptance_authorities")),
        temporal_authorities=tuple(_decode_temporal(item) for item in _array(values["temporal_authorities"], "temporal_authorities")),
    )


def _decode_issue(raw: object) -> CommittedIssueAuthorityEvidenceV1:
    values = _mapping(raw, "Issue authority")
    _fields(values, set(_issue_body_keys()) | {"evidence_ref"}, "Issue authority")
    value = CommittedIssueAuthorityEvidenceV1(
        evidence_key=_text(values["evidence_key"], "evidence_key"), phase_coordinate=_decode_coordinate(values["phase_coordinate"]), issue_ref=_text(values["issue_ref"], "issue_ref"), repository_revision_ref=_text(values["repository_revision_ref"], "repository_revision_ref"), issue_blob_oid=_text(values["issue_blob_oid"], "issue_blob_oid"), expected_status=_text(values["expected_status"], "expected_status"), expected_owner_execution_id=_text(values["expected_owner_execution_id"], "expected_owner_execution_id"), expected_scope_digest=_text(values["expected_scope_digest"], "expected_scope_digest"), phase_association_ref=_text(values["phase_association_ref"], "phase_association_ref"), work_role=_text(values["work_role"], "work_role"), authority_admitted_at=_text(values["authority_admitted_at"], "authority_admitted_at"),
    )
    _check_ref(values, value.evidence_ref)
    return value


def _decode_hold(raw: object) -> GoalPhaseHoldAuthorityEvidenceV1:
    values = _mapping(raw, "hold authority")
    _fields(values, set(_hold_body_keys()) | {"evidence_ref"}, "hold authority")
    value = GoalPhaseHoldAuthorityEvidenceV1(evidence_key=_text(values["evidence_key"], "evidence_key"), phase_coordinate=_decode_coordinate(values["phase_coordinate"]), current_issue_evidence_key=_text(values["current_issue_evidence_key"], "current_issue_evidence_key"), hold_receipt_ref=_text(values["hold_receipt_ref"], "hold_receipt_ref"), publication_receipt_ref=_text(values["publication_receipt_ref"], "publication_receipt_ref"), repository_commit_ref=_text(values["repository_commit_ref"], "repository_commit_ref"), source_currentness_ref=_text(values["source_currentness_ref"], "source_currentness_ref"))
    _check_ref(values, value.evidence_ref)
    return value


def _decode_acceptance_authority(raw: object) -> GoalPhaseAcceptanceAuthorityEnvelopeV1:
    values = _mapping(raw, "acceptance authority")
    _fields(values, set(_acceptance_body_keys()) | {"evidence_ref"}, "acceptance authority")
    value = GoalPhaseAcceptanceAuthorityEnvelopeV1(evidence_key=_text(values["evidence_key"], "evidence_key"), phase_coordinate=_decode_coordinate(values["phase_coordinate"]), definition_ref=_text(values["definition_ref"], "definition_ref"), gate_digest=_text(values["gate_digest"], "gate_digest"), acceptance_ref=_text(values["acceptance_ref"], "acceptance_ref"), accepted_phase=_decode_phase(values["accepted_phase"]), phase_publication_receipt_ref=_text(values["phase_publication_receipt_ref"], "phase_publication_receipt_ref"), repository_commit_ref=_text(values["repository_commit_ref"], "repository_commit_ref"), changed_authority_path=_text(values["changed_authority_path"], "changed_authority_path"), source_currentness_ref=_text(values["source_currentness_ref"], "source_currentness_ref"))
    if _text(values["accepted_phase_digest"], "accepted_phase_digest") != value.accepted_phase_digest:
        raise GoalPhaseNativeOperationalBootstrapError("accepted Phase digest mismatch")
    _check_ref(values, value.evidence_ref)
    return value


def _decode_temporal(raw: object) -> GoalPhaseTemporalAuthorityEvidenceV1:
    values = _mapping(raw, "temporal authority")
    _fields(values, set(_temporal_body_keys()) | {"evidence_ref"}, "temporal authority")
    value = GoalPhaseTemporalAuthorityEvidenceV1(evidence_key=_text(values["evidence_key"], "evidence_key"), phase_coordinate=_decode_coordinate(values["phase_coordinate"]), temporal_ledger_ref=_text(values["temporal_ledger_ref"], "temporal_ledger_ref"), temporal_publication_receipt_ref=_text(values["temporal_publication_receipt_ref"], "temporal_publication_receipt_ref"), snapshot_authority_ref=_text(values["snapshot_authority_ref"], "snapshot_authority_ref"), source_repository_revision_ref=_text(values["source_repository_revision_ref"], "source_repository_revision_ref"), coverage_boundary_ref=_text(values["coverage_boundary_ref"], "coverage_boundary_ref"), currentness_ref=_text(values["currentness_ref"], "currentness_ref"))
    _check_ref(values, value.evidence_ref)
    return value


def _phase_wire(value: GoalLanePhase) -> dict[str, object]:
    wire = goal_phase_bundle_to_wire(GoalPhaseContractBundleV1(phases=(value,), dependencies=()))
    phases = cast(list[object], wire["phases"])
    return cast(dict[str, object], phases[0])


def _decode_phase(raw: object) -> GoalLanePhase:
    bundle = decode_goal_phase_bundle(_canonical({"schema_id": "aware.goal.lane-phase.bundle.v1", "phases": [raw], "dependencies": []}))
    if len(bundle.phases) != 1:
        raise GoalPhaseNativeOperationalBootstrapError("desired_phase is invalid")
    return bundle.phases[0]


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, object]:
    return {"goal_tag": value.goal_tag, "lane_key": value.lane_key, "phase_key": value.phase_key}


def _decode_coordinate(raw: object) -> GoalPhaseCoordinate:
    values = _mapping(raw, "coordinate")
    _fields(values, {"goal_tag", "lane_key", "phase_key"}, "coordinate")
    return GoalPhaseCoordinate(goal_tag=_text(values["goal_tag"], "goal_tag"), lane_key=_text(values["lane_key"], "lane_key"), phase_key=_text(values["phase_key"], "phase_key"))


def _coordinate_sort(value: GoalPhaseCoordinate) -> tuple[str, str, str]:
    return value.goal_tag, value.lane_key, value.phase_key


def _evidence_common(key: object, coordinate: object) -> None:
    _key(key, "evidence_key")
    if type(coordinate) is not GoalPhaseCoordinate:
        raise TypeError("phase_coordinate must be GoalPhaseCoordinate")


def _issue_body_keys() -> tuple[str, ...]:
    return tuple(_issue_body.__annotations__) if False else ("evidence_key", "phase_coordinate", "issue_ref", "repository_revision_ref", "issue_blob_oid", "expected_status", "expected_owner_execution_id", "expected_scope_digest", "phase_association_ref", "work_role", "authority_admitted_at")


def _hold_body_keys() -> tuple[str, ...]:
    return ("evidence_key", "phase_coordinate", "current_issue_evidence_key", "hold_receipt_ref", "publication_receipt_ref", "repository_commit_ref", "source_currentness_ref")


def _acceptance_body_keys() -> tuple[str, ...]:
    return ("evidence_key", "phase_coordinate", "definition_ref", "gate_digest", "acceptance_ref", "accepted_phase", "accepted_phase_digest", "phase_publication_receipt_ref", "repository_commit_ref", "changed_authority_path", "source_currentness_ref")


def _temporal_body_keys() -> tuple[str, ...]:
    return ("evidence_key", "phase_coordinate", "temporal_ledger_ref", "temporal_publication_receipt_ref", "snapshot_authority_ref", "source_repository_revision_ref", "coverage_boundary_ref", "currentness_ref")


def _check_ref(values: Mapping[str, object], expected: str) -> None:
    if _text(values["evidence_ref"], "evidence_ref") != expected:
        raise GoalPhaseNativeOperationalBootstrapError("evidence_ref mismatch")


def _decode_object(payload: bytes, name: str) -> Mapping[str, object]:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = cast(object, json.loads(payload.decode("utf-8"), object_pairs_hook=_unique))
        return _mapping(raw, name)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} is not JSON") from error


def _unique(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise GoalPhaseNativeOperationalBootstrapError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be object")
    return cast(dict[str, object], value)


def _fields(value: Mapping[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} fields are not canonical")


def _array(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be array")
    return cast(list[object], value)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be canonical text")
    return value


def _key(value: object, name: str) -> str:
    result = _text(value, name)
    if not _KEY.fullmatch(result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be kebab-case")
    return result


def _sha(value: object, name: str) -> str:
    result = _text(value, name)
    if not _SHA.fullmatch(result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be SHA-256")
    return result


def _git(value: object, name: str) -> str:
    result = _text(value, name)
    if not _GIT.fullmatch(result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be 40- or 64-hex Git identity")
    return result


def _utc(value: object, name: str) -> str:
    result = _text(value, name)
    if not _UTC.fullmatch(result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be UTC RFC3339")
    return result


def _qualified(value: object, name: str) -> str:
    result = _text(value, name)
    if not re.fullmatch(r"[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*:sha256:[0-9a-f]{64}", result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be qualified digest")
    return result


def _ref(value: object, name: str, prefix: str) -> str:
    result = _text(value, name)
    if not re.fullmatch(re.escape(prefix) + r":sha256:[0-9a-f]{64}", result):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} has invalid domain")
    return result


def _tokens(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be exact tuple")
    result = tuple(_text(item, name) for item in cast(tuple[object, ...], value))
    if result != tuple(sorted(set(result))):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} must be sorted and unique")
    return result


def _keys_tuple(value: object, name: str) -> tuple[str, ...]:
    result = _tokens(value, name)
    for item in result:
        _key(item, name)
    return result


def _strings(value: object, name: str) -> tuple[str, ...]:
    return _tokens(tuple(_text(item, name) for item in _array(value, name)), name)


def _exact_mapping(actual: Mapping[str, object], expected: Mapping[str, object], name: str) -> None:
    if not _exact_json_equal(dict(actual), dict(expected)):
        raise GoalPhaseNativeOperationalBootstrapError(f"{name} differs from independently resolved authority")


def _exact_json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_map = cast(dict[object, object], left); right_map = cast(dict[object, object], right)
        return left_map.keys() == right_map.keys() and all(_exact_json_equal(left_map[key], right_map[key]) for key in left_map)
    if type(left) is list:
        left_list = cast(list[object], left); right_list = cast(list[object], right)
        return len(left_list) == len(right_list) and all(_exact_json_equal(a, b) for a, b in zip(left_list, right_list, strict=True))
    return left == right


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _content_ref(prefix: str, body: object) -> str:
    return prefix + ":" + _digest(_canonical(body))


__all__ = [name for name in globals() if name.startswith("Goal") or name.startswith("Committed") or name.startswith("decode_goal") or name.startswith("encode_goal") or name.startswith("plan_goal") or name.startswith("verify_goal") or name.startswith("verify_committed")]
