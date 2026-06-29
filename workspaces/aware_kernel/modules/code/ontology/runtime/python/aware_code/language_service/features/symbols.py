from __future__ import annotations

from typing import TypedDict
from uuid import UUID

from tree_sitter import Node
from typing_extensions import override

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.code.code_section import CodeSection
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_code.language_service.document import DocumentContext
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.programs import parse_tree

from aware_workspace.compiler.workspace import WorkspaceSnapshot


class _LspPosition(TypedDict):
    line: int
    character: int


class _LspRange(TypedDict):
    start: _LspPosition
    end: _LspPosition


class _LspDocumentSymbol(TypedDict, total=False):
    name: str
    kind: int
    range: _LspRange
    selectionRange: _LspRange
    detail: str
    children: list[_LspDocumentSymbol]


class _LspLocation(TypedDict):
    uri: str
    range: _LspRange


class _LspWorkspaceSymbol(TypedDict, total=False):
    name: str
    kind: int
    location: _LspLocation
    containerName: str


class SymbolsMixin(ServiceMixinBase):
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

    def document_symbols(self, *, uri: str, document_text: str) -> list[_LspDocumentSymbol]:
        """Return LSP DocumentSymbol[] for the current document (outline view)."""
        if self._is_aware_config_uri(uri):
            return []
        self._ensure_snapshot_for_uri(uri=uri)
        if self._snapshot is None or uri not in self._snapshot.codes_by_uri:
            return []
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return []

        ctx = self._document_context(uri=uri, document_text=document_text)
        mapper = ctx.mapper
        doc_bytes = ctx.document_bytes

        def _range_from_seg(
            seg: ContentPartTextSegment | None,
        ) -> _LspRange | None:
            if seg is None or seg.byte_start is None or seg.byte_end is None:
                return None
            if seg.byte_end <= seg.byte_start:
                return None
            start = mapper.byte_offset_to_position(seg.byte_start)
            end = mapper.byte_offset_to_position(seg.byte_end)
            return {
                "start": {"line": start.line, "character": start.character},
                "end": {"line": end.line, "character": end.character},
            }

        def _range_from_section(section: CodeSection) -> _LspRange | None:
            seg = section.content_part_text_segment
            return _range_from_seg(seg)

        member_function_section_ids: set[UUID] = set()
        for section in code.code_sections:
            if section.type != CodeSectionType.class_:
                continue
            cls = section.code_section_class
            if cls is None:
                continue
            for fn in cls.code_section_functions:
                cs = fn.code_section
                member_function_section_ids.add(cs.id)

        symbols: list[_LspDocumentSymbol] = []

        for section in code.code_sections:
            if section.type == CodeSectionType.class_:
                cls = section.code_section_class
                if cls is None:
                    continue
                range_ = _range_from_section(section)
                selection = _range_from_seg(cls.name_segment) or range_
                if range_ is None or selection is None:
                    continue

                children_attrs: list[_LspDocumentSymbol] = []
                for attr in cls.code_section_attributes:
                    attr_section = attr.code_section
                    attr_range = _range_from_section(attr_section)
                    attr_sel = _range_from_seg(attr.name_segment) or attr_range
                    if attr_range is None or attr_sel is None:
                        continue
                    children_attrs.append(
                        {
                            "name": attr.name,
                            "kind": 8,  # Field
                            "range": attr_range,
                            "selectionRange": attr_sel,
                        }
                    )

                for fn in cls.code_section_functions:
                    fn_section = fn.code_section
                    fn_range = _range_from_section(fn_section)
                    fn_sel = _range_from_seg(fn.name_segment) or _range_from_seg(fn.signature_segment)
                    if fn_range is None or fn_sel is None:
                        continue
                    children_attrs.append(
                        {
                            "name": fn.name,
                            "kind": 6,  # Method
                            "range": fn_range,
                            "selectionRange": fn_sel,
                        }
                    )

                symbols.append(
                    {
                        "name": cls.name,
                        "kind": 5,  # Class
                        "range": range_,
                        "selectionRange": selection,
                        "children": children_attrs,
                    }
                )
                continue

            if section.type == CodeSectionType.enum:
                enum = section.code_section_enum
                if enum is None:
                    continue
                range_ = _range_from_section(section)
                selection = _range_from_seg(enum.name_segment) or range_
                if range_ is None or selection is None:
                    continue

                children_enum_values: list[_LspDocumentSymbol] = []
                for val in enum.code_section_enum_values or []:
                    val_section = val.code_section
                    val_range = _range_from_section(val_section)
                    val_sel = _range_from_seg(val.value_segment) or val_range
                    if val_range is None or val_sel is None:
                        continue
                    children_enum_values.append(
                        {
                            "name": val.value,
                            "kind": 22,  # EnumMember
                            "range": val_range,
                            "selectionRange": val_sel,
                        }
                    )

                symbols.append(
                    {
                        "name": enum.name,
                        "kind": 10,  # Enum
                        "range": range_,
                        "selectionRange": selection,
                        "children": children_enum_values,
                    }
                )
                continue

            if section.type == CodeSectionType.function:
                if section.id in member_function_section_ids:
                    continue
                fn = section.code_section_function
                if fn is None:
                    continue
                range_ = _range_from_section(section)
                selection = _range_from_seg(fn.name_segment) or _range_from_seg(fn.signature_segment)
                if range_ is None or selection is None:
                    continue
                symbols.append(
                    {
                        "name": fn.name,
                        "kind": 12,  # Function
                        "range": range_,
                        "selectionRange": selection,
                    }
                )

        # Projection blocks are first-class Aware syntax but are currently lowered into ANN for compilation.
        # Include them in the outline to make large projection/view declarations navigable.
        if b"projection" in doc_bytes:
            try:
                root = parse_tree(document_bytes=doc_bytes)
            except Exception:
                root = None

            def _range_from_bytes(byte_start: int, byte_end: int) -> _LspRange | None:
                if byte_end <= byte_start:
                    return None
                start = mapper.byte_offset_to_position(byte_start)
                end = mapper.byte_offset_to_position(byte_end)
                return {
                    "start": {"line": start.line, "character": start.character},
                    "end": {"line": end.line, "character": end.character},
                }

            def _node_text(node: Node | None) -> str:
                try:
                    if node is None:
                        return ""
                    return doc_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()
                except Exception:
                    return ""

            def _join_view_prefix(prefix: str, part: str) -> str:
                if not prefix:
                    return part
                if not part:
                    return prefix
                return f"{prefix}.{part}"

            def _view_children_from_group(*, node: Node, prefix: str) -> list[_LspDocumentSymbol]:
                prefix_node = node.child_by_field_name("prefix")
                group_part = _node_text(prefix_node) if prefix_node is not None else ""
                full_prefix = _join_view_prefix(prefix, group_part)

                range_ = _range_from_bytes(node.start_byte, node.end_byte)
                selection = (
                    _range_from_bytes(prefix_node.start_byte, prefix_node.end_byte)
                    if prefix_node is not None
                    else range_
                )
                if range_ is None or selection is None:
                    return []

                children: list[_LspDocumentSymbol] = []
                for ch in node.named_children:
                    if ch.type == "projection_view_group":
                        children.extend(_view_children_from_group(node=ch, prefix=full_prefix))
                    if ch.type == "projection_view_def":
                        view_key_node = ch.child_by_field_name("view_key")
                        key_part = _node_text(view_key_node) if view_key_node is not None else ""
                        full_key = _join_view_prefix(full_prefix, key_part)
                        view_range = _range_from_bytes(ch.start_byte, ch.end_byte)
                        view_sel = (
                            _range_from_bytes(view_key_node.start_byte, view_key_node.end_byte)
                            if view_key_node is not None
                            else view_range
                        )
                        if view_range is None or view_sel is None:
                            continue
                        kind_node = ch.child_by_field_name("kind")
                        kind = _node_text(kind_node) if kind_node is not None else None
                        is_default = any(c.type == "default" for c in ch.children)

                        payload: _LspDocumentSymbol = {
                            "name": full_key or key_part,
                            "kind": 6,  # Method
                            "range": view_range,
                            "selectionRange": view_sel,
                        }
                        details: list[str] = []
                        if kind:
                            details.append(kind)
                        if is_default:
                            details.append("default")
                        if details:
                            payload["detail"] = " ".join(details)
                        children.append(payload)

                group_symbol: _LspDocumentSymbol = {
                    "name": group_part or full_prefix or "view",
                    "kind": 3,  # Namespace
                    "range": range_,
                    "selectionRange": selection,
                }
                if children:
                    group_symbol["children"] = children
                return [group_symbol]

            if root is not None:
                stack = [root]
                while stack:
                    node = stack.pop()
                    if node.type != "projection_def":
                        stack.extend(reversed(list(node.named_children)))
                        continue

                    name_node = node.child_by_field_name("name")
                    if name_node is None:
                        continue
                    proj_name = _node_text(name_node)
                    proj_range = _range_from_bytes(node.start_byte, node.end_byte)
                    proj_sel = _range_from_bytes(name_node.start_byte, name_node.end_byte) or proj_range
                    if proj_range is None or proj_sel is None:
                        continue

                    children: list[_LspDocumentSymbol] = []
                    for item in node.named_children:
                        if item.type != "projection_item":
                            continue
                        inner = next(
                            (
                                c
                                for c in item.named_children
                                if c.type in {"projection_view_group", "projection_view_def"}
                            ),
                            None,
                        )
                        if inner is None:
                            continue
                        if inner.type == "projection_view_group":
                            children.extend(_view_children_from_group(node=inner, prefix=""))
                        elif inner.type == "projection_view_def":
                            view_key_node = inner.child_by_field_name("view_key")
                            key = _node_text(view_key_node) if view_key_node is not None else ""
                            view_range = _range_from_bytes(inner.start_byte, inner.end_byte)
                            view_sel = (
                                _range_from_bytes(view_key_node.start_byte, view_key_node.end_byte)
                                if view_key_node is not None
                                else view_range
                            )
                            if view_range is None or view_sel is None:
                                continue
                            kind_node = inner.child_by_field_name("kind")
                            kind = _node_text(kind_node) if kind_node is not None else None
                            is_default = any(c.type == "default" for c in inner.children)
                            payload: _LspDocumentSymbol = {
                                "name": key,
                                "kind": 6,  # Method
                                "range": view_range,
                                "selectionRange": view_sel,
                            }
                            details: list[str] = []
                            if kind:
                                details.append(kind)
                            if is_default:
                                details.append("default")
                            if details:
                                payload["detail"] = " ".join(details)
                            children.append(payload)

                    proj_symbol: _LspDocumentSymbol = {
                        "name": proj_name or "projection",
                        "kind": 5,  # Class
                        "range": proj_range,
                        "selectionRange": proj_sel,
                    }
                    if children:
                        proj_symbol["children"] = children
                    symbols.append(proj_symbol)

        return symbols

    def workspace_symbols(self, *, query: str) -> list[_LspWorkspaceSymbol]:
        """Return LSP SymbolInformation[] for the current snapshot (workspace symbol search)."""
        q = (query or "").strip()
        if not q:
            return []

        if self._snapshot is None:
            self._rebuild_full()
        if self._snapshot is None:
            return []

        ql = q.lower()
        results: list[_LspWorkspaceSymbol] = []
        max_results = 500

        for uri, code in sorted(self._snapshot.codes_by_uri.items(), key=lambda item: item[0]):
            try:
                text = self._workspace.get_document_text(uri)
            except Exception:
                continue
            mapper = self._document_context(uri=uri, document_text=text).mapper

            ns = self._snapshot.namespace_by_code_id.get(code.id)
            container_ns = ns.prefix() if ns is not None else None

            def _range_from_seg(seg: ContentPartTextSegment | None) -> _LspRange | None:
                if seg is None or seg.byte_start is None or seg.byte_end is None:
                    return None
                if seg.byte_end <= seg.byte_start:
                    return None
                start = mapper.byte_offset_to_position(seg.byte_start)
                end = mapper.byte_offset_to_position(seg.byte_end)
                return {
                    "start": {"line": start.line, "character": start.character},
                    "end": {"line": end.line, "character": end.character},
                }

            def _add_symbol(
                *, name: str, kind: int, seg: ContentPartTextSegment | None, container: str | None
            ) -> None:
                if len(results) >= max_results:
                    return
                rng = _range_from_seg(seg)
                if rng is None:
                    return
                payload: _LspWorkspaceSymbol = {
                    "name": name,
                    "kind": kind,
                    "location": {"uri": uri, "range": rng},
                }
                if container:
                    payload["containerName"] = container
                results.append(payload)

            # Collect class member function ids to avoid double-reporting global symbols.
            member_function_section_ids: set[UUID] = set()
            for section in code.code_sections:
                if section.type != CodeSectionType.class_:
                    continue
                cls = section.code_section_class
                if cls is None:
                    continue
                for fn in cls.code_section_functions:
                    cs = fn.code_section
                    member_function_section_ids.add(cs.id)

            for section in code.code_sections:
                if len(results) >= max_results:
                    break

                if section.type == CodeSectionType.class_:
                    cls = section.code_section_class
                    if cls is None:
                        continue
                    fqn = ns.fqn(cls.name) if ns is not None else cls.name
                    if ql in cls.name.lower() or ql in fqn.lower():
                        _add_symbol(
                            name=cls.name,
                            kind=5,
                            seg=cls.name_segment,
                            container=container_ns,
                        )

                    # Member search
                    for attr in cls.code_section_attributes:
                        if ql not in attr.name.lower():
                            continue
                        _add_symbol(
                            name=attr.name,
                            kind=8,
                            seg=attr.name_segment,
                            container=cls.name,
                        )
                    for fn in cls.code_section_functions:
                        if ql not in fn.name.lower():
                            continue
                        _add_symbol(
                            name=fn.name,
                            kind=6,
                            seg=fn.name_segment,
                            container=cls.name,
                        )
                    continue

                if section.type == CodeSectionType.enum:
                    enum = section.code_section_enum
                    if enum is None:
                        continue
                    fqn = ns.fqn(enum.name) if ns is not None else enum.name
                    if ql in enum.name.lower() or ql in fqn.lower():
                        _add_symbol(
                            name=enum.name,
                            kind=10,
                            seg=enum.name_segment,
                            container=container_ns,
                        )
                    for val in enum.code_section_enum_values or []:
                        if ql not in (val.value or "").lower():
                            continue
                        _add_symbol(
                            name=val.value,
                            kind=22,
                            seg=val.value_segment,
                            container=enum.name,
                        )
                    continue

                if section.type == CodeSectionType.function:
                    if section.id in member_function_section_ids:
                        continue
                    fn = section.code_section_function
                    if fn is None:
                        continue
                    if ql not in fn.name.lower():
                        continue
                    _add_symbol(
                        name=fn.name,
                        kind=12,
                        seg=fn.name_segment or fn.signature_segment,
                        container=container_ns,
                    )
                    continue

                if section.type == CodeSectionType.projection:
                    proj = section.code_section_projection
                    if proj is None:
                        continue

                    symbol_name = (proj.name or "").strip()
                    projection_name = (proj.projection_name or "").strip()

                    if symbol_name:
                        if ql in symbol_name.lower() or (projection_name and ql in projection_name.lower()):
                            _add_symbol(
                                name=symbol_name,
                                kind=5,  # Class
                                seg=proj.name_segment,
                                container=container_ns,
                            )

                    for view in proj.projection_views or []:
                        view_key = (view.key or "").strip()
                        if not view_key:
                            continue
                        if ql not in view_key.lower():
                            continue
                        _add_symbol(
                            name=view_key,
                            kind=6,  # Method
                            seg=view.key_segment,
                            container=symbol_name or projection_name or container_ns,
                        )
                    continue

        return results
