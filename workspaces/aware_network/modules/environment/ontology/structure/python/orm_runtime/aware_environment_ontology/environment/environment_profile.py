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
    from aware_environment_ontology.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology.process.process import Process


class EnvironmentProfile(ORMModel):
    """
    Applied Environment profile under a concrete Environment.
    Contract:
    - Reusable OS topology config lives on EnvironmentProfileConfig.
    - This object is the concrete Environment application of that config.
    - Runtime Process instances live here; ProcessConfig is only the reusable key.
    - Runtime sessions are Environment-owned and resolve profile provenance
    through selected Process/Thread paths.
    """

    # Relationships
    profile_config: EnvironmentProfileConfig | None = Field(default=None)
    processes: list[Process] = Field(default_factory=list)

    # Attributes
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_id: UUID = Field(description="Foreign key for Environment.profiles")
    profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfile.profile_config")

    async def create_process(
        self, process_config_id: UUID, key: str, title: str, description: str | None = None
    ) -> Process:
        """
        Instantiate one runtime Process under this applied EnvironmentProfile.

        Contract:
        - EnvironmentProfile owns runtime Process membership.
        - ProcessConfig remains a reusable config portal/key.
        - Runtime identity is `(environment_profile_id via path, process_config_id, key)`.
        """

        payload = {"process_config_id": process_config_id, "key": key, "title": title, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_process", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.process.process import Process

        if isinstance(value, Process):
            return value
        return Process.validate_invocation_value(value)

    @classmethod
    async def build_via_environment(
        cls,
        environment_id: UUID,
        profile_config_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProfile:
        """
        Construct one applied EnvironmentProfile under an Environment.

        Contract:
        - Identity is derived from parent Environment path + ProfileConfig.
        - This owns concrete runtime Process membership.
        - It does not own process/thread/session reusable config topology.
        - It links concrete Environment runtime state back to reusable config.
        """

        payload = {
            "environment_id": environment_id,
            "profile_config_id": profile_config_id,
            "title": title,
            "description": description,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProfile):
            return value
        return EnvironmentProfile.validate_invocation_value(value)


class EnvironmentProfileCreateProcessInput(BaseModel):
    process_config_id: UUID
    key: str
    title: str
    description: str | None = Field(default=None)


class EnvironmentProfileCreateProcessOutput(BaseModel):
    value: Process


class EnvironmentProfileBuildViaEnvironmentInput(BaseModel):
    environment_id: UUID = Field(description="Foreign key for Environment.profiles")
    profile_config_id: UUID
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProfileBuildViaEnvironmentOutput(BaseModel):
    value: EnvironmentProfile


FUNCTIONS = {
    "EnvironmentProfile": {
        "create_process": {
            "canonical": {
                "name": "create_process",
                "description": "Instantiate one runtime Process under this applied EnvironmentProfile.\n\nContract:\n- EnvironmentProfile owns runtime Process membership.\n- ProcessConfig remains a reusable config portal/key.\n- Runtime identity is `(environment_profile_id via path, process_config_id, key)`.",
                "is_constructor": False,
            },
            "input": EnvironmentProfileCreateProcessInput,
            "output": EnvironmentProfileCreateProcessOutput,
        },
        "build_via_environment": {
            "canonical": {
                "name": "build_via_environment",
                "description": "Construct one applied EnvironmentProfile under an Environment.\n\nContract:\n- Identity is derived from parent Environment path + ProfileConfig.\n- This owns concrete runtime Process membership.\n- It does not own process/thread/session reusable config topology.\n- It links concrete Environment runtime state back to reusable config.",
                "is_constructor": True,
            },
            "input": EnvironmentProfileBuildViaEnvironmentInput,
            "output": EnvironmentProfileBuildViaEnvironmentOutput,
        },
    },
}

__all__ = [
    "EnvironmentProfile",
    "EnvironmentProfileCreateProcessInput",
    "EnvironmentProfileCreateProcessOutput",
    "EnvironmentProfileBuildViaEnvironmentInput",
    "EnvironmentProfileBuildViaEnvironmentOutput",
    "FUNCTIONS",
]
