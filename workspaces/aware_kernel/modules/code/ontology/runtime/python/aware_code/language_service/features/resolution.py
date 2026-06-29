from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.language_service.features.segments import SegmentMixin
from aware_code.language_service.position import ByteRange
from aware_code.language_service.text import extract_identifier_token_span
from aware_code.language_service.types import ResolvedSymbol

from aware_workspace.compiler.workspace import WorkspaceSnapshot


class ResolutionMixin(SegmentMixin):
    _snapshot: WorkspaceSnapshot | None

    def _definition_name_range_at(self, *, uri: str, byte_offset: int) -> tuple[ByteRange | None, str | None]:
        if self._snapshot is None:
            return None, None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None, None

        cursor = byte_offset

        for section in code.code_sections:
            if section.type == CodeSectionType.class_:
                cls = section.code_section_class
                if cls is None:
                    continue
                seg = cls.name_segment
                if seg.byte_start is None or seg.byte_end is None:
                    continue
                if seg.byte_end <= seg.byte_start:
                    continue
                c = cursor
                if c == seg.byte_end and c > seg.byte_start:
                    c -= 1
                if seg.byte_start <= c < seg.byte_end:
                    return ByteRange(start=seg.byte_start, end=seg.byte_end), cls.name

            if section.type == CodeSectionType.enum:
                enum = section.code_section_enum
                if enum is None:
                    continue
                seg = enum.name_segment
                if seg.byte_start is None or seg.byte_end is None:
                    continue
                if seg.byte_end <= seg.byte_start:
                    continue
                c = cursor
                if c == seg.byte_end and c > seg.byte_start:
                    c -= 1
                if seg.byte_start <= c < seg.byte_end:
                    return ByteRange(start=seg.byte_start, end=seg.byte_end), enum.name

        return None, None

    def _resolve_symbol_at_byte_offset(
        self, *, uri: str, byte_offset: int, document_bytes: bytes, document_text: str
    ) -> ResolvedSymbol | None:
        _ = document_text
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        scope = self._snapshot.fqn_resolver.scope_for_code_id(code.id)

        cursor = byte_offset

        # Cursor on a class/enum definition name.
        for section in code.code_sections:
            if section.type == CodeSectionType.class_:
                cls = section.code_section_class
                if cls is None:
                    continue
                seg = cls.name_segment
                if seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                    continue
                c = cursor
                if c == seg.byte_end and c > seg.byte_start:
                    c -= 1
                if not (seg.byte_start <= c < seg.byte_end):
                    continue
                resolved = scope.try_resolve_class_with_fqn(cls.name)
                if resolved is not None:
                    fqn, _ = resolved
                    return ResolvedSymbol(kind="class", fqn=fqn, name=cls.name)

            if section.type == CodeSectionType.enum:
                enum = section.code_section_enum
                if enum is None:
                    continue
                seg = enum.name_segment
                if seg.byte_start is None or seg.byte_end is None or seg.byte_end <= seg.byte_start:
                    continue
                c = cursor
                if c == seg.byte_end and c > seg.byte_start:
                    c -= 1
                if not (seg.byte_start <= c < seg.byte_end):
                    continue
                resolved = scope.try_resolve_enum_with_fqn(enum.name)
                if resolved is not None:
                    fqn, _ = resolved
                    return ResolvedSymbol(kind="enum", fqn=fqn, name=enum.name)

        # Cursor on a type token.
        token = self._find_type_token_at(uri=uri, byte_offset=byte_offset, document_bytes=document_bytes)
        if token:
            resolved_class = scope.try_resolve_class_with_fqn(token)
            if resolved_class is not None:
                fqn, cls_cfg = resolved_class
                return ResolvedSymbol(kind="class", fqn=fqn, name=cls_cfg.name)
            resolved_enum = scope.try_resolve_enum_with_fqn(token)
            if resolved_enum is not None:
                fqn, enum_cfg = resolved_enum
                return ResolvedSymbol(kind="enum", fqn=fqn, name=enum_cfg.name)

        # Cursor on an annotation path token.
        ann_seg = self._find_annotation_path_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)
        if ann_seg is not None:
            tok = extract_identifier_token_span(
                document_bytes=document_bytes,
                byte_offset=byte_offset,
                segment_start=ann_seg.start,
                segment_end=ann_seg.end,
            )
            if tok is not None:
                token_str, _, _ = tok
                resolved_class = scope.try_resolve_class_with_fqn(token_str)
                if resolved_class is not None:
                    fqn, cls_cfg = resolved_class
                    return ResolvedSymbol(kind="class", fqn=fqn, name=cls_cfg.name)
                resolved_enum = scope.try_resolve_enum_with_fqn(token_str)
                if resolved_enum is not None:
                    fqn, enum_cfg = resolved_enum
                    return ResolvedSymbol(kind="enum", fqn=fqn, name=enum_cfg.name)

        return None
