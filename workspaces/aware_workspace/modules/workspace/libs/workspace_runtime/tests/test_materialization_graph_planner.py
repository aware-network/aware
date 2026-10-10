from __future__ import annotations

from collections.abc import Callable
from math import ceil
from resource import RUSAGE_SELF, getrusage
from statistics import median
from time import perf_counter_ns

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticDependencyPlanner,
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticRequiredResultProduct,
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ProducedRoleDeclaration,
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    ProviderExecutionBinding,
    RoleBinding,
    SemanticConfigurationCoordinate,
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticDependencyTargetConstraint,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
    WorkspaceMaterializationPackageOccurrenceV4,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
)
from aware_workspace_runtime import (
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
    WorkspaceSemanticAuthoredDependency,
    WorkspaceSemanticMaterializationGraphPlanner,
    WorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationMembershipResolver,
    WorkspaceSemanticMaterializationPackageEntry,
    WorkspaceSemanticMaterializationParticipationPolicy,
    WorkspaceSemanticMaterializationPlanningError,
    WorkspaceSemanticPackageHeadObservation,
    WorkspaceSemanticRootCodePlan,
    decode_workspace_semantic_materialization_graph_execution_binding,
    decode_workspace_semantic_materialization_graph_plan_result,
    decode_workspace_semantic_materialization_node_execution_binding,
    encode_workspace_semantic_materialization_graph_execution_binding,
    encode_workspace_semantic_materialization_graph_plan_result,
    encode_workspace_semantic_materialization_node_execution_binding,
)
from aware_workspace_runtime.materialization_membership_catalog import (
    _issue_workspace_semantic_materialization_membership_catalog,
)
from aware_workspace_runtime.semantic_dependency_graph import (
    _create_planner_graph_execution_binding,
    _create_planner_node_execution_binding,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _contract(key: str) -> SemanticContractRef:
    return SemanticContractRef(key=key, version="1", schema_digest=_digest(key))


def _configuration(key: str) -> SemanticConfigurationCoordinate:
    return SemanticConfigurationCoordinate(
        configuration_ref=key, digest=_digest(f"config:{key}")
    )


def _implementation(key: str) -> SemanticImplementationCoordinate:
    return SemanticImplementationCoordinate(
        implementation_ref=key, closure_digest=_digest(f"impl:{key}")
    )


def _code_resolver(
    catalog: CodeSemanticContractCatalog,
    dependency_planners: dict[str, CodeSemanticDependencyPlanner],
) -> CodeSemanticContractCatalogResolver:
    provider_coordinates = {
        (binding.implementation, binding.configuration)
        for entry in catalog.entries
        for binding in entry.provider_execution_bindings
    }
    planner_bindings = tuple(
        (
            entry.dependency_planner_implementation,
            entry.dependency_planner_configuration,
            dependency_planners[
                entry.dependency_planner_implementation.implementation_ref
            ],
        )
        for entry in catalog.entries
    )
    admission = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=tuple(
            (implementation, configuration, object())
            for implementation, configuration in sorted(provider_coordinates)
        ),
        dependency_planner_bindings=planner_bindings,
        host_liveness=lambda: True,
    )
    return CodeSemanticContractCatalogResolver(admission)


def _workspace_resolver(
    catalog: WorkspaceSemanticMaterializationMembershipCatalog,
) -> WorkspaceSemanticMaterializationMembershipResolver:
    return WorkspaceSemanticMaterializationMembershipResolver(
        _issue_workspace_semantic_materialization_membership_catalog(
            catalog=catalog,
            host_liveness=lambda: True,
        )
    )


