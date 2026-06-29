"""Thin public entrypoint for generated Aware API clients."""

from __future__ import annotations

__all__ = [
    "ApiInterfaceCapabilityBinding",
    "ApiInterfaceEndpointBinding",
    "ApiInterfaceIndex",
    "ApiEndpointInvocation",
    "ApiEndpointResponse",
    "ApiEndpointStream",
    "ApiEndpointStreamTransport",
    "ApiEndpointTransport",
    "AwareApiEndpointInvoker",
    "LoadedApiInterface",
    "build_api_interface_index",
    "decode_api_endpoint_response_payload",
    "decode_api_stream_event_payload",
    "load_api_interface_spec_file",
    "load_api_interface_spec_json",
    "load_api_interface_spec_payload",
    "resolve_api_endpoint_model_class",
]


def __getattr__(name: str):  # noqa: ANN201 - module-level dynamic export
    if name == "AwareApiContext":
        from .context import AwareApiContext

        return AwareApiContext
    if name in {
        "ApiEndpointInvocation",
        "ApiEndpointResponse",
        "ApiEndpointStream",
        "ApiEndpointStreamTransport",
        "ApiEndpointTransport",
        "AwareApiEndpointInvoker",
        "decode_api_endpoint_response_payload",
        "decode_api_stream_event_payload",
        "resolve_api_endpoint_model_class",
    }:
        from .invoker import (
            ApiEndpointInvocation,
            ApiEndpointResponse,
            ApiEndpointStream,
            ApiEndpointStreamTransport,
            ApiEndpointTransport,
            AwareApiEndpointInvoker,
            decode_api_endpoint_response_payload,
            decode_api_stream_event_payload,
            resolve_api_endpoint_model_class,
        )

        exports = {
            "ApiEndpointInvocation": ApiEndpointInvocation,
            "ApiEndpointResponse": ApiEndpointResponse,
            "ApiEndpointStream": ApiEndpointStream,
            "ApiEndpointStreamTransport": ApiEndpointStreamTransport,
            "ApiEndpointTransport": ApiEndpointTransport,
            "AwareApiEndpointInvoker": AwareApiEndpointInvoker,
            "decode_api_endpoint_response_payload": decode_api_endpoint_response_payload,
            "decode_api_stream_event_payload": decode_api_stream_event_payload,
            "resolve_api_endpoint_model_class": resolve_api_endpoint_model_class,
        }
        return exports[name]
    if name in {
        "ApiInterfaceCapabilityBinding",
        "ApiInterfaceEndpointBinding",
        "ApiInterfaceIndex",
        "LoadedApiInterface",
        "build_api_interface_index",
        "load_api_interface_spec_file",
        "load_api_interface_spec_json",
        "load_api_interface_spec_payload",
    }:
        from .interface import (
            ApiInterfaceCapabilityBinding,
            ApiInterfaceEndpointBinding,
            ApiInterfaceIndex,
            LoadedApiInterface,
            build_api_interface_index,
            load_api_interface_spec_file,
            load_api_interface_spec_json,
            load_api_interface_spec_payload,
        )

        exports = {
            "ApiInterfaceCapabilityBinding": ApiInterfaceCapabilityBinding,
            "ApiInterfaceEndpointBinding": ApiInterfaceEndpointBinding,
            "ApiInterfaceIndex": ApiInterfaceIndex,
            "LoadedApiInterface": LoadedApiInterface,
            "build_api_interface_index": build_api_interface_index,
            "load_api_interface_spec_file": load_api_interface_spec_file,
            "load_api_interface_spec_json": load_api_interface_spec_json,
            "load_api_interface_spec_payload": load_api_interface_spec_payload,
        }
        return exports[name]
    raise AttributeError(name)
