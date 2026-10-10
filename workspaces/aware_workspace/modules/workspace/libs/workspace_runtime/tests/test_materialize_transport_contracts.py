from __future__ import annotations

import json
import statistics
import time
from dataclasses import replace

import pytest
from aware_workspace_materialize_transport import (
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeCommandProposalV3,
    WorkspaceMaterializeCommandSelectorV2,
    WorkspaceMaterializeHostResultV2,
    WorkspaceMaterializeHostResultV4,
    WorkspaceMaterializeSelectedRootV1,
    WorkspaceMaterializeTransportContractError,
    empty_workspace_materialize_host_counters_v2,
)
from aware_workspace_materialize_transport.contracts import (
    WorkspaceMaterializeHostOperationReceiptV1,
    WorkspaceMaterializeHostResultV3,
)


def _proposal(*, plan_only: bool = True) -> WorkspaceMaterializeCommandProposalV2:
    return WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="workspace-materialize-attempt:test",
        participant_checkout_root="/participant/checkout",
        workspace_manifest_name="aware.workspace.toml",
        selectors=(
            WorkspaceMaterializeCommandSelectorV2.create(
                selector_kind="module", selector_ref="module:api"
            ),
            WorkspaceMaterializeCommandSelectorV2.create(
                selector_kind="package", selector_ref="package:api"
            ),
        ),
        plan_only=plan_only,
    )


def _counters(proposal: WorkspaceMaterializeCommandProposalV2, **values: int):
    result = dict(empty_workspace_materialize_host_counters_v2(proposal))
    result.update(values)
    return tuple(result.items())


def test_exact_address_v3_and_selected_host_v4_are_canonical() -> None:
    proposal = WorkspaceMaterializeCommandProposalV3.create(
        attempt_ref="workspace-materialize-attempt:exact",
        participant_checkout_root="/participant/checkout",
        workspace_manifest_name="workspaces/kernel/aware.workspace.toml",
        package_address=("Kernel", "storage", "ontology"),
        plan_only=True,
    )
    assert WorkspaceMaterializeCommandProposalV3.from_wire(proposal.to_wire()) == proposal
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref=proposal.attempt_ref,
            participant_checkout_root=proposal.participant_checkout_root,
            workspace_manifest_name=proposal.workspace_manifest_name,
            package_address=("Kernel", "storage/foreign", "ontology"),
            plan_only=True,
        )
    counters = dict(empty_workspace_materialize_host_counters_v2(proposal))
    counters.update(authority_preflight_count=1, selected_package_count=1)
    predecessor = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal,
        outcome="blocked",
        terminal_stage="selection",
        host_timing_ns=(
            ("request_decode", 1), ("host_admission", 2),
            ("catalog_observation", 0), ("selection", 3),
        ),
        host_total_ns=6,
        host_counters=tuple(counters.items()),
        plan_result_wire=None,
        graph_result_wire=None,
        failure_kind="authority",
        failure_code="graph_host_not_ready",
    )
    receipt = WorkspaceMaterializeHostOperationReceiptV1.create(
        operation_ref="workspace-materialize-operation:00000000-0000-4000-8000-000000000001",
        parent_ref="workspace-command-parent:00000000-0000-4000-8000-000000000002",
        epoch_ref="workspace-command-epoch:00000000-0000-4000-8000-000000000003",
        attempt_ref=proposal.attempt_ref,
        proposal_digest=proposal.proposal_digest,
        declaration_scope_digest="sha256:" + "a" * 64,
    )
    root = WorkspaceMaterializeSelectedRootV1.create(
        workspace_handle="Kernel",
        workspace_manifest_path=proposal.workspace_manifest_name,
        module_id="storage",
        package_id="ontology",
        semantic_package_name="storage-ontology",
        semantic_version="1.0",
        source_identity_digest="sha256:" + "b" * 64,
    )
    result = WorkspaceMaterializeHostResultV4.create(
        predecessor=predecessor, operation_receipt=receipt, selected_root=root,
    )
    assert WorkspaceMaterializeHostResultV4.from_wire(
        result.to_wire(), proposal=proposal
    ) == result
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        replace(root, source_identity_digest="sha256:" + "c" * 64).__post_init__()
    foreign = WorkspaceMaterializeCommandProposalV3.create(
        attempt_ref=proposal.attempt_ref,
        participant_checkout_root=proposal.participant_checkout_root,
        workspace_manifest_name=proposal.workspace_manifest_name,
        package_address=("Kernel", "storage", "foreign"),
        plan_only=True,
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        WorkspaceMaterializeHostResultV4.from_wire(result.to_wire(), proposal=foreign)


def test_v2_proposal_and_contextual_results_are_byte_canonical() -> None:
    proposal = _proposal()
    assert WorkspaceMaterializeCommandProposalV2.from_wire(proposal.to_wire()) == proposal
    result = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal,
        outcome="succeeded",
        terminal_stage="graph_plan",
        host_timing_ns=tuple(
            (stage, 1)
            for stage in (
                "request_decode", "host_admission", "catalog_observation",
                "selection", "graph_plan",
            )
        ),
        host_total_ns=6,
        host_counters=_counters(
            proposal,
            authority_preflight_count=1,
            catalog_observation_count=2,
            selected_package_count=1,
            graph_node_count=1,
        ),
        plan_result_wire=b'{"contract":"plan"}',
        graph_result_wire=None,
        failure_kind=None,
        failure_code=None,
    )
    decoded = WorkspaceMaterializeHostResultV2.from_wire(
        result.to_wire(), proposal=proposal
    )
    assert decoded == result
    assert decoded.plan_result_wire() == b'{"contract":"plan"}'
    assert decoded.graph_result_wire() is None


