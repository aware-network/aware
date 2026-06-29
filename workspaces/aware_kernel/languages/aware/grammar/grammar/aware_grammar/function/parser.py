from __future__ import annotations

import ast
from dataclasses import dataclass

from tree_sitter import Node, Parser

from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


class FunctionParseError(ValueError):
    """Raised when tree-sitter parsing of an Aware function body fails."""


@dataclass(frozen=True, slots=True)
class FunctionBodyInvocation:
    line_number: int
    column_number: int
    kind: str
    target_path: tuple[str, ...]
    capture_name: str | None
    args: tuple[FunctionBodyCallArg, ...] = ()


@dataclass(frozen=True, slots=True)
class FunctionBodyExpression:
    line_number: int
    column_number: int
    kind: str
    text: str
    target_path: tuple[str, ...] = ()
    literal_value: object | None = None
    args: tuple[FunctionBodyCallArg, ...] = ()


@dataclass(frozen=True, slots=True)
class FunctionBodyCallArg:
    name: str | None
    value: FunctionBodyExpression


@dataclass(frozen=True, slots=True)
class FunctionBodyStatement:
    line_number: int
    column_number: int
    kind: str
    end_line_number: int | None = None
    name: str | None = None
    value: FunctionBodyExpression | None = None
    invoke_kind: str | None = None
    target_path: tuple[str, ...] = ()
    capture_name: str | None = None
    invoke_args: tuple[FunctionBodyCallArg, ...] = ()
    require_kind: str | None = None
    require_operands: tuple[FunctionBodyExpression, ...] = ()
    require_message: str | None = None


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8")


def _line_number(point: tuple[int, int], *, line_offset: int) -> int:
    return max(1, point[0] + 1 - line_offset)


def _unwrap_single_named_child(node: Node) -> Node:
    children = node.named_children
    if len(children) != 1:
        raise FunctionParseError(f"{node.type} must contain exactly one named child")
    return children[0]


def _decode_string_literal(node: Node) -> str:
    text = _node_text(node)
    if node.type == "string_literal":
        try:
            value = ast.literal_eval(text)
        except Exception as exc:
            raise FunctionParseError(f"Invalid string literal: {text!r}") from exc
        return value if isinstance(value, str) else str(value)
    if (
        node.type == "triple_string_literal"
        and text.startswith('"""')
        and text.endswith('"""')
    ):
        return text[3:-3]
    if (
        node.type == "dollar_string_literal"
        and text.startswith("$$")
        and text.endswith("$$")
    ):
        return text[2:-2]
    return text


def _parse_literal_expr(node: Node, *, line_offset: int) -> FunctionBodyExpression:
    literal_node = node
    if literal_node.type == "literal":
        literal_node = _unwrap_single_named_child(literal_node)

    start_point = literal_node.start_point
    line_number = _line_number(start_point, line_offset=line_offset)
    column_number = max(1, start_point[1] + 1)

    if literal_node.type in {
        "string_literal",
        "triple_string_literal",
        "dollar_string_literal",
    }:
        return FunctionBodyExpression(
            line_number=line_number,
            column_number=column_number,
            kind="literal",
            text=_node_text(literal_node),
            literal_value=_decode_string_literal(literal_node),
        )
    if literal_node.type == "number_literal":
        raw = _node_text(literal_node).strip()
        value: object
        if "." in raw:
            try:
                value = float(raw)
            except ValueError as exc:
                raise FunctionParseError(f"Invalid number literal: {raw!r}") from exc
        else:
            try:
                value = int(raw)
            except ValueError as exc:
                raise FunctionParseError(f"Invalid number literal: {raw!r}") from exc
        return FunctionBodyExpression(
            line_number=line_number,
            column_number=column_number,
            kind="literal",
            text=raw,
            literal_value=value,
        )
    if literal_node.type == "boolean_literal":
        raw = _node_text(literal_node).strip().lower()
        if raw not in {"true", "false"}:
            raise FunctionParseError(f"Invalid boolean literal: {raw!r}")
        return FunctionBodyExpression(
            line_number=line_number,
            column_number=column_number,
            kind="literal",
            text=raw,
            literal_value=(raw == "true"),
        )
    if literal_node.type == "null_literal":
        return FunctionBodyExpression(
            line_number=line_number,
            column_number=column_number,
            kind="literal",
            text="null",
            literal_value=None,
        )
    raise FunctionParseError(f"Unsupported literal expression: {literal_node.type!r}")


