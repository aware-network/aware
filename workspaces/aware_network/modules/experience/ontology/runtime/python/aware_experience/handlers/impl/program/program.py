from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program import Program
from aware_experience_ontology.program.program_actor import ProgramActor
from aware_experience_ontology.program.program_branch import ProgramBranch
from aware_experience_ontology.program.program_turn import ProgramTurn

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Environment Ontology
from aware_experience_ontology.program.program_enums import ProgramRunStatus
from aware_experience_ontology.stable_ids import stable_program_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    program_impl_id: UUID,
    key: str = "default",
    title: str | None = None,
    description: str | None = None,
    resolved_branch_id: UUID | None = None,
    resolved_projection_hash: str | None = None,
) -> Program:
    """
    Create a deterministic Program runtime instance for `(program_impl_id, key)`.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip() or "default"
    program_id = stable_program_id(
        program_impl_id=program_impl_id,
        key=normalized_key,
    )

    session = current_handler_session()
    existing = session.imap_get(Program, program_id)
    if existing is not None:
        if existing.program_impl_id != program_impl_id:
            raise RuntimeError("Program.build program_impl mismatch for existing program: " f"program_id={program_id}")
        existing_key = (existing.key or "").strip() or "default"
        if existing_key != normalized_key:
            raise RuntimeError("Program.build key mismatch for existing program: " f"program_id={program_id}")
        return existing

    return Program(
        id=program_id,
        program_impl_id=program_impl_id,
        key=normalized_key,
        title=title,
        description=description,
        status=ProgramRunStatus.pending,
    )
    # --- AWARE: LOGIC END build


async def attach_turn(program: Program, turn_id: UUID) -> ProgramTurn:
    """
    Attach a Turn receipt association to this Program.

    Contract:
    - Mutates only Program membership (`turns`).
    - Turn lifecycle semantics remain Experience-owned by `Turn`.
    """

    # --- AWARE: LOGIC START attach_turn
    program_id = program.id
    if program_id is None:
        raise RuntimeError("Program.attach_turn requires Program.id")

    next_order = len(program.turns)
    assoc = await ProgramTurn.build_via_program(program_id=program_id, turn_id=turn_id, order=next_order)
    if not any(existing.id == assoc.id for existing in program.turns):
        program.turns.append(assoc)
    return assoc
    # --- AWARE: LOGIC END attach_turn


async def add_actor(program: Program, program_config_actor_config_id: UUID, actor_id: UUID) -> ProgramActor:
    """
    Bind one ProgramConfig actor alias to one concrete Actor for this Program run.

    Contract:
    - Mutates only Program membership (`program_actors`).
    - Identity is deterministic under Program via ProgramActor constructor keys.
    """

    # --- AWARE: LOGIC START add_actor
    program_id = program.id
    if program_id is None:
        raise RuntimeError("Program.add_actor requires Program.id")

    assoc = await ProgramActor.build_via_program(
        program_id=program_id,
        program_config_actor_config_id=program_config_actor_config_id,
        actor_id=actor_id,
    )
    if not any(existing.id == assoc.id for existing in program.program_actors):
        program.program_actors.append(assoc)
    return assoc
    # --- AWARE: LOGIC END add_actor


async def set_active_turn(program: Program, active_turn_id: UUID | None = None) -> Program:
    """
    Set (or clear) the active ProgramTurn association pointer for this Program.

    Contract:
    - `active_turn_id` is optional.
    - When set, it must reference a `ProgramTurn` already attached under this Program.
    """

    # --- AWARE: LOGIC START set_active_turn
    program_id = program.id
    if program_id is None:
        raise RuntimeError("Program.set_active_turn requires Program.id")

    if active_turn_id is None:
        program.active_turn_id = None
        program.active_turn = None
        return program

    if not any(assoc.id == active_turn_id for assoc in program.turns):
        raise RuntimeError(
            "Program.set_active_turn requires active_turn_id already attached ProgramTurn id: "
            f"program_id={program_id} active_turn_id={active_turn_id}"
        )

    session = current_handler_session()
    active_turn = session.imap_get(ProgramTurn, active_turn_id)
    program.active_turn_id = active_turn_id
    program.active_turn = active_turn
    return program
    # --- AWARE: LOGIC END set_active_turn


async def attach_branch(
    program: Program,
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

    # --- AWARE: LOGIC START attach_branch
    program_id = program.id
    if program_id is None:
        raise RuntimeError("Program.attach_branch requires Program.id")

    assoc = await ProgramBranch.build_via_program(
        program_id=program_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        key=key,
        view_key=view_key,
        is_active=is_active,
    )
    if not any(existing.id == assoc.id for existing in program.branches):
        program.branches.append(assoc)
    return assoc
    # --- AWARE: LOGIC END attach_branch


async def set_running(
    program: Program, resolved_branch_id: UUID, resolved_projection_hash: str, started_at_unix_ms: int
) -> Program:
    """
    Mark Program as running with canonical branch resolution metadata.
    """

    # --- AWARE: LOGIC START set_running
    normalized_projection_hash = resolved_projection_hash.strip()
    if not normalized_projection_hash:
        raise RuntimeError("Program.set_running requires non-empty resolved_projection_hash")
    program.status = ProgramRunStatus.running
    program.started_at_unix_ms = int(started_at_unix_ms)
    return program
    # --- AWARE: LOGIC END set_running


async def finish_terminal(
    program: Program, terminal_at_unix_ms: int, terminal_status: str, result_summary: str | None = None
) -> Program:
    """
    Mark Program terminal with canonical status summary.
    """

    # --- AWARE: LOGIC START finish_terminal
    normalized_status = terminal_status.strip()
    if not normalized_status:
        raise RuntimeError("Program.finish_terminal requires non-empty terminal_status")
    program.status = ProgramRunStatus.terminal
    program.terminal_at_unix_ms = int(terminal_at_unix_ms)
    program.terminal_status = normalized_status
    program.result_summary = (result_summary or "").strip() or None
    return program
    # --- AWARE: LOGIC END finish_terminal
