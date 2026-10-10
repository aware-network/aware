from __future__ import annotations

import asyncio
import copy
import json
import pickle
import time
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import cast

import pytest
from aware_code_semantic_contract_runtime import (
    CodePortableSemanticPackageAuthority,
    CodeSemanticContractCatalog,
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticRequiredResultProduct,
    ContentDigest,
    ProviderExecutionBinding,
    SemanticBody,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from aware_workspace_runtime import (
    AdmittedWorkspaceSemanticMaterializationGraphExecution,
    AdmittedWorkspaceSemanticMaterializationGraphNodeExecution,
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
    WorkspaceRevisionPreparationAdmissionError,
    WorkspaceSemanticMaterializationGraphCoordinator,
    WorkspaceSemanticMaterializationGraphExecutionError,
    WorkspaceSemanticMaterializationGraphPlanner,
    WorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationPackageEntry,
    WorkspaceSemanticMaterializationParticipationPolicy,
    WorkspaceSemanticPackageHeadObservation,
    WorkspaceSemanticRootCodePlan,
    admit_completed_workspace_materialization_graph_execution,
)
from aware_workspace_runtime.materialization_graph_coordinator import (
    WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_KEY_V1,
    WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_NAMESPACE_V1,
    _create_workspace_materialization_production_cutover_head_v1,
    _create_workspace_materialization_production_writer_evidence_v1,
    _execution_state,
    _issue_workspace_semantic_materialization_graph_execution_for_test,
    _revoke_workspace_semantic_materialization_graph_execution,
    _WorkspaceSemanticMaterializationGraphHostPorts,
    decode_workspace_materialization_production_cutover_successor,
    observe_workspace_materialization_production_cutover_head,
)
from aware_workspace_runtime.materialization_operation import (
    WorkspaceMaterializeExecutionPlan,
    WorkspaceMaterializeOperation,
    WorkspaceMaterializeOperationError,
    _graph_node_admission_state,
    _validate_graph_node_owner_source,
)
from aware_workspace_runtime.materialization_session import (
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceMaterializationSessionBaselineGrade,
    WorkspaceMaterializationSessionJournal,
    WorkspaceMaterializationSessionSourceEvidenceV3,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceSemanticMaterializationRequestV3,
    _create_head_reread_v2_from_validated_head,
)
from aware_workspace_runtime.source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
    WorkspaceOwnerDefinedSourceInspection,
    WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
)
from test_materialization_graph_planner import (
    _code_resolver,
    _composition,
    _DomainPlanner,
    _FixtureOwnerPlanningSource,
    _HeadReader,
    _high_fan_in_composition,
    _workspace_resolver,
)
from test_materialization_operation import (
    _admission as _operation_admission,
)
from test_materialization_operation import (
    _Authority,
    _Resolver,
)
from test_materialization_operation import (
    _request as _operation_request,
)
from test_semantic_materialization_publication import (
    OUTPUT,
    SOURCE,
    RESULT,
    TRANSITION,
    EFFECT,
    _BodyStore,
    _JsonCodec,
    _Provider,
    _declaration,
    _invocation,
    _profile,
)


class _SelectedGraphFixtureProvider(_Provider):
    """Selected Code execution for the graph coordinator's isolated fixture."""

    def input_closure(self, value):  # type: ignore[no-untyped-def]
        from aware_code_semantic_contract_runtime.selected_provider import (
            SelectedProviderInvocationClosure,
        )

        if type(value) is not SelectedProviderInvocationClosure:
            raise TypeError("exact fixture closure required")
        decoded = json.loads(value.input_bodies[0].canonical_body)
        return SelectedProviderInvocationClosure(
            value.invocation,
            value.input_bodies,
            value.predecessor_body,
            (decoded,),
        )

    def execute(self, step, semantic_input):  # type: ignore[no-untyped-def]
        del semantic_input
        pending = self.derive(step)
        try:
            pending.send(None)
        except StopIteration as finished:
            return finished.value
        raise AssertionError("fixture provider unexpectedly suspended")


_GRAPH_IMPLEMENTATION_BODY = canonical_json_bytes(
    {"implementation": "selected graph fixture"}
)
_GRAPH_CONFIGURATION_BODY = canonical_json_bytes(
    {"configuration": "selected graph fixture"}
)
_GRAPH_IMPLEMENTATION = SemanticImplementationCoordinate(
    "test-semantic-provider", ContentDigest.of_bytes(_GRAPH_IMPLEMENTATION_BODY)
)
_GRAPH_CONFIGURATION = SemanticConfigurationCoordinate(
    "test-semantic-provider.no-options",
    ContentDigest.of_bytes(_GRAPH_CONFIGURATION_BODY),
)


def _construct_selected_graph_fixture():  # type: ignore[no-untyped-def]
    from aware_code_semantic_contract_runtime import SemanticContractRuntime
    from aware_code_semantic_contract_runtime import selected_provider

    provider = _SelectedGraphFixtureProvider()
    runtime = SemanticContractRuntime(
        _profile(),
        {"test-provider": provider},
        {contract: _JsonCodec(contract) for contract in (
            SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT
        )},
    )
    binding = ProviderExecutionBinding(
        "test-provider", _GRAPH_IMPLEMENTATION, _GRAPH_CONFIGURATION
    )

    return selected_provider._SelectedProviderFactoryProduct(
        runtime=runtime,
        provider=provider,
        binding=binding,
        executable_entrance=provider.execute,
        input_closure_entrance=provider.input_closure,
        semantic_implementation_contract_body=_GRAPH_IMPLEMENTATION_BODY,
        configuration_body=_GRAPH_CONFIGURATION_BODY,
    )


def _selected_graph_fixture():  # type: ignore[no-untyped-def]
    from aware_code_semantic_contract_runtime import selected_provider

    factory = getattr(_selected_graph_fixture, "factory", None)
    if factory is None:
        factory = selected_provider._admit_selected_provider_factory(
            factory_ref="test.workspace.graph-selected-execution.v1",
            provider_key="test-provider",
            selection_factory=_construct_selected_graph_fixture,
        )
        _selected_graph_fixture.factory = factory
    root = selected_provider._issue_selected_provider_selection_root(factory)
    runtime = selected_provider._selection_root_state(root).runtime
    registration = selected_provider.register_selected_provider(runtime, root)
    return runtime, registration


class _FixtureGraphNodeUse:
    def __init__(self, admission):  # type: ignore[no-untyped-def]
        self.admission = admission
        self.plan = None
        self.closed = False

    def bind_execution_plan(self, plan):  # type: ignore[no-untyped-def]
        if self.closed:
            raise RuntimeError("fixture graph node use unavailable")
        _graph_node_admission_state(self.admission)
        if self.plan is not None:
            raise RuntimeError("fixture graph plan already bound")
        self.plan = plan

    def validate(self):
        if self.closed or self.plan is None:
            raise RuntimeError("fixture graph node use unavailable")
        _graph_node_admission_state(self.admission)


