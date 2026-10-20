"""Real-Git source/Issue/Protocol verification, never echo resolvers."""
import gc
from copy import copy
from dataclasses import replace

import pytest

from aware_goal_operational_runtime import (
    GoalLanePhase, GoalLanePhaseState, GoalLanePhaseWork, GoalLanePhaseWorkDisposition, GoalLanePhaseWorkRole, GoalPhaseCoordinate,
    GoalPhaseNativeDocumentV3, GoalPhaseOperationJournalEntryV1, GoalPhaseOperationJournalV1,
    attach_goal_phase_native_carrier, extract_goal_phase_native_carrier,
)
from aware_goal_operational_runtime.phase_forward_admission import GoalPhaseOperationalAdmissionRequestV2
import aware_goal_native_fs_adapter.forward_admission_source as source_module
from aware_goal_native_fs_adapter.forward_admission_source import NativeGitForwardAdmissionSource
from aware_protocol_fs_adapter.native_goal_resolver import NativeGoalResolverError
from test_native_provider import (
    _source, _git, _native_capability, _publish_customer_issue,
    CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, CUSTOMER_EXTERNAL_PATH, _publish_external_source,
)


FOUNDATION_ISSUE = "work/issues/2026/09/26/fb-2026-09-26-foundation-work.md"


def _add_native_only_prerequisite(root, *, external=False):
    """Independent committed Phase/Work; deliberately no Markdown lane row."""
    target = CUSTOMER_EXTERNAL_PATH if external else CUSTOMER_PATH
    prefix, document = extract_goal_phase_native_carrier((root / target).read_bytes())
    original = document.definitions[-1]
    definition = replace(original, coordinate=GoalPhaseCoordinate(document.goal_tag, "native-foundation", "foundation"), ordinal=1)
    work = GoalLanePhaseWork(association_ref="goal-phase-work:foundation", issue_ref=FOUNDATION_ISSUE,
        role=GoalLanePhaseWorkRole.IMPLEMENTATION, disposition=GoalLanePhaseWorkDisposition.CURRENT,
        admitted_at="2026-10-01T12:00:00Z", receipt_ref="goal-phase-work-admission:foundation")
    phase = GoalLanePhase(coordinate=definition.coordinate, title=definition.title, intent=definition.intent,
        ordinal=definition.ordinal, gate=definition.gate, state=GoalLanePhaseState.ACTIVE, work_associations=(work,))
    document = replace(document, definitions=(*document.definitions, definition),
        operational_bundle=replace(document.operational_bundle, phases=(*document.operational_bundle.phases, phase)))
    (root / target).write_bytes(attach_goal_phase_native_carrier(prefix, document))
    dependent_prefix, dependent = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    dependent = replace(dependent, operational_bundle=replace(dependent.operational_bundle,
        dependencies=tuple(replace(edge, prerequisite=definition.coordinate,
            required_gate_digest=definition.gate.gate_digest) for edge in dependent.operational_bundle.dependencies)))
    (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_carrier(dependent_prefix, dependent))
    issue = root / FOUNDATION_ISSUE
    issue.write_text("# Issue: Foundation\n\n- Tag: fb/2026-09-26/foundation-work\n"
        "- Status: In Progress\n- Owner: codex-foundation\n\n## Ownership Scope\n"
        f"- `{target}`\n\n## Updates (append-only)\n- Explicit current Work.\n")
    _git(root, "add", target, CUSTOMER_PATH, FOUNDATION_ISSUE)
    _git(root, "commit", "-qm", "Admit native-only prerequisite source facts")


