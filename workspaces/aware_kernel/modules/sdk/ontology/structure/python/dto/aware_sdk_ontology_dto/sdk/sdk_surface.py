from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_surface_method import SdkSurfaceMethod


class SdkSurface(BaseModel):
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
