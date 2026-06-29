from __future__ import annotations

from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute

from aware_code.language_service.position import ByteRange
from aware_code.language_service.text import (
    extract_identifier_token,
    find_annotation_args_segment_at,
    find_annotation_path_segment_at,
)
from aware_code.language_service.types import CompletionSegment

from aware_workspace.compiler.workspace import WorkspaceSnapshot


class SegmentMixin:
    _snapshot: WorkspaceSnapshot | None = None

    def _find_mirror_target_token_at(self, *, uri: str, byte_offset: int, document_bytes: bytes) -> str | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.mirror:
                continue
            mirror = section.code_section_mirror
            if mirror is None:
                continue
            seg = mirror.target_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if not (seg.byte_start <= cursor < seg.byte_end):
                continue

            return extract_identifier_token(
                document_bytes=document_bytes,
                byte_offset=cursor,
                segment_start=seg.byte_start,
                segment_end=seg.byte_end,
            )
        return None

    def _find_mirror_target_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.mirror:
                continue
            mirror = section.code_section_mirror
            if mirror is None:
                continue
            seg = mirror.target_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_attribute_type_token_at(self, *, uri: str, byte_offset: int, document_bytes: bytes) -> str | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.attribute:
                continue
            attr = section.code_section_attribute
            if attr is None or attr.type_segment is None:
                continue
            seg = attr.type_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            # LSP positions are cursor offsets; allow a cursor at the segment end to resolve the last token.
            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if not (seg.byte_start <= cursor < seg.byte_end):
                continue

            return extract_identifier_token(
                document_bytes=document_bytes,
                byte_offset=cursor,
                segment_start=seg.byte_start,
                segment_end=seg.byte_end,
            )
        return None

    def _find_attribute_type_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.attribute:
                continue
            attr = section.code_section_attribute
            if attr is None or attr.type_segment is None:
                continue
            seg = attr.type_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_type_token_at(self, *, uri: str, byte_offset: int, document_bytes: bytes) -> str | None:
        token = self._find_attribute_type_token_at(uri=uri, byte_offset=byte_offset, document_bytes=document_bytes)
        if token:
            return token
        token = self._find_class_base_token_at(uri=uri, byte_offset=byte_offset, document_bytes=document_bytes)
        if token:
            return token
        token = self._find_function_return_token_at(uri=uri, byte_offset=byte_offset, document_bytes=document_bytes)
        if token:
            return token
        token = self._find_mirror_target_token_at(uri=uri, byte_offset=byte_offset, document_bytes=document_bytes)
        if token:
            return token
        return None

    def _find_type_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        seg = self._find_attribute_type_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return seg
        seg = self._find_class_base_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return seg
        seg = self._find_function_return_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return seg
        seg = self._find_mirror_target_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return seg
        return None

    def _find_import_module_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.import_:
                continue
            imp = section.code_section_import
            if imp is None:
                continue
            seg = imp.module_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_import_alias_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.import_:
                continue
            imp = section.code_section_import
            if imp is None:
                continue
            for name in imp.code_section_import_names:
                seg = name.alias_segment
                if seg is None or seg.byte_start is None or seg.byte_end is None:
                    continue
                if seg.byte_end <= seg.byte_start:
                    continue

                cursor = byte_offset
                if cursor == seg.byte_end and cursor > seg.byte_start:
                    cursor -= 1
                if seg.byte_start <= cursor < seg.byte_end:
                    return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_annotation_path_segment_at(self, *, byte_offset: int, document_bytes: bytes) -> ByteRange | None:
        return find_annotation_path_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)

    def _find_annotation_args_segment_at(self, *, byte_offset: int, document_bytes: bytes) -> ByteRange | None:
        return find_annotation_args_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)

    def _find_default_value_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.attribute:
                continue
            attr = section.code_section_attribute
            if attr is None:
                continue
            seg = attr.default_value_segment
            if seg is None or seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_attribute_with_default_at(self, *, uri: str, byte_offset: int) -> CodeSectionAttribute | None:
        """Return the attribute whose default-value segment contains the cursor."""
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None
        for section in code.code_sections:
            if section.type != CodeSectionType.attribute:
                continue
            attr = section.code_section_attribute
            if attr is None:
                continue
            seg = attr.default_value_segment
            if seg is None or seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return attr
        return None

    def _find_completion_segment_at(
        self, *, uri: str, byte_offset: int, document_bytes: bytes
    ) -> CompletionSegment | None:
        seg = self._find_type_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return CompletionSegment(range=seg, kind="type")
        seg = self._find_default_value_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return CompletionSegment(range=seg, kind="default_value")
        seg = self._find_import_module_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return CompletionSegment(range=seg, kind="import_module")
        seg = self._find_import_alias_segment_at(uri=uri, byte_offset=byte_offset)
        if seg is not None:
            return CompletionSegment(range=seg, kind="import_alias")
        seg = self._find_annotation_path_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)
        if seg is not None:
            return CompletionSegment(range=seg, kind="annotation_path")
        seg = self._find_annotation_args_segment_at(byte_offset=byte_offset, document_bytes=document_bytes)
        if seg is not None:
            return CompletionSegment(range=seg, kind="annotation_args")
        return None

    def _find_class_base_token_at(self, *, uri: str, byte_offset: int, document_bytes: bytes) -> str | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.class_:
                continue
            cls = section.code_section_class
            if cls is None:
                continue
            for base in cls.code_section_class_bases:
                seg = base.segment
                if seg is None or seg.byte_start is None or seg.byte_end is None:
                    continue
                if seg.byte_end <= seg.byte_start:
                    continue

                cursor = byte_offset
                if cursor == seg.byte_end and cursor > seg.byte_start:
                    cursor -= 1
                if not (seg.byte_start <= cursor < seg.byte_end):
                    continue

                return extract_identifier_token(
                    document_bytes=document_bytes,
                    byte_offset=cursor,
                    segment_start=seg.byte_start,
                    segment_end=seg.byte_end,
                )
        return None

    def _find_class_base_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.class_:
                continue
            cls = section.code_section_class
            if cls is None:
                continue
            for base in cls.code_section_class_bases:
                seg = base.segment
                if seg is None or seg.byte_start is None or seg.byte_end is None:
                    continue
                if seg.byte_end <= seg.byte_start:
                    continue

                cursor = byte_offset
                if cursor == seg.byte_end and cursor > seg.byte_start:
                    cursor -= 1
                if seg.byte_start <= cursor < seg.byte_end:
                    return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None

    def _find_function_return_token_at(self, *, uri: str, byte_offset: int, document_bytes: bytes) -> str | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.function:
                continue
            fn = section.code_section_function
            if fn is None or fn.return_type_segment is None:
                continue
            seg = fn.return_type_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if not (seg.byte_start <= cursor < seg.byte_end):
                continue

            return extract_identifier_token(
                document_bytes=document_bytes,
                byte_offset=cursor,
                segment_start=seg.byte_start,
                segment_end=seg.byte_end,
            )
        return None

    def _find_function_return_segment_at(self, *, uri: str, byte_offset: int) -> ByteRange | None:
        if self._snapshot is None:
            return None
        code = self._snapshot.codes_by_uri.get(uri)
        if code is None:
            return None

        for section in code.code_sections:
            if section.type != CodeSectionType.function:
                continue
            fn = section.code_section_function
            if fn is None or fn.return_type_segment is None:
                continue
            seg = fn.return_type_segment
            if seg.byte_start is None or seg.byte_end is None:
                continue
            if seg.byte_end <= seg.byte_start:
                continue

            cursor = byte_offset
            if cursor == seg.byte_end and cursor > seg.byte_start:
                cursor -= 1
            if seg.byte_start <= cursor < seg.byte_end:
                return ByteRange(start=seg.byte_start, end=seg.byte_end)
        return None
