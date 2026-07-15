from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_config import ActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_action_config_id


# --- AWARE: USER_IMPORTS END


async def create(
    name: str,
    description: str,
    api_capability_endpoint_id: UUID,
    action_type: str,
    is_enabled: bool = True,
    is_system: bool = False,
    require_authentication: bool = True,
    allowed_roles: list[str] = [],
    action_schema: JsonObject = JsonObject(),
) -> ActionConfig:
    """
    Create a canonical action policy root.

    Contract:
    - `api_capability_endpoint` is the required 1:1 API contract anchor
      for this action. Experience may activate/refine this contract by
      scenario or role, but must not redirect it to another endpoint.
    - `action_schema` is deprecated compatibility metadata only.
    - Request value truth is created once at `ApiCall.request_model`;
      Reactivity carries decision/lifecycle evidence only.
    """

    # --- AWARE: LOGIC START create
    return ActionConfig(
        id=stable_action_config_id(name=name),
        name=name,
        description=description,
        api_capability_endpoint_id=api_capability_endpoint_id,
        action_type=action_type,
        is_enabled=is_enabled,
        is_system=is_system,
        require_authentication=require_authentication,
        allowed_roles=list(allowed_roles),
        action_schema=JsonObject(action_schema),
    )
    # --- AWARE: LOGIC END create
