from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class FunctionConfigAttributeConfig(BaseModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    name: str
    position: int = Field(default=0)
    type: FunctionAttributeType
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)
