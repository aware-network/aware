from __future__ import annotations

from typing import cast

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalog,
    CodeSemanticContractMatchAdmission,
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2,
    WorkspaceAdmittedPackageIntent,
    WorkspaceFulfilledDependencyProductV3,
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionEventRereadEvidenceV3,
    WorkspaceMaterializationSessionEventV3,
    WorkspaceMaterializationSessionFanoutReceiptV3,
    WorkspaceMaterializationSessionHeadV2,
    WorkspaceMaterializationSessionSourceEvidenceV3,
    WorkspaceSemanticMaterializationFailureEvidenceEntryV2,
    WorkspaceSemanticMaterializationGraphExecutionBinding,
    WorkspaceSemanticMaterializationGraphExecutionMetrics,
    WorkspaceSemanticMaterializationGraphPlanAdmission,
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationNodeExecutionBinding,
    WorkspaceSemanticMaterializationNodeResultEvidenceV3,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    WorkspaceSemanticMaterializationRequestV3,
    WorkspaceSemanticMaterializationResultCounterEntryV2,
    WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
    WorkspaceSemanticMaterializationTerminalFailureV3,
    decode_workspace_fulfilled_dependency_product_v2,
    decode_workspace_materialization_session_append_request_v2,
    decode_workspace_materialization_session_event_reread_evidence_v2,
    decode_workspace_materialization_session_event_v2,
    decode_workspace_materialization_session_fanout_receipt_v2,
    decode_workspace_materialization_session_source_evidence_v2,
    decode_workspace_semantic_materialization_failure_evidence_entry_v2,
    decode_workspace_semantic_materialization_graph_execution_binding,
    decode_workspace_semantic_materialization_graph_plan_result,
    decode_workspace_semantic_materialization_graph_result_v2,
    decode_workspace_semantic_materialization_head_reread_evidence_v2,
    decode_workspace_semantic_materialization_head_v2,
    decode_workspace_semantic_materialization_node_execution_binding,
    decode_workspace_semantic_materialization_node_result_evidence_v2,
    decode_workspace_semantic_materialization_publication_receipt_v2,
    decode_workspace_semantic_materialization_request_v2,
    decode_workspace_semantic_materialization_terminal_failure_v2,
    encode_workspace_fulfilled_dependency_product_v2,
    encode_workspace_materialization_session_append_request_v2,
    encode_workspace_materialization_session_event_reread_evidence_v2,
    encode_workspace_materialization_session_event_v2,
    encode_workspace_materialization_session_fanout_receipt_v2,
    encode_workspace_materialization_session_source_evidence_v2,
    encode_workspace_semantic_materialization_failure_evidence_entry_v2,
    encode_workspace_semantic_materialization_graph_execution_binding,
    encode_workspace_semantic_materialization_graph_plan_result,
    encode_workspace_semantic_materialization_graph_result_v2,
    encode_workspace_semantic_materialization_head_reread_evidence_v2,
    encode_workspace_semantic_materialization_head_v2,
    encode_workspace_semantic_materialization_node_execution_binding,
    encode_workspace_semantic_materialization_node_result_evidence_v2,
    encode_workspace_semantic_materialization_publication_receipt_v2,
    encode_workspace_semantic_materialization_request_v2,
    encode_workspace_semantic_materialization_terminal_failure_v2,
)
from aware_workspace_runtime.semantic_dependency_graph import (
    _create_planner_graph_plan_result,
)
from test_materialization_graph_planner import (  # pyright: ignore[reportMissingImports]
    _composition,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _plan_admission_with(
    result: WorkspaceSemanticMaterializationGraphPlanResult,
    *,
    match_admission_digests: tuple[ContentDigest, ...],
) -> WorkspaceSemanticMaterializationGraphPlanAdmission:
    admitted = result.graph_plan_admission
    return WorkspaceSemanticMaterializationGraphPlanAdmission.create(
        selection_resolution_digest=admitted.selection_resolution_digest,
        workspace_catalog_ref=admitted.workspace_catalog_ref,
        workspace_catalog_generation=admitted.workspace_catalog_generation,
        workspace_catalog_root_digest=admitted.workspace_catalog_root_digest,
        code_catalog_ref=admitted.code_catalog_ref,
        code_catalog_generation=admitted.code_catalog_generation,
        code_catalog_root_digest=admitted.code_catalog_root_digest,
        code_catalog_match_admission_digests=match_admission_digests,
        graph_digest=admitted.graph_digest,
    )


def _plan_result_with_admission(
    result: WorkspaceSemanticMaterializationGraphPlanResult,
    admission: WorkspaceSemanticMaterializationGraphPlanAdmission,
) -> WorkspaceSemanticMaterializationGraphPlanResult:
    return WorkspaceSemanticMaterializationGraphPlanResult.create(
        selection_resolution=result.selection_resolution,
        graph=result.graph,
        graph_plan_admission=admission,
        graph_execution_binding=result.graph_execution_binding,
        timing_entries=result.timing_entries,
        counter_entries=result.counter_entries,
    )


def _node_binding_with(
    result: WorkspaceSemanticMaterializationGraphPlanResult,
    admitted: WorkspaceSemanticMaterializationNodeExecutionBinding,
    *,
    code_match_admission: CodeSemanticContractMatchAdmission | None = None,
    workspace_admitted_intent: WorkspaceAdmittedPackageIntent | None = None,
) -> WorkspaceSemanticMaterializationNodeExecutionBinding:
    return WorkspaceSemanticMaterializationNodeExecutionBinding.create(
        graph=result.graph,
        node_digest=admitted.node_digest,
        package=admitted.package,
        package_entry=admitted.package_entry,
        code_intent=admitted.code_intent,
        workspace_admitted_intent=(
            admitted.workspace_admitted_intent
            if workspace_admitted_intent is None
            else workspace_admitted_intent
        ),
        planning_context=admitted.planning_context,
        code_match=admitted.code_match,
        code_match_admission=(
            admitted.code_match_admission
            if code_match_admission is None
            else code_match_admission
        ),
        dependency_demand_set=admitted.dependency_demand_set,
        planning_input_digest=admitted.planning_input_digest,
        planning_demand_closure=admitted.planning_demand_closure,
        incoming_target_resolutions=admitted.incoming_target_resolutions,
        required_result_products=admitted.required_result_products,
    )


def _result_coordinate(
    binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    key: str,
) -> SemanticValueCoordinate:
    required = binding.required_result_products[0]
    return SemanticValueCoordinate(
        role=required.role,
        contract=required.contract,
        value_ref=f"cas:{key}",
        digest=_digest(f"body:{key}"),
        size_bytes=32,
    )


def _head_reread(
    binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
    *,
    role: str,
    coordinate: SemanticValueCoordinate,
    closure_key: str,
    head_key: str,
) -> WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=binding.package,
        result_coordinate=coordinate,
        source_identity_digest=binding.package_entry.source_identity_digest,
        code_intent_digest=binding.code_intent.intent_digest,
        code_match_digest=binding.code_match.match_digest,
        planning_input_digest=binding.planning_input_digest,
        execution_input_closure_digest=_digest(closure_key),
        operation_result_digest=_digest(f"operation:{head_key}"),
        expected_head_revision=6,
    )
    return WorkspaceSemanticMaterializationHeadRereadEvidenceV3.create(
        observation_role=role,
        materialization_head_revision=7,
        head=WorkspaceSemanticMaterializationHeadV3.create(request=request),
    )


