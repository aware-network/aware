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
    from aware_meta_ontology_dto.class_.class_instance_identity import ClassInstanceIdentity


class RoleClassInstance(BaseModel):
    # Relationships
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None)
    role_config_class_config: RoleConfigClassConfig | None = Field(default=None)
