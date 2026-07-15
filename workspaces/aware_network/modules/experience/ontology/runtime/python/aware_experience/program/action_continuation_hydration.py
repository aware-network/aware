from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_experience.program.action_continuation import (
    ProgramActionContinuationContract,
    ProgramActionContinuationFieldBinding,
    ProgramActionContinuationReceiptFieldBinding,
    require_program_action_continuation_compatible_types,
    resolve_program_action_continuation_class_attributes,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationFieldBinding,
    ProgramActionContinuationGraphStep,
    ProgramActionContinuationOutcomeSource,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_reactivity_ontology.action.action_config import ActionConfig


class ProgramActionContinuationHydrationError(ValueError):
    """Committed Program continuation truth cannot hydrate safely."""


@dataclass(frozen=True, slots=True)
class HydratedProgramActionContinuationGraph:
    initial_program_impl_instruction_intent_ids: tuple[UUID, ...]
    activation_input_class_config_ids_by_key: Mapping[str, UUID]
    steps: tuple[ProgramActionContinuationGraphStep, ...]


def hydrate_program_action_continuation_graph(
    *,
    snapshot: ProgramOntologySnapshot,
    action_configs_by_id: Mapping[UUID, ActionConfig],
    api_capability_endpoints_by_id: Mapping[UUID, ApiCapabilityEndpoint],
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> HydratedProgramActionContinuationGraph:
    sequence_by_intent_id: dict[UUID, int] = {}
    intents_by_id = dict(snapshot.instruction_intents_by_id)
    intents_by_key: dict[str, ProgramImplInstructionIntent] = {}
    for instruction in snapshot.instruction_rows:
        intent = getattr(instruction, "instruction_intent", None)
        intent_id = getattr(intent, "id", None)
        if not isinstance(intent_id, UUID):
            raw_intent_id = getattr(instruction, "instruction_intent_id", None)
            intent_id = raw_intent_id if isinstance(raw_intent_id, UUID) else None
        if intent_id is None or intent_id not in intents_by_id:
            continue
        sequence_by_intent_id[intent_id] = int(instruction.sequence)
        intent_row = intents_by_id[intent_id]
        key = (intent_row.continuation_key or "").strip()
        if not key:
            continue
        if key in intents_by_key:
            raise ProgramActionContinuationHydrationError(
                f"program_action_continuation_duplicate_key:{key}"
            )
        intents_by_key[key] = intent_row

    if not intents_by_key:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_intents_missing"
        )

    activation_classes: dict[str, UUID] = {}
    incoming_intent_ids: set[UUID] = set()
    steps: list[ProgramActionContinuationGraphStep] = []
    for _target_key, target in sorted(
        intents_by_key.items(),
        key=lambda item: sequence_by_intent_id[item[1].id],
    ):
        target_sequence = sequence_by_intent_id.get(target.id)
        if target_sequence is None:
            raise ProgramActionContinuationHydrationError(
                f"program_action_continuation_sequence_missing:{target.id}"
            )
        target_action, target_endpoint, target_request, target_response = (
            _validate_intent_contract(
                intent=target,
                action_configs_by_id=action_configs_by_id,
                api_capability_endpoints_by_id=api_capability_endpoints_by_id,
                class_configs_by_id=class_configs_by_id,
            )
        )
        activation_rows = snapshot.activation_field_bindings_by_intent_id.get(
            target.id, ()
        )
        outcome_rows = snapshot.outcome_field_bindings_by_intent_id.get(target.id, ())
        receipt_rows = snapshot.receipt_field_bindings_by_intent_id.get(target.id, ())
        if not activation_rows and not outcome_rows and not receipt_rows:
            continue
        incoming_intent_ids.add(target.id)

        activation_bindings: list[ProgramActionContinuationActivationFieldBinding] = []
        target_attributes = resolve_program_action_continuation_class_attributes(
            class_config=target_request,
            class_configs_by_id=class_configs_by_id,
        )
        for row in activation_rows:
            input_key = (row.source_input_key or "").strip()
            source_class = _required_class_config(
                class_configs_by_id,
                row.source_class_config_id,
                label="activation_source",
            )
            prior_class_id = activation_classes.setdefault(input_key, source_class.id)
            if prior_class_id != source_class.id:
                raise ProgramActionContinuationHydrationError(
                    f"program_action_continuation_activation_class_ambiguous:{input_key}"
                )
            source_attributes = resolve_program_action_continuation_class_attributes(
                class_config=source_class,
                class_configs_by_id=class_configs_by_id,
            )
            _validate_attribute_pair(
                source_attributes=source_attributes,
                source_attribute_id=row.source_attribute_config_id,
                target_attributes=target_attributes,
                target_attribute_id=row.target_request_attribute_config_id,
            )
            activation_bindings.append(
                ProgramActionContinuationActivationFieldBinding(
                    source_input_key=input_key,
                    source_attribute_config_id=row.source_attribute_config_id,
                    target_request_attribute_config_id=(
                        row.target_request_attribute_config_id
                    ),
                    required=row.required,
                    position=row.position,
                )
            )

        outcome_sources: list[ProgramActionContinuationOutcomeSource] = []
        source_ids = {
            row.source_program_impl_instruction_intent_id for row in outcome_rows
        } | {row.source_program_impl_instruction_intent_id for row in receipt_rows}
        for source_id in sorted(
            source_ids,
            key=lambda value: (
                sequence_by_intent_id[value]
                if value in sequence_by_intent_id
                else 2**31
            ),
        ):
            source = intents_by_id.get(source_id)
            source_sequence = sequence_by_intent_id.get(source_id)
            if source is None or source_sequence is None:
                raise ProgramActionContinuationHydrationError(
                    f"program_action_continuation_source_missing:{source_id}"
                )
            if source_sequence >= target_sequence:
                raise ProgramActionContinuationHydrationError(
                    "program_action_continuation_source_not_before_target"
                )
            source_action, source_endpoint, _source_request, source_response = (
                _validate_intent_contract(
                    intent=source,
                    action_configs_by_id=action_configs_by_id,
                    api_capability_endpoints_by_id=api_capability_endpoints_by_id,
                    class_configs_by_id=class_configs_by_id,
                )
            )
            source_attributes = resolve_program_action_continuation_class_attributes(
                class_config=source_response,
                class_configs_by_id=class_configs_by_id,
            )
            field_bindings: list[ProgramActionContinuationFieldBinding] = []
            for row in outcome_rows:
                if row.source_program_impl_instruction_intent_id != source_id:
                    continue
                _validate_attribute_pair(
                    source_attributes=source_attributes,
                    source_attribute_id=row.source_response_attribute_config_id,
                    target_attributes=target_attributes,
                    target_attribute_id=row.target_request_attribute_config_id,
                )
                field_bindings.append(
                    ProgramActionContinuationFieldBinding(
                        source_response_attribute_config_id=(
                            row.source_response_attribute_config_id
                        ),
                        target_request_attribute_config_id=(
                            row.target_request_attribute_config_id
                        ),
                        required=row.required,
                        position=row.position,
                    )
                )

            source_receipt_class: ClassConfig | None = None
            receipt_bindings: list[ProgramActionContinuationReceiptFieldBinding] = []
            for row in receipt_rows:
                if row.source_program_impl_instruction_intent_id != source_id:
                    continue
                candidate_receipt_class = _required_class_config(
                    class_configs_by_id,
                    row.source_receipt_class_config_id,
                    label="source_receipt",
                )
                if (
                    source_receipt_class is not None
                    and source_receipt_class.id != candidate_receipt_class.id
                ):
                    raise ProgramActionContinuationHydrationError(
                        "program_action_continuation_receipt_class_ambiguous"
                    )
                source_receipt_class = candidate_receipt_class
                receipt_attributes = (
                    resolve_program_action_continuation_class_attributes(
                        class_config=candidate_receipt_class,
                        class_configs_by_id=class_configs_by_id,
                    )
                )
                _validate_attribute_pair(
                    source_attributes=receipt_attributes,
                    source_attribute_id=row.source_receipt_attribute_config_id,
                    target_attributes=target_attributes,
                    target_attribute_id=row.target_request_attribute_config_id,
                )
                receipt_bindings.append(
                    ProgramActionContinuationReceiptFieldBinding(
                        source_receipt_attribute_config_id=(
                            row.source_receipt_attribute_config_id
                        ),
                        target_request_attribute_config_id=(
                            row.target_request_attribute_config_id
                        ),
                        required=row.required,
                        position=row.position,
                    )
                )
            outcome_sources.append(
                ProgramActionContinuationOutcomeSource(
                    contract=ProgramActionContinuationContract(
                        source_program_impl_instruction_intent_id=source.id,
                        target_program_impl_instruction_intent_id=target.id,
                        source_sequence=source_sequence,
                        target_sequence=target_sequence,
                        source_action_config_id=source_action.id,
                        target_action_config_id=target_action.id,
                        source_api_capability_endpoint_id=source_endpoint.id,
                        target_api_capability_endpoint_id=target_endpoint.id,
                        source_response_class_config_id=source_response.id,
                        target_request_class_config_id=target_request.id,
                        field_bindings=tuple(field_bindings),
                        source_receipt_class_config_id=(
                            source_receipt_class.id
                            if source_receipt_class is not None
                            else None
                        ),
                        receipt_field_bindings=tuple(receipt_bindings),
                    ),
                    source_response_class_config=source_response,
                    source_receipt_class_config=source_receipt_class,
                )
            )
        steps.append(
            ProgramActionContinuationGraphStep(
                target_program_impl_instruction_intent_id=target.id,
                target_sequence=target_sequence,
                target_action_config_id=target_action.id,
                target_api_capability_endpoint_id=target_endpoint.id,
                target_request_class_config=target_request,
                target_response_class_config_id=target_response.id,
                outcome_sources=tuple(outcome_sources),
                activation_field_bindings=tuple(activation_bindings),
            )
        )

    initial_ids = tuple(
        intent.id
        for intent in sorted(
            intents_by_key.values(), key=lambda row: sequence_by_intent_id[row.id]
        )
        if intent.id not in incoming_intent_ids
    )
    if not initial_ids or not steps:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_graph_incomplete"
        )
    return HydratedProgramActionContinuationGraph(
        initial_program_impl_instruction_intent_ids=initial_ids,
        activation_input_class_config_ids_by_key=MappingProxyType(
            dict(activation_classes)
        ),
        steps=tuple(steps),
    )


