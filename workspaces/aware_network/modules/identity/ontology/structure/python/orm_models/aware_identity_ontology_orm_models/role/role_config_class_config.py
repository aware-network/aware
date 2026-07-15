from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.role.role_enums import AccessLevelType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_config_class_config_function_config import (
        RoleConfigClassConfigFunctionConfig,
    )
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class RoleConfigClassConfig(ORMModel):
    # Relationships
    role_config_class_config_function_configs: list[RoleConfigClassConfigFunctionConfig] = Field(
        default_factory=list, exclude=True
    )
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_level: AccessLevelType

    # Foreign Keys
    role_config_id: UUID = Field(description="Foreign key for RoleConfig.role_config_class_configs")
    class_config_id: UUID = Field(description="Foreign key for RoleConfigClassConfig.class_config")
