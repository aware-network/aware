"""Canonical policy for Aware function verbs."""

from __future__ import annotations

from collections.abc import Iterable

KNOWN_FUNCTION_VERBS: set[str] = {"construct"}


def normalize_function_verb(verb: str | None) -> str | None:
    """Normalize verb tokens to a canonical, lowercase form."""

    if verb is None:
        return None
    normalized = verb.strip().lower()
    return normalized or None


def validate_function_verb(verb: str | None, *, context: str | None = None) -> str | None:
    """Validate function verbs against the canonical allowlist."""

    normalized = normalize_function_verb(verb)
    if normalized is None:
        return None
    if normalized not in KNOWN_FUNCTION_VERBS:
        msg = f"Unknown function verb {verb!r}"
        if context:
            msg += f" for {context}"
        raise ValueError(msg)
    return normalized


def is_constructor_verb(verb: str | None) -> bool:
    """Return True when the verb denotes a constructor function."""

    return normalize_function_verb(verb) == "construct"


def is_known_function_verb(verb: str | None) -> bool:
    """Return True if the verb is within the canonical allowlist."""

    normalized = normalize_function_verb(verb)
    return normalized in KNOWN_FUNCTION_VERBS if normalized is not None else True


def iter_known_function_verbs() -> Iterable[str]:
    """Return the canonical set of allowed function verbs."""

    return tuple(sorted(KNOWN_FUNCTION_VERBS))


__all__ = [
    "KNOWN_FUNCTION_VERBS",
    "is_constructor_verb",
    "is_known_function_verb",
    "iter_known_function_verbs",
    "normalize_function_verb",
    "validate_function_verb",
]
