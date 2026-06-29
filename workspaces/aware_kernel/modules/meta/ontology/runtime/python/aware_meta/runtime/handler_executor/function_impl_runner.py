from __future__ import annotations

from collections.abc import Mapping
import importlib
import json
import re
from dataclasses import dataclass, field, replace
from math import isfinite
from types import ModuleType
from time import perf_counter
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.attribute.instance.value.builder import EnumOptionResolver
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.class_.instance.stable_ids import (
    stable_class_instance_relationship_id,
)
from aware_meta.attribute.instance.value.builder import build_attribute_value_tree
from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphBoundArguments,
    MetaGraphExecutionSessionDelta,
    MetaGraphHandlerDispatchResult,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphHandlerExecutionRequest,
    MetaGraphImplementationKind,
    MetaGraphMutationBoundaryStatus,
    MetaGraphMutationSet,
    MetaGraphPreState,
    MetaGraphPreStateIndex,
    MetaGraphResolvedFunctionTarget,
)
from aware_meta.runtime.handler_executor.implementation_dispatch import (
    MetaGraphLanguageHandlerRunner,
)
from aware_meta.runtime.handler_executor.mutation_boundary import (
    MetaGraphMutateSelfOnlyPolicy,
)
from aware_meta.runtime.handler_executor.pre_state import (
    build_meta_graph_pre_state_index,
)
from aware_meta.runtime.handler_executor.session import (
    MetaGraphExecutionSessionDeltaBuilder,
)
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
    parse_meta_default_value,
)
from aware_meta.runtime.oig_value_decoder import decode_oig_attribute_value
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueSourceReadPathRootKind,
    FunctionImplValueSourceKind,
    FunctionImplValueTransformKind,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_instruction_let import (
    FunctionImplInstructionLet,
)
from aware_meta_ontology.function.function_impl_value_source import (
    FunctionImplValueSource,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_orm.models.introspection import MappingModelSource
from aware_orm.registry import ORMModelRegistry


_CONSTRUCTOR_STABLE_ID_BINDINGS_EXPORT = (
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
)
_MISSING = object()


class MetaGraphAwareFunctionImplExecutionError(RuntimeError):
    """Raised when Meta cannot execute a FunctionImpl instruction body safely."""


@dataclass(slots=True)
class _ExecutionState:
    request: MetaGraphHandlerExecutionRequest
    pre_state: MetaGraphPreState
    bound_arguments: MetaGraphBoundArguments
    post_oig: ObjectInstanceGraph
    oig_index: MetaGraphPreStateIndex
    implementation_descriptors_by_id: Mapping[
        UUID,
        MetaGraphFunctionImplementationDescriptor,
    ]
    function_input_edges_by_id: Mapping[UUID, FunctionConfigAttributeConfig]
    function_input_edges_by_function_id: Mapping[
        UUID,
        tuple[FunctionConfigAttributeConfig, ...],
    ]
    function_input_edges_by_attribute_config_id: Mapping[
        UUID,
        Mapping[UUID, FunctionConfigAttributeConfig],
    ]
    let_values_by_id: dict[UUID, JsonValue] = field(default_factory=dict)
    let_values_by_name: dict[str, JsonValue] = field(default_factory=dict)
    enum_option_resolver: EnumOptionResolver | None = None
    constructed_class_instance_ids: list[UUID] = field(default_factory=list)
    constructed_class_instances_by_id: dict[UUID, ClassInstance] = field(
        default_factory=dict
    )
    constructed_class_instances_by_class_and_source_object_id: dict[
        tuple[UUID, UUID],
        ClassInstance,
    ] = field(default_factory=dict)
    constructed_relationships_by_membership: dict[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ] = field(default_factory=dict)
    post_class_instances_by_id: dict[UUID, ClassInstance] | None = None
    post_attributes_by_class_instance_and_config_id: (
        dict[tuple[UUID, UUID], Attribute] | None
    ) = None
    language_handler_runner: MetaGraphLanguageHandlerRunner | None = None
    last_value: JsonValue | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphInstructionBodyFunctionImplRunner:
    """Execute compiler-owned FunctionImpl instruction bodies inside Meta."""

    delta_builder: MetaGraphExecutionSessionDeltaBuilder = field(
        default_factory=MetaGraphExecutionSessionDeltaBuilder,
    )
    language_handler_runner: MetaGraphLanguageHandlerRunner | None = None

    async def run_function_impl(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
        bound_arguments: MetaGraphBoundArguments,
    ) -> MetaGraphHandlerDispatchResult:
        started = perf_counter()
        _validate_runner_inputs(
            request=request,
            pre_state=pre_state,
            bound_arguments=bound_arguments,
        )
        function_impl = _require_function_impl(request)
        post_oig = pre_state.before_oig.model_copy(deep=True)
        state = _build_execution_state(
            request=request,
            pre_state=pre_state,
            bound_arguments=bound_arguments,
            post_oig=post_oig,
            language_handler_runner=self.language_handler_runner,
        )

        await _execute_function_impl_body(function_impl=function_impl, state=state)

        session_delta = self.delta_builder.build_delta_from_post_oig(
            request=request,
            pre_state=pre_state,
            post_oig=post_oig,
            constructed_class_instance_ids=tuple(state.constructed_class_instance_ids),
        )
        elapsed_ms = int((perf_counter() - started) * 1000)
        payload: JsonValue = JsonObject({"rail": "aware_function_impl"})
        if state.last_value is not None:
            payload = JsonObject({"value": state.last_value})
        return MetaGraphHandlerDispatchResult(
            execution_plan=request.execution_plan,
            success=True,
            payload=payload,
            execution_time_ms=elapsed_ms,
            session_delta=session_delta,
        )


def _build_execution_state(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    bound_arguments: MetaGraphBoundArguments,
    post_oig: ObjectInstanceGraph,
    language_handler_runner: MetaGraphLanguageHandlerRunner | None = None,
) -> _ExecutionState:
    oig_index = pre_state.oig_index
    if oig_index is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Aware FunctionImpl runner requires indexed OIG pre-state."
        )
    return _ExecutionState(
        request=request,
        pre_state=pre_state,
        bound_arguments=bound_arguments,
        post_oig=post_oig,
        oig_index=oig_index,
        implementation_descriptors_by_id=(
            request.execution_plan.implementation_descriptors_by_id or {}
        ),
        function_input_edges_by_id=(
            request.execution_plan.function_input_edges_by_id or {}
        ),
        function_input_edges_by_function_id=(
            request.execution_plan.function_input_edges_by_function_id or {}
        ),
        function_input_edges_by_attribute_config_id=(
            request.execution_plan.function_input_edges_by_attribute_config_id or {}
        ),
        enum_option_resolver=_build_runtime_enum_option_resolver(request=request),
        language_handler_runner=language_handler_runner,
    )


def _build_runtime_enum_option_resolver(
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> EnumOptionResolver:
    ocg_resolver: EnumOptionResolver | None = None
    object_config_graph = getattr(request.execution_plan.index, "ocg", None)
    if object_config_graph is not None:
        try:
            ocg_resolver = build_enum_option_resolver(
                object_config_graph=object_config_graph,
            )
        except Exception:
            ocg_resolver = None

    def _resolver(type_descriptor, value):
        try:
            return default_meta_enum_option_resolver(type_descriptor, value)
        except Exception as default_error:
            if ocg_resolver is not None:
                return ocg_resolver(type_descriptor, value)
            raise default_error

    return _resolver


def _validate_runner_inputs(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    bound_arguments: MetaGraphBoundArguments,
) -> None:
    execution_plan = request.execution_plan
    if pre_state.execution_plan is not execution_plan:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Aware FunctionImpl runner requires pre-state from the same "
            "execution plan."
        )
    if bound_arguments.execution_plan is not execution_plan:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Aware FunctionImpl runner requires bound arguments from the same "
            "execution plan."
        )


def _require_function_impl(
    request: MetaGraphHandlerExecutionRequest,
) -> FunctionImpl:
    function_config = request.execution_plan.implementation.function_config
    function_impl = function_config.function_impl
    if function_impl is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Aware FunctionImpl runner requires FunctionConfig.function_impl."
        )
    function_impl_kind = _function_impl_kind(function_impl)
    if function_impl_kind is not FunctionImplKind.instruction_body:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Aware FunctionImpl runner only supports instruction_body. "
            f"function_impl_kind={function_impl_kind.value}"
        )
    return function_impl


async def _execute_function_impl_body(
    *,
    function_impl: FunctionImpl,
    state: _ExecutionState,
) -> None:
    for instruction in sorted(
        function_impl.instructions,
        key=lambda item: item.sequence,
    ):
        await _execute_instruction(instruction=instruction, state=state)


async def _execute_instruction(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_type = _instruction_type(instruction)
    if instruction_type is FunctionImplInstructionType.let:
        _execute_let(instruction=instruction, state=state)
        return
    if instruction_type is FunctionImplInstructionType.require:
        _execute_require(instruction=instruction, state=state)
        return
    if instruction_type is FunctionImplInstructionType.set:
        _execute_set(instruction=instruction, state=state)
        return
    if instruction_type is FunctionImplInstructionType.invoke:
        await _execute_invoke(instruction=instruction, state=state)
        return
    if instruction_type is FunctionImplInstructionType.construct:
        _execute_construct(instruction=instruction, state=state)
        return
    if instruction_type is FunctionImplInstructionType.delete:
        _execute_delete(instruction=instruction, state=state)
        return
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported Aware FunctionImpl instruction. "
        f"instruction_type={instruction_type.value} "
        f"instruction_sequence={instruction.sequence}"
    )


def _execute_let(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_let = instruction.instruction_let
    if instruction_let is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl let instruction is missing instruction_let payload. "
            f"instruction_sequence={instruction.sequence}"
        )
    value_sources = tuple(instruction.value_sources)
    if len(value_sources) == 1:
        value = _evaluate_value_source(value_sources[0], state=state)
    elif len(value_sources) == 0:
        value = _evaluate_let_value_expr(instruction_let, state=state)
    else:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl let instruction must declare zero or one value source. "
            f"instruction_sequence={instruction.sequence}"
        )
    state.let_values_by_id[instruction_let.id] = value
    state.let_values_by_name[instruction_let.name] = value


def _evaluate_let_value_expr(
    instruction_let: FunctionImplInstructionLet,
    *,
    state: _ExecutionState,
) -> JsonValue:
    expression = instruction_let.value_expr
    if set(expression) == {"literal"}:
        return _copy_json_value(expression["literal"], path="let.literal")
    if set(expression) == {"input"}:
        input_name = expression["input"]
        if not isinstance(input_name, str):
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl let input expression must name a string input."
            )
        return _read_named_input(input_name, state=state)
    kind = expression.get("kind")
    if kind == "literal":
        return _copy_json_value(expression.get("value"), path="let.literal")
    if kind == "reference":
        input_name = expression.get("name")
        if not isinstance(input_name, str) or not input_name.strip():
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl let reference expression must name a non-empty input "
                "or target attribute."
            )
        return _read_named_input(input_name.strip(), state=state)
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl let expression is not supported. "
        f"let_name={instruction_let.name}"
    )


def _execute_require(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_require = instruction.instruction_require
    if instruction_require is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl require instruction is missing instruction_require "
            f"payload. instruction_sequence={instruction.sequence}"
        )
    operands = [
        _evaluate_value_source(operand.value_source, state=state)
        for operand in sorted(
            instruction_require.operands,
            key=lambda item: item.position,
        )
    ]
    if not _require_condition_holds(
        kind=_require_kind(instruction_require.kind),
        operands=operands,
        compare_operator=instruction_require.compare_operator,
        expected_count=instruction_require.expected_count,
    ):
        message = (
            instruction_require.message
            or "Aware FunctionImpl require instruction failed."
        )
        raise MetaGraphAwareFunctionImplExecutionError(
            f"{message} instruction_sequence={instruction.sequence}"
        )


