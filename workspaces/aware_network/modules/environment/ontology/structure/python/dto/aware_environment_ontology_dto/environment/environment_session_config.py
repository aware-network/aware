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
    from aware_environment_ontology_dto.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology_dto.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_dto.process.process_config import ProcessConfig
    from aware_environment_ontology_dto.thread.thread_config import ThreadConfig
    from aware_identity_ontology_dto.session.session_config import SessionConfig


class EnvironmentSessionConfig(BaseModel):
    """
    Environment-specific wrapper around an Identity SessionConfig.
    Contract:
    - Parent constructor is EnvironmentConfig.
    - Identity SessionConfig owns reusable actor participation policy.
    - EnvironmentSessionConfig owns Environment-level session meaning, title,
    purpose, status, provider-facing metadata, and optional bootstrap
    profile/process/thread defaults.
    - Concrete membership is never stored here; it lives on Identity Session.
    - Runtime EnvironmentSession instances are Environment-owned, not
    EnvironmentSessionConfig-owned.
    """

    # Relationships
    identity_session_config: SessionConfig | None = Field(default=None)
    default_profile_config: EnvironmentProfileConfig | None = Field(default=None)
    default_process_config: ProcessConfig | None = Field(default=None)
    default_thread_config: ThreadConfig | None = Field(default=None)
    environment_config: EnvironmentConfig | None = Field(
        default=None, description="Reverse view for EnvironmentConfig.session_configs"
    )

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
