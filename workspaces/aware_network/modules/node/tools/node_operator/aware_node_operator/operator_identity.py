"""Stable Network identity for one Workspace deployment Node process."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_network_ontology.stable_ids import stable_network_node_id


@dataclass(frozen=True, slots=True)
class OperatorNodeIdentity:
    node_id: UUID
    public_key: str


def stable_operator_node_identity(
    *,
    workspace_revision_id: UUID,
    node_package: str,
) -> OperatorNodeIdentity:
    normalized_package = node_package.casefold().strip()
    public_key = (
        "dev:workspace-deployment:" f"{workspace_revision_id}:node:{normalized_package}"
    )
    return OperatorNodeIdentity(
        node_id=stable_network_node_id(public_key=public_key),
        public_key=public_key,
    )


__all__ = ["OperatorNodeIdentity", "stable_operator_node_identity"]
