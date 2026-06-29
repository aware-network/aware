from __future__ import annotations

from collections.abc import Mapping

from tree_sitter import Node

from aware_code.language_service.programs import (
    intrinsic_signature,
    iter_program_body_statements,
    iter_program_calls_in_expr,
    resolve_owner_to_class,
)

from aware_meta_ontology.class_.class_config import ClassConfig

from .contracts import (
    ProgramAddDiagnostic,
    ProgramExperienceLookup,
    ProgramNodeTextFn,
    ProgramSuggestFn,
)
from .intrinsics import (
    call_target,
    check_call_arg_rules,
    check_intrinsic_signature,
    split_call_target,
)


def _declared_actor_aliases(
    *,
    statements: list[Node],
    node_text: ProgramNodeTextFn,
) -> frozenset[str]:
    aliases: set[str] = set()
    for stmt in statements:
        if stmt.type != "actor_decl_stmt":
            continue
        name_node = stmt.child_by_field_name("name")
        alias = node_text(name_node).strip() if name_node is not None else ""
        if alias:
            aliases.add(alias)
    return frozenset(aliases)


def _declared_port_node_aliases(
    *,
    statements: list[Node],
    node_text: ProgramNodeTextFn,
) -> frozenset[str]:
    aliases: set[str] = set()
    for stmt in statements:
        if stmt.type != "port_decl_stmt":
            continue
        body_node = stmt.child_by_field_name("body")
        if body_node is None:
            continue
        for child in body_node.named_children:
            if child.type != "port_decl_node_stmt":
                continue
            name_node = child.child_by_field_name("name")
            alias = node_text(name_node).strip() if name_node is not None else ""
            if alias:
                aliases.add(alias)
    return frozenset(aliases)


