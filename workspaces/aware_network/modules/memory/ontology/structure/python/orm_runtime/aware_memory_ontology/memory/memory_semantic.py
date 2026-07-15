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


class MemorySemantic(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for MemorySemantic.identity")

    @classmethod
    async def build(cls, identity_id: UUID, key: str = "default") -> MemorySemantic:
        """
        Create one deterministic semantic-memory lane for an owning Identity.

        Policy:
        - Memory owns the lane object and references Identity relationally.
        - Shared semantic memory is deterministic from Identity plus `key`.
        """

        payload = {"identity_id": identity_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemorySemantic):
            return value
        return MemorySemantic.validate_invocation_value(value)


class MemorySemanticBuildInput(BaseModel):
    identity_id: UUID
    key: str = Field(default="default")


class MemorySemanticBuildOutput(BaseModel):
    value: MemorySemantic


FUNCTIONS = {
    "MemorySemantic": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic semantic-memory lane for an owning Identity.\n\nPolicy:\n- Memory owns the lane object and references Identity relationally.\n- Shared semantic memory is deterministic from Identity plus `key`.",
                "is_constructor": True,
            },
            "input": MemorySemanticBuildInput,
            "output": MemorySemanticBuildOutput,
        },
    },
}

__all__ = [
    "MemorySemantic",
    "MemorySemanticBuildInput",
    "MemorySemanticBuildOutput",
    "FUNCTIONS",
]
