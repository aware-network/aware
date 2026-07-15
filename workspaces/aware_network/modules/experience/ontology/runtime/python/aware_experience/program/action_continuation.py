from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
)
from aware_meta.class_.inline_value_instance.resolution import (
    resolve_class_config_attribute_configs,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig


class ProgramActionContinuationError(ValueError):
    """A declared Program action continuation cannot be composed safely."""


class ProgramActionContinuationTargetValues(Protocol):
    """Target-anchored values accepted by Experience action dispatch."""

    target_program_impl_instruction_intent_id: UUID
    target_action_config_id: UUID
    target_api_capability_endpoint_id: UUID
    target_request_class_config_id: UUID
    request_payload: Mapping[str, object]
    target_values_by_attribute_config_id: Mapping[UUID, object]


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationFieldBinding:
    source_response_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationReceiptFieldBinding:
    source_receipt_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationContract:
    source_program_impl_instruction_intent_id: UUID
    target_program_impl_instruction_intent_id: UUID
    source_sequence: int
    target_sequence: int
    source_action_config_id: UUID
    target_action_config_id: UUID
    source_api_capability_endpoint_id: UUID
    target_api_capability_endpoint_id: UUID
    source_response_class_config_id: UUID
    target_request_class_config_id: UUID
    field_bindings: tuple[ProgramActionContinuationFieldBinding, ...]
    source_receipt_class_config_id: UUID | None = None
    receipt_field_bindings: tuple[
        ProgramActionContinuationReceiptFieldBinding, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationResult:
    source_program_impl_instruction_intent_id: UUID
    target_program_impl_instruction_intent_id: UUID
    source_action_config_id: UUID
    target_action_config_id: UUID
    source_api_capability_endpoint_id: UUID
    target_api_capability_endpoint_id: UUID
    source_response_class_config_id: UUID
    target_request_class_config_id: UUID
    source_api_call_id: UUID
    source_api_call_key: UUID
    source_api_call_outcome_id: UUID
    source_response_model_id: UUID
    source_receipt_class_config_id: UUID | None
    request_payload: Mapping[str, object]
    target_values_by_attribute_config_id: Mapping[UUID, object]


def compose_program_action_continuation(
    *,
    contract: ProgramActionContinuationContract,
    source_outcome: ActionDispatchTerminalOutcome | None,
    source_response_class_config: ClassConfig,
    target_request_class_config: ClassConfig,
    source_receipt_class_config: ClassConfig | None = None,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ProgramActionContinuationResult:
    """Project declared fields from one typed action outcome into a later request."""

    if source_outcome is None:
        raise ProgramActionContinuationError(
            "program_action_continuation_source_outcome_missing"
        )
    if contract.target_sequence <= contract.source_sequence:
        raise ProgramActionContinuationError(
            "program_action_continuation_target_not_after_source"
        )
    if not contract.field_bindings and not contract.receipt_field_bindings:
        raise ProgramActionContinuationError(
            "program_action_continuation_field_bindings_missing"
        )
    if not source_outcome.succeeded:
        raise ProgramActionContinuationError(
            "program_action_continuation_source_outcome_not_succeeded"
        )
    if (
        source_outcome.api_capability_endpoint_id
        != contract.source_api_capability_endpoint_id
    ):
        raise ProgramActionContinuationError(
            "program_action_continuation_source_endpoint_mismatch"
        )
    if (
        source_outcome.response_class_config_id
        != contract.source_response_class_config_id
    ):
        raise ProgramActionContinuationError(
            "program_action_continuation_source_response_class_mismatch"
        )
    if source_outcome.response_model_id is None:
        raise ProgramActionContinuationError(
            "program_action_continuation_source_response_model_missing"
        )

    _require_class_config_id(
        class_config=source_response_class_config,
        expected_id=contract.source_response_class_config_id,
        label="source_response",
    )
    _require_class_config_id(
        class_config=target_request_class_config,
        expected_id=contract.target_request_class_config_id,
        label="target_request",
    )
    receipt_attributes: dict[UUID, AttributeConfig] = {}
    if contract.receipt_field_bindings:
        if source_receipt_class_config is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_source_receipt_class_missing"
            )
        if contract.source_receipt_class_config_id is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_source_receipt_class_config_id_missing"
            )
        _require_class_config_id(
            class_config=source_receipt_class_config,
            expected_id=contract.source_receipt_class_config_id,
            label="source_receipt",
        )
        receipt_attributes = resolve_program_action_continuation_class_attributes(
            class_config=source_receipt_class_config,
            class_configs_by_id=class_configs_by_id,
        )
    response_payload = program_action_continuation_payload_mapping(
        source_outcome.response_payload
    )
    receipt_payload = _terminal_receipt_payload(
        contract=contract,
        source_outcome=source_outcome,
    )
    source_attributes = resolve_program_action_continuation_class_attributes(
        class_config=source_response_class_config,
        class_configs_by_id=class_configs_by_id,
    )
    target_attributes = resolve_program_action_continuation_class_attributes(
        class_config=target_request_class_config,
        class_configs_by_id=class_configs_by_id,
    )

    request_payload: dict[str, object] = {}
    target_values: dict[UUID, object] = {}
    seen_target_attribute_ids: set[UUID] = set()
    for binding in sorted(
        contract.field_bindings,
        key=lambda item: (
            item.position if item.position is not None else 0,
            str(item.target_request_attribute_config_id),
            str(item.source_response_attribute_config_id),
        ),
    ):
        source_attribute = source_attributes.get(
            binding.source_response_attribute_config_id
        )
        if source_attribute is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_source_attribute_not_in_response_class:"
                f"{binding.source_response_attribute_config_id}"
            )
        target_attribute = target_attributes.get(
            binding.target_request_attribute_config_id
        )
        if target_attribute is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_target_attribute_not_in_request_class:"
                f"{binding.target_request_attribute_config_id}"
            )
        if binding.target_request_attribute_config_id in seen_target_attribute_ids:
            raise ProgramActionContinuationError(
                "program_action_continuation_duplicate_target_attribute:"
                f"{binding.target_request_attribute_config_id}"
            )
        seen_target_attribute_ids.add(binding.target_request_attribute_config_id)
        require_program_action_continuation_compatible_types(
            source_attribute=source_attribute,
            target_attribute=target_attribute,
        )

        source_name = str(source_attribute.name or "").strip()
        target_name = str(target_attribute.name or "").strip()
        if not source_name or not target_name:
            raise ProgramActionContinuationError(
                "program_action_continuation_attribute_name_missing"
            )
        value = response_payload.get(source_name)
        if value is None:
            if binding.required or target_attribute.is_required:
                raise ProgramActionContinuationError(
                    "program_action_continuation_source_value_missing:"
                    f"{source_name}->{target_name}"
                )
            continue
        request_payload[target_name] = value
        target_values[binding.target_request_attribute_config_id] = value

    for binding in sorted(
        contract.receipt_field_bindings,
        key=lambda item: (
            item.position if item.position is not None else 0,
            str(item.target_request_attribute_config_id),
            str(item.source_receipt_attribute_config_id),
        ),
    ):
        source_attribute = receipt_attributes.get(
            binding.source_receipt_attribute_config_id
        )
        if source_attribute is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_source_attribute_not_in_receipt_class:"
                f"{binding.source_receipt_attribute_config_id}"
            )
        target_attribute = target_attributes.get(
            binding.target_request_attribute_config_id
        )
        if target_attribute is None:
            raise ProgramActionContinuationError(
                "program_action_continuation_target_attribute_not_in_request_class:"
                f"{binding.target_request_attribute_config_id}"
            )
        if binding.target_request_attribute_config_id in seen_target_attribute_ids:
            raise ProgramActionContinuationError(
                "program_action_continuation_duplicate_target_attribute:"
                f"{binding.target_request_attribute_config_id}"
            )
        seen_target_attribute_ids.add(binding.target_request_attribute_config_id)
        require_program_action_continuation_compatible_types(
            source_attribute=source_attribute,
            target_attribute=target_attribute,
        )

        source_name = str(source_attribute.name or "").strip()
        target_name = str(target_attribute.name or "").strip()
        if not source_name or not target_name:
            raise ProgramActionContinuationError(
                "program_action_continuation_attribute_name_missing"
            )
        if source_name not in receipt_payload:
            raise ProgramActionContinuationError(
                "program_action_continuation_receipt_field_not_allowed:"
                f"{source_name}"
            )
        value = receipt_payload[source_name]
        if value is None:
            if binding.required or target_attribute.is_required:
                raise ProgramActionContinuationError(
                    "program_action_continuation_receipt_value_missing:"
                    f"{source_name}->{target_name}"
                )
            continue
        request_payload[target_name] = value
        target_values[binding.target_request_attribute_config_id] = value

    return ProgramActionContinuationResult(
        source_program_impl_instruction_intent_id=(
            contract.source_program_impl_instruction_intent_id
        ),
        target_program_impl_instruction_intent_id=(
            contract.target_program_impl_instruction_intent_id
        ),
        source_action_config_id=contract.source_action_config_id,
        target_action_config_id=contract.target_action_config_id,
        source_api_capability_endpoint_id=(contract.source_api_capability_endpoint_id),
        target_api_capability_endpoint_id=(contract.target_api_capability_endpoint_id),
        source_response_class_config_id=contract.source_response_class_config_id,
        target_request_class_config_id=contract.target_request_class_config_id,
        source_api_call_id=source_outcome.api_call_id,
        source_api_call_key=source_outcome.api_call_key,
        source_api_call_outcome_id=source_outcome.api_call_outcome_id,
        source_response_model_id=source_outcome.response_model_id,
        source_receipt_class_config_id=contract.source_receipt_class_config_id,
        request_payload=MappingProxyType(request_payload),
        target_values_by_attribute_config_id=MappingProxyType(target_values),
    )


