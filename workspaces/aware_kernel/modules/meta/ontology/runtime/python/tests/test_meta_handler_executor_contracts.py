from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast, get_type_hints
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta.attribute.instance.value.builder import build_attribute_value_tree
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.config.stable_ids import stable_attribute_id
from aware_meta.primitive.config.builder import build_primitive_config
from aware_meta.runtime import (
    build_meta_graph_generated_handler_executor,
    build_meta_graph_generated_language_handler_registry,
    MetaGraphAppendReadyChangeAssembler,
    MetaGraphAppendReadyChanges,
    MetaGraphArgumentBinder,
    MetaGraphArgumentBinderPhase,
    MetaGraphArgumentBindingError,
    MetaGraphBoundArguments,
    MetaGraphCallTarget,
    MetaGraphCommitIndex,
    MetaGraphExecutionPlan,
    MetaGraphExecutionSessionDelta,
    MetaGraphExecutionSessionDeltaBuilder,
    MetaGraphExecutionSessionDeltaError,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphFunctionImplOwnership,
    MetaGraphAwareFunctionImplExecutionError,
    MetaGraphGeneratedLanguageHandlerImplementation,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphGeneratedLanguageHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerResolutionError,
    MetaGraphGeneratedLanguageHandlerResolver,
    MetaGraphGeneratedLanguageHandlerRunner,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphHandlerContext,
    MetaGraphHandlerDispatchResult,
    MetaGraphHandlerExecutionContext,
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphImplementationDispatcher,
    MetaGraphImplementationKind,
    MetaGraphImplementationPolicy,
    MetaGraphInstructionBodyFunctionImplRunner,
    MetaGraphInvocationLaneScope,
    MetaGraphLanguageHandlerExecution,
    MetaGraphLanguageHandlerExecutionError,
    MetaGraphLanguageHandlerImplementation,
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationBoundaryValidation,
    MetaGraphMutationBoundaryValidator,
    MetaGraphMutationRecorder,
    MetaGraphMutationSet,
    MetaGraphOigMaterializerPreStateProvider,
    MetaGraphPreState,
    MetaGraphPreStateMaterializer,
    MetaGraphPreStateMaterializerPhase,
    MetaGraphPreStateNotReadyError,
    MetaGraphPreStateProviderResult,
    MetaGraphResolvedFunctionTarget,
    MetaGraphRuntimeIndex,
    MetaGraphRuntimeIndexView,
    MetaGraphSessionDeltaLanguageHandlerRunner,
    MetaGraphStagedFunctionCall,
    build_meta_graph_bound_arguments,
    current_meta_graph_handler_execution_context,
    decode_oig_attribute_value,
    build_meta_graph_pre_state,
    build_meta_graph_pre_state_index,
    build_meta_graph_execution_plan,
    build_meta_graph_implementation_policy_from_packages,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.invocation import invoke_instance
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_meta.runtime import oigi_generated_handlers
from aware_meta.runtime.handler_executor import (
    build_meta_graph_append_ready_changes,
    build_meta_graph_mutation_boundary_validation,
    build_meta_graph_mutation_set,
    build_meta_graph_mutation_set_from_session_delta,
    MetaGraphAwareFunctionImplRunner,
    MetaGraphAppendReadyAssemblyError,
    MetaGraphAppendReadyChangeAssemblerPhase,
    MetaGraphHandlerExecutionNotReadyError,
    MetaGraphImplementationDispatchError,
    MetaGraphImplementationDispatchNotReadyError,
    MetaGraphImplementationDispatcherPhase,
    MetaGraphLanguageHandlerRunner,
    MetaGraphMutateSelfOnlyPolicy,
    MetaGraphMutationBoundaryError,
    MetaGraphMutationBoundaryNotReadyError,
    MetaGraphMutationBoundaryPolicy,
    MetaGraphMutationBoundaryValidatorPhase,
    MetaGraphMutationRecorderPhase,
    MetaGraphMutationRecordingError,
    MetaGraphMutationRecordingNotReadyError,
    MetaGraphMutationSource,
    MetaGraphPhaseHandlerExecutor,
    MetaGraphSessionDeltaMutationSource,
)
from aware_meta.runtime.invocation_engine import MetaGraphInvokeFunctionInput
from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphCommitInvocationBackend,
)
from aware_meta.runtime.handler_executor.function_impl_runner import (
    _filter_nested_session_delta_to_target_scope,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_enum_config,
    test_enum_fqn,
)
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_delete import (
    FunctionImplInstructionDelete,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplDeleteTargetKind,
    FunctionImplInvokeKind,
    FunctionImplInstructionType,
    FunctionImplRequireKind,
    FunctionImplValueSourceReadPathRootKind,
    FunctionImplValueSourceKind,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)
from aware_meta_ontology.function.function_impl_instruction_let import (
    FunctionImplInstructionLet,
)
from aware_meta_ontology.function.function_impl_instruction_require import (
    FunctionImplInstructionRequire,
)
from aware_meta_ontology.function.function_impl_instruction_require_operand import (
    FunctionImplInstructionRequireOperand,
)
from aware_meta_ontology.function.function_impl_instruction_set import (
    FunctionImplInstructionSet,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
    FunctionImplValueSourceLiteralPrimitive,
)
from aware_meta_ontology.function.function_impl_value_source_read_path import (
    FunctionImplValueSourceReadPath,
)
from aware_meta_ontology.function.function_impl_value_source_read_path_segment import (
    FunctionImplValueSourceReadPathSegment,
)
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_identity_id,
)


@pytest.fixture(autouse=True)
def _restore_orm_registry_after_test():
    snapshot = ORMModelRegistry.snapshot_state()
    try:
        yield
    finally:
        ORMModelRegistry.restore_state(snapshot)


def _meta_graph_commit_index(
    *,
    function_config: FunctionConfig,
    class_name: str = "Thread",
    is_constructor: bool = False,
) -> SimpleNamespace:
    opg_id = uuid4()
    projection_hash = "sha256:test:domain"
    opg = SimpleNamespace(id=opg_id, projection_hash=projection_hash)
    opg.object_projection_graph_edges = ()
    opg.object_projection_graph_nodes = ()
    class_config_id = uuid4()
    class_config = SimpleNamespace(
        id=class_config_id,
        name=class_name,
        class_fqn=f"aware.tests.{class_name}",
        class_config_function_configs=[
            SimpleNamespace(
                function_config_id=function_config.id,
                function_config=function_config,
                is_constructor=is_constructor,
            )
        ],
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            fqn_prefix="aware.tests",
            name="Aware Tests",
            object_config_graph_identity=None,
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ],
        ),
        class_configs_by_id={class_config_id: class_config},
        opg_by_id={opg_id: opg},
        opg_by_hash={projection_hash: opg},
        attribute_configs_by_id={},
        relationships_by_id={},
        portal_index=SimpleNamespace(),
    )


def test_meta_graph_invoke_input_uses_meta_runtime_index_contract() -> None:
    hints = get_type_hints(MetaGraphInvokeFunctionInput)

    assert hints["index"] is MetaGraphRuntimeIndex


def test_meta_graph_commit_index_accepts_lightweight_direct_field_source() -> None:
    index = _meta_graph_commit_index(
        function_config=FunctionConfig(
            id=uuid4(),
            owner_key="aware.tests",
            name="attach_lane",
        )
    )

    assert isinstance(index, MetaGraphCommitIndex)
    assert isinstance(index, MetaGraphRuntimeIndex)


def test_meta_runtime_index_view_caches_function_targets_by_source_identity() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="attach_lane",
    )
    index = _meta_graph_commit_index(function_config=function_config)
    index_view = MetaGraphRuntimeIndexView(index=cast(MetaGraphCommitIndex, index))

    first_targets = index_view.function_targets_by_id
    index.ocg.object_config_graph_nodes.append(
        SimpleNamespace(
            type=ObjectConfigGraphNodeType.function,
            function_config=FunctionConfig(
                id=uuid4(),
                owner_key="aware.tests",
                name="late_addition",
            ),
        )
    )
    second_targets = index_view.function_targets_by_id

    assert second_targets is first_targets
    assert tuple(second_targets) == (function_config.id,)
    assert second_targets[function_config.id].operation_label == "Thread.attach_lane"


def test_meta_runtime_index_view_resolves_language_handler_descriptor() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="attach_lane",
    )
    index = _meta_graph_commit_index(function_config=function_config)
    index_view = MetaGraphRuntimeIndexView(index=cast(MetaGraphCommitIndex, index))

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.language_handler
    assert descriptor.function_config is function_config
    assert descriptor.owner_class_config is next(
        iter(index.class_configs_by_id.values())
    )
    assert (
        descriptor.class_function_edge
        is descriptor.owner_class_config.class_config_function_configs[0]
    )
    assert descriptor.is_constructor is False


def test_meta_runtime_index_view_defaults_function_impl_to_language_handler() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="build",
        function_impl=FunctionImpl(
            key="aware.tests.build",
            kind=FunctionImplKind.instruction_body,
        ),
    )
    index = _meta_graph_commit_index(function_config=function_config)
    index_view = MetaGraphRuntimeIndexView(index=cast(MetaGraphCommitIndex, index))

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.language_handler
    assert descriptor.function_config is function_config


def test_meta_runtime_index_view_routes_compiler_owned_instruction_body_to_function_impl() -> (
    None
):
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="build",
        function_impl=_executable_instruction_body_impl("aware.tests.build"),
    )
    index = _meta_graph_commit_index(function_config=function_config)
    index_view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, index),
        implementation_policy=MetaGraphImplementationPolicy(
            function_impl_ownership_by_owner_key={
                "aware.tests": MetaGraphFunctionImplOwnership.compiler,
            },
        ),
    )

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.aware_function_impl
    assert descriptor.function_config is function_config


def test_meta_runtime_index_view_routes_auto_constructor_to_language_handler() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="build",
        function_impl=FunctionImpl(
            key="aware.tests.build",
            kind=FunctionImplKind.auto_constructor,
        ),
    )
    index = _meta_graph_commit_index(
        function_config=function_config,
        is_constructor=True,
    )
    index_view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, index),
        implementation_policy=MetaGraphImplementationPolicy(
            function_impl_ownership_by_owner_key={
                "aware.tests": MetaGraphFunctionImplOwnership.compiler,
            },
        ),
    )

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.language_handler
    assert descriptor.function_config is function_config
    assert descriptor.is_constructor is True


def test_meta_graph_implementation_policy_uses_package_fqn_prefix() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests.Thread",
        name="build",
        function_impl=_executable_instruction_body_impl("aware.tests.Thread.build"),
    )
    index = _meta_graph_commit_index(function_config=function_config)
    package = ObjectConfigGraphPackage(
        id=uuid4(),
        package_name="tests-ontology",
        fqn_prefix="aware.tests",
        function_impl_ownership=ObjectConfigGraphPackageFunctionImplOwnership.compiler,
    )
    index_view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, index),
        implementation_policy=build_meta_graph_implementation_policy_from_packages(
            (package,),
        ),
    )

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.aware_function_impl


def test_meta_graph_implementation_policy_defaults_package_to_authored() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests.Thread",
        name="build",
        function_impl=FunctionImpl(
            key="aware.tests.Thread.build",
            kind=FunctionImplKind.instruction_body,
        ),
    )
    index = _meta_graph_commit_index(function_config=function_config)
    package = ObjectConfigGraphPackage(
        id=uuid4(),
        package_name="tests-ontology",
        fqn_prefix="aware.tests",
    )
    index_view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, index),
        implementation_policy=build_meta_graph_implementation_policy_from_packages(
            (package,),
        ),
    )

    descriptor = index_view.resolve_implementation_descriptor(function_config.id)

    assert descriptor.kind is MetaGraphImplementationKind.language_handler


def test_meta_graph_execution_plan_uses_cached_descriptor_and_projection() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="attach_lane",
    )
    index = _meta_graph_commit_index(function_config=function_config)
    projection_hash = next(iter(index.opg_by_hash.keys()))
    target_object_id = uuid4()
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_config.id,
        domain_branch_id=uuid4(),
        domain_projection_hash=projection_hash,
        call_target=MetaGraphCallTarget.instance,
        target_object_id=target_object_id,
        expected_graph_hash_pre="sha256:test:pre",
        expected_head_commit_id=uuid4(),
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(request)
    index_view = MetaGraphRuntimeIndexView(index=cast(MetaGraphCommitIndex, index))

    plan = build_meta_graph_execution_plan(
        index=cast(MetaGraphRuntimeIndex, index),
        request=request,
        staged_call=staged_call,
        index_view=index_view,
    )

    assert plan.index is index
    assert plan.staged_call is staged_call
    assert plan.implementation is index_view.resolve_implementation_descriptor(
        function_config.id
    )
    assert plan.object_projection_graph is index.opg_by_hash[projection_hash]
    assert plan.target_object_id == target_object_id
    assert plan.expected_graph_hash_pre == "sha256:test:pre"
    assert plan.expected_head_commit_id == request.expected_head_commit_id


def test_meta_handler_execution_phase_protocols_are_explicitly_typed() -> None:
    dispatch_result_fields = get_type_hints(MetaGraphHandlerDispatchResult)
    materializer_hints = get_type_hints(
        MetaGraphPreStateMaterializer.materialize_pre_state
    )
    binder_hints = get_type_hints(MetaGraphArgumentBinder.bind_arguments)
    dispatcher_hints = get_type_hints(
        MetaGraphImplementationDispatcher.dispatch_implementation
    )
    aware_runner_hints = get_type_hints(
        MetaGraphAwareFunctionImplRunner.run_function_impl
    )
    handler_runner_hints = get_type_hints(
        MetaGraphLanguageHandlerRunner.run_language_handler
    )
    handler_impl_hints = get_type_hints(
        MetaGraphLanguageHandlerImplementation.execute_language_handler
    )
    generated_resolver_hints = get_type_hints(
        MetaGraphGeneratedLanguageHandlerResolver.resolve_generated_language_handler
    )
    recorder_hints = get_type_hints(MetaGraphMutationRecorder.record_mutations)
    source_hints = get_type_hints(MetaGraphMutationSource.collect_mutations)
    validator_hints = get_type_hints(
        MetaGraphMutationBoundaryValidator.validate_mutations
    )
    policy_hints = get_type_hints(
        MetaGraphMutationBoundaryPolicy.validate_mutation_boundary
    )
    assembler_hints = get_type_hints(
        MetaGraphAppendReadyChangeAssembler.assemble_append_ready_changes
    )

    assert (
        dispatch_result_fields["session_delta"] == MetaGraphExecutionSessionDelta | None
    )
    assert materializer_hints["request"] is MetaGraphHandlerExecutionRequest
    assert materializer_hints["return"] is MetaGraphPreState
    assert binder_hints["pre_state"] is MetaGraphPreState
    assert binder_hints["return"] is MetaGraphBoundArguments
    assert dispatcher_hints["bound_arguments"] is MetaGraphBoundArguments
    assert dispatcher_hints["return"] is MetaGraphHandlerDispatchResult
    assert aware_runner_hints["bound_arguments"] is MetaGraphBoundArguments
    assert aware_runner_hints["return"] is MetaGraphHandlerDispatchResult
    assert handler_runner_hints["bound_arguments"] is MetaGraphBoundArguments
    assert handler_runner_hints["return"] is MetaGraphHandlerDispatchResult
    assert handler_impl_hints["bound_arguments"] is MetaGraphBoundArguments
    assert handler_impl_hints["return"] is MetaGraphLanguageHandlerExecution
    assert (
        generated_resolver_hints["descriptor"]
        is MetaGraphFunctionImplementationDescriptor
    )
    assert recorder_hints["dispatch_result"] is MetaGraphHandlerDispatchResult
    assert recorder_hints["return"] is MetaGraphMutationSet
    assert source_hints["dispatch_result"] is MetaGraphHandlerDispatchResult
    assert source_hints["return"] is MetaGraphMutationSet
    assert validator_hints["mutation_set"] is MetaGraphMutationSet
    assert validator_hints["return"] is MetaGraphMutationBoundaryValidation
    assert policy_hints["mutation_set"] is MetaGraphMutationSet
    assert policy_hints["return"] is MetaGraphMutationBoundaryValidation
    assert assembler_hints["boundary_validation"] is MetaGraphMutationBoundaryValidation
    assert assembler_hints["return"] is MetaGraphAppendReadyChanges


