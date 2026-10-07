from __future__ import annotations

from dataclasses import replace

from .contracts import (
    AcceptAuthorityMappingIntent,
    AmendIssueScopePathsIntent,
    AppendIssueEvidenceIntent,
    AppendIssueUpdateIntent,
    BindIssueScopePathsIntent,
    BlockIssueIntent,
    CloseIssueIntent,
    EnsureIssueIntent,
    IntentRecord,
    IssueEvidenceRef,
    IssueIntent,
    IssueOperationalState,
    IssueSnapshot,
    IssueStatus,
    IssueUpdateLogEntry,
    PrepareAuthorityReconciliationIntent,
    ReconciliationState,
    ReconciliationStatus,
    RejectAuthorityMappingIntent,
    ReopenIssueIntent,
    ResumeIssueIntent,
    SetIssueOwnerIntent,
    StartIssueProgressIntent,
    TransitionOutcome,
    TransitionResult,
)
from .identity import fingerprint, stable_issue_ref

_MAX_INTENT_RECORDS = 128


def apply_issue_intent(
    state: IssueOperationalState,
    intent: IssueIntent,
) -> TransitionResult:
    """Apply one immutable issue intent without performing I/O."""

    intent_wire = intent.to_wire()
    intent_fingerprint = fingerprint(intent_wire)
    existing = next(
        (
            item
            for item in state.intent_records
            if item.client_intent_id == intent.context.client_intent_id
        ),
        None,
    )
    if existing is not None:
        if existing.fingerprint != intent_fingerprint:
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "client_intent_id_reused",
            )
        issue_ref = existing.affected_refs[0] if existing.affected_refs else None
        issue = state.issue_by_ref(issue_ref) if issue_ref is not None else None
        return TransitionResult(
            outcome=TransitionOutcome.IDEMPOTENT,
            state=state,
            issue_ref=issue_ref,
            issue_revision=None if issue is None else issue.revision,
            affected_refs=existing.affected_refs,
        )
    if not intent.context.actor_evidence.accepted:
        return _unchanged(state, TransitionOutcome.UNAUTHORIZED, "actor_not_accepted")
    if intent.context.expected_authority_generation != state.authority.generation:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "authority_generation_mismatch",
        )

    if isinstance(intent, EnsureIssueIntent):
        result = _ensure_issue(state, intent)
    elif isinstance(
        intent,
        (
            PrepareAuthorityReconciliationIntent,
            AcceptAuthorityMappingIntent,
            RejectAuthorityMappingIntent,
        ),
    ):
        result = _reconcile_authority(state, intent)
    else:
        result = _apply_target_intent(state, intent)

    if result.outcome is not TransitionOutcome.APPLIED:
        return result
    record = IntentRecord(
        client_intent_id=intent.context.client_intent_id,
        fingerprint=intent_fingerprint,
        outcome=result.outcome,
        affected_refs=result.affected_refs,
    )
    records = (*result.state.intent_records, record)[-_MAX_INTENT_RECORDS:]
    return replace(result, state=replace(result.state, intent_records=records))


def _ensure_issue(
    state: IssueOperationalState,
    intent: EnsureIssueIntent,
) -> TransitionResult:
    existing = state.issue_by_tag(intent.tag)
    if existing is not None:
        expected = (
            intent.title,
            intent.priority_level,
            intent.owner_session_id,
            intent.overview_content_ref,
        )
        observed = (
            existing.title,
            existing.priority_level,
            existing.owner_session_id,
            existing.overview_content_ref,
        )
        if expected != observed:
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "issue_tag_already_exists",
                issue=existing,
            )
        if intent.context.expected_issue_revision not in {None, existing.revision}:
            return _unchanged(
                state,
                TransitionOutcome.STALE,
                "issue_revision_mismatch",
                issue=existing,
            )
        return TransitionResult(
            outcome=TransitionOutcome.IDEMPOTENT,
            state=state,
            issue_ref=existing.issue_ref,
            issue_revision=existing.revision,
            affected_refs=(existing.issue_ref,),
        )
    if intent.context.expected_issue_revision is not None:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "issue_must_be_absent",
        )
    issue = IssueSnapshot(
        issue_ref=stable_issue_ref(
            authority_ref=state.authority.authority_ref,
            tag=intent.tag,
        ),
        tag=intent.tag,
        title=intent.title,
        status=IssueStatus.OPEN,
        priority_level=intent.priority_level,
        owner_session_id=intent.owner_session_id,
        overview_content_ref=intent.overview_content_ref,
        authority=state.authority,
    )
    issues = tuple(sorted((*state.issues, issue), key=lambda item: item.issue_ref))
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=replace(state, issues=issues),
        changed=True,
        issue_ref=issue.issue_ref,
        issue_revision=issue.revision,
        affected_refs=(issue.issue_ref,),
    )