def _code_binding(
    kind: str, provider_key: str
) -> CodeSemanticMaterializationProfileBinding:
    source = _contract(f"aware.{kind}.source")
    result = _contract(f"aware.{kind}.result")
    effect = _contract(f"aware.{kind}.effect")
    output = _contract(f"aware.{kind}.python")
    provider = SemanticContractProviderDeclaration(
        provider_key=provider_key,
        provider_contract=_contract(f"aware.{kind}.provider"),
        package_kinds=(kind,),
        operation_kinds=("materialize",),
        consumed_roles=(
            ConsumedRoleDeclaration(role="source", accepted_contracts=(source,)),
        ),
        result_role=ProducedRoleDeclaration(role="result", contract=result),
        transition_contract=_contract(f"aware.{kind}.transition"),
        effect_role=ProducedRoleDeclaration(role="effect", contract=effect),
        effect_contract=effect,
        output_roles=(ProducedRoleDeclaration(role="python", contract=output),),
    )
    profile = SemanticContractProfileDeclaration(
        profile_ref=f"{kind}.materialization",
        version="1",
        package_kinds=(kind,),
        operation_kinds=("materialize",),
        inputs=(ProfileInputDeclaration(role="source", contract=source),),
        providers=(provider,),
        steps=(
            ProfileStepDeclaration(
                step_key="render",
                provider_key=provider_key,
                bindings=(RoleBinding(target_role="source", source_role="source"),),
            ),
        ),
        terminal_result_role="result",
        terminal_effect_role="effect",
        terminal_output_roles=("python",),
    )
    return CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key=f"aware.{kind}",
        semantic_provider_key=provider_key,
        package_families=("public",),
        package_roles=(kind,),
        manifest_contracts=(_contract(f"aware.{kind}.manifest"),),
        profile_declaration=profile,
        provider_execution_bindings=(
            ProviderExecutionBinding(
                provider_key=provider_key,
                implementation=_implementation(f"{kind}.renderer"),
                configuration=_configuration(f"{kind}.renderer"),
            ),
        ),
        dependency_planner_contract=_contract(f"aware.{kind}.planner"),
        dependency_planner_implementation=_implementation(f"{kind}.planner"),
        dependency_planner_configuration=_configuration(f"{kind}.planner"),
        dependency_demand_contract=_contract("aware.code.dependency-demand"),
        dependency_target_intent_contract=_contract("aware.code.target-intent"),
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(role=role, contract=contract)
            for role, contract in (
                ("effect", effect),
                ("python", output),
                ("result", result),
            )
        ),
        priority=10,
    )


class _DomainPlanner:
    def __init__(
        self,
        binding: CodeSemanticMaterializationProfileBinding,
        demand_factory: Callable[
            [], SemanticDependencyDemand | tuple[SemanticDependencyDemand, ...]
        ]
        | None,
    ) -> None:
        self.binding = binding
        self.profile_digest = binding.profile_declaration.digest
        self.demand_factory = demand_factory
        self.calls = 0
        self._results: dict[tuple[str, str], SemanticDependencyDemandSet] = {}

    async def plan(self, *, package, intent, selected_match, planning_input):  # type: ignore[no-untyped-def]
        self.calls += 1
        cache_key = (package.package_ref, intent.intent_digest.value)
        cached = self._results.get(cache_key)
        if cached is not None:
            return cached
        produced = () if self.demand_factory is None else self.demand_factory()
        demands = (
            produced
            if type(produced) is tuple
            else (produced,)
            if type(produced) is SemanticDependencyDemand
            else ()
        )
        result = SemanticDependencyDemandSet.create(
            package=package,
            intent=intent,
            profile_ref=self.binding.profile_declaration.profile_ref,
            profile_digest=self.profile_digest,
            contract_profile_binding_digest=self.binding.binding_digest,
            planner_implementation_ref=self.binding.dependency_planner_implementation.implementation_ref,
            planner_implementation_digest=self.binding.dependency_planner_implementation.closure_digest,
            planner_configuration=self.binding.dependency_planner_configuration,
            demands=demands,
        )
        self._results[cache_key] = result
        return result


def _entry(
    package_ref: str,
    kind: str,
    *,
    dependency: WorkspaceSemanticAuthoredDependency | None = None,
    dependencies: tuple[WorkspaceSemanticAuthoredDependency, ...] | None = None,
    owned_semantic_root_refs: tuple[str, ...] | None = None,
    allowed_semantic_root_refs: tuple[str, ...] | None = None,
) -> WorkspaceSemanticMaterializationPackageEntry:
    package = SemanticPackageCoordinate(
        package_ref=package_ref,
        package_kind=kind,
        manifest_digest=_digest(f"manifest:{package_ref}"),
    )
    return WorkspaceSemanticMaterializationPackageEntry.create(
        repository_ref="aware",
        workspace_ref="aware_kernel",
        module_ref=kind,
        package=package,
        package_family="public",
        package_role=kind,
        manifest_contract=_contract(f"aware.{kind}.manifest"),
        manifest_relative_path=f"{kind}/{package_ref.rsplit(':', 1)[-1]}.aware",
        source_authority_ref=f"source:{package_ref}",
        source_authority_digest=_digest(f"source:{package_ref}"),
        owned_semantic_root_refs=(f"{kind}.public",)
        if owned_semantic_root_refs is None
        else owned_semantic_root_refs,
        authored_dependencies=(
            dependencies
            if dependencies is not None
            else ()
            if dependency is None
            else (dependency,)
        ),
        participation_policy=WorkspaceSemanticMaterializationParticipationPolicy.create(
            policy_ref=f"policy:{package_ref}",
            policy_revision=1,
            package_ref=package_ref,
            allowed_operation_kinds=("materialize",),
            allowed_semantic_root_refs=(f"{kind}.public",)
            if allowed_semantic_root_refs is None
            else allowed_semantic_root_refs,
            allowed_terminal_output_roles=("python",),
            allow_unconfigured=True,
            allowed_semantic_configuration_coordinates=(),
        ),
        allowed_profile_refs=(f"{kind}.materialization",),
    )


