from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramSlotOnBind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_attention_ontology.layout.layout_section import LayoutSection
    from aware_experience_ontology.program.program_config_port import ProgramConfigPort


class ProgramConfigLayoutPortSection(ORMModel):
    """Declarative port-to-section placement mapping for bind-time adaptation."""

    # Relationships
    program_config_port: ProgramConfigPort | None = Field(default=None, exclude=True)
    layout_section: LayoutSection | None = Field(default=None, exclude=True)

    # Attributes
    on_bind: ProgramSlotOnBind = Field(default=ProgramSlotOnBind.replace)
    is_visible_default: bool | None = Field(default=None)

    # Foreign Keys
    program_config_layout_id: UUID = Field(description="Foreign key for ProgramConfigLayout.port_sections")
    program_config_port_id: UUID = Field(
        description="Foreign key for ProgramConfigLayoutPortSection.program_config_port"
    )
    layout_section_id: UUID = Field(description="Foreign key for ProgramConfigLayoutPortSection.layout_section")

    @classmethod
    async def build_via_program_config_layout(
        cls,
        program_config_layout_id: UUID,
        program_config_port_id: UUID,
        layout_section_id: UUID,
        on_bind: ProgramSlotOnBind = ProgramSlotOnBind.replace,
        is_visible_default: bool | None = None,
    ) -> ProgramConfigLayoutPortSection:
        """Create a deterministic ProgramConfigLayoutPortSection under a ProgramConfigLayout."""

        payload = {
            "program_config_layout_id": program_config_layout_id,
            "program_config_port_id": program_config_port_id,
            "layout_section_id": layout_section_id,
            "on_bind": on_bind,
            "is_visible_default": is_visible_default,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_layout", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigLayoutPortSection):
            return value
        return ProgramConfigLayoutPortSection.validate_invocation_value(value)


class ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutInput(BaseModel):
    program_config_layout_id: UUID = Field(description="Foreign key for ProgramConfigLayout.port_sections")
    program_config_port_id: UUID
    layout_section_id: UUID
    on_bind: ProgramSlotOnBind = Field(default=ProgramSlotOnBind.replace)
    is_visible_default: bool | None = Field(default=None)


class ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutOutput(BaseModel):
    value: ProgramConfigLayoutPortSection


FUNCTIONS = {
    "ProgramConfigLayoutPortSection": {
        "build_via_program_config_layout": {
            "canonical": {
                "name": "build_via_program_config_layout",
                "description": "Create a deterministic ProgramConfigLayoutPortSection under a ProgramConfigLayout.",
                "is_constructor": True,
            },
            "input": ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutInput,
            "output": ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutOutput,
        },
    },
}

__all__ = [
    "ProgramConfigLayoutPortSection",
    "ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutInput",
    "ProgramConfigLayoutPortSectionBuildViaProgramConfigLayoutOutput",
    "FUNCTIONS",
]
