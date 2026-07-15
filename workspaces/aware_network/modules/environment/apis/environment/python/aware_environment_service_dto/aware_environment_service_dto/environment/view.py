from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class EnvironmentStatusBlockSummaryV1(BaseModel):
    """
    API-owned view-state contracts for Environment navigation surfaces.
    Public API view keys:
    - environment.navigator
    - environment.process_workspace
    - environment.thread_layout
    """

    # Attributes
    name: str
    available: bool = Field(default=True)
    authority_kind: str | None = Field(default=None)
    unavailable_reason: str | None = Field(default=None)
    payload: JsonObject = Field(default_factory=JsonObject)


class EnvironmentThreadNavigationItemV1(BaseModel):
    # Attributes
    thread_id: UUID | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    title: str = Field(default="Thread")
    description: str | None = Field(default=None)
    attachment_count: int = Field(default=0)
    active_attachment_count: int = Field(default=0)
    is_selected: bool = Field(default=False)


class EnvironmentProcessNavigationItemV1(BaseModel):
    # Attributes
    process_id: UUID | None = Field(default=None)
    process_key: str | None = Field(default=None)
    title: str = Field(default="Process")
    description: str | None = Field(default=None)
    thread_count: int = Field(default=0)
    is_selected: bool = Field(default=False)
    threads: list[EnvironmentThreadNavigationItemV1] = Field(default_factory=list)


class EnvironmentNavigatorViewStateV1(BaseModel):
    # Attributes
    environment_id: UUID | None = Field(default=None)
    title: str = Field(default="Environment")
    status: str = Field(default="waiting")
    ready: bool = Field(default=False)
    selected_process_id: UUID | None = Field(default=None)
    selected_process_key: str | None = Field(default=None)
    selected_thread_id: UUID | None = Field(default=None)
    selected_thread_key: str | None = Field(default=None)
    processes: list[EnvironmentProcessNavigationItemV1] = Field(default_factory=list)
    status_blocks: list[EnvironmentStatusBlockSummaryV1] = Field(default_factory=list)
    empty_message: str = Field(default="No environment topology available")
    provenance: JsonObject = Field(default_factory=JsonObject)


class ProcessWorkspaceThreadViewStateV1(BaseModel):
    # Attributes
    thread_id: UUID | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    title: str = Field(default="Thread")
    description: str | None = Field(default=None)
    attachment_count: int = Field(default=0)
    active_attachment_count: int = Field(default=0)
    lane_count: int = Field(default=0)
    layout_count: int = Field(default=0)
    is_selected: bool = Field(default=False)


class ProcessWorkspaceViewStateV1(BaseModel):
    # Attributes
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    process_key: str | None = Field(default=None)
    title: str = Field(default="Process")
    description: str | None = Field(default=None)
    status: str = Field(default="waiting")
    selected_thread_id: UUID | None = Field(default=None)
    selected_thread_key: str | None = Field(default=None)
    threads: list[ProcessWorkspaceThreadViewStateV1] = Field(default_factory=list)
    empty_message: str = Field(default="No threads available")
    provenance: JsonObject = Field(default_factory=JsonObject)


class ThreadLayoutLaneViewStateV1(BaseModel):
    # Attributes
    lane_hash: str
    opg_id: UUID | None = Field(default=None)
    opg_name: str | None = Field(default=None)


class ThreadLayoutAttachmentViewStateV1(BaseModel):
    # Attributes
    attachment_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    object_instance_graph_identity_id: UUID | None = Field(default=None)
    domain_branch_id: UUID | None = Field(default=None)
    lanes: list[ThreadLayoutLaneViewStateV1] = Field(default_factory=list)


class ThreadLayoutSectionViewStateV1(BaseModel):
    # Attributes
    section_key: str
    title: str = Field(default="Section")
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)
    focus_scope_id: UUID | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    view_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    pane_key: str | None = Field(default=None)


class ThreadLayoutCandidateViewStateV1(BaseModel):
    # Attributes
    layout_id: UUID | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    title: str = Field(default="Layout")
    description: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    sections: list[ThreadLayoutSectionViewStateV1] = Field(default_factory=list)


class ThreadLayoutViewStateV1(BaseModel):
    # Attributes
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    process_key: str | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    thread_key: str | None = Field(default=None)
    title: str = Field(default="Thread")
    description: str | None = Field(default=None)
    status: str = Field(default="waiting")
    active_layout_id: UUID | None = Field(default=None)
    active_layout_key: str | None = Field(default=None)
    layouts: list[ThreadLayoutCandidateViewStateV1] = Field(default_factory=list)
    sections: list[ThreadLayoutSectionViewStateV1] = Field(default_factory=list)
    attachments: list[ThreadLayoutAttachmentViewStateV1] = Field(default_factory=list)
    empty_message: str = Field(default="No thread layout available")
    provenance: JsonObject = Field(default_factory=JsonObject)