def provider_fixture(tmp_path, monkeypatch, *, journal=False, dependency=False, external=False, native_only=False):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, operational=False,
        current_issue_ref=CUSTOMER_ISSUE_PATH, dependency=dependency, external_dependency=external)
    if journal:
        compatibility, original = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
        other = replace(original.definitions[0], coordinate=GoalPhaseCoordinate(original.goal_tag, "other", "existing"))
        original = replace(original, definitions=original.definitions + (other,),
            operational_bundle=replace(original.operational_bundle, phases=(GoalLanePhase(
                coordinate=other.coordinate, title=other.title, intent=other.intent,
                ordinal=other.ordinal, state=GoalLanePhaseState.ACTIVE, gate=other.gate),)))
        entry = GoalPhaseOperationJournalEntryV1(operation_kind="approve_pursuit", decision="approve",
            coordinate=other.coordinate, gate_digest=other.gate.gate_digest,
            source_preimage_ref=original.document_ref, actor_ref="identity:human-one",
            action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
            policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64, policy_digest="sha256:" + "3" * 64,
            idempotency_key="approval-one", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
            event_ref="goal-phase-event:sha256:" + "5" * 64)
        document = GoalPhaseNativeDocumentV3(goal_tag=original.goal_tag,
            compatibility_projection_sha256=original.compatibility_projection_sha256,
            compatibility_projection_byte_count=original.compatibility_projection_byte_count,
            definitions=original.definitions, operational_bundle=original.operational_bundle,
            unresolved_dependencies=original.unresolved_dependencies, source_refs=original.source_refs,
            execution_authority=original.execution_authority,
            phase_operation_journal=GoalPhaseOperationJournalV1((entry,)))
        (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_carrier(compatibility, document))
        _git(root, "add", CUSTOMER_PATH); _git(root, "commit", "-qm", "Retain unrelated V3 journal")
    _publish_customer_issue(root)
    if external:
        _publish_external_source(root, goal_path=CUSTOMER_EXTERNAL_PATH)
    if native_only:
        assert dependency
        _add_native_only_prerequisite(root, external=external)
    capability = _native_capability(root, monkeypatch)
    _git(root, "add", "aware.protocol.toml")
    _git(root, "commit", "-qm", "Admit Protocol binding")
    publication_issue = CUSTOMER_ISSUE_PATH.replace("customer-work", "forward-admission")
    issue = root / publication_issue
    issue.write_text((root / CUSTOMER_ISSUE_PATH).read_text().replace("customer-work", "forward-admission"))
    _git(root, "add", publication_issue)
    _git(root, "commit", "-qm", "Admit separate Goal governance")
    _, document = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    definition = document.definitions[0]
    request = GoalPhaseOperationalAdmissionRequestV2(coordinate=definition.coordinate,
        expected_document_ref=document.document_ref, expected_source_revision_ref=_git(root, "rev-parse", "HEAD"),
        expected_definition_ref=definition.definition_ref, expected_gate_digest=definition.gate.gate_digest,
        initial_state=GoalLanePhaseState.PLANNED, issue_ref=CUSTOMER_ISSUE_PATH,
        work_role=GoalLanePhaseWorkRole.IMPLEMENTATION, admitted_at="2026-10-01T12:00:00Z",
        evidence_refs=("evidence:explicit-forward-preparation",), idempotency_key="admit-first")
    source = NativeGitForwardAdmissionSource(resolver_capability=capability)
    return root, capability, publication_issue, request, source


@pytest.mark.parametrize("journal,dependency", [(False, False), (True, False), (False, True)])
def test_verified_current_work_definition_only_and_complete_dependency_set(tmp_path, monkeypatch, journal, dependency):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, journal=journal, dependency=dependency)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain"))
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    source.require_verified(result)
    assert result.plan.phase.state is GoalLanePhaseState.PLANNED
    assert len(result.dependency_contexts) == int(dependency)
    if dependency:
        context = result.dependency_contexts[0]["prerequisite"]["context"]
        assert context["endpoint_profile"] == "definition_only_v1" and context["phase"] is None
        assert context["lane_issue_context"][0]["path"] == CUSTOMER_ISSUE_PATH
        assert context["gate_authority_profile"] == "not_evaluated"
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain")) == before


def test_cross_goal_epoch_and_carried_claims_are_not_fresh_gate_evidence(tmp_path, monkeypatch):
    _, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True, external=True)
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    context = result.dependency_contexts[0]["prerequisite"]["context"]
    assert context["coordinate"]["goal_tag"] != request.coordinate.goal_tag
    assert context["source_revision_ref"] == result.source_head
    assert context["gate_authority_profile"] == "unqualified_carrier_claim"
    assert context["phase"]["gate_observations"][0]["source_revision_refs"] == ["historical-source:external-later"]


@pytest.mark.parametrize("external", [False, True])
@pytest.mark.parametrize("journal", [False, True])
def test_native_only_incident_lane_is_explicit_non_authorizing_source_context(tmp_path, monkeypatch, external, journal):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch,
        dependency=True, external=external, journal=journal, native_only=True)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain"))
    verified = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    source.require_verified(verified)
    record = verified.dependency_contexts[0]
    context = record["prerequisite"]["context"]
    assert context["lane"] is None and context["lane_authority_profile"] == "absent_native_only_v1"
    assert context["lane_authority_reason"] == "lane_authority_absent"
    assert context["phase"]["state"] == "active" and context["gate_authority_profile"] == "not_evaluated"
    assert context["lane_issue_context"][0]["owner"] == "codex-foundation"
    assert context["source_revision_ref"] == request.expected_source_revision_ref
    assert record["dependent"]["context"]["scope_profile"] == "dependency_endpoint_context_v2"
    assert record["evaluation_profile"] == "source_context_only_non_authorizing"
    assert FOUNDATION_ISSUE in verified.protected_paths
    assert verified.to_wire()["scope_profile"] == "dependency_endpoint_context_v3"
    assert (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain")) == before


def test_native_only_selected_lane_still_refuses_admission(tmp_path, monkeypatch):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True, native_only=True)
    prefix, document = extract_goal_phase_native_carrier((root / CUSTOMER_PATH).read_bytes())
    definition = document.definitions[-1]
    document = replace(document, operational_bundle=replace(document.operational_bundle, phases=()))
    (root / CUSTOMER_PATH).write_bytes(attach_goal_phase_native_carrier(prefix, document))
    _git(root, "add", CUSTOMER_PATH); _git(root, "commit", "-qm", "Retain native-only definition without Phase")
    request = replace(request, coordinate=definition.coordinate, expected_document_ref=document.document_ref,
        expected_definition_ref=definition.definition_ref, expected_gate_digest=definition.gate.gate_digest,
        issue_ref=FOUNDATION_ISSUE, expected_source_revision_ref=_git(root, "rev-parse", "HEAD"))
    with pytest.raises(ValueError, match="forward_admission_lane_authority_absent"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)


