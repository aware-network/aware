from __future__ import annotations

from collections.abc import Callable, Mapping
from difflib import get_close_matches
from pathlib import Path

from tree_sitter import Node


from aware_code.language_service.position import Utf16PositionMapper
from aware_code.language_service.programs import (
    iter_program_body_statements,
    iter_program_defs,
    parse_tree,
)

from aware_code.language_service.snapshot import CodeLanguageServiceSnapshot

from ..contracts import AwareDiagnostic, DiagnosticDataValue
from .call_resolution import collect_program_body_diagnostics
from .contracts import (
    ProgramAddDiagnostic,
    ProgramNodeTextFn,
    ProgramSuggestFn,
)
from .experience import build_experience_lookup, resolve_experience_root_for_path
from .param_types import collect_program_param_type_diagnostics


def collect_program_diagnostics(
    *,
    snapshot: CodeLanguageServiceSnapshot | None,
    uri_to_path: Callable[[str], Path],
    common_primitive_tokens: tuple[str, ...],
    uri: str,
    document_bytes: bytes,
    mapper: Utf16PositionMapper,
) -> list[AwareDiagnostic]:
    if snapshot is None:
        return []
    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return []
    if not document_bytes or b"program" not in document_bytes:
        return []

    root = parse_tree(document_bytes=document_bytes)
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)
    classes_by_fqn = snapshot.fqn_resolver.classes_by_fqn
    enums_by_fqn = snapshot.fqn_resolver.enums_by_fqn
    class_candidates = sorted(classes_by_fqn.keys())
    enum_candidates = sorted(enums_by_fqn.keys())

    diagnostics: list[AwareDiagnostic] = []

    def node_text(node: Node | None) -> str:
        if node is None or node.text is None:
            return ""
        return node.text.decode("utf-8", errors="replace")

    def add(
        *,
        start_byte: int,
        end_byte: int,
        message: str,
        code: str,
        severity: int = 1,
        data: Mapping[str, DiagnosticDataValue] | None = None,
    ) -> None:
        if end_byte <= start_byte:
            return
        start = mapper.byte_offset_to_position(start_byte)
        end = mapper.byte_offset_to_position(end_byte)
        diagnostic: AwareDiagnostic = {
            "message": message,
            "severity": severity,
            "source": "aware",
            "code": code,
            "range": {
                "start": {"line": start.line, "character": start.character},
                "end": {"line": end.line, "character": end.character},
            },
        }
        if data is not None:
            diagnostic["data"] = data
        diagnostics.append(diagnostic)

    def suggest(value: str, options: list[str]) -> list[str]:
        normalized = (value or "").strip()
        if not normalized:
            return []
        return list(get_close_matches(normalized, options, n=3, cutoff=0.6))

    add_fn: ProgramAddDiagnostic = add
    suggest_fn: ProgramSuggestFn = suggest
    node_text_fn: ProgramNodeTextFn = node_text

    experience_lookup = build_experience_lookup(
        snapshot=snapshot,
        uri_to_path=uri_to_path,
        uri=uri,
    )

    program_defs = list(iter_program_defs(root=root))
    program_defs_by_name: dict[str, Node] = {}
    for program_def in program_defs:
        name_node = program_def.child_by_field_name("name")
        name = node_text(name_node).strip()
        if name_node is None or not name:
            continue
        program_defs_by_name[name] = program_def

    if program_defs:
        uri_path = uri_to_path(uri)
        if resolve_experience_root_for_path(path=uri_path) is None:
            add(
                start_byte=program_defs[0].start_byte,
                end_byte=program_defs[-1].end_byte,
                message=(
                    "Program declarations must live inside an experience package "
                    "(nearest aware.experience.toml not found)."
                ),
                code="aware.program.experience_required",
                severity=2,
            )

    for program_def in program_defs:
        if program_def.has_error:
            add(
                start_byte=program_def.start_byte,
                end_byte=program_def.end_byte,
                message="Program block contains parse errors",
                code="aware.program.parse_error",
            )

        declaration_statements: list[Node] | None = None
        impl_node = program_def.child_by_field_name("impl")
        impl_ref = node_text(impl_node).strip() if impl_node is not None else ""
        if impl_ref:
            declaration_program_def = program_defs_by_name.get(impl_ref)
            if declaration_program_def is not None:
                declaration_statements = list(iter_program_body_statements(program_def=declaration_program_def))

        collect_program_body_diagnostics(
            program_def=program_def,
            declaration_statements=declaration_statements,
            classes_by_fqn=classes_by_fqn,
            experience_lookup=experience_lookup,
            node_text=node_text_fn,
            suggest=suggest_fn,
            add=add_fn,
        )

    if program_defs:
        collect_program_param_type_diagnostics(
            program_defs=program_defs,
            common_primitive_tokens=common_primitive_tokens,
            scope=scope,
            class_candidates=class_candidates,
            enum_candidates=enum_candidates,
            node_text=node_text_fn,
            suggest=suggest_fn,
            add=add_fn,
        )

    return diagnostics

