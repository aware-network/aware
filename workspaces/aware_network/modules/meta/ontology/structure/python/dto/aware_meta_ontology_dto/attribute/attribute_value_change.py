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
    from aware_meta_ontology_dto.attribute.attribute_value_link_change import AttributeValueLinkChange


class AttributeValueChange(BaseModel):
    """
    Delta-only change node for an AttributeValue entity (value tree node).
    This mirrors the canonical Attribute.value_root tree:
    AttributeChange
    -> value_root_change (AttributeValueChange)
    -> attribute_value_link_changes (AttributeValueLinkChange[])
    -> child_attribute_value_change (AttributeValueChange)
    """

    # Relationships
    change: Change
    attribute_value_link_changes: list[AttributeValueLinkChange] = Field(default_factory=list)