def _parse_invocation_expr(
    *,
    expr_node: Node,
    let_capture: str | None,
    line_offset: int,
) -> FunctionBodyInvocation:
    if expr_node.type not in {"fn_call_expr", "fn_construct_expr"}:
        raise FunctionParseError(
            f"Unsupported function invocation expression: {expr_node.type!r}"
        )

    target_node = expr_node.child_by_field_name("target")
    if target_node is None:
        raise FunctionParseError(f"{expr_node.type} missing target")
    target_path = _parse_invoke_target(target_node=target_node)
    if not target_path:
        raise FunctionParseError(f"{expr_node.type} target must include function name")
    invoke_node = target_node
    if invoke_node.type == "fn_invoke_target":
        invoke_node = _unwrap_single_named_child(invoke_node)
    args_node = invoke_node.child_by_field_name("args")
    if args_node is None:
        raise FunctionParseError(f"{expr_node.type} target missing args")
    args = _parse_invoke_args(args_node=args_node, line_offset=line_offset)

    capture_name = (let_capture or "").strip() or None
    if capture_name is None:
        capture_node = expr_node.child_by_field_name("capture")
        capture_name = (_node_text(capture_node) or "").strip() or None

    start_point = target_node.start_point
    return FunctionBodyInvocation(
        line_number=max(1, start_point[0] + 1 - line_offset),
        column_number=max(1, start_point[1] + 1),
        kind="construct" if expr_node.type == "fn_construct_expr" else "call",
        target_path=target_path,
        capture_name=capture_name,
        args=args,
    )


def _parse_stmt_expression(
    *, expr_node: Node, line_offset: int
) -> FunctionBodyExpression:
    node = expr_node
    if node.type == "fn_stmt_expr":
        node = _unwrap_single_named_child(node)

    if node.type in {"fn_call_expr", "fn_construct_expr"}:
        invocation = _parse_invocation_expr(
            expr_node=node,
            let_capture=None,
            line_offset=line_offset,
        )
        return FunctionBodyExpression(
            line_number=invocation.line_number,
            column_number=invocation.column_number,
            kind=invocation.kind,
            text=".".join(invocation.target_path),
            target_path=invocation.target_path,
            args=invocation.args,
        )

    if node.type == "program_call":
        target_node = node.child_by_field_name("target")
        if target_node is None:
            raise FunctionParseError("program_call missing target")
        target_path = tuple(
            part for part in _node_text(target_node).strip().split(".") if part
        )
        if not target_path:
            raise FunctionParseError("program_call target must not be empty")
        args_node = node.child_by_field_name("args")
        if args_node is None:
            raise FunctionParseError("program_call missing args")
        start_point = target_node.start_point
        return FunctionBodyExpression(
            line_number=max(1, start_point[0] + 1 - line_offset),
            column_number=max(1, start_point[1] + 1),
            kind="intrinsic",
            text=".".join(target_path),
            target_path=target_path,
            args=_parse_invoke_args(args_node=args_node, line_offset=line_offset),
        )

    if node.type in {"ident", "qualified_name"}:
        start_point = node.start_point
        return FunctionBodyExpression(
            line_number=max(1, start_point[0] + 1 - line_offset),
            column_number=max(1, start_point[1] + 1),
            kind="reference",
            text=_node_text(node).strip(),
        )

    return _parse_literal_expr(node, line_offset=line_offset)


def _parse_invoke_target(*, target_node: Node) -> tuple[str, ...]:
    node = target_node
    if node.type == "fn_invoke_target":
        node = _unwrap_single_named_child(node)

    if node.type == "fn_member_invoke":
        receiver_node = node.child_by_field_name("receiver")
        function_node = node.child_by_field_name("function")
        receiver_parts = tuple(
            part for part in _node_text(receiver_node).strip().split(".") if part
        )
        function_name = _node_text(function_node).strip()
        if not receiver_parts or not function_name:
            return ()
        return (*receiver_parts, function_name)

    if node.type == "fn_local_invoke":
        function_node = node.child_by_field_name("function")
        function_name = _node_text(function_node).strip()
        if not function_name:
            return ()
        return (function_name,)

    return ()


