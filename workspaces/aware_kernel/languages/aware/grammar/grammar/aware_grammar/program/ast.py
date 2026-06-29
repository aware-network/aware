from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True, slots=True)
class ProgramRef:
    """A symbolic reference (qualified name) inside a program."""

    value: str


@dataclass(frozen=True, slots=True)
class ProgramCallArg:
    name: str | None
    value: "ProgramExpr"


@dataclass(frozen=True, slots=True)
class ProgramCall:
    target: str
    args: tuple[ProgramCallArg, ...] = ()
    object_expr: ProgramExpr | None = None
    actor: str | None = None


ProgramValue: TypeAlias = str | int | float | bool | None | dict[str, object] | list[object]
ProgramExpr: TypeAlias = ProgramRef | ProgramCall | ProgramValue


@dataclass(frozen=True, slots=True)
class ProgramParameter:
    name: str
    type_ref: str
    default: ProgramExpr | None = None


@dataclass(frozen=True, slots=True)
class ProgramInput:
    name: str
    source: ProgramExpr
    default: ProgramExpr | None = None


@dataclass(frozen=True, slots=True)
class ProgramActor:
    name: str
    actor: str


@dataclass(frozen=True, slots=True)
class ProgramExpectEventConfig:
    ref: ProgramExpr
    required: bool = True


@dataclass(frozen=True, slots=True)
class ProgramIntentActionConfig:
    action_ref: ProgramExpr
    event_ref: ProgramExpr


@dataclass(frozen=True, slots=True)
class ProgramLet:
    name: str
    value: ProgramExpr


ProgramStmt: TypeAlias = (
    ProgramActor | ProgramInput | ProgramExpectEventConfig | ProgramIntentActionConfig | ProgramLet | ProgramCall
)

ProgramDeclarationKind = Literal["config", "impl"]


@dataclass(frozen=True, slots=True)
class ProgramDeclaration:
    name: str
    statements: tuple[ProgramStmt, ...]
    parameters: tuple[ProgramParameter, ...] = ()
    impl_of: str | None = None

    @property
    def kind(self) -> ProgramDeclarationKind:
        return "impl" if self.impl_of else "config"