class _FixtureGraphExecutionOrigin:
    def adopt(self, use):  # type: ignore[no-untyped-def]
        use.validate()
        return use

    def validate(self, use, closure):  # type: ignore[no-untyped-def]
        use.validate()
        if (
            closure.invocation is not use.plan.invocation
            or closure.input_bodies is not use.plan.input_bodies
            or closure.predecessor_body is not use.plan.predecessor_body
        ):
            raise RuntimeError("fixture selected graph closure differs")

    def complete(self, use, completion):  # type: ignore[no-untyped-def]
        use.validate()
        del completion

    def fail(self, use):  # type: ignore[no-untyped-def]
        use.closed = True


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _writer_evidence(revision: int):  # type: ignore[no-untyped-def]
    release = _digest(f"release:{revision}").value
    return _create_workspace_materialization_production_writer_evidence_v1(
        managed_release_channel_revision=revision,
        managed_release_channel_pointer_digest=_digest(f"channel:{revision}").value,
        current_release_set_digest=release,
        writer_release_set_digests=(release,),
        managed_provider_generation_lineage_ref=f"provider-lineage:{revision}",
        managed_release_authority_evidence_digest=_digest(
            f"authority:{revision}"
        ).value,
    )


def test_production_cutover_successor_and_revision_two_restart_are_strict() -> None:
    store = InMemoryLocalOperationalStateStore()
    evidence_one = _writer_evidence(1)
    head_one = _create_workspace_materialization_production_cutover_head_v1(
        workspace_authority_root_ref="workspace-authority:test",
        workspace_authority_root_digest=_digest("workspace-authority").value,
        cutover_epoch="cutover-epoch:test",
        revision=1,
        predecessor_head_digest=None,
        writer_evidence=evidence_one,
    )
    admitted_one = decode_workspace_materialization_production_cutover_successor(
        head_one.to_wire(),
        predecessor_record=None,
        workspace_authority_root_ref="workspace-authority:test",
        workspace_authority_root_digest=_digest("workspace-authority").value,
        cutover_epoch="cutover-epoch:test",
        writer_evidence=evidence_one,
    )
    first_record = store.compare_and_set(
        WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_NAMESPACE_V1,
        WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_KEY_V1,
        expected_revision=0,
        value=admitted_one.to_state(),
    )
    evidence_two = _writer_evidence(2)
    head_two = _create_workspace_materialization_production_cutover_head_v1(
        workspace_authority_root_ref="workspace-authority:test",
        workspace_authority_root_digest=_digest("workspace-authority").value,
        cutover_epoch="cutover-epoch:test",
        revision=2,
        predecessor_head_digest=head_one.head_digest,
        writer_evidence=evidence_two,
    )
    admitted_two = decode_workspace_materialization_production_cutover_successor(
        head_two.to_wire(),
        predecessor_record=first_record,
        workspace_authority_root_ref="workspace-authority:test",
        workspace_authority_root_digest=_digest("workspace-authority").value,
        cutover_epoch="cutover-epoch:test",
        writer_evidence=evidence_two,
    )
    second_record = store.compare_and_set(
        WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_NAMESPACE_V1,
        WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_KEY_V1,
        expected_revision=1,
        value=admitted_two.to_state(),
    )
    assert (
        observe_workspace_materialization_production_cutover_head(
            second_record,
            workspace_authority_root_ref="workspace-authority:test",
            workspace_authority_root_digest=_digest("workspace-authority").value,
            cutover_epoch="cutover-epoch:test",
            writer_evidence=evidence_two,
        )
        == head_two
    )

    poison = head_two.to_wire().replace(b'"revision":2', b'"revision":true')
    with pytest.raises(WorkspaceSemanticMaterializationGraphExecutionError):
        decode_workspace_materialization_production_cutover_successor(
            poison,
            predecessor_record=first_record,
            workspace_authority_root_ref="workspace-authority:test",
            workspace_authority_root_digest=_digest("workspace-authority").value,
            cutover_epoch="cutover-epoch:test",
            writer_evidence=evidence_two,
        )
    moved = replace(first_record, value=head_two.to_state())
    with pytest.raises(WorkspaceSemanticMaterializationGraphExecutionError):
        observe_workspace_materialization_production_cutover_head(
            moved,
            workspace_authority_root_ref="workspace-authority:test",
            workspace_authority_root_digest=_digest("workspace-authority").value,
            cutover_epoch="cutover-epoch:test",
            writer_evidence=evidence_two,
        )


class _CurrentHeadReader:
    def __init__(self) -> None:
        self.heads: dict[str, WorkspaceSemanticMaterializationHeadV3] = {}
        self.bodies: dict[str, SemanticBody] = {}
        self.observe_calls = 0
        self.runtime_head_calls = 0
        self.body_calls = 0
        self.journal_ns = 0
        self.head_read_ns = 0
        self.body_read_ns = 0

    async def observe(
        self, *, entry, local_code_match, intent, planning_demand_closure, planning_input_digest
    ):  # type: ignore[no-untyped-def]
        del planning_demand_closure
        self.observe_calls += 1
        required = next(
            item
            for item in local_code_match.selected_binding.result_product_contracts
            if item.role == "python"
        )
        body_bytes = f"body:{entry.package.package_ref}".encode()
        coordinate = SemanticValueCoordinate(
            role=required.role,
            contract=required.contract,
            value_ref=f"value:{entry.package.package_ref}",
            digest=ContentDigest.of_bytes(body_bytes),
            size_bytes=len(body_bytes),
        )
        closure = _digest(f"closure:{entry.package.package_ref}")
        request = WorkspaceSemanticMaterializationRequestV3.create(
            package=entry.package,
            result_coordinate=coordinate,
            source_identity_digest=entry.source_identity_digest,
            code_intent_digest=intent.intent_digest,
            code_match_digest=local_code_match.match_digest,
            planning_input_digest=planning_input_digest,
            execution_input_closure_digest=closure,
            operation_result_digest=_digest(f"operation:{entry.package.package_ref}"),
            expected_head_revision=0,
        )
        head = WorkspaceSemanticMaterializationHeadV3.create(request=request)
        self.heads[entry.package.package_ref] = head
        self.bodies[coordinate.value_ref] = SemanticBody(
            coordinate=coordinate, canonical_body=body_bytes
        )
        return WorkspaceSemanticPackageHeadObservation.create(
            package=entry.package,
            source_identity_digest=entry.source_identity_digest,
            profile_binding_digest=local_code_match.selected_entry_digest,
            state="current",
            predecessor_head_revision=1,
            predecessor_head_digest=head.head_digest,
            historical_execution_input_closure_digest=closure,
            expected_post_revision=1,
            expected_post_head_digest=head.head_digest,
        )

    def read_head(
        self, package_ref: str, role: str
    ) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None:
        started = time.perf_counter_ns()
        self.runtime_head_calls += 1
        head = self.heads.get(package_ref)
        result = (
            None
            if head is None
            else _create_head_reread_v2_from_validated_head(
                observation_role=role,
                materialization_head_revision=1,
                head=head,
            )
        )
        self.head_read_ns += time.perf_counter_ns() - started
        return result

    def read_body(self, coordinate: SemanticValueCoordinate) -> SemanticBody | None:
        started = time.perf_counter_ns()
        self.body_calls += 1
        result = self.bodies.get(coordinate.value_ref)
        self.body_read_ns += time.perf_counter_ns() - started
        return result


async def _unexpected_preparer(preparation):  # type: ignore[no-untyped-def]
    del preparation
    raise AssertionError("all-current graph must not prepare or execute an operation")