class _HeadReader:
    def __init__(self) -> None:
        self.calls = 0

    async def observe(
        self, *, entry, local_code_match, intent, planning_demand_closure, planning_input_digest
    ):  # type: ignore[no-untyped-def]
        self.calls += 1
        return WorkspaceSemanticPackageHeadObservation.create(
            package=entry.package,
            source_identity_digest=entry.source_identity_digest,
            profile_binding_digest=local_code_match.selected_entry_digest,
            state="missing",
            predecessor_head_revision=None,
            predecessor_head_digest=None,
            historical_execution_input_closure_digest=None,
            expected_post_revision=1,
            expected_post_head_digest=None,
        )


def _root_plan(
    entry: WorkspaceSemanticMaterializationPackageEntry, output: SemanticContractRef
) -> WorkspaceSemanticRootCodePlan:
    intent = CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=entry.owned_semantic_root_refs,
        requested_terminal_output_roles=("python",),
        semantic_configuration_coordinate=None,
    )
    return WorkspaceSemanticRootCodePlan.create(
        package_ref=entry.package.package_ref,
        code_intent=intent,
        required_result_products=(
            CodeSemanticRequiredResultProduct.create(role="python", contract=output),
        ),
    )


def _composition(*, wrong_provider: bool = False, two_dependencies: bool = False):
    api_binding = _code_binding("api", "aware.api")
    sdk_binding = _code_binding("sdk", "aware.sdk")
    api_output = next(
        item.contract
        for item in api_binding.result_product_contracts
        if item.role == "python"
    )
    sdk_output = next(
        item.contract
        for item in sdk_binding.result_product_contracts
        if item.role == "python"
    )
    constraints = tuple(
        sorted(
            (
                SemanticDependencyTargetConstraint.create(
                    constraint_kind=kind, constraint_value=value
                )
                for kind, value in (
                    ("package_kind", "api"),
                    (
                        "semantic_provider_key",
                        "unknown.api" if wrong_provider else "aware.api",
                    ),
                )
            ),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    dependency = WorkspaceSemanticAuthoredDependency.create(
        dependency_kind="api_package",
        dependency_ref="sdk.api",
        admitted_target_package_refs=("package:api",),
        allowed_target_constraints=constraints,
    )
    second_dependency = WorkspaceSemanticAuthoredDependency.create(
        dependency_kind="api_package",
        dependency_ref="sdk.api.second",
        admitted_target_package_refs=("package:api-second",),
        allowed_target_constraints=constraints,
    )
    api_entry = _entry("package:api", "api")
    api_second_entry = _entry("package:api-second", "api")
    sdk_entry = _entry(
        "package:sdk",
        "sdk",
        dependency=dependency,
        dependencies=(dependency, second_dependency) if two_dependencies else None,
    )
    entries = (
        (api_entry, api_second_entry, sdk_entry)
        if two_dependencies
        else (api_entry, sdk_entry)
    )
    workspace_catalog = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.production", catalog_generation=1, entries=entries
    )

    def one_sdk_demand(*, dependency_ref: str) -> SemanticDependencyDemand:
        return SemanticDependencyDemand.create(
            consumer_semantic_role="sdk_source",
            authored_dependency_kind="api_package",
            authored_dependency_ref=dependency_ref,
            target_constraints=constraints,
            required_result_role="python",
            result_product_contract=api_output,
            target_intent=CodeSemanticMaterializationIntent.create(
                operation_kind="materialize",
                requested_semantic_root_refs=("api.public",),
                requested_terminal_output_roles=("python",),
                semantic_configuration_coordinate=None,
            ),
            cardinality="required",
        )

    def sdk_demand() -> SemanticDependencyDemand | tuple[SemanticDependencyDemand, ...]:
        first = one_sdk_demand(dependency_ref="sdk.api")
        if not two_dependencies:
            return first
        return (first, one_sdk_demand(dependency_ref="sdk.api.second"))

    api_planner = _DomainPlanner(api_binding, None)
    sdk_planner = _DomainPlanner(sdk_binding, sdk_demand)
    code_catalog = CodeSemanticContractCatalog.create(
        catalog_ref="code.production",
        catalog_generation=1,
        entries=(api_binding, sdk_binding),
    )
    resolver = _code_resolver(
        code_catalog,
        {
            api_binding.dependency_planner_implementation.implementation_ref: api_planner,
            sdk_binding.dependency_planner_implementation.implementation_ref: sdk_planner,
        },
    )
    head_reader = _HeadReader()
    planner = WorkspaceSemanticMaterializationGraphPlanner(
        planning_source=_FixtureOwnerPlanningSource(
            _workspace_resolver(workspace_catalog)
        ),
        workspace_catalog=_workspace_resolver(workspace_catalog),
        code_catalog=resolver,
        head_reader=head_reader,
    )
    proposal = WorkspaceMaterializationSelectionProposal.create(
        selectors=(
            WorkspaceMaterializationRootSelector.create(
                selector_kind="package", selector_ref="package:sdk"
            ),
        )
    )
    return (
        planner,
        proposal,
        (_root_plan(sdk_entry, sdk_output),),
        head_reader,
        api_planner,
        sdk_planner,
    )


@pytest.mark.asyncio
async def test_planner_resolves_workspace_then_code_and_builds_local_graph() -> None:
    planner, proposal, roots, head_reader, api_planner, sdk_planner = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    assert len(result.graph.nodes) == 2
    assert len(result.graph.edges) == 1
    assert head_reader.calls == 2
    assert api_planner.calls == 1
    assert sdk_planner.calls == 1
    counters = {item.counter: item.value for item in result.counter_entries}
    assert counters["dependency_body_read_count"] == 0
    assert counters["head_read_count"] == 2
    assert (
        result.graph_plan_admission.workspace_catalog_root_digest
        != result.graph_plan_admission.code_catalog_root_digest
    )


@pytest.mark.asyncio
async def test_v4_head_requires_original_workspace_occurrence() -> None:
    planner, proposal, roots, head_reader, *_ = _composition()
    original_observe = head_reader.observe
    occurrence = WorkspaceMaterializationPackageOccurrenceV4(
        repository_ref="repository:aware",
        workspace_ref="workspace:kernel",
        module_ref="module:sdk",
        package_id="sdk",
        package_root="workspaces/aware_kernel/modules/sdk",
        manifest_relative_path="workspaces/aware_kernel/modules/sdk/aware.module.toml",
    )

    async def observe(**values):
        missing = await original_observe(**values)
        if values["entry"].package.package_ref != "package:sdk":
            return missing
        return WorkspaceSemanticPackageHeadObservation.create(
            package=missing.package,
            source_identity_digest=missing.source_identity_digest,
            profile_binding_digest=missing.profile_binding_digest,
            state="stale",
            predecessor_head_revision=1,
            predecessor_head_digest=ContentDigest.of_bytes(b"retained-v4-head"),
            historical_execution_input_closure_digest=None,
            expected_post_revision=2,
            expected_post_head_digest=None,
            stored_head_contract=WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
            stored_package_occurrence=occurrence,
        )

    head_reader.observe = observe
    with pytest.raises(
        WorkspaceSemanticMaterializationPlanningError,
        match="head_observation_failed",
    ):
        await planner.plan(
            selection_proposal=proposal, requested_root_code_plans=roots
        )


@pytest.mark.asyncio
async def test_v2_execution_binding_is_complete_contextual_and_future_free() -> None:
    planner, proposal, roots, head_reader, api_planner, sdk_planner = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    binding = result.graph_execution_binding
    order = tuple(
        node_digest
        for layer in result.graph.topological_layers
        for node_digest in layer
    )
    assert tuple(item.node_digest for item in binding.ordered_node_bindings) == order
    assert head_reader.calls == 2
    assert api_planner.calls == 1
    assert sdk_planner.calls == 1
    assert "future" not in str(binding.to_wire())
    assert "consumed_body_coordinate" not in str(binding.to_wire())

    first = binding.ordered_node_bindings[0]
    node_wire = encode_workspace_semantic_materialization_node_execution_binding(
        first, plan_result=result
    )
    assert (
        decode_workspace_semantic_materialization_node_execution_binding(
            node_wire, plan_result=result, expected=first
        )
        is first
    )
    graph_wire = encode_workspace_semantic_materialization_graph_execution_binding(
        binding, plan_result=result
    )
    assert (
        decode_workspace_semantic_materialization_graph_execution_binding(
            graph_wire, plan_result=result, expected=binding
        )
        is binding
    )
    plan_wire = encode_workspace_semantic_materialization_graph_plan_result(result)
    assert (
        decode_workspace_semantic_materialization_graph_plan_result(
            plan_wire, expected=result
        )
        is result
    )
    with pytest.raises(ContractViolation, match="canonical"):
        decode_workspace_semantic_materialization_graph_plan_result(
            plan_wire + b"\n", expected=result
        )


@pytest.mark.asyncio
async def test_replay_rereads_heads_but_preserves_semantic_graph_identity() -> None:
    planner, proposal, roots, head_reader, _, _ = _composition()
    first = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    second = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    assert first.graph.graph_digest == second.graph.graph_digest
    assert (
        first.graph_plan_admission.admission_digest
        == second.graph_plan_admission.admission_digest
    )
    assert head_reader.calls == 4


@pytest.mark.asyncio
async def test_unknown_semantic_provider_is_filtered_only_by_code() -> None:
    planner, proposal, roots, _, _, _ = _composition(wrong_provider=True)
    with pytest.raises(WorkspaceSemanticMaterializationPlanningError) as caught:
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
    assert caught.value.code == "dependency_target_absent"


@pytest.mark.asyncio
async def test_root_plan_and_selector_closure_fail_closed() -> None:
    planner, proposal, _roots, _, _, _ = _composition()
    with pytest.raises(WorkspaceSemanticMaterializationPlanningError) as caught:
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=())
    assert caught.value.code == "selection_failed"


