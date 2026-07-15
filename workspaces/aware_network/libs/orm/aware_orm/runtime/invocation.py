"""In-process function invocation interface for canonical ORM facades.

This module defines a *runtime-owned* invocation surface that generated ORM
facade methods can call without importing the runtime package directly.

Contract:
- Generated methods call `invoke_instance(...)` / `invoke_constructor(...)`.
- A runtime (e.g. `aware_runtime`) installs an InvocationProvider in a
  ContextVar for the duration of a top-level FunctionCall execution.
- If no provider is set, invocation is a hard error (callers must go through
  the API/network boundary instead of calling facades directly).
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any, Mapping, Protocol, runtime_checkable

from pydantic import BaseModel


from aware_orm.models.orm_model import ORMModel


@runtime_checkable
class InvocationProvider(Protocol):
    async def invoke_instance(self, *, orm_model: ORMModel, function_name: str, payload: Mapping[str, Any]) -> Any:
        """Invoke an instance function on an ORM model."""

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        """Invoke a constructor function on an ORM class."""


_PROVIDER: ContextVar[InvocationProvider | None] = ContextVar("aware_orm_invocation_provider", default=None)


def set_invocation_provider(
    provider: InvocationProvider,
) -> Token[InvocationProvider | None]:
    """Set the invocation provider for the current context."""
    return _PROVIDER.set(provider)


def reset_invocation_provider(token: Token[InvocationProvider | None]) -> None:
    """Reset the invocation provider to a previous token."""
    _PROVIDER.reset(token)


def has_invocation_provider() -> bool:
    """Return whether ORM facade calls can resolve in the current context."""
    return _PROVIDER.get() is not None


def _require_provider() -> InvocationProvider:
    provider = _PROVIDER.get()
    if provider is None:
        raise RuntimeError(
            "No invocation provider set. ORM function facades cannot be called directly; "
            "use the API/network boundary (InvokeFunctionRequest) or run inside a runtime execution scope."
        )
    return provider


def _normalize_payload(payload: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    if isinstance(payload, BaseModel):  # type: ignore[arg-type]
        return payload.model_dump()
    # v0 envelope for primitive payloads.
    return {"value": payload}


async def invoke_instance(*, orm_model: ORMModel, function_name: str, payload: Mapping[str, Any] | Any) -> Any:
    """Invoke a function on an ORM instance via the current provider."""
    provider = _require_provider()
    return await provider.invoke_instance(
        orm_model=orm_model,
        function_name=function_name,
        payload=_normalize_payload(payload),
    )


async def invoke_constructor(*, orm_class: type[ORMModel], function_name: str, payload: Mapping[str, Any] | Any) -> Any:
    """Invoke a constructor function on an ORM class via the current provider."""
    provider = _require_provider()
    return await provider.invoke_constructor(
        orm_class=orm_class,
        function_name=function_name,
        payload=_normalize_payload(payload),
    )


__all__ = [
    "InvocationProvider",
    "has_invocation_provider",
    "invoke_constructor",
    "invoke_instance",
    "reset_invocation_provider",
    "set_invocation_provider",
]
