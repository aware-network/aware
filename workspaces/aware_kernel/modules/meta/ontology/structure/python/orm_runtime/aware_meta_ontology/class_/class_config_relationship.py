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
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_config_relationship_association import ClassConfigRelationshipAssociation
    from aware_meta_ontology.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute


class ClassConfigRelationship(ORMModel):
    """
    Canonical relationship SSOT.
    A relationship is declared by exactly one class attribute (single-sided). Any "backref"
    attribute is treated as a separate relationship in canonical mode.
    This model stores:
    - Declaring endpoints (ClassConfig ↔ ClassConfig) for augmentation honesty
    - Optional association edge container
    - Loading semantics (forward/reverse) derived from annotations
    """

    # Relationships
    target_class_config: ClassConfig | None = Field(default=None, exclude=True)
    class_config_relationship_attributes: list[ClassConfigRelationshipAttribute] = Field(default_factory=list)
    reified_from_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)

    # Attributes
    relationship_key: str
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_relationships")
    target_class_config_id: UUID = Field(description="Foreign key for ClassConfigRelationship.target_class_config")
    reified_from_relationship_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigRelationship.reified_from_relationship"
    )

    # Edges
    class_config_relationship_association_edge: ClassConfigRelationshipAssociation | None = Field(
        default=None, description="Edge association helper for class_config_relationship_association"
    )

    @property
    def class_config_relationship_association(self) -> ClassConfig | None:
        return (
            self.class_config_relationship_association_edge.class_config
            if self.class_config_relationship_association_edge is not None
            and self.class_config_relationship_association_edge.class_config is not None
            else None
        )

    async def create_association(
        self,
        class_config_id: UUID,
        forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    ) -> ClassConfigRelationshipAssociation:
        """Attach one deterministic association edge under this relationship."""

        payload = {
            "class_config_id": class_config_id,
            "forward_loading_strategy": forward_loading_strategy,
            "reverse_loading_strategy": reverse_loading_strategy,
        }
        result = await invoke_instance(orm_model=self, function_name="create_association", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_config_relationship_association import ClassConfigRelationshipAssociation

        if isinstance(value, ClassConfigRelationshipAssociation):
            return value
        return ClassConfigRelationshipAssociation.validate_invocation_value(value)

    async def create_attribute(
        self,
        attribute_config_id: UUID,
        direction: ClassConfigRelationshipDirection,
        role: ClassConfigRelationshipAttributeRole,
    ) -> ClassConfigRelationshipAttribute:
        """Attach one deterministic relationship-attribute edge under this relationship."""

        payload = {"attribute_config_id": attribute_config_id, "direction": direction, "role": role}
        result = await invoke_instance(orm_model=self, function_name="create_attribute", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute

        if isinstance(value, ClassConfigRelationshipAttribute):
            return value
        return ClassConfigRelationshipAttribute.validate_invocation_value(value)

    async def update_config(
        self,
        relationship_type: ClassConfigRelationshipType,
        identity_rail: ClassConfigRelationshipIdentityRail | None = None,
        forward_required: bool = False,
        forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reified_from_relationship_id: UUID | None = None,
        reified_role: ClassConfigRelationshipReifiedRole | None = None,
    ) -> None:
        """
        Update mutable relationship configuration for an existing ClassConfigRelationship.

        Contract:
        - `target_class_config_id` and `relationship_key` are identity and are not mutable here.
        - Changing either identity field is replacement semantics, not in-place update.
        - This full-payload update treats nullable arguments as current semantic truth.
        """

        payload = {
            "relationship_type": relationship_type,
            "identity_rail": identity_rail,
            "forward_required": forward_required,
            "forward_loading_strategy": forward_loading_strategy,
            "reverse_loading_strategy": reverse_loading_strategy,
            "reified_from_relationship_id": reified_from_relationship_id,
            "reified_role": reified_role,
        }
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_via_class_config(
        cls,
        class_config_id: UUID,
        target_class_config_id: UUID,
        relationship_key: str,
        relationship_type: ClassConfigRelationshipType,
        identity_rail: ClassConfigRelationshipIdentityRail | None = None,
        forward_required: bool = False,
        forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
        reified_from_relationship_id: UUID | None = None,
        reified_role: ClassConfigRelationshipReifiedRole | None = None,
    ) -> ClassConfigRelationship:
        """
        Create deterministic ClassConfigRelationship under a source ClassConfig scope.

        Contract:
        - Parent `ClassConfig` scope is propagated by traversal lowering.
        - Stable identity derives from propagated source class + `(target_class_config_id,
        relationship_key)`.
        - Association edges are materialized under this relationship via `create_association`.
        - Optional reification metadata does not participate in stable identity.
        """

        payload = {
            "class_config_id": class_config_id,
            "target_class_config_id": target_class_config_id,
            "relationship_key": relationship_key,
            "relationship_type": relationship_type,
            "identity_rail": identity_rail,
            "forward_required": forward_required,
            "forward_loading_strategy": forward_loading_strategy,
            "reverse_loading_strategy": reverse_loading_strategy,
            "reified_from_relationship_id": reified_from_relationship_id,
            "reified_role": reified_role,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_class_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfigRelationship):
            return value
        return ClassConfigRelationship.validate_invocation_value(value)


class ClassConfigRelationshipCreateAssociationInput(BaseModel):
    class_config_id: UUID
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)


class ClassConfigRelationshipCreateAssociationOutput(BaseModel):
    value: ClassConfigRelationshipAssociation


class ClassConfigRelationshipCreateAttributeInput(BaseModel):
    attribute_config_id: UUID
    direction: ClassConfigRelationshipDirection
    role: ClassConfigRelationshipAttributeRole


class ClassConfigRelationshipCreateAttributeOutput(BaseModel):
    value: ClassConfigRelationshipAttribute


class ClassConfigRelationshipUpdateConfigInput(BaseModel):
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool = Field(default=False)
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_from_relationship_id: UUID | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)