@pytest.mark.asyncio
async def test_explicit_root_provider_constraint_reaches_code_matcher() -> None:
    planner, proposal, roots, _, _, _ = _composition()
    original = roots[0]
    assert original.to_wire()["contract"].endswith(".v1")
    explicit = WorkspaceSemanticRootCodePlan.create(
        package_ref=original.package_ref,
        code_intent=original.code_intent,
        required_result_products=original.required_result_products,
        required_semantic_provider_keys=("aware.sdk",),
    )
    assert explicit.to_wire()["contract"].endswith(".v2")
    assert explicit.root_plan_digest != original.root_plan_digest
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=(explicit,)
    )
    sdk = next(
        node for node in result.graph_execution_binding.ordered_node_bindings
        if node.package.package_ref == "package:sdk"
    )
    assert sdk.code_match.selected_binding.semantic_provider_key == "aware.sdk"
    wrong = WorkspaceSemanticRootCodePlan.create(
        package_ref=original.package_ref,
        code_intent=original.code_intent,
        required_result_products=original.required_result_products,
        required_semantic_provider_keys=("foreign.provider",),
    )
    with pytest.raises(WorkspaceSemanticMaterializationPlanningError):
        await planner.plan(
            selection_proposal=proposal, requested_root_code_plans=(wrong,)
        )


