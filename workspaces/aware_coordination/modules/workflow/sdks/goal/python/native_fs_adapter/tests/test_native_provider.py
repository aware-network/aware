from __future__ import annotations

import hashlib
from importlib import import_module
import subprocess
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from aware_goal_operational_runtime import (
    GoalDependencyRelation,
    GoalLanePhase,
    GoalLanePhaseDefinitionV1,
    GoalLanePhaseGate,
    GoalLanePhaseGateObservation,
    GoalLanePhaseGateOutcome,
    GoalLanePhaseState,
    GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition,
    GoalLanePhaseWorkRole,
    GoalPhaseContractBundleV1,
    GoalPhaseCoordinate,
    GoalPhaseDependency,
    GoalPhaseExecutionAuthorityV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    GoalNativeLaneAuthorityV1,
    attach_goal_phase_native_carrier,
    GoalPhaseOperationJournalEntryV1,
    GoalPhaseOperationJournalV1,
    GoalPhaseUnresolvedDependencyV1,
)
from aware_goal_sdk import (
    attach_goal_phase_native_document,
    extract_goal_phase_native_document,
)
from aware_goal_sdk.phase_operation import (
    GoalPhaseObserveEligibilityRequestV1,
    GoalPhaseOperationClient,
    decode_goal_phase_observe_eligibility_request,
    decode_goal_phase_observe_eligibility_result,
    issue_goal_phase_eligibility_decision_ref,
)
from aware_goal_sdk.phase_direction import (
    GoalPhaseDirectionClient,
    GoalPhaseDirectionCurrentnessRequestV1,
    GoalPhaseDirectionObserveRequestV1,
)
from aware_goal_native_fs_adapter.phase_direction import (
    NativeGitGoalPhaseDirectionProvider,
)
from aware_goal_native_fs_adapter.phase_operation import (
    NativeGitGoalPhaseOperationProvider,
)

