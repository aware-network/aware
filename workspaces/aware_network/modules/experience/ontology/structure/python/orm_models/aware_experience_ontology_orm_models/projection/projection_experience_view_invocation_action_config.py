from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_sdk_ontology_orm_models.sdk.sdk_operation_api_view_capability_endpoint import (
        SdkOperationApiViewCapabilityEndpoint,
    )


class ProjectionExperienceViewInvocationActionConfig(ORMModel):
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

    # Foreign Keys
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProjectionExperienceView.invocation_action_configs"
    )
    api_view_capability_endpoint_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.api_view_capability_endpoint"
    )
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(
        default=None,
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.sdk_operation_api_view_capability_endpoint",
    )
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.experience_invocation_action_config"
    )
