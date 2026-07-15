from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout import Layout
    from aware_experience_ontology_dto.program.program_config_layout_port_section import ProgramConfigLayoutPortSection


class ProgramConfigLayout(BaseModel):
    """
    Declarative layout contract under one ProgramConfig.
    Contract:
    - Defines section topology and port placement policies for one program config.
    - Runtime materializes ProgramConfigLayout instances from this config rail.
    """

    # Relationships
    layout: Layout | None = Field(default=None)
    port_sections: list[ProgramConfigLayoutPortSection] = Field(default_factory=list)

    # Attributes
    key: str
    is_default: bool = Field(default=False)
