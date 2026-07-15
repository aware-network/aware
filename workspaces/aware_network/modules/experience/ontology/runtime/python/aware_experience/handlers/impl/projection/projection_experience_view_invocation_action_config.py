from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_view_capability_endpoint import (
    ApiViewCapabilityEndpoint,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_sdk_ontology.sdk.sdk_operation_api_view_capability_endpoint import (
    SdkOperationApiViewCapabilityEndpoint,
)
from aware_experience.stable_ids import (
    stable_projection_experience_view_invocation_action_config_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_invocation(
    projection_experience_view_invocation_action_config: ProjectionExperienceViewInvocationActionConfig,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ExperienceInvocationAction:
    """
    Record one actual invocation handled through this view action config.

    Contract:
    - `ExperienceInvocationAction` is the single standalone invocation
      receipt for one crossing.
    - `ExperienceInvocationActionConfig` remains target metadata only.
    - Concrete view provenance attaches through
      `ProjectionExperienceViewInvocationAction`.
    - This view config does not own receipt identity.
    """

    # --- AWARE: LOGIC START record_invocation
    return await ExperienceInvocationAction.build(
        experience_invocation_action_config_id=(
            projection_experience_view_invocation_action_config.experience_invocation_action_config_id
        ),
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=request_ref,
        receipt_ref=receipt_ref,
        status=status,
    )
    # --- AWARE: LOGIC END record_invocation


async def build_via_projection_experience_view(
    projection_experience_view_id: UUID,
    api_view_capability_endpoint_id: UUID,
    experience_invocation_action_config_id: UUID,
    action_key: str,
    sdk_operation_api_view_capability_endpoint_id: UUID | None = None,
    label: str | None = None,
    receipt_policy: str | None = None,
    confirmation_policy: str | None = None,
    optimistic_policy: str | None = None,
) -> ProjectionExperienceViewInvocationActionConfig:
    """
    Bind one API-owned view action under a ProjectionExperienceView.

    Contract:
    - Parent `ProjectionExperienceView` scope is propagated by constructor lowering.
    - Identity is scoped by parent `ProjectionExperienceView` and
      `ApiViewCapabilityEndpoint`.
    - `experience_invocation_action_config` holds executable API endpoint XOR
      SDK operation target metadata.
    - `sdk_operation_api_view_capability_endpoint` may wrap the API view action
      with an SDK operation but must resolve to the same API view capability
      endpoint.
    - `action_key` is copied from API-owned view action truth for panes.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_view
    normalized_action_key = (action_key or "").strip()
    if not normalized_action_key:
        raise RuntimeError("ProjectionExperienceViewInvocationActionConfig requires non-empty action_key")
    normalized_label = (label or "").strip() or None
    normalized_receipt_policy = (receipt_policy or "").strip() or None
    normalized_confirmation_policy = (confirmation_policy or "").strip() or None
    normalized_optimistic_policy = (optimistic_policy or "").strip() or None

    action_config_id = stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=projection_experience_view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )
    session = current_handler_session()
    api_view_capability_endpoint = session.imap_get(
        ApiViewCapabilityEndpoint,
        api_view_capability_endpoint_id,
    )
    if api_view_capability_endpoint is not None:
        if api_view_capability_endpoint.action_key.strip() != normalized_action_key:
            raise RuntimeError(
                "ProjectionExperienceViewInvocationActionConfig action_key must match API view action: "
                + f"expected={api_view_capability_endpoint.action_key!r} actual={normalized_action_key!r}"
            )

    experience_invocation_action_config = session.imap_get(
        ExperienceInvocationActionConfig,
        experience_invocation_action_config_id,
    )
    sdk_operation_api_view_capability_endpoint = None
    if sdk_operation_api_view_capability_endpoint_id is not None:
        sdk_operation_api_view_capability_endpoint = session.imap_get(
            SdkOperationApiViewCapabilityEndpoint,
            sdk_operation_api_view_capability_endpoint_id,
        )
        if (
            experience_invocation_action_config is not None
            and experience_invocation_action_config.target_kind != ExperienceInvocationActionTargetKind.sdk
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInvocationActionConfig SDK view binding requires an SDK "
                + "ExperienceInvocationActionConfig target"
            )
        if sdk_operation_api_view_capability_endpoint is not None:
            if (
                sdk_operation_api_view_capability_endpoint.api_view_capability_endpoint_id
                != api_view_capability_endpoint_id
            ):
                raise RuntimeError(
                    "ProjectionExperienceViewInvocationActionConfig SDK view binding must target the same "
                    + "ApiViewCapabilityEndpoint"
                )
            if sdk_operation_api_view_capability_endpoint.action_key.strip() != normalized_action_key:
                raise RuntimeError(
                    "ProjectionExperienceViewInvocationActionConfig SDK action_key must match API view action"
                )
            if (
                experience_invocation_action_config is not None
                and experience_invocation_action_config.sdk_operation_id
                != sdk_operation_api_view_capability_endpoint.sdk_operation_id
            ):
                raise RuntimeError("ProjectionExperienceViewInvocationActionConfig SDK operation target mismatch")
    else:
        if (
            experience_invocation_action_config is not None
            and experience_invocation_action_config.target_kind != ExperienceInvocationActionTargetKind.api
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInvocationActionConfig API view action without SDK binding requires "
                + "an API ExperienceInvocationActionConfig target"
            )
        if (
            experience_invocation_action_config is not None
            and api_view_capability_endpoint is not None
            and (
                experience_invocation_action_config.api_capability_endpoint_id
                != api_view_capability_endpoint.api_capability_endpoint_id
            )
        ):
            raise RuntimeError("ProjectionExperienceViewInvocationActionConfig API endpoint target mismatch")

    existing = session.imap_get(ProjectionExperienceViewInvocationActionConfig, action_config_id)
    if existing is not None:
        if (
            existing.projection_experience_view_id != projection_experience_view_id
            or existing.api_view_capability_endpoint_id != api_view_capability_endpoint_id
            or existing.sdk_operation_api_view_capability_endpoint_id != sdk_operation_api_view_capability_endpoint_id
            or existing.experience_invocation_action_config_id != experience_invocation_action_config_id
            or existing.action_key != normalized_action_key
            or existing.label != normalized_label
            or existing.receipt_policy != normalized_receipt_policy
            or existing.confirmation_policy != normalized_confirmation_policy
            or existing.optimistic_policy != normalized_optimistic_policy
        ):
            raise RuntimeError(
                "ProjectionExperienceViewInvocationActionConfig field mismatch for existing action config: "
                + f"projection_experience_view_invocation_action_config_id={action_config_id}"
            )
        return existing

    return ProjectionExperienceViewInvocationActionConfig(
        id=action_config_id,
        projection_experience_view_id=projection_experience_view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        api_view_capability_endpoint=api_view_capability_endpoint,
        sdk_operation_api_view_capability_endpoint_id=sdk_operation_api_view_capability_endpoint_id,
        sdk_operation_api_view_capability_endpoint=sdk_operation_api_view_capability_endpoint,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        experience_invocation_action_config=experience_invocation_action_config,
        action_key=normalized_action_key,
        label=normalized_label,
        receipt_policy=normalized_receipt_policy,
        confirmation_policy=normalized_confirmation_policy,
        optimistic_policy=normalized_optimistic_policy,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_view
