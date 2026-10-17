"""Original product planning input into the existing public CLI graph planner.

The original factory declares source roles and owns dependency meaning. This
composition delivers retained bytes and keeps the Code source/context alive.
Ordinary local backing reads supply observations, never genesis approval.
"""

from __future__ import annotations

import inspect
import time
from contextlib import ExitStack
from dataclasses import dataclass
from typing import cast
from uuid import uuid4

from aware_code_retained_registry_policy_runtime import (
    direct_host,
)
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
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)
from aware_code_semantic_contract_runtime.source_origin import SOURCE_ORIGIN_REF
from aware_code_semantic_contract_runtime.source_selection import SOURCE_SELECTION_REF
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore

from . import direct_command_composition as composition
from .declaration_product_membership import (
    WorkspaceDeclarationProductCorrespondence,
    read_declaration_product_correspondence_package,
)
from .declaration_scope_admission import (
    WorkspaceDeclarationScopeRuntime,
    WorkspaceSelectedPackageSource,
)
from .direct_cli_product_demands import DirectCLIProductDemands
from .direct_cli_selected_host import (
    DirectCLIProductParticipant,
    DirectCLISelectedProduct,
)
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
    demands: DirectCLIProductDemands | None = None


def _bind_target_source_preparation():
    retain = WorkspaceDeclarationScopeRuntime._retain_targets
    code = retain.__code__

    def prepare(issuer, source, addresses):
        if (
            type(issuer) is not WorkspaceDeclarationScopeRuntime
            or inspect.getattr_static(issuer, "_retain_targets") is not retain
            or retain.__code__ is not code
        ):
            raise ContractViolation("original planning target source retainer changed")
        retain(issuer, source, addresses)
        if inspect.getattr_static(issuer, "_retain_targets") is not retain or retain.__code__ is not code:
            raise ContractViolation("original planning target source retainer changed")

    return prepare


_prepare_target_sources = _bind_target_source_preparation()


