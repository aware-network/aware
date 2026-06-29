from __future__ import annotations

# Standard
from enum import Enum


class ContentPartLayoutUnit(Enum):
    em = "em"
    percentage = "percentage"
    pixel = "pixel"
    rem = "rem"
    vh = "vh"
    vw = "vw"


class ContentPartType(Enum):
    file = "file"
    text = "text"
