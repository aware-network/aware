from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramRunStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.impl.program_impl import ProgramImpl
    from aware_experience_ontology.program.program_actor import ProgramActor
    from aware_experience_ontology.program.program_attribute import ProgramAttribute
    from aware_experience_ontology.program.program_branch import ProgramBranch
    from aware_experience_ontology.program.program_input_attribute import ProgramInputAttribute
    from aware_experience_ontology.program.program_layout import ProgramLayout
    from aware_experience_ontology.program.program_turn import ProgramTurn


class Program(ORMModel):
    """
    Runtime program execution truth owned by Experience.
    Contract:
    - Program is the runtime instance of an Experience ProgramImpl.
    - Environment thread participation is modeled by Experience-owned
    `thread.ThreadProgram` binding objects.
    - Environment Thread does not reference Program; Experience binds to
    Environment topology explicitly.
    - Turn lifecycle remains Experience-owned by `turn.Turn`.
    """

    # Relationships
    program_impl: ProgramImpl | None = Field(default=None, exclude=True)
    program_actors: list[ProgramActor] = Field(default_factory=list, exclude=True)
    attributes: list[ProgramAttribute] = Field(default_factory=list, exclude=True)
    input_attributes: list[ProgramInputAttribute] = Field(default_factory=list, exclude=True)
    branches: list[ProgramBranch] = Field(default_factory=list, exclude=True)
    layouts: list[ProgramLayout] = Field(default_factory=list, exclude=True)
    turns: list[ProgramTurn] = Field(default_factory=list, exclude=True)
    active_turn: ProgramTurn | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: ProgramRunStatus = Field(default=ProgramRunStatus.pending)
    result_summary: str | None = Field(default=None)
    started_at_unix_ms: int | None = Field(default=None)
    terminal_at_unix_ms: int | None = Field(default=None)
    terminal_status: str | None = Field(default=None)

    # Foreign Keys
    program_impl_id: UUID = Field(description="Foreign key for Program.program_impl")
    active_turn_id: UUID | None = Field(default=None, description="Foreign key for Program.active_turn")

    @classmethod
    async def build(
        cls,
        program_impl_id: UUID,
        key: str = "default",
        title: str | None = None,
        description: str | None = None,
        resolved_branch_id: UUID | None = None,
        resolved_projection_hash: str | None = None,
    ) -> Program:
        """Create a deterministic Program runtime instance for `(program_impl_id, key)`."""

        payload = {
            "program_impl_id": program_impl_id,
            "key": key,
            "title": title,
            "description": description,
            "resolved_branch_id": resolved_branch_id,
            "resolved_projection_hash": resolved_projection_hash,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Program):
            return value
        return Program.validate_invocation_value(value)

    async def attach_turn(self, turn_id: UUID) -> ProgramTurn:
        """
        Attach a Turn receipt association to this Program.

        Contract:
        - Mutates only Program membership (`turns`).
        - Turn lifecycle semantics remain Experience-owned by `Turn`.
        """

        payload = {"turn_id": turn_id}
        result = await invoke_instance(orm_model=self, function_name="attach_turn", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn import ProgramTurn

        if isinstance(value, ProgramTurn):
            return value
        return ProgramTurn.validate_invocation_value(value)

    async def add_actor(self, program_config_actor_config_id: UUID, actor_id: UUID) -> ProgramActor:
        """
        Bind one ProgramConfig actor alias to one concrete Actor for this Program run.

        Contract:
        - Mutates only Program membership (`program_actors`).
        - Identity is deterministic under Program via ProgramActor constructor keys.
        """

        payload = {"program_config_actor_config_id": program_config_actor_config_id, "actor_id": actor_id}
        result = await invoke_instance(orm_model=self, function_name="add_actor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_actor import ProgramActor

        if isinstance(value, ProgramActor):
            return value
        return ProgramActor.validate_invocation_value(value)

    async def set_active_turn(self, active_turn_id: UUID | None = None) -> Program:
        """
        Set (or clear) the active ProgramTurn association pointer for this Program.

        Contract:
        - `active_turn_id` is optional.
        - When set, it must reference a `ProgramTurn` already attached under this Program.
        """

        payload = {"active_turn_id": active_turn_id}
        result = await invoke_instance(orm_model=self, function_name="set_active_turn", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Program):
            return value
        return Program.validate_invocation_value(value)

    async def attach_branch(
        self,
        object_instance_graph_branch_id: UUID,
        key: str | None = None,
        view_key: str | None = None,
        is_active: bool = True,
    ) -> ProgramBranch:
        """
        Attach a resolved runtime branch receipt to this Program.

        Contract:
        - Mutates only Program membership (`branches`).
        - Branch resolution remains runtime-owned by Turn/Projection authority.
        - Runtime may persist branch visibility/attention hints (`is_active`, `view_key`).
        """

        payload = {
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "key": key,
            "view_key": view_key,
            "is_active": is_active,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_branch", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_branch import ProgramBranch

        if isinstance(value, ProgramBranch):
            return value
        return ProgramBranch.validate_invocation_value(value)

    async def set_running(
        self, resolved_branch_id: UUID, resolved_projection_hash: str, started_at_unix_ms: int
    ) -> Program:
        """Mark Program as running with canonical branch resolution metadata."""

        payload = {
            "resolved_branch_id": resolved_branch_id,
            "resolved_projection_hash": resolved_projection_hash,
            "started_at_unix_ms": started_at_unix_ms,
        }
        result = await invoke_instance(orm_model=self, function_name="set_running", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Program):
            return value
        return Program.validate_invocation_value(value)

    async def finish_terminal(
        self, terminal_at_unix_ms: int, terminal_status: str, result_summary: str | None = None
    ) -> Program:
        """Mark Program terminal with canonical status summary."""

        payload = {
            "terminal_at_unix_ms": terminal_at_unix_ms,
            "terminal_status": terminal_status,
            "result_summary": result_summary,
        }
        result = await invoke_instance(orm_model=self, function_name="finish_terminal", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Program):
            return value
        return Program.validate_invocation_value(value)


class ProgramBuildInput(BaseModel):
    program_impl_id: UUID
    key: str = Field(default="default")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)


class ProgramBuildOutput(BaseModel):
    value: Program


class ProgramAttachTurnInput(BaseModel):
    turn_id: UUID


class ProgramAttachTurnOutput(BaseModel):
    value: ProgramTurn


class ProgramAddActorInput(BaseModel):
    program_config_actor_config_id: UUID
    actor_id: UUID


class ProgramAddActorOutput(BaseModel):
    value: ProgramActor


class ProgramSetActiveTurnInput(BaseModel):
    active_turn_id: UUID | None = Field(default=None)


class ProgramSetActiveTurnOutput(BaseModel):
    value: Program


class ProgramAttachBranchInput(BaseModel):
    object_instance_graph_branch_id: UUID
    key: str | None = Field(default=None)
    view_key: str | None = Field(default=None)
    is_active: bool = Field(default=True)


class ProgramAttachBranchOutput(BaseModel):
    value: ProgramBranch


class ProgramSetRunningInput(BaseModel):
    resolved_branch_id: UUID
    resolved_projection_hash: str
    started_at_unix_ms: int


class ProgramSetRunningOutput(BaseModel):
    value: Program


class ProgramFinishTerminalInput(BaseModel):
    terminal_at_unix_ms: int
    terminal_status: str
    result_summary: str | None = Field(default=None)


class ProgramFinishTerminalOutput(BaseModel):
    value: Program


FUNCTIONS = {
    "Program": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic Program runtime instance for `(program_impl_id, key)`.",
                "is_constructor": True,
            },
            "input": ProgramBuildInput,
            "output": ProgramBuildOutput,
        },
        "attach_turn": {
            "canonical": {
                "name": "attach_turn",
                "description": "Attach a Turn receipt association to this Program.\n\nContract:\n- Mutates only Program membership (`turns`).\n- Turn lifecycle semantics remain Experience-owned by `Turn`.",
                "is_constructor": False,
            },
            "input": ProgramAttachTurnInput,
            "output": ProgramAttachTurnOutput,
        },
        "add_actor": {
            "canonical": {
                "name": "add_actor",
                "description": "Bind one ProgramConfig actor alias to one concrete Actor for this Program run.\n\nContract:\n- Mutates only Program membership (`program_actors`).\n- Identity is deterministic under Program via ProgramActor constructor keys.",
                "is_constructor": False,
            },
            "input": ProgramAddActorInput,
            "output": ProgramAddActorOutput,
        },
        "set_active_turn": {
            "canonical": {
                "name": "set_active_turn",
                "description": "Set (or clear) the active ProgramTurn association pointer for this Program.\n\nContract:\n- `active_turn_id` is optional.\n- When set, it must reference a `ProgramTurn` already attached under this Program.",
                "is_constructor": False,
            },
            "input": ProgramSetActiveTurnInput,
            "output": ProgramSetActiveTurnOutput,
        },
        "attach_branch": {
            "canonical": {
                "name": "attach_branch",
                "description": "Attach a resolved runtime branch receipt to this Program.\n\nContract:\n- Mutates only Program membership (`branches`).\n- Branch resolution remains runtime-owned by Turn/Projection authority.\n- Runtime may persist branch visibility/attention hints (`is_active`, `view_key`).",
                "is_constructor": False,
            },
            "input": ProgramAttachBranchInput,
            "output": ProgramAttachBranchOutput,
        },
        "set_running": {
            "canonical": {
                "name": "set_running",
                "description": "Mark Program as running with canonical branch resolution metadata.",
                "is_constructor": False,
            },
            "input": ProgramSetRunningInput,
            "output": ProgramSetRunningOutput,
        },
        "finish_terminal": {
            "canonical": {
                "name": "finish_terminal",
                "description": "Mark Program terminal with canonical status summary.",
                "is_constructor": False,
            },
            "input": ProgramFinishTerminalInput,
            "output": ProgramFinishTerminalOutput,
        },
    },
}

__all__ = [
    "Program",
    "ProgramBuildInput",
    "ProgramBuildOutput",
    "ProgramAttachTurnInput",
    "ProgramAttachTurnOutput",
    "ProgramAddActorInput",
    "ProgramAddActorOutput",
    "ProgramSetActiveTurnInput",
    "ProgramSetActiveTurnOutput",
    "ProgramAttachBranchInput",
    "ProgramAttachBranchOutput",
    "ProgramSetRunningInput",
    "ProgramSetRunningOutput",
    "ProgramFinishTerminalInput",
    "ProgramFinishTerminalOutput",
    "FUNCTIONS",
]
