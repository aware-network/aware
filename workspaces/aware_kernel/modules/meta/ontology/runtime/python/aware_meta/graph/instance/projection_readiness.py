from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.orm_projection_catchup import (
    LaneProjectionCatchupResult,
    MetaOrmProjectionIndex,
    ensure_lane_projection_caught_up,
)
from aware_orm.session.session import Session
from aware_utils.logging import logger

ProjectionReadinessMode = Literal["required_db", "optional_db", "off"]


class ProjectionReadinessModes:
    REQUIRED_DB: ProjectionReadinessMode = "required_db"
    OPTIONAL_DB: ProjectionReadinessMode = "optional_db"
    OFF: ProjectionReadinessMode = "off"


class ProjectionReadinessError(RuntimeError):
    """Raised when a required DB projection cannot be advanced to committed truth."""


@dataclass(frozen=True, slots=True)
class ProjectionReadinessRequirement:
    name: str
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID | None = None
    object_instance_graph_id: UUID | None = None
    mode: ProjectionReadinessMode = ProjectionReadinessModes.REQUIRED_DB
    commit_every: int = 25


@dataclass(frozen=True, slots=True)
class ProjectionReadinessResult:
    requirement: ProjectionReadinessRequirement
    status: Literal["ready", "skipped", "degraded"]
    lane_result: LaneProjectionCatchupResult | None = None
    skipped_reason: str | None = None

    @property
    def commits_applied(self) -> int:
        if self.lane_result is None:
            return 0
        return self.lane_result.commits_applied

    @property
    def head_commit_id(self) -> UUID | None:
        if self.lane_result is None:
            return self.requirement.head_commit_id
        return self.lane_result.head_commit_id

    @property
    def object_instance_graph_id(self) -> UUID | None:
        if self.lane_result is None:
            return self.requirement.object_instance_graph_id
        return self.lane_result.object_instance_graph_id


def _is_backend_skip(reason: str | None) -> bool:
    return bool(reason and reason.startswith("backend:"))


def _normalize_mode(mode: str) -> ProjectionReadinessMode:
    normalized = mode.strip().lower()
    if normalized in {
        ProjectionReadinessModes.REQUIRED_DB,
        ProjectionReadinessModes.OPTIONAL_DB,
        ProjectionReadinessModes.OFF,
    }:
        return normalized  # type: ignore[return-value]
    raise ValueError(f"Unknown projection readiness mode: {mode!r}")


async def ensure_projection_readiness(
    *,
    index: MetaOrmProjectionIndex | Any | None,
    requirement: ProjectionReadinessRequirement,
    commit_store: FSCommitStore | None = None,
    session: Session | None = None,
) -> ProjectionReadinessResult:
    """Advance a committed OIG lane into the DB read model for activation/readiness.

    OIG commits remain source truth. This gate names the activation contract around
    ``ensure_lane_projection_caught_up`` so package startup and ``read_model``
    receipts can share one readiness rule instead of scattering lane-specific
    catch-up helpers.
    """

    mode = _normalize_mode(requirement.mode)
    if mode == ProjectionReadinessModes.OFF:
        return ProjectionReadinessResult(
            requirement=requirement,
            status="skipped",
            skipped_reason="mode:off",
        )
    if index is None:
        raise ProjectionReadinessError(
            "Projection readiness requires a runtime index when mode is not off: "
            f"name={requirement.name!r} branch_id={requirement.branch_id} "
            f"projection_hash={requirement.projection_hash}"
        )

    lane_result = await ensure_lane_projection_caught_up(
        index=index,
        branch_id=requirement.branch_id,
        projection_hash=requirement.projection_hash,
        head_commit_id=requirement.head_commit_id,
        object_instance_graph_id=requirement.object_instance_graph_id,
        commit_store=commit_store,
        session=session or Session(branch_id=requirement.branch_id),
        commit_every=requirement.commit_every,
    )
    if lane_result.skipped_reason:
        if (
            mode == ProjectionReadinessModes.REQUIRED_DB
            and not _is_backend_skip(lane_result.skipped_reason)
        ):
            raise ProjectionReadinessError(
                "Required DB projection readiness was not reached: "
                f"name={requirement.name!r} branch_id={requirement.branch_id} "
                f"projection_hash={requirement.projection_hash} "
                f"head_commit_id={lane_result.head_commit_id} "
                f"reason={lane_result.skipped_reason}"
            )
        status: Literal["skipped", "degraded"] = (
            "skipped" if _is_backend_skip(lane_result.skipped_reason) else "degraded"
        )
        logger.debug(
            "Projection readiness skipped/degraded "
            "name=%s branch_id=%s projection_hash=%s status=%s reason=%s",
            requirement.name,
            requirement.branch_id,
            requirement.projection_hash,
            status,
            lane_result.skipped_reason,
        )
        return ProjectionReadinessResult(
            requirement=requirement,
            status=status,
            lane_result=lane_result,
            skipped_reason=lane_result.skipped_reason,
        )

    if lane_result.commits_applied:
        logger.info(
            "Projection readiness applied committed lane "
            "name=%s branch_id=%s projection_hash=%s commits=%s head_commit_id=%s",
            requirement.name,
            requirement.branch_id,
            requirement.projection_hash,
            lane_result.commits_applied,
            lane_result.head_commit_id,
        )
    return ProjectionReadinessResult(
        requirement=requirement,
        status="ready",
        lane_result=lane_result,
        skipped_reason=None,
    )


__all__ = [
    "ProjectionReadinessError",
    "ProjectionReadinessModes",
    "ProjectionReadinessRequirement",
    "ProjectionReadinessResult",
    "ensure_projection_readiness",
]
