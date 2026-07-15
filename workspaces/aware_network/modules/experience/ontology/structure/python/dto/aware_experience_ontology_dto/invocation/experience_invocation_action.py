from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_call import ApiCall
    from aware_experience_ontology_dto.invocation.experience_invocation_action_commit import (
        ExperienceInvocationActionCommit,
    )
    from aware_experience_ontology_dto.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_experience_ontology_dto.invocation.experience_invocation_action_propagation import (
        ExperienceInvocationActionPropagation,
    )
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_sdk_ontology_dto.sdk.sdk_operation_call import SdkOperationCall


class ExperienceInvocationAction(BaseModel):
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
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)
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
