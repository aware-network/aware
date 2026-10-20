from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalLanePhaseDefinitionV1,
    GoalLanePhase,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    GoalNativeLaneAuthorityV1,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    GoalPhaseDependency,
    GoalDependencyRelation,
)
from aware_goal_sdk.native_phase_markdown import (
    END_MARKER,
    START_MARKER,
    GoalPhaseNativeMarkdownError,
    attach_goal_phase_native_document,
    extract_goal_phase_native_document,
    repair_advanced_goal_phase_native_document,
    withdraw_goal_phase_native_dependency,
)


def _source(*, trailing_newline: bool = True) -> bytes:
    text = """# Goal: Carrier test

- Tag: `goal/2026-09-20/carrier-test-v0`

## Lane Sequences

### runtime

| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | m1 | [ ] | Planned | Reviewed | TBD:m1 | TBD | This issue |
"""
    return text.encode() if trailing_newline else text.rstrip("\n").encode()


def _document(
    source: bytes,
    *,
    goal_tag: str = "goal/2026-09-20/carrier-test-v0",
    title: str = "Carrier",
    intent: str = "Preserve authority.",
) -> GoalPhaseNativeDocumentV1:
    coordinate = GoalPhaseCoordinate(
        goal_tag=goal_tag,
        lane_key="runtime",
        phase_key="m1",
    )
    gate = GoalLanePhaseGate(
        gate_key="reviewed",
        promise="Independent review accepts the carrier.",
        gate_contract_ref="aware.goal.gate/reviewed-v1",
        evidence_schema_ref="aware.goal.gate-evidence/reviewed-v1",
    )
    return GoalPhaseNativeDocumentV1(
        goal_tag=coordinate.goal_tag,
        compatibility_projection_sha256=(
            "sha256:" + hashlib.sha256(source).hexdigest()
        ),
        compatibility_projection_byte_count=len(source),
        definitions=(
            GoalLanePhaseDefinitionV1(
                coordinate=coordinate,
                ordinal=1,
                gate=gate,
                title=title,
                intent=intent,
            ),
        ),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/test.md",),
    )


def _dependency_candidate() -> tuple[bytes, bytes, str]:
    key = "runtime-requires-external-proof"
    owner = "goal/2026-09-20/carrier-test-v0"
    declaration = {
        "dependency_key": key,
        "dependent_lane_key": "runtime",
        "dependent_row_key": "m1",
        "prerequisite_goal_tag": "goal/2026-09-20/external-v0",
        "prerequisite_lane_key": "proof",
        "prerequisite_row_key": "p1",
        "relation": "requires_acceptance",
        "reason": "External proof is required.",
        "evidence_refs": ["proof:one"],
    }
    prefix = _source()
    before_compatibility = (
        prefix
        + b"\n## Dependencies\n\n```json\n"
        + json.dumps([declaration], indent=2).encode()
        + b"\n```\n"
    )
    after_compatibility = before_compatibility.replace(
        json.dumps([declaration], indent=2).encode(), b"[]"
    )
    base = _document(before_compatibility)
    dependency = GoalPhaseDependency(
        owner_goal_tag=owner,
        dependency_key=key,
        dependent=base.definitions[0].coordinate,
        prerequisite=GoalPhaseCoordinate(
            goal_tag="goal/2026-09-20/external-v0",
            lane_key="proof",
            phase_key="p1",
        ),
        required_gate_digest="sha256:" + "a" * 64,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="External proof is required.",
        evidence_refs=("proof:one",),
    )
    authority = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:sha256:" + "b" * 64,
        proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "c" * 64,
        coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "d" * 64,
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=base.goal_tag,
        compatibility_projection_sha256=base.compatibility_projection_sha256,
        compatibility_projection_byte_count=base.compatibility_projection_byte_count,
        definitions=base.definitions,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(), dependencies=(dependency,)
        ),
        unresolved_dependencies=(),
        source_refs=base.source_refs,
        execution_authority=authority,
    )
    return (
        attach_goal_phase_native_document(before_compatibility, document),
        after_compatibility,
        key,
    )


