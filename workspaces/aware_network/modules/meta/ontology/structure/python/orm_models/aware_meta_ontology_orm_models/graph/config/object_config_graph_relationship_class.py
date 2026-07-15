from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class ObjectConfigGraphRelationshipClass(ORMModel):
    """One concrete cross-OCG relationship to reference a ClassConfig"""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_config_graph_relationship_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphRelationship.object_config_graph_relationship_classes"
    )
    class_config_id: UUID = Field(description="Foreign key for ObjectConfigGraphRelationshipClass.class_config")
