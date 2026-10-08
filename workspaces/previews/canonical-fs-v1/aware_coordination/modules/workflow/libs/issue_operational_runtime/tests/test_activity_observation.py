from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from aware_issue_operational_runtime import (
    AuthorityKind,
    IssueAuthorityEvidence,
    IssueEvent,
    IssueEventKind,
    IssueSnapshot,
    IssueStatus,
    IssueTimeAuthority,
    WorkflowIssueActivityMemberV1,
    WorkflowIssueActivityObservationError,
    WorkflowIssueActivitySelectionKind,
    WorkflowIssueActivityUnavailableReason,
    derive_workflow_issue_activity_head,
    derive_workflow_issue_activity_horizon,
    derive_workflow_issue_activity_member,
    derive_workflow_issue_activity_owner_observation,
    derive_workflow_issue_activity_selection,
    derive_workflow_issue_activity_unavailable,
    validate_workflow_issue_activity_observation_closure,
)


def authority(generation: int, *, historical: bool = False) -> IssueAuthorityEvidence:
    return IssueAuthorityEvidence(
        kind=(
            AuthorityKind.DETERMINISTIC_FIXTURE
            if historical
            else AuthorityKind.CANONICAL_COMMITTED
        ),
        provider_key="workflow.fixture",
        authority_ref="issue-authority:fixture",
        generation=generation,
        receipt_ref=f"receipt:g{generation}",
    )


def snapshot(
    revision: int, generation: int, *, historical: bool = False
) -> IssueSnapshot:
    return IssueSnapshot(
        issue_ref="issue:one",
        tag="fb/issue-one",
        title=f"Issue {revision}",
        status=IssueStatus.CLOSED if revision == 1 else IssueStatus.IN_PROGRESS,
        priority_level="p0",
        authority=authority(generation, historical=historical),
        revision=revision,
    )


def event(revision: int, generation: int, cursor: int) -> IssueEvent:
    return IssueEvent(
        event_ref=f"event:{cursor}",
        authority_ref="issue-authority:fixture",
        epoch="journal:one",
        cursor=cursor,
        kind=IssueEventKind.LIFECYCLE_CHANGED,
        authority_generation=generation,
        issue_ref="issue:one",
        issue_revision=revision,
        receipt_ref=f"event-receipt:{cursor}",
        affected_refs=("issue:one",),
    )


def make_closure():
    owner = derive_workflow_issue_activity_owner_observation(
        authority_kind=AuthorityKind.CANONICAL_COMMITTED,
        authority_ref="issue-authority:fixture",
        authority_generation=2,
        authority_receipt_ref="receipt:g2",
        store_generation=7,
        journal_epoch="journal:one",
        earliest_cursor=1,
        latest_cursor=2,
        next_cursor=3,
    )
    current_snapshot = snapshot(2, 2)
    historical_snapshot = snapshot(1, 1, historical=True)
    head = derive_workflow_issue_activity_head(
        owner_observation=owner, issue_snapshot=current_snapshot
    )
    current = derive_workflow_issue_activity_member(
        owner_observation=owner,
        issue_snapshot=current_snapshot,
        event=event(2, 2, 2),
        activity_at="2026-09-08T12:00:02Z",
        activity_time_authority=IssueTimeAuthority.COMMIT_RECEIPT,
        actor_execution_ref="codex:current",
    )
    historical = derive_workflow_issue_activity_member(
        owner_observation=owner,
        issue_snapshot=historical_snapshot,
        event=event(1, 1, 1),
        activity_at="2026-09-08T12:00:01Z",
        activity_time_authority=IssueTimeAuthority.SOURCE_OBSERVED,
        actor_execution_ref=None,
    )
    unavailable = derive_workflow_issue_activity_unavailable(
        owner_observation=owner,
        issue_ref="issue:missing",
        selection_kind=WorkflowIssueActivitySelectionKind.HISTORICAL,
        requested_issue_revision_ref="issue:missing:revision:1",
        reason=WorkflowIssueActivityUnavailableReason.HISTORY_NOT_RETAINED,
        detail="revision is outside retained suffix",
        observed_at="2026-09-08T12:00:03Z",
    )

    def outcome_key(item):
        if isinstance(item, WorkflowIssueActivityMemberV1):
            return (
                item.owner_observation.owner_observation_ref.encode(),
                item.issue_ref.encode(),
                b"selected",
                item.activity_ref.encode(),
            )
        return (
            item.owner_observation.owner_observation_ref.encode(),
            item.issue_ref.encode(),
            b"unavailable",
            item.unavailable_ref.encode(),
        )

    outcomes = tuple(
        sorted(
            (current, historical, unavailable),
            key=outcome_key,
        )
    )
    horizon = derive_workflow_issue_activity_horizon(
        owner_observation=owner,
        observed_at="2026-09-08T12:00:03Z",
        heads=(head,),
        outcomes=outcomes,
    )
    selections = tuple(
        sorted(
            (
                derive_workflow_issue_activity_selection(
                    horizon=horizon,
                    selection_kind=WorkflowIssueActivitySelectionKind.CURRENT,
                    issue_ref="issue:one",
                    requested_issue_revision_ref=None,
                    outcome=current,
                ),
                derive_workflow_issue_activity_selection(
                    horizon=horizon,
                    selection_kind=WorkflowIssueActivitySelectionKind.HISTORICAL,
                    issue_ref="issue:one",
                    requested_issue_revision_ref="issue:one:revision:1",
                    outcome=historical,
                ),
                derive_workflow_issue_activity_selection(
                    horizon=horizon,
                    selection_kind=WorkflowIssueActivitySelectionKind.HISTORICAL,
                    issue_ref="issue:missing",
                    requested_issue_revision_ref="issue:missing:revision:1",
                    outcome=unavailable,
                ),
            ),
            key=lambda item: (
                item.horizon_ref,
                item.issue_ref,
                item.selection_kind.value,
                item.requested_issue_revision_ref or "",
            ),
        )
    )
    return (head,), (horizon,), outcomes, selections


