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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_content_ontology.content.content import Content


class ContentChainContent(ORMModel):
    # Relationships
    content: Content | None = Field(default=None, exclude=True, description="Association target reference to Content")

    # Attributes
    position: int

    # Foreign Keys
    content_id: UUID = Field(description="Join FK to Content")
    content_chain_id: UUID = Field(description="Join FK to ContentChain")

    @classmethod
    async def create_content_chain_content_via_content_chain(
        cls, content_chain_id: UUID, content_id: UUID, position: int
    ) -> ContentChainContent:
        """Appends a Content to a ContentChain by creating a ContentChainContent edge."""

        payload = {"content_chain_id": content_chain_id, "content_id": content_id, "position": position}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_chain_content_via_content_chain", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentChainContent):
            return value
        return ContentChainContent.validate_invocation_value(value)


class ContentChainContentCreateContentChainContentViaContentChainInput(BaseModel):
    content_chain_id: UUID = Field(description="Join FK to ContentChain")
    content_id: UUID
    position: int


class ContentChainContentCreateContentChainContentViaContentChainOutput(BaseModel):
    value: ContentChainContent


FUNCTIONS = {
    "ContentChainContent": {
        "create_content_chain_content_via_content_chain": {
            "canonical": {
                "name": "create_content_chain_content_via_content_chain",
                "description": "Appends a Content to a ContentChain by creating a ContentChainContent edge.",
                "is_constructor": True,
            },
            "input": ContentChainContentCreateContentChainContentViaContentChainInput,
            "output": ContentChainContentCreateContentChainContentViaContentChainOutput,
        },
    },
}

__all__ = [
    "ContentChainContent",
    "ContentChainContentCreateContentChainContentViaContentChainInput",
    "ContentChainContentCreateContentChainContentViaContentChainOutput",
    "FUNCTIONS",
]
