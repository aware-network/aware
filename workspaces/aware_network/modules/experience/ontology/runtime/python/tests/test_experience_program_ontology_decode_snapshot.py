from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_experience.program.language import (
    PlanExpectEventConfig,
    PlanInput,
    PlanIntentActionConfig,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanSymbolRef,
)
from aware_experience.program import ontology_decode
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_uses_snapshot_contract_for_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_assoc_id = uuid4()
    projection_node_identity_id = uuid4()
    class_instance_identity_id = uuid4()
    instruction_id = uuid4()
    instruction_invoke_id = uuid4()
    function_config_id = uuid4()
    invoke_attribute_id = uuid4()
    invoke_attribute_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(
            SimpleNamespace(
                id=actor_assoc_id,
                alias="resident",
                actor_config_id=actor_config_id,
            ),
        ),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={
            actor_assoc_id: SimpleNamespace(id=actor_config_id, key="resident"),
        },
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story"),
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=projection_node_identity_assoc_id,
                ),
            ),
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={
            projection_node_identity_assoc_id: SimpleNamespace(
                id=projection_node_identity_assoc_id,
                projection_experience_node_identity_id=projection_node_identity_id,
            ),
        },
        projection_node_identities_by_id={
            projection_node_identity_id: SimpleNamespace(
                id=projection_node_identity_id,
                key="front_door",
            ),
        },
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id,
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={
            instruction_invoke_id: SimpleNamespace(
                id=instruction_invoke_id,
                program_config_actor_config_id=actor_assoc_id,
                program_config_port_projection_experience_node_id=port_node_id,
                target_kind="instance",
                function_config_id=function_config_id,
            ),
        },
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={
            instruction_invoke_id: (
                SimpleNamespace(
                    id=invoke_attribute_id,
                    position=1,
                    attribute_config_id=invoke_attribute_config_id,
                    value_expr={"$expr": "local_ref", "name": "channel_number"},
                ),
            ),
        },
        attribute_name_by_id={invoke_attribute_config_id: "channel_number"},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    invocation_plan = await ontology_decode._load_invocation_plan_for_branch(
        branch_id=branch_id,
        environment_id=environment_id,
        program_config_id=program_config_id,
        program_ref="home_story:home_story_scene",
        function_targets={function_config_id: "aware_home.home.Door.unlock"},
    )

    assert invocation_plan.name == "home_story_scene"
    assert len(invocation_plan.actors) == 1
    assert invocation_plan.actors[0].key == "resident"
    assert invocation_plan.actors[0].actor == "resident"

    assert len(invocation_plan.ports) == 1
    port_contract = invocation_plan.ports[0]
    assert port_contract.key == "main"
    assert port_contract.projection == "home_story"
    assert len(port_contract.projection_nodes) == 1
    node_contract = port_contract.projection_nodes[0]
    assert node_contract.key == "door"
    assert node_contract.node == "doors.front_door"
    assert len(node_contract.keys) == 1
    assert node_contract.keys[0].name == "class_instance_identity_id"
    assert node_contract.keys[0].value_expr == str(class_instance_identity_id)

    assert len(invocation_plan.steps) == 1
    invoke_step = cast(PlanInvoke, invocation_plan.steps[0])
    assert invoke_step.kind == "effect"
    assert invoke_step.actor == "resident"
    assert invoke_step.call.target == "aware_home.home.Door.unlock"
    assert isinstance(invoke_step.call.object_expr, PlanSymbolRef)
    assert invoke_step.call.object_expr.name == "door"
    assert len(invoke_step.call.args) == 1
    assert invoke_step.call.args[0].name == "channel_number"
    assert isinstance(invoke_step.call.args[0].value, PlanLocalRef)
    assert invoke_step.call.args[0].value.name == "channel_number"


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_uses_snapshot_contract_for_bind_and_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_assoc_id = uuid4()
    projection_node_identity_id = uuid4()
    class_instance_identity_id = uuid4()
    bind_instruction_id = uuid4()
    bind_instruction_bind_id = uuid4()
    intent_instruction_id = uuid4()
    intent_instruction_intent_id = uuid4()
    action_config_id = uuid4()
    event_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=bind_instruction_id,
                sequence=1,
                type="bind",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=bind_instruction_bind_id,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
            SimpleNamespace(
                id=intent_instruction_id,
                sequence=2,
                type="intent",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=intent_instruction_intent_id,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story"),
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=projection_node_identity_assoc_id,
                ),
            ),
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={
            projection_node_identity_assoc_id: SimpleNamespace(
                id=projection_node_identity_assoc_id,
                projection_experience_node_identity_id=projection_node_identity_id,
            ),
        },
        projection_node_identities_by_id={
            projection_node_identity_id: SimpleNamespace(
                id=projection_node_identity_id,
                key="front_door",
            ),
        },
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id,
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={
            bind_instruction_bind_id: SimpleNamespace(
                id=bind_instruction_bind_id,
                program_config_port_id=port_id,
                view_key="home_story.security.door",
                is_active=True,
            ),
        },
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={
            intent_instruction_intent_id: SimpleNamespace(
                id=intent_instruction_intent_id,
                action_config_id=action_config_id,
                event_config_id=event_config_id,
            ),
        },
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    invocation_plan = await ontology_decode._load_invocation_plan_for_branch(
        branch_id=branch_id,
        environment_id=environment_id,
        program_config_id=program_config_id,
        program_ref="home_story:home_story_scene",
        function_targets={},
    )

    assert invocation_plan.name == "home_story_scene"
    assert len(invocation_plan.steps) == 2

    bind_step = cast(PlanInvoke, invocation_plan.steps[0])
    assert bind_step.kind == "effect"
    assert bind_step.call.target == "bind"
    assert len(bind_step.call.args) == 3
    bind_port_arg = bind_step.call.args[0]
    assert bind_port_arg.name == "port"
    assert isinstance(bind_port_arg.value, PlanSymbolRef)
    assert bind_port_arg.value.name == "program.port.main"
    bind_view_arg = bind_step.call.args[1]
    assert bind_view_arg.name == "view_key"
    assert bind_view_arg.value == "home_story.security.door"
    bind_is_active_arg = bind_step.call.args[2]
    assert bind_is_active_arg.name == "is_active"
    assert bind_is_active_arg.value is True

    intent_step = cast(PlanIntentActionConfig, invocation_plan.steps[1])
    assert intent_step.action_ref == str(action_config_id)
    assert intent_step.event_ref == str(event_config_id)


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_replay_uses_bind_receipt_view(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    program_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    class_instance_identity_id = uuid4()
    bind_instruction_id = uuid4()
    bind_instruction_bind_id = uuid4()
    replay_bind_receipt_id = uuid4()
    replay_view_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=bind_instruction_id,
                sequence=1,
                type="bind",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=bind_instruction_bind_id,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story")
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=None,
                ),
            )
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={
            bind_instruction_bind_id: SimpleNamespace(
                id=bind_instruction_bind_id,
                program_config_port_id=port_id,
                view_key="home_story.security.door",
                is_active=True,
            ),
        },
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
        replay_bind_receipts_by_instruction_bind_id={
            bind_instruction_bind_id: SimpleNamespace(
                id=replay_bind_receipt_id,
                program_impl_instruction_bind_id=bind_instruction_bind_id,
                projection_experience_view_id=replay_view_id,
            ),
        },
        replay_views_by_bind_receipt_id={
            replay_bind_receipt_id: SimpleNamespace(
                id=replay_view_id, name="home_story.replay.door"
            ),
        },
        replay_invoke_receipts_by_instruction_invoke_id={},
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        assert program_id is not None
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    invocation_plan = await ontology_decode._load_invocation_plan_for_branch(
        branch_id=branch_id,
        environment_id=environment_id,
        program_config_id=program_config_id,
        program_ref="home_story:home_story_scene",
        function_targets={},
        program_id=program_id,
    )

    assert len(invocation_plan.steps) == 1
    bind_step = cast(PlanInvoke, invocation_plan.steps[0])
    assert bind_step.call.target == "bind"
    assert bind_step.call.args[1].name == "view_key"
    assert bind_step.call.args[1].value == "home_story.replay.door"


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_replay_fail_closes_when_bind_receipt_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    program_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    class_instance_identity_id = uuid4()
    bind_instruction_id = uuid4()
    bind_instruction_bind_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=bind_instruction_id,
                sequence=1,
                type="bind",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=bind_instruction_bind_id,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story")
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=None,
                ),
            )
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={
            bind_instruction_bind_id: SimpleNamespace(
                id=bind_instruction_bind_id,
                program_config_port_id=port_id,
                view_key="home_story.security.door",
                is_active=True,
            ),
        },
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
        replay_bind_receipts_by_instruction_bind_id={},
        replay_views_by_bind_receipt_id={},
        replay_invoke_receipts_by_instruction_invoke_id={},
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        assert program_id is not None
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology replay snapshot missing ProgramTurnInstructionBind",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
            program_id=program_id,
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_replay_fail_closes_when_invoke_receipt_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    program_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_assoc_id = uuid4()
    projection_node_identity_id = uuid4()
    class_instance_identity_id = uuid4()
    invoke_instruction_id = uuid4()
    invoke_instruction_invoke_id = uuid4()
    function_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(
            SimpleNamespace(
                id=actor_assoc_id,
                alias="resident",
                actor_config_id=actor_config_id,
            ),
        ),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=invoke_instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=invoke_instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={
            actor_assoc_id: SimpleNamespace(id=actor_config_id, key="resident"),
        },
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story")
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=projection_node_identity_assoc_id,
                ),
            )
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={
            projection_node_identity_assoc_id: SimpleNamespace(
                id=projection_node_identity_assoc_id,
                projection_experience_node_identity_id=projection_node_identity_id,
            ),
        },
        projection_node_identities_by_id={
            projection_node_identity_id: SimpleNamespace(
                id=projection_node_identity_id,
                key="front_door",
            ),
        },
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=invoke_instruction_invoke_id,
                program_config_actor_config_id=actor_assoc_id,
                program_config_port_projection_experience_node_id=port_node_id,
                target_kind="instance",
                function_config_id=function_config_id,
            ),
        },
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
        replay_bind_receipts_by_instruction_bind_id={},
        replay_views_by_bind_receipt_id={},
        replay_invoke_receipts_by_instruction_invoke_id={},
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        assert program_id is not None
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology replay snapshot missing ProgramTurnInstructionInvoke",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={function_config_id: "aware_home.home.Door.unlock"},
            program_id=program_id,
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_replay_uses_invoke_receipts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    program_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_assoc_id = uuid4()
    projection_node_identity_id = uuid4()
    class_instance_identity_id = uuid4()
    invoke_instruction_id = uuid4()
    invoke_instruction_invoke_id = uuid4()
    replay_invoke_receipt_id = uuid4()
    function_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(
            SimpleNamespace(
                id=actor_assoc_id,
                alias="resident",
                actor_config_id=actor_config_id,
            ),
        ),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=invoke_instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=invoke_instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={
            actor_assoc_id: SimpleNamespace(id=actor_config_id, key="resident"),
        },
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story")
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=projection_node_identity_assoc_id,
                ),
            )
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={
            projection_node_identity_assoc_id: SimpleNamespace(
                id=projection_node_identity_assoc_id,
                projection_experience_node_identity_id=projection_node_identity_id,
            ),
        },
        projection_node_identities_by_id={
            projection_node_identity_id: SimpleNamespace(
                id=projection_node_identity_id,
                key="front_door",
            ),
        },
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=invoke_instruction_invoke_id,
                program_config_actor_config_id=actor_assoc_id,
                program_config_port_projection_experience_node_id=port_node_id,
                target_kind="instance",
                function_config_id=function_config_id,
            ),
        },
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
        replay_bind_receipts_by_instruction_bind_id={},
        replay_views_by_bind_receipt_id={},
        replay_invoke_receipts_by_instruction_invoke_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=replay_invoke_receipt_id,
                program_impl_instruction_invoke_id=invoke_instruction_invoke_id,
            ),
        },
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        assert program_id is not None
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    invocation_plan = await ontology_decode._load_invocation_plan_for_branch(
        branch_id=branch_id,
        environment_id=environment_id,
        program_config_id=program_config_id,
        program_ref="home_story:home_story_scene",
        function_targets={function_config_id: "aware_home.home.Door.unlock"},
        program_id=program_id,
    )

    assert len(invocation_plan.steps) == 1
    invoke_step = cast(PlanInvoke, invocation_plan.steps[0])
    assert invoke_step.actor == "resident"
    assert invoke_step.call.target == "aware_home.home.Door.unlock"
    assert isinstance(invoke_step.call.object_expr, PlanSymbolRef)
    assert invoke_step.call.object_expr.name == "door"


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_replay_fail_closes_when_invoke_argument_receipt_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    program_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_assoc_id = uuid4()
    projection_node_identity_id = uuid4()
    class_instance_identity_id = uuid4()
    invoke_instruction_id = uuid4()
    invoke_instruction_invoke_id = uuid4()
    replay_invoke_receipt_id = uuid4()
    invoke_attribute_id = uuid4()
    invoke_attribute_config_id = uuid4()
    function_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(
            SimpleNamespace(
                id=actor_assoc_id,
                alias="resident",
                actor_config_id=actor_config_id,
            ),
        ),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=invoke_instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=invoke_instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={
            actor_assoc_id: SimpleNamespace(id=actor_config_id, key="resident"),
        },
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story")
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=projection_node_identity_assoc_id,
                ),
            )
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={
            projection_node_identity_assoc_id: SimpleNamespace(
                id=projection_node_identity_assoc_id,
                projection_experience_node_identity_id=projection_node_identity_id,
            ),
        },
        projection_node_identities_by_id={
            projection_node_identity_id: SimpleNamespace(
                id=projection_node_identity_id,
                key="front_door",
            ),
        },
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=invoke_instruction_invoke_id,
                program_config_actor_config_id=actor_assoc_id,
                program_config_port_projection_experience_node_id=port_node_id,
                target_kind="instance",
                function_config_id=function_config_id,
            ),
        },
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={
            invoke_instruction_invoke_id: (
                SimpleNamespace(
                    id=invoke_attribute_id,
                    position=1,
                    attribute_config_id=invoke_attribute_config_id,
                    value_expr={"$expr": "local_ref", "name": "channel_number"},
                ),
            ),
        },
        attribute_name_by_id={invoke_attribute_config_id: "channel_number"},
        replay_bind_receipts_by_instruction_bind_id={},
        replay_views_by_bind_receipt_id={},
        replay_invoke_receipts_by_instruction_invoke_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=replay_invoke_receipt_id,
                program_impl_instruction_invoke_id=invoke_instruction_invoke_id,
            ),
        },
        replay_invoke_attribute_receipts_by_instruction_invoke_attribute_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        program_id: UUID | None = None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        assert program_id is not None
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology replay snapshot missing invoke-argument receipt",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={function_config_id: "aware_home.home.Door.unlock"},
            program_id=program_id,
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_uses_snapshot_contract_for_input_let_expect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    input_config_id = uuid4()
    input_instruction_id = uuid4()
    input_instruction_input_id = uuid4()
    let_instruction_id = uuid4()
    let_instruction_let_id = uuid4()
    expect_instruction_id = uuid4()
    expect_instruction_expect_id = uuid4()
    event_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(
            SimpleNamespace(
                id=input_config_id,
                name="channel_number",
                source="plan.channel_number",
                default_expr=7,
                required=True,
            ),
        ),
        instruction_rows=(
            SimpleNamespace(
                id=input_instruction_id,
                sequence=1,
                type="input",
                instruction_input_id=input_instruction_input_id,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
            SimpleNamespace(
                id=let_instruction_id,
                sequence=2,
                type="let",
                instruction_input_id=None,
                instruction_let_id=let_instruction_let_id,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
            SimpleNamespace(
                id=expect_instruction_id,
                sequence=3,
                type="expect",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=expect_instruction_expect_id,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={
            input_instruction_input_id: SimpleNamespace(
                id=input_instruction_input_id,
                program_config_input_config_id=input_config_id,
            ),
        },
        instruction_lets_by_id={
            let_instruction_let_id: SimpleNamespace(
                id=let_instruction_let_id,
                name="selected_channel",
                value_expr={"$expr": "local_ref", "name": "channel_number"},
            ),
        },
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={
            expect_instruction_expect_id: SimpleNamespace(
                id=expect_instruction_expect_id,
                event_config_id=event_config_id,
                required=True,
            ),
        },
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    invocation_plan = await ontology_decode._load_invocation_plan_for_branch(
        branch_id=branch_id,
        environment_id=environment_id,
        program_config_id=program_config_id,
        program_ref="home_story:home_story_scene",
        function_targets={},
    )

    assert invocation_plan.name == "home_story_scene"
    assert len(invocation_plan.steps) == 3

    input_step = cast(PlanInput, invocation_plan.steps[0])
    assert input_step.name == "channel_number"
    assert isinstance(input_step.source, PlanSymbolRef)
    assert input_step.source.name == "plan.channel_number"
    assert input_step.default == 7
    assert input_step.required is True

    let_step = cast(PlanLet, invocation_plan.steps[1])
    assert let_step.name == "selected_channel"
    assert isinstance(let_step.value, PlanLocalRef)
    assert let_step.value.name == "channel_number"

    expect_step = cast(PlanExpectEventConfig, invocation_plan.steps[2])
    assert expect_step.ref == str(event_config_id)
    assert expect_step.required is True


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_bind_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    class_instance_identity_id = uuid4()
    bind_instruction_id = uuid4()
    bind_instruction_bind_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=bind_instruction_id,
                sequence=1,
                type="bind",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=bind_instruction_bind_id,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story"),
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=None,
                ),
            ),
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionBind",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_invoke_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    invoke_instruction_id = uuid4()
    invoke_instruction_invoke_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=invoke_instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=invoke_instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionInvoke",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_intent_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    intent_instruction_id = uuid4()
    intent_instruction_intent_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=intent_instruction_id,
                sequence=1,
                type="intent",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=intent_instruction_intent_id,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionIntent",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_input_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    input_instruction_id = uuid4()
    input_instruction_input_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=input_instruction_id,
                sequence=1,
                type="input",
                instruction_input_id=input_instruction_input_id,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionInput",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_let_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    let_instruction_id = uuid4()
    let_instruction_let_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=let_instruction_id,
                sequence=1,
                type="let",
                instruction_input_id=None,
                instruction_let_id=let_instruction_let_id,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionLet",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_expect_snapshot_entry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    expect_instruction_id = uuid4()
    expect_instruction_expect_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(),
        port_rows=(),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=expect_instruction_id,
                sequence=1,
                type="expect",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=None,
                instruction_expect_id=expect_instruction_expect_id,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={},
        projections_by_port_id={},
        port_nodes_by_port_id={},
        projection_nodes_by_id={},
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={},
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={},
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={},
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing ProgramImplInstructionExpect",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={},
        )


@pytest.mark.asyncio
async def test_load_invocation_plan_for_branch_fail_closes_when_invoke_attribute_name_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    program_impl_id = uuid4()
    actor_assoc_id = uuid4()
    actor_config_id = uuid4()
    port_id = uuid4()
    projection_id = uuid4()
    port_node_id = uuid4()
    projection_node_id = uuid4()
    class_instance_identity_id = uuid4()
    invoke_instruction_id = uuid4()
    invoke_instruction_invoke_id = uuid4()
    function_config_id = uuid4()
    invoke_attribute_id = uuid4()
    invoke_attribute_config_id = uuid4()
    branch_id = uuid4()
    environment_id = uuid4()

    snapshot_obj: object = SimpleNamespace(
        program_config=SimpleNamespace(
            id=program_config_id, key="home_story_scene_config"
        ),
        program_impl=SimpleNamespace(id=program_impl_id, key="home_story_scene"),
        actor_rows=(
            SimpleNamespace(
                id=actor_assoc_id,
                alias="resident",
                actor_config_id=actor_config_id,
            ),
        ),
        port_rows=(
            SimpleNamespace(
                id=port_id,
                key="main",
                projection_id=projection_id,
                intent=None,
            ),
        ),
        input_config_rows=(),
        instruction_rows=(
            SimpleNamespace(
                id=invoke_instruction_id,
                sequence=1,
                type="invoke",
                instruction_input_id=None,
                instruction_let_id=None,
                instruction_bind_id=None,
                instruction_invoke_id=invoke_instruction_invoke_id,
                instruction_expect_id=None,
                instruction_intent_id=None,
            ),
        ),
        actor_configs_by_assoc_id={
            actor_assoc_id: SimpleNamespace(id=actor_config_id, key="resident"),
        },
        projections_by_port_id={
            port_id: SimpleNamespace(id=projection_id, name="home_story"),
        },
        port_nodes_by_port_id={
            port_id: (
                SimpleNamespace(
                    id=port_node_id,
                    key="door",
                    projection_experience_node_id=projection_node_id,
                    projection_node_identity_id=None,
                ),
            ),
        },
        projection_nodes_by_id={
            projection_node_id: SimpleNamespace(id=projection_node_id, key="doors"),
        },
        projection_node_identity_assocs_by_id={},
        projection_node_identities_by_id={},
        class_instance_identity_ids_by_port_node_id={
            port_node_id: class_instance_identity_id
        },
        instruction_inputs_by_id={},
        instruction_lets_by_id={},
        instruction_binds_by_id={},
        instruction_invokes_by_id={
            invoke_instruction_invoke_id: SimpleNamespace(
                id=invoke_instruction_invoke_id,
                program_config_actor_config_id=actor_assoc_id,
                program_config_port_projection_experience_node_id=port_node_id,
                target_kind="instance",
                function_config_id=function_config_id,
            ),
        },
        instruction_expects_by_id={},
        instruction_intents_by_id={},
        invoke_attributes_by_invoke_id={
            invoke_instruction_invoke_id: (
                SimpleNamespace(
                    id=invoke_attribute_id,
                    position=1,
                    attribute_config_id=invoke_attribute_config_id,
                    value_expr={"$expr": "local_ref", "name": "channel_number"},
                ),
            ),
        },
        attribute_name_by_id={},
    )
    snapshot = cast(ProgramOntologySnapshot, cast(object, snapshot_obj))

    async def _snapshot_loader(
        *,
        branch_id: UUID,
        environment_id: UUID,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
    ) -> ProgramOntologySnapshot:
        assert preferred_program_impl_key == "home_story_scene"
        _ = branch_id, environment_id, program_config_id
        return snapshot

    monkeypatch.setattr(
        ontology_decode, "_load_program_ontology_snapshot_for_branch", _snapshot_loader
    )

    with pytest.raises(
        ValueError,
        match="Program ontology snapshot missing invoke attribute name",
    ):
        await ontology_decode._load_invocation_plan_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref="home_story:home_story_scene",
            function_targets={function_config_id: "aware_home.home.Door.unlock"},
        )
