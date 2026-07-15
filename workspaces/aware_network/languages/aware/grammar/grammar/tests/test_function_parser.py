from __future__ import annotations

import pytest

from aware_grammar.function import (
    FunctionParseError,
    parse_function_statements_from_block,
    parse_function_invocations_from_block,
)


def test_parse_function_invocations_from_block_extracts_call_and_construct() -> None:
    invocations = parse_function_invocations_from_block(
        """\
{
    call child.step()
    let built = construct child.make()
}
"""
    )

    assert len(invocations) == 2
    assert [inv.kind for inv in invocations] == ["call", "construct"]
    assert [inv.target_path for inv in invocations] == [
        ("child", "step"),
        ("child", "make"),
    ]
    assert [inv.capture_name for inv in invocations] == [None, "built"]
    assert [inv.line_number for inv in invocations] == [2, 3]


def test_parse_function_invocations_from_block_extracts_inline_capture() -> None:
    invocations = parse_function_invocations_from_block(
        """\
{
    call loaded child.step()
}
"""
    )

    assert len(invocations) == 1
    assert invocations[0].kind == "call"
    assert invocations[0].target_path == ("child", "step")
    assert invocations[0].capture_name == "loaded"


def test_parse_function_invocations_from_block_ignores_non_invocation_lets() -> None:
    invocations = parse_function_invocations_from_block(
        """\
{
    let name = "ready"
    let status = active
}
"""
    )
    assert invocations == ()


def test_parse_function_invocations_from_block_rejects_parse_errors() -> None:
    with pytest.raises(FunctionParseError, match="parse errors"):
        _ = parse_function_invocations_from_block(
            """\
{
    call child.step()
"""
        )


def test_parse_function_statements_from_block_extracts_set_and_require() -> None:
    statements = parse_function_statements_from_block(
        """\
{
    let label = "ready"
    set display_name = label
    require exists(display_name) message "display name required"
}
"""
    )

    assert [stmt.kind for stmt in statements] == ["let", "set", "require"]
    assert statements[0].name == "label"
    assert statements[0].value is not None
    assert statements[0].value.kind == "literal"
    assert statements[0].value.literal_value == "ready"

    assert statements[1].name == "display_name"
    assert statements[1].value is not None
    assert statements[1].value.kind == "reference"
    assert statements[1].value.text == "label"

    assert statements[2].require_kind == "exists"
    assert [operand.text for operand in statements[2].require_operands] == [
        "display_name"
    ]
    assert statements[2].require_message == "display name required"


def test_parse_function_statements_from_block_extracts_guard_list_intrinsic() -> None:
    statements = parse_function_statements_from_block(
        """\
{
    let current_status = status
    require member(current_status, list.of(proposed, parked, blocked)) message "status guard failed"
}
"""
    )

    assert [stmt.kind for stmt in statements] == ["let", "require"]
    require = statements[1]
    assert require.require_kind == "member"
    assert len(require.require_operands) == 2
    assert require.require_operands[0].kind == "reference"
    assert require.require_operands[0].text == "current_status"
    assert require.require_operands[1].kind == "intrinsic"
    assert require.require_operands[1].target_path == ("list", "of")
    assert [arg.value.text for arg in require.require_operands[1].args] == [
        "proposed",
        "parked",
        "blocked",
    ]
    assert require.require_message == "status guard failed"


def test_parse_function_statements_from_block_extracts_invoke_args() -> None:
    statements = parse_function_statements_from_block(
        """\
{
    let created = construct child.make(name = alias, score = 1, true)
}
"""
    )

    assert len(statements) == 1
    stmt = statements[0]
    assert stmt.kind == "let"
    assert stmt.value is not None
    assert stmt.value.kind == "construct"
    assert [arg.name for arg in stmt.value.args] == ["name", "score", None]
    assert [arg.value.kind for arg in stmt.value.args] == [
        "reference",
        "literal",
        "literal",
    ]
    assert stmt.value.args[0].value.text == "alias"
    assert stmt.value.args[1].value.literal_value == 1
    assert stmt.value.args[2].value.literal_value is True


def test_parse_function_statements_from_block_extracts_explicit_class_construct_shape() -> (
    None
):
    statements = parse_function_statements_from_block(
        """\
{
    let built = construct Home(name = alias, is_on = true)
}
"""
    )

    assert len(statements) == 1
    stmt = statements[0]
    assert stmt.kind == "let"
    assert stmt.value is not None
    assert stmt.value.kind == "construct"
    assert stmt.value.target_path == ("Home",)
    assert [arg.name for arg in stmt.value.args] == ["name", "is_on"]
    assert [arg.value.kind for arg in stmt.value.args] == ["reference", "literal"]


def test_parse_function_statements_from_block_ignores_quoted_leading_docstring() -> (
    None
):
    statements = parse_function_statements_from_block(
        '''\
{
    """
    Joins a focus scope by linking this Actor to the FocusScope.

    Canonical v0:
    - This is the OS-level "shared attention" primitive.
    - Creates/ensures an ActorFocusScope(id=stable(actor_id, focus_scope_id)).
    - The FocusScope itself lives in the `focus_scope` projection lane (separate receipt).
    """
    let created_focus_scope = construct actor_focus_scopes.create(focus_scope_id = focus_scope_id)
}
'''
    )

    assert len(statements) == 1
    stmt = statements[0]
    assert stmt.kind == "let"
    assert stmt.name == "created_focus_scope"
    assert stmt.value is not None
    assert stmt.value.kind == "construct"
    assert stmt.value.target_path == ("actor_focus_scopes", "create")
    assert [arg.name for arg in stmt.value.args] == ["focus_scope_id"]
    assert [arg.value.kind for arg in stmt.value.args] == ["reference"]