def test_meta_handler_execution_phase_contracts_flow_to_append_ready_changes() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="mutate",
    )
    index = _meta_graph_commit_index(function_config=function_config)
    projection_hash = next(iter(index.opg_by_hash.keys()))
    target_object_id = uuid4()
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_config.id,
        domain_branch_id=uuid4(),
        domain_projection_hash=projection_hash,
        call_target=MetaGraphCallTarget.instance,
        target_object_id=target_object_id,
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(request)
    plan = backend.build_execution_plan(request=request, staged_call=staged_call)
    before_oig = ObjectInstanceGraph.model_construct(
        id=staged_call.lane_scope.object_instance_graph_id
    )

    pre_state = MetaGraphPreState(
        execution_plan=plan,
        before_oig=before_oig,
        graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=plan,
        positional=JsonArray(["left"]),
        keyword=JsonObject({"right": True}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=3,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=plan,
        before_oig=pre_state.before_oig,
        changes=(),
        graph_hash_pre=pre_state.graph_hash_pre,
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
    )
    boundary_validation = MetaGraphMutationBoundaryValidation(
        execution_plan=plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )
    append_ready = MetaGraphAppendReadyChanges(
        execution_plan=plan,
        before_oig=mutation_set.before_oig,
        changes=mutation_set.changes,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
    )
    execution_result = MetaGraphHandlerExecutionResult(
        success=dispatch_result.success,
        payload=dispatch_result.payload,
        execution_time_ms=dispatch_result.execution_time_ms,
        append_ready_changes=append_ready,
    )

    assert bound_arguments.positional == JsonArray(["left"])
    assert bound_arguments.keyword == JsonObject({"right": True})
    assert boundary_validation.status is MetaGraphMutationBoundaryStatus.accepted
    assert execution_result.append_ready_changes is append_ready


@pytest.mark.asyncio
async def test_meta_pre_state_materializer_phase_reads_provider_and_validates_plan() -> (
    None
):
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="mutate",
    )
    index = _meta_graph_commit_index(function_config=function_config)
    projection_hash = next(iter(index.opg_by_hash.keys()))
    target_object_id = uuid4()
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_config.id,
        domain_branch_id=uuid4(),
        domain_projection_hash=projection_hash,
        call_target=MetaGraphCallTarget.instance,
        target_object_id=target_object_id,
        expected_graph_hash_pre="sha256:test:pre",
        expected_head_commit_id=uuid4(),
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(request)
    execution_plan = backend.build_execution_plan(
        request=request,
        staged_call=staged_call,
    )
    handler_request = MetaGraphHandlerExecutionRequest(
        request=request,
        staged_call=staged_call,
        execution_plan=execution_plan,
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=staged_call.lane_scope.object_instance_graph_id,
        hash="sha256:test:pre",
    )
    root_object_id = uuid4()
    root_class_instance_identity_id = uuid4()
    provider = _RecordingPreStateProvider(
        result=MetaGraphPreStateProviderResult(
            before_oig=before_oig,
            graph_hash_pre="sha256:test:pre",
            head_commit_id=request.expected_head_commit_id,
            root_object_id=root_object_id,
            root_class_instance_identity_id=root_class_instance_identity_id,
        )
    )
    phase = MetaGraphPreStateMaterializerPhase(provider=provider)

    pre_state = await phase.materialize_pre_state(handler_request)

    assert provider.requests == [handler_request]
    assert pre_state.execution_plan is execution_plan
    assert pre_state.before_oig is before_oig
    assert pre_state.graph_hash_pre == "sha256:test:pre"
    assert pre_state.target_object_id == target_object_id
    assert pre_state.root_object_id == root_object_id
    assert pre_state.root_class_instance_identity_id == root_class_instance_identity_id


def test_meta_pre_state_builder_rejects_hash_mismatch() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:expected",
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        hash="sha256:test:actual",
    )

    with pytest.raises(MetaGraphPreStateNotReadyError, match="graph hash mismatch"):
        build_meta_graph_pre_state(
            request=handler_request,
            snapshot=MetaGraphPreStateProviderResult(before_oig=before_oig),
        )


@pytest.mark.asyncio
async def test_meta_oig_materializer_pre_state_provider_uses_execution_plan() -> None:
    expected_head_commit_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        expected_head_commit_id=expected_head_commit_id,
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        hash="sha256:test:pre",
    )
    materializer = _RecordingOigMaterializer(before_oig=before_oig)
    provider = MetaGraphOigMaterializerPreStateProvider(materializer=materializer)

    snapshot = await provider.read_pre_state(handler_request)

    call = materializer.calls[0]
    plan = handler_request.execution_plan
    lane_scope = handler_request.staged_call.lane_scope
    assert snapshot.before_oig is before_oig
    assert snapshot.graph_hash_pre == "sha256:test:pre"
    assert snapshot.head_commit_id == expected_head_commit_id
    assert call.branch_id == lane_scope.domain_branch_id
    assert call.ocg is plan.index.ocg
    assert call.opg is plan.object_projection_graph
    assert call.commit_id == expected_head_commit_id
    assert call.oig_id == lane_scope.object_instance_graph_id
    assert call.attribute_configs_by_id is plan.index.attribute_configs_by_id
    assert call.class_configs_by_id is plan.index.class_configs_by_id


@pytest.mark.asyncio
async def test_meta_argument_binder_phase_copies_json_args_and_kwargs() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        args=JsonArray([1, JsonObject({"nested": JsonArray([True, None])})]),
        kwargs=JsonObject({"flag": True, "label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    phase = MetaGraphArgumentBinderPhase()

    bound = await phase.bind_arguments(handler_request, pre_state)

    assert bound.execution_plan is handler_request.execution_plan
    assert bound.positional == JsonArray(
        [1, JsonObject({"nested": JsonArray([True, None])})]
    )
    assert bound.keyword == JsonObject({"flag": True, "label": "ok"})
    assert bound.positional is not handler_request.request.args
    assert bound.keyword is not handler_request.request.kwargs


def test_meta_argument_binder_rejects_non_json_value() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        args=cast(JsonArray, [uuid4()]),
    )

    with pytest.raises(MetaGraphArgumentBindingError, match="non-JSON value"):
        build_meta_graph_bound_arguments(
            request=handler_request,
            pre_state=_meta_pre_state(handler_request),
        )


def test_meta_argument_binder_rejects_pre_state_from_different_plan() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )

    with pytest.raises(MetaGraphArgumentBindingError, match="same execution plan"):
        build_meta_graph_bound_arguments(
            request=handler_request,
            pre_state=_meta_pre_state(other_handler_request),
        )


