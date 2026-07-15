from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class SectionConfig(BaseModel):
    """
    Declarative section configuration for Attention.
    Contract:
    - Config-level section source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
