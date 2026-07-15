import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class AwareTupleEntry:
    label: str | None
    type_text: str


class AwareTypeParser:
    """Token-level parser for Aware type text.

    This layer is intentionally **raw-text only**:
    - It does not construct TypeNode
    - It does not construct CodePrimitiveType
    - It only answers structural questions and extracts substrings
    """

    _PARAM_RX: ClassVar[re.Pattern[str]] = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*)\((?P<params>[^)]*)\)$")

    def strip_trailing_field_modifiers(self, text: str) -> str:
        """Strip trailing field modifiers after the type token.

        Examples:
        - `AnalyticMetric[] @AnalyticExecutionMetric many` -> `AnalyticMetric[]`
        - `(User, Post) @SomeEdge` -> `(User, Post)`
        """
        s = (text or "").strip()
        if not s:
            return s
        depth = 0
        bracket_depth = 0
        for idx, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth = max(0, bracket_depth - 1)
            elif depth == 0 and bracket_depth == 0 and ch.isspace():
                return s[:idx].strip()
        return s

    def strip_edge_annotation(self, text: str) -> str:
        """Remove trailing edge annotations (e.g., `Type[] @Edge`)."""
        s = (text or "").strip()
        if "@" not in s:
            return s
        return s.split("@", 1)[0].strip()

    def split_top_level_commas(self, text: str) -> list[str]:
        """Split by comma while respecting nested parentheses.

        This prevents splitting inside parametric types like Vector(1536) or tuples.
        """
        s = (text or "").strip()
        if not s:
            return []
        parts: list[str] = []
        current: list[str] = []
        depth = 0
        bracket_depth = 0
        for ch in s:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth = max(0, bracket_depth - 1)
            if ch == "," and depth == 0 and bracket_depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
            current.append(ch)
        if current:
            parts.append("".join(current).strip())
        return [p for p in parts if p]

    def split_named_tuple_entry(self, text: str) -> AwareTupleEntry:
        """Parse a tuple entry which may be labeled: `name: Type`."""
        s = (text or "").strip()
        if not s:
            return AwareTupleEntry(label=None, type_text=s)
        depth = 0
        bracket_depth = 0
        for idx, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth = max(0, bracket_depth - 1)
            elif ch == ":" and depth == 0 and bracket_depth == 0:
                label = s[:idx].strip()
                remainder = s[idx + 1:].strip()
                if label and remainder:
                    return AwareTupleEntry(label=label, type_text=remainder)
                break
        return AwareTupleEntry(label=None, type_text=s)

    def get_optional_suffix_inner(self, type_text: str) -> str | None:
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text))
        if s.endswith("?") and len(s) > 1:
            return s[:-1].strip()
        return None

    def get_array_suffix_inner(self, type_text: str) -> str | None:
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text))
        if s.endswith("[]") and len(s) > 2:
            return s[:-2].strip()
        return None

    def is_parametric(self, type_text: str) -> bool:
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text))
        return bool(self._PARAM_RX.match(s))

    def get_parametric_call(self, type_text: str) -> tuple[str, str] | None:
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text))
        m = self._PARAM_RX.match(s)
        if not m:
            return None
        name = (m.group("label") or "").strip()
        params = (m.group("params") or "").strip()
        if not name:
            return None
        return name, params

    def get_dict_kv(self, type_text: str) -> tuple[str, str] | None:
        """Parse Dict[K, V] and return (key_text, value_text)."""
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text)).strip()
        if not s:
            return None
        low = s.lower()
        if not low.startswith("dict[") or not s.endswith("]"):
            return None
        inner = s[s.find("[") + 1:-1].strip()
        if not inner:
            return None
        parts = self.split_top_level_commas(inner)
        if len(parts) < 2:
            return None
        key_text = parts[0].strip()
        value_text = parts[1].strip()
        if not key_text or not value_text:
            return None
        return key_text, value_text

    def get_tuple_entries(self, type_text: str) -> list[AwareTupleEntry] | None:
        s = self.strip_trailing_field_modifiers(type_text)
        s = s.strip()
        if not (s.startswith("(") and s.endswith(")")):
            return None
        inner = s[1:-1].strip()
        parts = self.split_top_level_commas(inner)
        if len(parts) <= 1:
            return None
        entries: list[AwareTupleEntry] = []
        for part in parts:
            entries.append(self.split_named_tuple_entry(part))
        return entries

    def enum_ident(self, type_text: str) -> str:
        """Strip Aware decorations to expose the semantic type identifier.

        - Foo? -> Foo
        - Foo[] -> Foo
        - Vector(1536) -> Vector
        """
        s = self.strip_edge_annotation(self.strip_trailing_field_modifiers(type_text)).strip()
        if s.endswith("?"):
            s = s[:-1].strip()
        if s.endswith("[]"):
            s = s[:-2].strip()
        if self.get_dict_kv(s) is not None:
            return "Dict"
        call = self.get_parametric_call(s)
        if call is not None:
            name, _params = call
            return name
        return s
