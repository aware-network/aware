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
    from aware_environment_ontology_orm_models.environment.environment_navigation_context import (
        EnvironmentNavigationContext,
    )
    from aware_environment_ontology_orm_models.environment.environment_session_attention_session import (
        EnvironmentSessionAttentionSession,
    )
    from aware_environment_ontology_orm_models.environment.environment_session_config import EnvironmentSessionConfig
    from aware_environment_ontology_orm_models.environment.environment_session_thread import EnvironmentSessionThread
    from aware_identity_ontology_orm_models.session.session import Session


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
