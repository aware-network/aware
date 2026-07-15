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
from aware_content_ontology.content.content_enums import ContentSource

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.chain.content_chain_content import ContentChainContent
    from aware_content_ontology.chain.content_chain_section import ContentChainSection
    from aware_content_ontology.content.content import Content


class ContentChain(ORMModel):
    # Relationships
    content_chain_section: ContentChainSection | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Edges
    content_chain_contents_edges: list[ContentChainContent] = Field(
        default_factory=list, exclude=True, description="Edge association helper for content_chain_contents"
    )

    @property
    def content_chain_contents(self) -> list[Content]:
        return [edge.content for edge in self.content_chain_contents_edges if edge.content is not None]

    @classmethod
    async def build(cls, key: str = "default") -> ContentChain:
        """
        Creates a new content chain.

        Used by other modules (e.g. Conversation.build) to allocate a chain root.
        """

        payload = {"key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentChain):
            return value
        return ContentChain.validate_invocation_value(value)

    async def append_content(self, content_id: UUID, position: int = 0) -> UUID:
        """
        Appends a Content to this ContentChain.

        Canonical mutation boundary:
        - Callers must invoke this instance function (mutate-self-only) instead of constructing
          ContentChainContent directly from another object's handler.
        """

        payload = {"content_id": content_id, "position": position}
        result = await invoke_instance(orm_model=self, function_name="append_content", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def append_inline_text(
        self,
        seed_inline_text: str,
        source: ContentSource = ContentSource.user,
        token_count: int | None = None,
        title: str | None = None,
        position: int = 0,
    ) -> UUID:
        """
        Appends inline text to this ContentChain by creating Content + ContentChainContent.

        Canonical mutation boundary:
        - Parent handlers must call this instance function instead of creating Content directly.
        """

        payload = {
            "seed_inline_text": seed_inline_text,
            "source": source,
            "token_count": token_count,
            "title": title,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="append_inline_text", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value


class ContentChainBuildInput(BaseModel):
    key: str = Field(default="default")


class ContentChainBuildOutput(BaseModel):
    value: ContentChain


class ContentChainAppendContentInput(BaseModel):
    content_id: UUID
    position: int = Field(default=0)


class ContentChainAppendContentOutput(BaseModel):
    value: UUID


class ContentChainAppendInlineTextInput(BaseModel):
    seed_inline_text: str
    source: ContentSource = Field(default=ContentSource.user)
    token_count: int | None = Field(default=None)
    title: str | None = Field(default=None)
    position: int = Field(default=0)


class ContentChainAppendInlineTextOutput(BaseModel):
    value: UUID


FUNCTIONS = {
    "ContentChain": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a new content chain.\n\nUsed by other modules (e.g. Conversation.build) to allocate a chain root.",
                "is_constructor": True,
            },
            "input": ContentChainBuildInput,
            "output": ContentChainBuildOutput,
        },
        "append_content": {
            "canonical": {
                "name": "append_content",
                "description": "Appends a Content to this ContentChain.\n\nCanonical mutation boundary:\n- Callers must invoke this instance function (mutate-self-only) instead of constructing\n  ContentChainContent directly from another object's handler.",
                "is_constructor": False,
            },
            "input": ContentChainAppendContentInput,
            "output": ContentChainAppendContentOutput,
        },
        "append_inline_text": {
            "canonical": {
                "name": "append_inline_text",
                "description": "Appends inline text to this ContentChain by creating Content + ContentChainContent.\n\nCanonical mutation boundary:\n- Parent handlers must call this instance function instead of creating Content directly.",
                "is_constructor": False,
            },
            "input": ContentChainAppendInlineTextInput,
            "output": ContentChainAppendInlineTextOutput,
        },
    },
}

__all__ = [
    "ContentChain",
    "ContentChainBuildInput",
    "ContentChainBuildOutput",
    "ContentChainAppendContentInput",
    "ContentChainAppendContentOutput",
    "ContentChainAppendInlineTextInput",
    "ContentChainAppendInlineTextOutput",
    "FUNCTIONS",
]