async def _fixture(  # type: ignore[no-untyped-def]
    node_count: int = 2,
    *,
    operation_digest: ContentDigest | None = None,
):
    if node_count == 2:
        planner, proposal, roots, _, _, _ = _composition()
    else:
        planner, proposal, roots = _high_fan_in_composition(node_count)
    reader = _CurrentHeadReader()
    planner._head_reader = reader  # exact isolated planner host seam
    plan = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    owner, admission = _issue_current_graph_admission(
        plan, reader, operation_digest=operation_digest
    )
    return plan, reader, owner, admission


def _issue_current_graph_admission(  # type: ignore[no-untyped-def]
    plan,
    reader,
    suffix: str = "graph",
    *,
    operation_digest: ContentDigest | None = None,
):
    journal = WorkspaceMaterializationSessionJournal(
        state_store=InMemoryLocalOperationalStateStore(),
        package_head_resolver=lambda _package_ref: None,
    )
    append_graph_v2 = journal._append_graph_v2

    def measured_append(*, request):  # type: ignore[no-untyped-def]
        started = time.perf_counter_ns()
        try:
            return append_graph_v2(request=request)
        finally:
            reader.journal_ns += time.perf_counter_ns() - started

    journal._append_graph_v2 = measured_append  # type: ignore[method-assign]
    ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=reader.read_head,
        body_reader=reader.read_body,
        operation_preparer=_unexpected_preparer,
        session_journal=journal,
    )
    owner = object()
    admission = _issue_workspace_semantic_materialization_graph_execution_for_test(
        plan_result=plan,
        workspace_session_ref=f"workspace-session:{suffix}",
        epoch=f"epoch:{suffix}",
        participant_ref="participant:graph",
        actor_ref="actor:graph",
        workflow_session_ref="workflow:graph",
        materialization_attempt_ref=f"attempt:{suffix}",
        branch_baseline_ref="baseline:graph",
        branch_baseline_digest=_digest("baseline"),
        branch_baseline_grade=(
            WorkspaceMaterializationSessionBaselineGrade.SOURCE_HEAD_LOCAL_OPERATIONAL.value
        ),
        operation_ref="workspace-operation:materialize",
        operation_digest=(
            _digest("operation") if operation_digest is None else operation_digest
        ),
        authority_grade=WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
        expected_session_head_revision=0,
        expected_session_cursor=0,
        expected_predecessor_event_digest=None,
        ports=ports,
        owner=owner,
    )
    return owner, admission


@dataclass
class _ExecutedFixtureMetrics:
    preparation_ns: int = 0
    operation_ns: int = 0