def _terminal_receipt_payload(
    *,
    contract: ProgramActionContinuationContract,
    source_outcome: ActionDispatchTerminalOutcome,
) -> Mapping[str, object | None]:
    return {
        "status": source_outcome.status,
        "endpoint_ref": source_outcome.endpoint_ref,
        "discriminant": source_outcome.discriminant,
        "source_program_impl_instruction_intent_id": (
            contract.source_program_impl_instruction_intent_id
        ),
        "source_action_config_id": contract.source_action_config_id,
        "api_capability_endpoint_id": source_outcome.api_capability_endpoint_id,
        "api_call_id": source_outcome.api_call_id,
        "api_call_key": source_outcome.api_call_key,
        "request_model_id": source_outcome.request_model_id,
        "api_call_outcome_id": source_outcome.api_call_outcome_id,
        "response_model_id": source_outcome.response_model_id,
        "response_class_config_id": source_outcome.response_class_config_id,
        "service_operation_id": source_outcome.service_operation_id,
        "service_operation_config_id": source_outcome.service_operation_config_id,
        "service_operation_commit_id": source_outcome.service_operation_commit_id,
        "service_operation_head_commit_id": (
            source_outcome.service_operation_head_commit_id
        ),
        "service_operation_branch_id": source_outcome.service_operation_branch_id,
        "service_operation_projection_hash": (
            source_outcome.service_operation_projection_hash
        ),
        "api_call_outcome_commit_id": source_outcome.api_call_outcome_commit_id,
        "api_call_outcome_head_commit_id": (
            source_outcome.api_call_outcome_head_commit_id
        ),
        "api_call_outcome_branch_id": source_outcome.api_call_outcome_branch_id,
        "api_call_outcome_projection_hash": (
            source_outcome.api_call_outcome_projection_hash
        ),
    }


