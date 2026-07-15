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
    from aware_content_ontology.chain.content_chain import ContentChain
    from aware_content_ontology.content.content import Content
    from aware_environment_ontology.thread.thread_config import ThreadConfig
    from aware_environment_ontology.thread.thread_layout import ThreadLayout
    from aware_environment_ontology.thread.thread_object_instance_graph_branch import ThreadObjectInstanceGraphBranch
    from aware_storage_ontology.blob.storage_blob import StorageBlob


class ActorDirectoryEntry(BaseModel):
    # Attributes
    actor_id: UUID
    identity_id: UUID


class ActorDirectoryResponse(BaseModel):
    # Attributes
    entries: list[ActorDirectoryEntry] = Field(default_factory=list)


class Thread(ORMModel):
    # Relationships
    parent: Thread | None = Field(default=None, exclude=True)
    thread_config: ThreadConfig | None = Field(
        default=None,
        description="Reusable ThreadConfig this runtime Thread instantiates.\nContract:\n- ThreadConfig is a reusable key/config portal.\n- Process owns runtime Thread containment through the parent path.",
    )
    image: StorageBlob | None = Field(
        default=None,
        exclude=True,
        description="Optional territory image override for this thread.\nFallback guidance:\n- If unset, UI should resolve via parent ThreadConfig image/profile context.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    overview_content: Content | None = Field(default=None)
    backlog_chain: ContentChain | None = Field(default=None, exclude=True)
    thread_layouts: list[ThreadLayout] = Field(
        default_factory=list,
        description="Canonical layout portal for attention-owned section/focus resolution.\nContract:\n- Thread stores layout attachments as orchestration context.\n- Attention session/layout/section/focus transition owns active focus semantics.\n- Active layout selection is session/navigation scoped, not a Thread property.",
    )
    thread_object_instance_graph_branches: list[ThreadObjectInstanceGraphBranch] = Field(default_factory=list)

    # Attributes
    key: str
    description: str | None = Field(default=None)
    is_main: bool = Field(default=False)
    title: str | None = Field(default=None)

    # Foreign Keys
    process_id: UUID = Field(description="Foreign key for Process.threads")
    parent_id: UUID | None = Field(default=None, description="Foreign key for Thread.parent")
    thread_config_id: UUID = Field(description="Foreign key for Thread.thread_config")
    image_id: UUID | None = Field(default=None, description="Foreign key for Thread.image")
    overview_content_id: UUID | None = Field(default=None, description="Foreign key for Thread.overview_content")
    backlog_chain_id: UUID | None = Field(default=None, description="Foreign key for Thread.backlog_chain")

    async def attach_lane(
        self, domain_branch_id: UUID, projection_hash: str, title: str | None = None, is_active: bool = True
    ) -> ThreadObjectInstanceGraphBranch:
        """
        Attach an existing domain lane (branch_id, projection_hash) to this Thread.

        Canonical v0 intent:
        - Enables cross-environment reuse of global lanes (e.g. Identity) without copying commits.
        - OS lane commit only: does not create or mutate domain commits; commits are always SSOT.
        - Idempotent: safe to call multiple times for the same lane.
        """

        payload = {
            "domain_branch_id": domain_branch_id,
            "projection_hash": projection_hash,
            "title": title,
            "is_active": is_active,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_lane", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_object_instance_graph_branch import (
            ThreadObjectInstanceGraphBranch,
        )

        if isinstance(value, ThreadObjectInstanceGraphBranch):
            return value
        return ThreadObjectInstanceGraphBranch.validate_invocation_value(value)

    async def add_layout(self, layout_id: UUID, key: str | None = None) -> ThreadLayout:
        """
        Register a Layout for this Thread via canonical ThreadLayout association.

        Contract:
        - Uses parent->child propagation (`construct thread_layouts.create(...)`) so child identity derives
        from `_via_thread_layouts` + `layout_id`.
        - Idempotent for repeated parent/layout pairs.
        """

        payload = {"layout_id": layout_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="add_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.thread.thread_layout import ThreadLayout

        if isinstance(value, ThreadLayout):
            return value
        return ThreadLayout.validate_invocation_value(value)

    async def update_picture(
        self,
        image_id: UUID | None = None,
        image_sha: str | None = None,
        image_mime_type: str | None = None,
        image_size_bytes: int | None = None,
    ) -> None:
        """
        Updates (or clears) the thread territory image override.

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
    async def build_via_process(
        cls,
        process_id: UUID,
        thread_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        is_main: bool = False,
    ) -> Thread:
        """
        Create a runtime Thread under a Process.

        Contract:
        - Parent Process context is propagated by constructor lowering.
        - ThreadConfig is a reusable config portal/key.
        - Runtime identity is `(process_id via path, thread_config_id, key)`.
        """

        payload = {
            "process_id": process_id,
            "thread_config_id": thread_config_id,
            "key": key,
            "title": title,
            "description": description,
            "is_main": is_main,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_process", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Thread):
            return value
        return Thread.validate_invocation_value(value)


class ThreadAttachLaneInput(BaseModel):
    domain_branch_id: UUID
    projection_hash: str
    title: str | None = Field(default=None)
    is_active: bool = Field(default=True)


class ThreadAttachLaneOutput(BaseModel):
    value: ThreadObjectInstanceGraphBranch


class ThreadAddLayoutInput(BaseModel):
    layout_id: UUID
    key: str | None = Field(default=None)


class ThreadAddLayoutOutput(BaseModel):
    value: ThreadLayout


class ThreadUpdatePictureInput(BaseModel):
    image_id: UUID | None = Field(default=None)
    image_sha: str | None = Field(default=None)
    image_mime_type: str | None = Field(default=None)
    image_size_bytes: int | None = Field(default=None)


class ThreadUpdatePictureOutput(BaseModel):
    pass


class ThreadBuildViaProcessInput(BaseModel):
    process_id: UUID = Field(description="Foreign key for Process.threads")
    thread_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_main: bool = Field(default=False)


class ThreadBuildViaProcessOutput(BaseModel):
    value: Thread


FUNCTIONS = {
    "Thread": {
        "attach_lane": {
            "canonical": {
                "name": "attach_lane",
                "description": "Attach an existing domain lane (branch_id, projection_hash) to this Thread.\n\nCanonical v0 intent:\n- Enables cross-environment reuse of global lanes (e.g. Identity) without copying commits.\n- OS lane commit only: does not create or mutate domain commits; commits are always SSOT.\n- Idempotent: safe to call multiple times for the same lane.",
                "is_constructor": False,
            },
            "input": ThreadAttachLaneInput,
            "output": ThreadAttachLaneOutput,
        },
        "add_layout": {
            "canonical": {
                "name": "add_layout",
                "description": "Register a Layout for this Thread via canonical ThreadLayout association.\n\nContract:\n- Uses parent->child propagation (`construct thread_layouts.create(...)`) so child identity derives from `_via_thread_layouts` + `layout_id`.\n- Idempotent for repeated parent/layout pairs.",
                "is_constructor": False,
            },
            "input": ThreadAddLayoutInput,
            "output": ThreadAddLayoutOutput,
        },
        "update_picture": {
            "canonical": {
                "name": "update_picture",
                "description": "Updates (or clears) the thread territory image override.\n\nContract:\n- Raw bytes are uploaded out-of-band via HTTP file operations.\n- Commits must reference commit-backed StorageBlob metadata only.\n- When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.\n\nParameters:\n    image_id: Optional uploaded blob id to assert against image_sha-derived stable id.\n    image_sha: SHA-256 hex digest of uploaded bytes.\n    image_mime_type: MIME type of uploaded bytes.\n    image_size_bytes: Size of uploaded bytes.\nReturns: None.",
                "is_constructor": False,
            },
            "input": ThreadUpdatePictureInput,
            "output": ThreadUpdatePictureOutput,
        },
        "build_via_process": {
            "canonical": {
                "name": "build_via_process",
                "description": "Create a runtime Thread under a Process.\n\nContract:\n- Parent Process context is propagated by constructor lowering.\n- ThreadConfig is a reusable config portal/key.\n- Runtime identity is `(process_id via path, thread_config_id, key)`.",
                "is_constructor": True,
            },
            "input": ThreadBuildViaProcessInput,
            "output": ThreadBuildViaProcessOutput,
        },
    },
}

__all__ = [
    "Thread",
    "ThreadAttachLaneInput",
    "ThreadAttachLaneOutput",
    "ThreadAddLayoutInput",
    "ThreadAddLayoutOutput",
    "ThreadUpdatePictureInput",
    "ThreadUpdatePictureOutput",
    "ThreadBuildViaProcessInput",
    "ThreadBuildViaProcessOutput",
    "FUNCTIONS",
]
