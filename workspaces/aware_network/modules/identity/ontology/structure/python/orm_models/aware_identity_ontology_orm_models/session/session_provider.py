from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.session.session_provider_session_config import SessionProviderSessionConfig


class SessionProvider(ORMModel):
    """
    Generic provider descriptor for Identity session attachments.
    Contract:
    - Provider is not a Service, Environment, Conversation, Goal, Workspace, or
    Attention object.
    - Identity stores provider keys/contracts so actors can discover active
    session capabilities without Identity importing provider domains.
    - Concrete domain behavior remains provider-owned and is reached outside
    Identity through the provider contract.
    """

    # Relationships
    session_provider_session_configs: list[SessionProviderSessionConfig] = Field(default_factory=list)

    # Attributes
    provider_key: str
    provider_kind: str = Field(default="provider")
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    contract_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
