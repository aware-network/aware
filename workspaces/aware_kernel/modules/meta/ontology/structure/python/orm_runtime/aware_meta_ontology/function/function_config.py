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
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.function.code_section_function import CodeSectionFunction
    from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology.function.function_config_invocation import FunctionConfigInvocation
    from aware_meta_ontology.function.function_impl import FunctionImpl


class FunctionConfig(ORMModel):
    # Relationships
    function_config_attribute_configs: list[FunctionConfigAttributeConfig] = Field(default_factory=list)
    invocations: list[FunctionConfigInvocation] = Field(default_factory=list)
    function_impl: FunctionImpl | None = Field(default=None)
    code_section_function: CodeSectionFunction | None = Field(default=None, exclude=True)

    # Attributes
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)

    # Foreign Keys
    code_section_function_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfig.code_section_function"
    )

    @classmethod
    async def create(
        cls,
        owner_key: str,
        name: str,
        description: str | None = None,
        verb: str | None = None,
        is_async: bool = False,
        kind: FunctionKind = FunctionKind.instance,
    ) -> FunctionConfig:
        """
        Create deterministic FunctionConfig.

        Contract:
        - Function identity is semantic and standalone on `(owner_key, name, kind)`.
        - Traversal may still materialize this function through membership edges such as
          `ClassConfigFunctionConfig`, but parent propagation must not enter the function stable-id formula.
        """

        payload = {
            "owner_key": owner_key,
            "name": name,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "kind": kind,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionConfig):
            return value
        return FunctionConfig.validate_invocation_value(value)

    async def update_config(
        self, description: str | None = None, verb: str | None = None, is_async: bool = False
    ) -> None:
        """
        Update mutable FunctionConfig metadata for an existing function.

        Contract:
        - `owner_key`, `name`, and `kind` are identity keys and are not mutable here.
        - Class membership metadata (`is_public`, `is_constructor`, `position`) lives on
          ClassConfigFunctionConfig and requires its own edge-level function.
        - This full-payload update treats nullable arguments as current semantic truth.
        """

        payload = {"description": description, "verb": verb, "is_async": is_async}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    async def add_primitive_attribute_config(
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
    ) -> FunctionConfigAttributeConfig:
        """
        Attach one pre-existing typed AttributeConfig contract edge under this FunctionConfig.

        Contract:
        - Represents canonical function I/O schema intent.
        - Materializes/ensures a reusable primitive AttributeConfig via semantic standalone keys.
        - Idempotent per `(function_config_id, name, type)`.
        """

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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_instance(orm_model=self, function_name="add_primitive_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig

        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)

    async def add_enum_attribute_config(
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
    ) -> FunctionConfigAttributeConfig:
        """Attach one pre-existing typed enum AttributeConfig contract edge under this FunctionConfig."""

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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_instance(orm_model=self, function_name="add_enum_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig

        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)

    async def add_class_attribute_config(
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
        type: FunctionAttributeType = FunctionAttributeType.input,
        position: int = 0,
        is_identity_key: bool = False,
    ) -> FunctionConfigAttributeConfig:
        """Attach one pre-existing typed class AttributeConfig contract edge under this FunctionConfig."""

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
            "type": type,
            "position": position,
            "is_identity_key": is_identity_key,
        }
        result = await invoke_instance(orm_model=self, function_name="add_class_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig

        if isinstance(value, FunctionConfigAttributeConfig):
            return value
        return FunctionConfigAttributeConfig.validate_invocation_value(value)

    async def remove_attribute_config(
        self,
        name: str,
        type: FunctionAttributeType = FunctionAttributeType.input,
        attribute_config_id: UUID | None = None,
    ) -> None:
        """
        Remove one AttributeConfig membership from this FunctionConfig.

        Contract:
        - Mutates only function_config_attribute_configs on this FunctionConfig.
        - Attribute identity comes from committed semantic baseline truth when available.
        - Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.
        """

        payload = {"name": name, "type": type, "attribute_config_id": attribute_config_id}
        await invoke_instance(orm_model=self, function_name="remove_attribute_config", payload=payload)
        return None

    async def create_function_impl(
        self, key: str = "default", impl_kind: FunctionImplKind = FunctionImplKind.instruction_body
    ) -> FunctionImpl:
        """
        Create or return the canonical execution rail (`FunctionImpl`) for this FunctionConfig.

        Contract:
        - Parent (`FunctionConfig`) owns `function_impl` propagation.
        - One rail per FunctionConfig (idempotent under parent scope).
        - `impl_kind` carries whether this rail is an instruction body or an auto constructor template.
        """

        payload = {"key": key, "impl_kind": impl_kind}
        result = await invoke_instance(orm_model=self, function_name="create_function_impl", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl import FunctionImpl

        if isinstance(value, FunctionImpl):
            return value
        return FunctionImpl.validate_invocation_value(value)

    async def create_invocation(
        self,
        position: int,
        kind: FunctionInvocationKind,
        target_function_config_id: UUID,
        relationship_fingerprint: str = "owner",
        class_config_relationship_id: UUID | None = None,
        root_invocation_id: UUID | None = None,
        root_kind: FunctionInvocationRootKind = FunctionInvocationRootKind.owner,
        capture_name: str | None = None,
    ) -> FunctionConfigInvocation:
        """
        Create one deterministic invocation-plan step under this FunctionConfig.

        Contract:
        - Parent (`FunctionConfig`) owns invocation membership propagation.
        - Identity is constructor-keyed on
          `(function_config_id via parent path, position, kind, target_function_config_id,
        relationship_fingerprint)`.
        - `class_config_relationship_id` remains explicit traversal metadata; owner-local invocations use
          `relationship_fingerprint = owner` and `class_config_relationship_id = null`.
        """

        payload = {
            "position": position,
            "kind": kind,
            "target_function_config_id": target_function_config_id,
            "relationship_fingerprint": relationship_fingerprint,
            "class_config_relationship_id": class_config_relationship_id,
            "root_invocation_id": root_invocation_id,
            "root_kind": root_kind,
            "capture_name": capture_name,
        }
        result = await invoke_instance(orm_model=self, function_name="create_invocation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_config_invocation import FunctionConfigInvocation

        if isinstance(value, FunctionConfigInvocation):
            return value
        return FunctionConfigInvocation.validate_invocation_value(value)


class FunctionConfigCreateInput(BaseModel):
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)


class FunctionConfigCreateOutput(BaseModel):
    value: FunctionConfig


class FunctionConfigUpdateConfigInput(BaseModel):
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)


class FunctionConfigUpdateConfigOutput(BaseModel):
    pass


class FunctionConfigAddPrimitiveAttributeConfigInput(BaseModel):
    name: str
    primitive_base_type: CodePrimitiveBaseType = Field(default=CodePrimitiveBaseType.any)
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class FunctionConfigAddPrimitiveAttributeConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


class FunctionConfigAddEnumAttributeConfigInput(BaseModel):
    name: str
    enum_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class FunctionConfigAddEnumAttributeConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


class FunctionConfigAddClassAttributeConfigInput(BaseModel):
    name: str
    type_class_config_id: UUID
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_primary: bool = Field(default=False)
    is_public: bool = Field(default=True)
    is_required: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    is_virtual: bool = Field(default=False)
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)


