from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable
from uuid import UUID

from aware_code.types import JsonObject
from aware_service_runtime.contracts import (
    BootstrapServiceContractAccessContextHostControlRequest,
    BootstrapServiceContractAccessContextHostControlResponse,
    EnsureServiceContractAccessContextHostControlRequest,
    EnsureServiceContractAccessContextHostControlResponse,
    RequestStatus,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
)


class ServiceContractAccessContextBootstrapError(RuntimeError):
    """Raised when callers require a ready Service contract access context."""


@runtime_checkable
class ServiceHostControlSender(Protocol):
    async def send_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostControlResponse: ...


@runtime_checkable
class ServiceHostControlHandler(Protocol):
    async def handle_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
    ) -> ServiceHostControlResponse: ...


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContextBootstrapResult:
    ready: bool
    service_contract_access_context: JsonObject | None
    bootstrap: JsonObject | None
    status: RequestStatus | None = None
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    error: str | None = None
    response: BootstrapServiceContractAccessContextHostControlResponse | None = None

    @property
    def invocation_context(self) -> JsonObject | None:
        if self.service_contract_access_context is None:
            return None
        return cast(
            JsonObject,
            {
                "service_contract_access_context": (
                    self.service_contract_access_context
                ),
            },
        )

    def require_service_contract_access_context(self) -> JsonObject:
        if self.service_contract_access_context is not None and not self.blockers:
            return self.service_contract_access_context
        detail = self.blocker or ",".join(self.blockers) or "not_ready"
        next_action = f" next_action={self.next_action}" if self.next_action else ""
        raise ServiceContractAccessContextBootstrapError(
            "Service contract access context is not ready: " f"{detail}.{next_action}"
        )

    def require_invocation_context(self) -> JsonObject:
        _ = self.require_service_contract_access_context()
        assert self.invocation_context is not None
        return self.invocation_context


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContextEnsureResult:
    ready: bool
    ensured: bool
    service_contract_access_context: JsonObject | None
    bootstrap: JsonObject | None
    admission: JsonObject | None
    status: RequestStatus | None = None
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    error: str | None = None
    response: EnsureServiceContractAccessContextHostControlResponse | None = None

    @property
    def invocation_context(self) -> JsonObject | None:
        if self.service_contract_access_context is None:
            return None
        return cast(
            JsonObject,
            {
                "service_contract_access_context": (
                    self.service_contract_access_context
                ),
            },
        )

    def require_service_contract_access_context(self) -> JsonObject:
        if self.service_contract_access_context is not None and not self.blockers:
            return self.service_contract_access_context
        detail = self.blocker or ",".join(self.blockers) or "not_ready"
        next_action = f" next_action={self.next_action}" if self.next_action else ""
        raise ServiceContractAccessContextBootstrapError(
            "Service contract access context is not ready: " f"{detail}.{next_action}"
        )

    def require_invocation_context(self) -> JsonObject:
        _ = self.require_service_contract_access_context()
        assert self.invocation_context is not None
        return self.invocation_context


