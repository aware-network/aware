from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ExperienceGraphIdentityProfileExemplar(BaseModel):
    """
    Canonical Experience profile read/query DTOs (transport-layer, ontology agnostic).
    SSOT: `experience-service-dto` generated from this `.aware` contract.
    This package sits between later Experience service-host operations and
    consumers such as Perception. Runtime-local shims may re-export these DTOs
    for compatibility, but schema ownership remains here.
    """

    # Attributes
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)


class ExperienceGraphIdentityProfile(BaseModel):
    # Attributes
    graph_identity_ref: str
    review_label: str
    resolution_prompts: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    exemplars: list[ExperienceGraphIdentityProfileExemplar] = Field(default_factory=list)


class ExperienceGraphIdentityProfileCatalogReadRequest(BaseModel):
    # Attributes
    operation: str = Field(default="read_graph_identity_profile_catalog")
    experience_name: str
    graph_name: str


class ExperienceGraphIdentityProfileCatalogReadResponse(BaseModel):
    # Attributes
    operation: str = Field(default="read_graph_identity_profile_catalog")
    experience_name: str
    graph_name: str
    catalog_revision: str | None = Field(default=None)
    profiles: list[ExperienceGraphIdentityProfile] = Field(default_factory=list)


class ExperienceGraphIdentityProfileReadRequest(BaseModel):
    # Attributes
    operation: str = Field(default="read_graph_identity_profile")
    experience_name: str
    graph_name: str
    graph_identity_refs: list[str] = Field(default_factory=list)


class ExperienceGraphIdentityProfileReadResponse(BaseModel):
    # Attributes
    operation: str = Field(default="read_graph_identity_profile")
    experience_name: str
    graph_name: str
    catalog_revision: str | None = Field(default=None)
    profiles: list[ExperienceGraphIdentityProfile] = Field(default_factory=list)
