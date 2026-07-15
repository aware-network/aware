from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig


class ActorConfigRoleConfig(ORMModel):
    """RoleConfig eligibility edge under an Identity ActorConfig."""

    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Foreign Keys
    actor_config_id: UUID = Field(description="Foreign key for ActorConfig.role_configs")
    role_config_id: UUID = Field(description="Foreign key for ActorConfigRoleConfig.role_config")
