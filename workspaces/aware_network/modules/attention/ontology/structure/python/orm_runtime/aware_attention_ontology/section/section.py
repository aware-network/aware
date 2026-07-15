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
    from aware_attention_ontology.section.section_focus_scope import SectionFocusScope


class Section(ORMModel):
    """Declarative "representation unit" as section for Attention contract via FocusScope."""

    # Relationships
    focus_scopes: list[SectionFocusScope] = Field(default_factory=list, exclude=True)
    active_focus_scope: SectionFocusScope | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    active_focus_scope_id: UUID | None = Field(default=None, description="Foreign key for Section.active_focus_scope")

    @classmethod
    async def build(cls, key: str, title: str, description: str | None = None) -> Section:
        """Builds a deterministic Section for a key."""

        payload = {"key": key, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Section):
            return value
        return Section.validate_invocation_value(value)

    async def add_focus_scope(
        self, focus_scope_id: UUID, title: str, description: str | None = None
    ) -> SectionFocusScope:
        """Adds a FocusScope binding to this Section."""

        payload = {"focus_scope_id": focus_scope_id, "title": title, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.section.section_focus_scope import SectionFocusScope

        if isinstance(value, SectionFocusScope):
            return value
        return SectionFocusScope.validate_invocation_value(value)

    async def set_active_focus_scope(self, focus_scope_id: UUID) -> SectionFocusScope:
        """Set active_focus_scope to the given focus_scope_id."""

        payload = {"focus_scope_id": focus_scope_id}
        result = await invoke_instance(orm_model=self, function_name="set_active_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.section.section_focus_scope import SectionFocusScope

        if isinstance(value, SectionFocusScope):
            return value
        return SectionFocusScope.validate_invocation_value(value)


class SectionBuildInput(BaseModel):
    key: str
    title: str
    description: str | None = Field(default=None)


class SectionBuildOutput(BaseModel):
    value: Section


class SectionAddFocusScopeInput(BaseModel):
    focus_scope_id: UUID
    title: str
    description: str | None = Field(default=None)


class SectionAddFocusScopeOutput(BaseModel):
    value: SectionFocusScope


class SectionSetActiveFocusScopeInput(BaseModel):
    focus_scope_id: UUID


class SectionSetActiveFocusScopeOutput(BaseModel):
    value: SectionFocusScope


FUNCTIONS = {
    "Section": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Builds a deterministic Section for a key.",
                "is_constructor": True,
            },
            "input": SectionBuildInput,
            "output": SectionBuildOutput,
        },
        "add_focus_scope": {
            "canonical": {
                "name": "add_focus_scope",
                "description": "Adds a FocusScope binding to this Section.",
                "is_constructor": False,
            },
            "input": SectionAddFocusScopeInput,
            "output": SectionAddFocusScopeOutput,
        },
        "set_active_focus_scope": {
            "canonical": {
                "name": "set_active_focus_scope",
                "description": "Set active_focus_scope to the given focus_scope_id.",
                "is_constructor": False,
            },
            "input": SectionSetActiveFocusScopeInput,
            "output": SectionSetActiveFocusScopeOutput,
        },
    },
}

__all__ = [
    "Section",
    "SectionBuildInput",
    "SectionBuildOutput",
    "SectionAddFocusScopeInput",
    "SectionAddFocusScopeOutput",
    "SectionSetActiveFocusScopeInput",
    "SectionSetActiveFocusScopeOutput",
    "FUNCTIONS",
]
