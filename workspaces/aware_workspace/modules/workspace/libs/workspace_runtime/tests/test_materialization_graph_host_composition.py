from __future__ import annotations

import asyncio
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime import ContentDigest, SemanticBody
from aware_local_service_runtime import InMemoryLocalOperationalStateStore
from aware_workspace_runtime.materialization_graph_host_composition import (
    WorkspaceMaterializationGraphBacking,
    WorkspaceCurrentGraphProductOperationFactory,
    WorkspaceCurrentGraphProductOperationSet,
    group_current_workspace_graph_product_sources,
    resolve_selected_workspace_graph_products,
    plan_current_workspace_materialization_graph,
    plan_workspace_materialization_graph,
)
from aware_workspace_runtime import materialization_graph_host_composition as graph_host
from aware_workspace_runtime.semantic_dependency_graph_codec import (
    decode_workspace_semantic_materialization_graph_plan_result,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4,
)
from aware_workspace_runtime.semantic_dependency_graph import (
    WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2,
)
from test_materialization_graph_planner import _composition
from test_current_head_two_stage_host import real_environment_factory, real_sdk_factory
from test_v3_direct_command_composition import real_sdk_graph_product_factory
from test_semantic_materialization_publication import (
    SOURCE,
    _graph_v2_fixture,
    _coordinate,
    _runtime,
    _state_bound_head_fixture,
    _declaration,
)


class _ReadInput:
    """Non-authorizing inputs for the package-head reader's value projection."""

    def __init__(self, **fields):
        self.__dict__.update(fields)

    def __post_init__(self) -> None:
        pass


def _observe_matching_package(backing, request):
    entry = _ReadInput(
        package=request.package,
        source_identity_digest=request.source_identity_digest,
    )
    binding = _ReadInput(
        binding_digest=ContentDigest.of_bytes(b"selected-binding"),
        result_product_contracts=(
            _ReadInput(
                role=request.result_coordinate.role,
                contract=request.result_coordinate.contract,
            ),
        ),
    )
    match = _ReadInput(
        selected_binding=binding,
        match_digest=request.code_match_digest,
    )
    intent = _ReadInput(
        intent_digest=request.code_intent_digest,
        requested_terminal_output_roles=(request.result_coordinate.role,),
    )
    return asyncio.run(
        backing.head_reader.observe(
            entry=entry,
            local_code_match=match,
            intent=intent,
            planning_demand_closure=_ReadInput(),
            planning_input_digest=request.planning_input_digest,
        )
    )


def test_graph_backing_reuses_one_body_head_and_session_store(tmp_path) -> None:
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:test",
        state_store=InMemoryLocalOperationalStateStore(),
    )
    body = b'{"source":"one"}'
    coordinate = _coordinate("source", SOURCE, "source:one", body)
    assert backing.read_dependency_body(coordinate) is None
    backing.body_store.store_body(
        "cas://workspace-semantic-materialization/body/"
        + coordinate.digest.value[7:],
        body,
    )
    assert backing.read_dependency_body(coordinate) == SemanticBody(
        coordinate=coordinate, canonical_body=body
    )
    assert backing.head_reader._publisher is backing.publisher
    assert backing.session_journal._package_head_resolver == backing.publisher.read_head


def test_graph_host_ports_use_the_same_backing_without_issuing_authority(tmp_path) -> None:
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:test",
        runtime=_runtime(),
        state_store=InMemoryLocalOperationalStateStore(),
    )
    async def prepare(_preparation):
        raise AssertionError("host issuance must not prepare an operation")

    ports = backing.graph_host_ports(
        operation_preparer=prepare,
        cutover_fence_reader=lambda _stage: None,
    )
    assert ports.session_journal is backing.session_journal
    assert ports.body_reader.__self__ is backing
    assert ports.operation_preparer is prepare


async def test_graph_planning_round_trips_one_contextual_result() -> None:
    planner, selection, root_plans, *_ = _composition()
    plan, wire = await plan_workspace_materialization_graph(
        planner=planner,
        selection=selection,
        root_plans=root_plans,
    )
    assert decode_workspace_semantic_materialization_graph_plan_result(
        wire, expected=plan
    ) == plan


