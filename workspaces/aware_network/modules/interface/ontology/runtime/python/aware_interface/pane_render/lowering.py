# flake8: noqa: E501
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from aware_interface.pane_render.ir import (
    PaneRenderActionBinding,
    PaneRenderInputBinding,
    PaneRenderNode,
    PaneRenderSpecIR,
    PaneRenderStateBinding,
)

_NON_LOCAL_INPUT_SOURCE_ROOTS = frozenset({"pane", "focus", "object", "action"})


@dataclass(frozen=True, slots=True)
class PaneRenderLoweringError(ValueError):
    message: str

    def __str__(self) -> str:
        return self.message


def lower_pane_render_spec_to_payload(spec: PaneRenderSpecIR) -> dict[str, object]:
    """Lower authored pane render IR to the existing render-spec source payload.

    The returned mapping intentionally matches the pane-local
    `*.render_spec.json` compatibility shape consumed by the Interface builder.
    Runtime-only fields such as `spec_id`, `pane_kind`, state model ids, and
    pane action relation ids remain builder/enrichment responsibility.
    """

    root_node_key = _effective_root_key(spec)
    orders = _node_orders(spec=spec, root_node_key=root_node_key)
    spec_name = _render_spec_name(spec)
    payload: dict[str, object] = {
        "name": spec_name,
        "spec_version": spec.version or "0.1.0",
        "root_node_key": root_node_key,
        "nodes": [_lower_node(node=node, root_node_key=root_node_key, order=orders[node.key]) for node in spec.nodes],
        "renderer_requirements": [
            {
                "capability_kind": requirement.capability_kind,
                "capability_key": requirement.capability_key,
                "is_required": True,
            }
            for requirement in spec.requirements
        ],
    }
    if spec.view:
        payload["view_ref"] = spec.view
    if spec.pane_name:
        payload["pane_name"] = spec.pane_name
    return payload


def lower_pane_render_specs_to_payloads(specs: tuple[PaneRenderSpecIR, ...]) -> tuple[dict[str, object], ...]:
    return tuple(lower_pane_render_spec_to_payload(spec) for spec in specs)


def _render_spec_name(spec: PaneRenderSpecIR) -> str:
    if spec.name.casefold().startswith(f"{spec.pane_name.casefold()}_"):
        return spec.name
    return f"{spec.pane_name}_{spec.name}"


def _lower_node(*, node: PaneRenderNode, root_node_key: str, order: int) -> dict[str, object]:
    parent_key = _effective_parent_key(node=node, root_node_key=root_node_key)
    payload: dict[str, object] = {
        "node_key": node.key,
        "node_kind": node.kind,
        "order": order,
    }
    if parent_key:
        payload["parent_node_key"] = parent_key
    if node.semantic_role:
        payload["semantic_role"] = node.semantic_role
    if node.slot:
        payload["slot_key"] = node.slot
    if node.label is not None:
        payload["label"] = node.label
    if node.text is not None:
        payload["text"] = node.text
    if node.placeholder is not None:
        payload["placeholder"] = node.placeholder
    if node.component_ref is not None:
        payload["component_ref"] = node.component_ref
    if node.fallback_node_kind is not None:
        payload["fallback_node_kind"] = node.fallback_node_kind
    if node.fallback_text is not None:
        payload["fallback_text"] = node.fallback_text

    state_bindings = [_lower_state_binding(binding) for binding in node.state_bindings]
    if state_bindings:
        payload["state_bindings"] = state_bindings

    action_bindings = [_lower_action_binding(node=node, binding=binding) for binding in node.action_bindings]
    if action_bindings:
        payload["action_bindings"] = action_bindings

    style_tokens = [
        {
            key: value
            for key, value in {
                "token_key": token.token,
                "token_value": token.value,
            }.items()
            if value is not None
        }
        for token in node.style_tokens
    ]
    if style_tokens:
        payload["style_tokens"] = style_tokens

    return payload


def _node_order(*, node: PaneRenderNode, fallback: int) -> int:
    if node.order is None:
        return fallback
    if isinstance(node.order, int):
        return node.order
    if isinstance(node.order, float) and node.order.is_integer():
        return int(node.order)
    raise PaneRenderLoweringError(f"Pane render node {node.key!r} has non-integer order {node.order!r}")


def _lower_state_binding(binding: PaneRenderStateBinding) -> dict[str, object]:
    state_attribute = _state_attribute_ref(binding)
    return {
        "binding_key": _state_binding_key(binding),
        "target_property": binding.target_property,
        "json_path": _state_path_to_json_path(binding.state_path),
        "state_attribute_ref": state_attribute,
        "transform": binding.transform or _default_transform_for_target(binding.target_property),
        **(
            {"component_input_port_key": binding.component_input_port_key}
            if binding.component_input_port_key is not None
            else {}
        ),
        **({"fallback_value": binding.fallback} if binding.fallback is not None else {}),
    }


