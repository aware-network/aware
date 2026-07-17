from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types import JsonArray
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package import (
    ExperiencePackage,
)
from aware_experience_ontology.environment.experience_package_attention_package import (
    ExperiencePackageAttentionPackage,
)
from aware_experience_ontology.environment.experience_package_dependency import (
    ExperiencePackageDependency,
)
from aware_experience_ontology.environment.experience_package_language_package import (
    ExperiencePackageLanguagePackage,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_branch import (
    ProjectionExperienceBranch,
)
from aware_experience_ontology.projection.projection_experience_graph import (
    ProjectionExperienceGraph,
)
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
from aware_experience_ontology.projection.projection_experience_graph_identity_edge import (
    ProjectionExperienceGraphIdentityEdge,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
    ProjectionExperienceLayoutSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
    ProjectionExperienceNodeIdentityEdge,
)
from aware_experience_ontology.projection.projection_experience_oigi import (
    ProjectionExperienceOIGI,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_state_provider import (
    ProjectionExperienceViewStateProvider,
)
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
    ProgramImplInvokeTargetKind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_expect import (
    ProgramImplInstructionExpect,
)
from aware_experience_ontology.program.impl.program_impl_instruction_input import (
    ProgramImplInstructionInput,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
    ProgramImplInstructionIntentActivationFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
    ProgramImplInstructionIntentOutcomeFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
    ProgramImplInstructionIntentReceiptFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience_ontology.program.impl.program_impl_instruction_let import (
    ProgramImplInstructionLet,
)
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_experience_ontology.program.program_config_actor_config import (
    ProgramConfigActorConfig,
)
from aware_experience_ontology.program.program_config_attribute_config import (
    ProgramConfigAttributeConfig,
)
from aware_experience_ontology.program.program_config_input_config import (
    ProgramConfigInputConfig,
)
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.program.program_enums import (
    ProgramAttributeType,
    ProgramBranchBindingMode,
)
from aware_identity_ontology.stable_ids import stable_actor_config_id
from aware_attention_ontology.stable_ids import (
    stable_layout_config_section_config_id,
)
from aware_experience_ontology.stable_ids import (
    stable_environment_experience_id,
    stable_experience_invocation_action_config_id,
    stable_experience_package_dependency_id,
    stable_experience_package_attention_package_id,
    stable_experience_package_id,
    stable_experience_package_language_package_id,
    stable_program_config_actor_config_id,
    stable_program_config_attribute_config_id,
    stable_program_config_id,
    stable_program_config_input_config_id,
    stable_program_config_port_id,
    stable_program_config_port_projection_experience_node_id,
    stable_program_config_port_projection_experience_node_identity_id,
    stable_program_impl_id,
    stable_program_impl_instruction_bind_id,
    stable_program_impl_instruction_expect_id,
    stable_program_impl_instruction_id,
    stable_program_impl_instruction_input_id,
    stable_program_impl_instruction_intent_id,
    stable_program_impl_instruction_intent_activation_field_binding_id,
    stable_program_impl_instruction_intent_outcome_field_binding_id,
    stable_program_impl_instruction_intent_receipt_field_binding_id,
    stable_program_impl_instruction_invoke_attribute_config_id,
    stable_program_impl_instruction_invoke_id,
    stable_program_impl_instruction_let_id,
    stable_projection_experience_branch_id,
    stable_projection_experience_graph_id,
    stable_projection_experience_graph_identity_edge_id,
    stable_projection_experience_graph_identity_id,
    stable_projection_experience_layout_graph_binding_id,
    stable_projection_experience_layout_section_graph_binding_id,
    stable_projection_experience_id,
    stable_projection_experience_node_class_identity_id,
    stable_projection_experience_node_id,
    stable_projection_experience_node_identity_edge_id,
    stable_projection_experience_node_identity_id,
    stable_projection_experience_oigi_id,
    stable_projection_experience_section_graph_binding_id,
    stable_projection_experience_view_invocation_action_config_id,
    stable_projection_experience_view_id,
    stable_projection_experience_view_state_provider_id,
)
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_meta.attribute.config.type_descriptor_builder import (
    ensure_stable_descriptor_tree_ids,
)
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.graph.instance.root import resolve_root_source_object_id
from aware_meta_ontology.stable_ids import (
    stable_attribute_config_id,
    stable_class_instance_id,
    stable_class_instance_identity_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.primitive.config.builder import build_primitive_config
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.portal_lane_resolution import (
    attach_portal_target_branch_relationship_for_object,
    ensure_portal_target_lane_ref_for_object,
    resolve_portal_target_branch_ref_for_object,
)
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_types import JsonObject

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class ExperienceEnvironmentSnapshotCommitResult:
    environment_experience: EnvironmentExperience
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ExperiencePackageManifestSnapshotCommitResult:
    experience_package: ExperiencePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ExperiencePackageDependencySnapshot:
    target_experience_package_id: UUID
    target_package_name: str
    target_experience_package_object_instance_graph_commit_id: UUID | None = None
    target_version_number: int | None = None
    expected_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ExperiencePackageAttentionPackageSnapshotRef:
    attention_package_id: UUID
    package_name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ExperiencePackageLanguagePackageSnapshotRef:
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = None
    role: str = "view_model_package"
    output_key: str = "experience.language_contract.generated_code_packages"
    include_paths: JsonArray = field(default_factory=JsonArray)
    exclude_paths: JsonArray = field(default_factory=JsonArray)


@dataclass(frozen=True, slots=True)
class ExperienceProjectionBranchSnapshot:
    name: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionViewSnapshot:
    api_view_id: UUID
    name: str
    state_provider_ref: str | None = None
    provider_kind: str = "runtime_callable"
    purity: str = "pure_read"
    invocation_actions: Sequence[
        "ExperienceProjectionViewInvocationActionConfigSnapshot"
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceProjectionViewInvocationActionConfigSnapshot:
    api_view_capability_endpoint_id: UUID
    action_key: str
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None
    api_capability_endpoint_id: UUID | None = None
    sdk_operation_id: UUID | None = None
    label: str | None = None
    receipt_policy: str | None = None
    confirmation_policy: str | None = None
    optimistic_policy: str | None = None


ExperienceProjectionViewInvocationActionSnapshot = (
    ExperienceProjectionViewInvocationActionConfigSnapshot
)


@dataclass(frozen=True, slots=True)
class ExperienceProjectionNodeSnapshot:
    object_projection_graph_node_id: UUID
    key: str
    identity_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperienceProjectionNodeClassIdentitySnapshot:
    projection_experience_node_identity_id: UUID
    class_config_id: UUID
    source_object_id: UUID
    key: str


@dataclass(frozen=True, slots=True)
class ExperienceProjectionOIGISnapshot:
    object_instance_graph_id: UUID
    object_instance_graph_identity_id: UUID
    key: str | None = None
    node_class_identities: Sequence[ExperienceProjectionNodeClassIdentitySnapshot] = ()


@dataclass(frozen=True, slots=True)
class ExperienceSectionGraphBindingSnapshot:
    layout_config_section_config_id: UUID
    projection_experience_view_id: UUID
    projection_experience_graph_identity_id: UUID
    binding_key: str
    section_key: str


@dataclass(frozen=True, slots=True)
class ExperienceLayoutGraphBindingSnapshot:
    layout_config_id: UUID
    binding_key: str
    section_graph_binding_keys: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class ExperienceProjectionSnapshotCommitResult:
    projection_experience: ProjectionExperience
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int
    projection_oigi_commit_ids: tuple[UUID, ...] = ()
    projection_oigi_object_instance_graph_commit_ids: tuple[UUID, ...] = ()
    section_graph_binding_branch_ids: tuple[UUID, ...] = ()
    section_graph_binding_commit_ids: tuple[UUID, ...] = ()
    layout_graph_binding_branch_ids: tuple[UUID, ...] = ()
    layout_graph_binding_commit_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceGraphIdentitySnapshot:
    projection_experience_node_identity_id: UUID
    key: str
    is_root: bool = False


@dataclass(frozen=True, slots=True)
class ExperienceNodeIdentityEdgeSnapshot:
    parent_projection_experience_node_identity_id: UUID
    child_projection_experience_node_identity_id: UUID
    key: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceGraphIdentityEdgeSnapshot:
    parent_projection_experience_graph_identity_id: UUID
    child_projection_experience_graph_identity_id: UUID
    projection_experience_node_identity_edge_id: UUID
    key: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceGraphSnapshotCommitResult:
    projection_experience_graph: ProjectionExperienceGraph
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ExperienceActorSnapshotCommitResult:
    actor_config: ActorConfig
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ExperienceProgramInputSnapshot:
    name: str
    source: str
    required: bool
    position: int
    attribute_type_ref: str = "any"
    default_expr: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramActorConfigSnapshot:
    alias: str
    actor_config_id: UUID
    actor_key: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramPortNodeIdentitySnapshot:
    projection_experience_node_identity_id: UUID
    key: str


@dataclass(frozen=True, slots=True)
class ExperienceProgramPortNodeSnapshot:
    projection_experience_node_id: UUID
    key: str
    identity: ExperienceProgramPortNodeIdentitySnapshot | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramPortSnapshot:
    projection_id: UUID
    key: str
    intent: str | None = None
    branch_binding_mode: ProgramBranchBindingMode = ProgramBranchBindingMode.reference
    nodes: tuple[ExperienceProgramPortNodeSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceProgramConfigSnapshotCommitResult:
    program_config: ProgramConfig
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplInvokeAttributeSnapshot:
    attribute_config_id: UUID
    value_expr: JsonObject
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplActivationFieldBindingSnapshot:
    source_input_key: str
    source_class_config_id: UUID
    source_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplOutcomeFieldBindingSnapshot:
    source_program_impl_instruction_intent_id: UUID
    source_response_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplReceiptFieldBindingSnapshot:
    source_program_impl_instruction_intent_id: UUID
    source_receipt_class_config_id: UUID
    source_receipt_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = True
    position: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplInstructionSnapshot:
    instruction_type: ProgramImplInstructionType
    sequence: int
    program_config_input_config_id: UUID | None = None
    name: str | None = None
    value_expr: JsonObject | None = None
    program_config_port_id: UUID | None = None
    view_key: str | None = None
    is_active: bool = True
    event_config_id: UUID | None = None
    required: bool = True
    action_config_id: UUID | None = None
    continuation_key: str | None = None
    api_capability_endpoint_id: UUID | None = None
    request_class_config_id: UUID | None = None
    response_class_config_id: UUID | None = None
    activation_field_bindings: tuple[
        ExperienceProgramImplActivationFieldBindingSnapshot, ...
    ] = ()
    outcome_field_bindings: tuple[
        ExperienceProgramImplOutcomeFieldBindingSnapshot, ...
    ] = ()
    receipt_field_bindings: tuple[
        ExperienceProgramImplReceiptFieldBindingSnapshot, ...
    ] = ()
    function_config_id: UUID | None = None
    program_config_actor_config_id: UUID | None = None
    program_config_port_projection_experience_node_id: UUID | None = None
    target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance
    invoke_attributes: tuple[ExperienceProgramImplInvokeAttributeSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperienceProgramImplSnapshotCommitResult:
    program_impl: ProgramImpl
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class _SnapshotCommit:
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class _SnapshotLanePreState:
    before_oig: ObjectInstanceGraph
    parent_commit_id: UUID | None


_EXPERIENCE_ENVIRONMENT_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/environment/snapshot-commit/v1",
)
_EXPERIENCE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/package/manifest-snapshot-commit/v1",
)
_EXPERIENCE_PROJECTION_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/projection/snapshot-commit/v1",
)
_EXPERIENCE_PROJECTION_OIGI_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/projection/oigi-snapshot-commit/v1",
)
_EXPERIENCE_SECTION_GRAPH_BINDING_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/projection/section-graph-binding-snapshot-commit/v1",
)
_EXPERIENCE_LAYOUT_GRAPH_BINDING_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/projection/layout-graph-binding-snapshot-commit/v1",
)
_EXPERIENCE_GRAPH_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/graph/snapshot-commit/v1",
)
_EXPERIENCE_ACTOR_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/actor/snapshot-commit/v1",
)
_EXPERIENCE_PROGRAM_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/program-config/snapshot-commit/v1",
)
_EXPERIENCE_PROGRAM_IMPL_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/program-impl/snapshot-commit/v1",
)


