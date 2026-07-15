from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Network Ontology
from aware_network_ontology.network.network_directory import NetworkDirectory

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_network_ontology.stable_ids import stable_network_directory_id

# --- AWARE: USER_IMPORTS END


async def bootstrap(name: str = "default") -> NetworkDirectory:
    """
    Bootstrap the Network-owned directory/read-model root.

    Contract:
    - This root is the stable Network-owned directory lane for territory-wide discovery.
    - Durable discovery facts remain committed on `NetworkNode`, `NetworkNodePeer`,
      `NetworkNodeService`, and `NetworkNodeEnvironment`.
    - Reads must derive from committed Network state or service-owned read models,
      not ontology read functions.
    """

    # --- AWARE: LOGIC START bootstrap
    return NetworkDirectory(
        id=stable_network_directory_id(name=name),
        name=name,
    )
    # --- AWARE: LOGIC END bootstrap
