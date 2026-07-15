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
    from aware_content_ontology.part.content_part_content import ContentPartContent
    from aware_content_ontology.part.content_part_content_layout import ContentPartContentLayout


class ContentLayout(ORMModel):
    # Attributes
    background_color: str | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    viewport_height: float | None = Field(default=None)
    viewport_width: float | None = Field(default=None)

    # Foreign Keys
    content_id: UUID = Field(description="Foreign key for Content.content_layouts")

    # Edges
    content_part_content_layouts: list[ContentPartContentLayout] = Field(
        default_factory=list, exclude=True, description="Edge association helper for content_part_contents"
    )

    @property
    def content_part_contents(self) -> list[ContentPartContent]:
        return [
            edge.content_part_content
            for edge in self.content_part_content_layouts
            if edge.content_part_content is not None
        ]

    async def add_part_layout(self, content_part_content_id: UUID, layout_order: int = 0) -> ContentPartContentLayout:
        """Creates placement metadata for an existing content part in this content layout."""

        payload = {"content_part_content_id": content_part_content_id, "layout_order": layout_order}
        result = await invoke_instance(orm_model=self, function_name="add_part_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_content_ontology.part.content_part_content_layout import ContentPartContentLayout

        if isinstance(value, ContentPartContentLayout):
            return value
        return ContentPartContentLayout.validate_invocation_value(value)

    @classmethod
    async def create_content_layout_via_content(
        cls,
        content_id: UUID,
        name: str,
        background_color: str | None = None,
        description: str | None = None,
        viewport_height: float | None = None,
        viewport_width: float | None = None,
    ) -> ContentLayout:
        """Creates a named content layout."""

        payload = {
            "content_id": content_id,
            "name": name,
            "background_color": background_color,
            "description": description,
            "viewport_height": viewport_height,
            "viewport_width": viewport_width,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_layout_via_content", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentLayout):
            return value
        return ContentLayout.validate_invocation_value(value)


class ContentLayoutAddPartLayoutInput(BaseModel):
    content_part_content_id: UUID
    layout_order: int = Field(default=0)


class ContentLayoutAddPartLayoutOutput(BaseModel):
    value: ContentPartContentLayout


class ContentLayoutCreateContentLayoutViaContentInput(BaseModel):
    content_id: UUID = Field(description="Foreign key for Content.content_layouts")
    name: str
    background_color: str | None = Field(default=None)
    description: str | None = Field(default=None)
    viewport_height: float | None = Field(default=None)
    viewport_width: float | None = Field(default=None)


class ContentLayoutCreateContentLayoutViaContentOutput(BaseModel):
    value: ContentLayout


FUNCTIONS = {
    "ContentLayout": {
        "add_part_layout": {
            "canonical": {
                "name": "add_part_layout",
                "description": "Creates placement metadata for an existing content part in this content layout.",
                "is_constructor": False,
            },
            "input": ContentLayoutAddPartLayoutInput,
            "output": ContentLayoutAddPartLayoutOutput,
        },
        "create_content_layout_via_content": {
            "canonical": {
                "name": "create_content_layout_via_content",
                "description": "Creates a named content layout.",
                "is_constructor": True,
            },
            "input": ContentLayoutCreateContentLayoutViaContentInput,
            "output": ContentLayoutCreateContentLayoutViaContentOutput,
        },
    },
}

__all__ = [
    "ContentLayout",
    "ContentLayoutAddPartLayoutInput",
    "ContentLayoutAddPartLayoutOutput",
    "ContentLayoutCreateContentLayoutViaContentInput",
    "ContentLayoutCreateContentLayoutViaContentOutput",
    "FUNCTIONS",
]
