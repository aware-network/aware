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
)

if TYPE_CHECKING:
    from aware_reactivity_ontology.condition.condition_config_class_config import ConditionConfigClassConfig


class ConditionConfig(ORMModel):
    # Relationships
    condition_config_class_configs: list[ConditionConfigClassConfig] = Field(default_factory=list)

    # Attributes
    name: str
    description: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    logic_strategy: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)

    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
        logic_strategy: ConditionLogicStrategy = ConditionLogicStrategy.all,
        is_enabled: bool = True,
        is_system: bool = False,
    ) -> ConditionConfig:
        """
        Create a canonical condition policy root.

        Contract:
        - Constructor-owned creation path for condition policy roots.
        - Initial evaluation flags and logic strategy are persisted at creation time.
        """

        payload = {
            "name": name,
            "description": description,
            "logic_strategy": logic_strategy,
            "is_enabled": is_enabled,
            "is_system": is_system,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfig):
            return value
        return ConditionConfig.validate_invocation_value(value)

    async def add_class_config(
        self,
        class_config_id: UUID,
        class_selection: ClassSelectionMode = ClassSelectionMode.base_class,
        class_logic: ConditionLogicStrategy = ConditionLogicStrategy.all,
        require_existence: bool = True,
    ) -> ConditionConfigClassConfig:
        """
        Attach a class-level policy node to this condition root.

        Contract:
        - Canonical edge creation through the ConditionConfig root.
        - Deterministic id scoped by (condition_config_id, class_config_id).
        """

        payload = {
            "class_config_id": class_config_id,
            "class_selection": class_selection,
            "class_logic": class_logic,
            "require_existence": require_existence,
        }
        result = await invoke_instance(orm_model=self, function_name="add_class_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_class_config import ConditionConfigClassConfig

        if isinstance(value, ConditionConfigClassConfig):
            return value
        return ConditionConfigClassConfig.validate_invocation_value(value)


class ConditionConfigCreateInput(BaseModel):
    name: str
    description: str
    logic_strategy: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)


class ConditionConfigCreateOutput(BaseModel):
    value: ConditionConfig


class ConditionConfigAddClassConfigInput(BaseModel):
    class_config_id: UUID
    class_selection: ClassSelectionMode = Field(default=ClassSelectionMode.base_class)
    class_logic: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    require_existence: bool = Field(default=True)


class ConditionConfigAddClassConfigOutput(BaseModel):
    value: ConditionConfigClassConfig


FUNCTIONS = {
    "ConditionConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a canonical condition policy root.\n\nContract:\n- Constructor-owned creation path for condition policy roots.\n- Initial evaluation flags and logic strategy are persisted at creation time.",
                "is_constructor": True,
            },
            "input": ConditionConfigCreateInput,
            "output": ConditionConfigCreateOutput,
        },
        "add_class_config": {
            "canonical": {
                "name": "add_class_config",
                "description": "Attach a class-level policy node to this condition root.\n\nContract:\n- Canonical edge creation through the ConditionConfig root.\n- Deterministic id scoped by (condition_config_id, class_config_id).",
                "is_constructor": False,
            },
            "input": ConditionConfigAddClassConfigInput,
            "output": ConditionConfigAddClassConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfig",
    "ConditionConfigCreateInput",
    "ConditionConfigCreateOutput",
    "ConditionConfigAddClassConfigInput",
    "ConditionConfigAddClassConfigOutput",
    "FUNCTIONS",
]
