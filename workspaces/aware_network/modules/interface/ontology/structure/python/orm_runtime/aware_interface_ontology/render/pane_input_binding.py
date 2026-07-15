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


class PaneInputBinding(ORMModel):
    # Attributes
    payload_path: str
    source_node_key: str | None = Field(default=None)
    source_json_path: str | None = Field(default=None)
    literal_value: str | None = Field(default=None)

    # Foreign Keys
    pane_action_binding_id: UUID = Field(description="Foreign key for PaneActionBinding.input_bindings")

    @classmethod
    async def create_via_pane_action_binding(
        cls,
        pane_action_binding_id: UUID,
        payload_path: str,
        source_node_key: str | None = None,
        source_json_path: str | None = None,
        literal_value: str | None = None,
    ) -> PaneInputBinding:
        """
        Create one deterministic action payload binding.

        Contract:
        - Renderer-local input values are payload inputs only, never canonical state.
        - Canonical state values can be copied through `source_json_path`.
        - Constants can be supplied through `literal_value` for simple action payloads.
        """

        payload = {
            "pane_action_binding_id": pane_action_binding_id,
            "payload_path": payload_path,
            "source_node_key": source_node_key,
            "source_json_path": source_json_path,
            "literal_value": literal_value,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_pane_action_binding", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PaneInputBinding):
            return value
        return PaneInputBinding.validate_invocation_value(value)


class PaneInputBindingCreateViaPaneActionBindingInput(BaseModel):
    pane_action_binding_id: UUID = Field(description="Foreign key for PaneActionBinding.input_bindings")
    payload_path: str
    source_node_key: str | None = Field(default=None)
    source_json_path: str | None = Field(default=None)
    literal_value: str | None = Field(default=None)


class PaneInputBindingCreateViaPaneActionBindingOutput(BaseModel):
    value: PaneInputBinding


FUNCTIONS = {
    "PaneInputBinding": {
        "create_via_pane_action_binding": {
            "canonical": {
                "name": "create_via_pane_action_binding",
                "description": "Create one deterministic action payload binding.\n\nContract:\n- Renderer-local input values are payload inputs only, never canonical state.\n- Canonical state values can be copied through `source_json_path`.\n- Constants can be supplied through `literal_value` for simple action payloads.",
                "is_constructor": True,
            },
            "input": PaneInputBindingCreateViaPaneActionBindingInput,
            "output": PaneInputBindingCreateViaPaneActionBindingOutput,
        },
    },
}

__all__ = [
    "PaneInputBinding",
    "PaneInputBindingCreateViaPaneActionBindingInput",
    "PaneInputBindingCreateViaPaneActionBindingOutput",
    "FUNCTIONS",
]
