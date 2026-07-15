from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_view_invocation_action import (
    ProjectionExperienceViewInvocationAction,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience.stable_ids import (
    stable_projection_experience_view_invocation_action_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    projection_experience_view_instance_id: UUID,
    view_invocation_action_config_id: UUID,
    experience_invocation_action_id: UUID,
) -> ProjectionExperienceViewInvocationAction:
    """
    Create one deterministic view provenance bridge under a view instance.

    Contract:
    - `projection_experience_view_instance_id` is explicit provenance for the concrete view instance.
    - `view_invocation_action_config` proves the action was exposed by the view.
    - `experience_invocation_action` carries the actual invocation receipt.
    """

    # --- AWARE: LOGIC START build
    action_id = stable_projection_experience_view_invocation_action_id(
        view_invocation_action_config_id=view_invocation_action_config_id,
        experience_invocation_action_id=experience_invocation_action_id,
    )

    session = current_handler_session()
    view_invocation_action_config = session.imap_get(
        ProjectionExperienceViewInvocationActionConfig,
        view_invocation_action_config_id,
    )
    experience_invocation_action = session.imap_get(
        ExperienceInvocationAction,
        experience_invocation_action_id,
    )
    existing = session.imap_get(ProjectionExperienceViewInvocationAction, action_id)
    if existing is not None:
        if (
            existing.projection_experience_view_instance_id != projection_experience_view_instance_id
            or existing.view_invocation_action_config_id != view_invocation_action_config_id
            or existing.experience_invocation_action_id != experience_invocation_action_id
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInvocationAction payload mismatch for existing invocation: "
                + f"projection_experience_view_invocation_action_id={action_id}"
            )
        return existing

    payload = {
        "id": action_id,
        "projection_experience_view_instance_id": projection_experience_view_instance_id,
        "view_invocation_action_config_id": view_invocation_action_config_id,
        "experience_invocation_action_id": experience_invocation_action_id,
        "experience_invocation_action": experience_invocation_action,
    }
    if view_invocation_action_config is not None:
        payload["view_invocation_action_config"] = view_invocation_action_config
        return ProjectionExperienceViewInvocationAction(**payload)
    return ProjectionExperienceViewInvocationAction.model_construct(
        view_invocation_action_config=None,
        **payload,
    )
    # --- AWARE: LOGIC END build
