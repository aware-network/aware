from __future__ import annotations

from dataclasses import replace

import pytest

from aware_goal_operational_runtime.phase_contracts import (
    GoalLanePhaseGate,
    GoalDependencyRelation,
    GoalPhaseDependency,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
)
from aware_goal_operational_runtime.phase_document import (
    GoalLanePhaseDefinitionV1,
    GoalNativeLaneAuthorityV1,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV4,
)
from aware_goal_operational_runtime.phase_native_lane_authority import (
    GoalNativeLaneIntroductionPublicationReceiptV1,
    GoalNativeLaneDependencySourceV1,
    GoalNativeLanePublicationError,
    decode_goal_native_lane_introduction_receipt,
    require_exact_native_lane_introduction,
    derive_goal_native_lane_semantic_closure,
    derive_goal_native_lane_dependency_scope,
    reduce_goal_native_lane_scope_history,
)
from aware_goal_operational_runtime.phase_native_scope_advancement import (
    GoalGlobalDirectionAuthorityV1, GoalPhaseNativeScopeDescriptorV1,
    GoalPhaseNativeScopeProfile, project_goal_phase_native_scope,
)
from aware_goal_operational_runtime.phase_native_lane_hold import (
    GoalNativeLaneHoldDecisionV1,
    decode_goal_native_lane_hold_decision,
    encode_goal_native_lane_hold_block,
    extract_goal_native_lane_hold_block,
)
from aware_goal_operational_runtime.phase_native_lane_evidence import (
    GoalNativeLaneEvidenceIssuerV2, GoalNativeLaneEvidenceSnapshotV2, GoalNativeLaneQualifiedHoldV2,
    decode_goal_native_lane_evidence_snapshot, require_qualified_native_lane_evidence,
)


