from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_config_class_config import RoleConfigClassConfig
    from aware_meta_ontology_orm_models.class_.class_instance_identity import ClassInstanceIdentity


class RoleClassInstance(ORMModel):
    # Relationships
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None, exclude=True)
    role_config_class_config: RoleConfigClassConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    role_id: UUID = Field(description="Foreign key for Role.role_class_instances")
    class_instance_identity_id: UUID = Field(description="Foreign key for RoleClassInstance.class_instance_identity")
    role_config_class_config_id: UUID = Field(description="Foreign key for RoleClassInstance.role_config_class_config")
