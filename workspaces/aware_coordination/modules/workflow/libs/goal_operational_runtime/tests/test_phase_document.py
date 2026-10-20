from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseNativeDocumentError,
    GoalPhaseNativeCarrierError,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    GoalNativeLaneAuthorityV1,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    GoalPhaseUnresolvedDependencyV1,
    decode_goal_phase_native_document,
    encode_goal_phase_native_document,
    attach_goal_phase_native_carrier,
    extract_goal_phase_native_carrier,
)

GOAL = "goal/2026-09-20/native-document-test-v0"


def _gate(key: str = "reviewed") -> GoalLanePhaseGate:
    return GoalLanePhaseGate(
        gate_key=key,
        promise="Independent acceptance is recorded.",
        gate_contract_ref="aware.goal.gate/reviewed-v1",
        evidence_schema_ref="aware.goal.gate-evidence/reviewed-v1",
        invariant_refs=("invariant:issue-closure-is-not-phase-acceptance",),
    )


def _coordinate(phase: str = "m1") -> GoalPhaseCoordinate:
    return GoalPhaseCoordinate(goal_tag=GOAL, lane_key="runtime", phase_key=phase)


def _definition(*, complete: bool = True) -> GoalLanePhaseDefinitionV1:
    return GoalLanePhaseDefinitionV1(
        coordinate=_coordinate(),
        ordinal=1,
        title="Native carrier" if complete else None,
        intent="Carry native authority honestly." if complete else None,
        gate=_gate(),
    )


def _document(
    *,
    definition: GoalLanePhaseDefinitionV1 | None = None,
    phases: tuple[GoalLanePhase, ...] = (),
) -> GoalPhaseNativeDocumentV1:
    source = b"# Compatibility Goal\n"
    return GoalPhaseNativeDocumentV1(
        goal_tag=GOAL,
        compatibility_projection_sha256=(
            "sha256:" + hashlib.sha256(source).hexdigest()
        ),
        compatibility_projection_byte_count=len(source),
        definitions=(definition or _definition(),),
        operational_bundle=GoalPhaseContractBundleV1(
            phases=phases,
            dependencies=(),
        ),
        unresolved_dependencies=(),
        source_refs=("repository:path:docs/goals/test.md",),
    )


def test_definition_without_operational_facts_is_authoritative() -> None:
    document = _document(definition=_definition(complete=False))
    decoded = decode_goal_phase_native_document(
        encode_goal_phase_native_document(document)
    )
    assert decoded == document
    assert decoded.operational_bundle.phases == ()


def test_qualified_operational_phase_must_match_definition() -> None:
    definition = _definition()
    phase = GoalLanePhase(
        coordinate=definition.coordinate,
        title=definition.title or "",
        ordinal=definition.ordinal,
        intent=definition.intent or "",
        state=GoalLanePhaseState.PLANNED,
        gate=definition.gate,
    )
    assert _document(definition=definition, phases=(phase,)).operational_bundle.phases
    with pytest.raises(GoalPhaseNativeDocumentError, match="differs"):
        _document(
            definition=definition,
            phases=(replace(phase, title="Changed meaning"),),
        )


def test_operational_phase_requires_complete_definition() -> None:
    incomplete = _definition(complete=False)
    phase = GoalLanePhase(
        coordinate=incomplete.coordinate,
        title="Invented title",
        ordinal=incomplete.ordinal,
        intent="Invented intent",
        state=GoalLanePhaseState.PLANNED,
        gate=incomplete.gate,
    )
    with pytest.raises(GoalPhaseNativeDocumentError, match="complete title"):
        _document(definition=incomplete, phases=(phase,))


