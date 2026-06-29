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
    from aware_code_ontology.enum.code_section_enum import CodeSectionEnum
    from aware_meta_ontology.enum.enum_option import EnumOption


class EnumConfig(ORMModel):
    # Relationships
    enum_options: list[EnumOption] = Field(default_factory=list)
    code_section_enum: CodeSectionEnum | None = Field(default=None, exclude=True)

    # Attributes
    enum_fqn: str
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    object_config_graph_node_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphNode.enum_config"
    )
    code_section_enum_id: UUID | None = Field(default=None, description="Foreign key for EnumConfig.code_section_enum")

    async def create_enum_option(
        self, value: str, label: str | None = None, description: str | None = None, position: int = 0
    ) -> EnumOption:
        """Materialize one EnumOption under this EnumConfig."""

        payload = {"value": value, "label": label, "description": description, "position": position}
        result = await invoke_instance(orm_model=self, function_name="create_enum_option", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.enum.enum_option import EnumOption

        if isinstance(value, EnumOption):
            return value
        return EnumOption.validate_invocation_value(value)

    async def delete_enum_option(self, value: str, enum_option_id: UUID | None = None) -> None:
        """
        Remove one EnumOption membership from this EnumConfig.

        Contract:
        - Mutates only enum_options on this EnumConfig.
        - EnumOption identity comes from committed semantic baseline truth when available.
        - Rooted OIG commit reachability owns stale EnumOption deletion after membership removal.
        """

        payload = {"value": value, "enum_option_id": enum_option_id}
        await invoke_instance(orm_model=self, function_name="delete_enum_option", payload=payload)
        return None

    async def update_config(self, description: str | None = None) -> None:
        """
        Update mutable EnumConfig metadata.

        Contract:
        - `enum_fqn` and `name` are identity and are not mutable here.
        - EnumOption membership and option metadata changes use explicit
          EnumConfig/EnumOption ontology functions.
        - This full-payload update treats nullable arguments as current
          semantic truth.
        """

        payload = {"description": description}
        await invoke_instance(orm_model=self, function_name="update_config", payload=payload)
        return None

    @classmethod
    async def create_via_object_config_graph_node(
        cls,
        object_config_graph_node_id: UUID,
        enum_fqn: str,
        name: str,
        description: str | None = None,
        values: list[str] = [],
    ) -> EnumConfig:
        """Create deterministic EnumConfig with optional ordered EnumOption values."""

        payload = {
            "object_config_graph_node_id": object_config_graph_node_id,
            "enum_fqn": enum_fqn,
            "name": name,
            "description": description,
            "values": values,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_config_graph_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnumConfig):
            return value
        return EnumConfig.validate_invocation_value(value)


class EnumConfigCreateEnumOptionInput(BaseModel):
    value: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)


class EnumConfigCreateEnumOptionOutput(BaseModel):
    value: EnumOption


class EnumConfigDeleteEnumOptionInput(BaseModel):
    value: str
    enum_option_id: UUID | None = Field(default=None)


class EnumConfigDeleteEnumOptionOutput(BaseModel):
    pass


class EnumConfigUpdateConfigInput(BaseModel):
    description: str | None = Field(default=None)


class EnumConfigUpdateConfigOutput(BaseModel):
    pass


class EnumConfigCreateViaObjectConfigGraphNodeInput(BaseModel):
    object_config_graph_node_id: UUID = Field(description="Foreign key for ObjectConfigGraphNode.enum_config")
    enum_fqn: str
    name: str
    description: str | None = Field(default=None)
    values: list[str] = Field(default_factory=list)


class EnumConfigCreateViaObjectConfigGraphNodeOutput(BaseModel):
    value: EnumConfig


FUNCTIONS = {
    "EnumConfig": {
        "create_enum_option": {
            "canonical": {
                "name": "create_enum_option",
                "description": "Materialize one EnumOption under this EnumConfig.",
                "is_constructor": False,
            },
            "input": EnumConfigCreateEnumOptionInput,
            "output": EnumConfigCreateEnumOptionOutput,
        },
        "delete_enum_option": {
            "canonical": {
                "name": "delete_enum_option",
                "description": "Remove one EnumOption membership from this EnumConfig.\n\nContract:\n- Mutates only enum_options on this EnumConfig.\n- EnumOption identity comes from committed semantic baseline truth when available.\n- Rooted OIG commit reachability owns stale EnumOption deletion after membership removal.",
                "is_constructor": False,
            },
            "input": EnumConfigDeleteEnumOptionInput,
            "output": EnumConfigDeleteEnumOptionOutput,
        },
        "update_config": {
            "canonical": {
                "name": "update_config",
                "description": "Update mutable EnumConfig metadata.\n\nContract:\n- `enum_fqn` and `name` are identity and are not mutable here.\n- EnumOption membership and option metadata changes use explicit\n  EnumConfig/EnumOption ontology functions.\n- This full-payload update treats nullable arguments as current\n  semantic truth.",
                "is_constructor": False,
            },
            "input": EnumConfigUpdateConfigInput,
            "output": EnumConfigUpdateConfigOutput,
        },
        "create_via_object_config_graph_node": {
            "canonical": {
                "name": "create_via_object_config_graph_node",
                "description": "Create deterministic EnumConfig with optional ordered EnumOption values.",
                "is_constructor": True,
            },
            "input": EnumConfigCreateViaObjectConfigGraphNodeInput,
            "output": EnumConfigCreateViaObjectConfigGraphNodeOutput,
        },
    },
}

__all__ = [
    "EnumConfig",
    "EnumConfigCreateEnumOptionInput",
    "EnumConfigCreateEnumOptionOutput",
    "EnumConfigDeleteEnumOptionInput",
    "EnumConfigDeleteEnumOptionOutput",
    "EnumConfigUpdateConfigInput",
    "EnumConfigUpdateConfigOutput",
    "EnumConfigCreateViaObjectConfigGraphNodeInput",
    "EnumConfigCreateViaObjectConfigGraphNodeOutput",
    "FUNCTIONS",
]