def test_historical_authority_is_preserved_under_current_owner() -> None:
    heads, horizons, outcomes, selections = make_closure()
    validate_workflow_issue_activity_observation_closure(
        heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
    )
    historical = cast(
        WorkflowIssueActivityMemberV1,
        next(
            item
            for item in outcomes
            if isinstance(item, WorkflowIssueActivityMemberV1)
            and item.authority_generation == 1
        ),
    )
    assert (
        historical.issue_snapshot.authority.kind is AuthorityKind.DETERMINISTIC_FIXTURE
    )
    assert historical.owner_observation.authority_generation == 2


def test_empty_owner_cannot_admit_member() -> None:
    empty = derive_workflow_issue_activity_owner_observation(
        authority_kind=AuthorityKind.CANONICAL_COMMITTED,
        authority_ref="issue-authority:fixture",
        authority_generation=2,
        authority_receipt_ref="receipt:g2",
        store_generation=7,
        journal_epoch="journal:one",
        earliest_cursor=3,
        latest_cursor=None,
        next_cursor=3,
    )
    with pytest.raises(WorkflowIssueActivityObservationError):
        derive_workflow_issue_activity_member(
            owner_observation=empty,
            issue_snapshot=snapshot(2, 2),
            event=event(2, 2, 2),
            activity_at="2026-09-08T12:00:02Z",
            activity_time_authority=IssueTimeAuthority.COMMIT_RECEIPT,
            actor_execution_ref=None,
        )


def test_event_snapshot_authority_disagreement_rejects() -> None:
    _, horizons, outcomes, _ = make_closure()
    historical = cast(
        WorkflowIssueActivityMemberV1,
        next(
            item
            for item in outcomes
            if isinstance(item, WorkflowIssueActivityMemberV1)
            and item.authority_generation == 1
        ),
    )
    with pytest.raises(WorkflowIssueActivityObservationError):
        derive_workflow_issue_activity_member(
            owner_observation=horizons[0].owner_observation,
            issue_snapshot=replace(historical.issue_snapshot, authority=authority(2)),
            event=historical.event,
            activity_at=historical.activity_at,
            activity_time_authority=historical.activity_time_authority,
            actor_execution_ref=None,
        )


def test_owner_generation_cannot_precede_historical_member() -> None:
    _, horizons, outcomes, _ = make_closure()
    historical = cast(
        WorkflowIssueActivityMemberV1,
        next(
            item
            for item in outcomes
            if isinstance(item, WorkflowIssueActivityMemberV1)
            and item.authority_generation == 1
        ),
    )
    observed = horizons[0].owner_observation
    owner = derive_workflow_issue_activity_owner_observation(
        authority_kind=observed.authority_kind,
        authority_ref=observed.authority_ref,
        authority_generation=0,
        authority_receipt_ref=observed.authority_receipt_ref,
        store_generation=observed.store_generation,
        journal_epoch=observed.journal_epoch,
        earliest_cursor=observed.earliest_cursor,
        latest_cursor=observed.latest_cursor,
        next_cursor=observed.next_cursor,
    )
    with pytest.raises(WorkflowIssueActivityObservationError):
        derive_workflow_issue_activity_member(
            owner_observation=owner,
            issue_snapshot=historical.issue_snapshot,
            event=historical.event,
            activity_at=historical.activity_at,
            activity_time_authority=historical.activity_time_authority,
            actor_execution_ref=None,
        )


def test_reordered_complete_closure_rejects() -> None:
    heads, horizons, outcomes, selections = make_closure()
    with pytest.raises(WorkflowIssueActivityObservationError):
        validate_workflow_issue_activity_observation_closure(
            heads=heads,
            horizons=horizons,
            outcomes=tuple(reversed(outcomes)),
            selections=selections,
        )
