from __future__ import annotations

import pytest
from tree_sitter import Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_grammar.program import (
    ProgramCall,
    ProgramExpectEventConfig,
    ProgramInput,
    ProgramIntentActionConfig,
    ProgramLet,
    ProgramParameter,
    ProgramRef,
    parse_program_declarations,
)


def test_parse_program_declarations_let_and_call() -> None:
    programs = parse_program_declarations(
        """\
program KernelSeed {
    let public_key = "ed25519:abc"
    call identity.Identity.signup(public_key=public_key, type=human)
}
"""
    )

    assert len(programs) == 1
    program = programs[0]
    assert program.name == "KernelSeed"
    assert len(program.statements) == 2

    let_stmt = program.statements[0]
    assert isinstance(let_stmt, ProgramLet)
    assert let_stmt.name == "public_key"
    assert let_stmt.value == "ed25519:abc"

    call_stmt = program.statements[1]
    assert isinstance(call_stmt, ProgramCall)
    assert call_stmt.target == "identity.Identity.signup"
    assert [arg.name for arg in call_stmt.args] == ["public_key", "type"]
    assert call_stmt.args[0].value == ProgramRef("public_key")
    assert call_stmt.args[1].value == ProgramRef("human")


def test_parse_program_declarations_preserves_actor_without_object_selector() -> None:
    programs = parse_program_declarations(
        """\
program Boot {
    actor agent_system system
    agent_system call identity.Identity.signup(public_key="ed25519:abc", type=agent)
}
"""
    )

    assert len(programs) == 1
    program = programs[0]
    assert len(program.statements) == 2
    call_stmt = program.statements[1]
    assert isinstance(call_stmt, ProgramCall)
    assert call_stmt.target == "identity.Identity.signup"
    assert call_stmt.actor == "agent_system"
    assert call_stmt.object_expr is None


def test_parse_program_json_literal_expr() -> None:
    programs = parse_program_declarations(
        """\
program ReactivitySeed {
    let schema = {"name": "conversation.created", "version": 1}
    call event.EventConfig.create(
        name="conversation.created",
        description="Conversation creation domain event.",
        event_schema=schema
    )
}
"""
    )

    program = programs[0]
    let_stmt = program.statements[0]
    assert isinstance(let_stmt, ProgramLet)
    assert let_stmt.value == {"name": "conversation.created", "version": 1}


def test_parse_program_signature_parameters() -> None:
    programs = parse_program_declarations(
        """\
program ActReact_v1(
    event_config_name String,
    condition_config_name String = "conversation.message.created.condition"
) {
    let event_config_id = EventConfig.id(name=event_config_name)
}
"""
    )
    assert len(programs) == 1
    program = programs[0]
    assert len(program.parameters) == 2
    assert isinstance(program.parameters[0], ProgramParameter)
    assert program.parameters[0].name == "event_config_name"
    assert program.parameters[0].type_ref == "String"
    assert program.parameters[0].default is None
    assert program.parameters[1].name == "condition_config_name"
    assert program.parameters[1].type_ref == "String"
    assert program.parameters[1].default == "conversation.message.created.condition"


def test_parse_program_impl_declaration_without_params() -> None:
    programs = parse_program_declarations(
        """\
program HomeSceneConfig(home_key String) {
    port main home_story {
        node door doors.front_door
    }
}

program HomeSceneDefault impl HomeSceneConfig {
    bind main home_story.entertainment.home
}
"""
    )

    assert len(programs) == 2
    config = programs[0]
    impl = programs[1]

    assert config.name == "HomeSceneConfig"
    assert config.impl_of is None
    assert len(config.parameters) == 1

    assert impl.name == "HomeSceneDefault"
    assert impl.impl_of == "HomeSceneConfig"
    assert len(impl.parameters) == 0
    assert len(impl.statements) == 1
    assert isinstance(impl.statements[0], ProgramCall)
    assert impl.statements[0].target == "bind"


