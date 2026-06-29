"""Declarative handler manifest helpers for legacy Meta handler lists."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from aware_orm.models.orm_model import ORMModel


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


__all__ = ["constructor", "instance"]
