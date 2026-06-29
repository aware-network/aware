from __future__ import annotations

from dataclasses import dataclass

from aware_code.semantic_materialization import (
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
)


META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION = (
    "aware.meta.ocg-delta-coverage-matrix.v1"
)
META_OCG_DELTA_PRODUCT_READINESS_KIND = "meta_ocg_delta_product_readiness"

STATUS_READY = "ready"
STATUS_SKIPPED_POLICY = "skipped_policy"
STATUS_PLANNED = "planned"
STATUS_BLOCKED = "blocked"
STATUS_NOT_APPLICABLE = "not_applicable"

HOME_PROOF_COVERED = "home_latest_baseline_covered"
HOME_PROOF_MODULE_TESTS = "module_tests_only"
HOME_PROOF_NOT_COVERED = "not_covered"

LANGUAGE_TARGET_STRUCTURAL = "structural_language_targets_only"
LANGUAGE_TARGET_FUNCTION_IMPL = "function_impl_runtime_handlers_only"
LANGUAGE_TARGET_UNION = "supported_operation_target_union"
LANGUAGE_TARGET_RENDER_ALL = "render_all_currently"

SOURCE_PROJECTION_POLICY_SEGMENT_READY = "segment_ready"
SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED = "render_all_required"
SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT = "blocked_no_code_segment"
SOURCE_PROJECTION_POLICIES = (
    SOURCE_PROJECTION_POLICY_SEGMENT_READY,
    SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
    SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT,
)

WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY = "public_segment_ready"
WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY = (
    "public_generated_apply_ready"
)
WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY = "public_graph_only_ready"
WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY = "semantic_contract_only"
WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED = (
    "explicit_fallback_required"
)
WORKSPACE_DELTA_FIRST_MODES = (
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY,
    WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED,
)
WORKSPACE_DELTA_FIRST_READY_MODES = (
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
)

_NEXT_PRIORITY_ORDER = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "TBD": 3,
}
_WORKSPACE_DELTA_FIRST_GRAPH_ONLY_CASE_KEYS = {
    "attribute_membership.update",
    "function_membership.update",
    "object_config_graph.create",
    "object_config_graph_package.create",
    "object_config_graph_package.update",
    "object_projection_graph.create",
    "object_projection_graph_node.create",
}


@dataclass(frozen=True, slots=True)
class MetaOcgDeltaCoverageMatrixEntry:
    case_key: str
    feature_key: str
    ontology_subject_kind: str
    operation_family: str
    provider_operation_type: str
    semantic_change_status: str
    typed_operation_status: str
    ontology_execution_status: str
    source_projection_status: str
    source_projection_reason: str
    source_projection_policy: str
    language_target_impact_policy: str
    home_proof_status: str
    code_section_type: str | None = None
    code_segment_name: str | None = None
    home_proof_refs: tuple[str, ...] = ()
    next_priority: str | None = None
    notes: str = ""
    contract_version: str = META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION

    @property
    def registration_key(self) -> tuple[str, str]:
        return (self.ontology_subject_kind, self.operation_family)

    @property
    def source_projection_ready(self) -> bool:
        return self.source_projection_status == STATUS_READY

    @property
    def source_projection_gap(self) -> bool:
        return self.source_projection_status in {
            STATUS_PLANNED,
            STATUS_BLOCKED,
            STATUS_SKIPPED_POLICY,
        }

    @property
    def workspace_delta_first_mode(self) -> str:
        return workspace_delta_first_mode(entry=self)

    @property
    def workspace_delta_first_ready(self) -> bool:
        return self.workspace_delta_first_mode in WORKSPACE_DELTA_FIRST_READY_MODES

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "case_key": self.case_key,
            "feature_key": self.feature_key,
            "ontology_subject_kind": self.ontology_subject_kind,
            "operation_family": self.operation_family,
            "provider_operation_type": self.provider_operation_type,
            "semantic_change_status": self.semantic_change_status,
            "typed_operation_status": self.typed_operation_status,
            "ontology_execution_status": self.ontology_execution_status,
            "source_projection_status": self.source_projection_status,
            "source_projection_reason": self.source_projection_reason,
            "source_projection_policy": self.source_projection_policy,
            "code_section_type": self.code_section_type,
            "code_segment_name": self.code_segment_name,
            "language_target_impact_policy": self.language_target_impact_policy,
            "home_proof_status": self.home_proof_status,
            "home_proof_refs": self.home_proof_refs,
            "next_priority": self.next_priority,
            "notes": self.notes,
            "workspace_delta_first_mode": self.workspace_delta_first_mode,
            "workspace_delta_first_ready": self.workspace_delta_first_ready,
        }


