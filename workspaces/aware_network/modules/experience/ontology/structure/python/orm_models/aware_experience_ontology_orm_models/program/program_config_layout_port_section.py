from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.program_enums import ProgramSlotOnBind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_section import LayoutSection
    from aware_experience_ontology_orm_models.program.program_config_port import ProgramConfigPort


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