def test_v2_dependency_withdrawal_rebinds_both_projections() -> None:
    candidate, corrected, key = _dependency_candidate()
    result, before, after = withdraw_goal_phase_native_dependency(
        candidate=candidate,
        corrected_compatibility=corrected,
        dependency_key=key,
    )
    recovered_compatibility, recovered = extract_goal_phase_native_document(result)
    assert recovered_compatibility == corrected
    assert recovered == after
    assert after.operational_bundle.dependencies == ()
    assert before.operational_bundle.phases == after.operational_bundle.phases
    assert before.definitions == after.definitions
    assert before.source_refs == after.source_refs
    assert before.execution_authority == after.execution_authority


def test_v2_dependency_withdrawal_rejects_wrong_edge_or_extra_delta() -> None:
    candidate, corrected, key = _dependency_candidate()
    with pytest.raises(GoalPhaseNativeMarkdownError):
        withdraw_goal_phase_native_dependency(
            candidate=candidate,
            corrected_compatibility=corrected,
            dependency_key="other-edge",
        )
    with pytest.raises(GoalPhaseNativeMarkdownError):
        withdraw_goal_phase_native_dependency(
            candidate=candidate,
            corrected_compatibility=corrected.replace(b"[]", b"[{}]"),
            dependency_key=key,
        )


@pytest.mark.parametrize("trailing_newline", [True, False])
def test_attach_extract_preserves_exact_compatibility_bytes(
    trailing_newline: bool,
) -> None:
    source = _source(trailing_newline=trailing_newline)
    document = _document(source)
    candidate = attach_goal_phase_native_document(source, document)
    recovered_source, recovered_document = extract_goal_phase_native_document(candidate)
    assert recovered_source == source
    assert recovered_document == document
    assert attach_goal_phase_native_document(source, document) == candidate


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.replace(START_MARKER, START_MARKER + START_MARKER, 1),
        lambda value: value + b"trailing",
        lambda value: b"!" + value[1:],
        lambda value: value.replace(b'"ordinal":1', b'"ordinal":true', 1),
        lambda value: value.replace(END_MARKER, b"<!-- wrong:end -->", 1),
    ],
)
def test_extract_rejects_tampering(mutator) -> None:
    source = _source()
    candidate = attach_goal_phase_native_document(source, _document(source))
    with pytest.raises((GoalPhaseNativeMarkdownError, ValueError)):
        extract_goal_phase_native_document(mutator(candidate))


def test_attach_rejects_existing_markers_and_wrong_binding() -> None:
    source = _source()
    document = _document(source)
    with pytest.raises(GoalPhaseNativeMarkdownError, match="already has markers"):
        attach_goal_phase_native_document(source + START_MARKER, document)
    with pytest.raises(GoalPhaseNativeMarkdownError, match="does not bind"):
        attach_goal_phase_native_document(
            source.replace(b"Carrier test", b"Other title"),
            document,
        )


def test_attach_rejects_different_goal_even_with_matching_bytes() -> None:
    source = _source()
    document = _document(
        source,
        goal_tag="goal/2026-09-20/different-v0",
    )
    with pytest.raises(GoalPhaseNativeMarkdownError, match="Goal differs"):
        attach_goal_phase_native_document(source, document)


def test_semantic_marker_text_is_not_mistaken_for_framing() -> None:
    source = _source()
    document = _document(
        source,
        title=START_MARKER.decode(),
        intent=END_MARKER.decode(),
    )
    candidate = attach_goal_phase_native_document(source, document)
    recovered_source, recovered_document = extract_goal_phase_native_document(candidate)
    assert recovered_source == source
    assert recovered_document == document


def test_duplicate_real_authority_block_is_rejected() -> None:
    source = _source()
    document = _document(source)
    candidate = attach_goal_phase_native_document(source, document)
    duplicate = candidate + candidate[len(source) :]
    with pytest.raises(GoalPhaseNativeMarkdownError, match="separator"):
        extract_goal_phase_native_document(duplicate)


