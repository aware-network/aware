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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_attention_ontology.layout.layout import Layout
    from aware_experience_ontology.program.program_config_layout_port_section import ProgramConfigLayoutPortSection


class ProgramConfigLayout(ORMModel):
    """
    Declarative layout contract under one ProgramConfig.
    Contract:
    - Defines section topology and port placement policies for one program config.
    - Runtime materializes ProgramConfigLayout instances from this config rail.
    """

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)
    port_sections: list[ProgramConfigLayoutPortSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    is_default: bool = Field(default=False)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.layouts")
    layout_id: UUID = Field(description="Foreign key for ProgramConfigLayout.layout")

    async def add_port_section(
        self,
        program_config_port_id: UUID,
        layout_section_id: UUID,
        on_bind: ProgramSlotOnBind = ProgramSlotOnBind.replace,
        is_visible_default: bool | None = None,
    ) -> ProgramConfigLayoutPortSection:
        """Attach one deterministic ProgramConfigLayoutPortSection under this ProgramConfigLayout."""

        payload = {
            "program_config_port_id": program_config_port_id,
            "layout_section_id": layout_section_id,
            "on_bind": on_bind,
            "is_visible_default": is_visible_default,
        }
        result = await invoke_instance(orm_model=self, function_name="add_port_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_layout_port_section import ProgramConfigLayoutPortSection

        if isinstance(value, ProgramConfigLayoutPortSection):
            return value
        return ProgramConfigLayoutPortSection.validate_invocation_value(value)

    @classmethod
    async def build_via_program_config(
        cls, program_config_id: UUID, key: str, is_default: bool = False
    ) -> ProgramConfigLayout:
        """Create a deterministic ProgramConfigLayout under a ProgramConfig."""

        payload = {"program_config_id": program_config_id, "key": key, "is_default": is_default}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigLayout):
            return value
        return ProgramConfigLayout.validate_invocation_value(value)


class ProgramConfigLayoutAddPortSectionInput(BaseModel):
    program_config_port_id: UUID
    layout_section_id: UUID
    on_bind: ProgramSlotOnBind = Field(default=ProgramSlotOnBind.replace)
    is_visible_default: bool | None = Field(default=None)


class ProgramConfigLayoutAddPortSectionOutput(BaseModel):
    value: ProgramConfigLayoutPortSection


class ProgramConfigLayoutBuildViaProgramConfigInput(BaseModel):
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.layouts")
    key: str
    is_default: bool = Field(default=False)


class ProgramConfigLayoutBuildViaProgramConfigOutput(BaseModel):
    value: ProgramConfigLayout


FUNCTIONS = {
    "ProgramConfigLayout": {
        "add_port_section": {
            "canonical": {
                "name": "add_port_section",
                "description": "Attach one deterministic ProgramConfigLayoutPortSection under this ProgramConfigLayout.",
                "is_constructor": False,
            },
            "input": ProgramConfigLayoutAddPortSectionInput,
            "output": ProgramConfigLayoutAddPortSectionOutput,
        },
        "build_via_program_config": {
            "canonical": {
                "name": "build_via_program_config",
                "description": "Create a deterministic ProgramConfigLayout under a ProgramConfig.",
                "is_constructor": True,
            },
            "input": ProgramConfigLayoutBuildViaProgramConfigInput,
            "output": ProgramConfigLayoutBuildViaProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigLayout",
    "ProgramConfigLayoutAddPortSectionInput",
    "ProgramConfigLayoutAddPortSectionOutput",
    "ProgramConfigLayoutBuildViaProgramConfigInput",
    "ProgramConfigLayoutBuildViaProgramConfigOutput",
    "FUNCTIONS",
]
