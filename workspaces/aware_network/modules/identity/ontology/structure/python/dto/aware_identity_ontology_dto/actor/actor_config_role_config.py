from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role_config import RoleConfig


class ActorConfigRoleConfig(BaseModel):
    """RoleConfig eligibility edge under an Identity ActorConfig."""

    # Relationships
    role_config: RoleConfig | None = Field(default=None)
