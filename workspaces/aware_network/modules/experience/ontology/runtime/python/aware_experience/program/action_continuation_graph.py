from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
)
from aware_experience.program.action_continuation import (
    ProgramActionContinuationContract,
    ProgramActionContinuationError,
    ProgramActionContinuationResult,
    compose_program_action_continuation,
    program_action_continuation_payload_mapping,
    require_program_action_continuation_compatible_types,
    resolve_program_action_continuation_class_attributes,
)
from aware_meta_ontology.class_.class_config import ClassConfig


class ProgramActionContinuationGraphError(ValueError):
    """An explicitly declared continuation graph cannot execute safely."""


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationActivationInput:
    input_key: str
    model_id: UUID
    class_config: ClassConfig
    payload: object


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationActivationFieldBinding:
    source_input_key: str
    source_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationOutcomeSource:
    contract: ProgramActionContinuationContract
    source_response_class_config: ClassConfig
    source_receipt_class_config: ClassConfig | None = None


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationGraphStep:
    target_program_impl_instruction_intent_id: UUID
    target_sequence: int
    target_action_config_id: UUID
    target_api_capability_endpoint_id: UUID
    target_request_class_config: ClassConfig
    target_response_class_config_id: UUID
    outcome_sources: tuple[ProgramActionContinuationOutcomeSource, ...] = ()
    activation_field_bindings: tuple[
        ProgramActionContinuationActivationFieldBinding, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationCompositeResult:
    target_program_impl_instruction_intent_id: UUID
    target_action_config_id: UUID
    target_api_capability_endpoint_id: UUID
    target_request_class_config_id: UUID
    source_continuations: tuple[ProgramActionContinuationResult, ...]
    activation_input_keys: tuple[str, ...]
    request_payload: Mapping[str, object]
    target_values_by_attribute_config_id: Mapping[UUID, object]


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationGraphResult:
    initial_outcomes_by_instruction_intent_id: Mapping[
        UUID, ActionDispatchTerminalOutcome
    ]
    continuations: tuple[ProgramActionContinuationCompositeResult, ...]
    dispatched_outcomes: tuple[ActionDispatchTerminalOutcome, ...]
    outcomes_by_instruction_intent_id: Mapping[UUID, ActionDispatchTerminalOutcome]


ProgramActionContinuationGraphDispatch = Callable[
    [
        ProgramActionContinuationGraphStep,
        ProgramActionContinuationCompositeResult,
    ],
    Awaitable[ActionDispatchTerminalOutcome],
]


async def execute_program_action_continuation_graph(
    *,
    initial_outcomes_by_instruction_intent_id: Mapping[
        UUID, ActionDispatchTerminalOutcome
    ],
    activation_inputs_by_key: Mapping[str, ProgramActionContinuationActivationInput],
    steps: Sequence[ProgramActionContinuationGraphStep],
    dispatch: ProgramActionContinuationGraphDispatch,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ProgramActionContinuationGraphResult:
    """Compose and dispatch dependency-ready Program action nodes."""

    ordered_steps = _validate_graph(
        initial_outcomes_by_instruction_intent_id=(
            initial_outcomes_by_instruction_intent_id
        ),
        activation_inputs_by_key=activation_inputs_by_key,
        steps=steps,
    )
    outcomes = dict(initial_outcomes_by_instruction_intent_id)
    remaining = list(ordered_steps)
    continuations: list[ProgramActionContinuationCompositeResult] = []
    dispatched_outcomes: list[ActionDispatchTerminalOutcome] = []

    while remaining:
        ready_index = next(
            (
                index
                for index, step in enumerate(remaining)
                if _step_dependencies(step).issubset(outcomes)
            ),
            None,
        )
        if ready_index is None:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_dependencies_unresolved"
            )
        step = remaining.pop(ready_index)
        continuation = _compose_graph_step(
            step=step,
            outcomes_by_instruction_intent_id=outcomes,
            activation_inputs_by_key=activation_inputs_by_key,
            class_configs_by_id=class_configs_by_id,
        )
        target_outcome = await dispatch(step, continuation)
        _require_target_outcome(step=step, outcome=target_outcome)
        outcomes[step.target_program_impl_instruction_intent_id] = target_outcome
        continuations.append(continuation)
        dispatched_outcomes.append(target_outcome)

    return ProgramActionContinuationGraphResult(
        initial_outcomes_by_instruction_intent_id=MappingProxyType(
            dict(initial_outcomes_by_instruction_intent_id)
        ),
        continuations=tuple(continuations),
        dispatched_outcomes=tuple(dispatched_outcomes),
        outcomes_by_instruction_intent_id=MappingProxyType(outcomes),
    )


def _validate_graph(
    *,
    initial_outcomes_by_instruction_intent_id: Mapping[
        UUID, ActionDispatchTerminalOutcome
    ],
    activation_inputs_by_key: Mapping[str, ProgramActionContinuationActivationInput],
    steps: Sequence[ProgramActionContinuationGraphStep],
) -> tuple[ProgramActionContinuationGraphStep, ...]:
    if not steps:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_steps_missing"
        )

    ordered = tuple(
        sorted(
            steps,
            key=lambda step: (
                step.target_sequence,
                str(step.target_program_impl_instruction_intent_id),
            ),
        )
    )
    target_ids: set[UUID] = set()
    target_sequences: set[int] = set()
    normalized_activation_inputs: dict[
        str, ProgramActionContinuationActivationInput
    ] = {}
    for mapping_key, activation_input in activation_inputs_by_key.items():
        normalized_mapping_key = _normalized_input_key(mapping_key)
        normalized_declared_key = _normalized_input_key(activation_input.input_key)
        if (
            mapping_key != normalized_mapping_key
            or activation_input.input_key != normalized_declared_key
            or normalized_mapping_key != normalized_declared_key
        ):
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_activation_input_key_mismatch"
            )
        if normalized_mapping_key in normalized_activation_inputs:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_duplicate_activation_input"
            )
        normalized_activation_inputs[normalized_mapping_key] = activation_input
    for step in ordered:
        if step.target_program_impl_instruction_intent_id in target_ids:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_duplicate_target_intent"
            )
        if step.target_sequence in target_sequences:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_duplicate_target_sequence"
            )
        if not step.outcome_sources and not step.activation_field_bindings:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_sources_missing"
            )
        target_ids.add(step.target_program_impl_instruction_intent_id)
        target_sequences.add(step.target_sequence)

    available_source_ids = set(initial_outcomes_by_instruction_intent_id) | target_ids
    dependency_edges: dict[UUID, set[UUID]] = {
        step.target_program_impl_instruction_intent_id: set() for step in ordered
    }
    source_not_before_target = False
    for step in ordered:
        seen_source_ids: set[UUID] = set()
        seen_target_attribute_ids: set[UUID] = set()
        for source in step.outcome_sources:
            contract = source.contract
            _require_source_targets_step(source=source, step=step)
            source_id = contract.source_program_impl_instruction_intent_id
            if source_id in seen_source_ids:
                raise ProgramActionContinuationGraphError(
                    "program_action_continuation_graph_duplicate_outcome_source"
                )
            if source_id not in available_source_ids:
                raise ProgramActionContinuationGraphError(
                    "program_action_continuation_graph_source_intent_missing"
                )
            if source_id == step.target_program_impl_instruction_intent_id:
                raise ProgramActionContinuationGraphError(
                    "program_action_continuation_graph_self_dependency"
                )
            if contract.source_sequence >= step.target_sequence:
                source_not_before_target = True
            if source_id in target_ids:
                dependency_edges[step.target_program_impl_instruction_intent_id].add(
                    source_id
                )
            seen_source_ids.add(source_id)
            for binding in (
                *contract.field_bindings,
                *contract.receipt_field_bindings,
            ):
                _claim_target_attribute(
                    seen_target_attribute_ids,
                    binding.target_request_attribute_config_id,
                )

        for binding in step.activation_field_bindings:
            input_key = _normalized_input_key(binding.source_input_key)
            if input_key not in normalized_activation_inputs:
                raise ProgramActionContinuationGraphError(
                    f"program_action_continuation_graph_activation_input_missing:{input_key}"
                )
            _claim_target_attribute(
                seen_target_attribute_ids,
                binding.target_request_attribute_config_id,
            )

    _require_acyclic(dependency_edges)
    if source_not_before_target:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_source_not_before_target"
        )
    return ordered


