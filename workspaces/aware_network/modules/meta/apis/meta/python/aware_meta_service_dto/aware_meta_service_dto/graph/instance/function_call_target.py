from __future__ import annotations

# Standard
from enum import Enum


class MetaGraphFunctionCallTarget(Enum):
    """Function-call target variants supported by the Meta graph authority API."""

    instance = "instance"
    opg_constructor = "opg_constructor"
