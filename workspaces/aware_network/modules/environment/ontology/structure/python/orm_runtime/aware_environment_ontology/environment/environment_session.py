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
    from aware_environment_ontology.environment.environment_navigation_context import EnvironmentNavigationContext
    from aware_environment_ontology.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology.environment.environment_session_config import EnvironmentSessionConfig
    from aware_environment_ontology.environment.environment_session_thread import EnvironmentSessionThread
    from aware_identity_ontology.session.session import Session


class EnvironmentSession(ORMModel):
    """
    Environment-specific wrapper around an Identity Session.
    Contract:
    - Parent constructor is Environment.
    - Optional EnvironmentSessionConfig provides non-key defaults/provenance.
    - Identity Session owns actor members, ActorRole evidence, and provider
    session attachments.
    - EnvironmentSession records Environment-specific resolution state only.
    - Profiles remain Process/Thread provenance and are reached through the
    selected Thread path.
    - Navigation contexts live here as shared browser-like surfaces.
    - Attention focus remains a later Layout/Section rail.
    """

    # Relationships
    session_config: EnvironmentSessionConfig | None = Field(default=None)
    identity_session: Session | None = Field(default=None)
    navigation_contexts: list[EnvironmentNavigationContext] = Field(default_factory=list)
    session_threads: list[EnvironmentSessionThread] = Field(
        default_factory=list,
        description="Session-local Thread/Layout resolution rows.\nContract:\n- EnvironmentNavigationContext points to one of these rows as its\ncurrent target.\n- These rows pin Thread + ThreadLayout for this EnvironmentSession.\n- There is no EnvironmentSession-global active thread.",
    )
    attention_sessions: list[EnvironmentSessionAttentionSession] = Field(
        default_factory=list,
        description="Environment-visible AttentionSession portal rows.\nContract:\n- Attention owns AttentionSession internals.\n- Environment only records which AttentionSessions this\nEnvironmentSession resolves against.",
    )

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_id: UUID = Field(description="Foreign key for Environment.sessions")
    session_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentSession.session_config"
    )
    identity_session_id: UUID = Field(description="Foreign key for EnvironmentSession.identity_session")

    async def create_navigation_context(
        self,
        key: str,
        session_thread_id: UUID,
        title: str | None = None,
        status: str = "active",
        is_default: bool = False,
    ) -> EnvironmentNavigationContext:
        """
        Create one shared navigation context under this EnvironmentSession.

        Contract:
        - Stable identity is EnvironmentSession path + `key`.
        - This is a shared tab/window-like OS pointer.
        - Multiple contexts may exist per EnvironmentSession.
        - SessionThread target history is derived from commits over this
          context; no custom navigation-event object exists in v0.
        - Attention focus and Experience lenses remain separate downstream
          rails.
        """

        payload = {
            "key": key,
            "session_thread_id": session_thread_id,
            "title": title,
            "status": status,
            "is_default": is_default,
        }
        result = await invoke_instance(orm_model=self, function_name="create_navigation_context", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_navigation_context import EnvironmentNavigationContext

        if isinstance(value, EnvironmentNavigationContext):
            return value
        return EnvironmentNavigationContext.validate_invocation_value(value)

    async def attach_attention_session(
        self,
        attention_session_id: UUID,
        key: str | None = None,
        title: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionAttentionSession:
        """
        Attach one AttentionSession portal to this EnvironmentSession.

        Contract:
        - Stable identity is EnvironmentSession path + AttentionSession.
        - AttentionSession remains Attention-owned source truth.
        - This is a pure Environment session relationship object, not a
          capability object.
        """

        payload = {
            "attention_session_id": attention_session_id,
            "key": key,
            "title": title,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_attention_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_session_attention_session import (
            EnvironmentSessionAttentionSession,
        )

        if isinstance(value, EnvironmentSessionAttentionSession):
            return value
        return EnvironmentSessionAttentionSession.validate_invocation_value(value)

    async def resolve_thread(
        self,
        thread_id: UUID,
        thread_layout_id: UUID,
        attention_session_id: UUID | None = None,
        key: str | None = None,
        title: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionThread:
        """
        Resolve one EnvironmentSession-local Thread/Layout row.

        Contract:
        - Stable identity is EnvironmentSession path + Thread + ThreadLayout.
        - NavigationContext points to this row when selected.
        - ThreadLayout is session-scoped here, not Thread-global active state.
        - Optional attention_session_id points at an
          EnvironmentSessionAttentionSession row owned by this session.
        """

        payload = {
            "thread_id": thread_id,
            "thread_layout_id": thread_layout_id,
            "attention_session_id": attention_session_id,
            "key": key,
            "title": title,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="resolve_thread", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_session_thread import EnvironmentSessionThread

        if isinstance(value, EnvironmentSessionThread):
            return value
        return EnvironmentSessionThread.validate_invocation_value(value)

    @classmethod
    async def build_via_environment(
        cls,
        environment_id: UUID,
        identity_session_id: UUID,
        session_config_id: UUID | None = None,
        key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSession:
        """
        Construct one EnvironmentSession under an Environment.

        Contract:
        - Stable identity is Environment path + Identity Session.
        - `session_config_id` is optional non-key session defaults/provenance.
        - `identity_session_id` resolves the required Identity Session portal
          and must not be inferred from keys.
        - Actor membership, ActorRole evidence, and provider sessions live on
          the linked Identity Session.
        """

        payload = {
            "environment_id": environment_id,
            "identity_session_id": identity_session_id,
            "session_config_id": session_config_id,
            "key": key,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentSession):
            return value
        return EnvironmentSession.validate_invocation_value(value)


class EnvironmentSessionCreateNavigationContextInput(BaseModel):
    key: str
    session_thread_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    is_default: bool = Field(default=False)


class EnvironmentSessionCreateNavigationContextOutput(BaseModel):
    value: EnvironmentNavigationContext


class EnvironmentSessionAttachAttentionSessionInput(BaseModel):
    attention_session_id: UUID
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionAttachAttentionSessionOutput(BaseModel):
    value: EnvironmentSessionAttentionSession


class EnvironmentSessionResolveThreadInput(BaseModel):
    thread_id: UUID
    thread_layout_id: UUID
    attention_session_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionResolveThreadOutput(BaseModel):
    value: EnvironmentSessionThread


class EnvironmentSessionBuildViaEnvironmentInput(BaseModel):
    environment_id: UUID = Field(description="Foreign key for Environment.sessions")
    identity_session_id: UUID
    session_config_id: UUID | None = Field(default=None)
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionBuildViaEnvironmentOutput(BaseModel):
    value: EnvironmentSession


FUNCTIONS = {
    "EnvironmentSession": {
        "create_navigation_context": {
            "canonical": {
                "name": "create_navigation_context",
                "description": "Create one shared navigation context under this EnvironmentSession.\n\nContract:\n- Stable identity is EnvironmentSession path + `key`.\n- This is a shared tab/window-like OS pointer.\n- Multiple contexts may exist per EnvironmentSession.\n- SessionThread target history is derived from commits over this\n  context; no custom navigation-event object exists in v0.\n- Attention focus and Experience lenses remain separate downstream\n  rails.",
                "is_constructor": False,
            },
            "input": EnvironmentSessionCreateNavigationContextInput,
            "output": EnvironmentSessionCreateNavigationContextOutput,
        },
        "attach_attention_session": {
            "canonical": {
                "name": "attach_attention_session",
                "description": "Attach one AttentionSession portal to this EnvironmentSession.\n\nContract:\n- Stable identity is EnvironmentSession path + AttentionSession.\n- AttentionSession remains Attention-owned source truth.\n- This is a pure Environment session relationship object, not a\n  capability object.",
                "is_constructor": False,
            },
            "input": EnvironmentSessionAttachAttentionSessionInput,
            "output": EnvironmentSessionAttachAttentionSessionOutput,
        },
        "resolve_thread": {
            "canonical": {
                "name": "resolve_thread",
                "description": "Resolve one EnvironmentSession-local Thread/Layout row.\n\nContract:\n- Stable identity is EnvironmentSession path + Thread + ThreadLayout.\n- NavigationContext points to this row when selected.\n- ThreadLayout is session-scoped here, not Thread-global active state.\n- Optional attention_session_id points at an\n  EnvironmentSessionAttentionSession row owned by this session.",
                "is_constructor": False,
            },
            "input": EnvironmentSessionResolveThreadInput,
            "output": EnvironmentSessionResolveThreadOutput,
        },
        "build_via_environment": {
            "canonical": {
                "name": "build_via_environment",
                "description": "Construct one EnvironmentSession under an Environment.\n\nContract:\n- Stable identity is Environment path + Identity Session.\n- `session_config_id` is optional non-key session defaults/provenance.\n- `identity_session_id` resolves the required Identity Session portal\n  and must not be inferred from keys.\n- Actor membership, ActorRole evidence, and provider sessions live on\n  the linked Identity Session.",
                "is_constructor": True,
            },
            "input": EnvironmentSessionBuildViaEnvironmentInput,
            "output": EnvironmentSessionBuildViaEnvironmentOutput,
        },
    },
}

__all__ = [
    "EnvironmentSession",
    "EnvironmentSessionCreateNavigationContextInput",
    "EnvironmentSessionCreateNavigationContextOutput",
    "EnvironmentSessionAttachAttentionSessionInput",
    "EnvironmentSessionAttachAttentionSessionOutput",
    "EnvironmentSessionResolveThreadInput",
    "EnvironmentSessionResolveThreadOutput",
    "EnvironmentSessionBuildViaEnvironmentInput",
    "EnvironmentSessionBuildViaEnvironmentOutput",
    "FUNCTIONS",
]