def meta_ocg_delta_coverage_matrix() -> tuple[
    MetaOcgDeltaCoverageMatrixEntry,
    ...,
]:
    return _MATRIX


def coverage_matrix_payload() -> dict[str, object]:
    return {
        "contract_version": META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION,
        "entry_count": len(_MATRIX),
        "entries": tuple(entry.evidence_payload() for entry in _MATRIX),
        "source_projection_ready_count": len(source_projection_ready_entries()),
        "source_projection_gap_count": len(source_projection_gap_entries()),
        "source_projection_policy_counts": {
            policy: len(source_projection_policy_entries(policy=policy))
            for policy in SOURCE_PROJECTION_POLICIES
        },
        "workspace_delta_first_mode_counts": workspace_delta_first_mode_counts(),
    }


def meta_ocg_delta_product_readiness_payload() -> dict[str, object]:
    ready_entries = source_projection_ready_entries()
    render_all_entries = source_projection_policy_entries(
        policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
    )
    blocked_entries = source_projection_policy_entries(
        policy=SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT,
    )
    workspace_ready_entries = workspace_delta_first_ready_entries()
    workspace_generated_entries = workspace_delta_first_mode_entries(
        mode=WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
    )
    workspace_graph_only_entries = workspace_delta_first_mode_entries(
        mode=WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    )
    workspace_contract_only_entries = workspace_delta_first_mode_entries(
        mode=WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY,
    )
    workspace_explicit_fallback_entries = workspace_delta_first_mode_entries(
        mode=WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED,
    )
    return {
        "readiness_kind": META_OCG_DELTA_PRODUCT_READINESS_KIND,
        "contract_version": (
            SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION
        ),
        "provider_contract_version": (META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION),
        "provider_key": "aware_meta",
        "status": "ready",
        "reason": "meta_ocg_delta_product_readiness_matrix_ready",
        "default_policy": "ready_operations_only",
        "fallback_policy": "explicit_fallback_required",
        "operation_count": len(_MATRIX),
        "ready_operation_count": len(ready_entries),
        "render_all_required_operation_count": len(render_all_entries),
        "blocked_operation_count": len(blocked_entries),
        "workspace_delta_first_default_policy": (
            "public_lifecycle_ready_operations_only"
        ),
        "workspace_delta_first_ready_operation_count": len(workspace_ready_entries),
        "workspace_delta_first_mode_counts": workspace_delta_first_mode_counts(),
        "workspace_delta_first_ready_operations": tuple(
            _product_readiness_operation_payload(entry)
            for entry in workspace_ready_entries
        ),
        "workspace_generated_apply_ready_operations": tuple(
            _product_readiness_operation_payload(entry)
            for entry in workspace_generated_entries
        ),
        "workspace_graph_only_ready_operations": tuple(
            _product_readiness_operation_payload(entry)
            for entry in workspace_graph_only_entries
        ),
        "workspace_semantic_contract_only_operations": tuple(
            _product_readiness_operation_payload(entry)
            for entry in workspace_contract_only_entries
        ),
        "workspace_explicit_fallback_required_operations": tuple(
            _product_readiness_operation_payload(entry)
            for entry in workspace_explicit_fallback_entries
        ),
        "ready_operations": tuple(
            _product_readiness_operation_payload(entry) for entry in ready_entries
        ),
        "render_all_required_operations": tuple(
            _product_readiness_operation_payload(entry) for entry in render_all_entries
        ),
        "blocked_operations": tuple(
            _product_readiness_operation_payload(entry) for entry in blocked_entries
        ),
    }


