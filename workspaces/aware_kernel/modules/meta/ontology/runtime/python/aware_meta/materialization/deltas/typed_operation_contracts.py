from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from aware_meta.materialization.deltas.coercion import (
    mapping_or_none,
    mapping_value,
    optional_text,
    string_value,
    tuple_mappings,
    tuple_text,
)
from aware_meta.materialization.deltas.constants import (
    META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaTypedOperation:
    operation_kind: str
    operation_key: str
    operation_family: str
    provider_operation_type: str
    semantic_key: str
    ontology_subject_kind: str
    semantic_subject_type: str | None = None
    source_entry_key: str | None = None
    source_delta_key: str | None = None
    source_refs: tuple[str, ...] = ()
    baseline: Mapping[str, object] = field(default_factory=dict)
    current: Mapping[str, object] = field(default_factory=dict)
    ocg_operation: Mapping[str, object] | None = None
    source_semantic_change: Mapping[str, object] | None = None
    semantic_change_projection: Mapping[str, object] | None = None
    function_call_plan: Mapping[str, object] | None = None
    blocked: bool = False
    blocked_reason: str | None = None
    would_execute: bool = False
    did_execute: bool = False
    would_persist: bool = False
    did_persist: bool = False
    execution_wired: bool = False
    production_execution_wired: bool = False
    include_operation_evidence: bool = False
    extra: Mapping[str, object] = field(default_factory=dict)
    contract_version: str = META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaTypedOperation | None":
        operation_key = optional_text(payload.get("operation_key"))
        semantic_key = optional_text(payload.get("semantic_key"))
        if operation_key is None or semantic_key is None:
            return None
        operation_kind = (
            optional_text(payload.get("operation_kind"))
            or "meta_ocg_provider_delta_typed_operation"
        )
        operation_evidence_keys = {
            "ocg_operation",
            "source_semantic_change",
            "semantic_change_projection",
            "function_call_plan",
            "blocked_reason",
        }
        known_keys = {
            "operation_kind",
            "contract_version",
            "operation_key",
            "operation_family",
            "provider_operation_type",
            "semantic_key",
            "semantic_subject_type",
            "ontology_subject_kind",
            "source_entry_key",
            "source_delta_key",
            "source_refs",
            "baseline",
            "current",
            "ocg_operation",
            "source_semantic_change",
            "semantic_change_projection",
            "function_call_plan",
            "blocked",
            "blocked_reason",
            "would_execute",
            "did_execute",
            "would_persist",
            "did_persist",
            "execution_wired",
            "production_execution_wired",
        }
        return cls(
            operation_kind=operation_kind,
            contract_version=(
                optional_text(payload.get("contract_version"))
                or META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION
            ),
            operation_key=operation_key,
            operation_family=string_value(payload.get("operation_family")),
            provider_operation_type=string_value(
                payload.get("provider_operation_type")
            ),
            semantic_key=semantic_key,
            semantic_subject_type=optional_text(payload.get("semantic_subject_type")),
            ontology_subject_kind=string_value(payload.get("ontology_subject_kind")),
            source_entry_key=optional_text(payload.get("source_entry_key")),
            source_delta_key=optional_text(payload.get("source_delta_key")),
            source_refs=tuple_text(payload.get("source_refs")),
            baseline=mapping_value(payload.get("baseline")),
            current=mapping_value(payload.get("current")),
            ocg_operation=mapping_or_none(payload.get("ocg_operation")),
            source_semantic_change=mapping_or_none(
                payload.get("source_semantic_change")
            ),
            semantic_change_projection=mapping_or_none(
                payload.get("semantic_change_projection")
            ),
            function_call_plan=mapping_or_none(payload.get("function_call_plan")),
            blocked=payload.get("blocked") is True,
            blocked_reason=optional_text(payload.get("blocked_reason")),
            would_execute=payload.get("would_execute") is True,
            did_execute=payload.get("did_execute") is True,
            would_persist=payload.get("would_persist") is True,
            did_persist=payload.get("did_persist") is True,
            execution_wired=payload.get("execution_wired") is True,
            production_execution_wired=(
                payload.get("production_execution_wired") is True
            ),
            include_operation_evidence=(
                operation_kind == "meta_ocg_provider_delta_typed_operation"
                or any(key in payload for key in operation_evidence_keys)
            ),
            extra={
                str(key): value
                for key, value in payload.items()
                if str(key) not in known_keys
            },
        )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "operation_kind": self.operation_kind,
            "contract_version": self.contract_version,
            "operation_key": self.operation_key,
            "operation_family": self.operation_family,
            "provider_operation_type": self.provider_operation_type,
            "semantic_key": self.semantic_key,
            "semantic_subject_type": self.semantic_subject_type,
            "ontology_subject_kind": self.ontology_subject_kind,
            "source_entry_key": self.source_entry_key,
            "source_delta_key": self.source_delta_key,
            "source_refs": self.source_refs,
            "baseline": dict(self.baseline),
            "current": dict(self.current),
        }
        payload.update(dict(self.extra))
        if self.include_operation_evidence:
            payload.update(
                {
                    "ocg_operation": (
                        dict(self.ocg_operation)
                        if self.ocg_operation is not None
                        else None
                    ),
                    "source_semantic_change": (
                        dict(self.source_semantic_change)
                        if self.source_semantic_change is not None
                        else None
                    ),
                    "semantic_change_projection": (
                        dict(self.semantic_change_projection)
                        if self.semantic_change_projection is not None
                        else None
                    ),
                    "function_call_plan": (
                        dict(self.function_call_plan)
                        if self.function_call_plan is not None
                        else None
                    ),
                    "blocked_reason": self.blocked_reason,
                }
            )
        payload.update(
            {
                "blocked": self.blocked,
                "would_execute": self.would_execute,
                "did_execute": self.did_execute,
                "would_persist": self.would_persist,
                "did_persist": self.did_persist,
                "execution_wired": self.execution_wired,
                "production_execution_wired": self.production_execution_wired,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaTypedOperationPlan:
    payload: Mapping[str, object]
    typed_operations: tuple[MetaProviderDeltaTypedOperation, ...]
    semantic_object_anchors: tuple[MetaProviderDeltaTypedOperation, ...]
    blocked_operations: tuple[MetaProviderDeltaTypedOperation, ...]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaTypedOperationPlan":
        return cls(
            payload={str(key): value for key, value in payload.items()},
            typed_operations=typed_operations_from_payloads(
                payload.get("typed_operations")
            ),
            semantic_object_anchors=typed_operations_from_payloads(
                payload.get("semantic_object_anchors")
            ),
            blocked_operations=typed_operations_from_payloads(
                payload.get("blocked_operations")
            ),
        )

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    def evidence_payload(self) -> dict[str, object]:
        payload = {str(key): value for key, value in self.payload.items()}
        payload["typed_operations"] = tuple(
            operation.evidence_payload() for operation in self.typed_operations
        )
        payload["semantic_object_anchors"] = tuple(
            operation.evidence_payload() for operation in self.semantic_object_anchors
        )
        payload["blocked_operations"] = tuple(
            operation.evidence_payload() for operation in self.blocked_operations
        )
        return payload


def typed_operations_from_payloads(
    value: object,
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    operations: list[MetaProviderDeltaTypedOperation] = []
    for payload in tuple_mappings(value):
        operation = MetaProviderDeltaTypedOperation.from_payload(payload)
        if operation is not None:
            operations.append(operation)
    return tuple(operations)


__all__ = [
    "MetaProviderDeltaTypedOperation",
    "MetaProviderDeltaTypedOperationPlan",
    "typed_operations_from_payloads",
]
