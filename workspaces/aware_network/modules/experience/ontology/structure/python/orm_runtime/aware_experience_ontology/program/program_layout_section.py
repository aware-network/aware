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
    from aware_experience_ontology.program.program_branch import ProgramBranch
    from aware_experience_ontology.program.program_config_layout_port_section import ProgramConfigLayoutPortSection


class ProgramLayoutSection(ORMModel):
    """
    Runtime section state under one ProgramWindowLayout.
    Contract:
    - Stores current branch/view targeting for one visible section.
    - No reverse ProgramWindowLayout reference is declared in this child class.
    """

    # Relationships
    port_section: ProgramConfigLayoutPortSection | None = Field(default=None, exclude=True)
    program_branch: ProgramBranch | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    order: int = Field(default=0)
    is_visible: bool = Field(default=True)
    flex: float | None = Field(default=None)
    is_active: bool = Field(default=False)
    view_key: str | None = Field(default=None)

    # Foreign Keys
    program_layout_id: UUID = Field(description="Foreign key for ProgramLayout.sections")
    port_section_id: UUID | None = Field(default=None, description="Foreign key for ProgramLayoutSection.port_section")
    program_branch_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramLayoutSection.program_branch"
    )

    @classmethod
    async def build(
        cls,
        layout_id: UUID,
        key: str,
        order: int = 0,
        is_visible: bool = True,
        flex: float | None = None,
        is_active: bool = False,
        view_key: str | None = None,
        program_branch_id: UUID | None = None,
        port_section_id: UUID | None = None,
    ) -> ProgramLayoutSection:
        """Create a deterministic ProgramLayoutSection under a Program."""

        payload = {
            "layout_id": layout_id,
            "key": key,
            "order": order,
            "is_visible": is_visible,
            "flex": flex,
            "is_active": is_active,
            "view_key": view_key,
            "program_branch_id": program_branch_id,
            "port_section_id": port_section_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramLayoutSection):
            return value
        return ProgramLayoutSection.validate_invocation_value(value)


class ProgramLayoutSectionBuildInput(BaseModel):
    layout_id: UUID
    key: str
    order: int = Field(default=0)
    is_visible: bool = Field(default=True)
    flex: float | None = Field(default=None)
    is_active: bool = Field(default=False)
    view_key: str | None = Field(default=None)
    program_branch_id: UUID | None = Field(default=None)
    port_section_id: UUID | None = Field(default=None)


class ProgramLayoutSectionBuildOutput(BaseModel):
    value: ProgramLayoutSection


FUNCTIONS = {
    "ProgramLayoutSection": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ProgramLayoutSection under a Program.",
                "is_constructor": True,
            },
            "input": ProgramLayoutSectionBuildInput,
            "output": ProgramLayoutSectionBuildOutput,
        },
    },
}

__all__ = [
    "ProgramLayoutSection",
    "ProgramLayoutSectionBuildInput",
    "ProgramLayoutSectionBuildOutput",
    "FUNCTIONS",
]