def test_repair_rebinds_compatibility_only_advancement() -> None:
    source = _source()
    prior = attach_goal_phase_native_document(source, _document(source))
    advanced = prior.replace(b"| 1 | m1 | [ ] | Planned |", b"| 1 | m1 | [~] | Active |")
    advanced += b"- compatibility-only update\n"

    repaired, document = repair_advanced_goal_phase_native_document(
        prior_candidate=prior,
        advanced_candidate=advanced,
        source_refs=("repository-commit:advanced", "repository-path:goal.md"),
    )

    compatibility, recovered = extract_goal_phase_native_document(repaired)
    assert b"| 1 | m1 | [~] | Active |" in compatibility
    assert compatibility.endswith(b"- compatibility-only update\n")
    assert recovered == document
    assert recovered.document_ref != _document(source).document_ref


def test_repair_rejects_phase_or_dependency_meaning_change() -> None:
    source = _source()
    prior = attach_goal_phase_native_document(source, _document(source))
    advanced = prior.replace(b"| Planned | Reviewed |", b"| Planned | Changed |")

    with pytest.raises(GoalPhaseNativeMarkdownError, match="changes native Phase"):
        repair_advanced_goal_phase_native_document(
            prior_candidate=prior,
            advanced_candidate=advanced,
            source_refs=("repository-commit:advanced",),
        )


