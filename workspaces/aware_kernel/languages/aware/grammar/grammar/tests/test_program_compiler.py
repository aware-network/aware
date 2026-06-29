from __future__ import annotations

from pathlib import Path

import pytest

from aware_grammar.program import (
    ProgramConfigApplyCall,
    ProgramConfigApplyRef,
    PlanCall,
    PlanExpectEventConfig,
    PlanInput,
    PlanIntentActionConfig,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanSymbolRef,
    ProgramConfigInstructionBindPayload,
    ProgramConfigInstructionInputPayload,
    ProgramConfigInstructionInvokePayload,
    ProgramConfigPortProjectionNodeIdentityContract,
    ProgramConfigPlan,
    ProgramConfigPortContract,
    ProgramConfigWindowLayoutContract,
    ProgramConfigWindowSectionContract,
    ProgramConfigWindowSlotMappingContract,
    ProgramConfigReferenceCatalog,
    ProgramTypeIdContract,
    ProgramCompileError,
    build_type_id_registry_from_aware_sources,
    compile_program_config_apply_calls,
    compile_program_apply_calls,
    compile_program_config_graph_apply_calls,
    compile_program_config_plans,
    compile_invocation_plans,
)


_TYPE_ID_REGISTRY = build_type_id_registry_from_aware_sources(
    """\
class ActionConfig {
    id primary(name String) {
        namespace NS_REACTIVITY
        template "action_config:{name_norm}"
        let name_norm = normalize(name, casefold, strip)
    }
}
""",
    """\
class EventConfig {
    id primary(name String) {
        namespace NS_REACTIVITY
        template "event_config:{name_norm}"
        let name_norm = normalize(name, casefold, strip)
    }
}
""",
)

_TYPE_ID_REGISTRY_FROM_CONSTRUCTOR_KEYS = build_type_id_registry_from_aware_sources(
    """\
class EventConfig {
    fn create_event_config construct(name String key, description String?) -> EventConfig {
    }
}
""",
    default_module_id="reactivity",
)


_PROGRAM_CONFIG_INSTRUCTION_TYPE_MEMBERS = {
    "input",
    "let",
    "bind",
    "invoke",
    "expect",
    "intent",
}


def test_compile_invocation_plans_sample_file() -> None:
    src = Path(__file__).parent / "samples" / "reactivity_seed_program.aware"
    plans = compile_invocation_plans(src.read_text(encoding="utf-8"))

    assert len(plans) == 1
    plan = plans[0]
    assert plan.name == "ReactivitySeed"
    assert len(plan.steps) == 2

    let_step = plan.steps[0]
    assert isinstance(let_step, PlanLet)
    assert let_step.name == "schema"
    assert let_step.value == {"name": "conversation.created", "version": 1}

    invoke = plan.steps[1]
    assert isinstance(invoke, PlanInvoke)
    assert invoke.call.target == "event.EventConfig.create"
    assert [a.name for a in invoke.call.args] == ["name", "description", "event_schema"]
    assert isinstance(invoke.call.args[2].value, PlanLocalRef)
    assert invoke.call.args[2].value.name == "schema"


def test_compile_canonicalizes_json_object_keys() -> None:
    plans = compile_invocation_plans(
        """\
program P {
    let x = {"b": 1, "a": 2}
    call foo.bar()
}
"""
    )
    let_step = plans[0].steps[0]
    assert isinstance(let_step, PlanLet)
    assert isinstance(let_step.value, dict)
    assert list(let_step.value.keys()) == ["a", "b"]


def test_compile_rejects_positional_after_keyword() -> None:
    with pytest.raises(
        ProgramCompileError, match="Positional arguments cannot appear after keyword"
    ):
        _ = compile_invocation_plans(
            """\
program P {
    call foo.bar(a=1, 2)
}
"""
        )


def test_compile_input_expect_intent_contract_steps() -> None:
    plans = compile_invocation_plans(
        """\
program Contract {
    input thread_id from plan.thread_id
    input event_name from plan.event_config_name default "conversation.message.created"
    let event_config_id = reactivity.stable_event_config_id(name=event_name)
    let action_config_id = reactivity.stable_action_config_id(name="conversation.message.created.execute")
    expect event_config event_config_id required
    intent action_config action_config_id on event_config event_config_id
    call event.EventConfig.create(name=event_name)
}
"""
    )

    plan = plans[0]
    assert len(plan.steps) == 7

    input_required = plan.steps[0]
    assert isinstance(input_required, PlanInput)
    assert input_required.name == "thread_id"
    assert input_required.required is True
    assert input_required.default is None

    input_optional = plan.steps[1]
    assert isinstance(input_optional, PlanInput)
    assert input_optional.name == "event_name"
    assert input_optional.required is False
    assert input_optional.default == "conversation.message.created"

    expect_step = plan.steps[4]
    assert isinstance(expect_step, PlanExpectEventConfig)
    assert expect_step.required is True
    assert isinstance(expect_step.ref, PlanLocalRef)
    assert expect_step.ref.name == "event_config_id"

    intent_step = plan.steps[5]
    assert isinstance(intent_step, PlanIntentActionConfig)
    assert isinstance(intent_step.action_ref, PlanLocalRef)
    assert intent_step.action_ref.name == "action_config_id"
    assert isinstance(intent_step.event_ref, PlanLocalRef)
    assert intent_step.event_ref.name == "event_config_id"

    invoke_step = plan.steps[6]
    assert isinstance(invoke_step, PlanInvoke)
    assert invoke_step.kind == "effect"


def test_compile_signature_inputs_and_stable_id_sugar() -> None:
    plans = compile_invocation_plans(
        """\
program Contract(
    event_config_name String,
    action_config_name String = "conversation.message.created.execute"
) {
    let event_config_id = EventConfig.id(name=event_config_name)
    let action_config_id = ActionConfig.id(name=action_config_name)
    expect event_config event_config_id required
    intent action_config action_config_id on event_config event_config_id
}
""",
        type_id_registry=_TYPE_ID_REGISTRY,
    )

    plan = plans[0]
    assert len(plan.steps) == 6

    required_input = plan.steps[0]
    assert isinstance(required_input, PlanInput)
    assert required_input.name == "event_config_name"
    assert required_input.type_ref == "string"
    assert isinstance(required_input.source, PlanSymbolRef)
    assert required_input.source.name == "event_config_name"
    assert required_input.required is True

    optional_input = plan.steps[1]
    assert isinstance(optional_input, PlanInput)
    assert optional_input.name == "action_config_name"
    assert optional_input.type_ref == "string"
    assert optional_input.required is False
    assert optional_input.default == "conversation.message.created.execute"

    event_let = plan.steps[2]
    assert isinstance(event_let, PlanLet)
    assert isinstance(event_let.value, PlanCall)
    assert event_let.value.target == "reactivity.stable_event_config_id"

    action_let = plan.steps[3]
    assert isinstance(action_let, PlanLet)
    assert isinstance(action_let.value, PlanCall)
    assert action_let.value.target == "reactivity.stable_action_config_id"


