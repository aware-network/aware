from __future__ import annotations

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def _text(source_bytes: bytes, node: Node | None) -> str:
    assert node is not None
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _find_nodes(node: Node, node_type: str) -> list[Node]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_find_nodes(child, node_type))
    return matches


def test_tree_sitter_parses_experience_section_surfaces() -> None:
    source = """\
experience home_story on aware_home.home.Home {
    observable overview {
        view home default state aware_home.home.Home provider aware_home.views.home_state {
            action open_chat sdk home_sdk.open_chat {
                label "Open chat";
                receipt show_receipt;
            }

            action open_panel view {
                label "Open panel";
                receipt show_receipt;
            }
        }
    }

    observable security {
        view door default state aware_home.home.Door {}
    }

    node home.Home {
        id home
    }

    node home.Home::doors {
        id front_door
    }

    surface home.primary {
        section primary;
        view overview.home;
        graph home;
    }

    surface security.front_door {
        section orchestration;
        view security.door;
        node front_door;
        source home.primary;
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    experience_defs = _find_nodes(root, "experience_def")
    assert len(experience_defs) == 1

    surface_defs = _find_nodes(root, "experience_surface_def")
    assert len(surface_defs) == 2
    assert (
        _text(source_bytes, surface_defs[0].child_by_field_name("surface_key"))
        == "home.primary"
    )
    assert (
        _text(source_bytes, surface_defs[1].child_by_field_name("surface_key"))
        == "security.front_door"
    )

    section_decls = _find_nodes(root, "experience_surface_section_decl")
    assert [
        _text(source_bytes, node.child_by_field_name("section_key"))
        for node in section_decls
    ] == [
        "primary",
        "orchestration",
    ]

    view_decls = _find_nodes(root, "experience_surface_view_decl")
    assert [
        _text(source_bytes, node.child_by_field_name("view_ref")) for node in view_decls
    ] == [
        "overview.home",
        "security.door",
    ]

    view_defs = _find_nodes(root, "experience_view_def")
    assert [
        _text(source_bytes, node.child_by_field_name("state_model"))
        for node in view_defs
    ] == [
        "aware_home.home.Home",
        "aware_home.home.Door",
    ]
    assert _text(source_bytes, view_defs[0].child_by_field_name("state_provider")) == (
        "aware_home.views.home_state"
    )
    assert view_defs[1].child_by_field_name("state_provider") is None

    action_defs = _find_nodes(root, "experience_view_action_def")
    assert len(action_defs) == 2
    assert (
        _text(source_bytes, action_defs[0].child_by_field_name("action_key"))
        == "open_chat"
    )
    assert (
        _text(source_bytes, action_defs[0].child_by_field_name("action_kind")) == "sdk"
    )
    assert (
        _text(source_bytes, action_defs[0].child_by_field_name("target_ref"))
        == "home_sdk.open_chat"
    )
    assert (
        _text(source_bytes, action_defs[1].child_by_field_name("action_key"))
        == "open_panel"
    )
    assert (
        _text(source_bytes, action_defs[1].child_by_field_name("action_kind"))
        == "view"
    )
    assert action_defs[1].child_by_field_name("target_ref") is None
    action_label_stmts = _find_nodes(root, "experience_view_action_label_stmt")
    assert len(action_label_stmts) == 2
    assert (
        _text(source_bytes, action_label_stmts[0].child_by_field_name("label"))
        == '"Open chat"'
    )
    action_receipt_stmts = _find_nodes(root, "experience_view_action_receipt_stmt")
    assert len(action_receipt_stmts) == 2
    assert (
        _text(source_bytes, action_receipt_stmts[0].child_by_field_name("policy"))
        == "show_receipt"
    )

    graph_anchor_decls = _find_nodes(root, "experience_surface_graph_anchor_decl")
    assert len(graph_anchor_decls) == 1
    assert (
        _text(source_bytes, graph_anchor_decls[0].child_by_field_name("graph_identity"))
        == "home"
    )

    node_anchor_decls = _find_nodes(root, "experience_surface_node_anchor_decl")
    assert len(node_anchor_decls) == 1
    assert (
        _text(source_bytes, node_anchor_decls[0].child_by_field_name("node_identity"))
        == "front_door"
    )

    source_decls = _find_nodes(root, "experience_surface_source_decl")
    assert len(source_decls) == 1
    assert (
        _text(source_bytes, source_decls[0].child_by_field_name("source_surface"))
        == "home.primary"
    )


def test_tree_sitter_parses_experience_profile_view_event_transition() -> None:
    source = """\
experience aware_conversation_spaces {
    profile coordination.default {
        transition conversation.select.active {
            source projection aware_conversation_spaces view chat.selector.v1
            trigger event ConversationActiveBranchChanged
            target projection aware_conversation_spaces binding conversations.active
            name "Open active conversation"
            rationale "Selection opens the active conversation."
            idempotency_policy "event_commit"
        }

        process continuous coordination default {
            thread coordination.conversation default {
                projection aware_conversation_spaces view chat.selector.v1 default
                projection aware_conversation_spaces view chat.active.v1

                layout coordination_center default {
                    section orchestration projection aware_conversation_spaces view chat.selector.v1 binding conversations.selector default
                    section primary projection aware_conversation_spaces view chat.active.v1 binding conversations.active
                }
            }
        }
    }
}
"""
    source_bytes = source.encode("utf-8")
    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(source_bytes)
    root = tree.root_node

    assert not root.has_error

    transitions = _find_nodes(root, "experience_profile_transition_def")
    assert len(transitions) == 1
    assert _text(source_bytes, transitions[0].child_by_field_name("key")) == (
        "conversation.select.active"
    )
    source_stmts = _find_nodes(root, "experience_profile_transition_source_stmt")
    assert len(source_stmts) == 1
    assert _text(source_bytes, source_stmts[0].child_by_field_name("experience")) == (
        "aware_conversation_spaces"
    )
    assert _text(source_bytes, source_stmts[0].child_by_field_name("view_key")) == (
        "chat.selector.v1"
    )
    trigger_stmts = _find_nodes(root, "experience_profile_transition_trigger_stmt")
    assert len(trigger_stmts) == 1
    assert _text(source_bytes, trigger_stmts[0].child_by_field_name("event")) == (
        "ConversationActiveBranchChanged"
    )
    target_stmts = _find_nodes(root, "experience_profile_transition_target_stmt")
    assert len(target_stmts) == 1
    assert _text(source_bytes, target_stmts[0].child_by_field_name("binding_key")) == (
        "conversations.active"
    )