GOAL = "goal/2026-09-26/eligibility-proof"
PATH = "docs/goals/2026/09/26/goal-2026-09-26-eligibility-proof.md"
EXTERNAL_GOAL = "goal/2026-09-26/eligibility-external"
EXTERNAL_PATH = "docs/goals/2026/09/26/goal-2026-09-26-eligibility-external.md"
CUSTOMER_PATH = "customer/objectives/2026/09/26/goal-2026-09-26-eligibility-proof.md"
CUSTOMER_EXTERNAL_PATH = "customer/objectives/2026/09/26/goal-2026-09-26-eligibility-external.md"
CUSTOMER_ISSUE_PATH = "work/issues/2026/09/26/fb-2026-09-26-customer-work.md"
CUSTOMER_ISSUE_TAG = "fb/2026-09-26/customer-work"
CUSTOMER_ISSUE_LINK = (
    "[Customer Issue](../../../../../work/issues/2026/09/26/"
    "fb-2026-09-26-customer-work.md)"
)
COMPATIBILITY = (
    "# Goal: Eligibility proof\n\n"
    "- Slug: `eligibility-proof`\n"
    f"- Tag: `{GOAL}`\n"
    "- Status: `Active`\n- Priority: `P1`\n- Owner: `codex-test`\n\n"
    "## Lane Map\n\n"
    "| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
    "| `runtime` | Runtime | `codex-test` | Ready | `TBD:first` | Pending | Pending | Runtime |\n\n"
    "## Forward Plan By Lane\n\n"
    "| Lane | Next Issue | Gate |\n| --- | --- | --- |\n"
    "| `runtime` | `TBD:first` | First gate. |\n\n"
    "## Lane Sequences\n\n### `runtime`\n\n"
    "| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |\n"
    "| ---: | --- | --- | --- | --- | --- | --- | --- |\n"
    "| 1 | `first` | Pending | `[ ]` | `TBD:first` | First gate. | Planned | `codex-test` | Pending |\n"
    "| 2 | `later` | Pending | `[ ]` | `TBD:later` | Later gate. | Planned | `codex-test` | Pending |\n\n"
    "## Integrated Updates (append-only)\n\n"
).encode()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args), cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _source(
    tmp_path: Path,
    *,
    goal_path: str = PATH,
    dependency: bool = False,
    unresolved: bool = False,
    operational: bool = True,
    accepted_predecessor: bool = False,
    external_dependency: bool = False,
    v3: bool = False,
    current_issue_ref: str | None = None,
):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.invalid")
    first = GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(GOAL, "runtime", "first"),
        ordinal=1,
        title="First",
        intent="Prove eligibility.",
        gate=GoalLanePhaseGate(
            gate_key="first", promise="First gate.",
            gate_contract_ref="contract:first", evidence_schema_ref="evidence:first",
        ),
    )
    later = GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(GOAL, "runtime", "later"),
        ordinal=2,
        title="Later",
        intent="Remain definition-only.",
        gate=GoalLanePhaseGate(
            gate_key="later", promise="Later gate.",
            gate_contract_ref="contract:later", evidence_schema_ref="evidence:later",
        ),
    )
    phase = GoalLanePhase(
        coordinate=first.coordinate, title=first.title or "", ordinal=1,
        intent=first.intent or "", state=GoalLanePhaseState.ACTIVE, gate=first.gate,
        work_associations=(
            (GoalLanePhaseWork(
                association_ref="goal-phase-work:customer",
                issue_ref=(
                    current_issue_ref.rsplit("](", 1)[1].removesuffix(")")
                    if current_issue_ref.startswith("[") else current_issue_ref
                ),
                role=GoalLanePhaseWorkRole.IMPLEMENTATION,
                disposition=GoalLanePhaseWorkDisposition.CURRENT,
                admitted_at="2026-09-26T12:00:00Z",
                receipt_ref="goal-phase-work-admission:customer",
            ),)
            if current_issue_ref is not None else ()
        ),
    )
    predecessor_phase = GoalLanePhase(
        coordinate=later.coordinate, title=later.title or "", ordinal=2,
        intent=later.intent or "", state=GoalLanePhaseState.ACCEPTED,
        gate=later.gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="gate-observation:later",
            gate_digest=later.gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED,
            evaluator_ref="evaluator:later",
            evidence_refs=("evidence:later",),
            source_revision_refs=("historical-source:later",),
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="historical-currentness:later",
        ),),
        last_receipt_ref="goal-phase-acceptance:sha256:" + "a" * 64,
    )
    dependencies = (
        (
            GoalPhaseDependency(
                owner_goal_tag=GOAL,
                dependency_key="first-requires-later",
                dependent=first.coordinate,
                prerequisite=(
                    GoalPhaseCoordinate(EXTERNAL_GOAL, "runtime", "later")
                    if external_dependency else later.coordinate
                ),
                required_gate_digest=later.gate.gate_digest,
                relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
                reason="Explicit prerequisite for coverage proof.",
            ),
        )
        if dependency else ()
    )
    compatibility = (
        COMPATIBILITY.replace(b"TBD:first", current_issue_ref.encode("utf-8"))
        .replace(b"| Ready |", b"| Active |")
        if current_issue_ref is not None else COMPATIBILITY
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
        definitions=(first, later),
        operational_bundle=GoalPhaseContractBundleV1(
            phases=((phase,) if operational else ()) + (
                (predecessor_phase,) if accepted_predecessor else ()
            ), dependencies=dependencies,
        ),
        unresolved_dependencies=(
            (
                GoalPhaseUnresolvedDependencyV1(
                    owner_goal_tag=GOAL,
                    dependency_key="first-requires-external",
                    dependent=first.coordinate,
                    prerequisite=GoalPhaseCoordinate(
                        "goal/2026-09-26/external", "runtime", "external"
                    ),
                    relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
                    reason="Exact external Gate remains unresolved.",
                ),
            )
            if unresolved else ()
        ),
        source_refs=("repository-path:" + goal_path,),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    if v3:
        entry = GoalPhaseOperationJournalEntryV1(
            operation_kind="approve_pursuit", decision="approve",
            coordinate=first.coordinate, gate_digest=first.gate.gate_digest,
            source_preimage_ref=document.document_ref,
            actor_ref="identity:human-one",
            action_occurrence_ref="actor-action-occurrence:sha256:" + "1" * 64,
            policy_ref="goal-phase-approval-policy:sha256:" + "2" * 64,
            policy_digest="sha256:" + "3" * 64,
            idempotency_key="approve-first", delta_ref="goal-phase-delta:sha256:" + "4" * 64,
            event_ref="goal-phase-event:sha256:" + "5" * 64,
        )
        document = GoalPhaseNativeDocumentV3(
            goal_tag=document.goal_tag,
            compatibility_projection_sha256=document.compatibility_projection_sha256,
            compatibility_projection_byte_count=document.compatibility_projection_byte_count,
            definitions=document.definitions,
            operational_bundle=document.operational_bundle,
            unresolved_dependencies=document.unresolved_dependencies,
            source_refs=document.source_refs,
            execution_authority=document.execution_authority,
            phase_operation_journal=GoalPhaseOperationJournalV1((entry,)),
        )
    source = attach_goal_phase_native_document(compatibility, document)
    target = root / goal_path
    target.parent.mkdir(parents=True)
    target.write_bytes(source)
    _git(root, "add", "--", goal_path)
    _git(root, "commit", "-qm", "Publish native Goal")
    request = GoalPhaseObserveEligibilityRequestV1(
        source_locator_ref="repository-path:" + goal_path, goal_tag=GOAL, lane_key="runtime", phase_key="first",
        expected_goal_sha256="sha256:" + hashlib.sha256(source).hexdigest(),
        expected_native_document_ref=document.document_ref,
        expected_gate_digest=first.gate.gate_digest,
    )
    return root, request


def _publish_external_source(root: Path, *, goal_path: str = EXTERNAL_PATH) -> None:
    compatibility = COMPATIBILITY.replace(
        b"eligibility-proof", b"eligibility-external"
    )
    coordinate = GoalPhaseCoordinate(EXTERNAL_GOAL, "runtime", "later")
    gate = GoalLanePhaseGate(
        gate_key="later", promise="Later gate.",
        gate_contract_ref="contract:later", evidence_schema_ref="evidence:later",
    )
    definition = GoalLanePhaseDefinitionV1(
        coordinate=coordinate, ordinal=2, title="Later",
        intent="Remain definition-only.", gate=gate,
    )
    phase = GoalLanePhase(
        coordinate=coordinate, title="Later", ordinal=2,
        intent="Remain definition-only.", state=GoalLanePhaseState.ACCEPTED,
        gate=gate,
        gate_observations=(GoalLanePhaseGateObservation(
            observation_ref="gate-observation:external-later",
            gate_digest=gate.gate_digest,
            outcome=GoalLanePhaseGateOutcome.SATISFIED,
            evaluator_ref="evaluator:external-later",
            evidence_refs=("evidence:external-later",),
            source_revision_refs=("historical-source:external-later",),
            evaluated_at="2026-09-26T16:00:00Z",
            currentness_ref="historical-currentness:external-later",
        ),),
        last_receipt_ref="goal-phase-acceptance:sha256:" + "a" * 64,
    )
    document = GoalPhaseNativeDocumentV2(
        goal_tag=EXTERNAL_GOAL,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(compatibility).hexdigest(),
        compatibility_projection_byte_count=len(compatibility),
        definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1(phases=(phase,), dependencies=()),
        unresolved_dependencies=(),
        source_refs=("repository-path:" + goal_path,),
        execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref="goal-phase-native-compatibility-parity:sha256:" + "1" * 64,
            proposal_aggregate_ref="goal-phase-native-operational-bootstrap-proposal:sha256:" + "2" * 64,
            coordinator_acceptance_ref="goal-phase-native-operational-bootstrap-coordinator-acceptance:sha256:" + "3" * 64,
        ),
    )
    external_path = root / goal_path
    external_path.parent.mkdir(parents=True, exist_ok=True)
    external_path.write_bytes(attach_goal_phase_native_document(compatibility, document))
    _git(root, "add", "--", goal_path)
    _git(root, "commit", "-qm", "Publish external native Goal")


