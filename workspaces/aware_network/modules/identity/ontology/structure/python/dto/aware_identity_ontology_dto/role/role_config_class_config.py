from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.role.role_enums import AccessLevelType

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role_config_class_config_function_config import (
        RoleConfigClassConfigFunctionConfig,
    )
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class RoleConfigClassConfig(BaseModel):
    # Relationships
    role_config_class_config_function_configs: list[RoleConfigClassConfigFunctionConfig] = Field(default_factory=list)
    class_config: ClassConfig | None = Field(default=None)

    # Attributes
    access_level: AccessLevelType
