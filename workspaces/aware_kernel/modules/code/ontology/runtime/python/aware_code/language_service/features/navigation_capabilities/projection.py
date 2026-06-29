from __future__ import annotations

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code.language_service.features.navigation_capabilities.contracts import (
    AttributeDefinitionTargetResolver,
    ClassDefinitionTargetResolver,
    FunctionDefinitionTargetResolver,
    SymbolTargetResolver,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_projection_view_definition_targets_by_symbol(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    symbol: str,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []

    token = (symbol or "").strip()
    if "." not in token:
        return []
    projection_ref, view_ref = token.split(".", 1)
    projection_ref = projection_ref.strip()
    view_ref = view_ref.strip()
    if not projection_ref or not view_ref:
        return []

    local_pkg: str | None = None
    code = snapshot.codes_by_uri.get(uri)
    if code is not None:
        ns = snapshot.namespace_by_code_id.get(code.id)
        local_pkg = ns.package if ns is not None else None

    candidates: list[DefinitionTarget] = []
    preferred: list[DefinitionTarget] = []
    for other_uri, other_code in snapshot.codes_by_uri.items():
        ns = snapshot.namespace_by_code_id.get(other_code.id)
        other_pkg = ns.package if ns is not None else None

        for section in other_code.code_sections:
            if section.type != CodeSectionType.projection:
                continue
            proj = section.code_section_projection
            if proj is None:
                continue

            proj_symbol = (proj.name or "").strip()
            proj_name = (proj.projection_name or "").strip()
            if projection_ref not in {proj_symbol, proj_name}:
                continue

            for view in proj.projection_views or []:
                key = (view.key or "").strip()
                if not key:
                    continue
                if key != view_ref and key != token and token != f"{projection_ref}.{key}":
                    continue
                seg = view.key_segment
                if seg.byte_start is None or seg.byte_end is None:
                    continue
                target = DefinitionTarget(
                    uri=other_uri,
                    range=ByteRange(start=seg.byte_start, end=seg.byte_end),
                )
                candidates.append(target)
                if local_pkg is not None and other_pkg == local_pkg:
                    preferred.append(target)
    return preferred or candidates


def collect_projection_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    class_definition_target: ClassDefinitionTargetResolver,
    attribute_definition_target: AttributeDefinitionTargetResolver,
    function_definition_target: FunctionDefinitionTargetResolver,
    projection_targets_by_symbol: SymbolTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if not document_bytes or b"projection" not in document_bytes:
        return []

    code = snapshot.codes_by_uri.get(uri)
    if code is None:
        return []
    scope = snapshot.fqn_resolver.scope_for_code_id(code.id)

    cursor = byte_offset
    if cursor < 0:
        cursor = 0
    if cursor >= len(document_bytes):
        cursor = max(0, len(document_bytes) - 1)

    def _strip_string_literal(value: str) -> str:
        raw = (value or "").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            return raw[1:-1]
        return raw

    def _projection_definition_targets_for_symbol(
        symbol: str,
    ) -> list[DefinitionTarget]:
        if not symbol:
            return []
        try:
            return projection_targets_by_symbol(uri=uri, symbol=symbol)
        except Exception:
            return []

    # Use code sections for position lookups so the language-service stays tree-sitter free.
    for section in code.code_sections:
        if section.type != CodeSectionType.projection:
            continue
        proj = section.code_section_projection
        if proj is None:
            continue

        root_seg = proj.root_type_segment
        if (
            root_seg is not None
            and root_seg.byte_start is not None
            and root_seg.byte_end is not None
            and root_seg.byte_start <= cursor < root_seg.byte_end
        ):
            type_ref = (proj.root_type_ref or "").strip()
            if not type_ref:
                return []
            resolved = scope.try_resolve_class_with_fqn(type_ref)
            if resolved is None:
                return []
            _fqn, class_cfg = resolved
            target = class_definition_target(class_cfg)
            return [target] if target is not None else []

        for edge in proj.projection_edges or []:
            type_seg = edge.type_segment
            if (
                type_seg.byte_start is not None
                and type_seg.byte_end is not None
                and type_seg.byte_start <= cursor < type_seg.byte_end
            ):
                type_ref = (edge.type_ref or "").strip()
                if not type_ref:
                    return []
                resolved = scope.try_resolve_class_with_fqn(type_ref)
                if resolved is None:
                    return []
                _fqn, class_cfg = resolved
                target = class_definition_target(class_cfg)
                return [target] if target is not None else []

            member_seg = edge.member_segment
            if (
                member_seg.byte_start is not None
                and member_seg.byte_end is not None
                and member_seg.byte_start <= cursor < member_seg.byte_end
            ):
                type_ref = (edge.type_ref or "").strip()
                member = (edge.member or "").strip()
                if not type_ref or not member:
                    return []
                resolved = scope.try_resolve_class_with_fqn(type_ref)
                if resolved is None:
                    return []
                _fqn, class_cfg = resolved
                cls = class_cfg.code_section_class
                if cls is None:
                    return []
                attr = next(
                    (a for a in cls.code_section_attributes if a.name == member),
                    None,
                )
                if attr is not None:
                    target = attribute_definition_target(attr)
                    return [target] if target is not None else []
                fn = next(
                    (f for f in cls.code_section_functions if f.name == member),
                    None,
                )
                if fn is not None:
                    target = function_definition_target(fn)
                    return [target] if target is not None else []
                return []

            target_seg = edge.target_segment
            if (
                target_seg is not None
                and target_seg.byte_start is not None
                and target_seg.byte_end is not None
                and target_seg.byte_start <= cursor < target_seg.byte_end
            ):
                raw = document_bytes[target_seg.byte_start:target_seg.byte_end].decode("utf-8", errors="replace")
                raw = _strip_string_literal(raw)
                proj_targets = _projection_definition_targets_for_symbol(raw)
                if proj_targets:
                    return proj_targets
                resolved = scope.try_resolve_class_with_fqn(raw)
                if resolved is not None:
                    _fqn, class_cfg = resolved
                    target = class_definition_target(class_cfg)
                    return [target] if target is not None else []
                return []

    return []


def collect_projection_definition_targets_by_symbol(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    symbol: str,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []

    def _strip_string_literal(value: str) -> str:
        raw = (value or "").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            return raw[1:-1]
        return raw

    # Parse qualified projection references like `aware_identity.Identity`.
    token = _strip_string_literal(symbol)
    known_packages: set[str] = set()
    for _other_uri, other_code in snapshot.codes_by_uri.items():
        ns = snapshot.namespace_by_code_id.get(other_code.id)
        if ns is not None and ns.package:
            known_packages.add(ns.package)

    qualifier_pkg: str | None = None
    symbol_ref = token
    if "." in token:
        prefix, last = token.rsplit(".", 1)
        prefix = (prefix or "").strip()
        last = (last or "").strip()
        if prefix in known_packages:
            qualifier_pkg = prefix or None
        # Context-aware fallback for projection-target tokens:
        # unknown dotted prefixes (for example `schema.ClassName`) are treated
        # as projection symbol references using the second segment.
        symbol_ref = last
    symbol_ref = (symbol_ref or "").strip()

    # Prefer matches in the current file's package when the reference is unqualified.
    local_pkg: str | None = None
    code = snapshot.codes_by_uri.get(uri)
    if code is not None:
        ns = snapshot.namespace_by_code_id.get(code.id)
        local_pkg = ns.package if ns is not None else None

    candidates: list[DefinitionTarget] = []
    preferred: list[DefinitionTarget] = []

    for other_uri, other_code in snapshot.codes_by_uri.items():
        ns = snapshot.namespace_by_code_id.get(other_code.id)
        other_pkg = ns.package if ns is not None else None
        if qualifier_pkg is not None and qualifier_pkg and other_pkg != qualifier_pkg:
            continue

        for section in other_code.code_sections:
            if section.type != CodeSectionType.projection:
                continue
            proj = section.code_section_projection
            if proj is None:
                continue

            # Match by symbol name (preferred) and by canonical projection_name (fallback).
            symbol_name = (proj.name or "").strip()
            projection_name = (proj.projection_name or "").strip()

            hit = False
            if symbol_ref and symbol_name == symbol_ref:
                hit = True
            elif token and projection_name == token:
                hit = True
            elif projection_name and projection_name == symbol_ref:
                # Support package-qualified projection ids like `aware_identity.identity`
                # and class-style projection target refs like `schema.ClassName`.
                hit = True

            if not hit:
                continue

            seg = proj.name_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue

            target = DefinitionTarget(
                uri=other_uri,
                range=ByteRange(start=seg.byte_start, end=seg.byte_end),
            )
            candidates.append(target)
            if qualifier_pkg is None and local_pkg is not None and other_pkg == local_pkg:
                preferred.append(target)

    return preferred or candidates