def _publication_receipt(
    head: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
) -> WorkspaceSemanticMaterializationPublicationReceiptV3:
    return WorkspaceSemanticMaterializationPublicationReceiptV3.create(
        request=head.head.request,
        head=head.head,
        prior_head_revision=head.materialization_head_revision - 1,
        head_revision=head.materialization_head_revision,
        head_advanced=True,
    )


def _session_evidence(
    *,
    key: str,
    disposition: str,
    head: WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    publication: WorkspaceSemanticMaterializationPublicationReceiptV3 | None,
) -> tuple[
    WorkspaceMaterializationSessionSourceEvidenceV3,
    WorkspaceMaterializationSessionEventRereadEvidenceV3,
    WorkspaceMaterializationSessionFanoutReceiptV3,
]:
    source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
        disposition=disposition,
        head_reread_evidence=head,
        publication_receipt=publication,
    )
    append = WorkspaceMaterializationSessionAppendRequestV3.create(
        workspace_session_ref="workspace-session:test",
        epoch="epoch:test",
        participant_ref="participant:test",
        actor_ref="actor:test",
        workflow_session_ref="workflow-session:test",
        materialization_attempt_ref=f"attempt:{key}",
        branch_baseline_ref="baseline:test",
        branch_baseline_digest=_digest("baseline:test"),
        branch_baseline_grade="source_head_local_operational",
        package_ref=head.package.package_ref,
        operation_ref=f"operation:{key}",
        operation_digest=_digest(f"operation:{key}"),
        source_evidence=source,
        expected_session_head_revision=0,
        expected_cursor=0,
        expected_predecessor_event_digest=None,
    )
    event = WorkspaceMaterializationSessionEventV3.create(append_request=append)
    session_head = WorkspaceMaterializationSessionHeadV2.from_event(event)
    reread = WorkspaceMaterializationSessionEventRereadEvidenceV3.create(
        session_head_revision=1,
        event=event,
        session_head=session_head,
    )
    fanout = WorkspaceMaterializationSessionFanoutReceiptV3.create(
        append_request=append,
        event_reread_evidence=reread,
        prior_head_revision=0,
        head_revision=1,
        head_advanced=True,
    )
    return source, reread, fanout


def _result_counters(
    **overrides: int,
) -> tuple[WorkspaceSemanticMaterializationResultCounterEntryV2, ...]:
    values = {
        "dependency_body_observation_count": 1,
        "dependency_head_observation_count": 2,
        "edge_count": 1,
        "executed_count": 1,
        "fulfilled_product_count": 1,
        "node_count": 2,
        "package_head_observation_count": 2,
        "publication_count": 1,
        "reused_count": 1,
        "session_event_count": 2,
        **overrides,
    }
    return tuple(
        WorkspaceSemanticMaterializationResultCounterEntryV2(
            counter=counter,
            value=values[counter],
        )
        for counter in WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2
    )