def _native_capability(root: Path, monkeypatch: pytest.MonkeyPatch) -> object:
    """Exercise Protocol source without claiming an installed distribution."""

    repo = next(
        parent for parent in Path(__file__).resolve().parents
        if (parent / "workspaces/aware_kernel/modules/protocol").is_dir()
    )
    protocol_root = repo / "workspaces/aware_kernel/modules/protocol"
    for source in (
        protocol_root / "libs/runtime/python",
        protocol_root / "sdks/protocol/python",
        protocol_root / "libs/fs_adapter/python",
    ):
        monkeypatch.syspath_prepend(str(source))
    manifest = root / "aware.protocol.toml"
    manifest.write_text(
        '''aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v2"
semantic_version = 2
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.goal]
profile = "aware.goal.phase.markdown.v1"
role = "authority"
root = "customer/objectives"
path_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"
[records.issue]
profile = "aware.issue.markdown.v1"
role = "authority"
root = "work/issues"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
''',
        encoding="utf-8",
    )
    protocol = import_module("aware_protocol_fs_adapter")
    admission = protocol.admit_native_goal_resolver(
        repository_root=root, manifest_path=manifest
    )
    assert admission.capability is not None
    return admission.capability


def _publish_customer_issue(root: Path, *, tag: str = CUSTOMER_ISSUE_TAG) -> None:
    target = root / CUSTOMER_ISSUE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Issue: Customer work\n\n"
        f"- Tag: {tag}\n"
        "- Status: In Progress\n"
        "- Owner: codex-test\n\n"
        "## Ownership Scope\n"
        "- `customer/objectives/2026/09/26/goal-2026-09-26-eligibility-proof.md`\n",
        encoding="utf-8",
    )
    _git(root, "add", "--", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Publish customer Issue")


def _publish_native_only_lane(
    root: Path, *, keep_shared_lane: bool = True
) -> tuple[str, str, str]:
    """Add one native lane without adding a compatibility Lane Map row."""

    target = root / CUSTOMER_PATH
    compatibility, document = extract_goal_phase_native_document(target.read_bytes())
    coordinate = GoalPhaseCoordinate(GOAL, "foundation", "native-first")
    native_definition = replace(
        document.definitions[0],
        coordinate=coordinate,
        ordinal=1,
        title="Native first",
        intent="Observe native direction without invented lane authority.",
    )
    native_phase = replace(
        document.operational_bundle.phases[0],
        coordinate=coordinate,
        title="Native first",
        intent=native_definition.intent or "",
        work_associations=(),
    )
    definitions = (
        document.definitions + (native_definition,)
        if keep_shared_lane else (native_definition,)
    )
    phases = (
        document.operational_bundle.phases + (native_phase,)
        if keep_shared_lane else (native_phase,)
    )
    advanced = replace(
        document,
        definitions=definitions,
        operational_bundle=GoalPhaseContractBundleV1(
            phases=phases,
            dependencies=document.operational_bundle.dependencies,
        ),
    )
    source = attach_goal_phase_native_document(compatibility, advanced)
    target.write_bytes(source)
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Publish native-only lane")
    return (
        "sha256:" + hashlib.sha256(source).hexdigest(),
        advanced.document_ref,
        native_definition.gate.gate_digest,
    )


@pytest.mark.parametrize("v3", [False, True])
def test_native_only_lane_has_direction_but_no_invented_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool
) -> None:
    root, original = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3)
    goal_sha, document_ref, gate_digest = _publish_native_only_lane(root)
    capability = _native_capability(root, monkeypatch)
    eligibility = NativeGitGoalPhaseOperationProvider(capability)
    shared = eligibility.observe_eligibility(
        replace(
            original,
            expected_goal_sha256=goal_sha,
            expected_native_document_ref=document_ref,
        )
    )
    assert (shared["status"], shared["eligibility"]) == ("observed", "eligible")
    native = eligibility.observe_eligibility(
        GoalPhaseObserveEligibilityRequestV1(
            source_locator_ref="repository-path:" + CUSTOMER_PATH,
            goal_tag=GOAL,
            lane_key="foundation",
            phase_key="native-first",
            expected_goal_sha256=goal_sha,
            expected_native_document_ref=document_ref,
            expected_gate_digest=gate_digest,
        )
    )
    assert (native["status"], native["reasons"]) == (
        "refused", ["lane_authority_absent"]
    )

    direction = GoalPhaseDirectionClient(
        NativeGitGoalPhaseDirectionProvider(capability)
    )
    receipt = direction.observe_phase_direction(
        GoalPhaseDirectionObserveRequestV1(
            CUSTOMER_PATH, GOAL, "foundation", "native-first"
        )
    )
    currentness = direction.verify_phase_direction_currentness(
        GoalPhaseDirectionCurrentnessRequestV1(CUSTOMER_PATH, receipt)
    )
    assert currentness["status"] == "current"


