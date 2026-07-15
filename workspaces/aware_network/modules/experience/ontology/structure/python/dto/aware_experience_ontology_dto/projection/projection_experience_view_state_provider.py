from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ProjectionExperienceViewStateProvider(BaseModel):
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
