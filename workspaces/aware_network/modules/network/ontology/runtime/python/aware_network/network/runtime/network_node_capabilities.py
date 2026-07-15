from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID
from typing import Optional, TYPE_CHECKING

from aware_network.network.network_node import NetworkNode
from aware_economy.blockchain.blockchain_interfaces import IBlockchainOperations

if TYPE_CHECKING:
    from aware_economy.transaction.transaction import Transaction
    from aware_economy.escrow.escrow import Escrow
    from aware_economy.wallet.wallet_public import WalletPublic


class NetworkNodeCapabilities(IBlockchainOperations):
    """
    Runtime capabilities for a NetworkNode, separated from the ORM model to comply with OCG.

    Phase A: Surface IBlockchainOperations with placeholders. Future phases will
    initialize validator/consensus managers and wire to ORM models for persistence.
    """

    def __init__(self, node: NetworkNode) -> None:
        self._logger = logging.getLogger(__name__)
        self._node: NetworkNode = node
        self._initialized: bool = False

    @property
    def node(self) -> NetworkNode:
        return self._node

    async def initialize_runtime(self) -> None:
        """Initialize runtime managers (validator/consensus/transaction pool).

        Placeholder for now to keep adapter ready for router integration.
        """
        self._initialized = True
        self._logger.info("NetworkNodeCapabilities initialized (placeholder)")

    # ============== IBlockchainOperations ==============
    async def make_transaction(
        self,
        *,
        source_wallet_public: WalletPublic,
        target_wallet_public: WalletPublic,
        coin_id: UUID,
        amount: Decimal,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Transaction:
        raise NotImplementedError("make_transaction not yet implemented in capabilities (Phase B)")

    async def make_escrow(
        self,
        *,
        wallet_public: WalletPublic,
        coin_id: UUID,
        amount: Decimal,
        description: Optional[str] = None,
    ) -> Escrow:
        raise NotImplementedError("make_escrow not yet implemented in capabilities (Phase B)")

    async def release_escrow(self, escrow: Escrow) -> None:
        raise NotImplementedError("release_escrow not yet implemented in capabilities (Phase B)")


def create_capabilities(node: NetworkNode) -> NetworkNodeCapabilities:
    """Factory helper to create capabilities for a given node."""
    return NetworkNodeCapabilities(node)
