from aware_network.communications.duplex.client import NetworkDuplexClient

from aware_node_service.duplex.duplex import NetworkNodeDuplex


class NetworkNodeDuplexClient(NetworkDuplexClient, NetworkNodeDuplex):
    """
    Mixin for NetworkNodeDuplexClient to use NetworkDuplexClient and NetworkNodeDuplex implementing message building as NetworkNode
    """

    pass
