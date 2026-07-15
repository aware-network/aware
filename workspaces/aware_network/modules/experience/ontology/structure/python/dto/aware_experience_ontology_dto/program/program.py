from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.program_enums import ProgramRunStatus

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl import ProgramImpl
    from aware_experience_ontology_dto.program.program_actor import ProgramActor
    from aware_experience_ontology_dto.program.program_attribute import ProgramAttribute
    from aware_experience_ontology_dto.program.program_branch import ProgramBranch
    from aware_experience_ontology_dto.program.program_input_attribute import ProgramInputAttribute
    from aware_experience_ontology_dto.program.program_layout import ProgramLayout
    from aware_experience_ontology_dto.program.program_turn import ProgramTurn


class Program(BaseModel):
    """
    Runtime program execution truth owned by Experience.
    Contract:
    - Program is the runtime instance of an Experience ProgramImpl.
    - Environment thread participation is modeled by Experience-owned
    `thread.ThreadProgram` binding objects.
    - Environment Thread does not reference Program; Experience binds to
    Environment topology explicitly.
    - Turn lifecycle remains Experience-owned by `turn.Turn`.
    """

    # Relationships
    program_impl: ProgramImpl | None = Field(default=None)
    program_actors: list[ProgramActor] = Field(default_factory=list)
    attributes: list[ProgramAttribute] = Field(default_factory=list)
    input_attributes: list[ProgramInputAttribute] = Field(default_factory=list)
    branches: list[ProgramBranch] = Field(default_factory=list)
    layouts: list[ProgramLayout] = Field(default_factory=list)
    turns: list[ProgramTurn] = Field(default_factory=list)
    active_turn: ProgramTurn | None = Field(default=None)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: ProgramRunStatus = Field(default=ProgramRunStatus.pending)
    result_summary: str | None = Field(default=None)
    started_at_unix_ms: int | None = Field(default=None)
    terminal_at_unix_ms: int | None = Field(default=None)
    terminal_status: str | None = Field(default=None)
