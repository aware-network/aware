from __future__ import annotations

# Standard
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage
from aware_code_ontology_dto.code.code_section_enums import CodeSectionType

# Types
from aware_types import JsonObject


class CodeSectionAnnotationPlan(BaseModel):
    """
    Canonical parser-emitted annotation payload plan.
    This is a transport/materialization-plan DTO. It is not a graph entity.
    """

    # Attributes
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)


class CodeSegmentPlan(BaseModel):
    """
    Canonical parser-emitted segment slot plan.
    This is a transport/materialization-plan DTO. It is not a graph entity.
    """

    # Attributes
    slot_key: str
    byte_start: int
    byte_end: int


class CodeSectionImportNamePlan(BaseModel):
    """
    Canonical parser-emitted import-name payload plan.
    This is a transport/materialization-plan DTO. It is not a graph entity.
    """

    # Attributes
    name_text: str
    alias_text: str | None = Field(default=None)
    name_segment_plan: CodeSegmentPlan
    alias_segment_plan: CodeSegmentPlan | None = Field(default=None)


class CodeSectionImportPlan(BaseModel):
    """
    Canonical parser-emitted import payload plan.
    This is a transport/materialization-plan DTO. It is not a graph entity.
    """

    # Attributes
    module_text: str
    is_from_import: bool
    is_star_import: bool
    relative_level: int = Field(default=0)
    module_segment_plan: CodeSegmentPlan
    name_plans: list[CodeSectionImportNamePlan] = Field(default_factory=list)


class CodeSectionPlan(BaseModel):
    """
    Canonical parser-emitted section materialization plan.
    This is a transport/materialization-plan DTO. It is not a graph entity.
    """

    # Attributes
    section_key: str
    section_type: CodeSectionType
    qualname: str
    identity_hash: str
    byte_start: int
    byte_end: int
    reference: str | None = Field(default=None)
    parent_qualname: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)
    annotation_plan: CodeSectionAnnotationPlan | None = Field(default=None)
    import_plan: CodeSectionImportPlan | None = Field(default=None)


class CodeContentPlan(BaseModel):
    """
    Canonical code content plan emitted by pure parser/planner rails.
    This plan is platonic:
    - no filesystem path semantics
    - no graph ids
    - no ontology object ownership
    """

    # Attributes
    language: CodeLanguage
    content_text: str
    section_plans: list[CodeSectionPlan] = Field(default_factory=list)


class CodePackageDeltaKind(Enum):
    """
    Package-local source delta operation kind.
    This is Code-owned IR, not repository-layout state. Workspace and semantic owners
    should exchange package deltas through this shape after neutral source observation.
    """

    create = "create"
    update = "update"
    delete = "delete"


class CodePackageDeltaAuthorityKind(Enum):
    """
    Typed authority class for a CodePackageDelta.
    This classifies how the delta entered the raw CodePackage lane. It does not
    name semantic packages, Workspace revisions, or materialization receipts.
    """

    local_fs_view = "local_fs_view"
    remote_workspace_view = "remote_workspace_view"
    code_package_delta = "code_package_delta"
    semantic_materialization = "semantic_materialization"
    tool_materialization = "tool_materialization"


class CodePackagePathRole(Enum):
    """
    Package-relative role for one Code path.
    This role belongs to the package attachment, not to semantic package truth.
    """

    authored_source = "authored_source"
    generated_code = "generated_code"
    generated_manifest = "generated_manifest"
    generated_metadata = "generated_metadata"


class CodePackageDeltaProducerRef(BaseModel):
    """
    Generic producer pointer for CodePackageDelta output.
    Code owns only the raw producer identity:
    - provider identity
    - provider-local stable producer key
    - opaque provider payload for later hub/runtime routing
    Semantic package identities and materialization receipts stay on Workspace
    materialization rails.
    """

    # Attributes
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaProduction(BaseModel):
    """
    One producer emission for CodePackageDelta output.
    This is a raw CodePackage provenance pointer. OIG commit ids are opaque UUIDs
    here; Code does not hydrate or interpret meta/workspace commit truth.
    """

    # Attributes
    producer: CodePackageDeltaProducerRef
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaPath(BaseModel):
    """
    One package-relative code path delta.
    Upsert operations may carry either raw `content_text` or a precomputed `content_plan`.
    `CodePackage.apply_delta` treats `content_plan` as authoritative when present.
    """

    # Attributes
    relative_path: str
    kind: CodePackageDeltaKind
    content_text: str | None = Field(default=None)
    content_plan: CodeContentPlan | None = Field(default=None)
    before_hash: str | None = Field(default=None)
    after_hash: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    language: CodeLanguage | None = Field(default=None)
    is_structural: bool | None = Field(default=None)
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
    production: CodePackageDeltaProduction | None = Field(default=None)


class CodePackageDelta(BaseModel):
    """
    CodePackage-level delta bundle.
    Canonical ownership:
    - Structure/Repository may observe raw file changes.
    - Workspace normalizes those observations into CodePackageDelta.
    - CodePackage consumes this IR to commit package-owned code.
    - Semantic owners consume this same IR after the CodePackage commit.
    """

    # Attributes
    package_name: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    authority: CodePackageDeltaAuthorityKind | None = Field(default=None)
    authority_kind: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    production: CodePackageDeltaProduction | None = Field(default=None)
    paths: list[CodePackageDeltaPath] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CodePackageDeltaApplyResult(BaseModel):
    """Result of applying a CodePackageDelta through the CodePackage mutation boundary."""

    # Attributes
    applied_path_count: int = Field(default=0)
    created_path_count: int = Field(default=0)
    updated_path_count: int = Field(default=0)
    deleted_path_count: int = Field(default=0)
    deleted_missing_path_count: int = Field(default=0)
    skipped_path_count: int = Field(default=0)
