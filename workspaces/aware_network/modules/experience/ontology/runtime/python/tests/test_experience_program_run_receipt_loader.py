from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from aware_experience.program import program_run_receipt_loader

from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
    ProgramConfigPortProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.program.program_actor import ProgramActor
from aware_experience_ontology.program.program_actor_role import ProgramActorRole
from aware_experience_ontology.program.program_turn_instruction_invoke import (
    ProgramTurnInstructionInvoke,
)
from aware_experience_ontology.program.program_turn_instruction_invoke_attribute_config import (
    ProgramTurnInstructionInvokeAttributeConfig,
)


@dataclass(frozen=True, slots=True)
class _InvokeResolutionFixture:
    instruction_invoke_id: UUID
    instruction_invoke_attribute_id: UUID
    instruction_rows: tuple[ProgramImplInstruction, ...]
    instruction_invokes_by_id: dict[UUID, ProgramImplInstructionInvoke]
    invoke_attributes_by_invoke_id: dict[
        UUID, tuple[ProgramImplInstructionInvokeAttributeConfig, ...]
    ]
    actor_configs_by_assoc_id: dict[UUID, ActorConfig]
    port_nodes_by_port_id: dict[
        UUID, tuple[ProgramConfigPortProjectionExperienceNode, ...]
    ]
    replay_invoke_receipts_by_program_instruction_id: dict[
        UUID, ProgramTurnInstructionInvoke
    ]
    replay_invoke_attribute_rows_by_receipt_id: dict[
        UUID, tuple[ProgramTurnInstructionInvokeAttributeConfig, ...]
    ]
    replay_program_actor_roles_by_id: dict[UUID, ProgramActorRole]
    replay_program_actors_by_id: dict[UUID, ProgramActor]
    replay_actor_config_role_configs_by_id: dict[UUID, ActorConfigRoleConfig]
    replay_node_class_identities_by_id: dict[
        UUID, ProjectionExperienceNodeClassIdentity
    ]
    replay_projection_node_identities_by_id: dict[
        UUID, ProjectionExperienceNodeIdentity
    ]