def _execute_set(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_set = instruction.instruction_set
    if instruction_set is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set instruction is missing instruction_set payload. "
            f"instruction_sequence={instruction.sequence}"
        )
    target_edge = instruction_set.target_class_config_attribute_config
    target_attribute_config = _target_attribute_config(
        target_edge,
        request=state.request,
    )
    target_instance = _target_class_instance_for_mutation(state)
    if target_edge.class_config_id != target_instance.class_config_id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set target attribute does not belong to invoked "
            "ClassInstance class_config."
        )
    attribute = _target_attribute_or_none(
        state=state,
        target_instance=target_instance,
        attribute_config_id=target_attribute_config.id,
    )
    type_descriptor = target_attribute_config.type_descriptor
    if type_descriptor is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set requires AttributeConfig.type_descriptor."
        )
    value = _evaluate_value_source(instruction_set.value_source, state=state)
    if attribute is None or attribute.value_root is None:
        built_attribute = build_attribute(
            owner_key=target_instance.id,
            attribute_config=target_attribute_config,
            value=value,
            class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
            enum_option_resolver=state.enum_option_resolver,
        )
        if attribute is None:
            attribute = built_attribute
            link_attribute(target_instance, attribute)
            if state.post_attributes_by_class_instance_and_config_id is not None:
                state.post_attributes_by_class_instance_and_config_id[
                    (target_instance.id, target_attribute_config.id)
                ] = attribute
        else:
            attribute.value_root = built_attribute.value_root
            attribute.value_root_id = built_attribute.value_root_id
        return
    value_root = build_attribute_value_tree(
        type_descriptor=type_descriptor,
        value=value,
        stable_root_id=attribute.value_root.id,
        class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        enum_option_resolver=state.enum_option_resolver,
    )
    attribute.value_root = value_root
    attribute.value_root_id = value_root.id


def _execute_delete(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_delete = instruction.instruction_delete
    if instruction_delete is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl delete instruction is missing instruction_delete "
            f"payload. instruction_sequence={instruction.sequence}"
        )
    target_kind = _delete_target_kind_value(instruction_delete.target_kind)
    if target_kind != "self":
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl delete instruction only supports target_kind=self. "
            f"instruction_sequence={instruction.sequence} "
            f"target_kind={target_kind}"
        )

    target_instance = _target_class_instance_for_mutation(state)
    delete_ids = {
        target_instance.id,
        *_descendant_ids_in_oig(
            oig=state.post_oig,
            target_class_instance_id=target_instance.id,
        ),
    }
    root_ids = {
        item
        for item in (
            state.post_oig.root_class_instance_id,
            getattr(state.post_oig.root_class_instance, "id", None),
        )
        if item is not None
    }
    if delete_ids.intersection(root_ids):
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl delete self cannot delete the OIG root ClassInstance "
            "in v0."
        )

    post_instances_by_id = _post_class_instances_by_id(state)
    missing_ids = delete_ids.difference(post_instances_by_id)
    if missing_ids:
        missing = ", ".join(sorted(str(item) for item in missing_ids))
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl delete self closure references missing ClassInstance "
            f"id(s): {missing}"
        )

    external_incoming = [
        relationship
        for relationship in state.post_oig.class_instance_relationships
        if relationship.target_class_instance_id in delete_ids
        and relationship.source_class_instance_id not in delete_ids
    ]
    if external_incoming:
        relationship = sorted(
            external_incoming,
            key=lambda item: (
                str(item.source_class_instance_id),
                str(item.target_class_instance_id),
                str(item.class_config_relationship_id),
            ),
        )[0]
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl delete self cannot remove a ClassInstance with an "
            "incoming relationship from outside the self-owned delete closure. "
            f"source_class_instance_id={relationship.source_class_instance_id} "
            f"target_class_instance_id={relationship.target_class_instance_id}"
        )

    state.post_oig.class_instances = [
        class_instance
        for class_instance in state.post_oig.class_instances
        if class_instance.id not in delete_ids
    ]
    state.post_oig.class_instance_relationships = [
        relationship
        for relationship in state.post_oig.class_instance_relationships
        if relationship.source_class_instance_id not in delete_ids
        and relationship.target_class_instance_id not in delete_ids
    ]
    state.constructed_class_instance_ids[:] = [
        class_instance_id
        for class_instance_id in state.constructed_class_instance_ids
        if class_instance_id not in delete_ids
    ]
    for class_instance_id in delete_ids:
        state.constructed_class_instances_by_id.pop(class_instance_id, None)
    for key, class_instance in list(
        state.constructed_class_instances_by_class_and_source_object_id.items()
    ):
        if class_instance.id in delete_ids:
            state.constructed_class_instances_by_class_and_source_object_id.pop(
                key,
                None,
            )
    state.constructed_relationships_by_membership = {
        key: relationship
        for key, relationship in state.constructed_relationships_by_membership.items()
        if relationship.source_class_instance_id not in delete_ids
        and relationship.target_class_instance_id not in delete_ids
    }
    state.post_class_instances_by_id = None
    state.post_attributes_by_class_instance_and_config_id = None


def _execute_construct(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_construct = instruction.instruction_construct
    if instruction_construct is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct instruction is missing instruction_construct "
            f"payload. instruction_sequence={instruction.sequence}"
        )
    target_class_config = _construct_instruction_target_class_config(
        instruction_construct,
        state=state,
    )
    current_owner_target = _current_owner_construct_target(
        target_class_config=target_class_config,
        state=state,
    )
    if current_owner_target is not None:
        target_function_config = state.request.execution_plan.implementation.function_config
    else:
        target_function_config = _single_constructor_function_config(
            target_class_config=target_class_config,
            state=state,
        )
    target_values = _construct_instruction_target_values(
        instruction_construct=instruction_construct,
        target_class_config=target_class_config,
        target_function_config=target_function_config,
        state=state,
        allow_missing_required=bool(current_owner_target is not None),
    )
    if current_owner_target is not None:
        target_class_instance = current_owner_target
        target_object_id = current_owner_target.source_object_id
        if target_object_id is None:
            target_object_id = current_owner_target.id
    else:
        target_object_id = _resolve_constructor_object_id(
            target_class_config=target_class_config,
            target_function_config=target_function_config,
            target_values=target_values,
        )
        target_class_instance = _find_class_instance_by_source(
            state=state,
            class_config_id=target_class_config.id,
            source_object_id=target_object_id,
        )
    built_target_class_instance = build_class_instance(
        object_instance_graph_id=state.post_oig.id,
        class_config=target_class_config,
        class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        source=MappingModelSource(
            id=target_object_id,
            values=target_values,
            class_config_id=target_class_config.id,
        ),
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=default_meta_class_instance_resolver,
        include_relationship_attribute_config_ids=(
            _explicit_relationship_attribute_config_ids(
                class_config=target_class_config,
                values=target_values,
            )
        ),
    )
    if target_class_instance is None:
        target_class_instance = built_target_class_instance
        state.post_oig.class_instances.append(target_class_instance)
        state.constructed_class_instance_ids.append(target_class_instance.id)
    else:
        target_class_instance.class_instance_attributes.clear()
        target_class_instance.class_instance_attributes.extend(
            built_target_class_instance.class_instance_attributes
        )

    state.constructed_class_instances_by_id[target_class_instance.id] = (
        target_class_instance
    )
    state.constructed_class_instances_by_class_and_source_object_id[
        (target_class_config.id, target_object_id)
    ] = target_class_instance
    if state.post_class_instances_by_id is not None:
        state.post_class_instances_by_id[target_class_instance.id] = (
            target_class_instance
        )
    if state.post_attributes_by_class_instance_and_config_id is not None:
        for attribute in target_class_instance.attributes:
            state.post_attributes_by_class_instance_and_config_id[
                (target_class_instance.id, attribute.attribute_config_id)
            ] = attribute

    state.last_value = _json_object_value(
        {
            "id": target_object_id,
            **target_values,
        },
        path=f"construct[{instruction.sequence}].value",
    )


def _construct_instruction_target_class_config(
    instruction_construct: object,
    *,
    state: _ExecutionState,
) -> ClassConfig:
    target_class_config = getattr(instruction_construct, "target_class_config", None)
    if isinstance(target_class_config, ClassConfig):
        return target_class_config
    target_class_config_id = getattr(
        instruction_construct,
        "target_class_config_id",
        None,
    )
    if target_class_config_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct instruction requires target_class_config_id."
        )
    resolved = state.request.execution_plan.index.class_configs_by_id.get(
        target_class_config_id,
    )
    if resolved is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct target ClassConfig is not present in the "
            "Meta runtime index. "
            f"target_class_config_id={target_class_config_id}"
        )
    return resolved


def _single_constructor_function_config(
    *,
    target_class_config: ClassConfig,
    state: _ExecutionState,
) -> FunctionConfig:
    constructors: list[FunctionConfig] = []
    for edge in target_class_config.class_config_function_configs:
        if not bool(edge.is_constructor):
            continue
        function_config = edge.function_config
        if function_config is None:
            descriptor = state.implementation_descriptors_by_id.get(
                edge.function_config_id,
            )
            if descriptor is not None:
                function_config = descriptor.function_config
        if function_config is not None:
            constructors.append(function_config)
    if not constructors:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct target class has no constructor. "
            f"class_config_id={target_class_config.id}"
        )
    if len(constructors) != 1:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct target class has ambiguous constructors. "
            f"class_config_id={target_class_config.id} matches={len(constructors)}"
        )
    return constructors[0]


def _construct_instruction_target_values(
    *,
    instruction_construct: object,
    target_class_config: ClassConfig,
    target_function_config: FunctionConfig,
    state: _ExecutionState,
    allow_missing_required: bool = False,
) -> dict[str, object]:
    target_values: dict[str, object] = {}
    assigned_names: set[str] = set()
    assignments = sorted(
        getattr(instruction_construct, "assignments", ()),
        key=lambda item: (
            item.position if item.position is not None else 999999,
            str(item.id),
        ),
    )
    for assignment in assignments:
        target_link = _construct_assignment_target_link(
            assignment,
            target_class_config=target_class_config,
            state=state,
        )
        attr_cfg = target_link.attribute_config
        if attr_cfg is None or not (attr_cfg.name or "").strip():
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct assignment target requires non-empty "
                "AttributeConfig.name."
            )
        attr_name = attr_cfg.name.strip()
        if attr_name in assigned_names:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct assignment target names must be unique. "
                f"attribute={attr_name!r}"
            )
        value_source = assignment.value_source
        if value_source is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct assignment requires value_source payload."
            )
        target_values[attr_name] = _evaluate_value_source(value_source, state=state)
        assigned_names.add(attr_name)

    for input_edge in _constructor_input_edges(
        target_function_config=target_function_config,
        state=state,
    ):
        input_name = _function_input_name(input_edge)
        if input_name in target_values:
            continue
        default_value = input_edge.attribute_config.default_value
        if default_value is not None:
            target_values[input_name] = parse_meta_default_value(default_value)
            continue
        if bool(input_edge.attribute_config.is_required):
            if allow_missing_required:
                continue
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct missing required constructor input. "
                f"input_name={input_name}"
            )
    return target_values


def _current_owner_construct_target(
    *,
    target_class_config: ClassConfig,
    state: _ExecutionState,
) -> ClassInstance | None:
    descriptor = state.request.execution_plan.implementation
    if not descriptor.is_constructor:
        return None
    owner_class_config = descriptor.owner_class_config
    if owner_class_config is None or owner_class_config.id != target_class_config.id:
        return None
    return _target_class_instance_for_mutation(state)


def _construct_assignment_target_link(
    assignment: object,
    *,
    target_class_config: ClassConfig,
    state: _ExecutionState,
) -> ClassConfigAttributeConfig:
    target_link = getattr(
        assignment,
        "target_class_config_attribute_config",
        None,
    )
    if isinstance(target_link, ClassConfigAttributeConfig):
        resolved = target_link
    else:
        _ = state
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct assignment requires embedded target "
            "ClassConfigAttributeConfig payload."
        )
    if resolved.class_config_id != target_class_config.id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct assignment target class mismatch. "
            f"target_class_config_id={target_class_config.id} "
            f"assignment_class_config_id={resolved.class_config_id}"
        )
    return resolved