async def _portable_execution_evidence() -> tuple[
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceFulfilledDependencyProductV3,
    WorkspaceSemanticMaterializationNodeResultEvidenceV3,
    WorkspaceSemanticMaterializationNodeResultEvidenceV3,
]:
    planner, proposal, roots, *_ = _composition()
    plan = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    target, consumer = plan.graph_execution_binding.ordered_node_bindings
    resolution = consumer.incoming_target_resolutions[0]
    edge = next(
        item
        for item in plan.graph.edges
        if item.consumer_node_digest == consumer.node_digest
        and item.target_resolution_digest == resolution.resolution_digest
    )
    target_coordinate = _result_coordinate(target, "target")
    h1 = _head_reread(
        target,
        role="dependency_h1",
        coordinate=target_coordinate,
        closure_key="target-closure",
        head_key="target-head",
    )
    h2 = _head_reread(
        target,
        role="dependency_h2",
        coordinate=target_coordinate,
        closure_key="target-closure",
        head_key="target-head",
    )
    product = WorkspaceFulfilledDependencyProductV3.create(
        plan_result=plan,
        consumer_node_digest=consumer.node_digest,
        target_node_digest=edge.target_node_digest,
        target_resolution=resolution,
        head_h1=h1,
        head_h2=h2,
        consumed_body_coordinate=target_coordinate,
    )
    target_result_head = _head_reread(
        target,
        role="package_result",
        coordinate=target_coordinate,
        closure_key="target-operation-closure",
        head_key="target-result-head",
    )
    target_publication = _publication_receipt(target_result_head)
    target_source, target_event, target_fanout = _session_evidence(
        key="target",
        disposition="executed",
        head=target_result_head,
        publication=target_publication,
    )
    target_result = WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
        plan_result=plan,
        node_digest=target.node_digest,
        outcome="executed",
        execution_input_closure_digest=target_result_head.execution_input_closure_digest,
        ordered_fulfilled_products=(),
        package_head_reread_evidence=target_result_head,
        publication_receipt=target_publication,
        session_source_evidence=target_source,
        session_event_reread_evidence=target_event,
        session_fanout_receipt=target_fanout,
    )
    consumer_head = _head_reread(
        consumer,
        role="package_reuse",
        coordinate=_result_coordinate(consumer, "consumer"),
        closure_key="consumer-operation-closure",
        head_key="consumer-result-head",
    )
    consumer_source, consumer_event, consumer_fanout = _session_evidence(
        key="consumer",
        disposition="reused",
        head=consumer_head,
        publication=None,
    )
    consumer_result = WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
        plan_result=plan,
        node_digest=consumer.node_digest,
        outcome="reused",
        execution_input_closure_digest=consumer_head.execution_input_closure_digest,
        ordered_fulfilled_products=(product,),
        package_head_reread_evidence=consumer_head,
        publication_receipt=None,
        session_source_evidence=consumer_source,
        session_event_reread_evidence=consumer_event,
        session_fanout_receipt=consumer_fanout,
    )
    return plan, h1, h2, product, target_result, consumer_result


@pytest.mark.asyncio
async def test_v2_plan_codec_rejects_retained_digest_boolean_integer_poison() -> None:
    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    wire = encode_workspace_semantic_materialization_graph_plan_result(result)
    assert b'"allow_unconfigured":true' in wire
    poisoned = wire.replace(b'"allow_unconfigured":true', b'"allow_unconfigured":1')
    assert poisoned != wire
    with pytest.raises(ContractViolation, match="canonical"):
        decode_workspace_semantic_materialization_graph_plan_result(
            poisoned, expected=result
        )


@pytest.mark.asyncio
async def test_v2_plan_requires_exact_code_match_admission_closure() -> None:
    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    digests = cast(
        tuple[ContentDigest, ...],
        result.graph_plan_admission.code_catalog_match_admission_digests,
    )
    extra = tuple(
        sorted(
            (*digests, _digest("extra-match-admission")), key=lambda item: item.value
        )
    )
    substituted = tuple(
        sorted(
            (*digests[1:], _digest("substituted-match-admission")),
            key=lambda item: item.value,
        )
    )
    admitted_poisons = tuple(
        _plan_admission_with(result, match_admission_digests=poison)
        for poison in (digests[1:], extra, substituted)
    )
    for poison in admitted_poisons:
        with pytest.raises(ContractViolation, match="match-admission closure"):
            _plan_result_with_admission(result, poison)
    with pytest.raises(ContractViolation, match="match-admission closure"):
        _create_planner_graph_plan_result(
            selection_resolution=result.selection_resolution,
            graph=result.graph,
            graph_plan_admission=admitted_poisons[0],
            graph_execution_binding=result.graph_execution_binding,
            timing_entries=result.timing_entries,
            counter_entries=result.counter_entries,
        )
    forged = object.__new__(WorkspaceSemanticMaterializationGraphPlanResult)
    for name in (
        "selection_resolution",
        "graph",
        "graph_execution_binding",
        "timing_entries",
        "counter_entries",
        "planning_result_digest",
    ):
        object.__setattr__(forged, name, getattr(result, name))
    object.__setattr__(forged, "graph_plan_admission", admitted_poisons[1])
    with pytest.raises(ContractViolation, match="match-admission closure"):
        encode_workspace_semantic_materialization_graph_plan_result(forged)
    with pytest.raises(ContractViolation, match="unique and digest ordered"):
        _plan_admission_with(
            result, match_admission_digests=(digests[0], digests[0], *digests[1:])
        )
    with pytest.raises(ContractViolation, match="unique and digest ordered"):
        _plan_admission_with(result, match_admission_digests=tuple(reversed(digests)))


