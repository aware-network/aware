from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.coercion import (
    int_value,
    mapping_value,
    optional_text,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaOntologyExecutionPlan:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaOntologyExecutionPlan":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def invocation_intent_count(self) -> int:
        return int_value(self.payload.get("invocation_intent_count"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaCapabilityMatrixReceipt:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaCapabilityMatrixReceipt":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def coverage_status(self) -> str | None:
        return optional_text(self.payload.get("coverage_status"))

    @property
    def execution_allowed(self) -> bool:
        return self.payload.get("execution_allowed") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaOigCommitReceipt:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaOigCommitReceipt":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def applied(self) -> bool:
        return self.status == "execute_flag_commit_applied"

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def commit_id(self) -> str | None:
        return optional_text(self.payload.get("commit_id"))

    @property
    def domain_commit_id(self) -> str | None:
        return optional_text(self.payload.get("domain_commit_id"))

    @property
    def object_instance_graph_commit_id(self) -> str | None:
        return optional_text(self.payload.get("object_instance_graph_commit_id"))

    @property
    def branch_id(self) -> str | None:
        return optional_text(self.payload.get("branch_id"))

    @property
    def projection_hash(self) -> str | None:
        return optional_text(self.payload.get("projection_hash"))

    @property
    def ontology_function_call_execution_status(self) -> str | None:
        return optional_text(
            self.payload.get("ontology_function_call_execution_status")
        )

    @property
    def applied_invocation_count(self) -> int:
        return int_value(
            self.payload.get(
                "ontology_function_call_execution_applied_invocation_count"
            )
        )

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaHeadMoveAppliedReceipt:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaHeadMoveAppliedReceipt":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def ready(self) -> bool:
        return self.status == "head_move_applied_receipt_ready"

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def head_refs(self) -> dict[str, object]:
        return mapping_value(self.payload.get("head_refs"))

    @property
    def head_ref_status(self) -> str | None:
        return optional_text(self.head_refs.get("head_ref_status"))

    @property
    def semantic_package_commit_id(self) -> str | None:
        return optional_text(self.head_refs.get("semantic_package_commit_id"))

    @property
    def semantic_object_instance_graph_commit_id(self) -> str | None:
        return optional_text(
            self.head_refs.get("semantic_object_instance_graph_commit_id")
        )

    @property
    def dirty_status_after_head_move(self) -> str | None:
        return optional_text(self.payload.get("dirty_status_after_head_move"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaRuntimePackageIndexPatchReceipt:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaRuntimePackageIndexPatchReceipt":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def applied(self) -> bool:
        return self.status == "runtime_package_index_patch_applied"

    @property
    def available(self) -> bool:
        return self.payload.get("available") is True

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def semantic_object_upsert_count(self) -> int:
        return int_value(self.payload.get("semantic_object_upsert_count"))

    @property
    def semantic_object_delete_count(self) -> int:
        return int_value(self.payload.get("semantic_object_delete_count"))

    @property
    def package_index_semantic_object_count(self) -> int:
        return int_value(self.payload.get("package_index_semantic_object_count"))

    @property
    def head_refs(self) -> dict[str, object]:
        return mapping_value(self.payload.get("head_refs"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaOutputMaterializationReceipt:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaOutputMaterializationReceipt":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def ready(self) -> bool:
        return self.status == "provider_delta_output_materialization_ready"

    @property
    def blocked(self) -> bool:
        return self.payload.get("blocked") is True

    @property
    def target_count(self) -> int:
        return int_value(self.payload.get("target_count"))

    @property
    def rendered_target_count(self) -> int:
        return int_value(self.payload.get("rendered_target_count"))

    @property
    def artifact_ownership_receipt_count(self) -> int:
        return int_value(self.payload.get("artifact_ownership_receipt_count"))

    @property
    def post_step_receipt_count(self) -> int:
        return int_value(self.payload.get("post_step_receipt_count"))

    @property
    def tool_step_receipt_count(self) -> int:
        return int_value(self.payload.get("tool_step_receipt_count"))

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


__all__ = [
    "MetaProviderDeltaCapabilityMatrixReceipt",
    "MetaProviderDeltaHeadMoveAppliedReceipt",
    "MetaProviderDeltaOigCommitReceipt",
    "MetaProviderDeltaOntologyExecutionPlan",
    "MetaProviderDeltaOutputMaterializationReceipt",
    "MetaProviderDeltaRuntimePackageIndexPatchReceipt",
]
