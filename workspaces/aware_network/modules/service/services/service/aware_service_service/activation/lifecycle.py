from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
import inspect
from typing import Any

from aware_service_service.activation.registry import (
    ActivatedServiceImplementationPackage,
)


PackageLifecycleContext = Callable[
    [ActivatedServiceImplementationPackage],
    AbstractContextManager[object],
]


async def start_activated_service_lifecycle_handlers(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    environment_api_client: object,
    package_context: PackageLifecycleContext,
) -> tuple[object, ...]:
    started_handlers: list[object] = []
    seen_handler_ids: set[int] = set()
    try:
        for activated in packages:
            with package_context(activated):
                prepared = getattr(activated.binding, "prepared", None)
                service_bindings = getattr(prepared, "service_bindings", {}) or {}
                for handler in service_bindings.values():
                    if id(handler) in seen_handler_ids:
                        continue
                    seen_handler_ids.add(id(handler))
                    start_service_host = getattr(
                        handler,
                        "start_service_host",
                        None,
                    )
                    if not callable(start_service_host):
                        continue
                    kwargs = (
                        {"environment_api_client": environment_api_client}
                        if _callable_accepts_keyword(
                            start_service_host,
                            "environment_api_client",
                        )
                        else {}
                    )
                    result = start_service_host(**kwargs)
                    if inspect.isawaitable(result):
                        await result
                    started_handlers.append(handler)
        return tuple(started_handlers)
    except Exception:
        await stop_started_service_lifecycle_handlers(handlers=tuple(started_handlers))
        raise


async def stop_started_service_lifecycle_handlers(
    *,
    handlers: tuple[object, ...],
) -> None:
    for handler in reversed(handlers):
        close_service_host = getattr(handler, "close_service_host", None)
        if not callable(close_service_host):
            continue
        result = close_service_host()
        if inspect.isawaitable(result):
            await result


def _callable_accepts_keyword(fn: Callable[..., Any], keyword: str) -> bool:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    parameters = signature.parameters
    if keyword in parameters:
        return True
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )


__all__ = [
    "PackageLifecycleContext",
    "start_activated_service_lifecycle_handlers",
    "stop_started_service_lifecycle_handlers",
]