def _explicit_relationship_attribute_config_ids(
    *,
    class_config: ClassConfig,
    values: Mapping[str, object],
) -> set[UUID]:
    attribute_names_by_id = {
        link.attribute_config_id: link.attribute_config.name
        for link in class_config.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config_id is not None
        and (link.attribute_config.name or "").strip()
    }
    included: set[UUID] = set()
    for relationship in class_config.class_config_relationships or []:
        for rel_attr in relationship.class_config_relationship_attributes or []:
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            attr_name = attribute_names_by_id.get(attr_id)
            if not attr_name:
                continue
            if values.get(attr_name) is not None:
                included.add(attr_id)
    return included


def _constructor_input_edges(
    *,
    target_function_config: FunctionConfig,
    state: _ExecutionState,
) -> tuple[FunctionConfigAttributeConfig, ...]:
    indexed = state.function_input_edges_by_function_id.get(target_function_config.id)
    if indexed is not None:
        return tuple(indexed)
    edges = [
        edge
        for edge in target_function_config.function_config_attribute_configs
        if edge.type == FunctionAttributeType.input
    ]
    return tuple(sorted(edges, key=lambda edge: int(edge.position)))


async def _execute_invoke(
    *,
    instruction: FunctionImplInstruction,
    state: _ExecutionState,
) -> None:
    instruction_invoke = instruction.instruction_invoke
    if instruction_invoke is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl invoke instruction is missing instruction_invoke "
            f"payload. instruction_sequence={instruction.sequence}"
        )
    invoke_kind = _invoke_kind(instruction_invoke)
    if invoke_kind is FunctionImplInvokeKind.construct:
        await _execute_construct_invoke(
            instruction=instruction,
            instruction_invoke=instruction_invoke,
            state=state,
        )
        return
    if invoke_kind is FunctionImplInvokeKind.call:
        await _execute_call_invoke(
            instruction=instruction,
            instruction_invoke=instruction_invoke,
            state=state,
        )
        return
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl invoke instruction kind is unsupported. "
        f"instruction_sequence={instruction.sequence} "
        f"invoke_kind={invoke_kind.value}"
    )


async def _execute_construct_invoke(
    *,
    instruction: FunctionImplInstruction,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> None:
    source_instance = _target_class_instance_for_read(state)
    relationship: ClassConfigRelationship | None = None
    link_constructed_relationship_target = False
    if (
        instruction_invoke.class_config_relationship_id is not None
        or instruction_invoke.class_config_relationship is not None
    ):
        relationship = _construct_relationship(
            instruction_invoke,
            request=state.request,
        )
        relationship_target_class_config = _construct_target_class_config(
            relationship=relationship,
            request=state.request,
        )
        target_function_descriptor = _construct_target_function_descriptor(
            instruction_invoke=instruction_invoke,
            state=state,
        )
        descriptor_owner_class = target_function_descriptor.owner_class_config
        if descriptor_owner_class is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke target FunctionConfig has no owner ClassConfig. "
                f"function_config_id={target_function_descriptor.function_config.id}"
            )
        association_class_config = _relationship_association_class_config(
            relationship=relationship,
            request=state.request,
        )
        if descriptor_owner_class.id == relationship_target_class_config.id:
            target_class_config = relationship_target_class_config
            _validate_construct_relationship(
                relationship=relationship,
                source_instance=source_instance,
                target_class_config=target_class_config,
            )
            link_constructed_relationship_target = True
        elif (
            association_class_config is not None
            and descriptor_owner_class.id == association_class_config.id
        ):
            if relationship.class_config_id != source_instance.class_config_id:
                raise MetaGraphAwareFunctionImplExecutionError(
                    "FunctionImpl construct association relationship source does not match "
                    "the invoked ClassInstance class_config."
                )
            target_class_config = association_class_config
        else:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke target FunctionConfig is not declared on "
                "the relationship target or association ClassConfig. "
                f"target_class_config_id={relationship_target_class_config.id} "
                f"association_class_config_id={getattr(association_class_config, 'id', None)} "
                f"owner_class_config_id={descriptor_owner_class.id} "
                f"function_config_id={target_function_descriptor.function_config.id}"
            )
        target_function_config = target_function_descriptor.function_config
    else:
        target_function_config = _standalone_construct_target_function_config(
            instruction_invoke=instruction_invoke,
            state=state,
        )
        target_class_config = _standalone_construct_target_class_config(
            target_function_config=target_function_config,
            state=state,
        )
    target_values = _construct_target_values(
        instruction_invoke=instruction_invoke,
        target_function_config=target_function_config,
        source_instance=source_instance,
        state=state,
    )
    target_object_id = _resolve_constructor_object_id(
        target_class_config=target_class_config,
        target_function_config=target_function_config,
        target_values=target_values,
    )
    target_class_instance = _find_class_instance_by_source(
        state=state,
        class_config_id=target_class_config.id,
        source_object_id=target_object_id,
    )
    if target_class_instance is None:
        target_class_instance = build_class_instance(
            object_instance_graph_id=state.post_oig.id,
            class_config=target_class_config,
            class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
            source=MappingModelSource(
                id=target_object_id,
                values=target_values,
                class_config_id=target_class_config.id,
            ),
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=default_meta_class_instance_resolver,
        )
        state.post_oig.class_instances.append(target_class_instance)
        state.constructed_class_instance_ids.append(target_class_instance.id)
        state.constructed_class_instances_by_id[target_class_instance.id] = (
            target_class_instance
        )
        state.constructed_class_instances_by_class_and_source_object_id[
            (target_class_config.id, target_object_id)
        ] = target_class_instance
        if state.post_class_instances_by_id is not None:
            state.post_class_instances_by_id[target_class_instance.id] = (
                target_class_instance
            )
        if state.post_attributes_by_class_instance_and_config_id is not None:
            for attribute in target_class_instance.attributes:
                state.post_attributes_by_class_instance_and_config_id[
                    (target_class_instance.id, attribute.attribute_config_id)
                ] = attribute

    if relationship is not None and link_constructed_relationship_target:
        _ensure_class_instance_relationship(
            state=state,
            relationship=relationship,
            source_instance=source_instance,
            target_instance=target_class_instance,
        )
    await _execute_constructed_target_body(
        target_function_config=target_function_config,
        target_instance=target_class_instance,
        target_values=target_values,
        state=state,
    )
    constructed_value = _json_object_value(
        {
            "id": target_object_id,
            **target_values,
        },
        path=f"invoke[{instruction.sequence}].value",
    )
    state.last_value = constructed_value
    _capture_construct_return(
        instruction_sequence=instruction.sequence,
        instruction_invoke=instruction_invoke,
        return_value=constructed_value,
        state=state,
    )


async def _execute_constructed_target_body(
    *,
    target_function_config: FunctionConfig,
    target_instance: ClassInstance,
    target_values: Mapping[str, object],
    state: _ExecutionState,
) -> None:
    descriptor = state.implementation_descriptors_by_id.get(target_function_config.id)
    if descriptor is None:
        return
    if descriptor.kind is not MetaGraphImplementationKind.aware_function_impl:
        return
    function_impl = descriptor.function_config.function_impl
    if function_impl is None or not function_impl.instructions:
        return
    call_keyword = JsonObject(
        {
            str(key): _json_like_value(value, path=f"construct.body.{key}")
            for key, value in target_values.items()
        }
    )
    nested_request = _nested_call_request(
        state=state,
        descriptor=descriptor,
        target_instance=target_instance,
        call_keyword=call_keyword,
    )
    nested_pre_state = _nested_call_pre_state(
        state=state,
        nested_request=nested_request,
        before_oig=state.post_oig.model_copy(deep=True),
        target_instance=target_instance,
    )
    nested_bound_arguments = MetaGraphBoundArguments(
        execution_plan=nested_request.execution_plan,
        positional=JsonArray(),
        keyword=call_keyword,
    )
    await _execute_native_nested_call(
        state=state,
        nested_request=nested_request,
        nested_pre_state=nested_pre_state,
        nested_bound_arguments=nested_bound_arguments,
        descriptor=descriptor,
    )

async def _execute_call_invoke(
    *,
    instruction: FunctionImplInstruction,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> None:
    source_instance = _target_class_instance_for_read(state)
    descriptor = _call_target_descriptor(
        instruction_invoke=instruction_invoke,
        state=state,
    )
    target_instance = _call_target_instance(
        instruction_invoke=instruction_invoke,
        descriptor=descriptor,
        source_instance=source_instance,
        state=state,
    )
    call_keyword = _call_target_keyword_arguments(
        instruction_invoke=instruction_invoke,
        target_function_config=descriptor.function_config,
        source_instance=source_instance,
        state=state,
    )
    nested_request = _nested_call_request(
        state=state,
        descriptor=descriptor,
        target_instance=target_instance,
        call_keyword=call_keyword,
    )
    nested_pre_state = _nested_call_pre_state(
        state=state,
        nested_request=nested_request,
        before_oig=state.post_oig.model_copy(deep=True),
        target_instance=target_instance,
    )
    nested_bound_arguments = MetaGraphBoundArguments(
        execution_plan=nested_request.execution_plan,
        positional=JsonArray(),
        keyword=call_keyword,
    )

    if descriptor.kind is MetaGraphImplementationKind.aware_function_impl:
        return_value = await _execute_native_nested_call(
            state=state,
            nested_request=nested_request,
            nested_pre_state=nested_pre_state,
            nested_bound_arguments=nested_bound_arguments,
            descriptor=descriptor,
        )
    elif descriptor.kind is MetaGraphImplementationKind.language_handler:
        return_value = await _execute_language_handler_nested_call(
            state=state,
            nested_request=nested_request,
            nested_pre_state=nested_pre_state,
            nested_bound_arguments=nested_bound_arguments,
        )
    else:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target implementation kind is unsupported. "
            f"instruction_sequence={instruction.sequence} "
            f"implementation_kind={descriptor.kind.value}"
        )

    _capture_call_return(
        instruction_sequence=instruction.sequence,
        instruction_invoke=instruction_invoke,
        return_value=return_value,
        state=state,
    )


async def _execute_native_nested_call(
    *,
    state: _ExecutionState,
    nested_request: MetaGraphHandlerExecutionRequest,
    nested_pre_state: MetaGraphPreState,
    nested_bound_arguments: MetaGraphBoundArguments,
    descriptor: MetaGraphFunctionImplementationDescriptor,
) -> JsonValue | None:
    function_impl = descriptor.function_config.function_impl
    if function_impl is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target is native but has no FunctionImpl. "
            f"function_config_id={descriptor.function_config.id}"
        )
    nested_state = _build_execution_state(
        request=nested_request,
        pre_state=nested_pre_state,
        bound_arguments=nested_bound_arguments,
        post_oig=state.post_oig,
        language_handler_runner=state.language_handler_runner,
    )
    _share_nested_mutation_state(parent_state=state, nested_state=nested_state)
    await _execute_function_impl_body(
        function_impl=function_impl,
        state=nested_state,
    )
    nested_delta = MetaGraphExecutionSessionDeltaBuilder().build_delta_from_post_oig(
        request=nested_request,
        pre_state=nested_pre_state,
        post_oig=state.post_oig,
        constructed_class_instance_ids=tuple(
            state.constructed_class_instance_ids,
        ),
    )
    await _validate_nested_call_delta(
        nested_request=nested_request,
        session_delta=nested_delta,
    )
    return nested_state.last_value


async def _execute_language_handler_nested_call(
    *,
    state: _ExecutionState,
    nested_request: MetaGraphHandlerExecutionRequest,
    nested_pre_state: MetaGraphPreState,
    nested_bound_arguments: MetaGraphBoundArguments,
) -> JsonValue | None:
    if state.language_handler_runner is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target is language-handler backed, but "
            "no Meta language handler runner is wired."
        )
    dispatch_result = await state.language_handler_runner.run_language_handler(
        nested_request,
        nested_pre_state,
        nested_bound_arguments,
    )
    if not dispatch_result.success:
        message = dispatch_result.error_message or "nested language handler failed"
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke language-handler target failed. "
            f"function_config_id={nested_request.execution_plan.implementation.function_config.id} "
            f"error={message}"
        )
    session_delta = dispatch_result.session_delta
    if session_delta is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke language-handler target returned no "
            "execution-session delta."
        )
    _validate_nested_session_delta_plan(
        nested_request=nested_request,
        session_delta=session_delta,
    )
    scoped_delta = _filter_nested_session_delta_to_target_scope(
        session_delta=session_delta,
    )
    _apply_nested_session_delta(state=state, session_delta=scoped_delta)
    return _dispatch_payload_return_value(dispatch_result.payload)