def source_projection_ready_entries() -> tuple[
    MetaOcgDeltaCoverageMatrixEntry,
    ...,
]:
    return tuple(entry for entry in _MATRIX if entry.source_projection_ready)


def workspace_delta_first_ready_entries() -> tuple[
    MetaOcgDeltaCoverageMatrixEntry,
    ...,
]:
    return tuple(entry for entry in _MATRIX if entry.workspace_delta_first_ready)


def workspace_delta_first_mode_entries(
    *,
    mode: str,
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    return tuple(entry for entry in _MATRIX if entry.workspace_delta_first_mode == mode)


def workspace_delta_first_mode_counts() -> dict[str, int]:
    return {
        mode: len(workspace_delta_first_mode_entries(mode=mode))
        for mode in WORKSPACE_DELTA_FIRST_MODES
    }


def workspace_delta_first_mode(
    *,
    entry: MetaOcgDeltaCoverageMatrixEntry,
) -> str:
    if (
        entry.ontology_execution_status == STATUS_BLOCKED
        or entry.source_projection_status == STATUS_BLOCKED
    ):
        return WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED
    if entry.home_proof_status != HOME_PROOF_COVERED:
        return WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY
    if entry.case_key in _WORKSPACE_DELTA_FIRST_GRAPH_ONLY_CASE_KEYS:
        return WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY
    if entry.source_projection_status == STATUS_READY:
        return WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY
    return WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY


def source_projection_gap_entries(
    *,
    priority: str | None = None,
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    entries = tuple(
        entry
        for entry in _MATRIX
        if entry.source_projection_gap
        and entry.source_projection_status != STATUS_SKIPPED_POLICY
        and (priority is None or entry.next_priority == priority)
    )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                _NEXT_PRIORITY_ORDER.get(entry.next_priority or "TBD", 99),
                entry.case_key,
            ),
        )
    )


