from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from aware_network_service_dto.comms.view.territory_discovery import (
    NetworkTerritoryDiscoveryViewStateV1,
    NetworkTerritoryEnvironmentViewStateV1,
    NetworkTerritoryHostedServiceViewStateV1,
    NetworkTerritoryNodeRouteViewStateV1,
    NetworkTerritoryNodeViewStateV1,
    NetworkTerritoryPeerViewStateV1,
)
from pydantic import BaseModel, ConfigDict, Field

NETWORK_TERRITORY_DISCOVERY_API_VIEW_REF = "network.territory_discovery"
NETWORK_TERRITORY_DISCOVERY_PROJECTION_VIEW_KEY = "territory.discovery.v1"


class ViewProviderProvenanceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source_kind: str | None = Field(default="network_service_api")
    authority_source_url: str | None = Field(default=None)
    request_id: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_provider_ref: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class NetworkTerritoryDiscoveryV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    receipt: Any | None = Field(default=None)
    authority_source_url: str | None = Field(default=None)
    error: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        payload = self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"receipt"},
        )
        if self.receipt is not None:
            payload["has_receipt"] = True
        return payload


class NetworkTerritoryDiscoveryClient(Protocol):
    async def discover_territory(
        self,
        *,
        node_id: UUID | None = None,
        include_peers: bool = True,
        include_hosted_services: bool = True,
        include_environments: bool = True,
        active_environments_only: bool = True,
        accepted_peers_only: bool = True,
        limit_nodes: int | None = 200,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> object: ...


async def network_territory_discovery_v1_provider_input_from_client(
    *,
    client: NetworkTerritoryDiscoveryClient,
    node_id: UUID | None = None,
    include_peers: bool = True,
    include_hosted_services: bool = True,
    include_environments: bool = True,
    active_environments_only: bool = True,
    accepted_peers_only: bool = True,
    limit_nodes: int | None = 200,
    actor_id: UUID | None = None,
    request_id: UUID | None = None,
    authority_source_url: str | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
    raise_errors: bool = False,
) -> NetworkTerritoryDiscoveryV1ProviderInput:
    base_provenance = _provider_provenance(provenance)
    try:
        receipt = await client.discover_territory(
            node_id=node_id,
            include_peers=include_peers,
            include_hosted_services=include_hosted_services,
            include_environments=include_environments,
            active_environments_only=active_environments_only,
            accepted_peers_only=accepted_peers_only,
            limit_nodes=limit_nodes,
            actor_id=actor_id,
            request_id=request_id,
        )
    except Exception as exc:
        if raise_errors:
            raise
        return NetworkTerritoryDiscoveryV1ProviderInput(
            authority_source_url=authority_source_url,
            error=str(exc),
            provenance=base_provenance,
        )
    return NetworkTerritoryDiscoveryV1ProviderInput(
        receipt=receipt,
        authority_source_url=authority_source_url
        or _optional_text(_field(receipt, "authority_source_url"))
        or base_provenance.authority_source_url,
        provenance=_provider_provenance(
            {
                **base_provenance.to_json(),
                "request_id": _optional_text(_field(receipt, "request_id"))
                or base_provenance.request_id,
            }
        ),
    )


def network_territory_discovery_v1_provider_input(
    provider_context: object,
) -> NetworkTerritoryDiscoveryV1ProviderInput:
    return NetworkTerritoryDiscoveryV1ProviderInput(
        receipt=_context_value(
            provider_context,
            "network_territory_receipt",
            "territory_receipt",
            "receipt",
        ),
        authority_source_url=_optional_text(
            _context_value(provider_context, "authority_source_url")
        ),
        error=_optional_text(
            _context_value(provider_context, "network_territory_error", "error")
        ),
        provenance=_provider_provenance(
            _mapping_payload(_context_value(provider_context, "provenance"))
        ),
    )


def network_territory_discovery_view_state_from_input(
    provider_input: NetworkTerritoryDiscoveryV1ProviderInput | Mapping[str, Any],
) -> NetworkTerritoryDiscoveryViewStateV1:
    typed_input = NetworkTerritoryDiscoveryV1ProviderInput.model_validate(
        provider_input
    )
    nodes = [_territory_node(node) for node in _receipt_nodes(typed_input.receipt)]
    status = _view_status(typed_input, nodes)
    return NetworkTerritoryDiscoveryViewStateV1(
        status=status,
        authority_source_url=typed_input.authority_source_url,
        nodes=nodes,
        summary=_summary(typed_input, nodes=nodes),
        error=typed_input.error,
        provenance=_provenance_payload(typed_input, nodes=nodes),
    )


def network_territory_discovery_view_state(
    *,
    provider_input: NetworkTerritoryDiscoveryV1ProviderInput | Mapping[str, Any],
) -> NetworkTerritoryDiscoveryViewStateV1:
    return network_territory_discovery_view_state_from_input(provider_input)


setattr(
    network_territory_discovery_view_state,
    "provider_input_resolver",
    network_territory_discovery_v1_provider_input,
)


def _territory_node(node: object) -> NetworkTerritoryNodeViewStateV1:
    return NetworkTerritoryNodeViewStateV1(
        node=_node_route(_field(node, "node")),
        environments=[
            _environment(environment)
            for environment in _iterable(_field(node, "environments"))
        ],
        hosted_services=[
            _hosted_service(hosted_service)
            for hosted_service in _iterable(_field(node, "hosted_services"))
        ],
        peers=[_peer(peer) for peer in _iterable(_field(node, "peers"))],
    )


def _node_route(node: object | None) -> NetworkTerritoryNodeRouteViewStateV1 | None:
    if node is None:
        return None
    return NetworkTerritoryNodeRouteViewStateV1(
        node_id=_optional_text(_field(node, "node_id")),
        public_key=_optional_text(_field(node, "public_key")),
        hostname=_optional_text(_field(node, "hostname")),
        port=_optional_int(_field(node, "port")),
        base_url=_optional_text(_field(node, "base_url")),
        status=_optional_text(_field(node, "status")) or "active",
        last_seen_at=_optional_text(_field(node, "last_seen_at")),
    )


def _environment(environment: object) -> NetworkTerritoryEnvironmentViewStateV1:
    return NetworkTerritoryEnvironmentViewStateV1(
        node_id=_optional_text(_field(environment, "node_id")),
        environment_id=_optional_text(_field(environment, "environment_id")),
        environment_key=_optional_text(_field(environment, "environment_key")),
        environment_title=_optional_text(_field(environment, "environment_title")),
        role=_optional_text(_field(environment, "role")) or "replica",
        is_active=_optional_bool(_field(environment, "is_active"), default=True),
        priority=_optional_int(_field(environment, "priority")) or 0,
        status=_optional_text(_field(environment, "status")) or "active",
        experience_names=_string_list(_field(environment, "experience_names")),
        environment_config_id=_optional_text(
            _field(environment, "environment_config_id")
        ),
        environment_config_key=_optional_text(
            _field(environment, "environment_config_key")
        ),
    )


def _hosted_service(
    hosted_service: object,
) -> NetworkTerritoryHostedServiceViewStateV1:
    return NetworkTerritoryHostedServiceViewStateV1(
        service_id=_optional_text(_field(hosted_service, "service_id")),
        service_name=_optional_text(_field(hosted_service, "service_name")),
        service_package_names=_string_list(
            _field(hosted_service, "service_package_names")
        ),
        endpoint_refs=_string_list(_field(hosted_service, "endpoint_refs")),
        stream_endpoint_refs=_string_list(
            _field(hosted_service, "stream_endpoint_refs")
        ),
        host_id=_optional_text(_field(hosted_service, "host_id")),
        host_version=_optional_text(_field(hosted_service, "host_version")),
        protocol_version=_optional_text(_field(hosted_service, "protocol_version")),
        supports_stream_events=_optional_bool(
            _field(hosted_service, "supports_stream_events"),
            default=False,
        ),
    )


def _peer(peer: object) -> NetworkTerritoryPeerViewStateV1:
    return NetworkTerritoryPeerViewStateV1(
        edge_id=_optional_text(_field(peer, "edge_id")),
        source_node_id=_optional_text(_field(peer, "source_node_id")),
        target_node_id=_optional_text(_field(peer, "target_node_id")),
        peer_node_id=_optional_text(_field(peer, "peer_node_id")),
        peer_base_url=_optional_text(_field(peer, "peer_base_url")),
        direction=_optional_text(_field(peer, "direction")) or "outgoing",
        status=_optional_text(_field(peer, "status")) or "accepted",
        trust_score=_optional_float(_field(peer, "trust_score")) or 0.0,
        connected_at=_optional_text(_field(peer, "connected_at")),
        last_ping_at=_optional_text(_field(peer, "last_ping_at")),
    )


def _receipt_nodes(receipt: object | None) -> tuple[object, ...]:
    return tuple(_iterable(_field(receipt, "nodes")))


def _view_status(
    provider_input: NetworkTerritoryDiscoveryV1ProviderInput,
    nodes: list[NetworkTerritoryNodeViewStateV1],
) -> str:
    if provider_input.error:
        return "unavailable"
    if nodes:
        return "live"
    return "waiting"


def _summary(
    provider_input: NetworkTerritoryDiscoveryV1ProviderInput,
    *,
    nodes: list[NetworkTerritoryNodeViewStateV1],
) -> str:
    receipt_summary = _optional_text(_field(provider_input.receipt, "summary"))
    if receipt_summary:
        return receipt_summary
    environment_count = sum(len(node.environments) for node in nodes)
    hosted_service_count = sum(len(node.hosted_services) for node in nodes)
    return (
        f"{len(nodes)} nodes, "
        f"{environment_count} environments, "
        f"{hosted_service_count} hosted services"
    )


def _provenance_payload(
    provider_input: NetworkTerritoryDiscoveryV1ProviderInput,
    *,
    nodes: list[NetworkTerritoryNodeViewStateV1],
) -> dict[str, Any]:
    payload = provider_input.provenance.to_json()
    payload.update(
        {
            "view_ref": NETWORK_TERRITORY_DISCOVERY_API_VIEW_REF,
            "projection_view_key": NETWORK_TERRITORY_DISCOVERY_PROJECTION_VIEW_KEY,
            "state_provider_ref": (
                "aware_network_sdk.view_state_providers."
                "network_territory_discovery_view_state"
            ),
            "node_count": len(nodes),
            "environment_count": sum(len(node.environments) for node in nodes),
            "hosted_service_count": sum(len(node.hosted_services) for node in nodes),
        }
    )
    return payload


def _provider_provenance(
    value: ViewProviderProvenanceV1 | Mapping[str, Any] | None,
) -> ViewProviderProvenanceV1:
    if isinstance(value, ViewProviderProvenanceV1):
        return value
    return ViewProviderProvenanceV1.model_validate(value or {})


def _field(value: object | None, name: str) -> object | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _context_value(provider_context: object, *names: str) -> object | None:
    for name in names:
        value = _field(provider_context, name)
        if value is not None:
            return value
    return None


def _mapping_payload(value: object | None) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    return None


def _iterable(value: object | None) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _string_list(value: object | None) -> list[str]:
    return [
        text for text in (_optional_text(item) for item in _iterable(value)) if text
    ]


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object | None) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _optional_float(value: object | None) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _optional_bool(value: object | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() not in {"", "0", "false", "no", "off"}
    return bool(value)


__all__ = [
    "NetworkTerritoryDiscoveryClient",
    "NetworkTerritoryDiscoveryV1ProviderInput",
    "ViewProviderProvenanceV1",
    "network_territory_discovery_v1_provider_input",
    "network_territory_discovery_v1_provider_input_from_client",
    "network_territory_discovery_view_state",
    "network_territory_discovery_view_state_from_input",
]
