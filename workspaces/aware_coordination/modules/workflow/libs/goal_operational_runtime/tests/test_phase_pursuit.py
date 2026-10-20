from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import cast

import pytest

from aware_goal_operational_runtime import (
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV4,
    GoalPhaseNativeDocumentV2,
    GoalPhaseDependency,
    GoalDependencyRelation,
    GoalLanePhaseWorkRole,
    GoalPhaseExecutionAuthorityV1,
    GoalNativeLaneAuthorityV1,
    GoalPhasePursuitError,
    GoalPhaseRevisionLineageV1,
    GoalPhaseSourceBindingV1,
    decode_goal_phase_native_observation,
    decode_goal_phase_pursuit,
    decode_goal_phase_pursuit_currentness,
    encode_goal_phase_native_observation,
    encode_goal_phase_pursuit,
    encode_goal_phase_pursuit_currentness,
    issue_goal_phase_pursuit,
    observe_goal_phase_native_document,
    encode_goal_phase_native_document,
    plan_goal_phase_native_admission,
    plan_goal_phase_native_dependency_addition,
    make_goal_phase_future_schedule,
    verify_goal_phase_pursuit_currentness,
)


def _document(*, source: bytes = b"goal-v1", promise: str = "Accept G2.") -> GoalPhaseNativeDocumentV1:
    coordinate = GoalPhaseCoordinate("goal/actorworld", "goal-ontology-object-runtime", "g2")
    return GoalPhaseNativeDocumentV1(
        goal_tag=coordinate.goal_tag,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(source).hexdigest(),
        compatibility_projection_byte_count=len(source),
        definitions=(
            GoalLanePhaseDefinitionV1(
                coordinate=coordinate,
                ordinal=2,
                title=None,
                intent=None,
                gate=GoalLanePhaseGate(
                    gate_key="legacy-gate",
                    promise=promise,
                    gate_contract_ref="aware.goal.phase-gate.profile/legacy_text_v1",
                    evidence_schema_ref="aware.goal.phase-gate-evidence/unavailable_v1",
                    invariant_refs=(
                        "invariant:issue-closure-does-not-accept-phase",
                        "invariant:legacy-lifecycle-is-source-snapshot",
                    ),
                ),
            ),
        ),
        operational_bundle=GoalPhaseContractBundleV1((), ()),
        unresolved_dependencies=(),
        source_refs=("repository-path:actorworld.md",),
    )


def _source(seed: str = "1") -> GoalPhaseSourceBindingV1:
    return GoalPhaseSourceBindingV1(
        repository_revision_ref=seed * 40,
        goal_sha256="sha256:" + seed * 64,
        goal_blob_oid=seed * 40,
    )


def _v4_document() -> GoalPhaseNativeDocumentV4:
    prior = _document()
    return GoalPhaseNativeDocumentV4(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions, operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs,
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
        native_lane_authorities=(GoalNativeLaneAuthorityV1(
            goal_tag=prior.goal_tag, lane_key="goal-ontology-object-runtime",
            role="Ontology", owner_profile="provider_execution_v1",
            owner_ref="codex-reader", operational_state="planned",
            state_detail=None, hold_authority_refs=(), current_work_association_ref=None,
        ),),
        operation_journal_profile="none",
    )


def test_v4_observation_and_pursuit_bind_complete_native_lane_carrier() -> None:
    document = _v4_document()
    source = _source()
    observation = observe_goal_phase_native_document(document=document, source=source)
    assert decode_goal_phase_native_observation(
        encode_goal_phase_native_observation(observation), document=document, source=source
    ) == observation
    receipt = issue_goal_phase_pursuit(
        document=document, coordinate=document.definitions[0].coordinate,
        source=source, expected_document_ref=document.document_ref,
    )
    assert decode_goal_phase_pursuit(
        encode_goal_phase_pursuit(receipt), document=document, source=source
    ) == receipt
    changed = replace(document, native_lane_authorities=(
        replace(document.native_lane_authorities[0], owner_ref="codex-other"),
    ))
    # Neither structural decoding nor direction grants lane eligibility.
    with pytest.raises(GoalPhasePursuitError):
        decode_goal_phase_native_observation(
            encode_goal_phase_native_observation(observation), document=changed, source=source
        )
    with pytest.raises(GoalPhasePursuitError):
        decode_goal_phase_pursuit(
            encode_goal_phase_pursuit(receipt), document=changed, source=source
        )
    currentness = verify_goal_phase_pursuit_currentness(
        expected=receipt, observed_document=changed, observed_source=source,
        revision_lineage=_lineage(source, source),
    )
    assert currentness.status == "stale"
    assert "document_advanced" in currentness.reasons