@pytest.mark.asyncio
async def test_meta_implementation_dispatcher_routes_function_impl_runner() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        function_impl=_executable_instruction_body_impl("aware.tests.mutate"),
        implementation_policy=_compiler_owned_policy(),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"rail": "function_impl"}),
        execution_time_ms=5,
    )
    runner = _RecordingAwareFunctionImplRunner(result=dispatch_result)
    phase = MetaGraphImplementationDispatcherPhase(
        aware_function_impl_runner=runner,
    )

    result = await phase.dispatch_implementation(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert result is dispatch_result
    assert runner.calls == [(handler_request, pre_state, bound_arguments)]


@pytest.mark.asyncio
async def test_meta_implementation_dispatcher_routes_language_handler_runner() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"rail": "language_handler"}),
        execution_time_ms=6,
    )
    runner = _RecordingLanguageHandlerRunner(result=dispatch_result)
    phase = MetaGraphImplementationDispatcherPhase(language_handler_runner=runner)

    result = await phase.dispatch_implementation(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert result is dispatch_result
    assert runner.calls == [(handler_request, pre_state, bound_arguments)]


@pytest.mark.asyncio
async def test_meta_dispatcher_fails_closed_without_function_impl_runner() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        function_impl=_executable_instruction_body_impl("aware.tests.mutate"),
        implementation_policy=_compiler_owned_policy(),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    phase = MetaGraphImplementationDispatcherPhase()

    with pytest.raises(
        MetaGraphImplementationDispatchNotReadyError,
        match="Aware FunctionImpl runner",
    ) as exc_info:
        await phase.dispatch_implementation(
            handler_request,
            pre_state,
            bound_arguments,
        )

    message = str(exc_info.value)
    assert "function_impl_key=aware.tests.mutate" in message
    assert "function_impl_kind=instruction_body" in message


@pytest.mark.asyncio
async def test_meta_dispatcher_fails_closed_without_handler_runner() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    phase = MetaGraphImplementationDispatcherPhase()

    with pytest.raises(
        MetaGraphImplementationDispatchNotReadyError,
        match="language handler runner",
    ) as exc_info:
        await phase.dispatch_implementation(
            handler_request,
            pre_state,
            bound_arguments,
        )

    message = str(exc_info.value)
    assert "owner_key=aware.tests" in message
    assert "function_name=mutate" in message
    assert "owner_class_name=Thread" in message


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_sets_self_attribute_from_let_input() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    function_impl.instructions = [
        FunctionImplInstruction(
            id=uuid4(),
            function_impl_id=function_impl.id or uuid4(),
            type=FunctionImplInstructionType.let,
            sequence=0,
        )
    ]
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"label": "after"}),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="label",
    )
    function_impl.instructions = fixture.instructions
    pre_state = fixture.pre_state

    runner = MetaGraphInstructionBodyFunctionImplRunner()
    result = await runner.run_function_impl(
        handler_request,
        pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject({"label": "after"}),
        ),
    )

    assert result.success is True
    assert result.payload == JsonObject({"rail": "aware_function_impl"})
    assert result.session_delta is not None
    assert result.session_delta.graph_hash_pre == pre_state.graph_hash_pre
    assert result.session_delta.graph_hash_post != pre_state.graph_hash_pre
    assert result.session_delta.changes
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    assert class_change.class_instance_id == target_object_id
    attr_change = class_change.attribute_changes[0]
    assert attr_change.attribute_id == fixture.attribute_id
    assert attr_change.value_root_change is not None


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_reads_defaulted_input_value_source() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="label",
        input_default_value='"after-default"',
    )
    function_impl.instructions = fixture.instructions

    result = await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
        handler_request,
        fixture.pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject(),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    attr_change = class_change.attribute_changes[0]
    assert attr_change.attribute_id == fixture.attribute_id
    assert attr_change.value_root_change is not None
    value_delta = attr_change.value_root_change.change.change_deltas[0]
    assert value_delta.payload == {"value": "after-default"}


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_sets_self_attribute_from_read_path() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.apply_patch",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"patch": {"text_after": "after"}}),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="patch",
    )
    input_source = fixture.instructions[0].value_sources[0]
    function_input = input_source.source_function_config_attribute_config
    assert function_input is not None
    target_set_payload = fixture.instructions[-1].instruction_set
    assert target_set_payload is not None
    target_edge = target_set_payload.target_class_config_attribute_config
    assert target_edge is not None
    target_attr_cfg = target_edge.attribute_config
    assert target_attr_cfg is not None

    segment_attr_cfg = make_attribute_config(
        owner_key="aware.tests.Patch",
        name="text_after",
        type_descriptor=target_attr_cfg.type_descriptor,
        type_descriptor_id=target_attr_cfg.type_descriptor_id,
    )
    handler_request.execution_plan.index.attribute_configs_by_id[
        segment_attr_cfg.id
    ] = segment_attr_cfg

    set_instruction_id = uuid4()
    read_path_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        key="patch.text_after",
        kind=FunctionImplValueSourceKind.read_path,
    )
    read_path_id = uuid4()
    read_path = FunctionImplValueSourceReadPath(
        id=read_path_id,
        function_impl_value_source_id=read_path_source.id,
        root_kind=FunctionImplValueSourceReadPathRootKind.function_input,
        root_function_config_attribute_config=function_input,
        root_function_config_attribute_config_id=function_input.id,
        segments=[
            FunctionImplValueSourceReadPathSegment(
                id=uuid4(),
                function_impl_value_source_read_path_id=read_path_id,
                position=0,
                attribute_config=segment_attr_cfg,
                attribute_config_id=segment_attr_cfg.id,
            )
        ],
    )
    read_path_source.source_read_path = read_path
    set_payload = FunctionImplInstructionSet(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        target_class_config_attribute_config=target_edge,
        target_class_config_attribute_config_id=target_edge.id,
        value_source=read_path_source,
        value_source_id=read_path_source.id,
    )
    set_instruction = FunctionImplInstruction(
        id=set_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.set,
        sequence=0,
        instruction_set=set_payload,
        value_sources=[read_path_source],
    )
    function_impl.instructions = [set_instruction]

    result = await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
        handler_request,
        fixture.pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject({"patch": {"text_after": "after"}}),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    changed_instance_ids = {
        class_change.class_instance_id
        for graph_change in result.session_delta.changes
        for class_change in graph_change.class_instance_changes
    }
    assert changed_instance_ids == {target_object_id}
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    attr_change = class_change.attribute_changes[0]
    assert attr_change.attribute_id == fixture.attribute_id
    assert attr_change.value_root_change is not None


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_deletes_self_owned_closure() -> None:
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.delete_self",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_delete_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        include_descendant=True,
    )
    function_impl.instructions = fixture.instructions

    result = await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
        handler_request,
        fixture.pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject(),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    deleted_instance_ids = {
        class_change.class_instance_id
        for graph_change in result.session_delta.changes
        for class_change in graph_change.class_instance_changes
        if class_change.change.type == ChangeType.delete
    }
    assert deleted_instance_ids == {
        fixture.target_class_instance_id,
        fixture.descendant_class_instance_id,
    }
    deleted_relationship_sources = {
        relationship_change.source_class_instance_id
        for graph_change in result.session_delta.changes
        for relationship_change in graph_change.class_instance_relationship_changes
        if relationship_change.change.type == ChangeType.delete
    }
    assert deleted_relationship_sources == {fixture.target_class_instance_id}

    mutation_set = build_meta_graph_mutation_set_from_session_delta(
        request=handler_request,
        pre_state=fixture.pre_state,
        dispatch_result=result,
        session_delta=result.session_delta,
    )
    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )
    assert validation.status is MetaGraphMutationBoundaryStatus.accepted


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_rejects_delete_self_on_root() -> None:
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.delete_self",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_delete_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        target_is_root=True,
    )
    function_impl.instructions = fixture.instructions

    with pytest.raises(
        MetaGraphAwareFunctionImplExecutionError,
        match="cannot delete the OIG root",
    ):
        await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
            handler_request,
            fixture.pre_state,
            MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(),
            ),
        )


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_rejects_delete_self_with_external_incoming() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.delete_self",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_delete_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        external_incoming=True,
    )
    function_impl.instructions = fixture.instructions

    with pytest.raises(
        MetaGraphAwareFunctionImplExecutionError,
        match="incoming relationship from outside the self-owned delete closure",
    ):
        await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
            handler_request,
            fixture.pre_state,
            MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(),
            ),
        )


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_creates_missing_self_attribute_from_set() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"label": "after"}),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="label",
    )
    function_impl.instructions = fixture.instructions
    before_oig = fixture.pre_state.before_oig
    target_instance = before_oig.class_instances[0]
    target_instance.class_instance_attributes = []
    before_hash = compute_hash(before_oig, index=build_index(before_oig))
    before_oig.hash = before_hash
    pre_state = MetaGraphPreState(
        execution_plan=fixture.pre_state.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=before_hash,
        target_object_id=fixture.pre_state.target_object_id,
        root_object_id=fixture.pre_state.root_object_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )

    runner = MetaGraphInstructionBodyFunctionImplRunner()
    result = await runner.run_function_impl(
        handler_request,
        pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject({"label": "after"}),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    assert result.session_delta.graph_hash_pre == pre_state.graph_hash_pre
    assert result.session_delta.graph_hash_post != pre_state.graph_hash_pre
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    attr_change = class_change.attribute_changes[0]
    set_payload = fixture.instructions[-1].instruction_set
    assert set_payload is not None
    target_edge = set_payload.target_class_config_attribute_config
    assert target_edge is not None
    assert target_edge.attribute_config_id is not None
    assert attr_change.attribute_id == stable_attribute_id(
        owner_key=target_object_id,
        attribute_config_id=target_edge.attribute_config_id,
    )
    assert attr_change.value_root_change is not None


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_sets_self_enum_attribute_from_literal() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.block",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_enum_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="active",
        target_value="blocked",
    )
    function_impl.instructions = fixture.instructions

    runner = MetaGraphInstructionBodyFunctionImplRunner()
    result = await runner.run_function_impl(
        handler_request,
        fixture.pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject(),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    attr_change = class_change.attribute_changes[0]
    assert attr_change.attribute_id == fixture.attribute_id
    assert attr_change.value_root_change is not None
    enum_delta = next(
        delta
        for delta in attr_change.value_root_change.change.change_deltas
        if delta.property == "enum_option_id"
    )
    assert enum_delta.payload == {"value": str(fixture.target_enum_option_id)}


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_allows_self_enum_lifecycle_guard() -> None:
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.activate",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_enum_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="parked",
        target_value="active",
        allowed_values=["proposed", "parked", "blocked"],
    )
    function_impl.instructions = fixture.instructions

    runner = MetaGraphInstructionBodyFunctionImplRunner()
    result = await runner.run_function_impl(
        handler_request,
        fixture.pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject(),
        ),
    )

    assert result.success is True
    assert result.session_delta is not None
    class_change = result.session_delta.changes[0].class_instance_changes[0]
    attr_change = class_change.attribute_changes[0]
    assert attr_change.attribute_id == fixture.attribute_id
    assert attr_change.value_root_change is not None
    enum_delta = next(
        delta
        for delta in attr_change.value_root_change.change.change_deltas
        if delta.property == "enum_option_id"
    )
    assert enum_delta.payload == {"value": str(fixture.target_enum_option_id)}


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_rejects_self_enum_lifecycle_guard() -> None:
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.activate",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
    )
    fixture = _function_impl_self_enum_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="achieved",
        target_value="active",
        allowed_values=["proposed", "parked", "blocked"],
    )
    function_impl.instructions = fixture.instructions

    runner = MetaGraphInstructionBodyFunctionImplRunner()
    with pytest.raises(
        MetaGraphAwareFunctionImplExecutionError,
        match="status must be proposed, parked, or blocked",
    ):
        await runner.run_function_impl(
            handler_request,
            fixture.pre_state,
            MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(),
            ),
        )


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_executes_call_invoke_and_captures_return() -> (
    None
):
    parent_object_id = uuid4()
    child_object_id = uuid4()
    parent_impl = FunctionImpl(
        key="aware.tests.Parent.run",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=parent_impl,
        target_object_id=parent_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"label": "from-parent"}),
    )
    parent_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )
    parent_config = handler_request.execution_plan.index.class_configs_by_id[
        parent_config_id
    ]
    child_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware.tests.Child",
        name="Child",
    )
    child_function = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests.Child",
        name="emit",
    )
    child_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            id=uuid4(),
            class_config_id=child_config.id,
            function_config_id=child_function.id,
            function_config=child_function,
            is_constructor=False,
        )
    ]
    child_input_attr = make_attribute_config(
        owner_key="aware.tests.Child.emit",
        name="value",
        type_descriptor=AttributeTypeDescriptor(
            id=uuid4(),
            kind=AttributeTypeDescriptorKind.primitive,
        ),
    )
    child_input = FunctionConfigAttributeConfig(
        id=uuid4(),
        function_config_id=child_function.id,
        attribute_config=child_input_attr,
        attribute_config_id=child_input_attr.id,
        name="value",
        position=0,
        type=FunctionAttributeType.input,
    )
    child_function.function_config_attribute_configs = [child_input]

    parent_label_attr = make_attribute_config(
        owner_key="aware.tests.Parent.run",
        name="label",
        type_descriptor=AttributeTypeDescriptor(
            id=uuid4(),
            kind=AttributeTypeDescriptorKind.primitive,
        ),
    )
    parent_label_input = FunctionConfigAttributeConfig(
        id=uuid4(),
        function_config_id=handler_request.execution_plan.implementation.function_config.id,
        attribute_config=parent_label_attr,
        attribute_config_id=parent_label_attr.id,
        name="label",
        position=0,
        type=FunctionAttributeType.input,
    )
    parent_summary_attr = make_attribute_config(
        owner_key="aware.tests.Parent",
        name="summary",
        type_descriptor=AttributeTypeDescriptor(
            id=uuid4(),
            kind=AttributeTypeDescriptorKind.primitive,
        ),
    )
    parent_summary_edge = ClassConfigAttributeConfig(
        id=uuid4(),
        class_config_id=parent_config_id,
        attribute_config=parent_summary_attr,
        attribute_config_id=parent_summary_attr.id,
    )
    parent_config.class_config_attribute_configs = [parent_summary_edge]
    handler_request.execution_plan.implementation.function_config.function_config_attribute_configs = [
        parent_label_input
    ]

    relationship_attr = make_attribute_config(
        owner_key="aware.tests.Parent",
        name="child",
        type_descriptor=AttributeTypeDescriptor(
            id=uuid4(),
            kind=AttributeTypeDescriptorKind.class_,
            class_config=child_config,
            class_config_id=child_config.id,
        ),
    )
    relationship = ClassConfigRelationship(
        id=uuid4(),
        class_config_id=parent_config_id,
        target_class_config_id=child_config.id,
        target_class_config=child_config,
        relationship_key="parent_child",
        relationship_type=ClassConfigRelationshipType.one_to_one,
        forward_required=True,
        class_config_relationship_attributes=[
            ClassConfigRelationshipAttribute(
                id=uuid4(),
                class_config_relationship_id=uuid4(),
                attribute_config=relationship_attr,
                attribute_config_id=relationship_attr.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            )
        ],
    )
    relationship.class_config_relationship_attributes[
        0
    ].class_config_relationship_id = relationship.id
    parent_config.class_config_relationships = [relationship]
    handler_request.execution_plan.index.class_configs_by_id[child_config.id] = (
        child_config
    )
    handler_request.execution_plan.index.attribute_configs_by_id[
        child_input_attr.id
    ] = child_input_attr
    handler_request.execution_plan.index.attribute_configs_by_id[
        parent_label_attr.id
    ] = parent_label_attr
    handler_request.execution_plan.index.attribute_configs_by_id[
        parent_summary_attr.id
    ] = parent_summary_attr
    handler_request.execution_plan.index.attribute_configs_by_id[
        relationship_attr.id
    ] = relationship_attr
    handler_request.execution_plan.index.relationships_by_id[relationship.id] = (
        relationship
    )
    assert handler_request.execution_plan.implementation_descriptors_by_id is not None
    handler_request.execution_plan.implementation_descriptors_by_id[
        child_function.id
    ] = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=child_function,
        owner_class_config=child_config,
        is_constructor=False,
    )
    assert handler_request.execution_plan.function_input_edges_by_id is not None
    handler_request.execution_plan.function_input_edges_by_id[parent_label_input.id] = (
        parent_label_input
    )
    handler_request.execution_plan.function_input_edges_by_id[child_input.id] = (
        child_input
    )
    assert (
        handler_request.execution_plan.function_input_edges_by_function_id is not None
    )
    handler_request.execution_plan.function_input_edges_by_function_id[
        child_function.id
    ] = (child_input,)
    handler_request.execution_plan.function_input_edges_by_function_id[
        handler_request.execution_plan.implementation.function_config.id
    ] = (parent_label_input,)
    assert (
        handler_request.execution_plan.function_input_edges_by_attribute_config_id
        is not None
    )
    handler_request.execution_plan.function_input_edges_by_attribute_config_id[
        child_function.id
    ] = {child_input.attribute_config_id: child_input}

    invoke_instruction_id = uuid4()
    invoke_payload = FunctionImplInstructionInvoke(
        id=uuid4(),
        function_impl_instruction_id=invoke_instruction_id,
        target_function_config=child_function,
        target_function_config_id=child_function.id,
        class_config_relationship=relationship,
        class_config_relationship_id=relationship.id,
        kind=FunctionImplInvokeKind.call,
        attribute_configs=[
            FunctionImplInstructionInvokeAttributeConfig(
                id=uuid4(),
                function_impl_instruction_invoke_id=uuid4(),
                attribute_config=child_input_attr,
                attribute_config_id=child_input_attr.id,
                value_expr=JsonObject({"kind": "reference", "name": "label"}),
                position=0,
            )
        ],
    )
    object.__setattr__(invoke_payload, "capture_name", "child_result")
    invoke_instruction = FunctionImplInstruction(
        id=invoke_instruction_id,
        function_impl_id=parent_impl.id,
        type=FunctionImplInstructionType.invoke,
        sequence=0,
        instruction_invoke=invoke_payload,
    )
    captured_let = FunctionImplInstructionLet(
        id=uuid4(),
        function_impl_instruction_id=uuid4(),
        name="child_result",
        value_expr=JsonObject(),
    )
    set_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=uuid4(),
        key="let:child_result:set",
        kind=FunctionImplValueSourceKind.let_ref,
        source_instruction_let=captured_let,
        source_instruction_let_id=captured_let.id,
    )
    set_instruction = FunctionImplInstruction(
        id=uuid4(),
        function_impl_id=parent_impl.id,
        type=FunctionImplInstructionType.set,
        sequence=1,
        instruction_set=FunctionImplInstructionSet(
            id=uuid4(),
            function_impl_instruction_id=uuid4(),
            target_class_config_attribute_config=parent_summary_edge,
            target_class_config_attribute_config_id=parent_summary_edge.id,
            value_source=set_source,
            value_source_id=set_source.id,
        ),
        value_sources=[set_source],
    )
    parent_impl.instructions = [invoke_instruction, set_instruction]

    graph_id = handler_request.staged_call.lane_scope.object_instance_graph_id
    parent_instance = ClassInstance.model_construct(
        id=parent_object_id,
        object_instance_graph_id=graph_id,
        class_config_id=parent_config_id,
        source_object_id=parent_object_id,
        class_instance_attributes=[],
    )
    child_instance = ClassInstance.model_construct(
        id=child_object_id,
        object_instance_graph_id=graph_id,
        class_config_id=child_config.id,
        source_object_id=child_object_id,
        class_instance_attributes=[],
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        key="test",
        name="test",
        object_projection_graph_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_id
        ),
        root_class_instance=parent_instance,
        root_class_instance_id=parent_instance.id,
        class_instances=[parent_instance, child_instance],
        class_instance_relationships=[
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=graph_id,
                class_config_relationship=relationship,
                class_config_relationship_id=relationship.id,
                source_class_instance_id=parent_instance.id,
                target_class_instance_id=child_instance.id,
            )
        ],
        hash="",
    )
    before_hash = compute_hash(before_oig, index=build_index(before_oig))
    before_oig.hash = before_hash
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=before_hash,
        target_object_id=parent_object_id,
        root_object_id=parent_object_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )
    with pytest.raises(
        MetaGraphAwareFunctionImplExecutionError,
        match="no Meta language handler runner is wired",
    ):
        await MetaGraphInstructionBodyFunctionImplRunner().run_function_impl(
            handler_request,
            pre_state,
            MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject({"label": "from-parent"}),
            ),
        )

    class _NestedCallLanguageHandlerRunner:
        def __init__(self) -> None:
            self.calls: list[
                tuple[
                    MetaGraphHandlerExecutionRequest,
                    MetaGraphPreState,
                    MetaGraphBoundArguments,
                ]
            ] = []

        async def run_language_handler(
            self,
            request: MetaGraphHandlerExecutionRequest,
            pre_state_arg: MetaGraphPreState,
            bound_arguments: MetaGraphBoundArguments,
        ) -> MetaGraphHandlerDispatchResult:
            self.calls.append((request, pre_state_arg, bound_arguments))
            nested_delta = MetaGraphExecutionSessionDelta(
                execution_plan=request.execution_plan,
                before_oig=pre_state_arg.before_oig,
                graph_hash_pre=pre_state_arg.graph_hash_pre,
                graph_hash_post=pre_state_arg.graph_hash_pre,
                changes=(),
                target_class_instance_id=request.execution_plan.target_object_id,
            )
            return MetaGraphHandlerDispatchResult(
                execution_plan=request.execution_plan,
                success=True,
                payload=JsonObject({"value": "from-child"}),
                session_delta=nested_delta,
            )

    nested_runner = _NestedCallLanguageHandlerRunner()
    runner = MetaGraphInstructionBodyFunctionImplRunner(
        language_handler_runner=nested_runner,
    )

    result = await runner.run_function_impl(
        handler_request,
        pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=JsonObject({"label": "from-parent"}),
        ),
    )

    assert result.success is True
    assert len(nested_runner.calls) == 1
    nested_request, nested_pre_state, nested_bound = nested_runner.calls[0]
    assert (
        nested_request.execution_plan.implementation.function_config is child_function
    )
    assert nested_request.execution_plan.target_object_id == child_object_id
    assert nested_pre_state.target_object_id == child_object_id
    assert nested_bound.keyword == JsonObject({"value": "from-parent"})
    assert result.session_delta is not None
    summary_change = result.session_delta.changes[0].class_instance_changes[0]
    assert summary_change.class_instance_id == parent_object_id
    value_delta = summary_change.attribute_changes[
        0
    ].value_root_change.change.change_deltas[0]
    assert value_delta.payload == {"value": "from-child"}


def test_meta_filters_nested_language_handler_delta_to_target_scope() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    graph_id = handler_request.staged_call.lane_scope.object_instance_graph_id
    parent_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )
    ancestor_id = uuid4()
    target_id = uuid4()
    descendant_id = uuid4()
    constructed_id = uuid4()
    before_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        key="test",
        name="test",
        object_projection_graph_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_id
        ),
        root_class_instance_id=ancestor_id,
        class_instances=[
            ClassInstance.model_construct(
                id=ancestor_id,
                object_instance_graph_id=graph_id,
                class_config_id=parent_config_id,
                source_object_id=ancestor_id,
                class_instance_attributes=[],
            ),
            ClassInstance.model_construct(
                id=target_id,
                object_instance_graph_id=graph_id,
                class_config_id=parent_config_id,
                source_object_id=target_id,
                class_instance_attributes=[],
            ),
            ClassInstance.model_construct(
                id=descendant_id,
                object_instance_graph_id=graph_id,
                class_config_id=parent_config_id,
                source_object_id=descendant_id,
                class_instance_attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=graph_id,
                class_config_relationship_id=uuid4(),
                source_class_instance_id=ancestor_id,
                target_class_instance_id=target_id,
            ),
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=graph_id,
                class_config_relationship_id=uuid4(),
                source_class_instance_id=target_id,
                target_class_instance_id=descendant_id,
            ),
        ],
        hash="sha256:test:pre",
    )
    mixed_change = _object_change(
        object_instance_graph_id=graph_id,
        class_changes=(
            _class_instance_change(
                class_instance_id=ancestor_id,
                change_type=ChangeType.update,
            ),
            _class_instance_change(
                class_instance_id=target_id,
                change_type=ChangeType.update,
            ),
            _class_instance_change(
                class_instance_id=descendant_id,
                change_type=ChangeType.update,
            ),
            _class_instance_change(
                class_instance_id=constructed_id,
                change_type=ChangeType.create,
            ),
        ),
    )
    relationship_change = _relationship_change(
        source_class_instance_id=target_id,
        target_class_instance_id=constructed_id,
    )
    session_delta = MetaGraphExecutionSessionDelta(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        changes=(mixed_change, relationship_change),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        target_class_instance_id=target_id,
        constructed_class_instance_ids=(constructed_id,),
    )

    scoped_delta = _filter_nested_session_delta_to_target_scope(
        session_delta=session_delta,
    )

    assert scoped_delta is not session_delta
    assert scoped_delta.constructed_class_instance_ids == (constructed_id,)
    scoped_class_ids = [
        item.class_instance_id
        for change in scoped_delta.changes
        for item in change.class_instance_changes
    ]
    assert scoped_class_ids == [target_id, descendant_id, constructed_id]
    scoped_relationships = [
        item
        for change in scoped_delta.changes
        for item in change.class_instance_relationship_changes
    ]
    assert len(scoped_relationships) == 1
    assert scoped_relationships[0].source_class_instance_id == target_id
    assert scoped_relationships[0].target_class_instance_id == constructed_id


