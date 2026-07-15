from aware_network_ontology.network.network_node import NetworkNode, NetworkNodeStatus
from aware_network_ontology.network.network_node_config import NetworkNodeConfig


def load_network_node(
    config: NetworkNodeConfig,
    public_key: str,
    hostname: str,
    port: int,
    is_validator: bool = False,
) -> NetworkNode:
    """Lightweight constructor for runtime use from LocalNetworkNodeInfo (no DB)."""
    return NetworkNode(
        public_key=public_key,
        hostname=hostname,
        port=port,
        is_validator=is_validator,
        status=NetworkNodeStatus.active,
        blockchain_height=0,
        config_id=config.id,
        config=config,
    )
