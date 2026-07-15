#!/usr/bin/env python3
# flake8: noqa: E501
"""See an Aware pane from raw .aware source - no control machinery.

Parses authored `render default { node ... }` pane source with the canonical
`aware_interface.pane_render` parser and renders the PaneRenderSpec to a
self-contained HTML preview in the aware.run visual system (deep navy + cyan).

This is a RENDERER, not control machinery: no Flutter, no Node, no Interface
Host, no SDK. State bindings resolve to their declared `fallback` for a static
preview, or to values from an optional `--state <json>` sample so collection
panes (Goal -> GoalLane -> GoalLaneIssue) show real rows.

Usage:
    python tools/pane_preview/pane_preview.py <pane.aware> [--state state.json] [--out out.html] [--render <name>]

Honors the pane-render-spec authored grammar:
    workspaces/aware_network/modules/interface/docs/specs/pane-render-spec-authored-grammar/SPEC.md
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

from aware_interface.pane_render import (
    PaneRenderNode,
    PaneRenderSpecIR,
    parse_pane_render_specs,
)

# aware.run visual system tokens (see docs/conversations/2026-06-02-PUBLIC-SYSTEM-SPEC.md)
_CSS = """
:root {
  --bg: #0b0e14; --card: #11161f; --card-soft: #151b26;
  --accent: #4cc9f0; --text: #f0f4fc; --muted: #98a3b3;
  --line: rgba(152,163,179,0.16);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font-family: "Inter", system-ui, sans-serif; padding: 40px;
  background-image: radial-gradient(520px 360px at 30% 12%, rgba(76,201,240,0.10), transparent 70%); }
.preview-shell { max-width: 1080px; margin: 0 auto; }
.preview-meta { color: var(--muted); font: 500 13px ui-monospace, monospace;
  letter-spacing: .04em; margin-bottom: 18px; }
.preview-meta b { color: var(--accent); }
.pane { background: var(--card); border: 1px solid var(--line); border-radius: 18px;
  padding: 28px; box-shadow: 0 18px 48px rgba(0,0,0,0.42); }
