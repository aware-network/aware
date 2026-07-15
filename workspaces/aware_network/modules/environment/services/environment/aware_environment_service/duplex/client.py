from aware_network.communications.duplex.client import NetworkDuplexClient

from aware_environment_service.duplex.duplex import EnvironmentDuplex


class EnvironmentDuplexClient(NetworkDuplexClient, EnvironmentDuplex):
    """
    Mixin for EnvironmentDuplexClient to use NetworkDuplexClient and EnvironmentDuplex
    implementing message building as Environment app
    """

    pass
