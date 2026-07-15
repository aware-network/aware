"""Shared bootstrap context for generated package bootstrapping.

This module exists to avoid circular imports between:
- `package_bootstrap` (imports modules + rebuilds Pydantic models)
- `package_install` (installs embedded `_aware/*` artifacts)

During a dependency bootstrap, we must avoid running installs for dependencies
until the full dependency closure has been imported and rebuilt, otherwise
install-time imports can re-enter the bootstrap stack and create cycles.
"""

from __future__ import annotations

from contextvars import ContextVar, Token


_BOOTSTRAP_ROOT: ContextVar[str | None] = ContextVar("aware_orm_bootstrap_root", default=None)

# Deferred installs keyed by the root package that initiated the bootstrap.
_DEFERRED_INSTALLS: dict[str, set[str]] = {}


def get_bootstrap_root() -> str | None:
    """Return the active bootstrap root package, if any."""

    return _BOOTSTRAP_ROOT.get()


def set_bootstrap_root(root_package: str) -> Token[str | None]:
    """Set the active bootstrap root package for the current context."""

    return _BOOTSTRAP_ROOT.set(root_package)


def reset_bootstrap_root(token: Token[str | None]) -> None:
    """Reset the bootstrap root package to a previous token."""

    _BOOTSTRAP_ROOT.reset(token)


def defer_install(*, root_package: str, package_prefix: str) -> None:
    """Record that `package_prefix` should be installed after `root_package` finishes bootstrapping."""

    _DEFERRED_INSTALLS.setdefault(root_package, set()).add(package_prefix)


def pop_deferred_installs(root_package: str) -> set[str]:
    """Return and clear deferred installs for a root package."""

    return _DEFERRED_INSTALLS.pop(root_package, set())


__all__ = [
    "defer_install",
    "get_bootstrap_root",
    "pop_deferred_installs",
    "reset_bootstrap_root",
    "set_bootstrap_root",
]
