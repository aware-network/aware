from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_value import AttributeValue
    from aware_meta_ontology_orm_models.attribute.attribute_value_link_change import AttributeValueLinkChange


class AttributeValueLink(ORMModel):
    """
    Edge in the AttributeValue tree.
    This mirrors AttributeTypeDescriptorLink, but adds `identity_key` for
    non-positional collections:
    - SET: identity_key = fingerprint(element subtree)
    - MAPPING: identity_key = fingerprint(key subtree) (shared by KEY and VALUE)
    """

    # Relationships
    attribute_value_link_changes: list[AttributeValueLinkChange] = Field(default_factory=list, exclude=True)
    child: AttributeValue

    # Attributes
    role: AttributeTypeDescriptorRole
    position: int | None = Field(default=None)
    identity_key: str | None = Field(default=None)

    # Foreign Keys
    attribute_value_id: UUID = Field(description="Foreign key for AttributeValue.child_links")
    child_id: UUID | None = Field(default=None, description="Foreign key for AttributeValueLink.child")
