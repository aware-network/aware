# flake8: noqa: E501
from __future__ import annotations
import ast
from dataclasses import dataclass
from typing import cast

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_interface.pane_render.ir import (
    PaneRenderActionBinding,
    PaneRenderActionKind,
    PaneRenderInputBinding,
    PaneRenderNode,
    PaneRenderRequirement,
    PaneRenderSpecIR,
    PaneRenderStateBinding,
    PaneRenderStyleToken,
)


class PaneRenderParseError(ValueError):
    """Raised when `.aware pane { render ... }` parsing fails."""


@dataclass(frozen=True, slots=True)
class PaneRenderValidationError(ValueError):
    errors: tuple[str, ...]

    def __str__(self) -> str:
        return "; ".join(self.errors)


_PARSER = Parser(language=AWARE_LANGUAGE)
_NON_LOCAL_INPUT_SOURCE_ROOTS = frozenset({"state", "pane", "focus", "object", "action"})


def parse_pane_render_specs(source: str) -> tuple[PaneRenderSpecIR, ...]:
    """Parse and validate authored pane render specs from Aware source."""

    source_bytes = source.encode("utf-8")
    tree = _PARSER.parse(source_bytes)
    if tree.root_node.has_error:
        raise PaneRenderParseError("Aware source contains syntax errors")

    specs: list[PaneRenderSpecIR] = []
    errors: list[str] = []
    for pane_node in _find_nodes(tree.root_node, "pane_def"):
        pane_name = _required_field_text(pane_node, "name")
        render_names: set[str] = set()
        for render_node in _render_nodes_for_pane(pane_node):
            spec = _parse_render_spec(pane_name=pane_name, render_node=render_node)
            if spec.name in render_names:
                errors.append(f"pane {pane_name!r} declares duplicate render {spec.name!r}")
            render_names.add(spec.name)
            errors.extend(_validate_render_spec(spec))
            specs.append(spec)

    if errors:
        raise PaneRenderValidationError(tuple(errors))
    return tuple(specs)


def _find_nodes(node: Node, node_type: str) -> list[Node]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_find_nodes(child, node_type))
    return matches


def _render_nodes_for_pane(pane_node: Node) -> tuple[Node, ...]:
    body = pane_node.child_by_field_name("body")
    if body is None:
        return ()

    render_nodes: list[Node] = []
    for child in body.named_children:
        inner = _unwrap_item(child)
        if inner.type == "pane_render_def":
            render_nodes.append(inner)
    return tuple(render_nodes)


def _parse_render_spec(*, pane_name: str, render_node: Node) -> PaneRenderSpecIR:
    name = _required_field_text(render_node, "name")
    body = render_node.child_by_field_name("body")
    if body is None:
        raise PaneRenderParseError(f"render {name!r} missing body")

    view: str | None = None
    version: str | None = None
    root: str | None = None
    requirements: list[PaneRenderRequirement] = []
    nodes: list[PaneRenderNode] = []

    for child in body.named_children:
        item = _unwrap_item(child)
        if item.type == "pane_render_view_decl":
            view = _required_field_text(item, "view")
        elif item.type == "pane_render_version_decl":
            version = _decode_string_field(item, "version")
        elif item.type == "pane_render_root_decl":
            root = _required_field_text(item, "node")
        elif item.type == "pane_render_require_decl":
            requirements.append(
                PaneRenderRequirement(
                    capability_kind=_required_field_text(item, "capability_kind"),
                    capability_key=_required_field_text(item, "capability_key"),
                )
            )
        elif item.type == "pane_render_node_def":
            nodes.append(_parse_node(item))

    return PaneRenderSpecIR(
        pane_name=pane_name,
        name=name,
        view=view,
        version=version,
        root=root,
        requirements=tuple(requirements),
        nodes=tuple(nodes),
    )


