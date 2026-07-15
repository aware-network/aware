from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aware_meta.materialization.deltas.coverage_matrix import (
    HOME_PROOF_COVERED,
    STATUS_READY as COVERAGE_STATUS_READY,
    MetaOcgDeltaCoverageMatrixEntry,
    meta_ocg_delta_coverage_matrix,
)
from aware_meta.graph.config.annotation.compile_contract import (
    meta_ocg_annotation_compile_contract_payload,
)
from aware_meta.graph.config.binding_mirror_contract import (
    meta_ocg_binding_mirror_contract_payload,
)
from aware_meta.materialization.deltas.ocg_opg_readiness_matrix import (
    MetaOcgOpgReadinessMatrixEntry,
    meta_ocg_opg_readiness_matrix,
)


META_OCG_PACKAGE_READINESS_CONTRACT_VERSION = (
    "aware.meta.ocg-package-delta-first-readiness.v0"
)
META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION = (
    "aware.meta.ocg-package-delta-first-readiness-proof.v0"
)

STEP_STATUS_READY = "ready"
STEP_STATUS_BLOCKED = "blocked"

READINESS_MODE_GRAPH_ONLY = "graph_only"
READINESS_MODE_GENERATED_APPLY = "generated_apply"
READINESS_MODE_SEGMENT = "segment"
READINESS_MODE_MIXED = "mixed"

PACKAGE_SPINE_STEP_KEYS = (
    "object_config_graph_package",
    "object_config_graph",
    "class_config",
    "function_config",
)
PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS = (
    "package_class_function_create",
    "attribute_relationship_create",
    "post_create_update",
    "post_update_delete",
)
RELATIONSHIP_CONFIG_CAPABILITY_KEY = "ocg.relationship.config_contract"
DERIVED_RELATIONSHIP_CAPABILITY_KEY = "ocg.relationship.derived_edges"
ANNOTATION_DERIVED_RELATIONSHIP_CAPABILITY_KEY = (
    "ocg.relationship.annotation_derived_edges"
)
NAMESPACE_LAYOUT_CAPABILITY_KEY = "ocg.namespace_layout"
BINDING_MIRROR_CAPABILITY_KEY = "ocg.binding_mirror"
ANNOTATION_SEMANTICS_CAPABILITY_KEY = "ocg.annotation_semantics"
PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS = (
    "no_full_genesis_fallback",
    "no_render_all_fallback",
    "no_source_delta_inference",
    "no_direct_meta_runtime_call",
)
_KERNEL_OCG_PACKAGE_CLASS_FUNCTION_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_ocg_package_class_function_delta_chain_"
    "public_lifecycle_servicehost.py"
)
_KERNEL_OCG_PACKAGE_ATTRIBUTE_RELATIONSHIP_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_ocg_package_attribute_relationship_delta_chain_"
    "public_lifecycle_servicehost.py"
)
_KERNEL_OCG_POST_CREATE_UPDATE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_ocg_post_create_update_delta_chain_"
    "public_lifecycle_servicehost.py"
)
_KERNEL_OCG_POST_UPDATE_DELETE_PUBLIC_PROOF = (
    "workspaces/aware_kernel/docs/proofs/tests/"
    "test_workspace_sdk_kernel_meta_ocg_post_update_delete_delta_chain_"
    "public_lifecycle_servicehost.py"
)


