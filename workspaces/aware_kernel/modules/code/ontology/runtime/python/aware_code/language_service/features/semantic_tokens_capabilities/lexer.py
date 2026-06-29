from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language_service.position import ByteRange

from .collector import SemanticTokenCollector
from .contracts import LexicalToken


_AWARE_KEYWORDS: set[str] = {
    # Declarations.
    "class",
    "edge",
    "enum",
    "fn",
    "ann",
    "import",
    "as",
    "view",
    "program",
    "experience",
    "environment",
    "role",
    "actor",
    "port",
    "bind",
    "call",
    "impl",
    "let",
    "branch",
    "observable",
    "input",
    "expect",
    # Class verbs.
    "augment",
    "construct",
    # Projection blocks.
    "root",
    "default",
    "instance",
    # Annotation verbs.
    "load",
    "project",
    "overlay",
    "override",
    "discriminate",
    # Annotation args / flags.
    "language",
    "entity",
    "rename",
    "wire_name",
    "fk",
    "relationship",
    "nullable",
    "name",
    "label",
    "target",
    "side",
    "is_branchable",
    "key",
    "tag",
    "forward",
    "reverse",
    "both",
    "eager",
    "lazy",
    # Literals.
    "true",
    "false",
    "null",
}

_AWARE_MODIFIERS: set[str] = {
    "async",
    "unique",
    "many",
    "inline_value",
}

_AWARE_KEYWORD_MODIFIERS: dict[str, tuple[str, ...]] = {
    "view": ("projection",),
    "root": ("projection",),
    "instance": ("projection",),
    "experience": ("experience",),
    "observable": ("experience",),
    "branch": ("experience",),
    "program": ("program",),
    "port": ("program", "portNode"),
    "bind": ("program",),
    "call": ("program",),
    "let": ("program",),
    "input": ("program",),
    "expect": ("program",),
    "impl": ("program",),
    "environment": ("environment",),
    "role": ("role",),
    "actor": ("actor",),
    "key": ("identity",),
}


def _is_ident_start(value: int) -> bool:
    return (ord("A") <= value <= ord("Z")) or (ord("a") <= value <= ord("z")) or value == ord("_")


def _is_ident_part(value: int) -> bool:
    return _is_ident_start(value) or (ord("0") <= value <= ord("9"))


def iter_aware_lexical_tokens(*, document_bytes: bytes) -> list[LexicalToken]:
    """Return lexical tokens as (type, byte_range, modifiers) for Aware."""
    tokens: list[LexicalToken] = []
    i = 0
    n = len(document_bytes)

    def _add(token_type: str, start: int, end: int, modifiers: tuple[str, ...] = ()) -> None:
        if end <= start:
            return
        tokens.append(
            LexicalToken(
                token_type=token_type,
                byte_range=ByteRange(start=start, end=end),
                modifiers=modifiers,
            )
        )

    while i < n:
        # Comments: //...
        if document_bytes[i:i + 2] == b"//":
            start = i
            line_end = document_bytes.find(b"\n", i)
            end = n if line_end == -1 else line_end
            _add("comment", start, end)
            i = end
            continue

        current_byte = document_bytes[i]

        # Strings: "..." or '...' (escape-aware, best-effort).
        if current_byte in (ord('"'), ord("'")):
            quote = current_byte
            start = i
            i += 1
            while i < n:
                marker = document_bytes[i]
                if marker == ord("\\"):
                    i += 2
                    continue
                i += 1
                if marker == quote:
                    break
            _add("string", start, i)
            continue

        # Operators / punctuation (minimal, high-signal set).
        if document_bytes[i:i + 2] in (b"::", b"->"):
            _add("operator", i, i + 2)
            i += 2
            continue
        if current_byte in (ord("@"), ord("?"), ord(":"), ord("=")):
            _add("operator", i, i + 1)
            i += 1
            continue

        # Numbers.
        if ord("0") <= current_byte <= ord("9"):
            start = i
            i += 1
            seen_dot = False
            while i < n:
                marker = document_bytes[i]
                if ord("0") <= marker <= ord("9"):
                    i += 1
                    continue
                if marker == ord(".") and not seen_dot:
                    seen_dot = True
                    i += 1
                    continue
                break
            _add("number", start, i)
            continue

        # Identifiers (keywords/modifiers only).
        if _is_ident_start(current_byte):
            start = i
            i += 1
            while i < n and _is_ident_part(document_bytes[i]):
                i += 1
            word = document_bytes[start:i].decode("utf-8", errors="replace")
            normalized = word.lower()
            if normalized in _AWARE_MODIFIERS:
                _add("modifier", start, i, _AWARE_KEYWORD_MODIFIERS.get(normalized, ()))
            elif normalized in _AWARE_KEYWORDS:
                _add("keyword", start, i, _AWARE_KEYWORD_MODIFIERS.get(normalized, ()))
            continue

        i += 1

    return tokens


def collect_aware_lexical_tokens(*, collector: SemanticTokenCollector) -> None:
    if collector.context.workspace_language != CodeLanguage.aware:
        return

    for token in iter_aware_lexical_tokens(document_bytes=collector.document_bytes):
        collector.add_token_range(
            byte_range=token.byte_range,
            token_type_name=token.token_type,
            modifier_names=token.modifiers,
        )
