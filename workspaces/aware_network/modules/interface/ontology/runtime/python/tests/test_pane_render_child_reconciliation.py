from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

import pytest

from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
from aware_interface_ontology.render.pane_input_binding import PaneInputBinding
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderCapabilityKind,
    PaneRenderNodeKind,
    PaneStateBindingTargetProperty,
)
from aware_interface_ontology.render.pane_render_node import PaneRenderNode
from aware_interface_ontology.render.pane_render_spec import PaneRenderSpec
from aware_interface_ontology.render.pane_renderer_capability_requirement import (
    PaneRendererCapabilityRequirement,
)
from aware_interface_ontology.render.pane_state_binding import PaneStateBinding
from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef
from aware_interface_ontology.stable_ids import (
    stable_pane_action_binding_id,
    stable_pane_input_binding_id,
    stable_pane_render_node_id,
    stable_pane_renderer_capability_requirement_id,
    stable_pane_state_binding_id,
    stable_pane_style_token_ref_id,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    reset_invocation_provider,
    set_invocation_provider,
)


class _PaneRenderInvocationProvider:
    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        if isinstance(orm_model, PaneRenderSpec) and function_name == "add_node":
            from aware_interface.handlers.impl.render.pane_render_spec import add_node

            return await add_node(pane_render_spec=orm_model, **payload)
        if isinstance(orm_model, PaneRenderSpec) and function_name == "require_renderer_capability":
            from aware_interface.handlers.impl.render.pane_render_spec import (
                require_renderer_capability,
            )

            return await require_renderer_capability(
                pane_render_spec=orm_model,
                **payload,
            )
        if isinstance(orm_model, PaneRenderNode) and function_name == "bind_state":
            from aware_interface.handlers.impl.render.pane_render_node import bind_state

            return await bind_state(pane_render_node=orm_model, **payload)
        if isinstance(orm_model, PaneRenderNode) and function_name == "bind_action":
            from aware_interface.handlers.impl.render.pane_render_node import bind_action

            return await bind_action(pane_render_node=orm_model, **payload)
        if isinstance(orm_model, PaneRenderNode) and function_name == "add_style_token":
            from aware_interface.handlers.impl.render.pane_render_node import (
                add_style_token,
            )

            return await add_style_token(pane_render_node=orm_model, **payload)
        if isinstance(orm_model, PaneActionBinding) and function_name == "bind_input":
            from aware_interface.handlers.impl.render.pane_action_binding import (
                bind_input,
            )

            return await bind_input(pane_action_binding=orm_model, **payload)
        raise AssertionError(f"Unexpected pane render invocation: {type(orm_model).__name__}.{function_name}")

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        raise AssertionError(f"Unexpected constructor invocation: {orm_class.__name__}.{function_name}")


@pytest.mark.asyncio
async def test_pane_render_facades_reconcile_reused_child_relationship_fks() -> None:
    pane_render_spec_id = uuid4()
    node_id = stable_pane_render_node_id(
        pane_render_spec_id=pane_render_spec_id,
        node_key="root",
    )
    state_binding_id = stable_pane_state_binding_id(
        pane_render_node_id=node_id,
        binding_key="title",
    )
    action_binding_id = stable_pane_action_binding_id(
        pane_render_node_id=node_id,
        binding_key="activate",
    )
    input_binding_id = stable_pane_input_binding_id(
        pane_action_binding_id=action_binding_id,
        payload_path="identity.name",
    )
    style_token_id = stable_pane_style_token_ref_id(
        pane_render_node_id=node_id,
        token_key="density",
    )
    requirement_id = stable_pane_renderer_capability_requirement_id(
        pane_render_spec_id=pane_render_spec_id,
        capability_kind=PaneRenderCapabilityKind.node_kind.value,
        capability_key="column",
    )

    stale_input = PaneInputBinding.model_construct(
        id=input_binding_id,
        payload_path="identity.name",
    )
    stale_action = PaneActionBinding.model_construct(
        id=action_binding_id,
        binding_key="activate",
        event=PaneActionEvent.activate,
        action_key="submit",
        input_bindings=[stale_input],
    )
    stale_state = PaneStateBinding.model_construct(
        id=state_binding_id,
        binding_key="title",
        target_property=PaneStateBindingTargetProperty.text,
        json_path="$.old_title",
    )
    stale_token = PaneStyleTokenRef.model_construct(
        id=style_token_id,
        token_key="density",
        token_value="comfortable",
    )
    stale_node = PaneRenderNode.model_construct(
        id=node_id,
        node_key="root",
        node_kind=PaneRenderNodeKind.column,
        state_bindings=[stale_state],
        action_bindings=[stale_action],
        style_tokens=[stale_token],
        component_contract=None,
    )
    stale_requirement = PaneRendererCapabilityRequirement.model_construct(
        id=requirement_id,
        capability_kind=PaneRenderCapabilityKind.node_kind,
        capability_key="column",
    )
    pane_render_spec = PaneRenderSpec.model_construct(
        id=pane_render_spec_id,
        pane_config_id=uuid4(),
        name="demo",
        spec_version="0.1.0",
        root_node_key="root",
        nodes=[stale_node],
        renderer_requirements=[stale_requirement],
    )

    token = set_invocation_provider(_PaneRenderInvocationProvider())
    try:
        node = await pane_render_spec.add_node(
            node_key="root",
            node_kind=PaneRenderNodeKind.component,
            order=7,
            component_ref="aware.storage.media.image",
            fallback_node_kind=PaneRenderNodeKind.text,
            fallback_text="Image unavailable",
        )
        state = await node.bind_state(
            binding_key="title",
            target_property=PaneStateBindingTargetProperty.text,
            json_path="$.title",
        )
        action = await node.bind_action(
            binding_key="activate",
            event=PaneActionEvent.activate,
            action_key="submit",
        )
        input_binding = await action.bind_input(
            payload_path="identity.name",
            source_node_key="name_input",
        )
        style_token = await node.add_style_token(
            token_key="density",
            token_value="compact",
        )
        requirement = await pane_render_spec.require_renderer_capability(
            capability_kind=PaneRenderCapabilityKind.node_kind,
            capability_key="column",
        )
    finally:
        reset_invocation_provider(token)

    assert node is stale_node
    assert node.pane_render_spec_id == pane_render_spec_id
    assert node.node_kind is PaneRenderNodeKind.component
    assert node.component_ref == "aware.storage.media.image"
    assert node.fallback_node_kind is PaneRenderNodeKind.text
    assert node.fallback_text == "Image unavailable"
    assert state is stale_state
    assert state.pane_render_node_id == node_id
    assert state.json_path == "$.title"
    assert action is stale_action
    assert action.pane_render_node_id == node_id
    assert input_binding is stale_input
    assert input_binding.pane_action_binding_id == action_binding_id
    assert input_binding.source_node_key == "name_input"
    assert style_token is stale_token
    assert style_token.pane_render_node_id == node_id
    assert style_token.token_value == "compact"
    assert requirement is stale_requirement
    assert requirement.pane_render_spec_id == pane_render_spec_id

    PaneRenderSpec.model_validate(pane_render_spec.model_dump(mode="json"))