class FunctionConfigAddClassAttributeConfigOutput(BaseModel):
    value: FunctionConfigAttributeConfig


class FunctionConfigRemoveAttributeConfigInput(BaseModel):
    name: str
    type: FunctionAttributeType = Field(default=FunctionAttributeType.input)
    attribute_config_id: UUID | None = Field(default=None)


class FunctionConfigRemoveAttributeConfigOutput(BaseModel):
    pass


class FunctionConfigCreateFunctionImplInput(BaseModel):
    key: str = Field(default="default")
    impl_kind: FunctionImplKind = Field(default=FunctionImplKind.instruction_body)


class FunctionConfigCreateFunctionImplOutput(BaseModel):
    value: FunctionImpl


class FunctionConfigCreateInvocationInput(BaseModel):
    position: int
    kind: FunctionInvocationKind
    target_function_config_id: UUID
    relationship_fingerprint: str = Field(default="owner")
    class_config_relationship_id: UUID | None = Field(default=None)
    root_invocation_id: UUID | None = Field(default=None)
    root_kind: FunctionInvocationRootKind = Field(default=FunctionInvocationRootKind.owner)
    capture_name: str | None = Field(default=None)


class FunctionConfigCreateInvocationOutput(BaseModel):
    value: FunctionConfigInvocation


