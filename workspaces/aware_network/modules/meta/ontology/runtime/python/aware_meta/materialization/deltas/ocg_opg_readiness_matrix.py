from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aware_meta.graph.config.annotation.compile_contract import (
    META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION,
)
from aware_meta.graph.config.binding_mirror_contract import (
    BINDING_SEMANTIC_POLICY,
    META_OCG_BINDING_MIRROR_CONTRACT_VERSION,
    MIRROR_SEMANTIC_POLICY,
)
from aware_meta.graph.config.namespace.layout_contract import (
    NAMESPACE_LAYOUT_DERIVATION_POLICY,
    NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY,
)


META_OCG_OPG_READINESS_MATRIX_CONTRACT_VERSION = (
    "aware.meta.ocg-opg-typed-operation-readiness-matrix.v0"
)

STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_PLANNED = "planned"
STATUS_BLOCKED = "blocked"
STATUS_BUILDER_ONLY = "builder_only"
STATUS_NOT_APPLICABLE = "not_applicable"

RETIRE_READY = "builder_retirement_ready"
RETIRE_PARTIAL = "builder_retirement_partial"
RETIRE_BLOCKED = "builder_retirement_blocked"

PROOF_HOME = "home_proof"
PROOF_MODULE = "module_proof"
PROOF_MISSING = "missing_proof"

GROUP_OCG_IDENTITY = "ocg_identity"
GROUP_OCG_NODE = "ocg_node"
GROUP_OCG_MEMBER = "ocg_member"
GROUP_OCG_RELATIONSHIP = "ocg_relationship"
GROUP_OCG_DERIVED = "ocg_derived_semantics"
GROUP_OPG_DECLARATION = "opg_declaration"
GROUP_OPG_MATERIALIZATION = "opg_materialization"

_NEXT_PRIORITY_ORDER = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "TBD": 3,
}


@dataclass(frozen=True, slots=True)
class MetaOcgOpgReadinessMatrixEntry:
    capability_key: str
    capability_group: str
    semantic_surface: str
    builder_authority_refs: tuple[str, ...]
    required_ontology_functions: tuple[str, ...]
    typed_operation_status: str
    ontology_function_status: str
    handler_status: str
    functioncall_execution_status: str
    oig_commit_status: str
    package_index_status: str
    opg_materialization_status: str
    source_generated_delta_status: str
    builder_retirement_status: str
    proof_status: str
    next_priority: str
    blockers: tuple[str, ...]
    notes: str = ""
    contract_version: str = META_OCG_OPG_READINESS_MATRIX_CONTRACT_VERSION

    @property
    def builder_retirement_ready(self) -> bool:
        return self.builder_retirement_status == RETIRE_READY

    @property
    def builder_retirement_blocked(self) -> bool:
        return self.builder_retirement_status == RETIRE_BLOCKED

    @property
    def provider_delta_production_ready(self) -> bool:
        if self.proof_status == PROOF_MISSING:
            return False
        return all(
            status == STATUS_READY
            for status in (
                self.typed_operation_status,
                self.ontology_function_status,
                self.handler_status,
                self.functioncall_execution_status,
                self.oig_commit_status,
                self.package_index_status,
            )
        )

    @property
    def minimal_ocg_opg_blocker(self) -> bool:
        return self.next_priority == "P0" and not self.builder_retirement_ready

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "capability_key": self.capability_key,
            "capability_group": self.capability_group,
            "semantic_surface": self.semantic_surface,
            "builder_authority_refs": self.builder_authority_refs,
            "required_ontology_functions": self.required_ontology_functions,
            "typed_operation_status": self.typed_operation_status,
            "ontology_function_status": self.ontology_function_status,
            "handler_status": self.handler_status,
            "functioncall_execution_status": self.functioncall_execution_status,
            "oig_commit_status": self.oig_commit_status,
            "package_index_status": self.package_index_status,
            "opg_materialization_status": self.opg_materialization_status,
            "source_generated_delta_status": self.source_generated_delta_status,
            "builder_retirement_status": self.builder_retirement_status,
            "provider_delta_production_ready": (self.provider_delta_production_ready),
            "proof_status": self.proof_status,
            "next_priority": self.next_priority,
            "blockers": self.blockers,
            "notes": self.notes,
        }


