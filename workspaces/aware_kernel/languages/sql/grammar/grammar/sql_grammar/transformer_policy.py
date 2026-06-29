from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SQLTransformPolicy:
    """SQL runtime-to-language lowering policy."""

    emit_lane_scope_columns: bool = True

    @classmethod
    def projection_default(cls) -> "SQLTransformPolicy":
        return cls(emit_lane_scope_columns=True)

    @classmethod
    def orm_models_default(cls) -> "SQLTransformPolicy":
        return cls(emit_lane_scope_columns=False)


__all__ = ["SQLTransformPolicy"]
