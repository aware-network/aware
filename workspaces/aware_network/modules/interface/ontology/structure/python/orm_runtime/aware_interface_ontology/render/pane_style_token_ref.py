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


class PaneStyleTokenRef(ORMModel):
    # Attributes
    token_key: str
    token_value: str | None = Field(default=None)

    # Foreign Keys
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.style_tokens")

    @classmethod
    async def create_via_pane_render_node(
        cls, pane_render_node_id: UUID, token_key: str, token_value: str | None = None
    ) -> PaneStyleTokenRef:
        """
        Attach renderer-adaptive style intent to a render node.

        Contract:
        - Tokens express semantic intent such as emphasis, density, status, or destructive.
        - Exact Flutter/CSS/Textual styling remains renderer policy, not ontology truth.
        """

        payload = {"pane_render_node_id": pane_render_node_id, "token_key": token_key, "token_value": token_value}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_pane_render_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneStyleTokenRef):
            return value
        return PaneStyleTokenRef.validate_invocation_value(value)


class PaneStyleTokenRefCreateViaPaneRenderNodeInput(BaseModel):
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.style_tokens")
    token_key: str
    token_value: str | None = Field(default=None)


class PaneStyleTokenRefCreateViaPaneRenderNodeOutput(BaseModel):
    value: PaneStyleTokenRef


FUNCTIONS = {
    "PaneStyleTokenRef": {
        "create_via_pane_render_node": {
            "canonical": {
                "name": "create_via_pane_render_node",
                "description": "Attach renderer-adaptive style intent to a render node.\n\nContract:\n- Tokens express semantic intent such as emphasis, density, status, or destructive.\n- Exact Flutter/CSS/Textual styling remains renderer policy, not ontology truth.",
                "is_constructor": True,
            },
            "input": PaneStyleTokenRefCreateViaPaneRenderNodeInput,
            "output": PaneStyleTokenRefCreateViaPaneRenderNodeOutput,
        },
    },
}

__all__ = [
    "PaneStyleTokenRef",
    "PaneStyleTokenRefCreateViaPaneRenderNodeInput",
    "PaneStyleTokenRefCreateViaPaneRenderNodeOutput",
    "FUNCTIONS",
]
