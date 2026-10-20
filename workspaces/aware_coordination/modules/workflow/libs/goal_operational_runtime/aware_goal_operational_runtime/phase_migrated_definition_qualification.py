"""Qualification of one incomplete migrated Phase definition in a V2 carrier."""
# pyright: reportAny=false, reportArgumentType=false, reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false, reportUnusedCallResult=false
# pyright: reportUnnecessaryCast=false
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from typing import cast

from .phase_contracts import GoalPhaseCoordinate
from .phase_document import (
    GoalLanePhaseDefinitionV1,
    GoalPhaseNativeDocumentV2,
)
from .phase_native_operational_bootstrap import (
    GoalCoordinatorAuthorityV1,
    GoalOwnerCoordinatorAuthorityPublicationV1,
    decode_goal_coordinator_authority,
    decode_goal_owner_coordinator_authority_publication,
    encode_goal_coordinator_authority,
    encode_goal_owner_coordinator_authority_publication,
)

PROPOSAL_SCHEMA = "aware.goal.migrated-definition-qualification-proposal.v1"
PROPOSAL_PUBLICATION_SCHEMA = (
    "aware.goal.migrated-definition-qualification-proposal-publication.v1"
)
ACCEPTANCE_SCHEMA = "aware.goal.migrated-definition-qualification-acceptance.v1"
ACCEPTANCE_PUBLICATION_SCHEMA = (
    "aware.goal.migrated-definition-qualification-acceptance-publication.v1"
)
PLAN_SCHEMA = "aware.goal.migrated-definition-qualification-plan.v1"
PUBLICATION_RECEIPT_SCHEMA = (
    "aware.goal.migrated-definition-qualification-publication-receipt.v1"
)

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_BLOB = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_TOKEN = re.compile(r"^[^\s|]+$")


class GoalPhaseMigratedDefinitionQualificationError(ValueError):
    """Definition qualification authority or transition is invalid."""


def _text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be non-empty text"
        )
    return value


def _token(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if _TOKEN.fullmatch(result) is None:
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be one token"
        )
    return result


def _sha(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if _SHA.fullmatch(result) is None:
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be sha256:<64 lowercase hex>"
        )
    return result


def _commit(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if _COMMIT.fullmatch(result) is None:
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be an exact Git commit identity"
        )
    return result


def _blob(value: object, field_name: str) -> str:
    result = _text(value, field_name)
    if _BLOB.fullmatch(result) is None:
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be an exact Git blob identity"
        )
    return result


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _content_ref(kind: str, body: dict[str, object]) -> str:
    return f"{kind}:{_digest(body).removeprefix('sha256:')}"