def source_projection_policy_entries(
    *,
    policy: str,
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    return tuple(entry for entry in _MATRIX if entry.source_projection_policy == policy)


def _product_readiness_operation_payload(
    entry: MetaOcgDeltaCoverageMatrixEntry,
) -> dict[str, object]:
    return {
        "case_key": entry.case_key,
        "feature_key": entry.feature_key,
        "provider_operation_type": entry.provider_operation_type,
        "ontology_subject_kind": entry.ontology_subject_kind,
        "operation_family": entry.operation_family,
        "source_projection_policy": entry.source_projection_policy,
        "source_projection_reason": entry.source_projection_reason,
        "language_target_impact_policy": entry.language_target_impact_policy,
        "public_lifecycle_status": entry.home_proof_status,
        "public_lifecycle_refs": entry.home_proof_refs,
        "workspace_delta_first_mode": entry.workspace_delta_first_mode,
        "workspace_delta_first_ready": entry.workspace_delta_first_ready,
    }


def matrix_entries_for_registration_key(
    *,
    ontology_subject_kind: str,
    operation_family: str,
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    return tuple(
        entry
        for entry in _MATRIX
        if entry.ontology_subject_kind == ontology_subject_kind
        and entry.operation_family == operation_family
    )


_HOME_LATEST_BASELINE_PROOF = (
    "workspaces/aware_home/docs/proofs/tests/"
    "test_workspace_meta_latest_baseline_delta_dogfood.py"
)
_HOME_WORLD_CHANGE_PROOF = (
    "workspaces/aware_home/docs/proofs/meta-delta-world-change-events"
)
_HOME_FUNCTION_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_home/docs/proofs/tests/"
    "test_workspace_sdk_home_meta_function_generated_materialization_actual_apply_servicehost.py"
)
_HOME_ATTRIBUTE_DEFAULT_PUBLIC_PROOF = (
    "workspaces/aware_home/docs/proofs/tests/"
    "test_workspace_sdk_home_meta_attribute_config_default_value_semantic_apply_e2e_servicehost.py"
)
_HOME_FUNCTION_SIGNATURE_PROVIDER_DELTA_PROOF = (
    "workspaces/aware_home/docs/proofs/tests/"
    "test_workspace_sdk_home_meta_function_signature_provider_delta_receipt_servicehost.py"
)
_KERNEL_ATTRIBUTE_STRUCTURAL_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_attribute_config_structural_create_delete_public_lifecycle_servicehost.py"
)
_KERNEL_CLASS_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_class_config_structural_create_public_lifecycle_servicehost.py"
)
_KERNEL_CLASS_DELETE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_class_config_structural_delete_public_lifecycle_servicehost.py"
)
_KERNEL_RELATIONSHIP_STRUCTURAL_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_relationship_config_structural_create_delete_public_lifecycle_servicehost.py"
)
_KERNEL_ENUM_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_enum_structural_create_public_lifecycle_servicehost.py"
)
_KERNEL_ENUM_DESCRIPTION_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_enum_config_description_public_lifecycle_servicehost.py"
)
_KERNEL_ENUM_DELETE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_enum_structural_delete_public_lifecycle_servicehost.py"
)
_KERNEL_ENUM_OPTION_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_enum_option_create_public_lifecycle_servicehost.py"
)
_KERNEL_ENUM_OPTION_REORDER_DELETE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_enum_option_reorder_delete_public_lifecycle_servicehost.py"
)
_KERNEL_FUNCTION_DELETE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_function_config_delete_public_lifecycle_servicehost.py"
)
_KERNEL_FUNCTION_IMPL_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_function_impl_create_public_lifecycle_servicehost.py"
)
_KERNEL_FUNCTION_INVOCATION_CREATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_function_invocation_create_public_lifecycle_servicehost.py"
)
_KERNEL_FUNCTION_MEMBERSHIP_UPDATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_function_membership_update_public_lifecycle_servicehost.py"
)
_KERNEL_ATTRIBUTE_MEMBERSHIP_UPDATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_attribute_membership_update_public_lifecycle_servicehost.py"
)
_KERNEL_ATTRIBUTE_IDENTITY_REPLACEMENT_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_attribute_config_identity_replacement_public_lifecycle_servicehost.py"
)
_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF = (
    "workspaces/aware_workspace/modules/workspace/ontology/runtime/python/tests/"
    "test_workspace_meta_genesis_materialize_delta_only.py"
)

