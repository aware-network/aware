from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_config import FunctionConfig


class FunctionConfigOverlay(BaseModel):
    """Per-language overrides for FunctionConfig entities."""

    # Relationships
    function_config: FunctionConfig | None = Field(
        default=None, description="Association target reference to FunctionConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    lang_flags: JsonObject | None = Field(default=None)
