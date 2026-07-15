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


class ExperiencePackageProjectionNodeContract(BaseModel):
    """
    Canonical DTOs for Experience package projection ownership/materialization receipts.
    Ownership:
    - Experience API owns this transport boundary.
    - Experience runtime owns source parsing and projection ownership semantics.
    - Consumers must use this receipt instead of importing Experience materialization
    internals or reconstructing projection references from local source files.
    """

    # Attributes
    name: str
    node_ref: str
    identity_keys: list[str] = Field(default_factory=list)


class ExperiencePackageProjectionConsumerRef(BaseModel):
    # Attributes
    kind: str = Field(
        description="Consumer kind examples: profile_projection, profile_layout_section,\nprofile_view_event_transition, program_port."
    )
    ref: str
    source_path: str | None = Field(default=None)
    required: bool = Field(default=True)
    program_ref: str | None = Field(default=None)
    program_name: str | None = Field(default=None)
    port_key: str | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)


class ExperiencePackageProjectionOwnershipEntry(BaseModel):
    # Attributes
    experience_name: str
    target_projection: str
    source_path: str
    status: str = Field(default="declared")
    branch_id: UUID | None = Field(default=None)
    committed_projection_experience_id: UUID | None = Field(default=None)
    runtime_opgi_id: UUID | None = Field(default=None)
    nodes: list[ExperiencePackageProjectionNodeContract] = Field(default_factory=list)
    consumers: list[ExperiencePackageProjectionConsumerRef] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperiencePackageProjectionOwnershipCatalog(BaseModel):
    # Attributes
    package_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    experience_toml_path: str | None = Field(default=None)
    status: str
    entries: list[ExperiencePackageProjectionOwnershipEntry] = Field(default_factory=list)
    missing_required_projection_refs: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)