def test_markdown_only_lane_still_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, original = _source(tmp_path, goal_path=CUSTOMER_PATH)
    goal_sha, document_ref, _ = _publish_native_only_lane(
        root, keep_shared_lane=False
    )
    result = NativeGitGoalPhaseOperationProvider(
        _native_capability(root, monkeypatch)
    ).observe_eligibility(
        replace(
            original,
            expected_goal_sha256=goal_sha,
            expected_native_document_ref=document_ref,
        )
    )
    assert (result["status"], result["reasons"]) == (
        "refused", ["lane_set_mismatch"]
    )


@pytest.mark.parametrize("journal", [False, True])
@pytest.mark.parametrize("terminal_fault", [None, "target", "head"])
def test_v4_portable_direction_reads_exact_carrier_without_v1_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, journal: bool, terminal_fault: str | None,
) -> None:
    root, original = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=journal)
    _publish_native_only_lane(root)
    target = root / CUSTOMER_PATH
    compatibility, prior = extract_goal_phase_native_document(target.read_bytes())
    lane = GoalNativeLaneAuthorityV1(
        goal_tag=GOAL, lane_key="foundation", role="Foundation",
        owner_profile="provider_execution_v1", owner_ref="codex-test",
        operational_state="active", state_detail=None, hold_authority_refs=(),
        current_work_association_ref=None,
    )
    document = GoalPhaseNativeDocumentV4(
        goal_tag=prior.goal_tag,
        compatibility_projection_sha256=prior.compatibility_projection_sha256,
        compatibility_projection_byte_count=prior.compatibility_projection_byte_count,
        definitions=prior.definitions, operational_bundle=prior.operational_bundle,
        unresolved_dependencies=prior.unresolved_dependencies,
        source_refs=prior.source_refs, execution_authority=prior.execution_authority,
        native_lane_authorities=(lane,), operation_journal_profile="v1" if journal else "none",
        phase_operation_journal=prior.phase_operation_journal if journal else None,
    )
    target.write_bytes(attach_goal_phase_native_carrier(compatibility, document))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Publish V4 reader fixture")
    head = _git(root, "rev-parse", "HEAD")
    capability = _native_capability(root, monkeypatch)
    status = _git(root, "status", "--porcelain")
    provider = NativeGitGoalPhaseDirectionProvider(capability)
    client = GoalPhaseDirectionClient(provider)
    receipt = client.observe_phase_direction(GoalPhaseDirectionObserveRequestV1(
        CUSTOMER_PATH, GOAL, "foundation", "native-first",
    ))
    assert receipt["document_ref"] == document.document_ref
    verification_request = GoalPhaseDirectionCurrentnessRequestV1(CUSTOMER_PATH, receipt)
    assert client.verify_phase_direction_currentness(verification_request)["status"] == "current"
    old_transport = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(replace(
        original, expected_goal_sha256="sha256:" + hashlib.sha256(target.read_bytes()).hexdigest(),
        expected_native_document_ref=document.document_ref,
    ))
    assert old_transport["reasons"] == ["document_profile_unsupported"]
    assert _git(root, "rev-parse", "HEAD") == head
    assert _git(root, "status", "--porcelain") == status
    (root / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    _git(root, "add", "unrelated.txt")
    _git(root, "commit", "-qm", "Unrelated descendant")
    advanced = client.verify_phase_direction_currentness(verification_request)
    assert (advanced["status"], advanced["projection_currentness"], advanced["replay_disposition"]) == (
        "current", "advanced", "reobserved_unchanged",
    )
    changed = replace(document, native_lane_authorities=(replace(lane, owner_ref="codex-other"),))
    target.write_bytes(attach_goal_phase_native_carrier(compatibility, changed))
    _git(root, "add", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Change native lane owner")
    stale = client.verify_phase_direction_currentness(verification_request)
    assert stale["status"] == "stale"
    assert "document_advanced" in stale["reasons"]
    if terminal_fault is not None:
        def interleave() -> None:
            if terminal_fault == "target":
                foreign = tmp_path / "foreign.md"
                foreign.write_bytes(target.read_bytes())
                target.unlink()
                target.symlink_to(foreign)
            else:
                successor = replace(changed, native_lane_authorities=(
                    replace(lane, owner_ref="codex-terminal"),
                ))
                target.write_bytes(attach_goal_phase_native_carrier(compatibility, successor))
                _git(root, "add", CUSTOMER_PATH)
                _git(root, "commit", "-qm", "Terminal source advance")
        monkeypatch.setattr(provider, "_before_success", interleave)
        with pytest.raises(ValueError, match=(
            "native_goal_target_unresolvable" if terminal_fault == "target"
            else "repository_head_advanced"
        )):
            client.observe_phase_direction(GoalPhaseDirectionObserveRequestV1(
                CUSTOMER_PATH, GOAL, "foundation", "native-first",
            ))


@pytest.mark.parametrize("v3", [False, True])
def test_native_discovery_derives_exact_request_from_committed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool
) -> None:
    root, expected = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    (root / "foreign-work.txt").write_text("preserve me\n", encoding="utf-8")
    before_head = _git(root, "rev-parse", "HEAD")
    before_status = _git(root, "status", "--porcelain=v1")

    discovered = provider.discover_eligibility_request(
        goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
    )

    assert discovered == expected
    assert GoalPhaseOperationClient(provider).observe_eligibility(discovered)["status"] == "observed"
    assert _git(root, "rev-parse", "HEAD") == before_head
    assert _git(root, "status", "--porcelain=v1") == before_status


def test_native_discovery_refuses_missing_or_duplicate_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    with pytest.raises(ValueError, match="phase_definition_absent_or_ambiguous"):
        provider.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="absent"
        )
    with pytest.raises(ValueError, match="native_goal_target_outside_binding"):
        provider.discover_eligibility_request(
            goal_path=PATH, lane_key="runtime", phase_key="first"
        )
    duplicate = root / "customer/objectives/2026/09/26/goal-2026-09-26-copy.md"
    duplicate.write_bytes((root / CUSTOMER_PATH).read_bytes())
    _git(root, "add", "--", duplicate.relative_to(root).as_posix())
    _git(root, "commit", "-qm", "Publish duplicate Goal identity")
    with pytest.raises(ValueError, match="goal_source_ambiguous"):
        provider.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )


