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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology.thread.thread import Thread
    from aware_environment_ontology.thread.thread_layout import ThreadLayout


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

    async def select_attention_session(self, attention_session_id: UUID | None = None) -> EnvironmentSessionThread:
        """
        Select the session-local AttentionSession resolution for this pin.

        Contract:
        - Mutates only the invoked EnvironmentSessionThread.
        - Does not mutate Thread, ThreadLayout, AttentionSession, or
          EnvironmentNavigationContext.
        """

        payload = {"attention_session_id": attention_session_id}
        result = await invoke_instance(orm_model=self, function_name="select_attention_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentSessionThread):
            return value
        return EnvironmentSessionThread.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_session(
        cls,
        environment_session_id: UUID,
        thread_id: UUID,
        thread_layout_id: UUID,
        attention_session_id: UUID | None = None,
        key: str | None = None,
        title: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionThread:
        """
        Construct one session-local Thread/Layout resolution row.

        Contract:
        - Stable identity is EnvironmentSession path + Thread + ThreadLayout.
        - `thread_layout_id` points at a Thread-owned layout attachment.
        - `attention_session_id` points at an Environment-owned
          EnvironmentSessionAttentionSession row.
        - Mutating attention pointer on this row records session-local attention
          resolution history through commits.
        """

        payload = {
            "environment_session_id": environment_session_id,
            "thread_id": thread_id,
            "thread_layout_id": thread_layout_id,
            "attention_session_id": attention_session_id,
            "key": key,
            "title": title,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentSessionThread):
            return value
        return EnvironmentSessionThread.validate_invocation_value(value)


class EnvironmentSessionThreadSelectAttentionSessionInput(BaseModel):
    attention_session_id: UUID | None = Field(default=None)


class EnvironmentSessionThreadSelectAttentionSessionOutput(BaseModel):
    value: EnvironmentSessionThread


class EnvironmentSessionThreadBuildViaEnvironmentSessionInput(BaseModel):
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.session_threads")
    thread_id: UUID
    thread_layout_id: UUID
    attention_session_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionThreadBuildViaEnvironmentSessionOutput(BaseModel):
    value: EnvironmentSessionThread


FUNCTIONS = {
    "EnvironmentSessionThread": {
        "select_attention_session": {
            "canonical": {
                "name": "select_attention_session",
                "description": "Select the session-local AttentionSession resolution for this pin.\n\nContract:\n- Mutates only the invoked EnvironmentSessionThread.\n- Does not mutate Thread, ThreadLayout, AttentionSession, or\n  EnvironmentNavigationContext.",
                "is_constructor": False,
            },
            "input": EnvironmentSessionThreadSelectAttentionSessionInput,
            "output": EnvironmentSessionThreadSelectAttentionSessionOutput,
        },
        "build_via_environment_session": {
            "canonical": {
                "name": "build_via_environment_session",
                "description": "Construct one session-local Thread/Layout resolution row.\n\nContract:\n- Stable identity is EnvironmentSession path + Thread + ThreadLayout.\n- `thread_layout_id` points at a Thread-owned layout attachment.\n- `attention_session_id` points at an Environment-owned\n  EnvironmentSessionAttentionSession row.\n- Mutating attention pointer on this row records session-local attention\n  resolution history through commits.",
                "is_constructor": True,
            },
            "input": EnvironmentSessionThreadBuildViaEnvironmentSessionInput,
            "output": EnvironmentSessionThreadBuildViaEnvironmentSessionOutput,
        },
    },
}

__all__ = [
    "EnvironmentSessionThread",
    "EnvironmentSessionThreadSelectAttentionSessionInput",
    "EnvironmentSessionThreadSelectAttentionSessionOutput",
    "EnvironmentSessionThreadBuildViaEnvironmentSessionInput",
    "EnvironmentSessionThreadBuildViaEnvironmentSessionOutput",
    "FUNCTIONS",
]
