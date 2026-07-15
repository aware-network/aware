# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_NETWORK = uuid5(NAMESPACE_URL, "aware://network/v1")


def stable_external_app_id(*, provider: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider"""

    provider_norm = (provider or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:external_app:{provider_norm}")


def stable_network_directory_id(*, name: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip() or "default"
    return uuid5(NS_NETWORK, f"aware:network_directory:{name_norm}")


def stable_network_node_id(*, public_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: public_key"""

    public_key_norm = (public_key or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:network_node:{public_key_norm}")


def stable_network_node_config_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:network_node_config:{name_norm}")


def stable_network_node_environment_id(*, network_node_id: UUID, environment_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_node_id, environment_id"""

    return uuid5(NS_NETWORK, f"aware:network_node_environment:{network_node_id}:{environment_id}")


def stable_network_node_member_id(*, identity_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id"""

    return uuid5(NS_NETWORK, f"aware:network_node_member:{identity_id}")


def stable_network_node_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:network_node_package:{name_norm}")


def stable_network_node_peer_id(*, source_peer_node_id: UUID, target_peer_node_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: source_peer_node_id, target_peer_node_id"""

    return uuid5(NS_NETWORK, f"aware:network_node_peer:{source_peer_node_id}:{target_peer_node_id}")


def stable_network_node_peer_fanout_rule_id(
    *, network_node_peer_id: UUID, lane_branch_id: UUID, lane_projection_hash: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_node_peer_id, lane_branch_id, lane_projection_hash"""

    lane_projection_hash_norm = (lane_projection_hash or "").casefold().strip()
    return uuid5(
        NS_NETWORK,
        f"aware:network_node_peer_fanout_rule:{network_node_peer_id}:{lane_branch_id}:{lane_projection_hash_norm}",
    )


def stable_network_node_service_id(*, network_node_id: UUID, service_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_node_id, service_package_id"""

    return uuid5(NS_NETWORK, f"aware:network_node_service:{network_node_id}:{service_package_id}")


def stable_network_node_validator_id(*, public_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: public_key"""

    public_key_norm = (public_key or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:network_node_validator:{public_key_norm}")


def stable_network_operation_id(*, message_type: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: message_type, type"""

    message_type_norm = (message_type or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_NETWORK, f"aware:network_operation:{message_type_norm}:{type_norm}")


def stable_network_operation_hop_id(*, hop_index: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: hop_index"""

    return uuid5(NS_NETWORK, f"aware:network_operation_hop:{hop_index}")


def stable_network_request_id(*, requester_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: requester_id"""

    return uuid5(NS_NETWORK, f"aware:network_request:{requester_id}")


def stable_network_response_id(*, network_request_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_request_id"""

    return uuid5(NS_NETWORK, f"aware:network_response:{network_request_id}")


def stable_network_stream_id(*, object_instance_graph_branch_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: object_instance_graph_branch_id"""

    return uuid5(NS_NETWORK, f"aware:network_stream:{object_instance_graph_branch_id}")


def stable_network_stream_frame_id(*, network_stream_id: UUID, seq: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: network_stream_id, seq"""

    return uuid5(NS_NETWORK, f"aware:network_stream_frame:{network_stream_id}:{seq}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "3c85b0a6-06d8-573c-affc-288aabe5b9f0": (
        "stable_network_node_environment_id",
        ("network_node_id", "environment_id"),
    ),
    "506be797-ee85-5003-8378-d6dfdee6e11c": (
        "stable_network_node_peer_fanout_rule_id",
        ("network_node_peer_id", "lane_branch_id", "lane_projection_hash"),
    ),
    "98e34abb-07bc-58a0-968a-6a50e8967d6b": ("stable_network_directory_id", ("name",)),
    "b0df3046-a64d-5865-8462-e357ad10ea08": ("stable_network_node_package_id", ("name",)),
    "c58f539f-b850-5bd9-9aa3-c9467f9dca61": ("stable_network_node_config_id", ("name",)),
    "cfe7a9ae-c32d-5651-98c5-4573cbf657b0": (
        "stable_network_node_service_id",
        ("network_node_id", "service_package_id"),
    ),
    "de1e6a4c-303f-5943-a309-cb8af1d24de1": ("stable_network_node_id", ("public_key",)),
}

__all__ = [
    "stable_external_app_id",
    "stable_network_directory_id",
    "stable_network_node_id",
    "stable_network_node_config_id",
    "stable_network_node_environment_id",
    "stable_network_node_member_id",
    "stable_network_node_package_id",
    "stable_network_node_peer_id",
    "stable_network_node_peer_fanout_rule_id",
    "stable_network_node_service_id",
    "stable_network_node_validator_id",
    "stable_network_operation_id",
    "stable_network_operation_hop_id",
    "stable_network_request_id",
    "stable_network_response_id",
    "stable_network_stream_id",
    "stable_network_stream_frame_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