@pytest.mark.asyncio
async def test_meta_generated_executor_runs_compiler_owned_function_impl_runner() -> (
    None
):
    target_object_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    function_impl.instructions = [
        FunctionImplInstruction(
            id=uuid4(),
            function_impl_id=function_impl.id or uuid4(),
            type=FunctionImplInstructionType.let,
            sequence=0,
        )
    ]
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"label": "after"}),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="label",
    )
    function_impl.instructions = fixture.instructions
    registry = MetaGraphGeneratedLanguageHandlerRegistry(handlers_by_key={})
    executor = build_meta_graph_generated_handler_executor(
        handler_resolver=registry,
        pre_state_provider=_RecordingPreStateProvider(
            result=MetaGraphPreStateProviderResult(
                before_oig=fixture.pre_state.before_oig,
                graph_hash_pre=fixture.pre_state.graph_hash_pre,
                root_object_id=target_object_id,
            ),
        ),
    )

    result = await executor.execute_function(handler_request)

    assert result.success is True
    assert result.payload == JsonObject({"rail": "aware_function_impl"})
    assert result.graph_hash_pre == fixture.pre_state.graph_hash_pre
    assert result.graph_hash_post != fixture.pre_state.graph_hash_pre
    assert result.changes


@pytest.mark.asyncio
async def test_meta_instruction_body_runner_fails_closed_on_cross_object_set() -> None:
    target_object_id = uuid4()
    other_class_config_id = uuid4()
    function_impl = FunctionImpl(
        key="aware.tests.Thread.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    handler_request = _meta_handler_execution_request(
        function_impl=function_impl,
        target_object_id=target_object_id,
        implementation_policy=_compiler_owned_policy(),
        kwargs=JsonObject({"label": "after"}),
    )
    fixture = _function_impl_self_set_fixture(
        handler_request=handler_request,
        target_object_id=target_object_id,
        initial_value="before",
        input_value_name="label",
        target_edge_class_config_id=other_class_config_id,
    )
    function_impl.instructions = fixture.instructions
    runner = MetaGraphInstructionBodyFunctionImplRunner()

    with pytest.raises(
        MetaGraphAwareFunctionImplExecutionError,
        match="does not belong to invoked ClassInstance",
    ):
        await runner.run_function_impl(
            handler_request,
            fixture.pre_state,
            MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject({"label": "after"}),
            ),
        )


@pytest.mark.asyncio
async def test_meta_implementation_dispatcher_rejects_stale_bound_arguments() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    phase = MetaGraphImplementationDispatcherPhase()

    with pytest.raises(
        MetaGraphImplementationDispatchError,
        match="same execution plan",
    ):
        await phase.dispatch_implementation(
            handler_request,
            _meta_pre_state(handler_request),
            MetaGraphBoundArguments(
                execution_plan=other_handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(),
            ),
        )


@pytest.mark.asyncio
async def test_meta_language_handler_runner_builds_session_delta_from_changes() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    implementation = _RecordingLanguageHandlerImplementation(
        result=MetaGraphLanguageHandlerExecution(
            success=True,
            payload=JsonObject({"ok": True}),
            execution_time_ms=11,
            changes=changes,
            expected_graph_hash_post=expected_post_hash,
        )
    )
    runner = MetaGraphSessionDeltaLanguageHandlerRunner(
        implementation=implementation,
    )
    phase = MetaGraphImplementationDispatcherPhase(language_handler_runner=runner)

    dispatch_result = await phase.dispatch_implementation(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert implementation.calls == [(handler_request, pre_state, bound_arguments)]
    assert dispatch_result.execution_plan is handler_request.execution_plan
    assert dispatch_result.success is True
    assert dispatch_result.payload == JsonObject({"ok": True})
    assert dispatch_result.execution_time_ms == 11
    assert dispatch_result.session_delta is not None
    assert dispatch_result.session_delta.changes == changes
    assert dispatch_result.session_delta.graph_hash_pre == "sha256:test:pre"
    assert dispatch_result.session_delta.graph_hash_post == expected_post_hash


@pytest.mark.asyncio
async def test_meta_language_handler_runner_builds_session_delta_from_post_oig() -> (
    None
):
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    implementation = _RecordingLanguageHandlerImplementation(
        result=MetaGraphLanguageHandlerExecution(
            success=True,
            post_oig=post_oig,
            expected_graph_hash_post=expected_post_hash,
        )
    )
    runner = MetaGraphSessionDeltaLanguageHandlerRunner(
        implementation=implementation,
    )

    dispatch_result = await runner.run_language_handler(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert dispatch_result.session_delta is not None
    assert dispatch_result.session_delta.graph_hash_post == expected_post_hash
    assert len(dispatch_result.session_delta.changes) == 1


@pytest.mark.asyncio
async def test_meta_language_handler_runner_rejects_ambiguous_mutation_evidence() -> (
    None
):
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    implementation = _RecordingLanguageHandlerImplementation(
        result=MetaGraphLanguageHandlerExecution(
            success=True,
            changes=changes,
            post_oig=pre_state.before_oig.model_copy(deep=True),
        )
    )
    runner = MetaGraphSessionDeltaLanguageHandlerRunner(
        implementation=implementation,
    )

    with pytest.raises(
        MetaGraphLanguageHandlerExecutionError,
        match="either post_oig",
    ):
        await runner.run_language_handler(
            handler_request,
            pre_state,
            bound_arguments,
        )


@pytest.mark.asyncio
async def test_meta_generated_language_handler_adapter_feeds_session_runner() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    calls: list[
        tuple[
            MetaGraphHandlerExecutionRequest,
            MetaGraphPreState,
            JsonArray,
            JsonObject,
        ]
    ] = []

    async def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        calls.append((request, pre_state_arg, positional, keyword))
        positional.append("local-mutation")
        keyword["local_mutation"] = True
        return MetaGraphLanguageHandlerExecution(
            success=True,
            payload=JsonObject({"ok": True}),
            execution_time_ms=13,
            changes=changes,
            expected_graph_hash_post=expected_post_hash,
        )

    runner = MetaGraphSessionDeltaLanguageHandlerRunner(
        implementation=MetaGraphGeneratedLanguageHandlerImplementation(
            handler=generated_handler,
        ),
    )

    dispatch_result = await runner.run_language_handler(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert len(calls) == 1
    called_request, called_pre_state, positional, keyword = calls[0]
    assert called_request is handler_request
    assert called_pre_state is pre_state
    assert positional is not bound_arguments.positional
    assert keyword is not bound_arguments.keyword
    assert positional == JsonArray([1, "local-mutation"])
    assert keyword == JsonObject({"label": "ok", "local_mutation": True})
    assert bound_arguments.positional == JsonArray([1])
    assert bound_arguments.keyword == JsonObject({"label": "ok"})
    assert dispatch_result.success is True
    assert dispatch_result.payload == JsonObject({"ok": True})
    assert dispatch_result.execution_time_ms == 13
    assert dispatch_result.session_delta is not None
    assert dispatch_result.session_delta.changes == changes
    assert dispatch_result.session_delta.graph_hash_post == expected_post_hash


@pytest.mark.asyncio
async def test_meta_generated_language_handler_adapter_rejects_untyped_result() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )

    def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> JsonObject:
        _ = request, pre_state_arg, positional, keyword
        return JsonObject({"not": "execution-evidence"})

    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=generated_handler,
    )

    with pytest.raises(
        MetaGraphLanguageHandlerExecutionError,
        match="MetaGraphLanguageHandlerExecution",
    ):
        await implementation.execute_language_handler(
            handler_request,
            pre_state,
            bound_arguments,
        )


@pytest.mark.asyncio
async def test_meta_generated_language_handler_adapter_sets_meta_context() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    observed: dict[str, object] = {}

    def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state_arg, positional, keyword
        context = current_meta_graph_handler_execution_context()
        observed["context"] = context
        observed["ctx"] = context.ctx
        observed["session_branch_id"] = context.session.branch_id
        return MetaGraphLanguageHandlerExecution(success=True)

    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=generated_handler,
    )

    await implementation.execute_language_handler(
        handler_request,
        pre_state,
        bound_arguments,
    )

    context = cast(MetaGraphHandlerExecutionContext, observed["context"])
    ctx = cast(MetaGraphHandlerContext, observed["ctx"])
    lane_scope = handler_request.staged_call.lane_scope
    assert context.function_call is handler_request.staged_call.function_call
    assert context.index is handler_request.execution_plan.index
    assert observed["session_branch_id"] == lane_scope.domain_branch_id
    assert ctx.requester_id == handler_request.request.actor_id
    assert ctx.domain_oigb_id == lane_scope.object_instance_graph_branch_id
    assert ctx.branch_id == lane_scope.domain_branch_id
    assert ctx.projection_hash == lane_scope.domain_projection_hash
    assert ctx.portal_index is handler_request.execution_plan.index.portal_index


@pytest.mark.asyncio
async def test_meta_generated_constructor_empty_lane_does_not_bind_bootstrap_root() -> (
    None
):
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    model_cls = ORMModelRegistry.get_class_by_class_config_id(fixture.class_config.id)
    assert model_cls is not None
    observed: dict[str, object] = {}

    def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state_arg, positional, keyword
        session = current_handler_session()
        observed["bound_bootstrap_root"] = (
            session.imap_get(
                cast(type[ORMModel], model_cls),
                fixture.object_instance_graph_identity_id,
            )
            is not None
        )
        return MetaGraphLanguageHandlerExecution(success=True)

    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=generated_handler,
    )

    await implementation.execute_language_handler(
        handler_request,
        MetaGraphPreState(
            execution_plan=handler_request.execution_plan,
            before_oig=fixture.before_oig,
            graph_hash_pre=fixture.before_oig.hash,
            head_commit_id=None,
            root_object_id=fixture.object_instance_graph_identity_id,
        ),
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=handler_request.request.kwargs,
        ),
    )

    assert observed["bound_bootstrap_root"] is False


@pytest.mark.asyncio
async def test_meta_generated_constructor_committed_lane_binds_pre_state_root() -> None:
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    model_cls = ORMModelRegistry.get_class_by_class_config_id(fixture.class_config.id)
    assert model_cls is not None
    observed: dict[str, object] = {}

    def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state_arg, positional, keyword
        session = current_handler_session()
        observed["bound_pre_state_root"] = (
            session.imap_get(
                cast(type[ORMModel], model_cls),
                fixture.object_instance_graph_identity_id,
            )
            is not None
        )
        return MetaGraphLanguageHandlerExecution(success=True)

    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=generated_handler,
    )

    await implementation.execute_language_handler(
        handler_request,
        MetaGraphPreState(
            execution_plan=handler_request.execution_plan,
            before_oig=fixture.before_oig,
            graph_hash_pre=fixture.before_oig.hash,
            head_commit_id=uuid4(),
            root_object_id=fixture.object_instance_graph_identity_id,
        ),
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=handler_request.request.kwargs,
        ),
    )

    assert observed["bound_pre_state_root"] is True


@pytest.mark.asyncio
async def test_meta_generated_language_handler_installs_invocation_provider() -> None:
    nested_function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests.Nested",
        name="touch",
    )
    nested_class_config_id = uuid4()
    nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_fqn="aware.tests.Nested",
        name="Nested",
        class_config_function_configs=[
            ClassConfigFunctionConfig(
                id=uuid4(),
                class_config_id=nested_class_config_id,
                function_config_id=nested_function_config.id,
                function_config=nested_function_config,
                is_constructor=False,
            )
        ],
    )

    class NestedModel(ORMModel):
        value: str | None = None

    NestedModel.bind_class_config(nested_class_config)

    handler_request = _meta_handler_execution_request()
    handler_request.execution_plan.index.class_configs_by_id[nested_class_config.id] = (
        nested_class_config
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    observed: dict[str, object] = {}

    async def nested_invocation_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        target: ORMModel | type[ORMModel],
        positional: JsonArray,
        keyword: JsonObject,
    ) -> object:
        _ = request, pre_state_arg, positional
        assert isinstance(target, NestedModel)
        target.value = str(keyword["value"])
        observed["target"] = target
        return target

    async def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state_arg, positional, keyword
        model = NestedModel()
        result = await invoke_instance(
            orm_model=model,
            function_name="touch",
            payload={"value": "provider-ok"},
        )
        observed["result"] = result
        return MetaGraphLanguageHandlerExecution(success=True)

    invocation_registry = MetaGraphGeneratedInvocationHandlerRegistry(
        handlers_by_key={
            MetaGraphGeneratedLanguageHandlerKey(
                owner_key=nested_function_config.owner_key,
                function_name=nested_function_config.name,
                is_constructor=False,
                owner_class_fqn=nested_class_config.class_fqn,
                owner_class_name=nested_class_config.name,
            ): nested_invocation_handler
        },
    )
    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=generated_handler,
        invocation_handler_resolver=invocation_registry,
    )

    await implementation.execute_language_handler(
        handler_request,
        pre_state,
        bound_arguments,
    )

    result = cast(NestedModel, observed["result"])
    assert result.value == "provider-ok"
    assert observed["target"] is result


@pytest.mark.asyncio
async def test_meta_generated_language_handler_runner_resolves_descriptor() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(["input"]),
        keyword=JsonObject({"flag": True}),
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    descriptor = handler_request.execution_plan.implementation
    key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(descriptor)
    calls: list[
        tuple[
            MetaGraphHandlerExecutionRequest,
            MetaGraphPreState,
            JsonArray,
            JsonObject,
        ]
    ] = []

    def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        calls.append((request, pre_state_arg, positional, keyword))
        return MetaGraphLanguageHandlerExecution(
            success=True,
            payload=JsonObject({"resolved": True}),
            execution_time_ms=17,
            changes=changes,
            expected_graph_hash_post=expected_post_hash,
        )

    handlers = {key: generated_handler}
    registry = MetaGraphGeneratedLanguageHandlerRegistry(handlers_by_key=handlers)
    handlers.clear()
    runner = MetaGraphGeneratedLanguageHandlerRunner(handler_resolver=registry)
    phase = MetaGraphImplementationDispatcherPhase(language_handler_runner=runner)

    dispatch_result = await phase.dispatch_implementation(
        handler_request,
        pre_state,
        bound_arguments,
    )

    assert key.function_id == descriptor.function_config.id
    assert key.owner_key == "aware.tests"
    assert key.function_name == "mutate"
    assert key.owner_class_fqn == "aware.tests.Thread"
    assert key.owner_class_name == "Thread"
    assert calls[0][0] is handler_request
    assert calls[0][1] is pre_state
    assert calls[0][2] == JsonArray(["input"])
    assert calls[0][3] == JsonObject({"flag": True})
    assert dispatch_result.payload == JsonObject({"resolved": True})
    assert dispatch_result.execution_time_ms == 17
    assert dispatch_result.session_delta is not None
    assert dispatch_result.session_delta.changes == changes
    assert dispatch_result.session_delta.graph_hash_post == expected_post_hash


@pytest.mark.asyncio
async def test_meta_generated_handler_registry_fails_closed_missing_handler() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray(),
        keyword=JsonObject(),
    )
    runner = MetaGraphGeneratedLanguageHandlerRunner(
        handler_resolver=MetaGraphGeneratedLanguageHandlerRegistry(
            handlers_by_key={},
        ),
    )

    with pytest.raises(
        MetaGraphGeneratedLanguageHandlerResolutionError,
        match="No generated Meta language handler registered",
    ) as exc_info:
        await runner.run_language_handler(
            handler_request,
            pre_state,
            bound_arguments,
        )

    message = str(exc_info.value)
    assert f"function_id={handler_request.request.function_id}" in message
    assert "owner_key=aware.tests" in message
    assert "function_name=mutate" in message
    assert "owner_class_name=Thread" in message


def test_meta_generated_handler_registry_rejects_function_impl_descriptor() -> None:
    function_impl = FunctionImpl(
        key="aware.tests.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    function_impl.instructions = [
        FunctionImplInstruction(
            id=uuid4(),
            function_impl_id=function_impl.id or uuid4(),
            type=FunctionImplInstructionType.let,
            sequence=0,
        )
    ]
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        function_impl=function_impl,
        implementation_policy=_compiler_owned_policy(),
    )
    registry = MetaGraphGeneratedLanguageHandlerRegistry(handlers_by_key={})

    with pytest.raises(
        MetaGraphGeneratedLanguageHandlerResolutionError,
        match="requires a language-handler descriptor",
    ):
        registry.resolve_generated_language_handler(
            handler_request.execution_plan.implementation,
        )


