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
    from aware_api_ontology.api.api_call import ApiCall
    from aware_experience_ontology.invocation.experience_invocation_action_commit import (
        ExperienceInvocationActionCommit,
    )
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_experience_ontology.invocation.experience_invocation_action_propagation import (
        ExperienceInvocationActionPropagation,
    )
    from aware_identity_ontology.actor.actor import Actor
    from aware_sdk_ontology.sdk.sdk_operation_call import SdkOperationCall


class ExperienceInvocationAction(ORMModel):
    """
    Experience-owned record of one actual invocation action.
    Contract:
    - `ExperienceInvocationActionConfig` is reusable configuration.
    - `ExperienceInvocationAction` is the single standalone invocation receipt.
    - Surface provenance (view, sensor, actuator, action-experience policy)
    attaches through surface-specific bridge objects; surfaces must not create
    separate receipt identities for the same crossing.
    - API and SDK receipts stay module-owned and are linked here for
    cross-surface provenance.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None, exclude=True)
    actor: Actor | None = Field(default=None)
    api_call: ApiCall | None = Field(default=None)
    commits: list[ExperienceInvocationActionCommit] = Field(default_factory=list)
    propagations: list[ExperienceInvocationActionPropagation] = Field(default_factory=list)
    sdk_operation_call: SdkOperationCall | None = Field(default=None)

    # Attributes
    invocation_key: UUID
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")

    # Foreign Keys
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ExperienceInvocationAction.experience_invocation_action_config"
    )
    actor_id: UUID | None = Field(default=None, description="Foreign key for ExperienceInvocationAction.actor")
    api_call_id: UUID | None = Field(default=None, description="Foreign key for ExperienceInvocationAction.api_call")
    sdk_operation_call_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceInvocationAction.sdk_operation_call"
    )

    @classmethod
    async def build(
        cls,
        experience_invocation_action_config_id: UUID,
        invocation_key: UUID,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> ExperienceInvocationAction:
        """
        Create one deterministic standalone invocation receipt.

        Contract:
        - Stable identity is `(experience_invocation_action_config, invocation_key)`.
        - `invocation_key` is stable for one dispatch attempt.
        - `actor_id` links to Identity-owned Actor provenance.
        - `api_call_id` and `sdk_operation_call_id` are optional module-owned
          receipts for the same dispatch.
        """

        payload = {
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "invocation_key": invocation_key,
            "actor_id": actor_id,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceInvocationAction):
            return value
        return ExperienceInvocationAction.validate_invocation_value(value)

    async def add_commit(
        self, object_instance_graph_commit_id: UUID, commit_role: str = "mutation", description: str | None = None
    ) -> ExperienceInvocationActionCommit:
        """
        Link one graph commit produced or consumed by this invocation action.

        Contract:
        - The commit wrapper remains Meta-owned.
        - Events emitted from that commit are linked through child commit-event edges.
        """

        payload = {
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "commit_role": commit_role,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_commit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action_commit import (
            ExperienceInvocationActionCommit,
        )

        if isinstance(value, ExperienceInvocationActionCommit):
            return value
        return ExperienceInvocationActionCommit.validate_invocation_value(value)

    async def add_propagation(
        self, target_invocation_action_id: UUID, propagation_kind: str = "invokes", description: str | None = None
    ) -> ExperienceInvocationActionPropagation:
        """
        Link this invocation action to another invocation action it caused.

        Contract:
        - SDK actions can point to API actions, service actions, or future
          adapter-specific actions without collapsing their receipts.
        - Commit and event provenance stays on the action that produced it.
        """

        payload = {
            "target_invocation_action_id": target_invocation_action_id,
            "propagation_kind": propagation_kind,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="add_propagation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action_propagation import (
            ExperienceInvocationActionPropagation,
        )

        if isinstance(value, ExperienceInvocationActionPropagation):
            return value
        return ExperienceInvocationActionPropagation.validate_invocation_value(value)


class ExperienceInvocationActionBuildInput(BaseModel):
    experience_invocation_action_config_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class ExperienceInvocationActionBuildOutput(BaseModel):
    value: ExperienceInvocationAction


class ExperienceInvocationActionAddCommitInput(BaseModel):
    object_instance_graph_commit_id: UUID
    commit_role: str = Field(default="mutation")
    description: str | None = Field(default=None)


class ExperienceInvocationActionAddCommitOutput(BaseModel):
    value: ExperienceInvocationActionCommit


class ExperienceInvocationActionAddPropagationInput(BaseModel):
    target_invocation_action_id: UUID
    propagation_kind: str = Field(default="invokes")
    description: str | None = Field(default=None)


class ExperienceInvocationActionAddPropagationOutput(BaseModel):
    value: ExperienceInvocationActionPropagation


FUNCTIONS = {
    "ExperienceInvocationAction": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic standalone invocation receipt.\n\nContract:\n- Stable identity is `(experience_invocation_action_config, invocation_key)`.\n- `invocation_key` is stable for one dispatch attempt.\n- `actor_id` links to Identity-owned Actor provenance.\n- `api_call_id` and `sdk_operation_call_id` are optional module-owned\n  receipts for the same dispatch.",
                "is_constructor": True,
            },
            "input": ExperienceInvocationActionBuildInput,
            "output": ExperienceInvocationActionBuildOutput,
        },
        "add_commit": {
            "canonical": {
                "name": "add_commit",
                "description": "Link one graph commit produced or consumed by this invocation action.\n\nContract:\n- The commit wrapper remains Meta-owned.\n- Events emitted from that commit are linked through child commit-event edges.",
                "is_constructor": False,
            },
            "input": ExperienceInvocationActionAddCommitInput,
            "output": ExperienceInvocationActionAddCommitOutput,
        },
        "add_propagation": {
            "canonical": {
                "name": "add_propagation",
                "description": "Link this invocation action to another invocation action it caused.\n\nContract:\n- SDK actions can point to API actions, service actions, or future\n  adapter-specific actions without collapsing their receipts.\n- Commit and event provenance stays on the action that produced it.",
                "is_constructor": False,
            },
            "input": ExperienceInvocationActionAddPropagationInput,
            "output": ExperienceInvocationActionAddPropagationOutput,
        },
    },
}

__all__ = [
    "ExperienceInvocationAction",
    "ExperienceInvocationActionBuildInput",
    "ExperienceInvocationActionBuildOutput",
    "ExperienceInvocationActionAddCommitInput",
    "ExperienceInvocationActionAddCommitOutput",
    "ExperienceInvocationActionAddPropagationInput",
    "ExperienceInvocationActionAddPropagationOutput",
    "FUNCTIONS",
]