def test_compile_signature_input_types_use_primitive_codec_ssot() -> None:
    plans = compile_invocation_plans(
        """\
program TypeNorm(flag Bool, count integer) {
    let x = flag
}
"""
    )

    plan = plans[0]
    first_input = plan.steps[0]
    assert isinstance(first_input, PlanInput)
    assert first_input.name == "flag"
    assert first_input.type_ref == "boolean"

    second_input = plan.steps[1]
    assert isinstance(second_input, PlanInput)
    assert second_input.name == "count"
    assert second_input.type_ref == "integer"


def test_compile_signature_input_type_accepts_fully_qualified_contract_refs() -> None:
    plans = compile_invocation_plans(
        """\
program TypeContract(status alpha.types.Status) {
    let x = status
}
"""
    )

    plan = plans[0]
    input_step = plan.steps[0]
    assert isinstance(input_step, PlanInput)
    assert input_step.name == "status"
    assert input_step.type_ref == "alpha.types.Status"


def test_compile_type_id_sugar_auto_resolves_from_workspace_contracts() -> None:
    plans = compile_invocation_plans(
        """\
program AutoTypeId(name String) {
    let event_config_id = EventConfig.id(name=name)
}
"""
    )
    plan = plans[0]
    assert len(plan.steps) == 2
    let_step = plan.steps[1]
    assert isinstance(let_step, PlanLet)
    assert isinstance(let_step.value, PlanCall)
    assert let_step.value.target == "reactivity.stable_event_config_id"


def test_compile_rejects_unknown_stable_id_sugar_target() -> None:
    with pytest.raises(ProgramCompileError, match="Unknown Type.id sugar target"):
        _ = compile_invocation_plans(
            """\
program Bad(x String) {
    let y = UnknownThing.id(name=x)
}
"""
        )


def test_compile_rejects_unsupported_program_parameter_type() -> None:
    with pytest.raises(ProgramCompileError, match="unsupported type"):
        _ = compile_invocation_plans(
            """\
program BadType(x NotAType) {
    let y = x
}
"""
        )


def test_build_type_id_registry_from_aware_sources() -> None:
    registry = build_type_id_registry_from_aware_sources(
        """\
class ConditionConfig {
    id primary(name String) {
        namespace NS_REACTIVITY
        template "condition_config:{name_norm}"
        let name_norm = normalize(name, casefold, strip)
    }
}
"""
    )
    assert "ConditionConfig" in registry
    contract = registry["ConditionConfig"]
    assert isinstance(contract, ProgramTypeIdContract)
    assert contract.class_name == "ConditionConfig"
    assert contract.key == "primary"
    assert contract.namespace == "NS_REACTIVITY"
    assert contract.target == "reactivity.stable_condition_config_id"
    assert contract.identity_keys == ("name",)


def test_build_type_id_registry_from_constructor_key_contracts() -> None:
    registry = build_type_id_registry_from_aware_sources(
        """\
class EventConfig {
    fn create_event_config construct(name String key, description String?) -> EventConfig {
    }
}
""",
        default_module_id="reactivity",
    )
    contract = registry["EventConfig"]
    assert isinstance(contract, ProgramTypeIdContract)
    assert contract.class_name == "EventConfig"
    assert contract.key == "primary"
    assert contract.namespace == "NS_REACTIVITY"
    assert contract.target == "reactivity.stable_event_config_id"
    assert contract.source == "constructor_key"
    assert contract.identity_keys == ("name",)


def test_build_type_id_registry_rejects_ambiguous_constructor_key_contracts() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"multiple constructor key signatures",
    ):
        _ = build_type_id_registry_from_aware_sources(
            """\
class EventConfig {
    fn create_by_name construct(name String key) -> EventConfig {
    }

    fn create_by_alias construct(alias String key) -> EventConfig {
    }
}
""",
            default_module_id="reactivity",
        )


def test_compile_type_id_sugar_with_constructor_key_contracts() -> None:
    plans = compile_invocation_plans(
        """\
program ConstructorKeySugar(name String) {
    let event_config_id = EventConfig.id(name=name)
}
""",
        type_id_registry=_TYPE_ID_REGISTRY_FROM_CONSTRUCTOR_KEYS,
    )

    plan = plans[0]
    let_step = plan.steps[1]
    assert isinstance(let_step, PlanLet)
    assert isinstance(let_step.value, PlanCall)
    assert let_step.value.target == "reactivity.stable_event_config_id"


def test_compile_type_id_sugar_rejects_missing_identity_key_args() -> None:
    with pytest.raises(ProgramCompileError, match="identity-key contract mismatch"):
        _ = compile_invocation_plans(
            """\
program ConstructorKeySugar(name String) {
    let event_config_id = EventConfig.id(alias=name)
}
""",
            type_id_registry=_TYPE_ID_REGISTRY_FROM_CONSTRUCTOR_KEYS,
        )


def test_compile_type_id_sugar_rejects_extra_identity_key_args() -> None:
    with pytest.raises(ProgramCompileError, match="identity-key contract mismatch"):
        _ = compile_invocation_plans(
            """\
program ConstructorKeySugar(name String) {
    let event_config_id = EventConfig.id(name=name, alias=name)
}
""",
            type_id_registry=_TYPE_ID_REGISTRY_FROM_CONSTRUCTOR_KEYS,
        )


def test_compile_type_id_sugar_resolves_qualified_owner_contract() -> None:
    plans = compile_invocation_plans(
        """\
program QualifiedTypeId(thread_id UUID) {
    let resolved_id = conversation.Thread.id(thread_id=thread_id)
}
""",
        type_id_registry={
            "conversation.Thread": ProgramTypeIdContract(
                class_name="Thread",
                key="primary",
                namespace="NS_CONVERSATION",
                target="conversation.stable_thread_id",
                source="constructor_key",
                identity_keys=("thread_id",),
            )
        },
    )
    plan = plans[0]
    let_step = plan.steps[1]
    assert isinstance(let_step, PlanLet)
    assert isinstance(let_step.value, PlanCall)
    assert let_step.value.target == "conversation.stable_thread_id"


