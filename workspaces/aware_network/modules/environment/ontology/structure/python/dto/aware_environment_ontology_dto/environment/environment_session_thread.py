from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology_dto.thread.thread import Thread
    from aware_environment_ontology_dto.thread.thread_layout import ThreadLayout


class EnvironmentSessionThread(BaseModel):
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
