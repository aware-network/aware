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
from aware_orm.runtime.invocation import invoke_constructor


class ContentPartTextSegmentTranslation(ORMModel):
    # Attributes
    language: str
    text: str

    # Foreign Keys
    content_part_text_segment_id: UUID = Field(
        description="Foreign key for ContentPartTextSegment.content_part_text_segment_translations"
    )

    @classmethod
    async def create_translation_via_content_part_text_segment(
        cls, content_part_text_segment_id: UUID, language: str, text: str
    ) -> ContentPartTextSegmentTranslation:
        """Creates a translated text segment value."""

        payload = {"content_part_text_segment_id": content_part_text_segment_id, "language": language, "text": text}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_translation_via_content_part_text_segment", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartTextSegmentTranslation):
            return value
        return ContentPartTextSegmentTranslation.validate_invocation_value(value)


class ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentInput(BaseModel):
    content_part_text_segment_id: UUID = Field(
        description="Foreign key for ContentPartTextSegment.content_part_text_segment_translations"
    )
    language: str
    text: str


class ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentOutput(BaseModel):
    value: ContentPartTextSegmentTranslation


FUNCTIONS = {
    "ContentPartTextSegmentTranslation": {
        "create_translation_via_content_part_text_segment": {
            "canonical": {
                "name": "create_translation_via_content_part_text_segment",
                "description": "Creates a translated text segment value.",
                "is_constructor": True,
            },
            "input": ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentInput,
            "output": ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentOutput,
        },
    },
}

__all__ = [
    "ContentPartTextSegmentTranslation",
    "ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentInput",
    "ContentPartTextSegmentTranslationCreateTranslationViaContentPartTextSegmentOutput",
    "FUNCTIONS",
]
