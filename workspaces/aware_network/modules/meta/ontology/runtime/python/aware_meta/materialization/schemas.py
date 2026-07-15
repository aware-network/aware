from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageResult,
    ObjectConfigGraphPackageSpec,
)
from aware_meta.materialization.artifact_lifecycle import (
    LanguageMaterializationArtifactChangeKind as MaterializationArtifactChangeKind,
    LanguageMaterializationArtifactKind as MaterializationArtifactKind,
    LanguageMaterializationProducerStep as MaterializationProducerStep,
    LanguageMaterializationStageability as MaterializationStageability,
)


ORM_RUNTIME_RENDERER_PROFILE = "orm_runtime"
API_RUNTIME_RENDERER_PROFILE = "api_runtime"
API_PUBLIC_PACKAGE_KIND = "api_public_package"
API_SERVICE_PROTOCOL_KIND = "api_service_protocol"
ONTOLOGY_DTO_PACKAGE_KIND = "ontology_dto"
API_PUBLIC_PACKAGE_RENDERER_PROFILE = API_PUBLIC_PACKAGE_KIND
API_SERVICE_PROTOCOL_RENDERER_PROFILE = API_SERVICE_PROTOCOL_KIND
ONTOLOGY_DTO_RENDERER_PROFILE = ONTOLOGY_DTO_PACKAGE_KIND


class MaterializationSource(str, Enum):
    """Where a materialization derives its graph."""

    ontology = "ontology"
    # Compiler-owned consumer DTO packages derived from ontology truth but free
    # of ORM/runtime helpers.
    ontology_dto = "ontology_dto"
    api = "api"
    # Runtime-owned artifacts derived from the same canonical graph but not
    # treated as structural outputs.
    runtime_handlers = "runtime_handlers"


class MaterializationProfileInputFormat(str, Enum):
    """Serialization format for generic renderer profile inputs."""

    json = "json"
    text = "text"


class MaterializationProfileInputRef(BaseModel):
    """Generic profile-scoped input reference resolved before render."""

    key: str
    path: Path
    format: MaterializationProfileInputFormat = MaterializationProfileInputFormat.json
    required: bool = True


class MaterializationEntityType(str, Enum):
    """Type of entity being materialized."""

    object = "object"
    class_ = "class"
    function = "function"
    enum = "enum"


class MaterializationEntityMetadata(BaseModel):
    """Metadata describing a rendered entity for manifest consumers."""

    entity_type: MaterializationEntityType
    name: str
    namespace: str | None = None
    class_name: str | None = None
    class_id: str | None = None
    parent_class_id: str | None = None
    runtime_class_fqn: str | None = None


class MaterializationPostStep(BaseModel):
    """
    Post-materialization steps.

    Executed after packages are built so they validate the real, final artifacts.
    """

    name: str
    packages: list[str] = Field(default_factory=list)
    on_fail: str = Field(default="fail")
    args: list[str] = Field(default_factory=list)


class MaterializationConfig(BaseModel):
    """Language materialization configuration."""

    name: str = Field(default="materialize")
    # SSOT anchor for what is being materialized.
    source_aware_toml_path: Path | None = None
    # Derived at runtime; used for stable import_root resolution.
    source_package_name: str | None = Field(default=None, exclude=True)
    target_language: CodeLanguage = CodeLanguage.aware
    derive_language: CodeLanguage | None = None
    renderer_kind: str | None = None
    stable_ids_ownership: str = "authored"
    stable_ids_parity_policy: str = "warn"
    stable_ids_resolution_policy: str = "class_strict"
    function_impl_ownership: str = "authored"
    function_impl_parity_policy: str = "off"
    target_output_dir: Path = Path(".")
    manifest_path: Path | None = None
    import_root: str | None = None
    packages: list[ObjectConfigGraphPackageSpec] = Field(default_factory=list)
    source: MaterializationSource = MaterializationSource.ontology
    profile_input_refs: list[MaterializationProfileInputRef] = Field(
        default_factory=list
    )
    post_steps: list[MaterializationPostStep] = Field(default_factory=list)