def _compose_graph_step(
    *,
    step: ProgramActionContinuationGraphStep,
    outcomes_by_instruction_intent_id: Mapping[UUID, ActionDispatchTerminalOutcome],
    activation_inputs_by_key: Mapping[str, ProgramActionContinuationActivationInput],
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> ProgramActionContinuationCompositeResult:
    source_results: list[ProgramActionContinuationResult] = []
    request_payload: dict[str, object] = {}
    target_values: dict[UUID, object] = {}
    activation_keys: set[str] = set()

    for source in sorted(
        step.outcome_sources,
        key=lambda item: (
            item.contract.source_sequence,
            str(item.contract.source_program_impl_instruction_intent_id),
        ),
    ):
        contract = source.contract
        try:
            result = compose_program_action_continuation(
                contract=contract,
                source_outcome=outcomes_by_instruction_intent_id.get(
                    contract.source_program_impl_instruction_intent_id
                ),
                source_response_class_config=source.source_response_class_config,
                target_request_class_config=step.target_request_class_config,
                source_receipt_class_config=source.source_receipt_class_config,
                class_configs_by_id=class_configs_by_id,
            )
        except ProgramActionContinuationError as exc:
            raise ProgramActionContinuationGraphError(str(exc)) from exc
        _merge_values(
            request_payload=request_payload,
            target_values=target_values,
            source_payload=result.request_payload,
            source_values=result.target_values_by_attribute_config_id,
        )
        source_results.append(result)

    target_attributes = resolve_program_action_continuation_class_attributes(
        class_config=step.target_request_class_config,
        class_configs_by_id=class_configs_by_id,
    )
    for binding in sorted(
        step.activation_field_bindings,
        key=lambda item: (
            item.position if item.position is not None else 0,
            _normalized_input_key(item.source_input_key),
            str(item.target_request_attribute_config_id),
            str(item.source_attribute_config_id),
        ),
    ):
        input_key = _normalized_input_key(binding.source_input_key)
        activation_input = activation_inputs_by_key[input_key]
        source_attributes = resolve_program_action_continuation_class_attributes(
            class_config=activation_input.class_config,
            class_configs_by_id=class_configs_by_id,
        )
        source_attribute = source_attributes.get(binding.source_attribute_config_id)
        if source_attribute is None:
            raise ProgramActionContinuationGraphError(
                f"program_action_continuation_graph_activation_attribute_missing:{binding.source_attribute_config_id}"
            )
        target_attribute = target_attributes.get(
            binding.target_request_attribute_config_id
        )
        if target_attribute is None:
            raise ProgramActionContinuationGraphError(
                f"program_action_continuation_target_attribute_not_in_request_class:{binding.target_request_attribute_config_id}"
            )
        try:
            require_program_action_continuation_compatible_types(
                source_attribute=source_attribute,
                target_attribute=target_attribute,
            )
            payload = program_action_continuation_payload_mapping(
                activation_input.payload
            )
        except ProgramActionContinuationError as exc:
            raise ProgramActionContinuationGraphError(str(exc)) from exc
        source_name = str(source_attribute.name or "").strip()
        target_name = str(target_attribute.name or "").strip()
        if not source_name or not target_name:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_attribute_name_missing"
            )
        value = payload.get(source_name)
        if value is None:
            if binding.required or target_attribute.is_required:
                raise ProgramActionContinuationGraphError(
                    f"program_action_continuation_graph_activation_value_missing:{input_key}:{source_name}->{target_name}"
                )
            continue
        _merge_values(
            request_payload=request_payload,
            target_values=target_values,
            source_payload={target_name: value},
            source_values={binding.target_request_attribute_config_id: value},
        )
        activation_keys.add(input_key)

    target_request_class_config_id = step.target_request_class_config.id
    return ProgramActionContinuationCompositeResult(
        target_program_impl_instruction_intent_id=(
            step.target_program_impl_instruction_intent_id
        ),
        target_action_config_id=step.target_action_config_id,
        target_api_capability_endpoint_id=step.target_api_capability_endpoint_id,
        target_request_class_config_id=target_request_class_config_id,
        source_continuations=tuple(source_results),
        activation_input_keys=tuple(sorted(activation_keys)),
        request_payload=MappingProxyType(request_payload),
        target_values_by_attribute_config_id=MappingProxyType(target_values),
    )