async def commit_environment_experience_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    fqn_prefix: str,
    title: str | None,
    description: str | None,
) -> ExperienceEnvironmentSnapshotCommitResult:
    environment_experience, objects_by_id = _build_environment_experience_objects(
        fqn_prefix=fqn_prefix,
        title=title,
        description=description,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=environment_experience.id,
        root_object=environment_experience,
        objects_by_id=objects_by_id,
        operation_label="EnvironmentExperience.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_ENVIRONMENT_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ExperienceEnvironmentSnapshotCommitResult(
        environment_experience=environment_experience,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_experience_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    environment_experience_id: UUID,
    source_code_package_id: UUID | None,
    dependencies: Sequence[ExperiencePackageDependencySnapshot] = (),
    attention_package_refs: Sequence[ExperiencePackageAttentionPackageSnapshotRef] = (),
    language_package_refs: Sequence[ExperiencePackageLanguagePackageSnapshotRef] = (),
) -> ExperiencePackageManifestSnapshotCommitResult:
    experience_package, objects_by_id = _build_experience_package_objects(
        name=name,
        environment_experience_id=environment_experience_id,
        source_code_package_id=source_code_package_id,
        dependencies=dependencies,
        attention_package_refs=attention_package_refs,
        language_package_refs=language_package_refs,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=experience_package.id,
        root_object=experience_package,
        objects_by_id=objects_by_id,
        operation_label="ExperiencePackage.materialize_manifest_snapshot",
        commit_id_namespace=_EXPERIENCE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
        reconcile_class_fqn_suffixes=(
            ".ExperiencePackageAttentionPackage",
            ".ExperiencePackageDependency",
            ".ExperiencePackageLanguagePackage",
        ),
    )
    return ExperiencePackageManifestSnapshotCommitResult(
        experience_package=experience_package,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_projection_experience_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    projection_oigi_hash: str | None = None,
    projection_graph_hash: str | None = None,
    section_graph_binding_hash: str | None = None,
    layout_graph_binding_hash: str | None = None,
    attention_layout_config_hash: str | None = None,
    object_projection_graph_identity_id: UUID,
    name: str,
    branches: Sequence[ExperienceProjectionBranchSnapshot] = (),
    views: Sequence[ExperienceProjectionViewSnapshot] = (),
    nodes: Sequence[ExperienceProjectionNodeSnapshot] = (),
    oigis: Sequence[ExperienceProjectionOIGISnapshot] = (),
    section_graph_bindings: Sequence[ExperienceSectionGraphBindingSnapshot] = (),
    layout_graph_bindings: Sequence[ExperienceLayoutGraphBindingSnapshot] = (),
) -> ExperienceProjectionSnapshotCommitResult:
    projection_experience, objects_by_id = _build_projection_experience_objects(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        name=name,
        branches=branches,
        views=views,
        nodes=nodes,
        oigis=(),
        section_graph_bindings=section_graph_bindings,
        layout_graph_bindings=layout_graph_bindings,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=projection_experience.id,
        root_object=projection_experience,
        objects_by_id=objects_by_id,
        operation_label="ProjectionExperience.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_PROJECTION_SNAPSHOT_COMMIT_NAMESPACE,
    )
    projection_oigi_commits: tuple[_SnapshotCommit, ...] = ()
    if oigis:
        if projection_oigi_hash is None:
            raise RuntimeError(
                "ProjectionExperience snapshot has OIGI topology but no "
                "ProjectionExperienceOIGI projection hash."
            )
        projection_oigi_commits = await _commit_projection_oigi_snapshots(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_oigi_hash,
            projection_experience=projection_experience,
            oigis=oigis,
        )
    section_binding_commits: tuple[tuple[UUID, _SnapshotCommit], ...] = ()
    layout_binding_commits: tuple[tuple[UUID, _SnapshotCommit], ...] = ()
    if section_graph_bindings or layout_graph_bindings:
        if section_graph_binding_hash is None:
            raise RuntimeError(
                "ProjectionExperience binding snapshot requires the "
                "ProjectionExperienceSectionGraphBinding projection hash."
            )
        if layout_graph_bindings and layout_graph_binding_hash is None:
            raise RuntimeError(
                "ProjectionExperience layout binding snapshot requires the "
                "ProjectionExperienceLayoutGraphBinding projection hash."
            )
        if projection_graph_hash is None:
            raise RuntimeError(
                "ProjectionExperience binding snapshot requires the "
                "ProjectionExperienceGraph projection hash."
            )
        if attention_layout_config_hash is None:
            raise RuntimeError(
                "ProjectionExperience binding snapshot requires the Attention "
                "LayoutConfig projection hash."
            )
        section_binding_commits, layout_binding_commits = (
            await _commit_projection_binding_snapshots(
                index=index,
                actor_id=actor_id,
                parent_branch_id=branch_id,
                parent_projection_hash=projection_hash,
                projection_graph_hash=projection_graph_hash,
                section_graph_binding_hash=section_graph_binding_hash,
                layout_graph_binding_hash=layout_graph_binding_hash,
                attention_layout_config_hash=attention_layout_config_hash,
                projection_experience=projection_experience,
            )
        )
    return ExperienceProjectionSnapshotCommitResult(
        projection_experience=projection_experience,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
        projection_oigi_commit_ids=tuple(
            item.commit_id for item in projection_oigi_commits
        ),
        projection_oigi_object_instance_graph_commit_ids=tuple(
            item.object_instance_graph_commit_id for item in projection_oigi_commits
        ),
        section_graph_binding_branch_ids=tuple(
            branch_id for branch_id, _commit in section_binding_commits
        ),
        section_graph_binding_commit_ids=tuple(
            item.commit_id for _branch_id, item in section_binding_commits
        ),
        layout_graph_binding_branch_ids=tuple(
            branch_id for branch_id, _commit in layout_binding_commits
        ),
        layout_graph_binding_commit_ids=tuple(
            item.commit_id for _branch_id, item in layout_binding_commits
        ),
    )