def _validate_intent_contract(
    *,
    intent: ProgramImplInstructionIntent,
    action_configs_by_id: Mapping[UUID, ActionConfig],
    api_capability_endpoints_by_id: Mapping[UUID, ApiCapabilityEndpoint],
    class_configs_by_id: Mapping[UUID, ClassConfig],
) -> tuple[ActionConfig, ApiCapabilityEndpoint, ClassConfig, ClassConfig]:
    endpoint_id = intent.api_capability_endpoint_id
    request_class_id = intent.request_class_config_id
    response_class_id = intent.response_class_config_id
    if endpoint_id is None or request_class_id is None or response_class_id is None:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_intent_contract_pin_missing"
        )
    action = action_configs_by_id.get(intent.action_config_id)
    endpoint = api_capability_endpoints_by_id.get(endpoint_id)
    request_class = _required_class_config(
        class_configs_by_id, request_class_id, label="request"
    )
    response_class = _required_class_config(
        class_configs_by_id, response_class_id, label="response"
    )
    if action is None or endpoint is None:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_action_or_endpoint_missing"
        )
    if action.api_capability_endpoint_id != endpoint.id:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_action_endpoint_mismatch"
        )
    request_config = endpoint.request_config
    response_config = request_config.response_config if request_config else None
    if (
        request_config is None
        or request_config.class_config_id != request_class.id
        or response_config is None
        or response_config.class_config_id != response_class.id
    ):
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_endpoint_class_config_mismatch"
        )
    return action, endpoint, request_class, response_class