async def plan_direct_cli_selected_product(
    command: composition._DirectWorkspaceCommandResources,
    selected: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
    *, retention: ExitStack | None = None, allow_unused_sources: bool = False,
) -> DirectCLIProductGraphPlan:
    """Plan once; close sources or retain their originals for graph execution."""
    if retention is not None and type(retention) is not ExitStack:
        raise TypeError("original planning retention stack required")
    if type(allow_unused_sources) is not bool:
        raise TypeError("exact candidate planning mode required")
    if (
        type(product) is not DirectCLISelectedProduct
        or type(product.host) is not composition.DirectWorkspaceSelectedHost
        or product.host.staged.command is not command
    ):
        raise TypeError("original selected command/product required")
    composition._require_live_direct_workspace_command(command)
    if (
        composition._selected_input_identity_lookup(composition._POLICY_HOSTS, product.host.code_host)
        is not product.host.staged
    ):
        raise ContractViolation("original selected Code host differs")
    sources = command.sources
    if type(sources) is not composition._DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration sources required")
    host = product.host.code_host
    hosted = product.host
    issuer = sources.declaration_scope_runtime
    participants = product.participants
    if (
        type(participants) is not tuple or not 1 <= len(participants) <= 256
        or any(type(item) is not DirectCLIProductParticipant for item in participants)
        or any(tuple.__len__(item) != 5 for item in participants)
    ):
        raise ContractViolation("complete original planning participants required")
    # Read immutable tuple storage, never replaceable named-field descriptors.
    rows = tuple(tuple(tuple.__iter__(item)) for item in participants)
    if (
        any(
            type(source) is not WorkspaceSelectedPackageSource
            or type(policy) is not direct_host.AdmittedRegistryPolicy
            or type(contribution) is not SelectedProviderProductContribution
            or type(package_ref) is not str or type(provider_key) is not str
            for source, provider_key, package_ref, policy, contribution in rows
        )
        or rows[0][0] is not selected or rows[0][3] is not product.policy
        or rows[0][2] != product.package_ref or rows[0][1] != product.provider_key
        or len({id(row[0]) for row in rows}) != len(rows)
        or len({row[2] for row in rows}) != len(rows)
    ):
        raise ContractViolation("complete original planning participants required")
    intent, required_product = derive_selected_root_intent(host, product.policy)
    root_key, root_ref, root_policy = rows[0][1], rows[0][2], rows[0][3]

    def check_selection():
        if (
            product.host is not hosted or product.policy is not root_policy
            or product.participants is not participants
            or type(product.provider_key) is not str or product.provider_key != root_key
            or type(product.package_ref) is not str or product.package_ref != root_ref
            or type(product.requested_role) is not str or product.requested_role != required_product.role
        ):
            raise ContractViolation("original planning participant set changed")

    check_selection()
    pair = product.host.catalog_pair
    if type(pair) is not WorkspaceJointCatalogResolvers or pair is not command.catalog_host._result:
        raise TypeError("original current paired catalog required")
    if any(type(item) is not WorkspaceDeclarationProductCorrespondence for item in pair.source_correspondences):
        raise TypeError("original product source correspondence required")
    correspondences = cast(tuple[WorkspaceDeclarationProductCorrespondence, ...], pair.source_correspondences)
    package_refs = {row[2] for row in rows}
    started_ns = time.perf_counter_ns()
    result = None
    input_hosts = []
    original_sources = []
    packages = []
    evidence = None
    demands = None
    handed_off = False
    with ExitStack() as expectations:
        try:
            for source, _key, package_ref, policy, contribution in rows:
                check_selection()
                original = read_selected_provider_product_contribution(contribution)
                if original.binding.provider_key != _key:
                    raise ContractViolation("original planning provider differs")
                declared = planning.read_product_planning_input_declaration(
                    host, policy, contribution,
                )
                # The existing graph law authenticates every exposed direct
                # target before owner demand planning. Nonparticipating targets
                # need original membership, not an executable factory or a
                # fabricated planning source. Reuse the issuer's retained path.
                entry = pair.workspace.package(package_ref)
                if any(
                    target_ref not in package_refs
                    for dependency in entry.authored_dependencies
                    for target_ref in dependency.admitted_target_package_refs
                ):
                    semantic = composition._original_group_method(issuer, "_semantic_values", source)
                    addresses = semantic[6]
                    _prepare_target_sources(issuer, source, addresses)
                evidence = issuer.inspect_selected_package_evidence(source)
                if (len(declared.source_contracts) != 1
                    or any(item.contract in (SOURCE_SELECTION_REF, SOURCE_ORIGIN_REF)
                           for item in declared.context_contracts)):
                    from .direct_cli_product_execution import (
                        prepare_direct_cli_selected_planning_source,
                    )

                    input_host, expected = await prepare_direct_cli_selected_planning_source(
                        command, source, product, retention=expectations,
                    )
                else:
                    source_role, = declared.source_contracts
                    coordinates = tuple(
                        SemanticInputSourceCoordinate(
                            body.relative_path,
                            SemanticValueCoordinate(
                                source_role.role, source_role.contract, body.body_ref,
                                ContentDigest(body.content_digest), body.size_bytes,
                            ),
                        ) for body in evidence.bodies
                    )
                    expected = expectations.enter_context(issuer.original_pre_request_input(
                        source, use_ref="workspace-product-planning:" + str(uuid4()),
                        stage="source_planning", source_coordinates=coordinates,
                        context_contracts=declared.context_contracts,
                    ))
                    input_host = SemanticInputProducerHost()
                    input_hosts.append(input_host)
                package = expected.package_identity.package
                if package.package_ref != package_ref:
                    raise ContractViolation("original product package differs")
                packages.append(package)
                registration = planning.register_product_planning_input_producer(
                    host, policy, contribution, input_host=input_host,
                )
                original_sources.append(await planning.execute_product_planning_input(
                    host, policy, contribution, input_host=input_host,
                    registration=registration, expected=expected,
                ))
                check_selection()
            target_validator = issuer.bind_original_graph_target_validator(
                tuple(row[0] for row in rows)
            )
            # Fixed ordinary Workspace filesystem placement; no Service is
            # contacted. Plan reads cannot authorize predecessor/genesis use.
            state_root = composition._direct_workspace_cli_state_root(
                sources.observation_runtime._session.binding.root_path
            ) / "materialization"
            state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            assert evidence is not None
            backing = WorkspaceMaterializationGraphBacking(
                state_root=state_root,
                repository_binding_ref=evidence.repository_binding_ref,
                state_store=SqliteLocalOperationalStateStore(state_root / "heads.sqlite3"),
            )
            selection = WorkspaceMaterializationSelectionProposal.create(
                selectors=(WorkspaceMaterializationRootSelector.create(
                    selector_kind="package", selector_ref=packages[0].package_ref,
                ),),
            )
            root_plan = WorkspaceSemanticRootCodePlan.create(
                package_ref=packages[0].package_ref, code_intent=intent,
                required_result_products=(required_product,),
                required_semantic_provider_keys=(root_key,),
            )
            epoch = command.catalog_host.read_initial_epoch()
            expected_epoch = command.catalog_host.read_initial_publication()
            if retention is not None:
                demands = DirectCLIProductDemands(tuple(zip(packages, original_sources, strict=True)))
            plan, wire = await plan_current_workspace_materialization_graph(
                code_host=host, catalog_host=command.catalog_host,
                epoch=epoch, expected_epoch=expected_epoch,
                original_sources=tuple(original_sources),
                package_closure=tuple(sorted(packages, key=lambda item: item.package_ref)),
                backing=backing, selection=selection, root_plans=(root_plan,),
                source_only_target_validator=target_validator,
                source_correspondences=tuple(item for item in correspondences
                    if read_declaration_product_correspondence_package(item).package_ref in package_refs),
                retained_product_demands=demands,
                allow_unused_sources=allow_unused_sources,
            )
            result = DirectCLIProductGraphPlan(plan, wire, time.perf_counter_ns() - started_ns, demands)
            check_selection()
            if retention is not None:
                assert demands is not None
                retained = expectations.pop_all()
                for input_host in input_hosts:
                    retained.callback(input_host.close)
                retained.callback(planning.close_product_planning_sources, host)
                retained.callback(demands.close)
                retention.callback(retained.close)
                handed_off = True
        finally:
            original_sources.clear()
            # If release refuses, preserve the input host for Code's retry and
            # do not return a successful plan. Never dispose borrowed admissions.
            if not handed_off:
                if demands is not None:
                    demands.close()
                planning.close_product_planning_sources(host)
                with ExitStack() as close_hosts:
                    for input_host in input_hosts:
                        close_hosts.callback(input_host.close)
    composition._require_live_direct_workspace_command(command)
    assert result is not None
    return result