def test_unresolved_dependency_cannot_produce_eligibility() -> None:
    with pytest.raises(GoalPhaseNativeDocumentError, match="cannot produce"):
        GoalPhaseUnresolvedDependencyV1(
            owner_goal_tag=GOAL,
            dependency_key="external-gate",
            dependent=_coordinate(),
            prerequisite=GoalPhaseCoordinate(
                goal_tag="goal/2026-09-20/external-v0",
                lane_key="api",
                phase_key="a1",
            ),
            relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            reason="External Gate digest is not admitted.",
            eligibility_effect="eligible",
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda wire: wire.update(extra="value"), "fields"),
        (
            lambda wire: wire["definitions"][0].update(definition_ref="bad"),
            "definition_ref",
        ),
        (lambda wire: wire.update(document_ref="bad"), "document_ref"),
        (
            lambda wire: wire.update(compatibility_projection_byte_count=True),
            "integer",
        ),
    ],
)
def test_strict_decoder_rejects_tampering(mutation, match: str) -> None:
    wire = json.loads(encode_goal_phase_native_document(_document()))
    mutation(wire)
    with pytest.raises(GoalPhaseNativeDocumentError, match=match):
        decode_goal_phase_native_document(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def test_strict_decoder_rejects_duplicate_json_key() -> None:
    payload = encode_goal_phase_native_document(_document())
    duplicate = payload[:-1] + b',"schema_id":"duplicate"}'
    with pytest.raises(GoalPhaseNativeDocumentError, match="duplicate JSON key"):
        decode_goal_phase_native_document(duplicate)


def test_v2_execution_authority_is_strict_and_v1_remains_decodable() -> None:
    prior = _document()
    authority = GoalPhaseExecutionAuthorityV1(
        source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
        parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
        proposal_aggregate_ref=(
            "goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64
        ),
        coordinator_acceptance_ref=(
            "goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:"
            + "3" * 64
        ),
    )
    value = GoalPhaseNativeDocumentV2(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions,
        operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs,
        execution_authority=authority,
    )
    assert decode_goal_phase_native_document(encode_goal_phase_native_document(prior)) == prior
    assert decode_goal_phase_native_document(encode_goal_phase_native_document(value)) == value

    wire = json.loads(encode_goal_phase_native_document(value))
    wire["execution_authority"]["legacy_execution_disposition"] = "active"
    with pytest.raises(GoalPhaseNativeDocumentError, match="retired"):
        decode_goal_phase_native_document(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def _typed(prefix: str, digit: str) -> str:
    return prefix + ":sha256:" + digit * 64


def _v2_document() -> GoalPhaseNativeDocumentV2:
    prior = _document()
    definition = prior.definitions[0]
    return GoalPhaseNativeDocumentV2(
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
            parity_ref=_typed("goal-phase-native-compatibility-parity", "1"),
            proposal_aggregate_ref=_typed(
                "goal-phase-native-operational-bootstrap-proposal", "2"
            ),
            coordinator_acceptance_ref=_typed(
                "goal-phase-native-operational-bootstrap-coordinator-acceptance", "3"
            ),
        ),
    )


def _entry(
    *, decision: str = "approve", approval_entry_ref: str | None = None,
    digit: str = "4",
) -> GoalPhaseOperationJournalEntryV1:
    return GoalPhaseOperationJournalEntryV1(
        operation_kind="admit_pursuit" if decision == "admit" else "approve_pursuit",
        decision=decision,
        coordinate=_coordinate(),
        gate_digest=_gate().gate_digest,
        source_preimage_ref=_v2_document().document_ref,
        actor_ref="identity:actor-one",
        action_occurrence_ref=_typed("actor-action-occurrence", digit),
        policy_ref=_typed("goal-phase-approval-policy", "5"),
        policy_digest="sha256:" + "6" * 64,
        idempotency_key="request-" + digit,
        delta_ref=_typed("goal-phase-delta", digit),
        event_ref=_typed("goal-phase-event", digit),
        approval_entry_ref=approval_entry_ref,
        agent_run_request_ref=(
            _typed("agent-run-request", "7") if decision == "admit" else None
        ),
        assignment_ref=(
            _typed("agent-assignment", "8") if decision == "admit" else None
        ),
        execution_ref=(
            _typed("agent-execution", "9") if decision == "admit" else None
        ),
    )


def _v3_document(
    entries: tuple[GoalPhaseOperationJournalEntryV1, ...] | None = None,
) -> GoalPhaseNativeDocumentV3:
    prior = _v2_document()
    return GoalPhaseNativeDocumentV3(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions,
        operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs,
        execution_authority=prior.execution_authority,
        phase_operation_journal=GoalPhaseOperationJournalV1(
            entries=(_entry(),) if entries is None else entries
        ),
    )


def test_v3_round_trip_preserves_v2_and_v1_wire_laws() -> None:
    prior = _v2_document()
    prior_wire = encode_goal_phase_native_document(prior)
    value = _v3_document()
    assert decode_goal_phase_native_document(encode_goal_phase_native_document(value)) == value
    assert encode_goal_phase_native_document(prior) == prior_wire
    assert decode_goal_phase_native_document(prior_wire) == prior
    assert decode_goal_phase_native_document(
        encode_goal_phase_native_document(_document())
    ) == _document()
    injected = json.loads(prior_wire)
    injected["phase_operation_journal"] = json.loads(
        encode_goal_phase_native_document(value)
    )["phase_operation_journal"]
    with pytest.raises(GoalPhaseNativeDocumentError, match="fields"):
        decode_goal_phase_native_document(
            json.dumps(injected, sort_keys=True, separators=(",", ":")).encode()
        )


def test_v3_local_journal_sequence_and_post_pursuit_revocation() -> None:
    approval = _entry()
    revoke = _entry(decision="revoke", approval_entry_ref=approval.entry_ref, digit="a")
    reapproval = _entry(digit="b")
    pursuit = _entry(
        decision="admit", approval_entry_ref=reapproval.entry_ref, digit="c"
    )
    document = _v3_document((approval, revoke, reapproval, pursuit))
    assert decode_goal_phase_native_document(encode_goal_phase_native_document(document)) == document
    with pytest.raises(GoalPhaseNativeDocumentError, match="after admitted pursuit"):
        _v3_document((approval, revoke, reapproval, pursuit, _entry(
            decision="revoke", approval_entry_ref=reapproval.entry_ref, digit="d"
        )))
    with pytest.raises(GoalPhaseNativeDocumentError, match="exact live approval"):
        _v3_document((approval, _entry(
            decision="revoke", approval_entry_ref=_typed(
                "goal-phase-operation-journal-entry", "e"
            ), digit="d"
        )))
    with pytest.raises(GoalPhaseNativeDocumentError, match="duplicate journal action"):
        _v3_document((approval, _entry(digit="4")))


def test_v3_entry_variants_fail_closed_on_foreign_or_missing_chain_fields() -> None:
    approval = _entry()
    with pytest.raises(GoalPhaseNativeDocumentError, match="foreign chain fields"):
        replace(approval, approval_entry_ref=approval.entry_ref)
    with pytest.raises(GoalPhaseNativeDocumentError, match="execution fields"):
        replace(
            _entry(decision="revoke", approval_entry_ref=approval.entry_ref, digit="a"),
            assignment_ref=_typed("agent-assignment", "8"),
        )
    with pytest.raises(GoalPhaseNativeDocumentError, match="execution_ref"):
        replace(
            _entry(decision="admit", approval_entry_ref=approval.entry_ref, digit="b"),
            execution_ref=None,
        )
    with pytest.raises(GoalPhaseNativeDocumentError, match="exact live approval"):
        _v3_document((_entry(decision="admit", approval_entry_ref=approval.entry_ref),))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda wire: wire.update(extra="foreign"),
        lambda wire: wire["phase_operation_journal"].update(extra="foreign"),
        lambda wire: wire["phase_operation_journal"]["entries"][0].update(extra="foreign"),
        lambda wire: wire["phase_operation_journal"]["entries"][0].update(entry_ref="wrong"),
        lambda wire: wire["phase_operation_journal"].update(journal_ref="wrong"),
        lambda wire: wire.update(document_ref="wrong"),
        lambda wire: wire["phase_operation_journal"]["entries"][0].update(idempotency_key=True),
        lambda wire: wire["phase_operation_journal"]["entries"][0].update(decision="revoke"),
    ],
)
def test_v3_decoder_rejects_noncanonical_or_tampered_entries(mutation) -> None:
    wire = json.loads(encode_goal_phase_native_document(_v3_document()))
    mutation(wire)
    with pytest.raises(GoalPhaseNativeDocumentError):
        decode_goal_phase_native_document(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def test_v3_rejects_empty_journal_and_foreign_coordinate() -> None:
    with pytest.raises(GoalPhaseNativeDocumentError, match="requires entries"):
        _v3_document(())
    foreign = replace(_entry(), coordinate=GoalPhaseCoordinate(
        goal_tag="goal/2026-09-20/foreign-v0", lane_key="runtime", phase_key="m1"
    ))
    with pytest.raises(GoalPhaseNativeDocumentError, match="not defined"):
        _v3_document((foreign,))
    prior = _document()
    with pytest.raises(GoalPhaseNativeDocumentError, match="not operational"):
        GoalPhaseNativeDocumentV3(
            goal_tag=prior.goal_tag,
            compatibility_projection_sha256=prior.compatibility_projection_sha256,
            compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
            definitions=prior.definitions,
            operational_bundle=prior.operational_bundle,
            unresolved_dependencies=prior.unresolved_dependencies,
            source_refs=prior.source_refs,
            execution_authority=_v2_document().execution_authority,
            phase_operation_journal=GoalPhaseOperationJournalV1(entries=(_entry(),)),
        )


def _v4_document(*, journal: bool = False) -> GoalPhaseNativeDocumentV4:
    prior = _v3_document() if journal else _v2_document()
    journal_value = _v3_document().phase_operation_journal if journal else None
    return GoalPhaseNativeDocumentV4(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions,
        operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs,
        execution_authority=prior.execution_authority,
        native_lane_authorities=(GoalNativeLaneAuthorityV1(
            goal_tag=GOAL,
            lane_key="runtime",
            role="Neutral runtime",
            owner_profile="provider_execution_v1",
            owner_ref="codex-01a0ecf9-719a-7923-afdc-e6ec5f8db283",
            operational_state="planned",
            state_detail=None,
            hold_authority_refs=(),
            current_work_association_ref=None,
        ),),
        operation_journal_profile="v1" if journal else "none",
        phase_operation_journal=journal_value,
    )


def test_v4_round_trip_has_distinct_journal_profiles_and_preserves_prior_wires() -> None:
    before_v1 = encode_goal_phase_native_document(_document())
    before_v2 = encode_goal_phase_native_document(_v2_document())
    before_v3 = encode_goal_phase_native_document(_v3_document())
    for journal in (False, True):
        document = _v4_document(journal=journal)
        encoded = encode_goal_phase_native_document(document)
        wire = json.loads(encoded)
        assert ("phase_operation_journal" in wire) is journal
        assert decode_goal_phase_native_document(encoded) == document
        compatibility, restored = extract_goal_phase_native_carrier(
            attach_goal_phase_native_carrier(b"# Compatibility Goal\n", document)
        )
        assert compatibility == b"# Compatibility Goal\n"
        assert restored == document
        if journal:
            assert wire["phase_operation_journal"] == json.loads(before_v3)[
                "phase_operation_journal"
            ]
    assert encode_goal_phase_native_document(_document()) == before_v1
    assert encode_goal_phase_native_document(_v2_document()) == before_v2
    assert encode_goal_phase_native_document(_v3_document()) == before_v3


def test_v4_carrier_and_duplicate_json_keys_fail_closed() -> None:
    document = _v4_document()
    carrier = attach_goal_phase_native_carrier(b"# Compatibility Goal\n", document)
    with pytest.raises(GoalPhaseNativeCarrierError, match="terminal"):
        extract_goal_phase_native_carrier(carrier + b"unexpected")
    with pytest.raises(GoalPhaseNativeDocumentError, match="duplicate JSON key"):
        decode_goal_phase_native_document(
            encode_goal_phase_native_document(document).replace(
                b'"schema_id":', b'"schema_id":"duplicate","schema_id":', 1
            )
        )
    prior = json.loads(encode_goal_phase_native_document(_v3_document()))
    prior["native_lane_authorities"] = json.loads(
        encode_goal_phase_native_document(document)
    )["native_lane_authorities"]
    with pytest.raises(GoalPhaseNativeDocumentError, match="fields"):
        decode_goal_phase_native_document(
            json.dumps(prior, sort_keys=True, separators=(",", ":")).encode()
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda wire: wire.update(foreign=True),
        lambda wire: wire.update(document_ref="goal-phase-document:sha256:" + "0" * 64),
        lambda wire: wire.update(operation_journal_profile=True),
        lambda wire: wire.update(phase_operation_journal=None),
        lambda wire: wire["native_lane_authorities"][0].update(foreign="value"),
        lambda wire: wire["native_lane_authorities"][0].update(role=True),
        lambda wire: wire["native_lane_authorities"][0].update(lane_authority_ref="forged"),
        lambda wire: wire["native_lane_authorities"][0].update(current_work_association_ref=True),
        lambda wire: wire["native_lane_authorities"].append(wire["native_lane_authorities"][0]),
    ],
)
def test_v4_strict_decoder_rejects_tampering(mutation) -> None:
    wire = json.loads(encode_goal_phase_native_document(_v4_document()))
    mutation(wire)
    with pytest.raises((GoalPhaseNativeDocumentError, TypeError)):
        decode_goal_phase_native_document(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def test_v4_journal_profile_and_lane_state_are_closed() -> None:
    value = _v4_document()
    with pytest.raises(GoalPhaseNativeDocumentError, match="journal must be absent"):
        replace(value, phase_operation_journal=_v3_document().phase_operation_journal)
    with pytest.raises(GoalPhaseNativeDocumentError, match="requires exact journal"):
        replace(value, operation_journal_profile="v1")
    lane = value.native_lane_authorities[0]
    with pytest.raises(GoalPhaseNativeDocumentError, match="requires hold authority"):
        replace(lane, operational_state="held", state_detail="Waiting")
    with pytest.raises(GoalPhaseNativeDocumentError, match="matching definition"):
        replace(value, native_lane_authorities=(replace(lane, lane_key="foreign"),))


@pytest.mark.parametrize("state", ["active", "held", "blocked"])
def test_v4_lane_state_does_not_imply_current_work(state: str) -> None:
    value = _v4_document()
    lane = replace(
        value.native_lane_authorities[0],
        operational_state=state,
        state_detail="Pending authority" if state != "active" else None,
        hold_authority_refs=(
            (_typed("goal-lane-hold", "7"),) if state != "active" else ()
        ),
    )
    assert lane.current_work_association_ref is None
    successor = replace(value, native_lane_authorities=(lane,))
    assert decode_goal_phase_native_document(
        encode_goal_phase_native_document(successor)
    ) == successor


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("authority_profile", "authority profile"),
        ("compatibility_profile", "compatibility profile"),
    ],
)
def test_v4_constructor_and_decoder_reject_altered_profiles(
    field: str, message: str,
) -> None:
    value = _v4_document()
    with pytest.raises(GoalPhaseNativeDocumentError, match=message):
        replace(value, **{field: "foreign_profile_v1"})
    wire = json.loads(encode_goal_phase_native_document(value))
    wire[field] = "foreign_profile_v1"
    with pytest.raises(GoalPhaseNativeDocumentError, match=message):
        decode_goal_phase_native_document(
            json.dumps(wire, sort_keys=True, separators=(",", ":")).encode()
        )