def _parse_invoke_args(
    *, args_node: Node, line_offset: int
) -> tuple[FunctionBodyCallArg, ...]:
    args: list[FunctionBodyCallArg] = []
    for child in args_node.named_children:
        if child.type != "call_arg":
            continue
        name_node = child.child_by_field_name("name")
        name = _node_text(name_node).strip() if name_node is not None else None
        value_node = child.child_by_field_name("value")
        if value_node is None:
            raise FunctionParseError("call_arg missing value")
        args.append(
            FunctionBodyCallArg(
                name=(name or None),
                value=_parse_stmt_expression(
                    expr_node=value_node, line_offset=line_offset
                ),
            )
        )
    return tuple(args)


def _parse_stmt(node: Node, *, line_offset: int) -> FunctionBodyStatement | None:
    if node.type == "fn_stmt":
        if not node.named_children:
            return None
        return _parse_stmt(node.named_children[0], line_offset=line_offset)

    if node.type in {"fn_call_stmt", "fn_construct_stmt"}:
        if not node.named_children:
            raise FunctionParseError(f"{node.type} missing invocation expression")
        expr_node = node.named_children[0]
        invocation = _parse_invocation_expr(
            expr_node=expr_node,
            let_capture=None,
            line_offset=line_offset,
        )
        return FunctionBodyStatement(
            line_number=invocation.line_number,
            column_number=invocation.column_number,
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="invoke",
            invoke_kind=invocation.kind,
            target_path=invocation.target_path,
            capture_name=invocation.capture_name,
            invoke_args=invocation.args,
        )

    if node.type == "fn_let_stmt":
        let_name = (_node_text(node.child_by_field_name("name")) or "").strip() or None
        value_node = node.child_by_field_name("value")
        if value_node is None:
            raise FunctionParseError("fn_let_stmt missing value")
        expr = _parse_stmt_expression(
            expr_node=value_node,
            line_offset=line_offset,
        )
        return FunctionBodyStatement(
            line_number=_line_number(node.start_point, line_offset=line_offset),
            column_number=max(1, node.start_point[1] + 1),
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="let",
            name=let_name,
            value=expr,
        )

    if node.type == "fn_set_stmt":
        target_name = (_node_text(node.child_by_field_name("target")) or "").strip()
        if not target_name:
            raise FunctionParseError("fn_set_stmt missing target")
        value_node = node.child_by_field_name("value")
        if value_node is None:
            raise FunctionParseError("fn_set_stmt missing value")
        expr = _parse_stmt_expression(expr_node=value_node, line_offset=line_offset)
        return FunctionBodyStatement(
            line_number=_line_number(node.start_point, line_offset=line_offset),
            column_number=max(1, node.start_point[1] + 1),
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="set",
            name=target_name,
            value=expr,
        )

    if node.type == "fn_require_stmt":
        require_kind = (_node_text(node.child_by_field_name("kind")) or "").strip()
        if not require_kind:
            raise FunctionParseError("fn_require_stmt missing kind")

        operands_node = node.child_by_field_name("operands")
        operands: list[FunctionBodyExpression] = []
        if operands_node is not None:
            for child in operands_node.named_children:
                operands.append(
                    _parse_stmt_expression(expr_node=child, line_offset=line_offset)
                )

        message: str | None = None
        message_node = node.child_by_field_name("message")
        if message_node is not None:
            literal_node: Node | None = None
            if message_node.type == "fn_require_message":
                for child in message_node.named_children:
                    if child.type in {
                        "string_literal",
                        "triple_string_literal",
                        "dollar_string_literal",
                    }:
                        literal_node = child
                        break
            elif message_node.type in {
                "string_literal",
                "triple_string_literal",
                "dollar_string_literal",
            }:
                literal_node = message_node
            if literal_node is None:
                raise FunctionParseError(
                    "fn_require_stmt message must be a string literal"
                )
            message = _decode_string_literal(literal_node)

        return FunctionBodyStatement(
            line_number=_line_number(node.start_point, line_offset=line_offset),
            column_number=max(1, node.start_point[1] + 1),
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="require",
            require_kind=require_kind,
            require_operands=tuple(operands),
            require_message=message,
        )

    if node.type == "fn_delete_stmt":
        target = (_node_text(node.child_by_field_name("target")) or "").strip()
        if target != "self":
            raise FunctionParseError("fn_delete_stmt target must be `self`")
        return FunctionBodyStatement(
            line_number=_line_number(node.start_point, line_offset=line_offset),
            column_number=max(1, node.start_point[1] + 1),
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="delete",
            target_path=("self",),
        )

    if node.type in {"fn_call_expr", "fn_construct_expr"}:
        invocation = _parse_invocation_expr(
            expr_node=node, let_capture=None, line_offset=line_offset
        )
        return FunctionBodyStatement(
            line_number=invocation.line_number,
            column_number=invocation.column_number,
            end_line_number=_line_number(node.end_point, line_offset=line_offset),
            kind="invoke",
            invoke_kind=invocation.kind,
            target_path=invocation.target_path,
            capture_name=invocation.capture_name,
            invoke_args=invocation.args,
        )

    return None


