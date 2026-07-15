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

if TYPE_CHECKING:
    from aware_economy_ontology.wallet.wallet import Wallet
    from aware_identity_ontology.identity.identity import Identity


class FinanceEntity(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)
    wallet: Wallet | None = Field(default=None, exclude=True)

    # Attributes
    role_key: str = Field(default="primary")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for FinanceEntity.identity")
    wallet_id: UUID | None = Field(default=None, description="Foreign key for FinanceEntity.wallet")

    @classmethod
    async def build(cls, identity_id: UUID, wallet_id: UUID, role_key: str = "primary") -> FinanceEntity:
        """
        Creates a FinanceEntity for the given identity.

        Receipt: FinanceEntity(id=stable(identity_id), role_key=role_key) referencing the deterministic
        Wallet id.

        Notes:
        - This constructor is finance_entity-lane only (it does not create wallet-lane commits).
        - Wallet objects are created via Wallet.build in the `wallet` lane (separate receipt).
        - It does not mutate the Identity.
        - role_key declares the wallet purpose for v0 readiness; `primary` is the default person/agent
        wallet role.

        Validation:
        - wallet_id must match the deterministic wallet id derived from identity_id + role_key custody
        material (v0 anti-footgun).
        """

        payload = {"identity_id": identity_id, "wallet_id": wallet_id, "role_key": role_key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FinanceEntity):
            return value
        return FinanceEntity.validate_invocation_value(value)


class FinanceEntityBuildInput(BaseModel):
    identity_id: UUID
    wallet_id: UUID
    role_key: str = Field(default="primary")


class FinanceEntityBuildOutput(BaseModel):
    value: FinanceEntity


FUNCTIONS = {
    "FinanceEntity": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a FinanceEntity for the given identity.\n\nReceipt: FinanceEntity(id=stable(identity_id), role_key=role_key) referencing the deterministic Wallet id.\n\nNotes:\n- This constructor is finance_entity-lane only (it does not create wallet-lane commits).\n- Wallet objects are created via Wallet.build in the `wallet` lane (separate receipt).\n- It does not mutate the Identity.\n- role_key declares the wallet purpose for v0 readiness; `primary` is the default person/agent wallet role.\n\nValidation:\n- wallet_id must match the deterministic wallet id derived from identity_id + role_key custody material (v0 anti-footgun).",
                "is_constructor": True,
            },
            "input": FinanceEntityBuildInput,
            "output": FinanceEntityBuildOutput,
        },
    },
}

__all__ = [
    "FinanceEntity",
    "FinanceEntityBuildInput",
    "FinanceEntityBuildOutput",
    "FUNCTIONS",
]
