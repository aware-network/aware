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


class MetaRuntimeReadModelProjectionRef(BaseModel):
    """
    Runtime read-model API DTOs for Meta-owned Workspace projection/index truth.
    These DTOs intentionally expose stable read-model facts and opaque handles
    only. Raw Meta runtime contexts and index snapshots stay inside Meta service
    and runtime implementation packages.
    """

    # Attributes
    projection_name: str
    projection_hash: str | None = Field(default=None)
    object_projection_graph_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)


class MetaRuntimeReadModelGraphRef(BaseModel):
    # Attributes
    graph_id: UUID
    graph_role: str
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)


class MetaRuntimeReadModelPackageTiming(BaseModel):
    # Attributes
    package_name: str
    manifest_path: str
    cache_status: str
    cache_miss_reason: str | None = Field(default=None)
    phase_timings_s: JsonObject | None = Field(default=None)


class MetaWorkspaceCommitTruthSummary(BaseModel):
    # Attributes
    summary_source: str | None = Field(default=None)
    revision_count: int = Field(default=0)
    compilation_count: int = Field(default=0)
    materialization_count: int = Field(default=0)
    build_count: int = Field(default=0)
    latest_revision: JsonObject | None = Field(default=None)
    latest_compilation: JsonObject | None = Field(default=None)
    latest_materialization: JsonObject | None = Field(default=None)
    latest_successful_materialization: JsonObject | None = Field(default=None)
    latest_build: JsonObject | None = Field(default=None)
    latest_successful_build: JsonObject | None = Field(default=None)


class MetaRuntimeReadModelRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    repo_root: str | None = Field(default=None)
    aware_root: str | None = Field(default=None)
    required_projection_names: list[str] = Field(default_factory=list)
    force_refresh: bool = Field(default=False)
    include_timings: bool = Field(default=True)
    include_package_timings: bool = Field(default=True)
    include_workspace_commit_truth: bool = Field(default=False)


class MetaRuntimeReadModelResponse(BaseModel):
    # Attributes
    status: str
    actor_id: UUID | None = Field(default=None)
    read_model_version: str | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    repo_root: str | None = Field(default=None)
    aware_root: str | None = Field(default=None)
    required_projection_names: list[str] = Field(default_factory=list)
    projections: list[MetaRuntimeReadModelProjectionRef] = Field(default_factory=list)
    runtime_graphs: list[MetaRuntimeReadModelGraphRef] = Field(default_factory=list)
    source_graphs: list[MetaRuntimeReadModelGraphRef] = Field(default_factory=list)
    cache_status: str | None = Field(default=None)
    provider_duration_s: float | None = Field(default=None)
    phase_timings_s: JsonObject | None = Field(default=None)
    package_timings: list[MetaRuntimeReadModelPackageTiming] = Field(default_factory=list)
    workspace_commit_truth: MetaWorkspaceCommitTruthSummary | None = Field(default=None)
    read_model_handle: str | None = Field(default=None)
    handle_expires_at_unix_ms: int | None = Field(default=None)
    diagnostics: list[str] = Field(default_factory=list)
    error: str | None = Field(default=None)
