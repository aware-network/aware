"""Generic graph reconciler implementation."""

from __future__ import annotations

import uuid
from typing import Any, Generic
from uuid import UUID

from aware_meta.graph.support.member import GraphMember, T_Kind

# Fingerprint
from aware_meta.graph.support.protocols.reconcile.fingerprint import (
    FingerprintContext,
    fingerprint,
)

# Index
from aware_meta.graph.support.protocols.reconcile.index import GraphReconcilerIndex


class GraphReconciler(Generic[T_Kind]):
    """
    Generic reconciler that relies only on the GraphMember protocol.
    """

    def __init__(self, index: GraphReconcilerIndex):
        """Initialize reconciler with index."""
        self.index = index

    def same(
        self,
        a: Any,
        b: Any,
        context: FingerprintContext = FingerprintContext.RECONCILIATION,
    ) -> bool:
        """
        Compare two entities for equality.

        Args:
            a: First entity
            b: Second entity
            context: The context for comparison:
                - RECONCILIATION: For entity identity matching (uses only path_key)
                - CONTENT: For content comparison (uses all mutable fields)

        Returns:
            True if the entities are equivalent in the given context
        """
        return fingerprint(a, context) == fingerprint(b, context)

    def get_stable_id(self, entity: Any) -> UUID:
        """Get a stable ID for the given entity."""
        # Check if we have a mapping for this new entity
        if isinstance(entity, GraphMember):
            entity_obj_id = entity.get_id()
        else:
            # Fallback for legacy callers that pass raw ORM entities
            entity_obj_id = getattr(entity, "id", None)

        if entity_obj_id is None:
            raise ValueError(f"Entity {entity!r} has no ID")

        if entity_obj_id in self.index.stable_id_map:
            return self.index.stable_id_map[entity_obj_id]

        # Otherwise return the entity's own ID
        return entity_obj_id

    def new_id(self) -> UUID:
        """Generate a fresh, collision-free ID."""
        new_id = uuid.uuid4()
        while new_id in self.index.seen_ids:
            new_id = uuid.uuid4()
        self.index.seen_ids.add(new_id)
        return new_id
