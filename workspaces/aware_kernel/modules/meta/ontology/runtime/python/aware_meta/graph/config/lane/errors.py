from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


class OcgSeedError(RuntimeError):
    pass


class GraphIdentitySeedError(RuntimeError):
    pass


class OcgLaneCommitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OcgLaneHeadPreHashMismatchDetails:
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID | None
    head_graph_hash_post: str
    graph_hash_pre_raw: str
    graph_hash_pre: str
    graph_hash_post: str
    previous_ocg_supplied: bool
    source_error_type: str

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "head_commit_id": (None if self.head_commit_id is None else str(self.head_commit_id)),
            "head_graph_hash_post": self.head_graph_hash_post,
            "graph_hash_pre_raw": self.graph_hash_pre_raw,
            "graph_hash_pre": self.graph_hash_pre,
            "graph_hash_post": self.graph_hash_post,
            "previous_ocg_supplied": self.previous_ocg_supplied,
            "source_error_type": self.source_error_type,
        }


class OcgLaneHeadPreHashMismatchError(OcgLaneCommitError):
    details: OcgLaneHeadPreHashMismatchDetails

    def __init__(self, *, details: OcgLaneHeadPreHashMismatchDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: OcgLaneHeadPreHashMismatchDetails) -> str:
        return (
            "OCG lane HEAD/pre-hash mismatch (compiler session out of sync with lane HEAD): "
            f"head_graph_hash_post={details.head_graph_hash_post} "
            f"graph_hash_pre_raw={details.graph_hash_pre_raw} "
            f"graph_hash_pre={details.graph_hash_pre} "
            f"graph_hash_post={details.graph_hash_post} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"head_commit_id={details.head_commit_id} "
            f"previous_ocg_supplied={details.previous_ocg_supplied}"
        )


@dataclass(frozen=True, slots=True)
class OcgLaneHashContractDriftDetails:
    branch_id: UUID
    projection_hash: str
    object_instance_graph_id: UUID
    head_commit_id: UUID | None
    head_graph_hash_post: str | None
    graph_hash_pre_raw: str
    graph_hash_pre: str
    graph_hash_post: str
    lane_hash: str
    raw_hash: str
    previous_ocg_supplied: bool
    source_error_type: str

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "object_instance_graph_id": str(self.object_instance_graph_id),
            "head_commit_id": (None if self.head_commit_id is None else str(self.head_commit_id)),
            "head_graph_hash_post": self.head_graph_hash_post,
            "graph_hash_pre_raw": self.graph_hash_pre_raw,
            "graph_hash_pre": self.graph_hash_pre,
            "graph_hash_post": self.graph_hash_post,
            "lane_hash": self.lane_hash,
            "raw_hash": self.raw_hash,
            "previous_ocg_supplied": self.previous_ocg_supplied,
            "source_error_type": self.source_error_type,
        }


class OcgLaneHashContractDriftError(OcgLaneCommitError):
    details: OcgLaneHashContractDriftDetails

    def __init__(self, *, details: OcgLaneHashContractDriftDetails) -> None:
        self.details = details
        super().__init__(self._build_message(details))

    @staticmethod
    def _build_message(details: OcgLaneHashContractDriftDetails) -> str:
        return (
            "OCG lane hash contract drift: "
            f"lane_hash={details.lane_hash} raw_hash={details.raw_hash} "
            f"graph_hash_pre={details.graph_hash_pre} "
            f"graph_hash_pre_raw={details.graph_hash_pre_raw} "
            f"graph_hash_post={details.graph_hash_post} "
            f"branch_id={details.branch_id} projection_hash={details.projection_hash} "
            f"head_commit_id={details.head_commit_id} "
            f"head_graph_hash_post={details.head_graph_hash_post} "
            f"object_instance_graph_id={details.object_instance_graph_id} "
            f"previous_ocg_supplied={details.previous_ocg_supplied}"
        )


__all__ = [
    "GraphIdentitySeedError",
    "OcgLaneCommitError",
    "OcgLaneHashContractDriftDetails",
    "OcgLaneHashContractDriftError",
    "OcgLaneHeadPreHashMismatchDetails",
    "OcgLaneHeadPreHashMismatchError",
    "OcgSeedError",
]
