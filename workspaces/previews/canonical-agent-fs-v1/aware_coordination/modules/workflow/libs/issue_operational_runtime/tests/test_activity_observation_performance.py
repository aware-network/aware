from __future__ import annotations

import json
import statistics
import time

from aware_issue_operational_runtime import (
    AuthorityKind,
    IssueAuthorityEvidence,
    IssueEvent,
    IssueEventKind,
    IssueSnapshot,
    IssueStatus,
    IssueTimeAuthority,
    WorkflowIssueActivityMemberV1,
    WorkflowIssueActivitySelectionKind,
    WorkflowIssueActivityUnavailableReason,
    decode_workflow_issue_activity_observation_closure,
    derive_workflow_issue_activity_head,
    derive_workflow_issue_activity_horizon,
    derive_workflow_issue_activity_member,
    derive_workflow_issue_activity_owner_observation,
    derive_workflow_issue_activity_selection,
    derive_workflow_issue_activity_unavailable,
    encode_workflow_issue_activity_observation_closure,
    validate_workflow_issue_activity_observation_closure,
)


def _fixture(count: int):
    heads, horizons, outcomes, selections = [], [], [], []
    for index in range(count):
        auth_ref, issue_ref, epoch = (
            f"authority:{index:04}",
            f"issue:{index:04}",
            f"epoch:{index:04}",
        )
        current_auth = IssueAuthorityEvidence(
            kind=AuthorityKind.CANONICAL_COMMITTED,
            provider_key="fixture",
            authority_ref=auth_ref,
            generation=2,
            receipt_ref=f"receipt:{index}:2",
        )
        current_snapshot = IssueSnapshot(
            issue_ref=issue_ref,
            tag=f"fb/fixture-{index}",
            title=f"Fixture {index}",
            status=IssueStatus.IN_PROGRESS,
            priority_level="p0",
            authority=current_auth,
            revision=2,
        )
        owner = derive_workflow_issue_activity_owner_observation(
            authority_kind=current_auth.kind,
            authority_ref=auth_ref,
            authority_generation=2,
            authority_receipt_ref=current_auth.receipt_ref,
            store_generation=index,
            journal_epoch=epoch,
            earliest_cursor=1,
            latest_cursor=2,
            next_cursor=3,
        )
        head = derive_workflow_issue_activity_head(
            owner_observation=owner, issue_snapshot=current_snapshot
        )
        current_event = IssueEvent(
            event_ref=f"event:{index}:2",
            authority_ref=auth_ref,
            epoch=epoch,
            cursor=2,
            kind=IssueEventKind.LIFECYCLE_CHANGED,
            authority_generation=2,
            issue_ref=issue_ref,
            issue_revision=2,
            receipt_ref=f"event-receipt:{index}:2",
            affected_refs=(issue_ref,),
        )
        current = derive_workflow_issue_activity_member(
            owner_observation=owner,
            issue_snapshot=current_snapshot,
            event=current_event,
            activity_at="2026-09-08T12:00:02Z",
            activity_time_authority=IssueTimeAuthority.COMMIT_RECEIPT,
            actor_execution_ref=None,
        )
        if index % 2 == 0:
            old_auth = IssueAuthorityEvidence(
                kind=AuthorityKind.DETERMINISTIC_FIXTURE,
                provider_key="fixture",
                authority_ref=auth_ref,
                generation=1,
                receipt_ref=f"receipt:{index}:1",
            )
            old_snapshot = IssueSnapshot(
                issue_ref=issue_ref,
                tag=f"fb/fixture-{index}",
                title=f"Old {index}",
                status=IssueStatus.OPEN,
                priority_level="p0",
                authority=old_auth,
                revision=1,
            )
            old_event = IssueEvent(
                event_ref=f"event:{index}:1",
                authority_ref=auth_ref,
                epoch=epoch,
                cursor=1,
                kind=IssueEventKind.ISSUE_ENSURED,
                authority_generation=1,
                issue_ref=issue_ref,
                issue_revision=1,
                receipt_ref=f"event-receipt:{index}:1",
                affected_refs=(issue_ref,),
            )
            second = derive_workflow_issue_activity_member(
                owner_observation=owner,
                issue_snapshot=old_snapshot,
                event=old_event,
                activity_at="2026-09-08T12:00:01Z",
                activity_time_authority=IssueTimeAuthority.SOURCE_OBSERVED,
                actor_execution_ref=None,
            )
        else:
            second = derive_workflow_issue_activity_unavailable(
                owner_observation=owner,
                issue_ref=issue_ref,
                selection_kind=WorkflowIssueActivitySelectionKind.HISTORICAL,
                requested_issue_revision_ref=f"{issue_ref}:revision:1",
                reason=WorkflowIssueActivityUnavailableReason.HISTORY_NOT_RETAINED,
                detail="not retained",
                observed_at="2026-09-08T12:00:03Z",
            )
        local = sorted(
            (current, second),
            key=lambda item: (
                "selected"
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else "unavailable",
                item.activity_ref
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else item.unavailable_ref,
            ),
        )
        horizon = derive_workflow_issue_activity_horizon(
            owner_observation=owner,
            observed_at="2026-09-08T12:00:03Z",
            heads=(head,),
            outcomes=tuple(local),
        )
        heads.append(head)
        horizons.append(horizon)
        outcomes.extend(local)
        selections.extend(
            (
                derive_workflow_issue_activity_selection(
                    horizon=horizon,
                    selection_kind=WorkflowIssueActivitySelectionKind.CURRENT,
                    issue_ref=issue_ref,
                    requested_issue_revision_ref=None,
                    outcome=current,
                ),
                derive_workflow_issue_activity_selection(
                    horizon=horizon,
                    selection_kind=WorkflowIssueActivitySelectionKind.HISTORICAL,
                    issue_ref=issue_ref,
                    requested_issue_revision_ref=f"{issue_ref}:revision:1",
                    outcome=second,
                ),
            )
        )
    heads.sort(
        key=lambda item: (
            item.owner_observation.owner_observation_ref.encode(),
            item.issue_ref.encode(),
        )
    )
    horizons.sort(
        key=lambda item: item.owner_observation.owner_observation_ref.encode()
    )
    outcomes.sort(
        key=lambda item: (
            item.owner_observation.owner_observation_ref.encode(),
            item.issue_ref.encode(),
            (
                "selected"
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else "unavailable"
            ).encode(),
            (
                item.activity_ref
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else item.unavailable_ref
            ).encode(),
        )
    )
    selections.sort(
        key=lambda item: json.dumps(
            [
                item.horizon_ref,
                item.issue_ref,
                item.selection_kind.value,
                item.requested_issue_revision_ref,
            ],
            separators=(",", ":"),
        ).encode()
    )
    return tuple(heads), tuple(horizons), tuple(outcomes), tuple(selections)


