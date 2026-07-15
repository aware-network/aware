from aware_network.communications.duplex.server import NetworkDuplexServer

from aware_environment_service.duplex.duplex import EnvironmentDuplex


class EnvironmentDuplexServer(NetworkDuplexServer, EnvironmentDuplex):
    """
    Mixin for EnvironmentDuplexServer to use NetworkDuplexServer and EnvironmentDuplex
    implementing message building as Environment app
    """

    pass
