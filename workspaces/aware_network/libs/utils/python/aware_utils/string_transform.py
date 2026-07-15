"""String transformation helpers."""

from __future__ import annotations

import re
from typing import Any, Optional

_FK_SUFFIXES = ("_id", "_ids", "_uuid", "_uuids", "_fk", "_fks")


def to_snake_case(name: str) -> str:
    """Convert CamelCase/PascalCase to snake_case, handling acronyms."""
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def to_camel_case(name: str) -> str:
    words = name.split("_")
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_pascal_case(name: str) -> str:
    if not name:
        return ""
    if "_" not in name:
        return name[0].upper() + name[1:]
    return "".join(word.capitalize() for word in name.split("_"))


def normalize_identifier(name: Any) -> str:
    """
    Trim leading/trailing whitespace from identifier-like strings.

    Non-string inputs fall back to string conversion; None returns empty string.
    """
    if not isinstance(name, str):
        return str(name).strip()
    value = name.strip()
    # Remove balanced wrapping parentheses (commonly introduced by line-wrapped annotations)
    while value.startswith("(") and value.endswith(")") and len(value) > 1:
        inner = value[1:-1].strip()
        if inner == value:
            break
        value = inner
    return value


def strip_fk_suffix(name: Optional[str]) -> Optional[str]:
    """Trim common foreign-key suffixes like _id, _uuid, _fk."""
    if not isinstance(name, str) or not name:
        return name
    lower = name.lower()
    for suffix in _FK_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return name


def pluralize(name: str) -> str:
    """Return a simple English plural for identifiers."""
    if not isinstance(name, str) or not name:
        return name
    lower = name.lower()
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    if lower.endswith("y") and len(name) > 1 and lower[-2] not in "aeiou":
        return name[:-1] + "ies"
    return name + "s"


def singularize(name: str) -> str:
    """Return a simple English singular form."""
    if not isinstance(name, str) or not name:
        return name
    lower = name.lower()
    if lower.endswith("ies") and len(name) > 3 and lower[-4] not in "aeiou":
        return name[:-3] + "y"
    if lower.endswith("ses"):
        if len(name) > 3 and lower[-4] != "s":
            return name[:-1]
        return name[:-2]
    for ending in ("xes", "zes", "ches", "shes"):
        if lower.endswith(ending):
            return name[:-2]
    if lower.endswith("s") and not lower.endswith("ss"):
        return name[:-1]
    return name


__all__ = [
    "pluralize",
    "normalize_identifier",
    "singularize",
    "strip_fk_suffix",
    "to_snake_case",
    "to_camel_case",
    "to_pascal_case",
]