class MaterializationArtifactChange(BaseModel):
    """Canonical per-artifact mutation record emitted by the materialization rail."""

    repo_rel_path: Path
    materialization_rel_path: Path | None = None
    package_rel_path: Path | None = None
    package_name: str | None = None
    change_kind: MaterializationArtifactChangeKind
    artifact_kind: MaterializationArtifactKind
    producer_step: MaterializationProducerStep
    stageability: MaterializationStageability
    stageability_reason: str | None = None
    hash_before: str | None = None
    hash_after: str | None = None
    bytes_before: int | None = None
    bytes_after: int | None = None
    ownership_receipt: dict[str, object] | None = None

    @model_validator(mode="after")
    def _validate_stageability_reason(self) -> "MaterializationArtifactChange":
        if self.stageability == MaterializationStageability.stage:
            return self
        if self.stageability_reason is None or not self.stageability_reason.strip():
            raise ValueError(
                "stageability_reason is required when stageability is review or skip"
            )
        return self


class MaterializationPackageOutcome(BaseModel):
    """Package-scoped grouping for final emitted package surfaces."""

    package_name: str
    output_root: Path
    import_root: str | None = None
    artifact_change_refs: list[Path] = Field(default_factory=list)


class MaterializationOutcomeSummary(BaseModel):
    """Derived summary for a materialization outcome."""

    changes_total: int = 0
    changes_by_kind: dict[str, int] = Field(default_factory=dict)
    changes_by_producer_step: dict[str, int] = Field(default_factory=dict)
    changes_by_stageability: dict[str, int] = Field(default_factory=dict)
    package_count: int = 0
    warning_count: int = 0


class MaterializationOutcome(BaseModel):
    """Typed materialization outcome envelope."""

    materialization_name: str
    source_package_name: str | None = None
    source_kind: MaterializationSource
    target_language: CodeLanguage
    aware_root: Path
    output_root: Path
    manifest_path: Path | None = None
    warnings: list[str] = Field(default_factory=list)
    package_outcomes: list[MaterializationPackageOutcome] = Field(default_factory=list)
    artifact_changes: list[MaterializationArtifactChange] = Field(default_factory=list)
    ownership_receipts: list[dict[str, object]] = Field(default_factory=list)
    summary: MaterializationOutcomeSummary = Field(
        default_factory=MaterializationOutcomeSummary
    )


class LocalMaterializationExecutionResult(MaterializationOutcome):
    """Local execution result with fields excluded from typed outcome payloads."""

    files: list[Path] = Field(default_factory=list, exclude=True)
    packages: list[ObjectConfigGraphPackageResult] = Field(
        default_factory=list,
        exclude=True,
    )
    post_step_receipts: list[dict[str, object]] = Field(
        default_factory=list,
        exclude=True,
    )


__all__ = [
    "API_PUBLIC_PACKAGE_KIND",
    "API_PUBLIC_PACKAGE_RENDERER_PROFILE",
    "API_RUNTIME_RENDERER_PROFILE",
    "API_SERVICE_PROTOCOL_KIND",
    "API_SERVICE_PROTOCOL_RENDERER_PROFILE",
    "MaterializationArtifactChange",
    "MaterializationArtifactChangeKind",
    "MaterializationArtifactKind",
    "MaterializationConfig",
    "MaterializationEntityMetadata",
    "MaterializationEntityType",
    "LocalMaterializationExecutionResult",
    "MaterializationOutcome",
    "MaterializationOutcomeSummary",
    "MaterializationPackageOutcome",
    "MaterializationPostStep",
    "MaterializationProducerStep",
    "MaterializationProfileInputFormat",
    "MaterializationProfileInputRef",
    "MaterializationSource",
    "MaterializationStageability",
    "ONTOLOGY_DTO_PACKAGE_KIND",
    "ONTOLOGY_DTO_RENDERER_PROFILE",
    "ORM_RUNTIME_RENDERER_PROFILE",
]
