from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition import Condition

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_condition_id

# --- AWARE: USER_IMPORTS END


async def create(
    config_id: UUID,
    activation_id: UUID,
    trigger_object_instance_graph_commit_id: UUID,
    arguments: JsonObject = JsonObject(),
) -> Condition:
    """
    Create runtime condition evidence anchored to one activation.
    """

    # --- AWARE: LOGIC START create
    return Condition(
        id=stable_condition_id(config_id=config_id, activation_id=activation_id),
        config_id=config_id,
        activation_id=activation_id,
        trigger_object_instance_graph_commit_id=trigger_object_instance_graph_commit_id,
        arguments=dict(arguments),
    )
    # --- AWARE: LOGIC END create