def _call_target_descriptor(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> MetaGraphFunctionImplementationDescriptor:
    target_function_id = instruction_invoke.target_function_config_id
    if target_function_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke requires target_function_config_id."
        )
    descriptor = state.implementation_descriptors_by_id.get(target_function_id)
    if descriptor is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target FunctionConfig is not indexed on "
            "the execution plan. "
            f"function_config_id={target_function_id}"
        )
    return descriptor


def _call_target_instance(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    descriptor: MetaGraphFunctionImplementationDescriptor,
    source_instance: ClassInstance,
    state: _ExecutionState,
) -> ClassInstance:
    relationship = _optional_call_relationship(
        instruction_invoke,
        request=state.request,
    )
    if relationship is None:
        target_instance = source_instance
    else:
        _validate_call_relationship(
            relationship=relationship,
            source_instance=source_instance,
            descriptor=descriptor,
        )
        target_instance = _relationship_target_instance(
            relationship=relationship,
            source_instance=source_instance,
            state=state,
        )
    owner_class_config = descriptor.owner_class_config
    if owner_class_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target descriptor is missing owner "
            "ClassConfig."
        )
    if target_instance.class_config_id != owner_class_config.id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke target object class does not match target "
            "FunctionConfig owner. "
            f"target_class_config_id={target_instance.class_config_id} "
            f"owner_class_config_id={owner_class_config.id}"
        )
    return target_instance


def _optional_call_relationship(
    instruction_invoke: FunctionImplInstructionInvoke,
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> ClassConfigRelationship | None:
    relationship = instruction_invoke.class_config_relationship
    if relationship is not None:
        return relationship
    relationship_id = instruction_invoke.class_config_relationship_id
    if relationship_id is None:
        return None
    relationship = request.execution_plan.index.relationships_by_id.get(
        relationship_id,
    )
    if relationship is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke relationship is not present in the Meta "
            "runtime index. "
            f"class_config_relationship_id={relationship_id}"
        )
    return relationship


def _validate_call_relationship(
    *,
    relationship: ClassConfigRelationship,
    source_instance: ClassInstance,
    descriptor: MetaGraphFunctionImplementationDescriptor,
) -> None:
    if relationship.class_config_id != source_instance.class_config_id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call relationship source does not match the invoked "
            "ClassInstance class_config."
        )
    owner_class_config = descriptor.owner_class_config
    if owner_class_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call target descriptor is missing owner ClassConfig."
        )
    if relationship.target_class_config_id != owner_class_config.id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call target FunctionConfig is not declared on the "
            "relationship target ClassConfig. "
            f"relationship_target_class_config_id={relationship.target_class_config_id} "
            f"owner_class_config_id={owner_class_config.id} "
            f"function_config_id={descriptor.function_config.id}"
        )


def _relationship_target_instance(
    *,
    relationship: ClassConfigRelationship,
    source_instance: ClassInstance,
    state: _ExecutionState,
) -> ClassInstance:
    matches = [
        item
        for item in state.post_oig.class_instance_relationships
        if item.class_config_relationship_id == relationship.id
        and item.source_class_instance_id == source_instance.id
    ]
    if not matches:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call relationship target is not present in the "
            "current OIG. "
            f"class_config_relationship_id={relationship.id} "
            f"source_class_instance_id={source_instance.id}"
        )
    if len(matches) != 1:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call relationship target is ambiguous in v0. "
            f"class_config_relationship_id={relationship.id} "
            f"source_class_instance_id={source_instance.id} "
            f"match_count={len(matches)}"
        )
    target_id = matches[0].target_class_instance_id
    target_instance = _post_class_instances_by_id(state).get(target_id)
    if target_instance is not None:
        return target_instance
    target_instance = state.oig_index.class_instances_by_id.get(target_id)
    if target_instance is not None:
        return target_instance
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl call relationship target ClassInstance is missing. "
        f"target_class_instance_id={target_id}"
    )


def _call_target_keyword_arguments(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    target_function_config: FunctionConfig,
    source_instance: ClassInstance,
    state: _ExecutionState,
) -> JsonObject:
    input_edges = _call_input_edges(
        target_function_config=target_function_config,
        state=state,
    )
    inputs_by_attribute_config_id = _call_inputs_by_attribute_config_id(
        target_function_config=target_function_config,
        input_edges=input_edges,
        state=state,
    )
    values_by_input_id: dict[UUID, object] = {}

    for binding in instruction_invoke.attribute_configs:
        target_input = inputs_by_attribute_config_id.get(
            binding.attribute_config_id,
        )
        if target_input is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl call invoke binding does not target a function "
                "input. "
                f"attribute_config_id={binding.attribute_config_id}"
            )
        if target_input.id in values_by_input_id:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl call invoke has duplicate binding for function "
                "input. "
                f"function_config_attribute_config_id={target_input.id}"
            )
        values_by_input_id[target_input.id] = _evaluate_invoke_value_expr(
            binding.value_expr,
            source_instance=source_instance,
            state=state,
            path=f"call.{target_input.name}",
        )

    target_values = JsonObject()
    for input_edge in input_edges:
        name = _function_input_name(input_edge)
        if input_edge.id in values_by_input_id:
            target_values[name] = _json_like_value(
                values_by_input_id[input_edge.id],
                path=f"call.{name}",
            )
            continue
        default_value = input_edge.attribute_config.default_value
        if default_value is not None:
            target_values[name] = _json_like_value(
                parse_meta_default_value(default_value),
                path=f"call.{name}",
            )
            continue
        if bool(input_edge.attribute_config.is_required):
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl call invoke missing required function input. "
                f"input_name={name}"
            )
    return target_values


def _call_input_edges(
    *,
    target_function_config: FunctionConfig,
    state: _ExecutionState,
) -> tuple[FunctionConfigAttributeConfig, ...]:
    indexed = state.function_input_edges_by_function_id.get(target_function_config.id)
    if indexed is not None:
        return tuple(indexed)
    return tuple(
        sorted(
            (
                edge
                for edge in target_function_config.function_config_attribute_configs
                if edge.type == FunctionAttributeType.input
            ),
            key=lambda edge: int(edge.position),
        )
    )


def _call_inputs_by_attribute_config_id(
    *,
    target_function_config: FunctionConfig,
    input_edges: tuple[FunctionConfigAttributeConfig, ...],
    state: _ExecutionState,
) -> Mapping[UUID, FunctionConfigAttributeConfig]:
    indexed = state.function_input_edges_by_attribute_config_id.get(
        target_function_config.id,
    )
    if indexed is not None:
        return indexed
    return {edge.attribute_config_id: edge for edge in input_edges}


def _nested_call_request(
    *,
    state: _ExecutionState,
    descriptor: MetaGraphFunctionImplementationDescriptor,
    target_instance: ClassInstance,
    call_keyword: JsonObject,
) -> MetaGraphHandlerExecutionRequest:
    operation_label = (descriptor.function_config.name or "call").strip() or "call"
    nested_resolved_target = MetaGraphResolvedFunctionTarget(
        function_config=descriptor.function_config,
        operation_label=operation_label,
    )
    nested_staged_call = replace(
        state.request.staged_call,
        resolved_target=nested_resolved_target,
    )
    nested_execution_plan = replace(
        state.request.execution_plan,
        staged_call=nested_staged_call,
        implementation=descriptor,
        target_object_id=target_instance.id,
    )
    nested_input = replace(
        state.request.request,
        function_id=descriptor.function_config.id,
        target_object_id=target_instance.source_object_id,
        args=JsonArray(),
        kwargs=JsonObject(dict(call_keyword)),
    )
    return replace(
        state.request,
        request=nested_input,
        staged_call=nested_staged_call,
        execution_plan=nested_execution_plan,
    )


def _nested_call_pre_state(
    *,
    state: _ExecutionState,
    nested_request: MetaGraphHandlerExecutionRequest,
    before_oig: ObjectInstanceGraph,
    target_instance: ClassInstance,
) -> MetaGraphPreState:
    return MetaGraphPreState(
        execution_plan=nested_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre=state.pre_state.graph_hash_pre,
        head_commit_id=state.pre_state.head_commit_id,
        target_object_id=target_instance.id,
        root_object_id=state.pre_state.root_object_id,
        root_class_instance_identity_id=(
            state.pre_state.root_class_instance_identity_id
        ),
        oig_index=build_meta_graph_pre_state_index(before_oig),
    )


def _share_nested_mutation_state(
    *,
    parent_state: _ExecutionState,
    nested_state: _ExecutionState,
) -> None:
    nested_state.constructed_class_instance_ids = (
        parent_state.constructed_class_instance_ids
    )
    nested_state.constructed_class_instances_by_id = (
        parent_state.constructed_class_instances_by_id
    )
    nested_state.constructed_class_instances_by_class_and_source_object_id = (
        parent_state.constructed_class_instances_by_class_and_source_object_id
    )
    nested_state.constructed_relationships_by_membership = (
        parent_state.constructed_relationships_by_membership
    )
    nested_state.post_class_instances_by_id = parent_state.post_class_instances_by_id
    nested_state.post_attributes_by_class_instance_and_config_id = (
        parent_state.post_attributes_by_class_instance_and_config_id
    )


async def _validate_nested_call_delta(
    *,
    nested_request: MetaGraphHandlerExecutionRequest,
    session_delta: MetaGraphExecutionSessionDelta,
) -> None:
    _validate_nested_session_delta_plan(
        nested_request=nested_request,
        session_delta=session_delta,
    )
    mutation_set = MetaGraphMutationSet(
        execution_plan=nested_request.execution_plan,
        before_oig=session_delta.before_oig,
        changes=session_delta.changes,
        graph_hash_pre=session_delta.graph_hash_pre,
        graph_hash_post=session_delta.graph_hash_post,
        root_object_id=session_delta.root_object_id,
        root_class_instance_identity_id=(session_delta.root_class_instance_identity_id),
        target_class_instance_id=(
            session_delta.target_class_instance_id
            or nested_request.execution_plan.target_object_id
        ),
        constructed_class_instance_ids=session_delta.constructed_class_instance_ids,
    )
    validation = await MetaGraphMutateSelfOnlyPolicy().validate_mutation_boundary(
        nested_request,
        mutation_set,
    )
    if validation.status is MetaGraphMutationBoundaryStatus.rejected:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke rejected nested mutations. "
            f"{validation.violation_message}"
        )


def _validate_nested_session_delta_plan(
    *,
    nested_request: MetaGraphHandlerExecutionRequest,
    session_delta: MetaGraphExecutionSessionDelta,
) -> None:
    if session_delta.execution_plan is not nested_request.execution_plan:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke returned a session delta for a different "
            "execution plan."
        )


def _filter_nested_session_delta_to_target_scope(
    *,
    session_delta: MetaGraphExecutionSessionDelta,
) -> MetaGraphExecutionSessionDelta:
    target_class_instance_id = session_delta.target_class_instance_id
    if target_class_instance_id is None:
        return session_delta
    allowed_ids = {
        target_class_instance_id,
        *session_delta.constructed_class_instance_ids,
        *_descendant_ids_in_oig(
            oig=session_delta.before_oig,
            target_class_instance_id=target_class_instance_id,
        ),
    }
    if not allowed_ids:
        return session_delta

    scoped_changes = []
    for change in session_delta.changes:
        class_instance_changes = [
            item
            for item in change.class_instance_changes
            if item.class_instance_id in allowed_ids
        ]
        relationship_changes = [
            item
            for item in change.class_instance_relationship_changes
            if item.source_class_instance_id in allowed_ids
            or item.target_class_instance_id in allowed_ids
        ]
        if not class_instance_changes and not relationship_changes:
            continue
        scoped_changes.append(
            change.model_copy(
                update={
                    "class_instance_changes": class_instance_changes,
                    "class_instance_relationship_changes": relationship_changes,
                },
            )
        )
    if len(scoped_changes) == len(session_delta.changes) and all(
        scoped_change is original
        for scoped_change, original in zip(scoped_changes, session_delta.changes)
    ):
        return session_delta
    return replace(session_delta, changes=tuple(scoped_changes))