def _tokens(values: object, field_name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be exact tuple")
    result = tuple(_token(item, field_name) for item in values)
    if not result or len(result) != len(set(result)):
        raise GoalPhaseMigratedDefinitionQualificationError(
            f"{field_name} must be non-empty and unique"
        )
    return result


def _coordinate_wire(value: GoalPhaseCoordinate) -> dict[str, str]:
    return {
        "goal_tag": value.goal_tag,
        "lane_key": value.lane_key,
        "phase_key": value.phase_key,
    }


@dataclass(frozen=True, slots=True)
class GoalPhaseDefinitionQualificationProposalV1:
    goal_path: str
    goal_tag: str
    source_document_ref: str
    source_repository_revision: str
    coordinate: GoalPhaseCoordinate
    ordinal: int
    gate_digest: str
    before_definition_ref: str
    title: str
    intent: str
    evidence_refs: tuple[str, ...]
    issuer_execution_id: str
    proposed_at: str
    proposal_ref: str = field(init=False)
    schema_id: str = PROPOSAL_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDefinitionQualificationProposalV1:
            raise TypeError("proposal type must be exact")
        if self.schema_id != PROPOSAL_SCHEMA:
            raise GoalPhaseMigratedDefinitionQualificationError("unsupported proposal")
        _token(self.goal_path, "goal_path")
        _token(self.goal_tag, "goal_tag")
        _token(self.source_document_ref, "source_document_ref")
        _commit(self.source_repository_revision, "source_repository_revision")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate must be GoalPhaseCoordinate")
        if self.coordinate.goal_tag != self.goal_tag:
            raise GoalPhaseMigratedDefinitionQualificationError("wrong Goal coordinate")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise GoalPhaseMigratedDefinitionQualificationError("invalid ordinal")
        _sha(self.gate_digest, "gate_digest")
        _token(self.before_definition_ref, "before_definition_ref")
        _text(self.title, "title")
        _text(self.intent, "intent")
        _tokens(self.evidence_refs, "evidence_refs")
        _token(self.issuer_execution_id, "issuer_execution_id")
        _text(self.proposed_at, "proposed_at")
        object.__setattr__(self, "proposal_ref", _content_ref("goal-phase-definition-qualification-proposal", _proposal_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_proposal_body(self), "proposal_ref": self.proposal_ref}


@dataclass(frozen=True, slots=True)
class GoalDefinitionQualificationIssueAuthorityV1:
    issue_path: str
    issue_blob: str
    owner_execution_id: str
    status: str
    scope_digest: str

    def __post_init__(self) -> None:
        if type(self) is not GoalDefinitionQualificationIssueAuthorityV1:
            raise TypeError("Issue authority type must be exact")
        _token(self.issue_path, "issue_path")
        _blob(self.issue_blob, "issue_blob")
        _token(self.owner_execution_id, "owner_execution_id")
        if self.status != "In Progress":
            raise GoalPhaseMigratedDefinitionQualificationError("Issue must be In Progress")
        _sha(self.scope_digest, "scope_digest")

    def to_wire(self) -> dict[str, str]:
        return {
            "issue_path": self.issue_path,
            "issue_blob": self.issue_blob,
            "owner_execution_id": self.owner_execution_id,
            "status": self.status,
            "scope_digest": self.scope_digest,
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseDefinitionQualificationProposalPublicationV1:
    proposal: GoalPhaseDefinitionQualificationProposalV1
    artifact_path: str
    publication_commit: str
    artifact_blob: str
    repository_commit_receipt_ref: str
    issue_authority: GoalDefinitionQualificationIssueAuthorityV1
    artifact_payload_digest: str
    authority_ref: str = field(init=False)
    schema_id: str = PROPOSAL_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDefinitionQualificationProposalPublicationV1:
            raise TypeError("proposal publication type must be exact")
        self.proposal.__post_init__()
        self.issue_authority.__post_init__()
        if self.issue_authority.owner_execution_id != self.proposal.issuer_execution_id:
            raise GoalPhaseMigratedDefinitionQualificationError(
                "proposal Issue is not issuer-owned"
            )
        _token(self.artifact_path, "artifact_path")
        _commit(self.publication_commit, "publication_commit")
        _blob(self.artifact_blob, "artifact_blob")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.publication_commit}":
            raise GoalPhaseMigratedDefinitionQualificationError("proposal repository receipt mismatch")
        _sha(self.artifact_payload_digest, "artifact_payload_digest")
        expected = "sha256:" + hashlib.sha256(encode_goal_phase_definition_qualification_proposal(self.proposal)).hexdigest()
        if self.artifact_payload_digest != expected:
            raise GoalPhaseMigratedDefinitionQualificationError("proposal payload digest mismatch")
        object.__setattr__(self, "authority_ref", _content_ref("goal-phase-definition-qualification-proposal-publication", _proposal_publication_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_proposal_publication_body(self), "authority_ref": self.authority_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseDefinitionQualificationAcceptanceV1:
    proposal_publication_authority_ref: str
    goal_path: str
    goal_tag: str
    source_document_ref: str
    source_repository_revision: str
    coordinator_authority_ref: str
    accepting_execution_id: str
    publication_issue_path: str
    accepted_at: str
    acceptance_ref: str = field(init=False)
    schema_id: str = ACCEPTANCE_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDefinitionQualificationAcceptanceV1:
            raise TypeError("acceptance type must be exact")
        for field_name in ("proposal_publication_authority_ref", "goal_path", "goal_tag", "source_document_ref", "coordinator_authority_ref", "accepting_execution_id", "publication_issue_path"):
            _token(getattr(self, field_name), field_name)
        _commit(self.source_repository_revision, "source_repository_revision")
        _text(self.accepted_at, "accepted_at")
        object.__setattr__(self, "acceptance_ref", _content_ref("goal-phase-definition-qualification-acceptance", _acceptance_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_acceptance_body(self), "acceptance_ref": self.acceptance_ref}


@dataclass(frozen=True, slots=True)
class GoalCoordinatorDelegationPublicationV1:
    authority: GoalCoordinatorAuthorityV1
    publication: GoalOwnerCoordinatorAuthorityPublicationV1

    def __post_init__(self) -> None:
        if type(self) is not GoalCoordinatorDelegationPublicationV1:
            raise TypeError("delegation publication type must be exact")
        if type(self.authority) is not GoalCoordinatorAuthorityV1:
            raise TypeError("authority must be exact GoalCoordinatorAuthorityV1")
        if type(self.publication) is not GoalOwnerCoordinatorAuthorityPublicationV1:
            raise TypeError(
                "publication must be exact GoalOwnerCoordinatorAuthorityPublicationV1"
            )
        self.authority.__post_init__()
        self.publication.__post_init__()
        if (
            self.publication.coordinator_authority_ref != self.authority.authority_ref
            or self.publication.coordinator_execution_id
            != self.authority.coordinator_execution_id
            or self.publication.goal_tag != self.authority.goal_tag
            or self.publication.goal_doc_path != self.authority.goal_doc_path
            or self.publication.authority_source_ref
            != self.authority.authority_source_ref
        ):
            raise GoalPhaseMigratedDefinitionQualificationError(
                "Goal-owner publication does not bind coordinator authority"
            )
        if (
            self.authority.authority_profile == "committed_goal_owner_v1"
            and self.authority.coordinator_execution_id
            != self.publication.goal_owner_execution_id
        ):
            raise GoalPhaseMigratedDefinitionQualificationError(
                "committed Goal-owner authority cannot delegate to another execution"
            )

    @property
    def authority_ref(self) -> str:
        return self.authority.authority_ref

    @property
    def currentness_ref(self) -> str:
        return self.authority.currentness_ref

    @property
    def revocation_ref(self) -> str:
        return f"goal-coordinator-revocation:{self.authority.revocation_state}"

    def to_wire(self) -> dict[str, object]:
        return {
            "authority": json.loads(encode_goal_coordinator_authority(self.authority)),
            "publication": json.loads(
                encode_goal_owner_coordinator_authority_publication(self.publication)
            ),
        }


@dataclass(frozen=True, slots=True)
class GoalPhaseDefinitionQualificationAcceptancePublicationV1:
    acceptance: GoalPhaseDefinitionQualificationAcceptanceV1
    artifact_path: str
    publication_commit: str
    artifact_blob: str
    repository_commit_receipt_ref: str
    issue_authority: GoalDefinitionQualificationIssueAuthorityV1
    proposal_publication: GoalPhaseDefinitionQualificationProposalPublicationV1
    delegation: GoalCoordinatorDelegationPublicationV1
    authority_ref: str = field(init=False)
    schema_id: str = ACCEPTANCE_PUBLICATION_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseDefinitionQualificationAcceptancePublicationV1:
            raise TypeError("acceptance publication type must be exact")
        self.acceptance.__post_init__()
        self.issue_authority.__post_init__()
        self.proposal_publication.__post_init__()
        self.delegation.__post_init__()
        _token(self.artifact_path, "artifact_path")
        _commit(self.publication_commit, "publication_commit")
        _blob(self.artifact_blob, "artifact_blob")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.publication_commit}":
            raise GoalPhaseMigratedDefinitionQualificationError("acceptance repository receipt mismatch")
        if self.acceptance.proposal_publication_authority_ref != self.proposal_publication.authority_ref:
            raise GoalPhaseMigratedDefinitionQualificationError("acceptance names wrong proposal publication")
        if self.acceptance.coordinator_authority_ref != self.delegation.authority_ref:
            raise GoalPhaseMigratedDefinitionQualificationError("acceptance names wrong coordinator authority")
        if self.acceptance.accepting_execution_id != self.issue_authority.owner_execution_id:
            raise GoalPhaseMigratedDefinitionQualificationError("acceptance Issue is not coordinator-owned")
        if (
            self.acceptance.accepting_execution_id
            != self.delegation.authority.coordinator_execution_id
        ):
            raise GoalPhaseMigratedDefinitionQualificationError(
                "acceptance execution is not the authorized coordinator"
            )
        if self.acceptance.publication_issue_path != self.issue_authority.issue_path:
            raise GoalPhaseMigratedDefinitionQualificationError("acceptance Issue path mismatch")
        object.__setattr__(self, "authority_ref", _content_ref("goal-phase-definition-qualification-acceptance-publication", _acceptance_publication_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_acceptance_publication_body(self), "authority_ref": self.authority_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseMigratedDefinitionQualificationPlanV1:
    before_document: GoalPhaseNativeDocumentV2
    after_document: GoalPhaseNativeDocumentV2
    before_definition_ref: str
    after_definition_ref: str
    proposal_publication: GoalPhaseDefinitionQualificationProposalPublicationV1
    acceptance_publication: GoalPhaseDefinitionQualificationAcceptancePublicationV1
    semantic_intent_ref: str = field(init=False)
    schema_id: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMigratedDefinitionQualificationPlanV1:
            raise TypeError("plan type must be exact")
        _validate_plan(self)
        object.__setattr__(self, "semantic_intent_ref", _content_ref("goal-phase-definition-qualification-intent", _plan_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_plan_body(self), "semantic_intent_ref": self.semantic_intent_ref}


@dataclass(frozen=True, slots=True)
class GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1:
    semantic_intent_ref: str
    before_document_ref: str
    after_document_ref: str
    before_definition_ref: str
    after_definition_ref: str
    proposal_publication_authority_ref: str
    acceptance_publication_authority_ref: str
    publication_issue_authority_ref: str
    repository_parent_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    changed_path: str
    reconciliation_disposition: str
    receipt_ref: str = field(init=False)
    schema_id: str = PUBLICATION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1:
            raise TypeError("publication receipt type must be exact")
        if self.schema_id != PUBLICATION_RECEIPT_SCHEMA:
            raise GoalPhaseMigratedDefinitionQualificationError("unsupported publication receipt")
        for field_name in (
            "semantic_intent_ref", "before_document_ref", "after_document_ref",
            "before_definition_ref", "after_definition_ref",
            "proposal_publication_authority_ref",
            "acceptance_publication_authority_ref",
            "publication_issue_authority_ref", "changed_path",
        ):
            _token(getattr(self, field_name), field_name)
        _commit(self.repository_parent_ref, "repository_parent_ref")
        _commit(self.repository_commit_ref, "repository_commit_ref")
        if self.repository_commit_receipt_ref != f"repository-commit:{self.repository_commit_ref}":
            raise GoalPhaseMigratedDefinitionQualificationError("repository receipt mismatch")
        if self.reconciliation_disposition not in {"clear", "reconciliation_required"}:
            raise GoalPhaseMigratedDefinitionQualificationError("invalid reconciliation disposition")
        object.__setattr__(self, "receipt_ref", _content_ref("goal-migrated-definition-qualification-publication", _receipt_body(self)))

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": self.schema_id, **_receipt_body(self), "receipt_ref": self.receipt_ref}


def plan_goal_phase_migrated_definition_qualification(*, source_document: GoalPhaseNativeDocumentV2, proposal_publication: GoalPhaseDefinitionQualificationProposalPublicationV1, acceptance_publication: GoalPhaseDefinitionQualificationAcceptancePublicationV1) -> GoalPhaseMigratedDefinitionQualificationPlanV1:
    source_document.__post_init__()
    proposal_publication.__post_init__()
    acceptance_publication.__post_init__()
    proposal = proposal_publication.proposal
    acceptance = acceptance_publication.acceptance
    if acceptance_publication.proposal_publication != proposal_publication:
        raise GoalPhaseMigratedDefinitionQualificationError("acceptance proposal publication differs")
    if (proposal.goal_tag != source_document.goal_tag or proposal.source_document_ref != source_document.document_ref):
        raise GoalPhaseMigratedDefinitionQualificationError("proposal source document mismatch")
    if (acceptance.goal_path != proposal.goal_path or acceptance.goal_tag != proposal.goal_tag or acceptance.source_document_ref != proposal.source_document_ref or acceptance.source_repository_revision != proposal.source_repository_revision):
        raise GoalPhaseMigratedDefinitionQualificationError("acceptance source authority mismatch")
    matches = [(index, item) for index, item in enumerate(source_document.definitions) if item.coordinate == proposal.coordinate]
    if len(matches) != 1:
        raise GoalPhaseMigratedDefinitionQualificationError("target definition must exist exactly once")
    index, before = matches[0]
    if any(item.coordinate == proposal.coordinate for item in source_document.operational_bundle.phases):
        raise GoalPhaseMigratedDefinitionQualificationError("target Phase is already operational")
    if before.title is not None and before.intent is not None:
        raise GoalPhaseMigratedDefinitionQualificationError("complete definition cannot be qualified")
    if (before.ordinal != proposal.ordinal or before.gate.gate_digest != proposal.gate_digest or before.definition_ref != proposal.before_definition_ref):
        raise GoalPhaseMigratedDefinitionQualificationError("proposal definition preimage mismatch")
    after = GoalLanePhaseDefinitionV1(coordinate=before.coordinate, ordinal=before.ordinal, gate=before.gate, title=proposal.title, intent=proposal.intent)
    definitions = list(source_document.definitions)
    definitions[index] = after
    target = replace(source_document, definitions=tuple(definitions))
    return GoalPhaseMigratedDefinitionQualificationPlanV1(before_document=source_document, after_document=target, before_definition_ref=before.definition_ref, after_definition_ref=after.definition_ref, proposal_publication=proposal_publication, acceptance_publication=acceptance_publication)


def verify_goal_phase_migrated_definition_qualification_transition(plan: GoalPhaseMigratedDefinitionQualificationPlanV1) -> None:
    plan.__post_init__()


def issue_goal_phase_migrated_definition_qualification_publication_receipt(
    *,
    plan: GoalPhaseMigratedDefinitionQualificationPlanV1,
    publication_issue_authority_ref: str,
    repository_parent_ref: str,
    repository_commit_ref: str,
    repository_commit_receipt_ref: str,
    changed_path: str,
    reconciliation_disposition: str,
) -> GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1:
    plan.__post_init__()
    if changed_path != plan.proposal_publication.proposal.goal_path:
        raise GoalPhaseMigratedDefinitionQualificationError("changed path is not the Goal path")
    return GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1(
        semantic_intent_ref=plan.semantic_intent_ref,
        before_document_ref=plan.before_document.document_ref,
        after_document_ref=plan.after_document.document_ref,
        before_definition_ref=plan.before_definition_ref,
        after_definition_ref=plan.after_definition_ref,
        proposal_publication_authority_ref=plan.proposal_publication.authority_ref,
        acceptance_publication_authority_ref=plan.acceptance_publication.authority_ref,
        publication_issue_authority_ref=publication_issue_authority_ref,
        repository_parent_ref=repository_parent_ref,
        repository_commit_ref=repository_commit_ref,
        repository_commit_receipt_ref=repository_commit_receipt_ref,
        changed_path=changed_path,
        reconciliation_disposition=reconciliation_disposition,
    )


def encode_goal_phase_definition_qualification_proposal(value: GoalPhaseDefinitionQualificationProposalV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_definition_qualification_proposal(payload: bytes) -> GoalPhaseDefinitionQualificationProposalV1:
    values = _decode_object(payload, PROPOSAL_SCHEMA)
    coordinate = _decode_coordinate(values.pop("coordinate"))
    supplied_ref = values.pop("proposal_ref")
    proposal = GoalPhaseDefinitionQualificationProposalV1(coordinate=coordinate, evidence_refs=_string_tuple(values.pop("evidence_refs"), "evidence_refs"), **cast(dict[str, object], values))
    if supplied_ref != proposal.proposal_ref or payload != encode_goal_phase_definition_qualification_proposal(proposal):
        raise GoalPhaseMigratedDefinitionQualificationError("proposal is noncanonical")
    return proposal


def encode_goal_phase_definition_qualification_acceptance(value: GoalPhaseDefinitionQualificationAcceptanceV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_definition_qualification_acceptance(payload: bytes) -> GoalPhaseDefinitionQualificationAcceptanceV1:
    values = _decode_object(payload, ACCEPTANCE_SCHEMA)
    supplied_ref = values.pop("acceptance_ref")
    acceptance = GoalPhaseDefinitionQualificationAcceptanceV1(**cast(dict[str, object], values))
    if supplied_ref != acceptance.acceptance_ref or payload != encode_goal_phase_definition_qualification_acceptance(acceptance):
        raise GoalPhaseMigratedDefinitionQualificationError("acceptance is noncanonical")
    return acceptance


def encode_goal_phase_definition_qualification_proposal_publication(value: GoalPhaseDefinitionQualificationProposalPublicationV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_definition_qualification_proposal_publication(payload: bytes) -> GoalPhaseDefinitionQualificationProposalPublicationV1:
    values = _decode_object(payload, PROPOSAL_PUBLICATION_SCHEMA)
    supplied_ref = values.pop("authority_ref")
    proposal = decode_goal_phase_definition_qualification_proposal(
        _canonical(values.pop("proposal"))
    )
    issue = _decode_issue_authority(values.pop("issue_authority"))
    publication = GoalPhaseDefinitionQualificationProposalPublicationV1(
        proposal=proposal,
        issue_authority=issue,
        **cast(dict[str, object], values),
    )
    if supplied_ref != publication.authority_ref or payload != encode_goal_phase_definition_qualification_proposal_publication(publication):
        raise GoalPhaseMigratedDefinitionQualificationError("proposal publication is noncanonical")
    return publication


def encode_goal_phase_definition_qualification_acceptance_publication(value: GoalPhaseDefinitionQualificationAcceptancePublicationV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_definition_qualification_acceptance_publication(payload: bytes) -> GoalPhaseDefinitionQualificationAcceptancePublicationV1:
    values = _decode_object(payload, ACCEPTANCE_PUBLICATION_SCHEMA)
    supplied_ref = values.pop("authority_ref")
    acceptance = decode_goal_phase_definition_qualification_acceptance(
        _canonical(values.pop("acceptance"))
    )
    issue = _decode_issue_authority(values.pop("issue_authority"))
    proposal_publication = decode_goal_phase_definition_qualification_proposal_publication(
        _canonical(values.pop("proposal_publication"))
    )
    delegation = _decode_delegation(values.pop("delegation"))
    publication = GoalPhaseDefinitionQualificationAcceptancePublicationV1(
        acceptance=acceptance,
        issue_authority=issue,
        proposal_publication=proposal_publication,
        delegation=delegation,
        **cast(dict[str, object], values),
    )
    if supplied_ref != publication.authority_ref or payload != encode_goal_phase_definition_qualification_acceptance_publication(publication):
        raise GoalPhaseMigratedDefinitionQualificationError("acceptance publication is noncanonical")
    return publication


def encode_goal_phase_migrated_definition_qualification_publication_receipt(value: GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1) -> bytes:
    value.__post_init__()
    return _canonical(value.to_wire())


def decode_goal_phase_migrated_definition_qualification_publication_receipt(payload: bytes) -> GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1:
    values = _decode_object(payload, PUBLICATION_RECEIPT_SCHEMA)
    supplied_ref = values.pop("receipt_ref")
    receipt = GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1(**cast(dict[str, object], values))
    if supplied_ref != receipt.receipt_ref or payload != encode_goal_phase_migrated_definition_qualification_publication_receipt(receipt):
        raise GoalPhaseMigratedDefinitionQualificationError("publication receipt is noncanonical")
    return receipt


def _validate_plan(plan: GoalPhaseMigratedDefinitionQualificationPlanV1) -> None:
    plan.before_document.__post_init__()
    plan.after_document.__post_init__()
    plan.proposal_publication.__post_init__()
    plan.acceptance_publication.__post_init__()
    before = plan.before_document
    after = plan.after_document
    proposal = plan.proposal_publication.proposal
    if before.goal_tag != after.goal_tag or before.compatibility_projection_sha256 != after.compatibility_projection_sha256 or before.compatibility_projection_byte_count != after.compatibility_projection_byte_count or before.operational_bundle != after.operational_bundle or before.unresolved_dependencies != after.unresolved_dependencies or before.source_refs != after.source_refs or before.execution_authority != after.execution_authority:
        raise GoalPhaseMigratedDefinitionQualificationError("carrier authority outside target definition changed")
    if len(before.definitions) != len(after.definitions):
        raise GoalPhaseMigratedDefinitionQualificationError("definition count changed")
    changes = [(left, right) for left, right in zip(before.definitions, after.definitions, strict=True) if left != right]
    if len(changes) != 1:
        raise GoalPhaseMigratedDefinitionQualificationError("exactly one definition must change")
    left, right = changes[0]
    if left.coordinate != proposal.coordinate or left.definition_ref != plan.before_definition_ref or right.definition_ref != plan.after_definition_ref:
        raise GoalPhaseMigratedDefinitionQualificationError("definition refs do not bind transition")
    expected = GoalLanePhaseDefinitionV1(coordinate=left.coordinate, ordinal=left.ordinal, gate=left.gate, title=proposal.title, intent=proposal.intent)
    if right != expected:
        raise GoalPhaseMigratedDefinitionQualificationError("successor definition is not canonical")
    if any(item.coordinate == proposal.coordinate for item in after.operational_bundle.phases):
        raise GoalPhaseMigratedDefinitionQualificationError("qualification created operational authority")


def _proposal_body(value: GoalPhaseDefinitionQualificationProposalV1) -> dict[str, object]:
    return {"goal_path": value.goal_path, "goal_tag": value.goal_tag, "source_document_ref": value.source_document_ref, "source_repository_revision": value.source_repository_revision, "coordinate": _coordinate_wire(value.coordinate), "ordinal": value.ordinal, "gate_digest": value.gate_digest, "before_definition_ref": value.before_definition_ref, "title": value.title, "intent": value.intent, "evidence_refs": list(value.evidence_refs), "issuer_execution_id": value.issuer_execution_id, "proposed_at": value.proposed_at}


def _proposal_publication_body(value: GoalPhaseDefinitionQualificationProposalPublicationV1) -> dict[str, object]:
    return {"proposal": value.proposal.to_wire(), "artifact_path": value.artifact_path, "publication_commit": value.publication_commit, "artifact_blob": value.artifact_blob, "repository_commit_receipt_ref": value.repository_commit_receipt_ref, "issue_authority": value.issue_authority.to_wire(), "artifact_payload_digest": value.artifact_payload_digest}


def _acceptance_body(value: GoalPhaseDefinitionQualificationAcceptanceV1) -> dict[str, object]:
    return {"proposal_publication_authority_ref": value.proposal_publication_authority_ref, "goal_path": value.goal_path, "goal_tag": value.goal_tag, "source_document_ref": value.source_document_ref, "source_repository_revision": value.source_repository_revision, "coordinator_authority_ref": value.coordinator_authority_ref, "accepting_execution_id": value.accepting_execution_id, "publication_issue_path": value.publication_issue_path, "accepted_at": value.accepted_at}


def _acceptance_publication_body(value: GoalPhaseDefinitionQualificationAcceptancePublicationV1) -> dict[str, object]:
    return {"acceptance": value.acceptance.to_wire(), "artifact_path": value.artifact_path, "publication_commit": value.publication_commit, "artifact_blob": value.artifact_blob, "repository_commit_receipt_ref": value.repository_commit_receipt_ref, "issue_authority": value.issue_authority.to_wire(), "proposal_publication": value.proposal_publication.to_wire(), "delegation": value.delegation.to_wire()}


def _plan_body(value: GoalPhaseMigratedDefinitionQualificationPlanV1) -> dict[str, object]:
    return {"before_document_ref": value.before_document.document_ref, "after_document_ref": value.after_document.document_ref, "coordinate": _coordinate_wire(value.proposal_publication.proposal.coordinate), "before_definition_ref": value.before_definition_ref, "after_definition_ref": value.after_definition_ref, "proposal_publication_authority_ref": value.proposal_publication.authority_ref, "acceptance_publication_authority_ref": value.acceptance_publication.authority_ref}


def _receipt_body(value: GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1) -> dict[str, object]:
    return {
        "semantic_intent_ref": value.semantic_intent_ref,
        "before_document_ref": value.before_document_ref,
        "after_document_ref": value.after_document_ref,
        "before_definition_ref": value.before_definition_ref,
        "after_definition_ref": value.after_definition_ref,
        "proposal_publication_authority_ref": value.proposal_publication_authority_ref,
        "acceptance_publication_authority_ref": value.acceptance_publication_authority_ref,
        "publication_issue_authority_ref": value.publication_issue_authority_ref,
        "repository_parent_ref": value.repository_parent_ref,
        "repository_commit_ref": value.repository_commit_ref,
        "repository_commit_receipt_ref": value.repository_commit_receipt_ref,
        "changed_path": value.changed_path,
        "reconciliation_disposition": value.reconciliation_disposition,
    }


def _decode_object(payload: bytes, schema: str) -> dict[str, object]:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    try:
        raw = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoalPhaseMigratedDefinitionQualificationError("payload is not JSON") from error
    if type(raw) is not dict or raw.get("schema_id") != schema:
        raise GoalPhaseMigratedDefinitionQualificationError("wrong schema")
    values = cast(dict[str, object], raw)
    values.pop("schema_id")
    return values


def _decode_coordinate(raw: object) -> GoalPhaseCoordinate:
    if type(raw) is not dict or set(raw) != {"goal_tag", "lane_key", "phase_key"}:
        raise GoalPhaseMigratedDefinitionQualificationError("invalid coordinate")
    return GoalPhaseCoordinate(**cast(dict[str, str], raw))


def _string_tuple(raw: object, field_name: str) -> tuple[str, ...]:
    if type(raw) is not list or any(type(item) is not str for item in raw):
        raise GoalPhaseMigratedDefinitionQualificationError(f"{field_name} must contain exact strings")
    return tuple(cast(list[str], raw))


def _decode_issue_authority(raw: object) -> GoalDefinitionQualificationIssueAuthorityV1:
    if type(raw) is not dict or set(raw) != {"issue_path", "issue_blob", "owner_execution_id", "status", "scope_digest"}:
        raise GoalPhaseMigratedDefinitionQualificationError("invalid Issue authority")
    return GoalDefinitionQualificationIssueAuthorityV1(**cast(dict[str, str], raw))


def _decode_delegation(raw: object) -> GoalCoordinatorDelegationPublicationV1:
    if type(raw) is not dict or set(raw) != {"authority", "publication"}:
        raise GoalPhaseMigratedDefinitionQualificationError("invalid delegation authority")
    values = cast(dict[str, object], raw)
    return GoalCoordinatorDelegationPublicationV1(
        authority=decode_goal_coordinator_authority(_canonical(values["authority"])),
        publication=decode_goal_owner_coordinator_authority_publication(
            _canonical(values["publication"])
        ),
    )


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GoalPhaseMigratedDefinitionQualificationError("duplicate JSON key")
        result[key] = value
    return result


__all__ = [
    "ACCEPTANCE_PUBLICATION_SCHEMA",
    "ACCEPTANCE_SCHEMA",
    "PLAN_SCHEMA",
    "PROPOSAL_PUBLICATION_SCHEMA",
    "PROPOSAL_SCHEMA",
    "PUBLICATION_RECEIPT_SCHEMA",
    "GoalCoordinatorDelegationPublicationV1",
    "GoalDefinitionQualificationIssueAuthorityV1",
    "GoalPhaseDefinitionQualificationAcceptancePublicationV1",
    "GoalPhaseDefinitionQualificationAcceptanceV1",
    "GoalPhaseDefinitionQualificationProposalPublicationV1",
    "GoalPhaseDefinitionQualificationProposalV1",
    "GoalPhaseMigratedDefinitionQualificationError",
    "GoalPhaseMigratedDefinitionQualificationPlanV1",
    "GoalPhaseMigratedDefinitionQualificationPublicationReceiptV1",
    "decode_goal_phase_definition_qualification_acceptance",
    "decode_goal_phase_definition_qualification_acceptance_publication",
    "decode_goal_phase_definition_qualification_proposal",
    "decode_goal_phase_definition_qualification_proposal_publication",
    "decode_goal_phase_migrated_definition_qualification_publication_receipt",
    "encode_goal_phase_definition_qualification_acceptance",
    "encode_goal_phase_definition_qualification_acceptance_publication",
    "encode_goal_phase_definition_qualification_proposal",
    "encode_goal_phase_definition_qualification_proposal_publication",
    "encode_goal_phase_migrated_definition_qualification_publication_receipt",
    "issue_goal_phase_migrated_definition_qualification_publication_receipt",
    "plan_goal_phase_migrated_definition_qualification",
    "verify_goal_phase_migrated_definition_qualification_transition",
]
