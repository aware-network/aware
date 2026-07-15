from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience.handlers.impl.program import (
    program_turn_instruction_invoke as invoke_impl,
)
from aware_experience_ontology.program.program_turn_instruction_invoke import (
    ProgramTurnInstructionInvoke,
)


class _Session:
    def __init__(self) -> None:
        self._instances: dict[tuple[type, UUID], object] = {}

    def imap_get(self, cls, object_id):
        return self._instances.get((cls, object_id))

    def put(self, obj: object) -> None:
        object_id = getattr(obj, "id")
        self._instances[(obj.__class__, object_id)] = obj


def _u(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware://tests/experience/program-invoke-arg/{name}")


@pytest.mark.asyncio
async def test_add_attribute_config_receipt_appends_deterministic_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        invoke_impl, "current_handler_session", lambda _session=session: _session
    )

    invoke_id = _u("invoke")
    invoke_receipt_id = _u("invoke-receipt")
    invoke_attribute_id = _u("invoke-attribute")

    invoke_instruction = ProgramImplInstructionInvoke.model_construct(
        id=invoke_id,
        function_config_id=_u("function"),
        program_config_actor_config_id=_u("actor-config-assoc"),
        program_config_port_projection_experience_node_id=_u("port-node"),
    )
    invoke_receipt = ProgramTurnInstructionInvoke.model_construct(
        id=invoke_receipt_id,
        program_impl_instruction_invoke_id=invoke_id,
        program_actor_role_id=_u("program-actor-role"),
        projection_experience_node_class_identity_id=_u("node-class-identity"),
        attribute_config_receipts=[],
    )
    invoke_attribute = ProgramImplInstructionInvokeAttributeConfig.model_construct(
        id=invoke_attribute_id,
        program_impl_instruction_invoke_id=invoke_id,
        attribute_config_id=_u("attribute-config"),
        value_expr={"$expr": "local_ref", "name": "channel_number"},
        position=1,
    )
    session.put(invoke_instruction)
    session.put(invoke_receipt)
    session.put(invoke_attribute)

    created_receipt = await invoke_impl.add_attribute_config_receipt(
        program_turn_instruction_invoke=invoke_receipt,
        program_impl_instruction_invoke_attribute_config_id=invoke_attribute_id,
    )

    assert created_receipt.program_turn_instruction_invoke_id == invoke_receipt_id
    assert (
        created_receipt.program_impl_instruction_invoke_attribute_config_id
        == invoke_attribute_id
    )
    assert len(invoke_receipt.attribute_config_receipts) == 1
    assert invoke_receipt.attribute_config_receipts[0].id == created_receipt.id


@pytest.mark.asyncio
async def test_add_attribute_config_receipt_rejects_invoke_attribute_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        invoke_impl, "current_handler_session", lambda _session=session: _session
    )

    invoke_id = _u("invoke-mismatch")
    invoke_receipt_id = _u("invoke-receipt-mismatch")
    invoke_attribute_id = _u("invoke-attribute-mismatch")

    invoke_instruction = ProgramImplInstructionInvoke.model_construct(
        id=invoke_id,
        function_config_id=_u("function-mismatch"),
        program_config_actor_config_id=_u("actor-config-assoc-mismatch"),
        program_config_port_projection_experience_node_id=_u("port-node-mismatch"),
    )
    invoke_receipt = ProgramTurnInstructionInvoke.model_construct(
        id=invoke_receipt_id,
        program_impl_instruction_invoke_id=invoke_id,
        program_actor_role_id=_u("program-actor-role-mismatch"),
        projection_experience_node_class_identity_id=_u("node-class-identity-mismatch"),
        attribute_config_receipts=[],
    )
    invoke_attribute = ProgramImplInstructionInvokeAttributeConfig.model_construct(
        id=invoke_attribute_id,
        program_impl_instruction_invoke_id=_u("different-invoke"),
        attribute_config_id=_u("attribute-config-mismatch"),
        value_expr={"$expr": "local_ref", "name": "channel_number"},
        position=1,
    )
    session.put(invoke_instruction)
    session.put(invoke_receipt)
    session.put(invoke_attribute)

    with pytest.raises(
        RuntimeError,
        match="invoke-attribute mismatch for receipt",
    ):
        await invoke_impl.add_attribute_config_receipt(
            program_turn_instruction_invoke=invoke_receipt,
            program_impl_instruction_invoke_attribute_config_id=invoke_attribute_id,
        )
