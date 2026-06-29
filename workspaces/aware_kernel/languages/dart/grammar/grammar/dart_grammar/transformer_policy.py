from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DartTransformPolicy:
    """
    Transformer policy for Dart runtime->language lowering.

    Dart materializations are flat (no inheritance), so ORM semantics that rely on a Python base
    class (e.g. `id` on ORMModel/BaseORMModel) must be materialized into each derived class.

    API graphs must not receive implicit ORM fields.
    """

    emit_orm_base_fields: bool = True
    # Canonical UI/client surface: do not expose internal constructors that cannot be
    # invoked over the wire. Only constructors registered as OPG constructors (virtual builds)
    # should be emitted into Dart function wrappers.
    emit_non_opg_constructors: bool = False

    @classmethod
    def orm_default(cls) -> "DartTransformPolicy":
        return cls(emit_orm_base_fields=True, emit_non_opg_constructors=False)

    @classmethod
    def api_default(cls) -> "DartTransformPolicy":
        return cls(emit_orm_base_fields=False, emit_non_opg_constructors=False)


__all__ = ["DartTransformPolicy"]
