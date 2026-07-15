from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.contracts import (
    MetaProviderDeltaTypedOperation,
    MetaProviderDeltaTypedOperationPlan,
    mapping_value as _contract_mapping_value,
    optional_text as _contract_optional_text,
    string_value as _contract_string_value,
    tuple_mappings as _contract_tuple_mappings,
    tuple_text as _contract_tuple_text,
)
from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyTypedOperation,
)


def typed_operations_from_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> tuple[OntologyTypedOperation, ...]:
    plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    return _ontology_operations_from_typed_operations(plan.typed_operations)


def semantic_object_anchors_from_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> tuple[OntologyTypedOperation, ...]:
    plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    return _ontology_operations_from_typed_operations(plan.semantic_object_anchors)


def _ontology_operations_from_typed_operations(
    typed_operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[OntologyTypedOperation, ...]:
    operations: list[OntologyTypedOperation] = []
    for operation in typed_operations:
        operations.append(
            OntologyTypedOperation(
                operation_key=operation.operation_key,
                operation_family=operation.operation_family,
                provider_operation_type=operation.provider_operation_type,
                semantic_key=operation.semantic_key,
                ontology_subject_kind=operation.ontology_subject_kind,
                baseline=dict(operation.baseline),
                current=dict(operation.current),
                source_refs=operation.source_refs,
            )
        )
    return tuple(operations)


def mapping_value(value: object) -> dict[str, object]:
    return _contract_mapping_value(value)


def optional_text(value: object) -> str | None:
    return _contract_optional_text(value)


def string_value(value: object) -> str:
    return _contract_string_value(value)


def tuple_text(value: object) -> tuple[str, ...]:
    return _contract_tuple_text(value)


def tuple_mappings(value: object) -> tuple[dict[str, object], ...]:
    return _contract_tuple_mappings(value)


__all__ = [
    "mapping_value",
    "optional_text",
    "semantic_object_anchors_from_plan",
    "string_value",
    "tuple_mappings",
    "tuple_text",
    "typed_operations_from_plan",
]
