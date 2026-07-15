from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class MetaDatabaseArtifactRef(BaseModel):
    """
    Meta persistence DB readiness DTOs.
    Meta owns OCG-backed DB readiness behind this generated API surface.
    Higher orchestration adapters may decide when this route is called, but
    Environment identity is not part of this lower-level contract.
    """

    # Attributes
    path: str
    hash: str


class MetaDatabaseArtifactReceipt(BaseModel):
    # Attributes
    meta_package_id: UUID | None = Field(default=None)
    meta_manifest_ref: MetaDatabaseArtifactRef | None = Field(default=None)
    ocg_id: UUID
    ocg_hash: str
    ocg_head_commit_id: UUID | None = Field(default=None)
    ocg_lane_branch_id: UUID | None = Field(default=None)
    ocg_lane_projection_hash: str | None = Field(default=None)
    db_schema_registry_ref: MetaDatabaseArtifactRef
    db_schema_hash: str
    db_backend_target: str = Field(default="postgres")
    db_package_kind: str = Field(default="ontology")
    sql_roots: list[str] = Field(default_factory=list)
    meta_lock_ref: MetaDatabaseArtifactRef | None = Field(default=None)
    ocg_lane_index_ref: MetaDatabaseArtifactRef | None = Field(default=None)


class MetaPersistenceEnsureDatabaseReadyRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    database_artifact_receipt: MetaDatabaseArtifactReceipt
    database_url_ref: str | None = Field(default=None)
    boot_policy: str = Field(default="migrate")


class MetaPersistenceEnsureDatabaseReadyResponse(BaseModel):
    # Attributes
    status: str
    error: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    meta_package_id: UUID | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    db_schema_hash: str | None = Field(default=None)
    db_schema_registry_hash: str | None = Field(default=None)
    installed: bool = Field(default=False)
    migrated: bool = Field(default=False)
    marker_ocg_hash: str | None = Field(default=None)
    marker_head_commit_id: UUID | None = Field(default=None)
    sql_root_count: int = Field(default=0)
    step_count: int = Field(default=0)
    seeded_ocg_config: bool = Field(default=False)
    hydrated_domain_lanes: list[str] = Field(default_factory=list)
