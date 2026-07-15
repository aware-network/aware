from aware_code.type_parser import CodeTypeParser
from typing_extensions import override


class DartTypeParser(CodeTypeParser):
    """Token-level parser for Dart type annotation text.

    Dart conventions supported here:
    - Nullable suffix: `T?`
    - Generics: `List<T>`, `Set<T>`, `Map<K, V>`

    This layer is **raw-text only** and must not build TypeNode or CodePrimitiveType.
    """

    # ---------------------------
    # Small Dart helpers
    # ---------------------------
    def _strip_nullable_suffix(self, s: str) -> tuple[str, bool]:
        s = (s or "").strip()
        if s.endswith("?") and len(s) > 1:
            return s[:-1].strip(), True
        return s, False

    def _angle_content(self, prefix: str, text: str) -> str | None:
        """Return content inside `prefix <...>` if the text matches exactly."""
        s = (text or "").strip()
        if not s.startswith(prefix):
            return None
        # Allow whitespace: `List < T >`
        after = s[len(prefix):].lstrip()
        if not (after.startswith("<") and after.endswith(">")):
            return None
        return after[1:-1].strip()

    def _split_top_level_angle(self, text: str, sep: str) -> list[str]:
        """Split by sep while respecting nesting in `<...>`."""
        s = (text or "").strip()
        if not s:
            return []
        parts: list[str] = []
        depth = 0
        last = 0
        for i, ch in enumerate(s):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth = max(0, depth - 1)
            elif ch == sep and depth == 0:
                parts.append(s[last:i].strip())
                last = i + 1
        parts.append(s[last:].strip())
        return [p for p in parts if p]

    # ---------------------------
    # CodeTypeParser contract
    # ---------------------------
    @override
    def strip_forward_ref_quotes(self, type_text: str) -> tuple[str, bool]:
        # Dart doesn't use quoted forward refs in type annotations.
        s = (type_text or "").strip()
        return s, False

    @override
    def get_optional_inner(self, type_text: str) -> str | None:
        s, is_nullable = self._strip_nullable_suffix(type_text)
        return s if is_nullable else None

    @override
    def get_classvar_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_annotated_parts(self, type_text: str) -> tuple[str, list[str]] | None:
        return None

    @override
    def get_tuple_elements(self, type_text: str) -> list[str] | None:
        # Dart 3 has Record types, but we don't support them here yet.
        return None

    @override
    def get_union_members(self, type_text: str) -> list[str] | None:
        # Dart doesn't have unions in type syntax.
        return None

    @override
    def get_dict_kv(self, type_text: str) -> tuple[str, str] | None:
        # Map<K, V>
        s, _nullable = self._strip_nullable_suffix(type_text)
        inner = self._angle_content("Map", s)
        if inner is None:
            return None
        parts = self._split_top_level_angle(inner, ",")
        if len(parts) != 2:
            return None
        return parts[0].strip(), parts[1].strip()

    @override
    def get_list_inner(self, type_text: str) -> str | None:
        # List<T>
        s, _nullable = self._strip_nullable_suffix(type_text)
        inner = self._angle_content("List", s)
        if inner is not None:
            return inner.strip()
        # Bare List
        if s.strip() == "List":
            return "dynamic"
        return None

    @override
    def get_set_inner(self, type_text: str) -> str | None:
        # Set<T>
        s, _nullable = self._strip_nullable_suffix(type_text)
        inner = self._angle_content("Set", s)
        if inner is not None:
            return inner.strip()
        # Bare Set
        if s.strip() == "Set":
            return "dynamic"
        return None

    @override
    def get_literal_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_call(self, type_text: str) -> tuple[str, str] | None:
        # Dart type annotations don't use call syntax in our supported subset.
        return None
