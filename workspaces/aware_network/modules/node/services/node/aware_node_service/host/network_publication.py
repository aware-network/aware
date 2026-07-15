from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from typing import Protocol
from urllib.parse import urlparse
from uuid import UUID

from aware_network.network.node.manager import network_node_manager
from aware_network_service_dto.comms.models.network_node import (
    HostedServiceAdvertisement,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationEnvironment,
    NetworkNodePublicationHostedService,
    NetworkNodePublicationIntent,
    NetworkNodePublicationNode,
    NetworkReconcileNodePublicationResponse,
)
from aware_node_service.control_plane.actor_authority import (
    resolve_node_system_actor_id,
)
from aware_utils.logging import logger

_NODE_PUBLIC_BASE_URL_ENV = "AWARE_NODE_PUBLIC_BASE_URL"
_NODE_PUBLIC_HOST_ENV = "AWARE_NODE_PUBLIC_HOST"
_NODE_PUBLIC_PORT_ENV = "AWARE_NODE_PUBLIC_PORT"
_NODE_HOST_ENV = "AWARE_NODE_HOST"
_NODE_PORT_ENV = "AWARE_NODE_PORT"


class NetworkPublicationRuntime(Protocol):
    def discover_hosted_service_advertisements(
        self,
    ) -> tuple[HostedServiceAdvertisement, ...]: ...


