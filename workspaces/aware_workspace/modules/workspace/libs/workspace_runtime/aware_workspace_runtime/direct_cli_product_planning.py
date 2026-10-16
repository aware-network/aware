"""Original product planning input into the existing public CLI graph planner.

The original factory declares source roles and owns dependency meaning. This
composition delivers retained bytes and keeps the Code source/context alive.
Ordinary local backing reads supply observations, never genesis approval.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import cast
from uuid import uuid4

from aware_code_retained_registry_policy_runtime import (
    product_planning_source as planning,
)
from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore

from . import direct_command_composition as composition
from .declaration_product_membership import WorkspaceDeclarationProductCorrespondence
from .declaration_scope_admission import WorkspaceSelectedPackageSource
from .direct_cli_selected_host import DirectCLISelectedProduct
from .materialization_graph_host_composition import (
    WorkspaceMaterializationGraphBacking,
    plan_current_workspace_materialization_graph,
)
from .materialization_graph_planner import WorkspaceSemanticRootCodePlan
from .materialization_selection import (
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
)
from .semantic_catalog_host import WorkspaceJointCatalogResolvers
from .semantic_dependency_graph import WorkspaceSemanticMaterializationGraphPlanResult


@dataclass(frozen=True, slots=True)
class DirectCLIProductGraphPlan:
    plan: WorkspaceSemanticMaterializationGraphPlanResult
    wire: bytes
    elapsed_ns: int


async def plan_direct_cli_selected_product(
    command: composition._DirectWorkspaceCommandResources,
    selected: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
) -> DirectCLIProductGraphPlan:
    """Plan under the same original command; return only after source cleanup."""
    if type(product) is not DirectCLISelectedProduct or product.host.staged.command is not command:
        raise TypeError("original selected command/product required")
    composition._require_live_direct_workspace_command(command)
    if composition._POLICY_HOSTS.get(product.host.code_host) is not product.host.staged:
        raise ContractViolation("original selected Code host differs")
    sources = command.sources
    if type(sources) is not composition._DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration sources required")
    host = product.host.code_host
    intent, required_product = derive_selected_root_intent(host, product.policy)
    contribution, = product.host.staged.product_contributions
    issuer = sources.declaration_scope_runtime
    declared = planning.read_product_planning_input_declaration(host, product.policy, contribution)
    if len(declared.source_contracts) != 1:
        raise ContractViolation("complete product source-role mapping unavailable")
    source_role, = declared.source_contracts
    evidence = issuer.inspect_selected_package_evidence(selected)
    coordinates = tuple(
        SemanticInputSourceCoordinate(
            body.relative_path,
            SemanticValueCoordinate(
                source_role.role, source_role.contract, body.body_ref,
                ContentDigest(body.content_digest), body.size_bytes,
            ),
        ) for body in evidence.bodies
    )
    started_ns = time.perf_counter_ns()
    result = None
    with issuer.original_pre_request_input(
        selected, use_ref="workspace-product-planning:" + str(uuid4()),
        stage="source_planning", source_coordinates=coordinates,
        context_contracts=declared.context_contracts,
    ) as expected:
        input_host = SemanticInputProducerHost()
        original_source = None
        try:
            registration = planning.register_product_planning_input_producer(
                host, product.policy, contribution, input_host=input_host,
            )
            original_source = await planning.execute_product_planning_input(
                host, product.policy, contribution, input_host=input_host,
                registration=registration, expected=expected,
            )
            pair = product.host.catalog_pair
            if type(pair) is not WorkspaceJointCatalogResolvers or pair is not command.catalog_host._result:
                raise TypeError("original current paired catalog required")
            if any(type(item) is not WorkspaceDeclarationProductCorrespondence for item in pair.source_correspondences):
                raise TypeError("original product source correspondence required")
            package = expected.package_identity.package
            if package.package_ref != product.package_ref:
                raise ContractViolation("original product package differs")
            target_validator = issuer.bind_original_graph_target_validator((selected,))
            # Fixed ordinary Workspace filesystem placement; no Service is
            # contacted. Plan reads cannot authorize predecessor/genesis use.
            state_root = composition._direct_workspace_cli_state_root(
                sources.observation_runtime._session.binding.root_path
            ) / "materialization"
            state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            backing = WorkspaceMaterializationGraphBacking(
                state_root=state_root,
                repository_binding_ref=evidence.repository_binding_ref,
                state_store=SqliteLocalOperationalStateStore(state_root / "heads.sqlite3"),
            )
            selection = WorkspaceMaterializationSelectionProposal.create(
                selectors=(WorkspaceMaterializationRootSelector.create(
                    selector_kind="package", selector_ref=package.package_ref,
                ),),
            )
            root_plan = WorkspaceSemanticRootCodePlan.create(
                package_ref=package.package_ref, code_intent=intent,
                required_result_products=(required_product,),
                required_semantic_provider_keys=(product.provider_key,),
            )
            epoch = command.catalog_host.read_initial_epoch()
            expected_epoch = command.catalog_host.read_initial_publication()
            plan, wire = await plan_current_workspace_materialization_graph(
                code_host=host, catalog_host=command.catalog_host,
                epoch=epoch, expected_epoch=expected_epoch,
                original_sources=(original_source,), package_closure=(package,),
                backing=backing, selection=selection, root_plans=(root_plan,),
                source_only_target_validator=target_validator,
                source_correspondences=cast(
                    tuple[WorkspaceDeclarationProductCorrespondence, ...],
                    pair.source_correspondences,
                ),
            )
            result = DirectCLIProductGraphPlan(plan, wire, time.perf_counter_ns() - started_ns)
        finally:
            original_source = None
            # If release refuses, preserve the input host for Code's retry and
            # do not return a successful plan. Never dispose borrowed admissions.
            planning.close_product_planning_sources(host)
            input_host.close()
    composition._require_live_direct_workspace_command(command)
    assert result is not None
    return result
