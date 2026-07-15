from __future__ import annotations

# Third-party
from pydantic import BaseModel

# Types
from aware_types import JsonObject


class ProgramImplInstructionLet(BaseModel):
    """
    Program local binding step.
    Contract:
    - Deterministic/pure computation only.
    - No runtime effects.
    """

    # Attributes
    name: str
    value_expr: JsonObject
