from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.coercion import (
    int_mapping_value,
    int_value,
    mapping_value,
    optional_text,
    string_value,
    tuple_mappings,
    tuple_text,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaMutationStep:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaMutationStep | None":
        step_key = optional_text(payload.get("step_key"))
        semantic_key = optional_text(payload.get("semantic_key"))
        if step_key is None and semantic_key is None:
            return None
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def ready(self) -> bool:
        return self.status == "mutation_step_ready"

    @property
    def blocked(self) -> bool:
        return self.status == "mutation_step_blocked"

    @property
    def step_key(self) -> str | None:
        return optional_text(self.payload.get("step_key"))

    @property
    def source_typed_operation_key(self) -> str | None:
        return optional_text(self.payload.get("source_typed_operation_key"))

    @property
    def source_entry_key(self) -> str | None:
        return optional_text(self.payload.get("source_entry_key"))

    @property
    def source_delta_key(self) -> str | None:
        return optional_text(self.payload.get("source_delta_key"))

    @property
    def source_refs(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("source_refs"))

    @property
    def semantic_key(self) -> str | None:
        return optional_text(self.payload.get("semantic_key"))

    @property
    def operation_family(self) -> str:
        return string_value(self.payload.get("operation_family"))

    @property
    def provider_operation_type(self) -> str:
        return string_value(self.payload.get("provider_operation_type"))

    @property
    def semantic_subject_type(self) -> str | None:
        return optional_text(self.payload.get("semantic_subject_type"))

    @property
    def ontology_subject_kind(self) -> str:
        return string_value(self.payload.get("ontology_subject_kind"))

    @property
    def function_ref(self) -> str | None:
        return optional_text(self.payload.get("function_ref"))

    @property
    def receiver_semantic_key(self) -> str | None:
        return optional_text(self.payload.get("receiver_semantic_key"))

    @property
    def receiver_object_id(self) -> str | None:
        return optional_text(self.payload.get("receiver_object_id"))

    @property
    def receiver_source(self) -> str | None:
        return optional_text(self.payload.get("receiver_source"))

    @property
    def receiver_entity_kind(self) -> str | None:
        return optional_text(self.payload.get("receiver_entity_kind"))

    @property
    def receiver_entity_id(self) -> str | None:
        return optional_text(self.payload.get("receiver_entity_id"))

    @property
    def receiver_entity_path(self) -> str | None:
        return optional_text(self.payload.get("receiver_entity_path"))

    @property
    def arguments(self) -> dict[str, object]:
        return mapping_value(self.payload.get("arguments"))

    @property
    def argument_refs(self) -> dict[str, object]:
        return mapping_value(self.payload.get("argument_refs"))

    @property
    def dependencies(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("dependencies"))

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("blockers"))

    @property
    def baseline(self) -> dict[str, object]:
        return mapping_value(self.payload.get("baseline"))

    @property
    def current(self) -> dict[str, object]:
        return mapping_value(self.payload.get("current"))

    @property
    def candidate_arguments(self) -> dict[str, object]:
        return mapping_value(self.payload.get("candidate_arguments"))

    @property
    def function_call_plan(self) -> dict[str, object]:
        return mapping_value(self.payload.get("function_call_plan"))

    @property
    def receiver_resolution(self) -> dict[str, object]:
        return mapping_value(self.payload.get("receiver_resolution"))

    @property
    def method_binding(self) -> dict[str, object]:
        return mapping_value(self.payload.get("method_binding"))

    @property
    def attribute_descriptor_kind(self) -> str | None:
        return optional_text(self.payload.get("attribute_descriptor_kind"))

    @property
    def attribute_descriptor_resolution(self) -> dict[str, object]:
        return mapping_value(self.payload.get("attribute_descriptor_resolution"))

    @property
    def would_execute(self) -> bool:
        return self.payload.get("would_execute") is True

    @property
    def did_execute(self) -> bool:
        return self.payload.get("did_execute") is True

    @property
    def would_persist(self) -> bool:
        return self.payload.get("would_persist") is True

    @property
    def did_persist(self) -> bool:
        return self.payload.get("did_persist") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaMutationPlan:
    payload: Mapping[str, object]
    mutation_steps: tuple[MetaProviderDeltaMutationStep, ...]
    blocked_mutation_steps: tuple[MetaProviderDeltaMutationStep, ...]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaMutationPlan":
        return cls(
            payload={str(key): value for key, value in payload.items()},
            mutation_steps=mutation_steps_from_payloads(
                payload.get("mutation_steps")
            ),
            blocked_mutation_steps=mutation_steps_from_payloads(
                payload.get("blocked_mutation_steps")
            ),
        )

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def ready(self) -> bool:
        return (
            self.status == "mutation_plan_ready"
            and self.payload.get("blocked") is not True
        )

    @property
    def partially_blocked(self) -> bool:
        return self.status == "mutation_plan_partially_blocked"

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def available(self) -> bool:
        return self.payload.get("available") is True

    @property
    def typed_operation_plan_status(self) -> str | None:
        return optional_text(self.payload.get("typed_operation_plan_status"))

    @property
    def typed_operation_count(self) -> int:
        return int_value(self.payload.get("typed_operation_count"))

    @property
    def semantic_object_anchor_count(self) -> int:
        return int_value(self.payload.get("semantic_object_anchor_count"))

    @property
    def blocked_typed_operation_count(self) -> int:
        return int_value(self.payload.get("blocked_typed_operation_count"))

    @property
    def source_operation_count(self) -> int:
        return int_value(self.payload.get("source_operation_count"))

    @property
    def mutation_step_count(self) -> int:
        return int_value(self.payload.get("mutation_step_count"))

    @property
    def blocked_mutation_step_count(self) -> int:
        return int_value(self.payload.get("blocked_mutation_step_count"))

    @property
    def mutation_step_operation_counts(self) -> dict[str, int]:
        return int_mapping_value(self.payload.get("mutation_step_operation_counts"))

    @property
    def blocked_mutation_step_reason_counts(self) -> dict[str, int]:
        return int_mapping_value(
            self.payload.get("blocked_mutation_step_reason_counts")
        )

    def steps_for_subject(
        self,
        ontology_subject_kind: str,
    ) -> tuple[MetaProviderDeltaMutationStep, ...]:
        return tuple(
            step
            for step in self.mutation_steps
            if step.ontology_subject_kind == ontology_subject_kind
        )

    def evidence_payload(self) -> dict[str, object]:
        payload = {str(key): value for key, value in self.payload.items()}
        payload["mutation_steps"] = tuple(
            step.evidence_payload() for step in self.mutation_steps
        )
        payload["blocked_mutation_steps"] = tuple(
            step.evidence_payload() for step in self.blocked_mutation_steps
        )
        return payload


def mutation_steps_from_payloads(
    value: object,
) -> tuple[MetaProviderDeltaMutationStep, ...]:
    steps: list[MetaProviderDeltaMutationStep] = []
    for payload in tuple_mappings(value):
        step = MetaProviderDeltaMutationStep.from_payload(payload)
        if step is not None:
            steps.append(step)
    return tuple(steps)


__all__ = [
    "MetaProviderDeltaMutationPlan",
    "MetaProviderDeltaMutationStep",
    "mutation_steps_from_payloads",
]
