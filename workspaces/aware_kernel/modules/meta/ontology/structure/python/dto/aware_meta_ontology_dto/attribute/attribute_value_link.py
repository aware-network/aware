from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_value import AttributeValue
    from aware_meta_ontology_dto.attribute.attribute_value_link_change import AttributeValueLinkChange


class AttributeValueLink(BaseModel):
    """
    Edge in the AttributeValue tree.
    This mirrors AttributeTypeDescriptorLink, but adds `identity_key` for
    non-positional collections:
    - SET: identity_key = fingerprint(element subtree)
    - MAPPING: identity_key = fingerprint(key subtree) (shared by KEY and VALUE)
    """

    # Relationships
    attribute_value_link_changes: list[AttributeValueLinkChange] = Field(default_factory=list)
    child: AttributeValue

    # Attributes
    role: AttributeTypeDescriptorRole
    position: int | None = Field(default=None)
    identity_key: str | None = Field(default=None)
