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

if TYPE_CHECKING:
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ProcessConfig(ORMModel):
    """
    Environment-owned process topology config.
    Contract:
    - Owned by Environment under EnvironmentProfileConfig.
    - Reusable key/config for runtime Process instances.
    - Does not reference Experience-owned profile/config classes.
    """

    # Relationships
    thread_configs: list[ThreadConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional profile-level image used as the default for Process instances.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None, description="Narrative text for this continuous process topology.")
    intent: str | None = Field(
        default=None, description="Short canonical intent for process routing and UX composition."
    )
    key: str = Field(description="Stable topology key for this process config.")
    shape: str | None = Field(default=None, description="Optional shape hint for process replication variants.")
    title: str | None = Field(default=None, description="Display label override for desktop surfaces.")
    type: str
    position: int | None = Field(default=None, description="Ordering hint for selectors/home cards.")
    is_default: bool = Field(
        default=False, description="Profile-level default process option for Environment session entrypoints."
    )

    # Foreign Keys
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.process_configs")
    image_id: UUID | None = Field(default=None, description="Foreign key for ProcessConfig.image")

    async def create_thread_config(
        self,
        key: str,
        title: str | None = None,
        description: str | None = None,
        workspace_view_key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
        state_prompt_template: str | None = None,
    ) -> ThreadConfig:
        """
        Create a ThreadConfig under this ProcessConfig.

        Contract:
        - Deterministic identity under this ProcessConfig using config-level keys.
        - Runtime Thread instances are created under Process.
        - Does not carry Experience program/action semantics.
        """

        payload = {
            "key": key,
            "title": title,
            "description": description,
            "workspace_view_key": workspace_view_key,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
            "state_prompt_template": state_prompt_template,
        }
        result = await invoke_instance(orm_model=self, function_name="create_thread_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_config import ThreadConfig

        if isinstance(value, ThreadConfig):
            return value
        return ThreadConfig.validate_invocation_value(value)

    async def update_picture(
        self,
        image_id: UUID | None = None,
        image_sha: str | None = None,
        image_mime_type: str | None = None,
        image_size_bytes: int | None = None,
    ) -> None:
        """
        Updates (or clears) the process config image.

        Contract:
        - Raw bytes are uploaded out-of-band via HTTP file operations.
        - Commits must reference commit-backed StorageBlob metadata only.
        - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.
        """

        payload = {
            "image_id": image_id,
            "image_sha": image_sha,
            "image_mime_type": image_mime_type,
            "image_size_bytes": image_size_bytes,
        }
        await invoke_instance(orm_model=self, function_name="update_picture", payload=payload)
        return None

    @classmethod
    async def build_via_environment_profile_config(
        cls,
        environment_profile_config_id: UUID,
        type: str,
        key: str,
        title: str | None = None,
        description: str | None = None,
        shape: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ProcessConfig:
        """
        Construct a deterministic ProcessConfig under an EnvironmentProfileConfig.

        Contract:
        - Identity is profile-scoped configuration and does not derive from runtime Process.
        - Runtime Process instances are created under EnvironmentProfile.
        """

        payload = {
            "environment_profile_config_id": environment_profile_config_id,
            "type": type,
            "key": key,
            "title": title,
            "description": description,
            "shape": shape,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProcessConfig):
            return value
        return ProcessConfig.validate_invocation_value(value)


class ProcessConfigCreateThreadConfigInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    workspace_view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    state_prompt_template: str | None = Field(default=None)


class ProcessConfigCreateThreadConfigOutput(BaseModel):
    value: ThreadConfig


class ProcessConfigUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class ProcessConfigUpdatePictureOutput(BaseModel):
    pass


class ProcessConfigBuildViaEnvironmentProfileConfigInput(BaseModel):
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.process_configs")
    type: str
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    shape: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ProcessConfigBuildViaEnvironmentProfileConfigOutput(BaseModel):
    value: ProcessConfig


FUNCTIONS = {
    "ProcessConfig": {
        "create_thread_config": {
            "canonical": {
                "name": "create_thread_config",
                "description": "Create a ThreadConfig under this ProcessConfig.\n\nContract:\n- Deterministic identity under this ProcessConfig using config-level keys.\n- Runtime Thread instances are created under Process.\n- Does not carry Experience program/action semantics.",
                "is_constructor": False,
            },
            "input": ProcessConfigCreateThreadConfigInput,
            "output": ProcessConfigCreateThreadConfigOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the process config image.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.",
                "is_constructor": False,
            },
            "input": ProcessConfigUpdatePictureInput,
            "output": ProcessConfigUpdatePictureOutput,
        },
        "build_via_environment_profile_config": {
            "canonical": {
                "name": "build_via_environment_profile_config",
                "description": "Construct a deterministic ProcessConfig under an EnvironmentProfileConfig.\n\nContract:\n- Identity is profile-scoped configuration and does not derive from runtime Process.\n- Runtime Process instances are created under EnvironmentProfile.",
                "is_constructor": True,
            },
            "input": ProcessConfigBuildViaEnvironmentProfileConfigInput,
            "output": ProcessConfigBuildViaEnvironmentProfileConfigOutput,
        },
    },
}

__all__ = [
    "ProcessConfig",
    "ProcessConfigCreateThreadConfigInput",
    "ProcessConfigCreateThreadConfigOutput",
    "ProcessConfigUpdatePictureInput",
    "ProcessConfigUpdatePictureOutput",
    "ProcessConfigBuildViaEnvironmentProfileConfigInput",
    "ProcessConfigBuildViaEnvironmentProfileConfigOutput",
    "FUNCTIONS",
]
