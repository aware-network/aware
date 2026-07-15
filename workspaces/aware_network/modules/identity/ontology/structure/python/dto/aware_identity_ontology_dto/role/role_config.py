from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role_config_class_config import RoleConfigClassConfig
    from aware_identity_ontology_dto.role.role_config_class_config_relationship import RoleConfigClassConfigRelationship
    from aware_meta_ontology_dto.class_.class_config_relationship import ClassConfigRelationship


class RoleConfig(BaseModel):
    # Relationships
    role_config_class_configs: list[RoleConfigClassConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
