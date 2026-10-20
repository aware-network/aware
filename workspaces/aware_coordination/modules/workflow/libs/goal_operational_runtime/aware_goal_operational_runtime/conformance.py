from __future__ import annotations

from dataclasses import dataclass

from .authority import GoalOperationalAuthority
from .contracts import (
    ActorEvidence,
    AppendGoalLaneIssueIntent,
    EnsureGoalIntent,
    EnsureGoalLaneIntent,
    GoalLaneIssueTick,
    GoalLaneStatus,
    GoalStatus,
    IntentContext,
    LinkGoalLaneIssueIntent,
    SyncGoalLaneIssueIntent,
    TransitionOutcome,
)
from .host import HostOutcome, HostResult
from .identity import nonnegative, required_text, required_token
from .observation import (
    GoalObservationQuery,
    ObservationDepth,
    ObservationOutcome,
)
from .persistence import ReplayOutcome
from .reconciliation import (
    PrepareGoalReconciliationIntent,
    ReconciliationStatus,
)


@dataclass(frozen=True, slots=True)
class GoalOperationalConformanceFixture:
    """One already-admitted authority isolated for a destructive proof run."""

    authority: GoalOperationalAuthority
    authority_ref: str
    epoch: str
    actor_evidence: ActorEvidence
    authority_generation: int = 0

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        required_token(self.epoch, "epoch")
        if not isinstance(self.actor_evidence, ActorEvidence):
            raise TypeError("actor_evidence must be ActorEvidence")
        nonnegative(self.authority_generation, "authority_generation")


@dataclass(frozen=True, slots=True)
class GoalOperationalConformanceCheck:
    key: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        required_token(self.key, "key")
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be bool")
        required_text(self.detail, "detail")


@dataclass(frozen=True, slots=True)
class GoalOperationalConformanceReport:
    authority_ref: str
    checks: tuple[GoalOperationalConformanceCheck, ...]
    receipt_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required_token(self.authority_ref, "authority_ref")
        if len({check.key for check in self.checks}) != len(self.checks):
            raise ValueError("conformance check keys must be unique")
        for receipt_ref in self.receipt_refs:
            required_token(receipt_ref, "receipt_ref")

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    @property
    def failed_check_keys(self) -> tuple[str, ...]:
        return tuple(check.key for check in self.checks if not check.passed)