def _descendant_ids_in_oig(
    *,
    oig: ObjectInstanceGraph,
    target_class_instance_id: UUID,
) -> set[UUID]:
    relationships_by_source: dict[UUID, list[UUID]] = {}
    for relationship in oig.class_instance_relationships:
        relationships_by_source.setdefault(
            relationship.source_class_instance_id,
            [],
        ).append(relationship.target_class_instance_id)

    descendants: set[UUID] = set()
    stack = list(relationships_by_source.get(target_class_instance_id, ()))
    while stack:
        class_instance_id = stack.pop()
        if class_instance_id in descendants:
            continue
        descendants.add(class_instance_id)
        stack.extend(relationships_by_source.get(class_instance_id, ()))
    return descendants


def _apply_nested_session_delta(
    *,
    state: _ExecutionState,
    session_delta: MetaGraphExecutionSessionDelta,
) -> None:
    if session_delta.changes:
        apply_object_instance_graph_changes(
            graph=state.post_oig,
            changes=session_delta.changes,
            attribute_configs_by_id=(
                state.request.execution_plan.index.attribute_configs_by_id
            ),
            class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        )
        state.post_class_instances_by_id = None
        state.post_attributes_by_class_instance_and_config_id = None
    for class_instance_id in session_delta.constructed_class_instance_ids:
        if class_instance_id not in state.constructed_class_instance_ids:
            state.constructed_class_instance_ids.append(class_instance_id)


def _dispatch_payload_return_value(payload: JsonValue | None) -> JsonValue | None:
    if payload is None:
        return None
    if isinstance(payload, Mapping) and "value" in payload:
        return _json_return_value(payload["value"], path="call.payload.value")
    return _json_return_value(payload, path="call.payload")


def _json_return_value(value: object, *, path: str) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        result = JsonObject()
        for raw_key, raw_value in value.items():
            if not isinstance(raw_key, str):
                raise MetaGraphAwareFunctionImplExecutionError(
                    f"FunctionImpl value at {path} contains a non-string key."
                )
            result[raw_key] = _json_return_value(
                raw_value,
                path=f"{path}.{raw_key}" if raw_key else path,
            )
        return result
    if isinstance(value, list):
        return JsonArray(
            [
                _json_return_value(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]
        )
    return _copy_json_value(value, path=path)


def _capture_call_return(
    *,
    instruction_sequence: int,
    instruction_invoke: FunctionImplInstructionInvoke,
    return_value: JsonValue | None,
    state: _ExecutionState,
) -> None:
    capture_name = _invoke_capture_name(
        instruction_sequence=instruction_sequence,
        instruction_invoke=instruction_invoke,
        state=state,
    )
    if return_value is not None:
        state.last_value = _copy_json_value(return_value, path="call.return")
    if not capture_name:
        return
    if return_value is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl call invoke attempted to capture an empty return "
            f"value. capture_name={capture_name!r}"
        )
    captured = _copy_json_value(return_value, path=f"call.capture.{capture_name}")
    state.let_values_by_name[capture_name] = captured


def _capture_construct_return(
    *,
    instruction_sequence: int,
    instruction_invoke: FunctionImplInstructionInvoke,
    return_value: JsonValue,
    state: _ExecutionState,
) -> None:
    capture_name = _invoke_capture_name(
        instruction_sequence=instruction_sequence,
        instruction_invoke=instruction_invoke,
        state=state,
    )
    if not capture_name:
        return
    captured = _copy_json_value(
        return_value,
        path=f"construct.capture.{capture_name}",
    )
    state.let_values_by_name[capture_name] = captured


def _invoke_capture_name(
    *,
    instruction_sequence: int,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> str:
    capture_name = str(getattr(instruction_invoke, "capture_name", "") or "").strip()
    if capture_name:
        return capture_name
    function_config = state.request.execution_plan.implementation.function_config
    for invocation in getattr(function_config, "invocations", ()):
        if getattr(invocation, "position", None) != instruction_sequence:
            continue
        if (
            getattr(invocation, "target_function_config_id", None)
            != instruction_invoke.target_function_config_id
        ):
            continue
        return str(getattr(invocation, "capture_name", "") or "").strip()
    return ""


def _construct_relationship(
    instruction_invoke: FunctionImplInstructionInvoke,
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> ClassConfigRelationship:
    relationship = instruction_invoke.class_config_relationship
    if relationship is not None:
        return relationship
    relationship_id = instruction_invoke.class_config_relationship_id
    if relationship_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke requires class_config_relationship_id."
        )
    relationship = request.execution_plan.index.relationships_by_id.get(
        relationship_id,
    )
    if relationship is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke relationship is not present in the "
            "Meta runtime index. "
            f"class_config_relationship_id={relationship_id}"
        )
    return relationship


def _construct_target_class_config(
    *,
    relationship: ClassConfigRelationship,
    request: MetaGraphHandlerExecutionRequest,
) -> ClassConfig:
    target_class_config = relationship.target_class_config
    if target_class_config is not None:
        return target_class_config
    target_class_config = request.execution_plan.index.class_configs_by_id.get(
        relationship.target_class_config_id,
    )
    if target_class_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target ClassConfig is not present "
            "in the Meta runtime index. "
            f"target_class_config_id={relationship.target_class_config_id}"
        )
    return target_class_config


def _validate_construct_relationship(
    *,
    relationship: ClassConfigRelationship,
    source_instance: ClassInstance,
    target_class_config: ClassConfig,
) -> None:
    if relationship.class_config_id != source_instance.class_config_id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct relationship source does not match the "
            "invoked ClassInstance class_config."
        )
    if relationship.target_class_config_id != target_class_config.id:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct relationship target does not match the "
            "resolved target ClassConfig."
        )


def _construct_target_function_config(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    target_class_config: ClassConfig,
    state: _ExecutionState,
) -> FunctionConfig:
    target_function_id = instruction_invoke.target_function_config_id
    if target_function_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke requires target_function_config_id."
        )
    descriptor = state.implementation_descriptors_by_id.get(target_function_id)
    if descriptor is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target FunctionConfig is not "
            "indexed on the execution plan. "
            f"function_config_id={target_function_id}"
        )
    if not descriptor.is_constructor:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target is not a constructor. "
            f"function_config_id={target_function_id}"
        )
    owner_class_config = descriptor.owner_class_config
    if owner_class_config is None or owner_class_config.id != target_class_config.id:
        owner_class_config_id = None
        if owner_class_config is not None:
            owner_class_config_id = owner_class_config.id
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target FunctionConfig is not "
            "declared on the relationship target ClassConfig. "
            f"target_class_config_id={target_class_config.id} "
            f"owner_class_config_id={owner_class_config_id} "
            f"function_config_id={target_function_id}"
        )
    return descriptor.function_config


def _construct_target_function_descriptor(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> MetaGraphFunctionImplementationDescriptor:
    target_function_id = instruction_invoke.target_function_config_id
    if target_function_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke requires target_function_config_id."
        )
    descriptor = state.implementation_descriptors_by_id.get(target_function_id)
    if descriptor is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target FunctionConfig is not "
            "indexed on the execution plan. "
            f"function_config_id={target_function_id}"
        )
    if not descriptor.is_constructor:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke target is not a constructor. "
            f"function_config_id={target_function_id}"
        )
    return descriptor


def _relationship_association_class_config(
    *,
    relationship: ClassConfigRelationship,
    request: MetaGraphHandlerExecutionRequest,
) -> ClassConfig | None:
    association_class = relationship.class_config_relationship_association
    if association_class is not None:
        return association_class
    association_edge = relationship.class_config_relationship_association_edge
    association_class_id = (
        association_edge.class_config_id if association_edge is not None else None
    )
    if association_class_id is None:
        return None
    return request.execution_plan.index.class_configs_by_id.get(association_class_id)


def _standalone_construct_target_function_config(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    state: _ExecutionState,
) -> FunctionConfig:
    target_function_id = instruction_invoke.target_function_config_id
    if target_function_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl standalone construct invoke requires target_function_config_id."
        )
    descriptor = state.implementation_descriptors_by_id.get(target_function_id)
    if descriptor is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl standalone construct invoke target FunctionConfig is not "
            "indexed on the execution plan. "
            f"function_config_id={target_function_id}"
        )
    if not descriptor.is_constructor:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl standalone construct invoke target is not a constructor. "
            f"function_config_id={target_function_id}"
        )
    if descriptor.owner_class_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl standalone construct invoke target has no owner ClassConfig. "
            f"function_config_id={target_function_id}"
        )
    return descriptor.function_config


def _standalone_construct_target_class_config(
    *,
    target_function_config: FunctionConfig,
    state: _ExecutionState,
) -> ClassConfig:
    descriptor = state.implementation_descriptors_by_id.get(target_function_config.id)
    if descriptor is None or descriptor.owner_class_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl standalone construct invoke cannot resolve owner ClassConfig. "
            f"function_config_id={target_function_config.id}"
        )
    return descriptor.owner_class_config


def _construct_target_values(
    *,
    instruction_invoke: FunctionImplInstructionInvoke,
    target_function_config: FunctionConfig,
    source_instance: ClassInstance,
    state: _ExecutionState,
) -> dict[str, object]:
    input_edges = state.function_input_edges_by_function_id.get(
        target_function_config.id,
    )
    inputs_by_attribute_config_id = (
        state.function_input_edges_by_attribute_config_id.get(
            target_function_config.id,
        )
    )
    if input_edges is None or inputs_by_attribute_config_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke requires indexed constructor "
            f"inputs. function_config_id={target_function_config.id}"
        )
    values_by_input_id: dict[UUID, object] = {}

    for binding in instruction_invoke.attribute_configs:
        position = binding.position
        if position is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke binding position must be explicit."
            )
        target_input = inputs_by_attribute_config_id.get(
            binding.attribute_config_id,
        )
        if target_input is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke binding does not target a "
                "constructor input. "
                f"attribute_config_id={binding.attribute_config_id}"
            )
        if target_input.id in values_by_input_id:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke has duplicate binding for "
                "constructor input. "
                f"function_config_attribute_config_id={target_input.id}"
            )
        values_by_input_id[target_input.id] = _evaluate_invoke_value_expr(
            binding.value_expr,
            source_instance=source_instance,
            state=state,
            path=f"invoke.{target_input.name}",
        )

    target_values: dict[str, object] = {}
    for input_edge in input_edges:
        name = _function_input_name(input_edge)
        if input_edge.id in values_by_input_id:
            target_values[name] = values_by_input_id[input_edge.id]
            continue
        default_value = input_edge.attribute_config.default_value
        if default_value is not None:
            target_values[name] = parse_meta_default_value(default_value)
            continue
        if bool(input_edge.attribute_config.is_required):
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke missing required constructor "
                f"input. input_name={name}"
            )
    return target_values


def _function_input_name(input_edge: FunctionConfigAttributeConfig) -> str:
    name = (input_edge.name or "").strip()
    if name:
        return name
    attribute_config = input_edge.attribute_config
    if attribute_config is not None and (attribute_config.name or "").strip():
        return attribute_config.name.strip()
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl constructor input requires a name. "
        f"function_config_attribute_config_id={input_edge.id}"
    )


