from aware_network_ontology.network.network_operation import (
    NetworkOperation,
)
from aware_network_ontology.network.network_response import NetworkResponse


def build_environment_response(
    network_response: NetworkResponse,
    environment_operation: object | None = None,
) -> NetworkOperation:
    _ = (network_response, environment_operation)
    raise RuntimeError(
        "NetworkOperation(type=environment) is retired; publish environment calls through "
        "NetworkOperation(type=api) or NetworkOperation(type=service)."
    )
