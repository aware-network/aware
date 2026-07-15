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


class ContentPartMultimodalIndex(ORMModel):
    # Attributes
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)

    # Foreign Keys
    content_part_id: UUID | None = Field(
        default=None, description="Foreign key for ContentPart.content_part_multimodal_index"
    )

    @classmethod
    async def create_content_part_multimodal_index_via_content_part(
        cls, content_part_id: UUID, key: str = "default", embedding: Vector | None = None
    ) -> ContentPartMultimodalIndex:
        """Creates a multimodal content-part embedding/index record."""

        payload = {"content_part_id": content_part_id, "key": key, "embedding": embedding}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_multimodal_index_via_content_part", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartMultimodalIndex):
            return value
        return ContentPartMultimodalIndex.validate_invocation_value(value)


class ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartInput(BaseModel):
    content_part_id: UUID = Field(description="Foreign key for ContentPart.content_part_multimodal_index")
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)


class ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartOutput(BaseModel):
    value: ContentPartMultimodalIndex


FUNCTIONS = {
    "ContentPartMultimodalIndex": {
        "create_content_part_multimodal_index_via_content_part": {
            "canonical": {
                "name": "create_content_part_multimodal_index_via_content_part",
                "description": "Creates a multimodal content-part embedding/index record.",
                "is_constructor": True,
            },
            "input": ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartInput,
            "output": ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartOutput,
        },
    },
}

__all__ = [
    "ContentPartMultimodalIndex",
    "ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartInput",
    "ContentPartMultimodalIndexCreateContentPartMultimodalIndexViaContentPartOutput",
    "FUNCTIONS",
]