async def _executed_fixture(  # type: ignore[no-untyped-def]
    node_count: int = 1,
    *,
    owner_override: object | None = None,
    tracked_product: bool = True,
    require_use_during_resolution: bool = False,
    node_aware_resolver: bool = True,
):
    profile = _profile()
    planner_implementation = SemanticImplementationCoordinate(
        implementation_ref="test.dependency-planner",
        closure_digest=_digest("dependency-planner"),
    )
    planner_configuration = SemanticConfigurationCoordinate(
        configuration_ref="test.dependency-planner",
        digest=_digest("dependency-planner-config"),
    )
    binding = CodeSemanticMaterializationProfileBinding.create(
        semantic_owner_key="aware.test.sdk",
        semantic_provider_key="test-provider",
        package_families=("public",),
        package_roles=("sdk",),
        manifest_contracts=(
            SemanticContractRef(
                key="aware.test.manifest",
                version="1",
                schema_digest=_digest("manifest-contract"),
            ),
        ),
        profile_declaration=profile,
        provider_execution_bindings=(
            ProviderExecutionBinding(
                "test-provider", _GRAPH_IMPLEMENTATION, _GRAPH_CONFIGURATION
            ),
        ),
        dependency_planner_contract=SemanticContractRef(
            key="aware.test.planner",
            version="1",
            schema_digest=_digest("planner-contract"),
        ),
        dependency_planner_implementation=planner_implementation,
        dependency_planner_configuration=planner_configuration,
        dependency_demand_contract=SemanticContractRef(
            key="aware.code.dependency-demand",
            version="1",
            schema_digest=_digest("demand-contract"),
        ),
        dependency_target_intent_contract=SemanticContractRef(
            key="aware.code.target-intent",
            version="1",
            schema_digest=_digest("intent-contract"),
        ),
        result_product_contracts=tuple(
            CodeSemanticRequiredResultProduct.create(role=role, contract=contract)
            for role, contract in (
                ("effect", _declaration().effect_contract),
                ("output", OUTPUT),
                ("result", _declaration().result_role.contract),
            )
        ),
        priority=10,
    )
    base_package = _invocation("one")[0].target_package
    entries = tuple(
        WorkspaceSemanticMaterializationPackageEntry.create(
            repository_ref="aware",
            workspace_ref="aware_kernel",
            module_ref="sdk",
            package=replace(base_package, package_ref=f"aware.sdk.demo{index:04d}"),
            package_family="public",
            package_role="sdk",
            manifest_contract=binding.manifest_contracts[0],
            manifest_relative_path=f"sdk/test-{index:04d}.aware",
            source_authority_ref="workspace-source:test",
            source_authority_digest=_digest("source"),
            owned_semantic_root_refs=(f"sdk.public.{index:04d}",),
            authored_dependencies=(),
            participation_policy=WorkspaceSemanticMaterializationParticipationPolicy.create(
                policy_ref=f"policy:test-sdk-{index:04d}",
                policy_revision=1,
                package_ref=f"aware.sdk.demo{index:04d}",
                allowed_operation_kinds=("materialize",),
                allowed_semantic_root_refs=(f"sdk.public.{index:04d}",),
                allowed_terminal_output_roles=("output",),
                allow_unconfigured=True,
                allowed_semantic_configuration_coordinates=(),
            ),
            allowed_profile_refs=(profile.profile_ref,),
        )
        for index in range(node_count)
    )
    workspace_catalog = WorkspaceSemanticMaterializationMembershipCatalog.create(
        catalog_ref="workspace.test", catalog_generation=1, entries=entries
    )
    code_catalog = CodeSemanticContractCatalog.create(
        catalog_ref="code.test", catalog_generation=1, entries=(binding,)
    )
    domain_planner = _DomainPlanner(binding, None)
    planner = WorkspaceSemanticMaterializationGraphPlanner(
        planning_source=_FixtureOwnerPlanningSource(
            _workspace_resolver(workspace_catalog)
        ),
        workspace_catalog=_workspace_resolver(workspace_catalog),
        code_catalog=_code_resolver(
            code_catalog,
            {planner_implementation.implementation_ref: domain_planner},
        ),
        head_reader=_HeadReader(),
    )
    proposal = WorkspaceMaterializationSelectionProposal.create(
        selectors=tuple(
            sorted(
                (
                    WorkspaceMaterializationRootSelector.create(
                        selector_kind="package",
                        selector_ref=entry.package.package_ref,
                    )
                    for entry in entries
                ),
                key=lambda item: canonical_json_bytes(item.to_wire()),
            )
        )
    )
    roots = tuple(
        sorted(
            (
                WorkspaceSemanticRootCodePlan.create(
                    package_ref=entry.package.package_ref,
                    code_intent=CodeSemanticMaterializationIntent.create(
                        operation_kind="materialize",
                        requested_semantic_root_refs=entry.owned_semantic_root_refs,
                        requested_terminal_output_roles=("output",),
                        semantic_configuration_coordinate=None,
                    ),
                    required_result_products=(
                        CodeSemanticRequiredResultProduct.create(
                            role="output", contract=OUTPUT
                        ),
                    ),
                )
                for entry in entries
            ),
            key=lambda item: item.package_ref.encode(),
        )
    )
    plan_result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    store = InMemoryLocalOperationalStateStore()
    from aware_code_semantic_contract_runtime import selected_provider

    runtime, registration = _selected_graph_fixture()
    selected_provider._bind_selected_execution_lifecycle(
        runtime,
        registration,
        _FixtureGraphExecutionOrigin(),
        terminal_mode="runtime_completion",
    )

    active_node_uses: list[_FixtureGraphNodeUse] = []

    @contextmanager
    def node_use(node_admission):  # type: ignore[no-untyped-def]
        use = _FixtureGraphNodeUse(node_admission)
        active_node_uses.append(use)
        try:
            yield use
        finally:
            use.closed = True
            active_node_uses.remove(use)

    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=_BodyStore()
    )
    journal = WorkspaceMaterializationSessionJournal(
        state_store=store, package_head_resolver=lambda _package_ref: None
    )
    metrics = _ExecutedFixtureMetrics()

    async def prepare(preparation):  # type: ignore[no-untyped-def]
        preparation_started = time.perf_counter_ns()
        package = preparation.node_execution_binding.package
        marker = package.package_ref.rsplit(".", 1)[-1]
        invocation, bodies = _invocation(marker)
        invocation = replace(
            invocation,
            invocation_ref=f"invocation-{marker}",
            idempotency_key=f"invocation-{marker}",
            target_package=package,
            provider_bindings=(
                ProviderExecutionBinding(
                    "test-provider", _GRAPH_IMPLEMENTATION, _GRAPH_CONFIGURATION
                ),
            ),
        )
        operation_plan = WorkspaceMaterializeExecutionPlan.create(
            source_authority_ref="workspace-source:test",
            source_authority_digest=_digest("source").value,
            operation_ref=_Authority.operation_ref,
            operation_digest=_Authority.operation_digest,
            invocation=invocation,
            input_bodies=bodies,
        )
        class _NodeBoundResolver(_Resolver):
            async def resolve_graph_node(  # type: ignore[no-untyped-def]
                self, admission, *, node_use
            ):
                assert len(active_node_uses) == 1
                assert node_use is active_node_uses[0]
                assert not node_use.closed
                assert node_use.plan is None
                if require_use_during_resolution:
                    await asyncio.sleep(0)
                    assert active_node_uses == [node_use]
                    assert not node_use.closed
                return await super().resolve(admission)

        resolver = (
            _NodeBoundResolver(operation_plan)
            if node_aware_resolver
            else _Resolver(operation_plan)
        )
        request = _operation_request(
            operation_plan,
            resolver,
            materialization_revision=preparation.expected_package_head_revision,
            session_revision=preparation.expected_session_head_revision,
            session_cursor=preparation.expected_session_cursor,
            predecessor_event_digest=(
                None
                if preparation.expected_predecessor_event_digest is None
                else preparation.expected_predecessor_event_digest.value
            ),
        )
        admission = _operation_admission(request, operation_plan, resolver)
        operation = WorkspaceMaterializeOperation(
            runtime=runtime,
            plan_resolver=resolver,
            publisher=publisher,
            session_journal=journal,
            graph_product_registration=registration if tracked_product else None,
            graph_node_use=node_use if tracked_product else None,
        )
        execute_graph_v2 = operation._execute_graph_v2

        async def measured_execute(node_admission):  # type: ignore[no-untyped-def]
            started = time.perf_counter_ns()
            try:
                return await execute_graph_v2(node_admission)
            finally:
                metrics.operation_ns += time.perf_counter_ns() - started

        operation._execute_graph_v2 = measured_execute  # type: ignore[method-assign]
        metrics.preparation_ns += time.perf_counter_ns() - preparation_started
        return operation, admission

    ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=lambda package_ref, role: publisher._read_graph_v2_head(
            package_ref, observation_role=role
        ),
        body_reader=lambda _coordinate: None,
        operation_preparer=prepare,
        session_journal=journal,
    )
    owner = object() if owner_override is None else owner_override
    admission = _issue_workspace_semantic_materialization_graph_execution_for_test(
        plan_result=plan_result,
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        participant_ref="participant:test",
        actor_ref="actor:test",
        workflow_session_ref="workflow-session:test",
        materialization_attempt_ref="attempt:test",
        branch_baseline_ref="workspace-source-head:test",
        branch_baseline_digest=_digest("baseline"),
        branch_baseline_grade=(
            WorkspaceMaterializationSessionBaselineGrade.SOURCE_HEAD_LOCAL_OPERATIONAL.value
        ),
        operation_ref=_Authority.operation_ref,
        operation_digest=ContentDigest(_Authority.operation_digest),
        authority_grade=WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
        expected_session_head_revision=0,
        expected_session_cursor=0,
        expected_predecessor_event_digest=None,
        ports=ports,
        owner=owner,
    )
    return plan_result, publisher, owner, admission, metrics


