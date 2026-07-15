from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from aware_meta.materialization.contracts import MaterializationLaneContext

MaterializationStepStatus = Literal["succeeded", "failed"]
MaterializationRunStatus = Literal["succeeded", "failed"]


@dataclass(frozen=True, slots=True)
class MaterializationStepReceipt:
    step_id: str
    step_kind: str
    status: MaterializationStepStatus
    commit_requested: bool
    commit_id: UUID | None
    head_commit_id: UUID | None
    started_at_utc: str
    finished_at_utc: str
    details: Mapping[str, object]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class MaterializationRunReceipt:
    module_id: str
    pipeline_id: str
    lane: MaterializationLaneContext
    status: MaterializationRunStatus
    started_at_utc: str
    finished_at_utc: str
    steps: tuple[MaterializationStepReceipt, ...]


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def encode_materialization_run_receipt(
    *,
    receipt: MaterializationRunReceipt,
) -> dict[str, object]:
    return {
        "module_id": receipt.module_id,
        "pipeline_id": receipt.pipeline_id,
        "lane": {
            "branch_id": str(receipt.lane.branch_id),
            "projection_hash": receipt.lane.projection_hash,
        },
        "status": receipt.status,
        "started_at_utc": receipt.started_at_utc,
        "finished_at_utc": receipt.finished_at_utc,
        "steps": [
            {
                "step_id": step.step_id,
                "step_kind": step.step_kind,
                "status": step.status,
                "commit_requested": step.commit_requested,
                "commit_id": (
                    str(step.commit_id) if step.commit_id is not None else None
                ),
                "head_commit_id": (
                    str(step.head_commit_id)
                    if step.head_commit_id is not None
                    else None
                ),
                "started_at_utc": step.started_at_utc,
                "finished_at_utc": step.finished_at_utc,
                "details": dict(step.details),
                "error": step.error,
            }
            for step in receipt.steps
        ],
    }


__all__ = [
    "MaterializationRunReceipt",
    "MaterializationRunStatus",
    "MaterializationStepReceipt",
    "MaterializationStepStatus",
    "encode_materialization_run_receipt",
    "utc_now_iso",
]