class NetworkPublicationSdkClient(Protocol):
    async def reconcile_node_publication(
        self,
        *,
        intent: NetworkNodePublicationIntent,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkReconcileNodePublicationResponse: ...


@dataclass(frozen=True, slots=True)
class NetworkNodePublicEndpoint:
    hostname: str
    port: int
    base_url: str


def build_node_runtime_publication_intent(
    *,
    runtime: NetworkPublicationRuntime,
    environment_id: UUID,
    source_workspace_revision_id: UUID | None = None,
    source_node_config_id: UUID | None = None,
) -> NetworkNodePublicationIntent:
    local_node = network_node_manager.ensure_local_info()
    endpoint = resolve_node_public_endpoint(local_node.http_base_url)
    hosted_services = sorted(
        (
            _publication_service(advertisement)
            for advertisement in runtime.discover_hosted_service_advertisements()
        ),
        key=lambda item: str(item.service_package_id),
    )
    payload = {
        "node": {
            "node_id": str(local_node.id),
            "public_key": (local_node.public_key or "").strip() or str(local_node.id),
            "hostname": endpoint.hostname,
            "port": endpoint.port,
            "base_url": endpoint.base_url,
            "status": "active",
        },
        "environment": {
            "environment_id": str(environment_id),
            "role": "owner",
            "is_active": True,
            "priority": 100,
            "status": "active",
        },
        "hosted_services": [
            service.model_dump(mode="json", exclude_none=True)
            for service in hosted_services
        ],
        "source_workspace_revision_id": (
            str(source_workspace_revision_id)
            if source_workspace_revision_id is not None
            else None
        ),
        "source_node_config_id": (
            str(source_node_config_id) if source_node_config_id is not None else None
        ),
    }
    digest = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    return NetworkNodePublicationIntent(
        publication_digest=digest,
        node=NetworkNodePublicationNode(
            node_id=local_node.id,
            public_key=(local_node.public_key or "").strip() or str(local_node.id),
            hostname=endpoint.hostname,
            port=endpoint.port,
            base_url=endpoint.base_url,
            status="active",
        ),
        environment=NetworkNodePublicationEnvironment(
            environment_id=environment_id,
            role="owner",
            is_active=True,
            priority=100,
            status="active",
            experience_names=[],
        ),
        hosted_services=hosted_services,
        source_workspace_revision_id=source_workspace_revision_id,
        source_node_config_id=source_node_config_id,
    )


async def reconcile_node_runtime_publication(
    *,
    network_sdk_client: NetworkPublicationSdkClient,
    runtime: NetworkPublicationRuntime,
    environment_id: UUID,
    actor_id: UUID | None = None,
    source_workspace_revision_id: UUID | None = None,
    source_node_config_id: UUID | None = None,
) -> NetworkReconcileNodePublicationResponse:
    publication_actor_id = actor_id or resolve_node_system_actor_id()
    intent = build_node_runtime_publication_intent(
        runtime=runtime,
        environment_id=environment_id,
        source_workspace_revision_id=source_workspace_revision_id,
        source_node_config_id=source_node_config_id,
    )
    response = await network_sdk_client.reconcile_node_publication(
        intent=intent,
        actor_id=publication_actor_id,
    )
    logger.info(
        "Reconciled Node runtime publication through Network Service "
        "(node_id=%s environment_id=%s actor_id=%s hosted_services=%s digest=%s)",
        intent.node.node_id,
        environment_id,
        publication_actor_id,
        len(intent.hosted_services),
        intent.publication_digest,
    )
    return response


def resolve_node_public_endpoint(
    fallback_base_url: str | None = None,
) -> NetworkNodePublicEndpoint:
    explicit_base_url = _clean_env(_NODE_PUBLIC_BASE_URL_ENV)
    if explicit_base_url is not None:
        return _endpoint_from_base_url(explicit_base_url)

    host = _clean_env(_NODE_PUBLIC_HOST_ENV) or _clean_env(_NODE_HOST_ENV)
    port = _int_env(_NODE_PUBLIC_PORT_ENV) or _int_env(_NODE_PORT_ENV)
    fallback = _endpoint_from_base_url(fallback_base_url or "http://localhost:8000")
    hostname = _public_hostname(host or fallback.hostname)
    resolved_port = port or fallback.port
    return NetworkNodePublicEndpoint(
        hostname=hostname,
        port=resolved_port,
        base_url=f"http://{hostname}:{resolved_port}",
    )


def _publication_service(
    advertisement: HostedServiceAdvertisement,
) -> NetworkNodePublicationHostedService:
    if advertisement.service_id is None or advertisement.service_package_id is None:
        raise RuntimeError(
            "Network publication requires committed service_id and "
            f"service_package_id for {advertisement.service_name!r}."
        )
    return NetworkNodePublicationHostedService(
        service_package_id=advertisement.service_package_id,
        service_id=advertisement.service_id,
        service_name=advertisement.service_name,
        service_package_names=list(_clean_tuple(advertisement.service_package_names)),
        endpoint_refs=list(_clean_tuple(advertisement.endpoint_refs)),
        stream_endpoint_refs=list(
            _clean_tuple(getattr(advertisement, "stream_endpoint_refs", ()))
        ),
        host_id=advertisement.host_id,
        host_version=advertisement.host_version,
        protocol_version=advertisement.protocol_version,
        supports_stream_events=advertisement.supports_stream_events,
    )


def _endpoint_from_base_url(base_url: str) -> NetworkNodePublicEndpoint:
    parsed = urlparse(base_url.strip().rstrip("/"))
    hostname = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    scheme = parsed.scheme or "http"
    public_hostname = _public_hostname(hostname)
    return NetworkNodePublicEndpoint(
        hostname=public_hostname,
        port=port,
        base_url=f"{scheme}://{public_hostname}:{port}",
    )


def _public_hostname(hostname: str) -> str:
    normalized = hostname.strip()
    return "127.0.0.1" if normalized in {"", "0.0.0.0", "::"} else normalized


def _clean_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _int_env(name: str) -> int | None:
    value = _clean_env(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise RuntimeError(f"{name} must be positive, got {parsed}")
    return parsed


def _clean_tuple(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


__all__ = [
    "NetworkNodePublicEndpoint",
    "NetworkPublicationRuntime",
    "NetworkPublicationSdkClient",
    "build_node_runtime_publication_intent",
    "reconcile_node_runtime_publication",
    "resolve_node_public_endpoint",
]
