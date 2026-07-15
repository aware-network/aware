from pydantic import BaseModel
from typing import Self
from uuid import uuid4

from aware_network.network.node.local_info import LocalNetworkNodeInfo
from aware_network.network.node.manager import network_node_manager


def random_public_key() -> str:
    """Generate a random public key."""
    return str(uuid4())


class HelperTestNetworkNodeRegistry(BaseModel):
    network_node: LocalNetworkNodeInfo | None

    @classmethod
    async def create_random(
        cls,
        finance_entity: object | None = None,
        version: str = "0.1.0",
        container_template: str = "test",
    ) -> Self:
        _ = finance_entity, version, container_template
        return cls(
            network_node=network_node_manager.ensure_local_info(
                label="test-network-node",
            ),
        )

    @classmethod
    async def initialize_manager(
        cls,
        hostname: str = "test.node",
        port: int = 8000,
        public_key: str = "0x1234567890abcdef",
        version: str = "0.1.0",
        is_validator: bool = True,
        finance_entity: object | None = None,
    ) -> object | None:
        _ = hostname, port, public_key, version, is_validator
        network_node_manager.ensure_local_info(
            label="test-network-node",
        )
        return finance_entity

    @classmethod
    async def create(
        cls,
        finance_entity: object | None = None,
        hostname: str = "test.node",
        port: int = 8000,
        public_key: str = "0x1234567890abcdef",
        version: str = "0.1.0",
        is_validator: bool = True,
    ) -> Self:
        _ = finance_entity, hostname, port, public_key, version, is_validator
        return cls(
            network_node=network_node_manager.ensure_local_info(
                label="test-network-node",
            ),
        )

    async def unregister(self):
        if self.network_node:
            self.network_node = None
