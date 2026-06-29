from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from tree_sitter import Node

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.projection.code_section_projection import CodeSectionProjection

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.position import ByteRange

from aware_workspace.compiler.workspace import WorkspaceSnapshot

from .contracts import DiagnosticDataValue


class ProjectionAddDiagnostic(Protocol):
    def __call__(
        self,
        *,
        rng: ByteRange,
        message: str,
        code: str | None = None,
        data: Mapping[str, DiagnosticDataValue] | None = None,
        severity: int = 1,
    ) -> None: ...


class ProjectionSuggestFn(Protocol):
    def __call__(self, value: str, options: list[str]) -> list[str]: ...


@dataclass(frozen=True)
class ProjectionLookup:
    local_pkg: str | None
    projection_candidates: list[str]
    projection_index: list[tuple[str, str | None, CodeSectionProjection]]
    known_packages: set[str]


def strip_string_literal(value: str) -> str:
    raw = (value or "").strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def build_projection_lookup(*, snapshot: WorkspaceSnapshot, code: Code) -> ProjectionLookup:
    local_pkg: str | None = None
    try:
        ns_local = snapshot.namespace_by_code_id.get(code.id)
        local_pkg = ns_local.package if ns_local is not None else None
    except Exception:
        local_pkg = None

    projection_candidates_set: set[str] = set()
    projection_index: list[tuple[str, str | None, CodeSectionProjection]] = []
    known_packages: set[str] = set()
    try:
        for other_uri, other_code in snapshot.codes_by_uri.items():
            ns_other = snapshot.namespace_by_code_id.get(other_code.id)
            other_pkg = ns_other.package if ns_other is not None else None
            if other_pkg:
                known_packages.add(other_pkg)
            for other_section in other_code.code_sections:
                if other_section.type != CodeSectionType.projection:
                    continue
                other_proj = other_section.code_section_projection
                if other_proj is None:
                    continue
                projection_index.append((other_uri, other_pkg, other_proj))
                sym = (other_proj.name or "").strip()
                if sym:
                    projection_candidates_set.add(sym)
                    if other_pkg:
                        projection_candidates_set.add(f"{other_pkg}.{sym}")
                proj_name = (other_proj.projection_name or "").strip()
                if proj_name:
                    projection_candidates_set.add(proj_name)
                    if other_pkg:
                        projection_candidates_set.add(f"{other_pkg}.{proj_name}")
    except Exception:
        projection_index = []
        projection_candidates_set = set()
        known_packages = set()

    return ProjectionLookup(
        local_pkg=local_pkg,
        projection_candidates=sorted(projection_candidates_set),
        projection_index=projection_index,
        known_packages=known_packages,
    )


def match_projection_symbol(
    *,
    symbol: str,
    lookup: ProjectionLookup,
) -> list[tuple[str, str | None, CodeSectionProjection]]:
    token = strip_string_literal(symbol)
    if not token:
        return []

    qualifier_pkg: str | None = None
    symbol_ref = token
    if "." in token:
        prefix, last = token.rsplit(".", 1)
        prefix = (prefix or "").strip()
        last = (last or "").strip()
        if prefix in lookup.known_packages:
            qualifier_pkg = prefix
        # Context-aware fallback for projection targets:
        # in projection-target position, `schema.ClassName` should resolve by
        # projection symbol/id (`ClassName`) when `schema` is not a package.
        symbol_ref = last

    symbol_ref = (symbol_ref or "").strip()

    hits: list[tuple[str, str | None, CodeSectionProjection]] = []
    for other_uri, other_pkg, other_proj in lookup.projection_index:
        if qualifier_pkg is not None and other_pkg != qualifier_pkg:
            continue

        symbol_name = (other_proj.name or "").strip()
        projection_name = (other_proj.projection_name or "").strip()

        if symbol_ref and symbol_name == symbol_ref:
            hits.append((other_uri, other_pkg, other_proj))
            continue
        if token and projection_name == token:
            hits.append((other_uri, other_pkg, other_proj))
            continue
        if projection_name and projection_name == symbol_ref:
            hits.append((other_uri, other_pkg, other_proj))
            continue

    return hits


