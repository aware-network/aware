from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_service_runtime.api_ingress.host_context import (
        ServiceEnvironmentCommitReader,
        ServiceEnvironmentCommitReceiptSource,
    )


def current_service_environment_commit_receipt_source() -> (
    "ServiceEnvironmentCommitReceiptSource | None"
):
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.environment_commit_receipt_source


def require_service_environment_commit_receipt_source() -> (
    "ServiceEnvironmentCommitReceiptSource"
):
    source = current_service_environment_commit_receipt_source()
    if source is None:
        raise RuntimeError(
            "Service Environment commit receipt source requires an active "
            "Service API host context with Environment fanout configured."
        )
    return source


def current_service_environment_commit_reader() -> (
    "ServiceEnvironmentCommitReader | None"
):
    from aware_service_runtime.api_ingress.host_context import (
        current_service_api_host_context,
    )

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    return host_context.environment_commit_reader


def require_service_environment_commit_reader() -> "ServiceEnvironmentCommitReader":
    reader = current_service_environment_commit_reader()
    if reader is None:
        raise RuntimeError(
            "Service Environment commit reader requires an active Service API "
            "host context with Environment commit readback configured."
        )
    return reader


__all__ = [
    "current_service_environment_commit_reader",
    "current_service_environment_commit_receipt_source",
    "require_service_environment_commit_reader",
    "require_service_environment_commit_receipt_source",
]