def _required_class_config(
    class_configs_by_id: Mapping[UUID, ClassConfig],
    class_config_id: UUID | None,
    *,
    label: str,
) -> ClassConfig:
    if class_config_id is None or class_config_id not in class_configs_by_id:
        raise ProgramActionContinuationHydrationError(
            f"program_action_continuation_{label}_class_config_missing:{class_config_id}"
        )
    return class_configs_by_id[class_config_id]


def _validate_attribute_pair(
    *,
    source_attributes: Mapping[UUID, AttributeConfig],
    source_attribute_id: UUID,
    target_attributes: Mapping[UUID, AttributeConfig],
    target_attribute_id: UUID,
) -> None:
    source_attribute = source_attributes.get(source_attribute_id)
    target_attribute = target_attributes.get(target_attribute_id)
    if source_attribute is None or target_attribute is None:
        raise ProgramActionContinuationHydrationError(
            "program_action_continuation_attribute_not_in_declared_class"
        )
    try:
        require_program_action_continuation_compatible_types(
            source_attribute=source_attribute,
            target_attribute=target_attribute,
        )
    except ValueError as exc:
        raise ProgramActionContinuationHydrationError(str(exc)) from exc


__all__ = [
    "HydratedProgramActionContinuationGraph",
    "ProgramActionContinuationHydrationError",
    "hydrate_program_action_continuation_graph",
]
