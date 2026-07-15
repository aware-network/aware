from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import ClassConfigRelationshipSideLoadingStrategy

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig


class ClassConfigRelationshipAssociation(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(
        default=None, exclude=True, description="Association target reference to ClassConfig"
    )

    # Attributes
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)

    # Foreign Keys
    class_config_id: UUID = Field(description="Join FK to ClassConfig")
    class_config_relationship_id: UUID = Field(description="Join FK to ClassConfigRelationship")

    @classmethod
    async def create_via_class_config_relationship(
        cls,
        class_config_relationship_id: UUID,
        class_config_id: UUID,
        forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    ) -> ClassConfigRelationshipAssociation:
        """
        Create deterministic association metadata under a ClassConfigRelationship scope.

        Contract:
        - Parent `ClassConfigRelationship` scope is propagated by traversal lowering.
        - Stable identity derives from propagated relationship scope + `class_config_id`.
        """

        payload = {
            "class_config_relationship_id": class_config_relationship_id,
            "class_config_id": class_config_id,
            "forward_loading_strategy": forward_loading_strategy,
            "reverse_loading_strategy": reverse_loading_strategy,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_class_config_relationship", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigRelationshipAssociation):
            return value
        return ClassConfigRelationshipAssociation.validate_invocation_value(value)


class ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipInput(BaseModel):
    class_config_relationship_id: UUID = Field(description="Join FK to ClassConfigRelationship")
    class_config_id: UUID
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)


class ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipOutput(BaseModel):
    value: ClassConfigRelationshipAssociation


FUNCTIONS = {
    "ClassConfigRelationshipAssociation": {
        "create_via_class_config_relationship": {
            "canonical": {
                "name": "create_via_class_config_relationship",
                "description": "Create deterministic association metadata under a ClassConfigRelationship scope.\n\nContract:\n- Parent `ClassConfigRelationship` scope is propagated by traversal lowering.\n- Stable identity derives from propagated relationship scope + `class_config_id`.",
                "is_constructor": True,
            },
            "input": ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipInput,
            "output": ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipOutput,
        },
    },
}

__all__ = [
    "ClassConfigRelationshipAssociation",
    "ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipInput",
    "ClassConfigRelationshipAssociationCreateViaClassConfigRelationshipOutput",
    "FUNCTIONS",
]