def _require_source_targets_step(
    *,
    source: ProgramActionContinuationOutcomeSource,
    step: ProgramActionContinuationGraphStep,
) -> None:
    contract = source.contract
    target_request_class_config_id = step.target_request_class_config.id
    if (
        contract.target_program_impl_instruction_intent_id
        != step.target_program_impl_instruction_intent_id
        or contract.target_sequence != step.target_sequence
        or contract.target_action_config_id != step.target_action_config_id
        or contract.target_api_capability_endpoint_id
        != step.target_api_capability_endpoint_id
        or contract.target_request_class_config_id != target_request_class_config_id
    ):
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_source_target_mismatch"
        )


def _step_dependencies(step: ProgramActionContinuationGraphStep) -> set[UUID]:
    return {
        source.contract.source_program_impl_instruction_intent_id
        for source in step.outcome_sources
    }


def _claim_target_attribute(seen: set[UUID], attribute_id: UUID) -> None:
    if attribute_id in seen:
        raise ProgramActionContinuationGraphError(
            f"program_action_continuation_graph_duplicate_target_attribute:{attribute_id}"
        )
    seen.add(attribute_id)


def _merge_values(
    *,
    request_payload: dict[str, object],
    target_values: dict[UUID, object],
    source_payload: Mapping[str, object],
    source_values: Mapping[UUID, object],
) -> None:
    for attribute_id, value in source_values.items():
        if attribute_id in target_values:
            raise ProgramActionContinuationGraphError(
                f"program_action_continuation_graph_duplicate_target_attribute:{attribute_id}"
            )
        target_values[attribute_id] = value
    for name, value in source_payload.items():
        if name in request_payload:
            raise ProgramActionContinuationGraphError(
                f"program_action_continuation_graph_duplicate_target_name:{name}"
            )
        request_payload[name] = value


