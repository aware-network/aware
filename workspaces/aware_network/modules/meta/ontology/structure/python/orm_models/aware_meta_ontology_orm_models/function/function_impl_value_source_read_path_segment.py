from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class FunctionImplValueSourceReadPathSegment(ORMModel):
    """
    Ordered typed member segment for `FunctionImplValueSourceReadPath`.
    Contract:
    - `attribute_config` is compiler-resolved from the previous class-valued hop.
    - `position` is compiler-owned path order.
    """

    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    position: int

    # Foreign Keys
    function_impl_value_source_read_path_id: UUID = Field(
        description="Foreign key for FunctionImplValueSourceReadPath.segments"
    )
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceReadPathSegment.attribute_config"
    )
