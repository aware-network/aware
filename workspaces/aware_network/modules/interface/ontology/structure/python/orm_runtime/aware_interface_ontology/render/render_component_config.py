from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

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
    from aware_interface_ontology.render.render_component_contract import RenderComponentContract


class RenderComponentConfig(ORMModel):
    # Relationships
    contracts: list[RenderComponentContract] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> RenderComponentConfig:
        """
        Create one reusable render component contract root.

        Contract:
        - This is the semantic root for a render component package.
        - Contracts describe renderer-neutral component ports and requirements.
        - State and actions still arrive through PaneRenderSpec bindings and canonical API rails.
        """

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentConfig):
            return value
        return RenderComponentConfig.validate_invocation_value(value)

    async def add_contract(
        self,
        component_ref: str,
        contract_version: int = 1,
        display_name: str | None = None,
        description: str | None = None,
        surface_kind: str | None = None,
    ) -> RenderComponentContract:
        """Add one reusable render component contract exposed by this config."""

        payload = {
            "component_ref": component_ref,
            "contract_version": contract_version,
            "display_name": display_name,
            "description": description,
            "surface_kind": surface_kind,
        }
        result = await invoke_instance(orm_model=self, function_name="add_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.render.render_component_contract import RenderComponentContract

        if isinstance(value, RenderComponentContract):
            return value
        return RenderComponentContract.validate_invocation_value(value)


class RenderComponentConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class RenderComponentConfigBuildOutput(BaseModel):
    value: RenderComponentConfig


class RenderComponentConfigAddContractInput(BaseModel):
    component_ref: str
    contract_version: int = Field(default=1)
    display_name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    surface_kind: str | None = Field(default=None)


class RenderComponentConfigAddContractOutput(BaseModel):
    value: RenderComponentContract


FUNCTIONS = {
    "RenderComponentConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one reusable render component contract root.\n\nContract:\n- This is the semantic root for a render component package.\n- Contracts describe renderer-neutral component ports and requirements.\n- State and actions still arrive through PaneRenderSpec bindings and canonical API rails.",
                "is_constructor": True,
            },
            "input": RenderComponentConfigBuildInput,
            "output": RenderComponentConfigBuildOutput,
        },
        "add_contract": {
            "canonical": {
                "name": "add_contract",
                "description": "Add one reusable render component contract exposed by this config.",
                "is_constructor": False,
            },
            "input": RenderComponentConfigAddContractInput,
            "output": RenderComponentConfigAddContractOutput,
        },
    },
}

__all__ = [
    "RenderComponentConfig",
    "RenderComponentConfigBuildInput",
    "RenderComponentConfigBuildOutput",
    "RenderComponentConfigAddContractInput",
    "RenderComponentConfigAddContractOutput",
    "FUNCTIONS",
]