def meta_ocg_opg_readiness_matrix() -> tuple[
    MetaOcgOpgReadinessMatrixEntry,
    ...,
]:
    return _MATRIX


def ocg_opg_readiness_payload() -> dict[str, object]:
    return {
        "contract_version": META_OCG_OPG_READINESS_MATRIX_CONTRACT_VERSION,
        "entry_count": len(_MATRIX),
        "entries": tuple(entry.evidence_payload() for entry in _MATRIX),
        "builder_retirement_ready_count": len(builder_retirement_ready_entries()),
        "builder_retirement_blocked_count": len(builder_retirement_blocked_entries()),
        "provider_delta_production_ready_count": len(
            provider_delta_production_ready_entries()
        ),
        "provider_delta_production_ready_keys": tuple(
            entry.capability_key for entry in provider_delta_production_ready_entries()
        ),
        "minimal_ocg_opg_blocker_count": len(minimal_ocg_opg_blocker_entries()),
        "builder_retirement_status_counts": _count_by_field(
            field_name="builder_retirement_status",
        ),
        "typed_operation_status_counts": _count_by_field(
            field_name="typed_operation_status",
        ),
        "functioncall_execution_status_counts": _count_by_field(
            field_name="functioncall_execution_status",
        ),
        "oig_commit_status_counts": _count_by_field(
            field_name="oig_commit_status",
        ),
        "opg_materialization_status_counts": _count_by_field(
            field_name="opg_materialization_status",
        ),
        "proof_status_counts": _count_by_field(field_name="proof_status"),
    }


def builder_retirement_ready_entries() -> tuple[
    MetaOcgOpgReadinessMatrixEntry,
    ...,
]:
    return tuple(entry for entry in _MATRIX if entry.builder_retirement_ready)


def builder_retirement_blocked_entries(
    *,
    priority: str | None = None,
) -> tuple[MetaOcgOpgReadinessMatrixEntry, ...]:
    return _sorted_entries(
        entry
        for entry in _MATRIX
        if entry.builder_retirement_blocked
        and (priority is None or entry.next_priority == priority)
    )


def provider_delta_production_ready_entries() -> tuple[
    MetaOcgOpgReadinessMatrixEntry,
    ...,
]:
    return _sorted_entries(
        entry for entry in _MATRIX if entry.provider_delta_production_ready
    )


def minimal_ocg_opg_blocker_entries() -> tuple[
    MetaOcgOpgReadinessMatrixEntry,
    ...,
]:
    return _sorted_entries(entry for entry in _MATRIX if entry.minimal_ocg_opg_blocker)


def entries_for_capability_group(
    *,
    capability_group: str,
) -> tuple[MetaOcgOpgReadinessMatrixEntry, ...]:
    return tuple(
        entry for entry in _MATRIX if entry.capability_group == capability_group
    )


def _count_by_field(*, field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in _MATRIX:
        value = str(getattr(entry, field_name))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _sorted_entries(
    entries: Iterable[MetaOcgOpgReadinessMatrixEntry],
) -> tuple[MetaOcgOpgReadinessMatrixEntry, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                _NEXT_PRIORITY_ORDER.get(entry.next_priority, 99),
                entry.capability_group,
                entry.capability_key,
            ),
        )
    )


_BUILDER = "aware_meta.graph.config.builder"
_PACKAGE_MATERIALIZATION = "aware_meta.graph.package.materialization"
_PROJECTION_COMPILER = "aware_meta.graph.projection.compiler"
_ANNOTATION_COMPILER = "aware_meta.graph.config.annotation"
_RUNTIME_DERIVATION = "aware_meta.graph.config.runtime_derivation.service"