def _evaluate_invoke_value_expr(
    value_expr: Mapping[str, object],
    *,
    source_instance: ClassInstance,
    state: _ExecutionState,
    path: str,
) -> object:
    if not isinstance(value_expr, Mapping):
        raise MetaGraphAwareFunctionImplExecutionError(
            f"FunctionImpl invoke value expression at {path} must be an object."
        )
    kind = value_expr.get("kind")
    if not isinstance(kind, str):
        raise MetaGraphAwareFunctionImplExecutionError(
            f"FunctionImpl invoke value expression at {path} requires kind."
        )
    if kind == "self_id":
        return source_instance.source_object_id
    if kind == "literal":
        if "value" not in value_expr:
            raise MetaGraphAwareFunctionImplExecutionError(
                f"FunctionImpl invoke literal expression at {path} requires value."
            )
        return value_expr["value"]
    if kind == "reference":
        source_name = str(value_expr.get("name") or "").strip()
        if not source_name:
            raise MetaGraphAwareFunctionImplExecutionError(
                f"FunctionImpl invoke reference expression at {path} requires name."
            )
        return _read_reference_value(source_name, state=state)
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl invoke value expression kind. "
        f"path={path} kind={kind!r}"
    )


def _read_reference_value(
    source_name: str,
    *,
    state: _ExecutionState,
) -> object:
    parts = tuple(part.strip() for part in source_name.split(".") if part.strip())
    if not parts:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl invoke reference requires a non-empty name."
        )
    root_name = parts[0]
    if root_name in state.let_values_by_name:
        current_value: object = state.let_values_by_name[root_name]
    else:
        current_value = _read_named_input(root_name, state=state)
    for member_name in parts[1:]:
        current_value = _read_reference_member_value(
            current_value=current_value,
            member_name=member_name,
            source_name=source_name,
        )
    return current_value


def _read_reference_member_value(
    *,
    current_value: object,
    member_name: str,
    source_name: str,
) -> object:
    if isinstance(current_value, Mapping):
        if member_name not in current_value:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl invoke reference cannot resolve mapping member. "
                f"source_name={source_name!r} member_name={member_name!r}"
            )
        return current_value[member_name]
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl invoke reference member traversal is unsupported for "
        f"{type(current_value).__name__}. source_name={source_name!r}"
    )


def _resolve_constructor_object_id(
    *,
    target_class_config: ClassConfig,
    target_function_config: FunctionConfig,
    target_values: Mapping[str, object],
) -> UUID:
    helper_module = _stable_ids_module_for_class_config(target_class_config)
    helper_name, identity_input_names = _stable_id_binding_for_class_config(
        helper_module=helper_module,
        target_class_config=target_class_config,
    )
    identity_kwargs: dict[str, object] = {}
    for input_name in identity_input_names:
        if input_name not in target_values:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl construct invoke missing stable-id input. "
                f"input_name={input_name!r} function_config_id={target_function_config.id}"
            )
        identity_kwargs[input_name] = _stable_id_input_value(
            target_values[input_name],
        )
    stable_id_fn = helper_module.__dict__.get(helper_name)
    if stable_id_fn is None or not callable(stable_id_fn):
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id helper is not callable. "
            f"module={helper_module.__name__!r} helper={helper_name!r}"
        )
    resolved_id = stable_id_fn(**identity_kwargs)
    if not isinstance(resolved_id, UUID):
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id helper returned non-UUID result. "
            f"helper={helper_name!r} result_type={type(resolved_id).__name__}"
        )
    return resolved_id


def _stable_ids_module_for_class_config(
    target_class_config: ClassConfig,
) -> ModuleType:
    orm_class = ORMModelRegistry.get_class_by_class_config_id(target_class_config.id)
    if orm_class is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke requires ORM binding for target "
            "ClassConfig stable-id resolution. "
            f"class_config_id={target_class_config.id}"
        )
    module_root = orm_class.__module__.split(".", maxsplit=1)[0].strip()
    if not module_root:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke cannot resolve target ORM module root. "
            f"class_config_id={target_class_config.id}"
        )
    try:
        return importlib.import_module(f"{module_root}.stable_ids")
    except Exception as exc:  # pragma: no cover - importlib backend specifics
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl construct invoke could not import stable-id module. "
            f"module_root={module_root!r}"
        ) from exc


def _stable_id_binding_for_class_config(
    *,
    helper_module: ModuleType,
    target_class_config: ClassConfig,
) -> tuple[str, tuple[str, ...]]:
    bindings = helper_module.__dict__.get(_CONSTRUCTOR_STABLE_ID_BINDINGS_EXPORT)
    if not isinstance(bindings, dict):
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id module is missing constructor binding export. "
            f"module={helper_module.__name__!r}"
        )
    raw_entry = bindings.get(str(target_class_config.id))
    if not isinstance(raw_entry, tuple) or len(raw_entry) != 2:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id constructor binding row is missing or malformed. "
            f"class_config_id={target_class_config.id}"
        )
    helper_name_raw, identity_names_raw = raw_entry
    helper_name = str(helper_name_raw or "").strip()
    if not helper_name:
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id constructor binding helper name is empty. "
            f"class_config_id={target_class_config.id}"
        )
    if not isinstance(identity_names_raw, tuple):
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id constructor binding identity names must be a tuple. "
            f"class_config_id={target_class_config.id}"
        )
    identity_names = tuple(str(name or "").strip() for name in identity_names_raw)
    if any(not name for name in identity_names):
        raise MetaGraphAwareFunctionImplExecutionError(
            "Stable-id constructor binding identity names must be non-empty. "
            f"class_config_id={target_class_config.id}"
        )
    return helper_name, identity_names


def _stable_id_input_value(value: object) -> object:
    if hasattr(value, "value") and not isinstance(value, (str, bytes, bytearray)):
        return value.value
    return value


def _find_class_instance_by_source(
    *,
    state: _ExecutionState,
    class_config_id: UUID,
    source_object_id: UUID,
) -> ClassInstance | None:
    key = (class_config_id, source_object_id)
    class_instance = (
        state.constructed_class_instances_by_class_and_source_object_id.get(key)
    )
    if class_instance is not None:
        return class_instance
    for class_instance in state.post_oig.class_instances:
        if (
            class_instance.class_config_id == class_config_id
            and class_instance.source_object_id == source_object_id
        ):
            return class_instance
    return state.oig_index.class_instances_by_class_and_source_object_id.get(key)


def _ensure_class_instance_relationship(
    *,
    state: _ExecutionState,
    relationship: ClassConfigRelationship,
    source_instance: ClassInstance,
    target_instance: ClassInstance,
) -> None:
    relationship_id = stable_class_instance_relationship_id(
        class_config_relationship_id=relationship.id,
        source_class_instance_id=source_instance.id,
        target_class_instance_id=target_instance.id,
    )
    membership = (
        relationship.id,
        source_instance.id,
        target_instance.id,
    )
    if membership in state.constructed_relationships_by_membership:
        return
    if membership in state.oig_index.relationships_by_membership:
        return
    class_instance_relationship = ClassInstanceRelationship(
        id=relationship_id,
        object_instance_graph_id=state.post_oig.id,
        class_config_relationship_id=relationship.id,
        class_config_relationship=relationship,
        source_class_instance_id=source_instance.id,
        target_class_instance_id=target_instance.id,
    )
    state.post_oig.class_instance_relationships.append(class_instance_relationship)
    state.constructed_relationships_by_membership[membership] = (
        class_instance_relationship
    )


def _json_object_value(
    values: Mapping[str, object],
    *,
    path: str,
) -> JsonObject:
    return JsonObject(
        {
            str(key): _json_like_value(value, path=f"{path}.{key}")
            for key, value in values.items()
        }
    )


def _json_like_value(value: object, *, path: str) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    return _copy_json_value(value, path=path)


def _target_attribute_config(
    edge: ClassConfigAttributeConfig,
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> AttributeConfig:
    if edge.attribute_config is not None:
        return edge.attribute_config
    attribute_config_id = edge.attribute_config_id
    if attribute_config_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set target is missing attribute_config_id."
        )
    attribute_config = request.execution_plan.index.attribute_configs_by_id.get(
        attribute_config_id,
    )
    if attribute_config is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set target AttributeConfig is not present in the "
            "Meta runtime index."
        )
    return attribute_config


def _target_class_instance_for_read(state: _ExecutionState) -> ClassInstance:
    target_object_id = state.pre_state.target_object_id
    if target_object_id is None:
        target_object_id = state.request.execution_plan.target_object_id
    if target_object_id is None:
        target_object_id = _constructor_root_target_object_id(state)
    if target_object_id is None:
        target_object_id = _constructor_last_value_target_object_id(state)
    if target_object_id is None:
        descriptor = state.request.execution_plan.implementation
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set requires a target object id. "
            f"owner_key={descriptor.function_config.owner_key!r} "
            f"function_name={descriptor.function_config.name!r} "
            f"is_constructor={descriptor.is_constructor}"
        )
    class_instance = state.constructed_class_instances_by_id.get(target_object_id)
    if class_instance is not None:
        return class_instance
    class_instance = state.oig_index.class_instances_by_id.get(target_object_id)
    if class_instance is not None:
        return class_instance
    class_instance = _ensure_constructor_target_class_instance(
        state=state,
        target_object_id=target_object_id,
    )
    if class_instance is not None:
        return class_instance
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl set target object is not present in pre-state OIG. "
        f"target_object_id={target_object_id}"
    )


def _constructor_root_target_object_id(state: _ExecutionState) -> UUID | None:
    if not state.request.execution_plan.implementation.is_constructor:
        return None
    root_object_id = state.pre_state.root_object_id
    if isinstance(root_object_id, UUID):
        return root_object_id
    return None


def _constructor_last_value_target_object_id(state: _ExecutionState) -> UUID | None:
    if not state.request.execution_plan.implementation.is_constructor:
        return None
    value = state.last_value
    if not isinstance(value, Mapping):
        return None
    raw_id = value.get("id")
    if isinstance(raw_id, UUID):
        return raw_id
    if isinstance(raw_id, str):
        try:
            return UUID(raw_id)
        except ValueError:
            return None
    return None


def _ensure_constructor_target_class_instance(
    *,
    state: _ExecutionState,
    target_object_id: UUID,
) -> ClassInstance | None:
    descriptor = state.request.execution_plan.implementation
    if not descriptor.is_constructor:
        return None
    target_class_config = descriptor.owner_class_config
    if target_class_config is None:
        return None
    existing = _find_class_instance_by_source(
        state=state,
        class_config_id=target_class_config.id,
        source_object_id=target_object_id,
    )
    if existing is not None:
        return existing
    target_class_instance = build_class_instance(
        object_instance_graph_id=state.post_oig.id,
        class_config=target_class_config,
        class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        source=MappingModelSource(
            id=target_object_id,
            values={},
            class_config_id=target_class_config.id,
        ),
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=default_meta_class_instance_resolver,
    )
    state.post_oig.class_instances.append(target_class_instance)
    state.constructed_class_instance_ids.append(target_class_instance.id)
    state.constructed_class_instances_by_id[target_class_instance.id] = (
        target_class_instance
    )
    state.constructed_class_instances_by_class_and_source_object_id[
        (target_class_config.id, target_object_id)
    ] = target_class_instance
    if state.post_class_instances_by_id is not None:
        state.post_class_instances_by_id[target_class_instance.id] = (
            target_class_instance
        )
    if state.post_attributes_by_class_instance_and_config_id is not None:
        for attribute in target_class_instance.attributes:
            state.post_attributes_by_class_instance_and_config_id[
                (target_class_instance.id, attribute.attribute_config_id)
            ] = attribute
    return target_class_instance


def _target_class_instance_for_mutation(state: _ExecutionState) -> ClassInstance:
    target_instance = _target_class_instance_for_read(state)
    post_index = _post_class_instances_by_id(state)
    post_target = post_index.get(target_instance.id)
    if post_target is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl set target object is not present in post-state OIG. "
            f"target_object_id={target_instance.id}"
        )
    return post_target


def _post_class_instances_by_id(
    state: _ExecutionState,
) -> dict[UUID, ClassInstance]:
    post_index = state.post_class_instances_by_id
    if post_index is None:
        post_index = {
            class_instance.id: class_instance
            for class_instance in state.post_oig.class_instances
        }
        state.post_class_instances_by_id = post_index
    return post_index


