from __future__ import annotations

# Third-party
from pydantic import BaseModel

# Types
from aware_types import JsonObject


class FunctionImplInstructionLet(BaseModel):
    """Function-local deterministic binding instruction payload."""

    # Attributes
    name: str
    value_expr: JsonObject
