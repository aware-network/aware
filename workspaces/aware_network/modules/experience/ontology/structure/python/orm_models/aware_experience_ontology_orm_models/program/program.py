from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.program_enums import ProgramRunStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl import ProgramImpl
    from aware_experience_ontology_orm_models.program.program_actor import ProgramActor
    from aware_experience_ontology_orm_models.program.program_attribute import ProgramAttribute
    from aware_experience_ontology_orm_models.program.program_branch import ProgramBranch
    from aware_experience_ontology_orm_models.program.program_input_attribute import ProgramInputAttribute
    from aware_experience_ontology_orm_models.program.program_layout import ProgramLayout
    from aware_experience_ontology_orm_models.program.program_turn import ProgramTurn


class Program(ORMModel):
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
    program_impl: ProgramImpl | None = Field(default=None, exclude=True)
    program_actors: list[ProgramActor] = Field(default_factory=list, exclude=True)
    attributes: list[ProgramAttribute] = Field(default_factory=list, exclude=True)
    input_attributes: list[ProgramInputAttribute] = Field(default_factory=list, exclude=True)
    branches: list[ProgramBranch] = Field(default_factory=list, exclude=True)
    layouts: list[ProgramLayout] = Field(default_factory=list, exclude=True)
    turns: list[ProgramTurn] = Field(default_factory=list, exclude=True)
    active_turn: ProgramTurn | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: ProgramRunStatus = Field(default=ProgramRunStatus.pending)
    result_summary: str | None = Field(default=None)
    started_at_unix_ms: int | None = Field(default=None)
    terminal_at_unix_ms: int | None = Field(default=None)
    terminal_status: str | None = Field(default=None)

    # Foreign Keys
    program_impl_id: UUID = Field(description="Foreign key for Program.program_impl")
    active_turn_id: UUID | None = Field(default=None, description="Foreign key for Program.active_turn")
