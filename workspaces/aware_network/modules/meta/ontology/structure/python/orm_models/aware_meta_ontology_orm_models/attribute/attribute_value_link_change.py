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
    from aware_meta_ontology_orm_models.attribute.attribute_value_change import AttributeValueChange


class AttributeValueLinkChange(ORMModel):
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

    # Foreign Keys
    attribute_value_link_id: UUID = Field(description="Foreign key for AttributeValueLink.attribute_value_link_changes")
    attribute_value_change_id: UUID = Field(
        description="Foreign key for AttributeValueChange.attribute_value_link_changes"
    )
    change_id: UUID | None = Field(default=None, description="Foreign key for AttributeValueLinkChange.change")
    child_attribute_value_change_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeValueLinkChange.child_attribute_value_change"
    )
