from __future__ import annotations

# Standard
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


class ContentPartTextStyle(ORMModel):
    # Attributes
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)
    bold: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=0)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)

    # Foreign Keys
    content_part_text_segment_id: UUID | None = Field(
        default=None, description="Foreign key for ContentPartTextSegment.style"
    )

    async def delete_if_unreferenced(self) -> None:
        """Deletes this text style when no text segment in the current lane references it."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete_if_unreferenced", payload=payload)
        return None

    @classmethod
    async def create_or_get_style_via_content_part_text_segment(
        cls,
        content_part_text_segment_id: UUID,
        font_family: str | None = None,
        font_size: int | None = None,
        bold: bool | None = False,
        italic: bool | None = False,
        underline: bool | None = False,
        color: str | None = None,
        background_color: str | None = None,
        block_semantic_type: str | None = None,
    ) -> ContentPartTextStyle:
        """
        Creates or retrieves a text style.
        Parameters: font_family: The font family.
        font_size: The font size.
        bold: Whether the text is bold.
        italic: Whether the text is italic.
        underline: Whether the text is underlined.
        color: The text color.
        background_color: The background color.
        block_semantic_type: Optional block semantic type tag (e.g. header/list/task/table).
        """

        payload = {
            "content_part_text_segment_id": content_part_text_segment_id,
            "font_family": font_family,
            "font_size": font_size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "color": color,
            "background_color": background_color,
            "block_semantic_type": block_semantic_type,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_or_get_style_via_content_part_text_segment", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartTextStyle):
            return value
        return ContentPartTextStyle.validate_invocation_value(value)


class ContentPartTextStyleDeleteIfUnreferencedInput(BaseModel):
    pass


class ContentPartTextStyleDeleteIfUnreferencedOutput(BaseModel):
    pass


class ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentInput(BaseModel):
    content_part_text_segment_id: UUID = Field(description="Foreign key for ContentPartTextSegment.style")
    font_family: str | None = Field(default=None)
    font_size: int | None = Field(default=None)
    bold: bool | None = Field(default=False)
    italic: bool | None = Field(default=False)
    underline: bool | None = Field(default=False)
    color: str | None = Field(default=None)
    background_color: str | None = Field(default=None)
    block_semantic_type: str | None = Field(default=None)


class ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentOutput(BaseModel):
    value: ContentPartTextStyle


FUNCTIONS = {
    "ContentPartTextStyle": {
        "delete_if_unreferenced": {
            "canonical": {
                "name": "delete_if_unreferenced",
                "description": "Deletes this text style when no text segment in the current lane references it.",
                "is_constructor": False,
            },
            "input": ContentPartTextStyleDeleteIfUnreferencedInput,
            "output": ContentPartTextStyleDeleteIfUnreferencedOutput,
        },
        "create_or_get_style_via_content_part_text_segment": {
            "canonical": {
                "name": "create_or_get_style_via_content_part_text_segment",
                "description": "Creates or retrieves a text style.\nParameters: font_family: The font family.\nfont_size: The font size.\nbold: Whether the text is bold.\nitalic: Whether the text is italic.\nunderline: Whether the text is underlined.\ncolor: The text color.\nbackground_color: The background color.\nblock_semantic_type: Optional block semantic type tag (e.g. header/list/task/table).",
                "is_constructor": True,
            },
            "input": ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentInput,
            "output": ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentOutput,
        },
    },
}

__all__ = [
    "ContentPartTextStyle",
    "ContentPartTextStyleDeleteIfUnreferencedInput",
    "ContentPartTextStyleDeleteIfUnreferencedOutput",
    "ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentInput",
    "ContentPartTextStyleCreateOrGetStyleViaContentPartTextSegmentOutput",
    "FUNCTIONS",
]