def test_graph_execution_admission_is_nominal_and_nonportable() -> None:
    with pytest.raises(TypeError):
        AdmittedWorkspaceSemanticMaterializationGraphExecution()
    forged = object.__new__(AdmittedWorkspaceSemanticMaterializationGraphExecution)
    with pytest.raises(WorkspaceSemanticMaterializationGraphExecutionError):
        _revoke_workspace_semantic_materialization_graph_execution(
            forged, owner=object()
        )
    # A registered capability cannot be copied or serialized.
    plan, reader, owner, admission = __import__("asyncio").run(_fixture())
    del plan, reader, owner
    with pytest.raises(TypeError):
        copy.copy(admission)
    with pytest.raises(TypeError):
        copy.deepcopy(admission)
    with pytest.raises(TypeError):
        pickle.dumps(admission)
    with pytest.raises(AttributeError):
        object.__setattr__(admission, "owner", object())
    with pytest.raises(TypeError):

        class _ForeignGraphExecutionAdmission(
            AdmittedWorkspaceSemanticMaterializationGraphExecution
        ):
            pass

    forged_node = object.__new__(
        AdmittedWorkspaceSemanticMaterializationGraphNodeExecution
    )
    with pytest.raises(TypeError):
        copy.copy(forged_node)
    with pytest.raises(TypeError):
        copy.deepcopy(forged_node)
    with pytest.raises(TypeError):
        pickle.dumps(forged_node)
    with pytest.raises(AttributeError):
        object.__setattr__(forged_node, "operation", object())
    with pytest.raises(TypeError):

        class _ForeignGraphNodeAdmission(
            AdmittedWorkspaceSemanticMaterializationGraphNodeExecution
        ):
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source_runtime_type",
    (
        WorkspaceOwnerDefinedSourceAdmissionRuntime,
        WorkspaceV3OwnerDefinedSourceAdmissionRuntime,
    ),
)
async def test_owner_source_corresponds_to_live_graph_node(
    monkeypatch, source_runtime_type
) -> None:
    _, _, owner, execution, _ = await _executed_fixture()
    graph_state = _execution_state(execution)
    original_prepare = graph_state.ports.operation_preparer
    source_runtime = object.__new__(source_runtime_type)
    source_admission = object.__new__(WorkspaceOwnerDefinedSourceAdmission)
    inspections = []
    nodes = []

    def inspect(self, admission):  # type: ignore[no-untyped-def]
        assert self is source_runtime and admission is source_admission
        return inspections[-1]

    monkeypatch.setattr(source_runtime_type, "inspect", inspect)

    async def prepare(preparation):  # type: ignore[no-untyped-def]
        operation, operation_admission = await original_prepare(preparation)
        original_execute = operation._execute_graph_v2

        async def checked_execute(node):  # type: ignore[no-untyped-def]
            nodes.append(node)
            state = _graph_node_admission_state(node)
            entry = state.node_binding.package_entry
            coordinate = SemanticValueCoordinate(
                "package_authority",
                entry.manifest_contract,
                entry.source_authority_ref,
                entry.source_authority_digest,
                1,
            )
            inspections.append(
                WorkspaceOwnerDefinedSourceInspection(
                    repository_ref=entry.repository_ref,
                    workspace_ref=entry.workspace_ref,
                    module_ref=entry.module_ref,
                    package_id="fixture-package",
                    package_root="modules/fixture",
                    package_kind=entry.package.package_kind,
                    manifest_relative_path=entry.manifest_relative_path,
                    source_identity_digest=_digest("retained observation"),
                    package=entry.package,
                    manifest_contract=entry.manifest_contract,
                    profile_ref=state.node_binding.code_match.selected_binding.profile_declaration.profile_ref,
                    operation_kinds=("materialize",),
                    terminal_roles=("package_authority",),
                    configured=False,
                    package_authority=cast(
                        CodePortableSemanticPackageAuthority, object()
                    ),  # irrelevant to this correlation check
                    declaration_inventory=cast(
                        CodeSemanticDeclarationTargetInventory, object()
                    ),
                    authority_result_coordinate=coordinate,
                )
            )
            _validate_graph_node_owner_source(
                node, source_runtime=source_runtime, source_admission=source_admission
            )
            for altered in (
                replace(inspections[-1], module_ref="foreign-module"),
                replace(inspections[-1], profile_ref="foreign-profile"),
                replace(
                    inspections[-1],
                    authority_result_coordinate=replace(
                        coordinate, digest=_digest("foreign authority")
                    ),
                ),
            ):
                inspections.append(altered)
                with pytest.raises(WorkspaceMaterializeOperationError, match="differs"):
                    _validate_graph_node_owner_source(
                        node,
                        source_runtime=source_runtime,
                        source_admission=source_admission,
                    )
                inspections.pop()
            return await original_execute(node)

        operation._execute_graph_v2 = checked_execute  # type: ignore[method-assign]
        return operation, operation_admission

    graph_state.ports = replace(graph_state.ports, operation_preparer=prepare)
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        execution, owner=owner
    )
    assert result.status == "succeeded"
    with pytest.raises(WorkspaceMaterializeOperationError, match="revoked"):
        _validate_graph_node_owner_source(
            nodes[0], source_runtime=source_runtime, source_admission=source_admission
        )


@pytest.mark.asyncio
async def test_wrong_owner_rejects_before_host_access() -> None:
    _, reader, _, admission = await _fixture()
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="owner"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=object()
        )
    assert reader.runtime_head_calls == 0
    assert reader.body_calls == 0


@pytest.mark.asyncio
async def test_all_current_graph_fulfills_and_fans_out_without_execution() -> None:
    plan, reader, owner, admission = await _fixture()
    started = time.perf_counter_ns()
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    coordinator_ns = time.perf_counter_ns() - started
    result.__post_init__()
    assert result.status == "succeeded"
    assert tuple(item.outcome for item in result.ordered_node_results) == (
        "reused",
        "reused",
    )
    assert len(result.ordered_fulfilled_products) == len(plan.graph.edges) == 1
    assert reader.runtime_head_calls == 4
    assert reader.body_calls == 1
    counters = {item.counter: item.value for item in result.counter_entries}
    assert counters["executed_count"] == 0
    assert counters["reused_count"] == 2
    assert counters["publication_count"] == 0
    assert counters["session_event_count"] == 2
    assert coordinator_ns - reader.journal_ns < 100_000_000
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="consumed"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )


@pytest.mark.asyncio
async def test_successful_coordinator_execution_mints_revision_provenance() -> None:
    plan, _reader, owner, execution = await _fixture()
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        execution, owner=owner
    )
    provenance, capability = admit_completed_workspace_materialization_graph_execution(
        execution=execution,
        owner=owner,
        result=result,
    )
    assert provenance.disposition == "admitted"
    assert provenance.graph_result_digest == result.result_digest.value
    assert provenance.plan_body_size_bytes == len(canonical_json_bytes(plan.to_wire()))
    assert capability is not None


@pytest.mark.asyncio
async def test_revocation_rejects_before_host_access() -> None:
    _, reader, owner, admission = await _fixture()
    _revoke_workspace_semantic_materialization_graph_execution(admission, owner=owner)
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="consumed"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert reader.runtime_head_calls == 0


@pytest.mark.asyncio
async def test_body_absence_returns_exact_completed_prefix_failure() -> None:
    plan, reader, owner, admission = await _fixture()
    reader.bodies.clear()
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "failed"
    assert len(result.ordered_node_results) == 1
    assert result.ordered_node_results[0].node_digest == (
        plan.graph_execution_binding.ordered_node_bindings[0].node_digest
    )
    assert result.terminal_failure is not None
    assert result.terminal_failure.terminal_stage == "dependency_body_read"
    assert result.terminal_failure.failure_code == "body_absent"
    assert result.terminal_failure.terminal_node_digest == (
        plan.graph_execution_binding.ordered_node_bindings[1].node_digest
    )
    assert result.ordered_fulfilled_products == ()
    with pytest.raises(
        WorkspaceRevisionPreparationAdmissionError,
        match="exact current-process execution",
    ):
        admit_completed_workspace_materialization_graph_execution(
            execution=admission,
            owner=owner,
            result=result,
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="consumed"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("missing_role", "failure_code"),
    (
        ("dependency_h1", "target_head_absent"),
        ("dependency_h2", "target_head_disappeared"),
    ),
)
async def test_dependency_head_absence_returns_exact_terminal_failure(
    missing_role: str, failure_code: str
) -> None:
    plan, _reader, owner, admission = await _fixture()
    state = _execution_state(admission)
    original_ports = state.ports

    def selective_head(package_ref: str, role: str):
        if role == missing_role:
            return None
        return original_ports.head_reader(package_ref, role)

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=selective_head,
        body_reader=original_ports.body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=original_ports.session_journal,
    )
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "failed"
    assert result.terminal_failure is not None
    assert result.terminal_failure.failure_code == failure_code
    assert result.terminal_failure.terminal_node_digest == (
        plan.graph_execution_binding.ordered_node_bindings[1].node_digest
    )
    assert len(result.ordered_node_results) == 1


