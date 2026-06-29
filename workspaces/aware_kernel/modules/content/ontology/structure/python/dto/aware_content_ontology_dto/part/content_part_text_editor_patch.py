from __future__ import annotations

# Standard
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class ContentTextPatchOp(Enum):
    """
    Canonical Content editor patch payloads (inline values).
    Contract:
    - Operation-driven: no full before/after graph snapshots.
    - Inline values only: not graph entities (no ids/reachability).
    - Intended to be applied by `ContentPartText.apply_editor_patch(...)`.
    """

    insert = "insert"
    delete = "delete"
    replace = "replace"


class ContentTextPatch(BaseModel):
    """
    Byte-level text patch operation (aligned with meta attribute delta semantics).
    Notes:
    - `pos` and `len` are UTF-8 byte offsets/lengths.
    - `text` is a UTF-8 string that will be inserted/replaced at `pos`.
    """

    # Attributes
    op: ContentTextPatchOp
    pos: int
    len: int | None = Field(default=None)
    text: str | None = Field(default=None)


class ContentPartTextStyleSpec(BaseModel):
    """
    Style spec (inline) used by content editor patches.
    Mirrors `ContentPartTextStyle` attributes.
    """

    # Attributes
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)
    bold: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=None)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)


class ContentPartTextSegmentUpsert(BaseModel):
    """Segment upsert operation (byte ranges + style)."""

    # Attributes
    segment_id: UUID
    byte_start: int
    byte_end: int
    parent_id: UUID | None = Field(default=None)
    style: ContentPartTextStyleSpec | None = Field(default=None)


class ContentPartTextSegmentDetach(BaseModel):
    """Segment detach operation (deletes the segment)."""

    # Attributes
    segment_id: UUID


class ContentPartTextSegmentOp(BaseModel):
    """Segment operation union."""

    # Attributes
    upsert: ContentPartTextSegmentUpsert | None = Field(default=None)
    detach: ContentPartTextSegmentDetach | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.upsert,
                    self.detach,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of upsert, detach must be set")
        return self


class ContentPartTextEditorPatch(BaseModel):
    """Patch for ContentPartText editor persistence (v1)."""

    # Attributes
    schema_version: int = Field(default=1)
    text_after: str | None = Field(default=None)
    text_patches: list[ContentTextPatch] = Field(default_factory=list)
    segment_ops: list[ContentPartTextSegmentOp] = Field(default_factory=list)
