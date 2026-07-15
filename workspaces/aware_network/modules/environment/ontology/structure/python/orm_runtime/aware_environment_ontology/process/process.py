from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Environment Ontology
from aware_environment_ontology.priority.priority_enums import PriorityLevel
from aware_environment_ontology.process.process_enums import ProcessStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_content_ontology.chain.content_chain import ContentChain
    from aware_content_ontology.content.content import Content
    from aware_environment_ontology.process.process_config import ProcessConfig
    from aware_environment_ontology.thread.thread import Thread
    from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class Process(ORMModel):
    # Relationships
    parent: Process | None = Field(default=None, exclude=True)
    process_config: ProcessConfig | None = Field(
        default=None,
        description="Reusable ProcessConfig this runtime Process instantiates.\nContract:\n- ProcessConfig is a reusable key/config portal.\n- EnvironmentProfile owns runtime Process containment.",
    )
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional territory image override for this process.\nFallback guidance:\n- If unset, UI should resolve via parent ProcessConfig image/profile context.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    object_instance_graphs: list[ObjectInstanceGraph] = Field(default_factory=list, exclude=True)
    overview_content: Content | None = Field(default=None, exclude=True)
    backlog_chain: ContentChain | None = Field(default=None, exclude=True)
    threads: list[Thread] = Field(
        default_factory=list,
        description="Runtime Thread instances under this Process.\nContract:\n- Process owns concrete Thread containment.\n- ThreadConfig remains a reusable key/config portal.",
    )

    # Attributes
    key: str
    description: str | None = Field(default=None)
    priority_level: PriorityLevel = Field(default=PriorityLevel.medium)
    status: ProcessStatus = Field(default=ProcessStatus.pending)
    title: str

    # Foreign Keys
    environment_profile_id: UUID = Field(description="Foreign key for EnvironmentProfile.processes")
    parent_id: UUID | None = Field(default=None, description="Foreign key for Process.parent")
    process_config_id: UUID = Field(description="Foreign key for Process.process_config")
    image_id: UUID | None = Field(default=None, description="Foreign key for Process.image")
    overview_content_id: UUID | None = Field(default=None, description="Foreign key for Process.overview_content")
    backlog_chain_id: UUID | None = Field(default=None, description="Foreign key for Process.backlog_chain")

    async def create_thread(
        self,
        thread_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        is_main: bool = False,
    ) -> Thread:
        """
        Instantiate one runtime Thread under this Process.

        Contract:
        - Process owns runtime Thread membership.
        - ThreadConfig remains a reusable config portal/key.
        - Runtime identity is `(process_id via path, thread_config_id, key)`.
        """

        payload = {
            "thread_config_id": thread_config_id,
            "key": key,
            "title": title,
            "description": description,
            "is_main": is_main,
        }
        result = await invoke_instance(orm_model=self, function_name="create_thread", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread import Thread

        if isinstance(value, Thread):
            return value
        return Thread.validate_invocation_value(value)

    async def update_picture(
        self,
        image_id: UUID | None = None,
        image_sha: str | None = None,
        image_mime_type: str | None = None,
        image_size_bytes: int | None = None,
    ) -> None:
        """
        Updates (or clears) the process territory image override.

        Contract:
        - Raw bytes are uploaded out-of-band via HTTP file operations.
        - Commits must reference commit-backed StorageBlob metadata only.
        - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.

        Parameters:
            image_id: Optional uploaded blob id to assert against image_sha-derived stable id.
            image_sha: SHA-256 hex digest of uploaded bytes.
            image_mime_type: MIME type of uploaded bytes.
            image_size_bytes: Size of uploaded bytes.
        Returns: None.
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
    async def build_via_environment_profile(
        cls, environment_profile_id: UUID, process_config_id: UUID, key: str, title: str, description: str | None = None
    ) -> Process:
        """
        Create a runtime Process under an EnvironmentProfile.

        Contract:
        - Parent EnvironmentProfile context is propagated by constructor lowering.
        - ProcessConfig is a reusable config portal/key.
        - Runtime identity is `(environment_profile_id via path, process_config_id, key)`.
        """

        payload = {
            "environment_profile_id": environment_profile_id,
            "process_config_id": process_config_id,
            "key": key,
            "title": title,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Process):
            return value
        return Process.validate_invocation_value(value)


class ProcessCreateThreadInput(BaseModel):
    thread_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_main: bool = Field(default=False)


class ProcessCreateThreadOutput(BaseModel):
    value: Thread


class ProcessUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class ProcessUpdatePictureOutput(BaseModel):
    pass


class ProcessBuildViaEnvironmentProfileInput(BaseModel):
    environment_profile_id: UUID = Field(description="Foreign key for EnvironmentProfile.processes")
    process_config_id: UUID
    key: str
    title: str
    description: str | None = Field(default=None)


class ProcessBuildViaEnvironmentProfileOutput(BaseModel):
    value: Process


FUNCTIONS = {
    "Process": {
        "create_thread": {
            "canonical": {
                "name": "create_thread",
                "description": "Instantiate one runtime Thread under this Process.\n\nContract:\n- Process owns runtime Thread membership.\n- ThreadConfig remains a reusable config portal/key.\n- Runtime identity is `(process_id via path, thread_config_id, key)`.",
                "is_constructor": False,
            },
            "input": ProcessCreateThreadInput,
            "output": ProcessCreateThreadOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the process territory image override.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.\n\nParameters:\n    image_id: Optional uploaded blob id to assert against image_sha-derived stable id.\n    image_sha: SHA-256 hex digest of uploaded bytes.\n    image_mime_type: MIME type of uploaded bytes.\n    image_size_bytes: Size of uploaded bytes.\nReturns: None.",
                "is_constructor": False,
            },
            "input": ProcessUpdatePictureInput,
            "output": ProcessUpdatePictureOutput,
        },
        "build_via_environment_profile": {
            "canonical": {
                "name": "build_via_environment_profile",
                "description": "Create a runtime Process under an EnvironmentProfile.\n\nContract:\n- Parent EnvironmentProfile context is propagated by constructor lowering.\n- ProcessConfig is a reusable config portal/key.\n- Runtime identity is `(environment_profile_id via path, process_config_id, key)`.",
                "is_constructor": True,
            },
            "input": ProcessBuildViaEnvironmentProfileInput,
            "output": ProcessBuildViaEnvironmentProfileOutput,
        },
    },
}

__all__ = [
    "Process",
    "ProcessCreateThreadInput",
    "ProcessCreateThreadOutput",
    "ProcessUpdatePictureInput",
    "ProcessUpdatePictureOutput",
    "ProcessBuildViaEnvironmentProfileInput",
    "ProcessBuildViaEnvironmentProfileOutput",
    "FUNCTIONS",
]
