from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from aware_economy_ontology_dto.stable_ids import stable_finance_entity_id
from aware_service_runtime.contracts import (
    BootstrapServiceContractAccessContextHostControlRequest,
    BootstrapServiceContractAccessContextHostControlResponse,
    RequestStatus,
)
from aware_service_runtime.duplex_client import (
    ServiceHostDuplexClient,
    build_service_host_duplex_client_from_env,
)
from aware_utils.logging import logger

SERVICE_CONTRACT_ACCESS_ROLE = "member"


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContext:
    service_id: UUID
    service_operation_config_id: UUID | None = None

    @classmethod
    def from_env(cls) -> "ServiceContractAccessContext":
        return cls(
            service_id=UUID(
                _require_env("AWARE_NODE_SERVICE_CONTRACT_ACCESS_SERVICE_ID")
            ),
            service_operation_config_id=_optional_env_uuid(
                "AWARE_NODE_SERVICE_CONTRACT_ACCESS_OPERATION_CONFIG_ID"
            ),
        )


@dataclass(frozen=True, slots=True)
class ServiceContractAccessStatusResult:
    is_active: bool
    plan_label: str | None = None
    current_period_end: str | None = None
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    consumer_finance_entity_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None


class _ServiceContractAccessDispatcher(Protocol):
    async def start(self) -> None: ...

    async def read_access_status(
        self,
        *,
        actor_id: UUID,
    ) -> ServiceContractAccessStatusResult: ...


class ServiceContractAccessDispatcher:
    def __init__(
        self,
        *,
        service_host_client: ServiceHostDuplexClient,
        context: ServiceContractAccessContext,
    ) -> None:
        self._service_host_client = service_host_client
        self._context = context
        self._started = False

    @classmethod
    def from_env(cls) -> "ServiceContractAccessDispatcher":
        return cls(
            service_host_client=build_service_host_duplex_client_from_env(
                "AWARE_NODE_SERVICE_CONTRACT_ACCESS_SERVICE_HOST_SOCKET_PATH",
                "AWARE_SERVICE_HOST_SOCKET_PATH",
            ),
            context=ServiceContractAccessContext.from_env(),
        )

    async def start(self) -> None:
        if self._started:
            return
        self._started = True

    async def read_access_status(
        self,
        *,
        actor_id: UUID,
    ) -> ServiceContractAccessStatusResult:
        await self.start()
        consumer_finance_entity_id = stable_finance_entity_id(identity_id=actor_id)
        response = await self._service_host_client.send_host_control_request(
            request=BootstrapServiceContractAccessContextHostControlRequest(
                service_id=self._context.service_id,
                consumer_finance_entity_id=consumer_finance_entity_id,
                service_operation_config_id=self._context.service_operation_config_id,
            )
        )
        if not isinstance(
            response,
            BootstrapServiceContractAccessContextHostControlResponse,
        ):
            response = (
                BootstrapServiceContractAccessContextHostControlResponse.model_validate(
                    response
                )
            )
        return _status_from_bootstrap_response(
            response=response,
            consumer_finance_entity_id=consumer_finance_entity_id,
        )


_service_contract_access_dispatcher_lock = asyncio.Lock()
_service_contract_access_dispatcher: _ServiceContractAccessDispatcher | None = None


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    raw = value.strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def service_contract_access_gate_required() -> bool:
    """Whether the node must require Service contract access before provisioning."""

    mode = (
        (
            os.environ.get("AWARE_NODE_SERVICE_CONTRACT_ACCESS_GATE")
            or os.environ.get("AWARE_NODE_MEMBERSHIP_GATE")
            or "off"
        )
        .strip()
        .lower()
    )
    if mode in {"required", "require", "on"}:
        return True
    if mode in {"off", "disabled", "false", "0"}:
        return False
    return _parse_bool(mode, default=False)


def _bypass_actor_ids() -> set[UUID]:
    raw = (
        os.environ.get("AWARE_NODE_SERVICE_CONTRACT_ACCESS_BYPASS_ACTOR_IDS")
        or os.environ.get("AWARE_NODE_MEMBERSHIP_BYPASS_ACTOR_IDS")
        or ""
    ).strip()
    if not raw:
        return set()
    out: set[UUID] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            out.add(UUID(token))
        except Exception:
            logger.warning(
                "Invalid bypass actor id in Service contract access env: %r",
                token,
            )
    return out


