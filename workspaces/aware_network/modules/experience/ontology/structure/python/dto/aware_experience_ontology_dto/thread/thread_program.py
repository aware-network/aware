from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.thread.thread import Thread
    from aware_experience_ontology_dto.program.program import Program


class ThreadProgram(BaseModel):
    """
    Experience-owned Environment Thread -> Program association edge.
    Contract:
    - Environment owns the real Thread topology.
    - Experience owns the Program runtime and the ThreadProgram binding.
    - Environment never points back to Program; Experience explicitly binds
    a Program to the Thread it can operate within.
    """

    # Relationships
    thread: Thread | None = Field(default=None)
    program: Program | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None, description="Stable association key for thread-local program surfaces.")
    position: int | None = Field(default=None, description="Ordering hint for thread runtime program timelines.")
    is_default: bool = Field(
        default=False, description="Marks preferred/default program association for thread surfaces."
    )
