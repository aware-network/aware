from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ProjectionExperienceViewStateProvider(ORMModel):
    """
    Experience-owned view-state provider binding.
    Contract:
    - There is one effective provider per ProjectionExperienceView.
    - The provider is a pure read transformation from host-owned materialized state to the view state model.
    - Runtime callables and SDK functions are implementation adapters selected by this canonical binding.
    """

    # Attributes
    provider_ref: str
    provider_kind: str = Field(default="runtime_callable")
    purity: str = Field(default="pure_read")

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.state_providers")
