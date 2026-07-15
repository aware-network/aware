from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_actor_config import ProgramConfigActorConfig
    from aware_experience_ontology_orm_models.program.program_config_attribute_config import (
        ProgramConfigAttributeConfig,
    )
    from aware_experience_ontology_orm_models.program.program_config_input_config import ProgramConfigInputConfig
    from aware_experience_ontology_orm_models.program.program_config_layout import ProgramConfigLayout
    from aware_experience_ontology_orm_models.program.program_config_port import ProgramConfigPort


class ProgramConfig(ORMModel):
    """
    Declarative program configuration unit.
    Contract:
    - Stores stable config intent and projection-port bindings.
    - Is graph-agnostic; graph membership is represented by ProgramConfigGraphProgramConfig edges.
    - Does not execute; runtime creates Program instances and Turn receipts.
    """

    # Relationships
    actor_configs: list[ProgramConfigActorConfig] = Field(default_factory=list, exclude=True)
    attribute_configs: list[ProgramConfigAttributeConfig] = Field(default_factory=list, exclude=True)
    input_configs: list[ProgramConfigInputConfig] = Field(default_factory=list, exclude=True)
    ports: list[ProgramConfigPort] = Field(default_factory=list, exclude=True)
    layouts: list[ProgramConfigLayout] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    is_default: bool = Field(default=False)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)
