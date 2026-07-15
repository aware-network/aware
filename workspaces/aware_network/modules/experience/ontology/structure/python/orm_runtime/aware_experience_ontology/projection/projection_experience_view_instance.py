from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology.projection.projection_experience_view_invocation_action import (
        ProjectionExperienceViewInvocationAction,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProjectionExperienceViewInstance(ORMModel):
    """
    Concrete runtime/display instance of one ProjectionExperienceView.
    Contract:
    - `ProjectionExperienceView` remains configuration.
    - This object identifies one concrete fulfillment of a view for a
    section-graph binding and optional materialized branch.
    - Attention is not part of this object's identity. Attention selects
    Section -> FocusScope -> Observable; Experience resolves Section + Observable
    to this view instance through ProjectionExperienceSectionView.
    """

    # Relationships
    section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    invocation_actions: list[ProjectionExperienceViewInvocationAction] = Field(default_factory=list)

    # Attributes
    view_instance_key: str
    state_commit_id: UUID | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.view_instances")
    section_graph_binding_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInstance.section_graph_binding"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for ProjectionExperienceViewInstance.object_instance_graph_branch"
    )

    async def record_action_invocation(
        self,
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

        payload = {
            "view_invocation_action_config_id": view_invocation_action_config_id,
            "invocation_key": invocation_key,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "actor_id": actor_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="record_action_invocation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view_invocation_action import (
            ProjectionExperienceViewInvocationAction,
        )

        if isinstance(value, ProjectionExperienceViewInvocationAction):
            return value
        return ProjectionExperienceViewInvocationAction.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience_view(
        cls,
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

        payload = {
            "projection_experience_view_id": projection_experience_view_id,
            "section_graph_binding_id": section_graph_binding_id,
            "view_instance_key": view_instance_key,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "state_commit_id": state_commit_id,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_view", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceViewInstance):
            return value
        return ProjectionExperienceViewInstance.validate_invocation_value(value)


class ProjectionExperienceViewInstanceRecordActionInvocationInput(BaseModel):
    view_invocation_action_config_id: UUID
    invocation_key: UUID
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class ProjectionExperienceViewInstanceRecordActionInvocationOutput(BaseModel):
    value: ProjectionExperienceViewInvocationAction


class ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewInput(BaseModel):
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.view_instances")
    section_graph_binding_id: UUID
    view_instance_key: str
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    state_commit_id: UUID | None = Field(default=None)
    status: str = Field(default="active")


class ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewOutput(BaseModel):
    value: ProjectionExperienceViewInstance


FUNCTIONS = {
    "ProjectionExperienceViewInstance": {
        "record_action_invocation": {
            "canonical": {
                "name": "record_action_invocation",
                "description": "Record one action invocation performed through this concrete view instance.\n\nContract:\n- `view_invocation_action_config_id` points to the view-exposed action config binding.\n- The actual call is recorded as a generic `ExperienceInvocationAction`.\n- This view instance stores only the provenance bridge to that invocation.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewInstanceRecordActionInvocationInput,
            "output": ProjectionExperienceViewInstanceRecordActionInvocationOutput,
        },
        "build_via_projection_experience_view": {
            "canonical": {
                "name": "build_via_projection_experience_view",
                "description": "Create one deterministic view instance under a ProjectionExperienceView.\n\nContract:\n- Identity is scoped by parent view, section graph binding, and view instance key.\n- `section_graph_binding` is the canonical bridge to view + layout section + graph occurrence.\n- Runtime focus/environment/thread evidence belongs on invocation or transition receipts,\n  not on the view-instance identity.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewInput,
            "output": ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceViewInstance",
    "ProjectionExperienceViewInstanceRecordActionInvocationInput",
    "ProjectionExperienceViewInstanceRecordActionInvocationOutput",
    "ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewInput",
    "ProjectionExperienceViewInstanceBuildViaProjectionExperienceViewOutput",
    "FUNCTIONS",
]