@pytest.mark.asyncio
async def test_dependency_h2_movement_returns_exact_terminal_failure() -> None:
    plan, _, owner, admission = await _fixture()
    state = _execution_state(admission)
    original_ports = state.ports

    def moved_h2(package_ref: str, role: str):
        observed = original_ports.head_reader(package_ref, role)
        if observed is None or role != "dependency_h2":
            return observed
        request = observed.head.request
        moved_request = WorkspaceSemanticMaterializationRequestV3.create(
            package=request.package,
            result_coordinate=request.result_coordinate,
            source_identity_digest=request.source_identity_digest,
            code_intent_digest=request.code_intent_digest,
            code_match_digest=request.code_match_digest,
            planning_input_digest=request.planning_input_digest,
            execution_input_closure_digest=request.execution_input_closure_digest,
            operation_result_digest=_digest("moved-operation"),
            expected_head_revision=request.expected_head_revision,
        )
        return _create_head_reread_v2_from_validated_head(
            observation_role="dependency_h2",
            materialization_head_revision=observed.materialization_head_revision,
            head=WorkspaceSemanticMaterializationHeadV3.create(request=moved_request),
        )

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=moved_h2,
        body_reader=original_ports.body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=original_ports.session_journal,
    )
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "failed"
    assert result.terminal_failure is not None
    assert result.terminal_failure.failure_code == "target_head_moved"
    assert result.terminal_failure.terminal_node_digest == (
        plan.graph_execution_binding.ordered_node_bindings[1].node_digest
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("foreign_role", "expected_body_reads"),
    (("dependency_h1", 0), ("dependency_h2", 1)),
)
async def test_foreign_dependency_head_rejects_before_foreign_or_downstream_access(
    foreign_role: str, expected_body_reads: int
) -> None:
    _, _, owner, admission = await _fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    foreign_calls: list[str] = []
    body_reads = 0

    class _ForeignHead:
        def __getattribute__(self, name: str) -> object:
            if name != "__class__":
                foreign_calls.append(name)
            return object.__getattribute__(self, name)

    foreign = _ForeignHead()

    def head_reader(package_ref: str, role: str):  # type: ignore[no-untyped-def]
        if role == foreign_role:
            return foreign
        return original_ports.head_reader(package_ref, role)

    def body_reader(coordinate):  # type: ignore[no-untyped-def]
        nonlocal body_reads
        body_reads += 1
        return original_ports.body_reader(coordinate)

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=head_reader,
        body_reader=body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=original_ports.session_journal,
    )
    with pytest.raises(TypeError, match=f"dependency {foreign_role[-2:].upper()}"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert foreign_calls == []
    assert body_reads == expected_body_reads


@pytest.mark.asyncio
async def test_exact_body_digest_mismatch_is_terminal_body_invalid() -> None:
    _, reader, owner, admission = await _fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    source = next(iter(reader.bodies.values()))
    invalid = object.__new__(SemanticBody)
    object.__setattr__(invalid, "coordinate", source.coordinate)
    object.__setattr__(invalid, "canonical_body", b"body-substituted")
    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=lambda _coordinate: invalid,
        operation_preparer=original_ports.operation_preparer,
        session_journal=original_ports.session_journal,
    )
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "failed"
    assert result.terminal_failure is not None
    assert result.terminal_failure.failure_code == "body_invalid"


@pytest.mark.asyncio
async def test_missing_node_executes_only_through_existing_admitted_operation() -> None:  # type: ignore[no-untyped-def]
    plan, publisher, owner, admission, _ = await _executed_fixture()
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "succeeded"
    assert len(result.ordered_node_results) == 1
    node = result.ordered_node_results[0]
    assert node.outcome == "executed"
    assert node.publication_receipt is not None
    assert node.operation_result_digest is not None
    assert node.package_head_reread_evidence.observation_role == "package_result"
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is not None
    )
    assert node.node_digest == (
        plan.graph_execution_binding.ordered_node_bindings[0].node_digest
    )
    counters = {item.counter: item.value for item in result.counter_entries}
    assert counters["executed_count"] == 1
    assert counters["publication_count"] == 1


@pytest.mark.asyncio
async def test_graph_node_use_covers_awaited_input_resolution() -> None:
    _, _, owner, admission, _ = await _executed_fixture(
        require_use_during_resolution=True
    )
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert result.status == "succeeded"
    assert result.ordered_node_results[0].outcome == "executed"


@pytest.mark.asyncio
async def test_graph_node_rejects_resolver_without_original_use_entrance() -> None:
    _, publisher, owner, admission, _ = await _executed_fixture(
        node_aware_resolver=False
    )
    with pytest.raises(
        WorkspaceMaterializeOperationError,
        match="graph-node-bound input resolver unavailable",
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is None
    )


@pytest.mark.asyncio
async def test_graph_node_without_tracked_product_cannot_publish() -> None:
    _, publisher, owner, admission, _ = await _executed_fixture(
        tracked_product=False
    )
    with pytest.raises(
        WorkspaceMaterializeOperationError,
        match="tracked graph-product execution unavailable",
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is None
    )


@pytest.mark.asyncio
async def test_executed_session_fence_moves_after_publication_before_append() -> None:
    _, publisher, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    journal = original_ports.session_journal
    fence = _create_workspace_materialization_production_cutover_head_v1(
        workspace_authority_root_ref="workspace-authority:test",
        workspace_authority_root_digest=_digest("workspace-authority").value,
        cutover_epoch="cutover-epoch:test",
        revision=1,
        predecessor_head_digest=None,
        writer_evidence=_writer_evidence(1),
    )
    first_stages: list[str] = []

    def moving_fence(stage: str):  # type: ignore[no-untyped-def]
        first_stages.append(stage)
        if stage == "session_append":
            assert (
                publisher._read_graph_v2_head(
                    "aware.sdk.demo0000", observation_role="package_result"
                )
                is not None
            )
            assert journal._read_graph_v2_head("workspace-session:test") is None
            raise RuntimeError("injected-cutover-movement")
        return fence

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=journal,
        cutover_fence_reader=moving_fence,
    )
    with pytest.raises(RuntimeError, match="injected-cutover-movement"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert first_stages == ["operation_admission", "session_append"]
    orphan = publisher._read_graph_v2_head(
        "aware.sdk.demo0000", observation_role="package_result"
    )
    assert orphan is not None
    assert journal._read_graph_v2_head("workspace-session:test") is None
    assert _execution_state(admission).status == "interrupted_resumable"

    resumed_stages: list[str] = []

    def stable_fence(stage: str):  # type: ignore[no-untyped-def]
        resumed_stages.append(stage)
        return fence

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=journal,
        cutover_fence_reader=stable_fence,
    )
    resumed = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert resumed.status == "succeeded"
    assert resumed_stages == ["operation_admission", "session_append"]
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        == orphan
    )
    assert journal._read_graph_v2_head("workspace-session:test") is not None


@pytest.mark.asyncio
async def test_ten_missing_nodes_execute_in_exact_plan_order() -> None:
    plan, _, owner, admission, metrics = await _executed_fixture(10)
    started = time.perf_counter_ns()
    result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    coordinator_overhead_ns = (
        time.perf_counter_ns() - started - metrics.preparation_ns - metrics.operation_ns
    )
    assert result.status == "succeeded"
    assert tuple(item.node_digest for item in result.ordered_node_results) == tuple(
        item.node_digest for item in plan.graph_execution_binding.ordered_node_bindings
    )
    assert all(item.outcome == "executed" for item in result.ordered_node_results)
    assert len(result.ordered_fulfilled_products) == 0
    counters = {item.counter: item.value for item in result.counter_entries}
    assert counters["executed_count"] == 10
    assert counters["publication_count"] == 10
    assert counters["session_event_count"] == 10
    assert coordinator_overhead_ns < 100_000_000
    print(
        "workspace-graph-ten-executed-overhead",
        {
            "node_count": 10,
            "coordinator_overhead_ms": round(coordinator_overhead_ns / 1_000_000, 6),
            "preparation_ms": round(metrics.preparation_ns / 1_000_000, 6),
            "operation_latency_ms": round(metrics.operation_ns / 1_000_000, 6),
        },
    )
    result.__post_init__()