def test_compile_type_id_sugar_rejects_ambiguous_unqualified_contract() -> None:
    with pytest.raises(ProgramCompileError, match="Ambiguous Type.id sugar target"):
        _ = compile_invocation_plans(
            """\
program AmbiguousTypeId(thread_id UUID) {
    let resolved_id = Thread.id(thread_id=thread_id)
}
""",
            type_id_registry={
                "conversation.Thread": ProgramTypeIdContract(
                    class_name="Thread",
                    key="primary",
                    namespace="NS_CONVERSATION",
                    target="conversation.stable_thread_id",
                    source="constructor_key",
                    identity_keys=("thread_id",),
                ),
                "environment.Thread": ProgramTypeIdContract(
                    class_name="Thread",
                    key="primary",
                    namespace="NS_ENVIRONMENT",
                    target="environment.stable_thread_id",
                    source="constructor_key",
                    identity_keys=("thread_id",),
                ),
            },
        )


def test_compile_program_config_plan_lowers_contract_and_bind() -> None:
    plans = compile_program_config_plans(
        """\
program ConversationTurn {
    actor assistant assistant
    port main environment {
        intent="conversation.main"
        projection="Conversation"
        node thread thread.main
    }
    call plan.layout(
        key="conversation.primary",
        is_default=true
    )
    call plan.section(
        layout_key="conversation.primary",
        key="main",
        order=0,
        is_visible=true,
        flex=1.0
    )
    call plan.slot(
        layout_key="conversation.primary",
        port=program.port.main,
        section_key="main",
        on_bind="replace",
        is_visible_default=true
    )
    input conversation_branch_id from plan.conversation_branch_id
    let event_config_id = reactivity.stable_event_config_id(name="conversation.message.created")
    expect event_config event_config_id required
    intent action_config reactivity.stable_action_config_id(name="conv.msg.created.ex") on event_config event_config_id
    bind main conversation.main
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )

    assert len(plans) == 1
    plan = plans[0]
    assert isinstance(plan, ProgramConfigPlan)
    assert plan.name == "ConversationTurn"
    assert plan.key == "ConversationTurn"
    assert len(plan.ports) == 1
    assert isinstance(plan.ports[0], ProgramConfigPortContract)
    assert plan.ports[0].key == "main"
    assert plan.ports[0].intent == "conversation.main"
    assert plan.ports[0].projection == "Conversation"
    assert plan.ports[0].projection_node_identities == (
        ProgramConfigPortProjectionNodeIdentityContract(
            key="thread",
            node="thread",
            identity="main",
        ),
    )
    assert len(plan.layouts) == 1
    assert isinstance(plan.layouts[0], ProgramConfigWindowLayoutContract)
    assert plan.layouts[0].key == "conversation.primary"
    assert plan.layouts[0].is_default is True
    assert len(plan.sections) == 1
    assert isinstance(plan.sections[0], ProgramConfigWindowSectionContract)
    assert plan.sections[0].layout_key == "conversation.primary"
    assert plan.sections[0].key == "main"
    assert plan.sections[0].order == 0
    assert plan.sections[0].is_visible is True
    assert plan.sections[0].flex == 1.0
    assert len(plan.slot_mappings) == 1
    assert isinstance(plan.slot_mappings[0], ProgramConfigWindowSlotMappingContract)
    assert plan.slot_mappings[0].layout_key == "conversation.primary"
    assert plan.slot_mappings[0].port_ref == "program.port.main"
    assert plan.slot_mappings[0].section_key == "main"
    assert plan.slot_mappings[0].on_bind == "replace"
    assert plan.slot_mappings[0].is_visible_default is True
    assert len(plan.instructions) == 6

    input_step = plan.instructions[0]
    assert input_step.step_id == "s0000_input"
    assert input_step.type == "input"
    assert isinstance(
        input_step.instruction_input, ProgramConfigInstructionInputPayload
    )
    assert input_step.instruction_input.name == "conversation_branch_id"
    assert input_step.instruction_input.source == "plan.conversation_branch_id"

    bind_step = plan.instructions[4]
    assert bind_step.step_id == "s0004_bind"
    assert bind_step.type == "bind"
    assert isinstance(bind_step.instruction_bind, ProgramConfigInstructionBindPayload)
    assert isinstance(bind_step.instruction_bind.port_ref, PlanSymbolRef)
    assert bind_step.instruction_bind.port_ref.name == "program.port.main"
    assert bind_step.instruction_bind.view_key == "conversation.main"
    assert bind_step.instruction_bind.is_active is True

    invoke_step = plan.instructions[5]
    assert invoke_step.step_id == "s0005_invoke"
    assert invoke_step.type == "invoke"
    assert isinstance(
        invoke_step.instruction_invoke, ProgramConfigInstructionInvokePayload
    )
    assert (
        invoke_step.instruction_invoke.function_ref
        == "conversation.Conversation.add_message"
    )
    assert invoke_step.instruction_invoke.actor_ref == PlanSymbolRef(
        name="program.actor.assistant"
    )
    assert invoke_step.instruction_invoke.object_ref == PlanSymbolRef(name="thread")
    assert invoke_step.instruction_invoke.target_kind == "instance"
    assert len(invoke_step.instruction_invoke.args) == 1
    assert invoke_step.instruction_invoke.args[0].name == "text"


def test_compile_program_config_plan_allows_port_declarations_after_signature_params() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program EnvironmentAnchor(
    environment_id UUID,
    environment_branch_id UUID
) {
    port environment Environment {
        node environment environment.main
        \"\"\"Environment entry port.\"\"\"
    }
    bind environment Environment.main
}
"""
    )[0]

    assert len(plan.ports) == 1
    port = plan.ports[0]
    assert port.key == "environment"
    assert port.intent is None
    assert port.projection == "Environment"
    assert port.projection_node_identities == (
        ProgramConfigPortProjectionNodeIdentityContract(
            key="environment",
            node="environment",
            identity="main",
        ),
    )

    # Signature params still lower as runtime input instructions.
    assert len(plan.instructions) == 3
    assert plan.instructions[0].type == "input"
    assert plan.instructions[1].type == "input"
    assert plan.instructions[2].type == "bind"
    assert plan.instructions[2].instruction_bind is not None
    assert isinstance(plan.instructions[2].instruction_bind.port_ref, PlanSymbolRef)
    assert (
        plan.instructions[2].instruction_bind.port_ref.name
        == "program.port.environment"
    )
    assert plan.instructions[2].instruction_bind.view_key == "Environment.main"


