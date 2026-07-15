from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology
from aware_content_ontology.content.content_enums import ContentSource

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.content.content_index import ContentIndex
    from aware_content_ontology.content.content_layout import ContentLayout
    from aware_content_ontology.part.content_part_content import ContentPartContent


class Content(ORMModel):
    # Relationships
    content_index: ContentIndex | None = Field(default=None, exclude=True)
    content_layouts: list[ContentLayout] = Field(default_factory=list, exclude=True)
    content_part_contents: list[ContentPartContent] = Field(default_factory=list)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    source: ContentSource
    token_count: int | None = Field(default=None)

    @classmethod
    async def create_content(
        cls,
        key: str = "default",
        title: str | None = None,
        source: ContentSource = ContentSource.user,
        token_count: int | None = None,
        seed_inline_text: str | None = None,
        seed_part_position: int = 0,
    ) -> Content:
        """Creates a new content container."""

        payload = {
            "key": key,
            "title": title,
            "source": source,
            "token_count": token_count,
            "seed_inline_text": seed_inline_text,
            "seed_part_position": seed_part_position,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Content):
            return value
        return Content.validate_invocation_value(value)

    async def set_title(self, title: str | None = None) -> None:
        """Sets (or clears) the content title."""

        payload = {"title": title}
        await invoke_instance(orm_model=self, function_name="set_title", payload=payload)
        return None


class ContentCreateContentInput(BaseModel):
    key: str = Field(default="default")
    title: str | None = Field(default=None)
    source: ContentSource = Field(default=ContentSource.user)
    token_count: int | None = Field(default=None)
    seed_inline_text: str | None = Field(default=None)
    seed_part_position: int = Field(default=0)


class ContentCreateContentOutput(BaseModel):
    value: Content


class ContentSetTitleInput(BaseModel):
    title: str | None = Field(default=None)


class ContentSetTitleOutput(BaseModel):
    pass


FUNCTIONS = {
    "Content": {
        "create_content": {
            "canonical": {
                "name": "create_content",
                "description": "Creates a new content container.",
                "is_constructor": True,
            },
            "input": ContentCreateContentInput,
            "output": ContentCreateContentOutput,
        },
        "set_title": {
            "canonical": {
                "name": "set_title",
                "description": "Sets (or clears) the content title.",
                "is_constructor": False,
            },
            "input": ContentSetTitleInput,
            "output": ContentSetTitleOutput,
        },
    },
}

__all__ = [
    "Content",
    "ContentCreateContentInput",
    "ContentCreateContentOutput",
    "ContentSetTitleInput",
    "ContentSetTitleOutput",
    "FUNCTIONS",
]