def run_goal_operational_authority_conformance(
    fixture: GoalOperationalConformanceFixture,
) -> GoalOperationalConformanceReport:
    """Exercise the minimum semantic rail every canonical adapter must preserve."""

    checks: list[GoalOperationalConformanceCheck] = []
    receipts: list[str] = []

    def passed(key: str, detail: str) -> None:
        checks.append(GoalOperationalConformanceCheck(key, True, detail))

    def failed(key: str, detail: str) -> GoalOperationalConformanceReport:
        checks.append(GoalOperationalConformanceCheck(key, False, detail))
        return GoalOperationalConformanceReport(
            fixture.authority_ref,
            tuple(checks),
            tuple(receipts),
        )

    def context(intent_key: str) -> IntentContext:
        return IntentContext(
            client_intent_id=f"conformance:{intent_key}",
            expected_authority_generation=fixture.authority_generation,
            actor_evidence=fixture.actor_evidence,
        )

    authority = fixture.authority
    authority_ref = fixture.authority_ref
    try:
        goal_intent = EnsureGoalIntent(
            context("ensure-goal"),
            tag="goal/2000-01-01/authority-conformance-v0",
            title="Goal operational authority conformance",
        )
        goal = authority.submit(authority_ref, goal_intent)
        goal_ref = _applied_ref(goal, "goal")
        if goal_ref is None or goal.receipt is None:
            return failed("ensure_goal", _result_detail(goal))
        receipts.append(goal.receipt.receipt_ref)
        passed("ensure_goal", "applied with a durable receipt")

        retry = authority.submit(authority_ref, goal_intent)
        if (
            retry.outcome is not HostOutcome.COMPLETED
            or retry.transition is None
            or retry.transition.outcome is not TransitionOutcome.IDEMPOTENT
            or retry.receipt != goal.receipt
        ):
            return failed("idempotent_retry", _result_detail(retry))
        passed("idempotent_retry", "returned the exact original receipt")

        lane = authority.submit(
            authority_ref,
            EnsureGoalLaneIntent(
                context("ensure-lane"),
                goal_ref=goal_ref,
                expected_goal_revision=0,
                lane_key="canonical-parity",
                status=GoalLaneStatus.ACTIVE,
            ),
        )
        lane_ref = _applied_ref(lane, "lane")
        if lane_ref is None or lane.receipt is None:
            return failed("ensure_lane", _result_detail(lane))
        receipts.append(lane.receipt.receipt_ref)
        passed("ensure_lane", "applied at the expected Goal revision")

        row = authority.submit(
            authority_ref,
            AppendGoalLaneIssueIntent(
                context("append-row"),
                goal_ref=goal_ref,
                lane_ref=lane_ref,
                expected_lane_revision=0,
                expected_head_row_ref=None,
                row_key="conformance-row",
                gate="The common authority semantics pass.",
                planned_issue_tag="fb/2000-01-01/conformance-v0",
                owner_execution_id="execution:conformance",
            ),
        )
        row_ref = _applied_ref(row, "row")
        if row_ref is None or row.receipt is None:
            return failed("append_row", _result_detail(row))
        receipts.append(row.receipt.receipt_ref)
        passed("append_row", "claimed the exact empty lane head")

        stale = authority.submit(
            authority_ref,
            AppendGoalLaneIssueIntent(
                context("stale-row"),
                goal_ref=goal_ref,
                lane_ref=lane_ref,
                expected_lane_revision=0,
                expected_head_row_ref=None,
                row_key="stale-row",
                gate="This stale append must not persist.",
            ),
        )
        if (
            stale.transition is None
            or stale.transition.outcome is not TransitionOutcome.STALE
            or stale.transition.actual_head_row_ref != row_ref
            or stale.receipt is not None
        ):
            return failed("stale_head_rejection", _result_detail(stale))
        passed("stale_head_rejection", "reported the actual head without a receipt")

        linked = authority.submit(
            authority_ref,
            LinkGoalLaneIssueIntent(
                context("link-issue"),
                goal_ref=goal_ref,
                lane_ref=lane_ref,
                row_ref=row_ref,
                expected_lane_revision=1,
                expected_row_revision=0,
                issue_ref="issue-instance:conformance",
                issue_authority_receipt_ref="issue-operation-receipt:conformance-open",
            ),
        )
        if _applied_ref(linked, "row") != row_ref or linked.receipt is None:
            return failed("link_issue", _result_detail(linked))
        receipts.append(linked.receipt.receipt_ref)
        passed("link_issue", "preserved distinct Issue authority evidence")

        synced = authority.submit(
            authority_ref,
            SyncGoalLaneIssueIntent(
                context("sync-issue"),
                goal_ref=goal_ref,
                lane_ref=lane_ref,
                row_ref=row_ref,
                expected_lane_revision=2,
                expected_row_revision=1,
                issue_ref="issue-instance:conformance",
                issue_observation_ref="issue-observation:conformance-closed",
                status_snapshot="Closed",
                tick=GoalLaneIssueTick.COMPLETE,
                owner_execution_id=None,
                receipt_ref="repository-revision:conformance",
            ),
        )
        if _applied_ref(synced, "row") != row_ref or synced.receipt is None:
            return failed("sync_issue", _result_detail(synced))
        receipts.append(synced.receipt.receipt_ref)
        passed("sync_issue", "completed only the linked row snapshot")

        reconciled = authority.reconcile(
            authority_ref,
            PrepareGoalReconciliationIntent(
                context("prepare-reconciliation"),
                expected_reconciliation_revision=0,
                canonical_authority_ref="goal-authority:canonical-conformance",
                evidence_ref="mapping-proposal:conformance",
            ),
        )
        if (
            reconciled.outcome is not HostOutcome.COMPLETED
            or reconciled.reconciliation is None
            or reconciled.reconciliation.outcome is not TransitionOutcome.APPLIED
            or reconciled.reconciliation.state.status
            is not ReconciliationStatus.PREPARED
            or reconciled.receipt is None
        ):
            return failed("prepare_reconciliation", _result_detail(reconciled))
        receipts.append(reconciled.receipt.receipt_ref)
        passed(
            "prepare_reconciliation",
            "persisted an explicit canonical mapping proposal",
        )

        observed = authority.observe(
            authority_ref,
            GoalObservationQuery(
                ObservationDepth.ROW,
                goal_ref=goal_ref,
                lane_ref=lane_ref,
                row_ref=row_ref,
            ),
        )
        if (
            observed is None
            or observed.outcome is not ObservationOutcome.FOUND
            or observed.goal is None
            or observed.row is None
            or observed.row.tick is not GoalLaneIssueTick.COMPLETE
            or observed.row.owner_execution_id is not None
        ):
            return failed("exact_observation", "exact completed row was not observed")
        passed("exact_observation", "resolved exact Goal, lane, and row coordinates")

        if observed.goal.status is not GoalStatus.PROPOSED:
            return failed(
                "no_implicit_goal_achievement",
                f"Goal status changed to {observed.goal.status.value}",
            )
        passed(
            "no_implicit_goal_achievement",
            "Issue closure left Goal achievement explicit",
        )

        replay = authority.replay(
            authority_ref,
            epoch=fixture.epoch,
            after_cursor=0,
        )
        expected_cursors = tuple(range(1, len(receipts) + 1))
        if (
            replay is None
            or replay.outcome is not ReplayOutcome.EVENTS
            or tuple(event.cursor for event in replay.events) != expected_cursors
            or tuple(event.receipt_ref for event in replay.events) != tuple(receipts)
        ):
            return failed(
                "ordered_replay", "journal did not replay exact applied receipts"
            )
        passed("ordered_replay", "replayed only persisted effects in cursor order")

        record = authority.read(authority_ref)
        if (
            record is None
            or record.state.goal_by_ref(goal_ref) != observed.goal
            or record.reconciliation.status is not ReconciliationStatus.PREPARED
        ):
            return failed("durable_read", "read did not match the exact observation")
        passed(
            "durable_read",
            "matched the observed Goal and prepared reconciliation snapshots",
        )
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError) as error:
        return failed("unexpected_exception", f"{type(error).__name__}: {error}")

    return GoalOperationalConformanceReport(
        authority_ref,
        tuple(checks),
        tuple(receipts),
    )


def _applied_ref(result: HostResult, coordinate: str) -> str | None:
    transition = result.transition
    if (
        result.outcome is not HostOutcome.COMPLETED
        or transition is None
        or transition.outcome is not TransitionOutcome.APPLIED
    ):
        return None
    value = getattr(transition, f"{coordinate}_ref", None)
    return value if isinstance(value, str) else None


def _result_detail(result: HostResult) -> str:
    transition = result.transition
    transition_outcome = None if transition is None else transition.outcome.value
    return (
        f"host={result.outcome.value}; transition={transition_outcome}; "
        f"blocker={result.blocker_code}"
    )
