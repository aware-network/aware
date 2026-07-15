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
    from aware_attention_ontology.focus.focus_scope import FocusScope


class SectionFocusScope(ORMModel):
    """FocusScope binding at Section level."""

    # Relationships
    focus_scope: FocusScope | None = Field(default=None, exclude=True)

    # Attributes
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    section_id: UUID = Field(description="Foreign key for Section.focus_scopes")
    focus_scope_id: UUID = Field(description="Foreign key for SectionFocusScope.focus_scope")

    @classmethod
    async def build_via_section(
        cls, section_id: UUID, focus_scope_id: UUID, title: str, description: str | None = None
    ) -> SectionFocusScope:
        """Builds a deterministic SectionFocusScope."""

        payload = {
            "section_id": section_id,
            "focus_scope_id": focus_scope_id,
            "title": title,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SectionFocusScope):
            return value
        return SectionFocusScope.validate_invocation_value(value)


class SectionFocusScopeBuildViaSectionInput(BaseModel):
    section_id: UUID = Field(description="Foreign key for Section.focus_scopes")
    focus_scope_id: UUID
    title: str
    description: str | None = Field(default=None)


class SectionFocusScopeBuildViaSectionOutput(BaseModel):
    value: SectionFocusScope


FUNCTIONS = {
    "SectionFocusScope": {
        "build_via_section": {
            "canonical": {
                "name": "build_via_section",
                "description": "Builds a deterministic SectionFocusScope.",
                "is_constructor": True,
            },
            "input": SectionFocusScopeBuildViaSectionInput,
            "output": SectionFocusScopeBuildViaSectionOutput,
        },
    },
}

__all__ = [
    "SectionFocusScope",
    "SectionFocusScopeBuildViaSectionInput",
    "SectionFocusScopeBuildViaSectionOutput",
    "FUNCTIONS",
]