def test_meta_docstring_only_function_impl_uses_language_handler_descriptor() -> None:
    function_impl = FunctionImpl(
        key="aware.tests.mutate",
        kind=FunctionImplKind.instruction_body,
    )
    function_impl.instructions = []

    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        function_impl=function_impl,
        implementation_policy=_compiler_owned_policy(),
    )

    descriptor = handler_request.execution_plan.implementation
    assert descriptor.kind is MetaGraphImplementationKind.language_handler
    assert descriptor.function_config.function_impl is function_impl


@pytest.mark.asyncio
async def test_meta_generated_handler_executor_factory_uses_module_registry() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    calls: list[
        tuple[
            MetaGraphHandlerExecutionRequest,
            MetaGraphPreState,
            JsonArray,
            JsonObject,
        ]
    ] = []

    async def generated_handler(
        request: MetaGraphHandlerExecutionRequest,
        pre_state_arg: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        calls.append((request, pre_state_arg, positional, keyword))
        return MetaGraphLanguageHandlerExecution(
            success=True,
            payload=JsonObject({"factory": True}),
            execution_time_ms=19,
            changes=changes,
            expected_graph_hash_post=expected_post_hash,
        )

    symbolic_key = MetaGraphGeneratedLanguageHandlerKey.from_descriptor(
        handler_request.execution_plan.implementation,
        include_function_id=False,
    )

    class _GeneratedModule:
        AWARE_META_GRAPH_HANDLERS = {symbolic_key: generated_handler}

    module: MetaGraphGeneratedLanguageHandlerModule = _GeneratedModule()
    registry = build_meta_graph_generated_language_handler_registry(module=module)
    executor = build_meta_graph_generated_handler_executor(
        handler_resolver=registry,
        pre_state_provider=_RecordingPreStateProvider(
            result=MetaGraphPreStateProviderResult(
                before_oig=pre_state.before_oig,
                graph_hash_pre=pre_state.graph_hash_pre,
            ),
        ),
    )

    result = await executor.execute_function(handler_request)

    assert calls[0][0] is handler_request
    assert calls[0][1].before_oig is pre_state.before_oig
    assert result.success is True
    assert result.payload == JsonObject({"factory": True})
    assert result.execution_time_ms == 19
    assert result.graph_hash_pre == "sha256:test:pre"
    assert result.graph_hash_post == expected_post_hash
    assert result.before_oig is pre_state.before_oig
    assert result.changes == changes
    assert result.append_ready_changes is not None
    assert result.append_ready_changes.changes == changes


@dataclass(frozen=True)
class _OigiGeneratedHandlerFixture:
    index: SimpleNamespace
    opg: ObjectProjectionGraph
    function_config: FunctionConfig
    class_config: ClassConfig
    before_oig: ObjectInstanceGraph
    object_projection_graph_identity_id: UUID
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID


def _primitive_descriptor(
    base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.string,
) -> AttributeTypeDescriptor:
    primitive_config = build_primitive_config(
        build_code_primitive_type(base_type=base_type)
    )
    return AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
        child_links=[],
    )


def _oigi_generated_handler_fixture() -> _OigiGeneratedHandlerFixture:
    class_fqn = oigi_generated_handlers.OIGI_OWNER_CLASS_FQN
    class_config = make_class_config(
        oigi_generated_handlers.OIGI_OWNER_CLASS_NAME,
        class_fqn=class_fqn,
    )
    object_instance_graph_class_config = make_class_config(
        "ObjectInstanceGraph",
        class_fqn="aware_meta.graph.instance.ObjectInstanceGraph",
    )
    function_config = FunctionConfig(
        owner_key=oigi_generated_handlers.OIGI_OWNER_KEY,
        name=oigi_generated_handlers.OIGI_CREATE_VIA_OPGI,
        kind=FunctionKind.instance,
        function_impl=FunctionImpl(
            key="default",
            kind=FunctionImplKind.auto_constructor,
        ),
    )
    function_edge = ClassConfigFunctionConfig(
        class_config_id=class_config.id,
        function_config=function_config,
        function_config_id=function_config.id,
        is_constructor=True,
    )
    object_projection_graph_identity_id_attr = make_attribute_config(
        owner_key=class_fqn,
        name="object_projection_graph_identity_id",
        is_required=True,
        type_descriptor=_primitive_descriptor(CodePrimitiveBaseType.uuid),
    )
    object_instance_graph_id_attr = make_attribute_config(
        owner_key=class_fqn,
        name="object_instance_graph_id",
        is_required=True,
        type_descriptor=_primitive_descriptor(CodePrimitiveBaseType.uuid),
    )
    label_attr = make_attribute_config(
        owner_key=class_fqn,
        name="label",
        is_required=False,
        type_descriptor=_primitive_descriptor(),
    )
    attr_configs = [
        object_projection_graph_identity_id_attr,
        object_instance_graph_id_attr,
        label_attr,
    ]
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=attr_config,
            position=position,
        )
        for position, attr_config in enumerate(attr_configs)
    ]
    class_config.class_config_function_configs = [function_edge]
    object_instance_graph_relationship = ClassConfigRelationship(
        id=uuid4(),
        class_config_id=class_config.id,
        target_class_config_id=object_instance_graph_class_config.id,
        target_class_config=object_instance_graph_class_config,
        relationship_key="object_instance_graph_identity_object_instance_graph",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_relationship_attributes=[],
    )
    object_instance_graph_relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            id=uuid4(),
            class_config_relationship_id=object_instance_graph_relationship.id,
            attribute_config=object_instance_graph_id_attr,
            attribute_config_id=object_instance_graph_id_attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    class_config.class_config_relationships = [object_instance_graph_relationship]
    _ensure_test_model_binding(class_config)

    ocg_id = uuid4()
    opg = ObjectProjectionGraph(
        object_config_graph_id=ocg_id,
        language=CodeLanguage.aware,
        name="ObjectInstanceGraphIdentity",
        projection_hash="sha256:test:oigi",
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            object_projection_graph_id=opg.id,
            class_config_id=class_config.id,
            class_config=class_config,
            is_root=True,
        )
    ]

    object_projection_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
    )
    before_oig = _meta_rooted_oig(
        object_config_graph_id=ocg_id,
        opg=opg,
        class_config=class_config,
        root_source_object_id=object_instance_graph_identity_id,
        oig_id=object_instance_graph_identity_id,
    )

    index = SimpleNamespace(
        ocg=SimpleNamespace(
            fqn_prefix="aware_meta",
            name="Aware Meta",
            object_config_graph_identity=None,
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ],
            object_projection_graphs=[opg],
        ),
        class_configs_by_id={
            class_config.id: class_config,
            object_instance_graph_class_config.id: object_instance_graph_class_config,
        },
        opg_by_id={opg.id: opg},
        opg_by_hash={opg.projection_hash: opg},
        attribute_configs_by_id={
            attr_config.id: attr_config for attr_config in attr_configs
        },
        relationships_by_id={
            object_instance_graph_relationship.id: object_instance_graph_relationship
        },
        portal_index=SimpleNamespace(),
    )
    return _OigiGeneratedHandlerFixture(
        index=index,
        opg=opg,
        function_config=function_config,
        class_config=class_config,
        before_oig=before_oig,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )


def _meta_rooted_oig(
    *,
    object_config_graph_id: UUID,
    opg: ObjectProjectionGraph,
    class_config: ClassConfig,
    root_source_object_id: UUID,
    oig_id: UUID,
) -> ObjectInstanceGraph:
    from aware_meta.graph.instance.builder import (
        build_rooted_object_instance_graph_base,
    )

    return build_rooted_object_instance_graph_base(
        key=str(oig_id),
        name="OIGI",
        description="ROOTED_BASE",
        object_config_graph_id=object_config_graph_id,
        object_projection_graph=opg,
        root_source_object_id=root_source_object_id,
        root_class_config_id=class_config.id,
        oig_id=oig_id,
    )


def _oigi_generated_handler_request(
    fixture: _OigiGeneratedHandlerFixture,
) -> MetaGraphHandlerExecutionRequest:
    lane_scope = MetaGraphInvocationLaneScope(
        domain_branch_id=fixture.object_instance_graph_id,
        domain_projection_hash=fixture.opg.projection_hash,
        object_projection_graph_id=fixture.opg.id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=fixture.object_instance_graph_identity_id,
        object_instance_graph_identity_id=fixture.object_instance_graph_identity_id,
        object_instance_graph_branch_id=uuid4(),
        lane_id=uuid4(),
        object_instance_graph_lane_id=uuid4(),
    )
    function_call = FunctionCall(
        id=uuid4(),
        object_instance_graph_lane_id=lane_scope.object_instance_graph_lane_id,
        call_key=uuid4(),
        function_config=fixture.function_config,
        function_config_id=fixture.function_config.id,
        graph_hash_pre=fixture.before_oig.hash,
    )
    staged_call = MetaGraphStagedFunctionCall(
        resolved_target=MetaGraphResolvedFunctionTarget(
            function_config=fixture.function_config,
            operation_label=(
                "ObjectInstanceGraphIdentity."
                "create_via_object_projection_graph_identity"
            ),
        ),
        lane_scope=lane_scope,
        function_call=function_call,
    )
    execution_plan = MetaGraphExecutionPlan(
        index=cast(MetaGraphRuntimeIndex, fixture.index),
        staged_call=staged_call,
        implementation=MetaGraphFunctionImplementationDescriptor(
            kind=MetaGraphImplementationKind.language_handler,
            function_config=fixture.function_config,
            owner_class_config=fixture.class_config,
            class_function_edge=fixture.class_config.class_config_function_configs[0],
            is_constructor=True,
        ),
        object_projection_graph=fixture.opg,
        target_object_id=fixture.before_oig.root_class_instance_id,
        expected_graph_hash_pre=fixture.before_oig.hash,
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, fixture.index),
        actor_id=uuid4(),
        function_id=fixture.function_config.id,
        domain_branch_id=fixture.object_instance_graph_id,
        domain_projection_hash=fixture.opg.projection_hash,
        call_target=MetaGraphCallTarget.opg_constructor,
        target_object_id=fixture.before_oig.root_class_instance_id,
        object_projection_graph_id=fixture.opg.id,
        args=JsonArray(),
        kwargs=JsonObject(
            {
                "object_projection_graph_identity_id": (
                    str(fixture.object_projection_graph_identity_id)
                ),
                "object_instance_graph_id": str(fixture.object_instance_graph_id),
                "label": "identity lane",
            }
        ),
        expected_graph_hash_pre=fixture.before_oig.hash,
    )
    return MetaGraphHandlerExecutionRequest(
        request=request,
        staged_call=staged_call,
        execution_plan=execution_plan,
    )


def test_oigi_auto_constructor_execution_plan_routes_to_generated_handler() -> None:
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    index_view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, fixture.index),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.compiler,
        ),
    )

    execution_plan = build_meta_graph_execution_plan(
        index=cast(MetaGraphRuntimeIndex, fixture.index),
        request=handler_request.request,
        staged_call=handler_request.staged_call,
        index_view=index_view,
    )
    registry = build_meta_graph_generated_language_handler_registry(
        module=oigi_generated_handlers,
    )

    handler = registry.resolve_generated_language_handler(
        execution_plan.implementation,
    )

    assert fixture.function_config.function_impl is not None
    assert (
        fixture.function_config.function_impl.kind is FunctionImplKind.auto_constructor
    )
    assert (
        execution_plan.implementation.kind
        is MetaGraphImplementationKind.language_handler
    )
    assert (
        handler
        is oigi_generated_handlers.object_instance_graph_identity__create_via_object_projection_graph_identity__handler
    )


@pytest.mark.asyncio
async def test_oigi_generated_constructor_handler_builds_meta_post_oig() -> None:
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=fixture.before_oig,
        graph_hash_pre=fixture.before_oig.hash,
        root_object_id=fixture.object_instance_graph_identity_id,
    )
    registry = build_meta_graph_generated_language_handler_registry(
        module=oigi_generated_handlers,
    )
    runner = MetaGraphGeneratedLanguageHandlerRunner(handler_resolver=registry)

    dispatch_result = await runner.run_language_handler(
        handler_request,
        pre_state,
        MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray(),
            keyword=handler_request.request.kwargs,
        ),
    )

    assert dispatch_result.success is True
    assert dispatch_result.payload is not None
    assert dispatch_result.payload["value"]["id"] == str(
        fixture.object_instance_graph_identity_id
    )
    assert dispatch_result.session_delta is not None
    assert dispatch_result.session_delta.root_object_id == (
        fixture.object_instance_graph_identity_id
    )
    assert dispatch_result.session_delta.graph_hash_post != fixture.before_oig.hash
    assert dispatch_result.session_delta.changes


def test_oigi_generated_constructor_retains_boundary_fk_attribute() -> None:
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=fixture.before_oig,
        graph_hash_pre=fixture.before_oig.hash,
        root_object_id=fixture.object_instance_graph_identity_id,
    )

    execution = oigi_generated_handlers.object_instance_graph_identity__create_via_object_projection_graph_identity__handler(
        handler_request,
        pre_state,
        JsonArray(),
        handler_request.request.kwargs,
    )

    assert execution.post_oig is not None
    root_class_instance = execution.post_oig.root_class_instance
    assert root_class_instance is not None

    decoded_attributes_by_name: dict[str, object] = {}
    for class_instance_attribute in root_class_instance.class_instance_attributes:
        attribute = class_instance_attribute.attribute
        assert attribute is not None
        attribute_config = fixture.index.attribute_configs_by_id[
            attribute.attribute_config_id
        ]
        decoded_attributes_by_name[attribute_config.name] = decode_oig_attribute_value(
            attribute.value_root,
            class_configs_by_id=fixture.index.class_configs_by_id,
        )

    assert decoded_attributes_by_name["object_projection_graph_identity_id"] == (
        fixture.object_projection_graph_identity_id
    )
    assert decoded_attributes_by_name["object_instance_graph_id"] == (
        fixture.object_instance_graph_id
    )


@pytest.mark.asyncio
async def test_oigi_generated_constructor_executor_builds_append_ready_changes() -> (
    None
):
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    executor = build_meta_graph_generated_handler_executor(
        handler_resolver=build_meta_graph_generated_language_handler_registry(
            module=oigi_generated_handlers,
        ),
        pre_state_provider=_RecordingPreStateProvider(
            result=MetaGraphPreStateProviderResult(
                before_oig=fixture.before_oig,
                graph_hash_pre=fixture.before_oig.hash,
                root_object_id=fixture.object_instance_graph_identity_id,
            ),
        ),
    )

    result = await executor.execute_function(handler_request)

    assert result.success is True
    assert result.before_oig is fixture.before_oig
    assert result.graph_hash_pre == fixture.before_oig.hash
    assert result.graph_hash_post is not None
    assert result.graph_hash_post != fixture.before_oig.hash
    assert result.root_object_id == fixture.object_instance_graph_identity_id
    assert result.append_ready_changes is not None
    assert result.append_ready_changes.changes


def test_oigi_generated_constructor_handler_uses_symbolic_meta_key() -> None:
    fixture = _oigi_generated_handler_fixture()
    handler_request = _oigi_generated_handler_request(fixture)
    registry = build_meta_graph_generated_language_handler_registry(
        module=oigi_generated_handlers,
    )

    handler = registry.resolve_generated_language_handler(
        handler_request.execution_plan.implementation,
    )

    assert (
        handler
        is oigi_generated_handlers.object_instance_graph_identity__create_via_object_projection_graph_identity__handler
    )


