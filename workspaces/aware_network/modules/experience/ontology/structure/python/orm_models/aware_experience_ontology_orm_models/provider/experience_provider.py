from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.provider.experience_provider_action_binding import (
        ExperienceProviderActionBinding,
    )


class ExperienceProvider(ORMModel):
    """
    Experience-owned provider slot.
    Contract:
    - Experience declares which provider slots can fulfill its public actions.
    - Provider ontologies bind concrete fulfillment to this slot later.
    - This object intentionally does not reference provider-owned implementation classes.
    """

    # Relationships
    action_bindings: list[ExperienceProviderActionBinding] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_id: UUID = Field(description="Foreign key for ProjectionExperience.providers")
