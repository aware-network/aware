from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import time
from typing import Any, Protocol, cast
from aware_node_service_dto.node.host import HostedRuntimeLifecycleStatus
from aware_node_service_dto.node.host import HostedServiceRuntimeServiceStatus
from aware_node_service_dto.node.host import HostedServiceRuntimeStatus
from aware_service_runtime.contracts import (
    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
    SERVICE_HOST_CAPABILITY_API_DISPATCH,
    ServiceHostCapabilityState,
    ServiceHostHandshakeResponse,
)
from aware_interface_service.models import (
    InterfaceHostServiceHostedServiceRequirementState,
    InterfaceHostServiceHostedRuntimeServiceState,
    InterfaceHostServiceHostedRuntimeState,
    InterfaceHostServiceHostedServicesState,
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceRecoveryCapabilityState,
)


class _LocalServiceHostHandshakeProbe(Protocol):
    def __call__(self) -> Awaitable[ServiceHostHandshakeResponse]: ...


@dataclass(frozen=True, slots=True)
class _RequiredHostedService:
    service_name: str
    service_label: str


_REQUIRED_HOSTED_SERVICES = (
    _RequiredHostedService(
        service_name="aware_environment",
        service_label="Environment",
    ),
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _elapsed_ms(started_at_s: float) -> int:
    return max(0, int((time.monotonic() - started_at_s) * 1000))


def _capability_state_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip().casefold()


def _is_available_capability_state(value: object) -> bool:
    return _capability_state_value(value) == ServiceHostCapabilityState.available.value


def _supports_node_hosted_service_status_query(client: object) -> bool:
    return callable(getattr(client, "describe_hosted_service_runtimes", None))


def _supports_node_hosted_runtime_lifecycle_query(client: object) -> bool:
    return callable(getattr(client, "describe_hosted_runtimes", None))


def _supports_node_hosted_runtime_lifecycle_restart(client: object) -> bool:
    return callable(getattr(client, "restart_hosted_runtime", None))


def _string_tuple_from_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        token = item.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return tuple(normalized)


def _string_tuple_from_mapping(value: object, service_name: str) -> tuple[str, ...]:
    if not isinstance(value, dict):
        return ()
    return _string_tuple_from_items(value.get(service_name))


def _service_names_from_api_dispatch_payload(
    payload: dict[str, object]
) -> tuple[str, ...]:
    names: set[str] = set(
        _string_tuple_from_items(
            payload.get(SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY)
        )
    )
    for key in (
        SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
        SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
    ):
        raw_mapping = payload.get(key)
        if not isinstance(raw_mapping, dict):
            continue
        names.update(
            item.strip()
            for item in raw_mapping
            if isinstance(item, str) and item.strip()
        )
    return tuple(sorted(names, key=str.casefold))


def _service_key(value: str) -> str:
    return value.strip().casefold()


def _runtime_endpoint(value: object | None) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _recovery_label(key: str) -> str:
    normalized = key.strip().casefold()
    if normalized == "refresh":
        return "Refresh status"
    if normalized == "restart":
        return "Restart host"
    if normalized == "upgrade":
        return "Upgrade host"
    return key.strip().replace("_", " ").title() or "Host recovery"


def _recovery_action_key(key: str) -> str:
    normalized = key.strip().casefold()
    if normalized == "refresh":
        return "interface.host.refresh_status"
    if normalized == "restart":
        return "interface.host.restart_host"
    if normalized == "upgrade":
        return "interface.host.upgrade_host"
    return f"interface.host.{normalized}" if normalized else "interface.host.recover"


def _select_hosted_interface_runtime(
    statuses: tuple[HostedRuntimeLifecycleStatus, ...],
    *,
    endpoint: str | None,
) -> HostedRuntimeLifecycleStatus | None:
    if not statuses:
        return None
    normalized_endpoint = _runtime_endpoint(endpoint)
    if normalized_endpoint is not None:
        for status in statuses:
            if _runtime_endpoint(status.endpoint) == normalized_endpoint:
                return status
    if len(statuses) == 1:
        return statuses[0]
    ready = tuple(status for status in statuses if status.is_alive)
    if len(ready) == 1:
        return ready[0]
    return statuses[0]


def _recovery_capabilities_from_lifecycle_status(
    status: HostedRuntimeLifecycleStatus,
) -> tuple[InterfaceHostServiceRecoveryCapabilityState, ...]:
    by_key = {
        capability.key.strip().casefold(): capability
        for capability in status.recovery_capabilities
        if capability.key.strip()
    }
    ordered_keys = ("refresh", "restart", "upgrade")
    capabilities: list[InterfaceHostServiceRecoveryCapabilityState] = []
    for key in ordered_keys:
        node_capability = by_key.get(key)
        capabilities.append(
            InterfaceHostServiceRecoveryCapabilityState(
                key=key,
                label=_recovery_label(key),
                enabled=bool(node_capability.enabled) if node_capability else False,
                reason=node_capability.reason if node_capability else None,
                action_key=_recovery_action_key(key),
            )
        )
    for key, node_capability in sorted(by_key.items()):
        if key in ordered_keys:
            continue
        capabilities.append(
            InterfaceHostServiceRecoveryCapabilityState(
                key=key,
                label=_recovery_label(key),
                enabled=bool(node_capability.enabled),
                reason=node_capability.reason,
                action_key=_recovery_action_key(key),
            )
        )
    return tuple(capabilities)


def _restart_capability_blocker(
    status: HostedRuntimeLifecycleStatus,
) -> str | None:
    for capability in status.recovery_capabilities:
        if capability.key.strip().casefold() != "restart":
            continue
        if capability.enabled:
            return None
        return (
            capability.reason
            or "Node reports hosted Interface restart is not available."
        )
    return (
        "Node did not publish a restart capability for this hosted Interface runtime."
    )


def _required_service_error(
    *,
    state_error: str | None,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
) -> str | None:
    if state_error:
        return state_error
    if local_service_host is None:
        return None
    return local_service_host.error


def _required_service_status(
    *,
    state_error: str | None,
    runtimes: tuple[InterfaceHostServiceHostedRuntimeState, ...],
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
) -> str:
    if state_error:
        return "error"
    if any(not runtime.is_ready for runtime in runtimes):
        return "starting"
    if local_service_host is None:
        return "missing"
    if not local_service_host.managed:
        return "missing"
    if not local_service_host.supported:
        return "unsupported"
    if local_service_host.error:
        return "error"
    if not local_service_host.ready:
        return "starting"
    return "missing"


def _required_service_summary(
    *,
    required_service: _RequiredHostedService,
    state_error: str | None,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
) -> str:
    label = required_service.service_label
    if state_error:
        return f"{label} service state could not be refreshed."
    if local_service_host is None:
        return (
            f"{label} service is required, but no hosted service runtime is "
            "advertising it yet."
        )
    if not local_service_host.managed:
        return (
            f"{label} service is required, but this host is not managing a "
            "local ServiceHost runtime."
        )
    if not local_service_host.supported:
        return f"{label} service requires a supported local ServiceHost runtime."
    if not local_service_host.ready:
        return (
            local_service_host.error
            or f"{label} service requires the local ServiceHost to become ready."
        )
    return f"{label} service is required but was not advertised by ServiceHost."


def _hosted_service_requirements(
    *,
    runtimes: tuple[InterfaceHostServiceHostedRuntimeState, ...] = (),
    source_kind: str,
    state_error: str | None = None,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None = None,
) -> tuple[InterfaceHostServiceHostedServiceRequirementState, ...]:
    requirements: list[InterfaceHostServiceHostedServiceRequirementState] = []
    for required_service in _REQUIRED_HOSTED_SERVICES:
        matched_runtime: InterfaceHostServiceHostedRuntimeState | None = None
        matched_service: InterfaceHostServiceHostedRuntimeServiceState | None = None
        for runtime in runtimes:
            for service in runtime.services:
                if _service_key(service.service_name) != _service_key(
                    required_service.service_name
                ):
                    continue
                matched_runtime = runtime
                matched_service = service
                break
            if matched_service is not None:
                break

        if matched_runtime is not None and matched_service is not None:
            status = (
                "error"
                if matched_runtime.error
                else "ready" if matched_runtime.is_ready else "starting"
            )
            requirements.append(
                InterfaceHostServiceHostedServiceRequirementState(
                    service_name=required_service.service_name,
                    service_label=required_service.service_label,
                    is_required=True,
                    status=status,
                    source_kind=source_kind,
                    summary=(
                        f"{required_service.service_label} service is advertised by "
                        f"{matched_runtime.host_id}."
                    ),
                    error=matched_runtime.error,
                    matched_runtime_host_id=matched_runtime.host_id,
                    endpoint_refs=matched_service.endpoint_refs,
                    stream_endpoint_refs=matched_service.stream_endpoint_refs,
                )
            )
            continue

        requirements.append(
            InterfaceHostServiceHostedServiceRequirementState(
                service_name=required_service.service_name,
                service_label=required_service.service_label,
                is_required=True,
                status=_required_service_status(
                    state_error=state_error,
                    runtimes=runtimes,
                    local_service_host=local_service_host,
                ),
                source_kind=source_kind,
                summary=_required_service_summary(
                    required_service=required_service,
                    state_error=state_error,
                    local_service_host=local_service_host,
                ),
                error=_required_service_error(
                    state_error=state_error,
                    local_service_host=local_service_host,
                ),
            )
        )
    return tuple(requirements)


def _with_required_service_state(
    state: InterfaceHostServiceHostedServicesState,
    *,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None = None,
) -> InterfaceHostServiceHostedServicesState:
    requirements = _hosted_service_requirements(
        runtimes=state.runtimes,
        source_kind=state.source_kind,
        state_error=state.error,
        local_service_host=local_service_host,
    )
    satisfied_count = sum(
        1 for requirement in requirements if requirement.status == "ready"
    )
    return replace(
        state,
        required_service_count=len(requirements),
        satisfied_service_count=satisfied_count,
        service_requirements=requirements,
    )


def unavailable_hosted_services_state(
    *,
    source_kind: str,
    updated_at: str | None = None,
    error: str | None = None,
    refresh_duration_ms: int | None = None,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None = None,
) -> InterfaceHostServiceHostedServicesState:
    return _with_required_service_state(
        InterfaceHostServiceHostedServicesState(
            available=False,
            source_kind=source_kind,
            updated_at=updated_at or _utc_now_iso(),
            error=error,
            refresh_duration_ms=refresh_duration_ms,
        ),
        local_service_host=local_service_host,
    )


def hosted_services_state_from_service_host_handshake(
    response: ServiceHostHandshakeResponse,
    *,
    updated_at: str | None = None,
    refresh_duration_ms: int | None = None,
) -> InterfaceHostServiceHostedServicesState:
    timestamp = updated_at or _utc_now_iso()
    services: list[InterfaceHostServiceHostedRuntimeServiceState] = []
    supports_stream_events = False
    for capability in response.capabilities:
        if not _is_available_capability_state(capability.state):
            continue
        if capability.capability_id == "duplex_stream_events":
            supports_stream_events = True
            continue
        if capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH:
            continue
        payload = capability.detail_payload
        if not isinstance(payload, dict):
            continue
        endpoint_refs_by_service = payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY
        )
        stream_endpoint_refs_by_service = payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY
        )
        services.extend(
            InterfaceHostServiceHostedRuntimeServiceState(
                service_name=service_name,
                endpoint_refs=_string_tuple_from_mapping(
                    endpoint_refs_by_service,
                    service_name,
                ),
                stream_endpoint_refs=_string_tuple_from_mapping(
                    stream_endpoint_refs_by_service,
                    service_name,
                ),
            )
            for service_name in _service_names_from_api_dispatch_payload(payload)
        )
    services_tuple = tuple(services)
    runtime = InterfaceHostServiceHostedRuntimeState(
        host_id=response.host_id,
        host_version=response.host_version,
        protocol_version=response.protocol_version,
        readiness_status=response.readiness.status.value,
        is_ready=response.readiness.is_ready,
        is_alive=True,
        supports_stream_events=supports_stream_events,
        summary=response.readiness.reason,
        error=None if response.readiness.is_ready else response.readiness.reason,
        updated_at=timestamp,
        probe_duration_ms=refresh_duration_ms,
        services=services_tuple,
    )
    return _with_required_service_state(
        InterfaceHostServiceHostedServicesState(
            available=response.readiness.is_ready,
            source_kind="local_service_host",
            updated_at=timestamp,
            refresh_duration_ms=refresh_duration_ms,
            runtime_count=1,
            service_count=len(services_tuple),
            runtimes=(runtime,),
        )
    )