def _apply_target_intent(
    state: IssueOperationalState,
    intent: IssueIntent,
) -> TransitionResult:
    issue_ref = getattr(intent, "issue_ref", None)
    issue = state.issue_by_ref(issue_ref) if isinstance(issue_ref, str) else None
    if issue is None:
        return _unchanged(state, TransitionOutcome.UNRESOLVED, "issue_not_found")
    if intent.context.expected_issue_revision != issue.revision:
        return _unchanged(
            state,
            TransitionOutcome.STALE,
            "issue_revision_mismatch",
            issue=issue,
        )

    if isinstance(intent, BindIssueScopePathsIntent):
        updated = replace(
            issue,
            scope_paths=intent.scope_paths,
            revision=issue.revision + 1,
        )
    elif isinstance(intent, SetIssueOwnerIntent):
        if issue.status is IssueStatus.CLOSED:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "issue_owner_transfer_closed",
                issue=issue,
            )
        if issue.owner_session_id is None:
            return _unchanged(
                state,
                TransitionOutcome.UNAUTHORIZED,
                "issue_owner_transfer_unassigned",
                issue=issue,
            )
        if issue.owner_session_id != intent.context.actor_evidence.actor_ref:
            return _unchanged(
                state,
                TransitionOutcome.UNAUTHORIZED,
                "issue_owner_transfer_actor_mismatch",
                issue=issue,
            )
        if issue.owner_session_id == intent.new_owner_session_id:
            return TransitionResult(
                outcome=TransitionOutcome.IDEMPOTENT,
                state=state,
                issue_ref=issue.issue_ref,
                issue_revision=issue.revision,
                affected_refs=(issue.issue_ref,),
            )
        updated = replace(
            issue,
            owner_session_id=intent.new_owner_session_id,
            revision=issue.revision + 1,
        )
    elif isinstance(intent, AmendIssueScopePathsIntent):
        if issue.status is not IssueStatus.IN_PROGRESS:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "issue_scope_amendment_status_invalid",
                issue=issue,
            )
        if issue.owner_session_id != intent.owner_session_id:
            return _unchanged(
                state,
                TransitionOutcome.UNAUTHORIZED,
                "issue_scope_amendment_owner_mismatch",
                issue=issue,
            )
        additions = tuple(
            item for item in intent.add_scope_paths if item not in issue.scope_paths
        )
        if not additions:
            return TransitionResult(
                outcome=TransitionOutcome.IDEMPOTENT,
                state=state,
                issue_ref=issue.issue_ref,
                issue_revision=issue.revision,
                affected_refs=(issue.issue_ref,),
            )
        amended_scope = tuple(sorted((*issue.scope_paths, *additions)))
        if len(amended_scope) > 128:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "issue_scope_capacity_exceeded",
                issue=issue,
            )
        updated = replace(
            issue,
            scope_paths=amended_scope,
            revision=issue.revision + 1,
        )
    elif isinstance(intent, AppendIssueUpdateIntent):
        entry = IssueUpdateLogEntry(
            sequence=len(issue.updates) + 1,
            message=intent.message,
            actor_ref=(
                intent.attributed_actor_ref or intent.context.actor_evidence.actor_ref
            ),
            actor_evidence_ref=(
                intent.attributed_actor_evidence_ref
                or intent.context.actor_evidence.evidence_ref
            ),
            outcome=intent.outcome,
            command=intent.command,
            command_exit_code=intent.command_exit_code,
            recorded_at=intent.recorded_at,
            time_authority=intent.time_authority,
        )
        updated = replace(
            issue,
            updates=(*issue.updates, entry),
            revision=issue.revision + 1,
        )
    elif isinstance(intent, AppendIssueEvidenceIntent):
        entry = IssueEvidenceRef(
            sequence=len(issue.evidence_refs) + 1,
            path=intent.path,
            description=intent.description,
        )
        updated = replace(
            issue,
            evidence_refs=(*issue.evidence_refs, entry),
            revision=issue.revision + 1,
        )
    else:
        target = _lifecycle_target(issue.status, intent)
        if target is None:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "invalid_lifecycle_transition",
                issue=issue,
            )
        updated = replace(issue, status=target, revision=issue.revision + 1)
    issues = tuple(
        updated if item.issue_ref == issue.issue_ref else item for item in state.issues
    )
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=replace(state, issues=issues),
        changed=True,
        issue_ref=updated.issue_ref,
        issue_revision=updated.revision,
        affected_refs=(updated.issue_ref,),
    )


