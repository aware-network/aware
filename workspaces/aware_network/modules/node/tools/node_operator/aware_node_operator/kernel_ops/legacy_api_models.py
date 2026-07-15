from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FunctionDescriptor:
    id: UUID
    name: str
    summary: str | None = None
    role_id: UUID | None = None
    is_constructor: bool = False
    inputs: list[Any] = field(default_factory=list)
    outputs: list[Any] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ObjectDescriptor:
    id: UUID
    name: str
    description: str | None = None
    functions: list[FunctionDescriptor] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FunctionCallRequest:
    call_target: str
    object_id: UUID | None
    object_projection_graph_id: UUID | None
    function_id: UUID
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    actor_id: UUID | None = None
    commit: bool = True
    publish: bool = False
