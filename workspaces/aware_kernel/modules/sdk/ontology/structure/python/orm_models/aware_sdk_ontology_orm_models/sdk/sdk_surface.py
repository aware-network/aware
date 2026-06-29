from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_sdk_ontology_orm_models.sdk.sdk_surface_method import SdkSurfaceMethod


class SdkSurface(ORMModel):
    """
    SDK conceptual surface truth.
    A surface groups stable SDK methods around one product concept. It is not a
    CLI command and does not replace API endpoint truth; CLI, Skill, and other
    renderers project from surface methods.
    """

    # Relationships
    methods: list[SdkSurfaceMethod] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.surfaces")
