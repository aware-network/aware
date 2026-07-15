from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


class ProjectionExperienceGraphIdentityProfileExemplar(ORMModel):
    """
    One commit-backed exemplar row for a graph-identity profile.
    Contract:
    - Image bytes are uploaded out-of-band (data-plane).
    - Commits reference StorageBlob metadata only.
    - Future content/location specialization may aggregate on top of this row.
    """

    # Relationships
    image: StorageBlob | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)

    # Foreign Keys
    projection_experience_graph_identity_profile_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityProfile.exemplars"
    )
    image_id: UUID | None = Field(
        default=None, description="Foreign key for ProjectionExperienceGraphIdentityProfileExemplar.image"
    )
