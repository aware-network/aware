from __future__ import annotations

import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from aware_goal_operational_runtime import (
    ActorEvidence,
    GoalAuthorityEvidence,
    GoalAuthorityKind,
    GoalOperationalState,
    IntentContext,
)


@pytest.fixture
def actor() -> ActorEvidence:
    return ActorEvidence(
        actor_ref="actor:goal-tests",
        evidence_ref="identity-receipt:goal-tests",
    )


@pytest.fixture
def state() -> GoalOperationalState:
    return GoalOperationalState(
        authority=GoalAuthorityEvidence(
            kind=GoalAuthorityKind.DETERMINISTIC_FIXTURE,
            provider_key="goal-tests",
            authority_ref="goal-authority:test",
            generation=0,
        )
    )


def context(
    actor: ActorEvidence,
    intent: str,
    *,
    generation: int = 0,
) -> IntentContext:
    return IntentContext(
        client_intent_id=f"intent:{intent}",
        expected_authority_generation=generation,
        actor_evidence=actor,
    )