def hosted_runtime_service_state(
    service: HostedServiceRuntimeServiceStatus,
) -> InterfaceHostServiceHostedRuntimeServiceState:
    return InterfaceHostServiceHostedRuntimeServiceState(
        service_name=service.service_name,
        endpoint_refs=tuple(service.endpoint_refs),
        stream_endpoint_refs=tuple(service.stream_endpoint_refs),
    )


def hosted_runtime_state(
    runtime: HostedServiceRuntimeStatus,
) -> InterfaceHostServiceHostedRuntimeState:
    return InterfaceHostServiceHostedRuntimeState(
        host_id=runtime.host_id,
        host_version=runtime.host_version,
        protocol_version=runtime.protocol_version,
        readiness_status=runtime.readiness_status,
        is_ready=runtime.is_ready,
        is_alive=runtime.is_alive,
        supports_stream_events=runtime.supports_stream_events,
        summary=runtime.summary,
        error=runtime.error,
        updated_at=runtime.updated_at,
        probe_duration_ms=None,
        services=tuple(hosted_runtime_service_state(item) for item in runtime.services),
    )


def should_query_hosted_service_status(
    *,
    transport_bound: bool,
    consumer_profile_active: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None,
) -> bool:
    if not transport_bound:
        return False
    if consumer_profile_active:
        return True
    if (
        local_service_host is not None
        and local_service_host.managed
        and not local_service_host.ready
    ):
        return False
    if (
        local_node_runtime is not None
        and local_node_runtime.managed
        and not local_node_runtime.ready
    ):
        return False
    return True


