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
    from aware_meta_ontology_dto.function.function_config import FunctionConfig


class RoleConfigClassConfigFunctionConfig(BaseModel):
    # Relationships
    function_config: FunctionConfig | None = Field(default=None)

    # Attributes
    access_level: AccessLevelType
