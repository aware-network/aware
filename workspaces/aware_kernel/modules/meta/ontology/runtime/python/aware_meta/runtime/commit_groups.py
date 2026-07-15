from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal
from uuid import UUID


META_INVOCATION_COMMIT_GROUP_CONTRACT_VERSION = (
    "aware.meta.invocation_commit_group.v0"
)
META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY = "independent_append"

MetaInvocationCommitRole = Literal[
    "domain_commit",
    "identity_lane_head_commit",
    "oigi_history_commit",
]


@dataclass(frozen=True, slots=True)
class MetaInvocationCommitGroupEntry:
    role: MetaInvocationCommitRole
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_id: UUID | None = None
    operation_label: str | None = None
    provider_key: str | None = None
    reaction_key: str | None = None
    durability_policy: str = META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "role": self.role,
            "branch_id": str(self.branch_id),
            "projection_hash": self.projection_hash,
            "commit_id": str(self.commit_id),
            "object_instance_graph_commit_id": str(
                self.object_instance_graph_commit_id
            ),
            "durability_policy": self.durability_policy,
        }
        if self.object_instance_graph_identity_id is not None:
            payload["object_instance_graph_identity_id"] = str(
                self.object_instance_graph_identity_id
            )
        if self.object_instance_graph_id is not None:
            payload["object_instance_graph_id"] = str(self.object_instance_graph_id)
        if self.operation_label:
            payload["operation_label"] = self.operation_label
        if self.provider_key:
            payload["provider_key"] = self.provider_key
        if self.reaction_key:
            payload["reaction_key"] = self.reaction_key
        return payload


@dataclass(frozen=True, slots=True)
class MetaInvocationCommitGroupEvidence:
    commit_group_id: str
    entries: tuple[MetaInvocationCommitGroupEntry, ...]
    contract_version: str = META_INVOCATION_COMMIT_GROUP_CONTRACT_VERSION
    durability_policy: str = META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def role_counts(self) -> dict[str, int]:
        return dict(Counter(entry.role for entry in self.entries))

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "commit_group_id": self.commit_group_id,
            "durability_policy": self.durability_policy,
            "entry_count": self.entry_count,
            "role_counts": self.role_counts,
            "entries": [entry.evidence_payload() for entry in self.entries],
        }


def build_meta_invocation_commit_group_evidence(
    *,
    commit_group_id: str,
    entries: tuple[MetaInvocationCommitGroupEntry, ...],
) -> MetaInvocationCommitGroupEvidence | None:
    if not entries:
        return None
    return MetaInvocationCommitGroupEvidence(
        commit_group_id=commit_group_id,
        entries=entries,
    )


__all__ = [
    "META_INVOCATION_COMMIT_GROUP_CONTRACT_VERSION",
    "META_INVOCATION_COMMIT_GROUP_DURABILITY_POLICY",
    "MetaInvocationCommitGroupEntry",
    "MetaInvocationCommitGroupEvidence",
    "MetaInvocationCommitRole",
    "build_meta_invocation_commit_group_evidence",
]