def test_parse_program_actor_declaration_in_config_surface() -> None:
    programs = parse_program_declarations(
        """\
program HomeSceneConfig(channel_number Int) {
    actor human_resident resident
    actor ai_assistant assistant
    port main home_story {
        node door doors.front_door
    }
}
"""
    )

    assert len(programs) == 1
    program = programs[0]
    assert len(program.statements) == 3
    actor_one = program.statements[0]
    actor_two = program.statements[1]
    assert isinstance(actor_one, ProgramCall)
    assert actor_one.target == "program.actor"
    assert actor_one.args[0].name == "key"
    assert actor_one.args[0].value == "human_resident"
    assert actor_one.args[1].name == "actor"
    assert actor_one.args[1].value == "resident"
    assert isinstance(actor_two, ProgramCall)
    assert actor_two.target == "program.actor"
    assert actor_two.args[0].value == "ai_assistant"
    assert actor_two.args[1].value == "assistant"


def test_parse_program_rejects_parse_errors() -> None:
    with pytest.raises(ValueError, match="parse errors"):
        _ = parse_program_declarations(
            """\
program Bad {
    let x =
}
"""
        )


def test_parse_program_input_expect_intent_contract_statements() -> None:
    programs = parse_program_declarations(
        """\
program Contract {
    input thread_id from plan.thread_id
    input event_name from plan.event_config_name default "conversation.message.created"

    let event_config_id = reactivity.stable_event_config_id(name=event_name)
    let action_config_id = reactivity.stable_action_config_id(name="conversation.message.created.execute")

    expect event_config event_config_id required
    intent action_config action_config_id on event_config event_config_id

    call plan.lane(branch_id=event_config_id, opg="EventConfig")
}
"""
    )

    assert len(programs) == 1
    program = programs[0]
    assert program.name == "Contract"
    assert len(program.statements) == 7

    input_required = program.statements[0]
    assert isinstance(input_required, ProgramInput)
    assert input_required.name == "thread_id"
    assert input_required.source == ProgramRef("plan.thread_id")
    assert input_required.default is None

    input_optional = program.statements[1]
    assert isinstance(input_optional, ProgramInput)
    assert input_optional.name == "event_name"
    assert input_optional.source == ProgramRef("plan.event_config_name")
    assert input_optional.default == "conversation.message.created"

    expect_stmt = program.statements[4]
    assert isinstance(expect_stmt, ProgramExpectEventConfig)
    assert expect_stmt.ref == ProgramRef("event_config_id")
    assert expect_stmt.required is True

    intent_stmt = program.statements[5]
    assert isinstance(intent_stmt, ProgramIntentActionConfig)
    assert intent_stmt.action_ref == ProgramRef("action_config_id")
    assert intent_stmt.event_ref == ProgramRef("event_config_id")


def test_parse_program_real_port_declaration() -> None:
    programs = parse_program_declarations(
        """\
program ConversationLayout {
    port main Conversation {
        node thread conversation.Conversation::messages(message_id=conversation_branch_id)
        \"\"\"Conversation main port.\"\"\"
    }

    layout {
        layout(key="conversation.primary", is_default=true)
        section(layout_key="conversation.primary", key="main", order=0, is_visible=true)
        slot(
            layout_key="conversation.primary",
            port=program.port.main,
            section_key="main",
            on_bind="replace",
            is_visible_default=true
        )
    }

    input conversation_branch_id from plan.conversation_branch_id
    bind main Conversation.main
}
"""
    )

    assert len(programs) == 1
    program = programs[0]
    assert program.name == "ConversationLayout"
    assert len(program.statements) == 6
    assert isinstance(program.statements[0], ProgramCall)
    assert program.statements[0].target == "program.port"
    port_args = {
        arg.name: arg.value
        for arg in program.statements[0].args
        if arg.name is not None
    }
    assert port_args["projection"] == "Conversation"
    assert port_args["node_thread"] == "conversation.Conversation::messages"
    assert port_args["node_thread_key_message_id"] == ProgramRef("conversation_branch_id")
    assert isinstance(program.statements[1], ProgramCall)
    assert program.statements[1].target == "plan.layout"
    assert isinstance(program.statements[2], ProgramCall)
    assert program.statements[2].target == "plan.section"
    assert isinstance(program.statements[3], ProgramCall)
    assert program.statements[3].target == "plan.slot"
    assert isinstance(program.statements[4], ProgramInput)
    assert isinstance(program.statements[5], ProgramCall)
    assert program.statements[5].target == "bind"
    bind_stmt = program.statements[5]
    assert isinstance(bind_stmt, ProgramCall)
    assert bind_stmt.args[0].name == "port"
    assert bind_stmt.args[0].value == ProgramRef("program.port.main")
    assert bind_stmt.args[1].name == "view_key"
    assert bind_stmt.args[1].value == "Conversation.main"


