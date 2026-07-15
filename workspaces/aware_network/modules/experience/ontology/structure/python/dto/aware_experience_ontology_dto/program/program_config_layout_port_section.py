from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.program_enums import ProgramSlotOnBind

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_section import LayoutSection
    from aware_experience_ontology_dto.program.program_config_port import ProgramConfigPort


class ProgramConfigLayoutPortSection(BaseModel):
    """Declarative port-to-section placement mapping for bind-time adaptation."""

    # Relationships
    program_config_port: ProgramConfigPort | None = Field(default=None)
    layout_section: LayoutSection | None = Field(default=None)

    # Attributes
    on_bind: ProgramSlotOnBind = Field(default=ProgramSlotOnBind.replace)
    is_visible_default: bool | None = Field(default=None)
