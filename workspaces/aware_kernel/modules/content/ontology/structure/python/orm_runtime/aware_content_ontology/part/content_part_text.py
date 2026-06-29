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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_text_editor_patch import ContentPartTextEditorPatch
    from aware_content_ontology.part.content_part_text_index import ContentPartTextIndex
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ContentPartText(ORMModel):
    # Relationships
    blob: StorageBlob | None = Field(default=None, exclude=True)
    index: ContentPartTextIndex | None = Field(default=None, exclude=True)
    segments: list[ContentPartTextSegment] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str = Field(default="default")
    inline_text: str | None = Field(default=None)

    # Foreign Keys
    content_part_id: UUID | None = Field(default=None, description="Foreign key for ContentPart.content_part_text")
    blob_id: UUID | None = Field(default=None, description="Foreign key for ContentPartText.blob")

    async def set_inline_text(self, inline_text: str) -> None:
        """Updates the inline_text for this ContentPartText (v0 editor persistence)."""

        payload = {"inline_text": inline_text}
        await invoke_instance(orm_model=self, function_name="set_inline_text", payload=payload)
        return None

    async def apply_editor_patch(self, patch: ContentPartTextEditorPatch) -> None:
        """
        Applies a canonical editor patch (v1).

        Contract:
        - `patch.text_after` or `patch.text_patches` update `inline_text`.
        - `patch.segment_ops` upserts/deletes `ContentPartTextSegment` objects.
        - Segment `byte_*` ranges are UTF-8 byte offsets into `inline_text`.
        """

        payload = {"patch": patch}
        await invoke_instance(orm_model=self, function_name="apply_editor_patch", payload=payload)
        return None

    async def delete(self) -> None:
        """Deletes this text content part and all owned segments."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    async def add_segment(
        self, segment_key: str = "default", byte_start: int | None = None, byte_end: int | None = None
    ) -> ContentPartTextSegment:
        """Adds a segment under this text content part."""

        payload = {"segment_key": segment_key, "byte_start": byte_start, "byte_end": byte_end}
        result = await invoke_instance(orm_model=self, function_name="add_segment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

        if isinstance(value, ContentPartTextSegment):
            return value
        return ContentPartTextSegment.validate_invocation_value(value)

    @classmethod
    async def create_content_part_text_via_content_part(
        cls, content_part_id: UUID, key: str = "default", inline_text: str | None = None
    ) -> ContentPartText:
        """Creates a new text content part container."""

        payload = {"content_part_id": content_part_id, "key": key, "inline_text": inline_text}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_text_via_content_part", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartText):
            return value
        return ContentPartText.validate_invocation_value(value)


class ContentPartTextSetInlineTextInput(BaseModel):
    inline_text: str


class ContentPartTextSetInlineTextOutput(BaseModel):
    pass


class ContentPartTextApplyEditorPatchInput(BaseModel):
    patch: ContentPartTextEditorPatch


class ContentPartTextApplyEditorPatchOutput(BaseModel):
    pass


class ContentPartTextDeleteInput(BaseModel):
    pass


class ContentPartTextDeleteOutput(BaseModel):
    pass


class ContentPartTextAddSegmentInput(BaseModel):
    segment_key: str = Field(default="default")
    byte_start: int | None = Field(default=None)
    byte_end: int | None = Field(default=None)


class ContentPartTextAddSegmentOutput(BaseModel):
    value: ContentPartTextSegment


class ContentPartTextCreateContentPartTextViaContentPartInput(BaseModel):
    content_part_id: UUID = Field(description="Foreign key for ContentPart.content_part_text")
    key: str = Field(default="default")
    inline_text: str | None = Field(default=None)


class ContentPartTextCreateContentPartTextViaContentPartOutput(BaseModel):
    value: ContentPartText


FUNCTIONS = {
    "ContentPartText": {
        "set_inline_text": {
            "canonical": {
                "name": "set_inline_text",
                "description": "Updates the inline_text for this ContentPartText (v0 editor persistence).",
                "is_constructor": False,
            },
            "input": ContentPartTextSetInlineTextInput,
            "output": ContentPartTextSetInlineTextOutput,
        },
        "apply_editor_patch": {
            "canonical": {
                "name": "apply_editor_patch",
                "description": "Applies a canonical editor patch (v1).\n\nContract:\n- `patch.text_after` or `patch.text_patches` update `inline_text`.\n- `patch.segment_ops` upserts/deletes `ContentPartTextSegment` objects.\n- Segment `byte_*` ranges are UTF-8 byte offsets into `inline_text`.",
                "is_constructor": False,
            },
            "input": ContentPartTextApplyEditorPatchInput,
            "output": ContentPartTextApplyEditorPatchOutput,
        },
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Deletes this text content part and all owned segments.",
                "is_constructor": False,
            },
            "input": ContentPartTextDeleteInput,
            "output": ContentPartTextDeleteOutput,
        },
        "add_segment": {
            "canonical": {
                "name": "add_segment",
                "description": "Adds a segment under this text content part.",
                "is_constructor": False,
            },
            "input": ContentPartTextAddSegmentInput,
            "output": ContentPartTextAddSegmentOutput,
        },
        "create_content_part_text_via_content_part": {
            "canonical": {
                "name": "create_content_part_text_via_content_part",
                "description": "Creates a new text content part container.",
                "is_constructor": True,
            },
            "input": ContentPartTextCreateContentPartTextViaContentPartInput,
            "output": ContentPartTextCreateContentPartTextViaContentPartOutput,
        },
    },
}

__all__ = [
    "ContentPartText",
    "ContentPartTextSetInlineTextInput",
    "ContentPartTextSetInlineTextOutput",
    "ContentPartTextApplyEditorPatchInput",
    "ContentPartTextApplyEditorPatchOutput",
    "ContentPartTextDeleteInput",
    "ContentPartTextDeleteOutput",
    "ContentPartTextAddSegmentInput",
    "ContentPartTextAddSegmentOutput",
    "ContentPartTextCreateContentPartTextViaContentPartInput",
    "ContentPartTextCreateContentPartTextViaContentPartOutput",
    "FUNCTIONS",
]
