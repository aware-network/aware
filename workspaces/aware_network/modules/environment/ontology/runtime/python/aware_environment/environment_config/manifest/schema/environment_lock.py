"""Environment lock schema (v1).

This is a compiler-owned artifact that pins a composed environment ("kernel") to a deterministic
set of module lane pointers.

Goal:
- allow a clean "genesis" declaration for a composed environment
- ensure runtime can validate that all required commit rails exist on disk before boot
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .environment_manifest import EnvironmentDescriptor


class EnvironmentLanePointer(BaseModel):
    """Honest pointer into `.aware/oig/**` (branch + projection + commit)."""

    branch_id: UUID = Field(
        ..., description="Lane branch_id (usually environment_config_id)"
    )
    projection_hash: str = Field(..., description="Lane projection_hash (OPG hash)")
    commit_id: UUID = Field(..., description="Pinned commit id (must exist on disk)")


class EnvironmentLockModule(BaseModel):
    """Pinned module entry in a composed environment lock."""

    module_id: str = Field(..., description="Module id (modules/<id>/...)")
    manifest_path: str = Field(
        ...,
        description=(
            "Path to the module environment.manifest.json used by composition. "
            "Relative paths resolve against the repo root."
        ),
    )
    package_name: str = Field(
        ..., description="Package name from the module aware.lock root entry"
    )
    version_number: int | None = Field(
        default=None, description="Optional package version number"
    )
    ocg_hash: str = Field(..., description="Module canonical OCG hash from aware.lock")
    ocg_lane: EnvironmentLanePointer = Field(
        ..., description="Pinned OCG lane pointer for this module"
    )


class EnvironmentLock(BaseModel):
    """Top-level environment lock definition."""

    v: int = Field(default=1, description="Schema version")
    built_at: datetime = Field(..., description="Timestamp when the lock was generated")
    environment: EnvironmentDescriptor = Field(
        ..., description="Environment descriptor"
    )
    ocg_hash: str = Field(
        ..., description="Composed environment hash (must match composition manifest)"
    )
    ocg_lane: EnvironmentLanePointer = Field(
        ..., description="Pinned composed OCG lane pointer (genesis)"
    )
    modules: list[EnvironmentLockModule] = Field(
        default_factory=list, description="Pinned module set (deterministic order)"
    )


__all__ = [
    "EnvironmentLanePointer",
    "EnvironmentLock",
    "EnvironmentLockModule",
]