async def refresh_hosted_service_status(
    *,
    transport_session: Any | None,
    consumer_profile_active: bool,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
    local_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None,
) -> InterfaceHostServiceHostedServicesState | None:
    if not should_query_hosted_service_status(
        transport_bound=transport_session is not None,
        consumer_profile_active=consumer_profile_active,
        local_service_host=local_service_host,
        local_node_runtime=local_node_runtime,
    ):
        return None

    if transport_session is None:
        return None

    client = transport_session.client
    if not _supports_node_hosted_service_status_query(client):
        if local_service_host is not None and local_service_host.managed:
            return None
        return unavailable_hosted_services_state(source_kind="host_requirements")

    started_at_s = time.monotonic()
    try:
        statuses = await client.describe_hosted_service_runtimes()
        runtimes = tuple(hosted_runtime_state(item) for item in statuses)
        return _with_required_service_state(
            InterfaceHostServiceHostedServicesState(
                available=True,
                updated_at=_utc_now_iso(),
                refresh_duration_ms=_elapsed_ms(started_at_s),
                runtime_count=len(runtimes),
                service_count=sum(len(runtime.services) for runtime in runtimes),
                runtimes=runtimes,
            )
        )
    except Exception as exc:
        return unavailable_hosted_services_state(
            source_kind="node_control_plane",
            updated_at=_utc_now_iso(),
            error=str(exc),
            refresh_duration_ms=_elapsed_ms(started_at_s),
        )


