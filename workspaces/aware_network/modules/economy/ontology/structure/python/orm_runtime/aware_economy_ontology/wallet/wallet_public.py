from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
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
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.escrow.escrow import Escrow


class WalletPublic(ORMModel):
    # Relationships
    escrows: list[Escrow] = Field(default_factory=list, exclude=True)

    # Attributes
    address: str
    nonce_counter: int = Field(default=0)
    public_key: str

    @classmethod
    async def build(cls, address: str, public_key: str) -> WalletPublic:
        """
        Creates a wallet public record.

        Receipt: WalletPublic (address + public_key).
        """

        payload = {"address": address, "public_key": public_key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WalletPublic):
            return value
        return WalletPublic.validate_invocation_value(value)

    async def lock_escrow(
        self,
        smart_contract_reservation_id: UUID,
        op_nonce: int,
        coin_id: UUID,
        locked_amount: Annotated[Decimal, DecimalWire()],
        description: str | None = None,
    ) -> Escrow:
        """
        Locks funds by creating an escrow under this wallet public key.

        Receipt: Escrow(status=locked) + WalletPublic.escrows link (commit-backed).
        """

        payload = {
            "smart_contract_reservation_id": smart_contract_reservation_id,
            "op_nonce": op_nonce,
            "coin_id": coin_id,
            "locked_amount": locked_amount,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="lock_escrow", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.escrow.escrow import Escrow

        if isinstance(value, Escrow):
            return value
        return Escrow.validate_invocation_value(value)


class WalletPublicBuildInput(BaseModel):
    address: str
    public_key: str


class WalletPublicBuildOutput(BaseModel):
    value: WalletPublic


class WalletPublicLockEscrowInput(BaseModel):
    smart_contract_reservation_id: UUID
    op_nonce: int
    coin_id: UUID
    locked_amount: Annotated[Decimal, DecimalWire()]
    description: str | None = Field(default=None)


class WalletPublicLockEscrowOutput(BaseModel):
    value: Escrow


FUNCTIONS = {
    "WalletPublic": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a wallet public record.\n\nReceipt: WalletPublic (address + public_key).",
                "is_constructor": True,
            },
            "input": WalletPublicBuildInput,
            "output": WalletPublicBuildOutput,
        },
        "lock_escrow": {
            "canonical": {
                "name": "lock_escrow",
                "description": "Locks funds by creating an escrow under this wallet public key.\n\nReceipt: Escrow(status=locked) + WalletPublic.escrows link (commit-backed).",
                "is_constructor": False,
            },
            "input": WalletPublicLockEscrowInput,
            "output": WalletPublicLockEscrowOutput,
        },
    },
}

__all__ = [
    "WalletPublic",
    "WalletPublicBuildInput",
    "WalletPublicBuildOutput",
    "WalletPublicLockEscrowInput",
    "WalletPublicLockEscrowOutput",
    "FUNCTIONS",
]