async def commit_projection_experience_graph_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    projection_experience_id: UUID,
    name: str,
    identities: Sequence[ExperienceGraphIdentitySnapshot],
    node_identity_edges: Sequence[ExperienceNodeIdentityEdgeSnapshot],
    graph_identity_edges: Sequence[ExperienceGraphIdentityEdgeSnapshot],
) -> ExperienceGraphSnapshotCommitResult:
    projection_experience_graph, objects_by_id = (
        _build_projection_experience_graph_objects(
            projection_experience_id=projection_experience_id,
            name=name,
            identities=identities,
            node_identity_edges=node_identity_edges,
            graph_identity_edges=graph_identity_edges,
        )
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=projection_experience_graph.id,
        root_object=projection_experience_graph,
        objects_by_id=objects_by_id,
        operation_label="ProjectionExperienceGraph.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_GRAPH_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ExperienceGraphSnapshotCommitResult(
        projection_experience_graph=projection_experience_graph,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_actor_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    key: str,
    title: str | None = None,
    description: str | None = None,
    type: ActorType | None = None,
) -> ExperienceActorSnapshotCommitResult:
    actor_config, objects_by_id = _build_actor_config_objects(
        key=key,
        title=title,
        description=description,
        type=type,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=actor_config.id,
        root_object=actor_config,
        objects_by_id=objects_by_id,
        operation_label="ActorConfig.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_ACTOR_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ExperienceActorSnapshotCommitResult(
        actor_config=actor_config,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_program_config_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
    intent: str | None = None,
    is_default: bool = False,
    inputs: Sequence[ExperienceProgramInputSnapshot] = (),
    actor_configs: Sequence[ExperienceProgramActorConfigSnapshot] = (),
    ports: Sequence[ExperienceProgramPortSnapshot] = (),
) -> ExperienceProgramConfigSnapshotCommitResult:
    program_config, objects_by_id = _build_program_config_objects(
        key=key,
        title=title,
        description=description,
        narrative=narrative,
        intent=intent,
        is_default=is_default,
        inputs=inputs,
        actor_configs=actor_configs,
        ports=ports,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=program_config.id,
        root_object=program_config,
        objects_by_id=objects_by_id,
        operation_label="ProgramConfig.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_PROGRAM_CONFIG_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ExperienceProgramConfigSnapshotCommitResult(
        program_config=program_config,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_program_impl_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    program_config_id: UUID,
    key: str,
    instructions: Sequence[ExperienceProgramImplInstructionSnapshot] = (),
) -> ExperienceProgramImplSnapshotCommitResult:
    program_impl, objects_by_id = _build_program_impl_objects(
        program_config_id=program_config_id,
        key=key,
        instructions=instructions,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=program_impl.id,
        root_object=program_impl,
        objects_by_id=objects_by_id,
        operation_label="ProgramImpl.materialize_snapshot",
        commit_id_namespace=_EXPERIENCE_PROGRAM_IMPL_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ExperienceProgramImplSnapshotCommitResult(
        program_impl=program_impl,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


def _build_environment_experience_objects(
    *,
    fqn_prefix: str,
    title: str | None,
    description: str | None,
) -> tuple[EnvironmentExperience, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "EnvironmentExperience snapshot requires non-empty fqn_prefix"
        )
    environment_experience = _remember(
        objects_by_id,
        EnvironmentExperience(
            id=stable_environment_experience_id(
                fqn_prefix=normalized_fqn_prefix,
            ),
            fqn_prefix=normalized_fqn_prefix,
            title=title,
            description=description,
        ),
    )
    return environment_experience, objects_by_id


def _build_experience_package_objects(
    *,
    name: str,
    environment_experience_id: UUID,
    source_code_package_id: UUID | None,
    dependencies: Sequence[ExperiencePackageDependencySnapshot],
    attention_package_refs: Sequence[ExperiencePackageAttentionPackageSnapshotRef],
    language_package_refs: Sequence[ExperiencePackageLanguagePackageSnapshotRef],
) -> tuple[ExperiencePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ExperiencePackage snapshot requires non-empty name")
    experience_package = _remember(
        objects_by_id,
        ExperiencePackage(
            id=stable_experience_package_id(name=normalized_name),
            name=normalized_name,
            environment_experience_id=environment_experience_id,
            source_code_package_id=source_code_package_id,
        ),
    )
    _append_experience_package_dependencies(
        objects_by_id=objects_by_id,
        experience_package=experience_package,
        dependencies=dependencies,
    )
    _append_experience_package_attention_packages(
        objects_by_id=objects_by_id,
        experience_package=experience_package,
        attention_package_refs=attention_package_refs,
    )
    _append_experience_package_language_packages(
        objects_by_id=objects_by_id,
        experience_package=experience_package,
        language_package_refs=language_package_refs,
    )
    return experience_package, objects_by_id


def _append_experience_package_attention_packages(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    experience_package: ExperiencePackage,
    attention_package_refs: Sequence[ExperiencePackageAttentionPackageSnapshotRef],
) -> None:
    for attention_ref in sorted(
        attention_package_refs,
        key=lambda item: (item.package_name.casefold(), str(item.attention_package_id)),
    ):
        _required_token(
            attention_ref.package_name,
            label="ExperiencePackageAttentionPackage.package_name",
        )
        edge = _remember(
            objects_by_id,
            ExperiencePackageAttentionPackage(
                id=stable_experience_package_attention_package_id(
                    experience_package_id=experience_package.id,
                    attention_package_id=attention_ref.attention_package_id,
                ),
                experience_package_id=experience_package.id,
                attention_package_id=attention_ref.attention_package_id,
                description=(attention_ref.description or "").strip() or None,
            ),
        )
        experience_package.attention_packages.append(edge)


def _append_experience_package_dependencies(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    experience_package: ExperiencePackage,
    dependencies: Sequence[ExperiencePackageDependencySnapshot],
) -> None:
    for dependency in dependencies:
        target_package_name = _required_token(
            dependency.target_package_name,
            label="ExperiencePackageDependency.target_package_name",
        )
        expected_hash_sha256 = (
            dependency.expected_hash_sha256 or ""
        ).strip().lower() or None
        if expected_hash_sha256 is not None and (
            len(expected_hash_sha256) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash_sha256)
        ):
            raise RuntimeError(
                "ExperiencePackageDependency expected_hash_sha256 must be 64 hex chars"
            )
        if (
            dependency.target_version_number is not None
            and dependency.target_version_number < 1
        ):
            raise RuntimeError(
                "ExperiencePackageDependency target_version_number must be >= 1"
            )
        edge = _remember(
            objects_by_id,
            ExperiencePackageDependency(
                id=stable_experience_package_dependency_id(
                    experience_package_id=experience_package.id,
                    target_experience_package_id=(
                        dependency.target_experience_package_id
                    ),
                ),
                experience_package_id=experience_package.id,
                target_experience_package_id=(dependency.target_experience_package_id),
                target_experience_package_object_instance_graph_commit_id=(
                    dependency.target_experience_package_object_instance_graph_commit_id
                ),
                target_package_name=target_package_name,
                target_version_number=dependency.target_version_number,
                expected_hash_sha256=expected_hash_sha256,
                description=(dependency.description or "").strip() or None,
            ),
        )
        experience_package.experience_package_dependencies.append(edge)


def _append_experience_package_language_packages(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    experience_package: ExperiencePackage,
    language_package_refs: Sequence[ExperiencePackageLanguagePackageSnapshotRef],
) -> None:
    for language_ref in sorted(
        language_package_refs,
        key=lambda item: (
            item.language.value,
            item.output_key,
            item.package_name,
            str(item.code_package_id),
        ),
    ):
        package_name = _required_token(
            language_ref.package_name,
            label="ExperiencePackageLanguagePackage.package_name",
        )
        import_root = _required_token(
            language_ref.import_root,
            label="ExperiencePackageLanguagePackage.import_root",
        )
        manifest_relative_path = _required_token(
            language_ref.manifest_relative_path,
            label="ExperiencePackageLanguagePackage.manifest_relative_path",
        )
        language_package = _remember(
            objects_by_id,
            ExperiencePackageLanguagePackage(
                id=stable_experience_package_language_package_id(
                    experience_package_id=experience_package.id,
                    code_package_id=language_ref.code_package_id,
                ),
                experience_package_id=experience_package.id,
                code_package_id=language_ref.code_package_id,
                package_name=package_name,
                language=language_ref.language,
                import_root=import_root,
                manifest_relative_path=manifest_relative_path,
                package_root=(language_ref.package_root or "").strip() or ".",
                sources_root=(language_ref.sources_root or "").strip() or None,
                role=(language_ref.role or "").strip() or "view_model_package",
                output_key=(
                    (language_ref.output_key or "").strip()
                    or "experience.language_contract.generated_code_packages"
                ),
                include_paths=JsonArray(language_ref.include_paths or []),
                exclude_paths=JsonArray(language_ref.exclude_paths or []),
            ),
        )
        experience_package.language_packages.append(language_package)


def _build_projection_experience_objects(
    *,
    object_projection_graph_identity_id: UUID,
    name: str,
    branches: Sequence[ExperienceProjectionBranchSnapshot],
    views: Sequence[ExperienceProjectionViewSnapshot],
    nodes: Sequence[ExperienceProjectionNodeSnapshot],
    oigis: Sequence[ExperienceProjectionOIGISnapshot],
    section_graph_bindings: Sequence[ExperienceSectionGraphBindingSnapshot],
    layout_graph_bindings: Sequence[ExperienceLayoutGraphBindingSnapshot],
) -> tuple[ProjectionExperience, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperience snapshot requires non-empty name")
    projection_experience = _remember(
        objects_by_id,
        ProjectionExperience(
            id=stable_projection_experience_id(
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                name=normalized_name,
            ),
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            name=normalized_name,
        ),
    )
    _append_projection_branches(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        branches=branches,
    )
    _append_projection_views(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        views=views,
    )
    _append_projection_nodes(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        nodes=nodes,
    )
    _append_projection_oigis(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        oigis=oigis,
    )
    _append_section_graph_bindings(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        bindings=section_graph_bindings,
    )
    _append_layout_graph_bindings(
        objects_by_id=objects_by_id,
        projection_experience=projection_experience,
        bindings=layout_graph_bindings,
    )
    return projection_experience, objects_by_id


async def _commit_projection_oigi_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    projection_experience: ProjectionExperience,
    oigis: Sequence[ExperienceProjectionOIGISnapshot],
) -> tuple[_SnapshotCommit, ...]:
    node_identities_by_id = {
        node_identity.id: node_identity
        for node in projection_experience.projection_experience_nodes
        for node_identity in node.projection_experience_node_identities
        if node_identity.id is not None
    }
    commits: list[_SnapshotCommit] = []
    for oigi in sorted(
        oigis,
        key=lambda item: (
            item.key or "",
            str(item.object_instance_graph_identity_id),
            str(item.object_instance_graph_id),
        ),
    ):
        projection_oigi, objects_by_id = _build_projection_oigi_objects(
            projection_experience_id=projection_experience.id,
            node_identities_by_id=node_identities_by_id,
            oigi=oigi,
        )
        commits.append(
            await _commit_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                root_object_id=projection_oigi.id,
                root_object=projection_oigi,
                objects_by_id=objects_by_id,
                operation_label="ProjectionExperienceOIGI.materialize_snapshot",
                commit_id_namespace=(
                    _EXPERIENCE_PROJECTION_OIGI_SNAPSHOT_COMMIT_NAMESPACE
                ),
            )
        )
    return tuple(commits)


async def _commit_projection_binding_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    parent_branch_id: UUID,
    parent_projection_hash: str,
    projection_graph_hash: str,
    section_graph_binding_hash: str,
    layout_graph_binding_hash: str | None,
    attention_layout_config_hash: str,
    projection_experience: ProjectionExperience,
) -> tuple[
    tuple[tuple[UUID, _SnapshotCommit], ...],
    tuple[tuple[UUID, _SnapshotCommit], ...],
]:
    author_id = resolve_meta_author_id(actor_id)
    await _ensure_binding_portal_source_identity(
        index=index,
        author_id=author_id,
        branch_id=parent_branch_id,
        projection_hash=parent_projection_hash,
        label="projection_experience_binding_portal_source",
    )
    projection_view_class_id = _required_class_config_id(
        index=index,
        class_fqn="aware_experience.projection.ProjectionExperienceView",
    )
    projection_graph_identity_class_id = _required_class_config_id(
        index=index,
        class_fqn="aware_experience.projection.ProjectionExperienceGraphIdentity",
    )
    section_binding_class_id = _required_class_config_id(
        index=index,
        class_fqn=(
            "aware_experience.projection." "ProjectionExperienceSectionGraphBinding"
        ),
    )
    layout_config_class_id = _required_class_config_id(
        index=index,
        class_fqn="aware_attention.layout.LayoutConfig",
    )
    layout_config_section_class_id = _required_class_config_id(
        index=index,
        class_fqn="aware_attention.layout.LayoutConfigSectionConfig",
    )
    layout_config_branch_ids_by_section_binding_id = (
        _layout_config_branch_ids_by_section_binding_id(
            projection_experience=projection_experience,
        )
    )

    section_commits: list[tuple[UUID, _SnapshotCommit]] = []
    section_binding_branch_ids_by_id: dict[UUID, UUID] = {}
    for section_binding in sorted(
        projection_experience.projection_experience_section_graph_bindings,
        key=lambda item: str(item.id),
    ):
        layout_config_branch_id = layout_config_branch_ids_by_section_binding_id.get(
            section_binding.id
        )
        if layout_config_branch_id is None:
            raise RuntimeError(
                "ProjectionExperience section graph binding requires one owning "
                "LayoutConfig branch: "
                f"section_graph_binding_id={section_binding.id}"
            )
        branch_ref = await resolve_portal_target_branch_ref_for_object(
            index=index,
            source_domain_branch_id=parent_branch_id,
            source_projection_hash=parent_projection_hash,
            target_projection_hash=section_graph_binding_hash,
            target_object_id=section_binding.id,
        )
        section_commit = await _commit_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_ref.target_branch_id,
            projection_hash=section_graph_binding_hash,
            root_object_id=section_binding.id,
            root_object=section_binding,
            objects_by_id={section_binding.id: section_binding},
            operation_label=(
                "ProjectionExperienceSectionGraphBinding.materialize_snapshot"
            ),
            commit_id_namespace=(
                _EXPERIENCE_SECTION_GRAPH_BINDING_SNAPSHOT_COMMIT_NAMESPACE
            ),
        )
        await _ensure_binding_portal_source_identity(
            index=index,
            author_id=author_id,
            branch_id=branch_ref.target_branch_id,
            projection_hash=section_graph_binding_hash,
            label="projection_experience_section_graph_binding_portal_source",
        )
        await attach_portal_target_branch_relationship_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=parent_branch_id,
            source_projection_hash=parent_projection_hash,
            target_projection_hash=section_graph_binding_hash,
            target_object_id=section_binding.id,
            target_domain_branch_id=branch_ref.target_branch_id,
        )
        await ensure_portal_target_lane_ref_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=branch_ref.target_branch_id,
            source_projection_hash=section_graph_binding_hash,
            target_projection_hash=parent_projection_hash,
            target_class_config_id=projection_view_class_id,
            target_object_id=section_binding.projection_experience_view_id,
            target_domain_branch_id=parent_branch_id,
        )
        await ensure_portal_target_lane_ref_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=branch_ref.target_branch_id,
            source_projection_hash=section_graph_binding_hash,
            target_projection_hash=projection_graph_hash,
            target_class_config_id=projection_graph_identity_class_id,
            target_object_id=(section_binding.projection_experience_graph_identity_id),
            target_domain_branch_id=parent_branch_id,
        )
        await ensure_portal_target_lane_ref_for_object(
            index=index,
            author_id=author_id,
            source_domain_branch_id=branch_ref.target_branch_id,
            source_projection_hash=section_graph_binding_hash,
            target_projection_hash=attention_layout_config_hash,
            target_class_config_id=layout_config_section_class_id,
            target_object_id=section_binding.layout_config_section_config_id,
            target_domain_branch_id=layout_config_branch_id,
        )
        section_binding_branch_ids_by_id[section_binding.id] = (
            branch_ref.target_branch_id
        )
        section_commits.append((branch_ref.target_branch_id, section_commit))

    layout_commits: list[tuple[UUID, _SnapshotCommit]] = []
    if projection_experience.projection_experience_layout_graph_bindings:
        if layout_graph_binding_hash is None:
            raise RuntimeError(
                "ProjectionExperience layout bindings require their projection hash."
            )
        for layout_binding in sorted(
            projection_experience.projection_experience_layout_graph_bindings,
            key=lambda item: str(item.id),
        ):
            branch_ref = await resolve_portal_target_branch_ref_for_object(
                index=index,
                source_domain_branch_id=parent_branch_id,
                source_projection_hash=parent_projection_hash,
                target_projection_hash=layout_graph_binding_hash,
                target_object_id=layout_binding.id,
            )
            layout_objects: dict[UUID, BaseORMModel] = {
                layout_binding.id: layout_binding
            }
            layout_objects.update(
                {row.id: row for row in layout_binding.layout_section_graph_bindings}
            )
            layout_commit = await _commit_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=branch_ref.target_branch_id,
                projection_hash=layout_graph_binding_hash,
                root_object_id=layout_binding.id,
                root_object=layout_binding,
                objects_by_id=layout_objects,
                operation_label=(
                    "ProjectionExperienceLayoutGraphBinding.materialize_snapshot"
                ),
                commit_id_namespace=(
                    _EXPERIENCE_LAYOUT_GRAPH_BINDING_SNAPSHOT_COMMIT_NAMESPACE
                ),
            )
            await _ensure_binding_portal_source_identity(
                index=index,
                author_id=author_id,
                branch_id=branch_ref.target_branch_id,
                projection_hash=layout_graph_binding_hash,
                label="projection_experience_layout_graph_binding_portal_source",
            )
            await attach_portal_target_branch_relationship_for_object(
                index=index,
                author_id=author_id,
                source_domain_branch_id=parent_branch_id,
                source_projection_hash=parent_projection_hash,
                target_projection_hash=layout_graph_binding_hash,
                target_object_id=layout_binding.id,
                target_domain_branch_id=branch_ref.target_branch_id,
            )
            await ensure_portal_target_lane_ref_for_object(
                index=index,
                author_id=author_id,
                source_domain_branch_id=branch_ref.target_branch_id,
                source_projection_hash=layout_graph_binding_hash,
                target_projection_hash=attention_layout_config_hash,
                target_class_config_id=layout_config_class_id,
                target_object_id=layout_binding.layout_config_id,
                target_domain_branch_id=layout_binding.layout_config_id,
            )
            for row in layout_binding.layout_section_graph_bindings:
                section_binding_branch_id = section_binding_branch_ids_by_id.get(
                    row.section_graph_binding_id
                )
                if section_binding_branch_id is None:
                    raise RuntimeError(
                        "ProjectionExperience layout graph binding requires a "
                        "committed section binding branch: "
                        f"section_graph_binding_id={row.section_graph_binding_id}"
                    )
                await ensure_portal_target_lane_ref_for_object(
                    index=index,
                    author_id=author_id,
                    source_domain_branch_id=branch_ref.target_branch_id,
                    source_projection_hash=layout_graph_binding_hash,
                    target_projection_hash=section_graph_binding_hash,
                    target_class_config_id=section_binding_class_id,
                    target_object_id=row.section_graph_binding_id,
                    target_domain_branch_id=section_binding_branch_id,
                )
            layout_commits.append((branch_ref.target_branch_id, layout_commit))

    return tuple(section_commits), tuple(layout_commits)


