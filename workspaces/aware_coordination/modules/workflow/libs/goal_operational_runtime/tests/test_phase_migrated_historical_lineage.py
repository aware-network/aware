from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from aware_goal_operational_runtime.phase_contracts import GoalPhaseCoordinate
from aware_goal_operational_runtime.phase_migrated_historical_lineage import (
    HistoricalEvaluationReasonV1,
    HistoricalLineageError,
    HistoricalLineageEventV1,
    HistoricalPathOidV1,
    MigratedHistoricalLineageEvaluationV1,
    MigratedHistoricalSourceScopeV1,
    decode_migrated_historical_lineage_evaluation,
    decode_migrated_historical_source_scope,
)
from aware_goal_operational_runtime.phase_migrated_gate_evaluation import EvaluationResult


def _scope() -> MigratedHistoricalSourceScopeV1:
    return MigratedHistoricalSourceScopeV1(
        repository_ref="repository:actorworld",
        goal_path="docs/goals/actorworld.md",
        coordinate=GoalPhaseCoordinate(
            goal_tag="goal/2026-09-10/actorworld-v0",
            lane_key="product-runtime",
            phase_key="d5-2-technical-substrate",
        ),
        definition_ref="goal-phase-definition:sha256:" + "1" * 64,
        gate_digest="sha256:" + "2" * 64,
        implementation_ref="goal-migrated-phase-implementation:sha256:" + "3" * 64,
        lineage_ref="goal-migrated-phase-lineage:sha256:" + "4" * 64,
        reviewed_source_commit="a" * 40,
        original_paths=("docs/issues/implementation.md", "src/implementation.py"),
        additional_gate_paths=("tests/current_proof.py",),
        path_oids=(
            HistoricalPathOidV1("docs/issues/implementation.md", "b" * 40),
            HistoricalPathOidV1("src/implementation.py", "c" * 40),
            HistoricalPathOidV1("tests/current_proof.py", "d" * 40),
        ),
    )


def test_source_scope_is_round_trip_canonical_but_not_authority() -> None:
    scope = _scope()
    assert decode_migrated_historical_source_scope(scope.to_wire()) == scope
    scope.require_committed_original_paths(scope.original_paths)


def test_source_evolution_event_requires_publication_receipt() -> None:
    with pytest.raises(HistoricalLineageError, match="requires repository receipt"):
        _ = HistoricalLineageEventV1(
            commit="a" * 40,
            parent="b" * 40,
            path="src/implementation.py",
            before_blob_oid="c" * 40,
            after_blob_oid="d" * 40,
            role="source_evolution",
            repository_commit_receipt_ref=None,
        )


def test_source_scope_refuses_omitted_original_or_new_gate_path() -> None:
    raw = _scope().to_wire()
    for omitted in ("src/implementation.py", "tests/current_proof.py"):
        forged = deepcopy(raw)
        bindings = cast(list[dict[str, object]], forged["path_oids"])
        forged["path_oids"] = [item for item in bindings if item["path"] != omitted]
        with pytest.raises(HistoricalLineageError, match="closed source union"):
            _ = decode_migrated_historical_source_scope(forged)


def test_source_scope_refuses_caller_substituted_original_path_set() -> None:
    scope = _scope()
    with pytest.raises(HistoricalLineageError, match="path set differs"):
        scope.require_committed_original_paths(("src/implementation.py",))


def test_source_scope_refuses_wrong_oid_type_unknown_field_and_rewritten_ref() -> None:
    raw = _scope().to_wire()
    wrong_type = deepcopy(raw)
    cast(list[dict[str, object]], wrong_type["path_oids"])[0]["blob_oid"] = True
    with pytest.raises(HistoricalLineageError, match="blob_oid"):
        _ = decode_migrated_historical_source_scope(wrong_type)
    unknown = deepcopy(raw)
    unknown["not_authority"] = "yes"
    with pytest.raises(HistoricalLineageError, match="fields differ"):
        _ = decode_migrated_historical_source_scope(unknown)
    forged_ref = deepcopy(raw)
    forged_ref["source_scope_ref"] = "goal-migrated-phase-source-scope:sha256:" + "0" * 64
    with pytest.raises(HistoricalLineageError, match="not canonical"):
        _ = decode_migrated_historical_source_scope(forged_ref)