def test_compile_program_config_plan_rejects_local_binding_in_port_branch_args() -> (
    None
):
    with pytest.raises(
        ProgramCompileError,
        match=r"port declarations must appear at top of program body",
    ):
        _ = compile_program_config_plans(
            """\
program BadPortBranchArgs {
    let eid = plan.environment_id
    port environment Environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
        )


def test_compile_program_config_plan_rejects_port_node_without_identity_or_keys() -> (
    None
):
    with pytest.raises(
        ProgramCompileError,
        match=r"port node ref must use `<opg-node>\.<identity>` or provide resolver keys via `<opg-node>\(<keys\.\.\.>\)`",
    ):
        _ = compile_program_config_plans(
            """\
program BadPortNodeShape(environment_id UUID) {
    port environment Environment {
        node current doors
    }
}
"""
        )


def test_compile_program_config_plan_rejects_port_object_id_arg() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"port object_id is not supported",
    ):
        _ = compile_program_config_plans(
            """\
program PortObjectTarget(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
        object_id=plan.thread_id
    }
}
"""
        )


def test_compile_program_config_plan_rejects_port_branch_id_arg() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"port branch_id is not supported",
    ):
        _ = compile_program_config_plans(
            """\
program PortBranchTarget(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
        branch_id=plan.thread_id
    }
}
"""
        )


def test_compile_program_config_plan_rejects_port_opg_arg() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"port opg is not supported",
    ):
        _ = compile_program_config_plans(
            """\
program PortLaneTarget(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
        opg="Conversation"
    }
}
"""
        )


def test_compile_program_config_plan_rejects_port_missing_projection_or_branch() -> (
    None
):
    with pytest.raises(
        ValueError,
        match=r"parse errors",
    ):
        _ = compile_program_config_plans(
            """\
program PortMissingResolver(environment_id UUID) {
    port main(environment_id) {}
}
"""
        )


def test_compile_program_config_plan_requires_projection_only_port_ref() -> None:
    with pytest.raises(
        ValueError,
        match=r"port declaration ref must use `<Experience>` form",
    ):
        _ = compile_program_config_plans(
            """\
program PortProjectionOnly(environment_id UUID) {
    port main environment.main {}
}
"""
        )


def test_compile_program_config_plan_rejects_call_plan_port_legacy_syntax() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"call plan\.port\(\.\.\.\) is not allowed",
    ):
        _ = compile_program_config_plans(
            """\
program ConversationTurn {
    call plan.port(key="main", branch_id=plan.conversation_branch_id)
}
"""
        )


def test_compile_invocation_plan_rejects_legacy_plan_lane_call() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"call plan\.lane\(\.\.\.\) is not allowed",
    ):
        _ = compile_invocation_plans(
            """\
program LegacyLane {
    call plan.lane(branch_id=plan.thread_id, opg="thread")
}
"""
        )


def test_compile_invocation_plan_rejects_legacy_plan_object_call() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"call plan\.object\(\.\.\.\) is not allowed",
    ):
        _ = compile_invocation_plans(
            """\
program LegacyObject {
    call plan.object(object_id=plan.thread_id)
}
"""
        )


def test_compile_invocation_plan_lowers_inline_object_selector() -> None:
    plans = compile_invocation_plans(
        """\
program InlineObject {
    bind main thread.main
    call thread_id thread.Thread.set_title(title="Hi")
}
"""
    )
    assert len(plans) == 1
    invoke_step = plans[0].steps[1]
    assert isinstance(invoke_step, PlanInvoke)
    assert isinstance(invoke_step.call, PlanCall)
    assert invoke_step.call.object_expr == PlanSymbolRef(name="thread_id")


def test_compile_invocation_plan_lowers_port_declaration_to_metadata() -> None:
    plans = compile_invocation_plans(
        """\
program PortMetadata(environment_id UUID) {
    port main Environment {
        node environment environment.main
        \"\"\"Environment main port.\"\"\"
    }
    bind main Environment.main
}
"""
    )
    assert len(plans) == 1
    plan = plans[0]
    assert len(plan.steps) == 2
    assert len(plan.ports) == 1
    assert isinstance(plan.ports[0], PlanPortContract)
    assert plan.ports[0].key == "main"
    assert plan.ports[0].projection == "Environment"
    assert plan.ports[0].intent is None
    assert plan.ports[0].projection_nodes == (
        PlanPortProjectionNodeContract(
            key="environment",
            node="environment.main",
            keys=(),
        ),
    )
    assert all(
        not (
            isinstance(step, PlanInvoke)
            and isinstance(step.call, PlanCall)
            and step.call.target == "plan.port"
        )
        for step in plan.steps
    )


def test_program_config_instruction_types_match_aware_enum_contract() -> None:
    plan = compile_program_config_plans(
        """\
program InstructionCoverage {
    actor assistant assistant
    port main environment {
        projection="thread"
        node thread thread.main
    }
    input thread_id from plan.thread_id
    let event_config_id = EventConfig.id(name="thread.updated")
    expect event_config event_config_id required
    intent action_config ActionConfig.id(name="thread.updated.execute") on event_config event_config_id
    bind main thread.main
    assistant call thread thread.Thread.set_title(title="Hello")
}
""",
        type_id_registry=_TYPE_ID_REGISTRY,
    )[0]

    observed = {instruction.type for instruction in plan.instructions}
    assert observed == _PROGRAM_CONFIG_INSTRUCTION_TYPE_MEMBERS


def test_compile_program_config_plan_real_port_surface() -> None:
    port_plan = compile_program_config_plans(
        """\
