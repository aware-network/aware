from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Memory Ontology Orm Models
from aware_memory_ontology_orm_models.memory.memory_working_item_enums import MemoryWorkingItemKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.session.attention_focus_transition import AttentionFocusTransition
    from aware_memory_ontology_orm_models.memory.memory_working_content_frame import MemoryWorkingContentFrame
    from aware_memory_ontology_orm_models.memory.memory_working_event_frame import MemoryWorkingEventFrame
    from aware_memory_ontology_orm_models.memory.memory_working_tool_frame import MemoryWorkingToolFrame


class MemoryWorkingItem(ORMModel):
    """
    Typed working-memory item for attention-first actor context.
    Contract:
    - One item captures one canonical dynamic axis:
    `event`, `content`, `tool`, or `attention`.
    - `MemoryWorking` owns item ordering (`position`).
    - Attention items point at Attention-owned transition source truth.
    Memory must not duplicate focus/layout/view envelopes.
    """

    # Relationships
    event_frame: MemoryWorkingEventFrame | None = Field(default=None, exclude=True)
    content_frame: MemoryWorkingContentFrame | None = Field(default=None, exclude=True)
    tool_frame: MemoryWorkingToolFrame | None = Field(default=None, exclude=True)
    attention_transition: AttentionFocusTransition | None = Field(default=None, exclude=True)

    # Attributes
    kind: MemoryWorkingItemKind
    position: int
    created_at: datetime
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)

    # Foreign Keys
    memory_working_id: UUID = Field(description="Foreign key for MemoryWorking.items")
    attention_transition_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.attention_transition"
    )
