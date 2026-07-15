"""Meta-owned helpers for legacy generated handler manifests.

The checked-in ``handlers._generated.handlers`` modules are manifest snapshots.
They declare ``AWARE_HANDLERS`` rows and wrapper callables, but active handler
execution is owned by Meta ``meta_handlers`` modules.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol

from aware_orm.models.orm_model import ORMModel


class HandlerContext(Protocol):
    """Type-only context placeholder for legacy generated wrapper signatures."""


def _class_fqn(value: type[ORMModel] | str) -> str:
    if isinstance(value, str):
        out = value.strip()
        if not out:
            raise ValueError("class_fqn must be a non-empty string")
        return out
    return f"{value.__module__}.{value.__name__}"


def _callable_fqn(fn: Callable[..., Any]) -> str:
    module = getattr(fn, "__module__", None)
    name = getattr(fn, "__name__", None)
    if not module or not name:
        raise ValueError(f"Handler callable must have __module__ and __name__: {fn!r}")
    return f"{module}.{name}"


def instance(
    orm_class: type[ORMModel] | str,
    function_name: str,
    handler: Callable[..., Any],
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "call_target": "instance",
        "class_fqn": _class_fqn(orm_class),
        "function_name": str(function_name),
        "handler_fqn": _callable_fqn(handler),
    }
    if extra:
        entry.update(dict(extra))
    return entry


def constructor(
    orm_class: type[ORMModel] | str,
    function_name: str,
    handler: Callable[..., Any],
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "call_target": "constructor",
        "class_fqn": _class_fqn(orm_class),
        "function_name": str(function_name),
        "handler_fqn": _callable_fqn(handler),
    }
    if extra:
        entry.update(dict(extra))
    return entry


def opg_constructor(
    orm_class: type[ORMModel] | str,
    function_name: str,
    handler: Callable[..., Any],
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return constructor(orm_class, function_name, handler, extra=extra)


__all__ = ["HandlerContext", "constructor", "instance", "opg_constructor"]
