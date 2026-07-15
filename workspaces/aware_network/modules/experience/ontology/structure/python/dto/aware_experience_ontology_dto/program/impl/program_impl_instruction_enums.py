from __future__ import annotations

# Standard
from enum import Enum


class ProgramImplInstructionType(Enum):
    """Polymorphic instruction for program impl construction."""

    input = "input"
    let = "let"
    bind = "bind"
    invoke = "invoke"
    expect = "expect"
    intent = "intent"


class ProgramImplInvokeTargetKind(Enum):
    """Canonical runtime target selection for invoke instructions."""

    instance = "instance"
    construct = "construct"
