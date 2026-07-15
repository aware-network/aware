from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ProjectionExperienceGraphIdentityProfileExemplar(BaseModel):
    """
    One commit-backed exemplar row for a graph-identity profile.
    Contract:
    - Image bytes are uploaded out-of-band (data-plane).
    - Commits reference StorageBlob metadata only.
    - Future content/location specialization may aggregate on top of this row.
    """

    # Relationships
    image: StorageBlob | None = Field(default=None)

    # Attributes
    key: str
    label: str | None = Field(default=None)
    prompt_hint: str | None = Field(default=None)
    note: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
