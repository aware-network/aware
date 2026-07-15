from __future__ import annotations

# Standard
from datetime import datetime
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
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import SmartContractPermitStatus

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
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.price.price_schedule import PriceSchedule
    from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation


class SmartContractPermit(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    parents: list[SmartContractPermit] = Field(default_factory=list, exclude=True)
    price_schedule: PriceSchedule | None = Field(default=None, exclude=True)
    smart_contract_reservations: list[SmartContractReservation] = Field(default_factory=list, exclude=True)

    # Attributes
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    nonce: int = Field(default=0)
    permit_nonce: int
    status: SmartContractPermitStatus = Field(default=SmartContractPermitStatus.active)

    # Foreign Keys
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_permits")
    smart_contract_permit_id: UUID | None = Field(
        default=None, description="Foreign key for SmartContractPermit.parents"
    )
    coin_id: UUID = Field(description="Foreign key for SmartContractPermit.coin")
    finance_entity_id: UUID = Field(description="Foreign key for SmartContractPermit.finance_entity")
    price_schedule_id: UUID = Field(description="Foreign key for SmartContractPermit.price_schedule")

    async def note_operation(self, op_nonce: int) -> SmartContractPermit:
        """
        Advances permit operation nonce monotonically after a successful reservation.

        Receipt: SmartContractPermit.nonce updated to `op_nonce`.
        """

        payload = {"op_nonce": op_nonce}
        result = await invoke_instance(orm_model=self, function_name="note_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractPermit):
            return value
        return SmartContractPermit.validate_invocation_value(value)

    async def revoke(self) -> SmartContractPermit:
        """
        Revokes this permit so no new operation reservation may consume its cap.

        Receipt: SmartContractPermit.status is revoked; repeated revocation is idempotent.
        """

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="revoke", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractPermit):
            return value
        return SmartContractPermit.validate_invocation_value(value)

    async def reserve_operation(
        self,
        payer_wallet_public_id: UUID,
        op_nonce: int,
        args_hash: str,
        max_cost: Annotated[Decimal, DecimalWire()],
        rate_snapshot_id: UUID,
        deadline: datetime,
        coin_id: UUID,
    ) -> SmartContractReservation:
        """
        Creates a reservation + escrow under this permit and links it canonically.

        Receipt: SmartContractReservation(status=pending) linked under this permit with deterministic escrow
        id.
        """

        payload = {
            "payer_wallet_public_id": payer_wallet_public_id,
            "op_nonce": op_nonce,
            "args_hash": args_hash,
            "max_cost": max_cost,
            "rate_snapshot_id": rate_snapshot_id,
            "deadline": deadline,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="reserve_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation

        if isinstance(value, SmartContractReservation):
            return value
        return SmartContractReservation.validate_invocation_value(value)

    @classmethod
    async def create_via_smart_contract(
        cls,
        smart_contract_id: UUID,
        finance_entity_id: UUID,
        permit_nonce: int,
        cap_amount: Annotated[Decimal, DecimalWire()],
        expires_at: datetime,
        price_schedule_id: UUID,
        coin_id: UUID,
        parent_id: UUID | None = None,
    ) -> SmartContractPermit:
        """
        Creates a SmartContractPermit under a contract.

        Receipt: SmartContractPermit linked to SmartContract + FinanceEntity.
        """

        payload = {
            "smart_contract_id": smart_contract_id,
            "finance_entity_id": finance_entity_id,
            "permit_nonce": permit_nonce,
            "cap_amount": cap_amount,
            "expires_at": expires_at,
            "price_schedule_id": price_schedule_id,
            "coin_id": coin_id,
            "parent_id": parent_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_smart_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractPermit):
            return value
        return SmartContractPermit.validate_invocation_value(value)


class SmartContractPermitNoteOperationInput(BaseModel):
    op_nonce: int


class SmartContractPermitNoteOperationOutput(BaseModel):
    value: SmartContractPermit


class SmartContractPermitRevokeInput(BaseModel):
    pass


class SmartContractPermitRevokeOutput(BaseModel):
    value: SmartContractPermit


class SmartContractPermitReserveOperationInput(BaseModel):
    payer_wallet_public_id: UUID
    op_nonce: int
    args_hash: str
    max_cost: Annotated[Decimal, DecimalWire()]
    rate_snapshot_id: UUID
    deadline: datetime
    coin_id: UUID


class SmartContractPermitReserveOperationOutput(BaseModel):
    value: SmartContractReservation


class SmartContractPermitCreateViaSmartContractInput(BaseModel):
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_permits")
    finance_entity_id: UUID
    permit_nonce: int
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    price_schedule_id: UUID
    coin_id: UUID
    parent_id: UUID | None = Field(default=None)


class SmartContractPermitCreateViaSmartContractOutput(BaseModel):
    value: SmartContractPermit


FUNCTIONS = {
    "SmartContractPermit": {
        "note_operation": {
            "canonical": {
                "name": "note_operation",
                "description": "Advances permit operation nonce monotonically after a successful reservation.\n\nReceipt: SmartContractPermit.nonce updated to `op_nonce`.",
                "is_constructor": False,
            },
            "input": SmartContractPermitNoteOperationInput,
            "output": SmartContractPermitNoteOperationOutput,
        },
        "revoke": {
            "canonical": {
                "name": "revoke",
                "description": "Revokes this permit so no new operation reservation may consume its cap.\n\nReceipt: SmartContractPermit.status is revoked; repeated revocation is idempotent.",
                "is_constructor": False,
            },
            "input": SmartContractPermitRevokeInput,
            "output": SmartContractPermitRevokeOutput,
        },
        "reserve_operation": {
            "canonical": {
                "name": "reserve_operation",
                "description": "Creates a reservation + escrow under this permit and links it canonically.\n\nReceipt: SmartContractReservation(status=pending) linked under this permit with deterministic escrow id.",
                "is_constructor": False,
            },
            "input": SmartContractPermitReserveOperationInput,
            "output": SmartContractPermitReserveOperationOutput,
        },
        "create_via_smart_contract": {
            "canonical": {
                "name": "create_via_smart_contract",
                "description": "Creates a SmartContractPermit under a contract.\n\nReceipt: SmartContractPermit linked to SmartContract + FinanceEntity.",
                "is_constructor": True,
            },
            "input": SmartContractPermitCreateViaSmartContractInput,
            "output": SmartContractPermitCreateViaSmartContractOutput,
        },
    },
}

__all__ = [
    "SmartContractPermit",
    "SmartContractPermitNoteOperationInput",
    "SmartContractPermitNoteOperationOutput",
    "SmartContractPermitRevokeInput",
    "SmartContractPermitRevokeOutput",
    "SmartContractPermitReserveOperationInput",
    "SmartContractPermitReserveOperationOutput",
    "SmartContractPermitCreateViaSmartContractInput",
    "SmartContractPermitCreateViaSmartContractOutput",
    "FUNCTIONS",
]
