from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class OntologyDatabaseArtifactRef(BaseModel):
    """
    Ontology persistence readiness DTOs.
    Ontology service owns graph DB readiness and any internal Meta persistence
    delegation. Higher service adapters may call this route, but their
    orchestration identity is not part of this lower-level contract.
    """

    # Attributes
    path: str
    hash: str


class OntologyDatabaseArtifactReceipt(BaseModel):
    # Attributes
    ontology_package_id: UUID | None = Field(default=None)
    ontology_manifest_ref: OntologyDatabaseArtifactRef | None = Field(default=None)
    ocg_id: UUID | None = Field(default=None)
    ocg_hash: str | None = Field(default=None)
    ocg_head_commit_id: UUID | None = Field(default=None)
    ocg_lane_branch_id: UUID | None = Field(default=None)
    ocg_lane_projection_hash: str | None = Field(default=None)
    db_schema_registry_ref: OntologyDatabaseArtifactRef | None = Field(default=None)
    db_schema_hash: str | None = Field(default=None)
    db_backend_target: str = Field(default="postgres")
    db_package_kind: str = Field(default="ontology")
    sql_roots: list[str] = Field(default_factory=list)
    ontology_lock_ref: OntologyDatabaseArtifactRef | None = Field(default=None)
    ocg_lane_index_ref: OntologyDatabaseArtifactRef | None = Field(default=None)


class OntologyPersistenceEnsureReadyRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    database_artifact_receipt: OntologyDatabaseArtifactReceipt
    database_url_ref: str | None = Field(default=None)
    boot_policy: str = Field(default="migrate")


class OntologyPersistenceEnsureReadyResponse(BaseModel):
    # Attributes
    status: str
    error: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    ontology_package_id: UUID | None = Field(default=None)
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