@pytest.mark.asyncio
async def test_binding_code_catalog_substitution_fails_in_plan_context() -> None:
    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    admitted = result.graph_execution_binding.ordered_node_bindings[0]
    substituted_catalog = CodeSemanticContractCatalog.create(
        catalog_ref="code.substituted",
        catalog_generation=99,
        entries=(admitted.code_match.selected_binding,),
    )
    substituted = _node_binding_with(
        result,
        admitted,
        code_match_admission=CodeSemanticContractMatchAdmission.create(
            match=admitted.code_match,
            catalog=substituted_catalog,
        ),
    )
    poisoned_wire = canonical_json_bytes(substituted.to_wire())
    with pytest.raises(ContractViolation, match="plan context"):
        encode_workspace_semantic_materialization_node_execution_binding(
            substituted, plan_result=result
        )
    with pytest.raises(ContractViolation, match="plan context"):
        decode_workspace_semantic_materialization_node_execution_binding(
            poisoned_wire,
            plan_result=result,
            expected=substituted,
        )
    substituted_graph_binding = (
        WorkspaceSemanticMaterializationGraphExecutionBinding.create(
            graph=result.graph,
            ordered_node_bindings=(
                substituted,
                *result.graph_execution_binding.ordered_node_bindings[1:],
            ),
        )
    )
    with pytest.raises(ContractViolation, match="plan context"):
        encode_workspace_semantic_materialization_graph_execution_binding(
            substituted_graph_binding,
            plan_result=result,
        )
    with pytest.raises(ContractViolation, match="plan context"):
        decode_workspace_semantic_materialization_graph_execution_binding(
            canonical_json_bytes(substituted_graph_binding.to_wire()),
            plan_result=result,
            expected=substituted_graph_binding,
        )


@pytest.mark.asyncio
async def test_binding_workspace_catalog_substitution_fails_in_plan_context() -> None:
    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    admitted = result.graph_execution_binding.ordered_node_bindings[0]
    original = admitted.workspace_admitted_intent
    substituted = _node_binding_with(
        result,
        admitted,
        workspace_admitted_intent=WorkspaceAdmittedPackageIntent.create(
            package_ref=original.package_ref,
            code_intent_body=original.code_intent_body,
            catalog_root_digest=_digest("workspace-substituted"),
            catalog_generation=original.catalog_generation + 1,
            participation_policy_body=original.participation_policy_body,
        ),
    )
    poisoned_wire = canonical_json_bytes(substituted.to_wire())
    with pytest.raises(ContractViolation, match="plan context"):
        encode_workspace_semantic_materialization_node_execution_binding(
            substituted, plan_result=result
        )
    with pytest.raises(ContractViolation, match="plan context"):
        decode_workspace_semantic_materialization_node_execution_binding(
            poisoned_wire,
            plan_result=result,
            expected=substituted,
        )
    substituted_graph_binding = (
        WorkspaceSemanticMaterializationGraphExecutionBinding.create(
            graph=result.graph,
            ordered_node_bindings=(
                substituted,
                *result.graph_execution_binding.ordered_node_bindings[1:],
            ),
        )
    )
    with pytest.raises(ContractViolation, match="plan context"):
        encode_workspace_semantic_materialization_graph_execution_binding(
            substituted_graph_binding,
            plan_result=result,
        )
    with pytest.raises(ContractViolation, match="plan context"):
        decode_workspace_semantic_materialization_graph_execution_binding(
            canonical_json_bytes(substituted_graph_binding.to_wire()),
            plan_result=result,
            expected=substituted_graph_binding,
        )