def _layout_config_branch_ids_by_section_binding_id(
    *,
    projection_experience: ProjectionExperience,
) -> dict[UUID, UUID]:
    branch_ids_by_section_binding_id: dict[UUID, UUID] = {}
    for (
        layout_binding
    ) in projection_experience.projection_experience_layout_graph_bindings:
        for row in layout_binding.layout_section_graph_bindings:
            section_binding_id = row.section_graph_binding_id
            existing_branch_id = branch_ids_by_section_binding_id.get(
                section_binding_id
            )
            if (
                existing_branch_id is not None
                and existing_branch_id != layout_binding.layout_config_id
            ):
                raise RuntimeError(
                    "ProjectionExperience section graph binding has conflicting "
                    "LayoutConfig branch ownership: "
                    f"section_graph_binding_id={section_binding_id} "
                    f"first_layout_config_id={existing_branch_id} "
                    f"second_layout_config_id={layout_binding.layout_config_id}"
                )
            branch_ids_by_section_binding_id[section_binding_id] = (
                layout_binding.layout_config_id
            )
    return branch_ids_by_section_binding_id


async def _ensure_binding_portal_source_identity(
    *,
    index: MetaGraphRuntimeIndex,
    author_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    label: str,
) -> None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None or opg.id is None:
        raise RuntimeError(
            "Experience binding portal source projection is missing: "
            f"projection_hash={projection_hash}"
        )
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    raw_commit_id = head.get("commit_id") if isinstance(head, Mapping) else None
    raw_object_instance_graph_id = (
        head.get("object_instance_graph_id") if isinstance(head, Mapping) else None
    )
    if raw_commit_id is None or raw_object_instance_graph_id is None:
        raise RuntimeError(
            "Experience binding portal source requires committed lane HEAD identity: "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )
    object_instance_graph_id = (
        raw_object_instance_graph_id
        if isinstance(raw_object_instance_graph_id, UUID)
        else UUID(str(raw_object_instance_graph_id))
    )
    await ensure_object_instance_graph_identity_lane_head(
        index=index,
        object_instance_graph_id=object_instance_graph_id,
        domain_projection_hash=projection_hash,
        author_id=author_id,
        label=label,
    )


def _required_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
) -> UUID:
    matches = [
        class_config.id
        for class_config in index.class_configs_by_id.values()
        if (class_config.class_fqn or "").strip() == class_fqn
        and class_config.id is not None
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Experience binding portal requires exactly one class config: "
            f"class_fqn={class_fqn!r} matches={len(matches)}"
        )
    return matches[0]