def _require_class_config_id(
    *,
    class_config: ClassConfig,
    expected_id: UUID,
    label: str,
) -> None:
    if class_config.id != expected_id:
        raise ProgramActionContinuationError(
            f"program_action_continuation_{label}_class_config_mismatch"
        )


def resolve_program_action_continuation_class_attributes(
    *,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> dict[UUID, AttributeConfig]:
    attributes: dict[UUID, AttributeConfig] = {}
    for link in resolve_class_config_attribute_configs(
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    ):
        attribute = link.attribute_config
        if attribute is None or attribute.id is None:
            continue
        attributes[attribute.id] = attribute
    return attributes


def require_program_action_continuation_compatible_types(
    *,
    source_attribute: AttributeConfig,
    target_attribute: AttributeConfig,
) -> None:
    source_descriptor_id = source_attribute.type_descriptor_id
    target_descriptor_id = target_attribute.type_descriptor_id
    if source_descriptor_id is None or target_descriptor_id is None:
        raise ProgramActionContinuationError(
            "program_action_continuation_type_descriptor_missing"
        )
    if source_descriptor_id != target_descriptor_id:
        raise ProgramActionContinuationError(
            "program_action_continuation_type_descriptor_mismatch:"
            f"{source_attribute.name}->{target_attribute.name}"
        )


def program_action_continuation_payload_mapping(
    value: object | None,
) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    raise ProgramActionContinuationError(
        "program_action_continuation_source_response_payload_not_object"
    )


__all__ = [
    "ProgramActionContinuationContract",
    "ProgramActionContinuationError",
    "ProgramActionContinuationFieldBinding",
    "ProgramActionContinuationResult",
    "ProgramActionContinuationTargetValues",
    "compose_program_action_continuation",
    "program_action_continuation_payload_mapping",
    "require_program_action_continuation_compatible_types",
    "resolve_program_action_continuation_class_attributes",
]
