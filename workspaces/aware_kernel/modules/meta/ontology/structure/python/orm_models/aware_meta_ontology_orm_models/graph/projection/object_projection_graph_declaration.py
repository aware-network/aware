from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_binding import (
        ObjectProjectionGraphBinding,
    )


class ObjectProjectionGraphDeclaration(ORMModel):
    """
    Compiler-owned, hashable projection declaration attached to an ObjectConfigGraph.
    This is the SSOT for *membership/portal* semantics of a projection:
    - Which canonical classes participate in a projection (root + members)
    - Which members form explicit cross-projection portals (target_projection_name)
    Notes:
    - Projections are declared in `.aware` via `projection { ... }` (grammar-level construct).
    - The compiler resolves type/member references to canonical namespaces and persists the
    resolved bindings here so the runtime can build OPGs deterministically.
    """

    # Relationships
    object_projection_graph_bindings: list[ObjectProjectionGraphBinding] = Field(default_factory=list)

    # Attributes
    key: str = Field(
        description='Stable key for this projection declaration (recommended: "{ocg.fqn_prefix}:{projection_name}").'
    )
    projection_name: str = Field(
        description="Canonical projection identity name (authored projection symbol unless explicitly overridden)."
    )
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_branchable: bool = Field(default=False)

    # Foreign Keys
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_projection_graph_declarations"
    )
