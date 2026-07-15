from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_network.network.node.manager import network_node_manager
from aware_network_service_dto.comms.models.network_service import NetworkPeerDescriptor
from aware_utils.logging import logger


class NetworkPeerBootstrapProviderInput(Protocol):
    @property
    def provider_node_id(self) -> UUID: ...

    @property
    def provider_node_base_url(self) -> str: ...


class NetworkPeerBootstrapSdkClient(Protocol):
    async def upsert_peer(
        self,
        *,
        source_node_id: UUID,
        target_node_id: UUID,
        target_base_url: str,
        status: str = "accepted",
        trust_score: float = 0.0,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkPeerDescriptor: ...


@dataclass(frozen=True, slots=True)
class NetworkProviderSetPeerBootstrapSummary:
    source_node_id: UUID
    peers: tuple[NetworkPeerDescriptor, ...]


async def bootstrap_network_peers_from_provider_inputs(
    *,
    network_sdk_client: NetworkPeerBootstrapSdkClient,
    provider_inputs: Sequence[NetworkPeerBootstrapProviderInput],
    actor_id: UUID | None = None,
) -> NetworkProviderSetPeerBootstrapSummary:
    source_node_id = network_node_manager.hosted_node_id
    provider_inputs_by_node = _provider_inputs_by_node(provider_inputs)
    peers = []
    for target_node_id, provider_input in provider_inputs_by_node.items():
        if target_node_id == source_node_id:
            continue
        peers.append(
            await network_sdk_client.upsert_peer(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                target_base_url=provider_input.provider_node_base_url,
                status="accepted",
                trust_score=0.0,
                actor_id=actor_id,
            )
        )
    if peers:
        logger.info(
            "Bootstrapped Network Service peer edges from provider refs "
            "(source_node_id=%s peer_count=%s)",
            source_node_id,
            len(peers),
        )
    return NetworkProviderSetPeerBootstrapSummary(
        source_node_id=source_node_id,
        peers=tuple(peers),
    )


def _provider_inputs_by_node(
    provider_inputs: Sequence[NetworkPeerBootstrapProviderInput],
) -> dict[UUID, NetworkPeerBootstrapProviderInput]:
    by_node: dict[UUID, NetworkPeerBootstrapProviderInput] = {}
    for provider_input in provider_inputs:
        base_url = provider_input.provider_node_base_url.strip()
        if not base_url:
            raise RuntimeError(
                "Remote Service API provider input requires provider_node_base_url."
            )
        existing = by_node.get(provider_input.provider_node_id)
        if existing is None:
            by_node[provider_input.provider_node_id] = provider_input
            continue
        existing_base_url = existing.provider_node_base_url.strip()
        if existing_base_url != base_url:
            raise RuntimeError(
                "Remote Service API provider refs disagree for provider node "
                f"{provider_input.provider_node_id}: "
                f"{existing_base_url!r} != {base_url!r}"
            )
    return by_node


__all__ = [
    "NetworkPeerBootstrapProviderInput",
    "NetworkPeerBootstrapSdkClient",
    "NetworkProviderSetPeerBootstrapSummary",
    "bootstrap_network_peers_from_provider_inputs",
]