def _post_attributes_by_class_instance_and_config_id(
    state: _ExecutionState,
) -> dict[tuple[UUID, UUID], Attribute]:
    attribute_index = state.post_attributes_by_class_instance_and_config_id
    if attribute_index is None:
        attribute_index = {
            (class_instance.id, attribute.attribute_config_id): attribute
            for class_instance in state.post_oig.class_instances
            for attribute in class_instance.attributes
        }
        state.post_attributes_by_class_instance_and_config_id = attribute_index
    return attribute_index


def _target_attribute_or_none(
    *,
    state: _ExecutionState,
    target_instance: ClassInstance,
    attribute_config_id: UUID,
) -> Attribute | None:
    attribute = _post_attributes_by_class_instance_and_config_id(state).get(
        (target_instance.id, attribute_config_id),
    )
    if attribute is not None:
        return attribute
    return None


def _evaluate_value_source(
    source: FunctionImplValueSource,
    *,
    state: _ExecutionState,
) -> JsonValue:
    kind = _value_source_kind(source)
    if kind is FunctionImplValueSourceKind.literal:
        literal = source.source_literal_primitive
        if literal is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl literal value source is missing literal payload."
            )
        return _copy_json_value(
            _literal_primitive_value(literal.value),
            path=f"value_source.{source.key}",
        )
    if kind is FunctionImplValueSourceKind.function_input_ref:
        function_input = _function_input_source(source, request=state.request)
        return _read_function_input(function_input, state=state)
    if kind is FunctionImplValueSourceKind.let_ref:
        return _read_let_ref(source, state=state)
    if kind is FunctionImplValueSourceKind.read_path:
        return _evaluate_read_path_value_source(source, state=state)
    if kind is FunctionImplValueSourceKind.transform:
        transform_payload = source.source_transform
        if transform_payload is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl transform value source is missing transform payload."
            )
        operand_values: list[JsonValue] = []
        seen_positions: set[int] = set()
        operands = sorted(
            transform_payload.operands,
            key=lambda operand: (int(operand.position), str(operand.id)),
        )
        for operand in operands:
            position = int(operand.position)
            if position < 0:
                raise MetaGraphAwareFunctionImplExecutionError(
                    "FunctionImpl transform operand position must be non-negative."
                )
            if position in seen_positions:
                raise MetaGraphAwareFunctionImplExecutionError(
                    "FunctionImpl transform operands must be unique by position."
                )
            seen_positions.add(position)
            operand_source = operand.value_source
            if operand_source is None:
                raise MetaGraphAwareFunctionImplExecutionError(
                    "FunctionImpl transform operand is missing value source payload."
                )
            operand_values.append(_evaluate_value_source(operand_source, state=state))
        return _evaluate_value_transform(
            operation=transform_payload.operation,
            operand_values=operand_values,
        )
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl value source kind. " f"value_source_kind={kind.value}"
    )


def _literal_primitive_value(value: object) -> object:
    if isinstance(value, Mapping) and tuple(value.keys()) == ("value",):
        return value["value"]
    return value


def _evaluate_value_transform(
    *,
    operation: FunctionImplValueTransformKind,
    operand_values: list[JsonValue],
) -> JsonValue:
    operation = _value_transform_kind(operation)
    if operation is FunctionImplValueTransformKind.text_strip:
        _require_transform_arity(
            operation=operation, operand_values=operand_values, arity=1
        )
        return _coerce_transform_text(operand_values[0], operation=operation).strip()
    if operation is FunctionImplValueTransformKind.text_casefold:
        _require_transform_arity(
            operation=operation, operand_values=operand_values, arity=1
        )
        return _coerce_transform_text(operand_values[0], operation=operation).casefold()
    if operation is FunctionImplValueTransformKind.text_lower:
        _require_transform_arity(
            operation=operation, operand_values=operand_values, arity=1
        )
        return _coerce_transform_text(operand_values[0], operation=operation).lower()
    if operation is FunctionImplValueTransformKind.text_default_if_blank:
        _require_transform_arity(
            operation=operation, operand_values=operand_values, arity=2
        )
        value = _coerce_transform_text(operand_values[0], operation=operation)
        default = _coerce_transform_text(operand_values[1], operation=operation)
        return default if value.strip() == "" else value
    if operation is FunctionImplValueTransformKind.text_slice:
        if len(operand_values) not in {2, 3}:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl transform text_slice expects 2 or 3 operands."
            )
        value = _coerce_transform_text(operand_values[0], operation=operation)
        start = _coerce_transform_int(
            operand_values[1],
            operation=operation,
            name="start",
        )
        end = (
            _coerce_transform_int(operand_values[2], operation=operation, name="end")
            if len(operand_values) == 3
            else None
        )
        return value[start:end]
    if operation is FunctionImplValueTransformKind.text_concat:
        if not operand_values:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl transform text_concat expects at least 1 operand."
            )
        return "".join(
            _coerce_transform_text(value, operation=operation)
            for value in operand_values
        )
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl value transform kind. " f"operation={operation.value}"
    )


def _require_transform_arity(
    *,
    operation: FunctionImplValueTransformKind,
    operand_values: list[JsonValue],
    arity: int,
) -> None:
    if len(operand_values) != arity:
        raise MetaGraphAwareFunctionImplExecutionError(
            f"FunctionImpl transform {operation.value} expects exactly {arity} operand(s)."
        )


def _coerce_transform_text(
    value: JsonValue,
    *,
    operation: FunctionImplValueTransformKind,
) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    raise MetaGraphAwareFunctionImplExecutionError(
        f"FunctionImpl transform {operation.value} expects text operands; "
        f"received {type(value).__name__}."
    )


def _coerce_transform_int(
    value: JsonValue,
    *,
    operation: FunctionImplValueTransformKind,
    name: str,
) -> int:
    if type(value) is int:
        return value
    raise MetaGraphAwareFunctionImplExecutionError(
        f"FunctionImpl transform {operation.value} expects integer {name} operand; "
        f"received {type(value).__name__}."
    )


def _function_input_source(
    source: FunctionImplValueSource,
    *,
    request: MetaGraphHandlerExecutionRequest,
) -> FunctionConfigAttributeConfig:
    function_input = source.source_function_config_attribute_config
    if function_input is not None:
        return function_input
    function_input_id = source.source_function_config_attribute_config_id
    if function_input_id is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl input value source is missing function input binding."
        )
    function_input = (request.execution_plan.function_input_edges_by_id or {}).get(
        function_input_id,
    )
    if function_input is not None:
        return function_input
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl input value source does not match an indexed "
        "FunctionConfig input."
    )


def _read_function_input(
    function_input: FunctionConfigAttributeConfig,
    *,
    state: _ExecutionState,
) -> JsonValue:
    if _function_attribute_type(function_input.type) is not FunctionAttributeType.input:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl input value source must reference an input attribute."
        )
    if function_input.name in state.bound_arguments.keyword:
        return _copy_json_value(
            state.bound_arguments.keyword[function_input.name],
            path=f"kwargs.{function_input.name}",
        )
    if function_input.position < 0:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl input value source has a negative position."
        )
    if function_input.position < len(state.bound_arguments.positional):
        return _copy_json_value(
            state.bound_arguments.positional[function_input.position],
            path=f"args[{function_input.position}]",
        )
    default_value = function_input.attribute_config.default_value
    if default_value is not None:
        return _copy_json_value(
            parse_meta_default_value(default_value),
            path=f"default.{function_input.name}",
        )
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl input value source was not provided. "
        f"input_name={function_input.name} input_position={function_input.position}"
    )


def _read_named_input(
    input_name: str,
    *,
    state: _ExecutionState,
) -> JsonValue:
    if input_name in state.bound_arguments.keyword:
        return _copy_json_value(
            state.bound_arguments.keyword[input_name],
            path=f"kwargs.{input_name}",
        )
    function_input = _current_function_input_by_name(input_name, state=state)
    if function_input is not None:
        return _read_function_input(function_input, state=state)
    target_value = _read_target_attribute_input(input_name, state=state)
    if target_value is not _MISSING:
        return _json_like_value(target_value, path=f"target.{input_name}")
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl named input was not provided. " f"input_name={input_name}"
    )


def _current_function_input_by_name(
    input_name: str,
    *,
    state: _ExecutionState,
) -> FunctionConfigAttributeConfig | None:
    function_config = state.request.execution_plan.implementation.function_config
    for input_edge in state.function_input_edges_by_function_id.get(
        function_config.id,
        (),
    ):
        if _function_input_name(input_edge) == input_name:
            return input_edge
    return None


def _read_target_attribute_input(
    input_name: str,
    *,
    state: _ExecutionState,
) -> object:
    try:
        target_instance = _target_class_instance_for_read(state)
    except MetaGraphAwareFunctionImplExecutionError:
        return _MISSING
    class_config = state.request.execution_plan.index.class_configs_by_id.get(
        target_instance.class_config_id,
    )
    if class_config is None:
        return _MISSING
    attribute_config_id = None
    for edge in class_config.class_config_attribute_configs:
        attribute_config = edge.attribute_config
        if attribute_config is None:
            continue
        if attribute_config.name == input_name:
            attribute_config_id = attribute_config.id
            break
    if attribute_config_id is None:
        return _MISSING
    for attribute in target_instance.attributes:
        if attribute.attribute_config_id != attribute_config_id:
            continue
        return decode_oig_attribute_value(
            attribute.value_root,
            class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        )
    return _MISSING


def _read_let_ref(
    source: FunctionImplValueSource,
    *,
    state: _ExecutionState,
) -> JsonValue:
    source_let = source.source_instruction_let
    if source_let is not None:
        if source_let.id in state.let_values_by_id:
            return _copy_json_value(
                state.let_values_by_id[source_let.id],
                path=f"let.{source_let.name}",
            )
        if source_let.name in state.let_values_by_name:
            return _copy_json_value(
                state.let_values_by_name[source_let.name],
                path=f"let.{source_let.name}",
            )
    source_let_id = source.source_instruction_let_id
    if source_let_id is not None and source_let_id in state.let_values_by_id:
        return _copy_json_value(
            state.let_values_by_id[source_let_id],
            path=f"let.{source_let_id}",
        )
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl let value source references an unavailable let binding. "
        f"value_source_key={source.key}"
    )


def _evaluate_read_path_value_source(
    source: FunctionImplValueSource,
    *,
    state: _ExecutionState,
) -> JsonValue:
    read_path = source.source_read_path
    if read_path is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl read-path value source is missing read-path payload."
        )
    current_value = _read_path_root_value(read_path, source=source, state=state)
    for segment in sorted(
        read_path.segments,
        key=lambda item: (int(item.position), str(item.id)),
    ):
        attr_cfg = segment.attribute_config
        if attr_cfg is None and segment.attribute_config_id is not None:
            attr_cfg = state.request.execution_plan.index.attribute_configs_by_id.get(
                segment.attribute_config_id,
            )
        if attr_cfg is None or not (attr_cfg.name or "").strip():
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl read-path segment is missing AttributeConfig.name. "
                f"value_source_key={source.key}"
            )
        current_value = _read_path_member_value(
            current_value=current_value,
            member_name=attr_cfg.name.strip(),
            value_source_key=source.key,
        )
    return _json_like_value(current_value, path=f"value_source.{source.key}.read_path")


