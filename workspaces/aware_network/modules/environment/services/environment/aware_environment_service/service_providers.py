from __future__ import annotations

from collections.abc import Callable


def register_plugins(register: Callable[[type], type]) -> None:
    _ = register
