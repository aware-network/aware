"""
Session autobind control.

The ORM can automatically bind newly constructed models to the *current*
SessionContext. This is convenient for runtime code, but it is harmful for
deterministic graph construction:

- building large in-memory graphs can unintentionally populate the global identity map
- deep copies of those graphs can become O(size_of_identity_map) due to private session refs

This module provides a small ContextVar guard so callers (kernel-meta builders,
diff/apply pipelines, tests) can explicitly disable automatic session binding
for pure in-memory work.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_autobind_enabled: ContextVar[bool] = ContextVar("aware_orm_autobind_enabled", default=True)


def is_autobind_enabled() -> bool:
    return _autobind_enabled.get()


@contextmanager
def disable_autobind() -> Iterator[None]:
    token = _autobind_enabled.set(False)
    try:
        yield
    finally:
        _autobind_enabled.reset(token)


__all__ = [
    "disable_autobind",
    "is_autobind_enabled",
]
