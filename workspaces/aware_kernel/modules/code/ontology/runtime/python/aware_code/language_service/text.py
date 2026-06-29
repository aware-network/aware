from __future__ import annotations

import re
from collections.abc import Iterator

from aware_code.language_service.position import ByteRange
from aware_code.language_service.types import AnnotationStatementTokens, SpannedToken


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier(value: str) -> bool:
    return bool(_IDENTIFIER_RE.match((value or "").strip()))


def extract_identifier_token(
    *, document_bytes: bytes, byte_offset: int, segment_start: int, segment_end: int
) -> str | None:
    allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."

    start = max(segment_start, min(byte_offset, segment_end))
    end = start

    # Expand left.
    while start > segment_start:
        b = document_bytes[start - 1:start]
        if not b or b[0] not in allowed:
            break
        start -= 1

    # Expand right.
    while end < segment_end:
        b = document_bytes[end:end + 1]
        if not b or b[0] not in allowed:
            break
        end += 1

    if end <= start:
        return None
    token = document_bytes[start:end].decode("utf-8", errors="replace").strip()
    return token or None


def extract_identifier_prefix(
    *,
    document_bytes: bytes,
    byte_offset: int,
    segment_start: int,
    segment_end: int,
    allowed: bytes,
) -> str:
    """Extract the identifier prefix preceding the cursor within a segment.

    This is used for completions: it returns a possibly-empty string containing
    only allowed identifier characters (e.g., including '.' or ':' when desired).
    """
    cursor = max(segment_start, min(byte_offset, segment_end))
    start = cursor
    while start > segment_start:
        b = document_bytes[start - 1:start]
        if not b or b[0] not in allowed:
            break
        start -= 1
    raw = document_bytes[start:cursor].decode("utf-8", errors="replace").strip()
    return raw


def extract_identifier_token_span(
    *, document_bytes: bytes, byte_offset: int, segment_start: int, segment_end: int
) -> tuple[str, bytes, ByteRange] | None:
    """Extract the identifier token at the cursor within a segment and return (token, token_bytes, byte_range)."""
    allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."

    if segment_end <= segment_start:
        return None

    cursor = max(segment_start, min(byte_offset, segment_end))
    if cursor == segment_end and cursor > segment_start:
        cursor -= 1
    if not (segment_start <= cursor < segment_end):
        return None

    start = cursor
    end = cursor

    # Expand left.
    while start > segment_start:
        b = document_bytes[start - 1:start]
        if not b or b[0] not in allowed:
            break
        start -= 1

    # Expand right.
    while end < segment_end:
        b = document_bytes[end:end + 1]
        if not b or b[0] not in allowed:
            break
        end += 1

    if end <= start:
        return None
    token_bytes = document_bytes[start:end]
    token = token_bytes.decode("utf-8", errors="replace").strip()
    if not token:
        return None
    return token, token_bytes, ByteRange(start=start, end=end)


def iter_identifier_tokens_in_range(
    *, document_bytes: bytes, segment_start: int, segment_end: int
) -> Iterator[tuple[str, bytes, ByteRange]]:
    """Yield (token, token_bytes, byte_range) for identifier tokens within a byte span."""
    allowed = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
    start = max(0, segment_start)
    end = max(start, segment_end)
    i = start
    while i < end:
        b = document_bytes[i:i + 1]
        if not b or b[0] not in allowed:
            i += 1
            continue
        token_start = i
        i += 1
        while i < end:
            b2 = document_bytes[i:i + 1]
            if not b2 or b2[0] not in allowed:
                break
            i += 1
        token_end = i
        if token_end <= token_start:
            continue
        token_bytes = document_bytes[token_start:token_end]
        token = token_bytes.decode("utf-8", errors="replace").strip()
        if not token:
            continue
        yield token, token_bytes, ByteRange(start=token_start, end=token_end)


def name_part_range_from_token_bytes(token_range: ByteRange, token_bytes: bytes) -> tuple[ByteRange, str]:
    """Return the renameable name-part range (last segment) for an identifier token."""
    dot = token_bytes.rfind(b".")
    if dot == -1:
        start = token_range.start
        name_bytes = token_bytes
    else:
        start = token_range.start + dot + 1
        name_bytes = token_bytes[dot + 1:]
    placeholder = name_bytes.decode("utf-8", errors="replace")
    return ByteRange(start=start, end=token_range.end), placeholder


def iter_annotation_path_ranges(document_bytes: bytes) -> Iterator[ByteRange]:
    """Best-effort scan of `ann <path> ...` lines, yielding the byte ranges for the `<path>` token."""
    i = 0
    n = len(document_bytes)
    while i < n:
        line_start = i
        line_end = document_bytes.find(b"\n", i)
        if line_end == -1:
            line_end = n
        line = document_bytes[line_start:line_end]

        j = 0
        while j < len(line) and line[j:j + 1] in (b" ", b"\t"):
            j += 1
        if line[j:j + 3] == b"ann":
            k = j + 3
            if k < len(line) and line[k:k + 1] not in (b" ", b"\t"):
                pass
            else:
                while k < len(line) and line[k:k + 1] in (b" ", b"\t"):
                    k += 1
                path_start = line_start + k
                m = k
                while m < len(line) and line[m:m + 1] not in (b" ", b"\t"):
                    m += 1
                path_end = line_start + m
                if path_end > path_start:
                    yield ByteRange(start=path_start, end=path_end)

        i = line_end + 1


