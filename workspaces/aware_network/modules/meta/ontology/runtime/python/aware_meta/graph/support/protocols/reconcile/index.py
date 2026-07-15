"""Graph Reconciler index."""

from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GraphReconcilerIndex:
    """Graph Reconciler index containing stable ID map and seen IDs."""

    stable_id_map: dict[UUID, UUID]
    seen_ids: set[UUID]