@pytest.mark.parametrize("operation", ["admit", "dependency", "schedule"])
def test_v4_reader_support_does_not_enable_unsupported_v2_writers(operation: str) -> None:
    document = _v4_document()
    before = encode_goal_phase_native_document(document)
    definition = document.definitions[0]
    # A type cast is not a carrier downgrade. Every old entrance must check
    # the actual type before constructing a postimage or publication plan.
    v2 = cast(GoalPhaseNativeDocumentV2, document)
    if operation == "admit":
        with pytest.raises(TypeError, match="document must be a native Goal document"):
            plan_goal_phase_native_admission(
                document=v2, coordinate=replace(definition.coordinate, phase_key="new-phase"),
                ordinal=3, title="New", intent="New forward work.", gate=definition.gate,
                issue_ref="fb/2026-10-01/new-work", work_role=GoalLanePhaseWorkRole.IMPLEMENTATION,
                admitted_at="2026-10-01T00:00:00Z", work_evidence_refs=("evidence:new-work",),
                dependencies=(), evidence_refs=("evidence:admission",), source_refs=document.source_refs,
            )
    elif operation == "dependency":
        dependency = GoalPhaseDependency(
            owner_goal_tag=document.goal_tag, dependency_key="new-edge",
            dependent=definition.coordinate,
            prerequisite=replace(definition.coordinate, phase_key="other-phase"),
            required_gate_digest=definition.gate.gate_digest,
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            reason="Require separately accepted work.", evidence_refs=("evidence:edge",),
        )
        with pytest.raises(TypeError, match="dependency addition requires exact V2 authority"):
            plan_goal_phase_native_dependency_addition(document=v2, dependency=dependency)
    else:
        with pytest.raises(TypeError, match="schedule requires V2 Goal authority"):
            make_goal_phase_future_schedule(
                document=v2, goal_doc_path="docs/goals/actorworld.md",
                lane_key=definition.coordinate.lane_key, authored_order=(definition.coordinate.phase_key,),
                decision_issue_path="docs/issues/decision.md", decision_issue_blob_oid="1" * 40,
            )
    assert encode_goal_phase_native_document(document) == before


def _pursuit(document: GoalPhaseNativeDocumentV1 | None = None):
    document = _document() if document is None else document
    return issue_goal_phase_pursuit(
        document=document,
        coordinate=document.definitions[0].coordinate,
        source=_source(),
        expected_document_ref=document.document_ref,
    )


def _lineage(
    expected: GoalPhaseSourceBindingV1,
    observed: GoalPhaseSourceBindingV1,
    relation: str = "equal",
) -> GoalPhaseRevisionLineageV1:
    return GoalPhaseRevisionLineageV1(
        expected_revision_ref=expected.repository_revision_ref,
        observed_revision_ref=observed.repository_revision_ref,
        relation=relation,
    )


def test_phase_pursuit_round_trips_against_exact_document() -> None:
    document = _document()
    pursuit = _pursuit(document)
    assert decode_goal_phase_pursuit(
        encode_goal_phase_pursuit(pursuit), document=document, source=_source()
    ) == pursuit


def test_phase_pursuit_decoder_rejects_unknown_and_boolean_ordinal() -> None:
    document = _document()
    raw = json.loads(encode_goal_phase_pursuit(_pursuit(document)))
    raw["unknown"] = True
    with pytest.raises(GoalPhasePursuitError):
        decode_goal_phase_pursuit(
            json.dumps(raw).encode(), document=document, source=_source()
        )
    raw.pop("unknown")
    raw["ordinal"] = True
    with pytest.raises(GoalPhasePursuitError):
        decode_goal_phase_pursuit(
            json.dumps(raw).encode(), document=document, source=_source()
        )


def test_phase_pursuit_decoder_rejects_self_attested_source() -> None:
    document = _document()
    forged = issue_goal_phase_pursuit(
        document=document,
        coordinate=document.definitions[0].coordinate,
        source=_source("2"),
        expected_document_ref=document.document_ref,
    )
    with pytest.raises(GoalPhasePursuitError, match="canonical"):
        decode_goal_phase_pursuit(
            encode_goal_phase_pursuit(forged),
            document=document,
            source=_source(),
        )


def test_currentness_is_exact_and_strictly_decodable() -> None:
    document = _document()
    pursuit = _pursuit(document)
    current = verify_goal_phase_pursuit_currentness(
        expected=pursuit,
        observed_document=document,
        observed_source=_source(),
        revision_lineage=_lineage(pursuit.source, _source()),
    )
    assert current.status == "current"
    assert decode_goal_phase_pursuit_currentness(
        encode_goal_phase_pursuit_currentness(current),
        expected=pursuit,
        observed_document=document,
        observed_source=_source(),
        revision_lineage=_lineage(pursuit.source, _source()),
    ) == current
    forged = json.loads(encode_goal_phase_pursuit_currentness(current))
    forged["projection_currentness"] = "advanced"
    forged["replay_disposition"] = "reobserved_unchanged"
    with pytest.raises(GoalPhasePursuitError, match="canonical"):
        decode_goal_phase_pursuit_currentness(
            json.dumps(forged).encode(),
            expected=pursuit,
            observed_document=document,
            observed_source=_source(),
            revision_lineage=_lineage(pursuit.source, _source()),
        )