def _build_projection_oigi_objects(
    *,
    projection_experience_id: UUID,
    node_identities_by_id: Mapping[UUID, ProjectionExperienceNodeIdentity],
    oigi: ExperienceProjectionOIGISnapshot,
) -> tuple[ProjectionExperienceOIGI, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    projection_oigi = _remember(
        objects_by_id,
        ProjectionExperienceOIGI(
            id=stable_projection_experience_oigi_id(
                projection_experience_id=projection_experience_id,
                object_instance_graph_identity_id=oigi.object_instance_graph_identity_id,
            ),
            projection_experience_id=projection_experience_id,
            object_instance_graph_identity_id=oigi.object_instance_graph_identity_id,
            key=(oigi.key or "").strip() or None,
        ),
    )
    _append_projection_oigi_node_class_identity_refs(
        objects_by_id=objects_by_id,
        projection_oigi=projection_oigi,
        object_instance_graph_id=oigi.object_instance_graph_id,
        node_identities_by_id=node_identities_by_id,
        identities=oigi.node_class_identities,
    )
    return projection_oigi, objects_by_id


def _append_projection_branches(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    branches: Sequence[ExperienceProjectionBranchSnapshot],
) -> None:
    for branch in branches:
        branch_name = _required_token(
            branch.name, label="ProjectionExperienceBranch.name"
        )
        projection_branch = _remember(
            objects_by_id,
            ProjectionExperienceBranch(
                id=stable_projection_experience_branch_id(
                    projection_experience_id=projection_experience.id,
                    name=branch_name,
                ),
                projection_experience_id=projection_experience.id,
                name=branch_name,
            ),
        )
        projection_experience.projection_experience_branches.append(projection_branch)


def _append_projection_views(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    views: Sequence[ExperienceProjectionViewSnapshot],
) -> None:
    for view in views:
        view_name = _required_token(view.name, label="ProjectionExperienceView.name")
        projection_view = _remember(
            objects_by_id,
            ProjectionExperienceView(
                id=stable_projection_experience_view_id(
                    projection_experience_id=projection_experience.id,
                    name=view_name,
                ),
                projection_experience_id=projection_experience.id,
                api_view_id=view.api_view_id,
                name=view_name,
            ),
        )
        projection_experience.projection_experience_views.append(projection_view)
        provider_ref = (view.state_provider_ref or "").strip()
        if provider_ref:
            provider = _remember(
                objects_by_id,
                ProjectionExperienceViewStateProvider(
                    id=stable_projection_experience_view_state_provider_id(
                        projection_experience_view_id=projection_view.id,
                    ),
                    projection_experience_view_id=projection_view.id,
                    provider_ref=provider_ref,
                    provider_kind=(
                        (view.provider_kind or "").strip() or "runtime_callable"
                    ),
                    purity=(view.purity or "").strip() or "pure_read",
                ),
            )
            projection_view.state_providers.append(provider)
        for action in view.invocation_actions:
            invocation_action_config = _experience_invocation_action_config(
                projection_experience_id=projection_experience.id,
                action=action,
            )
            invocation_action_config = _remember(
                objects_by_id,
                invocation_action_config,
            )
            if not any(
                existing.id == invocation_action_config.id
                for existing in projection_experience.invocation_action_configs
            ):
                projection_experience.invocation_action_configs.append(
                    invocation_action_config
                )
            view_invocation_action_config = _projection_view_invocation_action_config(
                projection_experience_view_id=projection_view.id,
                action=action,
                experience_invocation_action_config=invocation_action_config,
            )
            view_invocation_action_config = _remember(
                objects_by_id,
                view_invocation_action_config,
            )
            if not any(
                existing.id == view_invocation_action_config.id
                for existing in projection_view.invocation_action_configs
            ):
                projection_view.invocation_action_configs.append(
                    view_invocation_action_config
                )


def _experience_invocation_action_config(
    *,
    projection_experience_id: UUID,
    action: ExperienceProjectionViewInvocationActionConfigSnapshot,
) -> ExperienceInvocationActionConfig:
    api_capability_endpoint_id = action.api_capability_endpoint_id
    sdk_operation_id = action.sdk_operation_id
    if sdk_operation_id is not None:
        if action.sdk_operation_api_view_capability_endpoint_id is None:
            raise RuntimeError(
                "ExperienceInvocationActionConfig sdk target requires "
                + "sdk_operation_api_view_capability_endpoint_id"
            )
        target_kind = ExperienceInvocationActionTargetKind.sdk
        entity_id = sdk_operation_id
    elif api_capability_endpoint_id is not None:
        if api_capability_endpoint_id is None or sdk_operation_id is not None:
            raise RuntimeError(
                "ExperienceInvocationActionConfig api target requires only api_capability_endpoint_id"
            )
        target_kind = ExperienceInvocationActionTargetKind.api
        entity_id = api_capability_endpoint_id
    else:
        raise RuntimeError(
            "ExperienceInvocationActionConfig target requires api_capability_endpoint_id "
            + "or sdk_operation_id"
        )

    return ExperienceInvocationActionConfig(
        id=stable_experience_invocation_action_config_id(
            projection_experience_id=projection_experience_id,
            target_kind=target_kind.value,
            entity_id=entity_id,
        ),
        projection_experience_id=projection_experience_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        sdk_operation_id=sdk_operation_id,
        target_kind=target_kind,
    )


def _projection_view_invocation_action_config(
    *,
    projection_experience_view_id: UUID,
    action: ExperienceProjectionViewInvocationActionConfigSnapshot,
    experience_invocation_action_config: ExperienceInvocationActionConfig,
) -> ProjectionExperienceViewInvocationActionConfig:
    action_key = _required_token(
        action.action_key,
        label="ProjectionExperienceViewInvocationActionConfig.action_key",
    )
    return ProjectionExperienceViewInvocationActionConfig(
        id=stable_projection_experience_view_invocation_action_config_id(
            projection_experience_view_id=projection_experience_view_id,
            api_view_capability_endpoint_id=action.api_view_capability_endpoint_id,
        ),
        projection_experience_view_id=projection_experience_view_id,
        api_view_capability_endpoint_id=action.api_view_capability_endpoint_id,
        sdk_operation_api_view_capability_endpoint_id=(
            action.sdk_operation_api_view_capability_endpoint_id
        ),
        experience_invocation_action_config_id=(experience_invocation_action_config.id),
        experience_invocation_action_config=experience_invocation_action_config,
        action_key=action_key,
        label=action.label,
        receipt_policy=action.receipt_policy,
        confirmation_policy=action.confirmation_policy,
        optimistic_policy=action.optimistic_policy,
    )


def _append_projection_nodes(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    nodes: Sequence[ExperienceProjectionNodeSnapshot],
) -> None:
    for node in nodes:
        node_key = _required_token(node.key, label="ProjectionExperienceNode.key")
        projection_node = _remember(
            objects_by_id,
            ProjectionExperienceNode(
                id=stable_projection_experience_node_id(
                    projection_experience_id=projection_experience.id,
                    object_projection_graph_node_id=(
                        node.object_projection_graph_node_id
                    ),
                    key=node_key,
                ),
                projection_experience_id=projection_experience.id,
                object_projection_graph_node_id=node.object_projection_graph_node_id,
                key=node_key,
            ),
        )
        projection_experience.projection_experience_nodes.append(projection_node)
        identity_keys_seen: set[str] = set()
        for identity_key_raw in node.identity_keys:
            identity_key = _required_token(
                identity_key_raw,
                label="ProjectionExperienceNodeIdentity.key",
            )
            identity_key_casefolded = identity_key.casefold()
            if identity_key_casefolded in identity_keys_seen:
                raise RuntimeError(
                    "ProjectionExperienceNode snapshot duplicate identity key: "
                    + f"node={node_key!r} identity_key={identity_key!r}"
                )
            identity_keys_seen.add(identity_key_casefolded)
            node_identity = _remember(
                objects_by_id,
                ProjectionExperienceNodeIdentity(
                    id=stable_projection_experience_node_identity_id(
                        projection_experience_node_id=projection_node.id,
                        key=identity_key,
                    ),
                    projection_experience_node_id=projection_node.id,
                    key=identity_key,
                ),
            )
            projection_node.projection_experience_node_identities.append(node_identity)


def _append_projection_oigis(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    oigis: Sequence[ExperienceProjectionOIGISnapshot],
) -> None:
    projection_experience_id = projection_experience.id
    node_identities_by_id = {
        node_identity.id: node_identity
        for node in projection_experience.projection_experience_nodes
        for node_identity in node.projection_experience_node_identities
        if node_identity.id is not None
    }
    seen_oigi_ids: set[UUID] = set()
    for oigi in sorted(
        oigis,
        key=lambda item: (
            item.key or "",
            str(item.object_instance_graph_identity_id),
            str(item.object_instance_graph_id),
        ),
    ):
        expected_oigi_id = stable_projection_experience_oigi_id(
            projection_experience_id=projection_experience_id,
            object_instance_graph_identity_id=oigi.object_instance_graph_identity_id,
        )
        if expected_oigi_id in seen_oigi_ids:
            raise RuntimeError(
                "ProjectionExperience snapshot duplicate OIGI: "
                + f"projection_experience_oigi_id={expected_oigi_id}"
            )
        seen_oigi_ids.add(expected_oigi_id)
        projection_oigi = _remember(
            objects_by_id,
            ProjectionExperienceOIGI(
                id=expected_oigi_id,
                projection_experience_id=projection_experience_id,
                object_instance_graph_identity_id=(
                    oigi.object_instance_graph_identity_id
                ),
                key=(oigi.key or "").strip() or None,
            ),
        )
        projection_experience.projection_experience_oigis.append(projection_oigi)
        _append_projection_oigi_node_class_identities(
            objects_by_id=objects_by_id,
            projection_oigi=projection_oigi,
            object_instance_graph_id=oigi.object_instance_graph_id,
            node_identities_by_id=node_identities_by_id,
            identities=oigi.node_class_identities,
        )


def _append_projection_oigi_node_class_identities(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_oigi: ProjectionExperienceOIGI,
    object_instance_graph_id: UUID,
    node_identities_by_id: Mapping[UUID, ProjectionExperienceNodeIdentity],
    identities: Sequence[ExperienceProjectionNodeClassIdentitySnapshot],
) -> None:
    seen_node_identity_ids: set[UUID] = set()
    for identity in sorted(
        identities,
        key=lambda item: (
            item.key,
            str(item.projection_experience_node_identity_id),
            str(item.source_object_id),
        ),
    ):
        projection_node_identity = node_identities_by_id.get(
            identity.projection_experience_node_identity_id
        )
        if projection_node_identity is None:
            raise RuntimeError(
                "ProjectionExperience OIGI snapshot references unknown "
                + "ProjectionExperienceNodeIdentity: "
                + f"{identity.projection_experience_node_identity_id}"
            )
        if identity.projection_experience_node_identity_id in seen_node_identity_ids:
            raise RuntimeError(
                "ProjectionExperience OIGI snapshot has duplicate node binding: "
                + f"{identity.projection_experience_node_identity_id}"
            )
        seen_node_identity_ids.add(identity.projection_experience_node_identity_id)

        class_instance = _remember(
            objects_by_id,
            ClassInstance(
                id=stable_class_instance_id(
                    object_instance_graph_id=object_instance_graph_id,
                    class_config_id=identity.class_config_id,
                    source_object_id=identity.source_object_id,
                ),
                object_instance_graph_id=object_instance_graph_id,
                class_config_id=identity.class_config_id,
                source_object_id=identity.source_object_id,
            ),
        )
        class_instance_identity = _remember(
            objects_by_id,
            ClassInstanceIdentity(
                id=stable_class_instance_identity_id(
                    object_instance_graph_identity_id=(
                        projection_oigi.object_instance_graph_identity_id
                    ),
                    class_instance_id=class_instance.id,
                ),
                object_instance_graph_identity_id=(
                    projection_oigi.object_instance_graph_identity_id
                ),
                class_instance_id=class_instance.id,
                class_instance=class_instance,
                label=(identity.key or "").strip() or None,
            ),
        )
        if class_instance_identity.class_instance is None:
            class_instance_identity.class_instance = class_instance
        node_class_identity = _remember(
            objects_by_id,
            ProjectionExperienceNodeClassIdentity(
                id=stable_projection_experience_node_class_identity_id(
                    projection_experience_oigi_id=projection_oigi.id,
                    projection_experience_node_identity_id=(
                        identity.projection_experience_node_identity_id
                    ),
                    class_instance_identity_id=class_instance_identity.id,
                    key=identity.key,
                ),
                projection_experience_oigi_id=projection_oigi.id,
                projection_experience_node_identity_id=(
                    identity.projection_experience_node_identity_id
                ),
                projection_experience_node_identity=projection_node_identity,
                class_instance_identity_id=class_instance_identity.id,
                class_instance_identity=class_instance_identity,
                key=identity.key,
            ),
        )
        projection_oigi.node_class_identities.append(node_class_identity)


def _append_projection_oigi_node_class_identity_refs(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_oigi: ProjectionExperienceOIGI,
    object_instance_graph_id: UUID,
    node_identities_by_id: Mapping[UUID, ProjectionExperienceNodeIdentity],
    identities: Sequence[ExperienceProjectionNodeClassIdentitySnapshot],
) -> None:
    seen_node_identity_ids: set[UUID] = set()
    for identity in sorted(
        identities,
        key=lambda item: (
            item.key,
            str(item.projection_experience_node_identity_id),
            str(item.source_object_id),
        ),
    ):
        projection_node_identity = node_identities_by_id.get(
            identity.projection_experience_node_identity_id
        )
        if projection_node_identity is None:
            raise RuntimeError(
                "ProjectionExperience OIGI snapshot references unknown "
                + "ProjectionExperienceNodeIdentity: "
                + f"{identity.projection_experience_node_identity_id}"
            )
        if identity.projection_experience_node_identity_id in seen_node_identity_ids:
            raise RuntimeError(
                "ProjectionExperience OIGI snapshot has duplicate node binding: "
                + f"{identity.projection_experience_node_identity_id}"
            )
        seen_node_identity_ids.add(identity.projection_experience_node_identity_id)

        class_instance_id = stable_class_instance_id(
            object_instance_graph_id=object_instance_graph_id,
            class_config_id=identity.class_config_id,
            source_object_id=identity.source_object_id,
        )
        class_instance_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=(
                projection_oigi.object_instance_graph_identity_id
            ),
            class_instance_id=class_instance_id,
        )
        node_class_identity = _remember(
            objects_by_id,
            ProjectionExperienceNodeClassIdentity(
                id=stable_projection_experience_node_class_identity_id(
                    projection_experience_oigi_id=projection_oigi.id,
                    projection_experience_node_identity_id=(
                        identity.projection_experience_node_identity_id
                    ),
                    class_instance_identity_id=class_instance_identity_id,
                    key=identity.key,
                ),
                projection_experience_oigi_id=projection_oigi.id,
                projection_experience_node_identity_id=(
                    identity.projection_experience_node_identity_id
                ),
                projection_experience_node_identity=projection_node_identity,
                class_instance_identity_id=class_instance_identity_id,
                key=identity.key,
            ),
        )
        projection_oigi.node_class_identities.append(node_class_identity)


def _append_section_graph_bindings(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    bindings: Sequence[ExperienceSectionGraphBindingSnapshot],
) -> None:
    for binding in bindings:
        binding_key = _required_token(
            binding.binding_key,
            label="ProjectionExperienceSectionGraphBinding.binding_key",
        )
        section_key = _required_token(
            binding.section_key,
            label="ProjectionExperienceSectionGraphBinding.section_key",
        )
        section_binding = _remember(
            objects_by_id,
            ProjectionExperienceSectionGraphBinding(
                id=stable_projection_experience_section_graph_binding_id(
                    projection_experience_id=projection_experience.id,
                    layout_config_section_config_id=(
                        binding.layout_config_section_config_id
                    ),
                    projection_experience_view_id=(
                        binding.projection_experience_view_id
                    ),
                    projection_experience_graph_identity_id=(
                        binding.projection_experience_graph_identity_id
                    ),
                    binding_key=binding_key,
                ),
                projection_experience_id=projection_experience.id,
                layout_config_section_config_id=binding.layout_config_section_config_id,
                projection_experience_view_id=binding.projection_experience_view_id,
                projection_experience_graph_identity_id=(
                    binding.projection_experience_graph_identity_id
                ),
                binding_key=binding_key,
                section_key=section_key,
            ),
        )
        projection_experience.projection_experience_section_graph_bindings.append(
            section_binding
        )


def _append_layout_graph_bindings(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_experience: ProjectionExperience,
    bindings: Sequence[ExperienceLayoutGraphBindingSnapshot],
) -> None:
    section_bindings_by_key: dict[str, ProjectionExperienceSectionGraphBinding] = {}
    for (
        section_binding
    ) in projection_experience.projection_experience_section_graph_bindings:
        binding_key = _required_token(
            section_binding.binding_key,
            label="ProjectionExperienceSectionGraphBinding.binding_key",
        )
        key = binding_key.casefold()
        existing = section_bindings_by_key.get(key)
        if existing is not None and existing.id != section_binding.id:
            raise RuntimeError(
                "ProjectionExperience snapshot duplicate section graph binding key: "
                + f"{binding_key!r}"
            )
        section_bindings_by_key[key] = section_binding

    for binding in bindings:
        binding_key = _required_token(
            binding.binding_key,
            label="ProjectionExperienceLayoutGraphBinding.binding_key",
        )
        layout_binding = _remember(
            objects_by_id,
            ProjectionExperienceLayoutGraphBinding(
                id=stable_projection_experience_layout_graph_binding_id(
                    projection_experience_id=projection_experience.id,
                    layout_config_id=binding.layout_config_id,
                    binding_key=binding_key,
                ),
                projection_experience_id=projection_experience.id,
                layout_config_id=binding.layout_config_id,
                binding_key=binding_key,
            ),
        )
        seen_section_binding_ids: set[UUID] = set()
        for section_graph_binding_key in binding.section_graph_binding_keys:
            normalized_section_key = _required_token(
                section_graph_binding_key,
                label=(
                    "ProjectionExperienceLayoutGraphBinding."
                    + "section_graph_binding_key"
                ),
            )
            section_binding = section_bindings_by_key.get(
                normalized_section_key.casefold()
            )
            if section_binding is None:
                raise RuntimeError(
                    "ProjectionExperienceLayoutGraphBinding snapshot references "
                    + "unknown section graph binding "
                    + f"(layout_binding={binding_key!r}, "
                    + f"section_binding={normalized_section_key!r})"
                )
            expected_layout_section_id = stable_layout_config_section_config_id(
                layout_config_id=binding.layout_config_id,
                section_key=section_binding.section_key,
            )
            if (
                section_binding.layout_config_section_config_id
                != expected_layout_section_id
            ):
                raise RuntimeError(
                    "ProjectionExperienceLayoutGraphBinding snapshot section "
                    + "layout mismatch "
                    + f"(layout_binding={binding_key!r}, "
                    + f"section_binding={normalized_section_key!r})"
                )
            if section_binding.id in seen_section_binding_ids:
                raise RuntimeError(
                    "ProjectionExperienceLayoutGraphBinding snapshot duplicate "
                    + "section binding "
                    + f"(layout_binding={binding_key!r}, "
                    + f"section_binding={normalized_section_key!r})"
                )
            seen_section_binding_ids.add(section_binding.id)
            layout_section_binding = _remember(
                objects_by_id,
                ProjectionExperienceLayoutSectionGraphBinding(
                    id=stable_projection_experience_layout_section_graph_binding_id(
                        projection_experience_layout_graph_binding_id=(
                            layout_binding.id
                        ),
                        section_graph_binding_id=section_binding.id,
                    ),
                    projection_experience_layout_graph_binding_id=layout_binding.id,
                    section_graph_binding_id=section_binding.id,
                ),
            )
            layout_binding.layout_section_graph_bindings.append(layout_section_binding)
        projection_experience.projection_experience_layout_graph_bindings.append(
            layout_binding
        )