async def bootstrap_service_contract_access_context(
    *,
    client: ServiceHostControlSender | ServiceHostControlHandler,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    timeout_s: float | None = 5.0,
) -> ServiceContractAccessContextBootstrapResult:
    request = BootstrapServiceContractAccessContextHostControlRequest(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
    )
    try:
        response = await _send_or_handle_host_control_request(
            client=client,
            request=request,
            timeout_s=timeout_s,
        )
    except Exception as exc:
        return _blocked_result(
            blocker="contract_access_context_bootstrap_error",
            blockers=("contract_access_context_bootstrap_error",),
            next_action="inspect_servicehost_contract_access_context_bootstrap",
            error=str(exc),
        )
    if not isinstance(
        response, BootstrapServiceContractAccessContextHostControlResponse
    ):
        return _blocked_result(
            blocker="unexpected_contract_access_context_bootstrap_response",
            blockers=("unexpected_contract_access_context_bootstrap_response",),
            next_action="inspect_servicehost_contract_access_context_bootstrap",
            error=f"unexpected response type {type(response).__name__}",
        )
    bootstrap = _mapping_or_none(response.bootstrap)
    service_contract_access_context = _mapping_or_none(
        None if bootstrap is None else bootstrap.get("service_contract_access_context")
    )
    if response.status != RequestStatus.succeeded:
        blockers = response.blockers or ("contract_access_context_bootstrap_failed",)
        return ServiceContractAccessContextBootstrapResult(
            ready=False,
            service_contract_access_context=None,
            bootstrap=bootstrap,
            status=response.status,
            blocker=response.blocker or blockers[0],
            blockers=tuple(blockers),
            next_action=response.next_action
            or "inspect_servicehost_contract_access_context_bootstrap",
            error=response.error,
            response=response,
        )
    if response.ready and service_contract_access_context is not None:
        return ServiceContractAccessContextBootstrapResult(
            ready=True,
            service_contract_access_context=service_contract_access_context,
            bootstrap=bootstrap,
            status=response.status,
            blocker=None,
            blockers=(),
            next_action=None,
            error=response.error,
            response=response,
        )
    blockers = response.blockers or ("service_contract_access_context_not_ready",)
    return ServiceContractAccessContextBootstrapResult(
        ready=False,
        service_contract_access_context=None,
        bootstrap=bootstrap,
        status=response.status,
        blocker=response.blocker or blockers[0],
        blockers=tuple(blockers),
        next_action=response.next_action
        or "resolve_wallet_backed_service_contract_access_context",
        error=response.error,
        response=response,
    )


async def bootstrap_service_contract_access_invocation_context(
    *,
    client: ServiceHostControlSender | ServiceHostControlHandler,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    timeout_s: float | None = 5.0,
) -> JsonObject:
    result = await bootstrap_service_contract_access_context(
        client=client,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
        timeout_s=timeout_s,
    )
    return result.require_invocation_context()


async def ensure_service_contract_access_context(
    *,
    client: ServiceHostControlSender | ServiceHostControlHandler,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    service_contract_config_name: str = "local_dev",
    commercial_profile_id: UUID | None = None,
    producer_finance_entity_id: UUID | None = None,
    service_plan_id: UUID | None = None,
    timeout_s: float | None = 5.0,
) -> ServiceContractAccessContextEnsureResult:
    request = EnsureServiceContractAccessContextHostControlRequest(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
        service_contract_config_name=service_contract_config_name,
        commercial_profile_id=commercial_profile_id,
        producer_finance_entity_id=producer_finance_entity_id,
        service_plan_id=service_plan_id,
    )
    try:
        response = await _send_or_handle_host_control_request(
            client=client,
            request=request,
            timeout_s=timeout_s,
        )
    except Exception as exc:
        return _blocked_ensure_result(
            blocker="contract_access_context_ensure_error",
            blockers=("contract_access_context_ensure_error",),
            next_action="inspect_servicehost_contract_access_context_ensure",
            error=str(exc),
        )
    if not isinstance(response, EnsureServiceContractAccessContextHostControlResponse):
        return _blocked_ensure_result(
            blocker="unexpected_contract_access_context_ensure_response",
            blockers=("unexpected_contract_access_context_ensure_response",),
            next_action="inspect_servicehost_contract_access_context_ensure",
            error=f"unexpected response type {type(response).__name__}",
        )
    bootstrap = _mapping_or_none(response.bootstrap)
    admission = _mapping_or_none(response.admission)
    service_contract_access_context = _mapping_or_none(
        None if bootstrap is None else bootstrap.get("service_contract_access_context")
    )
    if response.status != RequestStatus.succeeded:
        blockers = response.blockers or ("contract_access_context_ensure_failed",)
        return ServiceContractAccessContextEnsureResult(
            ready=False,
            ensured=response.ensured,
            service_contract_access_context=None,
            bootstrap=bootstrap,
            admission=admission,
            status=response.status,
            blocker=response.blocker or blockers[0],
            blockers=tuple(blockers),
            next_action=response.next_action
            or "inspect_servicehost_contract_access_context_ensure",
            error=response.error,
            response=response,
        )
    if response.ready and service_contract_access_context is not None:
        return ServiceContractAccessContextEnsureResult(
            ready=True,
            ensured=response.ensured,
            service_contract_access_context=service_contract_access_context,
            bootstrap=bootstrap,
            admission=admission,
            status=response.status,
            blocker=None,
            blockers=(),
            next_action=None,
            error=response.error,
            response=response,
        )
    blockers = response.blockers or ("service_contract_access_context_not_ready",)
    return ServiceContractAccessContextEnsureResult(
        ready=False,
        ensured=response.ensured,
        service_contract_access_context=None,
        bootstrap=bootstrap,
        admission=admission,
        status=response.status,
        blocker=response.blocker or blockers[0],
        blockers=tuple(blockers),
        next_action=response.next_action
        or "resolve_wallet_backed_service_contract_access_context",
        error=response.error,
        response=response,
    )


