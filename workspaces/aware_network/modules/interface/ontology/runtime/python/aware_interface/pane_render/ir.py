from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PaneRenderActionKind = Literal["view"]


@dataclass(frozen=True, slots=True)
class PaneRenderRequirement:
    capability_kind: str
    capability_key: str


@dataclass(frozen=True, slots=True)
class PaneRenderStyleToken:
    token: str
    value: str | None = None


@dataclass(frozen=True, slots=True)
class PaneRenderStateBinding:
    target_property: str
    state_path: str
    state_attribute: str | None = None
    transform: str | None = None
    component_input_port_key: str | None = None
    fallback: str | None = None


@dataclass(frozen=True, slots=True)
class PaneRenderInputBinding:
    payload_path: str
    source: str


@dataclass(frozen=True, slots=True)
class PaneRenderActionBinding:
    event: str
    action_kind: PaneRenderActionKind
    action: str
    input_bindings: tuple[PaneRenderInputBinding, ...] = ()
    receipt_policy: str | None = None


@dataclass(frozen=True, slots=True)
class PaneRenderNode:
    key: str
    kind: str
    parent_key: str | None = None
    order: int | float | None = None
    semantic_role: str | None = None
    slot: str | None = None
    text: str | None = None
    label: str | None = None
    placeholder: str | None = None
    component_ref: str | None = None
    fallback_node_kind: str | None = None
    fallback_text: str | None = None
    state_bindings: tuple[PaneRenderStateBinding, ...] = ()
    action_bindings: tuple[PaneRenderActionBinding, ...] = ()
    style_tokens: tuple[PaneRenderStyleToken, ...] = ()


@dataclass(frozen=True, slots=True)
class PaneRenderSpecIR:
    pane_name: str
    name: str
    view: str | None = None
    version: str | None = None
    root: str | None = None
    requirements: tuple[PaneRenderRequirement, ...] = ()
    nodes: tuple[PaneRenderNode, ...] = ()
