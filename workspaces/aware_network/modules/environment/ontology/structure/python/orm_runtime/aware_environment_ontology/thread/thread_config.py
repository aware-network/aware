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
    from aware_environment_ontology.thread.thread_config_layout_config import ThreadConfigLayoutConfig
    from aware_environment_ontology.thread.thread_config_object_projection_graph import (
        ThreadConfigObjectProjectionGraph,
    )
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ThreadConfig(ORMModel):
    """
    Environment-owned contextual Thread topology config.
    Contract:
    - Owned by Environment under ProcessConfig.
    - Reusable key/config for runtime Thread instances.
    - Hosts projection graph authority refs and Attention layout configs.
    - Does not reference Experience ProjectionExperience or ProgramConfigGraph.
    """

    # Relationships
    object_projection_graphs: list[ThreadConfigObjectProjectionGraph] = Field(default_factory=list)
    layout_configs: list[ThreadConfigLayoutConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional profile-level image used as the default for Thread instances.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Narrative text for this thread context and workspace flow."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for thread-level decision/routing.")
    state_prompt_template: str | None = Field(
        default=None, description="Declarative prompt template anchor for state-aware thread composition."
    )
    key: str = Field(description="Stable key for thread narrative role (e.g. `main.workspace`, `ops.monitor`).")
    title: str | None = Field(default=None, description="Display label override for thread desktop surfaces.")
    workspace_view_key: str | None = Field(default=None, description="Canonical thread workspace view selector.")
    position: int | None = Field(default=None, description="Ordering hint for thread navigation surfaces.")
    is_default: bool = Field(
        default=False, description="Process-level default thread option for Environment session entrypoints."
    )

    # Foreign Keys
    process_config_id: UUID = Field(description="Foreign key for ProcessConfig.thread_configs")
    image_id: UUID | None = Field(default=None, description="Foreign key for ThreadConfig.image")

    async def add_object_projection_graph(
        self,
        object_projection_graph_id: UUID,
        view_key: str | None = None,
        position: int | None = None,
        is_default: bool = False,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigObjectProjectionGraph:
        """
        Declare one projection graph this ThreadConfig can host.

        Contract:
        - Environment declares projection authority, not Experience ownership.
        - Experience may later bind actions/views over this hosted projection.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "view_key": view_key,
            "position": position,
            "is_default": is_default,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_object_projection_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_config_object_projection_graph import (
            ThreadConfigObjectProjectionGraph,
        )

        if isinstance(value, ThreadConfigObjectProjectionGraph):
            return value
        return ThreadConfigObjectProjectionGraph.validate_invocation_value(value)

    async def add_layout_config(
        self,
        layout_config_id: UUID,
        key: str | None = None,
        position: int | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ThreadConfigLayoutConfig:
        """
        Create a deterministic ThreadConfigLayoutConfig association edge.

        Contract:
        - ThreadConfig declares which Attention LayoutConfig objects this thread offers.
        - Runtime Environment provisioning lowers this config edge into ThreadLayout.
        - Attention owns LayoutConfig/SectionConfig topology and focus state.
        """

        payload = {
            "layout_config_id": layout_config_id,
            "key": key,
            "position": position,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_instance(orm_model=self, function_name="add_layout_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_config_layout_config import ThreadConfigLayoutConfig

        if isinstance(value, ThreadConfigLayoutConfig):
            return value
        return ThreadConfigLayoutConfig.validate_invocation_value(value)

    async def update_picture(
        self,
        image_id: UUID | None = None,
        image_sha: str | None = None,
        image_mime_type: str | None = None,
        image_size_bytes: int | None = None,
    ) -> None:
        """
        Updates (or clears) the thread config image.

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
    async def build_via_process_config(
        cls,
        process_config_id: UUID,
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
        Construct a deterministic ThreadConfig under one ProcessConfig.

        Contract:
        - Identity is derived from ProcessConfig-scoped config keys.
        - Runtime Thread instances are created under Process.
        - Program/action semantics remain Experience-owned.
        """

        payload = {
            "process_config_id": process_config_id,
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
        result = await invoke_constructor(orm_class=cls, function_name="build_via_process_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadConfig):
            return value
        return ThreadConfig.validate_invocation_value(value)


class ThreadConfigAddObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID
    view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigAddObjectProjectionGraphOutput(BaseModel):
    value: ThreadConfigObjectProjectionGraph


class ThreadConfigAddLayoutConfigInput(BaseModel):
    layout_config_id: UUID
    key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ThreadConfigAddLayoutConfigOutput(BaseModel):
    value: ThreadConfigLayoutConfig


class ThreadConfigUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class ThreadConfigUpdatePictureOutput(BaseModel):
    pass


class ThreadConfigBuildViaProcessConfigInput(BaseModel):
    process_config_id: UUID = Field(description="Foreign key for ProcessConfig.thread_configs")
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    workspace_view_key: str | None = Field(default=None)
    position: int | None = Field(default=None)
    is_default: bool = Field(default=False)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    state_prompt_template: str | None = Field(default=None)


class ThreadConfigBuildViaProcessConfigOutput(BaseModel):
    value: ThreadConfig


FUNCTIONS = {
    "ThreadConfig": {
        "add_object_projection_graph": {
            "canonical": {
                "name": "add_object_projection_graph",
                "description": "Declare one projection graph this ThreadConfig can host.\n\nContract:\n- Environment declares projection authority, not Experience ownership.\n- Experience may later bind actions/views over this hosted projection.",
                "is_constructor": False,
            },
            "input": ThreadConfigAddObjectProjectionGraphInput,
            "output": ThreadConfigAddObjectProjectionGraphOutput,
        },
        "add_layout_config": {
            "canonical": {
                "name": "add_layout_config",
                "description": "Create a deterministic ThreadConfigLayoutConfig association edge.\n\nContract:\n- ThreadConfig declares which Attention LayoutConfig objects this thread offers.\n- Runtime Environment provisioning lowers this config edge into ThreadLayout.\n- Attention owns LayoutConfig/SectionConfig topology and focus state.",
                "is_constructor": False,
            },
            "input": ThreadConfigAddLayoutConfigInput,
            "output": ThreadConfigAddLayoutConfigOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the thread config image.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.",
                "is_constructor": False,
            },
            "input": ThreadConfigUpdatePictureInput,
            "output": ThreadConfigUpdatePictureOutput,
        },
        "build_via_process_config": {
            "canonical": {
                "name": "build_via_process_config",
                "description": "Construct a deterministic ThreadConfig under one ProcessConfig.\n\nContract:\n- Identity is derived from ProcessConfig-scoped config keys.\n- Runtime Thread instances are created under Process.\n- Program/action semantics remain Experience-owned.",
                "is_constructor": True,
            },
            "input": ThreadConfigBuildViaProcessConfigInput,
            "output": ThreadConfigBuildViaProcessConfigOutput,
        },
    },
}

__all__ = [
    "ThreadConfig",
    "ThreadConfigAddObjectProjectionGraphInput",
    "ThreadConfigAddObjectProjectionGraphOutput",
    "ThreadConfigAddLayoutConfigInput",
    "ThreadConfigAddLayoutConfigOutput",
    "ThreadConfigUpdatePictureInput",
    "ThreadConfigUpdatePictureOutput",
    "ThreadConfigBuildViaProcessConfigInput",
    "ThreadConfigBuildViaProcessConfigOutput",
    "FUNCTIONS",
]