@pytest.mark.asyncio
async def test_concurrent_entrance_rejects_before_additional_host_access() -> None:
    _, publisher, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocking_preparer(preparation):  # type: ignore[no-untyped-def]
        entered.set()
        await release.wait()
        return await original_ports.operation_preparer(preparation)

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=blocking_preparer,
        session_journal=original_ports.session_journal,
    )
    first = asyncio.create_task(
        WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    )
    await entered.wait()
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is None
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="busy"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is None
    )
    release.set()
    assert (await first).status == "succeeded"


@pytest.mark.asyncio
async def test_cancelled_execution_resumes_only_with_same_admission_and_owner() -> None:
    _, publisher, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    entered = asyncio.Event()

    async def interrupted_preparer(preparation):  # type: ignore[no-untyped-def]
        del preparation
        entered.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=interrupted_preparer,
        session_journal=original_ports.session_journal,
    )
    interrupted = asyncio.create_task(
        WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    )
    await entered.wait()
    interrupted.cancel()
    with pytest.raises(asyncio.CancelledError):
        await interrupted
    assert _execution_state(admission).status == "interrupted_resumable"
    assert (
        publisher._read_graph_v2_head(
            "aware.sdk.demo0000", observation_role="package_result"
        )
        is None
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError, match="owner"
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=object()
        )
    state.ports = original_ports
    resumed = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert resumed.status == "succeeded"
    resumed.__post_init__()


@pytest.mark.asyncio
async def test_cancelled_execution_reauthenticates_completed_prefix_before_resume() -> (
    None
):
    plan, _, owner, admission, _ = await _executed_fixture(3)
    state = _execution_state(admission)
    original_ports = state.ports
    entered = asyncio.Event()
    prepare_calls = 0

    async def interrupt_third(preparation):  # type: ignore[no-untyped-def]
        nonlocal prepare_calls
        prepare_calls += 1
        if prepare_calls == 3:
            entered.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")
        return await original_ports.operation_preparer(preparation)

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=interrupt_third,
        session_journal=original_ports.session_journal,
    )
    interrupted = asyncio.create_task(
        WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    )
    await entered.wait()
    interrupted.cancel()
    with pytest.raises(asyncio.CancelledError):
        await interrupted
    assert len(state.completed_results) == 2
    assert state.completed_session_cursor == 2
    state.ports = original_ports
    resumed = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert resumed.status == "succeeded"
    assert tuple(item.node_digest for item in resumed.ordered_node_results) == tuple(
        item.node_digest for item in plan.graph_execution_binding.ordered_node_bindings
    )
    assert prepare_calls == 3
    resumed.__post_init__()


@pytest.mark.asyncio
async def test_resume_authenticates_lawful_empty_prefix_pending_event() -> None:
    _, _, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    journal = original_ports.session_journal
    append = journal._append_graph_v2

    def persist_then_interrupt(*, request):  # type: ignore[no-untyped-def]
        append(request=request)
        raise RuntimeError("injected-after-persisted-event")

    journal._append_graph_v2 = persist_then_interrupt  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="injected-after-persisted-event"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert state.completed_results == ()
    assert state.status == "interrupted_resumable"

    prepare_calls = 0

    async def counted_preparer(preparation):  # type: ignore[no-untyped-def]
        nonlocal prepare_calls
        prepare_calls += 1
        return await original_ports.operation_preparer(preparation)

    journal._append_graph_v2 = append  # type: ignore[method-assign]
    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=counted_preparer,
        session_journal=journal,
    )
    resumed = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
        admission, owner=owner
    )
    assert resumed.status == "succeeded"
    assert len(resumed.ordered_node_results) == 1
    assert prepare_calls == 1
    resumed.__post_init__()