@pytest.mark.asyncio
async def test_c1_b_portable_success_evidence_is_contextual_and_canonical() -> None:
    (
        plan,
        h1,
        _h2,
        product,
        target_result,
        consumer_result,
    ) = await _portable_execution_evidence()
    publication = target_result.publication_receipt
    assert publication is not None
    source = target_result.session_source_evidence
    event = target_result.session_event_reread_evidence.event
    event_reread = target_result.session_event_reread_evidence
    fanout = target_result.session_fanout_receipt
    assert (
        decode_workspace_semantic_materialization_request_v2(
            encode_workspace_semantic_materialization_request_v2(publication.request),
            expected=publication.request,
        )
        is publication.request
    )
    assert (
        decode_workspace_semantic_materialization_head_v2(
            encode_workspace_semantic_materialization_head_v2(publication.head),
            expected=publication.head,
        )
        is publication.head
    )
    assert (
        decode_workspace_semantic_materialization_publication_receipt_v2(
            encode_workspace_semantic_materialization_publication_receipt_v2(
                publication
            ),
            expected=publication,
        )
        is publication
    )
    assert (
        decode_workspace_materialization_session_source_evidence_v2(
            encode_workspace_materialization_session_source_evidence_v2(source),
            expected=source,
        )
        is source
    )
    assert (
        decode_workspace_materialization_session_append_request_v2(
            encode_workspace_materialization_session_append_request_v2(
                event.append_request
            ),
            expected=event.append_request,
        )
        is event.append_request
    )
    assert (
        decode_workspace_materialization_session_event_v2(
            encode_workspace_materialization_session_event_v2(event),
            expected=event,
        )
        is event
    )
    assert (
        decode_workspace_materialization_session_event_reread_evidence_v2(
            encode_workspace_materialization_session_event_reread_evidence_v2(
                event_reread
            ),
            expected=event_reread,
        )
        is event_reread
    )
    assert (
        decode_workspace_materialization_session_fanout_receipt_v2(
            encode_workspace_materialization_session_fanout_receipt_v2(fanout),
            expected=fanout,
        )
        is fanout
    )
    h1_wire = encode_workspace_semantic_materialization_head_reread_evidence_v2(h1)
    assert (
        decode_workspace_semantic_materialization_head_reread_evidence_v2(
            h1_wire, expected=h1
        )
        is h1
    )
    product_wire = encode_workspace_fulfilled_dependency_product_v2(
        product,
        plan_result=plan,
    )
    assert (
        decode_workspace_fulfilled_dependency_product_v2(
            product_wire,
            plan_result=plan,
            expected=product,
        )
        is product
    )
    node_wire = encode_workspace_semantic_materialization_node_result_evidence_v2(
        consumer_result, plan_result=plan
    )
    assert (
        decode_workspace_semantic_materialization_node_result_evidence_v2(
            node_wire, plan_result=plan, expected=consumer_result
        )
        is consumer_result
    )
    result = WorkspaceSemanticMaterializationGraphResultV3.create(
        plan_result=plan,
        status="succeeded",
        ordered_node_results=(target_result, consumer_result),
        terminal_failure=None,
        ordered_fulfilled_products=(product,),
        counter_entries=_result_counters(),
    )
    result_wire = encode_workspace_semantic_materialization_graph_result_v2(
        result, plan_result=plan
    )
    assert b'"terminal_failure":null' in result_wire
    assert (
        decode_workspace_semantic_materialization_graph_result_v2(
            result_wire, plan_result=plan, expected=result
        )
        is result
    )


@pytest.mark.asyncio
async def test_c1_b_terminal_failure_closes_prefix_products_and_effect_counters() -> (
    None
):
    (
        plan,
        _h1,
        _h2,
        product,
        target_result,
        consumer_result,
    ) = await _portable_execution_evidence()
    consumer = plan.graph_execution_binding.ordered_node_bindings[1]
    context = WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
        execution_input_closure_digest=(consumer_result.execution_input_closure_digest),
        package_head_reread_evidence=(consumer_result.package_head_reread_evidence),
    )
    terminal = WorkspaceSemanticMaterializationTerminalFailureV3.create(
        plan_result=plan,
        terminal_node_digest=consumer.node_digest,
        terminal_stage="reuse_validation",
        failure_code="reuse_not_current",
        ordered_completed_fulfilled_products=(product,),
        evidence_context=context,
    )
    terminal_wire = encode_workspace_semantic_materialization_terminal_failure_v2(
        terminal, plan_result=plan, evidence_context=context
    )
    assert (
        decode_workspace_semantic_materialization_terminal_failure_v2(
            terminal_wire,
            plan_result=plan,
            evidence_context=context,
            expected=terminal,
        )
        is terminal
    )
    entries = terminal.ordered_evidence_entries
    entry_wire = encode_workspace_semantic_materialization_failure_evidence_entry_v2(
        entries[0]
    )
    assert (
        decode_workspace_semantic_materialization_failure_evidence_entry_v2(
            entry_wire, expected=entries[0]
        )
        is entries[0]
    )
    failed = WorkspaceSemanticMaterializationGraphResultV3.create(
        plan_result=plan,
        status="failed",
        ordered_node_results=(target_result,),
        terminal_failure=terminal,
        ordered_fulfilled_products=(product,),
        counter_entries=_result_counters(
            reused_count=0,
            session_event_count=1,
        ),
    )
    assert encode_workspace_semantic_materialization_graph_result_v2(
        failed, plan_result=plan
    )


