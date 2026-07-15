from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.program_config_actor_config import (
    ProgramConfigActorConfig,
)
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.program.program_enums import ProgramBranchBindingMode
from aware_identity_ontology.actor.actor_config_role_config import (
    ActorConfigRoleConfig,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_experience.handlers.impl.program import (
    program_turn_instruction_bind as bind_impl,
)
from aware_experience.handlers.impl.program import (
    program_turn_instruction as turn_instruction_impl,
)
from aware_experience.handlers.impl.program import (
    program_turn_instruction_bind_identity as bind_identity_impl,
)
from aware_experience_ontology.program.program_actor import ProgramActor
from aware_experience_ontology.program.program_actor_role import ProgramActorRole
from aware_experience_ontology.program.program_turn_instruction import (
    ProgramTurnInstruction,
)
from aware_experience_ontology.program.program_turn_instruction_bind import (
    ProgramTurnInstructionBind,
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
    return uuid5(NAMESPACE_URL, f"aware://tests/experience/program-bind/{name}")


def _fixed_port_node_identity(
    node_contract_id: UUID,
    projection_node_identity_id: UUID,
) -> ProgramConfigPortProjectionExperienceNodeIdentity:
    return ProgramConfigPortProjectionExperienceNodeIdentity.model_construct(
        id=_u(f"port-node-identity:{node_contract_id}:{projection_node_identity_id}"),
        program_config_port_projection_experience_node_id=node_contract_id,
        projection_experience_node_identity_id=projection_node_identity_id,
        key="fixed",
    )


@pytest.mark.asyncio
async def test_build_via_program_rejects_view_projection_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        bind_impl, "current_handler_session", lambda _session=session: _session
    )

    projection_a = _u("projection-a")
    projection_b = _u("projection-b")
    port_id = _u("port")
    bind_instruction_id = _u("bind-instruction")
    oigb_id = _u("oigb")
    view_id = _u("view")

    program_port = ProgramConfigPort.model_construct(
        id=port_id,
        program_config_id=_u("program-config"),
        projection_id=projection_a,
        key="main",
        intent=None,
        branch_binding_mode=ProgramBranchBindingMode.reference,
    )
    bind_instruction = ProgramImplInstructionBind.model_construct(
        id=bind_instruction_id,
        program_impl_instruction_id=_u("program-impl-instruction"),
        program_config_port_id=port_id,
        program_config_port=program_port,
        view_key="security.home",
        is_active=True,
    )
    oigb = ObjectInstanceGraphBranch.model_construct(
        id=oigb_id,
        object_instance_graph_identity_id=_u("oigi"),
        branch_id=_u("history-branch"),
        branch=None,
        object_instance_graph_lanes=[],
        object_instance_graph_branch_relationships=[],
    )
    view = ProjectionExperienceView.model_construct(
        id=view_id,
        projection_experience_id=projection_b,
        api_view_id=_u("api-view"),
        name="security.home",
    )
    session.put(program_port)
    session.put(bind_instruction)
    session.put(oigb)
    session.put(view)

    with pytest.raises(
        RuntimeError,
        match="view/projection mismatch for bind instruction",
    ):
        await bind_impl.build_via_program_turn_instruction(
            program_turn_instruction_id=_u("program-turn-instruction"),
            program_impl_instruction_bind_id=bind_instruction_id,
            object_instance_graph_branch_id=oigb_id,
            projection_experience_view_id=view_id,
        )


@pytest.mark.asyncio
async def test_add_resolved_node_identity_rejects_fixed_identity_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        bind_impl, "current_handler_session", lambda _session=session: _session
    )

    port_id = _u("fixed-port")
    bind_instruction_id = _u("fixed-bind-instruction")
    bind_receipt_id = _u("fixed-bind-receipt")
    projection_node_id = _u("fixed-projection-node")
    contract_identity_id = _u("contract-identity")
    resolved_identity_id = _u("resolved-identity")
    node_contract_id = _u("fixed-node-contract")
    node_class_identity_id = _u("fixed-node-class-identity")

    bind_instruction = ProgramImplInstructionBind.model_construct(
        id=bind_instruction_id,
        program_impl_instruction_id=_u("program-impl-instruction"),
        program_config_port_id=port_id,
        view_key="security.home",
        is_active=True,
    )
    bind_receipt = ProgramTurnInstructionBind.model_construct(
        id=bind_receipt_id,
        program_turn_instruction_id=_u("program-turn-instruction"),
        program_impl_instruction_bind_id=bind_instruction_id,
        program_impl_instruction_bind=bind_instruction,
        object_instance_graph_branch_id=_u("oigb"),
        projection_experience_view_id=_u("view"),
        resolved_node_identities=[],
    )
    node_contract = ProgramConfigPortProjectionExperienceNode.model_construct(
        id=node_contract_id,
        program_config_port_id=port_id,
        projection_experience_node_id=projection_node_id,
        key="door",
    )
    node_contract_identity = _fixed_port_node_identity(
        node_contract_id, contract_identity_id
    )
    node_contract.projection_node_identity = node_contract_identity
    node_class_identity = ProjectionExperienceNodeClassIdentity.model_construct(
        id=node_class_identity_id,
        projection_experience_oigi_id=_u("projection-experience-oigi"),
        projection_experience_node_identity_id=resolved_identity_id,
        class_instance_identity_id=_u("class-instance-identity"),
        key="door.front_door",
    )
    session.put(bind_instruction)
    session.put(bind_receipt)
    session.put(node_contract)
    session.put(node_contract_identity)
    session.put(node_class_identity)

    with pytest.raises(
        RuntimeError,
        match="identity mismatch for fixed port-node identity",
    ):
        await bind_impl.add_resolved_node_identity(
            program_turn_instruction_bind=bind_receipt,
            program_config_port_projection_experience_node_id=node_contract_id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        )