def test_v4_native_lane_keys_are_sorted_and_unique() -> None:
    value = _v4_document()
    alpha = GoalNativeLaneAuthorityV1(
        goal_tag=GOAL,
        lane_key="alpha",
        role="Independent responsibility",
        owner_profile="provider_execution_v1",
        owner_ref="codex-01a0ecf9-719a-7923-afdc-e6ec5f8db283",
        operational_state="planned",
        state_detail=None,
        hold_authority_refs=(),
        current_work_association_ref=None,
    )
    definition = replace(
        value.definitions[0],
        coordinate=GoalPhaseCoordinate(goal_tag=GOAL, lane_key="alpha", phase_key="a1"),
    )
    expanded = replace(
        value,
        definitions=(definition, *value.definitions),
        native_lane_authorities=(alpha, *value.native_lane_authorities),
    )
    assert decode_goal_phase_native_document(
        encode_goal_phase_native_document(expanded)
    ) == expanded
    with pytest.raises(GoalPhaseNativeDocumentError, match="sorted and unique"):
        replace(expanded, native_lane_authorities=tuple(reversed(expanded.native_lane_authorities)))
    with pytest.raises(GoalPhaseNativeDocumentError, match="sorted and unique"):
        replace(value, native_lane_authorities=(value.native_lane_authorities[0],) * 2)


