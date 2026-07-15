# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "node-service-api"
API_FQN_PREFIX: Final[str] = "aware_node_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Read generic Node-owned hosted runtime "
                                "lifecycle status from the supervising "
                                "Node.",
                                "discriminant": "node.host.describe_hosted_runtimes",
                                "name": "describe_hosted_runtimes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedRuntimesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedRuntimesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Read live Node-owned hosted-service "
                                "runtime status from the supervising "
                                "Node.",
                                "discriminant": "node.host.describe_hosted_service_runtimes",
                                "name": "describe_hosted_service_runtimes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Discover Node-managed "
                                "EnvironmentConfig descriptors "
                                "available for live provisioning.",
                                "discriminant": "node.host.discover_environment_configs",
                                "name": "discover_environment_configs",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Discover Node-bound service API "
                                "dependency routes for live "
                                "service-to-service calls.",
                                "discriminant": "node.host.discover_service_api_dependency_routes",
                                "name": "discover_service_api_dependency_routes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverApiRoutesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverApiRoutesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Read the Node-managed BOOT environment "
                                "descriptor without client-side kernel "
                                "heuristics.",
                                "discriminant": "node.host.get_boot_environment_descriptor",
                                "name": "get_boot_environment_descriptor",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Read live Node-owned status for one "
                                "Environment provisioned on this node.",
                                "discriminant": "node.host.get_environment_status",
                                "name": "get_environment_status",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetEnvironmentStatusRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetEnvironmentStatusResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Provision or resume one Environment "
                                "through live Node host authority.",
                                "discriminant": "node.host.provision_environment",
                                "name": "provision_environment",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.ProvisionEnvironmentRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.ProvisionEnvironmentResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "description": "Request a generic Node-owned hosted "
                                "runtime restart through the "
                                "supervising Node.",
                                "discriminant": "node.host.restart_hosted_runtime",
                                "name": "restart_hosted_runtime",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.RestartHostedRuntimeRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.RestartHostedRuntimeResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                        ],
                        "name": "host",
                        "source_path": "bindings/node.apis.aware",
                    }
                ],
                "name": "node",
                "source_path": "bindings/node.apis.aware",
            }
        ],
        "fqn_prefix": "aware_node_service_api",
        "package_name": "node-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read generic Node-owned hosted runtime "
                                "lifecycle status from the supervising "
                                "Node.",
                                "discriminant": "node.host.describe_hosted_runtimes",
                                "endpoint_ref": "node.host.describe_hosted_runtimes",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_hosted_runtimes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedRuntimesRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.DescribeHostedRuntimesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedRuntimesResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.DescribeHostedRuntimesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read live Node-owned hosted-service "
                                "runtime status from the supervising "
                                "Node.",
                                "discriminant": "node.host.describe_hosted_service_runtimes",
                                "endpoint_ref": "node.host.describe_hosted_service_runtimes",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_hosted_service_runtimes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.DescribeHostedServiceRuntimesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.DescribeHostedServiceRuntimesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Discover Node-managed "
                                "EnvironmentConfig descriptors "
                                "available for live provisioning.",
                                "discriminant": "node.host.discover_environment_configs",
                                "endpoint_ref": "node.host.discover_environment_configs",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover_environment_configs",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.DiscoverEnvironmentConfigsRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.DiscoverEnvironmentConfigsResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Discover Node-bound service API "
                                "dependency routes for live "
                                "service-to-service calls.",
                                "discriminant": "node.host.discover_service_api_dependency_routes",
                                "endpoint_ref": "node.host.discover_service_api_dependency_routes",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover_service_api_dependency_routes",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverApiRoutesRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.DiscoverApiRoutesRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.DiscoverApiRoutesResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.DiscoverApiRoutesResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the Node-managed BOOT environment "
                                "descriptor without client-side kernel "
                                "heuristics.",
                                "discriminant": "node.host.get_boot_environment_descriptor",
                                "endpoint_ref": "node.host.get_boot_environment_descriptor",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_boot_environment_descriptor",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.GetBootEnvironmentDescriptorRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.GetBootEnvironmentDescriptorResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read live Node-owned status for one "
                                "Environment provisioned on this node.",
                                "discriminant": "node.host.get_environment_status",
                                "endpoint_ref": "node.host.get_environment_status",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_environment_status",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetEnvironmentStatusRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.GetEnvironmentStatusRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.GetEnvironmentStatusResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.GetEnvironmentStatusResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Provision or resume one Environment "
                                "through live Node host authority.",
                                "discriminant": "node.host.provision_environment",
                                "endpoint_ref": "node.host.provision_environment",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "provision_environment",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.ProvisionEnvironmentRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.ProvisionEnvironmentRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.ProvisionEnvironmentResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.ProvisionEnvironmentResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Request a generic Node-owned hosted "
                                "runtime restart through the "
                                "supervising Node.",
                                "discriminant": "node.host.restart_hosted_runtime",
                                "endpoint_ref": "node.host.restart_hosted_runtime",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "restart_hosted_runtime",
                                "request": {
                                    "class_ref": "aware_node_service_dto.comms.models.RestartHostedRuntimeRequest",
                                    "python_model_ref": "aware_node_service_dto.node.host.RestartHostedRuntimeRequest",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_node_service_dto.comms.models.RestartHostedRuntimeResponse",
                                    "python_model_ref": "aware_node_service_dto.node.host.RestartHostedRuntimeResponse",
                                    "source_path": "bindings/node.apis.aware",
                                },
                                "source_path": "bindings/node.apis.aware",
                            },
                        ],
                        "name": "host",
                        "source_path": "bindings/node.apis.aware",
                    }
                ],
                "name": "node",
                "source_path": "bindings/node.apis.aware",
            }
        ],
        "fqn_prefix": "aware_node_service_api",
        "package_name": "node-service-api",
        "schema_version": 1,
    }
)

NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF: Final[str] = "node.host.describe_hosted_runtimes"
NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF: Final[str] = "node.host.describe_hosted_service_runtimes"
NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF: Final[str] = "node.host.discover_environment_configs"
NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: Final[str] = (
    "node.host.discover_service_api_dependency_routes"
)
NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF: Final[str] = "node.host.get_boot_environment_descriptor"
NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF: Final[str] = "node.host.get_environment_status"
NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF: Final[str] = "node.host.provision_environment"
NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF: Final[str] = "node.host.restart_hosted_runtime"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "node.host.describe_hosted_runtimes": NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF,
    "node.host.describe_hosted_service_runtimes": NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF,
    "node.host.discover_environment_configs": NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF,
    "node.host.discover_service_api_dependency_routes": NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
    "node.host.get_boot_environment_descriptor": NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF,
    "node.host.get_environment_status": NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF,
    "node.host.provision_environment": NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF,
    "node.host.restart_hosted_runtime": NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF",
    "NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF",
    "NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF",
    "NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF",
    "NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF",
    "NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF",
    "NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF",
    "NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF",
]
