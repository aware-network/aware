from __future__ import annotations

from contextvars import ContextVar
from typing import Any
from uuid import UUID

from aware_experience.program.language import InvocationPlan, encode_invocation_plan_artifact
from aware_environment.branching import stable_environment_thread_branch_id
from aware_experience.program.decode_snapshot_loader import (
    ProgramOntologySnapshotReader,
)
from aware_experience.program.invocation_plan_assembler import (
    assemble_invocation_plan_from_snapshot,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot

_PROGRAM_DECODE_INDEX_CTX: ContextVar[Any | None] = ContextVar(
    "program_decode_index",
    default=None,
)


def _resolve_decode_branch_id(
    *,
    environment_id: UUID,
    thread_id: UUID | None,
    request_branch_id: UUID | None,
) -> UUID:
    if request_branch_id is not None:
        return request_branch_id
    if thread_id is None:
        raise ValueError(
            "Program ontology decode requires thread_id when request branch_id is omitted"
        )
    return stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )


def _preferred_program_impl_key(program_ref: str) -> str | None:
    raw = (program_ref or "").strip()
    if ":" not in raw:
        return None
    _namespace, name = raw.split(":", 1)
    normalized = name.strip()
    return normalized or None


def _build_function_target_map(*, index: Any) -> dict[UUID, str]:
    mapping: dict[UUID, str] = {}
    for class_config in index.class_configs_by_id.values():
        owner = (class_config.name or "").strip()
        if not owner:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            function_name = (function_config.name or "").strip()
            if not function_name:
                continue
            function_target = f"{owner}.{function_name}"
            existing = mapping.get(function_config.id)
            if existing is None:
                mapping[function_config.id] = function_target
                continue
            if existing != function_target:
                raise ValueError(
                    "Ambiguous function target mapping for function_config_id "
                    + f"{function_config.id}: {existing!r} vs {function_target!r}"
                )
    return mapping


async def _load_program_ontology_snapshot_for_branch(
    *,
    branch_id: UUID,
    environment_id: UUID,
    program_config_id: UUID,
    preferred_program_impl_key: str | None,
    program_id: UUID | None = None,
) -> ProgramOntologySnapshot:
    decode_index = _PROGRAM_DECODE_INDEX_CTX.get()
    reader = ProgramOntologySnapshotReader(
        branch_id=branch_id,
        environment_id=environment_id,
        index=decode_index,
    )
    return await reader.load(
        program_config_id=program_config_id,
        preferred_program_impl_key=preferred_program_impl_key,
        program_id=program_id,
    )


async def _load_invocation_plan_for_branch(
    *,
    branch_id: UUID,
    environment_id: UUID,
    program_config_id: UUID,
    program_ref: str,
    function_targets: dict[UUID, str],
    program_id: UUID | None = None,
) -> InvocationPlan:
    if program_id is None:
        snapshot = await _load_program_ontology_snapshot_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            preferred_program_impl_key=_preferred_program_impl_key(program_ref),
        )
    else:
        snapshot = await _load_program_ontology_snapshot_for_branch(
            branch_id=branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            preferred_program_impl_key=_preferred_program_impl_key(program_ref),
            program_id=program_id,
        )
    return assemble_invocation_plan_from_snapshot(
        snapshot=snapshot,
        function_targets=function_targets,
        program_id=program_id,
    )


async def resolve_invocation_plan_artifact_from_ontology(
    *,
    resolver: Any,
    environment_id: UUID,
    thread_id: UUID | None,
    branch_id: UUID | None,
    program_config_id: UUID,
    program_ref: str,
    program_id: UUID | None = None,
) -> dict[str, object]:
    runtime = await resolver.get_runtime(environment_id=environment_id)
    index = runtime.invoker.get_index()
    function_targets = _build_function_target_map(index=index)
    decode_branch_id = _resolve_decode_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        request_branch_id=branch_id,
    )

    decode_index_token = _PROGRAM_DECODE_INDEX_CTX.set(index)
    try:
        invocation_plan = await _load_invocation_plan_for_branch(
            branch_id=decode_branch_id,
            environment_id=environment_id,
            program_config_id=program_config_id,
            program_ref=program_ref,
            function_targets=function_targets,
            program_id=program_id,
        )
    finally:
        _PROGRAM_DECODE_INDEX_CTX.reset(decode_index_token)

    return encode_invocation_plan_artifact(invocation_plan)


__all__ = ["resolve_invocation_plan_artifact_from_ontology"]
