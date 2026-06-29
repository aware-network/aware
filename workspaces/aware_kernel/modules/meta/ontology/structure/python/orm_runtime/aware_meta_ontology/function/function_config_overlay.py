from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_config import FunctionConfig


class FunctionConfigOverlay(ORMModel):
    """Per-language overrides for FunctionConfig entities."""

    # Relationships
    function_config: FunctionConfig | None = Field(
        default=None, exclude=True, description="Association target reference to FunctionConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    lang_flags: JsonObject | None = Field(default=None)

    # Foreign Keys
    function_config_id: UUID = Field(description="Join FK to FunctionConfig")
    object_config_graph_overlay_id: UUID = Field(description="Join FK to ObjectConfigGraphOverlay")


FUNCTIONS = {
    "FunctionConfigOverlay": {},
}

__all__ = [
    "FunctionConfigOverlay",
    "FUNCTIONS",
]
