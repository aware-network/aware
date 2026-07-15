from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwareProgramsTomlProgramSpec:
    ref: str
    path: str
    name: str
    dependencies: tuple[str, ...] = ()
    required_symbols: tuple[str, ...] = ()
    optional_symbols: tuple[str, ...] = ()

    @property
    def module_id(self) -> str:
        module_id, _ = self.ref.split(":", 1)
        return module_id

    @property
    def program_name(self) -> str:
        _, program_name = self.ref.split(":", 1)
        return program_name


@dataclass(frozen=True, slots=True)
class AwareProgramsTomlSpec:
    aware: int
    programs: tuple[AwareProgramsTomlProgramSpec, ...]


__all__ = [
    "AwareProgramsTomlProgramSpec",
    "AwareProgramsTomlSpec",
]