def _measure(operation):
    for _ in range(5):
        operation()
    samples = []
    for _ in range(30):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1000)
    return statistics.median(samples), sorted(samples)[28]


def test_representative_and_doubled_performance() -> None:
    results = []
    for count, ceilings in (
        (100, (120, 180, 160, 240, 260, 380)),
        (200, (280, 400, 360, 500, 600, 800)),
    ):
        closure = _fixture(count)
        arguments = {
            "heads": closure[0],
            "horizons": closure[1],
            "outcomes": closure[2],
            "selections": closure[3],
        }
        payload = encode_workflow_issue_activity_observation_closure(**arguments)
        assert len(payload) == (989_621 if count == 100 else 1_982_371)
        timings = (
            _measure(
                lambda arguments=arguments: (
                    validate_workflow_issue_activity_observation_closure(**arguments)
                )
            ),
            _measure(
                lambda arguments=arguments: (
                    encode_workflow_issue_activity_observation_closure(**arguments)
                )
            ),
            _measure(
                lambda payload=payload: (
                    decode_workflow_issue_activity_observation_closure(payload)
                )
            ),
        )
        assert timings[0][0] < ceilings[0] and timings[0][1] < ceilings[1]
        assert timings[1][0] < ceilings[2] and timings[1][1] < ceilings[3]
        assert timings[2][0] < ceilings[4] and timings[2][1] < ceilings[5]
        assert tuple(map(len, closure)) == (count, count, count * 2, count * 2)
        results.append((*timings, len(payload)))
    for operation in range(3):
        assert results[1][operation][0] / results[0][operation][0] < 2.5
