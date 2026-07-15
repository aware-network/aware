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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_relationship_class import (
        ObjectConfigGraphRelationshipClass,
    )


class ObjectConfigGraphRelationship(ORMModel):
    """Entry linking two ObjectConfigGraphs (source → target) and their relationships"""

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    object_config_graph_relationship_classes: list[ObjectConfigGraphRelationshipClass] = Field(default_factory=list)

    # Foreign Keys
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_config_graph_relationships"
    )
    target_object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphRelationship.target_object_config_graph"
    )

    async def create_class(self, class_config_id: UUID) -> ObjectConfigGraphRelationshipClass:
        """Create deterministic ObjectConfigGraphRelationshipClass under this relationship."""

        payload = {"class_config_id": class_config_id}
        result = await invoke_instance(orm_model=self, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_relationship_class import (
            ObjectConfigGraphRelationshipClass,
        )

        if isinstance(value, ObjectConfigGraphRelationshipClass):
            return value
        return ObjectConfigGraphRelationshipClass.validate_invocation_value(value)

    @classmethod
    async def build_via_object_config_graph(
        cls, object_config_graph_id: UUID, target_object_config_graph_id: UUID
    ) -> ObjectConfigGraphRelationship:
        """Build deterministic ObjectConfigGraphRelationship within an ObjectConfigGraph scope."""

        payload = {
            "object_config_graph_id": object_config_graph_id,
            "target_object_config_graph_id": target_object_config_graph_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_object_config_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphRelationship):
            return value
        return ObjectConfigGraphRelationship.validate_invocation_value(value)


class ObjectConfigGraphRelationshipCreateClassInput(BaseModel):
    class_config_id: UUID


class ObjectConfigGraphRelationshipCreateClassOutput(BaseModel):
    value: ObjectConfigGraphRelationshipClass


class ObjectConfigGraphRelationshipBuildViaObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraph.object_config_graph_relationships"
    )
    target_object_config_graph_id: UUID


class ObjectConfigGraphRelationshipBuildViaObjectConfigGraphOutput(BaseModel):
    value: ObjectConfigGraphRelationship


FUNCTIONS = {
    "ObjectConfigGraphRelationship": {
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Create deterministic ObjectConfigGraphRelationshipClass under this relationship.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphRelationshipCreateClassInput,
            "output": ObjectConfigGraphRelationshipCreateClassOutput,
        },
        "build_via_object_config_graph": {
            "canonical": {
                "name": "build_via_object_config_graph",
                "description": "Build deterministic ObjectConfigGraphRelationship within an ObjectConfigGraph scope.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphRelationshipBuildViaObjectConfigGraphInput,
            "output": ObjectConfigGraphRelationshipBuildViaObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphRelationship",
    "ObjectConfigGraphRelationshipCreateClassInput",
    "ObjectConfigGraphRelationshipCreateClassOutput",
    "ObjectConfigGraphRelationshipBuildViaObjectConfigGraphInput",
    "ObjectConfigGraphRelationshipBuildViaObjectConfigGraphOutput",
    "FUNCTIONS",
]
