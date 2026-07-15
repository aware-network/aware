"""
Main setup module for the Aware Network Node.
"""

import asyncio

from aware_economy.setup import setup_economy

from aware_network.communications.app import NetworkApp
from aware_network.communications.duplex.router import NetworkRouter
from aware_network.setup.public_config_manager import PublicConfigManager
from aware_network.network.node.manager import network_node_manager
from aware_network_service_dto.network.network_enums import NetworkAppType

from aware_utils.logging import logger


async def setup_network_node() -> None:
    """
    Set up the complete Aware Network Node environment.

    This function orchestrates the setup of:
    1. Docker environment
    2. Network node configuration
    3. Core network components
    4. Intelligent object system

    Args:
        public_key: Optional public key for existing node
        hostname: Optional hostname for new node
        port: Optional port for new node
        is_validator: Whether this is a validator node
    """
    logger.info("Starting Aware Network Node setup")

    # Get network node public config
    network_node_public_config = PublicConfigManager().read_config()

    if not network_node_public_config:
        raise RuntimeError("Network node config not found")

    logger.info(f"Loaded config: {network_node_public_config.model_dump()}")
    logger.info("Setting up network node core components")

    # Setup economy (fundamental for blockchain participation)
    await setup_economy()

    # Initialize or create network node
    initialized = await network_node_manager.initialize_from_public_key(network_node_public_config.public_key)
    if initialized:
        logger.info("Initialized existing node")
    else:
        # !! TODO: CLARIFY THIS - NEED PROPER ONBOARDING.
        # Create new node
        # Note: finance_entity will be provided by the caller
        await network_node_manager.create_hosted_node(
            finance_entity=None,  # To be provided by caller
            hostname=network_node_public_config.hostname,
            port=network_node_public_config.port,
            public_key=network_node_public_config.public_key,
            version="0.1.0",
            is_validator=network_node_public_config.is_validator,
        )

    # Create Network Node App
    network_node_app = NetworkApp(app_type=NetworkAppType.network_node.value)
    await network_node_app.start()

    # Initialize Network Router
    NetworkRouter(network_node_app)

    logger.info("Network node core components setup complete")

    logger.info("Aware Network Node setup complete")


if __name__ == "__main__":
    asyncio.run(setup_network_node())
