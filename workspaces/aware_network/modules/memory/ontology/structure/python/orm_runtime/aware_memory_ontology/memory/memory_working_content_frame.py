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
    from aware_content_ontology.content.content import Content


class MemoryWorkingContentFrame(ORMModel):
    """
    Content payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=content`.
    - Content remains multimodal-ready via aware_content.
    """

    # Relationships
    content: Content | None = Field(default=None, exclude=True)

    # Foreign Keys
    memory_working_item_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.content_frame"
    )
    content_id: UUID = Field(description="Foreign key for MemoryWorkingContentFrame.content")

    @classmethod
    async def build_via_memory_working_item(
        cls, memory_working_item_id: UUID, content_id: UUID
    ) -> MemoryWorkingContentFrame:
        """Builds deterministic content frame payload for a memory item."""

        payload = {"memory_working_item_id": memory_working_item_id, "content_id": content_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_memory_working_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorkingContentFrame):
            return value
        return MemoryWorkingContentFrame.validate_invocation_value(value)


class MemoryWorkingContentFrameBuildViaMemoryWorkingItemInput(BaseModel):
    memory_working_item_id: UUID = Field(description="Foreign key for MemoryWorkingItem.content_frame")
    content_id: UUID


class MemoryWorkingContentFrameBuildViaMemoryWorkingItemOutput(BaseModel):
    value: MemoryWorkingContentFrame


FUNCTIONS = {
    "MemoryWorkingContentFrame": {
        "build_via_memory_working_item": {
            "canonical": {
                "name": "build_via_memory_working_item",
                "description": "Builds deterministic content frame payload for a memory item.",
                "is_constructor": True,
            },
            "input": MemoryWorkingContentFrameBuildViaMemoryWorkingItemInput,
            "output": MemoryWorkingContentFrameBuildViaMemoryWorkingItemOutput,
        },
    },
}

__all__ = [
    "MemoryWorkingContentFrame",
    "MemoryWorkingContentFrameBuildViaMemoryWorkingItemInput",
    "MemoryWorkingContentFrameBuildViaMemoryWorkingItemOutput",
    "FUNCTIONS",
]
