from __future__ import annotations

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from tree_sitter import Node

from aware_meta.fqn_resolver import FqnScope

from .contracts import ProgramAddDiagnostic, ProgramNodeTextFn, ProgramSuggestFn


def collect_program_param_type_diagnostics(
    *,
    program_defs: list[Node],
    common_primitive_tokens: tuple[str, ...],
    scope: FqnScope,
    class_candidates: list[str],
    enum_candidates: list[str],
    node_text: ProgramNodeTextFn,
    suggest: ProgramSuggestFn,
    add: ProgramAddDiagnostic,
) -> None:
    primitive_type_tokens = {
        token.casefold().replace("_", "").replace(" ", "") for token in common_primitive_tokens
    }
    primitive_type_tokens.update(
        base.value.casefold().replace("_", "").replace(" ", "") for base in CodePrimitiveBaseType
    )

    for program_def in program_defs:
        params_node = program_def.child_by_field_name("params")
        if params_node is None:
            continue
        for param_node in params_node.named_children:
            if param_node.type != "program_param":
                continue
            type_node = param_node.child_by_field_name("type")
            if type_node is None:
                continue
            type_text = node_text(type_node).strip()
            if not type_text:
                continue
            normalized_type = type_text.casefold().replace("_", "").replace(" ", "")
            if normalized_type in primitive_type_tokens:
                continue
            if "." not in type_text:
                continue

            resolved_enum = scope.try_resolve_enum_with_fqn(type_text)
            resolved_class = scope.try_resolve_class_with_fqn(type_text)
            if resolved_enum is None and resolved_class is None:
                add(
                    start_byte=type_node.start_byte,
                    end_byte=type_node.end_byte,
                    message=(
                        "Program parameter type must resolve to a class/enum contract "
                        f"(not found: {type_text!r})"
                    ),
                    code="aware.program.param_type_unresolved",
                    data={
                        "suggestions": suggest(
                            type_text,
                            sorted({*class_candidates, *enum_candidates}),
                        )
                    },
                )
                continue
            if resolved_enum is not None and resolved_class is not None:
                add(
                    start_byte=type_node.start_byte,
                    end_byte=type_node.end_byte,
                    message=f"Program parameter type is ambiguous between enum and class contracts: {type_text!r}",
                    code="aware.program.param_type_ambiguous",
                )
