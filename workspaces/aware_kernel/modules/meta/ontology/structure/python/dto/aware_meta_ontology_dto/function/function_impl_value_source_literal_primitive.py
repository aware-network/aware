from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology_dto.primitive.primitive_config import PrimitiveConfig


class FunctionImplValueSourceLiteralPrimitive(BaseModel):
    """
    Deterministic typed primitive literal payload for function value sources.
    Contract:
    - Literal identity is anchored by `primitive_config`.
    - `value` must be compatible with the selected primitive type.
    """

    # Relationships
    primitive_config: PrimitiveConfig

    # Attributes
    value: Json
