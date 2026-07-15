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
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import ReservationStatus

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
    from aware_economy_ontology.price.rate_snapshot import RateSnapshot
    from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement


class SmartContractReservation(ORMModel):
    # Relationships
    escrow: Escrow | None = Field(default=None, exclude=True)
    rate_snapshot: RateSnapshot | None = Field(default=None, exclude=True)
    smart_contract_settlements: list[SmartContractSettlement] = Field(default_factory=list, exclude=True)

    # Attributes
    args_hash: str
    deadline: datetime
    final_cost: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    max_cost: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    reservation_signature: str | None = Field(default=None)
    status: ReservationStatus = Field(default=ReservationStatus.pending)

    # Foreign Keys
    smart_contract_permit_id: UUID = Field(
        description="Foreign key for SmartContractPermit.smart_contract_reservations"
    )
    escrow_id: UUID | None = Field(default=None, description="Foreign key for SmartContractReservation.escrow")
    rate_snapshot_id: UUID = Field(description="Foreign key for SmartContractReservation.rate_snapshot")

    async def set_status(
        self, status: ReservationStatus, final_cost: Annotated[Decimal, DecimalWire()] | None = None
    ) -> SmartContractReservation:
        """
        Updates reservation lifecycle status (and optional final cost on settlement paths).

        Receipt: SmartContractReservation status/final_cost transition.
        """

        payload = {"status": status, "final_cost": final_cost}
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractReservation):
            return value
        return SmartContractReservation.validate_invocation_value(value)

    async def prepare_settlement(
        self,
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        final_cost: Annotated[Decimal, DecimalWire()],
    ) -> SmartContractSettlement:
        """
        Creates or reuses the deterministic settlement receipt under this reservation.

        Receipt: SmartContractSettlement(status=prepared) linked under this reservation.
        """

        payload = {
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
            "final_cost": final_cost,
        }
        result = await invoke_instance(orm_model=self, function_name="prepare_settlement", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    @classmethod
    async def create_via_smart_contract_permit(
        cls,
        smart_contract_permit_id: UUID,
        op_nonce: int,
        args_hash: str,
        max_cost: Annotated[Decimal, DecimalWire()],
        rate_snapshot_id: UUID,
        deadline: datetime,
        reservation_signature: str | None = None,
        escrow: Escrow | None = None,
        status: ReservationStatus = ReservationStatus.pending,
    ) -> SmartContractReservation:
        """
        Creates a reservation under a permit.

        Receipt: SmartContractReservation(status=pending) linked to permit (+ optional escrow).
        """

        payload = {
            "smart_contract_permit_id": smart_contract_permit_id,
            "op_nonce": op_nonce,
            "args_hash": args_hash,
            "max_cost": max_cost,
            "rate_snapshot_id": rate_snapshot_id,
            "deadline": deadline,
            "reservation_signature": reservation_signature,
            "escrow": escrow,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_smart_contract_permit", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractReservation):
            return value
        return SmartContractReservation.validate_invocation_value(value)


class SmartContractReservationSetStatusInput(BaseModel):
    status: ReservationStatus
    final_cost: Annotated[Decimal, DecimalWire()] | None = Field(default=None)


class SmartContractReservationSetStatusOutput(BaseModel):
    value: SmartContractReservation


class SmartContractReservationPrepareSettlementInput(BaseModel):
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    final_cost: Annotated[Decimal, DecimalWire()]


class SmartContractReservationPrepareSettlementOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractReservationCreateViaSmartContractPermitInput(BaseModel):
    smart_contract_permit_id: UUID = Field(
        description="Foreign key for SmartContractPermit.smart_contract_reservations"
    )
    op_nonce: int
    args_hash: str
    max_cost: Annotated[Decimal, DecimalWire()]
    rate_snapshot_id: UUID
    deadline: datetime
    reservation_signature: str | None = Field(default=None)
    escrow: Escrow | None = Field(default=None)
    status: ReservationStatus = Field(default=ReservationStatus.pending)


class SmartContractReservationCreateViaSmartContractPermitOutput(BaseModel):
    value: SmartContractReservation


FUNCTIONS = {
    "SmartContractReservation": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Updates reservation lifecycle status (and optional final cost on settlement paths).\n\nReceipt: SmartContractReservation status/final_cost transition.",
                "is_constructor": False,
            },
            "input": SmartContractReservationSetStatusInput,
            "output": SmartContractReservationSetStatusOutput,
        },
        "prepare_settlement": {
            "canonical": {
                "name": "prepare_settlement",
                "description": "Creates or reuses the deterministic settlement receipt under this reservation.\n\nReceipt: SmartContractSettlement(status=prepared) linked under this reservation.",
                "is_constructor": False,
            },
            "input": SmartContractReservationPrepareSettlementInput,
            "output": SmartContractReservationPrepareSettlementOutput,
        },
        "create_via_smart_contract_permit": {
            "canonical": {
                "name": "create_via_smart_contract_permit",
                "description": "Creates a reservation under a permit.\n\nReceipt: SmartContractReservation(status=pending) linked to permit (+ optional escrow).",
                "is_constructor": True,
            },
            "input": SmartContractReservationCreateViaSmartContractPermitInput,
            "output": SmartContractReservationCreateViaSmartContractPermitOutput,
        },
    },
}

__all__ = [
    "SmartContractReservation",
    "SmartContractReservationSetStatusInput",
    "SmartContractReservationSetStatusOutput",
    "SmartContractReservationPrepareSettlementInput",
    "SmartContractReservationPrepareSettlementOutput",
    "SmartContractReservationCreateViaSmartContractPermitInput",
    "SmartContractReservationCreateViaSmartContractPermitOutput",
    "FUNCTIONS",
]
