from __future__ import annotations

from dataclasses import dataclass, field

from aware_code.language_service.position import Utf16PositionMapper


@dataclass(frozen=True, slots=True)
class DocumentContext:
    text: str
    document_bytes: bytes
    mapper: Utf16PositionMapper


@dataclass(slots=True)
class DocumentContextCache:
    _by_uri: dict[str, tuple[int, DocumentContext]] = field(default_factory=dict)

    def get(self, *, uri: str, version: int | None, text: str) -> DocumentContext:
        if version is None:
            doc_bytes = text.encode("utf-8")
            return DocumentContext(
                text=text,
                document_bytes=doc_bytes,
                mapper=Utf16PositionMapper(text=text),
            )

        cached = self._by_uri.get(uri)
        if cached is not None and cached[0] == version and cached[1].text == text:
            return cached[1]

        doc_bytes = text.encode("utf-8")
        ctx = DocumentContext(text=text, document_bytes=doc_bytes, mapper=Utf16PositionMapper(text=text))
        self._by_uri[uri] = (version, ctx)
        return ctx

    def evict(self, *, uri: str) -> None:
        _ = self._by_uri.pop(uri, None)

    def clear(self) -> None:
        self._by_uri.clear()
