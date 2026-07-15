from __future__ import annotations

from typing import Any

from aware_experience_service_dto.experience.program import (
    ApplyProgramRefRequest,
    ApplyProgramRefResponse,
    RunProgramRequest,
    RunProgramResponse,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)

from aware_experience.program.service import (
    ExperienceProgramRuntimeService,
    SubmitProgramTurnOperation,
)

_RETIRED_SUBMIT_PROGRAM_TURN_ERROR = (
    "Experience program operations require an injected Experience-owned submit "
    "turn operation; the deprecated runtime turn bridge is retired."
)


async def _retired_submit_program_turn(
    resolver: Any,
    request: SubmitProgramTurnRequest,
    *,
    apply_program_ref_op: object = None,
    store: Any | None = None,
) -> SubmitProgramTurnResponse:
    _ = resolver, request, apply_program_ref_op, store
    raise RuntimeError(_RETIRED_SUBMIT_PROGRAM_TURN_ERROR)


def _require_submit_program_turn_op(
    submit_program_turn_op: SubmitProgramTurnOperation | None,
) -> SubmitProgramTurnOperation:
    if submit_program_turn_op is None:
        raise RuntimeError(_RETIRED_SUBMIT_PROGRAM_TURN_ERROR)
    return submit_program_turn_op


def _build_program_runtime_service(
    *,
    submit_program_turn_op: SubmitProgramTurnOperation | None = None,
) -> ExperienceProgramRuntimeService:
    return ExperienceProgramRuntimeService(
        submit_program_turn_op=submit_program_turn_op or _retired_submit_program_turn,
    )


async def apply_program_ref(
    resolver: Any,
    request: ApplyProgramRefRequest,
) -> ApplyProgramRefResponse:
    service = _build_program_runtime_service()
    return await service.apply_program_ref(
        resolver=resolver,
        request=request,
    )


async def run_program(
    resolver: Any,
    request: RunProgramRequest | SubmitProgramTurnRequest,
    *,
    apply_program_ref_op: object = apply_program_ref,
    store: Any | None = None,
    submit_program_turn_op: SubmitProgramTurnOperation | None = None,
) -> RunProgramResponse | SubmitProgramTurnResponse:
    """Experience-owned Program runtime boundary.

    Compatibility note:
    `SubmitProgramTurnRequest` delegates only to an injected Experience-owned
    submit-turn operation. `RunProgramRequest` ownership and `program_run_id`
    materialization are Experience-owned here.
    """

    service = _build_program_runtime_service(
        submit_program_turn_op=_require_submit_program_turn_op(submit_program_turn_op),
    )
    return await service.run_program(
        resolver,
        request,
        apply_program_ref_op=apply_program_ref_op,
        store=store,
    )


__all__ = [
    "apply_program_ref",
    "run_program",
]