def test_v4_current_work_must_be_exactly_the_lane_phase_work() -> None:
    value = _v4_document()
    phase = value.operational_bundle.phases[0]
    association = GoalLanePhaseWork(
        association_ref="goal-phase-work:sha256:" + "4" * 64,
        issue_ref="fb/2026-09-29/current-work",
        role=GoalLanePhaseWorkRole.IMPLEMENTATION,
        disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at="2026-09-29T15:00:00Z",
        receipt_ref="goal-phase-work-admission:sha256:" + "5" * 64,
    )
    active = replace(
        value,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=(replace(phase, state=GoalLanePhaseState.ACTIVE,
                            work_associations=(association,)),),
            dependencies=(),
        ),
        native_lane_authorities=(replace(
            value.native_lane_authorities[0],
            operational_state="active",
            current_work_association_ref=association.association_ref,
        ),),
    )
    assert decode_goal_phase_native_document(
        encode_goal_phase_native_document(active)
    ) == active
    with pytest.raises(GoalPhaseNativeDocumentError, match="current Work differs"):
        replace(active, native_lane_authorities=(replace(
            active.native_lane_authorities[0],
            current_work_association_ref="goal-phase-work:sha256:" + "6" * 64,
        ),))
    with pytest.raises(GoalPhaseNativeDocumentError, match="omits current Phase Work"):
        replace(active, native_lane_authorities=(replace(
            active.native_lane_authorities[0], current_work_association_ref=None,
        ),))
    extra = replace(
        association,
        association_ref="goal-phase-work:sha256:" + "6" * 64,
        issue_ref="fb/2026-09-29/extra-work",
        receipt_ref="goal-phase-work-admission:sha256:" + "7" * 64,
    )
    with pytest.raises(GoalPhaseNativeDocumentError, match="current Work differs"):
        replace(
            active,
            operational_bundle=GoalPhaseContractBundleV1(
                phases=(replace(
                    active.operational_bundle.phases[0],
                    work_associations=(association, extra),
                ),),
                dependencies=(),
            ),
        )
