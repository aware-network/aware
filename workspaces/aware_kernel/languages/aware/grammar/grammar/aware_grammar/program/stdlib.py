from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

# NOTE:
# This module is intentionally pure and importable from tooling/executors.
# Do not import runtime handlers, ORM models, or workspace-specific utilities.
#
# Stable-id ownership:
# - This stdlib may include small *generic* UUIDv5 helpers (`stable.ns_url`, `stable.uuid5`).
# - Module-owned stable-id formulas must live in `modules/<module>/structure/ontology/stable_ids.toml`
#   and be resolved by executors from compiler-emitted stable-id libraries.


# ------------------------------------------------------------------
# Generic stable-id helpers (program stdlib)
# ------------------------------------------------------------------


def stable_ns_url(*, url: str) -> UUID:
    """Derive a UUID namespace from a stable URL string (UUIDv5 over NAMESPACE_URL)."""

    normalized = (url or "").strip()
    if not normalized:
        raise ValueError("stable_ns_url requires url")
    return uuid5(NAMESPACE_URL, normalized)


def _stable_key_from_parts(parts: list[object], *, sep: str) -> str:
    rendered: list[str] = []
    for part in parts:
        if part is None:
            rendered.append("null")
        elif isinstance(part, bool):
            rendered.append("true" if part else "false")
        else:
            rendered.append(str(part))
    key = sep.join(rendered).strip()
    if not key:
        raise ValueError("stable_uuid5 requires non-empty key parts")
    return key


def stable_uuid5(
    *,
    namespace: UUID | str,
    key: str | None = None,
    parts: list[object] | None = None,
    sep: str = ":",
) -> UUID:
    """Deterministically derive a UUID from (namespace, key) using UUIDv5.

    v0 usage:
    - `stable.uuid5(namespace=<uuid>, key="a:b:c")`
    - `stable.uuid5(namespace=<uuid>, parts=["a", "b", "c"])`
    """

    ns = namespace if isinstance(namespace, UUID) else UUID(str(namespace))

    if parts is not None:
        if key is not None:
            raise ValueError("stable_uuid5 does not allow both key and parts")
        return uuid5(ns, _stable_key_from_parts(list(parts), sep=str(sep)))

    k = (key or "").strip()
    if not k:
        raise ValueError("stable_uuid5 requires key or parts")
    return uuid5(ns, k)


# ------------------------------------------------------------------
__all__ = [
    "stable_ns_url",
    "stable_uuid5",
]