def test_parse_program_port_declaration_requires_projection_only() -> None:
    with pytest.raises(
        ValueError,
        match=r"port declaration ref must use `<Experience>` form",
    ):
        _ = parse_program_declarations(
            """\
program EnvironmentLayout {
    port environment Environment.main {
        \"\"\"Environment root port.\"\"\"
    }
    bind environment Environment.home
}
"""
        )


def test_parse_program_port_declaration_rejects_unclosed_block() -> None:
    with pytest.raises(ValueError, match="parse errors"):
        _ = parse_program_declarations(
            """\
program Bad {
    port main() {
        intent="conversation.main"
"""
        )


def test_treesitter_parses_port_declaration_natively() -> None:
    source = """\
program ConversationLayout {
    port main Conversation {
        node thread conversation.Conversation::messages(message_id=branch_id)
        \"\"\"Conversation main port.\"\"\"
    }
    layout {
        layout(key="conversation.primary", is_default=true)
        section(layout_key="conversation.primary", key="main", order=0, is_visible=true)
        slot(layout_key="conversation.primary", port=program.port.main, section_key="main", on_bind="replace")
    }
    input branch_id from plan.branch_id
    bind main Conversation.main
}
"""

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))

    assert tree.root_node.has_error is False
    program_node = tree.root_node.named_children[0]
    body_node = program_node.child_by_field_name("body")
    assert body_node is not None
    body_types = [child.type for child in body_node.named_children if child.type != "comment"]
    assert body_types[:3] == ["port_decl_stmt", "layout_decl_block", "input_stmt"]


def test_parse_program_call_with_inline_object_selector() -> None:
    programs = parse_program_declarations(
        """\
program InlineTarget {
    call thread_id thread.Thread.set_title(title="Hello")
}
"""
    )
    assert len(programs) == 1
    stmt = programs[0].statements[0]
    assert isinstance(stmt, ProgramCall)
    assert stmt.target == "thread.Thread.set_title"
    assert stmt.object_expr == ProgramRef("thread_id")


def test_parse_program_call_with_actor_prefix() -> None:
    programs = parse_program_declarations(
        """\
program InlineTarget {
    actor resident_actor resident
    resident_actor call thread_id thread.Thread.set_title(title="Hello")
}
"""
    )
    assert len(programs) == 1
    stmt = programs[0].statements[1]
    assert isinstance(stmt, ProgramCall)
    assert stmt.target == "thread.Thread.set_title"
    assert stmt.actor == "resident_actor"
    assert stmt.object_expr == ProgramRef("thread_id")


def test_treesitter_parses_class_id_declaration() -> None:
    source = """\
class ActionConfig {
    id primary(name String) {
        namespace NS_REACTIVITY
        template "action_config:{name_norm}"
        let name_norm = normalize(name, casefold, strip)
    }

    name String
}
"""
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))
    assert tree.root_node.has_error is False
    class_node = tree.root_node.named_children[0]
    body_types = [child.type for child in class_node.named_children if child.type != "comment"]
    assert "id_decl" in body_types


def test_treesitter_parses_dto_id_attribute_without_collision() -> None:
    source = """\
class NetworkNodePeerFanoutRuleListItem : inline_value {
    id UUID
    lane_branch_id UUID
}
"""
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))
    assert tree.root_node.has_error is False

    class_node = tree.root_node.named_children[0]
    body_types = [child.type for child in class_node.named_children if child.type != "comment"]
    assert body_types.count("attr_def") == 2
    assert "id_decl" not in body_types
