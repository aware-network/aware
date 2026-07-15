from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.session.session_config import SessionConfig


class SessionProviderSessionConfig(BaseModel):
    """
    Provider capability binding to one Identity SessionConfig.
    Contract:
    - Parent constructor is SessionProvider.
    - Points to Identity SessionConfig vocabulary.
    - Does not create a concrete provider session and does not grant actor
    access.
    """

    # Relationships
    session_config: SessionConfig | None = Field(default=None)

    # Attributes
    config_key: str
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    provider_contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
