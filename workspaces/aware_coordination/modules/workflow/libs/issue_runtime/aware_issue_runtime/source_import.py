from __future__ import annotations

from dataclasses import dataclass

from aware_issue_operational_runtime import (
    ActorEvidence,
    AppendIssueEvidenceIntent,
    AppendIssueUpdateIntent,
    BindIssueScopePathsIntent,
    BlockIssueIntent,
    CloseIssueIntent,
    EnsureIssueIntent,
    IssueIntent,
    IssueIntentContext,
    IssueOwnershipScopePath,
    IssueStatus,
    StartIssueProgressIntent,
    fingerprint,
    stable_issue_ref,
)
from aware_issue_operational_runtime import (
    IssueTimeAuthority as OperationalTimeAuthority,
)

from .contracts import IssueReadProjection, IssueTimeAuthority


@dataclass(frozen=True, slots=True)
class IssueSourceImportProposal:
    proposal_ref: str
    proposal_fingerprint: str
    source_issue_ref: str
    source_path: str
    source_digest: str
    target_authority_ref: str
    target_issue_ref: str | None
    tag: str | None
    title: str
    status: IssueStatus | None
    priority_level: str
    owner_session_id: str | None
    scope_paths: tuple[str, ...]
    blocker_codes: tuple[str, ...]

    @property
    def admissible(self) -> bool:
        return not self.blocker_codes

    def to_wire(self) -> dict[str, object]:
        return {
            "proposal_ref": self.proposal_ref,
            "proposal_fingerprint": self.proposal_fingerprint,
            "source_issue_ref": self.source_issue_ref,
            "source_path": self.source_path,
            "source_digest": self.source_digest,
            "target_authority_ref": self.target_authority_ref,
            "target_issue_ref": self.target_issue_ref,
            "tag": self.tag,
            "title": self.title,
            "status": None if self.status is None else self.status.value,
            "priority_level": self.priority_level,
            "owner_session_id": self.owner_session_id,
            "scope_paths": list(self.scope_paths),
            "blocker_codes": list(self.blocker_codes),
        }


@dataclass(frozen=True, slots=True)
class IssueSourceImportAdmission:
    proposal_ref: str
    proposal_fingerprint: str
    source_digest: str
    target_authority_ref: str
    target_issue_ref: str
    admitted_by: ActorEvidence
    intents: tuple[IssueIntent, ...]


def propose_issue_source_import(
    projection: IssueReadProjection,
    *,
    target_authority_ref: str,
) -> IssueSourceImportProposal:
    blockers: list[str] = []
    if projection.tag is None:
        blockers.append("source_tag_unresolved")
    try:
        status = IssueStatus(projection.status)
    except ValueError:
        status = None
        blockers.append("source_status_unsupported")
    target_issue_ref = (
        None
        if projection.tag is None
        else stable_issue_ref(
            authority_ref=target_authority_ref,
            tag=projection.tag,
        )
    )
    semantic = {
        "source_issue_ref": projection.issue_ref,
        "source_path": projection.source_path,
        "source_digest": projection.source_digest,
        "target_authority_ref": target_authority_ref,
        "target_issue_ref": target_issue_ref,
        "tag": projection.tag,
        "title": projection.title,
        "status": None if status is None else status.value,
        "priority_level": projection.priority or "medium",
        "owner_session_id": projection.owner_ref,
        "scope_paths": list(projection.ownership_scope),
        "blocker_codes": blockers,
    }
    proposal_fingerprint = fingerprint(semantic)
    return IssueSourceImportProposal(
        proposal_ref=f"issue-source-import:{proposal_fingerprint}",
        proposal_fingerprint=proposal_fingerprint,
        source_issue_ref=projection.issue_ref,
        source_path=projection.source_path,
        source_digest=projection.source_digest,
        target_authority_ref=target_authority_ref,
        target_issue_ref=target_issue_ref,
        tag=projection.tag,
        title=projection.title,
        status=status,
        priority_level=projection.priority or "medium",
        owner_session_id=projection.owner_ref,
        scope_paths=projection.ownership_scope,
        blocker_codes=tuple(blockers),
    )