async def test_current_graph_plan_requires_every_reachable_owner_source(
    monkeypatch,
) -> None:
    planner, selection, root_plans, *_ = _composition()
    admission = object()

    class CurrentPair:
        def validate_current_catalog_epoch(self, epoch, *, expected):
            assert epoch is admission and expected is admission

        def read_code_catalog_for_epoch(self, epoch, *, expected):
            self.validate_current_catalog_epoch(epoch, expected=expected)
            return admission

    monkeypatch.setattr(
        graph_host,
        "compose_current_workspace_graph_planner",
        lambda **_values: planner,
    )
    from aware_code_retained_registry_policy_runtime import planning_source_composition

    monkeypatch.setattr(
        planning_source_composition,
        "validate_composed_retained_planning_source",
        lambda *_values: None,
    )
    root_package = planner._workspace.package("package:sdk").package
    with pytest.raises(RuntimeError, match="reachable graph packages differ"):
        await plan_current_workspace_materialization_graph(
            code_host=object(),
            catalog_host=CurrentPair(),
            epoch=admission,
            expected_epoch=admission,
            original_sources=(),
            package_closure=(root_package,),
            backing=object(),
            selection=selection,
            root_plans=root_plans,
        )


def test_generic_graph_planning_preserves_state_bound_head_identity(tmp_path) -> None:
    _runtime, request, head, bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    state_store = InMemoryLocalOperationalStateStore()
    state_store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:versioned-head-test",
        state_store=state_store,
    )
    backing.body_store.store_bodies(tuple(bodies.bodies.items()))

    observed = _observe_matching_package(backing, request)
    assert observed.state == "stale"
    assert observed.stored_head_contract == WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD_V4
    assert observed.stored_package_occurrence == head.package_occurrence
    assert observed.to_wire()["contract"] == WORKSPACE_SEMANTIC_PACKAGE_HEAD_OBSERVATION_V2
    assert observed.predecessor_head_revision == 1
    assert observed.predecessor_head_digest == head.head_digest
    assert observed.historical_execution_input_closure_digest is None
    assert observed.expected_post_revision == 2


def test_graph_prior_read_rechecks_original_v4_head_and_state(
    tmp_path, monkeypatch
) -> None:
    """The command-use reader binds the real retained V4 result and state."""
    from aware_code_semantic_contract_runtime.product_contribution import (
        SelectedProviderProductContribution,
    )
    from aware_workspace_runtime import direct_command_composition as command

    runtime, request, head, bodies, output_state, *_ = _state_bound_head_fixture()
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:prior-state-test",
        state_store=store,
    )
    backing.body_store.store_bodies(tuple(bodies.bodies.items()))
    observation = _observe_matching_package(backing, request)
    registration = object()
    operation = SimpleNamespace(
        _publisher=backing.publisher,
        _runtime=runtime,
        _graph_product_registration=registration,
    )
    node_digest = ContentDigest.of_bytes(b"original-node")
    node = SimpleNamespace(
        operation=operation,
        node_binding=SimpleNamespace(
            node_digest=node_digest, package=request.package
        ),
        plan_result=SimpleNamespace(
            graph=SimpleNamespace(
                nodes=(SimpleNamespace(
                    node_digest=node_digest,
                    package=request.package,
                    head_observation=observation,
                ),)
            )
        ),
    )
    original = SimpleNamespace(runtime=runtime, registration=registration)
    selected = SimpleNamespace(
        expected=original,
        executable=SimpleNamespace(declaration=_declaration()),
    )
    contribution = object.__new__(SelectedProviderProductContribution)
    checked_occurrences = []

    class Source:
        def validate_publication_package_occurrence(self, _admission, *, occurrence):
            checked_occurrences.append(occurrence)
            if occurrence != head.package_occurrence:
                raise RuntimeError("source occurrence differs")

    monkeypatch.setattr(
        command, "read_selected_provider_product_contribution", lambda _value: selected
    )
    monkeypatch.setattr(
        command, "_original_graph_semantic_source", lambda _record: (Source(), object())
    )
    from aware_workspace_runtime import materialization_operation

    monkeypatch.setattr(
        materialization_operation, "_graph_node_admission_state", lambda _value: node
    )
    record = SimpleNamespace(
        node_admission=object(),
        publisher=backing.publisher,
        product_contribution=contribution,
    )
    binding = command._GraphPriorOutputStateBinding(
        request.package,
        1,
        head.head_digest,
        head.package_occurrence,
        "output",
        "aware_dev_sdk",
        output_state,
    )
    assert command._read_graph_prior_output_state(record, binding) == output_state
    assert checked_occurrences == [head.package_occurrence] * 2
    with pytest.raises(RuntimeError, match="predecessor unavailable"):
        command._read_graph_prior_output_state(
            record,
            replace(binding, occurrence=replace(head.package_occurrence, package_id="other")),
        )
    with pytest.raises(RuntimeError, match="predecessor unavailable"):
        command._read_graph_prior_output_state(
            record, replace(binding, head_digest=ContentDigest.of_bytes(b"other"))
        )