class ClassConfigRelationshipUpdateConfigOutput(BaseModel):
    pass


class ClassConfigRelationshipCreateViaClassConfigInput(BaseModel):
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_relationships")
    target_class_config_id: UUID
    relationship_key: str
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool = Field(default=False)
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_from_relationship_id: UUID | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)


class ClassConfigRelationshipCreateViaClassConfigOutput(BaseModel):
    value: ClassConfigRelationship


FUNCTIONS = {
    "ClassConfigRelationship": {
        "create_association": {
            "canonical": {
                "name": "create_association",
                "description": "Attach one deterministic association edge under this relationship.",
                "is_constructor": False,
            },
            "input": ClassConfigRelationshipCreateAssociationInput,
            "output": ClassConfigRelationshipCreateAssociationOutput,
        },
        "create_attribute": {
            "canonical": {
                "name": "create_attribute",
                "description": "Attach one deterministic relationship-attribute edge under this relationship.",
                "is_constructor": False,
            },
            "input": ClassConfigRelationshipCreateAttributeInput,
            "output": ClassConfigRelationshipCreateAttributeOutput,
        },
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable relationship configuration for an existing ClassConfigRelationship.\n\nContract:\n- `target_class_config_id` and `relationship_key` are identity and are not mutable here.\n- Changing either identity field is replacement semantics, not in-place update.\n- This full-payload update treats nullable arguments as current semantic truth.",
                "is_constructor": False,
            },
            "input": ClassConfigRelationshipUpdateConfigInput,
            "output": ClassConfigRelationshipUpdateConfigOutput,
        },
        "create_via_class_config": {
            "canonical": {
                "name": "create_via_class_config",
                "description": "Create deterministic ClassConfigRelationship under a source ClassConfig scope.\n\nContract:\n- Parent `ClassConfig` scope is propagated by traversal lowering.\n- Stable identity derives from propagated source class + `(target_class_config_id, relationship_key)`.\n- Association edges are materialized under this relationship via `create_association`.\n- Optional reification metadata does not participate in stable identity.",
                "is_constructor": True,
            },
            "input": ClassConfigRelationshipCreateViaClassConfigInput,
            "output": ClassConfigRelationshipCreateViaClassConfigOutput,
        },
    },
}

__all__ = [
    "ClassConfigRelationship",
    "ClassConfigRelationshipCreateAssociationInput",
    "ClassConfigRelationshipCreateAssociationOutput",
    "ClassConfigRelationshipCreateAttributeInput",
    "ClassConfigRelationshipCreateAttributeOutput",
    "ClassConfigRelationshipUpdateConfigInput",
    "ClassConfigRelationshipUpdateConfigOutput",
    "ClassConfigRelationshipCreateViaClassConfigInput",
    "ClassConfigRelationshipCreateViaClassConfigOutput",
    "FUNCTIONS",
]
