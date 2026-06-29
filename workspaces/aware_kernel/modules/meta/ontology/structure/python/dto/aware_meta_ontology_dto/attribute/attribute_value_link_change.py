from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.change.change import Change
    from aware_meta_ontology_dto.attribute.attribute_value_change import AttributeValueChange


class AttributeValueLinkChange(BaseModel):
    """
    Delta-only change node for an AttributeValueLink entity (value tree edge).
    The link identifies the child slot semantically via:
    - role
    - position (LIST/TUPLE/UNION)
    - identity_key (SET/MAPPING)
    This change node targets the concrete AttributeValueLink instance (via FK)
    so commits can be applied deterministically without parsing path strings.
    """

    # Relationships
    change: Change
    child_attribute_value_change: AttributeValueChange | None = Field(default=None)
