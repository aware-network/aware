from aware_network_ontology.network.network_operation import (
    NetworkOperation,
    NetworkOperationMessageType,
    NetworkOperationType,
)


def validate_polymorphism_and_type_constraints(
    network_operation: NetworkOperation,
) -> NetworkOperation:
    """
    Enforce message_type → FK XOR constraints and reject retired payload rails.

    Rules:
    - REQUEST: network_request_id set; response/stream/frame unset
    - RESPONSE: network_response_id set; request/stream/frame unset
    - STREAM: network_stream_id and network_stream_frame_id set; request/response unset
    - NOTIFICATION: none of request/response/stream/frame set

    - type=ENVIRONMENT / ENVIRONMENT_CONFIG: retired; Environment calls route through
      API/service operations, not embedded EnvironmentOperation payload fields.
    """
    # Message type constraints
    if network_operation.message_type == NetworkOperationMessageType.request:
        if network_operation.network_request_id is None:
            raise ValueError("REQUEST operations must include network_request_id")
        if any(
            x is not None
            for x in (
                network_operation.network_response_id,
                network_operation.network_stream_id,
                network_operation.network_stream_frame_id,
            )
        ):
            raise ValueError(
                "REQUEST operations must not include network_response_id, network_stream_id, or network_stream_frame_id"
            )
    elif network_operation.message_type == NetworkOperationMessageType.response:
        if network_operation.network_response_id is None:
            raise ValueError("RESPONSE operations must include network_response_id")
        if any(
            x is not None
            for x in (
                network_operation.network_request_id,
                network_operation.network_stream_id,
                network_operation.network_stream_frame_id,
            )
        ):
            raise ValueError(
                "RESPONSE operations must not include network_request_id, network_stream_id, or network_stream_frame_id"
            )
    elif network_operation.message_type == NetworkOperationMessageType.stream:
        if network_operation.network_stream_frame_id is None:
            raise ValueError("STREAM operations must include network_stream_frame_id")
        if any(
            x is not None
            for x in (
                network_operation.network_request_id,
                network_operation.network_response_id,
            )
        ):
            raise ValueError("STREAM operations must not include network_request_id or network_response_id")
    elif network_operation.message_type == NetworkOperationMessageType.notification:
        if any(
            x is not None
            for x in (
                network_operation.network_request_id,
                network_operation.network_response_id,
                network_operation.network_stream_id,
                network_operation.network_stream_frame_id,
            )
        ):
            raise ValueError(
                "NOTIFICATION operations must not include network_request_id, network_response_id, network_stream_id, or network_stream_frame_id"
            )
    else:
        raise ValueError(f"Unknown message type: {network_operation.message_type}")

    if network_operation.type in {
        NetworkOperationType.environment,
        NetworkOperationType.environment_config,
    }:
        raise ValueError(
            f"NetworkOperation(type={network_operation.type.value}) is retired; "
            "route through NetworkOperation(type=api) or NetworkOperation(type=service)"
        )

    return network_operation