def test_host_operation_receipt_v3_is_canonical_and_source_bound() -> None:
    proposal = _proposal()
    predecessor = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal,
        outcome="blocked",
        terminal_stage="host_admission",
        host_timing_ns=(("request_decode", 1), ("host_admission", 2)),
        host_total_ns=3,
        host_counters=_counters(proposal, authority_preflight_count=1),
        plan_result_wire=None,
        graph_result_wire=None,
        failure_kind="authority",
        failure_code="graph_host_not_ready",
    )
    receipt = WorkspaceMaterializeHostOperationReceiptV1.create(
        operation_ref="workspace-materialize-operation:00000000-0000-4000-8000-000000000001",
        parent_ref="workspace-command-parent:00000000-0000-4000-8000-000000000002",
        epoch_ref="workspace-command-epoch:00000000-0000-4000-8000-000000000003",
        attempt_ref=proposal.attempt_ref,
        proposal_digest=proposal.proposal_digest,
        declaration_scope_digest="sha256:" + "a" * 64,
    )
    result = WorkspaceMaterializeHostResultV3.create(
        predecessor=predecessor, operation_receipt=receipt
    )
    assert WorkspaceMaterializeHostResultV3.from_wire(
        result.to_wire(), proposal=proposal
    ) == result
    assert WorkspaceMaterializeHostOperationReceiptV1.from_wire(
        receipt.to_wire()
    ) == receipt

    foreign_proposal = WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="workspace-materialize-attempt:foreign",
        participant_checkout_root=proposal.participant_checkout_root,
        workspace_manifest_name=proposal.workspace_manifest_name,
        selectors=proposal.selectors,
        plan_only=proposal.plan_only,
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        WorkspaceMaterializeHostResultV3.from_wire(
            result.to_wire(), proposal=foreign_proposal
        )
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        WorkspaceMaterializeHostResultV3.create(
            predecessor=predecessor,
            operation_receipt=WorkspaceMaterializeHostOperationReceiptV1.create(
                operation_ref=receipt.operation_ref,
                parent_ref=receipt.parent_ref,
                epoch_ref=receipt.epoch_ref,
                attempt_ref="workspace-materialize-attempt:foreign",
                proposal_digest=receipt.proposal_digest,
                declaration_scope_digest=receipt.declaration_scope_digest,
            ),
        )
    poison = json.loads(result.to_wire())
    poison["operation_receipt_wire_text"] = receipt.to_wire().decode().replace(
        receipt.declaration_scope_digest, "sha256:" + "b" * 64
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError):
        WorkspaceMaterializeHostResultV3.from_wire(
            json.dumps(poison, sort_keys=True, separators=(",", ":")).encode(),
            proposal=proposal,
        )