async def refresh_host_recovery_capabilities(
    *,
    transport_session: Any | None,
    endpoint: str | None,
) -> tuple[InterfaceHostServiceRecoveryCapabilityState, ...]:
    if transport_session is None:
        return ()
    client = transport_session.client
    if not _supports_node_hosted_runtime_lifecycle_query(client):
        return ()
    try:
        statuses = await client.describe_hosted_runtimes(runtime_kind="interface")
    except Exception:
        return ()
    selected = _select_hosted_interface_runtime(
        tuple(statuses),
        endpoint=endpoint,
    )
    if selected is None:
        return ()
    return _recovery_capabilities_from_lifecycle_status(selected)


async def restart_hosted_interface_runtime(
    *,
    transport_session: Any | None,
    endpoint: str | None,
    reason: str | None = None,
    evidence: dict[str, object] | None = None,
) -> object:
    if transport_session is None:
        raise RuntimeError(
            "Interface Host is not attached to a Node transport session."
        )
    client = transport_session.client
    if not _supports_node_hosted_runtime_lifecycle_query(client):
        raise RuntimeError("Node SDK does not expose hosted runtime lifecycle status.")
    if not _supports_node_hosted_runtime_lifecycle_restart(client):
        raise RuntimeError("Node SDK does not expose hosted runtime restart.")
    statuses = await client.describe_hosted_runtimes(runtime_kind="interface")
    selected = _select_hosted_interface_runtime(
        tuple(statuses),
        endpoint=endpoint,
    )
    if selected is None:
        raise RuntimeError("Node did not report a hosted Interface runtime to restart.")
    blocker = _restart_capability_blocker(selected)
    if blocker is not None:
        raise RuntimeError(blocker)
    return await client.restart_hosted_runtime(
        runtime_key=selected.runtime_key,
        reason=reason,
        evidence=evidence,
    )


