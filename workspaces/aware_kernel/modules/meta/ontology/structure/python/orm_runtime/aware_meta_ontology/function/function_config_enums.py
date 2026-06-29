from __future__ import annotations

# Standard
from enum import Enum


class FunctionAttributeType(Enum):
    input = "input"
    output = "output"


class FunctionIdentityKeyOrigin(Enum):
    standalone = "standalone"
    propagated_parent = "propagated_parent"


class FunctionKind(Enum):
    class_ = "class"
    instance = "instance"
    static = "static"
