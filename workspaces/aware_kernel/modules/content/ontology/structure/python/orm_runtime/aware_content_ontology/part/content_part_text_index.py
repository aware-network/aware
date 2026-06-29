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

# Types
from aware_types import Vector


class ContentPartTextIndex(ORMModel):
    # Attributes
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)

    # Foreign Keys
    content_part_text_id: UUID | None = Field(default=None, description="Foreign key for ContentPartText.index")

    @classmethod
    async def create_content_part_text_index_via_content_part_text(
        cls, content_part_text_id: UUID, key: str = "default", embedding: Vector | None = None
    ) -> ContentPartTextIndex:
        """Creates a text-part embedding/index record."""

        payload = {"content_part_text_id": content_part_text_id, "key": key, "embedding": embedding}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_text_index_via_content_part_text", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartTextIndex):
            return value
        return ContentPartTextIndex.validate_invocation_value(value)


class ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextInput(BaseModel):
    content_part_text_id: UUID = Field(description="Foreign key for ContentPartText.index")
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)


class ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextOutput(BaseModel):
    value: ContentPartTextIndex


FUNCTIONS = {
    "ContentPartTextIndex": {
        "create_content_part_text_index_via_content_part_text": {
            "canonical": {
                "name": "create_content_part_text_index_via_content_part_text",
                "description": "Creates a text-part embedding/index record.",
                "is_constructor": True,
            },
            "input": ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextInput,
            "output": ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextOutput,
        },
    },
}

__all__ = [
    "ContentPartTextIndex",
    "ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextInput",
    "ContentPartTextIndexCreateContentPartTextIndexViaContentPartTextOutput",
    "FUNCTIONS",
]
