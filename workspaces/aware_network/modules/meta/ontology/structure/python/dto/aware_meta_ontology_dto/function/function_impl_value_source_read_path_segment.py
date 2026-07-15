from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class FunctionImplValueSourceReadPathSegment(BaseModel):
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
