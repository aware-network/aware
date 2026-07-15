from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView
from aware_experience_ontology.projection.projection_experience_view_instance import ProjectionExperienceViewInstance
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_state_provider import (
    ProjectionExperienceViewStateProvider,
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
from aware_experience.stable_ids import stable_projection_experience_view_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def set_state_provider(
    projection_experience_view: ProjectionExperienceView,
    provider_ref: str,
    provider_kind: str = "runtime_callable",
    purity: str = "pure_read",
) -> ProjectionExperienceViewStateProvider:
    """
    Bind the pure read provider for this exact ProjectionExperienceView.

    Contract:
    - The view remains the semantic selector and owns provider selection.
    - The provider must only read host-owned materialized state and produce the declared state model.
    - Runtime callables and SDK functions are adapter implementations, not semantic authority.
    """

    # --- AWARE: LOGIC START set_state_provider
    provider = await ProjectionExperienceViewStateProvider.build_via_projection_experience_view(
        projection_experience_view_id=projection_experience_view.id,
        provider_ref=provider_ref,
        provider_kind=provider_kind,
        purity=purity,
    )

    for existing in projection_experience_view.state_providers:
        if existing.id == provider.id:
            return existing
        raise RuntimeError(
            "ProjectionExperienceView already has a different state provider: "
            + f"projection_experience_view_id={projection_experience_view.id}"
        )
    projection_experience_view.state_providers.append(provider)
    return provider
    # --- AWARE: LOGIC END set_state_provider


async def add_invocation_action(
    projection_experience_view: ProjectionExperienceView,
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
    Bind one Experience-owned invocation action to this view.

    Contract:
    - `api_view_capability_endpoint` is the API-owned view action truth.
    - `sdk_operation_api_view_capability_endpoint`, when present, wraps the
      same API view action with an SDK operation.
    - `experience_invocation_action_config` carries executable API endpoint XOR
      SDK operation target metadata.
    - `action_key` is copied from API-owned view action truth for panes.
    - This is not a Reactivity `ActionConfig`; it is a user/client invocation capability.
    """

    # --- AWARE: LOGIC START add_invocation_action
    return await bind_invocation_action_config(
        projection_experience_view=projection_experience_view,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        action_key=action_key,
        sdk_operation_api_view_capability_endpoint_id=sdk_operation_api_view_capability_endpoint_id,
        label=label,
        receipt_policy=receipt_policy,
        confirmation_policy=confirmation_policy,
        optimistic_policy=optimistic_policy,
    )
    # --- AWARE: LOGIC END add_invocation_action


async def bind_invocation_action_config(
    projection_experience_view: ProjectionExperienceView,
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
    Bind one generic Experience invocation target config to an API-owned
    view action exposed by this view.

    Contract:
    - `api_view_capability_endpoint` is mandatory view-action truth.
    - Target execution metadata stays on `ExperienceInvocationActionConfig`.
    - Optional SDK operation view binding wraps the same API view action.
    """

    # --- AWARE: LOGIC START bind_invocation_action_config
    session = current_handler_session()
    normalized_action_key = (action_key or "").strip()
    if not normalized_action_key:
        raise RuntimeError("ProjectionExperienceView.bind_invocation_action_config requires non-empty action_key")

    api_view_capability_endpoint = session.imap_get(
        ApiViewCapabilityEndpoint,
        api_view_capability_endpoint_id,
    )
    if api_view_capability_endpoint is not None:
        if api_view_capability_endpoint.api_view_id != projection_experience_view.api_view_id:
            raise RuntimeError(
                "ProjectionExperienceView.bind_invocation_action_config ApiViewCapabilityEndpoint does not belong "
                + "to this ProjectionExperienceView api_view"
            )
        if api_view_capability_endpoint.action_key.strip() != normalized_action_key:
            raise RuntimeError(
                "ProjectionExperienceView.bind_invocation_action_config action_key must match API view action: "
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
                "ProjectionExperienceView.bind_invocation_action_config SDK view binding requires "
                + "an SDK ExperienceInvocationActionConfig target"
            )
        if sdk_operation_api_view_capability_endpoint is not None:
            if (
                sdk_operation_api_view_capability_endpoint.api_view_capability_endpoint_id
                != api_view_capability_endpoint_id
            ):
                raise RuntimeError(
                    "ProjectionExperienceView.bind_invocation_action_config SDK view binding does not target "
                    + "the same ApiViewCapabilityEndpoint"
                )
            if sdk_operation_api_view_capability_endpoint.api_view_id != projection_experience_view.api_view_id:
                raise RuntimeError(
                    "ProjectionExperienceView.bind_invocation_action_config SDK view binding does not target "
                    + "this ProjectionExperienceView api_view"
                )
            if sdk_operation_api_view_capability_endpoint.action_key.strip() != normalized_action_key:
                raise RuntimeError(
                    "ProjectionExperienceView.bind_invocation_action_config SDK action_key must match API view action"
                )
            if (
                experience_invocation_action_config is not None
                and experience_invocation_action_config.sdk_operation_id
                != sdk_operation_api_view_capability_endpoint.sdk_operation_id
            ):
                raise RuntimeError(
                    "ProjectionExperienceView.bind_invocation_action_config SDK operation target mismatch"
                )
    else:
        if (
            experience_invocation_action_config is not None
            and experience_invocation_action_config.target_kind != ExperienceInvocationActionTargetKind.api
        ):
            raise RuntimeError(
                "ProjectionExperienceView.bind_invocation_action_config API view action without SDK binding "
                + "requires an API ExperienceInvocationActionConfig target"
            )
        if (
            experience_invocation_action_config is not None
            and api_view_capability_endpoint is not None
            and (
                experience_invocation_action_config.api_capability_endpoint_id
                != api_view_capability_endpoint.api_capability_endpoint_id
            )
        ):
            raise RuntimeError("ProjectionExperienceView.bind_invocation_action_config API endpoint target mismatch")

    action_config = await ProjectionExperienceViewInvocationActionConfig.build_via_projection_experience_view(
        projection_experience_view_id=projection_experience_view.id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        action_key=normalized_action_key,
        sdk_operation_api_view_capability_endpoint_id=sdk_operation_api_view_capability_endpoint_id,
        label=label,
        receipt_policy=receipt_policy,
        confirmation_policy=confirmation_policy,
        optimistic_policy=optimistic_policy,
    )

    normalized_action_key_folded = normalized_action_key.casefold()
    for existing in projection_experience_view.invocation_action_configs:
        if existing.id == action_config.id:
            if (
                existing.api_view_capability_endpoint_id != api_view_capability_endpoint_id
                or existing.sdk_operation_api_view_capability_endpoint_id
                != sdk_operation_api_view_capability_endpoint_id
                or existing.experience_invocation_action_config_id != experience_invocation_action_config_id
                or existing.action_key != normalized_action_key
            ):
                raise RuntimeError(
                    "ProjectionExperienceView already has a mismatched invocation action config: "
                    + f"projection_experience_view_invocation_action_config_id={action_config.id}"
                )
            return existing
        if (
            existing.action_key.casefold().strip() == normalized_action_key_folded
            and existing.api_view_capability_endpoint_id != api_view_capability_endpoint_id
        ):
            raise RuntimeError(
                "ProjectionExperienceView already has a different ApiViewCapabilityEndpoint for action_key: "
                + f"projection_experience_view_id={projection_experience_view.id} "
                + f"action_key={normalized_action_key!r}"
            )
    projection_experience_view.invocation_action_configs.append(action_config)
    return action_config
    # --- AWARE: LOGIC END bind_invocation_action_config


async def create_instance(
    projection_experience_view: ProjectionExperienceView,
    section_graph_binding_id: UUID,
    view_instance_key: str,
    object_instance_graph_branch_id: UUID | None = None,
    state_commit_id: UUID | None = None,
    status: str = "active",
) -> ProjectionExperienceViewInstance:
    """
    Create one concrete rendered instance of this Experience view.

    Contract:
    - `ProjectionExperienceView` is reusable view configuration.
    - `ProjectionExperienceViewInstance` is the concrete view fulfillment for
      one section-graph binding, optionally backed by one materialized branch.
    - Attention FocusScope remains transitional selector state and is not view identity.
    - Action provenance must attach to this instance, not only to the view config.
    """

    # --- AWARE: LOGIC START create_instance
    view_instance = await ProjectionExperienceViewInstance.build_via_projection_experience_view(
        projection_experience_view_id=projection_experience_view.id,
        section_graph_binding_id=section_graph_binding_id,
        view_instance_key=view_instance_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        state_commit_id=state_commit_id,
        status=status,
    )

    for existing in projection_experience_view.view_instances:
        if existing.id == view_instance.id:
            if (
                existing.projection_experience_view_id != view_instance.projection_experience_view_id
                or existing.section_graph_binding_id != view_instance.section_graph_binding_id
                or existing.view_instance_key != view_instance.view_instance_key
                or existing.object_instance_graph_branch_id != view_instance.object_instance_graph_branch_id
                or existing.state_commit_id != view_instance.state_commit_id
                or existing.status != view_instance.status
            ):
                raise RuntimeError(
                    "ProjectionExperienceView already has a mismatched view instance: "
                    + f"projection_experience_view_instance_id={view_instance.id}"
                )
            return existing

    projection_experience_view.view_instances.append(view_instance)
    return view_instance
    # --- AWARE: LOGIC END create_instance


async def create_via_projection_experience(
    projection_experience_id: UUID, api_view_id: UUID, name: str
) -> ProjectionExperienceView:
    """
    Construct a deterministic ProjectionExperienceView under a ProjectionExperience.

    Contract:
    - `ProjectionExperienceView.id` is deterministic for `(projection_experience_id, name)`.
    - Constructor converges the API-view binding for repeated calls with the same Experience mount key.
    - `api_view` is the canonical lower API-owned readable view-state contract.
    - Observable and state-model metadata are derived from `api_view`; Experience
      does not duplicate lower view contract truth.
    """

    # --- AWARE: LOGIC START create_via_projection_experience
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperienceView.create_via_projection_experience requires non-empty name")

    session = current_handler_session()
    view_id = stable_projection_experience_view_id(
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    existing = session.imap_get(ProjectionExperienceView, view_id)
    if existing is not None:
        if existing.projection_experience_id != projection_experience_id or existing.name != normalized_name:
            raise RuntimeError(
                "ProjectionExperienceView.create_via_projection_experience payload mismatch for existing view: "
                + f"projection_experience_view_id={view_id}"
            )
        existing.api_view_id = api_view_id
        return existing

    return ProjectionExperienceView(
        id=view_id,
        projection_experience_id=projection_experience_id,
        api_view_id=api_view_id,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END create_via_projection_experience
