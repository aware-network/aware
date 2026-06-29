from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_service_dto.graph.config.package_compile import MetaObjectConfigGraphPackageDependencyRef


class MetaCompletenessDiagnostic(BaseModel):
    """
    Meta-owned OCG/OPG completeness diagnostics DTOs.
    Consumers use this surface through Meta API/SDK. Meta runtime internals stay
    behind services/meta and are not imported by SDK consumers.
    """

    # Attributes
    severity: str
    code: str
    message: str
    source_path: str | None = Field(default=None)


class MetaCompletenessAnalyzeRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    package_root: str
    aware_toml_path: str | None = Field(default=None)
    source_files: list[str] = Field(default_factory=list)
    dependency_refs: list[MetaObjectConfigGraphPackageDependencyRef] = Field(default_factory=list)
    completeness_diagnostics: bool = Field(default=True)
    diagnostic_severity: str = Field(default="warning")
    include_object_config_graph: bool = Field(default=False)


class MetaCompletenessAnalyzeResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    aware_toml_path: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    diagnostics: list[MetaCompletenessDiagnostic] = Field(default_factory=list)
    changed_source_files: list[str] = Field(default_factory=list)
    affected_object_config_graph_keys: list[str] = Field(default_factory=list)
    affected_node_keys: list[str] = Field(default_factory=list)
    graph_count: int = Field(default=0)
    node_count: int = Field(default=0)
    class_count: int = Field(default=0)
    enum_count: int = Field(default=0)
    function_count: int = Field(default=0)
    relationship_count: int = Field(default=0)
    required_materializations: list[str] = Field(default_factory=list)
    object_config_graph: JsonObject | None = Field(default=None)
    error: str | None = Field(default=None)