def is_actor_contract_access_bypassed(*, actor_id: UUID) -> bool:
    return actor_id in _bypass_actor_ids()


async def actor_has_service_contract_access(
    *,
    actor_id: UUID,
    fail_closed: bool = False,
) -> bool:
    if is_actor_contract_access_bypassed(actor_id=actor_id):
        return True
    try:
        status = await read_service_contract_access_status(actor_id=actor_id)
    except Exception as exc:
        if fail_closed:
            raise RuntimeError(
                f"service contract access status unavailable: {exc}"
            ) from exc
        logger.warning(
            "Service contract access status unavailable for actor %s; treating as inactive: %s",
            actor_id,
            exc,
        )
        return False
    return bool(status.is_active)


def set_service_contract_access_dispatcher(
    dispatcher: _ServiceContractAccessDispatcher | None,
) -> None:
    global _service_contract_access_dispatcher
    _service_contract_access_dispatcher = dispatcher


async def read_service_contract_access_status(
    *,
    actor_id: UUID,
) -> ServiceContractAccessStatusResult:
    return await (
        await _require_service_contract_access_dispatcher()
    ).read_access_status(actor_id=actor_id)


async def _require_service_contract_access_dispatcher() -> (
    _ServiceContractAccessDispatcher
):
    global _service_contract_access_dispatcher
    async with _service_contract_access_dispatcher_lock:
        if _service_contract_access_dispatcher is None:
            _service_contract_access_dispatcher = (
                ServiceContractAccessDispatcher.from_env()
            )
        dispatcher = _service_contract_access_dispatcher
    await dispatcher.start()
    return dispatcher


def _status_from_bootstrap_response(
    *,
    response: BootstrapServiceContractAccessContextHostControlResponse,
    consumer_finance_entity_id: UUID,
) -> ServiceContractAccessStatusResult:
    bootstrap = response.bootstrap or {}
    if response.status is not RequestStatus.succeeded:
        raise RuntimeError(response.error or "service contract access bootstrap failed")

    blockers = _blockers_from_response(response=response, bootstrap=bootstrap)
    ready = bool(response.ready or bootstrap.get("ready"))
    return ServiceContractAccessStatusResult(
        is_active=ready,
        blocker=response.blocker or _optional_text(bootstrap.get("blocker")),
        blockers=blockers,
        consumer_finance_entity_id=_optional_uuid(
            bootstrap.get("consumer_finance_entity_id")
        )
        or consumer_finance_entity_id,
        service_subscription_id=_optional_uuid(
            bootstrap.get("service_subscription_id")
        ),
        service_contract_id=_optional_uuid(bootstrap.get("service_contract_id")),
        service_contract_config_id=_optional_uuid(
            bootstrap.get("service_contract_config_id")
        ),
        smart_contract_id=_optional_uuid(bootstrap.get("smart_contract_id")),
    )


def _blockers_from_response(
    *,
    response: BootstrapServiceContractAccessContextHostControlResponse,
    bootstrap: dict[str, Any],
) -> tuple[str, ...]:
    values: list[str] = []
    for blocker in response.blockers:
        text = _optional_text(blocker)
        if text is not None:
            values.append(text)
    raw_blockers = bootstrap.get("blockers")
    if isinstance(raw_blockers, list | tuple):
        for blocker in raw_blockers:
            text = _optional_text(blocker)
            if text is not None:
                values.append(text)
    return tuple(dict.fromkeys(values))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    if not text:
        return None
    return UUID(text)


def _optional_env_uuid(name: str) -> UUID | None:
    return _optional_uuid(os.environ.get(name))


def _require_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


__all__ = [
    "SERVICE_CONTRACT_ACCESS_ROLE",
    "ServiceContractAccessContext",
    "ServiceContractAccessDispatcher",
    "ServiceContractAccessStatusResult",
    "actor_has_service_contract_access",
    "is_actor_contract_access_bypassed",
    "read_service_contract_access_status",
    "service_contract_access_gate_required",
    "set_service_contract_access_dispatcher",
]
