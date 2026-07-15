"""Provider discovery for service-surface Economy plugins."""

from collections.abc import Callable


def register_plugins(register: Callable[[type], type]) -> None:
    _ = register
