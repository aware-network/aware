from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.attention.attention_package import AttentionPackage


class ExperiencePackageAttentionPackage(ORMModel):
    # Relationships
    attention_package: AttentionPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.attention_packages")
    attention_package_id: UUID = Field(
        description="Foreign key for ExperiencePackageAttentionPackage.attention_package"
    )
