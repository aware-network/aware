from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology_orm_models.thread.thread import Thread
    from aware_environment_ontology_orm_models.thread.thread_layout import ThreadLayout


class EnvironmentSessionThread(ORMModel):
    """
    EnvironmentSession-local Thread/Layout resolution row.
    Contract:
    - This row pins a Thread + ThreadLayout for one EnvironmentSession.
    - EnvironmentNavigationContext selects one row as its current target.
    - Optional attention_session links to an EnvironmentSessionAttentionSession
    row, not directly into Attention internals.
    - EnvironmentSession owns these rows; no global active session-thread exists.
    """

    # Relationships
    thread: Thread | None = Field(default=None)
    thread_layout: ThreadLayout | None = Field(default=None)
    attention_session: EnvironmentSessionAttentionSession | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.session_threads")
    thread_id: UUID = Field(description="Foreign key for EnvironmentSessionThread.thread")
    thread_layout_id: UUID = Field(description="Foreign key for EnvironmentSessionThread.thread_layout")
    attention_session_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentSessionThread.attention_session"
    )
