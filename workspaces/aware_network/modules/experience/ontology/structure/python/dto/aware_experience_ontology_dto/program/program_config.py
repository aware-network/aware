from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology_dto.program.program_config_attribute_config import ProgramConfigAttributeConfig
    from aware_experience_ontology_dto.program.program_config_input_config import ProgramConfigInputConfig
    from aware_experience_ontology_dto.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology_dto.program.program_config_port import ProgramConfigPort


class ProgramConfig(BaseModel):
    """
    Declarative program configuration unit.
    Contract:
    - Stores stable config intent and projection-port bindings.
    - Is graph-agnostic; graph membership is represented by ProgramConfigGraphProgramConfig edges.
    - Does not execute; runtime creates Program instances and Turn receipts.
    """

    # Relationships
    actor_configs: list[ProgramConfigActorConfig] = Field(default_factory=list)
    attribute_configs: list[ProgramConfigAttributeConfig] = Field(default_factory=list)
    input_configs: list[ProgramConfigInputConfig] = Field(default_factory=list)
    ports: list[ProgramConfigPort] = Field(default_factory=list)
    layouts: list[ProgramConfigLayout] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)
