from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.attention.attention_package_layout_config import (
        AttentionPackageLayoutConfig,
    )
    from aware_code_ontology_orm_models.package.code_package import CodePackage


class AttentionPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    layout_configs: list[AttentionPackageLayoutConfig] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for AttentionPackage.source_code_package"
    )
