from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.contract.experience_contract_actor_role_grant import ExperienceContractActorRoleGrant
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
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
    from aware_meta_ontology.graph.projection.object_projection_graph_identity import ObjectProjectionGraphIdentity


class ProjectionExperience(ORMModel):
    # Relationships
    object_projection_graph_identity: ObjectProjectionGraphIdentity | None = Field(default=None, exclude=True)
    projection_experience_branches: list[ProjectionExperienceBranch] = Field(default_factory=list, exclude=True)
    projection_experience_graphs: list[ProjectionExperienceGraph] = Field(default_factory=list, exclude=True)
    projection_experience_layout_graph_bindings: list[ProjectionExperienceLayoutGraphBinding] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_nodes: list[ProjectionExperienceNode] = Field(default_factory=list, exclude=True)
    projection_experience_oigis: list[ProjectionExperienceOIGI] = Field(default_factory=list, exclude=True)
    projection_experience_sections: list[ProjectionExperienceSection] = Field(default_factory=list, exclude=True)
    projection_experience_section_graph_bindings: list[ProjectionExperienceSectionGraphBinding] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_views: list[ProjectionExperienceView] = Field(default_factory=list, exclude=True)
    providers: list[ExperienceProvider] = Field(default_factory=list)
    contract_actor_role_grants: list[ExperienceContractActorRoleGrant] = Field(default_factory=list)
    invocation_action_configs: list[ExperienceInvocationActionConfig] = Field(default_factory=list)

    # Attributes
    name: str

    # Foreign Keys
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperience.object_projection_graph_identity"
    )

    @classmethod
    async def create(cls, object_projection_graph_identity_id: UUID, name: str) -> ProjectionExperience:
        """
        Construct a deterministic ProjectionExperience under a Projection.

        Contract:
        - `ProjectionExperience.id` is deterministic for `(projection_id, name)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {"object_projection_graph_identity_id": object_projection_graph_identity_id, "name": name}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperience):
            return value
        return ProjectionExperience.validate_invocation_value(value)

    async def create_branch(self, name: str) -> ProjectionExperienceBranch:
        """
        Create a deterministic ProjectionExperienceBranch under this ProjectionExperience.

        Contract:
        - Delegates canonical branch identity to `ProjectionExperienceBranch.create(...)`.
        - Mutates only this ProjectionExperience membership (`projection_experience_branches`).
        """

        payload = {"name": name}
        result = await invoke_instance(orm_model=self, function_name="create_branch", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_branch import ProjectionExperienceBranch

        if isinstance(value, ProjectionExperienceBranch):
            return value
        return ProjectionExperienceBranch.validate_invocation_value(value)

    async def create_view(self, api_view_id: UUID, name: str) -> ProjectionExperienceView:
        """
        Create a deterministic ProjectionExperienceView under this ProjectionExperience.

        Contract:
        - Delegates canonical view identity to `ProjectionExperienceView.create(...)`.
        - Mutates only this ProjectionExperience membership (`projection_experience_views`).
        - Binds the Experience-local view mount to one API-owned readable view.
        """

        payload = {"api_view_id": api_view_id, "name": name}
        result = await invoke_instance(orm_model=self, function_name="create_view", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view import ProjectionExperienceView

        if isinstance(value, ProjectionExperienceView):
            return value
        return ProjectionExperienceView.validate_invocation_value(value)

    async def create_invocation_action_config(
        self,
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

        payload = {
            "target_kind": target_kind,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "sdk_operation_id": sdk_operation_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_invocation_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action_config import (
            ExperienceInvocationActionConfig,
        )

        if isinstance(value, ExperienceInvocationActionConfig):
            return value
        return ExperienceInvocationActionConfig.validate_invocation_value(value)

    async def create_provider(
        self,
        provider_key: str,
        provider_kind: str = "provider",
        selection_policy: str = "contract_required",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ExperienceProvider:
        """
        Create one Experience-owned public provider slot.

        Contract:
        - Provider ontologies bind concrete fulfillment to this slot.
        - ProjectionExperience does not import provider-owned operation or contract truth.
        - Mutates only this ProjectionExperience membership (`providers`).
        """

        payload = {
            "provider_key": provider_key,
            "provider_kind": provider_kind,
            "selection_policy": selection_policy,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="create_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.provider.experience_provider import ExperienceProvider

        if isinstance(value, ExperienceProvider):
            return value
        return ExperienceProvider.validate_invocation_value(value)

    async def create_contract_actor_role_grant(
        self,
        grant_key: str,
        actor_config_role_config_id: UUID,
        role_config_id: UUID,
        access_scope: str = "experience",
        participant_kind: str = "actor",
        class_instance_identity_required: bool = False,
        role_assignment_binding_required: bool = True,
        grant_policy_json: JsonObject | None = {},
        description: str | None = None,
    ) -> ExperienceContractActorRoleGrant:
        """
        Create one Experience-owned contract-visible actor-role grant.

        Contract:
        - This is the public Experience grant providers may accept/reference later.
        - The grant is scoped through ActorConfigRoleConfig, not a raw global role.
        - Mutates only this ProjectionExperience membership (`contract_actor_role_grants`).
        """

        payload = {
            "grant_key": grant_key,
            "actor_config_role_config_id": actor_config_role_config_id,
            "role_config_id": role_config_id,
            "access_scope": access_scope,
            "participant_kind": participant_kind,
            "class_instance_identity_required": class_instance_identity_required,
            "role_assignment_binding_required": role_assignment_binding_required,
            "grant_policy_json": grant_policy_json,
            "description": description,
        }
        result = await invoke_instance(
            orm_model=self, function_name="create_contract_actor_role_grant", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.contract.experience_contract_actor_role_grant import (
            ExperienceContractActorRoleGrant,
        )

        if isinstance(value, ExperienceContractActorRoleGrant):
            return value
        return ExperienceContractActorRoleGrant.validate_invocation_value(value)

    async def create_node(self, object_projection_graph_node_id: UUID, key: str) -> ProjectionExperienceNode:
        """
        Create a deterministic ProjectionExperienceNode under this ProjectionExperience.

        Contract:
        - Delegates canonical node identity to `ProjectionExperienceNode.build(...)`.
        - Mutates only this ProjectionExperience membership (`projection_experience_nodes`).
        """

        payload = {"object_projection_graph_node_id": object_projection_graph_node_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="create_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node import ProjectionExperienceNode

        if isinstance(value, ProjectionExperienceNode):
            return value
        return ProjectionExperienceNode.validate_invocation_value(value)

    async def create_graph(self, name: str) -> ProjectionExperienceGraph:
        """
        Create one deterministic ProjectionExperienceGraph under this ProjectionExperience.

        Contract:
        - Graph topology and graph-bound profiles evolve through the child
          `ProjectionExperienceGraph` projection reached from this shell rail.
        - API/profile/value contracts are out of scope for this object.
        """

        payload = {"name": name}
        result = await invoke_instance(orm_model=self, function_name="create_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph

        if isinstance(value, ProjectionExperienceGraph):
            return value
        return ProjectionExperienceGraph.validate_invocation_value(value)

    async def create_oigi(
        self, object_instance_graph_identity_id: UUID, key: str | None = None
    ) -> ProjectionExperienceOIGI:
        """
        Create one ProjectionExperienceOIGI bridge under this ProjectionExperience.

        Contract:
        - OIGI topology evolves through the child `ProjectionExperienceOIGI`
          projection reached from this shell rail.
        """

        payload = {"object_instance_graph_identity_id": object_instance_graph_identity_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="create_oigi", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_oigi import ProjectionExperienceOIGI

        if isinstance(value, ProjectionExperienceOIGI):
            return value
        return ProjectionExperienceOIGI.validate_invocation_value(value)

    async def create_section(self, section_id: UUID, section_key: str | None = None) -> ProjectionExperienceSection:
        """
        Create one Attention Section bridge under this ProjectionExperience.

        Contract:
        - Attention owns Section and FocusScope mutation.
        - Experience owns the section+observable -> view-instance resolver.
        - `section_key` is optional denormalized lookup text and is not a runtime mount id.
        """

        payload = {"section_id": section_id, "section_key": section_key}
        result = await invoke_instance(orm_model=self, function_name="create_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_section import ProjectionExperienceSection

        if isinstance(value, ProjectionExperienceSection):
            return value
        return ProjectionExperienceSection.validate_invocation_value(value)

    async def create_section_graph_binding(
        self,
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

        payload = {
            "layout_config_section_config_id": layout_config_section_config_id,
            "projection_experience_view_id": projection_experience_view_id,
            "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
            "binding_key": binding_key,
            "section_key": section_key,
        }
        result = await invoke_instance(orm_model=self, function_name="create_section_graph_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
            ProjectionExperienceSectionGraphBinding,
        )

        if isinstance(value, ProjectionExperienceSectionGraphBinding):
            return value
        return ProjectionExperienceSectionGraphBinding.validate_invocation_value(value)

    async def create_layout_graph_binding(
        self, layout_config_id: UUID, binding_key: str
    ) -> ProjectionExperienceLayoutGraphBinding:
        """
        Create one stable layout graph binding under this ProjectionExperience.

        Contract:
        - This is the Experience-owned layout-level entry point for consumers.
        - The layout target is an explicit portal to Attention layout topology.
        - Child rows point to existing section graph bindings; order remains Attention-owned.
        - This object expresses composition agreement only; it does not activate session state.
        """

        payload = {"layout_config_id": layout_config_id, "binding_key": binding_key}
        result = await invoke_instance(orm_model=self, function_name="create_layout_graph_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
            ProjectionExperienceLayoutGraphBinding,
        )

        if isinstance(value, ProjectionExperienceLayoutGraphBinding):
            return value
        return ProjectionExperienceLayoutGraphBinding.validate_invocation_value(value)


class ProjectionExperienceCreateInput(BaseModel):
    object_projection_graph_identity_id: UUID
    name: str


class ProjectionExperienceCreateOutput(BaseModel):
    value: ProjectionExperience


class ProjectionExperienceCreateBranchInput(BaseModel):
    name: str


class ProjectionExperienceCreateBranchOutput(BaseModel):
    value: ProjectionExperienceBranch


class ProjectionExperienceCreateViewInput(BaseModel):
    api_view_id: UUID
    name: str


class ProjectionExperienceCreateViewOutput(BaseModel):
    value: ProjectionExperienceView


class ProjectionExperienceCreateInvocationActionConfigInput(BaseModel):
    target_kind: ExperienceInvocationActionTargetKind
    api_capability_endpoint_id: UUID | None = Field(default=None)
    sdk_operation_id: UUID | None = Field(default=None)


class ProjectionExperienceCreateInvocationActionConfigOutput(BaseModel):
    value: ExperienceInvocationActionConfig


class ProjectionExperienceCreateProviderInput(BaseModel):
    provider_key: str
    provider_kind: str = Field(default="provider")
    selection_policy: str = Field(default="contract_required")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ProjectionExperienceCreateProviderOutput(BaseModel):
    value: ExperienceProvider


class ProjectionExperienceCreateContractActorRoleGrantInput(BaseModel):
    grant_key: str
    actor_config_role_config_id: UUID
    role_config_id: UUID
    access_scope: str = Field(default="experience")
    participant_kind: str = Field(default="actor")
    class_instance_identity_required: bool = Field(default=False)
    role_assignment_binding_required: bool = Field(default=True)
    grant_policy_json: JsonObject | None = Field(default_factory=JsonObject)
    description: str | None = Field(default=None)


class ProjectionExperienceCreateContractActorRoleGrantOutput(BaseModel):
    value: ExperienceContractActorRoleGrant


class ProjectionExperienceCreateNodeInput(BaseModel):
    object_projection_graph_node_id: UUID
    key: str


class ProjectionExperienceCreateNodeOutput(BaseModel):
    value: ProjectionExperienceNode


class ProjectionExperienceCreateGraphInput(BaseModel):
    name: str


class ProjectionExperienceCreateGraphOutput(BaseModel):
    value: ProjectionExperienceGraph


class ProjectionExperienceCreateOigiInput(BaseModel):
    object_instance_graph_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceCreateOigiOutput(BaseModel):
    value: ProjectionExperienceOIGI


class ProjectionExperienceCreateSectionInput(BaseModel):
    section_id: UUID
    section_key: str | None = Field(default=None)


class ProjectionExperienceCreateSectionOutput(BaseModel):
    value: ProjectionExperienceSection


class ProjectionExperienceCreateSectionGraphBindingInput(BaseModel):
    layout_config_section_config_id: UUID
    projection_experience_view_id: UUID
    projection_experience_graph_identity_id: UUID
    binding_key: str
    section_key: str


class ProjectionExperienceCreateSectionGraphBindingOutput(BaseModel):
    value: ProjectionExperienceSectionGraphBinding


class ProjectionExperienceCreateLayoutGraphBindingInput(BaseModel):
    layout_config_id: UUID
    binding_key: str


class ProjectionExperienceCreateLayoutGraphBindingOutput(BaseModel):
    value: ProjectionExperienceLayoutGraphBinding


FUNCTIONS = {
    "ProjectionExperience": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Construct a deterministic ProjectionExperience under a Projection.\n\nContract:\n- `ProjectionExperience.id` is deterministic for `(projection_id, name)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceCreateInput,
            "output": ProjectionExperienceCreateOutput,
        },
        "create_branch": {
            "canonical": {
                "name": "create_branch",
                "description": "Create a deterministic ProjectionExperienceBranch under this ProjectionExperience.\n\nContract:\n- Delegates canonical branch identity to `ProjectionExperienceBranch.create(...)`.\n- Mutates only this ProjectionExperience membership (`projection_experience_branches`).",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateBranchInput,
            "output": ProjectionExperienceCreateBranchOutput,
        },
        "create_view": {
            "canonical": {
                "name": "create_view",
                "description": "Create a deterministic ProjectionExperienceView under this ProjectionExperience.\n\nContract:\n- Delegates canonical view identity to `ProjectionExperienceView.create(...)`.\n- Mutates only this ProjectionExperience membership (`projection_experience_views`).\n- Binds the Experience-local view mount to one API-owned readable view.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateViewInput,
            "output": ProjectionExperienceCreateViewOutput,
        },
        "create_invocation_action_config": {
            "canonical": {
                "name": "create_invocation_action_config",
                "description": "Create a reusable Experience invocation action config under this ProjectionExperience.\n\nContract:\n- Views, sensors, actuators, and future surfaces bind to this config.\n- API/SDK executable target fields live here, not on consumer-specific wrappers.\n- `target_kind` selects exactly one executable target relationship.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateInvocationActionConfigInput,
            "output": ProjectionExperienceCreateInvocationActionConfigOutput,
        },
        "create_provider": {
            "canonical": {
                "name": "create_provider",
                "description": "Create one Experience-owned public provider slot.\n\nContract:\n- Provider ontologies bind concrete fulfillment to this slot.\n- ProjectionExperience does not import provider-owned operation or contract truth.\n- Mutates only this ProjectionExperience membership (`providers`).",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateProviderInput,
            "output": ProjectionExperienceCreateProviderOutput,
        },
        "create_contract_actor_role_grant": {
            "canonical": {
                "name": "create_contract_actor_role_grant",
                "description": "Create one Experience-owned contract-visible actor-role grant.\n\nContract:\n- This is the public Experience grant providers may accept/reference later.\n- The grant is scoped through ActorConfigRoleConfig, not a raw global role.\n- Mutates only this ProjectionExperience membership (`contract_actor_role_grants`).",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateContractActorRoleGrantInput,
            "output": ProjectionExperienceCreateContractActorRoleGrantOutput,
        },
        "create_node": {
            "canonical": {
                "name": "create_node",
                "description": "Create a deterministic ProjectionExperienceNode under this ProjectionExperience.\n\nContract:\n- Delegates canonical node identity to `ProjectionExperienceNode.build(...)`.\n- Mutates only this ProjectionExperience membership (`projection_experience_nodes`).",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateNodeInput,
            "output": ProjectionExperienceCreateNodeOutput,
        },
        "create_graph": {
            "canonical": {
                "name": "create_graph",
                "description": "Create one deterministic ProjectionExperienceGraph under this ProjectionExperience.\n\nContract:\n- Graph topology and graph-bound profiles evolve through the child\n  `ProjectionExperienceGraph` projection reached from this shell rail.\n- API/profile/value contracts are out of scope for this object.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateGraphInput,
            "output": ProjectionExperienceCreateGraphOutput,
        },
        "create_oigi": {
            "canonical": {
                "name": "create_oigi",
                "description": "Create one ProjectionExperienceOIGI bridge under this ProjectionExperience.\n\nContract:\n- OIGI topology evolves through the child `ProjectionExperienceOIGI`\n  projection reached from this shell rail.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateOigiInput,
            "output": ProjectionExperienceCreateOigiOutput,
        },
        "create_section": {
            "canonical": {
                "name": "create_section",
                "description": "Create one Attention Section bridge under this ProjectionExperience.\n\nContract:\n- Attention owns Section and FocusScope mutation.\n- Experience owns the section+observable -> view-instance resolver.\n- `section_key` is optional denormalized lookup text and is not a runtime mount id.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateSectionInput,
            "output": ProjectionExperienceCreateSectionOutput,
        },
        "create_section_graph_binding": {
            "canonical": {
                "name": "create_section_graph_binding",
                "description": "Create one stable section-graph binding under this ProjectionExperience.\n\nContract:\n- The view binding stays Experience-owned.\n- The layout section target is an explicit portal to Attention layout topology.\n- The graph-occurrence anchor stays explicit and canonical at Experience level.\n- This object expresses section selection agreement only; it does not mutate Attention truth.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateSectionGraphBindingInput,
            "output": ProjectionExperienceCreateSectionGraphBindingOutput,
        },
        "create_layout_graph_binding": {
            "canonical": {
                "name": "create_layout_graph_binding",
                "description": "Create one stable layout graph binding under this ProjectionExperience.\n\nContract:\n- This is the Experience-owned layout-level entry point for consumers.\n- The layout target is an explicit portal to Attention layout topology.\n- Child rows point to existing section graph bindings; order remains Attention-owned.\n- This object expresses composition agreement only; it does not activate session state.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceCreateLayoutGraphBindingInput,
            "output": ProjectionExperienceCreateLayoutGraphBindingOutput,
        },
    },
}

__all__ = [
    "ProjectionExperience",
    "ProjectionExperienceCreateInput",
    "ProjectionExperienceCreateOutput",
    "ProjectionExperienceCreateBranchInput",
    "ProjectionExperienceCreateBranchOutput",
    "ProjectionExperienceCreateViewInput",
    "ProjectionExperienceCreateViewOutput",
    "ProjectionExperienceCreateInvocationActionConfigInput",
    "ProjectionExperienceCreateInvocationActionConfigOutput",
    "ProjectionExperienceCreateProviderInput",
    "ProjectionExperienceCreateProviderOutput",
    "ProjectionExperienceCreateContractActorRoleGrantInput",
    "ProjectionExperienceCreateContractActorRoleGrantOutput",
    "ProjectionExperienceCreateNodeInput",
    "ProjectionExperienceCreateNodeOutput",
    "ProjectionExperienceCreateGraphInput",
    "ProjectionExperienceCreateGraphOutput",
    "ProjectionExperienceCreateOigiInput",
    "ProjectionExperienceCreateOigiOutput",
    "ProjectionExperienceCreateSectionInput",
    "ProjectionExperienceCreateSectionOutput",
    "ProjectionExperienceCreateSectionGraphBindingInput",
    "ProjectionExperienceCreateSectionGraphBindingOutput",
    "ProjectionExperienceCreateLayoutGraphBindingInput",
    "ProjectionExperienceCreateLayoutGraphBindingOutput",
    "FUNCTIONS",
]
