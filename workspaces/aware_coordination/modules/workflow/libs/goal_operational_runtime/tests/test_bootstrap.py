from __future__ import annotations

from dataclasses import replace

import pytest
from aware_goal_operational_runtime import (
    ActorEvidence,
    EnsureGoalIntent,
    GoalObservationQuery,
    IntentContext,
    ObservationDepth,
)
from aware_goal_operational_runtime.bootstrap import (
    CommittedGoalBootstrapSource,
    GoalOperationalBootstrapPlan,
    decode_goal_operational_bootstrap_plan,
    encode_goal_operational_bootstrap_plan,
)


def _source() -> CommittedGoalBootstrapSource:
    return CommittedGoalBootstrapSource(
        repository_revision="a" * 40,
        goal_path="docs/goals/2026/09/10/goal-example-v0.md",
        goal_sha256="b" * 64,
        publication_receipt_ref="goal-publication:sha256:source",
    )


def _plan() -> GoalOperationalBootstrapPlan:
    actor = ActorEvidence("actor:luis", "admission:accepted")
    return GoalOperationalBootstrapPlan(
        source=_source(),
        authority_ref="goal-authority:actorworld",
        actor_evidence=actor,
        intents=(
            EnsureGoalIntent(
                IntentContext("bootstrap:goal", 0, actor),
                tag="goal/2026-09-10/example-v0",
                title="Example",
            ),
        ),
        terminal_query=GoalObservationQuery(
            ObservationDepth.GOAL,
            goal_tag="goal/2026-09-10/example-v0",
        ),
    )


def test_bootstrap_plan_digest_is_deterministic() -> None:
    assert _plan().plan_digest == _plan().plan_digest


def test_bootstrap_plan_rejects_unaccepted_or_mixed_actor_evidence() -> None:
    plan = _plan()
    with pytest.raises(ValueError, match="accepted actor evidence"):
        _ = replace(
            plan,
            actor_evidence=ActorEvidence("actor:luis", "admission:rejected", False),
        )
    with pytest.raises(ValueError, match="actor evidence differs"):
        _ = replace(
            plan,
            intents=(
                EnsureGoalIntent(
                    IntentContext(
                        "bootstrap:goal",
                        0,
                        ActorEvidence("actor:other", "admission:other"),
                    ),
                    tag="goal/2026-09-10/example-v0",
                    title="Example",
                ),
            ),
        )


def test_committed_source_requires_exact_sha256() -> None:
    with pytest.raises(ValueError, match="64 lowercase hexadecimal"):
        _ = replace(_source(), goal_sha256="ABC")


def test_bootstrap_plan_portable_codec_is_exact_and_deterministic() -> None:
    encoded = encode_goal_operational_bootstrap_plan(_plan())

    assert decode_goal_operational_bootstrap_plan(encoded) == _plan()
    assert (
        encode_goal_operational_bootstrap_plan(
            decode_goal_operational_bootstrap_plan(encoded)
        )
        == encoded
    )


def test_bootstrap_plan_codec_rejects_extensions_and_tampering() -> None:
    encoded = encode_goal_operational_bootstrap_plan(_plan())
    with pytest.raises(ValueError, match="fields must be exact"):
        _ = decode_goal_operational_bootstrap_plan(
            encoded.replace('"schema":', '"extension":true,"schema":', 1)
        )
    with pytest.raises(ValueError, match="digest mismatch"):
        _ = decode_goal_operational_bootstrap_plan(
            encoded.replace('"title":"Example"', '"title":"Altered"')
        )
    with pytest.raises(ValueError, match="not canonical"):
        _ = decode_goal_operational_bootstrap_plan(encoded + "\n")
