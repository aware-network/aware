"""
Network node public configuration setup and exposure.
"""

import json
import os
from pathlib import Path
from typing import Optional

from aware_network.network.network_node_config import NetworkNodeConfig

from aware_utils.logging import logger


class PublicConfigManager:
    """
    Manages the exposure of network node public configuration.

    This class handles:
    1. Reading Docker configuration from host
    2. Writing network node config for container access
    3. Managing the location and format of the config
    """

    def __init__(self, config_dir: str = "/etc/aware"):
        """
        Initialize the public config manager.

        Args:
            config_dir: Directory where public configs are stored
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "network_node_config.json"

    def write_config(self, config: NetworkNodeConfig) -> None:
        """
        Write the network node config to a file.

        Args:
            config: The network node config to write
        """
        logger.info(f"Writing network node config to {self.config_file}")

        # Write to file
        with open(self.config_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)

        # Set proper permissions
        os.chmod(self.config_file, 0o644)

        logger.info("Network node config written successfully")

    def read_config(self) -> Optional[NetworkNodeConfig]:
        """
        Read the network node config from file.

        Returns:
            The network node config if it exists, None otherwise
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r") as f:
                config_dict = json.load(f)

            return NetworkNodeConfig.model_validate(config_dict)
        except Exception as e:
            logger.error(f"Error reading network node config: {e}")
            return None
