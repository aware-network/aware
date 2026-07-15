from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class RenderComponentCapability(ORMModel):
    # Attributes
    capability_kind: str
    capability_key: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.capabilities")

    @classmethod
    async def build_via_render_component_contract(
        cls,
        render_component_contract_id: UUID,
        capability_kind: str,
        capability_key: str,
        is_required: bool = True,
        description: str | None = None,
    ) -> RenderComponentCapability:
        """
        Create one renderer capability requirement or preference.

        Contract:
        - Capability kind/key are renderer-neutral labels.
        - Required capabilities must be satisfied or fall back according to policy.
        - Preferred capabilities may enhance native rendering without changing pane semantics.
        """

        payload = {
            "render_component_contract_id": render_component_contract_id,
            "capability_kind": capability_kind,
            "capability_key": capability_key,
            "is_required": is_required,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_render_component_contract", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentCapability):
            return value
        return RenderComponentCapability.validate_invocation_value(value)


class RenderComponentCapabilityBuildViaRenderComponentContractInput(BaseModel):
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.capabilities")
    capability_kind: str
    capability_key: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)


class RenderComponentCapabilityBuildViaRenderComponentContractOutput(BaseModel):
    value: RenderComponentCapability


FUNCTIONS = {
    "RenderComponentCapability": {
        "build_via_render_component_contract": {
            "canonical": {
                "name": "build_via_render_component_contract",
                "description": "Create one renderer capability requirement or preference.\n\nContract:\n- Capability kind/key are renderer-neutral labels.\n- Required capabilities must be satisfied or fall back according to policy.\n- Preferred capabilities may enhance native rendering without changing pane semantics.",
                "is_constructor": True,
            },
            "input": RenderComponentCapabilityBuildViaRenderComponentContractInput,
            "output": RenderComponentCapabilityBuildViaRenderComponentContractOutput,
        },
    },
}

__all__ = [
    "RenderComponentCapability",
    "RenderComponentCapabilityBuildViaRenderComponentContractInput",
    "RenderComponentCapabilityBuildViaRenderComponentContractOutput",
    "FUNCTIONS",
]