def _base_invoke_resolution_fixture() -> _InvokeResolutionFixture:
    instruction_id = uuid4()
    instruction_invoke_id = uuid4()
    program_impl_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_id = uuid4()
    function_config_id = uuid4()
    instruction_invoke_attribute_id = uuid4()
    attribute_config_id = uuid4()
    receipt_id = uuid4()
    invoke_attribute_receipt_id = uuid4()
    program_actor_role_id = uuid4()
    program_actor_id = uuid4()
    actor_config_role_config_id = uuid4()
    node_class_identity_id = uuid4()
    projection_experience_oigi_id = uuid4()
    class_instance_identity_id = uuid4()

    instruction_invoke = ProgramImplInstructionInvoke(
        id=instruction_invoke_id,
        function_config_id=function_config_id,
        program_config_actor_config_id=actor_assoc_id,
        program_config_port_projection_experience_node_id=port_node_id,
    )
    instruction_rows = (
        ProgramImplInstruction(
            id=instruction_id,
            program_impl_id=program_impl_id,
            type=ProgramImplInstructionType.invoke,
            sequence=1,
            instruction_invoke=instruction_invoke,
        ),
    )
    instruction_invokes_by_id = {
        instruction_invoke_id: instruction_invoke,
    }
    invoke_attributes_by_invoke_id = {
        instruction_invoke_id: (
            ProgramImplInstructionInvokeAttributeConfig(
                id=instruction_invoke_attribute_id,
                program_impl_instruction_invoke_id=instruction_invoke_id,
                attribute_config_id=attribute_config_id,
                value_expr={"$expr": "local_ref", "name": "channel_number"},
                position=1,
            ),
        ),
    }
    actor_configs_by_assoc_id = {
        actor_assoc_id: ActorConfig(
            id=actor_config_id,
            key="resident",
        ),
    }
    port_node_identity = ProgramConfigPortProjectionExperienceNodeIdentity(
        projection_experience_node_identity_id=projection_node_identity_id,
        key="front_door",
    )
    port_nodes_by_port_id = {
        port_id: (
            ProgramConfigPortProjectionExperienceNode(
                id=port_node_id,
                program_config_port_id=port_id,
                projection_experience_node_id=projection_node_id,
                projection_node_identity=port_node_identity,
                key="door",
            ),
        ),
    }
    replay_invoke_receipts_by_program_instruction_id = {
        instruction_id: ProgramTurnInstructionInvoke(
            id=receipt_id,
            program_impl_instruction_invoke_id=instruction_invoke_id,
            program_actor_role_id=program_actor_role_id,
            projection_experience_node_class_identity_id=node_class_identity_id,
        ),
    }
    replay_invoke_attribute_rows_by_receipt_id = {
        receipt_id: (
            ProgramTurnInstructionInvokeAttributeConfig(
                id=invoke_attribute_receipt_id,
                program_turn_instruction_invoke_id=receipt_id,
                program_impl_instruction_invoke_attribute_config_id=instruction_invoke_attribute_id,
            ),
        )
    }
    replay_program_actor_roles_by_id = {
        program_actor_role_id: ProgramActorRole(
            id=program_actor_role_id,
            program_actor_id=program_actor_id,
            actor_role_id=uuid4(),
            actor_config_role_config_id=actor_config_role_config_id,
        ),
    }
    replay_program_actors_by_id = {
        program_actor_id: ProgramActor(
            id=program_actor_id,
            program_id=uuid4(),
            program_config_actor_config_id=actor_assoc_id,
            actor_id=uuid4(),
        ),
    }
    replay_actor_config_role_configs_by_id = {
        actor_config_role_config_id: ActorConfigRoleConfig(
            id=actor_config_role_config_id,
            actor_config_id=actor_config_id,
            role_config_id=uuid4(),
        ),
    }
    replay_node_class_identities_by_id = {
        node_class_identity_id: ProjectionExperienceNodeClassIdentity(
            id=node_class_identity_id,
            projection_experience_oigi_id=projection_experience_oigi_id,
            projection_experience_node_identity_id=projection_node_identity_id,
            class_instance_identity_id=class_instance_identity_id,
            key="door_binding",
        ),
    }
    replay_projection_node_identities_by_id = {
        projection_node_identity_id: ProjectionExperienceNodeIdentity(
            id=projection_node_identity_id,
            projection_experience_node_id=projection_node_id,
            key="front_door",
        ),
    }
    return _InvokeResolutionFixture(
        instruction_invoke_id=instruction_invoke_id,
        instruction_invoke_attribute_id=instruction_invoke_attribute_id,
        instruction_rows=instruction_rows,
        instruction_invokes_by_id=instruction_invokes_by_id,
        invoke_attributes_by_invoke_id=invoke_attributes_by_invoke_id,
        actor_configs_by_assoc_id=actor_configs_by_assoc_id,
        port_nodes_by_port_id=port_nodes_by_port_id,
        replay_invoke_receipts_by_program_instruction_id=replay_invoke_receipts_by_program_instruction_id,
        replay_invoke_attribute_rows_by_receipt_id=replay_invoke_attribute_rows_by_receipt_id,
        replay_program_actor_roles_by_id=replay_program_actor_roles_by_id,
        replay_program_actors_by_id=replay_program_actors_by_id,
        replay_actor_config_role_configs_by_id=replay_actor_config_role_configs_by_id,
        replay_node_class_identities_by_id=replay_node_class_identities_by_id,
        replay_projection_node_identities_by_id=replay_projection_node_identities_by_id,
    )


def test_resolve_replay_invoke_contracts_happy_path() -> None:
    fixture = _base_invoke_resolution_fixture()
    (
        resolved_invoke_receipts,
        resolved_invoke_attribute_receipts,
    ) = program_run_receipt_loader._resolve_replay_invoke_contracts(  # pyright: ignore[reportPrivateUsage]
        instruction_rows=fixture.instruction_rows,
        instruction_invokes_by_id=fixture.instruction_invokes_by_id,
        invoke_attributes_by_invoke_id=fixture.invoke_attributes_by_invoke_id,
        actor_configs_by_assoc_id=fixture.actor_configs_by_assoc_id,
        port_nodes_by_port_id=fixture.port_nodes_by_port_id,
        replay_invoke_receipts_by_program_instruction_id=(
            fixture.replay_invoke_receipts_by_program_instruction_id
        ),
        replay_invoke_attribute_rows_by_receipt_id=fixture.replay_invoke_attribute_rows_by_receipt_id,
        replay_program_actor_roles_by_id=fixture.replay_program_actor_roles_by_id,
        replay_program_actors_by_id=fixture.replay_program_actors_by_id,
        replay_actor_config_role_configs_by_id=fixture.replay_actor_config_role_configs_by_id,
        replay_node_class_identities_by_id=fixture.replay_node_class_identities_by_id,
        replay_projection_node_identities_by_id=fixture.replay_projection_node_identities_by_id,
    )

    assert fixture.instruction_invoke_id in resolved_invoke_receipts
    assert fixture.instruction_invoke_attribute_id in resolved_invoke_attribute_receipts