def _transition() -> tuple[
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV4,
    GoalNativeLaneIntroductionPublicationReceiptV1,
]:
    goal = "goal/2026-09-29/native-lane"
    before = GoalPhaseNativeDocumentV2(
        goal_tag=goal,
        compatibility_projection_sha256="sha256:" + "a" * 64,
        compatibility_projection_byte_count=7,
        definitions=(GoalLanePhaseDefinitionV1(
            coordinate=GoalPhaseCoordinate(goal, "foundation", "f1"),
            ordinal=1,
            gate=GoalLanePhaseGate(
                gate_key="f1", promise="Foundation is ready.",
                gate_contract_ref="contract:f1", evidence_schema_ref="evidence:f1",
            ),
            title="Foundation", intent="Supply the agent foundation.",
        ),),
        operational_bundle=GoalPhaseContractBundleV1(phases=(), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("source:original",),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    lane = GoalNativeLaneAuthorityV1(
        goal_tag=goal,
        lane_key="foundation",
        role="Independent foundation responsibility",
        owner_profile="provider_execution_v1",
        owner_ref="codex-01a0ecf9-719a-7923-afdc-e6ec5f8db283",
        operational_state="planned",
        state_detail=None,
        hold_authority_refs=(),
        current_work_association_ref=None,
    )
    after = GoalPhaseNativeDocumentV4(
        goal_tag=before.goal_tag,
        compatibility_projection_sha256=before.compatibility_projection_sha256,
        compatibility_projection_byte_count=before.compatibility_projection_byte_count,
        definitions=before.definitions,
        operational_bundle=before.operational_bundle,
        unresolved_dependencies=before.unresolved_dependencies,
        source_refs=before.source_refs,
        execution_authority=before.execution_authority,
        native_lane_authorities=(lane,),
        operation_journal_profile="none",
    )
    receipt = GoalNativeLaneIntroductionPublicationReceiptV1(
        goal_tag=goal,
        lane_key=lane.lane_key,
        lane_authority_ref=lane.lane_authority_ref,
        goal_path="docs/goals/2026/09/29/goal-2026-09-29-native-lane.md",
        before_document_ref=before.document_ref,
        after_document_ref=after.document_ref,
        before_goal_sha256="sha256:" + "4" * 64,
        after_goal_sha256="sha256:" + "5" * 64,
        before_goal_blob_oid="6" * 40,
        after_goal_blob_oid="7" * 40,
        repository_parent_ref="8" * 40,
        repository_commit_ref="9" * 40,
        repository_commit_receipt_ref="repository-commit:" + "9" * 40,
        publication_issue_path="docs/issues/2026/09/29/fb-2026-09-29-lane.md",
        publication_issue_blob_oid="a" * 40,
        publication_issue_owner_execution_id="codex-01a0ecf9-719a-7923-afdc-e6ec5f8db283",
        publication_issue_status="in_progress",
        publication_issue_scope_digest="sha256:" + "b" * 64,
    )
    return before, after, receipt


def test_strict_receipt_and_exact_v2_to_v4_introduction() -> None:
    before, after, receipt = _transition()
    assert decode_goal_native_lane_introduction_receipt(receipt.to_wire()) == receipt
    assert require_exact_native_lane_introduction(
        before=before, after=after, receipt=receipt,
    ) == after.native_lane_authorities[0]
    assert receipt.receipt_ref.startswith("goal-native-lane-introduction-publication:sha256:")


@pytest.mark.parametrize("profile", list(GoalPhaseNativeScopeProfile))
def test_old_scope_consumer_refuses_v4_without_compatibility_authority_substitution(profile):
    _, document, _ = _transition()
    before = document.document_ref
    with pytest.raises(TypeError, match="exact native document"):
        project_goal_phase_native_scope(
            document=document, descriptor=GoalPhaseNativeScopeDescriptorV1(
                root=document.definitions[0].coordinate, profile=profile,
                consumer_authority_ref="consumer:refusal-proof", projector_ref="scope-projector:v1"),
            goal_authority=_global(document), lane_authorities=(),
        )
    assert document.document_ref == before


def _hold_decision():
    before, after, _ = _transition()
    lane = after.native_lane_authorities[0]
    return GoalNativeLaneHoldDecisionV1(
        goal_tag=before.goal_tag, lane_key=lane.lane_key,
        source_document_ref=before.document_ref,
        source_revision_ref="object-revision:one", owner_profile=lane.owner_profile,
        owner_ref=lane.owner_ref, target_state="held", state_detail="Explicitly held",
        current_work_association_ref=None, issued_at="2026-09-29T12:05:00Z",
        governing_issue_tag="issue:customer-governance",
    )


def test_neutral_hold_claim_roundtrips_without_git_or_fixed_roots():
    decision = _hold_decision()
    assert decode_goal_native_lane_hold_decision(decision.to_wire()) == decision
    assert decision.decision_ref.startswith("goal-native-lane-hold:sha256:")
    assert extract_goal_native_lane_hold_block(encode_goal_native_lane_hold_block(decision)) == decision
    assert "repository_commit_receipt_ref" not in decision.body()
    assert "decision_ref" not in decision.body()


@pytest.mark.parametrize("field,value", [
    ("source_revision_ref", False), ("current_work_association_ref", True),
    ("issued_at", 1), ("owner_profile", "delegation"),
    ("target_state", "ready"), ("issued_at", "2026-02-30T12:00:00Z"),
    ("source_document_ref", "arbitrary"), ("owner_ref", "issue-owner"),
])
def test_hold_wire_types_profiles_and_calendar_are_strict(field, value):
    # issue-owner is a syntactically valid execution ID; shape is not issuance.
    if field == "owner_ref":
        canonical = replace(_hold_decision(), owner_ref=value)
        assert decode_goal_native_lane_hold_decision(canonical.to_wire()) == canonical
        return
    payload = _hold_decision().to_wire()
    payload[field] = value
    with pytest.raises((ValueError, TypeError)):
        decode_goal_native_lane_hold_decision(payload)


@pytest.mark.parametrize("mutation", ["unknown", "digest", "nested_type", "schema"])
def test_hold_wire_unknown_fields_and_changed_identity_refuse(mutation):
    payload = _hold_decision().to_wire()
    if mutation == "unknown":
        payload["current"] = True
    elif mutation == "digest":
        payload["state_detail"] = "Different hold"
    elif mutation == "nested_type":
        payload["state_detail"] = {"reason": "held"}
    else:
        payload["schema_id"] = "aware.goal.native-lane-hold-decision.v2"
    with pytest.raises((ValueError, TypeError)):
        decode_goal_native_lane_hold_decision(payload)


def test_hold_block_semantic_markers_roundtrip_but_duplicate_blocks_refuse():
    text = "<!-- aware.goal.native-lane-hold-decision.v1:start -->\n```json\nreason\n```\n<!-- aware.goal.native-lane-hold-decision.v1:end -->"
    decision = replace(_hold_decision(), state_detail=text)
    block = encode_goal_native_lane_hold_block(decision)
    assert extract_goal_native_lane_hold_block("# Issue\n" + block + "\n## Updates\n") == decision
    with pytest.raises(ValueError, match="block_ambiguous"):
        extract_goal_native_lane_hold_block(block + "\n" + block)


def test_hold_block_duplicate_json_key_refuses():
    decision = _hold_decision()
    block = encode_goal_native_lane_hold_block(decision)
    block = block.replace('"goal_tag":', '"goal_tag":"foreign","goal_tag":', 1)
    with pytest.raises(ValueError, match="duplicate_json_key"):
        extract_goal_native_lane_hold_block(block)


def test_hold_postconstruction_mutation_does_not_repair_identity():
    decision = _hold_decision()
    object.__setattr__(decision, "state_detail", "Altered after construction")
    with pytest.raises(ValueError, match="wire_digest"):
        encode_goal_native_lane_hold_block(decision)


def _object_snapshot_claim():
    decision = _hold_decision()
    _, document, _ = _transition()
    hold = GoalNativeLaneQualifiedHoldV2(
        decision=decision, verifier_profile="object-provider:introduction-hold-v1",
        issuance_authority={"authority_ref": "object-publication:hold", "source_binding": {"revision": "object-revision:one"}},
        evidence_source_revision_ref=decision.source_revision_ref,
        observed_source_revision_ref="object-revision:two", currentness_ref="object-currentness:two",
    )
    return GoalNativeLaneEvidenceSnapshotV2(
        goal_tag=decision.goal_tag, lane_key=decision.lane_key, document_ref=document.document_ref,
        source_revision_ref="object-revision:two", source_binding_ref="object-source:two",
        incident_declarations=(), gate_observations=(), holds=(hold,),
        authority_inventory=({"profile": "object-source:v1", "source_ref": "object-source:two"},),
        source_evidence=GoalNativeLaneEvidenceIssuerV2(),
    )


def test_snapshot_shape_is_provider_neutral_but_never_issues_authority():
    snapshot = _object_snapshot_claim()
    wire = snapshot.to_wire()
    assert wire["source_revision_ref"] == "object-revision:two"
    assert wire["holds"][0]["evidence_source_revision_ref"] == "object-revision:one"
    assert wire["effect_profile"] == "read_only_non_authorizing"
    assert wire["snapshot_ref"].startswith("goal-native-lane-evidence:sha256:")
    assert "path" not in wire
    assert "snapshot_ref" not in wire["holds"][0]
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        require_qualified_native_lane_evidence(snapshot)
    with pytest.raises(ValueError, match="unissued_or_mutated"):
        decode_goal_native_lane_evidence_snapshot(wire, qualified=snapshot)


@pytest.mark.parametrize("field,value", [
    ("source_revision_ref", False), ("incident_declarations", (("z", "sha256:z"), ("a", "sha256:a"))),
    ("incident_declarations", (("a", "sha256:a"), ("a", "sha256:b"))),
    ("incident_declarations", (("a", False),)), ("gate_observations", ({"outcome": "satisfied"},)),
    ("holds", []), ("authority_inventory", ()), ("authority_inventory", ({"bad": object()},)),
])
def test_snapshot_claim_has_strict_types_and_no_gate_evaluator_fallback(field, value):
    with pytest.raises((ValueError, TypeError)):
        replace(_object_snapshot_claim(), **{field: value})


@pytest.mark.parametrize("mutation", ["coordinate", "epoch", "decision_ref"])
def test_hold_record_cross_bindings_are_revalidated(mutation):
    snapshot = _object_snapshot_claim()
    if mutation == "coordinate":
        object.__setattr__(snapshot.holds[0].decision, "lane_key", "foreign")
    elif mutation == "epoch":
        object.__setattr__(snapshot.holds[0], "observed_source_revision_ref", "object-revision:foreign")
    else:
        object.__setattr__(snapshot.holds[0].decision, "decision_ref", "goal-native-lane-hold:sha256:" + "a" * 64)
    with pytest.raises(ValueError):
        snapshot.__post_init__()


def _global(document):
    return GoalGlobalDirectionAuthorityV1(
        goal_tag=document.goal_tag, lifecycle_status="active", owner_ref="codex-test",
        governance_authority_refs=("goal-owner:verified",), hold_state="clear", hold_authority_refs=(),
        execution_authority_ref=document.execution_authority.authority_ref,
        compatibility_guard_ref="goal-compatibility-guard:verified-global",
        source_revision_ref="object-revision:one", projector_ref="object-provider:one",
        projection_receipt_ref="object-projection:one",
    )


def test_provider_neutral_closure_has_no_git_or_filesystem_dependency():
    _, document, _ = _transition()
    authority = _global(document)
    result = derive_goal_native_lane_semantic_closure(
        document=document, lane_key="foundation", global_authority=authority, issue_authorities={},
    )
    assert result["goal_global"] == authority.semantic_wire()
    assert result["definitions"][0]["coordinate"]["lane_key"] == "foundation"
    assert result["issues"] == []
    with pytest.raises(GoalNativeLanePublicationError, match="issue_set_mismatch"):
        derive_goal_native_lane_semantic_closure(
            document=document, lane_key="foundation", global_authority=authority,
            issue_authorities={"unrelated": {}},
        )


def _incident_sources():
    _, document, _ = _transition()
    definition = document.definitions[0]
    extra = replace(definition, coordinate=replace(definition.coordinate, phase_key="f2"), ordinal=2)
    third = replace(definition, coordinate=replace(definition.coordinate, phase_key="f3"), ordinal=3,
        gate=replace(definition.gate, gate_key="different"))
    edges = tuple(GoalPhaseDependency(
        owner_goal_tag=document.goal_tag, dependency_key=key,
        dependent=definition.coordinate, prerequisite=target.coordinate,
        relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        required_gate_digest=target.gate.gate_digest, reason="Explicit prerequisite",
    ) for key, target in (("z-edge", extra), ("a-edge", third)))
    document = replace(document, definitions=(*document.definitions, extra, third),
        operational_bundle=replace(document.operational_bundle, dependencies=edges))
    source = GoalNativeLaneDependencySourceV1(
        document=document, global_authority=_global(document), lane_authorities=(),
        issue_authorities={}, source_revision_ref="object-revision:one",
    )
    return document, {document.goal_tag: source}


def test_complete_object_source_snapshot_preserves_key_digest_pairs():
    from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest
    document, sources = _incident_sources()
    records = derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources=sources)
    assert [r["declaration"]["dependency_key"] for r in records] == ["a-edge", "z-edge"]
    expected = {d.dependency_key: goal_phase_dependency_digest(d) for d in document.operational_bundle.dependencies}
    assert {r["declaration"]["dependency_key"]: r["dependency_digest"] for r in records} == expected
    assert all(r["observation_profile"] == "not_evaluated" and r["observation"] is None for r in records)


def test_incident_sources_cannot_be_omitted_or_substituted():
    document, sources = _incident_sources()
    with pytest.raises(GoalNativeLanePublicationError, match="source_set_mismatch"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources={})
    with pytest.raises(GoalNativeLanePublicationError, match="source_set_mismatch"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources={**sources, "foreign": next(iter(sources.values()))})
    foreign = replace(next(iter(sources.values())), document=replace(document, source_refs=("source:substituted",)))
    with pytest.raises(GoalNativeLanePublicationError, match="document_mismatch"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources={document.goal_tag: foreign})


def test_incident_required_gate_and_issue_set_are_exact():
    document, sources = _incident_sources()
    object.__setattr__(document.operational_bundle.dependencies[0], "required_gate_digest", "sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="Gate digest differs"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources=sources)
    document, sources = _incident_sources()
    source = replace(next(iter(sources.values())), issue_authorities={"unrelated": {}})
    with pytest.raises(GoalNativeLanePublicationError, match="issue_set_mismatch"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources={document.goal_tag: source})


def test_incident_source_mutation_is_revalidated_at_consumption():
    document, sources = _incident_sources()
    source = next(iter(sources.values()))
    object.__setattr__(source, "source_revision_ref", "object-revision:forged")
    with pytest.raises(GoalNativeLanePublicationError, match="source_authority_mismatch"):
        derive_goal_native_lane_dependency_scope(document=document, lane_key="foundation", sources=sources)


@pytest.mark.parametrize("lineage, pairs, relations, expected", [
    ("equal", (), (), ("current", "exact", "exact")),
    ("descendant", (("a", "a"),), ("exact",), ("current", "advanced", "reobserved_unchanged")),
    ("descendant", (("a", "b"), ("b", "a")), ("exact", "exact"), ("stale", "advanced", "admitted_delta_required")),
    ("descendant", (("a", "a"),), ("unknown",), ("ambiguous", "advanced", "refuse")),
    ("unproven", (), (), ("ambiguous", "unproven", "refuse")),
])
def test_neutral_history_reduction(lineage, pairs, relations, expected):
    ref = lambda letter: "goal-native-lane-semantic-closure:sha256:" + letter * 64
    result = reduce_goal_native_lane_scope_history(
        lineage=lineage, origin_closure_ref=ref("a"), current_closure_ref=ref("a"),
        effect_closure_pairs=tuple((ref(a), ref(b)) for a, b in pairs),
        compatibility_relations=relations,
    )
    assert result[:3] == expected


def test_neutral_history_requires_complete_descendant_effects():
    ref = "goal-native-lane-semantic-closure:sha256:" + "a" * 64
    with pytest.raises(GoalNativeLanePublicationError, match="lacks effects"):
        reduce_goal_native_lane_scope_history(
            lineage="descendant", origin_closure_ref=ref, current_closure_ref=ref,
            effect_closure_pairs=(), compatibility_relations=(),
        )


def test_receipt_tamper_and_extra_field_refuse() -> None:
    _, _, receipt = _transition()
    changed = receipt.to_wire()
    changed["repository_commit_receipt_ref"] = "repository-commit:" + "1" * 40
    with pytest.raises(GoalNativeLanePublicationError, match="receipt/commit mismatch"):
        decode_goal_native_lane_introduction_receipt(changed)
    changed = receipt.to_wire()
    changed["publication_issue_status"] = True
    with pytest.raises(GoalNativeLanePublicationError, match="exact JSON strings"):
        decode_goal_native_lane_introduction_receipt(changed)
    changed = receipt.to_wire()
    changed["unknown"] = "x"
    with pytest.raises(GoalNativeLanePublicationError, match="fields differ"):
        decode_goal_native_lane_introduction_receipt(changed)
    changed = receipt.to_wire()
    changed["receipt_ref"] = "goal-native-lane-introduction-publication:sha256:" + "0" * 64
    with pytest.raises(GoalNativeLanePublicationError, match="digest or body differs"):
        decode_goal_native_lane_introduction_receipt(changed)


@pytest.mark.parametrize(
    "goal_path, issue_path",
    [
        (
            "customer/objectives/2026/09/29/goal-2026-09-29-native-lane.md",
            "work/issues/2026/09/29/fb-2026-09-29-lane.md",
        ),
        ("objectives/native-lane.record", "work/lane-publication.record"),
    ],
)
def test_receipt_paths_are_provider_independent(
    goal_path: str, issue_path: str,
) -> None:
    before, after, original = _transition()
    receipt = replace(original, goal_path=goal_path, publication_issue_path=issue_path)
    assert decode_goal_native_lane_introduction_receipt(receipt.to_wire()) == receipt
    assert require_exact_native_lane_introduction(
        before=before, after=after, receipt=receipt,
    ) == after.native_lane_authorities[0]


@pytest.mark.parametrize("field", ["goal_path", "publication_issue_path"])
@pytest.mark.parametrize(
    "path",
    [
        "/absolute/record.md", "../escape.md", "root/../escape.md",
        "root/./record.md", "root//record.md", "root/record.md/",
        "C:\\record.md", "file:record.md", "root/record\n.md",
        "root/record\r.md", "root/record\x00.md", "root/record\x7f.md",
    ],
)
def test_receipt_refuses_noncanonical_repository_paths(field: str, path: str) -> None:
    _, _, receipt = _transition()
    with pytest.raises(GoalNativeLanePublicationError, match="canonical path"):
        replace(receipt, **{field: path})


def test_introduction_preserves_every_existing_carrier_field() -> None:
    before, after, receipt = _transition()
    changed = replace(after, source_refs=("source:changed",))
    with pytest.raises(GoalNativeLanePublicationError, match="source_refs"):
        require_exact_native_lane_introduction(
            before=before,
            after=changed,
            receipt=replace(receipt, after_document_ref=changed.document_ref),
        )
    with pytest.raises(GoalNativeLanePublicationError, match="document/receipt"):
        require_exact_native_lane_introduction(
            before=before,
            after=after,
            receipt=replace(receipt, before_document_ref="goal-phase-document:sha256:" + "0" * 64),
        )


def test_v4_introduction_preserves_existing_lane_authority() -> None:
    _, first, original_receipt = _transition()
    support_definition = replace(
        first.definitions[0],
        coordinate=GoalPhaseCoordinate(first.goal_tag, "support", "s1"),
        ordinal=2,
    )
    before = replace(first, definitions=(*first.definitions, support_definition))
    support = replace(
        first.native_lane_authorities[0],
        lane_key="support",
        role="Independent support responsibility",
    )
    after = replace(
        before,
        native_lane_authorities=(*before.native_lane_authorities, support),
    )
    receipt = replace(
        original_receipt,
        lane_key="support",
        lane_authority_ref=support.lane_authority_ref,
        before_document_ref=before.document_ref,
        after_document_ref=after.document_ref,
    )
    assert require_exact_native_lane_introduction(
        before=before, after=after, receipt=receipt,
    ) == support
    substituted = replace(
        before.native_lane_authorities[0],
        role="Rewritten existing responsibility",
    )
    changed = replace(
        after,
        native_lane_authorities=(substituted, support),
    )
    with pytest.raises(GoalNativeLanePublicationError, match="other lane authority"):
        require_exact_native_lane_introduction(
            before=before,
            after=changed,
            receipt=replace(receipt, after_document_ref=changed.document_ref),
        )