async def refresh_local_service_host_status(
    *,
    local_runtime: object | None,
    local_service_host: InterfaceHostServiceLocalServiceHostState | None,
) -> InterfaceHostServiceHostedServicesState | None:
    if local_runtime is None or local_service_host is None:
        return None
    if not local_service_host.managed:
        return None
    if not local_service_host.ready:
        return unavailable_hosted_services_state(
            source_kind="local_service_host",
            updated_at=local_service_host.last_checked_at,
            error=local_service_host.error,
            refresh_duration_ms=local_service_host.probe_duration_ms,
            local_service_host=local_service_host,
        )
    handshake_probe = getattr(local_runtime, "probe_service_host_handshake", None)
    if not callable(handshake_probe):
        return unavailable_hosted_services_state(
            source_kind="local_service_host",
            error="Local ServiceHost does not expose a handshake probe.",
            local_service_host=local_service_host,
        )
    probe = cast(_LocalServiceHostHandshakeProbe, handshake_probe)
    started_at_s = time.monotonic()
    try:
        response = await probe()
        duration_ms = _elapsed_ms(started_at_s)
        return hosted_services_state_from_service_host_handshake(
            response,
            updated_at=_utc_now_iso(),
            refresh_duration_ms=duration_ms,
        )
    except Exception as exc:
        return unavailable_hosted_services_state(
            source_kind="local_service_host",
            updated_at=_utc_now_iso(),
            error=str(exc),
            refresh_duration_ms=_elapsed_ms(started_at_s),
            local_service_host=local_service_host,
        )


__all__ = [
    "hosted_runtime_service_state",
    "hosted_runtime_state",
    "hosted_services_state_from_service_host_handshake",
    "refresh_host_recovery_capabilities",
    "refresh_hosted_service_status",
    "refresh_local_service_host_status",
    "restart_hosted_interface_runtime",
    "should_query_hosted_service_status",
    "unavailable_hosted_services_state",
]
