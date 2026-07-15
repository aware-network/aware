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
    from aware_attention_ontology.layout.layout import Layout


class ThreadLayout(ORMModel):
    """
    Deterministic Thread -> Attention Layout association edge.
    Contract:
    - Canonical portal from environment thread context to attention layout topology.
    - Thread remains narrative/layout-management context; attention owns section/focus truth.
    """

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None, description="Stable association key under a Thread for layout attachments.")

    # Foreign Keys
    thread_id: UUID = Field(description="Foreign key for Thread.thread_layouts")
    layout_id: UUID = Field(description="Foreign key for ThreadLayout.layout")

    @classmethod
    async def create_via_thread(cls, thread_id: UUID, layout_id: UUID, key: str | None = None) -> ThreadLayout:
        """
        Create a deterministic ThreadLayout association edge.

        Contract:
        - Identity is derived from propagated parent Thread context (`_via_thread_layouts`) + `layout_id`.
        - Idempotent for repeated calls with the same parent/layout pair.
        """

        payload = {"thread_id": thread_id, "layout_id": layout_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_thread", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadLayout):
            return value
        return ThreadLayout.validate_invocation_value(value)


class ThreadLayoutCreateViaThreadInput(BaseModel):
    thread_id: UUID = Field(description="Foreign key for Thread.thread_layouts")
    layout_id: UUID
    key: str | None = Field(default=None)


class ThreadLayoutCreateViaThreadOutput(BaseModel):
    value: ThreadLayout


FUNCTIONS = {
    "ThreadLayout": {
        "create_via_thread": {
            "canonical": {
                "name": "create_via_thread",
                "description": "Create a deterministic ThreadLayout association edge.\n\nContract:\n- Identity is derived from propagated parent Thread context (`_via_thread_layouts`) + `layout_id`.\n- Idempotent for repeated calls with the same parent/layout pair.",
                "is_constructor": True,
            },
            "input": ThreadLayoutCreateViaThreadInput,
            "output": ThreadLayoutCreateViaThreadOutput,
        },
    },
}

__all__ = [
    "ThreadLayout",
    "ThreadLayoutCreateViaThreadInput",
    "ThreadLayoutCreateViaThreadOutput",
    "FUNCTIONS",
]
