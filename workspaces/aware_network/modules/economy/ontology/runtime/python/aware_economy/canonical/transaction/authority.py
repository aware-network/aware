from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from aware_economy_ontology.smart_contract.smart_contract_settlement import (
    SmartContractSettlement,
)
from aware_economy_ontology.transaction.transaction import Transaction
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta.runtime.portal_context import (
    MetaPortalPendingConstructorRequest,
    current_handler_portal_client,
    current_meta_portal_source_frame,
)
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session


async def _load_transaction_in_branch(
    *, branch_id: UUID, transaction_id: UUID
) -> Transaction | None:
    session = current_handler_session()
    backend_name = getattr(session, "_backend_name", None)
    branch_session = Session(
        branch_id=branch_id,
        skip_db=session.skip_db,
        backend_name=backend_name,
        sqlite_backend_config=session.sqlite_backend_config,
    )
    with set_session(branch_session):
        return await Transaction.by_id(transaction_id)


def _coerce_transaction(payload: object) -> Transaction | None:
    if isinstance(payload, Transaction):
        return payload
    if isinstance(payload, dict):
        value = payload.get("value", payload)
        if isinstance(value, Transaction):
            return value
        if isinstance(value, dict):
            return Transaction.model_validate(value)
    return None


async def create_transaction_via_settlement_portal(
    *,
    smart_contract_settlement: SmartContractSettlement,
    transaction_id: UUID,
    payload: Mapping[str, object],
) -> Transaction:
    frame = current_meta_portal_source_frame()
    if frame is None or frame.instance_id is None:
        raise RuntimeError(
            "transaction portal constructor requires an active source instance frame: "
            f"settlement_id={smart_contract_settlement.id}"
        )

    response = (
        await current_handler_portal_client().invoke_constructor_from_pending_field(
            MetaPortalPendingConstructorRequest(
                orm_class=SmartContractSettlement,
                source_instance_id=frame.instance_id,
                source_object_id=frame.source_object_id,
                reference_field_name="transactions",
                function_name="create",
                payload=payload,
                target_branch_id=None,
                target_object_id=transaction_id,
                commit=None,
            )
        )
    )

    status = getattr(response, "status", None)
    if status is None:
        transaction = _coerce_transaction(response)
        if transaction is not None:
            return transaction
        raise RuntimeError(
            "transaction portal constructor returned unexpected non-response payload: "
            f"settlement_id={smart_contract_settlement.id}"
        )
    if status != "succeeded":
        error = getattr(response, "error", None) or status
        raise RuntimeError(f"transaction portal constructor failed: {error}")

    transaction = _coerce_transaction(getattr(response, "payload", None))
    if transaction is not None:
        return transaction

    branch_id = getattr(response, "branch_id", None)
    if isinstance(branch_id, UUID):
        fetched = await _load_transaction_in_branch(
            branch_id=branch_id,
            transaction_id=transaction_id,
        )
        if fetched is not None:
            return fetched

    raise RuntimeError(
        "transaction portal constructor succeeded without a materialized transaction payload: "
        f"settlement_id={smart_contract_settlement.id} transaction_id={transaction_id}"
    )