@pytest.mark.asyncio
async def test_add_resolved_node_identity_rejects_dynamic_node_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        bind_impl, "current_handler_session", lambda _session=session: _session
    )

    port_id = _u("dynamic-port")
    bind_instruction_id = _u("dynamic-bind-instruction")
    bind_receipt_id = _u("dynamic-bind-receipt")
    expected_projection_node_id = _u("expected-projection-node")
    resolved_projection_node_id = _u("resolved-projection-node")
    resolved_identity_id = _u("resolved-identity")
    node_contract_id = _u("dynamic-node-contract")
    node_class_identity_id = _u("dynamic-node-class-identity")

    bind_instruction = ProgramImplInstructionBind.model_construct(
        id=bind_instruction_id,
        program_impl_instruction_id=_u("program-impl-instruction"),
        program_config_port_id=port_id,
        view_key="security.home",
        is_active=True,
    )
    bind_receipt = ProgramTurnInstructionBind.model_construct(
        id=bind_receipt_id,
        program_turn_instruction_id=_u("program-turn-instruction"),
        program_impl_instruction_bind_id=bind_instruction_id,
        program_impl_instruction_bind=bind_instruction,
        object_instance_graph_branch_id=_u("oigb"),
        projection_experience_view_id=_u("view"),
        resolved_node_identities=[],
    )
    node_contract = ProgramConfigPortProjectionExperienceNode.model_construct(
        id=node_contract_id,
        program_config_port_id=port_id,
        projection_experience_node_id=expected_projection_node_id,
        key="door",
    )
    node_class_identity = ProjectionExperienceNodeClassIdentity.model_construct(
        id=node_class_identity_id,
        projection_experience_oigi_id=_u("projection-experience-oigi"),
        projection_experience_node_identity_id=resolved_identity_id,
        class_instance_identity_id=_u("class-instance-identity"),
        key="door.dynamic",
    )
    resolved_identity = ProjectionExperienceNodeIdentity.model_construct(
        id=resolved_identity_id,
        projection_experience_node_id=resolved_projection_node_id,
        key="resolved",
    )
    session.put(bind_instruction)
    session.put(bind_receipt)
    session.put(node_contract)
    session.put(node_class_identity)
    session.put(resolved_identity)

    with pytest.raises(
        RuntimeError,
        match="node mismatch for dynamic port-node resolution",
    ):
        await bind_impl.add_resolved_node_identity(
            program_turn_instruction_bind=bind_receipt,
            program_config_port_projection_experience_node_id=node_contract_id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        )


