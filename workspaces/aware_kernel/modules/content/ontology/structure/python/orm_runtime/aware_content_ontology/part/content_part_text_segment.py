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
    from aware_content_ontology.part.content_part_text import ContentPartText
    from aware_content_ontology.part.content_part_text_segment_translation import ContentPartTextSegmentTranslation
    from aware_content_ontology.part.content_part_text_style import ContentPartTextStyle


class ContentPartTextSegment(ORMModel):
    # Relationships
    content_part_text_segment_translations: list[ContentPartTextSegmentTranslation] = Field(
        default_factory=list, exclude=True
    )
    parent: ContentPartTextSegment | None = Field(default=None, exclude=True)
    style: ContentPartTextStyle | None = Field(default=None, exclude=True)
    content_part_text: ContentPartText = Field(description="Reverse view for ContentPartText.segments")

    # Attributes
    key: str = Field(default="default")
    byte_end: int | None = Field(default=None)
    byte_start: int | None = Field(default=None)

    # Foreign Keys
    content_part_text_id: UUID | None = Field(default=None, description="Foreign key for ContentPartText.segments")
    parent_id: UUID | None = Field(default=None, description="Foreign key for ContentPartTextSegment.parent")

    async def update_segment(
        self,
        content_part_text_id: UUID,
        byte_start: int | None = None,
        byte_end: int | None = None,
        style_id: UUID | None = None,
        parent_id: UUID | None = None,
    ) -> None:
        """
        Updates an existing segment (v1).

        Contract:
        - `content_part_text_id` remains required.
        - `byte_start`/`byte_end` are UTF-8 byte offsets into the attached text's `inline_text`.
        """

        payload = {
            "content_part_text_id": content_part_text_id,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "style_id": style_id,
            "parent_id": parent_id,
        }
        await invoke_instance(orm_model=self, function_name="update_segment", payload=payload)
        return None

    async def delete_segment(self) -> None:
        """Deletes this segment explicitly from the lane."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete_segment", payload=payload)
        return None

    async def add_translation(self, language: str, text: str) -> ContentPartTextSegmentTranslation:
        """Adds a translated value for this segment."""

        payload = {"language": language, "text": text}
        result = await invoke_instance(orm_model=self, function_name="add_translation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.part.content_part_text_segment_translation import ContentPartTextSegmentTranslation

        if isinstance(value, ContentPartTextSegmentTranslation):
            return value
        return ContentPartTextSegmentTranslation.validate_invocation_value(value)

    async def apply_style(
        self,
        font_family: str | None = None,
        font_size: int | None = None,
        bold: bool | None = False,
        italic: bool | None = False,
        underline: bool | None = False,
        color: str | None = None,
        background_color: str | None = None,
        block_semantic_type: str | None = None,
    ) -> ContentPartTextStyle:
        """Creates or reuses a style for this segment."""

        payload = {
            "font_family": font_family,
            "font_size": font_size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "color": color,
            "background_color": background_color,
            "block_semantic_type": block_semantic_type,
        }
        result = await invoke_instance(orm_model=self, function_name="apply_style", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.part.content_part_text_style import ContentPartTextStyle

        if isinstance(value, ContentPartTextStyle):
            return value
        return ContentPartTextStyle.validate_invocation_value(value)

    @classmethod
    async def upsert_via_content_part_text(
        cls,
        content_part_text_id: UUID,
        segment_id: UUID | None = None,
        key: str = "default",
        byte_start: int | None = None,
        byte_end: int | None = None,
        style_id: UUID | None = None,
        parent_id: UUID | None = None,
    ) -> ContentPartTextSegment:
        """
        Creates a text segment with a deterministic id.

        Contract:
        - `content_part_text_id` is required for new segments.
        - `byte_start`/`byte_end` are UTF-8 byte offsets into the target text's `inline_text`.
        - `style_id` references a `ContentPartTextStyle` (caller may create-or-get styles separately).
        """

        payload = {
            "content_part_text_id": content_part_text_id,
            "segment_id": segment_id,
            "key": key,
            "byte_start": byte_start,
            "byte_end": byte_end,
            "style_id": style_id,
            "parent_id": parent_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="upsert_via_content_part_text", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartTextSegment):
            return value
        return ContentPartTextSegment.validate_invocation_value(value)


class ContentPartTextSegmentUpdateSegmentInput(BaseModel):
    content_part_text_id: UUID
    byte_start: int | None = Field(default=None)
    byte_end: int | None = Field(default=None)
    style_id: UUID | None = Field(default=None)
    parent_id: UUID | None = Field(default=None)


class ContentPartTextSegmentUpdateSegmentOutput(BaseModel):
    pass


class ContentPartTextSegmentDeleteSegmentInput(BaseModel):
    pass


class ContentPartTextSegmentDeleteSegmentOutput(BaseModel):
    pass


class ContentPartTextSegmentAddTranslationInput(BaseModel):
    language: str
    text: str


class ContentPartTextSegmentAddTranslationOutput(BaseModel):
    value: ContentPartTextSegmentTranslation


class ContentPartTextSegmentApplyStyleInput(BaseModel):
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=None)
    bold: bool | None = Field(default=False)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)


class ContentPartTextSegmentApplyStyleOutput(BaseModel):
    value: ContentPartTextStyle


class ContentPartTextSegmentUpsertViaContentPartTextInput(BaseModel):
    content_part_text_id: UUID = Field(description="Foreign key for ContentPartText.segments")
    segment_id: UUID | None = Field(default=None)
    key: str = Field(default="default")
    byte_start: int | None = Field(default=None)
    byte_end: int | None = Field(default=None)
    style_id: UUID | None = Field(default=None)
    parent_id: UUID | None = Field(default=None)


class ContentPartTextSegmentUpsertViaContentPartTextOutput(BaseModel):
    value: ContentPartTextSegment


FUNCTIONS = {
    "ContentPartTextSegment": {
        "update_segment": {
            "canonical": {
                "name": "update_segment",
                "description": "Updates an existing segment (v1).\n\nContract:\n- `content_part_text_id` remains required.\n- `byte_start`/`byte_end` are UTF-8 byte offsets into the attached text's `inline_text`.",
                "is_constructor": False,
            },
            "input": ContentPartTextSegmentUpdateSegmentInput,
            "output": ContentPartTextSegmentUpdateSegmentOutput,
        },
        "delete_segment": {
            "canonical": {
                "name": "delete_segment",
                "description": "Deletes this segment explicitly from the lane.",
                "is_constructor": False,
            },
            "input": ContentPartTextSegmentDeleteSegmentInput,
            "output": ContentPartTextSegmentDeleteSegmentOutput,
        },
        "add_translation": {
            "canonical": {
                "name": "add_translation",
                "description": "Adds a translated value for this segment.",
                "is_constructor": False,
            },
            "input": ContentPartTextSegmentAddTranslationInput,
            "output": ContentPartTextSegmentAddTranslationOutput,
        },
        "apply_style": {
            "canonical": {
                "name": "apply_style",
                "description": "Creates or reuses a style for this segment.",
                "is_constructor": False,
            },
            "input": ContentPartTextSegmentApplyStyleInput,
            "output": ContentPartTextSegmentApplyStyleOutput,
        },
        "upsert_via_content_part_text": {
            "canonical": {
                "name": "upsert_via_content_part_text",
                "description": "Creates a text segment with a deterministic id.\n\nContract:\n- `content_part_text_id` is required for new segments.\n- `byte_start`/`byte_end` are UTF-8 byte offsets into the target text's `inline_text`.\n- `style_id` references a `ContentPartTextStyle` (caller may create-or-get styles separately).",
                "is_constructor": True,
            },
            "input": ContentPartTextSegmentUpsertViaContentPartTextInput,
            "output": ContentPartTextSegmentUpsertViaContentPartTextOutput,
        },
    },
}

__all__ = [
    "ContentPartTextSegment",
    "ContentPartTextSegmentUpdateSegmentInput",
    "ContentPartTextSegmentUpdateSegmentOutput",
    "ContentPartTextSegmentDeleteSegmentInput",
    "ContentPartTextSegmentDeleteSegmentOutput",
    "ContentPartTextSegmentAddTranslationInput",
    "ContentPartTextSegmentAddTranslationOutput",
    "ContentPartTextSegmentApplyStyleInput",
    "ContentPartTextSegmentApplyStyleOutput",
    "ContentPartTextSegmentUpsertViaContentPartTextInput",
    "ContentPartTextSegmentUpsertViaContentPartTextOutput",
    "FUNCTIONS",
]
