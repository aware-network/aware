from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Utf16Position:
    line: int
    character: int


@dataclass(frozen=True, slots=True)
class ByteRange:
    start: int
    end: int


class Utf16PositionMapper:
    """Maps between UTF-8 byte offsets and LSP UTF-16 positions.

    Canonical contract for Aware:
    - All CodeSections use byte offsets (UTF-8).
    - LSP clients (VS Code/Cursor) default to UTF-16 code-unit positions.
    - Mapping happens at the protocol boundary, never inside kernel-meta.
    """

    _text: str
    _bytes: bytes
    _line_starts: list[int]

    def __init__(self, *, text: str) -> None:
        self._text = text
        self._bytes = text.encode("utf-8")
        self._line_starts = self._compute_line_start_bytes(self._bytes)

    @staticmethod
    def _compute_line_start_bytes(source: bytes) -> list[int]:
        # Always include line 0.
        starts = [0]
        for idx, b in enumerate(source):
            if b == 0x0A:  # '\n'
                starts.append(idx + 1)
        return starts

    @property
    def text(self) -> str:
        return self._text

    @property
    def source_bytes(self) -> bytes:
        return self._bytes

    def byte_offset_to_position(self, byte_offset: int) -> Utf16Position:
        if byte_offset < 0:
            byte_offset = 0
        if byte_offset > len(self._bytes):
            byte_offset = len(self._bytes)

        line = bisect_right(self._line_starts, byte_offset) - 1
        line = max(0, min(line, len(self._line_starts) - 1))
        line_start = self._line_starts[line]
        prefix = self._bytes[line_start:byte_offset].decode("utf-8", errors="replace")
        character = _utf16_code_units(prefix)
        return Utf16Position(line=line, character=character)

    def position_to_byte_offset(self, pos: Utf16Position) -> int:
        line = max(0, pos.line)
        if not self._line_starts:
            return 0
        if line >= len(self._line_starts):
            return len(self._bytes)

        line_start = self._line_starts[line]
        line_end = self._line_starts[line + 1] if line + 1 < len(self._line_starts) else len(self._bytes)
        line_text = self._bytes[line_start:line_end].decode("utf-8", errors="replace")

        desired = max(0, pos.character)
        consumed_utf16 = 0
        consumed_bytes = 0
        for ch in line_text:
            units = 2 if ord(ch) > 0xFFFF else 1
            if consumed_utf16 + units > desired:
                break
            consumed_utf16 += units
            consumed_bytes += len(ch.encode("utf-8"))

        return min(line_start + consumed_bytes, len(self._bytes))

    def byte_range_to_positions(self, rng: ByteRange) -> tuple[Utf16Position, Utf16Position]:
        return self.byte_offset_to_position(rng.start), self.byte_offset_to_position(rng.end)


def _utf16_code_units(text: str) -> int:
    # LSP "character" is UTF-16 code units.
    units = 0
    for ch in text:
        units += 2 if ord(ch) > 0xFFFF else 1
    return units
