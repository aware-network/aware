from __future__ import annotations

"""Compatibility stable-id helpers for the Interface module (Python runtime).

Canonical stable-id formulas are compiler-owned and generated from:
- `workspaces/aware_network/modules/interface/ontology/structure/stable_ids.toml`

Generated module:
- `aware_interface_ontology.stable_ids`
"""

from uuid import NAMESPACE_URL, UUID, uuid5

from aware_interface_ontology.stable_ids import (  # type: ignore[import-not-found]
    NS_INTERFACE,
    stable_interface_environment_id,
    stable_interface_id,
    stable_interface_window_id,
    stable_window_id as _stable_window_id_generated,
    stable_window_layout_id,
    stable_window_layout_section_id,
)


def stable_window_key_id(*, interface_id: UUID, window_key: str) -> UUID:
    """Derive the natural Window constructor key for an Interface window key."""

    key_norm = (window_key or "").casefold().strip()
    if not key_norm:
        raise ValueError("stable_window_key_id requires non-empty window_key")
    return uuid5(NAMESPACE_URL, f"aware:window:{interface_id}:{key_norm}")


def stable_window_id(
    *,
    window_id: UUID | None = None,
    interface_id: UUID | None = None,
    window_key: str | None = None,
) -> UUID:
    """
    Canonical window id helper.

    Preferred:
    - `stable_window_id(window_id=<uuid>)` (compiler-owned constructor key rail).

    Transitional compatibility:
    - `stable_window_id(interface_id=<uuid>, window_key=<str>)`
      derives a deterministic external window UUID and then normalizes through the
      compiler-owned window formula.
    """

    if window_id is not None and interface_id is None and window_key is None:
        return _stable_window_id_generated(window_id=window_id)

    if window_id is None and interface_id is not None and window_key is not None:
        window_key_id = stable_window_key_id(interface_id=interface_id, window_key=window_key)
        return _stable_window_id_generated(window_id=window_key_id)

    raise TypeError("stable_window_id requires either `window_id` or (`interface_id` and `window_key`)")


def stable_interface_window_navigation_context_id(
    *,
    interface_window_id: UUID,
    interface_environment_id: UUID,
    environment_navigation_context_id: UUID,
) -> UUID:
    """Derive the InterfaceWindowNavigationContext association id."""

    return uuid5(
        NS_INTERFACE,
        "aware:interface_window_navigation_context:"
        f"{interface_window_id}:{interface_environment_id}:{environment_navigation_context_id}",
    )


__all__ = [
    "NS_INTERFACE",
    "stable_interface_id",
    "stable_interface_environment_id",
    "stable_window_id",
    "stable_window_key_id",
    "stable_interface_window_id",
    "stable_interface_window_navigation_context_id",
    "stable_window_layout_id",
    "stable_window_layout_section_id",
]
