from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_graph import ApiGraph

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Api Ontology
from aware_api_ontology.stable_ids import stable_api_id

# --- AWARE: USER_IMPORTS END


async def create(name: str, description: str | None = None) -> Api:
    """
    Create deterministic public/vendor API identity.
    """

    # --- AWARE: LOGIC START create
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("Api.create requires non-empty name")
    return Api(
        id=stable_api_id(name=normalized_name),
        name=normalized_name,
        description=description,
    )
    # --- AWARE: LOGIC END create


async def create_api_graph(api: Api, object_config_graph_id: UUID, description: str | None = None) -> ApiGraph:
    """
    Create one API graph bridge under this Api.
    """

    # --- AWARE: LOGIC START create_api_graph
    return await ApiGraph.create_via_api(
        api_id=api.id,
        object_config_graph_id=object_config_graph_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_api_graph


async def create_capability(api: Api, name: str, description: str | None = None) -> ApiCapability:
    """
    Create one named reusable API capability contract under this Api identity.
    """

    # --- AWARE: LOGIC START create_capability
    return await ApiCapability.create_via_api(
        api_id=api.id,
        name=name,
        description=description,
    )
    # --- AWARE: LOGIC END create_capability
