from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_experience_ontology_dto.invocation.role_config_invocation_action_config import (
        RoleConfigInvocationActionConfig,
    )
    from aware_sdk_ontology_dto.sdk.sdk_operation import SdkOperation


class ExperienceInvocationActionConfig(BaseModel):
    """
    Experience-owned reusable invocation action configuration.
    Contract:
    - This is the canonical executable target configuration for an invocation
    action.
    - Projection views, sensors, actuators, and future surfaces consume this
    config instead of duplicating executable API/SDK target fields.
    - View-action identity lives on `ProjectionExperienceViewInvocationActionConfig`
    through API-owned `ApiViewCapabilityEndpoint` and optional SDK-owned
    `SdkOperationApiViewCapabilityEndpoint`; it does not live here.
    - Actual invocation receipts are children of the surface config that
    handled the action, for example `ProjectionExperienceViewInvocationActionConfig`.
    """

    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)
    sdk_operation: SdkOperation | None = Field(default=None)
    role_policies: list[RoleConfigInvocationActionConfig] = Field(default_factory=list)

    # Attributes
    target_kind: ExperienceInvocationActionTargetKind