_MATRIX: tuple[MetaOcgDeltaCoverageMatrixEntry, ...] = (
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="object_config_graph_package.create",
        feature_key="object_config_graph_package",
        ontology_subject_kind="object_config_graph_package",
        operation_family="create",
        provider_operation_type="meta_ocg.object_config_graph_package.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_object_config_graph_package_requires_renderer_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF,),
        notes=(
            "Package genesis executes through ObjectConfigGraphPackage.build and "
            "attach_object_config_graph FunctionCalls."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="object_config_graph_package.update",
        feature_key="object_config_graph_package",
        ontology_subject_kind="object_config_graph_package",
        operation_family="update",
        provider_operation_type="meta_ocg.object_config_graph_package.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_object_config_graph_package_requires_renderer_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF,),
        notes=(
            "Package update execution is graph-structural and Workspace "
            "materialize genesis-covered."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="object_config_graph.create",
        feature_key="object_config_graph",
        ontology_subject_kind="object_config_graph",
        operation_family="create",
        provider_operation_type="meta_ocg.object_config_graph.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_object_config_graph_requires_renderer_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF,),
        notes="ObjectConfigGraph genesis creates graph roots through FunctionCalls.",
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="object_projection_graph.create",
        feature_key="object_projection_graph",
        ontology_subject_kind="object_projection_graph",
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_object_projection_graph_requires_renderer_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF,),
        notes="OPG genesis executes through build_via_object_config_graph.",
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="object_projection_graph_node.create",
        feature_key="object_projection_graph",
        ontology_subject_kind="object_projection_graph_node",
        operation_family="create",
        provider_operation_type="meta_ocg.object_projection_graph_node.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_object_projection_graph_node_requires_renderer_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_WORKSPACE_META_GENESIS_DELTA_ONLY_PROOF,),
        notes=(
            "OPG node genesis is projection-structural and Workspace materialize "
            "genesis-covered."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="class.create",
        feature_key="class_config",
        ontology_subject_kind="class",
        operation_family="create",
        provider_operation_type="meta_ocg.class.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_class_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_CLASS_CREATE_PUBLIC_PROOF,),
        notes=(
            "Creates through ObjectConfigGraph.create_node and "
            "ObjectConfigGraphNode.create_class; selected-kernel public proof "
            "covers guarded generated Python ORM class insertion."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="class.delete",
        feature_key="class_config",
        ontology_subject_kind="class",
        operation_family="delete",
        provider_operation_type="meta_ocg.class.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_class_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_CLASS_DELETE_PUBLIC_PROOF,),
        notes=(
            "Deletes through ObjectConfigGraph.delete_node. Generated Python "
            "ORM class removal is ready and public Kernel proof exists; authored "
            ".aware source projection remains skipped until projected-section "
            "support exists."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="class.update.metadata",
        feature_key="class_config",
        ontology_subject_kind="class",
        operation_family="update",
        provider_operation_type="meta_ocg.class.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_class_config_description_segment_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        code_section_type="class",
        code_segment_name="description_comment",
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v10/DELTA.md",
        ),
        notes=(
            "Home v9 -> v10 proves ClassConfig.update_config; Code resolves "
            "class description_comment as an Aware doc-comment segment."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="relationship.create",
        feature_key="relationship_config",
        ontology_subject_kind="relationship",
        operation_family="create",
        provider_operation_type="meta_ocg.relationship.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_relationship_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_RELATIONSHIP_STRUCTURAL_PUBLIC_PROOF,),
        notes=(
            "Creates through ClassConfig.create_relationship. Generated Python "
            "ORM relationship field insertion is ready; authored .aware source "
            "projection remains skipped until projected-section support exists."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="relationship.update.metadata",
        feature_key="relationship_config",
        ontology_subject_kind="relationship",
        operation_family="update",
        provider_operation_type="meta_ocg.relationship.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_relationship_config_load_policy_annotation_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="annotation",
        code_segment_name="args",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v12/DELTA.md",
        ),
        notes=(
            "Home v11 -> v12 proves ClassConfigRelationship.update_config. "
            "Existing load annotations replace annotation.args; first load policy "
            "materialization inserts an annotation after the owning class section."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="relationship.delete",
        feature_key="relationship_config",
        ontology_subject_kind="relationship",
        operation_family="delete",
        provider_operation_type="meta_ocg.relationship.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_relationship_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_RELATIONSHIP_STRUCTURAL_PUBLIC_PROOF,),
        notes=(
            "Deletes through ClassConfig.remove_relationship_config. Generated "
            "Python ORM relationship field removal is ready; authored .aware "
            "source projection remains skipped until projected-section support "
            "exists."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum.create",
        feature_key="enum_config",
        ontology_subject_kind="enum",
        operation_family="create",
        provider_operation_type="meta_ocg.enum.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_enum_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_CREATE_PUBLIC_PROOF,),
        notes=(
            "EnumConfig creates through ObjectConfigGraphNode.create_enum; "
            "selected-kernel public proof covers guarded generated Python enum "
            "class insertion."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum.delete",
        feature_key="enum_config",
        ontology_subject_kind="enum",
        operation_family="delete",
        provider_operation_type="meta_ocg.enum.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_enum_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_DELETE_PUBLIC_PROOF,),
        notes=(
            "Deletes through ObjectConfigGraph.delete_node. Generated Python "
            "enum class removal is ready and public Kernel proof exists; authored "
            ".aware source projection remains skipped until projected-section "
            "support exists."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum.update",
        feature_key="enum_config",
        ontology_subject_kind="enum",
        operation_family="update",
        provider_operation_type="meta_ocg.enum.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_generated_materialization_enum_description_docstring_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="enum",
        code_segment_name="description_comment",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_DESCRIPTION_PUBLIC_PROOF,),
        notes=(
            "EnumConfig description source meaning resolves through "
            "enum_def.description_comment to EnumConfig.update_config and "
            "generated Python enum docstring deltas. Selected-kernel public "
            "proof covers guarded generated Python enum docstring replacement."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum_option.create",
        feature_key="enum_config",
        ontology_subject_kind="enum_option",
        operation_family="create",
        provider_operation_type="meta_ocg.enum_option.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_enum_option_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_OPTION_CREATE_PUBLIC_PROOF,),
        notes=(
            "EnumOption creates through EnumConfig.create_enum_option; "
            "selected-kernel public proof covers guarded generated Python enum "
            "option-line insertion."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum_option.update",
        feature_key="enum_config",
        ontology_subject_kind="enum_option",
        operation_family="update",
        provider_operation_type="meta_ocg.enum_option.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_generated_materialization_enum_option_reorder_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="enum",
        code_segment_name="option_line",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_OPTION_REORDER_DELETE_PUBLIC_PROOF,),
        notes=(
            "EnumOption position updates execute through EnumOption.update_config "
            "and generated Python enum option-line block rewrites when source "
            "spans are safe."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="enum_option.delete",
        feature_key="enum_config",
        ontology_subject_kind="enum_option",
        operation_family="delete",
        provider_operation_type="meta_ocg.enum_option.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_generated_materialization_enum_option_delete_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="enum",
        code_segment_name="option_line",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ENUM_OPTION_REORDER_DELETE_PUBLIC_PROOF,),
        notes=(
            "EnumOption deletes execute through EnumConfig.delete_enum_option "
            "and generated Python enum option-line removals when source spans "
            "are safe."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute.create",
        feature_key="attribute_config",
        ontology_subject_kind="attribute",
        operation_family="create",
        provider_operation_type="meta_ocg.attribute.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_attribute_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v9/DELTA.md",
            _KERNEL_ATTRIBUTE_STRUCTURAL_PUBLIC_PROOF,
        ),
        notes=(
            "Home v8 -> v9 covers function-input replacement create/delete "
            "through ontology FunctionCalls; selected-kernel public proof covers "
            "guarded generated Python ORM field insertion/removal."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute.update.primitive_type",
        feature_key="attribute_config",
        ontology_subject_kind="attribute",
        operation_family="update",
        provider_operation_type="meta_ocg.attribute.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_attribute_config_type_segment_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="attribute",
        code_segment_name="type",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v5/DELTA.md",
        ),
        notes="Code-owned replace_segment for AttributeConfig primitive type.",
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute.update.default_value",
        feature_key="attribute_config",
        ontology_subject_kind="attribute",
        operation_family="update",
        provider_operation_type="meta_ocg.attribute.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_attribute_config_default_value_segment_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="attribute",
        code_segment_name="default_value",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_HOME_ATTRIBUTE_DEFAULT_PUBLIC_PROOF,),
        notes=(
            "Code-owned replace_segment for renderable primitive "
            "AttributeConfig default values; unsupported deletion remains blocked."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute.identity.rename",
        feature_key="attribute_config",
        ontology_subject_kind="attribute",
        operation_family="rename",
        provider_operation_type="meta_ocg.attribute.identity.rename",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "Attribute name changes are identity replacements, not mutable "
            "scalar segment updates; public lifecycle uses ordered "
            "attribute.delete + attribute.create generated apply."
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        code_section_type="attribute",
        code_segment_name="name",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ATTRIBUTE_IDENTITY_REPLACEMENT_PUBLIC_PROOF,),
        notes=(
            "Attribute identity replacement composes trusted rename intent to "
            "delete/create and public source-delta lifecycle executes the current "
            "structural pair, applying ordered generated Python ORM field "
            "delete/create deltas. It must not route to AttributeConfig.update_config."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute.delete",
        feature_key="attribute_config",
        ontology_subject_kind="attribute",
        operation_family="delete",
        provider_operation_type="meta_ocg.attribute.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_attribute_config_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v9/DELTA.md",
            _KERNEL_ATTRIBUTE_STRUCTURAL_PUBLIC_PROOF,
        ),
        notes="Deletes through owner remove_attribute_config FunctionCalls.",
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="attribute_membership.update",
        feature_key="attribute_config",
        ontology_subject_kind="attribute_membership",
        operation_family="update",
        provider_operation_type="meta_ocg.attribute_membership.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_attribute_membership_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_ATTRIBUTE_MEMBERSHIP_UPDATE_PUBLIC_PROOF,),
        notes=(
            "Membership updates route through ClassConfigAttributeConfig or "
            "FunctionConfigAttributeConfig update_config."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function.create",
        feature_key="function_config",
        ontology_subject_kind="function",
        operation_family="create",
        provider_operation_type="meta_ocg.function.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_function_config_create_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_HOME_FUNCTION_CREATE_PUBLIC_PROOF,),
        notes=(
            "FunctionConfig creates through owning ClassConfig FunctionCalls; "
            "Home public proof covers semantic_apply plus guarded generated "
            "Python ORM nested function insertion while authored `.aware` "
            "source projection remains structural/render-all-required."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function.delete",
        feature_key="function_config",
        ontology_subject_kind="function",
        operation_family="delete",
        provider_operation_type="meta_ocg.function.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_function_config_delete_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_FUNCTION_DELETE_PUBLIC_PROOF,),
        notes=(
            "Deletes through owning ClassConfig.remove_function_config "
            "FunctionCalls; selected-kernel public proof covers guarded generated "
            "Python ORM function removal."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function.update.description",
        feature_key="function_config",
        ontology_subject_kind="function",
        operation_family="update",
        provider_operation_type="meta_ocg.function.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_function_config_description_segment_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="function",
        code_segment_name="description_comment",
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v11/DELTA.md",
        ),
        notes=(
            "Description-only FunctionConfig updates skip runtime handlers and "
            "refresh structural/generated ontology targets."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function.update.signature_shape",
        feature_key="function_config",
        ontology_subject_kind="function",
        operation_family="update",
        provider_operation_type="meta_ocg.function.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_function_config_signature_segment_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="function",
        code_segment_name="signature",
        language_target_impact_policy=LANGUAGE_TARGET_UNION,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_HOME_FUNCTION_SIGNATURE_PROVIDER_DELTA_PROOF,),
        notes=(
            "Code-owned replace_segment for renderable Aware FunctionConfig "
            "signature shapes; unsupported shapes remain blocked."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function_invocation.create",
        feature_key="function_config",
        ontology_subject_kind="function_invocation",
        operation_family="create",
        provider_operation_type="meta_ocg.function_invocation.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_function_invocation_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_FUNCTION_INVOCATION_CREATE_PUBLIC_PROOF,),
        notes=(
            "Selected-kernel public proof covers generated FunctionInvocation "
            "create as an intent-only generated-materialization row that applies "
            "a guarded Python ORM body CodePackageDelta."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function_membership.update",
        feature_key="function_config",
        ontology_subject_kind="function_membership",
        operation_family="update",
        provider_operation_type="meta_ocg.function_membership.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_SKIPPED_POLICY,
        source_projection_reason=(
            "meta_source_projection_function_membership_requires_renderer_segment_policy"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        language_target_impact_policy=LANGUAGE_TARGET_STRUCTURAL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_FUNCTION_MEMBERSHIP_UPDATE_PUBLIC_PROOF,),
        notes=(
            "Selected-kernel public proof covers fn_def.verb source meaning, "
            "FunctionConfig update split to ClassConfigFunctionConfig.update_config, "
            "and generated materialization as an intentional skipped/no-op stage."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function_impl.create",
        feature_key="function_impl",
        ontology_subject_kind="function_impl",
        operation_family="create",
        provider_operation_type="meta_ocg.function_impl.create",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_function_impl_section_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="function",
        code_segment_name="body",
        language_target_impact_policy=LANGUAGE_TARGET_FUNCTION_IMPL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(_KERNEL_FUNCTION_IMPL_CREATE_PUBLIC_PROOF,),
        notes=(
            "Selected-kernel public proof covers additive FunctionImpl "
            "instruction body creation through provider-delta ontology execution "
            "and guarded generated Python ORM body replacement."
        ),
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function_impl.update.body",
        feature_key="function_impl",
        ontology_subject_kind="function_impl",
        operation_family="update",
        provider_operation_type="meta_ocg.function_impl.update",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_function_impl_section_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="function",
        code_segment_name="body",
        language_target_impact_policy=LANGUAGE_TARGET_FUNCTION_IMPL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v6/DELTA.md",
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v7/DELTA.md",
        ),
        notes="Home covers additive and replacement FunctionImpl body deltas.",
    ),
    MetaOcgDeltaCoverageMatrixEntry(
        case_key="function_impl.delete.stale_instruction",
        feature_key="function_impl",
        ontology_subject_kind="function_impl",
        operation_family="delete",
        provider_operation_type="meta_ocg.function_impl.delete",
        semantic_change_status=STATUS_READY,
        typed_operation_status=STATUS_READY,
        ontology_execution_status=STATUS_READY,
        source_projection_status=STATUS_READY,
        source_projection_reason=(
            "meta_source_projection_function_impl_section_delta_ready"
        ),
        source_projection_policy=SOURCE_PROJECTION_POLICY_SEGMENT_READY,
        code_section_type="function",
        code_segment_name="body",
        language_target_impact_policy=LANGUAGE_TARGET_FUNCTION_IMPL,
        home_proof_status=HOME_PROOF_COVERED,
        home_proof_refs=(
            _HOME_LATEST_BASELINE_PROOF,
            f"{_HOME_WORLD_CHANGE_PROOF}/versions/v8/DELTA.md",
        ),
        notes="Home covers stale instruction removal as a body replacement.",
    ),
)


__all__ = [
    "HOME_PROOF_COVERED",
    "HOME_PROOF_MODULE_TESTS",
    "HOME_PROOF_NOT_COVERED",
    "LANGUAGE_TARGET_FUNCTION_IMPL",
    "LANGUAGE_TARGET_RENDER_ALL",
    "LANGUAGE_TARGET_STRUCTURAL",
    "META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION",
    "SOURCE_PROJECTION_POLICIES",
    "SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT",
    "SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED",
    "SOURCE_PROJECTION_POLICY_SEGMENT_READY",
    "STATUS_BLOCKED",
    "STATUS_NOT_APPLICABLE",
    "STATUS_PLANNED",
    "STATUS_READY",
    "STATUS_SKIPPED_POLICY",
    "MetaOcgDeltaCoverageMatrixEntry",
    "WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED",
    "WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY",
    "WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY",
    "WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY",
    "WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY",
    "WORKSPACE_DELTA_FIRST_MODES",
    "WORKSPACE_DELTA_FIRST_READY_MODES",
    "coverage_matrix_payload",
    "matrix_entries_for_registration_key",
    "meta_ocg_delta_product_readiness_payload",
    "meta_ocg_delta_coverage_matrix",
    "source_projection_gap_entries",
    "source_projection_policy_entries",
    "source_projection_ready_entries",
    "workspace_delta_first_mode_counts",
    "workspace_delta_first_mode_entries",
    "workspace_delta_first_ready_entries",
]
