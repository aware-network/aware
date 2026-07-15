from __future__ import annotations

import signal
from contextlib import contextmanager
from types import FrameType
from typing import TypedDict

from aware_code.language.registry import CodeLanguagePluginRegistry
from typing_extensions import override

from aware_code.language_service.document import DocumentContext
from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.json_rpc import JsonObject


_DEFAULT_FORMAT_TIMEOUT_S = 0.25


class _LspPosition(TypedDict):
    line: int
    character: int


class _LspRange(TypedDict):
    start: _LspPosition
    end: _LspPosition


class _LspTextEdit(TypedDict):
    range: _LspRange
    newText: str


class _FormattingOptions(TypedDict, total=False):
    tabSize: int
    insertSpaces: bool


@contextmanager
def _alarm_timeout(seconds: float):
    """Best-effort wall-clock timeout for formatting.

    VS Code/Cursor can run format-on-save synchronously; formatting must never hang
    the editor. We use SIGALRM where available and fall back to no timeout on
    unsupported platforms.
    """

    if seconds <= 0:
        yield
        return

    if not hasattr(signal, "SIGALRM") or not hasattr(signal, "setitimer"):
        yield
        return

    def _handler(_signum: int, _frame: FrameType | None) -> None:  # pragma: no cover
        raise TimeoutError("format timeout")

    try:
        old_handler = signal.getsignal(signal.SIGALRM)
        _ = signal.signal(signal.SIGALRM, _handler)
        _ = signal.setitimer(signal.ITIMER_REAL, seconds)
    except Exception:
        yield
        return

    try:
        yield
    finally:
        try:
            _ = signal.setitimer(signal.ITIMER_REAL, 0)
            _ = signal.signal(signal.SIGALRM, old_handler)
        except Exception:
            pass


class FormattingMixin(ServiceMixinBase):
    @override
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @override
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @override
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    def format_document(
        self,
        *,
        uri: str,
        document_text: str,
        options: _FormattingOptions | JsonObject | None = None,
    ) -> list[_LspTextEdit]:
        """Return LSP TextEdit[] for formatting a document (v0).

        v0 policy:
        - Formatter rules live in the code language plugin (`CodeLanguagePlugin.format_source`).
        - Apply a single full-document replacement edit (simple + reliable).
        - If the language plugin doesn't support formatting or the formatter refuses
          (e.g. invalid syntax), return no edits.
        """
        if self._is_aware_config_uri(uri):
            return []
        indent_size = 4
        if options is not None:
            tab_size = options.get("tabSize")
            insert_spaces = options.get("insertSpaces")
            if insert_spaces is True and isinstance(tab_size, int) and tab_size > 0:
                indent_size = tab_size

        try:
            plugin = CodeLanguagePluginRegistry.get(self._workspace.language)
        except Exception:
            return []

        try:
            with _alarm_timeout(_DEFAULT_FORMAT_TIMEOUT_S):
                formatted = plugin.format_source(document_text, indent_size=indent_size)
        except TimeoutError:
            return []
        except Exception:
            return []
        if formatted is None:
            return []
        if formatted == document_text:
            return []

        ctx = self._document_context(uri=uri, document_text=document_text)
        end = ctx.mapper.byte_offset_to_position(len(ctx.document_bytes))
        return [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": end.line, "character": end.character},
                },
                "newText": formatted,
            }
        ]