def test_native_discovery_refuses_changed_manifest_and_return_time_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    manifest = root / "aware.protocol.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n# changed bytes\n", encoding="utf-8")
    with pytest.raises(ValueError, match="native_goal_manifest_changed"):
        provider.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )
    fresh = NativeGitGoalPhaseOperationProvider(
        _native_capability(root, monkeypatch)
    )

    def advance_head() -> None:
        (root / "unrelated.txt").write_text("advanced\n", encoding="utf-8")
        _git(root, "add", "--", "unrelated.txt")
        _git(root, "commit", "-qm", "Advance unrelated HEAD")

    monkeypatch.setattr(fresh, "_before_success", advance_head)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        fresh.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )


def test_native_discovery_refuses_symlink_escape_and_committed_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    target = root / CUSTOMER_PATH
    outside = tmp_path / "outside.md"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(ValueError):
        provider.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )
    target.unlink()
    sibling = target.with_name("other.md")
    sibling.write_bytes(outside.read_bytes())
    target.symlink_to(sibling.name)
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Publish committed Goal symlink")
    with pytest.raises(ValueError, match="committed_goal_regular_file_required"):
        provider.discover_eligibility_request(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )


@pytest.mark.parametrize("v3", [False, True])
def test_native_customer_root_v2_v3_use_real_retained_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool
) -> None:
    root, request = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3)
    capability = _native_capability(root, monkeypatch)
    provider = NativeGitGoalPhaseOperationProvider(capability)
    before = _git(root, "rev-parse", "HEAD")

    result = GoalPhaseOperationClient(provider).observe_eligibility(request)

    assert result["status"] == "observed"
    assert result["eligibility"] == "eligible"
    assert result["source_locator_ref"] == "repository-path:" + CUSTOMER_PATH
    assert result["event_effect"] == result["dispatch_effect"] == "none"
    assert _git(root, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("v3", [False, True])
@pytest.mark.parametrize(
    "issue_ref", [CUSTOMER_ISSUE_TAG, CUSTOMER_ISSUE_PATH, CUSTOMER_ISSUE_LINK]
)
def test_native_customer_issue_uses_admitted_issue_root_and_committed_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, v3: bool, issue_ref: str
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, v3=v3, current_issue_ref=issue_ref
    )
    _publish_customer_issue(root)
    capability = _native_capability(root, monkeypatch)
    result = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)
    assert result["status"] == "observed"
    assert result["eligibility"] == "eligible", result["reasons"]


