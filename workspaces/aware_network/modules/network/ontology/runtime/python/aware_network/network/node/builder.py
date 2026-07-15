from aware_network_ontology.network.network_node import NetworkNode, NetworkNodeStatus
from aware_network_ontology.network.network_node_config import NetworkNodeConfig


async def build_network_node(
    config: NetworkNodeConfig,
    public_key: str,
    hostname: str,
    port: int,
    is_validator: bool = False,
    status: NetworkNodeStatus = NetworkNodeStatus.inactive,
    blockchain_height: int = 0,
) -> NetworkNode:
    """OCG-compliant factory for creating a NetworkNode instance.

    This method constructs a node object ready for ORM persistence via push().
    It does not perform DB writes itself.
    """
    node = NetworkNode(
        public_key=public_key,
        hostname=hostname,
        port=port,
        is_validator=is_validator,
        status=status,
        blockchain_height=blockchain_height,
        config_id=config.id,
        config=config,
    )
    return node