def test_oigi_generated_handlers_stay_off_legacy_runtime() -> None:
    source = (
        Path(__file__).parents[1]
        / "aware_meta"
        / "runtime"
        / "oigi_generated_handlers.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "getattr(" not in source


@pytest.mark.asyncio
async def test_meta_mutation_recorder_phase_collects_and_normalizes_delta() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=8,
    )
    source_result = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=(),
        graph_hash_pre=None,
        graph_hash_post="sha256:test:post",
    )
    source = _RecordingMutationSource(result=source_result)
    phase = MetaGraphMutationRecorderPhase(mutation_source=source)

    mutation_set = await phase.record_mutations(
        handler_request,
        pre_state,
        dispatch_result,
    )

    assert mutation_set.execution_plan is handler_request.execution_plan
    assert mutation_set.before_oig is pre_state.before_oig
    assert mutation_set.graph_hash_pre == "sha256:test:pre"
    assert mutation_set.graph_hash_post == "sha256:test:post"
    assert source.calls == [(handler_request, pre_state, dispatch_result)]


def test_meta_mutation_set_builder_rejects_source_pre_state_mismatch() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=ObjectInstanceGraph.model_construct(id=uuid4()),
        changes=(),
    )

    with pytest.raises(MetaGraphMutationRecordingError, match="pre-state OIG"):
        build_meta_graph_mutation_set(
            request=handler_request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
            mutation_set=mutation_set,
        )


@pytest.mark.asyncio
async def test_meta_mutation_recorder_fails_closed_without_source() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
    )
    phase = MetaGraphMutationRecorderPhase()

    with pytest.raises(
        MetaGraphMutationRecordingNotReadyError,
        match="mutation source",
    ) as exc_info:
        await phase.record_mutations(
            handler_request,
            pre_state,
            dispatch_result,
        )

    message = str(exc_info.value)
    assert f"function_call_id={handler_request.staged_call.function_call.id}" in message
    assert "dispatch_success=True" in message


@pytest.mark.asyncio
async def test_meta_mutation_recorder_rejects_stale_dispatch_result() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    phase = MetaGraphMutationRecorderPhase(
        mutation_source=_RecordingMutationSource(
            result=MetaGraphMutationSet(
                execution_plan=handler_request.execution_plan,
                before_oig=_meta_pre_state(handler_request).before_oig,
            )
        )
    )

    with pytest.raises(
        MetaGraphMutationRecordingError,
        match="same execution plan",
    ):
        await phase.record_mutations(
            handler_request,
            _meta_pre_state(handler_request),
            MetaGraphHandlerDispatchResult(
                execution_plan=other_handler_request.execution_plan,
                success=True,
            ),
        )


@pytest.mark.asyncio
async def test_meta_session_delta_mutation_source_collects_mutations() -> None:
    target_object_id = uuid4()
    root_identity_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state(handler_request)
    changes = (
        _object_change(
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.update,
                ),
            ),
        ),
    )
    session_delta = MetaGraphExecutionSessionDelta(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=changes,
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
        root_class_instance_identity_id=root_identity_id,
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        session_delta=session_delta,
    )
    source = MetaGraphSessionDeltaMutationSource()

    mutation_set = await source.collect_mutations(
        handler_request,
        pre_state,
        dispatch_result,
    )

    assert mutation_set.execution_plan is handler_request.execution_plan
    assert mutation_set.before_oig is pre_state.before_oig
    assert mutation_set.changes == changes
    assert mutation_set.graph_hash_pre == "sha256:test:pre"
    assert mutation_set.graph_hash_post == "sha256:test:post"
    assert mutation_set.root_object_id == target_object_id
    assert mutation_set.root_class_instance_identity_id == root_identity_id


def test_meta_session_delta_builder_rejects_stale_execution_plan() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
    )
    session_delta = MetaGraphExecutionSessionDelta(
        execution_plan=other_handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        graph_hash_post="sha256:test:post",
    )

    with pytest.raises(MetaGraphMutationRecordingError, match="execution plan"):
        build_meta_graph_mutation_set_from_session_delta(
            request=handler_request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
            session_delta=session_delta,
        )


def test_meta_session_delta_builder_requires_graph_hash_post() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
    )
    session_delta = MetaGraphExecutionSessionDelta(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        graph_hash_post=None,
    )

    with pytest.raises(MetaGraphMutationRecordingError, match="graph_hash_post"):
        build_meta_graph_mutation_set_from_session_delta(
            request=handler_request,
            pre_state=pre_state,
            dispatch_result=dispatch_result,
            session_delta=session_delta,
        )


def test_meta_execution_session_delta_builder_computes_post_hash_from_changes() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    changes = (
        _object_change(
            object_instance_graph_id=pre_state.before_oig.id,
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    expected_post_oig = pre_state.before_oig.model_copy(deep=True)
    expected_post_oig.class_instances = []
    expected_post_hash = compute_hash(
        expected_post_oig,
        index=build_index(expected_post_oig),
    )
    builder = MetaGraphExecutionSessionDeltaBuilder()

    session_delta = builder.build_delta_from_changes(
        request=handler_request,
        pre_state=pre_state,
        changes=changes,
    )

    assert session_delta.execution_plan is handler_request.execution_plan
    assert session_delta.before_oig is pre_state.before_oig
    assert session_delta.changes == changes
    assert session_delta.graph_hash_pre == "sha256:test:pre"
    assert session_delta.graph_hash_post == expected_post_hash
    assert session_delta.root_object_id == target_object_id


def test_meta_execution_session_delta_builder_diffs_post_oig_evidence() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    expected_post_hash = compute_hash(post_oig, index=build_index(post_oig))
    builder = MetaGraphExecutionSessionDeltaBuilder()

    session_delta = builder.build_delta_from_post_oig(
        request=handler_request,
        pre_state=pre_state,
        post_oig=post_oig,
        expected_graph_hash_post=expected_post_hash,
    )

    assert session_delta.execution_plan is handler_request.execution_plan
    assert session_delta.before_oig is pre_state.before_oig
    assert session_delta.graph_hash_pre == "sha256:test:pre"
    assert session_delta.graph_hash_post == expected_post_hash
    assert len(session_delta.changes) == 1
    assert session_delta.changes[0].object_instance_graph_id == pre_state.before_oig.id


def test_meta_execution_session_delta_builder_rejects_wrong_change_oig() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    changes = (
        _object_change(
            object_instance_graph_id=uuid4(),
            object_instance_graph_identity_id=(
                handler_request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.delete,
                ),
            ),
        ),
    )
    builder = MetaGraphExecutionSessionDeltaBuilder()

    with pytest.raises(MetaGraphExecutionSessionDeltaError, match="different"):
        builder.build_delta_from_changes(
            request=handler_request,
            pre_state=pre_state,
            changes=changes,
        )


def test_meta_execution_session_delta_builder_rejects_post_hash_mismatch() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state_with_class_instance(
        handler_request,
        class_instance_id=target_object_id,
    )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    post_oig.class_instances = []
    builder = MetaGraphExecutionSessionDeltaBuilder()

    with pytest.raises(MetaGraphExecutionSessionDeltaError, match="post hash"):
        builder.build_delta_from_post_oig(
            request=handler_request,
            pre_state=pre_state,
            post_oig=post_oig,
            expected_graph_hash_post="sha256:test:wrong",
        )


@pytest.mark.asyncio
async def test_meta_session_delta_mutation_source_fails_closed_without_delta() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
    )
    pre_state = _meta_pre_state(handler_request)
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
    )
    source = MetaGraphSessionDeltaMutationSource()

    with pytest.raises(
        MetaGraphMutationRecordingNotReadyError,
        match="execution-session delta",
    ) as exc_info:
        await source.collect_mutations(
            handler_request,
            pre_state,
            dispatch_result,
        )

    message = str(exc_info.value)
    assert f"function_call_id={handler_request.staged_call.function_call.id}" in message
    function_config = handler_request.execution_plan.implementation.function_config
    assert f"function_id={function_config.id}" in message


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_accepts_self_update() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=target_object_id,
                        change_type=ChangeType.update,
                    ),
                ),
            ),
        ),
    )
    phase = MetaGraphMutationBoundaryValidatorPhase(
        policy=MetaGraphMutateSelfOnlyPolicy(),
    )

    validation = await phase.validate_mutations(handler_request, mutation_set)

    assert validation.status is MetaGraphMutationBoundaryStatus.accepted
    assert validation.violation_message is None


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_rejects_cross_object_update() -> None:
    target_object_id = uuid4()
    other_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=other_object_id,
                        change_type=ChangeType.update,
                    ),
                ),
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.rejected
    assert validation.violation_message is not None
    assert "Cross-object class mutation detected" in validation.violation_message
    assert f"target_object_id={target_object_id}" in validation.violation_message
    assert f"class_instance_id={other_object_id}" in validation.violation_message


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_accepts_descendant_update() -> None:
    target_object_id = uuid4()
    child_object_id = uuid4()
    relationship_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    before_oig = _meta_pre_state(handler_request).before_oig
    before_oig.class_instance_relationships = [
        ClassInstanceRelationship(
            id=uuid4(),
            object_instance_graph_id=before_oig.id,
            class_config_relationship_id=relationship_id,
            source_class_instance_id=target_object_id,
            target_class_instance_id=child_object_id,
        )
    ]
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=child_object_id,
                        change_type=ChangeType.update,
                    ),
                ),
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.accepted
    assert validation.violation_message is None


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_accepts_constructed_id_update() -> None:
    target_object_id = uuid4()
    constructed_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        constructed_class_instance_ids=(constructed_object_id,),
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=constructed_object_id,
                        change_type=ChangeType.update,
                    ),
                ),
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.accepted
    assert validation.violation_message is None


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_rejects_non_constructor_create() -> None:
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=uuid4(),
                        change_type=ChangeType.create,
                    ),
                ),
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.rejected
    assert validation.violation_message is not None
    assert "constructor invocation" in validation.violation_message


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_accepts_constructor_created_relationship() -> (
    None
):
    root_object_id = uuid4()
    child_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        is_constructor=True,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=root_object_id,
                        change_type=ChangeType.create,
                    ),
                ),
            ),
            _relationship_change(
                source_class_instance_id=root_object_id,
                target_class_instance_id=child_object_id,
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.accepted


@pytest.mark.asyncio
async def test_meta_mutate_self_policy_accepts_constructor_root_descendant_delete() -> (
    None
):
    root_object_id = uuid4()
    child_object_id = uuid4()
    relationship_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        is_constructor=True,
    )
    before_oig = _meta_pre_state(handler_request).before_oig
    before_oig.root_class_instance_id = root_object_id
    before_oig.class_instance_relationships = [
        ClassInstanceRelationship(
            id=uuid4(),
            object_instance_graph_id=before_oig.id,
            class_config_relationship_id=relationship_id,
            source_class_instance_id=root_object_id,
            target_class_instance_id=child_object_id,
        )
    ]
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=child_object_id,
                        change_type=ChangeType.delete,
                    ),
                ),
            ),
        ),
    )

    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        handler_request,
        mutation_set,
    )

    assert validation.status is MetaGraphMutationBoundaryStatus.accepted
    assert validation.violation_message is None


@pytest.mark.asyncio
async def test_meta_mutation_boundary_phase_fails_closed_without_policy() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(),
    )
    phase = MetaGraphMutationBoundaryValidatorPhase()

    with pytest.raises(
        MetaGraphMutationBoundaryNotReadyError,
        match="boundary policy",
    ):
        await phase.validate_mutations(handler_request, mutation_set)


def test_meta_mutation_boundary_validation_rejects_stale_policy_result() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        changes=(),
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=other_handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )

    with pytest.raises(MetaGraphMutationBoundaryError, match="execution plan"):
        build_meta_graph_mutation_boundary_validation(
            request=handler_request,
            mutation_set=mutation_set,
            validation=validation,
        )


@pytest.mark.asyncio
async def test_meta_append_ready_assembler_builds_append_ready_changes() -> None:
    target_object_id = uuid4()
    root_identity_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
    )
    pre_state = _meta_pre_state(handler_request)
    changes = (
        _object_change(
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.update,
                ),
            ),
        ),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=changes,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
        root_class_instance_identity_id=root_identity_id,
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )
    phase = MetaGraphAppendReadyChangeAssemblerPhase()

    append_ready = await phase.assemble_append_ready_changes(
        handler_request,
        mutation_set,
        validation,
    )

    assert append_ready.execution_plan is handler_request.execution_plan
    assert append_ready.before_oig is pre_state.before_oig
    assert append_ready.changes == changes
    assert append_ready.graph_hash_pre == "sha256:test:pre"
    assert append_ready.graph_hash_post == "sha256:test:post"
    assert append_ready.root_object_id == target_object_id
    assert append_ready.root_class_instance_identity_id == root_identity_id


def test_meta_append_ready_assembler_rejects_boundary_failure() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.rejected,
        violation_message="Cross-object class mutation detected.",
    )

    with pytest.raises(
        MetaGraphAppendReadyAssemblyError,
        match="rejected mutations",
    ):
        build_meta_graph_append_ready_changes(
            request=handler_request,
            mutation_set=mutation_set,
            boundary_validation=validation,
        )


def test_meta_append_ready_assembler_requires_graph_hash_post() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post=None,
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )

    with pytest.raises(MetaGraphAppendReadyAssemblyError, match="graph_hash_post"):
        build_meta_graph_append_ready_changes(
            request=handler_request,
            mutation_set=mutation_set,
            boundary_validation=validation,
        )


def test_meta_append_ready_assembler_requires_graph_hash_pre() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        graph_hash_pre=None,
        graph_hash_post="sha256:test:post",
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )

    with pytest.raises(MetaGraphAppendReadyAssemblyError, match="graph_hash_pre"):
        build_meta_graph_append_ready_changes(
            request=handler_request,
            mutation_set=mutation_set,
            boundary_validation=validation,
        )


def test_meta_append_ready_assembler_rejects_stale_boundary_validation() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    other_handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=uuid4(),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=_meta_pre_state(handler_request).before_oig,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
    )
    validation = MetaGraphMutationBoundaryValidation(
        execution_plan=other_handler_request.execution_plan,
        mutation_set=mutation_set,
        status=MetaGraphMutationBoundaryStatus.accepted,
    )

    with pytest.raises(MetaGraphAppendReadyAssemblyError, match="execution plan"):
        build_meta_graph_append_ready_changes(
            request=handler_request,
            mutation_set=mutation_set,
            boundary_validation=validation,
        )


