from __future__ import annotations

# Standard
from enum import Enum


class ObjectConfigGraphNodeType(Enum):
    """
    Graph-level enums for ObjectConfigGraph.
    This must live in the ontology (SSOT) because it is referenced by core meta
    structures (e.g. ObjectConfigGraphNode.type) and must be available when the
    runtime OCG is composed without any DTO/API packages.
    """

    enum = "enum"
    function = "function"
    class_ = "class"
    relationship = "relationship"
