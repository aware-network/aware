from aware_network_ontology.network.network_stream_frame import (
    NetworkStreamFrame,
    NetworkStreamControl,
)


def validate_stream_frame_constraints(
    network_stream_frame: NetworkStreamFrame,
) -> NetworkStreamFrame:
    """
    Enforce control-specific constraints and sequencing invariants:
    - seq must be >= 1
    - DATA: object_instance_graph_branch_operation_id required, ack_seq must be NULL
    - HEARTBEAT: ack_seq required, object_instance_graph_branch_operation_id must be NULL
    - CLOSE: both ack_seq and object_instance_graph_branch_operation_id must be NULL
    """
    if network_stream_frame.seq < 1:
        raise ValueError("seq must be >= 1")

    if network_stream_frame.control == NetworkStreamControl.data:
        if network_stream_frame.object_instance_graph_branch_operation is None:
            raise ValueError("DATA frames require object_instance_graph_branch_operation")
        if network_stream_frame.ack_seq is not None:
            raise ValueError("DATA frames must not include ack_seq")
    elif network_stream_frame.control == NetworkStreamControl.heartbeat:
        if network_stream_frame.ack_seq is None:
            raise ValueError("HEARTBEAT frames require ack_seq")
        if network_stream_frame.object_instance_graph_branch_operation is not None:
            raise ValueError("HEARTBEAT frames must not include object_instance_graph_branch_operation")
    elif network_stream_frame.control == NetworkStreamControl.close:
        if network_stream_frame.ack_seq is not None:
            raise ValueError("CLOSE frames must not include ack_seq")
        if network_stream_frame.object_instance_graph_branch_operation is not None:
            raise ValueError("CLOSE frames must not include object_instance_graph_branch_operation")
    else:
        raise ValueError(f"Unknown stream control: {network_stream_frame.control}")

    return network_stream_frame
