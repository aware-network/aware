from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_config_class_config import RoleConfigClassConfig
    from aware_identity_ontology_orm_models.role.role_config_class_config_relationship import (
        RoleConfigClassConfigRelationship,
    )
    from aware_meta_ontology_orm_models.class_.class_config_relationship import ClassConfigRelationship


class RoleConfig(ORMModel):
    # Relationships
    role_config_class_configs: list[RoleConfigClassConfig] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str

    # Edges
    role_config_class_config_relationships: list[RoleConfigClassConfigRelationship] = Field(
        default_factory=list, exclude=True, description="Edge association helper for class_config_relationships"
    )

    @property
    def class_config_relationships(self) -> list[ClassConfigRelationship]:
        return [
            edge.class_config_relationship
            for edge in self.role_config_class_config_relationships
            if edge.class_config_relationship is not None
        ]