def _parse_node(node: Node) -> PaneRenderNode:
    text: str | None = None
    label: str | None = None
    placeholder: str | None = None
    component_ref: str | None = None
    fallback_node_kind: str | None = None
    fallback_text: str | None = None
    state_bindings: list[PaneRenderStateBinding] = []
    action_bindings: list[PaneRenderActionBinding] = []
    style_tokens: list[PaneRenderStyleToken] = []

    body = node.child_by_field_name("body")
    if body is not None:
        for child in body.named_children:
            item = _unwrap_item(child)
            if item.type == "pane_render_text_stmt":
                text = _decode_string_field(item, "value")
            elif item.type == "pane_render_label_stmt":
                label = _decode_string_field(item, "value")
            elif item.type == "pane_render_placeholder_stmt":
                placeholder = _decode_string_field(item, "value")
            elif item.type == "pane_render_component_stmt":
                component_ref = _required_field_text(item, "component_ref")
            elif item.type == "pane_render_fallback_stmt":
                fallback_node_kind = _optional_field_text(item, "fallback_node_kind") or fallback_node_kind
                fallback_text = _optional_decoded_string_field(item, "fallback_text") or fallback_text
            elif item.type == "pane_render_state_binding_stmt":
                state_bindings.append(_parse_state_binding(item))
            elif item.type == "pane_render_action_binding_def":
                action_bindings.append(_parse_action_binding(item))
            elif item.type == "pane_render_style_stmt":
                style_tokens.append(
                    PaneRenderStyleToken(
                        token=_required_field_text(item, "token"),
                        value=_optional_decoded_string_field(item, "value"),
                    )
                )

    explicit_role = _optional_node_option_text(node, "semantic_role")
    implicit_role = _optional_field_text(node, "implicit_semantic_role")
    if explicit_role and implicit_role:
        raise PaneRenderParseError(
            f"pane render node {_required_field_text(node, 'node_key')!r} declares both compact role and explicit role"
        )

    return PaneRenderNode(
        key=_required_field_text(node, "node_key"),
        kind=_required_field_text(node, "node_kind"),
        parent_key=_optional_node_option_text(node, "parent_node_key"),
        order=_optional_node_option_number(node, "order"),
        semantic_role=explicit_role or implicit_role,
        slot=_optional_node_option_text(node, "slot"),
        text=text,
        label=label,
        placeholder=placeholder,
        component_ref=component_ref,
        fallback_node_kind=fallback_node_kind,
        fallback_text=fallback_text,
        state_bindings=tuple(state_bindings),
        action_bindings=tuple(action_bindings),
        style_tokens=tuple(style_tokens),
    )


def _parse_state_binding(node: Node) -> PaneRenderStateBinding:
    state_path = _required_field_text(node, "state_path")
    return PaneRenderStateBinding(
        target_property=_required_field_text(node, "target_property"),
        state_path=_normalize_state_path(state_path),
        state_attribute=_optional_field_text(node, "state_attribute"),
        transform=_optional_field_text(node, "transform"),
        component_input_port_key=_optional_field_text(node, "component_input_port_key"),
        fallback=_optional_decoded_string_field(node, "fallback"),
    )


def _parse_action_binding(node: Node) -> PaneRenderActionBinding:
    body = node.child_by_field_name("body")
    input_bindings: list[PaneRenderInputBinding] = []
    receipt_policy: str | None = None
    if body is not None:
        for child in body.named_children:
            item = _unwrap_item(child)
            if item.type == "pane_render_input_binding_stmt":
                input_bindings.append(
                    PaneRenderInputBinding(
                        payload_path=_required_field_text(item, "payload_path"),
                        source=_required_field_text(item, "source"),
                    )
                )
            elif item.type == "pane_render_receipt_stmt":
                receipt_policy = _required_field_text(item, "policy")

    action_kind = _required_field_text(node, "action_kind")
    if action_kind != "view":
        raise PaneRenderParseError(
            "Pane render actions must bind Experience view actions; " + f"unsupported action kind: {action_kind!r}"
        )
    return PaneRenderActionBinding(
        event=_required_field_text(node, "event"),
        action_kind=cast(PaneRenderActionKind, action_kind),
        action=_required_field_text(node, "action"),
        input_bindings=tuple(input_bindings),
        receipt_policy=receipt_policy,
    )


def _validate_render_spec(spec: PaneRenderSpecIR) -> tuple[str, ...]:
    errors: list[str] = []
    node_keys: set[str] = set()
    duplicate_node_keys: set[str] = set()
    root_key = _effective_root_key(spec)

    for node in spec.nodes:
        if node.key in node_keys:
            duplicate_node_keys.add(node.key)
        node_keys.add(node.key)

    for key in sorted(duplicate_node_keys):
        errors.append(f"pane {spec.pane_name!r} render {spec.name!r} declares duplicate node {key!r}")

    if not root_key:
        errors.append(f"pane {spec.pane_name!r} render {spec.name!r} missing root")
    elif root_key not in node_keys:
        errors.append(f"pane {spec.pane_name!r} render {spec.name!r} root {root_key!r} is not declared")

    for node in spec.nodes:
        path_parent = _path_parent_key(node.key)
        if node.parent_key and path_parent and node.parent_key != path_parent:
            errors.append(
                f"pane {spec.pane_name!r} render {spec.name!r} node {node.key!r} "
                f"declares parent {node.parent_key!r} but path implies parent {path_parent!r}"
            )
        parent_key = _effective_parent_key(node=node, root_key=root_key)
        if parent_key and parent_key not in node_keys:
            errors.append(
                f"pane {spec.pane_name!r} render {spec.name!r} node {node.key!r} "
                f"references missing parent {parent_key!r}"
            )
        for state_binding in node.state_bindings:
            if state_binding.state_attribute is None and _requires_explicit_state_attribute(state_binding.state_path):
                errors.append(
                    f"pane {spec.pane_name!r} render {spec.name!r} node {node.key!r} "
                    f"binding {state_binding.target_property!r} path {state_binding.state_path!r} "
                    "requires explicit state attribute authority"
                )
        if node.kind == "component" and not node.component_ref:
            errors.append(
                f"pane {spec.pane_name!r} render {spec.name!r} component node {node.key!r} " "requires component ref"
            )
        if node.kind != "component" and node.component_ref:
            errors.append(
                f"pane {spec.pane_name!r} render {spec.name!r} node {node.key!r} "
                "declares component ref but is not node_kind 'component'"
            )
        for action_binding in node.action_bindings:
            for input_binding in action_binding.input_bindings:
                local_ref = _local_input_source_ref(input_binding.source)
                if local_ref and local_ref not in node_keys:
                    errors.append(
                        f"pane {spec.pane_name!r} render {spec.name!r} action {action_binding.action!r} "
                        f"input {input_binding.payload_path!r} references missing local source {local_ref!r}"
                    )

    return tuple(errors)