def _require_acyclic(dependency_edges: Mapping[UUID, set[UUID]]) -> None:
    visiting: set[UUID] = set()
    visited: set[UUID] = set()

    def visit(node_id: UUID) -> None:
        if node_id in visiting:
            raise ProgramActionContinuationGraphError(
                "program_action_continuation_graph_cycle"
            )
        if node_id in visited:
            return
        visiting.add(node_id)
        for dependency_id in dependency_edges.get(node_id, set()):
            visit(dependency_id)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in dependency_edges:
        visit(node_id)


def _require_target_outcome(
    *,
    step: ProgramActionContinuationGraphStep,
    outcome: ActionDispatchTerminalOutcome | None,
) -> None:
    if outcome is None:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_target_outcome_missing"
        )
    if not outcome.succeeded:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_target_outcome_not_succeeded"
        )
    if outcome.api_capability_endpoint_id != step.target_api_capability_endpoint_id:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_target_endpoint_mismatch"
        )
    if outcome.response_class_config_id != step.target_response_class_config_id:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_target_response_class_mismatch"
        )


def _normalized_input_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ProgramActionContinuationGraphError(
            "program_action_continuation_graph_activation_input_key_missing"
        )
    return normalized


__all__ = [
    "ProgramActionContinuationActivationFieldBinding",
    "ProgramActionContinuationActivationInput",
    "ProgramActionContinuationCompositeResult",
    "ProgramActionContinuationGraphDispatch",
    "ProgramActionContinuationGraphError",
    "ProgramActionContinuationGraphResult",
    "ProgramActionContinuationGraphStep",
    "ProgramActionContinuationOutcomeSource",
    "execute_program_action_continuation_graph",
]