@pytest.mark.asyncio
async def test_planner_performance_visibility_baseline() -> None:
    planner, proposal, roots, _, _, _ = _composition()
    samples: list[int] = []
    for _ in range(5):
        started = perf_counter_ns()
        result = await planner.plan(
            selection_proposal=proposal, requested_root_code_plans=roots
        )
        samples.append(perf_counter_ns() - started)
        counters = {item.counter: item.value for item in result.counter_entries}
        assert counters["fan_in_iteration_count"] >= 3
        assert counters["fan_in_lattice_addition_count"] >= 4
    samples.sort()
    assert samples[len(samples) // 2] < 100_000_000
    assert samples[-1] < 200_000_000


class _HighFanInConsumerPlanner:
    def __init__(
        self,
        binding: CodeSemanticMaterializationProfileBinding,
        *,
        target_output: SemanticContractRef,
        target_constraints: tuple[SemanticDependencyTargetConstraint, ...],
        shared_target_root: str | None = None,
        unique_consumer_role: bool = False,
    ) -> None:
        self.binding = binding
        self.profile_digest = binding.profile_declaration.digest
        self.target_output = target_output
        self.target_constraints = target_constraints
        self.shared_target_root = shared_target_root
        self.unique_consumer_role = unique_consumer_role
        self._results: dict[tuple[str, str], SemanticDependencyDemandSet] = {}

    async def plan(self, *, package, intent, selected_match, planning_input):  # type: ignore[no-untyped-def]
        cache_key = (package.package_ref, intent.intent_digest.value)
        cached = self._results.get(cache_key)
        if cached is not None:
            return cached
        suffix = package.package_ref.rsplit(":", 1)[-1]
        demand = SemanticDependencyDemand.create(
            consumer_semantic_role=(
                f"fan_in_source.{suffix}"
                if self.unique_consumer_role
                else "fan_in_source"
            ),
            authored_dependency_kind="shared_target",
            authored_dependency_ref="fan_in.shared_target",
            target_constraints=self.target_constraints,
            required_result_role="python",
            result_product_contract=self.target_output,
            target_intent=CodeSemanticMaterializationIntent.create(
                operation_kind="materialize",
                requested_semantic_root_refs=(
                    self.shared_target_root or f"target.{suffix}",
                ),
                requested_terminal_output_roles=("python",),
                semantic_configuration_coordinate=None,
            ),
            cardinality="required",
        )
        result = SemanticDependencyDemandSet.create(
            package=package,
            intent=intent,
            profile_ref=self.binding.profile_declaration.profile_ref,
            profile_digest=self.profile_digest,
            contract_profile_binding_digest=self.binding.binding_digest,
            planner_implementation_ref=self.binding.dependency_planner_implementation.implementation_ref,
            planner_implementation_digest=self.binding.dependency_planner_implementation.closure_digest,
            planner_configuration=self.binding.dependency_planner_configuration,
            demands=(demand,),
        )
        self._results[cache_key] = result
        return result


def _high_fan_in_composition(
    node_count: int,
    *,
    shared_target_root: str | None = None,
    unique_consumer_role: bool = False,
    target_package_ref: str = "package:zzzz-target",
):
    target_binding = _code_binding("target", "aware.target")
    consumer_binding = _code_binding("consumer", "aware.consumer")
    target_output = next(
        item.contract
        for item in target_binding.result_product_contracts
        if item.role == "python"
    )
    consumer_output = next(
        item.contract
        for item in consumer_binding.result_product_contracts
        if item.role == "python"
    )
    constraints = tuple(
        sorted(
            (
                SemanticDependencyTargetConstraint.create(
                    constraint_kind=kind, constraint_value=value
                )
                for kind, value in (
                    ("package_kind", "target"),
                    ("semantic_provider_key", "aware.target"),
                )
            ),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    dependency = WorkspaceSemanticAuthoredDependency.create(
        dependency_kind="shared_target",
        dependency_ref="fan_in.shared_target",
        admitted_target_package_refs=(target_package_ref,),
        allowed_target_constraints=constraints,
    )
    consumers = tuple(
        _entry(f"package:consumer{index:04d}", "consumer", dependency=dependency)
        for index in range(node_count - 1)
    )
    target_roots = (
        (shared_target_root,)
        if shared_target_root is not None
        else tuple(
            sorted(
                (
                    f"target.{entry.package.package_ref.rsplit(':', 1)[-1]}"
                    for entry in consumers
                ),
                key=str.encode,
            )
        )
    )
    target = _entry(
        target_package_ref,
        "target",
        allowed_semantic_root_refs=target_roots,
    )
    entries = tuple(
        sorted(
            (*consumers, target),
            key=lambda item: item.package.package_ref.encode(),
        )
    )
    workspace_catalog = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref=f"workspace.fan-in-{node_count}",
        catalog_generation=1,
        entries=entries,
    )
    code_entries = tuple(
        sorted(
            (consumer_binding, target_binding),
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    code_catalog = CodeSemanticContractCatalog.create(
        catalog_ref="code.fan-in", catalog_generation=1, entries=code_entries
    )
    dependency_planners: dict[str, CodeSemanticDependencyPlanner] = {
        target_binding.dependency_planner_implementation.implementation_ref: _DomainPlanner(
            target_binding, None
        ),
        consumer_binding.dependency_planner_implementation.implementation_ref: _HighFanInConsumerPlanner(
            consumer_binding,
            target_output=target_output,
            target_constraints=constraints,
            shared_target_root=shared_target_root,
            unique_consumer_role=unique_consumer_role,
        ),
    }
    planner = WorkspaceSemanticMaterializationGraphPlanner(
        planning_source=_FixtureOwnerPlanningSource(
            _workspace_resolver(workspace_catalog)
        ),
        workspace_catalog=_workspace_resolver(workspace_catalog),
        code_catalog=_code_resolver(code_catalog, dependency_planners),
        head_reader=_HeadReader(),
    )
    selectors = (
        WorkspaceMaterializationRootSelector.create(
            selector_kind="module", selector_ref="consumer"
        ),
    )
    proposal = WorkspaceMaterializationSelectionProposal.create(selectors=selectors)
    roots = tuple(
        sorted(
            (_root_plan(entry, consumer_output) for entry in consumers),
            key=lambda item: item.package_ref.encode(),
        )
    )
    return planner, proposal, roots


@pytest.mark.asyncio
async def test_candidate_context_cache_and_equal_fan_in_are_queue_independent() -> None:
    planner, proposal, roots = _high_fan_in_composition(
        5,
        shared_target_root="target.shared",
        unique_consumer_role=True,
        target_package_ref="package:consumer0001z",
    )
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    counters = {item.counter: item.value for item in result.counter_entries}
    assert counters["catalog_lookup_count"] == 5
    assert counters["provider_match_count"] == 5
    assert counters["demand_planner_invocation_count"] == 5
    assert counters["fan_in_equal_context_reuse_count"] >= 1
    assert len(result.graph.nodes) == 5
    assert len(result.graph.edges) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("node_count", "median_gate_ns", "p95_gate_ns"),
    ((100, 100_000_000, 200_000_000), (500, 500_000_000, 750_000_000)),
)
async def test_compatible_high_fan_in_performance_and_visibility(
    node_count: int, median_gate_ns: int, p95_gate_ns: int
) -> None:
    planner, proposal, roots = _high_fan_in_composition(node_count)
    for _ in range(2):
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
    samples: list[int] = []
    result = None
    for _ in range(10):
        started = perf_counter_ns()
        result = await planner.plan(
            selection_proposal=proposal, requested_root_code_plans=roots
        )
        samples.append(perf_counter_ns() - started)
    assert result is not None
    ordered = sorted(samples)
    p95 = ordered[ceil(len(ordered) * 0.95) - 1]
    counters = {item.counter: item.value for item in result.counter_entries}
    assert len(result.graph.nodes) == node_count
    assert len(result.graph.edges) == node_count - 1
    assert counters["fan_in_context_count"] == node_count
    assert counters["fan_in_iteration_count"] == node_count + 1
    assert counters["fan_in_lattice_addition_count"] == (node_count * 4) - 2
    assert counters["head_read_count"] == node_count
    assert counters["dependency_body_read_count"] == 0
    assert median(ordered) < median_gate_ns
    assert p95 < p95_gate_ns


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("node_count", "median_gate_ns", "p95_gate_ns"),
    ((100, 25_000_000, 50_000_000), (500, 125_000_000, 250_000_000)),
)
async def test_v3_binding_derivation_performance_gate(
    node_count: int, median_gate_ns: int, p95_gate_ns: int
) -> None:
    planner, proposal, roots = _high_fan_in_composition(node_count)
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )

    def derive() -> None:
        node_bindings = tuple(
            _create_planner_node_execution_binding(
                planning_input_digest=item.planning_input_digest,
                node_digest=item.node_digest,
                package=item.package,
                package_entry=item.package_entry,
                code_intent=item.code_intent,
                workspace_admitted_intent=item.workspace_admitted_intent,
                planning_context=item.planning_context,
                code_match=item.code_match,
                code_match_admission=item.code_match_admission,
                dependency_demand_set=item.dependency_demand_set,
                planning_demand_closure=item.planning_demand_closure,
                incoming_target_resolutions=item.incoming_target_resolutions,
                required_result_products=item.required_result_products,
            )
            for item in result.graph_execution_binding.ordered_node_bindings
        )
        _create_planner_graph_execution_binding(
            graph=result.graph, ordered_node_bindings=node_bindings
        )

    derive()
    derive()
    samples: list[int] = []
    for _ in range(10):
        started = perf_counter_ns()
        derive()
        samples.append(perf_counter_ns() - started)
    ordered = sorted(samples)
    assert median(ordered) < median_gate_ns
    assert ordered[ceil(len(ordered) * 0.95) - 1] < p95_gate_ns
    assert len(canonical_json_bytes(result.to_wire())) > 0
    assert getrusage(RUSAGE_SELF).ru_maxrss > 0


class _FixtureOwnerPlanningSource:
    """Synthetic owner meaning; not canonical source admission."""

    def __init__(self, membership):
        from copy import deepcopy

        from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
            DependencyPlanningInputCodec,
        )
        from aware_workspace_runtime.semantic_dependency_inputs import (
            WorkspaceSemanticDependencySource,
        )

        self._membership = membership
        self._codec = DependencyPlanningInputCodec()
        self._decoded_by_body = {}
        fixture_projection = WorkspaceSemanticDependencySource(membership)
        self._retained = {}
        for entry in membership.catalog.entries:
            value = fixture_projection.read_dependencies(entry.package)
            self._retained[entry.package.package_ref] = (
                entry, self._codec.encode(value),
                tuple(
                    deepcopy(membership.package(target.package.package_ref))
                    for dependency in value.dependencies
                    for target in dependency.targets
                ),
            )

    def read_dependencies(self, package):
        if getattr(self, "reject", False):
            raise ContractViolation("owner source expired")
        original, body, targets = self._retained[package.package_ref]
        if self._membership.package(package.package_ref) != original:
            raise ContractViolation("fixture membership changed")
        if package != original.package:
            raise ContractViolation("fixture package changed")
        for target in targets:
            if self._membership.package(target.package.package_ref) != target:
                raise ContractViolation("fixture target changed")
        value = self._decoded_by_body.get(body)
        if value is None:
            value = self._codec.decode(body)
            self._decoded_by_body[body] = value
        self._membership.package(package.package_ref)
        return value