def test_generic_graph_planning_preserves_v3_head_identity(tmp_path) -> None:
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="9"
    )
    backing = WorkspaceMaterializationGraphBacking(
        state_root=tmp_path,
        repository_binding_ref="repository:v3-head-test",
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
    )
    receipt, _reread = backing.publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    observed = _observe_matching_package(backing, request)
    assert observed.state == "current"
    assert observed.predecessor_head_digest == receipt.head.head_digest
    assert observed.expected_post_head_digest == receipt.head.head_digest


async def test_product_assignment_precedes_origin_binding(
    tmp_path, real_sdk_factory, real_sdk_graph_product_factory, monkeypatch
) -> None:
    from aware_code_retained_registry_policy_runtime import product_execution
    from aware_code_semantic_contract_runtime import (
        SemanticConfigurationCoordinate,
        SemanticImplementationCoordinate,
        SemanticPackageCoordinate,
    )
    from aware_code_semantic_contract_runtime.product_contribution import (
        read_selected_provider_product_catalog_contribution,
    )
    from aware_workspace_runtime import direct_command_composition as composition
    from test_current_head_two_stage_host import qualified_sdk_five_target_repository
    from test_dependency_scope_admission import fixture as source_fixture

    planner, selection, root_plans, *_ = _composition()
    plan_result = await planner.plan(
        selection_proposal=selection, requested_root_code_plans=root_plans
    )

    async with source_fixture(tmp_path, qualified_sdk_five_target_repository) as (
        _, _, _, borrowed, _, _
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_sdk_factory,
            product_factory_admissions=(real_sdk_graph_product_factory,),
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            composition._admit_direct_workspace_selected_provider_catalogs(staged)
            digest = ContentDigest.of_bytes(b"fixture graph composition")
            coordinates = dict(
                composition_implementation=SemanticImplementationCoordinate(
                    "fixture.graph.composition", digest
                ),
                composition_configuration=SemanticConfigurationCoordinate(
                    "fixture.graph.composition", digest
                ),
                policy_implementation=SemanticImplementationCoordinate(
                    "fixture.graph.policy", digest
                ),
                policy_configuration=SemanticConfigurationCoordinate(
                    "fixture.graph.policy", digest
                ),
            )
            with composition._compose_direct_workspace_policy_host(
                staged, **coordinates
            ) as host:
                epoch = staged.command.catalog_host.read_initial_epoch()
                expected = staged.command.catalog_host.read_initial_publication()
                package = SemanticPackageCoordinate(
                    "fixture.graph", "sdk", digest
                )

                class Correspondence:
                    def package(self):
                        return package

                source = composition._SuccessorGraphNodeSourceInputs(
                    staged, host, object(), (package,), Correspondence(),
                    epoch, expected,
                )
                runtime_binding = staged.product_runtime_bindings[0]
                product_catalog = (
                    read_selected_provider_product_catalog_contribution(
                        staged.product_contributions[0]
                    )
                )
                assert resolve_selected_workspace_graph_products(
                    staged=staged,
                    selected_bindings=product_catalog.entries,
                ) == ((runtime_binding.runtime, runtime_binding.registration),)
                product_entry = product_catalog.entries[0]
                changed_fields = {
                    field.name: getattr(product_entry, field.name)
                    for field in fields(product_entry)
                    if field.name != "binding_digest"
                }
                changed_fields["priority"] = product_entry.priority + 1
                changed_profile = type(product_entry).create(**changed_fields)
                with pytest.raises(
                    RuntimeError,
                    match="graph node product profile missing or ambiguous",
                ):
                    resolve_selected_workspace_graph_products(
                        staged=staged,
                        selected_bindings=(changed_profile,),
                    )
                with pytest.raises(
                    RuntimeError,
                    match="graph node product profile missing or ambiguous",
                ):
                    resolve_selected_workspace_graph_products(
                        staged=staged,
                        selected_bindings=tuple(
                            item.code_match.selected_binding
                            for item in plan_result.graph_execution_binding.ordered_node_bindings
                        ),
                    )

                def premature_bind(*_args):
                    raise AssertionError("Code product origin bound before successor")

                monkeypatch.setattr(
                    product_execution, "bind_product_execution_origin",
                    premature_bind,
                )
                backing = WorkspaceMaterializationGraphBacking(
                    state_root=tmp_path / "graph-state",
                    repository_binding_ref="repository:graph-test",
                    state_store=InMemoryLocalOperationalStateStore(),
                )
                with pytest.raises(
                    RuntimeError, match="graph node product profile missing or ambiguous"
                ):
                    WorkspaceCurrentGraphProductOperationFactory(
                        staged=staged,
                        code_host=host,
                        registration=runtime_binding.registration,
                        runtime=runtime_binding.runtime,
                        plan_result=plan_result,
                        source_inputs=(source,),
                        backing=backing,
                    )

                graph_nodes = plan_result.graph_execution_binding.ordered_node_bindings
                complete_sources = tuple(
                    composition._SuccessorGraphNodeSourceInputs(
                        staged,
                        host,
                        source.planning_source,
                        source.package_closure,
                        type("SourceCorrespondence", (), {
                            "package": lambda self, value=node.package: value,
                        })(),
                        epoch,
                        expected,
                    )
                    for node in graph_nodes
                )
                with pytest.raises(
                    RuntimeError, match="graph node product profile missing or ambiguous"
                ):
                    group_current_workspace_graph_product_sources(
                        staged=staged,
                        code_host=host,
                        plan_result=plan_result,
                        source_inputs=complete_sources,
                    )

                monkeypatch.setattr(
                    graph_host,
                    "resolve_selected_workspace_graph_products",
                    lambda **_values: (
                        (runtime_binding.runtime, runtime_binding.registration),
                    ) * len(graph_nodes),
                )
                monkeypatch.setattr(
                    composition,
                    "_compose_successor_graph_node_source_inputs",
                    lambda _staged, _host, **values: composition._SuccessorGraphNodeSourceInputs(
                        staged, host, **values
                    ),
                )
                with pytest.raises(RuntimeError, match="source set is incomplete"):
                    group_current_workspace_graph_product_sources(
                        staged=staged,
                        code_host=host,
                        plan_result=plan_result,
                        source_inputs=complete_sources[:-1],
                    )
                grouped = group_current_workspace_graph_product_sources(
                    staged=staged,
                    code_host=host,
                    plan_result=plan_result,
                    source_inputs=complete_sources,
                )
                assert len(grouped) == 1
                assert grouped[0][:2] == (
                    runtime_binding.runtime,
                    runtime_binding.registration,
                )
                assert tuple(
                    item.correspondence.package().package_ref for item in grouped[0][2]
                ) == tuple(node.package.package_ref for node in graph_nodes)
                with pytest.raises(RuntimeError, match="duplicate successor graph node source"):
                    group_current_workspace_graph_product_sources(
                        staged=staged,
                        code_host=host,
                        plan_result=plan_result,
                        source_inputs=complete_sources[:-1] + complete_sources[:1],
                    )
                with pytest.raises(
                    AssertionError, match="Code product origin bound before successor"
                ):
                    WorkspaceCurrentGraphProductOperationSet(
                        staged=staged,
                        code_host=host,
                        plan_result=plan_result,
                        source_inputs=complete_sources,
                        backing=backing,
                    )
                from aware_code_retained_registry_policy_runtime import direct_host

                assert direct_host._HOSTS.get(host) is None


async def test_real_environment_catalog_enters_paired_host_before_graph_selection(
    tmp_path, real_environment_factory
) -> None:
    from aware_code_semantic_contract_runtime.stage_contribution import (
        read_selected_provider_stage_catalog_contribution,
    )
    from aware_workspace_runtime import direct_command_composition as composition
    from test_current_head_two_stage_host import qualified_repository
    from test_dependency_scope_admission import fixture as source_fixture

    async with source_fixture(tmp_path, qualified_repository) as (
        _, _, _, borrowed, _, _
    ):
        with composition._compose_direct_workspace_staged_command_resources(
            factory_admission=real_environment_factory,
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="consumer/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as staged:
            composition._admit_direct_workspace_selected_provider_catalogs(staged)
            entries = read_selected_provider_stage_catalog_contribution(
                staged.contribution
            ).entries
            assert len(entries) == 2
            authority = next(
                entry for entry in entries
                if entry.profile_declaration.profile_ref
                == "aware.environment.authority-derivation"
            )
            with pytest.raises(RuntimeError, match="missing or ambiguous"):
                resolve_selected_workspace_graph_products(
                    staged=staged, selected_bindings=(authority,)
                )
