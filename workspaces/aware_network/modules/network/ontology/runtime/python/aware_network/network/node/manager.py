"""
Node manager for maintaining the server's network node instance.

This module ensures each server properly initializes and maintains its network node,
providing a thread-safe singleton interface for node operations.
"""

import logging
from typing import Optional
import threading
from uuid import UUID
from pathlib import Path
import json
import os

from aware_network.network.node.local_info import (
    LocalNetworkNodeInfo,
    normalize_local_network_node_info_identity,
)

logger = logging.getLogger(__name__)


class NetworkNodeManager:
    """
    Thread-safe singleton manager for the server's network node.

    Ensures:
    1. Single node instance per server
    2. Proper initialization and shutdown
    3. Node state management
    4. Connection to peer nodes
    5. Smart contract coordination
    """

    _instance = None
    _lock = threading.Lock()

    # ---------- Filesystem persistence (.aware) ----------
    _AWARE_DIR_NAME: str = ".aware"
    _NODE_INFO_FILENAME: str = "network_node.json"
    _NODE_INFO_ROOT_ENV_VARS: tuple[str, ...] = (
        "AWARE_NETWORK_NODE_INFO_ROOT",
        "AWARE_NODE_ROOT",
        "AWARE_ROOT",
    )

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._local_info_cache: Optional[LocalNetworkNodeInfo] = None
        self._initialized = True

    # ========================
    # Filesystem (.aware) API
    # ========================
    @classmethod
    def _get_node_info_path(cls) -> Path:
        explicit_path = os.environ.get("AWARE_NODE_INFO_PATH")
        if explicit_path is not None and explicit_path.strip():
            return Path(explicit_path).expanduser().resolve()

        for env_var in cls._NODE_INFO_ROOT_ENV_VARS:
            root_value = os.environ.get(env_var)
            if root_value is not None and root_value.strip():
                aware_dir = Path(root_value).expanduser().resolve() / cls._AWARE_DIR_NAME
                aware_dir.mkdir(parents=True, exist_ok=True)
                return aware_dir / cls._NODE_INFO_FILENAME

        raise RuntimeError(
            "Network node info path requires AWARE_NODE_INFO_PATH or one of " + ", ".join(cls._NODE_INFO_ROOT_ENV_VARS)
        )

    @classmethod
    def load_local_info(cls) -> Optional[LocalNetworkNodeInfo]:
        """Load persisted local node info from .aware; returns None if missing/invalid."""
        try:
            path = cls._get_node_info_path()
            if not path.exists():
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LocalNetworkNodeInfo.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to load local node info: {e}")
            return None

    @classmethod
    def save_local_info(cls, info: LocalNetworkNodeInfo) -> None:
        """Persist local node info to .aware for discovery by other processes."""
        try:
            path = cls._get_node_info_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(info.model_dump_json(indent=2))
            logger.info(f"Saved local network node info to {path}")
        except Exception as e:
            logger.error(f"Failed to save local node info: {e}")
            raise

    def ensure_local_info(
        self, *, http_base_url: Optional[str] = None, label: Optional[str] = None
    ) -> LocalNetworkNodeInfo:
        """Ensure local node info exists on disk; create default if missing.

        Returns the in-memory cached info.
        """
        if self._local_info_cache is not None:
            return self._local_info_cache

        info = self.load_local_info()
        created_new = info is None
        if info is None:
            info = LocalNetworkNodeInfo()
            if http_base_url:
                info.http_base_url = http_base_url
            if label:
                info.label = label
        normalized_info = normalize_local_network_node_info_identity(info)
        if normalized_info != info:
            info = normalized_info
            self.save_local_info(info)
        elif created_new:
            self.save_local_info(info)
        self._local_info_cache = info
        return info

    @property
    def hosted_node_id(self) -> UUID:
        """Return the local node id (filesystem bootstrap SSOT for v0)."""
        return self.ensure_local_info().id

    @property
    def hosted_node(self) -> LocalNetworkNodeInfo:
        """Back-compat alias: return local node info (not an ORM model)."""
        return self.ensure_local_info()

    def get_interface_ws_url(self, connection_id: UUID) -> str:
        """Convenience helper: interface -> node WS URL with connection id."""
        info = self.ensure_local_info()
        return info.get_interface_ws_url(connection_id)

    @property
    def is_initialized(self) -> bool:
        """Check if node has local bootstrap info."""
        return self.load_local_info() is not None

    async def get_node_connection_id(self, node_id: UUID) -> Optional[UUID]:
        """Get a connection to a node."""
        # !! TODO: Decide relationship node_id to connection_id
        return node_id


# Global network node manager instance
network_node_manager = NetworkNodeManager()
