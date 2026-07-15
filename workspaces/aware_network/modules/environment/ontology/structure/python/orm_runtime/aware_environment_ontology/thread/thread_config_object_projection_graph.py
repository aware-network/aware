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
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigObjectProjectionGraph(ORMModel):
    """
    Environment ThreadConfig -> Meta ObjectProjectionGraph authority edge.
    Contract:
    - Declares which projection graphs a thread config can host.
    - Does not identify an Experience or view implementation.
    """

    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    narrative: str | None = Field(
        default=None, description="Narrative text for why this projection graph is part of the thread context."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for this projection graph landing.")
    view_key: str | None = Field(
        default=None, description="Optional canonical view key under the target projection identity."
    )
    position: int | None = Field(default=None, description="Ordering hint for projection clusters.")
    is_default: bool = Field(
        default=False, description="Marks preferred/default projection graph for this thread config."
    )

    # Foreign Keys
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.object_projection_graphs")
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ThreadConfigObjectProjectionGraph.object_projection_graph"
    )

    @classmethod
    async def create_via_thread_config(
        cls,
        thread_config_id: UUID,
        object_projection_graph_id: UUID,
        view_key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigObjectProjectionGraph:
        """
        Create a deterministic ThreadConfigObjectProjectionGraph association edge.

        Contract:
        - Identity is `(thread_config_id, object_projection_graph_id)`.
        - Projection authority is Meta-owned.
        """

        payload = {
            "thread_config_id": thread_config_id,
            "object_projection_graph_id": object_projection_graph_id,
            "view_key": view_key,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_thread_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadConfigObjectProjectionGraph):
            return value
        return ThreadConfigObjectProjectionGraph.validate_invocation_value(value)


class ThreadConfigObjectProjectionGraphCreateViaThreadConfigInput(BaseModel):
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.object_projection_graphs")
    object_projection_graph_id: UUID
    view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigObjectProjectionGraphCreateViaThreadConfigOutput(BaseModel):
    value: ThreadConfigObjectProjectionGraph


FUNCTIONS = {
    "ThreadConfigObjectProjectionGraph": {
        "create_via_thread_config": {
            "canonical": {
                "name": "create_via_thread_config",
                "description": "Create a deterministic ThreadConfigObjectProjectionGraph association edge.\n\nContract:\n- Identity is `(thread_config_id, object_projection_graph_id)`.\n- Projection authority is Meta-owned.",
                "is_constructor": True,
            },
            "input": ThreadConfigObjectProjectionGraphCreateViaThreadConfigInput,
            "output": ThreadConfigObjectProjectionGraphCreateViaThreadConfigOutput,
        },
    },
}

__all__ = [
    "ThreadConfigObjectProjectionGraph",
    "ThreadConfigObjectProjectionGraphCreateViaThreadConfigInput",
    "ThreadConfigObjectProjectionGraphCreateViaThreadConfigOutput",
    "FUNCTIONS",
]