def test_native_customer_issue_tag_substitution_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG
    )
    _publish_customer_issue(root, tag="fb/2026-09-26/substituted-work")
    capability = _native_capability(root, monkeypatch)
    result = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_authority_ambiguous"]


def test_native_customer_issue_at_use_symlink_escape_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG
    )
    _publish_customer_issue(root)
    capability = _native_capability(root, monkeypatch)
    provider = NativeGitGoalPhaseOperationProvider(capability)
    issue = root / CUSTOMER_ISSUE_PATH
    issue.unlink()
    outside = tmp_path / "outside-issue.md"
    outside.write_text("outside\n", encoding="utf-8")
    issue.symlink_to(outside)
    result = provider.observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_outside_admitted_binding"]


def test_native_customer_issue_committed_symlink_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG
    )
    _publish_customer_issue(root)
    capability = _native_capability(root, monkeypatch)
    issue = root / CUSTOMER_ISSUE_PATH
    issue.unlink()
    issue.symlink_to("fb-2026-09-26-missing.md")
    _git(root, "add", "--", CUSTOMER_ISSUE_PATH)
    _git(root, "commit", "-qm", "Replace Issue with symlink")
    result = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_authority_ambiguous"]


def test_native_customer_issue_duplicate_tag_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG
    )
    _publish_customer_issue(root)
    duplicate = root / "work/issues/2026/09/26/fb-2026-09-26-other.md"
    duplicate.write_bytes((root / CUSTOMER_ISSUE_PATH).read_bytes())
    _git(root, "add", "--", duplicate.relative_to(root).as_posix())
    _git(root, "commit", "-qm", "Publish duplicate Issue tag")
    capability = _native_capability(root, monkeypatch)
    result = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_authority_ambiguous"]