program ConversationTurn {
    actor assistant assistant
    port main environment {
        intent="conversation.main"
        projection="Conversation"
        node thread thread.main
    }
    layout {
        layout(key="conversation.primary", is_default=true)
        section(layout_key="conversation.primary", key="main", order=0, is_visible=true, flex=1.0)
        slot(
            layout_key="conversation.primary",
            port=program.port.main,
            section_key="main",
            on_bind="replace",
            is_visible_default=true
        )
    }
    input conversation_branch_id from plan.conversation_branch_id
    let event_config_id = reactivity.stable_event_config_id(name="conversation.message.created")
    expect event_config event_config_id required
    intent action_config reactivity.stable_action_config_id(name="conv.msg.created.ex") on event_config event_config_id
    bind main conversation.main
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]
    second_plan = compile_program_config_plans(
        """\
program ConversationTurn {
    actor assistant assistant
    port main environment {
        intent="conversation.main"
        projection="Conversation"
        node thread thread.main
    }
    call plan.layout(
        key="conversation.primary",
        is_default=true
    )
    call plan.section(
        layout_key="conversation.primary",
        key="main",
        order=0,
        is_visible=true,
        flex=1.0
    )
    call plan.slot(
        layout_key="conversation.primary",
        port=program.port.main,
        section_key="main",
        on_bind="replace",
        is_visible_default=true
    )
    input conversation_branch_id from plan.conversation_branch_id
    let event_config_id = reactivity.stable_event_config_id(name="conversation.message.created")
    expect event_config event_config_id required
    intent action_config reactivity.stable_action_config_id(name="conv.msg.created.ex") on event_config event_config_id
    bind main conversation.main
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    assert port_plan == second_plan


def test_compile_program_config_apply_calls_emits_handler_constructors() -> None:
    plan = compile_program_config_plans(
        """\
program ApplyShapeConfig {
    actor assistant assistant
    port main conversation {
        projection="Conversation"
        node thread thread.main
    }
}

program ApplyShape impl ApplyShapeConfig {
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.thread": "projection-node-thread"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.thread": "projection-node-identity-thread"
            },
        ),
    )
    assert len(calls) >= 8
    assert all(isinstance(call, ProgramConfigApplyCall) for call in calls)

    by_step = {call.step_id: call for call in calls}

    actor_call = by_step["actor.0000.declare"]
    assert actor_call.target == "instance"
    assert actor_call.function_name == "create_actor_config"
    assert actor_call.args[0] == "program.actor.assistant"
    assert actor_call.args[1] == "assistant"

    port_call = by_step["port.0000.declare"]
    assert port_call.target == "instance"
    assert port_call.function_name == "create_port"
    assert port_call.args[0] == "projection-123"
    assert port_call.args[1] == "main"

    port_node_call = by_step["port.0000.node.0000.projection_node"]
    assert port_node_call.target == "instance"
    assert port_node_call.function_name == "create_projection_node"
    assert port_node_call.args[1] == "thread"

    port_node_identity_call = by_step["port.0000.node.0000.projection_node_identity"]
    assert port_node_identity_call.target == "instance"
    assert port_node_identity_call.function_name == "create_identity"
    assert port_node_identity_call.args[1] == "thread"

    program_impl_call = by_step["program.impl.create"]
    assert program_impl_call.target == "constructor"
    assert (
        program_impl_call.class_fqn
        == "aware_experience_ontology.program.impl.program_impl.ProgramImpl"
    )

    instruction_call = by_step["s0000_invoke.instruction"]
    assert instruction_call.target == "constructor"
    assert (
        instruction_call.class_fqn
        == "aware_experience_ontology.program.impl.program_impl_instruction.ProgramImplInstruction"
    )
    assert instruction_call.function_name == "build"
    assert isinstance(instruction_call.args[0], ProgramConfigApplyRef)
    assert instruction_call.args[0].name == "program_config_id.program_impl"
    assert instruction_call.args[1] == "invoke"
    assert instruction_call.args[2] == 0

    invoke_call = by_step["s0000_invoke.invoke"]
    assert invoke_call.target == "constructor"
    assert (
        invoke_call.class_fqn
        == "aware_experience_ontology.program.impl.program_impl_instruction_invoke.ProgramImplInstructionInvoke"
    )
    assert invoke_call.args[1] == "conversation.Conversation.add_message"
    assert isinstance(invoke_call.args[2], ProgramConfigApplyRef)
    assert invoke_call.args[2].name == "actor:assistant"
    assert isinstance(invoke_call.args[3], ProgramConfigApplyRef)
    assert invoke_call.args[3].name == "port_projection_node:main:thread"
    assert invoke_call.args[4] == "instance"

    invoke_attr_call = by_step["s0000_invoke.invoke_attribute_0000"]
    assert invoke_attr_call.target == "instance"
    assert invoke_attr_call.function_name == "add_attribute_config"
    assert invoke_attr_call.args[0] == "conversation.Conversation.add_message::text"
    assert invoke_attr_call.args[1] == "hello"
    assert invoke_attr_call.args[2] == 0


def test_compile_program_config_apply_calls_lowers_port_attribute_contracts() -> None:
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={"program.input.environment_id": "attr-123"},
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.environment": "projection-node-struct-123"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.environment": "projection-node-123",
            },
        ),
        strict_resolution=True,
    )
    assert calls[0].step_id == "program.attribute.0000.create"
    assert calls[0].args[0] == "attr-123"
    assert calls[0].args[1] == "environment_id"
    assert calls[0].args[2] == "uuid"
    assert calls[0].args[3] is None
    assert calls[0].args[4] is None
    assert calls[0].args[5] == "input"
    assert calls[0].args[6] == 0
    assert calls[0].args[7] is True
    assert calls[1].step_id == "port.0000.declare"
    assert calls[1].args[0] == "projection-123"
    assert calls[1].args[1] == "main"
    assert calls[1].args[2] is None
    assert calls[1].args[3] == "reference"
    assert calls[2].step_id == "port.0000.node.0000.projection_node"
    assert calls[2].target == "instance"
    assert (
        calls[2].class_fqn
        == "aware_experience_ontology.program.program_config_port.ProgramConfigPort"
    )
    assert calls[2].function_name == "create_projection_node"
    assert calls[2].args[0] == "projection-node-struct-123"
    assert calls[2].args[1] == "environment"
    assert calls[3].step_id == "port.0000.node.0000.projection_node_identity"
    assert calls[3].args[0] == "projection-node-123"
    assert calls[4].step_id == "program.impl.create"
    assert calls[5].step_id == "s0000_input.instruction"
    assert calls[6].step_id == "s0000_input.input_config"
    assert calls[7].step_id == "s0000_input.input"


def test_compile_program_config_apply_calls_lowers_non_primitive_enum_attribute_contract() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ApplyShape(status alpha.types.Status) {
}
"""
    )[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={"program.input.status": "attr-status"},
            enum_config_ids={"alpha.types.Status": "enum-status"},
        ),
        strict_resolution=True,
    )
    assert calls[0].step_id == "program.attribute.0000.create"
    assert calls[0].args[0] == "attr-status"
    assert calls[0].args[1] == "status"
    assert calls[0].args[2] == "alpha.types.Status"
    assert calls[0].args[3] == "enum-status"
    assert calls[0].args[4] is None


def test_compile_program_config_apply_calls_lowers_non_primitive_class_attribute_contract() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ApplyShape(profile alpha.types.Profile) {
}
"""
    )[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={"program.input.profile": "attr-profile"},
            class_config_ids={"alpha.types.Profile": "class-profile"},
        ),
        strict_resolution=True,
    )
    assert calls[0].step_id == "program.attribute.0000.create"
    assert calls[0].args[0] == "attr-profile"
    assert calls[0].args[1] == "profile"
    assert calls[0].args[2] == "alpha.types.Profile"
    assert calls[0].args[3] is None
    assert calls[0].args[4] == "class-profile"