def test_compatibility_only_advancement_requires_fresh_pursuit() -> None:
    expected = _pursuit()
    advanced = _document(source=b"goal-v2")
    currentness = verify_goal_phase_pursuit_currentness(
        expected=expected,
        observed_document=advanced,
        observed_source=_source("2"),
        revision_lineage=_lineage(expected.source, _source("2"), "descendant"),
    )
    assert currentness.status == "stale"
    assert "document_advanced" in currentness.reasons


def test_unrelated_repository_advance_preserves_direction_currentness() -> None:
    document = _document()
    expected = _pursuit(document)
    observed_source = GoalPhaseSourceBindingV1(
        repository_revision_ref="2" * 40,
        goal_sha256=expected.source.goal_sha256,
        goal_blob_oid=expected.source.goal_blob_oid,
    )
    currentness = verify_goal_phase_pursuit_currentness(
        expected=expected,
        observed_document=document,
        observed_source=observed_source,
        revision_lineage=_lineage(expected.source, observed_source, "descendant"),
    )
    assert currentness.status == "current"
    assert currentness.projection_currentness == "advanced"
    assert currentness.replay_disposition == "reobserved_unchanged"


def test_unproven_revision_lineage_is_ambiguous_and_refuses_replay() -> None:
    document = _document()
    expected = _pursuit(document)
    observed_source = GoalPhaseSourceBindingV1(
        repository_revision_ref="2" * 40,
        goal_sha256=expected.source.goal_sha256,
        goal_blob_oid=expected.source.goal_blob_oid,
    )
    currentness = verify_goal_phase_pursuit_currentness(
        expected=expected,
        observed_document=document,
        observed_source=observed_source,
        revision_lineage=_lineage(expected.source, observed_source, "unproven"),
    )
    assert currentness.status == "ambiguous"
    assert currentness.projection_currentness == "unproven"
    assert currentness.replay_disposition == "refuse"
    assert currentness.reasons == ("source_revision_lineage_unproven",)


def test_gate_change_is_stale() -> None:
    expected = _pursuit()
    changed = _document(promise="Different Gate.")
    currentness = verify_goal_phase_pursuit_currentness(
        expected=expected,
        observed_document=changed,
        observed_source=_source(),
        revision_lineage=_lineage(expected.source, _source()),
    )
    assert "definition_changed" in currentness.reasons
    assert "gate_changed" in currentness.reasons


@pytest.mark.parametrize("length", (39, 41, 63, 65))
def test_source_binding_rejects_unsupported_blob_lengths(length: int) -> None:
    with pytest.raises(GoalPhasePursuitError, match="Git blob identity"):
        GoalPhaseSourceBindingV1(
            repository_revision_ref="1" * 40,
            goal_sha256="sha256:" + "1" * 64,
            goal_blob_oid="1" * length,
        )


@pytest.mark.parametrize("length", (40, 64))
def test_source_binding_accepts_supported_blob_lengths(length: int) -> None:
    source = GoalPhaseSourceBindingV1(
        repository_revision_ref="1" * 40,
        goal_sha256="sha256:" + "1" * 64,
        goal_blob_oid="1" * length,
    )
    assert len(source.goal_blob_oid) == length


def test_native_observation_round_trips_and_rejects_forged_reference() -> None:
    observation = observe_goal_phase_native_document(
        document=_document(), source=_source()
    )
    payload = encode_goal_phase_native_observation(observation)
    assert decode_goal_phase_native_observation(
        payload, document=observation.document, source=_source()
    ) == observation
    raw = json.loads(payload)
    raw["observation_ref"] = "goal-phase-native-observation:sha256:" + "0" * 64
    with pytest.raises(GoalPhasePursuitError, match="canonical"):
        decode_goal_phase_native_observation(
            json.dumps(raw).encode(),
            document=observation.document,
            source=_source(),
        )


def test_native_observation_decoder_rejects_self_attested_authority() -> None:
    document = _document()
    forged_source = observe_goal_phase_native_document(
        document=document, source=_source("2")
    )
    with pytest.raises(GoalPhasePursuitError, match="canonical"):
        decode_goal_phase_native_observation(
            encode_goal_phase_native_observation(forged_source),
            document=document,
            source=_source(),
        )

    forged_document = observe_goal_phase_native_document(
        document=_document(source=b"goal-v2"), source=_source()
    )
    with pytest.raises(GoalPhasePursuitError, match="canonical"):
        decode_goal_phase_native_observation(
            encode_goal_phase_native_observation(forged_document),
            document=document,
            source=_source(),
        )
