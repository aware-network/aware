from __future__ import annotations

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

from aware_code.language_service.position import ByteRange
from aware_code.language_service.text import iter_identifier_tokens_in_range

from .contracts import (
    SemanticToken,
    SemanticTokensContext,
    TOKEN_MODIFIER_INDEX,
    TOKEN_TYPE_INDEX,
)


class SemanticTokenCollector:
    _context: SemanticTokensContext
    _tokens: list[SemanticToken]

    def __init__(self, *, context: SemanticTokensContext) -> None:
        self._context = context
        self._tokens = []

    @property
    def context(self) -> SemanticTokensContext:
        return self._context

    @property
    def document_bytes(self) -> bytes:
        return self._context.document_bytes

    @property
    def tokens(self) -> list[SemanticToken]:
        return list(self._tokens)

    def add_token(
        self,
        *,
        byte_start: int | None,
        byte_end: int | None,
        token_type_name: str,
        modifier_names: tuple[str, ...] = (),
    ) -> None:
        if byte_start is None or byte_end is None or byte_end <= byte_start:
            return

        start = self._context.mapper.byte_offset_to_position(byte_start)
        end = self._context.mapper.byte_offset_to_position(byte_end)
        if start.line != end.line:
            return

        length = end.character - start.character
        if length <= 0:
            return

        token_type = TOKEN_TYPE_INDEX.get(token_type_name)
        if token_type is None:
            return

        self._tokens.append(
            SemanticToken(
                line=start.line,
                start_char=start.character,
                length=length,
                token_type=token_type,
                token_modifiers=self._modifier_bitset(modifier_names),
            )
        )

    def add_token_range(
        self,
        *,
        byte_range: ByteRange,
        token_type_name: str,
        modifier_names: tuple[str, ...] = (),
    ) -> None:
        start = max(0, byte_range.start)
        end = max(start, byte_range.end)
        i = start
        while i < end:
            newline_index = self.document_bytes.find(b"\n", i, end)
            line_end = end if newline_index == -1 else newline_index
            self.add_token(
                byte_start=i,
                byte_end=line_end,
                token_type_name=token_type_name,
                modifier_names=modifier_names,
            )
            i = line_end + 1

    def add_type_tokens(
        self,
        *,
        segment: ContentPartTextSegment | None,
        modifier_names: tuple[str, ...] = (),
    ) -> None:
        if segment is None or segment.byte_start is None or segment.byte_end is None:
            return
        if segment.byte_end <= segment.byte_start:
            return

        for token_str, _token_bytes, token_range in iter_identifier_tokens_in_range(
            document_bytes=self.document_bytes,
            segment_start=segment.byte_start,
            segment_end=segment.byte_end,
        ):
            token_type_name = self.resolve_identifier_token_type(token_str=token_str)
            if token_type_name is None:
                continue
            self.add_token(
                byte_start=token_range.start,
                byte_end=token_range.end,
                token_type_name=token_type_name,
                modifier_names=modifier_names,
            )

    def add_type_span(
        self,
        *,
        byte_start: int,
        byte_end: int,
        modifier_names: tuple[str, ...] = (),
    ) -> None:
        for token_str, _token_bytes, token_range in iter_identifier_tokens_in_range(
            document_bytes=self.document_bytes,
            segment_start=byte_start,
            segment_end=byte_end,
        ):
            token_type_name = self.resolve_identifier_token_type(token_str=token_str)
            if token_type_name is None:
                continue
            self.add_token(
                byte_start=token_range.start,
                byte_end=token_range.end,
                token_type_name=token_type_name,
                modifier_names=modifier_names,
            )

    def resolve_identifier_token_type(self, *, token_str: str) -> str | None:
        if not token_str:
            return None

        scope = self._context.scope
        if scope.try_resolve_class_with_fqn(token_str) is not None:
            return "class"
        if scope.try_resolve_enum_with_fqn(token_str) is not None:
            return "enum"

        if self._context.is_primitive_type(token_str):
            return "type"

        return "type"

    @staticmethod
    def _modifier_bitset(modifier_names: tuple[str, ...]) -> int:
        bitset = 0
        for name in modifier_names:
            index = TOKEN_MODIFIER_INDEX.get(name)
            if index is None:
                continue
            bitset |= 1 << index
        return bitset