@pytest.mark.asyncio
async def test_bind_identity_constructor_requires_bind_receipt_instruction_relation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        bind_identity_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )

    bind_receipt_id = _u("ctor-bind-receipt")
    node_contract_id = _u("ctor-node-contract")
    node_class_identity_id = _u("ctor-node-class-identity")
    projection_node_id = _u("ctor-projection-node")
    projection_identity_id = _u("ctor-projection-identity")

    bind_receipt = ProgramTurnInstructionBind.model_construct(
        id=bind_receipt_id,
        program_turn_instruction_id=_u("program-turn-instruction"),
        program_impl_instruction_bind_id=_u("missing-bind-instruction"),
        program_impl_instruction_bind=None,
        object_instance_graph_branch_id=_u("oigb"),
        projection_experience_view_id=_u("view"),
        resolved_node_identities=[],
    )
    node_contract = ProgramConfigPortProjectionExperienceNode.model_construct(
        id=node_contract_id,
        program_config_port_id=_u("port"),
        projection_experience_node_id=projection_node_id,
        key="door",
    )
    node_contract_identity = _fixed_port_node_identity(
        node_contract_id, projection_identity_id
    )
    node_contract.projection_node_identity = node_contract_identity
    node_class_identity = ProjectionExperienceNodeClassIdentity.model_construct(
        id=node_class_identity_id,
        projection_experience_oigi_id=_u("projection-experience-oigi"),
        projection_experience_node_identity_id=projection_identity_id,
        class_instance_identity_id=_u("class-instance-identity"),
        key="door.front_door",
    )
    session.put(bind_receipt)
    session.put(node_contract)
    session.put(node_contract_identity)
    session.put(node_class_identity)

    with pytest.raises(
        RuntimeError,
        match="requires bind receipt ProgramImplInstructionBind relation",
    ):
        await bind_identity_impl.build_via_program_turn_instruction_bind(
            program_turn_instruction_bind_id=bind_receipt_id,
            program_config_port_projection_experience_node_id=node_contract_id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        )


@pytest.mark.asyncio
async def test_record_invoke_rejects_actor_alias_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        turn_instruction_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )

    actor_config_a = _u("actor-config-a")
    actor_config_b = _u("actor-config-b")
    invoke_actor_assoc_id = _u("invoke-actor-assoc")
    program_actor_assoc_id = _u("program-actor-assoc")
    actor_config_role_config_id = _u("actor-config-role-config")
    invoke_instruction_id = _u("invoke-instruction")
    port_node_id = _u("invoke-port-node")
    projection_identity_id = _u("invoke-projection-identity")
    node_class_identity_id = _u("invoke-node-class-identity")
    turn_instruction_id = _u("program-turn-instruction")

    program_turn_instruction = ProgramTurnInstruction.model_construct(
        id=turn_instruction_id,
        invoke_receipt=None,
    )
    invoke_instruction = ProgramImplInstructionInvoke.model_construct(
        id=invoke_instruction_id,
        program_impl_instruction_id=_u("program-impl-instruction"),
        function_config_id=_u("function-config"),
        program_config_actor_config_id=invoke_actor_assoc_id,
        program_config_port_projection_experience_node_id=port_node_id,
    )
    invoke_actor_assoc = ProgramConfigActorConfig.model_construct(
        id=invoke_actor_assoc_id,
        program_config_id=_u("program-config"),
        actor_config_id=actor_config_a,
        alias="assistant",
    )
    program_actor_assoc = ProgramConfigActorConfig.model_construct(
        id=program_actor_assoc_id,
        program_config_id=_u("program-config"),
        actor_config_id=actor_config_b,
        alias="assistant",
    )
    program_actor = ProgramActor.model_construct(
        id=_u("program-actor"),
        program_id=_u("program"),
        program_config_actor_config_id=program_actor_assoc_id,
        actor_id=_u("actor"),
    )
    actor_config_role_config = ActorConfigRoleConfig.model_construct(
        id=actor_config_role_config_id,
        actor_config_id=actor_config_a,
        role_config_id=_u("role-config"),
    )
    program_actor_role = ProgramActorRole.model_construct(
        id=_u("program-actor-role"),
        program_actor_id=program_actor.id,
        actor_role_id=_u("actor-role"),
        actor_config_role_config_id=actor_config_role_config_id,
    )
    invoke_node = ProgramConfigPortProjectionExperienceNode.model_construct(
        id=port_node_id,
        program_config_port_id=_u("port"),
        projection_experience_node_id=_u("projection-node"),
        key="door",
    )
    invoke_node_identity = _fixed_port_node_identity(
        port_node_id, projection_identity_id
    )
    invoke_node.projection_node_identity = invoke_node_identity
    node_class_identity = ProjectionExperienceNodeClassIdentity.model_construct(
        id=node_class_identity_id,
        projection_experience_oigi_id=_u("projection-experience-oigi"),
        projection_experience_node_identity_id=projection_identity_id,
        class_instance_identity_id=_u("class-instance-identity"),
        key="door.front_door",
    )
    session.put(invoke_instruction)
    session.put(invoke_actor_assoc)
    session.put(program_actor_assoc)
    session.put(program_actor)
    session.put(actor_config_role_config)
    session.put(program_actor_role)
    session.put(invoke_node)
    session.put(invoke_node_identity)
    session.put(node_class_identity)

    with pytest.raises(
        RuntimeError,
        match="actor alias mismatch between ProgramActor and invoke contract",
    ):
        await turn_instruction_impl.record_invoke(
            program_turn_instruction=program_turn_instruction,
            program_impl_instruction_invoke_id=invoke_instruction_id,
            program_actor_role_id=program_actor_role.id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        )


