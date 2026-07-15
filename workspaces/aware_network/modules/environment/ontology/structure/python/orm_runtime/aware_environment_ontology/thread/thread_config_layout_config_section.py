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
    from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigLayoutConfigSection(ORMModel):
    """
    Projection-host placement inside one ThreadConfig LayoutConfig option.
    Contract:
    - Attention owns layout section config.
    - Meta owns ObjectProjectionGraph authority.
    - Experience may later bind views/actions over these declared host slots.
    """

    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    key: str | None = Field(
        default=None, description="Optional stable association key under the parent ThreadConfigLayoutConfig."
    )
    position: int | None = Field(default=None, description="Ordering hint within repeated section placements.")
    is_default: bool = Field(
        default=False, description="Marks the preferred/default placement for this layout section."
    )
    narrative: str | None = Field(
        default=None, description="Narrative text for why this projection belongs in the section."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for the section placement.")

    # Foreign Keys
    thread_config_layout_config_id: UUID = Field(description="Foreign key for ThreadConfigLayoutConfig.sections")
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for ThreadConfigLayoutConfigSection.layout_config_section_config"
    )
    object_projection_graph_id: UUID | None = Field(
        default=None, description="Foreign key for ThreadConfigLayoutConfigSection.object_projection_graph"
    )

    @classmethod
    async def create_via_thread_config_layout_config(
        cls,
        thread_config_layout_config_id: UUID,
        layout_config_section_config_id: UUID,
        object_projection_graph_id: UUID | None = None,
        key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigLayoutConfigSection:
        """
        Create a deterministic ThreadConfigLayoutConfigSection edge.

        Contract:
        - Identity is scoped under ThreadConfigLayoutConfig by layout section config.
        - Optional OPG ref must point at a hosted projection graph for the same thread config.
        - No Experience-owned graph binding appears in this Environment topology object.
        """

        payload = {
            "thread_config_layout_config_id": thread_config_layout_config_id,
            "layout_config_section_config_id": layout_config_section_config_id,
            "object_projection_graph_id": object_projection_graph_id,
            "key": key,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_thread_config_layout_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadConfigLayoutConfigSection):
            return value
        return ThreadConfigLayoutConfigSection.validate_invocation_value(value)


class ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigInput(BaseModel):
    thread_config_layout_config_id: UUID = Field(description="Foreign key for ThreadConfigLayoutConfig.sections")
    layout_config_section_config_id: UUID
    object_projection_graph_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigOutput(BaseModel):
    value: ThreadConfigLayoutConfigSection


FUNCTIONS = {
    "ThreadConfigLayoutConfigSection": {
        "create_via_thread_config_layout_config": {
            "canonical": {
                "name": "create_via_thread_config_layout_config",
                "description": "Create a deterministic ThreadConfigLayoutConfigSection edge.\n\nContract:\n- Identity is scoped under ThreadConfigLayoutConfig by layout section config.\n- Optional OPG ref must point at a hosted projection graph for the same thread config.\n- No Experience-owned graph binding appears in this Environment topology object.",
                "is_constructor": True,
            },
            "input": ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigInput,
            "output": ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigOutput,
        },
    },
}

__all__ = [
    "ThreadConfigLayoutConfigSection",
    "ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigInput",
    "ThreadConfigLayoutConfigSectionCreateViaThreadConfigLayoutConfigOutput",
    "FUNCTIONS",
]