def test_native_customer_issue_template_substitution_has_no_legacy_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG
    )
    _publish_customer_issue(root)
    capability = _native_capability(root, monkeypatch)
    manifest = root / "aware.protocol.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'root = "work/issues"', 'root = "other/issues"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="native_goal_manifest_changed"):
        NativeGitGoalPhaseOperationProvider(capability)
    protocol = import_module("aware_protocol_fs_adapter")
    replacement = protocol.admit_native_goal_resolver(
        repository_root=root, manifest_path=manifest
    ).capability
    assert replacement is not None
    result = NativeGitGoalPhaseOperationProvider(replacement).observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_authority_ambiguous"]


def test_native_customer_repository_substitution_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original, request = _source(tmp_path / "original", goal_path=CUSTOMER_PATH)
    other, _ = _source(tmp_path / "other", goal_path=CUSTOMER_PATH)
    capability = _native_capability(original, monkeypatch)
    _native_capability(other, monkeypatch)
    goal = original / CUSTOMER_PATH
    goal.write_bytes(goal.read_bytes().replace(b"# Goal: Eligibility proof", b"# Goal: Changed proof"))
    _git(original, "add", "--", CUSTOMER_PATH)
    _git(original, "commit", "-qm", "Advance only original repository")
    assert (other / CUSTOMER_PATH).read_bytes() != goal.read_bytes()
    result = NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["goal_source_stale"]


def test_native_customer_goal_does_not_fall_back_to_compatibility_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(tmp_path)
    capability = _native_capability(root, monkeypatch)
    with pytest.raises(ValueError, match="native_goal_target_outside_binding"):
        NativeGitGoalPhaseOperationProvider(capability).observe_eligibility(request)


@pytest.mark.parametrize(
    "goal_path",
    [
        "other/objectives/2026/09/26/goal-2026-09-26-eligibility-proof.md",
        "customer/objectives/2026/09/26/foreign-template.md",
    ],
)
def test_native_provider_refuses_committed_goal_outside_admitted_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, goal_path: str,
) -> None:
    root, request = _source(tmp_path, goal_path=goal_path)
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    before = _git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="native_goal_target_outside_binding"):
        provider.observe_eligibility(request)
    assert _git(root, "rev-parse", "HEAD") == before


@pytest.mark.parametrize(
    "issue_path",
    [
        "other/issues/2026/09/26/fb-2026-09-26-customer-work.md",
        "docs/issues/2026/09/26/fb-2026-09-26-customer-work.md",
        "work/issues/2026/09/26/foreign-template.md",
    ],
)
def test_native_provider_refuses_committed_issue_outside_admitted_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, issue_path: str,
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=issue_path,
    )
    _publish_customer_issue(root)
    foreign = root / issue_path
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_bytes((root / CUSTOMER_ISSUE_PATH).read_bytes())
    _git(root, "add", "--", issue_path)
    _git(root, "commit", "-qm", "Publish identical Issue outside admitted binding")
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    before = _git(root, "rev-parse", "HEAD")
    result = provider.observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_outside_admitted_binding"]
    assert _git(root, "rev-parse", "HEAD") == before


