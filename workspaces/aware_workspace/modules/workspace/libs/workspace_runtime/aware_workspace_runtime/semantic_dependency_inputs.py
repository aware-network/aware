"""Workspace admission/evidence translated to the single Code consumer contract."""

from __future__ import annotations

from aware_code_semantic_contract_runtime import (
    ContractViolation,
    SemanticBody,
    SemanticDependencyCoordinate,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    dependency_product_input_body,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyProduct,
    SemanticDependencyProductInput,
    SemanticDependencyTarget,
)

from .materialization_graph_coordinator import (
    WorkspaceSemanticMaterializationNodePreparation,
)
from .materialization_membership_catalog import (
    WorkspaceSemanticMaterializationMembershipResolver,
)
from .semantic_dependency_graph import WorkspaceSemanticMaterializationGraphPlanResult


class WorkspaceSemanticDependencySource:
    """Code's dependency-source protocol backed by nominal Workspace membership."""

    def __init__(
        self, membership: WorkspaceSemanticMaterializationMembershipResolver
    ) -> None:
        if type(membership) is not WorkspaceSemanticMaterializationMembershipResolver:
            raise TypeError("admitted Workspace membership resolver required")
        self._membership = membership

    def read_dependencies(
        self, package: SemanticPackageCoordinate
    ) -> SemanticDependencyPlanningInput:
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact Code package coordinate required")
        package.__post_init__()
        entry = self._membership.package(package.package_ref)
        entry.__post_init__()
        if entry.package != package:
            raise ContractViolation("semantic_membership_package_mismatch")
        dependencies = []
        for declaration in entry.authored_dependencies:
            targets = []
            for ref in declaration.admitted_target_package_refs:
                target = self._membership.package(ref)
                target.__post_init__()
                targets.append(
                    SemanticDependencyTarget(
                        target.package, target.owned_semantic_root_refs
                    )
                )
            dependencies.append(
                SemanticAuthoredDependency(
                    declaration.dependency_kind,
                    declaration.dependency_ref,
                    tuple(sorted(targets, key=lambda item: item.package.package_ref)),
                    declaration.allowed_target_constraints,
                )
            )
        # Check host liveness again before releasing the projection.
        self._membership.package(package.package_ref)
        return SemanticDependencyPlanningInput(
            package,
            entry.source_identity_digest,
            tuple(
                sorted(
                    dependencies,
                    key=lambda item: (item.dependency_kind, item.dependency_ref),
                )
            ),
        )


def code_dependency_products(
    *,
    plan: WorkspaceSemanticMaterializationGraphPlanResult,
    preparation: WorkspaceSemanticMaterializationNodePreparation,
) -> SemanticDependencyProductInput:
    """Validate Workspace evidence before projecting provider-neutral values.

    Full head/graph evidence stays in Workspace. The provenance digest is a link
    to that evidence, not an admission token. The host still admits execution.
    """
    if type(plan) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("exact Workspace graph plan required")
    if type(preparation) is not WorkspaceSemanticMaterializationNodePreparation:
        raise TypeError("exact Workspace node preparation required")
    plan.__post_init__()
    preparation.__post_init__()
    execution = plan.graph_execution_binding
    node = preparation.node_execution_binding
    node.validate_graph_context(plan.graph)
    if (
        preparation.graph_execution_binding_digest != execution.binding_digest
        or node not in execution.ordered_node_bindings
    ):
        raise ContractViolation("dependency_graph_context_mismatch")
    resolutions = node.incoming_target_resolutions
    products = preparation.ordered_fulfilled_products
    bodies = preparation.ordered_dependency_bodies
    if not (len(resolutions) == len(products) == len(bodies)):
        raise ContractViolation("dependency_product_closure_incomplete")
    projected = []
    for resolution, product, body in zip(resolutions, products, bodies, strict=True):
        product.validate_context(plan_result=plan)
        if (
            product.consumer_node_digest != node.node_digest
            or product.target_resolution != resolution
            or product.consumed_body_coordinate != body.coordinate
        ):
            raise ContractViolation("dependency_product_context_mismatch")
        projected.append(
            SemanticDependencyProduct(
                resolution.demand_digest,
                SemanticDependencyCoordinate(
                    product.head_h1_reread_evidence.package,
                    body.coordinate.contract,
                    body.coordinate.value_ref,
                    body.coordinate.digest,
                ),
                body,
                product.fulfillment_digest,
            )
        )
    return SemanticDependencyProductInput(
        node.package,
        node.package_entry.source_identity_digest,
        tuple(
            sorted(
                (item.dependency_kind, item.dependency_ref)
                for item in node.package_entry.authored_dependencies
            )
        ),
        node.dependency_demand_set,
        tuple(projected),
        node.code_intent,
    )


def code_dependency_input_body(
    *,
    plan: WorkspaceSemanticMaterializationGraphPlanResult,
    preparation: WorkspaceSemanticMaterializationNodePreparation,
    role: str = "semantic_dependencies",
) -> SemanticBody:
    """Serialize validated products for the existing Code profile input path."""
    return dependency_product_input_body(
        code_dependency_products(plan=plan, preparation=preparation), role=role
    )
