from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config import LayoutConfig


class AttentionPackageLayoutConfig(ORMModel):
    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)

    # Foreign Keys
    attention_package_id: UUID = Field(description="Foreign key for AttentionPackage.layout_configs")
    layout_config_id: UUID = Field(description="Foreign key for AttentionPackageLayoutConfig.layout_config")
