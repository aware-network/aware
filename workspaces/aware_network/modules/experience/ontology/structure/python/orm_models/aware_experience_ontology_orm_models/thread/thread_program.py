from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.thread.thread import Thread
    from aware_experience_ontology_orm_models.program.program import Program


class ThreadProgram(ORMModel):
    """
    Experience-owned Environment Thread -> Program association edge.
    Contract:
    - Environment owns the real Thread topology.
    - Experience owns the Program runtime and the ThreadProgram binding.
    - Environment never points back to Program; Experience explicitly binds
    a Program to the Thread it can operate within.
    """

    # Relationships
    thread: Thread | None = Field(default=None, exclude=True)
    program: Program | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None, description="Stable association key for thread-local program surfaces.")
    position: int | None = Field(default=None, description="Ordering hint for thread runtime program timelines.")
    is_default: bool = Field(
        default=False, description="Marks preferred/default program association for thread surfaces."
    )

    # Foreign Keys
    thread_id: UUID = Field(description="Foreign key for ThreadProgram.thread")
    program_id: UUID = Field(description="Foreign key for ThreadProgram.program")
