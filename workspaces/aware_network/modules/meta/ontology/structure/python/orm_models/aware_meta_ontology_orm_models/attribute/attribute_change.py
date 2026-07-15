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


class AttributeChange(ORMModel):
    # Relationships
    change: Change
    value_root_change: AttributeValueChange | None = Field(
        default=None, description="Canonical descriptor-driven value tree change (root node)."
    )

    # Foreign Keys
    class_instance_change_id: UUID = Field(description="Foreign key for ClassInstanceChange.attribute_changes")
    attribute_id: UUID = Field(description="Foreign key for Attribute.attribute_changes")
    change_id: UUID | None = Field(default=None, description="Foreign key for AttributeChange.change")
    value_root_change_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeChange.value_root_change"
    )