def _read_path_root_value(
    read_path: object,
    *,
    source: FunctionImplValueSource,
    state: _ExecutionState,
) -> object:
    root_kind = _read_path_root_kind(getattr(read_path, "root_kind", None))
    if root_kind is FunctionImplValueSourceReadPathRootKind.function_input:
        function_input = getattr(
            read_path,
            "root_function_config_attribute_config",
            None,
        )
        if function_input is None:
            function_input_id = getattr(
                read_path,
                "root_function_config_attribute_config_id",
                None,
            )
            if function_input_id is not None:
                function_input = (
                    state.request.execution_plan.function_input_edges_by_id or {}
                ).get(function_input_id)
        if function_input is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl read-path root function input is not indexed. "
                f"value_source_key={source.key}"
            )
        return _read_function_input(function_input, state=state)

    if root_kind is FunctionImplValueSourceReadPathRootKind.let_binding:
        root_let = getattr(read_path, "root_instruction_let", None)
        root_let_id = getattr(read_path, "root_instruction_let_id", None)
        return _read_let_binding_value(
            root_let=root_let,
            root_let_id=root_let_id,
            value_source_key=source.key,
            state=state,
        )

    if root_kind is FunctionImplValueSourceReadPathRootKind.target_attribute:
        target_edge = getattr(
            read_path,
            "root_class_config_attribute_config",
            None,
        )
        if target_edge is None:
            target_edge_id = getattr(
                read_path,
                "root_class_config_attribute_config_id",
                None,
            )
            if target_edge_id is not None:
                target_edge = _class_attribute_edge_by_id(
                    target_edge_id,
                    state=state,
                )
        if target_edge is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl read-path root target attribute is not indexed. "
                f"value_source_key={source.key}"
            )
        target_attr_cfg = _target_attribute_config(
            target_edge,
            request=state.request,
        )
        target_value = _read_target_attribute_by_config_id(
            target_attr_cfg.id,
            state=state,
        )
        if target_value is _MISSING:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl read-path target attribute root is missing. "
                f"attribute_name={target_attr_cfg.name!r} value_source_key={source.key}"
            )
        return target_value

    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl read-path root kind. "
        f"root_kind={root_kind.value} value_source_key={source.key}"
    )


def _read_let_binding_value(
    *,
    root_let: FunctionImplInstructionLet | None,
    root_let_id: UUID | None,
    value_source_key: str,
    state: _ExecutionState,
) -> JsonValue:
    if root_let is not None:
        if root_let.id in state.let_values_by_id:
            return _copy_json_value(
                state.let_values_by_id[root_let.id],
                path=f"let.{root_let.name}",
            )
        if root_let.name in state.let_values_by_name:
            return _copy_json_value(
                state.let_values_by_name[root_let.name],
                path=f"let.{root_let.name}",
            )
    if root_let_id is not None and root_let_id in state.let_values_by_id:
        return _copy_json_value(
            state.let_values_by_id[root_let_id],
            path=f"let.{root_let_id}",
        )
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl read-path root references an unavailable let binding. "
        f"value_source_key={value_source_key}"
    )


def _read_path_member_value(
    *,
    current_value: object,
    member_name: str,
    value_source_key: str,
) -> object:
    if isinstance(current_value, Mapping):
        if member_name not in current_value:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl read-path cannot resolve mapping member. "
                f"member_name={member_name!r} value_source_key={value_source_key}"
            )
        return current_value[member_name]
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl read-path member traversal is unsupported for "
        f"{type(current_value).__name__}. value_source_key={value_source_key}"
    )


def _read_target_attribute_by_config_id(
    attribute_config_id: UUID,
    *,
    state: _ExecutionState,
) -> object:
    target_instance = _target_class_instance_for_read(state)
    for attribute in target_instance.attributes:
        if attribute.attribute_config_id != attribute_config_id:
            continue
        return decode_oig_attribute_value(
            attribute.value_root,
            class_configs_by_id=state.request.execution_plan.index.class_configs_by_id,
        )
    return _MISSING


def _class_attribute_edge_by_id(
    edge_id: UUID,
    *,
    state: _ExecutionState,
) -> ClassConfigAttributeConfig | None:
    for class_config in state.request.execution_plan.index.class_configs_by_id.values():
        for edge in getattr(class_config, "class_config_attribute_configs", ()):
            if getattr(edge, "id", None) == edge_id:
                return edge
    return None


def _require_condition_holds(
    *,
    kind: FunctionImplRequireKind,
    operands: list[JsonValue],
    compare_operator: FunctionImplRequireCompareOperator | None,
    expected_count: int | None,
) -> bool:
    if kind is FunctionImplRequireKind.exists:
        _require_operand_count(kind=kind, operands=operands, expected=1)
        return _is_present(operands[0])
    if kind is FunctionImplRequireKind.equals:
        _require_operand_count(kind=kind, operands=operands, expected=2)
        return operands[0] == operands[1]
    if kind is FunctionImplRequireKind.member:
        _require_operand_count(kind=kind, operands=operands, expected=2)
        return _is_member(needle=operands[0], haystack=operands[1])
    if kind is FunctionImplRequireKind.unique:
        _require_operand_count(kind=kind, operands=operands, expected=1)
        return _is_unique(operands[0])
    if kind is FunctionImplRequireKind.compare:
        _require_operand_count(kind=kind, operands=operands, expected=2)
        operator = _require_compare_operator(compare_operator)
        return _compare_values(left=operands[0], right=operands[1], operator=operator)
    if kind is FunctionImplRequireKind.cardinality:
        _require_operand_count(kind=kind, operands=operands, expected=1)
        if expected_count is None:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl cardinality require must declare expected_count."
            )
        operator = compare_operator or FunctionImplRequireCompareOperator.eq
        return _compare_numbers(
            left=_cardinality(operands[0]),
            right=expected_count,
            operator=_require_compare_operator(operator),
        )
    if kind is FunctionImplRequireKind.all_or_none:
        if not operands:
            raise MetaGraphAwareFunctionImplExecutionError(
                "FunctionImpl all_or_none require must declare operands."
            )
        present = [_is_present(operand) for operand in operands]
        return all(present) or not any(present)
    if kind is FunctionImplRequireKind.text_matches_regex:
        _require_operand_count(kind=kind, operands=operands, expected=2)
        return _text_matches_regex(value=operands[0], pattern=operands[1])
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl require kind. " f"require_kind={kind.value}"
    )


def _require_operand_count(
    *,
    kind: FunctionImplRequireKind,
    operands: list[JsonValue],
    expected: int,
) -> None:
    if len(operands) != expected:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl require operand count mismatch. "
            f"require_kind={kind.value} expected={expected} actual={len(operands)}"
        )


def _is_present(value: JsonValue) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if value == "":
        return False
    if value == []:
        return False
    if value == {}:
        return False
    return True


def _is_member(*, needle: JsonValue, haystack: JsonValue) -> bool:
    if isinstance(haystack, (list, str)):
        return needle in haystack
    if isinstance(haystack, dict):
        return isinstance(needle, str) and needle in haystack
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl member require needs a JSON array, object, or string " "haystack."
    )


def _is_unique(value: JsonValue) -> bool:
    if not isinstance(value, list):
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl unique require needs a JSON array operand."
        )
    fingerprints = [
        json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value
    ]
    return len(fingerprints) == len(set(fingerprints))


def _cardinality(value: JsonValue) -> int:
    if isinstance(value, (list, dict, str)):
        return len(value)
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl cardinality require needs a JSON array, object, or string."
    )


def _compare_values(
    *,
    left: JsonValue,
    right: JsonValue,
    operator: FunctionImplRequireCompareOperator,
) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return _compare_numbers(left=left, right=right, operator=operator)
    if isinstance(left, str) and isinstance(right, str):
        return _compare_strings(left=left, right=right, operator=operator)
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl compare require supports numeric or string operands only."
    )


def _compare_numbers(
    *,
    left: int | float,
    right: int | float,
    operator: FunctionImplRequireCompareOperator,
) -> bool:
    if operator is FunctionImplRequireCompareOperator.eq:
        return left == right
    if operator is FunctionImplRequireCompareOperator.neq:
        return left != right
    if operator is FunctionImplRequireCompareOperator.gt:
        return left > right
    if operator is FunctionImplRequireCompareOperator.gte:
        return left >= right
    if operator is FunctionImplRequireCompareOperator.lt:
        return left < right
    if operator is FunctionImplRequireCompareOperator.lte:
        return left <= right
    raise MetaGraphAwareFunctionImplExecutionError(
        "Unsupported FunctionImpl compare operator. "
        f"compare_operator={operator.value}"
    )


def _compare_strings(
    *,
    left: str,
    right: str,
    operator: FunctionImplRequireCompareOperator,
) -> bool:
    if operator is FunctionImplRequireCompareOperator.eq:
        return left == right
    if operator is FunctionImplRequireCompareOperator.neq:
        return left != right
    raise MetaGraphAwareFunctionImplExecutionError(
        "FunctionImpl string compare supports eq and neq only."
    )


def _text_matches_regex(*, value: JsonValue, pattern: JsonValue) -> bool:
    if not isinstance(value, str) or not isinstance(pattern, str):
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl text_matches_regex require needs string value and "
            "pattern operands."
        )
    try:
        return re.fullmatch(pattern, value) is not None
    except re.error as exc:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl text_matches_regex require received invalid regex " "pattern."
        ) from exc


def _require_compare_operator(
    operator: FunctionImplRequireCompareOperator | None,
) -> FunctionImplRequireCompareOperator:
    if operator is None:
        raise MetaGraphAwareFunctionImplExecutionError(
            "FunctionImpl compare require must declare compare_operator."
        )
    if isinstance(operator, FunctionImplRequireCompareOperator):
        return operator
    return FunctionImplRequireCompareOperator(operator)


def _copy_json_value(value: object, *, path: str) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise MetaGraphAwareFunctionImplExecutionError(
                f"FunctionImpl value at {path} is a non-finite number."
            )
        return value
    if isinstance(value, list):
        return JsonArray(
            [
                _copy_json_value(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]
        )
    if isinstance(value, dict):
        result = JsonObject()
        for raw_key, raw_value in value.items():
            if not isinstance(raw_key, str):
                raise MetaGraphAwareFunctionImplExecutionError(
                    f"FunctionImpl value at {path} contains a non-string key."
                )
            result[raw_key] = _copy_json_value(
                raw_value,
                path=f"{path}.{raw_key}" if raw_key else path,
            )
        return result
    raise MetaGraphAwareFunctionImplExecutionError(
        f"FunctionImpl value at {path} is not JSON: {type(value).__name__}."
    )


def _function_impl_kind(function_impl: FunctionImpl) -> FunctionImplKind:
    kind = function_impl.kind
    if isinstance(kind, FunctionImplKind):
        return kind
    return FunctionImplKind(kind)


def _instruction_type(
    instruction: FunctionImplInstruction,
) -> FunctionImplInstructionType:
    instruction_type = instruction.type
    if isinstance(instruction_type, FunctionImplInstructionType):
        return instruction_type
    return FunctionImplInstructionType(instruction_type)


def _delete_target_kind_value(kind: object) -> str:
    return str(getattr(kind, "value", kind)).strip().casefold()


def _invoke_kind(
    instruction_invoke: FunctionImplInstructionInvoke,
) -> FunctionImplInvokeKind:
    kind = instruction_invoke.kind
    if isinstance(kind, FunctionImplInvokeKind):
        return kind
    return FunctionImplInvokeKind(kind)


def _value_source_kind(source: FunctionImplValueSource) -> FunctionImplValueSourceKind:
    kind = source.kind
    if isinstance(kind, FunctionImplValueSourceKind):
        return kind
    return FunctionImplValueSourceKind(kind)


def _read_path_root_kind(
    kind: FunctionImplValueSourceReadPathRootKind,
) -> FunctionImplValueSourceReadPathRootKind:
    if isinstance(kind, FunctionImplValueSourceReadPathRootKind):
        return kind
    return FunctionImplValueSourceReadPathRootKind(kind)


def _value_transform_kind(
    operation: FunctionImplValueTransformKind,
) -> FunctionImplValueTransformKind:
    if isinstance(operation, FunctionImplValueTransformKind):
        return operation
    return FunctionImplValueTransformKind(operation)


def _require_kind(kind: FunctionImplRequireKind) -> FunctionImplRequireKind:
    if isinstance(kind, FunctionImplRequireKind):
        return kind
    return FunctionImplRequireKind(kind)


def _function_attribute_type(
    attribute_type: FunctionAttributeType,
) -> FunctionAttributeType:
    if isinstance(attribute_type, FunctionAttributeType):
        return attribute_type
    return FunctionAttributeType(attribute_type)


__all__ = [
    "MetaGraphAwareFunctionImplExecutionError",
    "MetaGraphInstructionBodyFunctionImplRunner",
]
