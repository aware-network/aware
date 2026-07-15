from __future__ import annotations

import re
from typing import ClassVar

from typing_extensions import override

from aware_code.type_parser import CodeTypeParser


class SqlTypeParser(CodeTypeParser):
    """Token-level parser for SQL type text.

    Supported structural forms:
    - Arrays:
      - `T[]`
      - `ARRAY<T>`
      - `ARRAY[T]`
      - `ARRAY(T)`
    - Calls (for parametric types): `name(args)` (used for VECTOR(dim), VARCHAR(255), NUMERIC(...), etc.)

    This layer is raw-text only and must not build TypeNode or CodePrimitiveType.
    """

    _WS_RX: ClassVar[re.Pattern[str]] = re.compile(r"\s+")
    _CALL_RX: ClassVar[re.Pattern[str]] = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_ ]*)\s*\(\s*(?P<args>.*)\s*\)$")

    @override
    def strip_forward_ref_quotes(self, type_text: str) -> tuple[str, bool]:
        # SQL uses double quotes for identifiers (not forward refs); treat as non-forward.
        s = (type_text or "").strip()
        if s.startswith('"') and s.endswith('"') and len(s) >= 2:
            return s[1:-1], False
        return s, False

    @override
    def get_optional_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_classvar_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_annotated_parts(self, type_text: str) -> tuple[str, list[str]] | None:
        return None

    @override
    def get_tuple_elements(self, type_text: str) -> list[str] | None:
        return None

    @override
    def get_union_members(self, type_text: str) -> list[str] | None:
        return None

    @override
    def get_dict_kv(self, type_text: str) -> tuple[str, str] | None:
        return None

    @override
    def get_set_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_literal_inner(self, type_text: str) -> str | None:
        return None

    @override
    def get_call(self, type_text: str) -> tuple[str, str] | None:
        s = (type_text or "").strip()
        m = self._CALL_RX.match(s)
        if not m:
            return None
        name = (m.group("name") or "").strip()
        args = (m.group("args") or "").strip()
        if not name:
            return None
        # collapse internal whitespace in function/type name for stable matching (e.g. "double precision")
        name = self._WS_RX.sub(" ", name).strip().lower()
        return name, args

    # ---------------------------
    # SQL-specific helpers
    # ---------------------------
    def normalize_exact_token(self, token: str) -> str:
        """Normalize a SQL type token for exact matching.

        - Lowercase
        - Collapse whitespace
        - Strip surrounding double quotes
        - Strip parameter calls like `varchar(255)` -> `varchar` (except vector)
        """
        t = (token or "").strip()
        if not t:
            return ""
        if t.startswith('"') and t.endswith('"') and len(t) >= 2:
            t = t[1:-1]
        t = t.lower()
        t = self._WS_RX.sub(" ", t).strip()

        call = self.get_call(t)
        if call is not None:
            name, _args = call
            if name.strip().lower() != "vector":
                return name.strip().lower()
        return t

    def is_qualified_ident(self, type_text: str) -> bool:
        """Return True if text looks like schema-qualified identifier: schema.name."""
        s = (type_text or "").strip()
        # ignore quoted identifiers for now (rarely used in type names; codec handles quotes separately)
        if s.startswith('"') and s.endswith('"'):
            return False
        return "." in s

    def get_array_inner(self, type_text: str) -> str | None:
        """Extract a single array wrapper.

        - `T[]` -> `T`
        - `ARRAY<T>` -> `T`
        - `ARRAY[T]` -> `T`
        - `ARRAY(T)` -> `T`

        Returns None if not an array type.
        """
        s = (type_text or "").strip()
        if not s:
            return None

        low = s.lower()
        # bracket suffix
        if low.endswith("[]") and len(s) > 2:
            return s[:-2].strip()

        # ARRAY<...>
        if low.startswith("array<") and low.endswith(">"):
            return s[len("array<"):-1].strip()
        # ARRAY[...]
        if low.startswith("array[") and low.endswith("]"):
            return s[len("array["):-1].strip()
        # ARRAY(...)
        if low.startswith("array(") and low.endswith(")"):
            return s[len("array("):-1].strip()

        return None

    @override
    def get_list_inner(self, type_text: str) -> str | None:
        # In SQL we treat arrays as LIST.
        return self.get_array_inner(type_text)