def _build_projection_experience_graph_objects(
    *,
    projection_experience_id: UUID,
    name: str,
    identities: Sequence[ExperienceGraphIdentitySnapshot],
    node_identity_edges: Sequence[ExperienceNodeIdentityEdgeSnapshot],
    graph_identity_edges: Sequence[ExperienceGraphIdentityEdgeSnapshot],
) -> tuple[ProjectionExperienceGraph, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = _required_token(name, label="ProjectionExperienceGraph.name")
    projection_graph = _remember(
        objects_by_id,
        ProjectionExperienceGraph(
            id=stable_projection_experience_graph_id(
                projection_experience_id=projection_experience_id,
                name=normalized_name,
            ),
            projection_experience_id=projection_experience_id,
            name=normalized_name,
        ),
    )
    _append_graph_identities(
        objects_by_id=objects_by_id,
        projection_graph=projection_graph,
        identities=identities,
    )
    _append_node_identity_edges(
        objects_by_id=objects_by_id,
        projection_graph=projection_graph,
        edges=node_identity_edges,
    )
    _append_graph_identity_edges(
        objects_by_id=objects_by_id,
        projection_graph=projection_graph,
        edges=graph_identity_edges,
    )
    return projection_graph, objects_by_id


def _append_graph_identities(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_graph: ProjectionExperienceGraph,
    identities: Sequence[ExperienceGraphIdentitySnapshot],
) -> None:
    root_count = sum(1 for identity in identities if identity.is_root)
    if identities and root_count != 1:
        raise RuntimeError(
            "ProjectionExperienceGraph snapshot requires exactly one root identity"
        )
    graph_identity_keys_seen: set[str] = set()
    node_identity_ids_seen: set[UUID] = set()
    for identity in identities:
        key = _required_token(
            identity.key,
            label="ProjectionExperienceGraphIdentity.key",
        )
        key_casefolded = key.casefold()
        if key_casefolded in graph_identity_keys_seen:
            raise RuntimeError(
                "ProjectionExperienceGraph snapshot duplicate identity key: "
                + f"key={key!r}"
            )
        if identity.projection_experience_node_identity_id in node_identity_ids_seen:
            raise RuntimeError(
                "ProjectionExperienceGraph snapshot duplicate node identity id: "
                + str(identity.projection_experience_node_identity_id)
            )
        graph_identity_keys_seen.add(key_casefolded)
        node_identity_ids_seen.add(identity.projection_experience_node_identity_id)
        graph_identity = _remember(
            objects_by_id,
            ProjectionExperienceGraphIdentity(
                id=stable_projection_experience_graph_identity_id(
                    projection_experience_graph_id=projection_graph.id,
                    projection_experience_node_identity_id=(
                        identity.projection_experience_node_identity_id
                    ),
                    key=key,
                ),
                projection_experience_graph_id=projection_graph.id,
                projection_experience_node_identity_id=(
                    identity.projection_experience_node_identity_id
                ),
                key=key,
                is_root=identity.is_root,
            ),
        )
        projection_graph.projection_experience_graph_identities.append(graph_identity)


def _append_node_identity_edges(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_graph: ProjectionExperienceGraph,
    edges: Sequence[ExperienceNodeIdentityEdgeSnapshot],
) -> None:
    child_ids_seen: set[UUID] = set()
    for edge in edges:
        if (
            edge.parent_projection_experience_node_identity_id
            == edge.child_projection_experience_node_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph node identity edge requires distinct parent/child ids"
            )
        if edge.child_projection_experience_node_identity_id in child_ids_seen:
            raise RuntimeError(
                "ProjectionExperienceGraph node identity edge snapshot enforces one parent per child"
            )
        child_ids_seen.add(edge.child_projection_experience_node_identity_id)
        node_identity_edge = _remember(
            objects_by_id,
            ProjectionExperienceNodeIdentityEdge(
                id=stable_projection_experience_node_identity_edge_id(
                    projection_experience_graph_id=projection_graph.id,
                    child_projection_experience_node_identity_id=(
                        edge.child_projection_experience_node_identity_id
                    ),
                    parent_projection_experience_node_identity_id=(
                        edge.parent_projection_experience_node_identity_id
                    ),
                ),
                projection_experience_graph_id=projection_graph.id,
                parent_projection_experience_node_identity_id=(
                    edge.parent_projection_experience_node_identity_id
                ),
                child_projection_experience_node_identity_id=(
                    edge.child_projection_experience_node_identity_id
                ),
                key=(edge.key or "").strip() or None,
            ),
        )
        projection_graph.projection_experience_node_identity_edges.append(
            node_identity_edge
        )


def _append_graph_identity_edges(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    projection_graph: ProjectionExperienceGraph,
    edges: Sequence[ExperienceGraphIdentityEdgeSnapshot],
) -> None:
    child_ids_seen: set[UUID] = set()
    for edge in edges:
        if (
            edge.parent_projection_experience_graph_identity_id
            == edge.child_projection_experience_graph_identity_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraph identity edge requires distinct parent/child ids"
            )
        if edge.child_projection_experience_graph_identity_id in child_ids_seen:
            raise RuntimeError(
                "ProjectionExperienceGraph identity edge snapshot enforces one parent per child"
            )
        child_ids_seen.add(edge.child_projection_experience_graph_identity_id)
        graph_identity_edge = _remember(
            objects_by_id,
            ProjectionExperienceGraphIdentityEdge(
                id=stable_projection_experience_graph_identity_edge_id(
                    projection_experience_graph_id=projection_graph.id,
                    child_projection_experience_graph_identity_id=(
                        edge.child_projection_experience_graph_identity_id
                    ),
                    parent_projection_experience_graph_identity_id=(
                        edge.parent_projection_experience_graph_identity_id
                    ),
                    projection_experience_node_identity_edge_id=(
                        edge.projection_experience_node_identity_edge_id
                    ),
                ),
                projection_experience_graph_id=projection_graph.id,
                parent_projection_experience_graph_identity_id=(
                    edge.parent_projection_experience_graph_identity_id
                ),
                child_projection_experience_graph_identity_id=(
                    edge.child_projection_experience_graph_identity_id
                ),
                projection_experience_node_identity_edge_id=(
                    edge.projection_experience_node_identity_edge_id
                ),
                key=(edge.key or "").strip() or None,
            ),
        )
        projection_graph.projection_experience_graph_identity_edges.append(
            graph_identity_edge
        )


def _build_actor_config_objects(
    *,
    key: str,
    title: str | None,
    description: str | None,
    type: ActorType | None,
) -> tuple[ActorConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_key = _required_token(key, label="ActorConfig.key")
    actor_config = _remember(
        objects_by_id,
        ActorConfig(
            id=stable_actor_config_id(key=normalized_key),
            key=normalized_key,
            title=title,
            description=description,
            type=type,
        ),
    )
    return actor_config, objects_by_id


def _build_program_config_objects(
    *,
    key: str,
    title: str | None,
    description: str | None,
    narrative: str | None,
    intent: str | None,
    is_default: bool,
    inputs: Sequence[ExperienceProgramInputSnapshot],
    actor_configs: Sequence[ExperienceProgramActorConfigSnapshot],
    ports: Sequence[ExperienceProgramPortSnapshot],
) -> tuple[ProgramConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_key = _required_token(key, label="ProgramConfig.key")
    program_config = _remember(
        objects_by_id,
        ProgramConfig(
            id=stable_program_config_id(key=normalized_key),
            key=normalized_key,
            title=title,
            description=description,
            narrative=narrative,
            intent=(intent or "").strip() or None,
            is_default=bool(is_default),
        ),
    )
    _append_program_inputs(
        objects_by_id=objects_by_id,
        program_config=program_config,
        inputs=inputs,
    )
    _append_program_actor_configs(
        objects_by_id=objects_by_id,
        program_config=program_config,
        actor_configs=actor_configs,
    )
    _append_program_ports(
        objects_by_id=objects_by_id,
        program_config=program_config,
        ports=ports,
    )
    return program_config, objects_by_id


def _append_program_inputs(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    program_config: ProgramConfig,
    inputs: Sequence[ExperienceProgramInputSnapshot],
) -> None:
    for item in inputs:
        input_name = _required_token(item.name, label="ProgramConfigInputConfig.name")
        input_source = _required_token(
            item.source,
            label="ProgramConfigInputConfig.source",
        )
        attribute_config = _build_primitive_attribute_config(
            objects_by_id=objects_by_id,
            owner_key=str(program_config.id),
            name=input_name,
            primitive_base_type=_program_primitive_type(item.attribute_type_ref),
            is_required=item.required,
        )
        program_attribute = _remember(
            objects_by_id,
            ProgramConfigAttributeConfig(
                id=stable_program_config_attribute_config_id(
                    program_config_id=program_config.id,
                    attribute_config_id=attribute_config.id,
                    type=ProgramAttributeType.input.value,
                ),
                program_config_id=program_config.id,
                attribute_config_id=attribute_config.id,
                attribute_config=attribute_config,
                type=ProgramAttributeType.input,
                position=item.position,
                required=item.required,
            ),
        )
        program_config.attribute_configs.append(program_attribute)
        input_config = _remember(
            objects_by_id,
            ProgramConfigInputConfig(
                id=stable_program_config_input_config_id(
                    program_config_id=program_config.id,
                    name=input_name,
                    source=input_source,
                ),
                program_config_id=program_config.id,
                name=input_name,
                source=input_source,
                required=item.required,
                default_expr=item.default_expr,
            ),
        )
        program_config.input_configs.append(input_config)


def _append_program_actor_configs(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    program_config: ProgramConfig,
    actor_configs: Sequence[ExperienceProgramActorConfigSnapshot],
) -> None:
    aliases_seen: set[str] = set()
    for item in actor_configs:
        alias = _required_token(item.alias, label="ProgramConfigActorConfig.alias")
        alias_key = alias.casefold()
        if alias_key in aliases_seen:
            raise RuntimeError(
                f"ProgramConfig snapshot duplicate actor alias: {alias!r}"
            )
        aliases_seen.add(alias_key)
        actor_key = (item.actor_key or "").strip()
        if actor_key:
            expected_actor_config_id = stable_actor_config_id(key=actor_key)
            if expected_actor_config_id != item.actor_config_id:
                raise RuntimeError(
                    "ProgramConfig actor snapshot id/key mismatch: "
                    + f"alias={alias!r} actor_key={actor_key!r}"
                )
            _remember(
                objects_by_id,
                ActorConfig(
                    id=item.actor_config_id,
                    key=actor_key,
                ),
            )
        actor_edge = _remember(
            objects_by_id,
            ProgramConfigActorConfig(
                id=stable_program_config_actor_config_id(
                    program_config_id=program_config.id,
                    alias=alias,
                ),
                program_config_id=program_config.id,
                actor_config_id=item.actor_config_id,
                alias=alias,
            ),
        )
        program_config.actor_configs.append(actor_edge)


def _append_program_ports(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    program_config: ProgramConfig,
    ports: Sequence[ExperienceProgramPortSnapshot],
) -> None:
    port_keys_seen: set[str] = set()
    for item in ports:
        port_key = _required_token(item.key, label="ProgramConfigPort.key")
        port_key_casefolded = port_key.casefold()
        if port_key_casefolded in port_keys_seen:
            raise RuntimeError(
                f"ProgramConfig snapshot duplicate port key: {port_key!r}"
            )
        port_keys_seen.add(port_key_casefolded)
        port = _remember(
            objects_by_id,
            ProgramConfigPort(
                id=stable_program_config_port_id(
                    program_config_id=program_config.id,
                    key=port_key,
                ),
                program_config_id=program_config.id,
                projection_id=item.projection_id,
                key=port_key,
                intent=(item.intent or "").strip() or None,
                branch_binding_mode=item.branch_binding_mode,
            ),
        )
        program_config.ports.append(port)
        node_keys_seen: set[str] = set()
        for node_snapshot in item.nodes:
            node_key = _required_token(
                node_snapshot.key,
                label="ProgramConfigPortProjectionExperienceNode.key",
            )
            node_key_casefolded = node_key.casefold()
            if node_key_casefolded in node_keys_seen:
                raise RuntimeError(
                    "ProgramConfig snapshot duplicate port node key: "
                    + f"port={port_key!r} node={node_key!r}"
                )
            node_keys_seen.add(node_key_casefolded)
            port_node = _remember(
                objects_by_id,
                ProgramConfigPortProjectionExperienceNode(
                    id=stable_program_config_port_projection_experience_node_id(
                        program_config_port_id=port.id,
                        projection_experience_node_id=(
                            node_snapshot.projection_experience_node_id
                        ),
                        key=node_key,
                    ),
                    program_config_port_id=port.id,
                    projection_experience_node_id=(
                        node_snapshot.projection_experience_node_id
                    ),
                    key=node_key,
                ),
            )
            port.projection_nodes.append(port_node)
            if node_snapshot.identity is not None:
                identity_key = _required_token(
                    node_snapshot.identity.key,
                    label=("ProgramConfigPortProjectionExperienceNodeIdentity.key"),
                )
                identity = _remember(
                    objects_by_id,
                    ProgramConfigPortProjectionExperienceNodeIdentity(
                        id=stable_program_config_port_projection_experience_node_identity_id(
                            program_config_port_projection_experience_node_id=(
                                port_node.id
                            ),
                            projection_experience_node_identity_id=(
                                node_snapshot.identity.projection_experience_node_identity_id
                            ),
                            key=identity_key,
                        ),
                        program_config_port_projection_experience_node_id=(
                            port_node.id
                        ),
                        projection_experience_node_identity_id=(
                            node_snapshot.identity.projection_experience_node_identity_id
                        ),
                        key=identity_key,
                    ),
                )
                port_node.projection_node_identity = identity


def _build_program_impl_objects(
    *,
    program_config_id: UUID,
    key: str,
    instructions: Sequence[ExperienceProgramImplInstructionSnapshot],
) -> tuple[ProgramImpl, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_key = _required_token(key, label="ProgramImpl.key")
    program_impl = _remember(
        objects_by_id,
        ProgramImpl(
            id=stable_program_impl_id(
                program_config_id=program_config_id,
                key=normalized_key,
            ),
            program_config_id=program_config_id,
            key=normalized_key,
        ),
    )
    sequences_seen: set[int] = set()
    for item in instructions:
        if item.sequence in sequences_seen:
            raise RuntimeError(
                f"ProgramImpl snapshot duplicate instruction sequence: {item.sequence}"
            )
        sequences_seen.add(item.sequence)
        instruction = _remember(
            objects_by_id,
            ProgramImplInstruction(
                id=stable_program_impl_instruction_id(
                    program_impl_id=program_impl.id,
                    sequence=item.sequence,
                ),
                program_impl_id=program_impl.id,
                type=item.instruction_type,
                sequence=item.sequence,
            ),
        )
        program_impl.instructions.append(instruction)
        _append_program_impl_instruction_payload(
            objects_by_id=objects_by_id,
            instruction=instruction,
            item=item,
        )
    return program_impl, objects_by_id


def _append_program_impl_instruction_payload(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    instruction: ProgramImplInstruction,
    item: ExperienceProgramImplInstructionSnapshot,
) -> None:
    instruction_id = instruction.id
    if item.instruction_type is ProgramImplInstructionType.input:
        input_config_id = _require_uuid(
            item.program_config_input_config_id,
            label="ProgramImplInstructionInput.program_config_input_config_id",
        )
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionInput(
                id=stable_program_impl_instruction_input_id(
                    program_impl_instruction_id=instruction_id,
                    program_config_input_config_id=input_config_id,
                ),
                program_impl_instruction_id=instruction_id,
                program_config_input_config_id=input_config_id,
            ),
        )
        instruction.instruction_input = payload
        return
    if item.instruction_type is ProgramImplInstructionType.let:
        name = _required_token(item.name or "", label="ProgramImplInstructionLet.name")
        value_expr = _require_json_object(
            item.value_expr,
            label="ProgramImplInstructionLet.value_expr",
        )
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionLet(
                id=stable_program_impl_instruction_let_id(
                    program_impl_instruction_id=instruction_id,
                ),
                program_impl_instruction_id=instruction_id,
                name=name,
                value_expr=value_expr,
            ),
        )
        instruction.instruction_let = payload
        return
    if item.instruction_type is ProgramImplInstructionType.bind:
        port_id = _require_uuid(
            item.program_config_port_id,
            label="ProgramImplInstructionBind.program_config_port_id",
        )
        view_key = _required_token(
            item.view_key or "",
            label="ProgramImplInstructionBind.view_key",
        )
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionBind(
                id=stable_program_impl_instruction_bind_id(
                    program_impl_instruction_id=instruction_id,
                ),
                program_impl_instruction_id=instruction_id,
                program_config_port_id=port_id,
                view_key=view_key,
                is_active=item.is_active,
            ),
        )
        instruction.instruction_bind = payload
        return
    if item.instruction_type is ProgramImplInstructionType.expect:
        event_config_id = _require_uuid(
            item.event_config_id,
            label="ProgramImplInstructionExpect.event_config_id",
        )
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionExpect(
                id=stable_program_impl_instruction_expect_id(
                    program_impl_instruction_id=instruction_id,
                ),
                program_impl_instruction_id=instruction_id,
                event_config_id=event_config_id,
                required=item.required,
            ),
        )
        instruction.instruction_expect = payload
        return
    if item.instruction_type is ProgramImplInstructionType.intent:
        action_config_id = _require_uuid(
            item.action_config_id,
            label="ProgramImplInstructionIntent.action_config_id",
        )
        event_config_id = _require_uuid(
            item.event_config_id,
            label="ProgramImplInstructionIntent.event_config_id",
        )
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionIntent(
                id=stable_program_impl_instruction_intent_id(
                    program_impl_instruction_id=instruction_id,
                ),
                program_impl_instruction_id=instruction_id,
                action_config_id=action_config_id,
                event_config_id=event_config_id,
                continuation_key=(item.continuation_key or "").strip() or None,
                api_capability_endpoint_id=item.api_capability_endpoint_id,
                request_class_config_id=item.request_class_config_id,
                response_class_config_id=item.response_class_config_id,
            ),
        )
        instruction.instruction_intent = payload
        _append_program_impl_instruction_intent_bindings(
            objects_by_id=objects_by_id,
            intent=payload,
            item=item,
        )
        return
    if item.instruction_type is ProgramImplInstructionType.invoke:
        invoke_payload = _build_program_impl_instruction_invoke(
            objects_by_id=objects_by_id,
            instruction_id=instruction_id,
            item=item,
        )
        instruction.instruction_invoke = invoke_payload
        return
    raise RuntimeError(
        "ProgramImpl snapshot unsupported instruction type: "
        + repr(item.instruction_type)
    )


