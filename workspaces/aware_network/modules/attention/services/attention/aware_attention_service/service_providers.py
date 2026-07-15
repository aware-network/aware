"""Provider discovery for service-surface attention plugins."""

from collections.abc import Callable


def register_plugins(register: Callable[[type], type]) -> None:
    _ = register
