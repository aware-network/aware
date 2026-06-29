from __future__ import annotations

import re
from typing import ClassVar
from typing_extensions import override

from aware_code.type_parser import CodeTypeParser


class PythonTypeParser(CodeTypeParser):
    """Token-level parser for Python type annotation text.

    This parser:
    - knows only Python *syntax* for wrappers (Optional, Union, list/dict/set, Annotated, Literal, ClassVar)
    - does not build TypeNode trees
    - does not construct CodePrimitiveType models
    """

    _CALL_RX: ClassVar[re.Pattern[str]] = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(\s*(?P<args>.*)\s*\)$")

    @override
    def strip_forward_ref_quotes(self, type_text: str) -> tuple[str, bool]:
        s = (type_text or "").strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1], True
        return s, False

    @override
    def get_optional_inner(self, type_text: str) -> str | None:
        s = (type_text or "").strip()
        inner = self.bracket_content("Optional[", s)
        if inner is not None:
            return inner.strip()
        inner = self.bracket_content("typing.Optional[", s)
        if inner is not None:
            return inner.strip()
        return None

    @override
    def get_classvar_inner(self, type_text: str) -> str | None:
        s = (type_text or "").strip()
        inner = self.bracket_content("ClassVar[", s)
        if inner is not None:
            return inner.strip()
        inner = self.bracket_content("typing.ClassVar[", s)
        if inner is not None:
            return inner.strip()
        return None

    @override
    def get_annotated_parts(self, type_text: str) -> tuple[str, list[str]] | None:
        s = (type_text or "").strip()
        inner = self.bracket_content("Annotated[", s) or self.bracket_content("typing.Annotated[", s)
        if inner is None:
            return None
        parts = self.split_top_level(inner, ",") if inner else []
        base = (parts[0].strip() if parts else "Any") or "Any"
        metas = [p.strip() for p in parts[1:] if p.strip()]
        return base, metas

    @override
    def get_tuple_elements(self, type_text: str) -> list[str] | None:
        s = (type_text or "").strip()
        inner = (
            self.bracket_content("tuple[", s)
            or self.bracket_content("Tuple[", s)
            or self.bracket_content("typing.Tuple[", s)
        )
        if inner is None:
            return None
        elems = self.split_top_level(inner, ",") if inner else []
        return [e for e in (x.strip() for x in elems) if e]

    @override
    def get_union_members(self, type_text: str) -> list[str] | None:
        s = (type_text or "").strip()
        inner = self.bracket_content("Union[", s) or self.bracket_content("typing.Union[", s)
        if inner is not None:
            members = self.split_top_level(inner, ",") if inner else []
            return [m for m in (x.strip() for x in members) if m]
        if self.has_top_level_bar(s):
            members = self.split_top_level(s, "|")
            return [m for m in (x.strip() for x in members) if m]
        return None

    def is_union_bracket_syntax(self, type_text: str) -> bool:
        """True for Union[...] / typing.Union[...] syntax (not the `A | B` form)."""
        s = (type_text or "").strip()
        return self.bracket_content("Union[", s) is not None or self.bracket_content("typing.Union[", s) is not None

    @override
    def get_dict_kv(self, type_text: str) -> tuple[str, str] | None:
        s = (type_text or "").strip()
        inner = (
            self.bracket_content("dict[", s)
            or self.bracket_content("Dict[", s)
            or self.bracket_content("typing.Dict[", s)
        )
        if inner is None:
            return None
        kv = self.split_top_level(inner, ",") if inner else []
        key_s = kv[0].strip() if len(kv) > 0 else "Any"
        val_s = kv[1].strip() if len(kv) > 1 else "Any"
        return key_s or "Any", val_s or "Any"

    @override
    def get_list_inner(self, type_text: str) -> str | None:
        s = (type_text or "").strip()
        list_prefixes = [
            "List[",
            "list[",
            "typing.List[",
            "Sequence[",
            "MutableSequence[",
            "typing.Sequence[",
            "typing.MutableSequence[",
        ]
        for pref in list_prefixes:
            inner = self.bracket_content(pref, s)
            if inner is not None:
                return inner.strip() or "Any"
        # Rare "Type[]" suffix
        if s.endswith("[]") and len(s) > 2:
            return s[:-2].strip() or "Any"
        return None

    @override
    def get_set_inner(self, type_text: str) -> str | None:
        s = (type_text or "").strip()
        set_prefixes = [
            "Set[",
            "set[",
            "typing.Set[",
            "MutableSet[",
            "typing.MutableSet[",
            "frozenset[",
            "typing.FrozenSet[",
        ]
        for pref in set_prefixes:
            inner = self.bracket_content(pref, s)
            if inner is not None:
                return inner.strip() or "Any"
        return None

    @override
    def get_literal_inner(self, type_text: str) -> str | None:
        s = (type_text or "").strip()
        inner = self.bracket_content("Literal[", s) or self.bracket_content("typing.Literal[", s)
        if inner is not None:
            return inner.strip()
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
        return name, args

    # -------------------------
    # Small token helpers
    # -------------------------
    def get_vector_dim_meta(self, meta_texts: list[str]) -> int | None:
        """Extract VectorDim(n) from Annotated metas, if present."""
        for m in meta_texts:
            mm = re.match(r"^VectorDim\s*\(\s*(\d+)\s*\)$", (m or "").strip())
            if mm:
                try:
                    return int(mm.group(1))
                except Exception:
                    return None
        return None
