from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.change.change import Change
    from aware_meta_ontology_orm_models.attribute.attribute_value_link_change import AttributeValueLinkChange


class AttributeValueChange(ORMModel):
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

    # Foreign Keys
    attribute_value_id: UUID = Field(description="Foreign key for AttributeValue.attribute_value_changes")
    change_id: UUID | None = Field(default=None, description="Foreign key for AttributeValueChange.change")