def _effective_root_key(spec: PaneRenderSpecIR) -> str | None:
    if spec.root:
        return spec.root
    for node in spec.nodes:
        if "." not in node.key:
            return node.key
    return None


def _path_parent_key(node_key: str) -> str | None:
    raw = node_key.strip()
    if "." not in raw:
        return None
    return raw.rsplit(".", 1)[0] or None


def _effective_parent_key(*, node: PaneRenderNode, root_key: str | None) -> str | None:
    if node.parent_key:
        return node.parent_key
    path_parent = _path_parent_key(node.key)
    if path_parent:
        return path_parent
    if root_key and node.key != root_key:
        return root_key
    return None


def _normalize_state_path(path: str) -> str:
    raw = path.strip()
    if raw == "state" or raw.startswith("state."):
        return raw
    return f"state.{raw}" if raw else raw


def _requires_explicit_state_attribute(path: str) -> bool:
    root = _state_path_segments(path)[0] if _state_path_segments(path) else ""
    return root in {"item", "parent", "item_index", "parent_index"}


def _state_path_segments(path: str) -> tuple[str, ...]:
    raw = path.strip()
    if raw == "state":
        return ()
    if raw.startswith("state."):
        raw = raw.removeprefix("state.").strip(".")
    return tuple(part for part in raw.split(".") if part)


def _local_input_source_ref(source: str) -> str | None:
    raw = source.strip()
    root = raw.split(".", 1)[0]
    if not root or root in _NON_LOCAL_INPUT_SOURCE_ROOTS:
        return None
    return raw


def _unwrap_item(node: Node) -> Node:
    if node.type in {"pane_item", "pane_render_item", "pane_render_node_item", "pane_render_action_item"}:
        children = node.named_children
        if len(children) == 1:
            return children[0]
    return node


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8")


def _required_field_text(node: Node, field_name: str) -> str:
    value = _optional_field_text(node, field_name)
    if not value:
        raise PaneRenderParseError(f"{node.type} missing {field_name}")
    return value


def _optional_field_text(node: Node, field_name: str) -> str | None:
    value_node = node.child_by_field_name(field_name)
    value = _node_text(value_node).strip()
    return value or None


def _decode_string_field(node: Node, field_name: str) -> str:
    value_node = node.child_by_field_name(field_name)
    if value_node is None:
        raise PaneRenderParseError(f"{node.type} missing {field_name}")
    return _decode_string_literal(value_node)


def _optional_decoded_string_field(node: Node, field_name: str) -> str | None:
    value_node = node.child_by_field_name(field_name)
    if value_node is None:
        return None
    return _decode_string_literal(value_node)


def _decode_string_literal(node: Node) -> str:
    text = _node_text(node).strip()
    try:
        value = ast.literal_eval(text)
    except Exception as exc:
        raise PaneRenderParseError(f"Invalid string literal: {text!r}") from exc
    return value if isinstance(value, str) else str(value)


def _optional_number_field(node: Node, field_name: str) -> int | float | None:
    raw = _optional_field_text(node, field_name)
    return _parse_optional_number(raw)


def _optional_node_option_text(node: Node, field_name: str) -> str | None:
    direct = _optional_field_text(node, field_name)
    if direct is not None:
        return direct
    for child in node.named_children:
        if child.type != "pane_render_node_option":
            continue
        value = _optional_field_text(child, field_name)
        if value is not None:
            return value
    return None


def _optional_node_option_number(node: Node, field_name: str) -> int | float | None:
    raw = _optional_node_option_text(node, field_name)
    return _parse_optional_number(raw)


def _parse_optional_number(raw: str | None) -> int | float | None:
    if raw is None:
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError as exc:
        raise PaneRenderParseError(f"Invalid number literal: {raw!r}") from exc
