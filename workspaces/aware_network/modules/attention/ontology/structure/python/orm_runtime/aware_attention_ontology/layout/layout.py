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
    from aware_attention_ontology.layout.layout_section import LayoutSection


class Layout(ORMModel):
    """
    Declarative layout for Attention Contracts.
    Contract:
    - Defines section topology for one attention contract.
    """

    # Relationships
    sections: list[LayoutSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, key: str, title: str, description: str | None = None) -> Layout:
        """Create a deterministic Layout by key."""

        payload = {"key": key, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Layout):
            return value
        return Layout.validate_invocation_value(value)

    async def add_section(self, section_id: UUID, title: str, description: str | None = None) -> LayoutSection:
        """Adds a Section to this Layout."""

        payload = {"section_id": section_id, "title": title, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.layout.layout_section import LayoutSection

        if isinstance(value, LayoutSection):
            return value
        return LayoutSection.validate_invocation_value(value)


class LayoutBuildInput(BaseModel):
    key: str
    title: str
    description: str | None = Field(default=None)


class LayoutBuildOutput(BaseModel):
    value: Layout


class LayoutAddSectionInput(BaseModel):
    section_id: UUID
    title: str
    description: str | None = Field(default=None)


class LayoutAddSectionOutput(BaseModel):
    value: LayoutSection


FUNCTIONS = {
    "Layout": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic Layout by key.",
                "is_constructor": True,
            },
            "input": LayoutBuildInput,
            "output": LayoutBuildOutput,
        },
        "add_section": {
            "canonical": {
                "name": "add_section",
                "description": "Adds a Section to this Layout.",
                "is_constructor": False,
            },
            "input": LayoutAddSectionInput,
            "output": LayoutAddSectionOutput,
        },
    },
}

__all__ = [
    "Layout",
    "LayoutBuildInput",
    "LayoutBuildOutput",
    "LayoutAddSectionInput",
    "LayoutAddSectionOutput",
    "FUNCTIONS",
]
