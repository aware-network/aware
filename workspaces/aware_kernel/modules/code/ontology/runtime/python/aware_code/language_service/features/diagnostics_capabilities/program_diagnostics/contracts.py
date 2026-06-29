from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from tree_sitter import Node

from ..contracts import DiagnosticDataValue


class ProgramAddDiagnostic(Protocol):
    def __call__(
        self,
        *,
        start_byte: int,
        end_byte: int,
        message: str,
        code: str,
        severity: int = 1,
        data: Mapping[str, DiagnosticDataValue] | None = None,
    ) -> None: ...


class ProgramSuggestFn(Protocol):
    def __call__(self, value: str, options: list[str]) -> list[str]: ...


class ProgramNodeTextFn(Protocol):
    def __call__(self, node: Node | None) -> str: ...


@dataclass(frozen=True, slots=True)
class ProgramCompilePlanRequirements:
    required_projection_ids: tuple[str, ...]
    required_projection_node_ids: tuple[str, ...]
    required_projection_node_identity_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProgramExperienceLookup:
    experience_candidates: tuple[str, ...]
    experience_names: frozenset[str]
    projection_fallback_symbols: frozenset[str]
    compile_plan_requirements_by_program_name: Mapping[str, ProgramCompilePlanRequirements]
