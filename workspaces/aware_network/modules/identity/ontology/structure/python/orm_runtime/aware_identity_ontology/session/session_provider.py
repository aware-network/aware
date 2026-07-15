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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.session.session_provider_session_config import SessionProviderSessionConfig


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

    @classmethod
    async def register(
        cls,
        provider_key: str,
        provider_kind: str = "provider",
        title: str | None = None,
        status: str = "active",
        contract_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> SessionProvider:
        """
        Register one provider-neutral session capability descriptor.

        Contract:
        - Stable identity is derived from `provider_key`.
        - This does not grant actors access and does not activate provider
          behavior.
        """

        payload = {
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "title": title,
            "status": status,
            "contract_ref": contract_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="register", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionProvider):
            return value
        return SessionProvider.validate_invocation_value(value)

    async def bind_session_config(
        self,
        config_key: str,
        session_config_id: UUID,
        title: str | None = None,
        status: str = "active",
        provider_contract_ref: str | None = None,
        selection_policy: str = "contract_required",
        metadata_json: JsonObject | None = {},
    ) -> SessionProviderSessionConfig:
        """
        Declare that this provider can attach concrete provider sessions under
        one Identity SessionConfig.

        Contract:
        - This is provider/config eligibility vocabulary only.
        - A concrete attachment is `SessionProviderSession` under `Session`.
        """

        payload = {
            "config_key": config_key,
            "session_config_id": session_config_id,
            "title": title,
            "status": status,
            "provider_contract_ref": provider_contract_ref,
            "selection_policy": selection_policy,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_session_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session_provider_session_config import SessionProviderSessionConfig

        if isinstance(value, SessionProviderSessionConfig):
            return value
        return SessionProviderSessionConfig.validate_invocation_value(value)


class SessionProviderRegisterInput(BaseModel):
    provider_key: str
    provider_kind: str = Field(default="provider")
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    contract_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionProviderRegisterOutput(BaseModel):
    value: SessionProvider


class SessionProviderBindSessionConfigInput(BaseModel):
    config_key: str
    session_config_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    provider_contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionProviderBindSessionConfigOutput(BaseModel):
    value: SessionProviderSessionConfig


FUNCTIONS = {
    "SessionProvider": {
        "register": {
            "canonical": {
                "name": "register",
                "description": "Register one provider-neutral session capability descriptor.\n\nContract:\n- Stable identity is derived from `provider_key`.\n- This does not grant actors access and does not activate provider\n  behavior.",
                "is_constructor": True,
            },
            "input": SessionProviderRegisterInput,
            "output": SessionProviderRegisterOutput,
        },
        "bind_session_config": {
            "canonical": {
                "name": "bind_session_config",
                "description": "Declare that this provider can attach concrete provider sessions under\none Identity SessionConfig.\n\nContract:\n- This is provider/config eligibility vocabulary only.\n- A concrete attachment is `SessionProviderSession` under `Session`.",
                "is_constructor": False,
            },
            "input": SessionProviderBindSessionConfigInput,
            "output": SessionProviderBindSessionConfigOutput,
        },
    },
}

__all__ = [
    "SessionProvider",
    "SessionProviderRegisterInput",
    "SessionProviderRegisterOutput",
    "SessionProviderBindSessionConfigInput",
    "SessionProviderBindSessionConfigOutput",
    "FUNCTIONS",
]
