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

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import (
    ClassSelectionMode,
    ConditionLogicStrategy,
    ConditionOperator,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_reactivity_ontology.condition.condition_config_attribute_config import ConditionConfigAttributeConfig


class ConditionConfigClassConfig(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    condition_config_attribute_configs: list[ConditionConfigAttributeConfig] = Field(default_factory=list)

    # Attributes
    class_logic: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    class_selection: ClassSelectionMode = Field(default=ClassSelectionMode.base_class)
    require_existence: bool = Field(default=True)

    # Foreign Keys
    condition_config_id: UUID = Field(description="Foreign key for ConditionConfig.condition_config_class_configs")
    class_config_id: UUID = Field(description="Foreign key for ConditionConfigClassConfig.class_config")

    async def add_attribute_config(
        self, attribute_config_id: UUID, operator: ConditionOperator, negate: bool = False
    ) -> ConditionConfigAttributeConfig:
        """Attach an attribute-level policy node to this class policy node."""

        payload = {"attribute_config_id": attribute_config_id, "operator": operator, "negate": negate}
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_attribute_config import ConditionConfigAttributeConfig

        if isinstance(value, ConditionConfigAttributeConfig):
            return value
        return ConditionConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_condition_config(
        cls,
        condition_config_id: UUID,
        class_config_id: UUID,
        class_selection: ClassSelectionMode = ClassSelectionMode.base_class,
        class_logic: ConditionLogicStrategy = ConditionLogicStrategy.all,
        require_existence: bool = True,
    ) -> ConditionConfigClassConfig:
        """
        Create a class-level condition policy node.

        Contract:
        - Canonical constructor-owned creation for class policy nodes.
        - Deterministic id scoped by (condition_config_id, class_config_id).
        """

        payload = {
            "condition_config_id": condition_config_id,
            "class_config_id": class_config_id,
            "class_selection": class_selection,
            "class_logic": class_logic,
            "require_existence": require_existence,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_condition_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigClassConfig):
            return value
        return ConditionConfigClassConfig.validate_invocation_value(value)


class ConditionConfigClassConfigAddAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    operator: ConditionOperator
    negate: bool = Field(default=False)


class ConditionConfigClassConfigAddAttributeConfigOutput(BaseModel):
    value: ConditionConfigAttributeConfig


class ConditionConfigClassConfigCreateViaConditionConfigInput(BaseModel):
    condition_config_id: UUID = Field(description="Foreign key for ConditionConfig.condition_config_class_configs")
    class_config_id: UUID
    class_selection: ClassSelectionMode = Field(default=ClassSelectionMode.base_class)
    class_logic: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    require_existence: bool = Field(default=True)


class ConditionConfigClassConfigCreateViaConditionConfigOutput(BaseModel):
    value: ConditionConfigClassConfig


FUNCTIONS = {
    "ConditionConfigClassConfig": {
        "add_attribute_config": {
            "canonical": {
                "name": "add_attribute_config",
                "description": "Attach an attribute-level policy node to this class policy node.",
                "is_constructor": False,
            },
            "input": ConditionConfigClassConfigAddAttributeConfigInput,
            "output": ConditionConfigClassConfigAddAttributeConfigOutput,
        },
        "create_via_condition_config": {
            "canonical": {
                "name": "create_via_condition_config",
                "description": "Create a class-level condition policy node.\n\nContract:\n- Canonical constructor-owned creation for class policy nodes.\n- Deterministic id scoped by (condition_config_id, class_config_id).",
                "is_constructor": True,
            },
            "input": ConditionConfigClassConfigCreateViaConditionConfigInput,
            "output": ConditionConfigClassConfigCreateViaConditionConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigClassConfig",
    "ConditionConfigClassConfigAddAttributeConfigInput",
    "ConditionConfigClassConfigAddAttributeConfigOutput",
    "ConditionConfigClassConfigCreateViaConditionConfigInput",
    "ConditionConfigClassConfigCreateViaConditionConfigOutput",
    "FUNCTIONS",
]