def _blank_preserving_newlines(text: str) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in text)


def _mask_leading_docstring_block(block_source: str) -> str:
    """Blank the leading function docstring while preserving line positions."""

    source = block_source
    if not source.startswith("{"):
        return source

    cursor = 1
    while cursor < len(source) and source[cursor].isspace():
        cursor += 1

    delimiter: str | None = None
    if source.startswith('"""', cursor):
        delimiter = '"""'
    elif source.startswith("$$", cursor):
        delimiter = "$$"
    if delimiter is None:
        return source

    end = source.find(delimiter, cursor + len(delimiter))
    if end < 0:
        return source
    end += len(delimiter)

    return (
        source[:cursor] + _blank_preserving_newlines(source[cursor:end]) + source[end:]
    )


def _parse_block_statements(block_source: str) -> list[FunctionBodyStatement]:
    source = (block_source or "").strip()
    if not source:
        return []

    wrapped_source = source
    extra_line_offset = 0
    if not wrapped_source.startswith("{"):
        wrapped_source = "{\n" + wrapped_source + "\n}"
        extra_line_offset = 1

    # FunctionImpl parsing only cares about executable statements. Mask the leading
    # docstring so triple-quoted text cannot swallow the first real statement.
    wrapped_source = _mask_leading_docstring_block(wrapped_source)

    wrapper_prefix = "class __AwareFnParseTmp__ {\n    fn __aware_tmp__ () -> String\n"
    wrapper_suffix = "\n}\n"
    parser_source = wrapper_prefix + wrapped_source + wrapper_suffix
    line_offset = wrapper_prefix.count("\n") + extra_line_offset

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse(parser_source.encode("utf-8"))
    if tree.root_node.has_error:
        raise FunctionParseError("Aware function body source contains parse errors")

    fn_node: Node | None = None
    for child in tree.root_node.named_children:
        if child.type != "class_def":
            continue
        for class_child in child.named_children:
            if class_child.type == "fn_def":
                fn_node = class_child
                break
        if fn_node is not None:
            break
    if fn_node is None:
        raise FunctionParseError(
            "Failed to locate wrapper fn_def while parsing function body"
        )

    block_node = fn_node.child_by_field_name("body")
    if block_node is None:
        for child in fn_node.named_children:
            if child.type == "block":
                block_node = child
                break
    if block_node is None or block_node.type != "block":
        return []

    statements: list[FunctionBodyStatement] = []
    for stmt_node in block_node.named_children:
        statement = _parse_stmt(stmt_node, line_offset=line_offset)
        if statement is None:
            continue
        statements.append(statement)

    statements.sort(key=lambda item: (item.line_number, item.column_number))
    return statements


def parse_function_statements_from_block(
    block_source: str,
) -> tuple[FunctionBodyStatement, ...]:
    """Parse canonical function-body statements from an Aware function body block."""

    return tuple(_parse_block_statements(block_source))


def parse_function_invocations_from_block(
    block_source: str,
) -> tuple[FunctionBodyInvocation, ...]:
    """Parse invocation statements (`call`/`construct`) from an Aware function body block."""

    invocations: list[FunctionBodyInvocation] = []
    for statement in _parse_block_statements(block_source):
        if statement.kind == "invoke" and statement.invoke_kind in {
            "call",
            "construct",
        }:
            invocations.append(
                FunctionBodyInvocation(
                    line_number=statement.line_number,
                    column_number=statement.column_number,
                    kind=statement.invoke_kind,
                    target_path=statement.target_path,
                    capture_name=statement.capture_name,
                    args=statement.invoke_args,
                )
            )
            continue

        if (
            statement.kind == "let"
            and statement.value is not None
            and statement.value.kind in {"call", "construct"}
        ):
            invocations.append(
                FunctionBodyInvocation(
                    line_number=statement.value.line_number,
                    column_number=statement.value.column_number,
                    kind=statement.value.kind,
                    target_path=statement.value.target_path,
                    capture_name=statement.name,
                    args=statement.value.args,
                )
            )

    invocations.sort(key=lambda item: (item.line_number, item.column_number))
    return tuple(invocations)