@pytest.mark.asyncio
async def test_resume_rejects_foreign_pending_event_before_operation_access() -> None:
    _, _, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    journal = original_ports.session_journal
    append = journal._append_graph_v2

    def persist_foreign_then_interrupt(*, request):  # type: ignore[no-untyped-def]
        foreign = WorkspaceMaterializationSessionAppendRequestV3.create(
            workspace_session_ref=request.workspace_session_ref,
            epoch=request.epoch,
            participant_ref="participant:foreign",
            actor_ref="actor:foreign",
            workflow_session_ref="workflow:foreign",
            materialization_attempt_ref="attempt:foreign",
            branch_baseline_ref="baseline:foreign",
            branch_baseline_digest=_digest("baseline:foreign"),
            branch_baseline_grade=request.branch_baseline_grade,
            package_ref=request.package_ref,
            operation_ref="operation:foreign",
            operation_digest=_digest("operation:foreign"),
            source_evidence=request.source_evidence,
            expected_session_head_revision=request.expected_session_head_revision,
            expected_cursor=request.expected_cursor,
            expected_predecessor_event_digest=(
                request.expected_predecessor_event_digest
            ),
        )
        append(request=foreign)
        raise RuntimeError("injected-foreign-pending-event")

    journal._append_graph_v2 = (  # type: ignore[method-assign]
        persist_foreign_then_interrupt
    )
    with pytest.raises(RuntimeError, match="injected-foreign-pending-event"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert state.completed_results == ()
    assert state.status == "interrupted_resumable"

    prepare_calls: list[object] = []

    async def forbidden_preparer(preparation):  # type: ignore[no-untyped-def]
        prepare_calls.append(preparation)
        return await original_ports.operation_preparer(preparation)

    journal._append_graph_v2 = append  # type: ignore[method-assign]
    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=forbidden_preparer,
        session_journal=journal,
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError,
        match="pending event differs",
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert prepare_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "substitution",
    (
        "package",
        "source_identity",
        "code_intent",
        "code_match",
        "planning_input",
        "result_role",
        "result_contract",
        "revision",
    ),
)
async def test_resume_rejects_semantically_foreign_executed_pending_source(
    substitution: str,
) -> None:
    _, _, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    journal = original_ports.session_journal
    append = journal._append_graph_v2
    pending_head: WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None = None

    def persist_substituted_then_interrupt(*, request):  # type: ignore[no-untyped-def]
        nonlocal pending_head
        original_source = request.source_evidence
        original_receipt = original_source.publication_receipt
        assert original_receipt is not None
        original_request = original_receipt.request
        package = original_request.package
        coordinate = original_request.result_coordinate
        source_identity = original_request.source_identity_digest
        code_intent = original_request.code_intent_digest
        code_match = original_request.code_match_digest
        planning_input = original_request.planning_input_digest
        expected_revision = original_request.expected_head_revision
        if substitution == "package":
            package = replace(package, manifest_digest=_digest("manifest:foreign"))
        elif substitution == "source_identity":
            source_identity = _digest("source-identity:foreign")
        elif substitution == "code_intent":
            code_intent = _digest("code-intent:foreign")
        elif substitution == "code_match":
            code_match = _digest("code-match:foreign")
        elif substitution == "planning_input":
            planning_input = _digest("planning-input:foreign")
        elif substitution == "result_role":
            coordinate = replace(coordinate, role="result:foreign")
        elif substitution == "result_contract":
            coordinate = replace(
                coordinate,
                contract=SemanticContractRef(
                    key="result.foreign",
                    version="1",
                    schema_digest=_digest("result-contract:foreign"),
                ),
            )
        elif substitution == "revision":
            expected_revision += 1
        else:
            raise AssertionError("unknown substitution")
        substituted_request = WorkspaceSemanticMaterializationRequestV3.create(
            package=package,
            result_coordinate=coordinate,
            source_identity_digest=source_identity,
            code_intent_digest=code_intent,
            code_match_digest=code_match,
            planning_input_digest=planning_input,
            execution_input_closure_digest=(
                original_request.execution_input_closure_digest
            ),
            operation_result_digest=original_request.operation_result_digest,
            expected_head_revision=expected_revision,
        )
        substituted_head = WorkspaceSemanticMaterializationHeadV3.create(
            request=substituted_request
        )
        head_revision = expected_revision + 1
        substituted_receipt = (
            WorkspaceSemanticMaterializationPublicationReceiptV3.create(
                request=substituted_request,
                head=substituted_head,
                prior_head_revision=expected_revision,
                head_revision=head_revision,
                head_advanced=True,
            )
        )
        pending_head = _create_head_reread_v2_from_validated_head(
            observation_role="package_result",
            materialization_head_revision=head_revision,
            head=substituted_head,
        )
        substituted_source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
            disposition="executed",
            head_reread_evidence=pending_head,
            publication_receipt=substituted_receipt,
        )
        substituted_append = WorkspaceMaterializationSessionAppendRequestV3.create(
            workspace_session_ref=request.workspace_session_ref,
            epoch=request.epoch,
            participant_ref=request.participant_ref,
            actor_ref=request.actor_ref,
            workflow_session_ref=request.workflow_session_ref,
            materialization_attempt_ref=request.materialization_attempt_ref,
            branch_baseline_ref=request.branch_baseline_ref,
            branch_baseline_digest=request.branch_baseline_digest,
            branch_baseline_grade=request.branch_baseline_grade,
            package_ref=request.package_ref,
            operation_ref=request.operation_ref,
            operation_digest=request.operation_digest,
            source_evidence=substituted_source,
            expected_session_head_revision=request.expected_session_head_revision,
            expected_cursor=request.expected_cursor,
            expected_predecessor_event_digest=(
                request.expected_predecessor_event_digest
            ),
        )
        append(request=substituted_append)
        raise RuntimeError("injected-semantic-pending-event")

    journal._append_graph_v2 = (  # type: ignore[method-assign]
        persist_substituted_then_interrupt
    )
    with pytest.raises(RuntimeError, match="injected-semantic-pending-event"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert pending_head is not None
    prepare_calls: list[object] = []

    async def forbidden_preparer(preparation):  # type: ignore[no-untyped-def]
        prepare_calls.append(preparation)
        return await original_ports.operation_preparer(preparation)

    def pending_head_reader(package_ref: str, role: str):  # type: ignore[no-untyped-def]
        if role == "package_result":
            return pending_head
        return original_ports.head_reader(package_ref, role)

    journal._append_graph_v2 = append  # type: ignore[method-assign]
    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=pending_head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=forbidden_preparer,
        session_journal=journal,
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError,
        match="pending (source|publication) differs",
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert prepare_calls == []


@pytest.mark.asyncio
async def test_resume_rejects_reused_pending_closure_substitution() -> None:
    _, _, owner, admission = await _fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    journal = original_ports.session_journal
    append = journal._append_graph_v2
    pending_head: WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None = None

    def persist_substituted_then_interrupt(*, request):  # type: ignore[no-untyped-def]
        nonlocal pending_head
        original_head = request.source_evidence.head_reread_evidence.head
        substituted_request = WorkspaceSemanticMaterializationRequestV3.create(
            package=original_head.package,
            result_coordinate=original_head.result_coordinate,
            source_identity_digest=original_head.source_identity_digest,
            code_intent_digest=original_head.code_intent_digest,
            code_match_digest=original_head.code_match_digest,
            planning_input_digest=original_head.planning_input_digest,
            execution_input_closure_digest=_digest("closure:foreign"),
            operation_result_digest=original_head.operation_result_digest,
            expected_head_revision=original_head.request.expected_head_revision,
        )
        substituted_head = WorkspaceSemanticMaterializationHeadV3.create(
            request=substituted_request
        )
        pending_head = _create_head_reread_v2_from_validated_head(
            observation_role="package_reuse",
            materialization_head_revision=(
                request.source_evidence.head_reread_evidence.materialization_head_revision
            ),
            head=substituted_head,
        )
        substituted_source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
            disposition="reused",
            head_reread_evidence=pending_head,
            publication_receipt=None,
        )
        substituted_append = WorkspaceMaterializationSessionAppendRequestV3.create(
            workspace_session_ref=request.workspace_session_ref,
            epoch=request.epoch,
            participant_ref=request.participant_ref,
            actor_ref=request.actor_ref,
            workflow_session_ref=request.workflow_session_ref,
            materialization_attempt_ref=request.materialization_attempt_ref,
            branch_baseline_ref=request.branch_baseline_ref,
            branch_baseline_digest=request.branch_baseline_digest,
            branch_baseline_grade=request.branch_baseline_grade,
            package_ref=request.package_ref,
            operation_ref=request.operation_ref,
            operation_digest=request.operation_digest,
            source_evidence=substituted_source,
            expected_session_head_revision=request.expected_session_head_revision,
            expected_cursor=request.expected_cursor,
            expected_predecessor_event_digest=(
                request.expected_predecessor_event_digest
            ),
        )
        append(request=substituted_append)
        raise RuntimeError("injected-reuse-closure")

    journal._append_graph_v2 = (  # type: ignore[method-assign]
        persist_substituted_then_interrupt
    )
    with pytest.raises(RuntimeError, match="injected-reuse-closure"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert pending_head is not None

    def pending_head_reader(package_ref: str, role: str):  # type: ignore[no-untyped-def]
        if role == "package_reuse":
            return pending_head
        return original_ports.head_reader(package_ref, role)

    journal._append_graph_v2 = append  # type: ignore[method-assign]
    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=pending_head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=original_ports.operation_preparer,
        session_journal=journal,
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationGraphExecutionError,
        match="not exactly reusable",
    ):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )


@pytest.mark.asyncio
async def test_foreign_prepared_operation_rejects_without_property_access() -> None:
    _, _, owner, admission, _ = await _executed_fixture()
    state = _execution_state(admission)
    original_ports = state.ports
    calls: list[str] = []

    class _ForeignOperation:
        @property
        def runtime(self):  # type: ignore[no-untyped-def]
            calls.append("runtime")

    async def foreign_preparer(preparation):  # type: ignore[no-untyped-def]
        _, operation_admission = await original_ports.operation_preparer(preparation)
        return _ForeignOperation(), operation_admission

    state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
        head_reader=original_ports.head_reader,
        body_reader=original_ports.body_reader,
        operation_preparer=foreign_preparer,
        session_journal=original_ports.session_journal,
    )
    with pytest.raises(TypeError, match="prepared graph operation must be exact"):
        await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=owner
        )
    assert calls == []
    assert _execution_state(admission).status == "interrupted_resumable"
