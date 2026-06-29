"""Small transport context DTO shared by endpoint-invocation callers."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AwareApiContext(BaseModel):
    """Runtime lane context carried by callers that already know their session."""

    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)


__all__ = ["AwareApiContext"]
