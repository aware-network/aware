from importlib import import_module

from aware_experience.connector.compiler import (
    load_connector_ownership_from_sources,
)

_PROTOCOL_RENDERER_EXPORTS = frozenset(
    {
        "CONNECTOR_PROTOCOL_PLAN_CONTRACT_VERSION",
        "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION",
        "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME",
        "ConnectorProtocolConnectorPlan",
        "ConnectorProtocolEndpointContractPlan",
        "ConnectorProtocolInvocationPlan",
        "ConnectorProtocolPlan",
        "ConnectorProtocolProviderPlan",
        "ConnectorProtocolSurfacePlan",
        "PythonConnectorProtocolRenderSection",
        "build_connector_protocol_plan",
        "build_python_connector_protocol_section_text_manifest",
        "encode_connector_protocol_plan",
        "endpoint_contract_from_service_protocol_binding",
        "render_python_connector_protocol_module",
        "render_python_connector_protocol_sections",
    }
)


def __getattr__(name: str) -> object:
    if name not in _PROTOCOL_RENDERER_EXPORTS:
        raise AttributeError(name)
    module = import_module("aware_experience.connector.protocol_renderer")
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "CONNECTOR_PROTOCOL_PLAN_CONTRACT_VERSION",
    "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION",
    "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME",
    "ConnectorProtocolConnectorPlan",
    "ConnectorProtocolEndpointContractPlan",
    "ConnectorProtocolInvocationPlan",
    "ConnectorProtocolPlan",
    "ConnectorProtocolProviderPlan",
    "ConnectorProtocolSurfacePlan",
    "PythonConnectorProtocolRenderSection",
    "build_connector_protocol_plan",
    "build_python_connector_protocol_section_text_manifest",
    "encode_connector_protocol_plan",
    "endpoint_contract_from_service_protocol_binding",
    "load_connector_ownership_from_sources",
    "render_python_connector_protocol_module",
    "render_python_connector_protocol_sections",
]
