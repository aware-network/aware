from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_view_instance import ProjectionExperienceViewInstance
from aware_experience_ontology.projection.projection_experience_view_invocation_action import (
    ProjectionExperienceViewInvocationAction,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience.stable_ids import stable_projection_experience_view_instance_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_action_invocation(
    projection_experience_view_instance: ProjectionExperienceViewInstance,
    view_invocation_action_config_id: UUID,
    invocation_key: UUID,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    actor_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ProjectionExperienceViewInvocationAction:
    """
    Record one action invocation performed through this concrete view instance.

    Contract:
    - `view_invocation_action_config_id` points to the view-exposed action config binding.
    - The actual call is recorded as a generic `ExperienceInvocationAction`.
    - This view instance stores only the provenance bridge to that invocation.
    """

    # --- AWARE: LOGIC START record_action_invocation
    session = current_handler_session()
    view_action_config = session.imap_get(
        ProjectionExperienceViewInvocationActionConfig,
        view_invocation_action_config_id,
    )
    if view_action_config is None:
        raise RuntimeError(
            "ProjectionExperienceViewInstance.record_action_invocation requires existing "
            + "ProjectionExperienceViewInvocationActionConfig to resolve the standalone "
            + "ExperienceInvocationActionConfig identity: "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )
    elif (
        view_action_config.projection_experience_view_id
        != projection_experience_view_instance.projection_experience_view_id
    ):
        raise RuntimeError(
            "ProjectionExperienceViewInvocationActionConfig does not belong to this view instance view: "
            + f"projection_experience_view_instance_id={projection_experience_view_instance.id} "
            + f"view_invocation_action_config_id={view_invocation_action_config_id}"
        )

    else:
        experience_action_config = session.imap_get(
            ExperienceInvocationActionConfig,
            view_action_config.experience_invocation_action_config_id,
        )
        if experience_action_config is None:
            experience_action_config = view_action_config.experience_invocation_action_config
        if (
            experience_action_config is not None
            and experience_action_config.id != view_action_config.experience_invocation_action_config_id
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInvocationActionConfig references mismatched "
                + "ExperienceInvocationActionConfig: "
                + f"expected={view_action_config.experience_invocation_action_config_id} "
                + f"actual={experience_action_config.id}"
            )

        experience_invocation_action = await view_action_config.record_invocation(
            invocation_key=invocation_key,
            actor_id=actor_id,
            api_call_id=api_call_id,
            sdk_operation_call_id=sdk_operation_call_id,
            request_ref=request_ref,
            receipt_ref=receipt_ref,
            status=status,
        )
    action_invocation = await ProjectionExperienceViewInvocationAction.build(
        projection_experience_view_instance_id=projection_experience_view_instance.id,
        view_invocation_action_config_id=view_invocation_action_config_id,
        experience_invocation_action_id=experience_invocation_action.id,
    )

    for existing in projection_experience_view_instance.invocation_actions:
        if existing.id == action_invocation.id:
            if (
                existing.projection_experience_view_instance_id
                != action_invocation.projection_experience_view_instance_id
                or existing.view_invocation_action_config_id != action_invocation.view_invocation_action_config_id
                or existing.experience_invocation_action_id != action_invocation.experience_invocation_action_id
            ):
                raise RuntimeError(
                    "ProjectionExperienceViewInstance already has a mismatched action invocation: "
                    + f"projection_experience_view_invocation_action_id={action_invocation.id}"
                )
            return existing

    projection_experience_view_instance.invocation_actions.append(action_invocation)
    return action_invocation
    # --- AWARE: LOGIC END record_action_invocation


async def build_via_projection_experience_view(
    projection_experience_view_id: UUID,
    section_graph_binding_id: UUID,
    view_instance_key: str,
    object_instance_graph_branch_id: UUID | None = None,
    state_commit_id: UUID | None = None,
    status: str = "active",
) -> ProjectionExperienceViewInstance:
    """
    Create one deterministic view instance under a ProjectionExperienceView.

    Contract:
    - Identity is scoped by parent view, section graph binding, and view instance key.
    - `section_graph_binding` is the canonical bridge to view + layout section + graph occurrence.
    - Runtime focus/environment/thread evidence belongs on invocation or transition receipts,
      not on the view-instance identity.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_view
    normalized_view_instance_key = (view_instance_key or "").strip()
    if not normalized_view_instance_key:
        raise RuntimeError(
            "ProjectionExperienceViewInstance.build_via_projection_experience_view "
            + "requires non-empty view_instance_key"
        )

    normalized_status = (status or "").strip() or "active"
    view_instance_id = stable_projection_experience_view_instance_id(
        projection_experience_view_id=projection_experience_view_id,
        section_graph_binding_id=section_graph_binding_id,
        view_instance_key=normalized_view_instance_key,
    )

    session = current_handler_session()
    existing = session.imap_get(ProjectionExperienceViewInstance, view_instance_id)
    if existing is not None:
        if (
            existing.projection_experience_view_id != projection_experience_view_id
            or existing.section_graph_binding_id != section_graph_binding_id
            or existing.view_instance_key != normalized_view_instance_key
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
            or existing.state_commit_id != state_commit_id
            or existing.status != normalized_status
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInstance field mismatch for existing instance: "
                + f"projection_experience_view_instance_id={view_instance_id}"
            )
        return existing

    return ProjectionExperienceViewInstance(
        id=view_instance_id,
        projection_experience_view_id=projection_experience_view_id,
        section_graph_binding_id=section_graph_binding_id,
        view_instance_key=normalized_view_instance_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        state_commit_id=state_commit_id,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_view
