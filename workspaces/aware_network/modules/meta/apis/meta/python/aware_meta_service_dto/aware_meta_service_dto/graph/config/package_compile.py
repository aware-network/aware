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


class MetaObjectConfigGraphPackageDependencyRef(BaseModel):
    """
    Meta-owned ObjectConfigGraph package compile DTOs.
    This surface is the public service/API boundary for asking Meta to produce
    canonical package OCG truth from `.aware` package sources. Callers pass
    workspace/package coordinates and optional dependency graph snapshots;
    Meta Service owns runtime/index/branch context and returns commit-backed
    package evidence.
    """

    # Attributes
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph: JsonObject | None = Field(default=None)


class MetaObjectConfigGraphPackageEnsureRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    aware_toml_path: str
    parent_branch_id: UUID | None = Field(default=None)
    package_branch_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    dependency_refs: list[MetaObjectConfigGraphPackageDependencyRef] = Field(default_factory=list)
    include_object_config_graph: bool = Field(default=False)
    collect_telemetry: bool = Field(default=True)


class MetaObjectConfigGraphPackageEnsureResponse(BaseModel):
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
    dependency_refs: list[MetaObjectConfigGraphPackageDependencyRef] = Field(default_factory=list)
    object_config_graph: JsonObject | None = Field(default=None)
    timings: JsonObject = Field(default_factory=JsonObject)
    telemetry: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)
