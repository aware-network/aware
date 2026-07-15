from __future__ import annotations

from abc import ABC, abstractmethod


class CodeTypeParser(ABC):
    """Token-level parser for language-specific type annotation text.

    This layer is intentionally **raw-text only**:
    - It must not construct semantic models (no TypeNode, no CodePrimitiveType).
    - It provides structural *questions* and *extractions* for higher layers.
    """

    # ---------------------------
    # Generic helpers (shared)
    # ---------------------------
    def split_top_level(self, text: str, sep: str) -> list[str]:
        """Split by `sep` while respecting bracket depth for `[...]`."""
        parts: list[str] = []
        depth = 0
        last = 0
        for i, ch in enumerate(text):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == sep and depth == 0:
                parts.append(text[last:i].strip())
                last = i + 1
        parts.append(text[last:].strip())
        return parts

    def bracket_content(self, prefix: str, text: str) -> str | None:
        """Return the content inside `prefix ... ]` if it matches."""
        if not text.startswith(prefix):
            return None
        if not text.endswith("]"):
            return None
        return text[len(prefix) : -1]

    def has_top_level_bar(self, text: str) -> bool:
        """Return True if `|` exists at top-level (bracket-depth aware)."""
        depth = 0
        for ch in text:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "|" and depth == 0:
                return True
        return False

    # ---------------------------
    # Language-specific extractors
    # ---------------------------
    @abstractmethod
    def strip_forward_ref_quotes(self, type_text: str) -> tuple[str, bool]:
        """Return (unquoted_text, is_forward_ref)."""

    @abstractmethod
    def get_optional_inner(self, type_text: str) -> str | None:
        """Return inner text for Optional[T] if present, else None."""

    @abstractmethod
    def get_classvar_inner(self, type_text: str) -> str | None:
        """Return inner text for ClassVar[T] if present, else None."""

    @abstractmethod
    def get_annotated_parts(self, type_text: str) -> tuple[str, list[str]] | None:
        """Return (base_text, meta_texts) for Annotated[Base, ...] if present."""

    @abstractmethod
    def get_tuple_elements(self, type_text: str) -> list[str] | None:
        """Return element texts for tuple[T1, T2, ...] if present."""

    @abstractmethod
    def get_union_members(self, type_text: str) -> list[str] | None:
        """Return member texts for Union[T1, T2] or T1 | T2 if present."""

    @abstractmethod
    def get_dict_kv(self, type_text: str) -> tuple[str, str] | None:
        """Return (key_text, value_text) for dict[K, V] if present."""

    @abstractmethod
    def get_list_inner(self, type_text: str) -> str | None:
        """Return inner text for list[T]/List[T]/Sequence[T] if present."""

    @abstractmethod
    def get_set_inner(self, type_text: str) -> str | None:
        """Return inner text for set[T]/Set[T] if present."""

    @abstractmethod
    def get_literal_inner(self, type_text: str) -> str | None:
        """Return inner raw content for Literal[...] if present."""

    @abstractmethod
    def get_call(self, type_text: str) -> tuple[str, str] | None:
        """Return (callee, raw_args) for Call(args) if present (single-level)."""
