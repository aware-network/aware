from aware_issue_operational_runtime import (
    AcceptAuthorityMappingIntent,
    PrepareAuthorityReconciliationIntent,
    ReconciliationStatus,
    TransitionOutcome,
    apply_issue_intent,
)
from conftest import context


def test_local_authority_mapping_is_prepare_then_accept(actor, state) -> None:
    prepared = apply_issue_intent(
        state,
        PrepareAuthorityReconciliationIntent(
            context(actor, "prepare", issue_revision=None),
            "canonical:workflow-repository",
        ),
    )
    assert prepared.outcome is TransitionOutcome.APPLIED
    assert prepared.state.authority.generation == 1
    accepted = apply_issue_intent(
        prepared.state,
        AcceptAuthorityMappingIntent(
            context(
                actor,
                "accept",
                issue_revision=None,
                authority_generation=1,
            ),
            "canonical:workflow-repository",
            "receipt:canonical-mapping",
        ),
    )
    reconciliation = accepted.state.authority.reconciliation
    assert reconciliation is not None
    assert reconciliation.status is ReconciliationStatus.MAPPED
    assert reconciliation.evidence_ref == "receipt:canonical-mapping"
