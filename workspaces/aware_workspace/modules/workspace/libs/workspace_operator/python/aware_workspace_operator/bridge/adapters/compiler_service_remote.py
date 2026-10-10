"""Remote compiler session adapter over CompilerServiceOperation payloads."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from aware_workspace_operator.bridge.interfaces import CompilerSessionPort
from aware_workspace_operator.bridge.models import CompilerOperationResult

CompilerServiceRequestFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class CompilerServiceRemoteAdapter(CompilerSessionPort):
    """Bridge adapter that speaks CompilerServiceOperation-compatible dictionaries."""

    def __init__(self, *, request_fn: CompilerServiceRequestFn):
        self._request_fn = request_fn

    async def open_session(
        self,
        *,
        repo_root: str,
        lane: str,
        language_id: str,
        focus_uri: str | None = None,
        session_id: UUID | None = None,
    ) -> CompilerOperationResult:
        payload = {
            "service": "compiler",
            "operation": "open_session",
            "repo_root": repo_root,
            "lane": lane,
            "language_id": language_id,
            "focus_uri": focus_uri,
            "session_id": str(session_id) if session_id is not None else None,
        }
        return await self._call(payload=payload)

    async def apply_code_package_delta(
        self,
        *,
        session_id: UUID,
        code_package_delta: dict[str, Any],
        focus_uri: str | None = None,
    ) -> CompilerOperationResult:
        payload = {
            "service": "compiler",
            "operation": "apply_code_package_delta",
            "session_id": str(session_id),
            "code_package_delta": code_package_delta,
            "focus_uri": focus_uri,
        }
        return await self._call(payload=payload)

    async def get_object_config_graph_delta(
        self,
        *,
        session_id: UUID,
        update_id: int | None = None,
        focus_uri: str | None = None,
    ) -> CompilerOperationResult:
        payload = {
            "service": "compiler",
            "operation": "get_object_config_graph_delta",
            "session_id": str(session_id),
            "update_id": update_id,
            "focus_uri": focus_uri,
        }
        return await self._call(payload=payload)

    async def close_session(
        self,
        *,
        session_id: UUID,
        repo_root: str | None = None,
        lane: str | None = None,
        language_id: str | None = None,
        focus_uri: str | None = None,
    ) -> CompilerOperationResult:
        payload = {
            "service": "compiler",
            "operation": "close_session",
            "session_id": str(session_id),
            "repo_root": repo_root,
            "lane": lane,
            "language_id": language_id,
            "focus_uri": focus_uri,
        }
        return await self._call(payload=payload)

    async def _call(self, *, payload: dict[str, Any]) -> CompilerOperationResult:
        response = await self._request_fn(payload)
        service_operation = _extract_service_operation_payload(response=response)
        if service_operation is None:
            raise ValueError(
                "Compiler service response did not include a service_operation payload."
            )
        normalized = dict(service_operation)
        normalized.pop("service", None)
        allowed_fields = set(CompilerOperationResult.model_fields.keys())
        filtered = {
            key: value for key, value in normalized.items() if key in allowed_fields
        }
        return CompilerOperationResult.model_validate(filtered)


def _extract_service_operation_payload(
    *, response: dict[str, Any]
) -> dict[str, Any] | None:
    if _is_compiler_service_operation(response):
        return response

    service_operation = response.get("service_operation")
    if _is_compiler_service_operation(service_operation):
        return service_operation

    nested_response = response.get("response")
    if isinstance(nested_response, dict):
        payload = _extract_service_operation_payload(response=nested_response)
        if payload is not None:
            return payload

    environment_operation = response.get("environment_operation")
    if isinstance(environment_operation, dict):
        payload = _extract_service_operation_payload(response=environment_operation)
        if payload is not None:
            return payload

    return None


def _is_compiler_service_operation(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("service") == "compiler"
        and isinstance(value.get("operation"), str)
    )


__all__ = ["CompilerServiceRemoteAdapter", "CompilerServiceRequestFn"]