def test_compile_program_config_apply_calls_rejects_unmapped_non_primitive_attribute_type() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ApplyShape(profile alpha.types.Profile) {
}
"""
    )[0]
    with pytest.raises(
        ProgramCompileError,
        match=r"requires explicit enum/class config mapping",
    ):
        _ = compile_program_config_apply_calls(plan)


def test_compile_program_config_graph_apply_calls_emits_graph_connector_first() -> None:
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]

    calls = compile_program_config_graph_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={"program.input.environment_id": "attr-123"},
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.environment": "projection-node-struct-123"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.environment": "projection-node-123",
            },
        ),
        strict_resolution=True,
    )
    assert calls[0].step_id == "program_config_graph.program_config.create"
    assert calls[0].target == "instance"
    assert (
        calls[0].class_fqn
        == "aware_experience_ontology.program.program_config_graph.ProgramConfigGraph"
    )
    assert calls[0].function_name == "create_program_config"
    assert isinstance(calls[0].object_ref, ProgramConfigApplyRef)
    assert calls[0].object_ref.name == "program_config_graph_id"
    assert isinstance(calls[0].result_ref, ProgramConfigApplyRef)
    assert calls[0].result_ref.name == "program_config_id.graph_program_config"
    assert calls[0].args[0] == "ApplyShape"
    assert calls[0].args[1] == "ApplyShape"
    assert calls[1].step_id == "program_config_graph.program_config.resolve"
    assert calls[2].step_id == "program.attribute.0000.create"
    assert isinstance(calls[2].object_ref, ProgramConfigApplyRef)
    assert calls[2].object_ref.name == "program_config_id"
    assert calls[3].step_id == "port.0000.declare"
    assert isinstance(calls[3].object_ref, ProgramConfigApplyRef)
    assert calls[3].object_ref.name == "program_config_id"
    assert calls[4].step_id == "port.0000.node.0000.projection_node"
    assert calls[5].step_id == "port.0000.node.0000.projection_node_identity"
    assert calls[6].step_id == "program.impl.create"
    assert calls[7].step_id == "s0000_input.instruction"
    assert calls[8].step_id == "s0000_input.input_config"
    assert calls[9].step_id == "s0000_input.input"


def test_compile_program_config_apply_calls_requires_port_projection_id() -> None:
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]

    with pytest.raises(ProgramCompileError, match=r"unresolved projection_id"):
        _ = compile_program_config_apply_calls(
            plan,
            references=ProgramConfigReferenceCatalog(
                attribute_config_ids={"program.input.environment_id": "attr-123"}
            ),
            strict_resolution=True,
        )


def test_compile_program_config_apply_calls_allows_projection_symbol_fallback_when_non_strict() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]

    calls = compile_program_config_apply_calls(plan)
    by_step = {call.step_id: call for call in calls}
    assert by_step["port.0000.declare"].args[0] == "program.port.main.projection"
    assert by_step["port.0000.node.0000.projection_node"].args[0] == (
        "program.port.main.projection_node.environment"
    )
    assert by_step["port.0000.node.0000.projection_node_identity"].args[0] == (
        "program.port.main.projection_node_identity.environment"
    )


def test_compile_program_apply_calls_defaults_to_graph_first_entrypoint() -> None:
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]

    calls = compile_program_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={"program.input.environment_id": "attr-123"},
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.environment": "projection-node-struct-123"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.environment": "projection-node-123",
            },
        ),
        strict_resolution=True,
    )
    assert calls[0].step_id == "program_config_graph.program_config.create"
    assert (
        calls[0].class_fqn
        == "aware_experience_ontology.program.program_config_graph.ProgramConfigGraph"
    )
    assert calls[1].step_id == "program_config_graph.program_config.resolve"
    assert calls[2].step_id == "program.attribute.0000.create"


def test_compile_program_config_apply_calls_allows_plan_symbol_port_arg_without_input_contract() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ApplyShape(environment_id UUID) {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
    )[0]
    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.environment": "projection-node-struct-123"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.environment": "projection-node-identity-123"
            },
        ),
    )
    assert calls[1].step_id == "port.0000.declare"
    assert calls[1].args[0] == "projection-123"


def test_compile_program_config_apply_calls_strict_resolution() -> None:
    plan = compile_program_config_plans(
        """\
program ResolveShapeConfig {
    actor assistant assistant
    port main conversation {
        projection="Conversation"
        node thread thread.main
    }
}

program ResolveShape impl ResolveShapeConfig {
    expect event_config reactivity.event.created required
    intent action_config reactivity.action.execute on event_config reactivity.event.created
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            function_config_ids={"conversation.Conversation.add_message": "fn-123"},
            function_attribute_config_ids={
                "conversation.Conversation.add_message::text": "fn-attr-text-123"
            },
            event_config_ids={"reactivity.event.created": "evt-123"},
            action_config_ids={"reactivity.action.execute": "act-123"},
            actor_config_ids={"program.actor.assistant": "actor-123"},
            projection_ids={"program.port.main.projection": "projection-123"},
            projection_node_ids={
                "program.port.main.projection_node.thread": "projection-node-thread"
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.thread": "projection-node-identity-thread"
            },
        ),
        strict_resolution=True,
    )

    by_step = {call.step_id: call for call in calls}
    assert by_step["program.impl.create"].step_id == "program.impl.create"

    # expect call
    expect_call = by_step["s0000_expect.expect"]
    assert expect_call.step_id == "s0000_expect.expect"
    assert expect_call.args[1] == "evt-123"

    # intent call
    intent_call = by_step["s0001_intent.intent"]
    assert intent_call.step_id == "s0001_intent.intent"
    assert intent_call.args[1] == "act-123"
    assert intent_call.args[2] == "evt-123"

    # invoke call
    invoke_call = by_step["s0002_invoke.invoke"]
    assert invoke_call.step_id == "s0002_invoke.invoke"
    assert invoke_call.args[1] == "fn-123"
    assert isinstance(invoke_call.args[2], ProgramConfigApplyRef)
    assert invoke_call.args[2].name == "actor:assistant"
    assert isinstance(invoke_call.args[3], ProgramConfigApplyRef)

    invoke_attr_call = by_step["s0002_invoke.invoke_attribute_0000"]
    assert invoke_attr_call.args[0] == "fn-attr-text-123"


def test_compile_program_config_apply_calls_strict_requires_function_attribute_contracts() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ResolveShapeConfig {
    actor assistant assistant
    port main conversation {
        projection="Conversation"
        node thread thread.main
    }
}

