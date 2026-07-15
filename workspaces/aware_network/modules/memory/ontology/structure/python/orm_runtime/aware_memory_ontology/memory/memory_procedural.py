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
    from aware_identity_ontology.identity.identity import Identity
    from aware_memory_ontology.memory.memory_procedure import MemoryProcedure


class MemoryProcedural(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)
    procedures: list[MemoryProcedure] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for MemoryProcedural.identity")

    @classmethod
    async def build(cls, identity_id: UUID, key: str = "default") -> MemoryProcedural:
        """
        Create one deterministic procedural-memory lane for an owning Identity.

        Policy:
        - Memory owns the lane object and references Identity relationally.
        - Shared procedural memory is deterministic from Identity plus `key`.
        """

        payload = {"identity_id": identity_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryProcedural):
            return value
        return MemoryProcedural.validate_invocation_value(value)


class MemoryProceduralBuildInput(BaseModel):
    identity_id: UUID
    key: str = Field(default="default")


class MemoryProceduralBuildOutput(BaseModel):
    value: MemoryProcedural


FUNCTIONS = {
    "MemoryProcedural": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic procedural-memory lane for an owning Identity.\n\nPolicy:\n- Memory owns the lane object and references Identity relationally.\n- Shared procedural memory is deterministic from Identity plus `key`.",
                "is_constructor": True,
            },
            "input": MemoryProceduralBuildInput,
            "output": MemoryProceduralBuildOutput,
        },
    },
}

__all__ = [
    "MemoryProcedural",
    "MemoryProceduralBuildInput",
    "MemoryProceduralBuildOutput",
    "FUNCTIONS",
]
