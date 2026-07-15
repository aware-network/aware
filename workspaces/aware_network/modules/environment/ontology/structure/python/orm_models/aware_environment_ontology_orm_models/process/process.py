from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Environment Ontology Orm Models
from aware_environment_ontology_orm_models.priority.priority_enums import PriorityLevel
from aware_environment_ontology_orm_models.process.process_enums import ProcessStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.chain.content_chain import ContentChain
    from aware_content_ontology_orm_models.content.content import Content
    from aware_environment_ontology_orm_models.process.process_config import ProcessConfig
    from aware_environment_ontology_orm_models.thread.thread import Thread
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_storage_ontology_orm_models.blob.storage_blob import StorageBlob


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
