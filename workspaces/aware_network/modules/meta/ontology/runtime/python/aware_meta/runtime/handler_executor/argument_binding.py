from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import cast

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphBoundArguments,
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
)


class MetaGraphArgumentBindingError(RuntimeError):
    """Raised when Meta cannot bind invocation arguments for execution."""


@dataclass(frozen=True, slots=True)
class MetaGraphArgumentBinderPhase:
    """Bind Meta invocation JSON containers without runtime harness decoding."""

    async def bind_arguments(
        self,
        request: MetaGraphHandlerExecutionRequest,
        pre_state: MetaGraphPreState,
    ) -> MetaGraphBoundArguments:
        return build_meta_graph_bound_arguments(
            request=request,
            pre_state=pre_state,
        )


def build_meta_graph_bound_arguments(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
) -> MetaGraphBoundArguments:
    execution_plan = request.execution_plan
    if pre_state.execution_plan is not execution_plan:
        raise MetaGraphArgumentBindingError(
            "Meta argument binding requires pre-state from the same execution plan."
        )

    return MetaGraphBoundArguments(
        execution_plan=execution_plan,
        positional=_coerce_json_array(request.request.args, path="args"),
        keyword=_coerce_json_object(request.request.kwargs, path="kwargs"),
    )


def _coerce_json_array(value: object, *, path: str) -> JsonArray:
    if not isinstance(value, list):
        raise MetaGraphArgumentBindingError(
            f"Meta invocation {path} must be a JSON array."
        )
    return JsonArray(
        [_coerce_json_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    )


def _coerce_json_object(value: object, *, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise MetaGraphArgumentBindingError(
            f"Meta invocation {path} must be a JSON object."
        )
    result = JsonObject()
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str):
            raise MetaGraphArgumentBindingError(
                f"Meta invocation {path} contains a non-string key."
            )
        result[raw_key] = _coerce_json_value(
            raw_value,
            path=f"{path}.{raw_key}" if raw_key else path,
        )
    return result


def _coerce_json_value(value: object, *, path: str) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return cast(JsonValue, value)
    if isinstance(value, float):
        if not isfinite(value):
            raise MetaGraphArgumentBindingError(
                f"Meta invocation {path} contains a non-finite number."
            )
        return cast(JsonValue, value)
    if isinstance(value, list):
        return _coerce_json_array(value, path=path)
    if isinstance(value, dict):
        return _coerce_json_object(value, path=path)
    raise MetaGraphArgumentBindingError(
        f"Meta invocation {path} contains a non-JSON value: {type(value).__name__}."
    )


__all__ = [
    "build_meta_graph_bound_arguments",
    "MetaGraphArgumentBinderPhase",
    "MetaGraphArgumentBindingError",
]