def _append_program_impl_instruction_intent_bindings(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    intent: ProgramImplInstructionIntent,
    item: ExperienceProgramImplInstructionSnapshot,
) -> None:
    for binding in item.activation_field_bindings:
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionIntentActivationFieldBinding(
                id=stable_program_impl_instruction_intent_activation_field_binding_id(
                    program_impl_instruction_intent_id=intent.id,
                    source_class_config_id=binding.source_class_config_id,
                    source_attribute_config_id=binding.source_attribute_config_id,
                    target_request_attribute_config_id=(
                        binding.target_request_attribute_config_id
                    ),
                    source_input_key=binding.source_input_key,
                ),
                program_impl_instruction_intent_id=intent.id,
                source_input_key=binding.source_input_key,
                source_class_config_id=binding.source_class_config_id,
                source_attribute_config_id=binding.source_attribute_config_id,
                target_request_attribute_config_id=(
                    binding.target_request_attribute_config_id
                ),
                required=binding.required,
                position=binding.position,
            ),
        )
        intent.activation_field_bindings.append(payload)
    for binding in item.outcome_field_bindings:
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionIntentOutcomeFieldBinding(
                id=stable_program_impl_instruction_intent_outcome_field_binding_id(
                    program_impl_instruction_intent_id=intent.id,
                    source_program_impl_instruction_intent_id=(
                        binding.source_program_impl_instruction_intent_id
                    ),
                    source_response_attribute_config_id=(
                        binding.source_response_attribute_config_id
                    ),
                    target_request_attribute_config_id=(
                        binding.target_request_attribute_config_id
                    ),
                ),
                program_impl_instruction_intent_id=intent.id,
                source_program_impl_instruction_intent_id=(
                    binding.source_program_impl_instruction_intent_id
                ),
                source_response_attribute_config_id=(
                    binding.source_response_attribute_config_id
                ),
                target_request_attribute_config_id=(
                    binding.target_request_attribute_config_id
                ),
                required=binding.required,
                position=binding.position,
            ),
        )
        intent.outcome_field_bindings.append(payload)
    for binding in item.receipt_field_bindings:
        payload = _remember(
            objects_by_id,
            ProgramImplInstructionIntentReceiptFieldBinding(
                id=stable_program_impl_instruction_intent_receipt_field_binding_id(
                    program_impl_instruction_intent_id=intent.id,
                    source_program_impl_instruction_intent_id=(
                        binding.source_program_impl_instruction_intent_id
                    ),
                    source_receipt_class_config_id=(
                        binding.source_receipt_class_config_id
                    ),
                    source_receipt_attribute_config_id=(
                        binding.source_receipt_attribute_config_id
                    ),
                    target_request_attribute_config_id=(
                        binding.target_request_attribute_config_id
                    ),
                ),
                program_impl_instruction_intent_id=intent.id,
                source_program_impl_instruction_intent_id=(
                    binding.source_program_impl_instruction_intent_id
                ),
                source_receipt_class_config_id=(binding.source_receipt_class_config_id),
                source_receipt_attribute_config_id=(
                    binding.source_receipt_attribute_config_id
                ),
                target_request_attribute_config_id=(
                    binding.target_request_attribute_config_id
                ),
                required=binding.required,
                position=binding.position,
            ),
        )
        intent.receipt_field_bindings.append(payload)


def _build_program_impl_instruction_invoke(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    instruction_id: UUID,
    item: ExperienceProgramImplInstructionSnapshot,
) -> ProgramImplInstructionInvoke:
    function_config_id = _require_uuid(
        item.function_config_id,
        label="ProgramImplInstructionInvoke.function_config_id",
    )
    actor_config_id = _require_uuid(
        item.program_config_actor_config_id,
        label="ProgramImplInstructionInvoke.program_config_actor_config_id",
    )
    port_node_id = _require_uuid(
        item.program_config_port_projection_experience_node_id,
        label=(
            "ProgramImplInstructionInvoke."
            "program_config_port_projection_experience_node_id"
        ),
    )
    invoke_payload = _remember(
        objects_by_id,
        ProgramImplInstructionInvoke(
            id=stable_program_impl_instruction_invoke_id(
                program_impl_instruction_id=instruction_id,
            ),
            program_impl_instruction_id=instruction_id,
            function_config_id=function_config_id,
            program_config_actor_config_id=actor_config_id,
            program_config_port_projection_experience_node_id=port_node_id,
            target_kind=item.target_kind,
        ),
    )
    attribute_ids_seen: set[UUID] = set()
    for attribute in item.invoke_attributes:
        if attribute.attribute_config_id in attribute_ids_seen:
            raise RuntimeError(
                "ProgramImpl invoke snapshot duplicate attribute config id: "
                + str(attribute.attribute_config_id)
            )
        attribute_ids_seen.add(attribute.attribute_config_id)
        attribute_payload = _remember(
            objects_by_id,
            ProgramImplInstructionInvokeAttributeConfig(
                id=stable_program_impl_instruction_invoke_attribute_config_id(
                    program_impl_instruction_invoke_id=invoke_payload.id,
                    attribute_config_id=attribute.attribute_config_id,
                ),
                program_impl_instruction_invoke_id=invoke_payload.id,
                attribute_config_id=attribute.attribute_config_id,
                value_expr=attribute.value_expr,
                position=attribute.position,
            ),
        )
        invoke_payload.attribute_configs.append(attribute_payload)
    return invoke_payload


