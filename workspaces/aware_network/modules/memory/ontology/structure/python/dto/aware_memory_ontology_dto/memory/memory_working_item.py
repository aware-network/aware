from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Memory Ontology Dto
from aware_memory_ontology_dto.memory.memory_working_item_enums import MemoryWorkingItemKind

if TYPE_CHECKING:
    from aware_attention_ontology_dto.session.attention_focus_transition import AttentionFocusTransition
    from aware_memory_ontology_dto.memory.memory_working_content_frame import MemoryWorkingContentFrame
    from aware_memory_ontology_dto.memory.memory_working_event_frame import MemoryWorkingEventFrame
    from aware_memory_ontology_dto.memory.memory_working_tool_frame import MemoryWorkingToolFrame


class MemoryWorkingItem(BaseModel):
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
    event_frame: MemoryWorkingEventFrame | None = Field(default=None)
    content_frame: MemoryWorkingContentFrame | None = Field(default=None)
    tool_frame: MemoryWorkingToolFrame | None = Field(default=None)
    attention_transition: AttentionFocusTransition | None = Field(default=None)

    # Attributes
    kind: MemoryWorkingItemKind
    position: int
    created_at: datetime
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)