def test_deleted_original_path_remains_explicitly_in_source_inventory() -> None:
    original = _scope()
    absent = MigratedHistoricalSourceScopeV1(
        repository_ref=original.repository_ref,
        goal_path=original.goal_path,
        coordinate=original.coordinate,
        definition_ref=original.definition_ref,
        gate_digest=original.gate_digest,
        implementation_ref=original.implementation_ref,
        lineage_ref=original.lineage_ref,
        reviewed_source_commit=original.reviewed_source_commit,
        original_paths=original.original_paths,
        additional_gate_paths=original.additional_gate_paths,
        path_oids=(
            HistoricalPathOidV1("docs/issues/implementation.md", "b" * 40),
            HistoricalPathOidV1("src/implementation.py", None),
            HistoricalPathOidV1("tests/current_proof.py", "d" * 40),
        ),
    )
    assert decode_migrated_historical_source_scope(absent.to_wire()) == absent
    assert absent.source_scope_ref != original.source_scope_ref


def _evaluation() -> MigratedHistoricalLineageEvaluationV1:
    return MigratedHistoricalLineageEvaluationV1(
        m14_evaluation_ref="goal-migrated-phase-evaluation:sha256:" + "1" * 64,
        original_implementation_ref="goal-migrated-phase-evidence:sha256:" + "2" * 64,
        source_scope_ref=_scope().source_scope_ref,
        lineage_ref=_scope().lineage_ref,
        proof_publication_binding_ref="goal-migrated-phase-proof-publication:" + "3" * 64,
        review_publication_binding_ref="goal-migrated-phase-review-publication:" + "4" * 64,
        observed_head="a" * 40,
        protected_paths=("docs/goals/actorworld.md", "src/implementation.py"),
        result=EvaluationResult.SATISFIED,
        reasons=(),
        gate_observation_ref="goal-phase-gate-observation:" + "5" * 64,
    )


def test_lineage_evaluation_codec_is_strict_but_not_an_authority_seal() -> None:
    evaluation = _evaluation()
    assert decode_migrated_historical_lineage_evaluation(evaluation.to_wire()) == evaluation
    wrong_type = deepcopy(evaluation.to_wire())
    wrong_type["protected_paths"] = True
    with pytest.raises(HistoricalLineageError):
        decode_migrated_historical_lineage_evaluation(wrong_type)
    tampered = deepcopy(evaluation.to_wire())
    tampered["observed_head"] = "b" * 40
    with pytest.raises(HistoricalLineageError, match="not canonical"):
        decode_migrated_historical_lineage_evaluation(tampered)
    forged_satisfaction = deepcopy(evaluation.to_wire())
    forged_satisfaction["reasons"] = [{"code": "current_proof_stale", "role_key": "current_proof"}]
    with pytest.raises(HistoricalLineageError, match="contradicts reasons"):
        decode_migrated_historical_lineage_evaluation(forged_satisfaction)


def test_rejected_review_cannot_carry_gate_observation() -> None:
    accepted = _evaluation()
    with pytest.raises(HistoricalLineageError, match="negative result"):
        MigratedHistoricalLineageEvaluationV1(
            m14_evaluation_ref=accepted.m14_evaluation_ref,
            original_implementation_ref=accepted.original_implementation_ref,
            source_scope_ref=accepted.source_scope_ref,
            lineage_ref=accepted.lineage_ref,
            proof_publication_binding_ref=accepted.proof_publication_binding_ref,
            review_publication_binding_ref=accepted.review_publication_binding_ref,
            observed_head=accepted.observed_head,
            protected_paths=accepted.protected_paths,
            result=EvaluationResult.REJECTED,
            reasons=(HistoricalEvaluationReasonV1("current_review_rejected", "current_review"),),
            gate_observation_ref=accepted.gate_observation_ref,
        )
