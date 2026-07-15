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
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig


class RoleConfigClassConfigFunctionConfig(ORMModel):
    # Relationships
    function_config: FunctionConfig | None = Field(default=None, exclude=True)

    # Attributes
    access_level: AccessLevelType

    # Foreign Keys
    role_config_class_config_id: UUID = Field(
        description="Foreign key for RoleConfigClassConfig.role_config_class_config_function_configs"
    )
    function_config_id: UUID = Field(description="Foreign key for RoleConfigClassConfigFunctionConfig.function_config")