@pytest.mark.asyncio
async def test_c1_b_rejects_counter_optional_and_wire_type_poisons() -> None:
    (
        plan,
        h1,
        _h2,
        product,
        target_result,
        consumer_result,
    ) = await _portable_execution_evidence()
    with pytest.raises(ContractViolation, match="counters"):
        WorkspaceSemanticMaterializationGraphResultV3.create(
            plan_result=plan,
            status="succeeded",
            ordered_node_results=(target_result, consumer_result),
            terminal_failure=None,
            ordered_fulfilled_products=(product,),
            counter_entries=_result_counters(publication_count=2),
        )
    with pytest.raises(ContractViolation, match="reused node result"):
        WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
            plan_result=plan,
            node_digest=consumer_result.node_digest,
            outcome="reused",
            execution_input_closure_digest=consumer_result.execution_input_closure_digest,
            ordered_fulfilled_products=(product,),
            package_head_reread_evidence=consumer_result.package_head_reread_evidence,
            publication_receipt=target_result.publication_receipt,
            session_source_evidence=consumer_result.session_source_evidence,
            session_event_reread_evidence=(
                consumer_result.session_event_reread_evidence
            ),
            session_fanout_receipt=consumer_result.session_fanout_receipt,
        )
    forged_node = object.__new__(WorkspaceSemanticMaterializationNodeResultEvidenceV3)
    for (
        name
    ) in WorkspaceSemanticMaterializationNodeResultEvidenceV3.__dataclass_fields__:
        object.__setattr__(forged_node, name, getattr(consumer_result, name))
    object.__setattr__(
        forged_node,
        "session_event_reread_evidence_digest",
        _digest("arbitrary-session-event-digest"),
    )
    with pytest.raises(ContractViolation, match="positive package head"):
        encode_workspace_semantic_materialization_node_result_evidence_v2(
            forged_node, plan_result=plan
        )
    wire = encode_workspace_semantic_materialization_head_reread_evidence_v2(h1)
    poisoned = wire.replace(
        b'"materialization_head_revision":7', b'"materialization_head_revision":true'
    )
    assert poisoned != wire
    with pytest.raises(ContractViolation, match="canonical"):
        decode_workspace_semantic_materialization_head_reread_evidence_v2(
            poisoned, expected=h1
        )
    with pytest.raises(TypeError):
        WorkspaceSemanticMaterializationHeadRereadEvidenceV3.create(
            observation_role="dependency_h1",
            materialization_head_revision=7,
            head=h1.head,
            canonical_head_wire_digest=_digest("caller-supplied-head-wire"),  # type: ignore[call-arg]
        )
    forged_head = object.__new__(WorkspaceSemanticMaterializationHeadRereadEvidenceV3)
    for (
        name
    ) in WorkspaceSemanticMaterializationHeadRereadEvidenceV3.__dataclass_fields__:
        object.__setattr__(forged_head, name, getattr(h1, name))
    object.__setattr__(
        forged_head,
        "canonical_head_wire_digest",
        _digest("coherently-substituted-head-wire"),
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="exact publication head",
    ):
        encode_workspace_semantic_materialization_head_reread_evidence_v2(forged_head)
    omitted = wire.replace(
        b'"head":' + canonical_json_bytes(h1.head.to_wire()) + b",", b""
    )
    assert omitted != wire
    with pytest.raises(ContractViolation, match="canonical"):
        decode_workspace_semantic_materialization_head_reread_evidence_v2(
            omitted, expected=h1
        )
    with pytest.raises((ContractViolation, TypeError)):
        WorkspaceSemanticMaterializationGraphExecutionMetrics(
            binding_validation_ns=True,
            dependency_head_reread_ns=0,
            dependency_body_read_ns=0,
            execution_input_closure_ns=0,
            package_operation_ns=0,
            session_fanout_ns=0,
            total_ns=1,
            physical_dependency_head_read_count=0,
            physical_dependency_body_read_count=0,
            physical_package_head_read_count=0,
            physical_body_read_bytes=0,
            physical_body_write_count=0,
            physical_body_write_bytes=0,
            physical_cas_attempt_count=0,
            physical_retry_count=0,
            physical_session_event_write_count=0,
            physical_session_event_read_count=0,
        )


