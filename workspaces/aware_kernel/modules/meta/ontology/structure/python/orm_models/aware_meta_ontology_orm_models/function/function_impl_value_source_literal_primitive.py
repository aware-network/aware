from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.primitive.primitive_config import PrimitiveConfig


class FunctionImplValueSourceLiteralPrimitive(ORMModel):
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

    # Foreign Keys
    function_impl_value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_literal_primitive"
    )
    primitive_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceLiteralPrimitive.primitive_config"
    )
