from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology
from aware_content_ontology.part.content_part_enums import ContentPartType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part import ContentPart


class ContentPartContent(ORMModel):
    # Relationships
    content_part: ContentPart

    # Attributes
    position: int

    # Foreign Keys
    content_id: UUID = Field(description="Foreign key for Content.content_part_contents")

    @classmethod
    async def create_content_part_content(
        cls,
        content_id: UUID,
        content_part_id: UUID,
        position: int,
        child_part_type: ContentPartType = ContentPartType.text,
    ) -> ContentPartContent:
        """Creates a new ContentPartContent edge linking a Content to a ContentPart."""

        payload = {
            "content_id": content_id,
            "content_part_id": content_part_id,
            "position": position,
            "child_part_type": child_part_type,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_content_part_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartContent):
            return value
        return ContentPartContent.validate_invocation_value(value)

    @classmethod
    async def create_text_part_content_via_content(
        cls,
        content_id: UUID,
        position: int = 0,
        seed_inline_text: str | None = None,
        child_part_type: ContentPartType = ContentPartType.text,
    ) -> ContentPartContent:
        """Creates a ContentPartContent edge with a text ContentPart child."""

        payload = {
            "content_id": content_id,
            "position": position,
            "seed_inline_text": seed_inline_text,
            "child_part_type": child_part_type,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_text_part_content_via_content", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartContent):
            return value
        return ContentPartContent.validate_invocation_value(value)


class ContentPartContentCreateContentPartContentInput(BaseModel):
    content_id: UUID
    content_part_id: UUID
    position: int
    child_part_type: ContentPartType = Field(default=ContentPartType.text)


class ContentPartContentCreateContentPartContentOutput(BaseModel):
    value: ContentPartContent


class ContentPartContentCreateTextPartContentViaContentInput(BaseModel):
    content_id: UUID = Field(description="Foreign key for Content.content_part_contents")
    position: int = Field(default=0)
    seed_inline_text: str | None = Field(default=None)
    child_part_type: ContentPartType = Field(default=ContentPartType.text)


class ContentPartContentCreateTextPartContentViaContentOutput(BaseModel):
    value: ContentPartContent


FUNCTIONS = {
    "ContentPartContent": {
        "create_content_part_content": {
            "canonical": {
                "name": "create_content_part_content",
                "description": "Creates a new ContentPartContent edge linking a Content to a ContentPart.",
                "is_constructor": True,
            },
            "input": ContentPartContentCreateContentPartContentInput,
            "output": ContentPartContentCreateContentPartContentOutput,
        },
        "create_text_part_content_via_content": {
            "canonical": {
                "name": "create_text_part_content_via_content",
                "description": "Creates a ContentPartContent edge with a text ContentPart child.",
                "is_constructor": True,
            },
            "input": ContentPartContentCreateTextPartContentViaContentInput,
            "output": ContentPartContentCreateTextPartContentViaContentOutput,
        },
    },
}

__all__ = [
    "ContentPartContent",
    "ContentPartContentCreateContentPartContentInput",
    "ContentPartContentCreateContentPartContentOutput",
    "ContentPartContentCreateTextPartContentViaContentInput",
    "ContentPartContentCreateTextPartContentViaContentOutput",
    "FUNCTIONS",
]
