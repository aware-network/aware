from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_experience_ontology_dto.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_sdk_ontology_dto.sdk.sdk_operation_api_view_capability_endpoint import (
        SdkOperationApiViewCapabilityEndpoint,
    )


class ProjectionExperienceViewInvocationActionConfig(BaseModel):
    """
    View-owned binding to one generic Experience invocation action config.
    Contract:
    - Panes render and dispatch these actions by `action_key`; they do not own
    the SDK/API capability target.
    - API-owned `ApiViewCapabilityEndpoint` is mandatory view-action truth.
    - SDK-owned `SdkOperationApiViewCapabilityEndpoint` is optional client-facing
    operation truth for the same API view capability endpoint.
    - Generic executable target relationships live on `ExperienceInvocationActionConfig`.
    - Reactivity actions remain separate under `ActionConfig` / `ActionExperience`.
    """

    # Relationships
    api_view_capability_endpoint: ApiViewCapabilityEndpoint | None = Field(default=None)
    sdk_operation_api_view_capability_endpoint: SdkOperationApiViewCapabilityEndpoint | None = Field(default=None)
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)

    # Attributes
    action_key: str
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)