def test_resolve_replay_invoke_contracts_rejects_actor_alias_mismatch() -> None:
    fixture = _base_invoke_resolution_fixture()
    actor_role = next(iter(fixture.replay_program_actor_roles_by_id.values()))
    program_actor = fixture.replay_program_actors_by_id[actor_role.program_actor_id]
    mutated_program_actors_by_id = dict(fixture.replay_program_actors_by_id)
    mutated_program_actors_by_id[program_actor.id] = ProgramActor(
        id=program_actor.id,
        program_id=program_actor.program_id,
        program_config_actor_config_id=uuid4(),
        actor_id=program_actor.actor_id,
    )

    with pytest.raises(
        ValueError,
        match="Program ontology replay snapshot actor alias mismatch for invoke receipt",
    ):
        _ = program_run_receipt_loader._resolve_replay_invoke_contracts(  # pyright: ignore[reportPrivateUsage]
            instruction_rows=fixture.instruction_rows,
            instruction_invokes_by_id=fixture.instruction_invokes_by_id,
            invoke_attributes_by_invoke_id=fixture.invoke_attributes_by_invoke_id,
            actor_configs_by_assoc_id=fixture.actor_configs_by_assoc_id,
            port_nodes_by_port_id=fixture.port_nodes_by_port_id,
            replay_invoke_receipts_by_program_instruction_id=(
                fixture.replay_invoke_receipts_by_program_instruction_id
            ),
            replay_invoke_attribute_rows_by_receipt_id=fixture.replay_invoke_attribute_rows_by_receipt_id,
            replay_program_actor_roles_by_id=fixture.replay_program_actor_roles_by_id,
            replay_program_actors_by_id=mutated_program_actors_by_id,
            replay_actor_config_role_configs_by_id=fixture.replay_actor_config_role_configs_by_id,
            replay_node_class_identities_by_id=fixture.replay_node_class_identities_by_id,
            replay_projection_node_identities_by_id=fixture.replay_projection_node_identities_by_id,
        )


def test_resolve_replay_invoke_contracts_rejects_fixed_identity_mismatch() -> None:
    fixture = _base_invoke_resolution_fixture()
    node_class_identity = next(
        iter(fixture.replay_node_class_identities_by_id.values())
    )
    mutated_node_class_identities_by_id = dict(
        fixture.replay_node_class_identities_by_id
    )
    mutated_node_class_identities_by_id[node_class_identity.id] = (
        ProjectionExperienceNodeClassIdentity(
            id=node_class_identity.id,
            projection_experience_oigi_id=node_class_identity.projection_experience_oigi_id,
            projection_experience_node_identity_id=uuid4(),
            class_instance_identity_id=node_class_identity.class_instance_identity_id,
            key=node_class_identity.key,
        )
    )

    with pytest.raises(
        ValueError,
        match="Program ontology replay snapshot identity mismatch for fixed invoke node identity",
    ):
        _ = program_run_receipt_loader._resolve_replay_invoke_contracts(  # pyright: ignore[reportPrivateUsage]
            instruction_rows=fixture.instruction_rows,
            instruction_invokes_by_id=fixture.instruction_invokes_by_id,
            invoke_attributes_by_invoke_id=fixture.invoke_attributes_by_invoke_id,
            actor_configs_by_assoc_id=fixture.actor_configs_by_assoc_id,
            port_nodes_by_port_id=fixture.port_nodes_by_port_id,
            replay_invoke_receipts_by_program_instruction_id=(
                fixture.replay_invoke_receipts_by_program_instruction_id
            ),
            replay_invoke_attribute_rows_by_receipt_id=fixture.replay_invoke_attribute_rows_by_receipt_id,
            replay_program_actor_roles_by_id=fixture.replay_program_actor_roles_by_id,
            replay_program_actors_by_id=fixture.replay_program_actors_by_id,
            replay_actor_config_role_configs_by_id=fixture.replay_actor_config_role_configs_by_id,
            replay_node_class_identities_by_id=mutated_node_class_identities_by_id,
            replay_projection_node_identities_by_id=fixture.replay_projection_node_identities_by_id,
        )
