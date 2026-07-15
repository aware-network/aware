from aware_network.communications.duplex.server import NetworkDuplexServer

from aware_node_service.duplex.duplex import NetworkNodeDuplex


class NetworkNodeDuplexServer(NetworkDuplexServer, NetworkNodeDuplex):
    """
    Mixin for NetworkNodeDuplexServer to use NetworkDuplexServer and NetworkNodeDuplex implementing message building as NetworkNode
    """

    pass