def test_v1_unknown_duplicate_reordered_and_boolean_poisons_fail_closed() -> None:
    proposal = _proposal()
    root = json.loads(proposal.to_wire())
    for mutation in (
        lambda value: value.__setitem__("contract", "aware.workspace.materialize-command-proposal.v1"),
        lambda value: value.__setitem__("package_refs", ["package:api"]),
        lambda value: value.__setitem__("plan_only", 1),
        lambda value: value["selectors"].reverse(),
    ):
        poisoned = json.loads(proposal.to_wire())
        mutation(poisoned)
        with pytest.raises((TypeError, WorkspaceMaterializeTransportContractError)):
            WorkspaceMaterializeCommandProposalV2.from_wire(
                json.dumps(poisoned, sort_keys=True, separators=(",", ":")).encode()
            )
    with pytest.raises(WorkspaceMaterializeTransportContractError, match="duplicate"):
        WorkspaceMaterializeCommandProposalV2.from_wire(
            proposal.to_wire()[:-1] + b',"attempt_ref":"duplicate"}'
        )
    with pytest.raises(WorkspaceMaterializeTransportContractError, match="canonical"):
        WorkspaceMaterializeCommandProposalV2.from_wire(
            json.dumps(root, indent=2, sort_keys=True).encode()
        )


def test_nested_wire_digest_presence_and_context_substitution_fail_closed() -> None:
    proposal = _proposal(plan_only=False)
    result = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal,
        outcome="succeeded",
        terminal_stage="graph_execution",
        host_timing_ns=tuple((stage, 1) for stage in (
            "request_decode", "host_admission", "catalog_observation", "selection",
            "graph_plan", "graph_admission", "graph_execution",
        )),
        host_total_ns=8,
        host_counters=_counters(
            proposal, authority_preflight_count=1, catalog_observation_count=2,
            selected_package_count=1, graph_node_count=1,
            graph_admission_count=1, graph_execution_count=1,
        ),
        plan_result_wire=b'{"contract":"plan"}',
        graph_result_wire=b'{"contract":"graph"}',
        failure_kind=None,
        failure_code=None,
    )
    root = json.loads(result.to_wire())
    for field, value in (
        ("plan_result_wire_text", '{"contract":"foreign"}'),
        ("graph_result_wire_digest", "sha256:" + "9" * 64),
        ("host_total_ns", True),
    ):
        poison = dict(root)
        poison[field] = value
        with pytest.raises(WorkspaceMaterializeTransportContractError):
            WorkspaceMaterializeHostResultV2.from_wire(
                json.dumps(poison, sort_keys=True, separators=(",", ":")).encode(),
                proposal=proposal,
            )
    foreign = WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="workspace-materialize-attempt:foreign",
        participant_checkout_root=proposal.participant_checkout_root,
        workspace_manifest_name=proposal.workspace_manifest_name,
        selectors=proposal.selectors,
        plan_only=proposal.plan_only,
    )
    with pytest.raises(WorkspaceMaterializeTransportContractError, match="correlation"):
        WorkspaceMaterializeHostResultV2.from_wire(result.to_wire(), proposal=foreign)


def test_proposal_derive_encode_100_selector_performance() -> None:
    samples: list[float] = []
    for run in range(32):
        started = time.perf_counter_ns()
        selectors = tuple(
            WorkspaceMaterializeCommandSelectorV2.create(
                selector_kind="package", selector_ref=f"package:{index:03d}"
            )
            for index in range(100)
        )
        proposal = WorkspaceMaterializeCommandProposalV2.create(
            attempt_ref=f"attempt:perf-{run}",
            participant_checkout_root=None,
            workspace_manifest_name="aware.workspace.toml",
            selectors=selectors,
            plan_only=True,
        )
        proposal.to_wire()
        elapsed = (time.perf_counter_ns() - started) / 1_000_000
        if run >= 2:
            samples.append(elapsed)
    ordered = sorted(samples)
    assert statistics.median(samples) < 25.0
    assert ordered[27] < 50.0
