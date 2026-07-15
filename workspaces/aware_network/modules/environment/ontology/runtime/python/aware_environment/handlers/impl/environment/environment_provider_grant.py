from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_provider_grant import EnvironmentProviderGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_environment_provider(
    environment_provider_id: UUID,
    grant_key: str,
    scope_kind: str = "profile",
    process_config_id: UUID | None = None,
    thread_config_id: UUID | None = None,
    object_projection_graph_id: UUID | None = None,
    action_scope: str | None = None,
    status: str = "active",
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentProviderGrant:
    """
    Create one Environment provider grant.

    Contract:
    - Stable identity is `(environment_provider_id, grant_key)`.
    - Optional scope refs constrain the granted Environment surface.
    - No Experience or Service class reference is allowed here.
    """

    # --- AWARE: LOGIC START build_via_environment_provider
    return EnvironmentProviderGrant(
        environment_provider_id=environment_provider_id,
        grant_key=grant_key,
        scope_kind=scope_kind,
        process_config_id=process_config_id,
        thread_config_id=thread_config_id,
        object_projection_graph_id=object_projection_graph_id,
        action_scope=action_scope,
        status=status,
        description=description,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment_provider
