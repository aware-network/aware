from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Mapping
from typing import Any, get_type_hints

from pydantic import TypeAdapter


def coerce_meta_handler_call_kwargs(
    handler: Callable[..., object],
    call_kwargs: Mapping[str, object],
) -> dict[str, object]:
    """Decode generated Meta JSON kwargs against authored handler annotations."""

    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return dict(call_kwargs)
    accepts_var_keyword = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )

    try:
        type_hints = get_type_hints(handler)
    except Exception:
        module = sys.modules.get(handler.__module__)
        globalns = dict(vars(module)) if module is not None else {}
        globalns.update(dict(getattr(handler, "__globals__", {})))
        globalns.setdefault("Any", Any)
        try:
            type_hints = get_type_hints(handler, globalns=globalns)
        except Exception:
            type_hints = {}

    coerced: dict[str, object] = {}
    for name, value in call_kwargs.items():
        parameter = signature.parameters.get(name)
        if parameter is None:
            if accepts_var_keyword:
                coerced[name] = value
            continue
        annotation = type_hints.get(name, parameter.annotation)
        if annotation is inspect.Parameter.empty or annotation is Any:
            coerced[name] = value
            continue
        coerced[name] = TypeAdapter(annotation).validate_python(value)
    return coerced


__all__ = ["coerce_meta_handler_call_kwargs"]
