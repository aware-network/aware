from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class OntologyObjectConfigGraphPackageDependencyRef(BaseModel):
    """
    Ontology-owned ObjectConfigGraph package ensure DTOs.
    This is the public boundary for asking Ontology service to establish OCG
    package truth from ontology sources. Meta may perform commit mechanics
    internally, but the service contract remains Ontology-owned.
    """

    # Attributes
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph: JsonObject | None = Field(default=None)


class OntologyObjectConfigGraphPackageEnsureRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    aware_toml_path: str
    parent_branch_id: UUID | None = Field(default=None)
    package_branch_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    dependency_refs: list[OntologyObjectConfigGraphPackageDependencyRef] = Field(default_factory=list)
    include_object_config_graph: bool = Field(default=False)
    collect_telemetry: bool = Field(default=True)


class OntologyObjectConfigGraphPackageEnsureResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    aware_toml_path: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    package_branch_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    code_package_commit_id: UUID | None = Field(default=None)
    code_package_head_commit_id: UUID | None = Field(default=None)
    code_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_hash: str | None = Field(default=None)
    object_config_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_head_commit_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    object_config_graph_package_commit_id: UUID | None = Field(default=None)
    object_config_graph_package_head_commit_id: UUID | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    owned_file_paths: list[str] = Field(default_factory=list)
    dependency_refs: list[OntologyObjectConfigGraphPackageDependencyRef] = Field(default_factory=list)
    object_config_graph: JsonObject | None = Field(default=None)
    timings: JsonObject = Field(default_factory=JsonObject)
    telemetry: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)
