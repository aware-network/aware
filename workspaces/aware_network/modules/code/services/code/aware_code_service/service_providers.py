from __future__ import annotations


def register_plugins(register):
    """Register Service host plugins.

    Code v0 is a service-protocol binding package and does not add standalone
    host plugins.
    """

    _ = register
    return ()


__all__ = [
    "register_plugins",
]
