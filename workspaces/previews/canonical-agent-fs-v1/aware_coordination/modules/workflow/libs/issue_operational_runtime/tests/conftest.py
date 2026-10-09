from __future__ import annotations

import pytest
from aware_issue_operational_runtime import (
    ActorEvidence,
    AuthorityKind,
    IssueAuthorityEvidence,
    IssueIntentContext,
    IssueOperationalState,
    ReconciliationState,
    ReconciliationStatus,
)


@pytest.fixture
def actor() -> ActorEvidence:
    return ActorEvidence("human:local", "evidence:human-admission")


@pytest.fixture
def state() -> IssueOperationalState:
    return IssueOperationalState(
        authority=IssueAuthorityEvidence(
            kind=AuthorityKind.LOCAL_OPERATIONAL,
            provider_key="workflow_issue_operational_runtime",
            authority_ref="issue-authority:repository-example",
            generation=0,
            reconciliation=ReconciliationState(ReconciliationStatus.UNMAPPED),
        )
    )


def context(
    actor: ActorEvidence,
    client_id: str,
    *,
    issue_revision: int | None,
    authority_generation: int = 0,
) -> IssueIntentContext:
    return IssueIntentContext(
        client_intent_id=client_id,
        expected_issue_revision=issue_revision,
        expected_authority_generation=authority_generation,
        actor_evidence=actor,
    )