def collect_program_body_diagnostics(
    *,
    program_def: Node,
    declaration_statements: list[Node] | None,
    classes_by_fqn: Mapping[str, ClassConfig],
    experience_lookup: ProgramExperienceLookup,
    node_text: ProgramNodeTextFn,
    suggest: ProgramSuggestFn,
    add: ProgramAddDiagnostic,
) -> None:
    statements = list(iter_program_body_statements(program_def=program_def))
    declaration_scope_statements = (
        statements
        if declaration_statements is None
        else [*declaration_statements, *statements]
    )
    actor_aliases = _declared_actor_aliases(
        statements=declaration_scope_statements,
        node_text=node_text,
    )
    port_node_aliases = _declared_port_node_aliases(
        statements=declaration_scope_statements,
        node_text=node_text,
    )

    locals_seen: set[str] = set()
    lane_active = False

    for stmt in statements:
        if stmt.type == "port_decl_stmt":
            ref_node = stmt.child_by_field_name("ref")
            ref_text = node_text(ref_node).strip() if ref_node is not None else ""
            if ref_node is None or not ref_text:
                continue

            ref_parts = [part.strip() for part in ref_text.split(".") if part.strip()]
            if len(ref_parts) != 1:
                add(
                    start_byte=ref_node.start_byte,
                    end_byte=ref_node.end_byte,
                    message=(
                        "Port reference must use `<Experience>` form "
                        "(no head args, no root identity in the port ref)."
                    ),
                    code="aware.program.port_ref_invalid",
                )
                continue
            experience_ref = ref_parts[0]
            body_node = stmt.child_by_field_name("body")
            has_node_decl = False
            if body_node is not None:
                has_node_decl = any(child.type == "port_decl_node_stmt" for child in body_node.named_children)
            if not has_node_decl:
                add(
                    start_byte=ref_node.start_byte,
                    end_byte=ref_node.end_byte,
                    message=(
                        "Port declaration requires at least one node resolver contract "
                        "(`node <name> <ProjectionNode>(...)`)."
                    ),
                    code="aware.program.port_node_required",
                )
            if experience_ref not in experience_lookup.experience_names:
                if experience_ref in experience_lookup.projection_fallback_symbols:
                    continue
                add(
                    start_byte=ref_node.start_byte,
                    end_byte=ref_node.end_byte,
                    message=f"Port experience not found in package: {experience_ref!r}",
                    code="aware.program.port_projection_unresolved",
                    data={
                        "suggestions": suggest(
                            experience_ref,
                            list(experience_lookup.experience_candidates),
                        )
                    },
                )
                continue
            continue

        if stmt.type == "let_stmt":
            name_node = stmt.child_by_field_name("name")
            if name_node is not None:
                name = node_text(name_node).strip()
                if name and name in locals_seen:
                    add(
                        start_byte=name_node.start_byte,
                        end_byte=name_node.end_byte,
                        message=f"Duplicate let binding: {name!r}",
                        code="aware.program.let_duplicate",
                    )
                if name:
                    locals_seen.add(name)

            value_node = stmt.child_by_field_name("value")
            if value_node is not None:
                for call in iter_program_calls_in_expr(expr=value_node):
                    hit = call_target(call_node=call, node_text=node_text)
                    if hit is None:
                        continue
                    call_target_name, _target_node = hit
                    check_call_arg_rules(
                        target=call_target_name,
                        call_node=call,
                        node_text=node_text,
                        add=add,
                    )
                    check_intrinsic_signature(
                        target=call_target_name,
                        call_node=call,
                        in_call_stmt=False,
                        node_text=node_text,
                        add=add,
                    )
            continue

        call_node: Node
        target: str
        target_node: Node
        call_actor: str = ""
        call_actor_node: Node | None = None
        call_object_node: Node | None = None
        if stmt.type == "bind_stmt":
            call_node = stmt
            target = "bind"
            target_node = stmt
        else:
            if stmt.type != "call_stmt":
                continue
            call_node_candidate = stmt.child_by_field_name("call")
            if call_node_candidate is None:
                continue
            call_node = call_node_candidate
            call_actor_node = stmt.child_by_field_name("actor")
            call_actor = (
                node_text(call_actor_node).strip()
                if call_actor_node is not None
                else ""
            )
            call_object_node = stmt.child_by_field_name("object")
            hit = call_target(call_node=call_node, node_text=node_text)
            if hit is None:
                continue
            target, target_node = hit

        if target == "plan.bind":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message="call plan.bind(...) is not allowed; use bind(...) statement",
                code="aware.program.bind_legacy_call",
            )
            continue
        if target == "plan.lane":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message="call plan.lane(...) is not allowed; bind(...) is the canonical context activation surface",
                code="aware.program.lane_legacy_call",
            )
            continue
        if target == "plan.object":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=(
                    "call plan.object(...) is not allowed; use inline instance call selector "
                    "`call <object_id> ...`"
                ),
                code="aware.program.object_legacy_call",
            )
            continue

        if stmt.type == "call_stmt":
            if not call_actor:
                add(
                    start_byte=target_node.start_byte,
                    end_byte=target_node.end_byte,
                    message=(
                        "Invoke requires actor attribution: "
                        "`<actor_alias> call <port_node_alias> Owner.Class.fn(...)`."
                    ),
                    code="aware.program.invoke_actor_required",
                )
                continue
            if call_actor not in actor_aliases:
                add(
                    start_byte=call_actor_node.start_byte if call_actor_node is not None else target_node.start_byte,
                    end_byte=call_actor_node.end_byte if call_actor_node is not None else target_node.end_byte,
                    message=f"Invoke references undeclared actor alias: {call_actor!r}",
                    code="aware.program.invoke_actor_undeclared",
                    data={
                        "suggestions": suggest(
                            call_actor,
                            list(sorted(actor_aliases)),
                        )
                    },
                )
                continue

        check_call_arg_rules(
            target=target,
            call_node=call_node,
            node_text=node_text,
            add=add,
        )
        check_intrinsic_signature(
            target=target,
            call_node=call_node,
            in_call_stmt=True,
            node_text=node_text,
            add=add,
        )

        sig = intrinsic_signature(target)
        if sig is not None:
            if sig.kind == "directive" and target == "bind":
                lane_active = True
            continue

        if not lane_active:
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Invocation requires an active lane: bind(...) before {target}",
                code="aware.program.call_requires_lane",
            )
            continue

        split = split_call_target(target=target)
        if split is None:
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Invalid call target: {target!r}",
                code="aware.program.call_target_invalid",
            )
            continue

        owner, function_name = split
        owner_res = resolve_owner_to_class(owner=owner, classes_by_fqn=classes_by_fqn)

        if owner_res.status == "ambiguous":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Ambiguous call owner in program: {target!r} (candidates={list(owner_res.candidates)})",
                code="aware.program.call_owner_ambiguous",
                data={"candidates": owner_res.candidates},
            )
            continue

        if owner_res.status == "unresolved":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Call owner not found in workspace: {target!r}",
                code="aware.program.call_owner_unresolved",
            )
            continue

        class_cfg = owner_res.class_cfg
        if class_cfg is None or class_cfg.code_section_class is None:
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Call owner is missing a code definition in the workspace: {target!r}",
                code="aware.program.call_owner_missing_definition",
            )
            continue

        cls = class_cfg.code_section_class
        fn = next(
            (candidate for candidate in cls.code_section_functions if candidate.name == function_name),
            None,
        )
        if fn is None:
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=f"Function not found for call target: {target!r}",
                code="aware.program.call_function_unresolved",
            )
            continue

        verb = (getattr(fn, "verb", None) or "").strip().casefold()
        if verb == "construct":
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=(
                    "Constructor call is idempotent: executors skip construct calls when the lane "
                    "already has a head"
                ),
                code="aware.program.constructor_idempotency_hint",
                severity=4,
                data={"target": target, "function": function_name},
            )
            continue

        if call_object_node is None:
            add(
                start_byte=target_node.start_byte,
                end_byte=target_node.end_byte,
                message=(
                    "Invoke requires port-node selector: "
                    f"`<actor_alias> call <port_node_alias> {target}(...)`."
                ),
                code="aware.program.instance_requires_object",
            )
            continue

        call_object = node_text(call_object_node).strip()
        if not call_object:
            add(
                start_byte=call_object_node.start_byte,
                end_byte=call_object_node.end_byte,
                message=(
                    "Invoke selector must be a declared port node alias: "
                    "`<actor_alias> call <port_node_alias> Owner.Class.fn(...)`."
                ),
                code="aware.program.invoke_selector_unresolved",
            )
            continue

        if call_object not in port_node_aliases:
            add(
                start_byte=call_object_node.start_byte,
                end_byte=call_object_node.end_byte,
                message=(
                    f"Invoke selector must reference a declared port node alias; got {call_object!r}."
                ),
                code="aware.program.invoke_selector_unresolved",
                data={
                    "suggestions": suggest(
                        call_object,
                        list(sorted(port_node_aliases)),
                    )
                },
            )