def _build_primitive_attribute_config(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    owner_key: str,
    name: str,
    primitive_base_type: CodePrimitiveBaseType,
    is_required: bool,
) -> AttributeConfig:
    normalized_owner_key = _required_token(
        owner_key,
        label="AttributeConfig.owner_key",
    ).casefold()
    normalized_name = _required_token(name, label="AttributeConfig.name").casefold()
    primitive_type = CodePrimitiveType(
        id=None,
        signature=primitive_base_type.value,
        base_type=primitive_base_type,
    )
    primitive_config = build_primitive_config(primitive_type)
    descriptor = ensure_stable_descriptor_tree_ids(
        AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=primitive_config,
            primitive_config_id=primitive_config.id,
        )
    )
    _remember_descriptor_tree(objects_by_id=objects_by_id, descriptor=descriptor)
    attribute_config = _remember(
        objects_by_id,
        AttributeConfig(
            id=stable_attribute_config_id(
                owner_key=normalized_owner_key,
                name=normalized_name,
            ),
            owner_key=normalized_owner_key,
            name=normalized_name,
            is_required=is_required,
            type_descriptor=descriptor,
            type_descriptor_id=descriptor.id,
        ),
    )
    return attribute_config


def _remember_descriptor_tree(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    descriptor: AttributeTypeDescriptor,
) -> None:
    primitive_config = descriptor.primitive_config
    if primitive_config is not None:
        primitive_type = primitive_config.primitive_type
        if primitive_type is not None:
            _remember(objects_by_id, primitive_type)
        _remember(objects_by_id, primitive_config)
    _remember(objects_by_id, descriptor)
    for link in descriptor.child_links:
        _remember_descriptor_tree(objects_by_id=objects_by_id, descriptor=link.child)
        _remember(objects_by_id, link)


def _program_primitive_type(type_ref: str) -> CodePrimitiveBaseType:
    normalized = (type_ref or "").strip().casefold() or "any"
    aliases = {
        "bool": CodePrimitiveBaseType.boolean,
        "boolean": CodePrimitiveBaseType.boolean,
        "bytes": CodePrimitiveBaseType.bytes,
        "datetime": CodePrimitiveBaseType.datetime,
        "float": CodePrimitiveBaseType.float,
        "int": CodePrimitiveBaseType.integer,
        "integer": CodePrimitiveBaseType.integer,
        "json": CodePrimitiveBaseType.json,
        "string": CodePrimitiveBaseType.string,
        "str": CodePrimitiveBaseType.string,
        "uuid": CodePrimitiveBaseType.uuid,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return CodePrimitiveBaseType(normalized)
    except ValueError as exc:
        raise RuntimeError(
            "ProgramConfig snapshot requires primitive input type ref: "
            + f"{type_ref!r}"
        ) from exc


async def _commit_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    root_object: BaseORMModel,
    objects_by_id: Mapping[UUID, BaseORMModel],
    operation_label: str,
    commit_id_namespace: UUID,
    reconcile_class_fqn_suffixes: Sequence[str] = (),
) -> _SnapshotCommit:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Experience snapshot commit missing projection hash: " f"{projection_hash}"
        )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index, projection_hash=projection_hash
    )
    if opgi is None:
        raise RuntimeError(
            "Experience snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    pre_state = await _load_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=root_object_id,
    )
    before_oig = pre_state.before_oig
    lane_root_object_id = resolve_root_source_object_id(before_oig)
    object_ids = frozenset(objects_by_id)
    reconciled_prior_object_ids = frozenset(
        class_instance.source_object_id
        for class_instance in before_oig.class_instances
        if class_instance.source_object_id is not None
        and (
            class_config := index.class_configs_by_id.get(
                class_instance.class_config_id
            )
        )
        is not None
        and any(
            str(class_config.class_fqn or "").endswith(suffix)
            for suffix in reconcile_class_fqn_suffixes
        )
    )
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=object_ids,
        touched_ids=object_ids,
        deleted_ids=reconciled_prior_object_ids - object_ids,
        objects_by_id=dict(objects_by_id),
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=oigi_id,
        ocg=index.ocg,
        opg=opg,
        change_set=change_set,
        class_configs_by_id=index.class_configs_by_id,
        relationships_by_id=index.relationships_by_id,
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        commit_store = FSCommitStore()
        head = await commit_store.head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        raw_head_commit_id = None if head is None else head.get("commit_id")
        if raw_head_commit_id is None:
            raise RuntimeError(
                "Experience snapshot commit produced no OIG changes and no "
                f"existing lane head: operation_label={operation_label!r}"
            )
        head_commit_id = (
            raw_head_commit_id
            if isinstance(raw_head_commit_id, UUID)
            else UUID(str(raw_head_commit_id))
        )
        committed_oig_commit_id = await _committed_oig_commit_id_for_head(
            commit_store=commit_store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=head_commit_id,
            head=head,
            operation_label=operation_label,
        )
        return _SnapshotCommit(
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=committed_oig_commit_id,
            object_count=len(objects_by_id),
            change_count=0,
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _snapshot_commit_id(
        namespace=commit_id_namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        parent_commit_id=pre_state.parent_commit_id,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=lane_root_object_id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label=operation_label,
            call_target="generated_materialization",
            object_id=root_object.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Experience snapshot commit did not append a lane commit: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    return _SnapshotCommit(
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


async def _committed_oig_commit_id_for_head(
    *,
    commit_store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    head_commit_id: UUID,
    head: Mapping[str, object],
    operation_label: str,
) -> UUID:
    committed_identity = await commit_store.get_commit_identity_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=head_commit_id,
    )
    if committed_identity is None:
        committed_head = await commit_store.get_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        if committed_head is None:
            raise RuntimeError(
                "Experience snapshot no-change HEAD has no committed identity: "
                f"operation_label={operation_label!r} "
                f"head_commit_id={head_commit_id}"
            )
        committed_oigi_id = committed_head.object_instance_graph_identity_id
    else:
        committed_oigi_id = committed_identity.object_instance_graph_identity_id
    committed_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=committed_oigi_id,
        commit_id=head_commit_id,
    )
    raw_head_oig_commit_id = head.get("object_instance_graph_commit_id")
    if raw_head_oig_commit_id is not None:
        head_oig_commit_id = (
            raw_head_oig_commit_id
            if isinstance(raw_head_oig_commit_id, UUID)
            else UUID(str(raw_head_oig_commit_id))
        )
        if head_oig_commit_id != committed_oig_commit_id:
            raise RuntimeError(
                "Experience snapshot no-change HEAD identity mismatch: "
                f"operation_label={operation_label!r} "
                f"head_commit_id={head_commit_id} "
                f"head_oig_commit_id={head_oig_commit_id} "
                f"committed_oig_commit_id={committed_oig_commit_id}"
            )
    return committed_oig_commit_id


async def _load_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
) -> _SnapshotLanePreState:
    opg = index.opg_by_hash[projection_hash]
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    raw_head_commit_id = None if head is None else head.get("commit_id")
    if raw_head_commit_id is not None:
        parent_commit_id = (
            raw_head_commit_id
            if isinstance(raw_head_commit_id, UUID)
            else UUID(str(raw_head_commit_id))
        )
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        return _SnapshotLanePreState(
            before_oig=oig,
            parent_commit_id=parent_commit_id,
        )
    return _SnapshotLanePreState(
        before_oig=build_rooted_object_instance_graph_base(
            key=str(branch_id),
            name=f"OIG_{branch_id.hex[:8]}",
            description="ROOTED_BASE",
            object_config_graph=index.ocg,
            object_projection_graph=opg,
            root_source_object_id=root_object_id,
            oig_id=domain_oig_id,
        ),
        parent_commit_id=None,
    )


def _snapshot_commit_id(
    *,
    namespace: UUID,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    parent_commit_id: UUID | None,
    graph_hash_pre: str,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        namespace,
        (
            f"{branch_id}:{projection_hash}:{root_object_id}:"
            f"{parent_commit_id or 'genesis'}:"
            f"{graph_hash_pre}:{graph_hash_post}"
        ),
    )


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    obj_id = obj.id
    previous = objects_by_id.get(obj_id)
    if previous is not None:
        if previous is obj or _snapshot_objects_equivalent(previous=previous, obj=obj):
            return cast(_TModel, previous)
        raise RuntimeError(
            "Experience snapshot duplicate object id with conflicting payload: "
            + f"{obj_id} previous={type(previous).__name__} "
            + f"current={type(obj).__name__}"
        )
    objects_by_id[obj_id] = obj
    return obj


def _snapshot_objects_equivalent(*, previous: BaseORMModel, obj: BaseORMModel) -> bool:
    if type(previous) is not type(obj):
        return False
    if previous == obj:
        return True
    try:
        return previous.model_dump(mode="json") == obj.model_dump(mode="json")
    except Exception:
        return False


def _required_token(value: str, *, label: str) -> str:
    token = (value or "").strip()
    if not token:
        raise RuntimeError(f"{label} is required")
    return token


def _require_uuid(value: UUID | None, *, label: str) -> UUID:
    if value is None:
        raise RuntimeError(f"{label} is required")
    return value


def _require_json_object(value: JsonObject | None, *, label: str) -> JsonObject:
    if value is None:
        raise RuntimeError(f"{label} is required")
    return value


__all__ = [
    "ExperienceActorSnapshotCommitResult",
    "ExperienceEnvironmentSnapshotCommitResult",
    "ExperienceGraphIdentityEdgeSnapshot",
    "ExperienceGraphIdentitySnapshot",
    "ExperienceGraphSnapshotCommitResult",
    "ExperienceLayoutGraphBindingSnapshot",
    "ExperienceNodeIdentityEdgeSnapshot",
    "ExperiencePackageManifestSnapshotCommitResult",
    "ExperiencePackageAttentionPackageSnapshotRef",
    "ExperiencePackageDependencySnapshot",
    "ExperiencePackageLanguagePackageSnapshotRef",
    "ExperienceProgramActorConfigSnapshot",
    "ExperienceProgramImplActivationFieldBindingSnapshot",
    "ExperienceProgramConfigSnapshotCommitResult",
    "ExperienceProgramImplInstructionSnapshot",
    "ExperienceProgramImplInvokeAttributeSnapshot",
    "ExperienceProgramImplOutcomeFieldBindingSnapshot",
    "ExperienceProgramImplReceiptFieldBindingSnapshot",
    "ExperienceProgramImplSnapshotCommitResult",
    "ExperienceProgramInputSnapshot",
    "ExperienceProgramPortNodeIdentitySnapshot",
    "ExperienceProgramPortNodeSnapshot",
    "ExperienceProgramPortSnapshot",
    "ExperienceProjectionBranchSnapshot",
    "ExperienceProjectionNodeSnapshot",
    "ExperienceProjectionSnapshotCommitResult",
    "ExperienceProjectionViewInvocationActionConfigSnapshot",
    "ExperienceProjectionViewInvocationActionSnapshot",
    "ExperienceProjectionViewSnapshot",
    "ExperienceSectionGraphBindingSnapshot",
    "commit_actor_config_snapshot",
    "commit_environment_experience_snapshot",
    "commit_experience_package_manifest_snapshot",
    "commit_program_config_snapshot",
    "commit_program_impl_snapshot",
    "commit_projection_experience_graph_snapshot",
    "commit_projection_experience_snapshot",
]
