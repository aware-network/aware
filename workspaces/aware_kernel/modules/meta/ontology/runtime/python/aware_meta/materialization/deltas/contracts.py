from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from aware_meta.materialization.deltas.coercion import (
    int_mapping_value,
    int_value,
    mapping_or_none,
    mapping_value,
    optional_text,
    string_value,
    tuple_mappings,
    tuple_text,
)
from aware_meta.materialization.deltas.constants import (
    META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION,
    META_PROVIDER_DELTA_DIRTY_ENTRY_CONTRACT_VERSION,
    META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION,
    META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
)
from aware_meta.materialization.deltas.dirty_diff_contracts import (
    MetaProviderDeltaDirtyEntry,
    MetaProviderDeltaSemanticDirtyDiff,
    dirty_entries_from_payloads,
)
from aware_meta.materialization.deltas.execution_receipt_contracts import (
    MetaProviderDeltaCapabilityMatrixReceipt,
    MetaProviderDeltaHeadMoveAppliedReceipt,
    MetaProviderDeltaOigCommitReceipt,
    MetaProviderDeltaOntologyExecutionPlan,
    MetaProviderDeltaOutputMaterializationReceipt,
    MetaProviderDeltaRuntimePackageIndexPatchReceipt,
)
from aware_meta.materialization.deltas.change_evidence_contracts import (
    MetaProviderDeltaCommittedSemanticChange,
    MetaProviderDeltaReadableSemanticChangeChain,
    MetaProviderDeltaSemanticChangeReport,
    MetaProviderDeltaSemanticCommitEvidence,
    MetaProviderDeltaSemanticWorldChange,
    committed_semantic_changes_from_payloads,
    semantic_world_changes_from_payloads,
)
from aware_meta.materialization.deltas.mutation_contracts import (
    MetaProviderDeltaMutationPlan,
    MetaProviderDeltaMutationStep,
    mutation_steps_from_payloads,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
    MetaProviderDeltaTypedOperationPlan,
    typed_operations_from_payloads,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaCommitRefContract:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaCommitRefContract":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def contract_kind(self) -> str | None:
        return optional_text(self.payload.get("contract_kind"))

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def reason(self) -> str | None:
        return optional_text(self.payload.get("reason"))

    @property
    def ready(self) -> bool:
        return self.payload.get("receipt_persistence_contract_ready") is True

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("required_fields"))

    @property
    def available_fields(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("available_fields"))

    @property
    def missing_required_fields(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("missing_required_fields"))

    @property
    def production_execution_wired(self) -> bool:
        return self.payload.get("production_execution_wired") is True

    @property
    def would_persist(self) -> bool:
        return self.payload.get("would_persist") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaBundlePackageRef:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaBundlePackageRef":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def package_key(self) -> str | None:
        return optional_text(self.payload.get("package_key"))

    @property
    def package_kind(self) -> str | None:
        return optional_text(self.payload.get("package_kind"))

    @property
    def manifest_toml_path(self) -> str | None:
        return optional_text(self.payload.get("manifest_toml_path"))

    @property
    def semantic_owner_module(self) -> str | None:
        return optional_text(self.payload.get("semantic_owner_module"))

    @property
    def semantic_package_kind(self) -> str | None:
        return optional_text(self.payload.get("semantic_package_kind"))

    @property
    def source_code_package_id(self) -> str | None:
        return optional_text(self.payload.get("source_code_package_id"))

    @property
    def source_object_instance_graph_commit_id(self) -> str | None:
        return optional_text(self.payload.get("source_object_instance_graph_commit_id"))

    @property
    def semantic_package_id(self) -> str | None:
        return optional_text(self.payload.get("semantic_package_id"))

    @property
    def semantic_branch_id(self) -> str | None:
        return optional_text(self.payload.get("semantic_branch_id"))

    @property
    def semantic_projection_hash(self) -> str | None:
        return optional_text(self.payload.get("semantic_projection_hash"))

    @property
    def semantic_head_commit_id(self) -> str | None:
        return optional_text(self.payload.get("semantic_head_commit_id"))

    @property
    def semantic_object_instance_graph_commit_id(self) -> str | None:
        return optional_text(
            self.payload.get("semantic_object_instance_graph_commit_id")
        )

    @property
    def semantic_root_id(self) -> str | None:
        return optional_text(self.payload.get("semantic_root_id"))

    @property
    def semantic_root_object_instance_graph_commit_id(self) -> str | None:
        return optional_text(
            self.payload.get("semantic_root_object_instance_graph_commit_id")
        )

    @property
    def commit_ref_contract_status(self) -> str | None:
        return optional_text(self.payload.get("commit_ref_contract_status"))

    @property
    def commit_ref_contract_reason(self) -> str | None:
        return optional_text(self.payload.get("commit_ref_contract_reason"))

    @property
    def receipt_persistence_contract_ready(self) -> bool:
        return self.payload.get("receipt_persistence_contract_ready") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaResultDetails:
    payload: Mapping[str, object]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaResultDetails":
        return cls(payload={str(key): value for key, value in payload.items()})

    @property
    def provider_key(self) -> str | None:
        return optional_text(self.payload.get("provider_key"))

    @property
    def mode(self) -> str | None:
        return optional_text(self.payload.get("mode"))

    @property
    def manifest_path(self) -> str | None:
        return optional_text(self.payload.get("manifest_path"))

    @property
    def source_files(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("source_files"))

    @property
    def changed_source_files(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("changed_source_files"))

    @property
    def semantic_delta_count(self) -> int:
        return int_value(self.payload.get("semantic_delta_count"))

    @property
    def semantic_change_count(self) -> int:
        return int_value(self.payload.get("semantic_change_count"))

    @property
    def current_delta_fingerprint(self) -> str | None:
        return optional_text(self.payload.get("current_delta_fingerprint"))

    @property
    def delta_operation_plan(self) -> dict[str, object]:
        return mapping_value(self.payload.get("delta_operation_plan"))

    @property
    def provider_delta_operation_execution(self) -> dict[str, object]:
        return mapping_value(self.payload.get("provider_delta_operation_execution"))

    @property
    def provider_delta_execution_context_preflight(self) -> dict[str, object]:
        return mapping_value(
            self.payload.get("provider_delta_execution_context_preflight")
        )

    @property
    def provider_delta_execute_flag_preflight(self) -> dict[str, object]:
        return mapping_value(self.payload.get("provider_delta_execute_flag_preflight"))

    @property
    def provider_delta_head_move_plan(self) -> dict[str, object]:
        return mapping_value(self.payload.get("provider_delta_head_move_plan"))

    @property
    def provider_delta_typed_operation_plan(
        self,
    ) -> MetaProviderDeltaTypedOperationPlan:
        return MetaProviderDeltaTypedOperationPlan.from_payload(
            mapping_value(self.payload.get("provider_delta_typed_operation_plan"))
        )

    @property
    def provider_delta_mutation_plan(self) -> MetaProviderDeltaMutationPlan:
        return MetaProviderDeltaMutationPlan.from_payload(
            mapping_value(self.payload.get("provider_delta_mutation_plan"))
        )

    @property
    def provider_delta_functioncall_capability_matrix(
        self,
    ) -> MetaProviderDeltaCapabilityMatrixReceipt:
        return MetaProviderDeltaCapabilityMatrixReceipt.from_payload(
            mapping_value(
                self.payload.get("provider_delta_functioncall_capability_matrix")
            )
        )

    @property
    def baseline_dirty_preflight(self) -> dict[str, object]:
        return mapping_value(self.payload.get("baseline_dirty_preflight"))

    @property
    def semantic_dirty_diff(self) -> MetaProviderDeltaSemanticDirtyDiff:
        return MetaProviderDeltaSemanticDirtyDiff.from_payload(
            mapping_value(self.payload.get("semantic_dirty_diff"))
        )

    @property
    def provider_delta_oig_commit_receipt(self) -> MetaProviderDeltaOigCommitReceipt:
        return MetaProviderDeltaOigCommitReceipt.from_payload(
            mapping_value(self.payload.get("provider_delta_oig_commit_receipt"))
        )

    @property
    def provider_delta_head_move_applied_receipt(
        self,
    ) -> MetaProviderDeltaHeadMoveAppliedReceipt:
        return MetaProviderDeltaHeadMoveAppliedReceipt.from_payload(
            mapping_value(self.payload.get("provider_delta_head_move_applied_receipt"))
        )

    @property
    def provider_delta_runtime_package_index_patch(
        self,
    ) -> MetaProviderDeltaRuntimePackageIndexPatchReceipt:
        return MetaProviderDeltaRuntimePackageIndexPatchReceipt.from_payload(
            mapping_value(
                self.payload.get("provider_delta_runtime_package_index_patch")
            )
        )

    @property
    def provider_delta_semantic_commit_evidence(
        self,
    ) -> MetaProviderDeltaSemanticCommitEvidence:
        return MetaProviderDeltaSemanticCommitEvidence.from_payload(
            mapping_value(self.payload.get("provider_delta_semantic_commit_evidence"))
        )

    @property
    def provider_delta_source_projection(self) -> dict[str, object]:
        return mapping_value(self.payload.get("provider_delta_source_projection"))

    @property
    def provider_delta_source_projection_status(self) -> str | None:
        return optional_text(
            self.payload.get("provider_delta_source_projection_status")
        )

    @property
    def provider_delta_source_projection_ready(self) -> bool:
        return self.payload.get("provider_delta_source_projection_ready") is True

    @property
    def provider_delta_output_materialization(
        self,
    ) -> MetaProviderDeltaOutputMaterializationReceipt:
        return MetaProviderDeltaOutputMaterializationReceipt.from_payload(
            mapping_value(self.payload.get("provider_delta_output_materialization"))
        )

    @property
    def artifact_ownership_receipts(self) -> tuple[dict[str, object], ...]:
        return tuple_mappings(self.payload.get("artifact_ownership_receipts"))

    @property
    def language_post_step_receipts(self) -> tuple[dict[str, object], ...]:
        return tuple_mappings(self.payload.get("language_post_step_receipts"))

    @property
    def language_materialization_tool_step_receipts(
        self,
    ) -> tuple[dict[str, object], ...]:
        return tuple_mappings(
            self.payload.get("language_materialization_tool_step_receipts")
        )

    @property
    def execute_flag_preflight_status(self) -> str | None:
        return optional_text(self.provider_delta_execute_flag_preflight.get("status"))

    @property
    def oig_commit_receipt_status(self) -> str | None:
        return self.provider_delta_oig_commit_receipt.status

    @property
    def head_move_applied_receipt_status(self) -> str | None:
        return self.provider_delta_head_move_applied_receipt.status

    @property
    def runtime_package_index_patch_status(self) -> str | None:
        return self.provider_delta_runtime_package_index_patch.status

    @property
    def semantic_commit_evidence_status(self) -> str | None:
        return self.provider_delta_semantic_commit_evidence.status

    @property
    def output_materialization_status(self) -> str | None:
        return self.provider_delta_output_materialization.status

    @property
    def head_move_plan_status(self) -> str | None:
        return optional_text(self.provider_delta_head_move_plan.get("status"))

    @property
    def typed_operation_plan_status(self) -> str | None:
        return self.provider_delta_typed_operation_plan.status

    @property
    def mutation_plan_status(self) -> str | None:
        return self.provider_delta_mutation_plan.status

    @property
    def functioncall_capability_status(self) -> str | None:
        return self.provider_delta_functioncall_capability_matrix.coverage_status

    @property
    def baseline_dirty_preflight_status(self) -> str | None:
        return optional_text(self.baseline_dirty_preflight.get("status"))

    @property
    def semantic_dirty_diff_status(self) -> str | None:
        return self.semantic_dirty_diff.status

    @property
    def commit_applied(self) -> bool:
        return self.provider_delta_oig_commit_receipt.applied

    @property
    def head_move_applied(self) -> bool:
        return self.head_move_plan_status == "head_move_applied"

    @property
    def runtime_package_index_patched(self) -> bool:
        return self.runtime_package_index_patch_status in {
            "runtime_package_index_patch_applied",
            "runtime_package_index_patch_empty",
        }

    @property
    def semantic_commit_evidence_ready(self) -> bool:
        return self.provider_delta_semantic_commit_evidence.ready

    @property
    def output_materialized(self) -> bool:
        materialization = mapping_value(
            self.payload.get("provider_delta_output_materialization")
        )
        if not materialization:
            return True
        status = self.output_materialization_status
        if status == "provider_delta_output_materialization_not_required":
            return True
        if status != "provider_delta_output_materialization_ready":
            return False
        artifact_count = self.provider_delta_output_materialization
        if artifact_count.artifact_ownership_receipt_count > 0:
            return True
        return bool(self.artifact_ownership_receipts)

    @property
    def production_execution_wired(self) -> bool:
        return self.payload.get("production_execution_wired") is True

    @property
    def request_execute(self) -> bool:
        return self.payload.get("request_execute") is True

    @property
    def request_dry_run(self) -> bool:
        return self.payload.get("request_dry_run") is True

    @property
    def request_commit_if_ready(self) -> bool:
        return self.payload.get("request_commit_if_ready") is True

    def evidence_payload(self) -> dict[str, object]:
        return {str(key): value for key, value in self.payload.items()}


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaResultEnvelope:
    payload: Mapping[str, object]
    details: MetaProviderDeltaResultDetails
    commit_ref_contract: MetaProviderDeltaCommitRefContract
    bundle_package: MetaProviderDeltaBundlePackageRef
    bundle_packages: tuple[MetaProviderDeltaBundlePackageRef, ...]

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "MetaProviderDeltaResultEnvelope":
        bundle_package_payload = mapping_value(payload.get("bundle_package"))
        return cls(
            payload={str(key): value for key, value in payload.items()},
            details=MetaProviderDeltaResultDetails.from_payload(
                mapping_value(payload.get("details"))
            ),
            commit_ref_contract=MetaProviderDeltaCommitRefContract.from_payload(
                mapping_value(payload.get("commit_ref_contract"))
            ),
            bundle_package=MetaProviderDeltaBundlePackageRef.from_payload(
                bundle_package_payload
            ),
            bundle_packages=tuple(
                MetaProviderDeltaBundlePackageRef.from_payload(item)
                for item in tuple_mappings(payload.get("bundle_packages"))
            )
            or (
                MetaProviderDeltaBundlePackageRef.from_payload(bundle_package_payload),
            ),
        )

    @property
    def contract_version(self) -> str | None:
        return optional_text(self.payload.get("contract_version"))

    @property
    def status(self) -> str | None:
        return optional_text(self.payload.get("status"))

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"

    @property
    def fallback_required(self) -> bool:
        return self.status == "fallback_required"

    @property
    def package(self) -> dict[str, object]:
        return mapping_value(self.payload.get("package"))

    @property
    def semantic_contract(self) -> dict[str, object]:
        return mapping_value(self.payload.get("semantic_contract"))

    @property
    def current_delta_fingerprint(self) -> str | None:
        return optional_text(self.payload.get("current_delta_fingerprint"))

    @property
    def applied_semantic_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("applied_semantic_keys"))

    @property
    def skipped_semantic_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("skipped_semantic_keys"))

    @property
    def stale_semantic_keys(self) -> tuple[str, ...]:
        return tuple_text(self.payload.get("stale_semantic_keys"))

    @property
    def implementation_required(self) -> bool:
        return self.payload.get("implementation_required") is True

    @property
    def implementation_work_items(self) -> tuple[dict[str, object], ...]:
        return tuple_mappings(self.payload.get("implementation_work_items"))

    @property
    def fallback_reason(self) -> str | None:
        return optional_text(self.payload.get("fallback_reason"))

    @property
    def error(self) -> dict[str, object] | None:
        return mapping_or_none(self.payload.get("error"))

    @property
    def production_execution_wired(self) -> bool:
        return self.details.production_execution_wired

    @property
    def semantic_commit_evidence_ready(self) -> bool:
        return self.details.semantic_commit_evidence_ready

    @property
    def output_materialized(self) -> bool:
        return self.details.output_materialized

    @property
    def commit_ref_ready(self) -> bool:
        return self.commit_ref_contract.ready

    def evidence_payload(self) -> dict[str, object]:
        payload = {str(key): value for key, value in self.payload.items()}
        payload["details"] = self.details.evidence_payload()
        payload["commit_ref_contract"] = self.commit_ref_contract.evidence_payload()
        payload["bundle_package"] = self.bundle_package.evidence_payload()
        payload["bundle_packages"] = tuple(
            bundle_package.evidence_payload() for bundle_package in self.bundle_packages
        )
        return payload


