from __future__ import annotations

# Standard
from enum import Enum


class PaneRenderNodeKind(Enum):
    box = "box"
    column = "column"
    field = "field"
    list_item = "list_item"
    metric = "metric"
    row = "row"
    scroll = "scroll"
    section_header = "section_header"
    repeat = "repeat"
    disclosure = "disclosure"
    text = "text"
    status = "status"
    text_input = "text_input"
    button = "button"
    receipt = "receipt"
    component = "component"


class PaneRenderSemanticRole(Enum):
    pane = "pane"
    section = "section"
    heading = "heading"
    paragraph = "paragraph"
    message = "message"
    metadata = "metadata"
    metric = "metric"
    status = "status"
    input = "input"
    action = "action"
    receipt = "receipt"


class PaneStateBindingTransform(Enum):
    raw = "raw"
    text = "text"
    count = "count"
    plural_count = "plural_count"
    exists = "exists"
    equals = "equals"
    not_empty = "not_empty"
    is_empty = "is_empty"


class PaneStateBindingTargetProperty(Enum):
    text = "text"
    visible = "visible"
    enabled = "enabled"
    value_ = "value"
    tone = "tone"
    items = "items"
    identity = "identity"
    media_ref = "media_ref"


class PaneActionEvent(Enum):
    activate = "activate"
    submit = "submit"
    change = "change"


class PaneRenderCapabilityKind(Enum):
    node_kind = "node_kind"
    layout_kind = "layout_kind"
    input_kind = "input_kind"
    action_binding = "action_binding"
    receipt = "receipt"
    render_component = "render_component"
