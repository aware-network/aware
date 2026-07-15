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
    from aware_environment_ontology_orm_models.environment.environment_provider_grant import EnvironmentProviderGrant


class EnvironmentProvider(ORMModel):
    """
    Provider-neutral Environment slot.
    Contract:
    - Environment declares approved provider slots without importing Experience.
    - Experiences bind to these slots in the Experience-owned provider rail.
    - Concrete service fulfillment remains outside Environment ontology.
    """

    # Relationships
    grants: list[EnvironmentProviderGrant] = Field(default_factory=list)

    # Attributes
    contract_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.providers")