def test_native_provider_refuses_foreign_current_sequence_location_before_tag_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH, current_issue_ref=CUSTOMER_ISSUE_TAG,
    )
    _publish_customer_issue(root)
    goal = root / CUSTOMER_PATH
    compatibility, document = extract_goal_phase_native_document(goal.read_bytes())
    row = b"| `" + CUSTOMER_ISSUE_TAG.encode() + b"` | First gate. |"
    foreign = b"docs/issues/2026/09/26/fb-2026-09-26-customer-work.md"
    changed = compatibility.replace(row, b"| `" + foreign + b"` | First gate. |")
    assert changed != compatibility
    successor = replace(
        document,
        compatibility_projection_sha256="sha256:" + hashlib.sha256(changed).hexdigest(),
        compatibility_projection_byte_count=len(changed),
    )
    source = attach_goal_phase_native_document(changed, successor)
    goal.write_bytes(source)
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Declare foreign current Issue location in sequence")
    request = replace(
        request,
        expected_goal_sha256="sha256:" + hashlib.sha256(source).hexdigest(),
        expected_native_document_ref=successor.document_ref,
    )
    provider = NativeGitGoalPhaseOperationProvider(_native_capability(root, monkeypatch))
    result = provider.observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["issue_outside_admitted_binding"]


def test_native_constructor_rejects_raw_root_and_decoded_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    capability = _native_capability(root, monkeypatch)
    protocol = import_module("aware_protocol_fs_adapter")

    for impostor in (
        root,
        {"repository_root": str(root), "manifest_sha256": getattr(capability, "manifest_sha256")},
        protocol.admit_protocol_manifest(
            repository_root=root, manifest_path=root / "aware.protocol.toml"
        ).admission.to_wire(),
    ):
        with pytest.raises(ValueError, match="native_goal_capability_invalid"):
            NativeGitGoalPhaseOperationProvider(impostor)


def test_native_cross_goal_source_uses_same_binding_and_manifest_currentness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(
        tmp_path, goal_path=CUSTOMER_PATH,
        dependency=True, external_dependency=True,
    )
    _publish_external_source(root, goal_path=CUSTOMER_EXTERNAL_PATH)
    capability = _native_capability(root, monkeypatch)
    provider = NativeGitGoalPhaseOperationProvider(
        capability,
        prerequisite_goal_paths={EXTERNAL_GOAL: CUSTOMER_EXTERNAL_PATH},
    )
    result = GoalPhaseOperationClient(provider).observe_eligibility(request)
    assert result["status"] == "observed"
    assert cast(dict[str, object], result["dependency_gate"])["stale"] == [
        "first-requires-later"
    ]

    outside = NativeGitGoalPhaseOperationProvider(
        capability, prerequisite_goal_paths={EXTERNAL_GOAL: EXTERNAL_PATH}
    ).observe_eligibility(request)
    assert outside["status"] == "refused"
    assert outside["reasons"] == ["prerequisite_source_unavailable"]

    with (root / "aware.protocol.toml").open("a", encoding="utf-8") as manifest:
        manifest.write("\n# same meaning, different bytes\n")
    with pytest.raises(ValueError, match="native_goal_manifest_changed"):
        provider.observe_eligibility(request)


def test_native_committed_symlink_and_duplicate_identity_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(tmp_path, goal_path=CUSTOMER_PATH)
    capability = _native_capability(root, monkeypatch)
    provider = NativeGitGoalPhaseOperationProvider(capability)
    other = root / "customer/objectives/2026/09/26/goal-2026-09-26-another.md"
    other.write_bytes((root / CUSTOMER_PATH).read_bytes())
    _git(root, "add", "--", other.relative_to(root).as_posix())
    _git(root, "commit", "-qm", "Publish duplicate Goal identity")
    duplicate = provider.observe_eligibility(request)
    assert duplicate["status"] == "refused"
    assert duplicate["reasons"] == ["goal_source_ambiguous"]

    target = root / CUSTOMER_PATH
    target.unlink()
    target.symlink_to(other.name)
    _git(root, "add", "--", CUSTOMER_PATH)
    _git(root, "commit", "-qm", "Replace Goal with committed symlink")
    with pytest.raises(ValueError, match="committed_goal_regular_file_required"):
        provider.observe_eligibility(request)


def test_native_return_rechecks_git_head_after_protocol_currentness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, request = _source(tmp_path, goal_path=CUSTOMER_PATH)
    capability = _native_capability(root, monkeypatch)
    provider = NativeGitGoalPhaseOperationProvider(capability)
    revalidate = provider._before_success

    def advance_after_revalidation() -> None:
        revalidate()
        (root / "unrelated.txt").write_text("advance\n", encoding="utf-8")
        _git(root, "add", "--", "unrelated.txt")
        _git(root, "commit", "-qm", "Advance during eligibility")

    monkeypatch.setattr(provider, "_before_success", advance_after_revalidation)
    result = provider.observe_eligibility(request)
    assert result["status"] == "refused"
    assert result["reasons"] == ["repository_head_advanced"]
