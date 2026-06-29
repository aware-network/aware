from __future__ import annotations

# Standard
from enum import Enum


class FunctionImplKind(Enum):
    """Canonical implementation mode for a FunctionImpl."""

    # FunctionImpl owns executable instruction payloads.
    instruction_body = "instruction_body"
    # Bodyless construct declaration materialized through constructor identity rails.
    auto_constructor = "auto_constructor"
