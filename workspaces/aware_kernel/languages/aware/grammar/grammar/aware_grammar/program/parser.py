from __future__ import annotations

import json
from typing import cast

from tree_sitter import Node, Parser

from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_grammar.program.ast import (
    ProgramCall,
    ProgramCallArg,
    ProgramDeclaration,
    ProgramExpr,
    ProgramExpectEventConfig,
    ProgramInput,
    ProgramIntentActionConfig,
    ProgramLet,
    ProgramParameter,
    ProgramRef,
    ProgramStmt,
)


class ProgramParseError(ValueError):
    """Raised when `.aware program { ... }` parsing fails."""


def _node_text(node: Node) -> str:
    if node.text is None:
        return ""
    return node.text.decode("utf-8")


def _parse_literal(text: str) -> str | int | float | bool | None:
    raw = (text or "").strip()
    if not raw:
        return ""

    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None

    if raw.startswith('"""') and raw.endswith('"""') and len(raw) >= 6:
        return raw[3:-3]
    if raw.startswith("$$") and raw.endswith("$$") and len(raw) >= 4:
        return raw[2:-2]

    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]

    # Numbers (v0): ints/floats only, no sign, no exponent.
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _coerce_json_member(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        list_value = cast(list[object], value)
        list_values: list[object] = []
        for item in list_value:
            list_values.append(_coerce_json_member(item))
        return list_values
    if isinstance(value, dict):
        map_value = cast(dict[object, object], value)
        map_values: dict[str, object] = {}
        for key, item in map_value.items():
            if not isinstance(key, str):
                raise ProgramParseError("JSON object keys must be strings")
            map_values[key] = _coerce_json_member(item)
        return map_values
    raise ProgramParseError(f"Unsupported JSON value in program literal: {value!r}")


def _parse_json_literal(node: Node) -> dict[str, object] | list[object]:
    try:
        parsed = cast(object, json.loads(_node_text(node)))
    except json.JSONDecodeError as exc:
        raise ProgramParseError(
            f"Invalid JSON literal in program: {exc}"
        ) from exc

    if isinstance(parsed, list):
        list_value = cast(list[object], parsed)
        list_values: list[object] = []
        for item in list_value:
            list_values.append(_coerce_json_member(item))
        return list_values
    if isinstance(parsed, dict):
        map_value = cast(dict[object, object], parsed)
        map_values: dict[str, object] = {}
        for key, item in map_value.items():
            if not isinstance(key, str):
                raise ProgramParseError("JSON object keys must be strings")
            map_values[key] = _coerce_json_member(item)
        return map_values
    raise ProgramParseError("Program JSON literal must be an object or array")


def _parse_expr(node: Node) -> ProgramExpr:
    # Older tree-sitter revisions used a named `program_expr` wrapper. Newer
    # grammar uses `_program_expr` (anonymous), so this unwrap keeps parsing
    # stable across both.
    if node.type == "program_expr":
        children = node.named_children
        if len(children) != 1:
            raise ProgramParseError("program_expr must contain exactly one expression")
        return _parse_expr(children[0])

    kind = node.type
    if kind == "program_call":
        return _parse_call(node)
    if kind == "qualified_name":
        return ProgramRef(_node_text(node).strip())
    if kind in {
        "literal",
        "string_literal",
        "number_literal",
        "boolean_literal",
        "null_literal",
        "triple_string_literal",
        "dollar_string_literal",
    }:
        return _parse_literal(_node_text(node))
    if kind in {"json_object", "json_array"}:
        return _parse_json_literal(node)
    raise ProgramParseError(f"Unsupported program expression node: {kind!r}")


def _parse_call(node: Node) -> ProgramCall:
    if node.type != "program_call":
        raise ProgramParseError(f"Expected program_call, got {node.type!r}")

    target_node = node.child_by_field_name("target")
    if target_node is None:
        raise ProgramParseError("program_call missing target")
    target = _node_text(target_node).strip()
    if not target:
        raise ProgramParseError("program_call target is empty")

    args_node = node.child_by_field_name("args")
    if args_node is None:
        raise ProgramParseError("program_call missing args")

    args = _parse_call_args(args_node)
    return ProgramCall(target=target, args=args)


def _parse_call_args(args_node: Node) -> tuple[ProgramCallArg, ...]:
    args: list[ProgramCallArg] = []
    for child in args_node.named_children:
        if child.type != "call_arg":
            continue
        name_node = child.child_by_field_name("name")
        name = _node_text(name_node).strip() if name_node is not None else None
        value_node = child.child_by_field_name("value")
        if value_node is None:
            raise ProgramParseError("call_arg missing value")
        value = _parse_expr(value_node)
        args.append(ProgramCallArg(name=name or None, value=value))
    return tuple(args)


def _parse_declaration_call_stmt(node: Node) -> ProgramCall:
    if node.type == "actor_decl_stmt":
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ProgramParseError("actor declaration missing name")
        key = _node_text(name_node).strip()
        if not key:
            raise ProgramParseError("actor declaration name is empty")

        actor_node = node.child_by_field_name("actor")
        if actor_node is None:
            raise ProgramParseError("actor declaration missing actor")
        actor = _node_text(actor_node).strip()
        if not actor:
            raise ProgramParseError("actor declaration actor is empty")

        return ProgramCall(
            target="program.actor",
            args=(
                ProgramCallArg(name="key", value=key),
                ProgramCallArg(name="actor", value=actor),
            ),
        )

    if node.type == "port_decl_stmt":
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ProgramParseError("port declaration missing name")
        key = _node_text(name_node).strip()
        if not key:
            raise ProgramParseError("port declaration name is empty")

        ref_node = node.child_by_field_name("ref")
        if ref_node is None:
            raise ProgramParseError("port declaration missing ref")
        ref = _node_text(ref_node).strip()
        if not ref:
            raise ProgramParseError("port declaration ref is empty")
        ref_parts = [part for part in ref.split(".") if part]
        if len(ref_parts) != 1:
            raise ProgramParseError(
                "port declaration ref must use `<Experience>` form"
            )

        args: list[ProgramCallArg] = [ProgramCallArg(name="key", value=key)]

        params_node = node.child_by_field_name("params")
        if params_node is not None:
            raise ProgramParseError(
                "port declaration does not accept head args; "
                + "move resolver keys into `node <alias> <node>(...)` contracts"
            )

        body_node = node.child_by_field_name("body")
        if body_node is None:
            raise ProgramParseError("port declaration missing body")
        field_names: set[str] = set()
        for child in body_node.named_children:
            if child.type == "port_decl_description_stmt":
                value_node = child.child_by_field_name("value")
                if value_node is not None:
                    args.append(
                        ProgramCallArg(name="description", value=_node_text(value_node))
                    )
                continue
            if child.type == "port_decl_node_stmt":
                node_name_node = child.child_by_field_name("name")
                if node_name_node is None:
                    raise ProgramParseError("port node declaration missing name")
                node_name = _node_text(node_name_node).strip()
                if not node_name:
                    raise ProgramParseError("port node declaration name is empty")
                node_ref_node = child.child_by_field_name("ref")
                if node_ref_node is None:
                    raise ProgramParseError("port node declaration missing ref")
                node_ref = _node_text(node_ref_node).strip()
                if not node_ref:
                    raise ProgramParseError("port node declaration ref is empty")
                args.append(
                    ProgramCallArg(name=f"node_{node_name}", value=node_ref)
                )
                node_params = child.child_by_field_name("params")
                if node_params is not None:
                    for node_param in node_params.named_children:
                        if node_param.type != "port_decl_param":
                            continue
                        node_param_name_node = node_param.child_by_field_name("name")
                        if node_param_name_node is None:
                            raise ProgramParseError(
                                "port node declaration param missing name"
                            )
                        node_param_name = _node_text(node_param_name_node).strip()
                        if not node_param_name:
                            raise ProgramParseError(
                                "port node declaration param name is empty"
                            )
                        node_value_node = node_param.child_by_field_name("value")
                        node_value = (
                            ProgramRef(node_param_name)
                            if node_value_node is None
                            else _parse_expr(node_value_node)
                        )
                        args.append(
                            ProgramCallArg(
                                name=f"node_{node_name}_key_{node_param_name}",
                                value=node_value,
                            )
                        )
                continue
            if child.type != "port_decl_field_stmt":
                continue
            field_name_node = child.child_by_field_name("name")
            if field_name_node is None:
                raise ProgramParseError("port declaration field missing name")
            field_name = _node_text(field_name_node).strip()
            if not field_name:
                raise ProgramParseError("port declaration field name is empty")
            field_names.add(field_name)
            field_value_node = child.child_by_field_name("value")
            if field_value_node is None:
                raise ProgramParseError(
                    f"port declaration field {field_name!r} missing value"
                )
            args.append(
                ProgramCallArg(name=field_name, value=_parse_expr(field_value_node))
            )
        projection_ref = ref_parts[0]
        if "projection" not in field_names:
            args.append(ProgramCallArg(name="projection", value=projection_ref))
        return ProgramCall(target="program.port", args=tuple(args))

    target_by_type = {
        "layout_decl_stmt": "plan.layout",
        "section_decl_stmt": "plan.section",
        "slot_decl_stmt": "plan.slot",
    }
    target = target_by_type.get(node.type)
    if not target:
        raise ProgramParseError(f"Unsupported declaration statement node: {node.type!r}")

    args_node = node.child_by_field_name("args")
    if args_node is None:
        raise ProgramParseError(f"{node.type} missing args")
    return ProgramCall(target=target, args=_parse_call_args(args_node))


def _parse_program_param(node: Node) -> ProgramParameter:
    if node.type != "program_param":
        raise ProgramParseError(f"Expected program_param, got {node.type!r}")
    name_node = node.child_by_field_name("name")
    if name_node is None:
        raise ProgramParseError("program_param missing name")
    name = _node_text(name_node).strip()
    if not name:
        raise ProgramParseError("program_param name is empty")
    type_node = node.child_by_field_name("type")
    if type_node is None:
        raise ProgramParseError("program_param missing type")
    type_ref = _node_text(type_node).strip()
    if not type_ref:
        raise ProgramParseError("program_param type is empty")
    default_node = node.child_by_field_name("default")
    return ProgramParameter(
        name=name,
        type_ref=type_ref,
        default=_parse_expr(default_node) if default_node is not None else None,
    )


def _parse_stmt(node: Node) -> ProgramStmt:
    # Older tree-sitter revisions used a named `program_stmt` wrapper. Newer
    # grammar uses `_program_stmt` (anonymous), so unwrap if present.
    if node.type == "program_stmt":
        children = node.named_children
        if len(children) != 1:
            raise ProgramParseError("program_stmt must contain exactly one statement")
        return _parse_stmt(children[0])

    if node.type == "let_stmt":
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ProgramParseError("let_stmt missing name")
        name = _node_text(name_node).strip()
        if not name:
            raise ProgramParseError("let_stmt name is empty")
        value_node = node.child_by_field_name("value")
        if value_node is None:
            raise ProgramParseError("let_stmt missing value")
        return ProgramLet(name=name, value=_parse_expr(value_node))

    if node.type == "input_stmt":
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ProgramParseError("input_stmt missing name")
        name = _node_text(name_node).strip()
        if not name:
            raise ProgramParseError("input_stmt name is empty")

        source_node = node.child_by_field_name("source")
        if source_node is None:
            raise ProgramParseError("input_stmt missing source")
        default_node = node.child_by_field_name("default")
        return ProgramInput(
            name=name,
            source=_parse_expr(source_node),
            default=_parse_expr(default_node) if default_node is not None else None,
        )

    if node.type == "expect_stmt":
        ref_node = node.child_by_field_name("ref")
        if ref_node is None:
            raise ProgramParseError("expect_stmt missing ref")
        requirement_node = node.child_by_field_name("requirement")
        requirement = _node_text(requirement_node).strip() if requirement_node else ""
        if not requirement:
            required = True
        elif requirement == "required":
            required = True
        elif requirement == "optional":
            required = False
        else:
            raise ProgramParseError(f"Unsupported expect requirement: {requirement!r}")
        return ProgramExpectEventConfig(ref=_parse_expr(ref_node), required=required)

    if node.type == "intent_stmt":
        action_ref_node = node.child_by_field_name("action_ref")
        if action_ref_node is None:
            raise ProgramParseError("intent_stmt missing action_ref")
        event_ref_node = node.child_by_field_name("event_ref")
        if event_ref_node is None:
            raise ProgramParseError("intent_stmt missing event_ref")
        return ProgramIntentActionConfig(
            action_ref=_parse_expr(action_ref_node),
            event_ref=_parse_expr(event_ref_node),
        )

    if node.type == "call_stmt":
        actor_node = node.child_by_field_name("actor")
        actor = _node_text(actor_node).strip() if actor_node is not None else ""
        call_node = node.child_by_field_name("call")
        if call_node is None:
            raise ProgramParseError("call_stmt missing call")
        call = _parse_call(call_node)
        object_node = node.child_by_field_name("object")
        if object_node is None:
            return ProgramCall(
                target=call.target,
                args=call.args,
                object_expr=None,
                actor=actor or None,
            )
        return ProgramCall(
            target=call.target,
            args=call.args,
            object_expr=_parse_expr(object_node),
            actor=actor or None,
        )

    if node.type == "bind_stmt":
        port_node = node.child_by_field_name("port")
        if port_node is None:
            raise ProgramParseError("bind_stmt missing port")
        view_node = node.child_by_field_name("view")
        if view_node is None:
            raise ProgramParseError("bind_stmt missing view")

        port_ref = _node_text(port_node).strip()
        if not port_ref:
            raise ProgramParseError("bind_stmt port is empty")
        if not port_ref.startswith("program.port."):
            port_ref = f"program.port.{port_ref}"

        view_key = _node_text(view_node).strip()
        if not view_key:
            raise ProgramParseError("bind_stmt view is empty")

        return ProgramCall(
            target="bind",
            args=(
                ProgramCallArg(name="port", value=ProgramRef(port_ref)),
                ProgramCallArg(name="view_key", value=view_key),
            ),
        )

    if node.type in {
        "actor_decl_stmt",
        "port_decl_stmt",
        "layout_decl_stmt",
        "section_decl_stmt",
        "slot_decl_stmt",
    }:
        return _parse_declaration_call_stmt(node)

    raise ProgramParseError(f"Unsupported program statement node: {node.type!r}")


def parse_program_declarations(source: str) -> tuple[ProgramDeclaration, ...]:
    """
    Parse `.aware` `program` declarations from `source`.

    v1 supports:
    - `program Name(<param_name> <TypeRef>[ = <expr>], ...) { ... }` (config form)
    - `program ImplName impl ConfigName { ... }` (impl form; no params)
    - `actor <name> <global_actor>`
    - `port <name> <Experience> { node <alias> <node>.<id> | node <alias> <node>(...) ... }`
    - `input <ident> from <qualified_name> [default <expr>]`
    - `expect event_config <expr> [required|optional]`
    - `intent action_config <expr> on event_config <expr>`
    - `let <ident> = <expr>`
    - `bind <port_name> <Projection>.<View>`
    - `call [ <qualified_name> ] <qualified_name>(...)`

    Expressions:
    - qualified name refs (e.g. `identity.Identity.signup`)
    - calls
    - scalar literals (`"..."`, `'...'`, `123`, `true`, `null`, `$$...$$`, triple-quoted blocks)
    - strict JSON objects/arrays
    """

    parser = Parser(language=AWARE_LANGUAGE)
    tree = parser.parse((source or "").encode("utf-8"))
    if tree.root_node.has_error:
        raise ProgramParseError("Aware program source contains parse errors")

    programs: list[ProgramDeclaration] = []
    for child in tree.root_node.named_children:
        if child.type != "program_def":
            continue

        name_node = child.child_by_field_name("name")
        if name_node is None:
            raise ProgramParseError("program_def missing name")
        name = _node_text(name_node).strip()
        if not name:
            raise ProgramParseError("program_def name is empty")

        impl_of: str | None = None
        impl_node = child.child_by_field_name("impl")
        if impl_node is not None:
            impl_value = _node_text(impl_node).strip()
            if not impl_value:
                raise ProgramParseError("program_def impl reference is empty")
            impl_of = impl_value

        params: list[ProgramParameter] = []
        params_node = child.child_by_field_name("params")
        if params_node is not None:
            for param_node in params_node.named_children:
                if param_node.type != "program_param":
                    continue
                params.append(_parse_program_param(param_node))

        body_node = child.child_by_field_name("body")
        if body_node is None:
            raise ProgramParseError("program_def missing body")

        stmts: list[ProgramStmt] = []
        for body_child in body_node.named_children:
            if body_child.type == "comment":
                continue
            if body_child.type in {"ports_decl_block", "layout_decl_block"}:
                for decl_child in body_child.named_children:
                    if decl_child.type == "comment":
                        continue
                    stmts.append(_parse_stmt(decl_child))
                continue
            stmts.append(_parse_stmt(body_child))

        programs.append(
            ProgramDeclaration(
                name=name,
                statements=tuple(stmts),
                parameters=tuple(params),
                impl_of=impl_of,
            )
        )

    return tuple(programs)