def test_v2_authority_survives_attach_extract_and_compatibility_repair() -> None:
    source = _source()
    prior_v1 = _document(source)
    document = GoalPhaseNativeDocumentV2(
        goal_tag=prior_v1.goal_tag,
        compatibility_projection_sha256=prior_v1.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior_v1.compatibility_projection_byte_count,
        definitions=prior_v1.definitions,
        operational_bundle=prior_v1.operational_bundle,
        unresolved_dependencies=prior_v1.unresolved_dependencies,
        source_refs=prior_v1.source_refs,
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    prior = attach_goal_phase_native_document(source, document)
    assert extract_goal_phase_native_document(prior)[1] == document

    advanced = prior + b"- compatibility-only update\n"
    repaired, rebound = repair_advanced_goal_phase_native_document(
        prior_candidate=prior,
        advanced_candidate=advanced,
        source_refs=("repository-commit:advanced",),
    )
    assert isinstance(rebound, GoalPhaseNativeDocumentV2)
    assert rebound.execution_authority == document.execution_authority
    assert extract_goal_phase_native_document(repaired)[1] == rebound


def test_v3_journal_round_trips_through_terminal_markdown_without_repair() -> None:
    source = _source()
    prior = _document(source)
    definition = prior.definitions[0]
    v2 = GoalPhaseNativeDocumentV2(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(GoalLanePhase(
                coordinate=definition.coordinate,
                title=definition.title or "",
                ordinal=definition.ordinal,
                intent=definition.intent or "",
                state=GoalLanePhaseState.PLANNED,
                gate=definition.gate,
            ),),
            dependencies=(),
        ),
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs,
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    v3 = GoalPhaseNativeDocumentV3(
        goal_tag=v2.goal_tag,
        compatibility_projection_sha256=v2.compatibility_projection_sha256,
        compatibility_projection_byte_count=v2.compatibility_projection_byte_count,
        definitions=v2.definitions,
        operational_bundle=v2.operational_bundle,
        unresolved_dependencies=v2.unresolved_dependencies,
        source_refs=v2.source_refs,
        execution_authority=v2.execution_authority,
        phase_operation_journal=GoalPhaseOperationJournalV1(entries=(
            GoalPhaseOperationJournalEntryV1(
                operation_kind="approve_pursuit",
                decision="approve",
                coordinate=v2.definitions[0].coordinate,
                gate_digest=v2.definitions[0].gate.gate_digest,
                source_preimage_ref=v2.document_ref,
                actor_ref=START_MARKER.decode(),
                action_occurrence_ref="actor-action-occurrence:sha256:" + "4" * 64,
                policy_ref="goal-phase-approval-policy:sha256:" + "5" * 64,
                policy_digest="sha256:" + "6" * 64,
                idempotency_key="request-1",
                delta_ref="goal-phase-delta:sha256:" + "7" * 64,
                event_ref="goal-phase-event:sha256:" + "8" * 64,
            ),
        )),
    )
    candidate = attach_goal_phase_native_document(source, v3)
    assert extract_goal_phase_native_document(candidate) == (source, v3)
    with pytest.raises(GoalPhaseNativeMarkdownError, match="V3 compatibility repair"):
        repair_advanced_goal_phase_native_document(
            prior_candidate=candidate,
            advanced_candidate=candidate + b"- later note\n",
            source_refs=("repository-commit:advanced",),
        )


@pytest.mark.parametrize("journal", [False, True])
def test_v4_round_trip_preserves_native_lane_and_optional_journal_without_repair(journal: bool) -> None:
    source = _source()
    base = _document(source, title=START_MARKER.decode(), intent=END_MARKER.decode())
    definition = base.definitions[0]
    authority = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
        proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
        coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
    )
    document = GoalPhaseNativeDocumentV4(
        goal_tag=base.goal_tag,
        compatibility_projection_sha256=base.compatibility_projection_sha256,
        compatibility_projection_byte_count=base.compatibility_projection_byte_count,
        definitions=base.definitions,
        operational_bundle=GoalPhaseContractBundleV1((GoalLanePhase(
            coordinate=definition.coordinate, title=definition.title or "",
            ordinal=definition.ordinal, intent=definition.intent or "",
            state=GoalLanePhaseState.PLANNED, gate=definition.gate,
        ),), ()),
        unresolved_dependencies=base.unresolved_dependencies, source_refs=base.source_refs,
        execution_authority=authority,
        native_lane_authorities=(GoalNativeLaneAuthorityV1(
            goal_tag=base.goal_tag, lane_key="runtime", role="Runtime",
            owner_profile="provider_execution_v1", owner_ref="codex-reader",
            operational_state="planned", state_detail=None, hold_authority_refs=(),
            current_work_association_ref=None,
        ),),
        operation_journal_profile="v1" if journal else "none",
        phase_operation_journal=GoalPhaseOperationJournalV1((GoalPhaseOperationJournalEntryV1(
            operation_kind="approve_pursuit", decision="approve",
            coordinate=definition.coordinate, gate_digest=definition.gate.gate_digest,
            source_preimage_ref=base.document_ref, actor_ref="identity:human-reader",
            action_occurrence_ref="actor-action-occurrence:sha256:" + "4" * 64,
            policy_ref="goal-phase-approval-policy:sha256:" + "5" * 64,
            policy_digest="sha256:" + "6" * 64,
            idempotency_key="reader-only", delta_ref="goal-phase-delta:sha256:" + "7" * 64,
            event_ref="goal-phase-event:sha256:" + "8" * 64,
        ),)) if journal else None,
    )
    candidate = attach_goal_phase_native_document(source, document)
    assert extract_goal_phase_native_document(candidate) == (source, document)
    with pytest.raises(GoalPhaseNativeMarkdownError, match="V4 compatibility repair"):
        repair_advanced_goal_phase_native_document(
            prior_candidate=candidate, advanced_candidate=candidate + b"- later note\n",
            source_refs=("repository-commit:advanced",),
        )
    changed_prefix = source + b"- foreign prefix\n"
    with pytest.raises(GoalPhaseNativeMarkdownError, match="exact compatibility"):
        attach_goal_phase_native_document(changed_prefix, document)
    foreign = replace(document, goal_tag="goal/2026-09-20/foreign",
                      definitions=tuple(replace(item, coordinate=replace(item.coordinate,
                          goal_tag="goal/2026-09-20/foreign")) for item in document.definitions),
                      operational_bundle=GoalPhaseContractBundleV1((), ()),
                      native_lane_authorities=(replace(document.native_lane_authorities[0],
                          goal_tag="goal/2026-09-20/foreign"),),
                      operation_journal_profile="none", phase_operation_journal=None)
    with pytest.raises(GoalPhaseNativeMarkdownError, match="Goal differs"):
        attach_goal_phase_native_document(source, foreign)