FUNCTIONS = {
    "FunctionConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic FunctionConfig.\n\nContract:\n- Function identity is semantic and standalone on `(owner_key, name, kind)`.\n- Traversal may still materialize this function through membership edges such as\n  `ClassConfigFunctionConfig`, but parent propagation must not enter the function stable-id formula.",
                "is_constructor": True,
            },
            "input": FunctionConfigCreateInput,
            "output": FunctionConfigCreateOutput,
        },
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable FunctionConfig metadata for an existing function.\n\nContract:\n- `owner_key`, `name`, and `kind` are identity keys and are not mutable here.\n- Class membership metadata (`is_public`, `is_constructor`, `position`) lives on\n  ClassConfigFunctionConfig and requires its own edge-level function.\n- This full-payload update treats nullable arguments as current semantic truth.",
                "is_constructor": False,
            },
            "input": FunctionConfigUpdateConfigInput,
            "output": FunctionConfigUpdateConfigOutput,
        },
        "add_primitive_attribute_config": {
            "canonical": {
                "name": "add_primitive_attribute_config",
                "description": "Attach one pre-existing typed AttributeConfig contract edge under this FunctionConfig.\n\nContract:\n- Represents canonical function I/O schema intent.\n- Materializes/ensures a reusable primitive AttributeConfig via semantic standalone keys.\n- Idempotent per `(function_config_id, name, type)`.",
                "is_constructor": False,
            },
            "input": FunctionConfigAddPrimitiveAttributeConfigInput,
            "output": FunctionConfigAddPrimitiveAttributeConfigOutput,
        },
        "add_enum_attribute_config": {
            "canonical": {
                "name": "add_enum_attribute_config",
                "description": "Attach one pre-existing typed enum AttributeConfig contract edge under this FunctionConfig.",
                "is_constructor": False,
            },
            "input": FunctionConfigAddEnumAttributeConfigInput,
            "output": FunctionConfigAddEnumAttributeConfigOutput,
        },
        "add_class_attribute_config": {
            "canonical": {
                "name": "add_class_attribute_config",
                "description": "Attach one pre-existing typed class AttributeConfig contract edge under this FunctionConfig.",
                "is_constructor": False,
            },
            "input": FunctionConfigAddClassAttributeConfigInput,
            "output": FunctionConfigAddClassAttributeConfigOutput,
        },
        "remove_attribute_config": {
            "canonical": {
                "name": "remove_attribute_config",
                "description": "Remove one AttributeConfig membership from this FunctionConfig.\n\nContract:\n- Mutates only function_config_attribute_configs on this FunctionConfig.\n- Attribute identity comes from committed semantic baseline truth when available.\n- Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.",
                "is_constructor": False,
            },
            "input": FunctionConfigRemoveAttributeConfigInput,
            "output": FunctionConfigRemoveAttributeConfigOutput,
        },
        "create_function_impl": {
            "canonical": {
                "name": "create_function_impl",
                "description": "Create or return the canonical execution rail (`FunctionImpl`) for this FunctionConfig.\n\nContract:\n- Parent (`FunctionConfig`) owns `function_impl` propagation.\n- One rail per FunctionConfig (idempotent under parent scope).\n- `impl_kind` carries whether this rail is an instruction body or an auto constructor template.",
                "is_constructor": False,
            },
            "input": FunctionConfigCreateFunctionImplInput,
            "output": FunctionConfigCreateFunctionImplOutput,
        },
        "create_invocation": {
            "canonical": {
                "name": "create_invocation",
                "description": "Create one deterministic invocation-plan step under this FunctionConfig.\n\nContract:\n- Parent (`FunctionConfig`) owns invocation membership propagation.\n- Identity is constructor-keyed on\n  `(function_config_id via parent path, position, kind, target_function_config_id, relationship_fingerprint)`.\n- `class_config_relationship_id` remains explicit traversal metadata; owner-local invocations use\n  `relationship_fingerprint = owner` and `class_config_relationship_id = null`.",
                "is_constructor": False,
            },
            "input": FunctionConfigCreateInvocationInput,
            "output": FunctionConfigCreateInvocationOutput,
        },
    },
}

__all__ = [
    "FunctionConfig",
    "FunctionConfigCreateInput",
    "FunctionConfigCreateOutput",
    "FunctionConfigUpdateConfigInput",
    "FunctionConfigUpdateConfigOutput",
    "FunctionConfigAddPrimitiveAttributeConfigInput",
    "FunctionConfigAddPrimitiveAttributeConfigOutput",
    "FunctionConfigAddEnumAttributeConfigInput",
    "FunctionConfigAddEnumAttributeConfigOutput",
    "FunctionConfigAddClassAttributeConfigInput",
    "FunctionConfigAddClassAttributeConfigOutput",
    "FunctionConfigRemoveAttributeConfigInput",
    "FunctionConfigRemoveAttributeConfigOutput",
    "FunctionConfigCreateFunctionImplInput",
    "FunctionConfigCreateFunctionImplOutput",
    "FunctionConfigCreateInvocationInput",
    "FunctionConfigCreateInvocationOutput",
    "FUNCTIONS",
]