.column, .col { display: flex; flex-direction: column; gap: 12px; }
.column.column-layout-pane-header { align-items: center; text-align: center; gap: 10px; margin-bottom: 6px; }
.column.column-align-center { align-items: center; text-align: center; }
.row { display: flex; flex-direction: row; gap: 12px 16px; align-items: center; flex-wrap: wrap; }
.row.row-align-center { justify-content: center; }
.row.row-layout-pane-header { justify-content: center; align-items: center; gap: 10px 12px; margin-bottom: 6px; }
.row.row-layout-pane-header .row-layout-metadata-bar { width: auto; }
.row.row-layout-summary-bar { display: grid; grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center; gap: 10px 14px; width: 100%; }
.row.row-layout-summary-bar h2.node,
.row.row-layout-summary-bar h3.node { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row.row-layout-summary-bar p.node { white-space: nowrap; color: var(--muted); }
.row.row-layout-metadata-bar { gap: 8px 10px; align-items: center; width: 100%; }
.row.row-layout-metadata-bar .status { align-self: center; }
.row.row-layout-metadata-bar .metric { display: inline-flex; flex-direction: row;
  align-items: baseline; gap: 6px; padding: 4px 10px; border: 1px solid var(--line);
  border-radius: 8px; background: rgba(152,163,179,0.08); }
.row.row-layout-metadata-bar .metric .value { font: 700 14px Inter; color: var(--text); }
.row.row-layout-metadata-bar .metric .label { font: 600 11px Inter; color: var(--muted);
  text-transform: none; letter-spacing: 0; }
.row.row-layout-composer { display: grid; grid-template-columns: minmax(0, 1fr) auto;
  align-items: stretch; gap: 10px; width: 100%; }
.row.row-layout-composer .btn { align-self: stretch; }
.box { padding: 12px; }
.scroll { max-height: 520px; overflow: auto; }
.repeat { display: flex; flex-direction: column; gap: 10px; }
.repeat.repeat-layout-message-thread { gap: 12px; padding: 6px 0; }
h2.node { font: 700 28px Inter, sans-serif; margin: 0; }
h3.node { font: 700 19px Inter, sans-serif; margin: 0; }
p.node { color: var(--muted); margin: 0; line-height: 1.5; }
.node.node-typography-pane-title { font-size: clamp(30px, 3.2vw, 44px); line-height: 1.04; letter-spacing: 0; }
.node.node-align-center { text-align: center; align-self: center; }
.node.node-overflow-truncate { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.status { --status-fg: var(--accent); --status-bg: rgba(76,201,240,0.10);
  --status-border: rgba(76,201,240,0.4);
  display: inline-flex; align-items: center; gap: 8px; align-self: flex-start;
  background: var(--status-bg); color: var(--status-fg); border: 1px solid var(--status-border);
  border-radius: 999px; padding: 4px 12px; font: 600 13px Inter; }
.tone-pending {
  --status-fg: #61d8ff; --status-bg: rgba(76,201,240,0.12); --status-border: rgba(76,201,240,0.48); }
.tone-success {
  --status-fg: #60d394; --status-bg: rgba(96,211,148,0.12); --status-border: rgba(96,211,148,0.46); }
.tone-neutral {
  --status-fg: #aeb8c7; --status-bg: rgba(152,163,179,0.10); --status-border: rgba(152,163,179,0.32); }
.tone-warning {
  --status-fg: #f4b860; --status-bg: rgba(244,184,96,0.12); --status-border: rgba(244,184,96,0.45); }
.tone-danger {
  --status-fg: #ff7f7f; --status-bg: rgba(255,127,127,0.12); --status-border: rgba(255,127,127,0.45); }
.tone-receipt, .tone-provenance {
  --status-fg: #f7c86f; --status-bg: rgba(247,200,111,0.12); --status-border: rgba(247,200,111,0.44); }
.chip { display: inline-flex; align-items: center; max-width: 220px; min-width: 0;
  border: 1px solid rgba(152,163,179,0.20); border-radius: 999px;
  padding: 4px 10px; color: var(--text); background: rgba(152,163,179,0.08);
  font: 650 12px Inter, sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.btn { align-self: flex-start; background: var(--accent); color: #06121a; border: none;
  border-radius: 12px; padding: 10px 18px; font: 600 15px Inter; cursor: default; }
input.node, textarea.node { background: var(--card-soft); border: 1px solid var(--line);
  color: var(--text); border-radius: 10px; padding: 10px 12px; font: 400 15px Inter; width: 100%; }
.field { display: grid; grid-template-columns: minmax(96px, auto) minmax(0, 1fr); gap: 10px;
  align-items: start; padding: 7px 0; border-bottom: 1px solid var(--line); min-width: 0; }
.field .label { color: var(--muted); font: 500 14px Inter; }
.field .value { color: var(--text); font: 600 14px Inter; text-align: right; overflow-wrap: anywhere; min-width: 0; }
.field.field-display-prose { grid-template-columns: minmax(0, 1fr); gap: 4px; }
.field.field-display-prose .value { text-align: left; line-height: 1.38; }
.field.field-display-identifier .value { text-align: left; font: 650 13px Inter, sans-serif; }
.field.field-display-scalar .value { text-align: right; white-space: nowrap; }
.field.field-display-chip { display: inline-flex; border-bottom: 0; padding: 0; grid-template-columns: none; }
.field.field-overflow-truncate .value { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; overflow-wrap: normal; }
.row > .field { border-bottom: 0; padding: 0; }
.row > .field.field-display-prose { flex: 1 1 320px; }
.row > .field.field-display-identifier { flex: 0 1 210px; }
.row > .field.field-display-scalar { flex: 0 0 auto; }
.metric { display: flex; flex-direction: column; }
.metric .value { font: 700 26px Inter; color: var(--accent); }
.metric .label { color: var(--muted); font: 500 12px Inter; text-transform: uppercase; letter-spacing: .06em; }
.section-header { color: var(--muted); font: 600 12px Inter; text-transform: uppercase;
  letter-spacing: .08em; margin-top: 8px; }
.list-item { background: var(--card-soft); border: 1px solid var(--line); border-radius: 12px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; }
.list-item.list-item-layout-compact-row { background: transparent; border: 0; border-radius: 0;
  padding: 0; flex-direction: row; flex-wrap: wrap; align-items: center; gap: 12px 16px; }
.list-item.list-item-layout-compact-row .field { border-bottom: 0; padding: 0; }
.list-item.list-item-layout-compact-row .field-display-prose { flex: 1 1 340px; }
.list-item.list-item-layout-compact-row h3.node { flex: 1 1 380px; font-size: 15px;
  line-height: 1.35; }
.list-item.list-item-layout-message-bubble { width: min(760px, 100%); padding: 14px 16px;
  gap: 8px; background: rgba(76,201,240,0.08); border-color: rgba(76,201,240,0.22);
  border-left: 3px solid var(--accent); box-shadow: 0 10px 24px rgba(0,0,0,0.14); }
.list-item.list-item-layout-message-bubble p.node { color: var(--text); font-size: 16px; }
.list-item.list-item-layout-message-bubble .field { border-bottom: 0; padding: 0; }
.list-item.list-item-layout-message-bubble .field .label { display: none; }
.list-item.list-item-layout-message-bubble .field-display-scalar .value { color: var(--muted);
  font: 500 12px Inter, sans-serif; text-align: left; }
.disclosure { background: var(--card-soft); border: 1px solid var(--line); border-radius: 14px;
  padding: 0; overflow: hidden; }
.disclosure + .disclosure { margin-top: 10px; }
.disclosure > summary { cursor: pointer; list-style: none; padding: 14px 16px; }
.disclosure > summary::-webkit-details-marker { display: none; }
.disclosure > summary::before { content: "+"; display: inline-flex; width: 20px; color: var(--accent);
  font: 700 15px ui-monospace, monospace; }
.disclosure[open] > summary::before { content: "-"; }
.disclosure-static { padding: 14px 16px; }
.disclosure > summary h2.node { font-size: 24px; }
.disclosure > summary h3.node { font-size: 17px; }
.disclosure-detail { border-top: 1px solid var(--line); padding: 14px 16px;
  background: rgba(5,9,15,0.22); }
.receipt { background: var(--card-soft); border: 1px dashed rgba(76,201,240,0.4);
  border-radius: 12px; padding: 12px 14px; color: var(--muted); font: 500 13px ui-monospace, monospace; }
.component { background: var(--card-soft); border: 1px solid var(--line); border-radius: 12px;
  padding: 14px; color: var(--muted); font: 500 14px Inter; }
.unknown { color: #e0746a; font: 500 13px ui-monospace, monospace; }
"""

_HEADINGS = {"heading", "title"}


def _resolve_path(state: Any, path: str, item: Any, parent: Any) -> Any:
    """Resolve a view-state path against sample state with repeat scope."""
    if not path:
        return None
    parts = path.split(".")
    head = parts[0]
    if head == "state":
        parts = parts[1:]
        head = parts[0] if parts else ""
    if head == "item":
        cur: Any = item
        parts = parts[1:]
    elif head == "parent":
        cur = parent
        parts = parts[1:]
    elif head in {"item_index", "parent_index"}:
        return None
    else:
        cur = state
    for key in parts:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def _binding(node: PaneRenderNode, target: str):
    for b in node.state_bindings:
        if b.target_property == target:
            return b
    return None


def _text_value(node: PaneRenderNode, target: str, state, item, parent) -> str | None:
    b = _binding(node, target)
    if b is None:
        return None
    val = _resolve_path(state, b.state_path, item, parent)
    if b.transform == "count":
        try:
            return str(len(val)) if val is not None else (b.fallback or "0")
        except TypeError:
            return b.fallback or "0"
    if b.transform == "plural_count":
        try:
            count = len(val) if val is not None else 0
        except TypeError:
            return b.fallback or "0"
        unit = (node.label or "item").strip() or "item"
        suffix = "" if count == 1 else "s"
        return f"{count} {unit}{suffix}"
    if val is None or val == "":
        return b.fallback
    return str(val)


def _items_value(node: PaneRenderNode, state, item, parent) -> list[Any]:
    b = _binding(node, "items")
    if b is None:
        return []
    val = _resolve_path(state, b.state_path, item, parent)
    return list(val) if isinstance(val, (list, tuple)) else []


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, list, tuple, dict, set)):
        return len(value) == 0
    return False


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)


def _visible_value(node: PaneRenderNode, state, item, parent) -> bool:
    b = _binding(node, "visible")
    if b is None:
        return True
    val = _resolve_path(state, b.state_path, item, parent)
    if b.transform == "is_empty":
        return _is_empty_value(val)
    if b.transform == "not_empty":
        return not _is_empty_value(val)
    if b.transform == "exists":
        return val is not None
    if val is None and b.fallback is not None:
        return _boolish(b.fallback)
    return _boolish(val)


def _path_parent_key(node_key: str) -> str | None:
    raw = node_key.strip()
    if "." not in raw:
        return None
    return raw.rsplit(".", 1)[0]


def _effective_parent_key(node: PaneRenderNode, root_key: str | None) -> str | None:
    if node.parent_key:
        return node.parent_key
    path_parent = _path_parent_key(node.key)
    if path_parent:
        return path_parent
    if root_key and node.key != root_key:
        return root_key
    return None


def _children(
    spec: PaneRenderSpecIR,
    parent_key: str | None,
    *,
    slot: str | None = None,
) -> list[PaneRenderNode]:
    root_key = _root_key(spec)
    kids = [
        n for n in spec.nodes if _effective_parent_key(n, root_key) == parent_key and (slot is None or n.slot == slot)
    ]
    return sorted(kids, key=lambda n: (n.order if n.order is not None else 1e9))


def _root_key(spec: PaneRenderSpecIR) -> str | None:
    if spec.root:
        return spec.root
    for node in spec.nodes:
        if node.parent_key is None and _path_parent_key(node.key) is None:
            return node.key
    return spec.nodes[0].key if spec.nodes else None


def _esc(s: Any) -> str:
    return html.escape(str(s)) if s is not None else ""


def _style_value(node: PaneRenderNode, token: str) -> str | None:
    for style_token in node.style_tokens:
        if style_token.token == token:
            return style_token.value or ""
    return None


def _style_values(node: PaneRenderNode, token: str) -> tuple[str, ...]:
    return tuple(style_token.value or "" for style_token in node.style_tokens if style_token.token == token)


def _css_token(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.strip().lower()).strip("-")


def _is_declared_empty(node: PaneRenderNode, value: str) -> bool:
    if value == "":
        return True
    declared_empty_values = set(_style_values(node, "empty_value"))
    return value in declared_empty_values


def _short_identifier(value: str) -> str:
    if len(value) <= 28:
        return value
    parts = value.split("-")
    if len(parts) >= 3 and len(parts[0]) <= 12:
        return f"{parts[0]}-{parts[1]}...{value[-8:]}"
    return f"{value[:18]}...{value[-8:]}"


def _field_value_html(node: PaneRenderNode, value: str) -> str:
    display = _style_value(node, "display") or "auto"
    rendered = value
    title = ""
    if display == "identifier":
        rendered = _short_identifier(value)
        if rendered != value:
            title = f' title="{_esc(value)}"'
    return f'<span class="value"{title}>{_esc(rendered)}</span>'


def _chip_html(node: PaneRenderNode, value: str) -> str:
    rendered = _short_identifier(value)
    title_value = f"{node.label}: {value}" if node.label else value
    return (
        f'<span class="chip" title="{_esc(title_value)}" ' f'aria-label="{_esc(title_value)}">{_esc(rendered)}</span>'
    )


def _field_classes(node: PaneRenderNode) -> str:
    classes = ["field"]
    for token in ("display", "overflow", "align"):
        value = _style_value(node, token)
        if value:
            classes.append(f"field-{_css_token(token)}-{_css_token(value)}")
    return " ".join(classes)


def _node_classes(node: PaneRenderNode) -> str:
    classes = ["node"]
    for token in ("display", "typography", "overflow", "align"):
        value = _style_value(node, token)
        if value:
            classes.append(f"node-{_css_token(token)}-{_css_token(value)}")
    return " ".join(classes)


def _container_classes(kind: str, node: PaneRenderNode) -> str:
    classes = [kind]
    for token in ("layout", "density", "align"):
        value = _style_value(node, token)
        if value:
            classes.append(f"{kind}-{_css_token(token)}-{_css_token(value)}")
    return " ".join(classes)


def _tone_value(node: PaneRenderNode, state, item, parent) -> str | None:
    bound = _text_value(node, "tone", state, item, parent)
    if bound:
        return bound
    return _style_value(node, "tone")


def _status_classes(tone: str | None) -> str:
    classes = ["status"]
    token = _css_token(tone or "")
    if token:
        classes.append(f"tone-{token}")
    return " ".join(classes)


def _node_attrs(node: PaneRenderNode, text: str) -> str:
    if _style_value(node, "overflow") == "truncate":
        return f' title="{_esc(text)}"'
    return ""


def _list_item_classes(node: PaneRenderNode) -> str:
    classes = ["list-item"]
    layout = _style_value(node, "layout")
    if layout:
        classes.append(f"list-item-layout-{_css_token(layout)}")
    return " ".join(classes)


def _render_node(spec, node: PaneRenderNode, state, item, parent) -> str:
    if not _visible_value(node, state, item, parent):
        return ""

    kind = node.kind
    role = node.semantic_role or ""

    def kids_html(scope_item=item) -> str:
        return "".join(_render_node(spec, c, state, scope_item, parent) for c in _children(spec, node.key))

    if kind in {"column", "row", "box", "scroll"}:
        inner = kids_html()
        if not inner.strip():
            return ""
        return f'<div class="{_container_classes(kind, node)}">{inner}</div>'

    if kind == "repeat":
        items = _items_value(node, state, item, parent)
        if not items:
            return ""
        rows = "".join(
            "".join(_render_node(spec, c, state, it, item) for c in _children(spec, node.key)) for it in items
        )
        return f'<div class="{_container_classes(kind, node)}">{rows}</div>'

    if kind == "text":
        txt = _text_value(node, "text", state, item, parent) or node.text or ""
        tag = "h2" if role in _HEADINGS else ("h3" if role == "subheading" else "p")
        return f'<{tag} class="{_node_classes(node)}"{_node_attrs(node, txt)}>{_esc(txt)}</{tag}>'

    if kind == "status":
        txt = _text_value(node, "text", state, item, parent) or node.text or ""
        tone = _tone_value(node, state, item, parent)
        return f'<span class="{_status_classes(tone)}">{_esc(txt)}</span>'

    if kind == "button":
        txt = node.label or _text_value(node, "text", state, item, parent) or "Action"
        return f'<button class="btn">{_esc(txt)}</button>'

    if kind == "text_input":
        val = _text_value(node, "value", state, item, parent) or ""
        ph = _esc(node.placeholder or node.label or "")
        multiline = any(t.token == "input" and t.value == "multiline" for t in node.style_tokens)
        lbl = f'<div class="field"><span class="label">{_esc(node.label)}</span></div>' if node.label else ""
        if multiline:
            return f'{lbl}<textarea class="node" rows="3" placeholder="{ph}">{_esc(val)}</textarea>'
        return f'{lbl}<input class="node" placeholder="{ph}" value="{_esc(val)}"/>'

    if kind == "field":
        val = _text_value(node, "text", state, item, parent) or ""
        if _style_value(node, "empty_policy") == "hide" and _is_declared_empty(node, val):
            return ""
        if _style_value(node, "display") == "chip":
            return f'<span class="{_field_classes(node)}">{_chip_html(node, val)}</span>'
        return (
            f'<div class="{_field_classes(node)}">'
            f'<span class="label">{_esc(node.label)}</span>'
            f"{_field_value_html(node, val)}</div>"
        )

    if kind == "metric":
        val = _text_value(node, "text", state, item, parent) or "0"
        return f'<div class="metric"><span class="value">{_esc(val)}</span><span class="label">{_esc(node.label)}</span></div>'

    if kind == "section_header":
        txt = _text_value(node, "text", state, item, parent) or node.text or ""
        return f'<div class="section-header">{_esc(txt)}</div>'

    if kind == "list_item":
        inner = kids_html()
        if not inner.strip():
            return ""
        return f'<div class="{_list_item_classes(node)}">{inner}</div>'

    if kind == "disclosure":
        identity = _text_value(node, "identity", state, item, parent) or node.key
        summary_nodes = _children(spec, node.key, slot="summary")
        detail_nodes = _children(spec, node.key, slot="detail")
        if not summary_nodes:
            summary_nodes = _children(spec, node.key)[:1]
        summary = "".join(_render_node(spec, c, state, item, parent) for c in summary_nodes)
        detail = "".join(_render_node(spec, c, state, item, parent) for c in detail_nodes)
        if not detail.strip():
            return (
                f'<div class="disclosure disclosure-static" data-disclosure-key="{_esc(identity)}">' f"{summary}</div>"
            )
        return (
            f'<details class="disclosure" data-disclosure-key="{_esc(identity)}">'
            f"<summary>{summary}</summary>"
            f'<div class="disclosure-detail">{detail}</div>'
            "</details>"
        )

    if kind == "receipt":
        txt = _text_value(node, "text", state, item, parent) or node.text or "(receipt)"
        return f'<div class="receipt">{_esc(txt)}</div>'

    if kind == "component":
        fb = node.fallback_text or node.component_ref or "(component)"
        return f'<div class="component">{_esc(fb)}{kids_html()}</div>'

    return f'<div class="unknown">[unknown node kind: {_esc(kind)}]{kids_html()}</div>'


def render_spec_html(spec: PaneRenderSpecIR, state: dict[str, Any]) -> str:
    root = _root_key(spec)
    root_node = next((n for n in spec.nodes if n.key == root), None)
    body = _render_node(spec, root_node, state, None, None) if root_node else "<p>(empty pane)</p>"
    meta = (
        f'<div class="preview-meta">pane <b>{_esc(spec.pane_name)}</b> - render '
        f"<b>{_esc(spec.name)}</b> - view <b>{_esc(spec.view)}</b> - "
        f"{len(spec.nodes)} nodes - from raw .aware</div>"
    )
    return f'<div class="preview-shell">{meta}<div class="pane">{body}</div></div>'


def render_pane_source_html(
    source: str,
    *,
    state: dict[str, Any] | None = None,
    render_name: str | None = None,
) -> str:
    specs = parse_pane_render_specs(source)
    if render_name:
        specs = tuple(s for s in specs if s.name == render_name)
    if not specs:
        raise ValueError("No matching pane render specs found in source.")

    resolved_state = state or {}
    sections = "".join(render_spec_html(s, resolved_state) for s in specs)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{sections}</body></html>"
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="See an Aware pane from raw .aware source.")
    ap.add_argument("source", help="path to a .aware pane file")
    ap.add_argument("--state", help="optional JSON sample view-state file")
    ap.add_argument("--render", help="render name to preview (default: all)")
    ap.add_argument("--out", help="output HTML path (default: <source>.preview.html)")
    args = ap.parse_args(argv)

    src_path = Path(args.source)
    source = src_path.read_text()
    state = json.loads(Path(args.state).read_text()) if args.state else {}

    try:
        doc = render_pane_source_html(
            source,
            state=state,
            render_name=args.render,
        )
    except Exception as exc:  # PaneRenderParse/Validation/Lowering errors
        print(f"parse failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else src_path.with_suffix(".preview.html")
    out.write_text(doc)
    print(f"rendered PaneRender HTML from {src_path} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
