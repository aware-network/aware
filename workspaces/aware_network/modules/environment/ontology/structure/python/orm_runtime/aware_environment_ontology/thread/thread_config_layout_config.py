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
    from aware_attention_ontology.layout.layout_config import LayoutConfig
    from aware_environment_ontology.thread.thread_config_layout_config_section import ThreadConfigLayoutConfigSection


class ThreadConfigLayoutConfig(ORMModel):
    """
    Deterministic ThreadConfig -> Attention LayoutConfig association edge.
    Contract:
    - ThreadConfig is the Environment-owned availability source.
    - LayoutConfig is Attention-owned topology config.
    - Runtime provisioning lowers this edge into Thread -> ThreadLayout -> Layout.
    """

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)
    sections: list[ThreadConfigLayoutConfigSection] = Field(default_factory=list)

    # Attributes
    key: str | None = Field(default=None, description="Optional stable association key under the parent ThreadConfig.")
    position: int | None = Field(default=None, description="Ordering hint for thread layout selectors.")
    narrative: str | None = Field(default=None, description="Narrative text for why this layout belongs to the thread.")
    intent: str | None = Field(default=None, description="Short canonical intent for the layout option.")

    # Foreign Keys
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.layout_configs")
    layout_config_id: UUID = Field(description="Foreign key for ThreadConfigLayoutConfig.layout_config")

    async def add_section(
        self,
        layout_config_section_config_id: UUID,
        object_projection_graph_id: UUID | None = None,
        key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigLayoutConfigSection:
        """
        Create a deterministic layout-section placement for this ThreadConfig layout.

        Contract:
        - Binds an Attention LayoutConfig section to an optional hosted projection graph.
        - Does not reference ProjectionExperienceSectionGraphBinding.
        """

        payload = {
            "layout_config_section_config_id": layout_config_section_config_id,
            "object_projection_graph_id": object_projection_graph_id,
            "key": key,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_section", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_config_layout_config_section import (
            ThreadConfigLayoutConfigSection,
        )

        if isinstance(value, ThreadConfigLayoutConfigSection):
            return value
        return ThreadConfigLayoutConfigSection.validate_invocation_value(value)

    @classmethod
    async def create_via_thread_config(
        cls,
        thread_config_id: UUID,
        layout_config_id: UUID,
        key: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigLayoutConfig:
        """
        Create a deterministic ThreadConfigLayoutConfig association edge.

        Contract:
        - Identity is `(thread_config_id, layout_config_id)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {
            "thread_config_id": thread_config_id,
            "layout_config_id": layout_config_id,
            "key": key,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_thread_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadConfigLayoutConfig):
            return value
        return ThreadConfigLayoutConfig.validate_invocation_value(value)


class ThreadConfigLayoutConfigAddSectionInput(BaseModel):
    layout_config_section_config_id: UUID
    object_projection_graph_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigLayoutConfigAddSectionOutput(BaseModel):
    value: ThreadConfigLayoutConfigSection


class ThreadConfigLayoutConfigCreateViaThreadConfigInput(BaseModel):
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.layout_configs")
    layout_config_id: UUID
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigLayoutConfigCreateViaThreadConfigOutput(BaseModel):
    value: ThreadConfigLayoutConfig


FUNCTIONS = {
    "ThreadConfigLayoutConfig": {
        "add_section": {
            "canonical": {
                "name": "add_section",
                "description": "Create a deterministic layout-section placement for this ThreadConfig layout.\n\nContract:\n- Binds an Attention LayoutConfig section to an optional hosted projection graph.\n- Does not reference ProjectionExperienceSectionGraphBinding.",
                "is_constructor": False,
            },
            "input": ThreadConfigLayoutConfigAddSectionInput,
            "output": ThreadConfigLayoutConfigAddSectionOutput,
        },
        "create_via_thread_config": {
            "canonical": {
                "name": "create_via_thread_config",
                "description": "Create a deterministic ThreadConfigLayoutConfig association edge.\n\nContract:\n- Identity is `(thread_config_id, layout_config_id)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": ThreadConfigLayoutConfigCreateViaThreadConfigInput,
            "output": ThreadConfigLayoutConfigCreateViaThreadConfigOutput,
        },
    },
}

__all__ = [
    "ThreadConfigLayoutConfig",
    "ThreadConfigLayoutConfigAddSectionInput",
    "ThreadConfigLayoutConfigAddSectionOutput",
    "ThreadConfigLayoutConfigCreateViaThreadConfigInput",
    "ThreadConfigLayoutConfigCreateViaThreadConfigOutput",
    "FUNCTIONS",
]
