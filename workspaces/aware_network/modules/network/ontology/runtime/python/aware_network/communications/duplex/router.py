"""
Network Router for network communication with hop-based routing.
"""

from typing import Optional
from uuid import UUID

# Logging
from aware_utils.logging import logger

# Core communications
from aware_comms.duplex.websocket.models import WsMessageFrameType

# Network communications
from aware_network.communications.app import NetworkApp

# Network Duplex
from aware_network.communications.duplex.duplex import NetworkDuplex
from aware_network.communications.interface_session_binding_manager import (
    InterfaceSessionBindingManager,
)

# Network Router Interface
from aware_network.communications.duplex.router_interface import (
    NetworkRouterInterface,
    NetworkFrameHandler,
)

# Network Node Manager
from aware_network.network.node.manager import network_node_manager

# NetworkOperation handling (protocol DTOs; no ORM dependency)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
)


class NetworkRouter(NetworkRouterInterface):
    """
    Central router for all network communication using hop-based routing.

    This class:
    1. Routes NetworkOperations using hop-based headers (single hop in hop_list)
    2. Maintains audit trail by persisting hops to database
    3. Handles privacy by stripping interface IDs when crossing node boundaries
    4. Supports path disclosure for compliance/diagnostics when needed
    """

    def __init__(self, network_app: NetworkApp):
        """Initialize the network router"""
        self._network_app = network_app

    # ===============================
    # Hop Management Helper Methods
    # ===============================

    def _get_current_header(self, network_op: NetworkOperation) -> NetworkOperationHop:
        """
        Get the current routing header from the hop list.

        Args:
            network_op: NetworkOperation with hop_list

        Returns:
            Current routing header (single hop)

        Raises:
            RuntimeError: If hop_list doesn't contain exactly one hop
        """
        if len(network_op.network_operation_hop_list) != 1:
            raise RuntimeError(
                f"NetworkOperation hop_list must contain exactly 1 hop (header), "
                f"found {len(network_op.network_operation_hop_list)}"
            )
        return network_op.network_operation_hop_list[0]

    async def _get_next_hop_index(self, network_operation_id: UUID) -> int:
        """
        Get the next hop index for a NetworkOperation.

        Args:
            network_operation_id: The NetworkOperation ID

        Returns:
            Next hop index to use
        """
        try:
            # TODO: In real implementation, query the database:
            # SELECT COALESCE(MAX(hop_index), -1) + 1 FROM network_operation_hop
            # WHERE network_operation_id = ?

            # For now, return a simple increment
            # In production, this would be handled by the database
            return 0  # Placeholder - always start at 0 for now

        except Exception as e:
            logger.error(f"Error getting next hop index: {e}")
            return 0

    async def _persist_hop_for_audit(self, network_op: NetworkOperation, hop: NetworkOperationHop) -> int:
        """
        Persist a hop to the database for audit trail.

        Args:
            network_op: The NetworkOperation
            hop: The hop to persist

        Returns:
            The hop index that was assigned
        """
        try:
            # Get next hop index
            next_hop_index = await self._get_next_hop_index(network_op.id)

            # NOTE: Audit persistence is node-implementation specific and must use
            # canonical graph ontology ORM models. Protocol-level hops are DTOs.
            # TODO: Convert + persist in node service when DB/graph storage is wired.

            logger.debug(
                f"Persisted hop {next_hop_index} for NetworkOperation {network_op.id}: "
                f"{hop.source_app_type}({hop.source_node_id}) -> "
                f"{hop.target_app_type}({hop.target_node_id})"
            )
            return next_hop_index

        except Exception as e:
            logger.error(f"Error persisting hop for audit: {e}")
            raise

    def _create_next_hop(
        self,
        current_hop: NetworkOperationHop,
        target_app_type: NetworkAppType,
        target_node_id: Optional[UUID] = None,
        target_interface_id: Optional[UUID] = None,
        strip_source_interface: bool = True,
    ) -> NetworkOperationHop:
        """
        Create the next hop for forwarding.

        Args:
            current_hop: The current hop (becomes the source of next hop)
            target_app_type: Platform type of the target
            target_node_id: Target node ID
            target_interface_id: Target interface ID
            strip_source_interface: Whether to strip source interface ID for privacy

        Returns:
            New hop for the next leg of routing
        """
        # Current target becomes new source
        source_app_type = current_hop.target_app_type
        source_node_id = current_hop.target_node_id
        source_interface_id = current_hop.target_interface_id

        # Strip interface ID when crossing node boundaries for privacy
        if strip_source_interface and source_app_type == NetworkAppType.interface:
            source_app_type = NetworkAppType.network_node
            source_interface_id = None
            # source_node_id stays the same - we know which node hosts the interface

        return NetworkOperationHop(
            source_app_type=source_app_type,
            source_node_id=source_node_id,
            source_interface_id=source_interface_id,
            target_app_type=target_app_type,
            target_node_id=target_node_id,
            target_interface_id=target_interface_id,
        )

    def _is_target_this_node(self, hop: NetworkOperationHop) -> bool:
        """
        Check if the current hop targets this node.

        Args:
            hop: The hop to check

        Returns:
            True if this node is the target
        """
        return (
            hop.target_app_type in [NetworkAppType.network_node, NetworkAppType.interface]
            and hop.target_node_id == network_node_manager.hosted_node_id
        )

    # ===============================
    # Routing Implementation
    # ===============================

    async def _forward_to_target_node(self, network_op: NetworkOperation) -> bool:
        """
        Forward NetworkOperation to target node using hop-based routing

        Args:
            network_op: The NetworkOperation to forward

        Returns:
            True if successful, False otherwise
        """
        try:
            current_hop = self._get_current_header(network_op)

            # Persist current hop for audit trail
            await self._persist_hop_for_audit(network_op, current_hop)

            target_node_id = current_hop.target_node_id
            if not target_node_id:
                raise RuntimeError("NetworkOperationHop missing target_node_id")

            duplex = self._get_duplex_for_connection(target_node_id)

            if not duplex:
                raise RuntimeError(f"No connection to target node {target_node_id}")

            # Create hop to target node (source becomes this node, target stays the same)
            next_hop = self._create_next_hop(
                current_hop=current_hop,
                target_app_type=current_hop.target_app_type,
                target_node_id=current_hop.target_node_id,
                target_interface_id=current_hop.target_interface_id,
                strip_source_interface=True,  # Strip interface info for privacy
            )

            # Update hop list with new header
            network_op.network_operation_hop_list = [next_hop]

            # Send NetworkOperation to target node
            response = await duplex.send_request(
                connection_id=target_node_id,
                data_serialized=network_op.model_dump_json(),
            )

            return response is not None

        except Exception as e:
            logger.error(f"Error forwarding NetworkOperation to target node: {e}")
            return False

    # ===============================
    # Registering Handlers
    # ===============================

    def register_handler(
        self,
        app_type: NetworkAppType,
        message_type: WsMessageFrameType,
        handler: NetworkFrameHandler,
    ) -> None:
        """Register a handler for a message type"""
        network_duplex = self._network_app.get_duplex(app_type)
        if not isinstance(network_duplex, NetworkDuplex):
            raise ValueError(f"Expected NetworkDuplex, got {type(network_duplex)}")
        network_duplex.register_handler(message_type, handler)

    def unregister_handler(
        self,
        app_type: NetworkAppType,
        message_type: WsMessageFrameType,
        handler: NetworkFrameHandler,
    ) -> None:
        """Unregister a handler for a message type"""
        network_duplex = self._network_app.get_duplex(app_type)
        if not isinstance(network_duplex, NetworkDuplex):
            raise ValueError(f"Expected NetworkDuplex, got {type(network_duplex)}")
        network_duplex.unregister_handler(message_type, handler)

    async def is_local_identity(self, identity_id: UUID) -> bool:
        """Check if we are the host node for this identity."""
        try:
            host_node_id = await self.get_host_node_id(identity_id)
            if host_node_id is None:
                return False
            return self.is_local_host(host_node_id)
        except Exception as e:
            logger.error(f"Error checking if identity {identity_id} is local: {e}")
            return False

    def is_local_host(self, node_id: UUID) -> bool:
        """Check if the node is the local host."""
        return node_id == network_node_manager.hosted_node_id

    async def get_host_node_id(self, identity_id: UUID) -> Optional[UUID]:
        """Resolve the host node id for an identity.

        The transport/router layer is graph-agnostic. For now we only resolve
        identities that have an active local interface session bound to this
        node; remote identity resolution must be implemented via the runtime
        directory/identity lane (OIG pipeline).
        """
        try:
            contexts = await InterfaceSessionBindingManager.instance().get_active_bindings_for_identity(identity_id)
        except Exception as exc:
            logger.error("Failed to resolve host node for identity %s: %s", identity_id, exc)
            return None
        if not contexts:
            return None
        return network_node_manager.hosted_node_id

    def _get_duplex_for_connection(self, connection_id: UUID) -> Optional[NetworkDuplex]:
        """Get the duplex for a connection."""
        if self._network_app is None:
            logger.error("WebsocketObjectManager not initialized")
            return None

        # Get duplex for responding
        duplex = self._network_app.get_duplex_for_connection(connection_id)
        if duplex is None:
            logger.error(f"No duplex found for connection {connection_id}")
            return None

        return duplex

    async def get_node_id(self, identity_id: UUID) -> Optional[UUID]:
        """Alias for `get_host_node_id` (kept for historical callers)."""
        return await self.get_host_node_id(identity_id)

    async def get_interface_ids(self, identity_id: UUID) -> list[UUID]:
        """Get interface IDs for an identity."""
        try:
            contexts = await InterfaceSessionBindingManager.instance().get_active_bindings_for_identity(identity_id)
            return [ctx.connection_id for ctx in contexts]
        except Exception as e:
            logger.error(f"Error getting interface IDs for identity {identity_id}: {e}")
            return []

    # ===============================
    # Utility Methods for NetworkOperation Creation
    # ===============================

    def create_initial_hop(
        self,
        source_app_type: NetworkAppType,
        source_node_id: Optional[UUID] = None,
        source_interface_id: Optional[UUID] = None,
        target_app_type: NetworkAppType = NetworkAppType.network_node,
        target_node_id: Optional[UUID] = None,
        target_interface_id: Optional[UUID] = None,
    ) -> NetworkOperationHop:
        """
        Create an initial hop for a new NetworkOperation.

        This is typically used when an interface creates a new request.

        Args:
            source_app_type: Platform type of the source
            source_node_id: Source node ID
            source_interface_id: Source interface ID
            target_app_type: Platform type of the target
            target_node_id: Target node ID
            target_interface_id: Target interface ID

        Returns:
            Initial hop for the NetworkOperation
        """
        return NetworkOperationHop(
            source_app_type=source_app_type,
            source_node_id=source_node_id,
            source_interface_id=source_interface_id,
            target_app_type=target_app_type,
            target_node_id=target_node_id,
            target_interface_id=target_interface_id,
        )

    async def get_hop_audit_trail(self, network_operation_id: UUID) -> list[NetworkOperationHop]:
        """
        Get the complete hop audit trail for a NetworkOperation.

        Args:
            network_operation_id: The NetworkOperation ID

        Returns:
            List of hops in chronological order
        """
        # NOTE: Audit persistence must be implemented using canonical ORM models in
        # the node service. This router operates on protocol DTOs only.
        logger.warning(
            "Hop audit trail lookup not implemented (network_operation_id=%s)",
            network_operation_id,
        )
        return []

    def validate_hop_constraints(self, hop: NetworkOperationHop) -> bool:
        """
        Validate that a hop meets the XOR constraints for platform types.

        Args:
            hop: The hop to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate source constraints
            if hop.source_app_type == NetworkAppType.network_node:
                if hop.source_node_id is None:
                    logger.error("Source node ID is required for NetworkNode")
                    return False
            elif hop.source_app_type == NetworkAppType.interface:
                if hop.source_interface_id is None:
                    logger.error("Source interface ID is required for Interface")
                    return False
            elif hop.source_app_type == NetworkAppType.environment:
                if hop.source_environment_id is None:
                    logger.error("Source environment ID is required for Environment")
                    return False

            # Validate target constraints
            if hop.target_app_type == NetworkAppType.network_node:
                if hop.target_node_id is None:
                    logger.error("Target node ID is required for NetworkNode")
                    return False
            elif hop.target_app_type == NetworkAppType.interface:
                if hop.target_interface_id is None:
                    logger.error("Target interface ID is required for Interface")
                    return False
            elif hop.target_app_type == NetworkAppType.environment:
                if hop.target_environment_id is None:
                    logger.error("Target environment ID is required for Environment")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating hop constraints: {e}")
            return False
