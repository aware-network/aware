from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True, slots=True)
class PlanLocalRef:
    """A reference to a `let`-bound local name."""

    name: str


@dataclass(frozen=True, slots=True)
class PlanSymbolRef:
    """A symbolic reference (qualified name) to be resolved by the executor."""

    name: str


@dataclass(frozen=True, slots=True)
class PlanCallArg:
    name: str | None
    value: "PlanExpr"


@dataclass(frozen=True, slots=True)
class PlanCall:
    target: str
    args: tuple[PlanCallArg, ...] = ()
    object_expr: PlanExpr | None = None


PlanValue: TypeAlias = str | int | float | bool | None | dict[str, object] | list[object]
PlanExpr: TypeAlias = PlanLocalRef | PlanSymbolRef | PlanCall | PlanValue


@dataclass(frozen=True, slots=True)
class PlanInput:
    name: str
    source: PlanExpr
    default: PlanExpr | None = None
    required: bool = True
    type_ref: str | None = None


@dataclass(frozen=True, slots=True)
class PlanExpectEventConfig:
    ref: PlanExpr
    required: bool = True


@dataclass(frozen=True, slots=True)
class PlanIntentActionConfig:
    action_ref: PlanExpr
    event_ref: PlanExpr


@dataclass(frozen=True, slots=True)
class PlanLet:
    name: str
    value: PlanExpr


@dataclass(frozen=True, slots=True)
class PlanInvoke:
    call: PlanCall
    kind: Literal["effect"] = "effect"
    actor: str | None = None


@dataclass(frozen=True, slots=True)
class PlanPortProjectionNodeKey:
    name: str
    value_expr: PlanExpr


@dataclass(frozen=True, slots=True)
class PlanPortProjectionNodeContract:
    key: str
    node: str
    keys: tuple[PlanPortProjectionNodeKey, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanActorContract:
    key: str
    actor: str


@dataclass(frozen=True, slots=True)
class PlanPortContract:
    key: str
    projection: str
    projection_nodes: tuple[PlanPortProjectionNodeContract, ...] = ()
    intent: str | None = None


PlanStep: TypeAlias = PlanInput | PlanExpectEventConfig | PlanIntentActionConfig | PlanLet | PlanInvoke


@dataclass(frozen=True, slots=True)
class InvocationPlan:
    name: str
    steps: tuple[PlanStep, ...]
    actors: tuple[PlanActorContract, ...] = ()
    ports: tuple[PlanPortContract, ...] = ()