def admit_issue_source_import(
    proposal: IssueSourceImportProposal,
    projection: IssueReadProjection,
    *,
    actor_evidence: ActorEvidence,
    expected_authority_generation: int,
) -> IssueSourceImportAdmission:
    current = propose_issue_source_import(
        projection,
        target_authority_ref=proposal.target_authority_ref,
    )
    if current.source_digest != proposal.source_digest:
        raise ValueError("source_digest_changed")
    if current.proposal_fingerprint != proposal.proposal_fingerprint:
        raise ValueError("proposal_fingerprint_changed")
    if not actor_evidence.accepted:
        raise ValueError("human_admission_required")
    if not proposal.admissible:
        raise ValueError("proposal_has_unresolved_blockers")
    assert proposal.tag is not None
    assert proposal.status is not None
    assert proposal.target_issue_ref is not None

    revision = 0
    intents: list[IssueIntent] = [
        EnsureIssueIntent(
            _context(
                proposal,
                actor_evidence,
                "ensure",
                issue_revision=None,
                authority_generation=expected_authority_generation,
            ),
            tag=proposal.tag,
            title=proposal.title,
            priority_level=proposal.priority_level,
            owner_session_id=proposal.owner_session_id,
        )
    ]
    lifecycle = _lifecycle_intent(
        proposal,
        actor_evidence,
        revision,
        expected_authority_generation,
    )
    if lifecycle is not None:
        intents.append(lifecycle)
        revision += 1
    if proposal.scope_paths:
        intents.append(
            BindIssueScopePathsIntent(
                _context(
                    proposal,
                    actor_evidence,
                    "scope",
                    issue_revision=revision,
                    authority_generation=expected_authority_generation,
                ),
                proposal.target_issue_ref,
                tuple(IssueOwnershipScopePath(path) for path in proposal.scope_paths),
            )
        )
        revision += 1
    source_evidence_ref = (
        f"issue-source:{projection.source_path}@{projection.source_digest}"
    )
    for activity in projection.activities:
        source_actor = activity.actor_ref or "source:unattributed"
        intents.append(
            AppendIssueUpdateIntent(
                _context(
                    proposal,
                    actor_evidence,
                    f"update-{activity.sequence}",
                    issue_revision=revision,
                    authority_generation=expected_authority_generation,
                ),
                proposal.target_issue_ref,
                message=activity.message,
                outcome=activity.outcome or "info",
                command=activity.command,
                command_exit_code=activity.command_exit_code,
                recorded_at=activity.activity_at,
                time_authority=_time_authority(activity.time_authority),
                attributed_actor_ref=source_actor,
                attributed_actor_evidence_ref=source_evidence_ref,
            )
        )
        revision += 1
    for evidence in projection.evidence:
        intents.append(
            AppendIssueEvidenceIntent(
                _context(
                    proposal,
                    actor_evidence,
                    f"evidence-{evidence.sequence}",
                    issue_revision=revision,
                    authority_generation=expected_authority_generation,
                ),
                proposal.target_issue_ref,
                path=evidence.reference,
                description=f"Imported {evidence.kind} source evidence",
            )
        )
        revision += 1
    return IssueSourceImportAdmission(
        proposal_ref=proposal.proposal_ref,
        proposal_fingerprint=proposal.proposal_fingerprint,
        source_digest=projection.source_digest,
        target_authority_ref=proposal.target_authority_ref,
        target_issue_ref=proposal.target_issue_ref,
        admitted_by=actor_evidence,
        intents=tuple(intents),
    )


def _lifecycle_intent(
    proposal: IssueSourceImportProposal,
    actor: ActorEvidence,
    revision: int,
    authority_generation: int,
) -> IssueIntent | None:
    assert proposal.status is not None
    assert proposal.target_issue_ref is not None
    if proposal.status is IssueStatus.OPEN:
        return None
    context = _context(
        proposal,
        actor,
        "lifecycle",
        issue_revision=revision,
        authority_generation=authority_generation,
    )
    if proposal.status is IssueStatus.IN_PROGRESS:
        return StartIssueProgressIntent(context, proposal.target_issue_ref)
    if proposal.status is IssueStatus.BLOCKED:
        return BlockIssueIntent(context, proposal.target_issue_ref)
    return CloseIssueIntent(context, proposal.target_issue_ref)


def _context(
    proposal: IssueSourceImportProposal,
    actor: ActorEvidence,
    suffix: str,
    *,
    issue_revision: int | None,
    authority_generation: int,
) -> IssueIntentContext:
    return IssueIntentContext(
        client_intent_id=f"{proposal.proposal_ref}:{suffix}",
        expected_issue_revision=issue_revision,
        expected_authority_generation=authority_generation,
        actor_evidence=actor,
    )


def _time_authority(value: IssueTimeAuthority) -> OperationalTimeAuthority:
    return {
        IssueTimeAuthority.COMMIT_RECEIPT: OperationalTimeAuthority.COMMIT_RECEIPT,
        IssueTimeAuthority.SOURCE_DECLARED: OperationalTimeAuthority.SOURCE_DECLARED,
        IssueTimeAuthority.SOURCE_OBSERVED: OperationalTimeAuthority.SOURCE_OBSERVED,
        IssueTimeAuthority.ISSUE_SERVICE: OperationalTimeAuthority.SOURCE_OBSERVED,
        IssueTimeAuthority.UNAVAILABLE: OperationalTimeAuthority.UNAVAILABLE,
    }[value]
