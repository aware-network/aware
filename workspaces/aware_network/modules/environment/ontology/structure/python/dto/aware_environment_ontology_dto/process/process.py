from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Environment Ontology Dto
from aware_environment_ontology_dto.priority.priority_enums import PriorityLevel
from aware_environment_ontology_dto.process.process_enums import ProcessStatus

if TYPE_CHECKING:
    from aware_content_ontology_dto.chain.content_chain import ContentChain
    from aware_content_ontology_dto.content.content import Content
    from aware_environment_ontology_dto.process.process_config import ProcessConfig
    from aware_environment_ontology_dto.thread.thread import Thread
    from aware_meta_ontology_dto.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class Process(BaseModel):
    # Relationships
    parent: Process | None = Field(default=None)
    process_config: ProcessConfig | None = Field(
        default=None,
        description="Reusable ProcessConfig this runtime Process instantiates.\nContract:\n- ProcessConfig is a reusable key/config portal.\n- EnvironmentProfile owns runtime Process containment.",
    )
    image: StorageBlob | None = Field(
        default=None,
        description="Optional territory image override for this process.\nFallback guidance:\n- If unset, UI should resolve via parent ProcessConfig image/profile context.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )
    object_instance_graphs: list[ObjectInstanceGraph] = Field(default_factory=list)
    overview_content: Content | None = Field(default=None)
    backlog_chain: ContentChain | None = Field(default=None)
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
