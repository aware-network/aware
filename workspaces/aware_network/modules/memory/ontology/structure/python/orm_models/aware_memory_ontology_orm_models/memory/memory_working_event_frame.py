from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_memory_ontology_orm_models.memory.memory_working_event_meaning import MemoryWorkingEventMeaning
    from aware_reactivity_ontology_orm_models.event.event import Event


class MemoryWorkingEventFrame(ORMModel):
    """
    Event payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=event`.
    - Event provenance is canonical reactivity evidence.
    """

    # Relationships
    event: Event | None = Field(default=None, exclude=True)
    resolved_meaning: MemoryWorkingEventMeaning | None = Field(default=None, exclude=True)

    # Attributes
    event_config_id: UUID | None = Field(default=None)
    event_activation_id: UUID | None = Field(default=None)
    event_type: str | None = Field(default=None)
    event_source: str | None = Field(default=None)
    event_status: str | None = Field(default=None)
    commit_branch_id: UUID | None = Field(default=None)
    commit_projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    intent_key: str | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_execution_key: str | None = Field(default=None)
    api_call_key: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_experience_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_event_id: UUID | None = Field(default=None)
    invocation_config_id: UUID | None = Field(default=None)
    endpoint_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)

    # Foreign Keys
    memory_working_item_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.event_frame"
    )
    event_id: UUID = Field(description="Foreign key for MemoryWorkingEventFrame.event")
