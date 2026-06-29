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
    from aware_content_ontology.chain.content_chain_content import ContentChainContent


class ContentChainSection(ORMModel):
    # Relationships
    newest_content_chain_content: ContentChainContent | None = Field(default=None, exclude=True)
    oldest_content_chain_content: ContentChainContent | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    content_chain_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChain.content_chain_section"
    )
    newest_content_chain_content_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChainSection.newest_content_chain_content"
    )
    oldest_content_chain_content_id: UUID | None = Field(
        default=None, description="Foreign key for ContentChainSection.oldest_content_chain_content"
    )

    @classmethod
    async def build_via_content_chain(cls, content_chain_id: UUID, key: str = "default") -> ContentChainSection:
        """Creates a content-chain section cursor."""

        payload = {"content_chain_id": content_chain_id, "key": key}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_content_chain", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentChainSection):
            return value
        return ContentChainSection.validate_invocation_value(value)


class ContentChainSectionBuildViaContentChainInput(BaseModel):
    content_chain_id: UUID = Field(description="Foreign key for ContentChain.content_chain_section")
    key: str = Field(default="default")


class ContentChainSectionBuildViaContentChainOutput(BaseModel):
    value: ContentChainSection


FUNCTIONS = {
    "ContentChainSection": {
        "build_via_content_chain": {
            "canonical": {
                "name": "build_via_content_chain",
                "description": "Creates a content-chain section cursor.",
                "is_constructor": True,
            },
            "input": ContentChainSectionBuildViaContentChainInput,
            "output": ContentChainSectionBuildViaContentChainOutput,
        },
    },
}

__all__ = [
    "ContentChainSection",
    "ContentChainSectionBuildViaContentChainInput",
    "ContentChainSectionBuildViaContentChainOutput",
    "FUNCTIONS",
]