@pytest.mark.parametrize("fault", ["missing", "closed", "invalid_tag", "scope"])
def test_native_only_current_work_requires_real_committed_issue(tmp_path, monkeypatch, fault):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True, native_only=True)
    path = root / FOUNDATION_ISSUE
    if fault == "missing": path.unlink()
    else:
        before = path.read_text()
        path.write_text(before.replace("In Progress", "Closed") if fault == "closed" else
            before.replace("fb/2026-09-26/foundation-work", "fb/2026-09-26/foreign") if fault == "invalid_tag" else
            before.replace(f"- `{CUSTOMER_PATH}`", ""))
    _git(root, "add", FOUNDATION_ISSUE); _git(root, "commit", "-qm", "Invalid committed Work Issue")
    request = replace(request, expected_source_revision_ref=_git(root, "rev-parse", "HEAD"))
    with pytest.raises((ValueError, RuntimeError)):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)


@pytest.mark.parametrize("external", [False, True])
def test_native_only_issue_change_restore_remains_protected(tmp_path, monkeypatch, external):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True, external=external, native_only=True)
    original = (root / FOUNDATION_ISSUE).read_bytes()
    (root / FOUNDATION_ISSUE).write_bytes(original.replace(b"codex-foundation", b"codex-foreign"))
    _git(root, "add", FOUNDATION_ISSUE); _git(root, "commit", "-qm", "Change source Work owner")
    (root / FOUNDATION_ISSUE).write_bytes(original)
    _git(root, "add", FOUNDATION_ISSUE); _git(root, "commit", "-qm", "Restore source Work owner")
    with pytest.raises(ValueError, match="protected_history_advanced"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)


@pytest.mark.parametrize("fault", ["foreign_issue", "closed", "scope", "foreign_work", "same_owner_foreign_work"])
def test_actual_authority_substitutions_refuse(tmp_path, monkeypatch, fault):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch)
    if fault == "same_owner_foreign_work":
        request = replace(request, issue_ref=issue)
    else:
        path = root / (CUSTOMER_ISSUE_PATH if fault == "foreign_work" else issue)
        original = path.read_text()
        changed = (original.replace("codex-test", "codex-foreign") if "foreign" in fault else
            original.replace("In Progress", "Closed") if fault == "closed" else original.replace(CUSTOMER_PATH, "other.py"))
        path.write_text(changed)
        _git(root, "add", path.relative_to(root).as_posix()); _git(root, "commit", "-qm", "Change committed authority")
        request = replace(request, expected_source_revision_ref=_git(root, "rev-parse", "HEAD"))
    with pytest.raises((ValueError, RuntimeError)):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)


def test_unrelated_descendant_and_changed_restored_issue_history(tmp_path, monkeypatch):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch)
    (root / "unrelated.txt").write_text("unrelated")
    _git(root, "add", "unrelated.txt"); _git(root, "commit", "-qm", "Unrelated advancement")
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    assert result.observed_head != result.source_head
    path = root / CUSTOMER_ISSUE_PATH
    original = path.read_text()
    path.write_text(original.replace("codex-test", "codex-foreign"))
    _git(root, "add", CUSTOMER_ISSUE_PATH); _git(root, "commit", "-qm", "Foreign owner")
    path.write_text(original)
    _git(root, "add", CUSTOMER_ISSUE_PATH); _git(root, "commit", "-qm", "Restore owner")
    with pytest.raises(ValueError, match="protected_history_advanced"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)


