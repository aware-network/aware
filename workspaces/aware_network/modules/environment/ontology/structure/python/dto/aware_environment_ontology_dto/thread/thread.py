from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.chain.content_chain import ContentChain
    from aware_content_ontology_dto.content.content import Content
    from aware_environment_ontology_dto.thread.thread_config import ThreadConfig
    from aware_environment_ontology_dto.thread.thread_layout import ThreadLayout
    from aware_environment_ontology_dto.thread.thread_object_instance_graph_branch import (
        ThreadObjectInstanceGraphBranch,
    )
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class Thread(BaseModel):
    # Relationships
    parent: Thread | None = Field(default=None)
    thread_config: ThreadConfig | None = Field(
        default=None,
        description="Reusable ThreadConfig this runtime Thread instantiates.\nContract:\n- ThreadConfig is a reusable key/config portal.\n- Process owns runtime Thread containment through the parent path.",
    )
    image: StorageBlob | None = Field(
        default=None,
        description="Optional territory image override for this thread.\nFallback guidance:\n- If unset, UI should resolve via parent ThreadConfig image/profile context.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    overview_content: Content | None = Field(default=None)
    backlog_chain: ContentChain | None = Field(default=None)
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


class ActorDirectoryEntry(BaseModel):
    # Attributes
    actor_id: UUID
    identity_id: UUID


class ActorDirectoryResponse(BaseModel):
    # Attributes
    entries: list[ActorDirectoryEntry] = Field(default_factory=list)
