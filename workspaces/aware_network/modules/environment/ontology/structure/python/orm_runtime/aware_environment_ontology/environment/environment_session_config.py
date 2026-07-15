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
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology.process.process_config import ProcessConfig
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_identity_ontology.session.session_config import SessionConfig


class EnvironmentSessionConfig(ORMModel):
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
        default=None, exclude=True, description="Reverse view for EnvironmentConfig.session_configs"
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

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.session_configs")
    identity_session_config_id: UUID = Field(
        description="Foreign key for EnvironmentSessionConfig.identity_session_config"
    )
    default_profile_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentSessionConfig.default_profile_config"
    )
    default_process_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentSessionConfig.default_process_config"
    )
    default_thread_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentSessionConfig.default_thread_config"
    )

    @classmethod
    async def build_via_environment_config(
        cls,
        environment_config_id: UUID,
        key: str,
        identity_session_config_id: UUID,
        default_profile_config_id: UUID | None = None,
        default_process_config_id: UUID | None = None,
        default_thread_config_id: UUID | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        status: str = "active",
        source_kind: str | None = None,
        source_ref: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentSessionConfig:
        """
        Construct one EnvironmentSessionConfig under an EnvironmentConfig.

        Contract:
        - Stable identity is EnvironmentConfig path + `key`.
        - `identity_session_config_id` resolves the Identity SessionConfig
          portal. It is required and must not be inferred from keys.
        - Optional default profile/process/thread refs are bootstrap defaults
          and must not define runtime session containment.
        - This object never owns actor membership.
        """

        payload = {
            "environment_config_id": environment_config_id,
            "key": key,
            "identity_session_config_id": identity_session_config_id,
            "default_profile_config_id": default_profile_config_id,
            "default_process_config_id": default_process_config_id,
            "default_thread_config_id": default_thread_config_id,
            "title": title,
            "description": description,
            "purpose": purpose,
            "status": status,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentSessionConfig):
            return value
        return EnvironmentSessionConfig.validate_invocation_value(value)


class EnvironmentSessionConfigBuildViaEnvironmentConfigInput(BaseModel):
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.session_configs")
    key: str
    identity_session_config_id: UUID
    default_profile_config_id: UUID | None = Field(default=None)
    default_process_config_id: UUID | None = Field(default=None)
    default_thread_config_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentSessionConfigBuildViaEnvironmentConfigOutput(BaseModel):
    value: EnvironmentSessionConfig


FUNCTIONS = {
    "EnvironmentSessionConfig": {
        "build_via_environment_config": {
            "canonical": {
                "name": "build_via_environment_config",
                "description": "Construct one EnvironmentSessionConfig under an EnvironmentConfig.\n\nContract:\n- Stable identity is EnvironmentConfig path + `key`.\n- `identity_session_config_id` resolves the Identity SessionConfig\n  portal. It is required and must not be inferred from keys.\n- Optional default profile/process/thread refs are bootstrap defaults\n  and must not define runtime session containment.\n- This object never owns actor membership.",
                "is_constructor": True,
            },
            "input": EnvironmentSessionConfigBuildViaEnvironmentConfigInput,
            "output": EnvironmentSessionConfigBuildViaEnvironmentConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentSessionConfig",
    "EnvironmentSessionConfigBuildViaEnvironmentConfigInput",
    "EnvironmentSessionConfigBuildViaEnvironmentConfigOutput",
    "FUNCTIONS",
]
