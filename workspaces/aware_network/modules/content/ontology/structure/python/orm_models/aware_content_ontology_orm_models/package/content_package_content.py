from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.content.content import Content


class ContentPackageContent(ORMModel):
    """
    Package-owned Content membership.
    Contract:
    - ContentPackageContent is membership/projection metadata only.
    - Content remains the multimodal content truth owner.
    - `relative_path` is a materialization coordinate for checkouts, not the
    content identity.
    """

    # Relationships
    content: Content | None = Field(default=None, exclude=True, description="Association target reference to Content")

    # Attributes
    relative_path: str
    content_role: str = Field(default="content")
    position: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
    receipt_payload: JsonObject | None = Field(default=None)

    # Foreign Keys
    content_id: UUID = Field(description="Join FK to Content")
    content_package_id: UUID = Field(description="Join FK to ContentPackage")
