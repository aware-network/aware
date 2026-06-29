from __future__ import annotations

# Standard
from enum import Enum


class ObjectProjectionGraphAttributeRole(Enum):
    foreign_key = "foreign_key"
    reference = "reference"


class ObjectProjectionGraphEdgeInclude(Enum):
    optional = "optional"
    required = "required"


class ObjectProjectionGraphEdgeMultiplicity(Enum):
    at_least_1 = "at_least_1"
    many = "many"
    one = "one"


class ObjectProjectionGraphNodeSelection(Enum):
    all = "all"
    one = "one"
    top_n = "top_n"