@pytest.mark.asyncio
async def test_c1_b_rejects_detached_head_and_fulfillment_closure_poisons() -> None:
    (
        plan,
        h1,
        h2,
        product,
        target_result,
        consumer_result,
    ) = await _portable_execution_evidence()
    target = plan.graph_execution_binding.ordered_node_bindings[0]
    moved_h2 = _head_reread(
        target,
        role="dependency_h2",
        coordinate=h2.result_coordinate,
        closure_key="target-closure",
        head_key="moved-target-head",
    )
    forged = object.__new__(WorkspaceFulfilledDependencyProductV3)
    for name in WorkspaceFulfilledDependencyProductV3.__dataclass_fields__:
        object.__setattr__(forged, name, getattr(product, name))
    object.__setattr__(forged, "head_h2_reread_evidence", moved_h2)
    with pytest.raises(
        ContractViolation, match="head (evidence pair|stability window)"
    ):
        encode_workspace_fulfilled_dependency_product_v2(
            forged,
            plan_result=plan,
        )

    for products in ((), (product, product)):
        with pytest.raises(ContractViolation, match="fulfillment closure"):
            WorkspaceSemanticMaterializationGraphResultV3.create(
                plan_result=plan,
                status="succeeded",
                ordered_node_results=(target_result, consumer_result),
                terminal_failure=None,
                ordered_fulfilled_products=products,
                counter_entries=_result_counters(
                    fulfilled_product_count=len(products),
                    dependency_body_observation_count=len(products),
                    dependency_head_observation_count=2 * len(products),
                ),
            )

    calls: list[str] = []

    class ForeignHead(WorkspaceSemanticMaterializationHeadRereadEvidenceV3):
        def __getattribute__(self, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    foreign = object.__new__(ForeignHead)
    with pytest.raises(TypeError, match="head_h1"):
        WorkspaceFulfilledDependencyProductV3.create(
            plan_result=plan,
            consumer_node_digest=product.consumer_node_digest,
            target_node_digest=product.target_node_digest,
            target_resolution=product.target_resolution,
            head_h1=foreign,
            head_h2=h2,
            consumed_body_coordinate=h1.result_coordinate,
        )
    assert calls == []


@pytest.mark.asyncio
async def test_c1_b_orders_products_by_exact_target_resolution_not_body_wire() -> None:
    planner, proposal, roots, *_ = _composition(two_dependencies=True)
    plan = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    *targets, consumer = plan.graph_execution_binding.ordered_node_bindings
    assert len(targets) == 2
    assert len(consumer.incoming_target_resolutions) == 2
    products: list[WorkspaceFulfilledDependencyProductV3] = []
    target_results: list[WorkspaceSemanticMaterializationNodeResultEvidenceV3] = []
    for index, resolution in enumerate(consumer.incoming_target_resolutions):
        edge = next(
            item
            for item in plan.graph.edges
            if item.consumer_node_digest == consumer.node_digest
            and item.target_resolution_digest == resolution.resolution_digest
        )
        target = next(
            item for item in targets if item.node_digest == edge.target_node_digest
        )
        coordinate = SemanticValueCoordinate(
            role=resolution.required_result_role,
            contract=resolution.result_product_contract,
            value_ref="cas:z-opposed" if index == 0 else "cas:a-opposed",
            digest=_digest(f"opposed-body:{index}"),
            size_bytes=32,
        )
        h1 = _head_reread(
            target,
            role="dependency_h1",
            coordinate=coordinate,
            closure_key=f"opposed-closure:{index}",
            head_key=f"opposed-head:{index}",
        )
        h2 = _head_reread(
            target,
            role="dependency_h2",
            coordinate=coordinate,
            closure_key=f"opposed-closure:{index}",
            head_key=f"opposed-head:{index}",
        )
        products.append(
            WorkspaceFulfilledDependencyProductV3.create(
                plan_result=plan,
                consumer_node_digest=consumer.node_digest,
                target_node_digest=target.node_digest,
                target_resolution=resolution,
                head_h1=h1,
                head_h2=h2,
                consumed_body_coordinate=coordinate,
            )
        )
        package_head = _head_reread(
            target,
            role="package_result",
            coordinate=coordinate,
            closure_key=f"target-result-closure:{index}",
            head_key=f"target-result-head:{index}",
        )
        publication = _publication_receipt(package_head)
        source, event, fanout = _session_evidence(
            key=f"opposed-target:{index}",
            disposition="executed",
            head=package_head,
            publication=publication,
        )
        target_results.append(
            WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
                plan_result=plan,
                node_digest=target.node_digest,
                outcome="executed",
                execution_input_closure_digest=(
                    package_head.execution_input_closure_digest
                ),
                ordered_fulfilled_products=(),
                package_head_reread_evidence=package_head,
                publication_receipt=publication,
                session_source_evidence=source,
                session_event_reread_evidence=event,
                session_fanout_receipt=fanout,
            )
        )
    assert canonical_json_bytes(products[0].to_wire()) > canonical_json_bytes(
        products[1].to_wire()
    )
    consumer_head = _head_reread(
        consumer,
        role="package_reuse",
        coordinate=_result_coordinate(consumer, "opposed-consumer"),
        closure_key="opposed-consumer-closure",
        head_key="opposed-consumer-head",
    )
    source, event, fanout = _session_evidence(
        key="opposed-consumer",
        disposition="reused",
        head=consumer_head,
        publication=None,
    )
    consumer_result = WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
        plan_result=plan,
        node_digest=consumer.node_digest,
        outcome="reused",
        execution_input_closure_digest=(consumer_head.execution_input_closure_digest),
        ordered_fulfilled_products=tuple(products),
        package_head_reread_evidence=consumer_head,
        publication_receipt=None,
        session_source_evidence=source,
        session_event_reread_evidence=event,
        session_fanout_receipt=fanout,
    )
    with pytest.raises(ContractViolation, match="plan context"):
        WorkspaceSemanticMaterializationNodeResultEvidenceV3.create(
            plan_result=plan,
            node_digest=consumer.node_digest,
            outcome="reused",
            execution_input_closure_digest=(
                consumer_head.execution_input_closure_digest
            ),
            ordered_fulfilled_products=tuple(reversed(products)),
            package_head_reread_evidence=consumer_head,
            publication_receipt=None,
            session_source_evidence=source,
            session_event_reread_evidence=event,
            session_fanout_receipt=fanout,
        )
    graph_result = WorkspaceSemanticMaterializationGraphResultV3.create(
        plan_result=plan,
        status="succeeded",
        ordered_node_results=(*target_results, consumer_result),
        terminal_failure=None,
        ordered_fulfilled_products=tuple(products),
        counter_entries=_result_counters(
            dependency_body_observation_count=2,
            dependency_head_observation_count=4,
            edge_count=2,
            executed_count=2,
            fulfilled_product_count=2,
            node_count=3,
            package_head_observation_count=3,
            publication_count=2,
            reused_count=1,
            session_event_count=3,
        ),
    )
    assert graph_result.ordered_fulfilled_products == tuple(products)
    with pytest.raises(ContractViolation, match="fulfillment closure"):
        WorkspaceSemanticMaterializationGraphResultV3.create(
            plan_result=plan,
            status="succeeded",
            ordered_node_results=(*target_results, consumer_result),
            terminal_failure=None,
            ordered_fulfilled_products=tuple(reversed(products)),
            counter_entries=graph_result.counter_entries,
        )


