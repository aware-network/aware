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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology.session.attention_session import AttentionSession


class EnvironmentSessionAttentionSession(ORMModel):
    """
    EnvironmentSession-owned portal to one AttentionSession.
    Contract:
    - Environment does not own or inspect AttentionSession internals.
    - One EnvironmentSession may resolve against many AttentionSessions.
    - The same AttentionSession may be shared by other EnvironmentSessions.
    - This is a pure relationship object, not a capability.
    """

    # Relationships
    attention_session: AttentionSession | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.attention_sessions")
    attention_session_id: UUID = Field(
        description="Foreign key for EnvironmentSessionAttentionSession.attention_session"
    )

    @classmethod
    async def build_via_environment_session(
        cls,
        environment_session_id: UUID,
        attention_session_id: UUID,
        key: str | None = None,
        title: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionAttentionSession:
        """
        Construct one EnvironmentSession -> AttentionSession portal row.

        Contract:
        - Stable identity is EnvironmentSession path + AttentionSession.
        - AttentionSession is only a portal target here.
        - No Attention layout/section/focus internals are authored here.
        """

        payload = {
            "environment_session_id": environment_session_id,
            "attention_session_id": attention_session_id,
            "key": key,
            "title": title,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentSessionAttentionSession):
            return value
        return EnvironmentSessionAttentionSession.validate_invocation_value(value)


class EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionInput(BaseModel):
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.attention_sessions")
    attention_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionOutput(BaseModel):
    value: EnvironmentSessionAttentionSession


FUNCTIONS = {
    "EnvironmentSessionAttentionSession": {
        "build_via_environment_session": {
            "canonical": {
                "name": "build_via_environment_session",
                "description": "Construct one EnvironmentSession -> AttentionSession portal row.\n\nContract:\n- Stable identity is EnvironmentSession path + AttentionSession.\n- AttentionSession is only a portal target here.\n- No Attention layout/section/focus internals are authored here.",
                "is_constructor": True,
            },
            "input": EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionInput,
            "output": EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionOutput,
        },
    },
}

__all__ = [
    "EnvironmentSessionAttentionSession",
    "EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionInput",
    "EnvironmentSessionAttentionSessionBuildViaEnvironmentSessionOutput",
    "FUNCTIONS",
]