_MATRIX: tuple[MetaOcgOpgReadinessMatrixEntry, ...] = (
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.package_identity_plane",
        capability_group=GROUP_OCG_IDENTITY,
        semantic_surface="ObjectConfigGraphPackage identity and receipt lane",
        builder_authority_refs=(
            f"{_PACKAGE_MATERIALIZATION}.materialize_object_config_graph_package_identity_plane",
            "ObjectConfigGraphPackage.attach_object_config_graph",
        ),
        required_ontology_functions=(
            "ObjectConfigGraphPackage.build",
            "ObjectConfigGraphPackage.attach_object_config_graph",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("full_package_scope_closure_still_builder_local",),
        notes=(
            "Package identity and package/root attachment now execute through "
            "ontology FunctionCalls and commit OIG/package-index truth. Full "
            "builder retirement still waits on package scope closure beyond "
            "the genesis package plane."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.graph_root",
        capability_group=GROUP_OCG_IDENTITY,
        semantic_surface="ObjectConfigGraph root identity/hash/layout hash",
        builder_authority_refs=(
            f"{_BUILDER}.build_object_config_graph",
            f"{_BUILDER}.compute_object_config_graph_hash",
        ),
        required_ontology_functions=("ObjectConfigGraph.build",),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("hash_layout_hash_recompute_policy_still_genesis_scoped",),
        notes=(
            "Root graph creation now executes through ObjectConfigGraph.build "
            "and commits OIG/package-index truth. Builder retirement remains "
            "partial until hash/layout recompute policy is generalized beyond "
            "genesis creation."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.namespace_fqn_resolution",
        capability_group=GROUP_OCG_IDENTITY,
        semantic_surface="Namespace, imports, FQN resolver, external graph closure",
        builder_authority_refs=(
            f"{_BUILDER}.build_fqn_resolver",
            f"{_BUILDER}.build_import_aliases_by_code_id",
        ),
        required_ontology_functions=(),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_NOT_APPLICABLE,
        handler_status=STATUS_NOT_APPLICABLE,
        functioncall_execution_status=STATUS_NOT_APPLICABLE,
        oig_commit_status=STATUS_NOT_APPLICABLE,
        package_index_status=STATUS_PARTIAL,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(),
        notes=(
            "Meta now exposes read-only semantic scope/FQN closure evidence "
            "over namespaces, imports, local symbols, external graph symbols, "
            "and resolution probes. OCG genesis typed-operation planning now "
            "consumes closure evidence before emitting operations, and "
            "ClassConfig create/update, EnumConfig create, and scalar "
            "FunctionConfig create/update plus RelationshipConfig "
            "create/update/delete planning can consume the same gate on "
            "existing graphs. The closure evidence now includes deterministic "
            "local/external closure refs and hashes, and closure-consuming "
            "class, enum, function, and relationship planners promote those "
            "committed refs into typed-operation evidence. Full builder "
            "retirement still needs explicit namespace layout, annotation "
            "semantics, and binding mirror rows."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.class.create_update",
        capability_group=GROUP_OCG_NODE,
        semantic_surface="ClassConfig create/update through OCG node ownership",
        builder_authority_refs=(
            f"{_BUILDER}.build_class_config_from_code",
            f"{_BUILDER}.build_object_config_graph_node",
        ),
        required_ontology_functions=(
            "ObjectConfigGraph.create_node",
            "ObjectConfigGraphNode.create_class",
            "ClassConfig.update_config",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("class_genesis_depends_on_ocg_root_and_namespace_closure",),
        notes=(
            "Provider deltas can commit class nodes, and Python ORM generated "
            "materialization covers class description update plus structural "
            "create/delete through guarded grammar-anchor render deltas. Full "
            "builder retirement still needs graph root and namespace closure "
            "to be typed as well."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.class.inheritance_augment",
        capability_group=GROUP_OCG_NODE,
        semantic_surface="Class inheritance, augment chains, cross-OCG augments",
        builder_authority_refs=(
            f"{_BUILDER}.build_object_config_graph_from_code",
            "cross_class_configs_by_target_ocg",
        ),
        required_ontology_functions=(
            "ClassConfig.update_parent_class",
            "ClassConfig.update_config",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_BLOCKED,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("cross_ocg_augment_functioncall_policy_missing",),
        notes=(
            "Parent inheritance is now a typed class update provider subtype "
            "with child/parent scope closure evidence. ClassConfig exposes a "
            "receiver-owned parent mutation FunctionCall that commits through "
            "the provider-delta OIG runtime fixture and patches package-index "
            "parent evidence. Python ORM generated materialization now emits "
            "guarded class base-expression text-span deltas. Builder retirement "
            "still needs explicit cross-OCG augment policy."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.enum.create_update",
        capability_group=GROUP_OCG_NODE,
        semantic_surface="EnumConfig and EnumOption node materialization",
        builder_authority_refs=(
            f"{_BUILDER}.build_enum_config_from_code",
            f"{_BUILDER}.ObjectConfigGraphNode.create_enum",
        ),
        required_ontology_functions=(
            "ObjectConfigGraph.create_node",
            "ObjectConfigGraphNode.create_enum",
            "EnumConfig.update_config",
            "EnumConfig.create_enum_option",
            "EnumOption.update_config",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_BLOCKED,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("enum_source_generated_delta_policy_incomplete",),
        notes=(
            "Enum create/update and enum-option create/update now have "
            "feature-owned typed-operation planning and ontology FunctionCall "
            "intent mapping. Workspace materialization generated the enum "
            "function surfaces for meta-ontology; builder retirement still "
            "needs source/generated materialization policy for enum changes."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.attribute.contract",
        capability_group=GROUP_OCG_MEMBER,
        semantic_surface="AttributeConfig descriptors and class/function membership",
        builder_authority_refs=(
            "aware_meta.class_.config.builder.build_class_config_members",
            "aware_meta.attribute.config.type_descriptor_helpers.resolve_type_info",
        ),
        required_ontology_functions=(
            "ClassConfig.create_primitive_attribute_config",
            "ClassConfig.create_enum_attribute_config",
            "ClassConfig.create_class_attribute_config",
            "FunctionConfig.create_primitive_attribute_config",
            "FunctionConfig.create_enum_attribute_config",
            "FunctionConfig.create_class_attribute_config",
            "AttributeConfig.update_primitive",
            "AttributeConfig.update_enum",
            "AttributeConfig.update_class",
            "ClassConfigAttributeConfig.update_config",
            "FunctionConfigAttributeConfig.update_config",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_HOME,
        next_priority="P0",
        blockers=(
            "descriptor_tree_collection_child_policy_incomplete",
            "attribute_identity_replacement_policy_not_fully_typed",
        ),
        notes=(
            "Primitive type/default and membership deltas are real; full "
            "attribute parity still needs descriptor tree child operations and "
            "identity replacement semantics."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.function.contract",
        capability_group=GROUP_OCG_MEMBER,
        semantic_surface="FunctionConfig signature, membership, invocation plan",
        builder_authority_refs=(
            "aware_meta.function.config.builder.build_function_config_from_code",
            f"{_BUILDER}._rebuild_class_function_invocations",
        ),
        required_ontology_functions=(
            "ClassConfig.create_function_config",
            "ClassConfig.remove_function_config",
            "ClassConfigFunctionConfig.update_config",
            "FunctionConfig.update_config",
            "FunctionConfig.create_invocation",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=("function_config_delete_public_lifecycle_proof_missing",),
        notes=(
            "Function create/update and class-function membership updates now "
            "have feature-owned typed-operation and ontology FunctionCall "
            "planning. Function invocation-plan creates now execute through "
            "FunctionConfig.create_invocation. FunctionConfig create generated "
            "materialization emits a typed nested-member CodeSectionDelta, and "
            "FunctionConfigInvocation create emits a typed Python ORM function "
            "body replacement when explicit body evidence is available. "
            "FunctionConfig update description changes now emit Python ORM "
            "body-segment replacement evidence for docstring updates. "
            "FunctionConfig signature/async changes now emit typed grammar-"
            "anchor render delta evidence for generated Python signature "
            "spans. Home public proofs cover FunctionConfig create nested "
            "insert, FunctionConfig signature semantic_apply, and "
            "FunctionConfigInvocation body replacement through guarded "
            "generated apply. FunctionConfig delete now routes through "
            "ClassConfig.remove_function_config and emits guarded generated "
            "Python ORM function removal evidence; public lifecycle proof "
            "remains before full builder retirement."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.function_impl.graph",
        capability_group=GROUP_OCG_MEMBER,
        semantic_surface="FunctionImpl instruction graph and body mutations",
        builder_authority_refs=(
            "aware_meta.function.impl.builder.build_function_impl_from_body",
            "aware_meta.function.impl.builder.build_function_invocation_plan_from_body",
        ),
        required_ontology_functions=(
            "FunctionConfig.create_function_impl",
            "FunctionImpl.create_instruction",
            "FunctionImpl.remove_instruction",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_HOME,
        next_priority="P1",
        blockers=("function_impl_genesis_still_depends_on_function_contract",),
        notes=(
            "FunctionImpl mutation is one of the strongest rails; full "
            "retirement waits on FunctionConfig creation/invocation parity."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.relationship.config_contract",
        capability_group=GROUP_OCG_RELATIONSHIP,
        semantic_surface="ClassConfigRelationship create/update/delete",
        builder_authority_refs=(
            "aware_meta.class_.config.relationship.builder.build_class_config_relationships",
        ),
        required_ontology_functions=(
            "ClassConfig.create_relationship",
            "ClassConfig.remove_relationship_config",
            "ClassConfigRelationship.update_config",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_HOME,
        next_priority="P1",
        blockers=(),
        notes=(
            "RelationshipConfig create/update/delete is production-ready for "
            "provider-delta package evolution. Association, relationship "
            "attribute, and annotation-derived behavior is tracked separately."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.relationship.derived_edges",
        capability_group=GROUP_OCG_RELATIONSHIP,
        semantic_surface=(
            "Explicit relationship association and relationship-attribute "
            "child edges"
        ),
        builder_authority_refs=(
            "aware_meta.class_.config.relationship.builder.build_class_config_relationships",
        ),
        required_ontology_functions=(
            "ClassConfigRelationship.create_association",
            "ClassConfigRelationship.create_attribute",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P1",
        blockers=(),
        notes=(
            "Association and relationship-attribute child edges now execute as "
            "relationship create operations selected by provider_operation_type. "
            "Annotation-derived load-policy behavior is tracked separately."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.relationship.annotation_derived_edges",
        capability_group=GROUP_OCG_DERIVED,
        semantic_surface="Annotation-derived relationship load-policy behavior",
        builder_authority_refs=(
            f"{_BUILDER}.apply_load_annotations_to_relationships",
            f"{_ANNOTATION_COMPILER}.handlers.apply_load_annotations_to_relationships",
        ),
        required_ontology_functions=("ObjectConfigGraphAnnotation.create",),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(),
        notes=(
            "Load-policy annotation effects now emit explicit relationship "
            "annotation-effect update operations and route to "
            "ClassConfigRelationship.update_config. Generic annotation object "
            "creation/compile semantics remain tracked by ocg.annotation_semantics."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.annotation_semantics",
        capability_group=GROUP_OCG_DERIVED,
        semantic_surface="Load/override/index/storage/discriminate annotations",
        builder_authority_refs=(
            f"{_ANNOTATION_COMPILER}.compiler.compile_object_config_graph_annotations",
            f"{_ANNOTATION_COMPILER}.handlers.apply_load_annotations_to_relationships",
            f"{_ANNOTATION_COMPILER}.handlers.apply_fk_override_annotations_to_relationships",
            "aware_meta.graph.config.annotation.compile_contract",
        ),
        required_ontology_functions=("ObjectConfigGraphAnnotation.create",),
        typed_operation_status=STATUS_PARTIAL,
        ontology_function_status=STATUS_PARTIAL,
        handler_status=STATUS_PARTIAL,
        functioncall_execution_status=STATUS_PARTIAL,
        oig_commit_status=STATUS_PARTIAL,
        package_index_status=STATUS_PARTIAL,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_PARTIAL,
        builder_retirement_status=RETIRE_BLOCKED,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(
            "annotation_override_effect_typed_operations_missing",
            "annotation_reference_effect_typed_operations_missing",
            "annotation_storage_effect_typed_operations_missing",
            "annotation_identity_effect_typed_operations_missing",
        ),
        notes=(
            f"Contract {META_OCG_ANNOTATION_COMPILE_CONTRACT_VERSION} splits "
            "deterministic annotation wrapper compile, load-policy relationship "
            "effects, overlay recompute, validation-only effects, and still-blocked "
            "annotation effect mutations."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.namespace_layout",
        capability_group=GROUP_OCG_DERIVED,
        semantic_surface="Namespace-derived node layout and overlays",
        builder_authority_refs=(
            f"{_BUILDER}.build_node_namespace_by_node_id",
            f"{_BUILDER}.build_object_config_graph_overlays_from_annotations",
            "aware_meta.graph.config.namespace.layout_contract",
        ),
        required_ontology_functions=(),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_NOT_APPLICABLE,
        handler_status=STATUS_NOT_APPLICABLE,
        functioncall_execution_status=STATUS_NOT_APPLICABLE,
        oig_commit_status=STATUS_NOT_APPLICABLE,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_NOT_APPLICABLE,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_READY,
        proof_status=PROOF_MODULE,
        next_priority="P1",
        blockers=(),
        notes=(
            "Namespace layout is not persisted semantic state. It is "
            f"{NAMESPACE_LAYOUT_DERIVATION_POLICY}; overlays use "
            f"{NAMESPACE_LAYOUT_OVERLAY_RECOMPUTE_POLICY}."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="opg.projection_declaration",
        capability_group=GROUP_OPG_DECLARATION,
        semantic_surface="ObjectProjectionGraphDeclaration and projection bindings",
        builder_authority_refs=(
            f"{_PROJECTION_COMPILER}.compile_object_config_graph_package_projections",
        ),
        required_ontology_functions=(
            "ObjectConfigGraph.create_object_projection_graph_declaration",
            "ObjectProjectionGraphDeclaration.create_binding",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_READY,
        source_generated_delta_status=STATUS_READY,
        builder_retirement_status=RETIRE_READY,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(),
        notes=(
            "Projection declaration and binding creates have OPG-owned typed "
            "operations, ontology functions, authored handlers, and FunctionCall "
            "planning with OIG commit and runtime package-index proof. Feature-owned "
            "generated-materialization evidence records that no generated language "
            "artifact patch is required for graph-runtime projection declarations."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="opg.root_node_genesis",
        capability_group=GROUP_OPG_MATERIALIZATION,
        semantic_surface="ObjectProjectionGraph root and root-node genesis",
        builder_authority_refs=(
            f"{_PACKAGE_MATERIALIZATION}.materialize_object_config_graph_package_identity_plane",
            "aware_meta.graph.projection.deltas.typed_operations",
        ),
        required_ontology_functions=(
            "ObjectProjectionGraph.build_via_object_config_graph",
            "ObjectProjectionGraph.create_node",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_READY,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_PARTIAL,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(),
        notes=(
            "OPG root and root-node creation now execute through projection-lane "
            "FunctionCalls and hydrate committed OPG truth. Runtime member "
            "materialization is tracked separately under opg.runtime_materialization."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="opg.runtime_materialization",
        capability_group=GROUP_OPG_MATERIALIZATION,
        semantic_surface="Concrete ObjectProjectionGraph edge, constructor, relationship, OIG",
        builder_authority_refs=(
            f"{_PACKAGE_MATERIALIZATION}.materialize_object_config_graph_package_identity_plane",
            f"{_RUNTIME_DERIVATION}.derive_runtime_context",
        ),
        required_ontology_functions=(
            "ObjectProjectionGraph.create_edge",
            "ObjectProjectionGraph.create_constructor",
            "ObjectProjectionGraph.create_relationship",
            "ObjectProjectionGraph.create_object_instance_graph",
        ),
        typed_operation_status=STATUS_READY,
        ontology_function_status=STATUS_READY,
        handler_status=STATUS_READY,
        functioncall_execution_status=STATUS_READY,
        oig_commit_status=STATUS_READY,
        package_index_status=STATUS_READY,
        opg_materialization_status=STATUS_READY,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_READY,
        proof_status=PROOF_MODULE,
        next_priority="P0",
        blockers=(),
        notes=(
            "OPG edge, constructor, portal relationship, and ObjectInstanceGraph "
            "derivation now have typed-operation and FunctionCall execution "
            "coverage through ObjectProjectionGraph-owned provider deltas."
        ),
    ),
    MetaOcgOpgReadinessMatrixEntry(
        capability_key="ocg.binding_mirror",
        capability_group=GROUP_OCG_DERIVED,
        semantic_surface="Bindings and mirrors",
        builder_authority_refs=(
            f"{_BUILDER}._compile_object_config_graph_bindings",
            f"{_BUILDER}.build_object_config_graph_mirrors",
            "aware_meta.graph.config.binding_mirror_contract",
        ),
        required_ontology_functions=(
            "ObjectConfigGraph.create_object_config_graph_binding",
            "ObjectConfigGraphBinding.create_class",
            "ObjectProjectionGraphNode.create_key",
            "ObjectProjectionGraphNodeKey.build_via_object_projection_graph_node",
        ),
        typed_operation_status=STATUS_PARTIAL,
        ontology_function_status=STATUS_PARTIAL,
        handler_status=STATUS_PARTIAL,
        functioncall_execution_status=STATUS_PARTIAL,
        oig_commit_status=STATUS_PARTIAL,
        package_index_status=STATUS_PARTIAL,
        opg_materialization_status=STATUS_PARTIAL,
        source_generated_delta_status=STATUS_NOT_APPLICABLE,
        builder_retirement_status=RETIRE_BLOCKED,
        proof_status=PROOF_MODULE,
        next_priority="P1",
        blockers=("mirror_rewrite_typed_operations_missing",),
        notes=(
            f"Contract {META_OCG_BINDING_MIRROR_CONTRACT_VERSION} splits "
            f"{BINDING_SEMANTIC_POLICY} from {MIRROR_SEMANTIC_POLICY}. "
            "ObjectConfigGraphBinding graph state has handlers and module proof "
            "coverage; mirror rewrite directives still need typed operations."
        ),
    ),
)


__all__ = [
    "GROUP_OCG_DERIVED",
    "GROUP_OCG_IDENTITY",
    "GROUP_OCG_MEMBER",
    "GROUP_OCG_NODE",
    "GROUP_OCG_RELATIONSHIP",
    "GROUP_OPG_DECLARATION",
    "GROUP_OPG_MATERIALIZATION",
    "META_OCG_OPG_READINESS_MATRIX_CONTRACT_VERSION",
    "PROOF_HOME",
    "PROOF_MISSING",
    "PROOF_MODULE",
    "RETIRE_BLOCKED",
    "RETIRE_PARTIAL",
    "RETIRE_READY",
    "STATUS_BLOCKED",
    "STATUS_BUILDER_ONLY",
    "STATUS_NOT_APPLICABLE",
    "STATUS_PARTIAL",
    "STATUS_PLANNED",
    "STATUS_READY",
    "MetaOcgOpgReadinessMatrixEntry",
    "builder_retirement_blocked_entries",
    "builder_retirement_ready_entries",
    "entries_for_capability_group",
    "meta_ocg_opg_readiness_matrix",
    "minimal_ocg_opg_blocker_entries",
    "ocg_opg_readiness_payload",
    "provider_delta_production_ready_entries",
]
