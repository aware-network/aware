from __future__ import annotations

# Standard
from enum import Enum


class ClassIdentityMode(Enum):
    contained = "contained"
    standalone = "standalone"


class ClassValueMode(Enum):
    graph_ref = "graph_ref"
    inline_value = "inline_value"
