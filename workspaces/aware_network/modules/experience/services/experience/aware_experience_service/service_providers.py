"""Provider discovery for service-surface Experience plugins."""

from collections.abc import Callable


def register_plugins(register: Callable[[type], type]) -> None:
    _ = register
