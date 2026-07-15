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


class ContentIndex(ORMModel):
    # Attributes
    key: str = Field(default="default")
    content_embedding: Vector | None = Field(default=None)

    # Foreign Keys
    content_id: UUID | None = Field(default=None, description="Foreign key for Content.content_index")

    @classmethod
    async def create_content_index_via_content(
        cls, content_id: UUID, key: str = "default", content_embedding: Vector | None = None
    ) -> ContentIndex:
        """Creates a content-level embedding/index record."""

        payload = {"content_id": content_id, "key": key, "content_embedding": content_embedding}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_index_via_content", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentIndex):
            return value
        return ContentIndex.validate_invocation_value(value)


class ContentIndexCreateContentIndexViaContentInput(BaseModel):
    content_id: UUID = Field(description="Foreign key for Content.content_index")
    key: str = Field(default="default")
    content_embedding: Vector | None = Field(default=None)


class ContentIndexCreateContentIndexViaContentOutput(BaseModel):
    value: ContentIndex


FUNCTIONS = {
    "ContentIndex": {
        "create_content_index_via_content": {
            "canonical": {
                "name": "create_content_index_via_content",
                "description": "Creates a content-level embedding/index record.",
                "is_constructor": True,
            },
            "input": ContentIndexCreateContentIndexViaContentInput,
            "output": ContentIndexCreateContentIndexViaContentOutput,
        },
    },
}

__all__ = [
    "ContentIndex",
    "ContentIndexCreateContentIndexViaContentInput",
    "ContentIndexCreateContentIndexViaContentOutput",
    "FUNCTIONS",
]
