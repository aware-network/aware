from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology
from aware_interface_ontology.render.pane_render_enums import PaneRenderNodeKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class RenderComponentFallbackPolicy(ORMModel):
    # Attributes
    policy_key: str
    fallback_kind: str
    fallback_component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.fallback_policies")

    @classmethod
    async def build_via_render_component_contract(
        cls,
        render_component_contract_id: UUID,
        policy_key: str,
        fallback_kind: str,
        fallback_component_ref: str | None = None,
        fallback_node_kind: PaneRenderNodeKind | None = None,
        description: str | None = None,
    ) -> RenderComponentFallbackPolicy:
        """
        Create one deterministic component fallback policy.

        Contract:
        - Fallback policy is declared by the component package, not improvised by a pane renderer.
        - `fallback_component_ref` supports a less capable component replacement.
        - `fallback_node_kind` supports lowering to primitive PaneRenderSpec nodes.
        """

        payload = {
            "render_component_contract_id": render_component_contract_id,
            "policy_key": policy_key,
            "fallback_kind": fallback_kind,
            "fallback_component_ref": fallback_component_ref,
            "fallback_node_kind": fallback_node_kind,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_render_component_contract", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RenderComponentFallbackPolicy):
            return value
        return RenderComponentFallbackPolicy.validate_invocation_value(value)


class RenderComponentFallbackPolicyBuildViaRenderComponentContractInput(BaseModel):
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.fallback_policies")
    policy_key: str
    fallback_kind: str
    fallback_component_ref: str | None = Field(default=None)
    fallback_node_kind: PaneRenderNodeKind | None = Field(default=None)
    description: str | None = Field(default=None)


class RenderComponentFallbackPolicyBuildViaRenderComponentContractOutput(BaseModel):
    value: RenderComponentFallbackPolicy


FUNCTIONS = {
    "RenderComponentFallbackPolicy": {
        "build_via_render_component_contract": {
            "canonical": {
                "name": "build_via_render_component_contract",
                "description": "Create one deterministic component fallback policy.\n\nContract:\n- Fallback policy is declared by the component package, not improvised by a pane renderer.\n- `fallback_component_ref` supports a less capable component replacement.\n- `fallback_node_kind` supports lowering to primitive PaneRenderSpec nodes.",
                "is_constructor": True,
            },
            "input": RenderComponentFallbackPolicyBuildViaRenderComponentContractInput,
            "output": RenderComponentFallbackPolicyBuildViaRenderComponentContractOutput,
        },
    },
}

__all__ = [
    "RenderComponentFallbackPolicy",
    "RenderComponentFallbackPolicyBuildViaRenderComponentContractInput",
    "RenderComponentFallbackPolicyBuildViaRenderComponentContractOutput",
    "FUNCTIONS",
]
