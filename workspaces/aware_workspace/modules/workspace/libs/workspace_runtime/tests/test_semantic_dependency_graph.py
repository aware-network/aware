from __future__ import annotations

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime import (
    WorkspaceDependencyTargetResolution,
    WorkspaceSemanticMaterializationGraph,
    WorkspaceSemanticMaterializationGraphEdge,
    WorkspaceSemanticMaterializationGraphNode,
    WorkspaceSemanticMaterializationLocalRootAssociation,
    WorkspaceSemanticPackageHeadObservation,
    WorkspaceSemanticPlannedDependencyInput,
    WorkspaceSemanticPlanningDemandClosure,
    decode_workspace_dependency_target_resolution,
    decode_workspace_semantic_materialization_graph,
    encode_workspace_dependency_target_resolution,
    encode_workspace_semantic_materialization_graph,
)
from aware_workspace_runtime.semantic_dependency_graph import (
    WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION,
    WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
    WorkspaceMaterializationPackageOccurrenceV4,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _contract() -> SemanticContractRef:
    return SemanticContractRef(
        key="aware.api.contract", version="1", schema_digest=_digest("schema")
    )


def _package(ref: str, kind: str) -> SemanticPackageCoordinate:
    return SemanticPackageCoordinate(
        package_ref=ref,
        package_kind=kind,
        manifest_digest=_digest(f"manifest:{ref}"),
    )


def _head(
    package: SemanticPackageCoordinate, state: str = "stale"
) -> WorkspaceSemanticPackageHeadObservation:
    return WorkspaceSemanticPackageHeadObservation.create(
        package=package,
        source_identity_digest=_digest(f"source:{package.package_ref}"),
        profile_binding_digest=_digest(f"profile:{package.package_ref}"),
        state=state,
        predecessor_head_revision=None if state == "missing" else 3,
        predecessor_head_digest=(
            None if state == "missing" else _digest(f"head:{package.package_ref}")
        ),
        historical_execution_input_closure_digest=(
            _digest("historical") if state == "current" else None
        ),
        expected_post_revision=(
            1 if state == "missing" else 3 if state == "current" else 4
        ),
        expected_post_head_digest=(
            _digest(f"head:{package.package_ref}") if state == "current" else None
        ),
    )


def _node(
    package: SemanticPackageCoordinate, state: str = "stale"
) -> WorkspaceSemanticMaterializationGraphNode:
    return WorkspaceSemanticMaterializationGraphNode.create(
        package=package,
        package_entry_digest=_digest(f"entry:{package.package_ref}"),
        participation_policy_digest=_digest(f"policy:{package.package_ref}"),
        source_identity_digest=_digest(f"source:{package.package_ref}"),
        local_code_match_digest=_digest(f"match:{package.package_ref}"),
        composed_intent_digest=_digest(f"intent:{package.package_ref}"),
        demand_set_digest=_digest(f"demands:{package.package_ref}"),
        planning_demand_closure_digest=_digest(f"closure:{package.package_ref}"),
        head_observation=_head(package, state),
    )


def _graph() -> tuple[
    WorkspaceSemanticMaterializationGraph,
    tuple[WorkspaceSemanticMaterializationLocalRootAssociation, ...],
]:
    api = _node(_package("package:api", "api"))
    sdk = _node(_package("package:sdk", "sdk"))
    nodes = tuple(
        sorted((api, sdk), key=lambda item: canonical_json_bytes(item.to_wire()))
    )
    edge = WorkspaceSemanticMaterializationGraphEdge.create(
        consumer_node_digest=sdk.node_digest,
        target_node_digest=api.node_digest,
        demand_digest=_digest("sdk-needs-api"),
        target_resolution_digest=_digest("resolution"),
    )
    roots = tuple(
        sorted(
            (
                WorkspaceSemanticMaterializationLocalRootAssociation.create(
                    package_entry_digest=node.package_entry_digest,
                    participation_policy_digest=node.participation_policy_digest,
                    code_intent_digest=node.composed_intent_digest,
                    required_result_product_digests=(
                        _digest(f"requirement:{node.package.package_ref}"),
                    ),
                    node_digest=node.node_digest,
                )
                for node in nodes
            ),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    return WorkspaceSemanticMaterializationGraph.create(
        local_root_associations=roots, nodes=nodes, edges=(edge,)
    ), roots


def test_planning_closure_contains_demands_not_future_values() -> None:
    planned = WorkspaceSemanticPlannedDependencyInput.create(
        demand_digest=_digest("demand"),
        target_resolution_digest=_digest("resolution"),
        required_result_role="api_contract",
        result_product_contract=_contract(),
    )
    closure = WorkspaceSemanticPlanningDemandClosure.create(
        consumer_package=_package("package:sdk", "sdk"),
        planned_dependency_inputs=(planned,),
    )
    wire = closure.to_wire()
    assert "value_ref" not in str(wire)
    assert "future" not in str(wire)


@pytest.mark.parametrize("state", ("missing", "current", "stale"))
def test_head_observation_state_revision_laws(state: str) -> None:
    assert _head(_package("package:api", "api"), state).state == state
    with pytest.raises((ContractViolation, TypeError)):
        WorkspaceSemanticPackageHeadObservation.create(
            package=_package("package:api", "api"),
            source_identity_digest=_digest("source:package:api"),
            profile_binding_digest=_digest("profile:package:api"),
            state=state,
            predecessor_head_revision=True,
            predecessor_head_digest=_digest("head"),
            historical_execution_input_closure_digest=None,
            expected_post_revision=4,
            expected_post_head_digest=None,
        )


def test_v4_head_observation_preserves_version_without_current_reuse() -> None:
    legacy = _head(_package("package:sdk", "sdk"))
    occurrence = WorkspaceMaterializationPackageOccurrenceV4(
        repository_ref="repository:aware",
        workspace_ref="workspace:kernel",
        module_ref="module:sdk",
        package_id="sdk",
        package_root="workspaces/aware_kernel/modules/sdk",
        manifest_relative_path="workspaces/aware_kernel/modules/sdk/aware.module.toml",
    )
    assert legacy.to_wire()["contract"] == WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION
    assert "stored_head_contract" not in legacy.to_wire()
    values = dict(
        package=legacy.package,
        source_identity_digest=legacy.source_identity_digest,
        profile_binding_digest=legacy.profile_binding_digest,
        state="stale",
        predecessor_head_revision=legacy.predecessor_head_revision,
        predecessor_head_digest=legacy.predecessor_head_digest,
        historical_execution_input_closure_digest=None,
        expected_post_revision=legacy.expected_post_revision,
        expected_post_head_digest=None,
        stored_head_contract=WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
        stored_package_occurrence=occurrence,
    )
    observed = WorkspaceSemanticPackageHeadObservation.create(**values)
    assert (
        observed.to_wire()["contract"]
        == WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2
    )
    assert (
        observed.to_wire()["stored_head_contract"]
        == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
    )
    assert observed.observation_digest != legacy.observation_digest
    assert observed.to_wire()["stored_package_occurrence"] == occurrence.to_wire()
    predecessor_node = _node(legacy.package)
    successor_node = WorkspaceSemanticMaterializationGraphNode.create(
        package=predecessor_node.package,
        package_entry_digest=predecessor_node.package_entry_digest,
        participation_policy_digest=predecessor_node.participation_policy_digest,
        source_identity_digest=predecessor_node.source_identity_digest,
        local_code_match_digest=predecessor_node.local_code_match_digest,
        composed_intent_digest=predecessor_node.composed_intent_digest,
        demand_set_digest=predecessor_node.demand_set_digest,
        planning_demand_closure_digest=predecessor_node.planning_demand_closure_digest,
        head_observation=observed,
    )
    assert successor_node.node_digest != predecessor_node.node_digest
    assert (
        successor_node.to_wire()["head_observation"]["contract"]
        == WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2
    )
    with pytest.raises(ContractViolation, match="stale execution"):
        WorkspaceSemanticPackageHeadObservation.create(
            **{**values, "state": "current"}
        )
    with pytest.raises(ContractViolation, match="unsupported"):
        WorkspaceSemanticPackageHeadObservation.create(
            **{**values, "stored_head_contract": "foreign.head.v4"}
        )
    with pytest.raises(ContractViolation, match="requires its exact package occurrence"):
        WorkspaceSemanticPackageHeadObservation.create(
            **{**values, "stored_package_occurrence": None}
        )
    with pytest.raises(ContractViolation, match="cannot carry a V4 occurrence"):
        WorkspaceSemanticPackageHeadObservation.create(
            **{**values, "stored_head_contract": None}
        )
    with pytest.raises(ContractViolation, match="digest mismatched"):
        replace(
            observed,
            stored_package_occurrence=replace(occurrence, package_id="other"),
        ).__post_init__()


def test_target_and_graph_codecs_are_context_bound() -> None:
    target = WorkspaceDependencyTargetResolution.create(
        demand_digest=_digest("demand"),
        target_package_entry_digest=_digest("entry"),
        target_local_code_match_digest=_digest("match"),
        composed_target_intent_digest=_digest("intent"),
        participation_policy_digest=_digest("policy"),
        required_result_role="api_contract",
        result_product_contract=_contract(),
        head_observation=_head(_package("package:api", "api"), "current"),
    )
    target_wire = encode_workspace_dependency_target_resolution(target)
    assert (
        decode_workspace_dependency_target_resolution(target_wire, expected=target)
        == target
    )

    graph, roots = _graph()
    graph_wire = encode_workspace_semantic_materialization_graph(
        graph, local_root_associations=roots
    )
    assert (
        decode_workspace_semantic_materialization_graph(
            graph_wire, expected=graph, local_root_associations=roots
        )
        == graph
    )
    with pytest.raises(ContractViolation):
        decode_workspace_semantic_materialization_graph(
            graph_wire + b"\n", expected=graph, local_root_associations=roots
        )


def test_graph_rejects_cycle_and_absent_endpoint() -> None:
    graph, roots = _graph()
    first = graph.nodes[0]
    reverse = WorkspaceSemanticMaterializationGraphEdge.create(
        consumer_node_digest=graph.edges[0].target_node_digest,
        target_node_digest=graph.edges[0].consumer_node_digest,
        demand_digest=_digest("reverse"),
        target_resolution_digest=_digest("reverse-resolution"),
    )
    edges = tuple(
        sorted(
            (*graph.edges, reverse),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    with pytest.raises(ContractViolation, match="cycle"):
        WorkspaceSemanticMaterializationGraph.create(
            local_root_associations=roots, nodes=graph.nodes, edges=edges
        )
    absent = WorkspaceSemanticMaterializationGraphEdge.create(
        consumer_node_digest=first.node_digest,
        target_node_digest=_digest("absent"),
        demand_digest=_digest("absent-demand"),
        target_resolution_digest=_digest("absent-resolution"),
    )
    with pytest.raises(ContractViolation, match="endpoint absent"):
        WorkspaceSemanticMaterializationGraph.create(
            local_root_associations=roots, nodes=graph.nodes, edges=(absent,)
        )


def test_graph_local_identity_excludes_global_catalog_and_selection() -> None:
    graph, _ = _graph()
    wire = graph.to_wire()
    assert "catalog_root_digest" not in wire
    assert "selection_resolution_digest" not in wire
    assert "workspace_intent_admission_digest" not in str(wire)
    assert "expected_publication_head" not in str(wire)
    with pytest.raises(ContractViolation, match="graph digest"):
        replace(graph, graph_digest=_digest("forged"))
