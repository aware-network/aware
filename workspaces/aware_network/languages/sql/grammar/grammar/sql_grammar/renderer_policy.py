from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SQLRenderPolicy:
    """SQL DDL render policy."""

    emit_lane_scoped_foreign_keys: bool = True
    emit_lane_scoped_indexes: bool = True
    emit_semantic_identity_primary_keys: bool = True
    emit_semantic_identity_unique_columns: bool = True
    emit_semantic_identity_unique_constraints: bool = False

    @classmethod
    def projection_default(cls) -> "SQLRenderPolicy":
        return cls(
            emit_lane_scoped_foreign_keys=True,
            emit_lane_scoped_indexes=True,
            emit_semantic_identity_primary_keys=False,
            emit_semantic_identity_unique_columns=False,
            emit_semantic_identity_unique_constraints=True,
        )

    @classmethod
    def orm_models_default(cls) -> "SQLRenderPolicy":
        return cls(
            emit_lane_scoped_foreign_keys=False,
            emit_lane_scoped_indexes=False,
            emit_semantic_identity_primary_keys=False,
            emit_semantic_identity_unique_columns=False,
        )


__all__ = ["SQLRenderPolicy"]
