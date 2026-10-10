import ast
from copy import copy
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    decode_dependency_product_input,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyProductInput,
)
from aware_workspace_runtime import (
    WorkspaceFulfilledDependencyProductV3,
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceSemanticMaterializationMembershipResolver,
    WorkspaceSemanticMaterializationNodePreparation,
)
from aware_workspace_runtime.materialization_membership_catalog import (
    _issue_workspace_semantic_materialization_membership_catalog,
)
from aware_workspace_runtime.semantic_dependency_inputs import (
    WorkspaceSemanticDependencySource,
    code_dependency_input_body,
    code_dependency_products,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationRequestV3,
)
from test_materialization_graph_planner import _composition, _digest


async def fixture(two=False):
    planner, selection, roots, *_ = _composition(two_dependencies=two)
    plan = await planner.plan(
        selection_proposal=selection, requested_root_code_plans=roots
    )
    bindings = plan.graph_execution_binding.ordered_node_bindings
    node = next(item for item in bindings if item.package.package_kind == "sdk")
    products, bodies = [], []
    for resolution in node.incoming_target_resolutions:
        target = next(
            item
            for item in bindings
            if item.package_entry.entry_digest == resolution.target_package_entry_digest
        )
        wire = target.package.package_ref.encode()
        coordinate = SemanticValueCoordinate(
            resolution.required_result_role,
            resolution.result_product_contract,
            "result:" + target.package.package_ref,
            ContentDigest.of_bytes(wire),
            len(wire),
        )
        request = WorkspaceSemanticMaterializationRequestV3.create(
            package=target.package,
            result_coordinate=coordinate,
            source_identity_digest=target.package_entry.source_identity_digest,
            code_intent_digest=target.code_intent.intent_digest,
            code_match_digest=target.code_match.match_digest,
            planning_input_digest=target.planning_input_digest,
            execution_input_closure_digest=_digest("closure"),
            operation_result_digest=_digest("operation"),
            expected_head_revision=0,
        )
        head = WorkspaceSemanticMaterializationHeadV3.create(request=request)
        h1, h2 = (
            WorkspaceSemanticMaterializationHeadRereadEvidenceV3.create(
                observation_role=role,
                materialization_head_revision=1,
                head=head,
            )
            for role in ("dependency_h1", "dependency_h2")
        )
        products.append(
            WorkspaceFulfilledDependencyProductV3.create(
                plan_result=plan,
                consumer_node_digest=node.node_digest,
                target_node_digest=target.node_digest,
                target_resolution=resolution,
                head_h1=h1,
                head_h2=h2,
                consumed_body_coordinate=coordinate,
            )
        )
        bodies.append(SemanticBody(coordinate, wire))
    preparation = WorkspaceSemanticMaterializationNodePreparation(
        plan.graph_execution_binding.binding_digest,
        node,
        "proof:session",
        "proof:participant",
        WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
        0,
        0,
        0,
        None,
        tuple(products),
        tuple(bodies),
    )
    return plan, preparation, planner._workspace


@pytest.mark.asyncio
@pytest.mark.parametrize("two", [False, True])
async def test_generic_bridge_projects_code_values_and_preserves_evidence_link(two):
    plan, prep, membership = await fixture(two)
    context = WorkspaceSemanticDependencySource(membership).read_dependencies(
        prep.node_execution_binding.package
    )
    assert len(context.dependencies) == 1 + two
    inputs = code_dependency_products(plan=plan, preparation=prep)
    assert type(inputs) is SemanticDependencyProductInput
    assert len(inputs.products) == 1 + two
    assert {p.provenance_digest for p in inputs.products} == {
        p.fulfillment_digest for p in prep.ordered_fulfilled_products
    }
    assert inputs.source_identity_digest == context.source_identity_digest
    body = code_dependency_input_body(plan=plan, preparation=prep)
    assert decode_dependency_product_input(body.canonical_body) == inputs
    assert inputs.intent == prep.node_execution_binding.code_intent


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["missing", "body", "graph", "stale"])
async def test_workspace_rejects_inexact_evidence_before_code_projection(change):
    plan, prep, _ = await fixture()
    if change == "missing":
        prep = replace(prep, ordered_dependency_bodies=())
    elif change == "graph":
        prep = replace(prep, graph_execution_binding_digest=_digest("foreign"))
    elif change == "body":
        body = prep.ordered_dependency_bodies[0]
        body = SemanticBody(
            replace(body.coordinate, value_ref="foreign"), body.canonical_body
        )
        prep = replace(prep, ordered_dependency_bodies=(body,))
    else:
        product = copy(prep.ordered_fulfilled_products[0])
        object.__setattr__(product, "result_head_revision", 7)
        prep = replace(prep, ordered_fulfilled_products=(product,))
    with pytest.raises(ValueError):
        code_dependency_products(plan=plan, preparation=prep)


@pytest.mark.asyncio
async def test_source_checks_membership_liveness_and_exact_package():
    _, prep, membership = await fixture()
    package = prep.node_execution_binding.package
    live = [True]
    source = WorkspaceSemanticDependencySource(
        WorkspaceSemanticMaterializationMembershipResolver(
            _issue_workspace_semantic_materialization_membership_catalog(
                catalog=membership.catalog, host_liveness=lambda: live[0]
            )
        )
    )
    source.read_dependencies(package)
    with pytest.raises(ValueError, match="semantic_membership_package_mismatch"):
        source.read_dependencies(replace(package, manifest_digest=_digest("other")))
    live[0] = False
    with pytest.raises(ValueError, match="membership host admission is not live"):
        source.read_dependencies(package)


def test_plain_dictionary_is_not_membership_admission():
    with pytest.raises(TypeError):
        WorkspaceSemanticDependencySource({})


def test_bridge_imports_only_code_and_workspace():
    path = (
        Path(__file__).resolve().parents[1]
        / "aware_workspace_runtime/semantic_dependency_inputs.py"
    )
    imports = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "aware_code_semantic_contract_runtime"}