@pytest.mark.asyncio
async def test_c1_b_rejects_terminal_matrix_and_prefix_poisons() -> None:
    (
        plan,
        _h1,
        _h2,
        product,
        target_result,
        consumer_result,
    ) = await _portable_execution_evidence()
    consumer = plan.graph_execution_binding.ordered_node_bindings[1]
    context = WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
        execution_input_closure_digest=(consumer_result.execution_input_closure_digest),
        package_head_reread_evidence=(consumer_result.package_head_reread_evidence),
    )
    terminal = WorkspaceSemanticMaterializationTerminalFailureV3.create(
        plan_result=plan,
        terminal_node_digest=consumer.node_digest,
        terminal_stage="reuse_validation",
        failure_code="reuse_not_current",
        ordered_completed_fulfilled_products=(product,),
        evidence_context=context,
    )
    arbitrary_entry = WorkspaceSemanticMaterializationFailureEvidenceEntryV2.create(
        evidence_kind="package_reuse",
        evidence_digest=_digest("arbitrary-terminal-package-reuse"),
    )
    arbitrary_entries = tuple(
        arbitrary_entry if item.evidence_kind == "package_reuse" else item
        for item in terminal.ordered_evidence_entries
    )
    forged_arbitrary = object.__new__(WorkspaceSemanticMaterializationTerminalFailureV3)
    for name in WorkspaceSemanticMaterializationTerminalFailureV3.__dataclass_fields__:
        object.__setattr__(forged_arbitrary, name, getattr(terminal, name))
    object.__setattr__(forged_arbitrary, "ordered_evidence_entries", arbitrary_entries)
    with pytest.raises(ContractViolation, match="exact context"):
        encode_workspace_semantic_materialization_terminal_failure_v2(
            forged_arbitrary,
            plan_result=plan,
            evidence_context=context,
        )
    for entries in (
        terminal.ordered_evidence_entries[:1],
        (*terminal.ordered_evidence_entries, terminal.ordered_evidence_entries[0]),
    ):
        forged = object.__new__(WorkspaceSemanticMaterializationTerminalFailureV3)
        for (
            name
        ) in WorkspaceSemanticMaterializationTerminalFailureV3.__dataclass_fields__:
            object.__setattr__(forged, name, getattr(terminal, name))
        object.__setattr__(forged, "ordered_evidence_entries", entries)
        with pytest.raises(ContractViolation):
            encode_workspace_semantic_materialization_terminal_failure_v2(
                forged,
                plan_result=plan,
                evidence_context=context,
            )
    with pytest.raises(ContractViolation, match="terminal node is not next"):
        WorkspaceSemanticMaterializationGraphResultV3.create(
            plan_result=plan,
            status="failed",
            ordered_node_results=(),
            terminal_failure=terminal,
            ordered_fulfilled_products=(product,),
            counter_entries=_result_counters(
                executed_count=0,
                reused_count=0,
                package_head_observation_count=0,
                publication_count=0,
                session_event_count=0,
            ),
        )


@pytest.mark.asyncio
async def test_node_binding_preflight_invokes_no_foreign_nested_behavior() -> None:
    planner, proposal, roots, *_ = _composition()
    result = await planner.plan(
        selection_proposal=proposal, requested_root_code_plans=roots
    )
    admitted = result.graph_execution_binding.ordered_node_bindings[0]
    calls: list[str] = []

    class ForeignIntent(CodeSemanticMaterializationIntent):
        def __getattribute__(self, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    foreign = object.__new__(ForeignIntent)
    with pytest.raises(TypeError, match="code_intent"):
        WorkspaceSemanticMaterializationNodeExecutionBinding.create(
            graph=result.graph,
            node_digest=admitted.node_digest,
            package=admitted.package,
            package_entry=admitted.package_entry,
            code_intent=foreign,
            workspace_admitted_intent=admitted.workspace_admitted_intent,
            planning_context=admitted.planning_context,
            code_match=admitted.code_match,
            code_match_admission=admitted.code_match_admission,
            dependency_demand_set=admitted.dependency_demand_set,
            planning_input_digest=admitted.planning_input_digest,
            planning_demand_closure=admitted.planning_demand_closure,
            incoming_target_resolutions=admitted.incoming_target_resolutions,
            required_result_products=admitted.required_result_products,
        )
    assert calls == []
