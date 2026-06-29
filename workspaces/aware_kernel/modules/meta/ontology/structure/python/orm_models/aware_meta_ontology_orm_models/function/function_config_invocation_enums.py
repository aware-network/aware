from __future__ import annotations

# Standard
from enum import Enum


class FunctionInvocationKind(Enum):
    call = "call"
    construct = "construct"


class FunctionInvocationRootKind(Enum):
    owner = "owner"
    capture = "capture"
