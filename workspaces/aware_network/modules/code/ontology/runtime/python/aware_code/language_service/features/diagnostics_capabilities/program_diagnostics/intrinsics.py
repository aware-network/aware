from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.programs import intrinsic_signature

from .contracts import ProgramAddDiagnostic, ProgramNodeTextFn


def call_target(
    *,
    call_node: Node,
    node_text: ProgramNodeTextFn,
) -> tuple[str, Node] | None:
    target_node = call_node.child_by_field_name("target")
    if target_node is None:
        return None
    target = node_text(target_node).strip()
    if not target:
        return None
    return target, target_node


def call_args(*, call_node: Node) -> list[Node]:
    args_node = call_node.child_by_field_name("args")
    if args_node is None:
        return []
    return [child for child in args_node.named_children if child.type == "call_arg"]


def check_call_arg_rules(
    *,
    target: str,
    call_node: Node,
    node_text: ProgramNodeTextFn,
    add: ProgramAddDiagnostic,
) -> None:
    saw_keyword = False
    keyword_names: set[str] = set()
    for arg in call_args(call_node=call_node):
        name_node = arg.child_by_field_name("name")
        name = node_text(name_node).strip() if name_node is not None else ""
        if not name:
            if saw_keyword:
                add(
                    start_byte=arg.start_byte,
                    end_byte=arg.end_byte,
                    message=f"Positional arguments cannot appear after keyword arguments in call to {target}",
                    code="aware.program.call_args_order_invalid",
                )
            continue

        saw_keyword = True
        if name in keyword_names:
            assert name_node is not None
            add(
                start_byte=name_node.start_byte,
                end_byte=name_node.end_byte,
                message=f"Duplicate keyword argument {name!r} in call to {target}",
                code="aware.program.call_args_duplicate_keyword",
            )
            continue
        keyword_names.add(name)


def check_intrinsic_signature(
    *,
    target: str,
    call_node: Node,
    in_call_stmt: bool,
    node_text: ProgramNodeTextFn,
    add: ProgramAddDiagnostic,
) -> None:
    sig = intrinsic_signature(target)
    if sig is None:
        return

    args = call_args(call_node=call_node)
    provided: dict[str, Node] = {}
    positional: list[Node] = []
    if target == "bind" and call_node.type == "bind_stmt":
        port_node = call_node.child_by_field_name("port")
        if port_node is not None and node_text(port_node).strip():
            provided["port"] = port_node
        view_node = call_node.child_by_field_name("view")
        if view_node is not None and node_text(view_node).strip():
            provided["view"] = view_node
    else:
        for arg in args:
            name_node = arg.child_by_field_name("name")
            name = node_text(name_node).strip() if name_node is not None else ""
            if not name:
                positional.append(arg)
                continue
            assert name_node is not None
            provided[name] = name_node

    if positional:
        for arg in positional:
            add(
                start_byte=arg.start_byte,
                end_byte=arg.end_byte,
                message=f"{target} requires keyword arguments (positional args are not supported)",
                code="aware.program.intrinsic_positional_args_not_allowed",
            )

    allowed = {param.name for param in sig.params}
    required = {param.name for param in sig.params if param.required}

    missing = sorted(required - set(provided.keys()))
    for name in missing:
        target_node = call_node.child_by_field_name("target")
        start_byte = target_node.start_byte if target_node is not None else call_node.start_byte
        end_byte = target_node.end_byte if target_node is not None else call_node.end_byte
        add(
            start_byte=start_byte,
            end_byte=end_byte,
            message=f"Missing required argument {name!r} for {target}",
            code="aware.program.intrinsic_args_missing",
            data={"signature": sig.render()},
        )

    for name, name_node in provided.items():
        if name in allowed:
            continue
        add(
            start_byte=name_node.start_byte,
            end_byte=name_node.end_byte,
            message=f"Unknown argument {name!r} for {target}",
            code="aware.program.intrinsic_args_unknown",
            data={"signature": sig.render()},
        )

    if in_call_stmt and sig.kind == "pure":
        target_node = call_node.child_by_field_name("target")
        start_byte = target_node.start_byte if target_node is not None else call_node.start_byte
        end_byte = target_node.end_byte if target_node is not None else call_node.end_byte
        add(
            start_byte=start_byte,
            end_byte=end_byte,
            message=f"{target} is a pure program stdlib call; use it in a `let` expression, not a `call` statement",
            code="aware.program.pure_intrinsic_used_as_statement",
        )


def split_call_target(*, target: str) -> tuple[str, str] | None:
    raw = (target or "").strip()
    if not raw or "." not in raw:
        return None
    owner, fn_name = raw.rsplit(".", 1)
    owner = (owner or "").strip()
    fn_name = (fn_name or "").strip()
    if not owner or not fn_name:
        return None
    return owner, fn_name
