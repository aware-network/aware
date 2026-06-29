from __future__ import annotations

# Standard
from enum import Enum


class ObjectConfigGraphPackageFunctionImplOwnership(Enum):
    """Package-level FunctionImpl execution authority for an ObjectConfigGraphPackage."""

    # Authored/generated language handlers remain execution authority.
    authored = "authored"
    # `.aware` FunctionImpl instruction bodies are execution authority.
    compiler = "compiler"


class ObjectConfigGraphPackageFunctionImplParityPolicy(Enum):
    """Package-level parity gate for FunctionImpl migration/proofs."""

    off = "off"
    warn = "warn"
    error = "error"
