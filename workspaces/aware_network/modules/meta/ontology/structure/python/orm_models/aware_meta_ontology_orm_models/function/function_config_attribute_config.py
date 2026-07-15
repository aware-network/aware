from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class FunctionConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    name: str
    position: int = Field(default=0)
    type: FunctionAttributeType
    is_identity_key: bool = Field(default=False)
    identity_key_origin: FunctionIdentityKeyOrigin = Field(default=FunctionIdentityKeyOrigin.standalone)

    # Foreign Keys
    function_config_id: UUID = Field(description="Foreign key for FunctionConfig.function_config_attribute_configs")
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfigAttributeConfig.attribute_config"
    )
