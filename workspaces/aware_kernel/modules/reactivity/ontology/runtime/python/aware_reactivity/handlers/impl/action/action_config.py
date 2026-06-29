from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
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
    - `action_schema` is deprecated compatibility metadata only.
    - New typed action contracts resolve through Experience invocation
      bindings and Meta `InlineValueInstance` payload evidence.
    """

    # --- AWARE: LOGIC START create
    return ActionConfig(
        id=stable_action_config_id(name=name),
        name=name,
        description=description,
        action_type=action_type,
        is_enabled=is_enabled,
        is_system=is_system,
        require_authentication=require_authentication,
        allowed_roles=list(allowed_roles),
        action_schema=JsonObject(action_schema),
    )
    # --- AWARE: LOGIC END create