@dataclass(frozen=True, slots=True)
class MetaOcgPackageReadinessStep:
    step_key: str
    order: int
    semantic_surface: str
    required_case_keys: tuple[str, ...]
    required_capability_keys: tuple[str, ...]
    required_ontology_functions: tuple[str, ...]
    readiness_mode: str
    depends_on: tuple[str, ...] = ()
    notes: str = ""
    contract_version: str = META_OCG_PACKAGE_READINESS_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        coverage_entries = _coverage_entries_for_step(self)
        capability_entries = _capability_entries_for_step(self)
        blocker_reasons = _step_blockers(
            coverage_entries=coverage_entries,
            capability_entries=capability_entries,
        )
        status = STEP_STATUS_READY if not blocker_reasons else STEP_STATUS_BLOCKED

        return {
            "contract_version": self.contract_version,
            "step_key": self.step_key,
            "order": self.order,
            "semantic_surface": self.semantic_surface,
            "status": status,
            "delta_first_ready": status == STEP_STATUS_READY,
            "readiness_mode": self.readiness_mode,
            "depends_on": self.depends_on,
            "required_case_keys": self.required_case_keys,
            "required_capability_keys": self.required_capability_keys,
            "required_ontology_functions": self.required_ontology_functions,
            "case_evidence": tuple(
                _coverage_evidence_payload(entry) for entry in coverage_entries
            ),
            "capability_evidence": tuple(
                _capability_evidence_payload(entry) for entry in capability_entries
            ),
            "blocker_reasons": blocker_reasons,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgPublicCompositionLifecycleStep:
    step_key: str
    order: int
    semantic_surface: str
    required_case_keys: tuple[str, ...]
    public_lifecycle_refs: tuple[str, ...]
    fallback_assertions: tuple[str, ...] = PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS
    notes: str = ""
    contract_version: str = META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        coverage_entries = _coverage_entries_for_case_keys(self.required_case_keys)
        blocker_reasons = _public_lifecycle_blockers(
            coverage_entries=coverage_entries,
            public_lifecycle_refs=self.public_lifecycle_refs,
        )
        status = STEP_STATUS_READY if not blocker_reasons else STEP_STATUS_BLOCKED

        return {
            "contract_version": self.contract_version,
            "step_key": self.step_key,
            "order": self.order,
            "semantic_surface": self.semantic_surface,
            "status": status,
            "public_lifecycle_ready": status == STEP_STATUS_READY,
            "required_case_keys": self.required_case_keys,
            "case_evidence": tuple(
                _coverage_evidence_payload(entry) for entry in coverage_entries
            ),
            "public_lifecycle_refs": self.public_lifecycle_refs,
            "fallback_assertions": self.fallback_assertions,
            "blocker_reasons": blocker_reasons,
            "notes": self.notes,
        }


def meta_ocg_package_readiness_steps() -> tuple[MetaOcgPackageReadinessStep, ...]:
    return _STEPS


def meta_ocg_public_composition_lifecycle_steps() -> tuple[
    MetaOcgPublicCompositionLifecycleStep,
    ...,
]:
    return _PUBLIC_COMPOSITION_LIFECYCLE_STEPS


def meta_ocg_package_readiness_payload() -> dict[str, object]:
    step_payloads = tuple(step.evidence_payload() for step in _STEPS)
    public_composition_lifecycle = meta_ocg_public_composition_lifecycle_payload()
    ready_steps = tuple(
        payload for payload in step_payloads if payload["status"] == STEP_STATUS_READY
    )
    blocked_steps = tuple(
        payload for payload in step_payloads if payload["status"] == STEP_STATUS_BLOCKED
    )
    package_spine_payloads = tuple(
        payload
        for payload in step_payloads
        if payload["step_key"] in PACKAGE_SPINE_STEP_KEYS
    )
    package_spine_ready = all(
        payload["status"] == STEP_STATUS_READY for payload in package_spine_payloads
    )
    next_blocked_step = blocked_steps[0] if blocked_steps else None

    complete_delta_first_ready = len(blocked_steps) == 0

    return {
        "contract_version": META_OCG_PACKAGE_READINESS_CONTRACT_VERSION,
        "readiness_kind": "meta_ocg_package_delta_first_readiness",
        "status": (
            "complete_delta_first_ready"
            if complete_delta_first_ready
            else (
                "package_spine_ready"
                if package_spine_ready
                else "package_spine_blocked"
            )
        ),
        "package_spine_ready": package_spine_ready,
        "complete_delta_first_ready": complete_delta_first_ready,
        "step_count": len(step_payloads),
        "ready_step_count": len(ready_steps),
        "blocked_step_count": len(blocked_steps),
        "package_spine_step_keys": PACKAGE_SPINE_STEP_KEYS,
        "steps": step_payloads,
        "next_blocked_step": next_blocked_step,
        "public_composition_lifecycle_ready": (
            public_composition_lifecycle["status"] == "public_lifecycle_ready"
        ),
        "public_composition_lifecycle_step_keys": (
            public_composition_lifecycle["ordered_step_keys"]
        ),
        "full_genesis_required": False,
        "builder_fallback_allowed": False,
        "notes": (
            "Package spine readiness composes existing provider-delta operations "
            "and OCG/OPG capability rows. Full builder retirement remains a "
            "separate readiness axis."
        ),
    }


def meta_ocg_public_composition_lifecycle_payload() -> dict[str, object]:
    step_payloads = tuple(
        step.evidence_payload() for step in _PUBLIC_COMPOSITION_LIFECYCLE_STEPS
    )
    blockers = tuple(
        str(blocker)
        for step in step_payloads
        for blocker in _tuple_payload(step, key="blocker_reasons")
    )
    ready = not blockers

    return {
        "contract_version": META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION,
        "lifecycle_kind": "meta_ocg_public_composition_lifecycle",
        "status": "public_lifecycle_ready" if ready else "blocked",
        "public_lifecycle_ready": ready,
        "ordered_step_keys": tuple(str(step["step_key"]) for step in step_payloads),
        "ordered_steps": step_payloads,
        "required_case_keys": _unique_texts(
            str(case_key)
            for step in step_payloads
            for case_key in _tuple_payload(step, key="required_case_keys")
        ),
        "required_provider_operation_types": _unique_texts(
            str(case["provider_operation_type"])
            for step in step_payloads
            for case in _case_evidence(step_payload=step)
        ),
        "public_lifecycle_refs": _unique_texts(
            str(ref)
            for step in step_payloads
            for ref in _tuple_payload(step, key="public_lifecycle_refs")
        ),
        "fallback_assertions": PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS,
        "blocker_reasons": blockers,
        "next_action": (
            "run_workspace_delta_first_composition_lifecycle"
            if ready
            else "inspect_public_composition_lifecycle_blockers"
        ),
    }


def meta_ocg_package_delta_first_readiness_proof_payload() -> dict[str, object]:
    readiness_payload = meta_ocg_package_readiness_payload()
    steps = _step_payloads(readiness_payload=readiness_payload)
    public_composition_lifecycle = meta_ocg_public_composition_lifecycle_payload()
    relationship_config = _capability_entry(
        capability_key=RELATIONSHIP_CONFIG_CAPABILITY_KEY,
    )
    derived_relationship = _capability_entry(
        capability_key=DERIVED_RELATIONSHIP_CAPABILITY_KEY,
    )
    annotation_derived_relationship = _capability_entry(
        capability_key=ANNOTATION_DERIVED_RELATIONSHIP_CAPABILITY_KEY,
    )
    namespace_layout = _capability_entry(
        capability_key=NAMESPACE_LAYOUT_CAPABILITY_KEY,
    )
    binding_mirror = _capability_entry(
        capability_key=BINDING_MIRROR_CAPABILITY_KEY,
    )
    annotation_semantics = _capability_entry(
        capability_key=ANNOTATION_SEMANTICS_CAPABILITY_KEY,
    )
    remaining_builder_retirement_blockers = tuple(
        _remaining_blocker_payload(entry)
        for entry in meta_ocg_opg_readiness_matrix()
        if entry.builder_retirement_blocked
    )

    return {
        "contract_version": META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION,
        "proof_kind": "meta_ocg_package_delta_first_readiness_proof",
        "readiness_contract_version": META_OCG_PACKAGE_READINESS_CONTRACT_VERSION,
        "status": readiness_payload["status"],
        "package_delta_first_ready": (
            readiness_payload["complete_delta_first_ready"] is True
        ),
        "package_spine_ready": readiness_payload["package_spine_ready"],
        "complete_delta_first_ready": (readiness_payload["complete_delta_first_ready"]),
        "full_genesis_required": readiness_payload["full_genesis_required"],
        "builder_fallback_allowed": readiness_payload["builder_fallback_allowed"],
        "public_composition_lifecycle_ready": (
            public_composition_lifecycle["public_lifecycle_ready"]
        ),
        "public_composition_lifecycle": public_composition_lifecycle,
        "ordered_step_keys": tuple(str(step["step_key"]) for step in steps),
        "ordered_package_sequence": tuple(
            _package_sequence_step_payload(step) for step in steps
        ),
        "required_provider_operation_types": _unique_texts(
            str(case["provider_operation_type"])
            for step in steps
            for case in _case_evidence(step_payload=step)
        ),
        "required_ontology_functions": _unique_texts(
            str(function_name)
            for step in steps
            for function_name in _tuple_payload(
                step,
                key="required_ontology_functions",
            )
        ),
        "relationship_config_capability": _capability_proof_payload(
            entry=relationship_config,
        ),
        "derived_relationship_edge_capability": _capability_proof_payload(
            entry=derived_relationship,
        ),
        "relationship_annotation_effect_capability": _capability_proof_payload(
            entry=annotation_derived_relationship,
        ),
        "namespace_layout_recompute_capability": _capability_proof_payload(
            entry=namespace_layout,
        ),
        "binding_mirror_capability": _capability_proof_payload(
            entry=binding_mirror,
        ),
        "binding_mirror_contract": meta_ocg_binding_mirror_contract_payload(),
        "annotation_semantics_capability": _capability_proof_payload(
            entry=annotation_semantics,
        ),
        "annotation_compile_contract": (meta_ocg_annotation_compile_contract_payload()),
        "derived_relationship_edge_debt": _capability_proof_payload(
            entry=annotation_derived_relationship,
        ),
        "remaining_builder_retirement_blockers": (
            remaining_builder_retirement_blockers
        ),
        "next_action": (
            "materialize_delta_first_without_full_genesis"
            if readiness_payload["complete_delta_first_ready"] is True
            else "inspect_blocked_package_readiness_step"
        ),
    }


def ready_package_spine_steps() -> tuple[MetaOcgPackageReadinessStep, ...]:
    return tuple(
        step
        for step in _STEPS
        if step.step_key in PACKAGE_SPINE_STEP_KEYS
        and step.evidence_payload()["status"] == STEP_STATUS_READY
    )


def blocked_package_readiness_steps() -> tuple[MetaOcgPackageReadinessStep, ...]:
    return tuple(
        step
        for step in _STEPS
        if step.evidence_payload()["status"] == STEP_STATUS_BLOCKED
    )


def _coverage_entries_for_step(
    step: MetaOcgPackageReadinessStep,
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    return _coverage_entries_for_case_keys(step.required_case_keys)


def _coverage_entries_for_case_keys(
    case_keys: tuple[str, ...],
) -> tuple[MetaOcgDeltaCoverageMatrixEntry, ...]:
    entry_by_case = {
        entry.case_key: entry for entry in meta_ocg_delta_coverage_matrix()
    }
    return tuple(entry_by_case[key] for key in case_keys)


def _capability_entries_for_step(
    step: MetaOcgPackageReadinessStep,
) -> tuple[MetaOcgOpgReadinessMatrixEntry, ...]:
    entry_by_key = {
        entry.capability_key: entry for entry in meta_ocg_opg_readiness_matrix()
    }
    return tuple(entry_by_key[key] for key in step.required_capability_keys)


def _capability_entry(*, capability_key: str) -> MetaOcgOpgReadinessMatrixEntry:
    entry_by_key = {
        entry.capability_key: entry for entry in meta_ocg_opg_readiness_matrix()
    }
    return entry_by_key[capability_key]


def _step_blockers(
    *,
    coverage_entries: Iterable[MetaOcgDeltaCoverageMatrixEntry],
    capability_entries: Iterable[MetaOcgOpgReadinessMatrixEntry],
) -> tuple[str, ...]:
    blockers: list[str] = []
    for entry in coverage_entries:
        if entry.semantic_change_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:semantic_change_not_ready")
        if entry.typed_operation_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:typed_operation_not_ready")
        if entry.ontology_execution_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:ontology_execution_not_ready")
        if entry.home_proof_status != HOME_PROOF_COVERED:
            blockers.append(f"{entry.case_key}:public_lifecycle_proof_missing")
        if not entry.workspace_delta_first_ready:
            blockers.append(f"{entry.case_key}:workspace_delta_first_not_ready")
    for entry in capability_entries:
        if not entry.provider_delta_production_ready:
            blockers.append(
                f"{entry.capability_key}:provider_delta_production_not_ready"
            )
            blockers.extend(
                f"{entry.capability_key}:{blocker}" for blocker in entry.blockers
            )
    return tuple(blockers)


def _public_lifecycle_blockers(
    *,
    coverage_entries: Iterable[MetaOcgDeltaCoverageMatrixEntry],
    public_lifecycle_refs: tuple[str, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not public_lifecycle_refs:
        blockers.append("public_lifecycle_refs_missing")
    for entry in coverage_entries:
        if entry.semantic_change_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:semantic_change_not_ready")
        if entry.typed_operation_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:typed_operation_not_ready")
        if entry.ontology_execution_status != COVERAGE_STATUS_READY:
            blockers.append(f"{entry.case_key}:ontology_execution_not_ready")
        if entry.home_proof_status != HOME_PROOF_COVERED:
            blockers.append(f"{entry.case_key}:public_lifecycle_proof_missing")
        if not entry.workspace_delta_first_ready:
            blockers.append(f"{entry.case_key}:workspace_delta_first_not_ready")
    return tuple(blockers)


def _coverage_evidence_payload(
    entry: MetaOcgDeltaCoverageMatrixEntry,
) -> dict[str, object]:
    return {
        "case_key": entry.case_key,
        "provider_operation_type": entry.provider_operation_type,
        "ontology_subject_kind": entry.ontology_subject_kind,
        "operation_family": entry.operation_family,
        "semantic_change_status": entry.semantic_change_status,
        "typed_operation_status": entry.typed_operation_status,
        "ontology_execution_status": entry.ontology_execution_status,
        "workspace_delta_first_mode": entry.workspace_delta_first_mode,
        "workspace_delta_first_ready": entry.workspace_delta_first_ready,
        "public_lifecycle_status": entry.home_proof_status,
        "public_lifecycle_refs": entry.home_proof_refs,
    }


def _capability_evidence_payload(
    entry: MetaOcgOpgReadinessMatrixEntry,
) -> dict[str, object]:
    return {
        "capability_key": entry.capability_key,
        "semantic_surface": entry.semantic_surface,
        "required_ontology_functions": entry.required_ontology_functions,
        "provider_delta_production_ready": entry.provider_delta_production_ready,
        "builder_retirement_status": entry.builder_retirement_status,
        "blockers": entry.blockers,
    }


def _step_payloads(
    *, readiness_payload: dict[str, object]
) -> tuple[dict[str, object], ...]:
    value = readiness_payload.get("steps")
    if not isinstance(value, tuple):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _case_evidence(*, step_payload: dict[str, object]) -> tuple[dict[str, object], ...]:
    value = step_payload.get("case_evidence")
    if not isinstance(value, tuple):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _tuple_payload(
    payload: dict[str, object],
    *,
    key: str,
) -> tuple[object, ...]:
    value = payload.get(key)
    if isinstance(value, tuple):
        return value
    return ()


def _package_sequence_step_payload(
    step_payload: dict[str, object]
) -> dict[str, object]:
    return {
        "step_key": step_payload["step_key"],
        "order": step_payload["order"],
        "status": step_payload["status"],
        "readiness_mode": step_payload["readiness_mode"],
        "required_case_keys": step_payload["required_case_keys"],
        "required_capability_keys": step_payload["required_capability_keys"],
        "required_ontology_functions": step_payload["required_ontology_functions"],
    }


def _capability_proof_payload(
    *,
    entry: MetaOcgOpgReadinessMatrixEntry,
) -> dict[str, object]:
    return {
        "capability_key": entry.capability_key,
        "semantic_surface": entry.semantic_surface,
        "typed_operation_status": entry.typed_operation_status,
        "ontology_function_status": entry.ontology_function_status,
        "handler_status": entry.handler_status,
        "functioncall_execution_status": entry.functioncall_execution_status,
        "oig_commit_status": entry.oig_commit_status,
        "package_index_status": entry.package_index_status,
        "opg_materialization_status": entry.opg_materialization_status,
        "provider_delta_production_ready": entry.provider_delta_production_ready,
        "builder_retirement_status": entry.builder_retirement_status,
        "blockers": entry.blockers,
    }


def _remaining_blocker_payload(
    entry: MetaOcgOpgReadinessMatrixEntry,
) -> dict[str, object]:
    return {
        "capability_key": entry.capability_key,
        "capability_group": entry.capability_group,
        "next_priority": entry.next_priority,
        "blockers": entry.blockers,
    }


def _unique_texts(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


_STEPS: tuple[MetaOcgPackageReadinessStep, ...] = (
    MetaOcgPackageReadinessStep(
        step_key="object_config_graph_package",
        order=1,
        semantic_surface="ObjectConfigGraphPackage package root",
        required_case_keys=("object_config_graph_package.create",),
        required_capability_keys=("ocg.package_identity_plane",),
        required_ontology_functions=(
            "ObjectConfigGraphPackage.build",
            "ObjectConfigGraphPackage.attach_object_config_graph",
        ),
        readiness_mode=READINESS_MODE_GRAPH_ONLY,
        notes=(
            "Creates the package shell and binds source package provenance "
            "without invoking a full genesis fallback."
        ),
    ),
    MetaOcgPackageReadinessStep(
        step_key="object_config_graph",
        order=2,
        semantic_surface="ObjectConfigGraph root attached to package",
        required_case_keys=("object_config_graph.create",),
        required_capability_keys=("ocg.graph_root",),
        required_ontology_functions=("ObjectConfigGraph.build",),
        readiness_mode=READINESS_MODE_GRAPH_ONLY,
        depends_on=("object_config_graph_package",),
        notes="Creates the canonical graph root before any class/function member.",
    ),
    MetaOcgPackageReadinessStep(
        step_key="class_config",
        order=3,
        semantic_surface="ObjectConfigGraphNode with ClassConfig payload",
        required_case_keys=("class.create",),
        required_capability_keys=("ocg.class.create_update",),
        required_ontology_functions=(
            "ObjectConfigGraph.create_node",
            "ObjectConfigGraphNode.create_class",
        ),
        readiness_mode=READINESS_MODE_GENERATED_APPLY,
        depends_on=("object_config_graph",),
        notes=(
            "Creates a valid OCG node before attaching the ClassConfig payload; "
            "generated Python ORM class apply is a downstream materialization."
        ),
    ),
    MetaOcgPackageReadinessStep(
        step_key="function_config",
        order=4,
        semantic_surface="FunctionConfig under a ClassConfig membership",
        required_case_keys=("function.create", "function_membership.update"),
        required_capability_keys=("ocg.function.contract",),
        required_ontology_functions=(
            "ClassConfig.create_function_config",
            "ClassConfigFunctionConfig.update_config",
        ),
        readiness_mode=READINESS_MODE_MIXED,
        depends_on=("class_config",),
        notes=(
            "Creates function structure through the class aggregate and locks "
            "membership updates as semantic-only graph changes."
        ),
    ),
    MetaOcgPackageReadinessStep(
        step_key="update_family",
        order=5,
        semantic_surface="Post-create class/function/attribute/relationship updates",
        required_case_keys=(
            "class.update.metadata",
            "function.update.signature_shape",
            "function.update.description",
            "function_impl.update.body",
            "attribute.update.primitive_type",
            "relationship.update.metadata",
        ),
        required_capability_keys=(
            "ocg.class.create_update",
            "ocg.function.contract",
            "ocg.function_impl.graph",
            "ocg.attribute.contract",
            "ocg.relationship.config_contract",
        ),
        required_ontology_functions=(
            "ClassConfig.update_config",
            "FunctionConfig.update_config",
            "FunctionImpl.create_instruction",
            "AttributeConfig.update_primitive",
            "ClassConfigRelationship.update_config",
        ),
        readiness_mode=READINESS_MODE_MIXED,
        depends_on=("function_config",),
        notes=(
            "Update coverage is broad enough for delta-first package evolution. "
            "Derived relationship attribute and annotation semantics remain "
            "tracked by the broader OCG/OPG builder-retirement matrix."
        ),
    ),
)

_PUBLIC_COMPOSITION_LIFECYCLE_STEPS: tuple[
    MetaOcgPublicCompositionLifecycleStep,
    ...,
] = (
    MetaOcgPublicCompositionLifecycleStep(
        step_key="package_class_function_create",
        order=1,
        semantic_surface=(
            "ObjectConfigGraphPackage, ObjectConfigGraph, ClassConfig, and "
            "FunctionConfig public create chain"
        ),
        required_case_keys=(
            "object_config_graph_package.create",
            "object_config_graph_identity.create",
            "object_config_graph.create",
            "object_config_graph_package.update",
            "class.create",
            "function.create",
            "function_membership.update",
        ),
        public_lifecycle_refs=(_KERNEL_OCG_PACKAGE_CLASS_FUNCTION_PUBLIC_PROOF,),
        notes=(
            "Row 172 proves the ordered package/graph/class/function chain "
            "through public Workspace SDK/ServiceHost semantic apply plus "
            "guarded generated class/function apply."
        ),
    ),
    MetaOcgPublicCompositionLifecycleStep(
        step_key="attribute_relationship_create",
        order=2,
        semantic_surface=(
            "AttributeConfig and RelationshipConfig public create chain over "
            "the package/class spine"
        ),
        required_case_keys=(
            "attribute.create",
            "relationship.create",
        ),
        public_lifecycle_refs=(
            _KERNEL_OCG_PACKAGE_ATTRIBUTE_RELATIONSHIP_PUBLIC_PROOF,
        ),
        notes=(
            "Row 173 extends the package/class spine with generated Python ORM "
            "field, relationship, foreign-key, and function stages."
        ),
    ),
    MetaOcgPublicCompositionLifecycleStep(
        step_key="post_create_update",
        order=3,
        semantic_surface=(
            "Existing AttributeConfig, RelationshipConfig, and FunctionConfig "
            "updates over the created package state"
        ),
        required_case_keys=(
            "attribute.update.primitive_type",
            "relationship.update.metadata",
            "function.update.signature_shape",
        ),
        public_lifecycle_refs=(_KERNEL_OCG_POST_CREATE_UPDATE_PUBLIC_PROOF,),
        notes=(
            "Row 174 proves the second pass consumes existing semantic head and "
            "generated package state instead of starting a new genesis pass."
        ),
    ),
    MetaOcgPublicCompositionLifecycleStep(
        step_key="post_update_delete",
        order=4,
        semantic_surface=(
            "Existing FunctionConfig, RelationshipConfig, and AttributeConfig "
            "delete chain over post-update state"
        ),
        required_case_keys=(
            "function.delete",
            "relationship.delete",
            "attribute.delete",
        ),
        public_lifecycle_refs=(_KERNEL_OCG_POST_UPDATE_DELETE_PUBLIC_PROOF,),
        notes=(
            "Row 175 proves delete/remove over the same semantic/generated "
            "state after create and update phases."
        ),
    ),
)