def collect_projection_diagnostics(
    *,
    code: Code,
    scope: FqnScope,
    document_bytes: bytes,
    projection_root: Node | None,
    class_candidates: list[str],
    lookup: ProjectionLookup,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
) -> None:
    if b"projection" not in document_bytes:
        return

    _add = add
    _suggest = suggest
    doc_bytes = document_bytes

    for section in code.code_sections:
        if section.type != CodeSectionType.projection:
            continue
        proj = section.code_section_projection
        if proj is None:
            continue

        root_seg = proj.root_type_segment
        root_ref = (proj.root_type_ref or "").strip()
        if (
            root_seg is not None
            and root_ref
            and root_seg.byte_start is not None
            and root_seg.byte_end is not None
        ):
            if scope.try_resolve_class_with_fqn(root_ref) is None:
                _add(
                    rng=ByteRange(start=root_seg.byte_start, end=root_seg.byte_end),
                    message=f"Class not found for projection root: {root_ref}",
                    code="aware.projection.class_not_found",
                    data={"suggestions": _suggest(root_ref, class_candidates)},
                )

        for edge in proj.projection_edges or []:
            type_ref = (edge.type_ref or "").strip()
            member = (edge.member or "").strip()

            type_seg = edge.type_segment
            member_seg = edge.member_segment

            if type_ref and type_seg.byte_start is not None and type_seg.byte_end is not None:
                resolved = scope.try_resolve_class_with_fqn(type_ref)
                if resolved is None:
                    _add(
                        rng=ByteRange(start=type_seg.byte_start, end=type_seg.byte_end),
                        message=f"Class not found for projection edge: {type_ref}",
                        code="aware.projection.class_not_found",
                        data={"suggestions": _suggest(type_ref, class_candidates)},
                    )
                    continue

                if member and member_seg.byte_start is not None and member_seg.byte_end is not None:
                    _fqn, class_cfg = resolved
                    cls = class_cfg.code_section_class
                    if cls is None:
                        continue
                    attr_names = [a.name for a in cls.code_section_attributes]
                    fn_names = [f.name for f in cls.code_section_functions]
                    if member not in attr_names and member not in fn_names:
                        _add(
                            rng=ByteRange(
                                start=member_seg.byte_start,
                                end=member_seg.byte_end,
                            ),
                            message=f"Member {member!r} not found on class {class_cfg.name} (projection edge)",
                            code="aware.projection.member_not_found",
                            data={
                                "suggestions": _suggest(
                                    member,
                                    attr_names + fn_names,
                                )
                            },
                        )

                target_seg = edge.target_segment
                if (
                    target_seg is not None
                    and target_seg.byte_start is not None
                    and target_seg.byte_end is not None
                    and target_seg.byte_end > target_seg.byte_start
                ):
                    raw_target = doc_bytes[target_seg.byte_start:target_seg.byte_end].decode(
                        "utf-8", errors="replace"
                    )
                    target = strip_string_literal(raw_target)
                    if target:
                        matches = match_projection_symbol(symbol=target, lookup=lookup)
                        if not matches:
                            resolved_target_cls = scope.try_resolve_class_with_fqn(target)
                            if resolved_target_cls is not None:
                                _add(
                                    rng=ByteRange(
                                        start=target_seg.byte_start,
                                        end=target_seg.byte_end,
                                    ),
                                    message=(
                                        "Projection portal target must reference a projection "
                                        f"(not a class): {target}"
                                    ),
                                    code="aware.projection.target_is_class",
                                )
                            else:
                                _add(
                                    rng=ByteRange(
                                        start=target_seg.byte_start,
                                        end=target_seg.byte_end,
                                    ),
                                    message=f"Projection not found for portal target: {target}",
                                    code="aware.projection.target_not_found",
                                    data={"suggestions": _suggest(target, lookup.projection_candidates)},
                                )
                        else:
                            # Warn when an unqualified target matches multiple external packages.
                            pkgs = {pkg for _uri, pkg, _proj in matches if isinstance(pkg, str) and pkg}
                            if "." not in target and lookup.local_pkg is not None and lookup.local_pkg in pkgs:
                                pkgs = {lookup.local_pkg}
                            if len(pkgs) > 1:
                                _add(
                                    rng=ByteRange(
                                        start=target_seg.byte_start,
                                        end=target_seg.byte_end,
                                    ),
                                    message=(
                                        f"Ambiguous projection target {target!r}; "
                                        "qualify with a package (e.g. `aware_identity.Identity`)."
                                    ),
                                    code="aware.projection.target_ambiguous",
                                    data={"matches": sorted(pkgs)},
                                    severity=2,
                                )

        # View validation (v1+ contract).
        seen_view_keys: set[str] = set()
        projection_default_view_ranges: list[ByteRange] = []
        for view in proj.projection_views or []:
            view_key = (view.key or "").strip()
            seg = view.key_segment
            if not view_key or seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            rng = ByteRange(start=seg.byte_start, end=seg.byte_end)

            if view_key in seen_view_keys:
                _add(
                    rng=rng,
                    message=(
                        f"Duplicate observable key {view_key!r} in projection "
                        f"{(proj.projection_name or proj.name)!r}"
                    ),
                    code="aware.projection.view_duplicate",
                )
            else:
                seen_view_keys.add(view_key)

            if bool(view.is_default):
                projection_default_view_ranges.append(rng)

        if len(projection_default_view_ranges) > 1:
            for rng in projection_default_view_ranges:
                _add(
                    rng=rng,
                    message=(
                        f"Projection {(proj.projection_name or proj.name)!r} defines multiple "
                        "default observables; mark exactly one observable as `default`."
                    ),
                    code="aware.projection.view_multiple_defaults",
                )

    # Legacy alias diagnostic: structural `view`/`observation` are
    # accepted temporarily, but canonical projection contracts should
    # use `observable`.
    if projection_root is None:
        return

    projection_alias_queue: list[Node] = [projection_root]
    while projection_alias_queue:
        node = projection_alias_queue.pop()
        projection_alias_queue.extend(node.children)
        if node.type not in {"projection_view_group", "projection_view_def"}:
            continue
        keyword_node = node.child_by_field_name("keyword")
        if keyword_node is None or keyword_node.text is None:
            continue
        keyword = keyword_node.text.decode("utf-8", errors="replace").strip()
        if keyword not in {"view", "observation"}:
            continue
        if keyword_node.end_byte <= keyword_node.start_byte:
            continue
        _add(
            rng=ByteRange(
                start=keyword_node.start_byte,
                end=keyword_node.end_byte,
            ),
            message="Projection keyword is legacy; use `observable` for structural attention contracts.",
            code="aware.projection.view_legacy_alias",
            severity=2,
            data={"replacement": "observable"},
        )