def _lifecycle_target(status: IssueStatus, intent: IssueIntent) -> IssueStatus | None:
    if isinstance(intent, StartIssueProgressIntent) and status is IssueStatus.OPEN:
        return IssueStatus.IN_PROGRESS
    if isinstance(intent, BlockIssueIntent) and status in {
        IssueStatus.OPEN,
        IssueStatus.IN_PROGRESS,
    }:
        return IssueStatus.BLOCKED
    if isinstance(intent, ResumeIssueIntent) and status is IssueStatus.BLOCKED:
        return IssueStatus.IN_PROGRESS
    if isinstance(intent, ReopenIssueIntent) and status is IssueStatus.CLOSED:
        return IssueStatus.OPEN
    if isinstance(intent, CloseIssueIntent) and status is not IssueStatus.CLOSED:
        return IssueStatus.CLOSED
    return None


def _reconcile_authority(
    state: IssueOperationalState,
    intent: (
        PrepareAuthorityReconciliationIntent
        | AcceptAuthorityMappingIntent
        | RejectAuthorityMappingIntent
    ),
) -> TransitionResult:
    if intent.context.expected_issue_revision is not None:
        return _unchanged(
            state,
            TransitionOutcome.INVALID,
            "authority_intent_cannot_target_issue_revision",
        )
    current = state.authority.reconciliation
    if current is None:
        return _unchanged(
            state,
            TransitionOutcome.BLOCKED,
            "authority_not_reconcilable",
        )
    if isinstance(intent, PrepareAuthorityReconciliationIntent):
        if current.status not in {
            ReconciliationStatus.UNMAPPED,
            ReconciliationStatus.REJECTED,
            ReconciliationStatus.CONFLICT,
        }:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "reconciliation_not_preparable",
            )
        reconciliation = ReconciliationState(
            status=ReconciliationStatus.MAPPING_PENDING,
            canonical_authority_ref=intent.canonical_authority_ref,
        )
    elif isinstance(intent, AcceptAuthorityMappingIntent):
        if (
            current.status is not ReconciliationStatus.MAPPING_PENDING
            or current.canonical_authority_ref != intent.canonical_authority_ref
        ):
            return _unchanged(
                state,
                TransitionOutcome.CONFLICT,
                "pending_mapping_mismatch",
            )
        reconciliation = ReconciliationState(
            status=ReconciliationStatus.MAPPED,
            canonical_authority_ref=intent.canonical_authority_ref,
            evidence_ref=intent.evidence_ref,
        )
    else:
        if current.status is not ReconciliationStatus.MAPPING_PENDING:
            return _unchanged(
                state,
                TransitionOutcome.INVALID,
                "reconciliation_not_pending",
            )
        reconciliation = ReconciliationState(
            status=ReconciliationStatus.REJECTED,
            reason=intent.reason,
        )
    authority = replace(
        state.authority,
        generation=state.authority.generation + 1,
        reconciliation=reconciliation,
    )
    issues = tuple(replace(item, authority=authority) for item in state.issues)
    affected = (state.authority.authority_ref, *(item.issue_ref for item in issues))
    return TransitionResult(
        outcome=TransitionOutcome.APPLIED,
        state=replace(state, authority=authority, issues=issues),
        changed=True,
        affected_refs=affected,
    )


def _unchanged(
    state: IssueOperationalState,
    outcome: TransitionOutcome,
    blocker_code: str,
    *,
    issue: IssueSnapshot | None = None,
) -> TransitionResult:
    return TransitionResult(
        outcome=outcome,
        state=state,
        issue_ref=None if issue is None else issue.issue_ref,
        issue_revision=None if issue is None else issue.revision,
        blocker_code=blocker_code,
    )
