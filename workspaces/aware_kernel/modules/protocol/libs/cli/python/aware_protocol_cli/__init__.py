from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke the CLI without preloading its executable module."""

    from .main import main as invoke

    return invoke(argv)


__all__ = ["main"]
