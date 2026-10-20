from __future__ import annotations

from conftest import context

from aware_goal_operational_runtime import (
    AcceptGoalReconciliationIntent,
    GoalOperationalRuntimeHost,
    GoalReconciliationState,
    InMemoryGoalStateStore,
    PrepareGoalReconciliationIntent,
    ReconciliationStatus,
    RejectGoalReconciliationIntent,
    TransitionOutcome,
    apply_reconciliation_intent,
)


def test_reconciliation_requires_prepare_then_explicit_accept(actor) -> None:
    initial = GoalReconciliationState()
    prepare_intent = PrepareGoalReconciliationIntent(
        context(actor, "prepare"),
        expected_reconciliation_revision=0,
        canonical_authority_ref="goal-authority:canonical",
        evidence_ref="mapping-proposal:one",
    )
    prepared = apply_reconciliation_intent(
        initial,
        prepare_intent,
        authority_generation=0,
    )
    accepted = apply_reconciliation_intent(
        prepared.state,
        AcceptGoalReconciliationIntent(
            context(actor, "accept"),
            expected_reconciliation_revision=1,
            canonical_authority_ref="goal-authority:canonical",
            evidence_ref="mapping-acceptance:one",
        ),
        authority_generation=0,
    )
    assert prepared.state.status is ReconciliationStatus.PREPARED
    assert accepted.outcome is TransitionOutcome.APPLIED
    assert accepted.state.status is ReconciliationStatus.ACCEPTED


def test_reconciliation_reject_is_reasoned_and_intent_reuse_conflicts(actor) -> None:
    prepared = apply_reconciliation_intent(
        GoalReconciliationState(),
        PrepareGoalReconciliationIntent(
            context(actor, "prepare-reject"),
            expected_reconciliation_revision=0,
            canonical_authority_ref="goal-authority:canonical",
            evidence_ref="mapping-proposal:reject",
        ),
        authority_generation=0,
    )
    rejected = apply_reconciliation_intent(
        prepared.state,
        RejectGoalReconciliationIntent(
            context(actor, "reject"),
            expected_reconciliation_revision=1,
            reason="Canonical evidence does not match.",
        ),
        authority_generation=0,
    )
    reused = apply_reconciliation_intent(
        rejected.state,
        RejectGoalReconciliationIntent(
            context(actor, "reject"),
            expected_reconciliation_revision=2,
            reason="Changed payload.",
        ),
        authority_generation=0,
    )
    assert rejected.state.status is ReconciliationStatus.REJECTED
    assert rejected.state.reason == "Canonical evidence does not match."
    assert reused.outcome is TransitionOutcome.CONFLICT
    assert reused.blocker_code == "client_intent_id_reused"


def test_host_persists_reconciliation_and_restart_idempotency(actor, state) -> None:
    store = InMemoryGoalStateStore()
    host = GoalOperationalRuntimeHost(store)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    intent = PrepareGoalReconciliationIntent(
        context(actor, "host-prepare"),
        expected_reconciliation_revision=0,
        canonical_authority_ref="goal-authority:canonical",
        evidence_ref="mapping-proposal:host",
    )
    first = host.reconcile(authority_ref, intent)
    replay = GoalOperationalRuntimeHost(store).reconcile(authority_ref, intent)
    current = host.read(authority_ref)
    assert first.receipt is not None and replay.receipt == first.receipt
    assert replay.reconciliation is not None
    assert replay.reconciliation.outcome is TransitionOutcome.IDEMPOTENT
    assert current is not None
    assert current.reconciliation.status is ReconciliationStatus.PREPARED
    assert current.state.goals == ()
