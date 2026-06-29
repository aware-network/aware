from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ObjectProjectionGraphBinding(ORMModel):
    """
    Resolved binding between a projection declaration and a canonical class (and optionally member).
    Contract:
    - Root membership is expressed by `attribute_name == null`.
    - Member membership is expressed by `attribute_name != null`.
    - Portal relationships are expressed by `target_projection_name != null`.
    """

    # Attributes
    fqn_prefix: str
    namespace: str
    class_name: str
    attribute_name: str | None = Field(default=None)
    target_projection_name: str | None = Field(
        default=None,
        description='Target projection reference (canonical authored identity, e.g. "Focus" or "aware_identity.Identity").',
    )
    side: str | None = Field(default=None)

    # Foreign Keys
    object_projection_graph_declaration_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphDeclaration.object_projection_graph_bindings"
    )


FUNCTIONS = {
    "ObjectProjectionGraphBinding": {},
}

__all__ = [
    "ObjectProjectionGraphBinding",
    "FUNCTIONS",
]
