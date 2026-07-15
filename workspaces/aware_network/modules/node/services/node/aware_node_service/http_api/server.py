from aware_network_service_dto.comms.models.network import NetworkAppType
from aware_comms.http import utils as http_utils
from aware_comms.http.file.router import FileRouter
from aware_comms.http.server import HttpServer, HttpServerConfig

from aware_node_service.http_api.file_ops import (
    download_file_handler,
    upload_file_handler,
)
from aware_node_service.http_api.auth import resolve_actor_id_from_bearer_token

# Install the node's canonical HTTP auth resolver for Bearer tokens.
http_utils.set_token_resolver(resolve_actor_id_from_bearer_token)

# Network Node HTTP Server
network_node_http_server = HttpServer(
    app_type=NetworkAppType.network_node.value,
    config=HttpServerConfig(requires_auth=True, requires_file_operations=True),
    route_metadata=[],
    routers={},
    file_router=FileRouter(
        upload_handler=upload_file_handler,
        download_handler=download_file_handler,
    ),
)
