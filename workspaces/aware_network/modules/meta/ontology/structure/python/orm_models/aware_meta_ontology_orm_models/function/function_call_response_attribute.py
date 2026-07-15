from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute import Attribute


class FunctionCallResponseAttribute(ORMModel):
    # Relationships
    attribute: Attribute = Field(description="Association target reference to Attribute")

    # Attributes
    position: int

    # Foreign Keys
    attribute_id: UUID | None = Field(default=None, description="Join FK to Attribute")
    function_call_response_id: UUID = Field(description="Join FK to FunctionCallResponse")