@pytest.mark.asyncio
async def test_record_invoke_rejects_fixed_identity_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        turn_instruction_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )

    actor_config_id = _u("actor-config")
    invoke_actor_assoc_id = _u("invoke-actor-assoc")
    actor_config_role_config_id = _u("actor-config-role-config")
    invoke_instruction_id = _u("invoke-instruction")
    port_node_id = _u("invoke-port-node")
    contract_identity_id = _u("contract-identity")
    resolved_identity_id = _u("resolved-identity")
    node_class_identity_id = _u("invoke-node-class-identity")
    turn_instruction_id = _u("program-turn-instruction")

    program_turn_instruction = ProgramTurnInstruction.model_construct(
        id=turn_instruction_id,
        invoke_receipt=None,
    )
    invoke_instruction = ProgramImplInstructionInvoke.model_construct(
        id=invoke_instruction_id,
        program_impl_instruction_id=_u("program-impl-instruction"),
        function_config_id=_u("function-config"),
        program_config_actor_config_id=invoke_actor_assoc_id,
        program_config_port_projection_experience_node_id=port_node_id,
    )
    invoke_actor_assoc = ProgramConfigActorConfig.model_construct(
        id=invoke_actor_assoc_id,
        program_config_id=_u("program-config"),
        actor_config_id=actor_config_id,
        alias="assistant",
    )
    program_actor = ProgramActor.model_construct(
        id=_u("program-actor"),
        program_id=_u("program"),
        program_config_actor_config_id=invoke_actor_assoc_id,
        actor_id=_u("actor"),
    )
    actor_config_role_config = ActorConfigRoleConfig.model_construct(
        id=actor_config_role_config_id,
        actor_config_id=actor_config_id,
        role_config_id=_u("role-config"),
    )
    program_actor_role = ProgramActorRole.model_construct(
        id=_u("program-actor-role"),
        program_actor_id=program_actor.id,
        actor_role_id=_u("actor-role"),
        actor_config_role_config_id=actor_config_role_config_id,
    )
    invoke_node = ProgramConfigPortProjectionExperienceNode.model_construct(
        id=port_node_id,
        program_config_port_id=_u("port"),
        projection_experience_node_id=_u("projection-node"),
        key="door",
    )
    invoke_node_identity = _fixed_port_node_identity(port_node_id, contract_identity_id)
    invoke_node.projection_node_identity = invoke_node_identity
    node_class_identity = ProjectionExperienceNodeClassIdentity.model_construct(
        id=node_class_identity_id,
        projection_experience_oigi_id=_u("projection-experience-oigi"),
        projection_experience_node_identity_id=resolved_identity_id,
        class_instance_identity_id=_u("class-instance-identity"),
        key="door.front_door",
    )
    session.put(invoke_instruction)
    session.put(invoke_actor_assoc)
    session.put(program_actor)
    session.put(actor_config_role_config)
    session.put(program_actor_role)
    session.put(invoke_node)
    session.put(invoke_node_identity)
    session.put(node_class_identity)

    with pytest.raises(
        RuntimeError,
        match="identity mismatch for fixed invoke node identity",
    ):
        await turn_instruction_impl.record_invoke(
            program_turn_instruction=program_turn_instruction,
            program_impl_instruction_invoke_id=invoke_instruction_id,
            program_actor_role_id=program_actor_role.id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        )