program ResolveShape impl ResolveShapeConfig {
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    with pytest.raises(
        ProgramCompileError, match=r"missing function attribute contract mappings"
    ):
        _ = compile_program_config_apply_calls(
            plan,
            references=ProgramConfigReferenceCatalog(
                function_config_ids={"conversation.Conversation.add_message": "fn-123"},
                actor_config_ids={"program.actor.assistant": "actor-123"},
                projection_ids={"program.port.main.projection": "projection-123"},
                projection_node_ids={
                    "program.port.main.projection_node.thread": "projection-node-thread"
                },
                projection_node_identity_ids={
                    "program.port.main.projection_node_identity.thread": "projection-node-identity-thread"
                },
            ),
            strict_resolution=True,
        )


def test_compile_program_config_apply_calls_strict_rejects_invoke_kwargs_mismatch() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program ResolveShapeConfig {
    actor assistant assistant
    port main conversation {
        projection="Conversation"
        node thread thread.main
    }
}

program ResolveShape impl ResolveShapeConfig {
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    with pytest.raises(ProgramCompileError, match=r"invoke kwargs mismatch"):
        _ = compile_program_config_apply_calls(
            plan,
            references=ProgramConfigReferenceCatalog(
                function_config_ids={"conversation.Conversation.add_message": "fn-123"},
                function_attribute_config_ids={
                    "conversation.Conversation.add_message::other": "fn-attr-other-123"
                },
                actor_config_ids={"program.actor.assistant": "actor-123"},
                projection_ids={"program.port.main.projection": "projection-123"},
                projection_node_ids={
                    "program.port.main.projection_node.thread": "projection-node-thread"
                },
                projection_node_identity_ids={
                    "program.port.main.projection_node_identity.thread": "projection-node-identity-thread"
                },
            ),
            strict_resolution=True,
        )


def test_compile_program_config_plan_rejects_bind_to_undeclared_port_symbol() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"undeclared program port",
    ):
        _ = compile_program_config_plans(
            """\
program BadBind {
    bind thread_id conversation.main
}
"""
        )


def test_compile_program_config_plan_rejects_port_not_at_top() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"port declarations must appear at top of program body",
    ):
        _ = compile_program_config_plans(
            """\
program PortOrder {
    input thread_id from plan.thread_id
    port main Conversation {}
}
"""
        )


def test_compile_program_config_plan_rejects_bind_to_undeclared_port() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"undeclared program port",
    ):
        _ = compile_program_config_plans(
            """\
program MissingPort {
    bind main conversation.main
}
"""
        )


def test_compile_program_config_plan_rejects_duplicate_port_key() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"Duplicate port key",
    ):
        _ = compile_program_config_plans(
            """\
program DuplicatePort {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
    port main environment {
        projection="Environment"
        node environment environment.main
    }
}
"""
        )


def test_compile_program_config_plan_rejects_layout_not_at_top() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.layout declarations must appear at top of program body",
    ):
        _ = compile_program_config_plans(
            """\
program LayoutOrder {
    input thread_id from plan.thread_id
    call plan.layout(key="main", is_default=true)
}
"""
        )


def test_compile_program_config_plan_rejects_duplicate_layout_key() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"Duplicate layout key",
    ):
        _ = compile_program_config_plans(
            """\
program DuplicateLayout {
    call plan.layout(key="main", is_default=true)
    call plan.layout(key="main", is_default=false)
}
"""
        )


def test_compile_program_config_plan_rejects_layout_default_count() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"exactly one default layout",
    ):
        _ = compile_program_config_plans(
            """\
program MissingDefaultLayout {
    call plan.layout(key="main")
}
"""
        )


def test_compile_program_config_plan_rejects_section_unknown_layout() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.section references unknown layout_key",
    ):
        _ = compile_program_config_plans(
            """\
program SectionUnknownLayout {
    call plan.section(layout_key="missing", key="main", order=0)
}
"""
        )


def test_compile_program_config_plan_rejects_duplicate_section_key_within_layout() -> (
    None
):
    with pytest.raises(
        ProgramCompileError,
        match=r"Duplicate section key in layout",
    ):
        _ = compile_program_config_plans(
            """\
program DuplicateSection {
    call plan.layout(key="main", is_default=true)
    call plan.section(layout_key="main", key="a", order=0)
    call plan.section(layout_key="main", key="a", order=1)
}
"""
        )