@pytest.mark.asyncio
async def test_original_planning_digest_is_in_binding_and_cache_evidence():
    from dataclasses import replace

    from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
        DependencyPlanningInputCodec,
    )

    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    for binding in result.graph_execution_binding.ordered_node_bindings:
        source = planner._planning_reader(binding.package)
        digest = ContentDigest.of_bytes(DependencyPlanningInputCodec().encode(source))
        assert binding.planning_input_digest == digest
        assert binding.to_wire()["planning_input_digest"] == digest.value
        assert any(
            digest.value in key for key in planner._node_execution_binding_digest_cache
        )
        with pytest.raises(ContractViolation):
            replace(
                binding, planning_input_digest=_digest("substituted")
            ).__post_init__()


@pytest.mark.asyncio
async def test_expired_owner_source_rejects_after_await_and_before_cache_reuse():
    planner, proposal, roots, _, _, sdk_planner = _composition()
    original = sdk_planner.demand_factory

    def expire():
        planner._planning_source.reject = True
        return original()

    sdk_planner.demand_factory = expire
    with pytest.raises(ContractViolation, match="owner source expired"):
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
    planner, proposal, roots, _, api_planner, sdk_planner = _composition()
    await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
    calls = api_planner.calls + sdk_planner.calls
    planner._planning_source.reject = True
    with pytest.raises(ContractViolation):
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
    assert api_planner.calls + sdk_planner.calls == calls


@pytest.mark.asyncio
async def test_changed_retained_body_rejects_after_planner_call():
    from dataclasses import replace

    planner, proposal, roots, _, _, sdk_planner = _composition()
    source = planner._planning_source
    original = sdk_planner.demand_factory

    def change_body():
        entry, body, targets = source._retained["package:sdk"]
        changed = replace(
            source._codec.decode(body), source_identity_digest=_digest("changed")
        )
        source._retained["package:sdk"] = (
            entry, source._codec.encode(changed), targets
        )
        return original()

    sdk_planner.demand_factory = change_body
    with pytest.raises(ContractViolation, match="owner planning package/source differs"):
        await planner.plan(selection_proposal=proposal, requested_root_code_plans=roots)
