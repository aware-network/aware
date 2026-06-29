from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.code.code import Code
from typing_extensions import override

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_code.language_service.document import DocumentContext
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.resolution import ResolutionMixin
from aware_code.language_service.position import ByteRange, Utf16Position
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.text import (
    extract_identifier_token_span,
    is_valid_identifier,
    iter_annotation_path_ranges,
    iter_identifier_tokens_in_range,
    name_part_range_from_token_bytes,
)
from aware_code.language_service.types import DefinitionTarget, ResolvedSymbol

from aware_workspace.compiler.workspace import WorkspaceSnapshot


class _LspPosition(TypedDict):
    line: int
    character: int


class _LspRange(TypedDict):
    start: _LspPosition
    end: _LspPosition


class _LspTextEdit(TypedDict):
    range: _LspRange
    newText: str


class _LspWorkspaceEdit(TypedDict):
    changes: dict[str, list[_LspTextEdit]]


@dataclass(frozen=True, slots=True)
class _GraphRefParts:
    node: str
    identity: str
    node_range: ByteRange
    identity_range: ByteRange


@dataclass(frozen=True, slots=True)
class _GraphRenameSymbol:
    kind: str
    experience: str
    node: str | None
    identity: str | None
    name_range: ByteRange
    name: str


class RefactorMixin(ServiceMixinBase, ResolutionMixin):
    _snapshot: WorkspaceSnapshot | None

    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @override
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    @staticmethod
    def _cursor_in_range(*, byte_offset: int, start: int, end: int) -> bool:
        if end <= start:
            return False
        cursor = int(byte_offset)
        if cursor < start:
            return False
        if cursor > end:
            return False
        if cursor == end and cursor > start:
            cursor -= 1
        return start <= cursor < end

    @staticmethod
    def _node_text(node) -> str:
        if node is None or node.text is None:
            return ""
        return node.text.decode("utf-8", errors="replace")

    def references(
        self,
        *,
        uri: str,
        position: Utf16Position,
        document_text: str,
        include_declaration: bool,
    ) -> list[DefinitionTarget]:
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return []

        ctx = self._document_context(uri=uri, document_text=document_text)
        mapper = ctx.mapper
        offset = mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        symbol = self._resolve_symbol_at_byte_offset(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            document_text=document_text,
        )
        graph_symbol = self._resolve_graph_symbol_at_byte_offset(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
        )
        if graph_symbol is not None:
            return self._find_graph_references(
                uri=uri,
                symbol=graph_symbol,
                include_declaration=include_declaration,
            )
        if symbol is None:
            return []

        return self._find_references(symbol=symbol, include_declaration=include_declaration)

    def prepare_rename(self, *, uri: str, position: Utf16Position, document_text: str) -> tuple[ByteRange, str] | None:
        """Return a (byte_range, placeholder) pair for the rename target at the cursor."""
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return None

        ctx = self._document_context(uri=uri, document_text=document_text)
        mapper = ctx.mapper
        offset = mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        def_rng, def_name = self._definition_name_range_at(uri=uri, byte_offset=offset)
        if def_rng is not None and def_name is not None:
            return def_rng, def_name

        type_seg = self._find_type_segment_at(uri=uri, byte_offset=offset)
        if type_seg is not None:
            token = extract_identifier_token_span(
                document_bytes=doc_bytes,
                byte_offset=offset,
                segment_start=type_seg.start,
                segment_end=type_seg.end,
            )
            if token is not None:
                _, token_bytes, token_rng = token
                name_rng, placeholder = name_part_range_from_token_bytes(token_rng, token_bytes)
                return name_rng, placeholder

        ann_seg = self._find_annotation_path_segment_at(byte_offset=offset, document_bytes=doc_bytes)
        if ann_seg is not None:
            token = extract_identifier_token_span(
                document_bytes=doc_bytes,
                byte_offset=offset,
                segment_start=ann_seg.start,
                segment_end=ann_seg.end,
            )
            if token is not None:
                _, token_bytes, token_rng = token
                name_rng, placeholder = name_part_range_from_token_bytes(token_rng, token_bytes)
                return name_rng, placeholder

        graph_symbol = self._resolve_graph_symbol_at_byte_offset(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
        )
        if graph_symbol is not None:
            return graph_symbol.name_range, graph_symbol.name

        return None

    def rename(
        self,
        *,
        uri: str,
        position: Utf16Position,
        document_text: str,
        new_name: str,
    ) -> _LspWorkspaceEdit | None:
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return None

        candidate = (new_name or "").strip()
        if not is_valid_identifier(candidate):
            raise ValueError(f"Invalid identifier: {new_name!r}")

        ctx = self._document_context(uri=uri, document_text=document_text)
        mapper = ctx.mapper
        offset = mapper.position_to_byte_offset(position)
        doc_bytes = ctx.document_bytes

        symbol = self._resolve_symbol_at_byte_offset(
            uri=uri,
            byte_offset=offset,
            document_bytes=doc_bytes,
            document_text=document_text,
        )
        changes: dict[str, list[_LspTextEdit]] = {}
        if symbol is not None:
            edit_rows = self._find_rename_ranges(symbol=symbol)
        else:
            graph_symbol = self._resolve_graph_symbol_at_byte_offset(
                uri=uri,
                byte_offset=offset,
                document_bytes=doc_bytes,
            )
            if graph_symbol is None:
                return None
            edit_rows = self._find_graph_rename_ranges(
                uri=uri,
                symbol=graph_symbol,
            )

        for occ_uri, occ_text, replace_ranges in edit_rows:
            mapper = self._document_context(uri=occ_uri, document_text=occ_text).mapper
            edits: list[_LspTextEdit] = []
            for rng in replace_ranges:
                start = mapper.byte_offset_to_position(rng.start)
                end = mapper.byte_offset_to_position(rng.end)
                edits.append(
                    {
                        "range": {
                            "start": {"line": start.line, "character": start.character},
                            "end": {"line": end.line, "character": end.character},
                        },
                        "newText": candidate,
                    }
                )
            if edits:
                changes[occ_uri] = edits

        if not changes:
            return None
        return {"changes": changes}

    def _find_references(self, *, symbol: ResolvedSymbol, include_declaration: bool) -> list[DefinitionTarget]:
        if self._snapshot is None:
            return []

        out: list[DefinitionTarget] = []
        seen: set[tuple[str, int, int]] = set()

        for doc_uri, code in self._snapshot.codes_by_uri.items():
            text = self._snapshot.text_by_uri.get(doc_uri)
            if text is None:
                continue
            doc_bytes = self._document_context(uri=doc_uri, document_text=text).document_bytes
            scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)

            if include_declaration:
                for section in code.code_sections:
                    if symbol.kind == "class" and section.type == CodeSectionType.class_:
                        cls = section.code_section_class
                        if cls is None:
                            continue
                        resolved = scope.try_resolve_class_with_fqn(cls.name)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                        seg = cls.name_segment
                        if (
                            seg.byte_start is None
                            or seg.byte_end is None
                            or seg.byte_end <= seg.byte_start
                        ):
                            continue
                        key = (doc_uri, seg.byte_start, seg.byte_end)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(
                            DefinitionTarget(
                                uri=doc_uri,
                                range=ByteRange(start=seg.byte_start, end=seg.byte_end),
                            )
                        )

                    if symbol.kind == "enum" and section.type == CodeSectionType.enum:
                        enum = section.code_section_enum
                        if enum is None:
                            continue
                        resolved = scope.try_resolve_enum_with_fqn(enum.name)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                        seg = enum.name_segment
                        if (
                            seg.byte_start is None
                            or seg.byte_end is None
                            or seg.byte_end <= seg.byte_start
                        ):
                            continue
                        key = (doc_uri, seg.byte_start, seg.byte_end)
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(
                            DefinitionTarget(
                                uri=doc_uri,
                                range=ByteRange(start=seg.byte_start, end=seg.byte_end),
                            )
                        )

            for seg_rng in self._iter_type_like_segments(code):
                for (
                    token_str,
                    _token_bytes,
                    token_rng,
                ) in iter_identifier_tokens_in_range(
                    document_bytes=doc_bytes,
                    segment_start=seg_rng.start,
                    segment_end=seg_rng.end,
                ):
                    if symbol.kind == "class":
                        resolved = scope.try_resolve_class_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    else:
                        resolved = scope.try_resolve_enum_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    key = (doc_uri, token_rng.start, token_rng.end)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(DefinitionTarget(uri=doc_uri, range=token_rng))

            for ann_rng in iter_annotation_path_ranges(doc_bytes):
                for (
                    token_str,
                    _token_bytes,
                    token_rng,
                ) in iter_identifier_tokens_in_range(
                    document_bytes=doc_bytes,
                    segment_start=ann_rng.start,
                    segment_end=ann_rng.end,
                ):
                    if symbol.kind == "class":
                        resolved = scope.try_resolve_class_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    else:
                        resolved = scope.try_resolve_enum_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    key = (doc_uri, token_rng.start, token_rng.end)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(DefinitionTarget(uri=doc_uri, range=token_rng))

        return out

    def _find_rename_ranges(self, *, symbol: ResolvedSymbol) -> Iterable[tuple[str, str, list[ByteRange]]]:
        if self._snapshot is None:
            return []

        results: list[tuple[str, str, list[ByteRange]]] = []
        for doc_uri, code in self._snapshot.codes_by_uri.items():
            text = self._snapshot.text_by_uri.get(doc_uri)
            if text is None:
                continue
            doc_bytes = self._document_context(uri=doc_uri, document_text=text).document_bytes
            scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)

            replace_ranges: set[tuple[int, int]] = set()

            for section in code.code_sections:
                if symbol.kind == "class" and section.type == CodeSectionType.class_:
                    cls = section.code_section_class
                    if cls is None:
                        continue
                    resolved = scope.try_resolve_class_with_fqn(cls.name)
                    if resolved is None or resolved[0] != symbol.fqn:
                        continue
                    seg = cls.name_segment
                    if seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                        continue
                    replace_ranges.add((seg.byte_start, seg.byte_end))
                if symbol.kind == "enum" and section.type == CodeSectionType.enum:
                    enum = section.code_section_enum
                    if enum is None:
                        continue
                    resolved = scope.try_resolve_enum_with_fqn(enum.name)
                    if resolved is None or resolved[0] != symbol.fqn:
                        continue
                    seg = enum.name_segment
                    if seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                        continue
                    replace_ranges.add((seg.byte_start, seg.byte_end))

            for seg_rng in self._iter_type_like_segments(code):
                for (
                    token_str,
                    token_bytes,
                    token_rng,
                ) in iter_identifier_tokens_in_range(
                    document_bytes=doc_bytes,
                    segment_start=seg_rng.start,
                    segment_end=seg_rng.end,
                ):
                    if symbol.kind == "class":
                        resolved = scope.try_resolve_class_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    else:
                        resolved = scope.try_resolve_enum_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    name_rng, _ = name_part_range_from_token_bytes(token_rng, token_bytes)
                    replace_ranges.add((name_rng.start, name_rng.end))

            for ann_rng in iter_annotation_path_ranges(doc_bytes):
                for (
                    token_str,
                    token_bytes,
                    token_rng,
                ) in iter_identifier_tokens_in_range(
                    document_bytes=doc_bytes,
                    segment_start=ann_rng.start,
                    segment_end=ann_rng.end,
                ):
                    if symbol.kind == "class":
                        resolved = scope.try_resolve_class_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    else:
                        resolved = scope.try_resolve_enum_with_fqn(token_str)
                        if resolved is None or resolved[0] != symbol.fqn:
                            continue
                    name_rng, _ = name_part_range_from_token_bytes(token_rng, token_bytes)
                    replace_ranges.add((name_rng.start, name_rng.end))

            if replace_ranges:
                ranges = [ByteRange(start=s, end=e) for s, e in sorted(replace_ranges)]
                results.append((doc_uri, text, ranges))

        return results

    def _iter_type_like_segments(self, code: Code) -> Iterable[ByteRange]:
        for section in code.code_sections:
            if section.type == CodeSectionType.attribute:
                attr = section.code_section_attribute
                if attr is None:
                    continue
                seg = attr.type_segment
                if seg is None or seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                    continue
                yield ByteRange(start=seg.byte_start, end=seg.byte_end)
                continue

            if section.type == CodeSectionType.class_:
                cls = section.code_section_class
                if cls is None:
                    continue
                for base in cls.code_section_class_bases:
                    seg = base.segment
                    if seg is None or seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                        continue
                    yield ByteRange(start=seg.byte_start, end=seg.byte_end)
                continue

            if section.type == CodeSectionType.function:
                fn = section.code_section_function
                if fn is None:
                    continue
                seg = fn.return_type_segment
                if seg is None or seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                    continue
                yield ByteRange(start=seg.byte_start, end=seg.byte_end)

    def _resolve_graph_symbol_at_byte_offset(
        self,
        *,
        uri: str,
        byte_offset: int,
        document_bytes: bytes,
    ) -> _GraphRenameSymbol | None:
        try:
            root = parse_tree(document_bytes=document_bytes)
        except Exception:
            return None
        cursor = max(int(byte_offset), 0)
        queue: list = [root]
        while queue:
            node = queue.pop()
            queue.extend(node.named_children)
            if node.type == "experience_def":
                exp_name_node = node.child_by_field_name("name")
                exp_name = self._node_text(exp_name_node).strip()
                if (
                    exp_name_node is not None
                    and exp_name
                    and self._cursor_in_range(
                        byte_offset=cursor,
                        start=exp_name_node.start_byte,
                        end=exp_name_node.end_byte,
                    )
                ):
                    return _GraphRenameSymbol(
                        kind="experience",
                        experience=exp_name,
                        node=None,
                        identity=None,
                        name_range=ByteRange(
                            start=exp_name_node.start_byte,
                            end=exp_name_node.end_byte,
                        ),
                        name=exp_name,
                    )
                for exp_item in node.named_children:
                    if exp_item.type != "experience_item":
                        continue
                    for member in exp_item.named_children:
                        if member.type != "experience_node_def":
                            continue
                        node_name_node = member.child_by_field_name("name")
                        node_name = self._node_text(node_name_node).strip()
                        if (
                            node_name_node is not None
                            and exp_name
                            and node_name
                            and self._cursor_in_range(
                                byte_offset=cursor,
                                start=node_name_node.start_byte,
                                end=node_name_node.end_byte,
                            )
                        ):
                            return _GraphRenameSymbol(
                                kind="node",
                                experience=exp_name,
                                node=node_name,
                                identity=None,
                                name_range=ByteRange(
                                    start=node_name_node.start_byte,
                                    end=node_name_node.end_byte,
                                ),
                                name=node_name,
                            )
                        for node_member in member.named_children:
                            if node_member.type != "experience_node_identity_def":
                                continue
                            key_node = node_member.child_by_field_name("key_name")
                            key_name = self._node_text(key_node).strip()
                            if (
                                key_node is None
                                or not exp_name
                                or not node_name
                                or not key_name
                                or not self._cursor_in_range(
                                    byte_offset=cursor,
                                    start=key_node.start_byte,
                                    end=key_node.end_byte,
                                )
                            ):
                                continue
                            return _GraphRenameSymbol(
                                kind="identity",
                                experience=exp_name,
                                node=node_name,
                                identity=key_name,
                                name_range=ByteRange(
                                    start=key_node.start_byte,
                                    end=key_node.end_byte,
                                ),
                                name=key_name,
                            )
            if node.type != "graph_def":
                continue
            experience_node = node.child_by_field_name("experience")
            experience_name = self._node_text(experience_node).strip()
            if (
                experience_node is not None
                and experience_name
                and self._cursor_in_range(
                    byte_offset=cursor,
                    start=experience_node.start_byte,
                    end=experience_node.end_byte,
                )
            ):
                return _GraphRenameSymbol(
                    kind="experience",
                    experience=experience_name,
                    node=None,
                    identity=None,
                    name_range=ByteRange(start=experience_node.start_byte, end=experience_node.end_byte),
                    name=experience_name,
                )
            for graph_item in node.named_children:
                if graph_item.type != "graph_item":
                    continue
                for stmt in graph_item.named_children:
                    if stmt.type == "graph_root_stmt":
                        ref_node = stmt.child_by_field_name("ref")
                        parts = self._split_graph_ref_parts(
                            ref_node=ref_node,
                            document_bytes=document_bytes,
                        )
                        if parts is None:
                            continue
                        if self._cursor_in_range(
                            byte_offset=cursor,
                            start=parts.node_range.start,
                            end=parts.node_range.end,
                        ):
                            return _GraphRenameSymbol(
                                kind="node",
                                experience=experience_name,
                                node=parts.node,
                                identity=None,
                                name_range=parts.node_range,
                                name=parts.node,
                            )
                        if self._cursor_in_range(
                            byte_offset=cursor,
                            start=parts.identity_range.start,
                            end=parts.identity_range.end,
                        ):
                            return _GraphRenameSymbol(
                                kind="identity",
                                experience=experience_name,
                                node=parts.node,
                                identity=parts.identity,
                                name_range=parts.identity_range,
                                name=parts.identity,
                            )
                    if stmt.type != "graph_edge_stmt":
                        continue
                    for field in ("parent", "child"):
                        ref_node = stmt.child_by_field_name(field)
                        parts = self._split_graph_ref_parts(
                            ref_node=ref_node,
                            document_bytes=document_bytes,
                        )
                        if parts is None:
                            continue
                        if self._cursor_in_range(
                            byte_offset=cursor,
                            start=parts.node_range.start,
                            end=parts.node_range.end,
                        ):
                            return _GraphRenameSymbol(
                                kind="node",
                                experience=experience_name,
                                node=parts.node,
                                identity=None,
                                name_range=parts.node_range,
                                name=parts.node,
                            )
                        if self._cursor_in_range(
                            byte_offset=cursor,
                            start=parts.identity_range.start,
                            end=parts.identity_range.end,
                        ):
                            return _GraphRenameSymbol(
                                kind="identity",
                                experience=experience_name,
                                node=parts.node,
                                identity=parts.identity,
                                name_range=parts.identity_range,
                                name=parts.identity,
                            )
        return None

    def _split_graph_ref_parts(
        self,
        *,
        ref_node,
        document_bytes: bytes,
    ) -> _GraphRefParts | None:
        if ref_node is None:
            return None
        if ref_node.end_byte <= ref_node.start_byte:
            return None
        raw = document_bytes[ref_node.start_byte:ref_node.end_byte].decode("utf-8", errors="replace").strip()
        if "." not in raw:
            return None
        node_name, identity_name = raw.split(".", 1)
        node_name = node_name.strip()
        identity_name = identity_name.strip()
        if not node_name or not identity_name:
            return None
        dot_index = raw.find(".")
        node_range = ByteRange(start=ref_node.start_byte, end=ref_node.start_byte + dot_index)
        identity_range = ByteRange(start=ref_node.start_byte + dot_index + 1, end=ref_node.end_byte)
        return _GraphRefParts(
            node=node_name,
            identity=identity_name,
            node_range=node_range,
            identity_range=identity_range,
        )

    def _resolve_experience_toml_for_uri(self, *, uri: str) -> Path | None:
        try:
            uri_path = self._workspace.uri_to_path(uri)
        except Exception:
            return None
        for parent in [uri_path.parent, *uri_path.parents]:
            candidate = parent / "aware.experience.toml"
            if candidate.is_file():
                return candidate
        return None

    def _iter_experience_sources(self, *, uri: str) -> Iterable[tuple[str, str]]:
        if self._snapshot is None:
            return ()
        experience_toml = self._resolve_experience_toml_for_uri(uri=uri)
        if experience_toml is None:
            return ()
        try:
            workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
            snapshot = workspace.build_snapshot()
        except Exception:
            return ()
        rows: list[tuple[str, str]] = []
        for relpath in snapshot.source_files:
            source_path = (snapshot.package_root / relpath).resolve()
            if not source_path.is_file():
                continue
            source_uri = self._workspace.path_to_uri(source_path)
            text = self._snapshot.text_by_uri.get(source_uri)
            if text is None:
                try:
                    text = source_path.read_text(encoding="utf-8")
                except Exception:
                    continue
            rows.append((source_uri, text))
        return tuple(rows)

    def _find_graph_references(
        self,
        *,
        uri: str,
        symbol: _GraphRenameSymbol,
        include_declaration: bool,
    ) -> list[DefinitionTarget]:
        seen: set[tuple[str, int, int]] = set()
        out: list[DefinitionTarget] = []
        for source_uri, source_text in self._iter_experience_sources(uri=uri):
            doc_bytes = source_text.encode("utf-8")
            try:
                root = parse_tree(document_bytes=doc_bytes)
            except Exception:
                continue
            for child in root.named_children:
                if child.type == "experience_def":
                    exp_name_node = child.child_by_field_name("name")
                    exp_name = self._node_text(exp_name_node).strip()
                    if exp_name != symbol.experience:
                        continue
                    if include_declaration and symbol.kind == "experience" and exp_name_node is not None:
                        self._append_unique_target(
                            out=out,
                            seen=seen,
                            uri=source_uri,
                            start=exp_name_node.start_byte,
                            end=exp_name_node.end_byte,
                        )
                    for exp_item in child.named_children:
                        if exp_item.type != "experience_item":
                            continue
                        for member in exp_item.named_children:
                            if member.type != "experience_node_def":
                                continue
                            node_name_node = member.child_by_field_name("name")
                            node_name = self._node_text(node_name_node).strip()
                            if (
                                include_declaration
                                and symbol.kind == "node"
                                and node_name == (symbol.node or "")
                                and node_name_node is not None
                            ):
                                self._append_unique_target(
                                    out=out,
                                    seen=seen,
                                    uri=source_uri,
                                    start=node_name_node.start_byte,
                                    end=node_name_node.end_byte,
                                )
                            for node_member in member.named_children:
                                if node_member.type != "experience_node_identity_def":
                                    continue
                                key_node = node_member.child_by_field_name("key_name")
                                key_name = self._node_text(key_node).strip()
                                if (
                                    include_declaration
                                    and symbol.kind == "identity"
                                    and key_name == (symbol.identity or "")
                                    and key_node is not None
                                    and ((symbol.node is None) or node_name == symbol.node)
                                ):
                                    self._append_unique_target(
                                        out=out,
                                        seen=seen,
                                        uri=source_uri,
                                        start=key_node.start_byte,
                                        end=key_node.end_byte,
                                    )
                    continue
                if child.type != "graph_def":
                    continue
                experience_node = child.child_by_field_name("experience")
                experience_name = self._node_text(experience_node).strip()
                if symbol.kind == "experience" and experience_name == symbol.experience and experience_node is not None:
                    self._append_unique_target(
                        out=out,
                        seen=seen,
                        uri=source_uri,
                        start=experience_node.start_byte,
                        end=experience_node.end_byte,
                    )
                if experience_name != symbol.experience:
                    continue
                for graph_item in child.named_children:
                    if graph_item.type != "graph_item":
                        continue
                    for stmt in graph_item.named_children:
                        if stmt.type == "graph_root_stmt":
                            self._append_graph_ref_match(
                                out=out,
                                seen=seen,
                                source_uri=source_uri,
                                symbol=symbol,
                                ref_node=stmt.child_by_field_name("ref"),
                                document_bytes=doc_bytes,
                            )
                        if stmt.type == "graph_edge_stmt":
                            self._append_graph_ref_match(
                                out=out,
                                seen=seen,
                                source_uri=source_uri,
                                symbol=symbol,
                                ref_node=stmt.child_by_field_name("parent"),
                                document_bytes=doc_bytes,
                            )
                            self._append_graph_ref_match(
                                out=out,
                                seen=seen,
                                source_uri=source_uri,
                                symbol=symbol,
                                ref_node=stmt.child_by_field_name("child"),
                                document_bytes=doc_bytes,
                            )
        return out

    def _find_graph_rename_ranges(
        self,
        *,
        uri: str,
        symbol: _GraphRenameSymbol,
    ) -> Iterable[tuple[str, str, list[ByteRange]]]:
        rows: list[tuple[str, str, list[ByteRange]]] = []
        refs = self._find_graph_references(uri=uri, symbol=symbol, include_declaration=True)
        refs_by_uri: dict[str, list[ByteRange]] = {}
        for target in refs:
            refs_by_uri.setdefault(target.uri, []).append(target.range)
        for source_uri, source_text in self._iter_experience_sources(uri=uri):
            ranges = refs_by_uri.get(source_uri)
            if not ranges:
                continue
            deduped = sorted({(rng.start, rng.end) for rng in ranges})
            rows.append(
                (
                    source_uri,
                    source_text,
                    [ByteRange(start=start, end=end) for start, end in deduped],
                )
            )
        return tuple(rows)

    def _append_graph_ref_match(
        self,
        *,
        out: list[DefinitionTarget],
        seen: set[tuple[str, int, int]],
        source_uri: str,
        symbol: _GraphRenameSymbol,
        ref_node,
        document_bytes: bytes,
    ) -> None:
        parts = self._split_graph_ref_parts(ref_node=ref_node, document_bytes=document_bytes)
        if parts is None:
            return
        if symbol.kind == "node" and parts.node == (symbol.node or ""):
            self._append_unique_target(
                out=out,
                seen=seen,
                uri=source_uri,
                start=parts.node_range.start,
                end=parts.node_range.end,
            )
            return
        if symbol.kind == "identity" and parts.identity == (symbol.identity or ""):
            if symbol.node is not None and parts.node != symbol.node:
                return
            self._append_unique_target(
                out=out,
                seen=seen,
                uri=source_uri,
                start=parts.identity_range.start,
                end=parts.identity_range.end,
            )

    def _append_unique_target(
        self,
        *,
        out: list[DefinitionTarget],
        seen: set[tuple[str, int, int]],
        uri: str,
        start: int,
        end: int,
    ) -> None:
        if end <= start:
            return
        key = (uri, start, end)
        if key in seen:
            return
        seen.add(key)
        out.append(
            DefinitionTarget(
                uri=uri,
                range=ByteRange(start=start, end=end),
            )
        )