__all__ = [
    "META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_DIRTY_ENTRY_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION",
    "META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION",
    "MetaProviderDeltaBundlePackageRef",
    "MetaProviderDeltaCapabilityMatrixReceipt",
    "MetaProviderDeltaCommitRefContract",
    "MetaProviderDeltaCommittedSemanticChange",
    "MetaProviderDeltaDirtyEntry",
    "MetaProviderDeltaHeadMoveAppliedReceipt",
    "MetaProviderDeltaMutationPlan",
    "MetaProviderDeltaMutationStep",
    "MetaProviderDeltaOigCommitReceipt",
    "MetaProviderDeltaOntologyExecutionPlan",
    "MetaProviderDeltaOutputMaterializationReceipt",
    "MetaProviderDeltaReadableSemanticChangeChain",
    "MetaProviderDeltaResultDetails",
    "MetaProviderDeltaResultEnvelope",
    "MetaProviderDeltaRuntimePackageIndexPatchReceipt",
    "MetaProviderDeltaSemanticDirtyDiff",
    "MetaProviderDeltaSemanticChangeReport",
    "MetaProviderDeltaSemanticCommitEvidence",
    "MetaProviderDeltaSemanticWorldChange",
    "MetaProviderDeltaTypedOperation",
    "MetaProviderDeltaTypedOperationPlan",
    "committed_semantic_changes_from_payloads",
    "dirty_entries_from_payloads",
    "int_mapping_value",
    "int_value",
    "mapping_or_none",
    "mapping_value",
    "mutation_steps_from_payloads",
    "optional_text",
    "semantic_world_changes_from_payloads",
    "string_value",
    "tuple_mappings",
    "tuple_text",
    "typed_operations_from_payloads",
]
