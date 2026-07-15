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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology.program.program_layout_section import ProgramLayoutSection


class ProgramLayout(ORMModel):
    """Runtime materialized layout state for one Program run."""

    # Relationships
    config: ProgramConfigLayout | None = Field(default=None, exclude=True)
    sections: list[ProgramLayoutSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    is_active: bool = Field(default=False)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.layouts")
    config_id: UUID | None = Field(default=None, description="Foreign key for ProgramLayout.config")

    @classmethod
    async def build(
        cls, program_id: UUID, key: str, config_id: UUID | None = None, is_active: bool = False
    ) -> ProgramLayout:
        """Create a deterministic ProgramLayout under a Program."""

        payload = {"program_id": program_id, "key": key, "config_id": config_id, "is_active": is_active}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramLayout):
            return value
        return ProgramLayout.validate_invocation_value(value)


class ProgramLayoutBuildInput(BaseModel):
    program_id: UUID
    key: str
    config_id: UUID | None = Field(default=None)
    is_active: bool = Field(default=False)


class ProgramLayoutBuildOutput(BaseModel):
    value: ProgramLayout


FUNCTIONS = {
    "ProgramLayout": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ProgramLayout under a Program.",
                "is_constructor": True,
            },
            "input": ProgramLayoutBuildInput,
            "output": ProgramLayoutBuildOutput,
        },
    },
}

__all__ = [
    "ProgramLayout",
    "ProgramLayoutBuildInput",
    "ProgramLayoutBuildOutput",
    "FUNCTIONS",
]
