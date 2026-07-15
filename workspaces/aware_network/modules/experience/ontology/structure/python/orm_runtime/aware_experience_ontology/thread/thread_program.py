from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_environment_ontology.thread.thread import Thread
    from aware_experience_ontology.program.program import Program


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

    @classmethod
    async def create(
        cls,
        thread_id: UUID,
        program_id: UUID,
        key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
    ) -> ThreadProgram:
        """
        Construct a deterministic Thread -> Program association edge.

        Contract:
        - Identity is derived from `(thread_id, program_id)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {
            "thread_id": thread_id,
            "program_id": program_id,
            "key": key,
            "position": position,
            "is_default": is_default,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadProgram):
            return value
        return ThreadProgram.validate_invocation_value(value)


class ThreadProgramCreateInput(BaseModel):
    thread_id: UUID
    program_id: UUID
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)


class ThreadProgramCreateOutput(BaseModel):
    value: ThreadProgram


FUNCTIONS = {
    "ThreadProgram": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Construct a deterministic Thread -> Program association edge.\n\nContract:\n- Identity is derived from `(thread_id, program_id)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": ThreadProgramCreateInput,
            "output": ThreadProgramCreateOutput,
        },
    },
}

__all__ = [
    "ThreadProgram",
    "ThreadProgramCreateInput",
    "ThreadProgramCreateOutput",
    "FUNCTIONS",
]
