from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EnvironmentNavigationContextViewSpec(BaseModel):
    environment_navigation_context_id: UUID
    environment_session_id: UUID
    environment_id: UUID
    key: str
    title: str | None = None
    status: str = "active"
    is_default: bool = False
    selected_process_id: UUID | None = None
    selected_thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    root_object_id: UUID | None = None
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentNavigationCommitReceiptSpec(BaseModel):
    accepted: bool = False
    status: str
    error: str | None = None
    reason: str | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = None
    key: str | None = None
    is_default: bool = False
    branch_id: UUID | None = None
    projection_hash: str | None = None
    root_object_id: UUID | None = None
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    function_call_id: UUID | None = None
    function_call_response_id: UUID | None = None
    selected_process_id: UUID | None = None
    selected_thread_id: UUID | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentDefaultNavigationContextResolutionSpec(BaseModel):
    context: EnvironmentNavigationContextViewSpec | None = None
    receipt: EnvironmentNavigationCommitReceiptSpec | None = None


__all__ = [
    "EnvironmentDefaultNavigationContextResolutionSpec",
    "EnvironmentNavigationCommitReceiptSpec",
    "EnvironmentNavigationContextViewSpec",
]
