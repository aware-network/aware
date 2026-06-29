from __future__ import annotations

# Standard
from enum import Enum


class ClassValueMode(Enum):
    graph_ref = "graph_ref"
    inline_value = "inline_value"


class ClassIdentityMode(Enum):
    contained = "contained"
    standalone = "standalone"
