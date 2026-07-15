from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.primitive.code_primitive_type import CodePrimitiveType


class PrimitiveConfig(ORMModel):
    # Relationships
    primitive_type: CodePrimitiveType

    # Foreign Keys
    primitive_type_id: UUID | None = Field(default=None, description="Foreign key for PrimitiveConfig.primitive_type")
