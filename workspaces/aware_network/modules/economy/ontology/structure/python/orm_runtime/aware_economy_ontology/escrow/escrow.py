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

# Economy Ontology
from aware_economy_ontology.escrow.escrow_enums import EscrowStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin


class Escrow(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    escrow_hash: str
    locked_amount: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    signature: str
    smart_contract_reservation_id: UUID
    status: EscrowStatus = Field(default=EscrowStatus.locked)

    # Foreign Keys
    wallet_public_id: UUID = Field(description="Foreign key for WalletPublic.escrows")
    coin_id: UUID = Field(description="Foreign key for Escrow.coin")

    async def release(self) -> Escrow:
        """
        Releases a locked escrow after reservation settlement/cancelation.

        Receipt: Escrow(status=completed).
        """

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="release", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Escrow):
            return value
        return Escrow.validate_invocation_value(value)

    async def release_for_reservation_status(self, reservation_id: UUID, reservation_status: str) -> Escrow:
        """
        Releases a locked escrow using a smart-contract reservation lifecycle receipt.

        Receipt: Escrow(status=completed) when reservation_id matches and reservation_status is
        terminal/releasable.
        """

        payload = {"reservation_id": reservation_id, "reservation_status": reservation_status}
        result = await invoke_instance(orm_model=self, function_name="release_for_reservation_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Escrow):
            return value
        return Escrow.validate_invocation_value(value)

    @classmethod
    async def create_via_wallet_public(
        cls,
        wallet_public_id: UUID,
        smart_contract_reservation_id: UUID,
        op_nonce: int,
        coin_id: UUID,
        locked_amount: Annotated[Decimal, DecimalWire()],
        description: str | None = None,
    ) -> Escrow:
        """
        Creates a new escrow record.

        Receipt: Escrow(status=locked) linked to SmartContractReservation + WalletPublic, with
        hash/signature computed by handler.
        """

        payload = {
            "wallet_public_id": wallet_public_id,
            "smart_contract_reservation_id": smart_contract_reservation_id,
            "op_nonce": op_nonce,
            "coin_id": coin_id,
            "locked_amount": locked_amount,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_wallet_public", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Escrow):
            return value
        return Escrow.validate_invocation_value(value)


class EscrowReleaseInput(BaseModel):
    pass


class EscrowReleaseOutput(BaseModel):
    value: Escrow


class EscrowReleaseForReservationStatusInput(BaseModel):
    reservation_id: UUID
    reservation_status: str


class EscrowReleaseForReservationStatusOutput(BaseModel):
    value: Escrow


class EscrowCreateViaWalletPublicInput(BaseModel):
    wallet_public_id: UUID = Field(description="Foreign key for WalletPublic.escrows")
    smart_contract_reservation_id: UUID
    op_nonce: int
    coin_id: UUID
    locked_amount: Annotated[Decimal, DecimalWire()]
    description: str | None = Field(default=None)


class EscrowCreateViaWalletPublicOutput(BaseModel):
    value: Escrow


FUNCTIONS = {
    "Escrow": {
        "release": {
            "canonical": {
                "name": "release",
                "description": "Releases a locked escrow after reservation settlement/cancelation.\n\nReceipt: Escrow(status=completed).",
                "is_constructor": False,
            },
            "input": EscrowReleaseInput,
            "output": EscrowReleaseOutput,
        },
        "release_for_reservation_status": {
            "canonical": {
                "name": "release_for_reservation_status",
                "description": "Releases a locked escrow using a smart-contract reservation lifecycle receipt.\n\nReceipt: Escrow(status=completed) when reservation_id matches and reservation_status is terminal/releasable.",
                "is_constructor": False,
            },
            "input": EscrowReleaseForReservationStatusInput,
            "output": EscrowReleaseForReservationStatusOutput,
        },
        "create_via_wallet_public": {
            "canonical": {
                "name": "create_via_wallet_public",
                "description": "Creates a new escrow record.\n\nReceipt: Escrow(status=locked) linked to SmartContractReservation + WalletPublic, with hash/signature computed by handler.",
                "is_constructor": True,
            },
            "input": EscrowCreateViaWalletPublicInput,
            "output": EscrowCreateViaWalletPublicOutput,
        },
    },
}

__all__ = [
    "Escrow",
    "EscrowReleaseInput",
    "EscrowReleaseOutput",
    "EscrowReleaseForReservationStatusInput",
    "EscrowReleaseForReservationStatusOutput",
    "EscrowCreateViaWalletPublicInput",
    "EscrowCreateViaWalletPublicOutput",
    "FUNCTIONS",
]
