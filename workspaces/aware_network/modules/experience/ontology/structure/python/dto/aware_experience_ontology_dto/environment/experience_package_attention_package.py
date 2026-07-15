from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.attention.attention_package import AttentionPackage


class ExperiencePackageAttentionPackage(BaseModel):
    # Relationships
    attention_package: AttentionPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