def find_annotation_path_segment_at(*, byte_offset: int, document_bytes: bytes) -> ByteRange | None:
    """Return the `ann <path> ...` path range for a cursor within that path (v0 heuristic)."""
    line_start = document_bytes.rfind(b"\n", 0, max(byte_offset, 0))
    line_start = 0 if line_start == -1 else line_start + 1
    line_end = document_bytes.find(b"\n", max(byte_offset, 0))
    if line_end == -1:
        line_end = len(document_bytes)

    line = document_bytes[line_start:line_end]
    i = 0
    while i < len(line) and line[i:i + 1] in (b" ", b"\t"):
        i += 1

    if line[i:i + 3] != b"ann":
        return None
    j = i + 3
    if j < len(line) and line[j:j + 1] not in (b" ", b"\t"):
        return None
    while j < len(line) and line[j:j + 1] in (b" ", b"\t"):
        j += 1

    path_start = line_start + j
    k = j
    while k < len(line) and line[k:k + 1] not in (b" ", b"\t"):
        k += 1
    path_end = line_start + k
    if path_end <= path_start:
        return None

    cursor = byte_offset
    if cursor == path_end and cursor > path_start:
        cursor -= 1
    if path_start <= cursor < path_end:
        return ByteRange(start=path_start, end=path_end)
    return None


def find_annotation_args_segment_at(*, byte_offset: int, document_bytes: bytes) -> ByteRange | None:
    """Return the `ann <path> <verb> <args...>` args span for a cursor after the verb.

    This is a lightweight, line-based heuristic (does not depend on the parser).
    It intentionally includes trailing whitespace so completions work before the
    user types the first arg token.
    """
    cursor = max(byte_offset, 0)

    line_start = document_bytes.rfind(b"\n", 0, cursor)
    line_start = 0 if line_start == -1 else line_start + 1
    line_end = document_bytes.find(b"\n", cursor)
    if line_end == -1:
        line_end = len(document_bytes)

    line = document_bytes[line_start:line_end]
    i = 0
    while i < len(line) and line[i:i + 1] in (b" ", b"\t"):
        i += 1

    if line[i:i + 3] != b"ann":
        return None
    j = i + 3
    if j < len(line) and line[j:j + 1] not in (b" ", b"\t"):
        return None
    while j < len(line) and line[j:j + 1] in (b" ", b"\t"):
        j += 1

    # Path token.
    path_start = line_start + j
    k = j
    while k < len(line) and line[k:k + 1] not in (b" ", b"\t"):
        k += 1
    path_end = line_start + k
    if path_end <= path_start:
        return None

    # Verb token.
    m = k
    while m < len(line) and line[m:m + 1] in (b" ", b"\t"):
        m += 1
    verb_start = line_start + m
    n = m
    while n < len(line) and line[n:n + 1] not in (b" ", b"\t"):
        n += 1
    verb_end = line_start + n
    if verb_end <= verb_start:
        return None

    # Cursor must be after the verb to be in args space.
    if cursor < verb_end:
        return None
    if path_start <= cursor < path_end:
        return None
    if verb_start <= cursor < verb_end:
        return None

    return ByteRange(start=verb_end, end=line_end)


def split_whitespace_tokens_with_ranges(
    *, document_bytes: bytes, segment_start: int, segment_end: int
) -> list[SpannedToken]:
    """Split a byte span into whitespace-delimited tokens with absolute ByteRanges."""
    start = max(0, segment_start)
    end = max(start, segment_end)
    tokens: list[SpannedToken] = []
    i = start
    while i < end:
        b = document_bytes[i:i + 1]
        if b in (b" ", b"\t", b"\r", b"\n"):
            i += 1
            continue
        token_start = i
        i += 1
        while i < end:
            b2 = document_bytes[i:i + 1]
            if b2 in (b" ", b"\t", b"\r", b"\n"):
                break
            i += 1
        token_end = i
        if token_end <= token_start:
            continue
        raw = document_bytes[token_start:token_end].decode("utf-8", errors="replace")
        text = raw.strip()
        if not text:
            continue
        tokens.append(SpannedToken(text=text, range=ByteRange(start=token_start, end=token_end)))
    return tokens


def parse_annotation_statement_tokens(
    *, document_bytes: bytes, segment_start: int, segment_end: int
) -> AnnotationStatementTokens | None:
    """Parse an `ann <path> <verb> ...args` statement within a section byte span."""
    tokens = split_whitespace_tokens_with_ranges(
        document_bytes=document_bytes,
        segment_start=segment_start,
        segment_end=segment_end,
    )
    if not tokens:
        return None
    if tokens[0].text != "ann":
        return None
    path = tokens[1] if len(tokens) >= 2 else None
    verb = tokens[2] if len(tokens) >= 3 else None
    args = tuple(tokens[3:]) if len(tokens) >= 4 else ()
    return AnnotationStatementTokens(path=path, verb=verb, args=args)


def split_double_colon_parts(*, token_bytes: bytes, token_range: ByteRange) -> list[SpannedToken]:
    """Split a `::`-delimited token (e.g. annotation path) into non-empty parts with ranges."""
    parts: list[SpannedToken] = []
    i = 0
    n = len(token_bytes)
    while i <= n:
        j = token_bytes.find(b"::", i)
        if j == -1:
            part_start = i
            part_end = n
            i = n + 1
        else:
            part_start = i
            part_end = j
            i = j + 2

        if part_end <= part_start:
            continue
        raw = token_bytes[part_start:part_end].decode("utf-8", errors="replace")
        text = raw.strip()
        if not text:
            continue
        parts.append(
            SpannedToken(
                text=text,
                range=ByteRange(
                    start=token_range.start + part_start,
                    end=token_range.start + part_end,
                ),
            )
        )
    return parts
