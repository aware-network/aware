from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from aware_meta.materialization.deltas.contracts import (
    MetaProviderDeltaCapabilityMatrixReceipt,
    MetaProviderDeltaHeadMoveAppliedReceipt,
    MetaProviderDeltaMutationPlan,
    MetaProviderDeltaOigCommitReceipt,
    MetaProviderDeltaOntologyExecutionPlan,
    MetaProviderDeltaOutputMaterializationReceipt,
    MetaProviderDeltaRuntimePackageIndexPatchReceipt,
    MetaProviderDeltaSemanticDirtyDiff,
    MetaProviderDeltaSemanticChangeReport,
    MetaProviderDeltaSemanticCommitEvidence,
    MetaProviderDeltaTypedOperationPlan,
    mapping_value,
    optional_text,
)


@dataclass(frozen=True, slots=True)
class MetaProviderDeltaPipelineContext:
    request: object
    package_payload: Mapping[str, object]
    semantic_contract_payload: Mapping[str, object]
    manifest_path: str
    current_delta_fingerprint: str
    provider_delta_execution_context_preflight: Mapping[str, object] = field(
        default_factory=dict
    )
    baseline_dirty_preflight: Mapping[str, object] = field(default_factory=dict)
    semantic_dirty_diff: Mapping[str, object] = field(default_factory=dict)
    provider_delta_head_move_plan: Mapping[str, object] = field(default_factory=dict)
    provider_delta_typed_operation_plan: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_semantic_change_report: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_source_projection: Mapping[str, object] = field(default_factory=dict)
    provider_delta_generated_materialization: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_semantic_commit_evidence: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_mutation_plan: Mapping[str, object] = field(default_factory=dict)
    provider_delta_ontology_execution_plan: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_functioncall_capability_matrix: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_execute_flag_preflight: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_oig_commit_receipt: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_head_move_applied_receipt: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_runtime_package_index_patch: Mapping[str, object] = field(
        default_factory=dict
    )
    provider_delta_output_materialization: Mapping[str, object] = field(
        default_factory=dict
    )

    @classmethod
    def create(
        cls,
        *,
        request: object,
        package_payload: Mapping[str, object],
        semantic_contract_payload: Mapping[str, object],
        manifest_path: str,
        current_delta_fingerprint: str,
        provider_delta_execution_context_preflight: Mapping[str, object],
        baseline_dirty_preflight: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return cls(
            request=request,
            package_payload=dict(package_payload),
            semantic_contract_payload=dict(semantic_contract_payload),
            manifest_path=manifest_path,
            current_delta_fingerprint=current_delta_fingerprint,
            provider_delta_execution_context_preflight=dict(
                provider_delta_execution_context_preflight
            ),
            baseline_dirty_preflight=dict(baseline_dirty_preflight),
        )

    def with_baseline_dirty_preflight(
        self,
        baseline_dirty_preflight: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            baseline_dirty_preflight=dict(baseline_dirty_preflight),
        )

    def with_semantic_dirty_diff(
        self,
        semantic_dirty_diff: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(self, semantic_dirty_diff=dict(semantic_dirty_diff))

    def with_head_move_plan(
        self,
        provider_delta_head_move_plan: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_head_move_plan=dict(provider_delta_head_move_plan),
        )

    def with_typed_operation_plan(
        self,
        provider_delta_typed_operation_plan: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_typed_operation_plan=dict(
                provider_delta_typed_operation_plan
            ),
        )

    def with_semantic_change_report(
        self,
        provider_delta_semantic_change_report: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_semantic_change_report=dict(
                provider_delta_semantic_change_report
            ),
        )

    def with_source_projection(
        self,
        provider_delta_source_projection: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_source_projection=dict(provider_delta_source_projection),
        )

    def with_generated_materialization(
        self,
        provider_delta_generated_materialization: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_generated_materialization=dict(
                provider_delta_generated_materialization
            ),
        )

    def with_semantic_commit_evidence(
        self,
        provider_delta_semantic_commit_evidence: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_semantic_commit_evidence=dict(
                provider_delta_semantic_commit_evidence
            ),
        )

    def with_mutation_plan(
        self,
        provider_delta_mutation_plan: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_mutation_plan=dict(provider_delta_mutation_plan),
        )

    def with_ontology_execution_plan(
        self,
        provider_delta_ontology_execution_plan: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_ontology_execution_plan=dict(
                provider_delta_ontology_execution_plan
            ),
        )

    def with_functioncall_capability_matrix(
        self,
        provider_delta_functioncall_capability_matrix: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_functioncall_capability_matrix=dict(
                provider_delta_functioncall_capability_matrix
            ),
        )

    def with_execute_flag_preflight(
        self,
        provider_delta_execute_flag_preflight: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_execute_flag_preflight=dict(
                provider_delta_execute_flag_preflight
            ),
        )

    def with_oig_commit_receipt(
        self,
        provider_delta_oig_commit_receipt: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_oig_commit_receipt=dict(provider_delta_oig_commit_receipt),
        )

    def with_head_move_applied_receipt(
        self,
        provider_delta_head_move_applied_receipt: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_head_move_applied_receipt=dict(
                provider_delta_head_move_applied_receipt
            ),
        )

    def with_runtime_package_index_patch(
        self,
        provider_delta_runtime_package_index_patch: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_runtime_package_index_patch=dict(
                provider_delta_runtime_package_index_patch
            ),
        )

    def with_output_materialization(
        self,
        provider_delta_output_materialization: Mapping[str, object],
    ) -> "MetaProviderDeltaPipelineContext":
        return replace(
            self,
            provider_delta_output_materialization=dict(
                provider_delta_output_materialization
            ),
        )

    def stage_payloads(self) -> dict[str, dict[str, object]]:
        return {
            "provider_delta_execution_context_preflight": dict(
                self.provider_delta_execution_context_preflight
            ),
            "baseline_dirty_preflight": dict(self.baseline_dirty_preflight),
            "semantic_dirty_diff": self.dirty_diff.evidence_payload(),
            "provider_delta_head_move_plan": dict(self.provider_delta_head_move_plan),
            "provider_delta_typed_operation_plan": (
                self.typed_operation_plan.evidence_payload()
            ),
            "provider_delta_semantic_change_report": (
                self.semantic_change_report.evidence_payload()
            ),
            "provider_delta_source_projection": dict(
                self.provider_delta_source_projection
            ),
            "provider_delta_generated_materialization": dict(
                self.provider_delta_generated_materialization
            ),
            "provider_delta_semantic_commit_evidence": (
                self.semantic_commit_evidence.evidence_payload()
            ),
            "provider_delta_mutation_plan": (self.mutation_plan.evidence_payload()),
            "provider_delta_ontology_execution_plan": (
                self.ontology_execution_plan.evidence_payload()
            ),
            "provider_delta_functioncall_capability_matrix": (
                self.functioncall_capability_matrix.evidence_payload()
            ),
            "provider_delta_execute_flag_preflight": dict(
                self.provider_delta_execute_flag_preflight
            ),
            "provider_delta_oig_commit_receipt": (
                self.oig_commit_receipt.evidence_payload()
            ),
            "provider_delta_head_move_applied_receipt": (
                self.head_move_applied_receipt.evidence_payload()
            ),
            "provider_delta_runtime_package_index_patch": (
                self.runtime_package_index_patch.evidence_payload()
            ),
            "provider_delta_output_materialization": (
                self.output_materialization.evidence_payload()
            ),
        }

    @property
    def typed_operation_plan(
        self,
    ) -> MetaProviderDeltaTypedOperationPlan:
        return MetaProviderDeltaTypedOperationPlan.from_payload(
            self.provider_delta_typed_operation_plan
        )

    @property
    def dirty_diff(self) -> MetaProviderDeltaSemanticDirtyDiff:
        return MetaProviderDeltaSemanticDirtyDiff.from_payload(self.semantic_dirty_diff)

    @property
    def mutation_plan(self) -> MetaProviderDeltaMutationPlan:
        return MetaProviderDeltaMutationPlan.from_payload(
            self.provider_delta_mutation_plan
        )

    @property
    def semantic_change_report(
        self,
    ) -> MetaProviderDeltaSemanticChangeReport:
        return MetaProviderDeltaSemanticChangeReport.from_payload(
            self.provider_delta_semantic_change_report
        )

    @property
    def semantic_commit_evidence(
        self,
    ) -> MetaProviderDeltaSemanticCommitEvidence:
        return MetaProviderDeltaSemanticCommitEvidence.from_payload(
            self.provider_delta_semantic_commit_evidence
        )

    @property
    def ontology_execution_plan(
        self,
    ) -> MetaProviderDeltaOntologyExecutionPlan:
        return MetaProviderDeltaOntologyExecutionPlan.from_payload(
            self.provider_delta_ontology_execution_plan
        )

    @property
    def functioncall_capability_matrix(
        self,
    ) -> MetaProviderDeltaCapabilityMatrixReceipt:
        return MetaProviderDeltaCapabilityMatrixReceipt.from_payload(
            self.provider_delta_functioncall_capability_matrix
        )

    @property
    def oig_commit_receipt(self) -> MetaProviderDeltaOigCommitReceipt:
        return MetaProviderDeltaOigCommitReceipt.from_payload(
            self.provider_delta_oig_commit_receipt
        )

    @property
    def head_move_applied_receipt(
        self,
    ) -> MetaProviderDeltaHeadMoveAppliedReceipt:
        return MetaProviderDeltaHeadMoveAppliedReceipt.from_payload(
            self.provider_delta_head_move_applied_receipt
        )

    @property
    def runtime_package_index_patch(
        self,
    ) -> MetaProviderDeltaRuntimePackageIndexPatchReceipt:
        return MetaProviderDeltaRuntimePackageIndexPatchReceipt.from_payload(
            self.provider_delta_runtime_package_index_patch
        )

    @property
    def output_materialization(
        self,
    ) -> MetaProviderDeltaOutputMaterializationReceipt:
        return MetaProviderDeltaOutputMaterializationReceipt.from_payload(
            self.provider_delta_output_materialization
        )

    @property
    def typed_operation_status(self) -> str | None:
        return self.typed_operation_plan.status

    @property
    def ontology_execution_status(self) -> str | None:
        return self.ontology_execution_plan.status

    @property
    def functioncall_execution_allowed(self) -> bool:
        return self.functioncall_capability_matrix.execution_allowed

    @property
    def mutation_plan_status(self) -> str | None:
        return self.mutation_plan.status

    @property
    def mutation_plan_ready(self) -> bool:
        return self.mutation_plan.ready

    @property
    def semantic_change_report_ready(self) -> bool:
        return self.semantic_change_report.ready

    @property
    def semantic_commit_evidence_ready(self) -> bool:
        return self.semantic_commit_evidence.ready

    @property
    def execute_flag_ready(self) -> bool:
        return (
            optional_text(self.provider_delta_execute_flag_preflight.get("status"))
            == "execute_flag_preflight_ready"
        )

    @property
    def oig_commit_applied(self) -> bool:
        return self.oig_commit_receipt.applied

    @property
    def head_move_applied(self) -> bool:
        return self.head_move_applied_receipt.ready

    @property
    def runtime_package_index_patch_applied(self) -> bool:
        return self.runtime_package_index_patch.applied

    @property
    def output_materialization_ready(self) -> bool:
        return self.output_materialization.ready

    def evidence_summary(self) -> dict[str, object]:
        dirty_diff = self.dirty_diff
        semantic_change_report = self.semantic_change_report
        semantic_commit_evidence = self.semantic_commit_evidence
        active_execution_rail = mapping_value(
            self.provider_delta_execute_flag_preflight.get(
                "provider_delta_active_execution_rail"
            )
        )
        return {
            "context_kind": "meta_ocg_provider_delta_pipeline_context",
            "manifest_path": self.manifest_path,
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "semantic_contract_provider_key": optional_text(
                self.semantic_contract_payload.get("provider_key")
            ),
            "baseline_dirty_preflight_status": optional_text(
                self.baseline_dirty_preflight.get("status")
            ),
            "semantic_dirty_diff_status": dirty_diff.status,
            "semantic_dirty_diff_ready": dirty_diff.ready,
            "semantic_dirty_entry_count": dirty_diff.dirty_entry_count,
            "semantic_dirty_diff_baseline_index_compare_status": (
                dirty_diff.baseline_index_compare_status
            ),
            "semantic_dirty_diff_baseline_compare_operation_counts": (
                dirty_diff.baseline_compare_operation_counts
            ),
            "semantic_dirty_diff_stale_semantic_key_count": (
                dirty_diff.stale_semantic_key_count
            ),
            "provider_delta_head_move_status": optional_text(
                self.provider_delta_head_move_plan.get("status")
            ),
            "provider_delta_typed_operation_status": self.typed_operation_status,
            "provider_delta_typed_operation_count": len(
                self.typed_operation_plan.typed_operations
            ),
            "provider_delta_ontology_execution_status": (
                self.ontology_execution_status
            ),
            "provider_delta_ontology_invocation_intent_count": (
                self.ontology_execution_plan.invocation_intent_count
            ),
            "provider_delta_functioncall_capability_status": (
                self.functioncall_capability_matrix.coverage_status
            ),
            "provider_delta_functioncall_execution_allowed": (
                self.functioncall_execution_allowed
            ),
            "provider_delta_execute_flag_preflight_status": optional_text(
                self.provider_delta_execute_flag_preflight.get("status")
            ),
            "provider_delta_execute_flag_ready": self.execute_flag_ready,
            "active_execution_rail": optional_text(
                active_execution_rail.get("active_execution_rail")
            ),
            "active_execution_status": optional_text(
                active_execution_rail.get("status")
            ),
            "provider_delta_active_execution_rail": active_execution_rail,
            "semantic_change_report_status": (semantic_change_report.status),
            "semantic_change_report_ready": (semantic_change_report.ready),
            "semantic_world_change_count": (
                semantic_change_report.semantic_world_change_count
            ),
            "semantic_readable_change_line_count": (
                semantic_change_report.readable_line_count
            ),
            "provider_delta_source_projection_status": optional_text(
                self.provider_delta_source_projection.get("status")
            ),
            "provider_delta_source_projection_ready": (
                self.provider_delta_source_projection.get("ready") is True
            ),
            "provider_delta_source_projection_projected_entry_count": (
                _int_stage_value(
                    self.provider_delta_source_projection.get("projected_entry_count")
                )
            ),
            "provider_delta_generated_materialization_status": optional_text(
                self.provider_delta_generated_materialization.get("status")
            ),
            "provider_delta_generated_materialization_ready": (
                self.provider_delta_generated_materialization.get("ready") is True
            ),
            "provider_delta_generated_materialization_renderer_operation_count": (
                _int_stage_value(
                    self.provider_delta_generated_materialization.get(
                        "renderer_operation_count"
                    )
                )
            ),
            "semantic_commit_evidence_status": (semantic_commit_evidence.status),
            "semantic_commit_evidence_ready": (semantic_commit_evidence.ready),
            "committed_semantic_change_count": (
                semantic_commit_evidence.committed_semantic_change_count
            ),
            "provider_delta_oig_commit_receipt_status": (
                self.oig_commit_receipt.status
            ),
            "provider_delta_oig_commit_applied": self.oig_commit_applied,
            "provider_delta_oig_commit_id": self.oig_commit_receipt.commit_id,
            "provider_delta_oig_object_instance_graph_commit_id": (
                self.oig_commit_receipt.object_instance_graph_commit_id
            ),
            "provider_delta_head_move_applied_receipt_status": (
                self.head_move_applied_receipt.status
            ),
            "provider_delta_head_move_applied": self.head_move_applied,
            "provider_delta_head_ref_status": (
                self.head_move_applied_receipt.head_ref_status
            ),
            "provider_delta_semantic_package_commit_id": (
                self.head_move_applied_receipt.semantic_package_commit_id
            ),
            "provider_delta_runtime_package_index_patch_status": (
                self.runtime_package_index_patch.status
            ),
            "provider_delta_runtime_package_index_patch_applied": (
                self.runtime_package_index_patch_applied
            ),
            "provider_delta_runtime_package_index_patch_upsert_count": (
                self.runtime_package_index_patch.semantic_object_upsert_count
            ),
            "provider_delta_runtime_package_index_patch_delete_count": (
                self.runtime_package_index_patch.semantic_object_delete_count
            ),
            "provider_delta_output_materialization_status": (
                self.output_materialization.status
            ),
            "provider_delta_output_materialization_ready": (
                self.output_materialization_ready
            ),
            "provider_delta_output_materialization_artifact_receipt_count": (
                self.output_materialization.artifact_ownership_receipt_count
            ),
            "stage_statuses": {
                "baseline_dirty_preflight": optional_text(
                    self.baseline_dirty_preflight.get("status")
                ),
                "semantic_dirty_diff": dirty_diff.status,
                "head_move_plan": optional_text(
                    self.provider_delta_head_move_plan.get("status")
                ),
                "typed_operation_plan": self.typed_operation_status,
                "semantic_change_report": (semantic_change_report.status),
                "source_projection": optional_text(
                    self.provider_delta_source_projection.get("status")
                ),
                "generated_materialization": optional_text(
                    self.provider_delta_generated_materialization.get("status")
                ),
                "semantic_commit_evidence": semantic_commit_evidence.status,
                "ontology_execution_plan": self.ontology_execution_status,
                "functioncall_capability_matrix": (
                    self.functioncall_capability_matrix.coverage_status
                ),
                "execute_flag_preflight": optional_text(
                    self.provider_delta_execute_flag_preflight.get("status")
                ),
                "oig_commit_receipt": self.oig_commit_receipt.status,
                "head_move_applied_receipt": self.head_move_applied_receipt.status,
                "runtime_package_index_patch": (
                    self.runtime_package_index_patch.status
                ),
                "output_materialization": self.output_materialization.status,
            },
        }


def mapping_stage(value: object) -> dict[str, object]:
    return mapping_value(value)


def _int_stage_value(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


__all__ = [
    "MetaProviderDeltaPipelineContext",
    "mapping_stage",
]
