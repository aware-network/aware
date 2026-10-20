from __future__ import annotations

from aware_goal_operational_runtime import (
    GoalOperationalAuthority,
    GoalOperationalConformanceFixture,
    GoalOperationalRuntimeHost,
    InMemoryGoalStateStore,
    run_goal_operational_authority_conformance,
)


def test_neutral_host_satisfies_operational_authority_conformance(actor, state) -> None:
    host = GoalOperationalRuntimeHost(InMemoryGoalStateStore())
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-conformance")
    assert isinstance(host, GoalOperationalAuthority)

    report = run_goal_operational_authority_conformance(
        GoalOperationalConformanceFixture(
            authority=host,
            authority_ref=authority_ref,
            epoch="epoch-conformance",
            actor_evidence=actor,
        )
    )

    assert report.passed, report.failed_check_keys
    assert tuple(check.key for check in report.checks) == (
        "ensure_goal",
        "idempotent_retry",
        "ensure_lane",
        "append_row",
        "stale_head_rejection",
        "link_issue",
        "sync_issue",
        "prepare_reconciliation",
        "exact_observation",
        "no_implicit_goal_achievement",
        "ordered_replay",
        "durable_read",
    )
    assert len(report.receipt_refs) == 6
    assert len(set(report.receipt_refs)) == 6