def test_compile_program_config_plan_rejects_slot_unknown_layout() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.slot references unknown layout_key",
    ):
        _ = compile_program_config_plans(
            """\
program SlotUnknownLayout {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
    call plan.slot(
        layout_key="missing",
        port=program.port.main,
        section_key="a",
        on_bind="replace"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_slot_unknown_section() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.slot references unknown section_key",
    ):
        _ = compile_program_config_plans(
            """\
program SlotUnknownSection {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
    call plan.layout(key="layout", is_default=true)
    call plan.slot(
        layout_key="layout",
        port=program.port.main,
        section_key="missing",
        on_bind="replace"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_slot_unknown_port() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.slot references undeclared program port",
    ):
        _ = compile_program_config_plans(
            """\
program SlotUnknownPort {
    call plan.layout(key="layout", is_default=true)
    call plan.section(layout_key="layout", key="main", order=0)
    call plan.slot(
        layout_key="layout",
        port=program.port.main,
        section_key="main",
        on_bind="replace"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_duplicate_slot_mapping() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"Duplicate slot mapping for layout",
    ):
        _ = compile_program_config_plans(
            """\
program DuplicateSlot {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
    call plan.layout(key="layout", is_default=true)
    call plan.section(layout_key="layout", key="main", order=0)
    call plan.slot(
        layout_key="layout",
        port=program.port.main,
        section_key="main",
        on_bind="replace"
    )
    call plan.slot(
        layout_key="layout",
        port=program.port.main,
        section_key="main",
        on_bind="if_empty"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_slot_invalid_on_bind() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.slot on_bind must be one of: replace, if_empty, sticky",
    ):
        _ = compile_program_config_plans(
            """\
program SlotBadOnBind {
    port main environment {
        projection="Environment"
        node environment environment.main
    }
    call plan.layout(key="layout", is_default=true)
    call plan.section(layout_key="layout", key="main", order=0)
    call plan.slot(
        layout_key="layout",
        port=program.port.main,
        section_key="main",
        on_bind="append"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_non_literal_layout_key() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"plan\.layout key must be a string literal",
    ):
        _ = compile_program_config_plans(
            """\
program NonLiteralLayoutKey {
    call plan.layout(key=layout_key, is_default=true)
}
"""
        )


def test_compile_program_config_apply_calls_strict_resolution_reports_missing_symbol() -> (
    None
):
    plan = compile_program_config_plans(
        """\
program MissingRefsConfig {
    actor assistant assistant
    port main conversation {
        projection="Conversation"
        node thread thread.main
    }
}

program MissingRefs impl MissingRefsConfig {
    assistant call thread conversation.Conversation.add_message(text="hello")
}
"""
    )[0]

    with pytest.raises(ProgramCompileError, match="unresolved function target"):
        _ = compile_program_config_apply_calls(
            plan,
            references=ProgramConfigReferenceCatalog(
                function_attribute_config_ids={
                    "conversation.Conversation.add_message::text": "fn-attr-text-123"
                },
                actor_config_ids={"program.actor.assistant": "actor-123"},
                projection_ids={"program.port.main.projection": "projection-123"},
                projection_node_ids={
                    "program.port.main.projection_node.thread": "projection-node-thread"
                },
                projection_node_identity_ids={
                    "program.port.main.projection_node_identity.thread": "projection-node-identity-thread"
                },
            ),
            strict_resolution=True,
        )


def test_compile_program_config_plan_merges_config_and_impl_surfaces() -> None:
    plans = compile_program_config_plans(
        """\
program HomeSceneConfig(channel_number Int) {
    actor resident resident
    port main home_story {
        node home home.home
        node door doors.front_door
        node channel channels(number=channel_number)
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    bind main home_story.entertainment.home
    resident call door aware_home.home.Door.unlock()
}
"""
    )

    assert len(plans) == 1
    plan = plans[0]
    assert plan.name == "HomeSceneDefault"
    assert len(plan.ports) == 1
    assert plan.ports[0].key == "main"
    assert [instruction.type for instruction in plan.instructions] == [
        "input",
        "bind",
        "invoke",
    ]


def test_compile_program_config_plan_keeps_actor_contract_role_agnostic() -> None:
    plans = compile_program_config_plans(
        """\
program HomeSceneConfig(channel_number Int) {
    actor human_resident resident
    actor ai_assistant assistant
    port main home_story {
        node home home.home
        node tv tvs.living_room_tv
        node channel channels(number=channel_number)
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    bind main home_story.entertainment.tv
    ai_assistant call tv aware_home.home.Tv.turn_on()
}
"""
    )

    assert len(plans) == 1
    plan = plans[0]
    assert len(plan.actors) == 2
    assert plan.actors[0].key == "human_resident"
    assert plan.actors[0].actor == "resident"
    assert plan.actors[1].key == "ai_assistant"
    assert plan.actors[1].actor == "assistant"
    assert [instruction.type for instruction in plan.instructions] == [
        "input",
        "bind",
        "invoke",
    ]
    invoke_instruction = plan.instructions[2]
    assert invoke_instruction.instruction_invoke is not None
    assert invoke_instruction.instruction_invoke.actor_ref == PlanSymbolRef(
        name="program.actor.ai_assistant"
    )


def test_compile_program_config_plan_keeps_actor_attributed_call_contract() -> None:
    plans = compile_program_config_plans(
        """\
program HomeSceneConfig(channel_number Int) {
    actor human_resident resident
    actor ai_assistant assistant
    port main home_story {
        node home home.home
        node tv tvs.living_room_tv
        node channel channels(number=channel_number)
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    bind main home_story.entertainment.tv
    ai_assistant call tv aware_home.home.Tv.turn_on()
}
"""
    )

    assert len(plans) == 1
    plan = plans[0]
    assert [instruction.type for instruction in plan.instructions] == [
        "input",
        "bind",
        "invoke",
    ]
    invoke_instruction = plan.instructions[2]
    assert invoke_instruction.instruction_invoke is not None
    assert invoke_instruction.instruction_invoke.actor_ref == PlanSymbolRef(
        name="program.actor.ai_assistant"
    )


def test_compile_program_config_plan_lowers_constructor_invoke_with_active_bind_context() -> (
    None
):
    plans = compile_program_config_plans(
        """\
program HomeSceneConfig {
    actor resident resident
    port main home_story {
        node home home.home
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    bind main home_story.entertainment.home
    resident call aware_home.home.Home.build(name="my-home")
}
"""
    )

    assert len(plans) == 1
    plan = plans[0]
    assert [instruction.type for instruction in plan.instructions] == [
        "bind",
        "invoke",
    ]
    invoke_instruction = plan.instructions[1]
    assert invoke_instruction.instruction_invoke is not None
    assert invoke_instruction.instruction_invoke.actor_ref == PlanSymbolRef(
        name="program.actor.resident"
    )
    assert invoke_instruction.instruction_invoke.object_ref == PlanSymbolRef(
        name="program.port.main.projection_node"
    )
    assert invoke_instruction.instruction_invoke.target_kind == "construct"


def test_compile_program_config_plan_rejects_constructor_invoke_without_bind_context() -> (
    None
):
    with pytest.raises(
        ProgramCompileError,
        match=r"constructor invoke requires active bind context",
    ):
        _ = compile_program_config_plans(
            """\
program HomeSceneConfig {
    actor resident resident
    port main home_story {
        node home home.home
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    resident call aware_home.home.Home.build(name="my-home")
}
"""
        )


def test_compile_program_config_plan_rejects_undeclared_actor_on_call() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"call references undeclared actor",
    ):
        _ = compile_program_config_plans(
            """\
program HomeSceneConfig(channel_number Int) {
    actor human_resident resident
    port main home_story {
        node home home.home
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    ai_assistant call home aware_home.home.Home.create(
        name="my-home"
    )
}
"""
        )


def test_compile_program_config_plan_rejects_impl_parameters() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"cannot declare parameters",
    ):
        _ = compile_program_config_plans(
            """\
program Config(home_key String) {
    port main home_story {
        node door doors.front_door
    }
}

program Impl impl Config(extra String) {
    bind main home_story.entertainment.home
}
"""
        )


def test_compile_program_config_plan_rejects_impl_unknown_config() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"references unknown config",
    ):
        _ = compile_program_config_plans(
            """\
program HomeSceneDefault impl MissingConfig {
    bind main home_story.entertainment.home
}
"""
        )


def test_compile_program_config_plan_rejects_executable_in_config_surface() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"config declarations cannot include executable statements",
    ):
        _ = compile_program_config_plans(
            """\
program HomeSceneConfig(home_key String) {
    port main home_story {
        node door doors.front_door
    }
    bind main home_story.entertainment.home
}

program HomeSceneDefault impl HomeSceneConfig {
    call door aware_home.home.Door.unlock()
}
"""
        )
