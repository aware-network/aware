"""Workspace-owned backing and host ports for the one materialization graph."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

from aware_code_package_delta_contract import CODE_PACKAGE_DELTA_CONTRACT
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticContractRuntime,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_local_service_runtime import LocalOperationalStateStore
from aware_code_semantic_contract_runtime.selected_provider import (
    AdmittedSemanticProviderRegistration,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)

if TYPE_CHECKING:
    from .direct_command_composition import (
        _DirectWorkspaceStagedCommandResources,
        _SuccessorGraphNodeSourceInputs,
    )

from .materialization_graph_coordinator import (
    WorkspaceMaterializationProductionCutoverHeadV1,
    WorkspaceSemanticMaterializationNodePreparation,
    _WorkspaceSemanticMaterializationGraphHostPorts,
)
from .materialization_graph_planner import (
    WorkspaceSemanticMaterializationGraphPlanner,
    WorkspaceSemanticRootCodePlan,
)
from .declaration_scope_admission import WorkspaceOriginalGraphTargetValidator
from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence
from .materialization_operation import (
    WorkspaceMaterializeOperation,
    WorkspaceMaterializeOperationAdmission,
    WorkspaceMaterializeExecutionPlanResolver,
)
from .materialization_selection import WorkspaceMaterializationSelectionProposal
from .semantic_catalog_host import WorkspaceSemanticCatalogHost
from .materialization_session import WorkspaceMaterializationSessionJournal
from .semantic_dependency_graph import (
    WorkspaceSemanticPackageHeadObservation,
    WorkspaceSemanticMaterializationGraphPlanResult,
)
from .semantic_dependency_graph_codec import (
    decode_workspace_semantic_materialization_graph_plan_result,
    encode_workspace_semantic_materialization_graph_plan_result,
)
from .semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
    DirectoryWorkspaceSemanticMaterializationBodyStore,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublisher,
)


class _WorkspacePackageHeadReader:
    """Resolve planner reuse from the original Workspace package-head store."""

    def __init__(self, publisher: WorkspaceSemanticMaterializationPublisher) -> None:
        if type(publisher) is not WorkspaceSemanticMaterializationPublisher:
            raise TypeError("package head reader publisher must be exact")
        self._publisher = publisher

    async def observe(
        self, *, entry, local_code_match, intent, planning_demand_closure, planning_input_digest
    ):  # type: ignore[no-untyped-def]
        if type(planning_input_digest) is not ContentDigest:
            raise TypeError("package head reader planning input digest must be exact")
        planning_input_digest.__post_init__()
        planning_demand_closure.__post_init__()
        entry.__post_init__()
        local_code_match.__post_init__()
        intent.__post_init__()
        current = self._publisher._read_graph_package_head_evidence(
            entry.package.package_ref,
            observation_role="package_reuse",
        )
        if current is None:
            return WorkspaceSemanticPackageHeadObservation.create(
                package=entry.package,
                source_identity_digest=entry.source_identity_digest,
                profile_binding_digest=local_code_match.selected_binding.binding_digest,
                state="missing",
                predecessor_head_revision=None,
                predecessor_head_digest=None,
                historical_execution_input_closure_digest=None,
                expected_post_revision=1,
                expected_post_head_digest=None,
            )
        current.__post_init__()
        if type(current) is WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
            result_head = current.head
            stored_head_contract = None
            stored_package_occurrence = None
        elif type(current) is WorkspaceSemanticMaterializationHeadRereadEvidenceV4:
            result_head = current.head.base_head
            stored_head_contract = WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
            stored_package_occurrence = current.head.package_occurrence
        else:
            raise TypeError("unsupported Workspace graph package-head evidence")
        required = {
            (item.role, item.contract)
            for item in local_code_match.selected_binding.result_product_contracts
            if item.role in intent.requested_terminal_output_roles
        }
        is_current = (
            stored_head_contract is None
            and result_head.package == entry.package
            and result_head.source_identity_digest == entry.source_identity_digest
            and result_head.code_intent_digest == intent.intent_digest
            and result_head.code_match_digest == local_code_match.match_digest
            and result_head.planning_input_digest == planning_input_digest
            and (
                result_head.result_coordinate.role,
                result_head.result_coordinate.contract,
            )
            in required
        )
        return WorkspaceSemanticPackageHeadObservation.create(
            package=entry.package,
            source_identity_digest=entry.source_identity_digest,
            profile_binding_digest=local_code_match.selected_binding.binding_digest,
            state="current" if is_current else "stale",
            predecessor_head_revision=current.materialization_head_revision,
            predecessor_head_digest=current.materialization_head_digest,
            historical_execution_input_closure_digest=(
                result_head.execution_input_closure_digest if is_current else None
            ),
            expected_post_revision=(
                current.materialization_head_revision
                if is_current
                else current.materialization_head_revision + 1
            ),
            expected_post_head_digest=(
                current.materialization_head_digest if is_current else None
            ),
            stored_head_contract=stored_head_contract,
            stored_package_occurrence=stored_package_occurrence,
        )


async def plan_workspace_materialization_graph(
    *,
    planner: WorkspaceSemanticMaterializationGraphPlanner,
    selection: WorkspaceMaterializationSelectionProposal,
    root_plans: tuple[WorkspaceSemanticRootCodePlan, ...],
) -> tuple[WorkspaceSemanticMaterializationGraphPlanResult, bytes]:
    """Plan and verify one contextual wire through the existing neutral planner."""
    if type(planner) is not WorkspaceSemanticMaterializationGraphPlanner:
        raise TypeError("original Workspace graph planner required")
    plan = await planner.plan(
        selection_proposal=selection,
        requested_root_code_plans=root_plans,
    )
    wire = encode_workspace_semantic_materialization_graph_plan_result(plan)
    decoded = decode_workspace_semantic_materialization_graph_plan_result(
        wire, expected=plan
    )
    if encode_workspace_semantic_materialization_graph_plan_result(decoded) != wire:
        raise RuntimeError("graph plan contextual round-trip failed")
    return decoded, wire


def compose_current_workspace_graph_planner(
    *,
    code_host: object,
    catalog_host: WorkspaceSemanticCatalogHost,
    epoch: object,
    expected_epoch: object,
    original_sources: tuple[object, ...],
    package_closure: tuple[SemanticPackageCoordinate, ...],
    backing: WorkspaceMaterializationGraphBacking,
    source_only_target_validator: WorkspaceOriginalGraphTargetValidator | None = None,
    source_correspondences: tuple[WorkspaceV3GraphSourceCorrespondence, ...] = (),
) -> WorkspaceSemanticMaterializationGraphPlanner:
    """Bind current original owner readers to the sole neutral graph planner.

    The fixed command supplies its original Code host, published epoch and
    Workspace-selected package closure. Code authenticates every returned owner
    reader; Workspace checks current membership before constructing the planner.
    """
    from aware_code_retained_registry_policy_runtime.planning_source_composition import (
        compose_retained_planning_sources,
        validate_composed_retained_planning_source,
    )

    if type(catalog_host) is not WorkspaceSemanticCatalogHost:
        raise TypeError("original Workspace catalog host required")
    if type(backing) is not WorkspaceMaterializationGraphBacking:
        raise TypeError("original Workspace graph backing required")
    if type(original_sources) is not tuple:
        raise TypeError("original planning source tuple required")
    catalog_host.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    code_admission = catalog_host.read_code_catalog_for_epoch(
        epoch, expected=expected_epoch
    )
    pair = catalog_host._result
    if pair is None or pair.code_admission is not code_admission:
        raise RuntimeError("original current catalog pair unavailable")
    source = compose_retained_planning_sources(original_sources)
    validate_composed_retained_planning_source(
        code_host, source, package_closure
    )
    if source_only_target_validator is not None:
        if type(source_only_target_validator) is not WorkspaceOriginalGraphTargetValidator:
            raise TypeError("original Workspace graph target validator required")
        source_only_target_validator.validate_source_packages(package_closure)
    if type(source_correspondences) is not tuple:
        raise TypeError("original graph source correspondence tuple required")
    if source_correspondences:
        by_ref = {}
        for item in source_correspondences:
            if type(item) is not WorkspaceV3GraphSourceCorrespondence:
                raise TypeError("original v3 graph source correspondence required")
            package_ref = item.package().package_ref
            if package_ref in by_ref:
                raise RuntimeError("duplicate graph source correspondence")
            by_ref[package_ref] = item
        if tuple(sorted(by_ref, key=str.encode)) != tuple(
            package.package_ref for package in package_closure
        ):
            raise RuntimeError("graph source correspondence closure differs")
    for package in package_closure:
        entry = pair.workspace.package(package.package_ref)
        if entry.package != package:
            raise RuntimeError("planning source is outside current Workspace membership")
        if source_correspondences:
            by_ref[package.package_ref].validate(
                entry, source.read_dependencies(package)
            )
    return WorkspaceSemanticMaterializationGraphPlanner(
        workspace_catalog=pair.workspace,
        code_catalog=pair.code,
        head_reader=backing.head_reader,
        planning_source=source,
        source_only_target_validator=source_only_target_validator,
        source_correspondences=source_correspondences,
    )


async def plan_current_workspace_materialization_graph(
    *,
    code_host: object,
    catalog_host: WorkspaceSemanticCatalogHost,
    epoch: object,
    expected_epoch: object,
    original_sources: tuple[object, ...],
    package_closure: tuple[SemanticPackageCoordinate, ...],
    backing: WorkspaceMaterializationGraphBacking,
    selection: WorkspaceMaterializationSelectionProposal,
    root_plans: tuple[WorkspaceSemanticRootCodePlan, ...],
    source_only_target_validator: WorkspaceOriginalGraphTargetValidator | None = None,
    source_correspondences: tuple[WorkspaceV3GraphSourceCorrespondence, ...] = (),
) -> tuple[WorkspaceSemanticMaterializationGraphPlanResult, bytes]:
    """Plan once and verify final graph coverage and currentness after await."""
    from aware_code_retained_registry_policy_runtime.planning_source_composition import (
        validate_composed_retained_planning_source,
    )

    planner = compose_current_workspace_graph_planner(
        code_host=code_host,
        catalog_host=catalog_host,
        epoch=epoch,
        expected_epoch=expected_epoch,
        original_sources=original_sources,
        package_closure=package_closure,
        backing=backing,
        source_only_target_validator=source_only_target_validator,
        source_correspondences=source_correspondences,
    )
    code_admission = catalog_host.read_code_catalog_for_epoch(
        epoch, expected=expected_epoch
    )
    result = await plan_workspace_materialization_graph(
        planner=planner,
        selection=selection,
        root_plans=root_plans,
    )
    reached = tuple(
        sorted(
            (node.package for node in result[0].graph.nodes),
            key=lambda package: package.package_ref,
        )
    )
    if reached != package_closure:
        raise RuntimeError("reachable graph packages differ from original owner sources")
    validate_composed_retained_planning_source(
        code_host, planner._planning_source, package_closure
    )
    if source_only_target_validator is not None:
        source_only_target_validator.validate_source_packages(package_closure)
    for item in source_correspondences:
        package = item.package()
        item.validate(
            planner._workspace.package(package.package_ref),
            planner._planning_source.read_dependencies(package),
        )
    catalog_host.validate_current_catalog_epoch(epoch, expected=expected_epoch)
    if catalog_host.read_code_catalog_for_epoch(
        epoch, expected=expected_epoch
    ) is not code_admission:
        raise RuntimeError("Code catalog admission changed during graph planning")
    return result


class WorkspaceMaterializationGraphBacking:
    """Compose one Workspace body/head/session backing from admitted host resources.

    The host supplies its original Code runtime and state store. This object
    neither chooses a semantic provider nor grants generation authority.
    """

    def __init__(
        self,
        *,
        state_root: Path,
        repository_binding_ref: str,
        state_store: LocalOperationalStateStore,
        runtime: SemanticContractRuntime | None = None,
    ) -> None:
        self.body_store = DirectoryWorkspaceSemanticMaterializationBodyStore(
            state_root, repository_binding_ref=repository_binding_ref
        )
        self.publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=state_store,
            body_store=self.body_store,
        )
        self.session_journal = WorkspaceMaterializationSessionJournal(
            state_store=state_store,
            package_head_resolver=self.publisher.read_head,
        )
        self.head_reader = _WorkspacePackageHeadReader(self.publisher)

    def read_dependency_body(
        self, coordinate: SemanticValueCoordinate
    ) -> SemanticBody | None:
        if type(coordinate) is not SemanticValueCoordinate:
            raise TypeError("dependency coordinate must be exact")
        coordinate.__post_init__()
        body_ref = (
            "cas://workspace-semantic-materialization/body/"
            + coordinate.digest.value[7:]
        )
        body = self.body_store.read_body(body_ref)
        if body is None:
            return None
        return SemanticBody(coordinate=coordinate, canonical_body=body)

    def graph_host_ports(
        self,
        *,
        operation_preparer: Callable[
            [WorkspaceSemanticMaterializationNodePreparation],
            Awaitable[
                tuple[WorkspaceMaterializeOperation, WorkspaceMaterializeOperationAdmission]
            ],
        ],
        cutover_fence_reader: Callable[[str], WorkspaceMaterializationProductionCutoverHeadV1],
    ) -> _WorkspaceSemanticMaterializationGraphHostPorts:
        """Build ports; the admitted lifecycle owner still issues the host."""
        return _WorkspaceSemanticMaterializationGraphHostPorts(
            head_reader=lambda package_ref, role: self.publisher._read_graph_v2_head(
                package_ref, observation_role=role
            ),
            body_reader=self.read_dependency_body,
            operation_preparer=operation_preparer,
            session_journal=self.session_journal,
            cutover_fence_reader=cutover_fence_reader,
        )


def resolve_selected_workspace_graph_products(
    *,
    staged: _DirectWorkspaceStagedCommandResources,
    selected_bindings: tuple[CodeSemanticMaterializationProfileBinding, ...],
) -> tuple[tuple[SemanticContractRuntime, AdmittedSemanticProviderRegistration], ...]:
    """Match every Code-selected profile to one original product registration.

    The returned references describe a complete assignment, not execution
    authority. The fixed host and successor source still validate each use.
    """
    from aware_code_semantic_contract_runtime.product_contribution import (
        read_selected_provider_product_catalog_contribution,
    )

    from . import direct_command_composition as command_composition

    if (
        type(staged) is not command_composition._DirectWorkspaceStagedCommandResources
        or command_composition._STAGED_ASSEMBLIES.get(
            staged.command.lifetime_runtime, (None,)
        )[0] is not staged
        or type(selected_bindings) is not tuple
        or not 1 <= len(selected_bindings) <= 4096
        or len(staged.product_contributions) != len(staged.product_runtime_bindings)
    ):
        raise RuntimeError("original graph-product selection scope required")
    products: dict[
        ContentDigest,
        list[tuple[SemanticContractRuntime, AdmittedSemanticProviderRegistration]],
    ] = {}
    for contribution, retained in zip(
        staged.product_contributions,
        staged.product_runtime_bindings,
        strict=True,
    ):
        catalog = read_selected_provider_product_catalog_contribution(contribution)
        for entry in catalog.entries:
            products.setdefault(entry.binding_digest, []).append(
                (retained.runtime, retained.registration)
            )
    result = []
    for selected in selected_bindings:
        if type(selected) is not CodeSemanticMaterializationProfileBinding:
            raise TypeError("exact Code-selected graph profile required")
        selected.__post_init__()
        matches = products.get(selected.binding_digest, ())
        if len(matches) != 1:
            raise RuntimeError("graph node product profile missing or ambiguous")
        result.append(matches[0])
    return tuple(result)


def group_current_workspace_graph_product_sources(
    *,
    staged: _DirectWorkspaceStagedCommandResources,
    code_host: object,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    source_inputs: tuple[_SuccessorGraphNodeSourceInputs, ...],
) -> tuple[
    tuple[
        SemanticContractRuntime,
        AdmittedSemanticProviderRegistration,
        tuple[_SuccessorGraphNodeSourceInputs, ...],
    ],
    ...,
]:
    """Preflight the complete node/source/product closure before origin binding.

    This groups original resources for the fixed command; the result is not an
    admission. Each product factory still revalidates its sources and Code host.
    """
    from . import direct_command_composition as command_composition

    if (
        type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult
        or type(source_inputs) is not tuple
        or not 1 <= len(source_inputs) <= 4096
        or command_composition._POLICY_HOSTS.get(code_host) is not staged
    ):
        raise RuntimeError("original complete graph-product source closure required")
    plan_result.__post_init__()
    nodes = plan_result.graph_execution_binding.ordered_node_bindings
    if len(source_inputs) != len(nodes):
        raise RuntimeError("graph-product source set is incomplete")
    assignments = resolve_selected_workspace_graph_products(
        staged=staged,
        selected_bindings=tuple(item.code_match.selected_binding for item in nodes),
    )
    original = source_inputs[0]
    if type(original) is not command_composition._SuccessorGraphNodeSourceInputs:
        raise RuntimeError("original successor graph source unavailable")
    sources_by_ref: dict[str, _SuccessorGraphNodeSourceInputs] = {}
    for source in source_inputs:
        if (
            type(source) is not command_composition._SuccessorGraphNodeSourceInputs
            or source.staged is not staged
            or source.code_host is not code_host
        ):
            raise RuntimeError("original successor graph source unavailable")
        validated = command_composition._compose_successor_graph_node_source_inputs(
            staged,
            code_host,
            planning_source=source.planning_source,
            package_closure=source.package_closure,
            correspondence=source.correspondence,
            epoch=source.epoch,
            expected_epoch=source.expected_epoch,
        )
        if (
            validated.planning_source is not original.planning_source
            or validated.package_closure != original.package_closure
            or validated.epoch is not original.epoch
            or validated.expected_epoch is not original.expected_epoch
        ):
            raise RuntimeError("successor graph source closure differs")
        package_ref = validated.correspondence.package().package_ref
        if package_ref in sources_by_ref:
            raise RuntimeError("duplicate successor graph node source")
        sources_by_ref[package_ref] = validated
    if set(sources_by_ref) != {
        node.package.package_ref for node in nodes
    }:
        raise RuntimeError("graph-product source set differs from selected nodes")
    groups: list[
        tuple[
            SemanticContractRuntime,
            AdmittedSemanticProviderRegistration,
            list[_SuccessorGraphNodeSourceInputs],
        ]
    ] = []
    for node, (runtime, registration) in zip(nodes, assignments, strict=True):
        for group_runtime, group_registration, group_sources in groups:
            if group_runtime is runtime and group_registration is registration:
                group_sources.append(sources_by_ref[node.package.package_ref])
                break
        else:
            groups.append(
                (runtime, registration, [sources_by_ref[node.package.package_ref]])
            )
    return tuple(
        (runtime, registration, tuple(group_sources))
        for runtime, registration, group_sources in groups
    )


class WorkspaceCurrentGraphProductOperationFactory:
    """Compose nodes assigned to one selected product in the original command.

    Code binds the product registration once. Each node then receives the
    original Workspace source session from that same command. This factory
    issues neither a graph admission nor a second package-head publisher.
    """

    def __init__(
        self,
        *,
        staged: _DirectWorkspaceStagedCommandResources,
        code_host: object,
        registration: AdmittedSemanticProviderRegistration,
        runtime: SemanticContractRuntime,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        source_inputs: tuple[_SuccessorGraphNodeSourceInputs, ...],
        backing: WorkspaceMaterializationGraphBacking,
    ) -> None:
        from aware_code_retained_registry_policy_runtime.product_execution import (
            bind_product_execution_origin,
        )
        from . import direct_command_composition as command_composition

        if (
            type(staged)
            is not command_composition._DirectWorkspaceStagedCommandResources
            or command_composition._POLICY_HOSTS.get(code_host) is not staged
            or type(runtime) is not SemanticContractRuntime
            or type(registration) is not AdmittedSemanticProviderRegistration
            or type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult
            or type(backing) is not WorkspaceMaterializationGraphBacking
            or type(source_inputs) is not tuple
            or not 1 <= len(source_inputs) <= 4096
        ):
            raise RuntimeError("original successor graph-product host required")
        plan_result.__post_init__()
        ordered_nodes = plan_result.graph_execution_binding.ordered_node_bindings
        nodes = {item.package.package_ref: item for item in ordered_nodes}
        if not nodes or len(nodes) != len(ordered_nodes):
            raise RuntimeError("graph node package closure differs")
        assignments = resolve_selected_workspace_graph_products(
            staged=staged,
            selected_bindings=tuple(
                item.code_match.selected_binding for item in ordered_nodes
            ),
        )
        selected_products = {
            item.package.package_ref: product
            for item, product in zip(ordered_nodes, assignments, strict=True)
        }
        by_ref: dict[str, object] = {}
        original = source_inputs[0]
        if type(original) is not command_composition._SuccessorGraphNodeSourceInputs:
            raise RuntimeError("original successor graph source unavailable")
        for item in source_inputs:
            if (
                type(item) is not command_composition._SuccessorGraphNodeSourceInputs
                or item.staged is not staged
                or item.code_host is not code_host
            ):
                raise RuntimeError("original successor graph source unavailable")
            validated = (
                command_composition._compose_successor_graph_node_source_inputs(
                    staged,
                    code_host,
                    planning_source=item.planning_source,
                    package_closure=item.package_closure,
                    correspondence=item.correspondence,
                    epoch=item.epoch,
                    expected_epoch=item.expected_epoch,
                )
            )
            if (
                validated.planning_source is not original.planning_source
                or validated.package_closure != original.package_closure
                or validated.epoch is not original.epoch
                or validated.expected_epoch is not original.expected_epoch
            ):
                raise RuntimeError("successor graph source closure differs")
            package_ref = item.correspondence.package().package_ref
            if package_ref in by_ref:
                raise RuntimeError("duplicate successor graph node source")
            by_ref[package_ref] = validated
        if any(package_ref not in nodes for package_ref in by_ref):
            raise RuntimeError("successor product source is outside the graph")
        if any(
            selected_products[package_ref][0] is not runtime
            or selected_products[package_ref][1] is not registration
            for package_ref in by_ref
        ):
            raise RuntimeError("graph node selected a different product profile")
        contributions = tuple(
            item
            for item in staged.product_contributions
            if (
                (selected := command_composition.read_selected_provider_product_contribution(
                    item
                )).expected.runtime is runtime
                and selected.expected.registration is registration
            )
        )
        if len(contributions) != 1:
            raise RuntimeError("original graph product contribution is ambiguous")
        # The fixed Code host authenticates the original product registration
        # and retains Workspace's original full and locked verifier methods.
        bind_product_execution_origin(code_host, registration)
        self._staged = staged
        self._code_host = code_host
        self._registration = registration
        self._runtime = runtime
        self._contribution = contributions[0]
        self._source_inputs = by_ref
        self._plan_result = plan_result
        self._nodes = nodes
        self._backing = backing

    def operation_for(
        self,
        *,
        preparation: WorkspaceSemanticMaterializationNodePreparation,
        plan_resolver: WorkspaceMaterializeExecutionPlanResolver,
    ) -> WorkspaceMaterializeOperation:
        from . import direct_command_composition as command_composition

        if type(preparation) is not WorkspaceSemanticMaterializationNodePreparation:
            raise TypeError("exact Workspace graph node preparation required")
        preparation.__post_init__()
        if (
            preparation.graph_execution_binding_digest
            != self._plan_result.graph_execution_binding.binding_digest
        ):
            raise RuntimeError("graph node preparation differs from original plan")
        package_ref = preparation.node_execution_binding.package.package_ref
        if self._nodes.get(package_ref) is not preparation.node_execution_binding:
            raise RuntimeError("graph node preparation is not the selected node")
        if any(
            product.contract.key == CODE_PACKAGE_DELTA_CONTRACT
            for product in preparation.node_execution_binding.required_result_products
        ):
            raise RuntimeError(
                "Code package delta requires state-bound graph publication"
            )
        source = self._source_inputs.get(
            package_ref
        )
        if source is None:
            raise RuntimeError("graph node lacks an original successor source")
        if command_composition._POLICY_HOSTS.get(self._code_host) is not self._staged:
            raise RuntimeError("original graph-product host retired")

        def node_use(admission):  # type: ignore[no-untyped-def]
            return command_composition._command_owned_graph_node_source_session(
                self._staged.command,
                admission,
                source,
                publisher=self._backing.publisher,
                product_contribution=self._contribution,
            )

        return WorkspaceMaterializeOperation(
            runtime=self._runtime,
            plan_resolver=plan_resolver,
            publisher=self._backing.publisher,
            session_journal=self._backing.session_journal,
            graph_product_registration=self._registration,
            graph_node_use=node_use,
        )


class WorkspaceCurrentGraphProductOperationSet:
    """Bind the complete selected graph to its original product registrations.

    Any partial binding failure revokes the Code host. The enclosing fixed
    command still owns final resource cleanup and graph-host publication.
    """

    def __init__(
        self,
        *,
        staged: _DirectWorkspaceStagedCommandResources,
        code_host: object,
        plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
        source_inputs: tuple[_SuccessorGraphNodeSourceInputs, ...],
        backing: WorkspaceMaterializationGraphBacking,
    ) -> None:
        from aware_code_retained_registry_policy_runtime.direct_host import (
            close_direct_validation_host,
        )

        groups = group_current_workspace_graph_product_sources(
            staged=staged,
            code_host=code_host,
            plan_result=plan_result,
            source_inputs=source_inputs,
        )
        factories: dict[str, WorkspaceCurrentGraphProductOperationFactory] = {}
        try:
            for runtime, registration, sources in groups:
                factory = WorkspaceCurrentGraphProductOperationFactory(
                    staged=staged,
                    code_host=code_host,
                    registration=registration,
                    runtime=runtime,
                    plan_result=plan_result,
                    source_inputs=sources,
                    backing=backing,
                )
                for source in sources:
                    factories[source.correspondence.package().package_ref] = factory
        except BaseException as error:
            try:
                close_direct_validation_host(code_host)
            except BaseException as cleanup_error:
                raise BaseExceptionGroup(
                    "graph-product binding and Code host revocation failed",
                    [error, cleanup_error],
                ) from error
            raise
        self._factories = factories

    def operation_for(
        self,
        *,
        preparation: WorkspaceSemanticMaterializationNodePreparation,
        plan_resolver: WorkspaceMaterializeExecutionPlanResolver,
    ) -> WorkspaceMaterializeOperation:
        if type(preparation) is not WorkspaceSemanticMaterializationNodePreparation:
            raise TypeError("exact Workspace graph node preparation required")
        preparation.__post_init__()
        factory = self._factories.get(
            preparation.node_execution_binding.package.package_ref
        )
        if factory is None:
            raise RuntimeError("graph node has no selected original product")
        return factory.operation_for(
            preparation=preparation,
            plan_resolver=plan_resolver,
        )
