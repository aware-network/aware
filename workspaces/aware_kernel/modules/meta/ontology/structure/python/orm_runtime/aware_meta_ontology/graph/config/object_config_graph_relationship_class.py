from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig


class ObjectConfigGraphRelationshipClass(ORMModel):
    """One concrete cross-OCG relationship to reference a ClassConfig"""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    object_config_graph_relationship_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphRelationship.object_config_graph_relationship_classes"
    )
    class_config_id: UUID = Field(description="Foreign key for ObjectConfigGraphRelationshipClass.class_config")

    @classmethod
    async def build_via_object_config_graph_relationship(
        cls, object_config_graph_relationship_id: UUID, class_config_id: UUID
    ) -> ObjectConfigGraphRelationshipClass:
        """Build deterministic ObjectConfigGraphRelationshipClass within a relationship scope."""

        payload = {
            "object_config_graph_relationship_id": object_config_graph_relationship_id,
            "class_config_id": class_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_config_graph_relationship", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphRelationshipClass):
            return value
        return ObjectConfigGraphRelationshipClass.validate_invocation_value(value)


class ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipInput(BaseModel):
    object_config_graph_relationship_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphRelationship.object_config_graph_relationship_classes"
    )
    class_config_id: UUID


class ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipOutput(BaseModel):
    value: ObjectConfigGraphRelationshipClass


FUNCTIONS = {
    "ObjectConfigGraphRelationshipClass": {
        "build_via_object_config_graph_relationship": {
            "canonical": {
                "name": "build_via_object_config_graph_relationship",
                "description": "Build deterministic ObjectConfigGraphRelationshipClass within a relationship scope.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipInput,
            "output": ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphRelationshipClass",
    "ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipInput",
    "ObjectConfigGraphRelationshipClassBuildViaObjectConfigGraphRelationshipOutput",
    "FUNCTIONS",
]
