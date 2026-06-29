"""Generated ObjectConfigGraphNode manifest for runtime->language materializations.

This artifact provides an explicit contract between:
- Runtime->Language transformers (which decide what entities exist after lowering),
- Render/layout strategies (which decide where to write those entities).

Design goals:
- OCG-node keyed (provenance is explicit: node id + node type)
- Minimal, deterministic, and explicit (no inference in the layout layer)
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


class GeneratedObjectConfigGraphNodeFilePolicy(str, Enum):
    # Write into the same canonical file container as `anchor_entity_id`.
    SAME_CONTAINER_AS_ANCHOR = "same_container_as_anchor"
    # Write into its own file (layout strategy decides exact path using canonical anchor dir).
    OWN_FILE = "own_file"


class GeneratedObjectConfigGraphNodeIntent(BaseModel):
    """
    Placement intent for a generated OCG node.

    Provenance contract:
    - `node_id` MUST exist on the derived graph.
    - `node_type` MUST match the derived node.type.
    """

    node_id: UUID
    node_type: ObjectConfigGraphNodeType
    # Placement anchor in the derived graph (typically the canonical source class node).
    anchor_node_id: UUID | None = None
    file_policy: GeneratedObjectConfigGraphNodeFilePolicy = GeneratedObjectConfigGraphNodeFilePolicy.OWN_FILE


class GeneratedObjectConfigGraphNodeManifest(BaseModel):
    intents_by_node_id: dict[UUID, GeneratedObjectConfigGraphNodeIntent] = Field(default_factory=dict)