@pytest.mark.asyncio
async def test_meta_phase_handler_executor_runs_ready_phases_then_fails_closed() -> (
    None
):
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        args=JsonArray([1, 2]),
        kwargs=JsonObject({"label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    events: list[str] = []
    materializer = _RecordingPreStateMaterializer(
        pre_state=pre_state,
        events=events,
    )
    binder = _RecordingArgumentBinder(
        bound_arguments=MetaGraphBoundArguments(
            execution_plan=handler_request.execution_plan,
            positional=JsonArray([1, 2]),
            keyword=JsonObject({"label": "ok"}),
        ),
        events=events,
    )
    executor = MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=materializer,
        argument_binder=binder,
    )

    with pytest.raises(
        MetaGraphHandlerExecutionNotReadyError,
        match="implementation dispatch",
    ) as exc_info:
        await executor.execute_function(handler_request)

    assert events == ["pre_state", "arguments"]
    assert materializer.requests == [handler_request]
    assert binder.calls == [(handler_request, pre_state)]
    message = str(exc_info.value)
    assert f"function_call_id={handler_request.staged_call.function_call.id}" in message
    assert "implementation_kind=language_handler" in message
    assert "positional_arg_count=2" in message
    assert "keyword_arg_count=1" in message


@pytest.mark.asyncio
async def test_meta_phase_executor_reaches_dispatcher_then_fails_closed() -> None:
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        args=JsonArray([1]),
        kwargs=JsonObject({"label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=7,
    )
    events: list[str] = []
    dispatcher = _RecordingImplementationDispatcher(
        result=dispatch_result,
        events=events,
    )
    executor = MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=_RecordingPreStateMaterializer(
            pre_state=pre_state,
            events=events,
        ),
        argument_binder=_RecordingArgumentBinder(
            bound_arguments=bound_arguments,
            events=events,
        ),
        implementation_dispatcher=dispatcher,
    )

    with pytest.raises(
        MetaGraphHandlerExecutionNotReadyError,
        match="mutation recording",
    ) as exc_info:
        await executor.execute_function(handler_request)

    assert events == ["pre_state", "arguments", "dispatch"]
    assert dispatcher.calls == [(handler_request, pre_state, bound_arguments)]
    message = str(exc_info.value)
    assert "dispatch_success=True" in message
    assert "dispatch_time_ms=7" in message


@pytest.mark.asyncio
async def test_meta_phase_executor_reaches_mutation_recorder_then_fails_closed() -> (
    None
):
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        args=JsonArray([1]),
        kwargs=JsonObject({"label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=7,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=(),
        graph_hash_pre=None,
        graph_hash_post="sha256:test:post",
    )
    events: list[str] = []
    executor = MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=_RecordingPreStateMaterializer(
            pre_state=pre_state,
            events=events,
        ),
        argument_binder=_RecordingArgumentBinder(
            bound_arguments=bound_arguments,
            events=events,
        ),
        implementation_dispatcher=_RecordingImplementationDispatcher(
            result=dispatch_result,
            events=events,
        ),
        mutation_recorder=MetaGraphMutationRecorderPhase(
            mutation_source=_RecordingMutationSource(
                result=mutation_set,
                events=events,
            ),
        ),
    )

    with pytest.raises(
        MetaGraphHandlerExecutionNotReadyError,
        match="mutation boundary validation",
    ) as exc_info:
        await executor.execute_function(handler_request)

    assert events == ["pre_state", "arguments", "dispatch", "mutations"]
    message = str(exc_info.value)
    assert "mutation_change_count=0" in message
    assert "graph_hash_pre=sha256:test:pre" in message
    assert "graph_hash_post=sha256:test:post" in message


@pytest.mark.asyncio
async def test_meta_phase_executor_reaches_boundary_validator_then_fails_closed() -> (
    None
):
    target_object_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
        args=JsonArray([1]),
        kwargs=JsonObject({"label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=7,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=(
            _object_change(
                class_changes=(
                    _class_instance_change(
                        class_instance_id=target_object_id,
                        change_type=ChangeType.update,
                    ),
                ),
            ),
        ),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
    )
    events: list[str] = []
    executor = MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=_RecordingPreStateMaterializer(
            pre_state=pre_state,
            events=events,
        ),
        argument_binder=_RecordingArgumentBinder(
            bound_arguments=bound_arguments,
            events=events,
        ),
        implementation_dispatcher=_RecordingImplementationDispatcher(
            result=dispatch_result,
            events=events,
        ),
        mutation_recorder=MetaGraphMutationRecorderPhase(
            mutation_source=_RecordingMutationSource(
                result=mutation_set,
                events=events,
            ),
        ),
        mutation_boundary_validator=MetaGraphMutationBoundaryValidatorPhase(
            policy=MetaGraphMutateSelfOnlyPolicy(),
        ),
    )

    with pytest.raises(
        MetaGraphHandlerExecutionNotReadyError,
        match="append-ready change assembly",
    ) as exc_info:
        await executor.execute_function(handler_request)

    assert events == ["pre_state", "arguments", "dispatch", "mutations"]
    message = str(exc_info.value)
    assert "boundary_status=accepted" in message
    assert "violation_message=None" in message


@pytest.mark.asyncio
async def test_meta_phase_executor_returns_append_ready_result() -> None:
    target_object_id = uuid4()
    root_identity_id = uuid4()
    handler_request = _meta_handler_execution_request(
        expected_graph_hash_pre="sha256:test:pre",
        target_object_id=target_object_id,
        args=JsonArray([1]),
        kwargs=JsonObject({"label": "ok"}),
    )
    pre_state = _meta_pre_state(handler_request)
    bound_arguments = MetaGraphBoundArguments(
        execution_plan=handler_request.execution_plan,
        positional=JsonArray([1]),
        keyword=JsonObject({"label": "ok"}),
    )
    dispatch_result = MetaGraphHandlerDispatchResult(
        execution_plan=handler_request.execution_plan,
        success=True,
        payload=JsonObject({"ok": True}),
        execution_time_ms=7,
    )
    changes = (
        _object_change(
            class_changes=(
                _class_instance_change(
                    class_instance_id=target_object_id,
                    change_type=ChangeType.update,
                ),
            ),
        ),
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=handler_request.execution_plan,
        before_oig=pre_state.before_oig,
        changes=changes,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
        root_class_instance_identity_id=root_identity_id,
    )
    events: list[str] = []
    executor = MetaGraphPhaseHandlerExecutor(
        pre_state_materializer=_RecordingPreStateMaterializer(
            pre_state=pre_state,
            events=events,
        ),
        argument_binder=_RecordingArgumentBinder(
            bound_arguments=bound_arguments,
            events=events,
        ),
        implementation_dispatcher=_RecordingImplementationDispatcher(
            result=dispatch_result,
            events=events,
        ),
        mutation_recorder=MetaGraphMutationRecorderPhase(
            mutation_source=_RecordingMutationSource(
                result=mutation_set,
                events=events,
            ),
        ),
        mutation_boundary_validator=MetaGraphMutationBoundaryValidatorPhase(
            policy=MetaGraphMutateSelfOnlyPolicy(),
        ),
        append_ready_change_assembler=MetaGraphAppendReadyChangeAssemblerPhase(),
    )

    result = await executor.execute_function(handler_request)

    assert events == ["pre_state", "arguments", "dispatch", "mutations"]
    assert result.success is True
    assert result.payload == JsonObject({"ok": True})
    assert result.execution_time_ms == 7
    assert result.graph_hash_pre == "sha256:test:pre"
    assert result.graph_hash_post == "sha256:test:post"
    assert result.root_object_id == target_object_id
    assert result.root_class_instance_identity_id == root_identity_id
    assert result.before_oig is pre_state.before_oig
    assert result.changes == changes
    assert result.append_ready_changes is not None
    assert result.append_ready_changes.graph_hash_post == "sha256:test:post"


def test_meta_function_implementation_descriptor_names_allowed_rails() -> None:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="mutate",
    )

    aware_descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.aware_function_impl,
        function_config=function_config,
    )
    handler_descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
    )

    assert aware_descriptor.kind.value == "aware_function_impl"
    assert handler_descriptor.kind.value == "language_handler"


def test_meta_handler_executor_contracts_do_not_import_heavy_runtime_index() -> None:
    runtime_root = Path(__file__).parents[1] / "aware_meta" / "runtime"
    paths = [
        runtime_root / "handler_executor" / "__init__.py",
        runtime_root / "handler_executor" / "append_ready.py",
        runtime_root / "handler_executor" / "argument_binding.py",
        runtime_root / "handler_executor" / "contracts.py",
        runtime_root / "handler_executor" / "executor.py",
        runtime_root / "handler_executor" / "execution_context.py",
        runtime_root / "handler_executor" / "implementation_dispatch.py",
        runtime_root / "handler_executor" / "index.py",
        runtime_root / "handler_executor" / "language_handler.py",
        runtime_root / "handler_executor" / "mutation_boundary.py",
        runtime_root / "handler_executor" / "mutation_recording.py",
        runtime_root / "handler_executor" / "plan.py",
        runtime_root / "handler_executor" / "pre_state.py",
        runtime_root / "handler_executor" / "session.py",
        runtime_root / "invocation_engine.py",
    ]
    forbidden_tokens = {
        "aware_runtime.index",
        "AwareRuntimeIndex",
        "FunctionCallInvoker",
        "RuntimeHarness",
        "getattr(",
    }

    leaked: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in source:
                leaked.append(f"{path.name}:{token}")

    assert not leaked


def _compiler_owned_policy() -> MetaGraphImplementationPolicy:
    return MetaGraphImplementationPolicy(
        function_impl_ownership_by_owner_key={
            "aware.tests": MetaGraphFunctionImplOwnership.compiler,
        },
    )


def _executable_instruction_body_impl(key: str) -> FunctionImpl:
    function_impl = FunctionImpl(
        key=key,
        kind=FunctionImplKind.instruction_body,
    )
    function_impl.instructions = [
        FunctionImplInstruction(
            id=uuid4(),
            function_impl_id=function_impl.id or uuid4(),
            type=FunctionImplInstructionType.let,
            sequence=0,
        )
    ]
    return function_impl


@dataclass(frozen=True)
class _FunctionImplSelfSetFixture:
    pre_state: MetaGraphPreState
    instructions: list[FunctionImplInstruction]
    attribute_id: UUID


@dataclass(frozen=True)
class _FunctionImplSelfEnumSetFixture:
    pre_state: MetaGraphPreState
    instructions: list[FunctionImplInstruction]
    attribute_id: UUID
    target_enum_option_id: UUID


@dataclass(frozen=True)
class _FunctionImplSelfDeleteFixture:
    pre_state: MetaGraphPreState
    instructions: list[FunctionImplInstruction]
    root_class_instance_id: UUID
    target_class_instance_id: UUID
    descendant_class_instance_id: UUID | None = None


def _function_impl_self_delete_fixture(
    *,
    handler_request: MetaGraphHandlerExecutionRequest,
    target_object_id: UUID,
    target_is_root: bool = False,
    include_descendant: bool = False,
    external_incoming: bool = False,
) -> _FunctionImplSelfDeleteFixture:
    function_config = handler_request.execution_plan.implementation.function_config
    function_impl = function_config.function_impl
    assert function_impl is not None
    graph_id = handler_request.staged_call.lane_scope.object_instance_graph_id
    class_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )

    root_id = target_object_id if target_is_root else uuid4()
    target_id = target_object_id
    root_instance = ClassInstance.model_construct(
        id=root_id,
        object_instance_graph_id=graph_id,
        class_config_id=class_config_id,
        source_object_id=root_id,
        class_instance_attributes=[],
    )
    target_instance = (
        root_instance
        if target_is_root
        else ClassInstance.model_construct(
            id=target_id,
            object_instance_graph_id=graph_id,
            class_config_id=class_config_id,
            source_object_id=target_id,
            class_instance_attributes=[],
        )
    )
    class_instances = [root_instance]
    if not target_is_root:
        class_instances.append(target_instance)

    relationships: list[ClassInstanceRelationship] = []
    relationship_config_id = uuid4()
    if include_descendant:
        descendant_id = uuid4()
        descendant_instance = ClassInstance.model_construct(
            id=descendant_id,
            object_instance_graph_id=graph_id,
            class_config_id=class_config_id,
            source_object_id=descendant_id,
            class_instance_attributes=[],
        )
        class_instances.append(descendant_instance)
        relationships.append(
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=graph_id,
                class_config_relationship_id=relationship_config_id,
                source_class_instance_id=target_id,
                target_class_instance_id=descendant_id,
            )
        )
    else:
        descendant_id = None

    if external_incoming:
        relationships.append(
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=graph_id,
                class_config_relationship_id=relationship_config_id,
                source_class_instance_id=root_id,
                target_class_instance_id=target_id,
            )
        )

    before_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        key="test",
        name="test",
        object_projection_graph_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_id
        ),
        root_class_instance=root_instance,
        root_class_instance_id=root_id,
        class_instances=class_instances,
        class_instance_relationships=relationships,
        hash="",
    )
    before_hash = compute_hash(before_oig, index=build_index(before_oig))
    before_oig.hash = before_hash

    delete_instruction_id = uuid4()
    delete_payload = FunctionImplInstructionDelete(
        id=uuid4(),
        function_impl_instruction_id=delete_instruction_id,
        target_kind=FunctionImplDeleteTargetKind.self,
    )
    delete_instruction = FunctionImplInstruction(
        id=delete_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.delete,
        sequence=0,
        instruction_delete=delete_payload,
    )
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=before_hash,
        target_object_id=target_object_id,
        root_object_id=root_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )
    return _FunctionImplSelfDeleteFixture(
        pre_state=pre_state,
        instructions=[delete_instruction],
        root_class_instance_id=root_id,
        target_class_instance_id=target_id,
        descendant_class_instance_id=descendant_id,
    )


def _function_impl_self_set_fixture(
    *,
    handler_request: MetaGraphHandlerExecutionRequest,
    target_object_id: UUID,
    initial_value: str,
    input_value_name: str,
    input_default_value: str | None = None,
    target_edge_class_config_id: UUID | None = None,
) -> _FunctionImplSelfSetFixture:
    function_config = handler_request.execution_plan.implementation.function_config
    function_impl = function_config.function_impl
    assert function_impl is not None
    class_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )
    type_descriptor = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.primitive,
    )
    attribute_config = make_attribute_config(
        owner_key="aware.tests.Thread",
        name="label",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    attribute_config.default_value = input_default_value
    handler_request.execution_plan.index.attribute_configs_by_id[
        attribute_config.id
    ] = attribute_config
    function_input = FunctionConfigAttributeConfig(
        id=uuid4(),
        function_config_id=function_config.id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        name=input_value_name,
        position=0,
        type=FunctionAttributeType.input,
    )
    function_config.function_config_attribute_configs = [function_input]
    target_edge = ClassConfigAttributeConfig(
        id=uuid4(),
        class_config_id=target_edge_class_config_id or class_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
    )
    value_root = build_attribute_value_tree(
        type_descriptor=type_descriptor,
        value=initial_value,
        stable_root_id=uuid4(),
    )
    attribute = Attribute(
        id=uuid4(),
        owner_key=target_object_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        value_root=value_root,
        value_root_id=value_root.id,
    )
    class_instance_attribute = ClassInstanceAttribute(
        id=uuid4(),
        class_instance_id=target_object_id,
        attribute=attribute,
        attribute_id=attribute.id,
    )
    class_instance = ClassInstance.model_construct(
        id=target_object_id,
        object_instance_graph_id=(
            handler_request.staged_call.lane_scope.object_instance_graph_id
        ),
        class_config_id=class_config_id,
        source_object_id=target_object_id,
        class_instance_attributes=[class_instance_attribute],
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        key="test",
        name="test",
        object_projection_graph_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_id
        ),
        root_class_instance=class_instance,
        root_class_instance_id=class_instance.id,
        class_instances=[class_instance],
        class_instance_relationships=[],
        hash="",
    )
    before_hash = compute_hash(before_oig, index=build_index(before_oig))
    before_oig.hash = before_hash
    let_instruction_id = uuid4()
    let_payload = FunctionImplInstructionLet(
        id=uuid4(),
        function_impl_instruction_id=let_instruction_id,
        name="new_label",
        value_expr=JsonObject(),
    )
    input_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=let_instruction_id,
        key=f"input:{input_value_name}",
        kind=FunctionImplValueSourceKind.function_input_ref,
        source_function_config_attribute_config=function_input,
        source_function_config_attribute_config_id=function_input.id,
    )
    let_instruction = FunctionImplInstruction(
        id=let_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.let,
        sequence=0,
        instruction_let=let_payload,
        value_sources=[input_source],
    )
    require_instruction_id = uuid4()
    require_payload_id = uuid4()
    require_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=require_instruction_id,
        key="let:new_label:require",
        kind=FunctionImplValueSourceKind.let_ref,
        source_instruction_let=let_payload,
        source_instruction_let_id=let_payload.id,
    )
    require_operand = FunctionImplInstructionRequireOperand(
        id=uuid4(),
        function_impl_instruction_require_id=require_payload_id,
        position=0,
        value_source=require_source,
        value_source_id=require_source.id,
    )
    require_payload = FunctionImplInstructionRequire(
        id=require_payload_id,
        function_impl_instruction_id=require_instruction_id,
        kind=FunctionImplRequireKind.exists,
        message="label required",
        operands=[require_operand],
    )
    require_instruction = FunctionImplInstruction(
        id=require_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.require,
        sequence=1,
        instruction_require=require_payload,
        value_sources=[require_source],
    )
    set_instruction_id = uuid4()
    set_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        key="let:new_label:set",
        kind=FunctionImplValueSourceKind.let_ref,
        source_instruction_let=let_payload,
        source_instruction_let_id=let_payload.id,
    )
    set_payload = FunctionImplInstructionSet(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        target_class_config_attribute_config=target_edge,
        target_class_config_attribute_config_id=target_edge.id,
        value_source=set_source,
        value_source_id=set_source.id,
    )
    set_instruction = FunctionImplInstruction(
        id=set_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.set,
        sequence=2,
        instruction_set=set_payload,
        value_sources=[set_source],
    )
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=before_hash,
        target_object_id=target_object_id,
        root_object_id=target_object_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )
    return _FunctionImplSelfSetFixture(
        pre_state=pre_state,
        instructions=[let_instruction, require_instruction, set_instruction],
        attribute_id=attribute.id,
    )