@pytest.mark.parametrize("fault", ["copy", "plan", "context"])
def test_valid_sealed_result_cannot_be_copied_or_mutated(tmp_path, monkeypatch, fault):
    _, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True)
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    if fault == "copy": result = copy(result)
    elif fault == "plan": object.__setattr__(result.plan.phase, "title", "Forged title")
    else: result.dependency_contexts[0]["prerequisite"]["context"]["endpoint_profile"] = "operational_v1"
    with pytest.raises(ValueError):
        source.require_verified(result)


@pytest.mark.parametrize("journal", [False, True])
def test_require_verified_rejects_mutated_request_ref_without_repair(tmp_path, monkeypatch, journal):
    _, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, journal=journal)
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    source.require_verified(result)
    original_intent = result.plan.semantic_intent_ref
    mutated_ref = "goal-phase-operational-admission-request:sha256:" + "e" * 64
    object.__setattr__(result.plan.request, "request_ref", mutated_ref)
    for _ in range(2):
        with pytest.raises(ValueError, match="forward_admission_request_reference_invalid"):
            source.require_verified(result)
        assert result.plan.request.request_ref == mutated_ref
        assert result.plan.semantic_intent_ref == original_intent


def test_weak_issuance_registry_releases_live_result(tmp_path, monkeypatch):
    gc.collect()
    baseline = len(source_module._ISSUED)
    _, _, issue, request, source = provider_fixture(tmp_path, monkeypatch)
    result = source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    assert len(source_module._ISSUED) == baseline + 1
    del result
    gc.collect()
    assert len(source_module._ISSUED) == baseline


@pytest.mark.parametrize("external", [False, True])
@pytest.mark.parametrize("native_only", [False, True])
def test_terminal_head_advance_never_registers_verification(tmp_path, monkeypatch, external, native_only):
    gc.collect()
    root, capability, issue, request, source = provider_fixture(
        tmp_path, monkeypatch, dependency=external or native_only, external=external, native_only=native_only)
    count_before = len(source_module._ISSUED)
    resolver_type = type(capability)
    resolve = resolver_type.resolve_goal_path
    terminal = source.terminal
    armed = False
    advanced = False
    target_path = CUSTOMER_EXTERNAL_PATH if external else CUSTOMER_PATH

    def terminal_checks(verified, *, expected_head):
        nonlocal armed
        armed = True
        terminal(verified, expected_head=expected_head)

    def resolve_then_advance(resolver, path):
        nonlocal advanced
        location = resolve(resolver, path)
        if armed and path == target_path and not advanced:
            (root / "concurrent.txt").write_text("Advance during terminal source I/O")
            _git(root, "add", "concurrent.txt")
            _git(root, "commit", "-qm", "Concurrent terminal advance")
            advanced = True
        return location

    monkeypatch.setattr(source, "terminal", terminal_checks)
    monkeypatch.setattr(resolver_type, "resolve_goal_path", resolve_then_advance)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    assert advanced
    assert len(source_module._ISSUED) == count_before


@pytest.mark.parametrize("native_only", [False, True])
def test_terminal_external_target_replacement_never_registers_verification(tmp_path, monkeypatch, native_only):
    gc.collect()
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch, dependency=True, external=True, native_only=native_only)
    count_before = len(source_module._ISSUED)
    terminal = source.terminal
    replaced = False

    def terminal_checks(verified, *, expected_head):
        nonlocal replaced
        external = tmp_path / "outside-goal.md"
        target = root / CUSTOMER_EXTERNAL_PATH
        external.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(external)
        replaced = True
        terminal(verified, expected_head=expected_head)

    monkeypatch.setattr(source, "terminal", terminal_checks)
    with pytest.raises(NativeGoalResolverError, match="native_goal_target_unresolvable"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    assert replaced
    assert len(source_module._ISSUED) == count_before


def test_changed_restored_goal_and_sibling_source_refuse(tmp_path, monkeypatch):
    root, _, issue, request, source = provider_fixture(tmp_path, monkeypatch)
    path = root / CUSTOMER_PATH
    original = path.read_bytes()
    path.write_bytes(original.replace(b"Shared", b"Foreign"))
    # Ensure this is a real committed path effect even if the fixture title changes.
    if path.read_bytes() == original:
        path.write_bytes(original + b"\nUnknown appended direction\n")
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Change Goal authority")
    path.write_bytes(original)
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Restore identical Goal authority")
    with pytest.raises(ValueError, match="protected_history_advanced"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
    current = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "--detach", request.expected_source_revision_ref)
    (root / "sibling.txt").write_text("Side branch with identical Goal")
    _git(root, "add", "sibling.txt")
    _git(root, "commit", "-qm", "Sibling publication epoch")
    sibling = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "--detach", current)
    request = replace(request, expected_source_revision_ref=sibling)
    with pytest.raises(ValueError, match="source_lineage_unproven"):
        source.verify(goal_path=CUSTOMER_PATH, publication_issue_path=issue, request=request)