async def ensure_service_contract_access_invocation_context(
    *,
    client: ServiceHostControlSender | ServiceHostControlHandler,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    service_contract_config_name: str = "local_dev",
    commercial_profile_id: UUID | None = None,
    producer_finance_entity_id: UUID | None = None,
    service_plan_id: UUID | None = None,
    timeout_s: float | None = 5.0,
) -> JsonObject:
    result = await ensure_service_contract_access_context(
        client=client,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
        service_contract_config_name=service_contract_config_name,
        commercial_profile_id=commercial_profile_id,
        producer_finance_entity_id=producer_finance_entity_id,
        service_plan_id=service_plan_id,
        timeout_s=timeout_s,
    )
    return result.require_invocation_context()


async def _send_or_handle_host_control_request(
    *,
    client: ServiceHostControlSender | ServiceHostControlHandler,
    request: ServiceHostControlRequest,
    timeout_s: float | None,
) -> ServiceHostControlResponse:
    if isinstance(client, ServiceHostControlSender):
        return await client.send_host_control_request(
            request=request,
            timeout_s=timeout_s,
        )
    if isinstance(client, ServiceHostControlHandler):
        return await client.handle_host_control_request(request=request)
    raise TypeError(
        "Service contract access bootstrap requires a ServiceHost control client "
        "with send_host_control_request(...) or handle_host_control_request(...)."
    )


def _mapping_or_none(value: object) -> JsonObject | None:
    if not isinstance(value, Mapping):
        return None
    return cast(JsonObject, dict(value))


def _blocked_result(
    *,
    blocker: str,
    blockers: tuple[str, ...],
    next_action: str,
    error: str | None = None,
) -> ServiceContractAccessContextBootstrapResult:
    return ServiceContractAccessContextBootstrapResult(
        ready=False,
        service_contract_access_context=None,
        bootstrap=None,
        status=None,
        blocker=blocker,
        blockers=blockers,
        next_action=next_action,
        error=error,
        response=None,
    )


def _blocked_ensure_result(
    *,
    blocker: str,
    blockers: tuple[str, ...],
    next_action: str,
    error: str | None = None,
) -> ServiceContractAccessContextEnsureResult:
    return ServiceContractAccessContextEnsureResult(
        ready=False,
        ensured=False,
        service_contract_access_context=None,
        bootstrap=None,
        admission=None,
        status=None,
        blocker=blocker,
        blockers=blockers,
        next_action=next_action,
        error=error,
        response=None,
    )


__all__ = [
    "ServiceContractAccessContextBootstrapError",
    "ServiceContractAccessContextBootstrapResult",
    "ServiceContractAccessContextEnsureResult",
    "ServiceHostControlHandler",
    "ServiceHostControlSender",
    "bootstrap_service_contract_access_context",
    "bootstrap_service_contract_access_invocation_context",
    "ensure_service_contract_access_context",
    "ensure_service_contract_access_invocation_context",
]