def _state_binding_key(binding: PaneRenderStateBinding) -> str:
    attribute_key = _token_key(_state_attribute_ref(binding))
    target_key = _token_key(binding.target_property)
    if attribute_key == target_key or attribute_key.endswith(f"_{target_key}"):
        return attribute_key
    return _token_key(f"{attribute_key}_{target_key}")


def _lower_action_binding(*, node: PaneRenderNode, binding: PaneRenderActionBinding) -> dict[str, object]:
    action_key, action_kind = _runtime_action_identity(binding)
    payload: dict[str, object] = {
        "binding_key": _action_binding_key(binding),
        "event": binding.event,
        "action_key": action_key,
        "action_kind": action_kind,
        "label": node.label or _action_label(binding),
        "receipt_policy": binding.receipt_policy or "none",
        "input_bindings": [_lower_input_binding(input_binding) for input_binding in binding.input_bindings],
    }
    if binding.action_kind != "view":
        raise PaneRenderLoweringError(f"Unsupported pane render action kind: {binding.action_kind!r}")
    payload["view_action_key"] = binding.action
    return payload


def _runtime_action_identity(binding: PaneRenderActionBinding) -> tuple[str, str]:
    if binding.action_kind == "view":
        return (binding.action, "view_action")
    raise PaneRenderLoweringError(f"Unsupported pane render action kind: {binding.action_kind!r}")


def _action_binding_key(binding: PaneRenderActionBinding) -> str:
    return _token_key(binding.action.rsplit(".", 1)[-1] or binding.event)


def _action_label(binding: PaneRenderActionBinding) -> str:
    return " ".join(part.capitalize() for part in _action_binding_key(binding).split("_") if part)


def _lower_input_binding(binding: PaneRenderInputBinding) -> dict[str, object]:
    payload: dict[str, object] = {"payload_path": binding.payload_path}
    source = binding.source.strip()
    if _is_state_path(source):
        payload["source_json_path"] = _state_path_to_json_path(source)
        return payload
    if _input_source_root(source) in _NON_LOCAL_INPUT_SOURCE_ROOTS:
        raise PaneRenderLoweringError(
            f"Pane render input binding {binding.payload_path!r} uses unsupported non-state source {source!r}"
        )
    payload["source_node_key"] = source
    return payload


def _state_path_to_json_path(path: str) -> str:
    raw = path.strip()
    if raw == "state":
        return "$"
    if raw.startswith("state."):
        suffix = raw.removeprefix("state.").strip(".")
        if suffix:
            return f"$.{suffix}"
    raise PaneRenderLoweringError(f"Pane render state path must start with 'state.': {path!r}")


def _is_state_path(path: str) -> bool:
    raw = path.strip()
    return raw == "state" or raw.startswith("state.")


def _input_source_root(source: str) -> str:
    return source.split(".", 1)[0].strip()


def _effective_root_key(spec: PaneRenderSpecIR) -> str:
    if spec.root:
        return spec.root
    for node in spec.nodes:
        if "." not in node.key:
            return node.key
    return "root"


def _node_orders(*, spec: PaneRenderSpecIR, root_node_key: str) -> dict[str, int]:
    sibling_counts: dict[str | None, int] = {}
    orders: dict[str, int] = {}
    for node in spec.nodes:
        parent_key = _effective_parent_key(node=node, root_node_key=root_node_key)
        fallback = sibling_counts.get(parent_key, 0)
        orders[node.key] = _node_order(node=node, fallback=fallback)
        sibling_counts[parent_key] = fallback + 1
    return orders


def _effective_parent_key(*, node: PaneRenderNode, root_node_key: str) -> str | None:
    if node.parent_key:
        return node.parent_key
    path_parent = _path_parent_key(node.key)
    if path_parent:
        return path_parent
    if node.key != root_node_key:
        return root_node_key
    return None


def _path_parent_key(node_key: str) -> str | None:
    if "." not in node_key:
        return None
    return node_key.rsplit(".", 1)[0] or None


def _state_attribute_ref(binding: PaneRenderStateBinding) -> str:
    if binding.state_attribute:
        return binding.state_attribute
    segments = _state_path_segments(binding.state_path)
    if not segments:
        raise PaneRenderLoweringError(
            f"Pane render binding {binding.target_property!r} cannot infer state attribute from {binding.state_path!r}"
        )
    root = segments[0]
    if root in {"item", "parent", "item_index", "parent_index"}:
        raise PaneRenderLoweringError(
            f"Pane render binding {binding.target_property!r} path {binding.state_path!r} "
            "requires explicit state attribute authority"
        )
    return root


def _state_path_segments(path: str) -> tuple[str, ...]:
    raw = path.strip()
    if raw == "state":
        return ()
    if raw.startswith("state."):
        raw = raw.removeprefix("state.").strip(".")
    return tuple(part for part in raw.split(".") if part)


def _default_transform_for_target(target_property: str) -> str:
    normalized = _token_key(target_property)
    if normalized in {"text", "value", "tone"}:
        return "text"
    return "raw"


def _token_key(value: str) -> str:
    return "_".join(part for part in cast(str, value or "").strip().casefold().replace("-", "_").split("_") if part)
