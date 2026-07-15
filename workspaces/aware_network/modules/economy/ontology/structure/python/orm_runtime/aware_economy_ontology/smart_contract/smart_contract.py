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
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import ReservationStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.smart_contract.smart_contract_member import SmartContractMember
    from aware_economy_ontology.smart_contract.smart_contract_permit import SmartContractPermit
    from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation
    from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement


class SmartContract(ORMModel):
    # Relationships
    smart_contract_members: list[SmartContractMember] = Field(default_factory=list, exclude=True)
    smart_contract_permits: list[SmartContractPermit] = Field(default_factory=list, exclude=True)

    # Attributes
    arguments: JsonObject = Field(default_factory=JsonObject)
    blockchain_address: str
    status: SmartContractStatus

    # Foreign Keys
    smart_contract_config_id: UUID = Field(description="Foreign key for SmartContractConfig.smart_contracts")

    async def add_member(self, finance_entity_id: UUID, type: SmartContractMemberType) -> SmartContractMember:
        """Adds a finance entity member to the contract."""

        payload = {"finance_entity_id": finance_entity_id, "type": type}
        result = await invoke_instance(orm_model=self, function_name="add_member", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_member import SmartContractMember

        if isinstance(value, SmartContractMember):
            return value
        return SmartContractMember.validate_invocation_value(value)

    async def open_session_permit(
        self,
        finance_entity_id: UUID,
        permit_nonce: int,
        cap_amount: Annotated[Decimal, DecimalWire()],
        expires_at: datetime,
        price_schedule_id: UUID,
        coin_id: UUID,
        parent_id: UUID | None = None,
    ) -> SmartContractPermit:
        """
        Opens a session permit for a finance entity under this contract.

        Returns: the created SmartContractPermit.
        """

        payload = {
            "finance_entity_id": finance_entity_id,
            "permit_nonce": permit_nonce,
            "cap_amount": cap_amount,
            "expires_at": expires_at,
            "price_schedule_id": price_schedule_id,
            "coin_id": coin_id,
            "parent_id": parent_id,
        }
        result = await invoke_instance(orm_model=self, function_name="open_session_permit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_permit import SmartContractPermit

        if isinstance(value, SmartContractPermit):
            return value
        return SmartContractPermit.validate_invocation_value(value)

    async def reserve_operation(
        self,
        permit_id: UUID,
        permit_nonce: int,
        finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        op_nonce: int,
        args_hash: str,
        max_cost: Annotated[Decimal, DecimalWire()],
        rate_snapshot_id: UUID,
        deadline: datetime,
        coin_id: UUID,
    ) -> SmartContractReservation:
        """
        Reserves up to max_cost by creating a deterministic reservation + escrow under this contract.

        Permit-local price schedule authority must match the referenced rate snapshot.

        Returns: the created SmartContractReservation receipt.
        """

        payload = {
            "permit_id": permit_id,
            "permit_nonce": permit_nonce,
            "finance_entity_id": finance_entity_id,
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

    async def prepare_settlement(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        final_cost: Annotated[Decimal, DecimalWire()],
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Builds a prepared smart-contract settlement receipt without finalizing reservation.

        Returns: the prepared SmartContractSettlement receipt.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "final_cost": final_cost,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="prepare_settlement", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def finalize_settlement(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        final_cost: Annotated[Decimal, DecimalWire()],
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Finalizes a prepared settlement receipt and closes reservation lifecycle.

        Returns: the finalized SmartContractSettlement receipt.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "final_cost": final_cost,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="finalize_settlement", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def settle_operation(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        final_cost: Annotated[Decimal, DecimalWire()],
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Compatibility settlement entrypoint that runs prepare/finalize on reservation lifecycle receipts.

        Note: escrow release is orchestrated by canonical settlement programs/service choreography.

        Returns: the finalized SmartContractSettlement receipt.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "final_cost": final_cost,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="settle_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def release_reservation(
        self, permit_id: UUID, reservation_id: UUID, status: ReservationStatus
    ) -> SmartContractReservation:
        """
        Releases a pending smart-contract reservation as cancelled or expired.

        Receipt: SmartContractReservation(status=cancelled/expired) and Escrow(status=completed).
        """

        payload = {"permit_id": permit_id, "reservation_id": reservation_id, "status": status}
        result = await invoke_instance(orm_model=self, function_name="release_reservation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_reservation import SmartContractReservation

        if isinstance(value, SmartContractReservation):
            return value
        return SmartContractReservation.validate_invocation_value(value)

    async def prepare_settlement_canonical(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Canonical prepare path that derives final_cost from reservation state (no caller-provided
        final_cost).

        v1 policy: final_cost is derived as reservation.max_cost.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="prepare_settlement_canonical", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def finalize_settlement_canonical(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Canonical finalize path that derives final_cost from reservation state (no caller-provided
        final_cost).

        v1 policy: final_cost is derived as reservation.max_cost.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="finalize_settlement_canonical", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    async def validate_settlement_wallet_transitions_canonical(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        payer_expected_coin_balance: Annotated[Decimal, DecimalWire()],
        payer_new_coin_balance: Annotated[Decimal, DecimalWire()],
        receiver_expected_coin_balance: Annotated[Decimal, DecimalWire()],
        receiver_new_coin_balance: Annotated[Decimal, DecimalWire()],
        coin_id: UUID,
    ) -> Annotated[Decimal, DecimalWire()]:
        """
        Validates v2 wallet transitions against reservation economics.

        Fail-closed:
        - Enforces payer debit == receiver credit (conservation).
        - Enforces transfer amount == reservation.max_cost (canonical final cost).
        - Enforces non-negative debit/credit deltas.

        Returns: the canonical transfer amount derived from reservation state.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "payer_expected_coin_balance": payer_expected_coin_balance,
            "payer_new_coin_balance": payer_new_coin_balance,
            "receiver_expected_coin_balance": receiver_expected_coin_balance,
            "receiver_new_coin_balance": receiver_new_coin_balance,
            "coin_id": coin_id,
        }
        result = await invoke_instance(
            orm_model=self, function_name="validate_settlement_wallet_transitions_canonical", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def settle_operation_canonical(
        self,
        permit_id: UUID,
        reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
    ) -> SmartContractSettlement:
        """
        Canonical compatibility wrapper over prepare/finalize canonical settlement functions.

        Note: escrow release is orchestrated by canonical settlement programs/service choreography.
        """

        payload = {
            "permit_id": permit_id,
            "reservation_id": reservation_id,
            "payer_finance_entity_id": payer_finance_entity_id,
            "payer_wallet_public_id": payer_wallet_public_id,
            "receiver_finance_entity_id": receiver_finance_entity_id,
            "receiver_wallet_public_id": receiver_wallet_public_id,
            "coin_id": coin_id,
        }
        result = await invoke_instance(orm_model=self, function_name="settle_operation_canonical", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement

        if isinstance(value, SmartContractSettlement):
            return value
        return SmartContractSettlement.validate_invocation_value(value)

    @classmethod
    async def build_via_smart_contract_config(
        cls,
        smart_contract_config_id: UUID,
        blockchain_address: str,
        status: SmartContractStatus = SmartContractStatus.active,
        arguments: JsonObject | None = None,
    ) -> SmartContract:
        """
        Creates a SmartContract instance.

        Receipt: SmartContract instance.
        """

        payload = {
            "smart_contract_config_id": smart_contract_config_id,
            "blockchain_address": blockchain_address,
            "status": status,
            "arguments": arguments,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_smart_contract_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContract):
            return value
        return SmartContract.validate_invocation_value(value)


class SmartContractAddMemberInput(BaseModel):
    finance_entity_id: UUID
    type: SmartContractMemberType


class SmartContractAddMemberOutput(BaseModel):
    value: SmartContractMember


class SmartContractOpenSessionPermitInput(BaseModel):
    finance_entity_id: UUID
    permit_nonce: int
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    price_schedule_id: UUID
    coin_id: UUID
    parent_id: UUID | None = Field(default=None)


class SmartContractOpenSessionPermitOutput(BaseModel):
    value: SmartContractPermit


class SmartContractReserveOperationInput(BaseModel):
    permit_id: UUID
    permit_nonce: int
    finance_entity_id: UUID
    payer_wallet_public_id: UUID
    op_nonce: int
    args_hash: str
    max_cost: Annotated[Decimal, DecimalWire()]
    rate_snapshot_id: UUID
    deadline: datetime
    coin_id: UUID


class SmartContractReserveOperationOutput(BaseModel):
    value: SmartContractReservation


class SmartContractPrepareSettlementInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    final_cost: Annotated[Decimal, DecimalWire()]
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractPrepareSettlementOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractFinalizeSettlementInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    final_cost: Annotated[Decimal, DecimalWire()]
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractFinalizeSettlementOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractSettleOperationInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    final_cost: Annotated[Decimal, DecimalWire()]
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractSettleOperationOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractReleaseReservationInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    status: ReservationStatus


class SmartContractReleaseReservationOutput(BaseModel):
    value: SmartContractReservation


class SmartContractPrepareSettlementCanonicalInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractPrepareSettlementCanonicalOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractFinalizeSettlementCanonicalInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractFinalizeSettlementCanonicalOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractValidateSettlementWalletTransitionsCanonicalInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    payer_expected_coin_balance: Annotated[Decimal, DecimalWire()]
    payer_new_coin_balance: Annotated[Decimal, DecimalWire()]
    receiver_expected_coin_balance: Annotated[Decimal, DecimalWire()]
    receiver_new_coin_balance: Annotated[Decimal, DecimalWire()]
    coin_id: UUID


class SmartContractValidateSettlementWalletTransitionsCanonicalOutput(BaseModel):
    value: Annotated[Decimal, DecimalWire()]


class SmartContractSettleOperationCanonicalInput(BaseModel):
    permit_id: UUID
    reservation_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID


class SmartContractSettleOperationCanonicalOutput(BaseModel):
    value: SmartContractSettlement


class SmartContractBuildViaSmartContractConfigInput(BaseModel):
    smart_contract_config_id: UUID = Field(description="Foreign key for SmartContractConfig.smart_contracts")
    blockchain_address: str
    status: SmartContractStatus = Field(default=SmartContractStatus.active)
    arguments: JsonObject | None = Field(default=None)


class SmartContractBuildViaSmartContractConfigOutput(BaseModel):
    value: SmartContract


FUNCTIONS = {
    "SmartContract": {
        "add_member": {
            "canonical": {
                "name": "add_member",
                "description": "Adds a finance entity member to the contract.",
                "is_constructor": False,
            },
            "input": SmartContractAddMemberInput,
            "output": SmartContractAddMemberOutput,
        },
        "open_session_permit": {
            "canonical": {
                "name": "open_session_permit",
                "description": "Opens a session permit for a finance entity under this contract.\n\nReturns: the created SmartContractPermit.",
                "is_constructor": False,
            },
            "input": SmartContractOpenSessionPermitInput,
            "output": SmartContractOpenSessionPermitOutput,
        },
        "reserve_operation": {
            "canonical": {
                "name": "reserve_operation",
                "description": "Reserves up to max_cost by creating a deterministic reservation + escrow under this contract.\n\nPermit-local price schedule authority must match the referenced rate snapshot.\n\nReturns: the created SmartContractReservation receipt.",
                "is_constructor": False,
            },
            "input": SmartContractReserveOperationInput,
            "output": SmartContractReserveOperationOutput,
        },
        "prepare_settlement": {
            "canonical": {
                "name": "prepare_settlement",
                "description": "Builds a prepared smart-contract settlement receipt without finalizing reservation.\n\nReturns: the prepared SmartContractSettlement receipt.",
                "is_constructor": False,
            },
            "input": SmartContractPrepareSettlementInput,
            "output": SmartContractPrepareSettlementOutput,
        },
        "finalize_settlement": {
            "canonical": {
                "name": "finalize_settlement",
                "description": "Finalizes a prepared settlement receipt and closes reservation lifecycle.\n\nReturns: the finalized SmartContractSettlement receipt.",
                "is_constructor": False,
            },
            "input": SmartContractFinalizeSettlementInput,
            "output": SmartContractFinalizeSettlementOutput,
        },
        "settle_operation": {
            "canonical": {
                "name": "settle_operation",
                "description": "Compatibility settlement entrypoint that runs prepare/finalize on reservation lifecycle receipts.\n\nNote: escrow release is orchestrated by canonical settlement programs/service choreography.\n\nReturns: the finalized SmartContractSettlement receipt.",
                "is_constructor": False,
            },
            "input": SmartContractSettleOperationInput,
            "output": SmartContractSettleOperationOutput,
        },
        "release_reservation": {
            "canonical": {
                "name": "release_reservation",
                "description": "Releases a pending smart-contract reservation as cancelled or expired.\n\nReceipt: SmartContractReservation(status=cancelled/expired) and Escrow(status=completed).",
                "is_constructor": False,
            },
            "input": SmartContractReleaseReservationInput,
            "output": SmartContractReleaseReservationOutput,
        },
        "prepare_settlement_canonical": {
            "canonical": {
                "name": "prepare_settlement_canonical",
                "description": "Canonical prepare path that derives final_cost from reservation state (no caller-provided final_cost).\n\nv1 policy: final_cost is derived as reservation.max_cost.",
                "is_constructor": False,
            },
            "input": SmartContractPrepareSettlementCanonicalInput,
            "output": SmartContractPrepareSettlementCanonicalOutput,
        },
        "finalize_settlement_canonical": {
            "canonical": {
                "name": "finalize_settlement_canonical",
                "description": "Canonical finalize path that derives final_cost from reservation state (no caller-provided final_cost).\n\nv1 policy: final_cost is derived as reservation.max_cost.",
                "is_constructor": False,
            },
            "input": SmartContractFinalizeSettlementCanonicalInput,
            "output": SmartContractFinalizeSettlementCanonicalOutput,
        },
        "validate_settlement_wallet_transitions_canonical": {
            "canonical": {
                "name": "validate_settlement_wallet_transitions_canonical",
                "description": "Validates v2 wallet transitions against reservation economics.\n\nFail-closed:\n- Enforces payer debit == receiver credit (conservation).\n- Enforces transfer amount == reservation.max_cost (canonical final cost).\n- Enforces non-negative debit/credit deltas.\n\nReturns: the canonical transfer amount derived from reservation state.",
                "is_constructor": False,
            },
            "input": SmartContractValidateSettlementWalletTransitionsCanonicalInput,
            "output": SmartContractValidateSettlementWalletTransitionsCanonicalOutput,
        },
        "settle_operation_canonical": {
            "canonical": {
                "name": "settle_operation_canonical",
                "description": "Canonical compatibility wrapper over prepare/finalize canonical settlement functions.\n\nNote: escrow release is orchestrated by canonical settlement programs/service choreography.",
                "is_constructor": False,
            },
            "input": SmartContractSettleOperationCanonicalInput,
            "output": SmartContractSettleOperationCanonicalOutput,
        },
        "build_via_smart_contract_config": {
            "canonical": {
                "name": "build_via_smart_contract_config",
                "description": "Creates a SmartContract instance.\n\nReceipt: SmartContract instance.",
                "is_constructor": True,
            },
            "input": SmartContractBuildViaSmartContractConfigInput,
            "output": SmartContractBuildViaSmartContractConfigOutput,
        },
    },
}

__all__ = [
    "SmartContract",
    "SmartContractAddMemberInput",
    "SmartContractAddMemberOutput",
    "SmartContractOpenSessionPermitInput",
    "SmartContractOpenSessionPermitOutput",
    "SmartContractReserveOperationInput",
    "SmartContractReserveOperationOutput",
    "SmartContractPrepareSettlementInput",
    "SmartContractPrepareSettlementOutput",
    "SmartContractFinalizeSettlementInput",
    "SmartContractFinalizeSettlementOutput",
    "SmartContractSettleOperationInput",
    "SmartContractSettleOperationOutput",
    "SmartContractReleaseReservationInput",
    "SmartContractReleaseReservationOutput",
    "SmartContractPrepareSettlementCanonicalInput",
    "SmartContractPrepareSettlementCanonicalOutput",
    "SmartContractFinalizeSettlementCanonicalInput",
    "SmartContractFinalizeSettlementCanonicalOutput",
    "SmartContractValidateSettlementWalletTransitionsCanonicalInput",
    "SmartContractValidateSettlementWalletTransitionsCanonicalOutput",
    "SmartContractSettleOperationCanonicalInput",
    "SmartContractSettleOperationCanonicalOutput",
    "SmartContractBuildViaSmartContractConfigInput",
    "SmartContractBuildViaSmartContractConfigOutput",
    "FUNCTIONS",
]
