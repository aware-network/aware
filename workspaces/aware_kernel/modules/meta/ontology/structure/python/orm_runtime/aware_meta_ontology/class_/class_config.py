from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config_enums import FunctionKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.class_.code_section_class import CodeSectionClass
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.function.function_config import FunctionConfig


class ClassConfig(ORMModel):
    # Relationships
    class_config_attribute_configs: list[ClassConfigAttributeConfig] = Field(default_factory=list)
    class_config_function_configs: list[ClassConfigFunctionConfig] = Field(default_factory=list)
    class_config_relationships: list[ClassConfigRelationship] = Field(default_factory=list)
    parent_class: ClassConfig | None = Field(default=None, exclude=True)
    code_section_class: CodeSectionClass | None = Field(default=None, exclude=True)

    # Attributes
    class_fqn: str
    description: str | None = Field(default=None)
    name: str
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)
    identity_mode: ClassIdentityMode = Field(default=ClassIdentityMode.contained)

    # Foreign Keys
    object_config_graph_node_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.class_config"
    )
    parent_class_id: UUID | None = Field(default=None, description="Foreign key for ClassConfig.parent_class")
    code_section_class_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfig.code_section_class"
    )

    async def update_config(
        self,
        description: str | None = None,
        is_base: bool = True,
        is_edge: bool = False,
        value_mode: ClassValueMode = ClassValueMode.graph_ref,
        identity_mode: ClassIdentityMode = ClassIdentityMode.contained,
    ) -> None:
        """
        Update mutable ClassConfig metadata.

        Contract:
        - `class_fqn` and `name` are identity and are not mutable here.
        - Attribute, function, and relationship membership changes use their
          own ontology functions.
        """

        payload = {
            "description": description,
            "is_base": is_base,
            "is_edge": is_edge,
            "value_mode": value_mode,
            "identity_mode": identity_mode,
        }
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    async def create_primitive_attribute_config(
        self,
        name: str,
        primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        position: int = 0,
    ) -> AttributeConfig:
        """Materialize one AttributeConfig and bind it through ClassConfigAttributeConfig."""

        payload = {
            "name": name,
            "primitive_base_type": primitive_base_type,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "position": position,
        }
        result = await invoke_instance(
            orm_model=self, function_name="create_primitive_attribute_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.attribute.attribute_config import AttributeConfig

        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    async def create_enum_attribute_config(
        self,
        name: str,
        enum_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        position: int = 0,
    ) -> AttributeConfig:
        """Materialize one enum AttributeConfig and bind it through ClassConfigAttributeConfig."""

        payload = {
            "name": name,
            "enum_config_id": enum_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="create_enum_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.attribute.attribute_config import AttributeConfig

        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    async def create_class_attribute_config(
        self,
        name: str,
        type_class_config_id: UUID,
        description: str | None = None,
        default_value: str | None = None,
        is_primary: bool = False,
        is_public: bool = True,
        is_required: bool = False,
        is_unique: bool = False,
        is_virtual: bool = False,
        position: int = 0,
    ) -> AttributeConfig:
        """Materialize one class AttributeConfig and bind it through ClassConfigAttributeConfig."""

        payload = {
            "name": name,
            "type_class_config_id": type_class_config_id,
            "description": description,
            "default_value": default_value,
            "is_primary": is_primary,
            "is_public": is_public,
            "is_required": is_required,
            "is_unique": is_unique,
            "is_virtual": is_virtual,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="create_class_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.attribute.attribute_config import AttributeConfig

        if isinstance(value, AttributeConfig):
            return value
        return AttributeConfig.validate_invocation_value(value)

    async def remove_attribute_config(self, name: str, attribute_config_id: UUID | None = None) -> None:
        """
        Remove one AttributeConfig membership from this ClassConfig.

        Contract:
        - Mutates only class_config_attribute_configs on this ClassConfig.
        - Attribute identity comes from committed semantic baseline truth when available.
        - Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.
        """

        payload = {"name": name, "attribute_config_id": attribute_config_id}
        await invoke_instance(orm_model=self, function_name="remove_attribute_config", payload=payload)
        return None

    async def create_function_config(
        self,
        name: str,
        description: str | None = None,
        verb: str | None = None,
        is_async: bool = False,
        kind: FunctionKind = FunctionKind.instance,
        is_public: bool = True,
        is_constructor: bool = False,
        position: int = 0,
    ) -> FunctionConfig:
        """Materialize one FunctionConfig and bind it through ClassConfigFunctionConfig."""

        payload = {
            "name": name,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "kind": kind,
            "is_public": is_public,
            "is_constructor": is_constructor,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="create_function_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_config import FunctionConfig

        if isinstance(value, FunctionConfig):
            return value
        return FunctionConfig.validate_invocation_value(value)

    async def remove_function_config(self, name: str, function_config_id: UUID | None = None) -> None:
        """
        Remove one FunctionConfig membership from this ClassConfig.

        Contract:
        - Mutates only class_config_function_configs on this ClassConfig.
        - Function identity comes from committed semantic baseline truth when available.
        - Rooted OIG commit reachability owns stale FunctionConfig deletion after membership removal.
        """

        payload = {"name": name, "function_config_id": function_config_id}
        await invoke_instance(orm_model=self, function_name="remove_function_config", payload=payload)
        return None

    async def create_relationship(
        self,
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
        Materialize one deterministic relationship owned by this ClassConfig.

        Contract:
        - Parent `ClassConfig` scope is propagated by traversal lowering.
        - Stable identity derives from parent scope + `(target_class_config_id, relationship_key)`.
        - Association class metadata is optional, materialized on the child rail, and is not part of stable
        identity.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="create_relationship", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship

        if isinstance(value, ClassConfigRelationship):
            return value
        return ClassConfigRelationship.validate_invocation_value(value)

    async def remove_relationship_config(
        self, relationship_key: str, relationship_config_id: UUID | None = None
    ) -> None:
        """
        Remove one ClassConfigRelationship membership from this ClassConfig.

        Contract:
        - Mutates only class_config_relationships on this ClassConfig.
        - Relationship identity comes from committed semantic baseline truth when available.
        - Rooted OIG commit reachability owns stale relationship object deletion after membership removal.
        """

        payload = {"relationship_key": relationship_key, "relationship_config_id": relationship_config_id}
        await invoke_instance(orm_model=self, function_name="remove_relationship_config", payload=payload)
        return None

    @classmethod
    async def create_via_object_config_graph_node(
        cls,
        object_config_graph_node_id: UUID,
        class_fqn: str,
        name: str,
        is_base: bool = True,
        is_edge: bool = False,
        description: str | None = None,
        value_mode: ClassValueMode = ClassValueMode.graph_ref,
    ) -> ClassConfig:
        """Create deterministic ClassConfig under an ObjectConfigGraphNode."""

        payload = {
            "object_config_graph_node_id": object_config_graph_node_id,
            "class_fqn": class_fqn,
            "name": name,
            "is_base": is_base,
            "is_edge": is_edge,
            "description": description,
            "value_mode": value_mode,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_config_graph_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassConfig):
            return value
        return ClassConfig.validate_invocation_value(value)


class ClassConfigUpdateConfigInput(BaseModel):
    description: str | None = Field(default=None)
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)
    identity_mode: ClassIdentityMode = Field(default=ClassIdentityMode.contained)


class ClassConfigUpdateConfigOutput(BaseModel):
    pass


class ClassConfigCreatePrimitiveAttributeConfigInput(BaseModel):
    name: str
    primitive_base_type: CodePrimitiveBaseType = Field(default=CodePrimitiveBaseType.any)
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigCreatePrimitiveAttributeConfigOutput(BaseModel):
    value: AttributeConfig


class ClassConfigCreateEnumAttributeConfigInput(BaseModel):
    name: str
    enum_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigCreateEnumAttributeConfigOutput(BaseModel):
    value: AttributeConfig


class ClassConfigCreateClassAttributeConfigInput(BaseModel):
    name: str
    type_class_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigCreateClassAttributeConfigOutput(BaseModel):
    value: AttributeConfig


class ClassConfigRemoveAttributeConfigInput(BaseModel):
    name: str
    attribute_config_id: UUID | None = Field(default=None)


class ClassConfigRemoveAttributeConfigOutput(BaseModel):
    pass


class ClassConfigCreateFunctionConfigInput(BaseModel):
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)


class ClassConfigCreateFunctionConfigOutput(BaseModel):
    value: FunctionConfig


class ClassConfigRemoveFunctionConfigInput(BaseModel):
    name: str
    function_config_id: UUID | None = Field(default=None)


class ClassConfigRemoveFunctionConfigOutput(BaseModel):
    pass


class ClassConfigCreateRelationshipInput(BaseModel):
    target_class_config_id: UUID
    relationship_key: str
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail | None = Field(default=None)
    forward_required: bool = Field(default=False)
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    reified_from_relationship_id: UUID | None = Field(default=None)
    reified_role: ClassConfigRelationshipReifiedRole | None = Field(default=None)


class ClassConfigCreateRelationshipOutput(BaseModel):
    value: ClassConfigRelationship


class ClassConfigRemoveRelationshipConfigInput(BaseModel):
    relationship_key: str
    relationship_config_id: UUID | None = Field(default=None)


class ClassConfigRemoveRelationshipConfigOutput(BaseModel):
    pass


class ClassConfigCreateViaObjectConfigGraphNodeInput(BaseModel):
    object_config_graph_node_id: UUID = Field(description="Foreign key for ObjectConfigGraphNode.class_config")
    class_fqn: str
    name: str
    is_base: bool = Field(default=True)
    is_edge: bool = Field(default=False)
    description: str | None = Field(default=None)
    value_mode: ClassValueMode = Field(default=ClassValueMode.graph_ref)


class ClassConfigCreateViaObjectConfigGraphNodeOutput(BaseModel):
    value: ClassConfig


FUNCTIONS = {
    "ClassConfig": {
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable ClassConfig metadata.\n\nContract:\n- `class_fqn` and `name` are identity and are not mutable here.\n- Attribute, function, and relationship membership changes use their\n  own ontology functions.",
                "is_constructor": False,
            },
            "input": ClassConfigUpdateConfigInput,
            "output": ClassConfigUpdateConfigOutput,
        },
        "create_primitive_attribute_config": {
            "canonical": {
                "name": "create_primitive_attribute_config",
                "description": "Materialize one AttributeConfig and bind it through ClassConfigAttributeConfig.",
                "is_constructor": False,
            },
            "input": ClassConfigCreatePrimitiveAttributeConfigInput,
            "output": ClassConfigCreatePrimitiveAttributeConfigOutput,
        },
        "create_enum_attribute_config": {
            "canonical": {
                "name": "create_enum_attribute_config",
                "description": "Materialize one enum AttributeConfig and bind it through ClassConfigAttributeConfig.",
                "is_constructor": False,
            },
            "input": ClassConfigCreateEnumAttributeConfigInput,
            "output": ClassConfigCreateEnumAttributeConfigOutput,
        },
        "create_class_attribute_config": {
            "canonical": {
                "name": "create_class_attribute_config",
                "description": "Materialize one class AttributeConfig and bind it through ClassConfigAttributeConfig.",
                "is_constructor": False,
            },
            "input": ClassConfigCreateClassAttributeConfigInput,
            "output": ClassConfigCreateClassAttributeConfigOutput,
        },
        "remove_attribute_config": {
            "canonical": {
                "name": "remove_attribute_config",
                "description": "Remove one AttributeConfig membership from this ClassConfig.\n\nContract:\n- Mutates only class_config_attribute_configs on this ClassConfig.\n- Attribute identity comes from committed semantic baseline truth when available.\n- Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.",
                "is_constructor": False,
            },
            "input": ClassConfigRemoveAttributeConfigInput,
            "output": ClassConfigRemoveAttributeConfigOutput,
        },
        "create_function_config": {
            "canonical": {
                "name": "create_function_config",
                "description": "Materialize one FunctionConfig and bind it through ClassConfigFunctionConfig.",
                "is_constructor": False,
            },
            "input": ClassConfigCreateFunctionConfigInput,
            "output": ClassConfigCreateFunctionConfigOutput,
        },
        "remove_function_config": {
            "canonical": {
                "name": "remove_function_config",
                "description": "Remove one FunctionConfig membership from this ClassConfig.\n\nContract:\n- Mutates only class_config_function_configs on this ClassConfig.\n- Function identity comes from committed semantic baseline truth when available.\n- Rooted OIG commit reachability owns stale FunctionConfig deletion after membership removal.",
                "is_constructor": False,
            },
            "input": ClassConfigRemoveFunctionConfigInput,
            "output": ClassConfigRemoveFunctionConfigOutput,
        },
        "create_relationship": {
            "canonical": {
                "name": "create_relationship",
                "description": "Materialize one deterministic relationship owned by this ClassConfig.\n\nContract:\n- Parent `ClassConfig` scope is propagated by traversal lowering.\n- Stable identity derives from parent scope + `(target_class_config_id, relationship_key)`.\n- Association class metadata is optional, materialized on the child rail, and is not part of stable identity.",
                "is_constructor": False,
            },
            "input": ClassConfigCreateRelationshipInput,
            "output": ClassConfigCreateRelationshipOutput,
        },
        "remove_relationship_config": {
            "canonical": {
                "name": "remove_relationship_config",
                "description": "Remove one ClassConfigRelationship membership from this ClassConfig.\n\nContract:\n- Mutates only class_config_relationships on this ClassConfig.\n- Relationship identity comes from committed semantic baseline truth when available.\n- Rooted OIG commit reachability owns stale relationship object deletion after membership removal.",
                "is_constructor": False,
            },
            "input": ClassConfigRemoveRelationshipConfigInput,
            "output": ClassConfigRemoveRelationshipConfigOutput,
        },
        "create_via_object_config_graph_node": {
            "canonical": {
                "name": "create_via_object_config_graph_node",
                "description": "Create deterministic ClassConfig under an ObjectConfigGraphNode.",
                "is_constructor": True,
            },
            "input": ClassConfigCreateViaObjectConfigGraphNodeInput,
            "output": ClassConfigCreateViaObjectConfigGraphNodeOutput,
        },
    },
}

__all__ = [
    "ClassConfig",
    "ClassConfigUpdateConfigInput",
    "ClassConfigUpdateConfigOutput",
    "ClassConfigCreatePrimitiveAttributeConfigInput",
    "ClassConfigCreatePrimitiveAttributeConfigOutput",
    "ClassConfigCreateEnumAttributeConfigInput",
    "ClassConfigCreateEnumAttributeConfigOutput",
    "ClassConfigCreateClassAttributeConfigInput",
    "ClassConfigCreateClassAttributeConfigOutput",
    "ClassConfigRemoveAttributeConfigInput",
    "ClassConfigRemoveAttributeConfigOutput",
    "ClassConfigCreateFunctionConfigInput",
    "ClassConfigCreateFunctionConfigOutput",
    "ClassConfigRemoveFunctionConfigInput",
    "ClassConfigRemoveFunctionConfigOutput",
    "ClassConfigCreateRelationshipInput",
    "ClassConfigCreateRelationshipOutput",
    "ClassConfigRemoveRelationshipConfigInput",
    "ClassConfigRemoveRelationshipConfigOutput",
    "ClassConfigCreateViaObjectConfigGraphNodeInput",
    "ClassConfigCreateViaObjectConfigGraphNodeOutput",
    "FUNCTIONS",
]
