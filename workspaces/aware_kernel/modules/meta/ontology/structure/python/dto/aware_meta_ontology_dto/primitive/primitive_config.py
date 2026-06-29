from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_code_ontology_dto.primitive.code_primitive_type import CodePrimitiveType


class PrimitiveConfig(BaseModel):
    # Relationships
    primitive_type: CodePrimitiveType
