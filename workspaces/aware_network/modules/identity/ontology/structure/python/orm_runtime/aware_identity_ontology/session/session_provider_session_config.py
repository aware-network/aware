from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.session.session_config import SessionConfig


class SessionProviderSessionConfig(ORMModel):
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

    # Foreign Keys
    session_provider_id: UUID = Field(description="Foreign key for SessionProvider.session_provider_session_configs")
    session_config_id: UUID = Field(description="Foreign key for SessionProviderSessionConfig.session_config")

    @classmethod
    async def create_via_session_provider(
        cls,
        session_provider_id: UUID,
        config_key: str,
        session_config_id: UUID,
        title: str | None = None,
        status: str = "active",
        provider_contract_ref: str | None = None,
        selection_policy: str = "contract_required",
        metadata_json: JsonObject | None = {},
    ) -> SessionProviderSessionConfig:
        """
        Bind one provider capability to one Identity SessionConfig.

        Contract:
        - Stable identity is `(session_provider_id, config_key,
          session_config_id)`.
        - This is provider capability eligibility only.
        """

        payload = {
            "session_provider_id": session_provider_id,
            "config_key": config_key,
            "session_config_id": session_config_id,
            "title": title,
            "status": status,
            "provider_contract_ref": provider_contract_ref,
            "selection_policy": selection_policy,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_session_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionProviderSessionConfig):
            return value
        return SessionProviderSessionConfig.validate_invocation_value(value)


class SessionProviderSessionConfigCreateViaSessionProviderInput(BaseModel):
    session_provider_id: UUID = Field(description="Foreign key for SessionProvider.session_provider_session_configs")
    config_key: str
    session_config_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    provider_contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionProviderSessionConfigCreateViaSessionProviderOutput(BaseModel):
    value: SessionProviderSessionConfig


FUNCTIONS = {
    "SessionProviderSessionConfig": {
        "create_via_session_provider": {
            "canonical": {
                "name": "create_via_session_provider",
                "description": "Bind one provider capability to one Identity SessionConfig.\n\nContract:\n- Stable identity is `(session_provider_id, config_key,\n  session_config_id)`.\n- This is provider capability eligibility only.",
                "is_constructor": True,
            },
            "input": SessionProviderSessionConfigCreateViaSessionProviderInput,
            "output": SessionProviderSessionConfigCreateViaSessionProviderOutput,
        },
    },
}

__all__ = [
    "SessionProviderSessionConfig",
    "SessionProviderSessionConfigCreateViaSessionProviderInput",
    "SessionProviderSessionConfigCreateViaSessionProviderOutput",
    "FUNCTIONS",
]
