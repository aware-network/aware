from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.contract.experience_contract_actor_role_grant import ExperienceContractActorRoleGrant
from aware_experience_ontology.invocation.experience_invocation_action_config import ExperienceInvocationActionConfig
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.projection.projection_experience import ProjectionExperience
from aware_experience_ontology.projection.projection_experience_branch import ProjectionExperienceBranch
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_node import ProjectionExperienceNode
from aware_experience_ontology.projection.projection_experience_oigi import ProjectionExperienceOIGI
from aware_experience_ontology.projection.projection_experience_section import ProjectionExperienceSection
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView
from aware_experience_ontology.provider.experience_provider import ExperienceProvider

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_experience_invocation_action_config_id
from aware_experience.stable_ids import stable_projection_experience_id
from aware_experience.stable_ids import stable_projection_experience_graph_id
from aware_experience.stable_ids import stable_projection_experience_oigi_id

from aware_experience.graph.resolver import (
    object_instance_graph_identity_exists_via_lane,
)

from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(object_projection_graph_identity_id: UUID, name: str) -> ProjectionExperience:
    """
    Construct a deterministic ProjectionExperience under a Projection.

    Contract:
    - `ProjectionExperience.id` is deterministic for `(projection_id, name)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START create
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperience.create requires non-empty name")
    normalized_object_projection_graph_identity_id = (
        object_projection_graph_identity_id
        if isinstance(object_projection_graph_identity_id, UUID)
        else UUID(str(object_projection_graph_identity_id))
    )

    session = current_handler_session()
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=(normalized_object_projection_graph_identity_id),
        name=normalized_name,
    )
    existing = session.imap_get(ProjectionExperience, projection_experience_id)
    if existing is not None:
        existing_data = existing.__dict__
        if "object_projection_graph_identity_id" not in existing_data and "name" not in existing_data:
            existing.object_projection_graph_identity_id = normalized_object_projection_graph_identity_id
            existing.name = normalized_name
            return existing
        if (
            existing.object_projection_graph_identity_id != (normalized_object_projection_graph_identity_id)
            or existing.name != normalized_name
        ):
            raise RuntimeError(
                "ProjectionExperience.create payload mismatch for existing experience: "
                + f"projection_experience_id={projection_experience_id}"
            )
        return existing

    return ProjectionExperience(
        id=projection_experience_id,
        object_projection_graph_identity_id=normalized_object_projection_graph_identity_id,
        name=normalized_name,
    )
    # --- AWARE: LOGIC END create


async def create_branch(projection_experience: ProjectionExperience, name: str) -> ProjectionExperienceBranch:
    """
    Create a deterministic ProjectionExperienceBranch under this ProjectionExperience.

    Contract:
    - Delegates canonical branch identity to `ProjectionExperienceBranch.create(...)`.
    - Mutates only this ProjectionExperience membership (`projection_experience_branches`).
    """

    # --- AWARE: LOGIC START create_branch
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceBranch.create_via_projection_experience(
        projection_experience_id=projection_experience_id,
        name=name,
    )

    for existing in projection_experience.projection_experience_branches:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_branches.append(created)
    return created
    # --- AWARE: LOGIC END create_branch


async def create_view(
    projection_experience: ProjectionExperience, api_view_id: UUID, name: str
) -> ProjectionExperienceView:
    """
    Create a deterministic ProjectionExperienceView under this ProjectionExperience.

    Contract:
    - Delegates canonical view identity to `ProjectionExperienceView.create(...)`.
    - Mutates only this ProjectionExperience membership (`projection_experience_views`).
    - Binds the Experience-local view mount to one API-owned readable view.
    """

    # --- AWARE: LOGIC START create_view
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceView.create_via_projection_experience(
        projection_experience_id=projection_experience_id,
        api_view_id=api_view_id,
        name=name,
    )

    for existing in projection_experience.projection_experience_views:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_views.append(created)
    return created
    # --- AWARE: LOGIC END create_view


async def create_invocation_action_config(
    projection_experience: ProjectionExperience,
    target_kind: ExperienceInvocationActionTargetKind,
    api_capability_endpoint_id: UUID | None = None,
    sdk_operation_id: UUID | None = None,
) -> ExperienceInvocationActionConfig:
    """
    Create a reusable Experience invocation action config under this ProjectionExperience.

    Contract:
    - Views, sensors, actuators, and future surfaces bind to this config.
    - API/SDK executable target fields live here, not on consumer-specific wrappers.
    - `target_kind` selects exactly one executable target relationship.
    """

    # --- AWARE: LOGIC START create_invocation_action_config
    target_kind_value = (
        target_kind.value
        if isinstance(target_kind, ExperienceInvocationActionTargetKind)
        else str(target_kind or "").strip().casefold()
    )
    if target_kind_value == ExperienceInvocationActionTargetKind.api.value:
        if api_capability_endpoint_id is None:
            raise RuntimeError("ProjectionExperience api invocation action config requires api_capability_endpoint_id")
        if sdk_operation_id is not None:
            raise RuntimeError("ProjectionExperience api invocation action config cannot set sdk_operation_id")
        normalized_target_kind = ExperienceInvocationActionTargetKind.api
        entity_id = api_capability_endpoint_id
    elif target_kind_value == ExperienceInvocationActionTargetKind.sdk.value:
        if sdk_operation_id is None:
            raise RuntimeError("ProjectionExperience sdk invocation action config requires sdk_operation_id")
        if api_capability_endpoint_id is not None:
            raise RuntimeError(
                "ProjectionExperience sdk invocation action config cannot set api_capability_endpoint_id"
            )
        normalized_target_kind = ExperienceInvocationActionTargetKind.sdk
        entity_id = sdk_operation_id
    else:
        raise RuntimeError(
            "ProjectionExperience invocation action target_kind must be api or sdk: " + f"target_kind={target_kind!r}"
        )

    created = await ExperienceInvocationActionConfig.build_via_projection_experience(
        projection_experience_id=projection_experience.id,
        target_kind=normalized_target_kind,
        api_capability_endpoint_id=api_capability_endpoint_id,
        sdk_operation_id=sdk_operation_id,
    )

    expected_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience.id,
        target_kind=normalized_target_kind.value,
        entity_id=entity_id,
    )
    if created.id != expected_id:
        raise RuntimeError(
            "ExperienceInvocationActionConfig constructor returned unexpected id: "
            + f"expected={expected_id} actual={created.id}"
        )
    for existing in projection_experience.invocation_action_configs:
        if existing.id == created.id:
            return existing
        if (
            existing.target_kind == normalized_target_kind
            and existing.api_capability_endpoint_id == api_capability_endpoint_id
            and existing.sdk_operation_id == sdk_operation_id
        ):
            raise RuntimeError(
                "ProjectionExperience already has a different invocation action config "
                + "for the same executable target"
            )
    projection_experience.invocation_action_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_invocation_action_config


async def create_provider(
    projection_experience: ProjectionExperience,
    provider_key: str,
    provider_kind: str = "provider",
    selection_policy: str = "contract_required",
    status: str = "active",
    title: str | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ExperienceProvider:
    """
    Create one Experience-owned public provider slot.

    Contract:
    - Provider ontologies bind concrete fulfillment to this slot.
    - ProjectionExperience does not import provider-owned operation or contract truth.
    - Mutates only this ProjectionExperience membership (`providers`).
    """

    # --- AWARE: LOGIC START create_provider
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_provider


async def create_contract_actor_role_grant(
    projection_experience: ProjectionExperience,
    grant_key: str,
    actor_config_role_config_id: UUID,
    role_config_id: UUID,
    access_scope: str = "experience",
    participant_kind: str = "actor",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    grant_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ExperienceContractActorRoleGrant:
    """
    Create one Experience-owned contract-visible actor-role grant.

    Contract:
    - This is the public Experience grant providers may accept/reference later.
    - The grant is scoped through ActorConfigRoleConfig, not a raw global role.
    - Mutates only this ProjectionExperience membership (`contract_actor_role_grants`).
    """

    # --- AWARE: LOGIC START create_contract_actor_role_grant
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_contract_actor_role_grant


async def create_node(
    projection_experience: ProjectionExperience, object_projection_graph_node_id: UUID, key: str
) -> ProjectionExperienceNode:
    """
    Create a deterministic ProjectionExperienceNode under this ProjectionExperience.

    Contract:
    - Delegates canonical node identity to `ProjectionExperienceNode.build(...)`.
    - Mutates only this ProjectionExperience membership (`projection_experience_nodes`).
    """

    # --- AWARE: LOGIC START create_node
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceNode.build_via_projection_experience(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
        key=key,
    )

    for existing in projection_experience.projection_experience_nodes:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_nodes.append(created)
    return created
    # --- AWARE: LOGIC END create_node


async def create_graph(projection_experience: ProjectionExperience, name: str) -> ProjectionExperienceGraph:
    """
    Create one deterministic ProjectionExperienceGraph under this ProjectionExperience.

    Contract:
    - Graph topology and graph-bound profiles evolve through the child
      `ProjectionExperienceGraph` projection reached from this shell rail.
    - API/profile/value contracts are out of scope for this object.
    """

    # --- AWARE: LOGIC START create_graph
    projection_experience_id = projection_experience.id
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProjectionExperience.create_graph requires non-empty name")

    session = current_handler_session()
    projection_experience_graph_id = stable_projection_experience_graph_id(
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )
    existing = session.imap_get(ProjectionExperienceGraph, projection_experience_graph_id)
    if existing is not None:
        if existing.projection_experience_id != projection_experience_id or existing.name != normalized_name:
            raise RuntimeError(
                "ProjectionExperience.create_graph payload mismatch for existing ProjectionExperienceGraph: "
                + f"projection_experience_graph_id={projection_experience_graph_id}"
            )
        for current in projection_experience.projection_experience_graphs:
            if current.id == existing.id:
                return current
        projection_experience.projection_experience_graphs.append(existing)
        return existing

    created = ProjectionExperienceGraph(
        id=projection_experience_graph_id,
        projection_experience_id=projection_experience_id,
        name=normalized_name,
    )

    for existing in projection_experience.projection_experience_graphs:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_graphs.append(created)
    return created
    # --- AWARE: LOGIC END create_graph


async def create_oigi(
    projection_experience: ProjectionExperience, object_instance_graph_identity_id: UUID, key: str | None = None
) -> ProjectionExperienceOIGI:
    """
    Create one ProjectionExperienceOIGI bridge under this ProjectionExperience.

    Contract:
    - OIGI topology evolves through the child `ProjectionExperienceOIGI`
      projection reached from this shell rail.
    """

    # --- AWARE: LOGIC START create_oigi
    projection_experience_id = projection_experience.id
    session = current_handler_session()
    exists = await object_instance_graph_identity_exists_via_lane(
        object_instance_graph_identity_id=object_instance_graph_identity_id
    )
    if not exists:
        raise RuntimeError(
            "ProjectionExperience.create_oigi requires existing ObjectInstanceGraphIdentity: "
            + f"object_instance_graph_identity_id={object_instance_graph_identity_id}"
        )

    normalized_key = (key or "").strip() or None
    projection_experience_oigi_id = stable_projection_experience_oigi_id(
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    existing = session.imap_get(ProjectionExperienceOIGI, projection_experience_oigi_id)
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.object_instance_graph_identity_id != object_instance_graph_identity_id
            or (existing.key or None) != normalized_key
        ):
            raise RuntimeError(
                "ProjectionExperience.create_oigi payload mismatch for existing ProjectionExperienceOIGI: "
                + f"projection_experience_oigi_id={projection_experience_oigi_id}"
            )
        for current in projection_experience.projection_experience_oigis:
            if current.id == existing.id:
                return current
        projection_experience.projection_experience_oigis.append(existing)
        return existing

    created = ProjectionExperienceOIGI(
        id=projection_experience_oigi_id,
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        key=normalized_key,
    )

    for existing in projection_experience.projection_experience_oigis:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_oigis.append(created)
    return created
    # --- AWARE: LOGIC END create_oigi


async def create_section(
    projection_experience: ProjectionExperience, section_id: UUID, section_key: str | None = None
) -> ProjectionExperienceSection:
    """
    Create one Attention Section bridge under this ProjectionExperience.

    Contract:
    - Attention owns Section and FocusScope mutation.
    - Experience owns the section+observable -> view-instance resolver.
    - `section_key` is optional denormalized lookup text and is not a runtime mount id.
    """

    # --- AWARE: LOGIC START create_section
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceSection.build_via_projection_experience(
        projection_experience_id=projection_experience_id,
        section_id=section_id,
        section_key=section_key,
    )

    for existing in projection_experience.projection_experience_sections:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_sections.append(created)
    return created
    # --- AWARE: LOGIC END create_section


async def create_section_graph_binding(
    projection_experience: ProjectionExperience,
    layout_config_section_config_id: UUID,
    projection_experience_view_id: UUID,
    projection_experience_graph_identity_id: UUID,
    binding_key: str,
    section_key: str,
) -> ProjectionExperienceSectionGraphBinding:
    """
    Create one stable section-graph binding under this ProjectionExperience.

    Contract:
    - The view binding stays Experience-owned.
    - The layout section target is an explicit portal to Attention layout topology.
    - The graph-occurrence anchor stays explicit and canonical at Experience level.
    - This object expresses section selection agreement only; it does not mutate Attention truth.
    """

    # --- AWARE: LOGIC START create_section_graph_binding
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceSectionGraphBinding.build_via_projection_experience(
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=layout_config_section_config_id,
        projection_experience_view_id=projection_experience_view_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        binding_key=binding_key,
        section_key=section_key,
    )

    for existing in projection_experience.projection_experience_section_graph_bindings:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_section_graph_bindings.append(created)
    return created
    # --- AWARE: LOGIC END create_section_graph_binding


async def create_layout_graph_binding(
    projection_experience: ProjectionExperience, layout_config_id: UUID, binding_key: str
) -> ProjectionExperienceLayoutGraphBinding:
    """
    Create one stable layout graph binding under this ProjectionExperience.

    Contract:
    - This is the Experience-owned layout-level entry point for consumers.
    - The layout target is an explicit portal to Attention layout topology.
    - Child rows point to existing section graph bindings; order remains Attention-owned.
    - This object expresses composition agreement only; it does not activate session state.
    """

    # --- AWARE: LOGIC START create_layout_graph_binding
    projection_experience_id = projection_experience.id
    created = await ProjectionExperienceLayoutGraphBinding.build_via_projection_experience(
        projection_experience_id=projection_experience_id,
        layout_config_id=layout_config_id,
        binding_key=binding_key,
    )

    for existing in projection_experience.projection_experience_layout_graph_bindings:
        if existing.id == created.id:
            return existing
    projection_experience.projection_experience_layout_graph_bindings.append(created)
    return created
    # --- AWARE: LOGIC END create_layout_graph_binding