def _function_impl_self_enum_set_fixture(
    *,
    handler_request: MetaGraphHandlerExecutionRequest,
    target_object_id: UUID,
    initial_value: str,
    target_value: str,
    allowed_values: list[str] | None = None,
) -> _FunctionImplSelfEnumSetFixture:
    function_config = handler_request.execution_plan.implementation.function_config
    function_impl = function_config.function_impl
    assert function_impl is not None
    class_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )
    class_config = handler_request.execution_plan.index.class_configs_by_id[
        class_config_id
    ]

    enum_config = make_enum_config(
        "ThreadStatus",
        enum_fqn=test_enum_fqn("ThreadStatus"),
    )
    enum_values = list(
        dict.fromkeys([initial_value, target_value, *(allowed_values or [])])
    )
    enum_options_by_value = {
        value: EnumOption(
            enum_config_id=enum_config.id,
            value=value,
            position=position,
        )
        for position, value in enumerate(enum_values)
    }
    enum_config.enum_options = list(enum_options_by_value.values())
    handler_request.execution_plan.index.ocg.object_config_graph_nodes.append(
        SimpleNamespace(
            type=ObjectConfigGraphNodeType.enum,
            enum_config=enum_config,
        )
    )

    type_descriptor = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.enum,
        enum_config=enum_config,
        enum_config_id=enum_config.id,
    )
    attribute_config = make_attribute_config(
        owner_key="aware.tests.Thread",
        name="status",
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )
    handler_request.execution_plan.index.attribute_configs_by_id[
        attribute_config.id
    ] = attribute_config
    target_edge = ClassConfigAttributeConfig(
        id=uuid4(),
        class_config_id=class_config_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
    )
    class_config.class_config_attribute_configs = [
        *getattr(class_config, "class_config_attribute_configs", []),
        target_edge,
    ]

    value_root = build_attribute_value_tree(
        type_descriptor=type_descriptor,
        value=enum_options_by_value[initial_value],
        stable_root_id=uuid4(),
        enum_option_resolver=default_meta_enum_option_resolver,
    )
    attribute = Attribute(
        id=uuid4(),
        owner_key=target_object_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        value_root=value_root,
        value_root_id=value_root.id,
    )
    class_instance_attribute = ClassInstanceAttribute(
        id=uuid4(),
        class_instance_id=target_object_id,
        attribute=attribute,
        attribute_id=attribute.id,
    )
    class_instance = ClassInstance.model_construct(
        id=target_object_id,
        object_instance_graph_id=(
            handler_request.staged_call.lane_scope.object_instance_graph_id
        ),
        class_config_id=class_config_id,
        source_object_id=target_object_id,
        class_instance_attributes=[class_instance_attribute],
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        key="test",
        name="test",
        object_projection_graph_id=(
            handler_request.staged_call.lane_scope.object_projection_graph_id
        ),
        root_class_instance=class_instance,
        root_class_instance_id=class_instance.id,
        class_instances=[class_instance],
        class_instance_relationships=[],
        hash="",
    )
    before_hash = compute_hash(before_oig, index=build_index(before_oig))
    before_oig.hash = before_hash

    primitive_config = build_primitive_config(
        build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    )
    instructions: list[FunctionImplInstruction] = []
    set_sequence = 0

    if allowed_values is not None:
        let_instruction_id = uuid4()
        let_payload = FunctionImplInstructionLet(
            id=uuid4(),
            function_impl_instruction_id=let_instruction_id,
            name="current_status",
            value_expr={
                "kind": "reference",
                "name": "status",
            },
        )
        let_instruction = FunctionImplInstruction(
            id=let_instruction_id,
            function_impl_id=function_impl.id,
            type=FunctionImplInstructionType.let,
            sequence=0,
            instruction_let=let_payload,
            value_sources=[],
        )
        instructions.append(let_instruction)

        require_instruction_id = uuid4()
        require_payload_id = uuid4()
        current_status_source = FunctionImplValueSource(
            id=uuid4(),
            function_impl_instruction_id=require_instruction_id,
            key="let:current_status:guard",
            kind=FunctionImplValueSourceKind.let_ref,
            source_instruction_let=let_payload,
            source_instruction_let_id=let_payload.id,
        )
        array_primitive_config = build_primitive_config(
            build_code_primitive_type(base_type=CodePrimitiveBaseType.array)
        )
        allowed_values_source = FunctionImplValueSource(
            id=uuid4(),
            function_impl_instruction_id=require_instruction_id,
            key="literal:allowed_statuses",
            kind=FunctionImplValueSourceKind.literal,
        )
        allowed_values_source.source_literal_primitive = (
            FunctionImplValueSourceLiteralPrimitive(
                id=uuid4(),
                function_impl_value_source_id=allowed_values_source.id,
                primitive_config=array_primitive_config,
                primitive_config_id=array_primitive_config.id,
                value={"value": allowed_values},
            )
        )
        require_operands = [
            FunctionImplInstructionRequireOperand(
                id=uuid4(),
                function_impl_instruction_require_id=require_payload_id,
                position=0,
                value_source=current_status_source,
                value_source_id=current_status_source.id,
            ),
            FunctionImplInstructionRequireOperand(
                id=uuid4(),
                function_impl_instruction_require_id=require_payload_id,
                position=1,
                value_source=allowed_values_source,
                value_source_id=allowed_values_source.id,
            ),
        ]
        require_payload = FunctionImplInstructionRequire(
            id=require_payload_id,
            function_impl_instruction_id=require_instruction_id,
            kind=FunctionImplRequireKind.member,
            message="status must be proposed, parked, or blocked",
            operands=require_operands,
        )
        require_instruction = FunctionImplInstruction(
            id=require_instruction_id,
            function_impl_id=function_impl.id,
            type=FunctionImplInstructionType.require,
            sequence=1,
            instruction_require=require_payload,
            value_sources=[current_status_source, allowed_values_source],
        )
        instructions.append(require_instruction)
        set_sequence = 2

    set_instruction_id = uuid4()
    set_source = FunctionImplValueSource(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        key="literal:status",
        kind=FunctionImplValueSourceKind.literal,
    )
    set_source.source_literal_primitive = FunctionImplValueSourceLiteralPrimitive(
        id=uuid4(),
        function_impl_value_source_id=set_source.id,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
        value={"value": target_value},
    )
    set_payload = FunctionImplInstructionSet(
        id=uuid4(),
        function_impl_instruction_id=set_instruction_id,
        target_class_config_attribute_config=target_edge,
        target_class_config_attribute_config_id=target_edge.id,
        value_source=set_source,
        value_source_id=set_source.id,
    )
    set_instruction = FunctionImplInstruction(
        id=set_instruction_id,
        function_impl_id=function_impl.id,
        type=FunctionImplInstructionType.set,
        sequence=set_sequence,
        instruction_set=set_payload,
        value_sources=[set_source],
    )
    instructions.append(set_instruction)
    pre_state = MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=before_hash,
        target_object_id=target_object_id,
        root_object_id=target_object_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )
    return _FunctionImplSelfEnumSetFixture(
        pre_state=pre_state,
        instructions=instructions,
        attribute_id=attribute.id,
        target_enum_option_id=enum_options_by_value[target_value].id,
    )


def _meta_handler_execution_request(
    *,
    expected_graph_hash_pre: str | None = None,
    expected_head_commit_id: UUID | None = None,
    args: JsonArray | None = None,
    kwargs: JsonObject | None = None,
    function_impl: FunctionImpl | None = None,
    target_object_id: UUID | None = None,
    is_constructor: bool = False,
    implementation_policy: MetaGraphImplementationPolicy | None = None,
) -> MetaGraphHandlerExecutionRequest:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key="aware.tests",
        name="mutate",
        function_impl=function_impl,
    )
    index = _meta_graph_commit_index(
        function_config=function_config,
        is_constructor=is_constructor,
    )
    projection_hash = next(iter(index.opg_by_hash.keys()))
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_config.id,
        domain_branch_id=uuid4(),
        domain_projection_hash=projection_hash,
        args=args if args is not None else JsonArray(),
        kwargs=kwargs if kwargs is not None else JsonObject(),
        target_object_id=target_object_id,
        expected_graph_hash_pre=expected_graph_hash_pre,
        expected_head_commit_id=expected_head_commit_id,
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(request)
    index_view = (
        MetaGraphRuntimeIndexView(
            index=cast(MetaGraphCommitIndex, index),
            implementation_policy=implementation_policy,
        )
        if implementation_policy is not None
        else None
    )
    execution_plan = build_meta_graph_execution_plan(
        index=cast(MetaGraphRuntimeIndex, index),
        request=request,
        staged_call=staged_call,
        index_view=index_view,
    )
    return MetaGraphHandlerExecutionRequest(
        request=request,
        staged_call=staged_call,
        execution_plan=execution_plan,
    )


def _meta_pre_state(
    handler_request: MetaGraphHandlerExecutionRequest,
) -> MetaGraphPreState:
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        hash=handler_request.execution_plan.expected_graph_hash_pre,
        class_instances=[],
        class_instance_relationships=[],
    )
    return MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=(
            handler_request.execution_plan.expected_graph_hash_pre or "sha256:test:pre"
        ),
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )


def _meta_pre_state_with_class_instance(
    handler_request: MetaGraphHandlerExecutionRequest,
    *,
    class_instance_id: UUID,
) -> MetaGraphPreState:
    graph_id = handler_request.staged_call.lane_scope.object_instance_graph_id
    class_config_id = next(
        iter(handler_request.execution_plan.index.class_configs_by_id)
    )
    class_config = handler_request.execution_plan.index.class_configs_by_id[
        class_config_id
    ]
    _ensure_test_model_binding(class_config)
    class_instance = ClassInstance.model_construct(
        id=class_instance_id,
        object_instance_graph_id=graph_id,
        class_config_id=class_config_id,
        source_object_id=class_instance_id,
        class_instance_attributes=[],
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=graph_id,
        hash=handler_request.execution_plan.expected_graph_hash_pre,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    return MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=(
            handler_request.execution_plan.expected_graph_hash_pre or "sha256:test:pre"
        ),
        target_object_id=handler_request.execution_plan.target_object_id,
        root_object_id=class_instance_id,
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )


def _ensure_test_model_binding(class_config: ClassConfig) -> None:
    if ORMModelRegistry.get_class_by_class_config_id(class_config.id) is not None:
        return

    class _MetaGraphSyntheticModel(ORMModel):
        pass

    fqn = ORMModelRegistry.register_class_stub(_MetaGraphSyntheticModel)
    _MetaGraphSyntheticModel.bind_class_config(class_config)
    _ = ORMModelRegistry.attach_class_config(fqn, class_config)


def _history_change(change_type: ChangeType) -> Change:
    return Change(
        key=f"test-{change_type.value}",
        created_at=datetime.now(timezone.utc),
        type=change_type,
    )


def _class_instance_change(
    *,
    class_instance_id: UUID,
    change_type: ChangeType,
) -> ClassInstanceChange:
    return ClassInstanceChange(
        class_instance_id=class_instance_id,
        change=_history_change(change_type),
    )


def _object_change(
    *,
    class_changes: tuple[ClassInstanceChange, ...],
    object_instance_graph_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
) -> ObjectInstanceGraphChange:
    return ObjectInstanceGraphChange(
        object_instance_graph_identity_id=object_instance_graph_identity_id or uuid4(),
        object_instance_graph_id=object_instance_graph_id or uuid4(),
        change=_history_change(ChangeType.update),
        type=ObjectInstanceGraphChangeType.object_instance,
        class_instance_changes=list(class_changes),
    )


def _relationship_change(
    *,
    source_class_instance_id: UUID,
    target_class_instance_id: UUID,
) -> ObjectInstanceGraphChange:
    return ObjectInstanceGraphChange(
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
        change=_history_change(ChangeType.update),
        type=ObjectInstanceGraphChangeType.object_instance_relationship,
        class_instance_relationship_changes=[
            ClassInstanceRelationshipChange(
                class_config_relationship_id=uuid4(),
                source_class_instance_id=source_class_instance_id,
                target_class_instance_id=target_class_instance_id,
                change=_history_change(ChangeType.update),
            )
        ],
    )


class _RecordingPreStateProvider:
    def __init__(self, *, result: MetaGraphPreStateProviderResult) -> None:
        self.result = result
        self.requests: list[MetaGraphHandlerExecutionRequest] = []

    async def read_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreStateProviderResult:
        self.requests.append(request)
        return self.result


class _RecordingPreStateMaterializer:
    def __init__(self, *, pre_state: MetaGraphPreState, events: list[str]) -> None:
        self.pre_state = pre_state
        self.events = events
        self.requests: list[MetaGraphHandlerExecutionRequest] = []

    async def materialize_pre_state(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphPreState:
        self.events.append("pre_state")
        self.requests.append(request)
        return self.pre_state


class _RecordingArgumentBinder:
    def __init__(
        self,
        *,
        bound_arguments: MetaGraphBoundArguments,
        events: list[str],
    ) -> None:
        self.bound_arguments = bound_arguments
        self.events = events
        self.calls: list[tuple[MetaGraphHandlerExecutionRequest, MetaGraphPreState]] = (
            []
        )

    async def bind_arguments(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
    ) -> MetaGraphBoundArguments:
        self.events.append("arguments")
        self.calls.append((request, pre_state))
        return self.bound_arguments


class _RecordingImplementationDispatcher:
    def __init__(
        self,
        *,
        result: MetaGraphHandlerDispatchResult,
        events: list[str],
    ) -> None:
        self.result = result
        self.events = events
        self.calls: list[
            tuple[
                MetaGraphHandlerExecutionRequest,
                MetaGraphPreState,
                MetaGraphBoundArguments,
            ]
        ] = []

    async def dispatch_implementation(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        self.events.append("dispatch")
        self.calls.append((request, pre_state, bound_arguments))
        return self.result


class _RecordingAwareFunctionImplRunner:
    def __init__(self, *, result: MetaGraphHandlerDispatchResult) -> None:
        self.result = result
        self.calls: list[
            tuple[
                MetaGraphHandlerExecutionRequest,
                MetaGraphPreState,
                MetaGraphBoundArguments,
            ]
        ] = []

    async def run_function_impl(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        self.calls.append((request, pre_state, bound_arguments))
        return self.result


class _RecordingLanguageHandlerRunner:
    def __init__(self, *, result: MetaGraphHandlerDispatchResult) -> None:
        self.result = result
        self.calls: list[
            tuple[
                MetaGraphHandlerExecutionRequest,
                MetaGraphPreState,
                MetaGraphBoundArguments,
            ]
        ] = []

    async def run_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        self.calls.append((request, pre_state, bound_arguments))
        return self.result


class _RecordingLanguageHandlerImplementation:
    def __init__(self, *, result: MetaGraphLanguageHandlerExecution) -> None:
        self.result = result
        self.calls: list[
            tuple[
                MetaGraphHandlerExecutionRequest,
                MetaGraphPreState,
                MetaGraphBoundArguments,
            ]
        ] = []

    async def execute_language_handler(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphLanguageHandlerExecution:
        self.calls.append((request, pre_state, bound_arguments))
        return self.result


class _RecordingMutationSource:
    def __init__(
        self,
        *,
        result: MetaGraphMutationSet,
        events: list[str] | None = None,
    ) -> None:
        self.result = result
        self.events = events
        self.calls: list[
            tuple[
                MetaGraphHandlerExecutionRequest,
                MetaGraphPreState,
                MetaGraphHandlerDispatchResult,
            ]
        ] = []

    async def collect_mutations(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        dispatch_result: MetaGraphHandlerDispatchResult,
    ) -> MetaGraphMutationSet:
        if self.events is not None:
            self.events.append("mutations")
        self.calls.append((request, pre_state, dispatch_result))
        return self.result


class _RecordingOigMaterializer:
    def __init__(self, *, before_oig: ObjectInstanceGraph) -> None:
        self.before_oig = before_oig
        self.calls: list[SimpleNamespace] = []

    async def get(
        self,
        **kwargs: object,
    ) -> tuple[ObjectInstanceGraph, dict[str, object]]:
        self.calls.append(SimpleNamespace(**kwargs))
        return self.before_oig, {}
