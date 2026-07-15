from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

from aware_environment_service_dto.environment.environment import InvokeFunctionResponse
from aware_experience.program.runtime_support import (
    invoke_support,
    ocg_support,
    stable_ids,
)


@dataclass(frozen=True, slots=True)
class ProgramProjectionFunctionIds:
    thread_create_program: UUID
    program_attach_turn: UUID
    program_set_running: UUID
    program_finish_terminal: UUID


class ProgramProjectionPersistenceService:
    """Program lifecycle persistence via canonical façade calls."""

    _resolver: Any
    _actor_id: UUID | None
    _environment_id: UUID
    _process_id: UUID
    _thread_id: UUID
    _lane_branch_id: UUID
    _runtime: Any | None
    _index: Any | None
    _environment_projection_hash: str | None
    _program_projection_hash: str | None
    _function_ids: ProgramProjectionFunctionIds | None

    def __init__(
        self,
        *,
        resolver: Any,
        actor_id: UUID | None,
        environment_id: UUID,
        process_id: UUID | None,
        thread_id: UUID,
    ) -> None:
        self._resolver = resolver
        self._actor_id = actor_id
        self._environment_id = environment_id
        self._process_id = process_id or stable_ids.stable_boot_process_id(
            environment_id=environment_id
        )
        self._thread_id = thread_id
        self._lane_branch_id = stable_ids.stable_branch_id(
            environment_id=environment_id,
            thread_id=stable_ids.stable_boot_thread_id(environment_id=environment_id),
        )
        self._runtime = None
        self._index = None
        self._environment_projection_hash = None
        self._program_projection_hash = None
        self._function_ids = None

    async def _ensure_runtime_index(self) -> tuple[Any, Any]:
        if self._runtime is None:
            self._runtime = await self._resolver.get_runtime(
                environment_id=self._environment_id
            )
        if self._index is None:
            index = self._runtime.invoker.get_index()
            self._index = index
        return self._runtime, self._index

    async def _ensure_projection_context(
        self,
    ) -> tuple[str, str, ProgramProjectionFunctionIds]:
        if (
            self._environment_projection_hash is not None
            and self._program_projection_hash is not None
            and self._function_ids is not None
        ):
            return (
                self._environment_projection_hash,
                self._program_projection_hash,
                self._function_ids,
            )

        _runtime, index = await self._ensure_runtime_index()
        environment_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="Environment",
        )
        program_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="Program",
        )
        function_ids = ProgramProjectionFunctionIds(
            thread_create_program=ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix="aware_environment_ontology.thread.thread.Thread",
                function_name="create_program",
            ),
            program_attach_turn=ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix="aware_experience_ontology.program.program.Program",
                function_name="attach_turn",
            ),
            program_set_running=ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix="aware_experience_ontology.program.program.Program",
                function_name="set_running",
            ),
            program_finish_terminal=ocg_support.resolve_public_function_id(
                index=index,
                class_name_suffix="aware_experience_ontology.program.program.Program",
                function_name="finish_terminal",
            ),
        )
        self._environment_projection_hash = environment_projection_hash
        self._program_projection_hash = program_projection_hash
        self._function_ids = function_ids
        return environment_projection_hash, program_projection_hash, function_ids

    async def create_or_get_program(
        self,
        *,
        program_config_id: UUID,
        key: str | None,
        title: str | None = None,
        description: str | None = None,
        resolved_branch_id: UUID | None = None,
        resolved_projection_hash: str | None = None,
        position: int | None = None,
        is_default: bool = False,
    ) -> UUID:
        runtime, index = await self._ensure_runtime_index()
        environment_projection_hash, _program_projection_hash, function_ids = (
            await self._ensure_projection_context()
        )
        response = await invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=index,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=self._lane_branch_id,
            projection_hash=environment_projection_hash,
            object_id=self._thread_id,
            function_id=function_ids.thread_create_program,
            args=[
                program_config_id,
                key,
                title,
                description,
                resolved_branch_id,
                resolved_projection_hash,
                position,
                is_default,
            ],
            commit=True,
        )
        invoke_support.assert_invoke_succeeded(
            response=response,
            label="Thread.create_program",
        )
        program_id = self._extract_program_id(response=response)
        if program_id is None:
            raise RuntimeError(
                "Thread.create_program did not return program_id in payload"
            )
        return program_id

    async def set_running(
        self,
        *,
        program_id: UUID,
        resolved_branch_id: UUID,
        resolved_projection_hash: str,
        started_at_unix_ms: int,
    ) -> None:
        runtime, index = await self._ensure_runtime_index()
        _environment_projection_hash, program_projection_hash, function_ids = (
            await self._ensure_projection_context()
        )
        response = await invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=index,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=self._lane_branch_id,
            projection_hash=program_projection_hash,
            object_id=program_id,
            function_id=function_ids.program_set_running,
            args=[
                resolved_branch_id,
                resolved_projection_hash,
                int(started_at_unix_ms),
            ],
            commit=True,
        )
        invoke_support.assert_invoke_succeeded(
            response=response,
            label="Program.set_running",
        )

    async def attach_turn(self, *, program_id: UUID, turn_id: UUID) -> None:
        runtime, index = await self._ensure_runtime_index()
        _environment_projection_hash, program_projection_hash, function_ids = (
            await self._ensure_projection_context()
        )
        response = await invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=index,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=self._lane_branch_id,
            projection_hash=program_projection_hash,
            object_id=program_id,
            function_id=function_ids.program_attach_turn,
            args=[turn_id],
            commit=True,
        )
        invoke_support.assert_invoke_succeeded(
            response=response,
            label="Program.attach_turn",
        )

    async def finish_terminal(
        self,
        *,
        program_id: UUID,
        terminal_at_unix_ms: int,
        terminal_status: str,
        result_summary: str | None = None,
    ) -> None:
        runtime, index = await self._ensure_runtime_index()
        _environment_projection_hash, program_projection_hash, function_ids = (
            await self._ensure_projection_context()
        )
        response = await invoke_support.invoke_instance_environment_function(
            runtime=runtime,
            index=index,
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=self._lane_branch_id,
            projection_hash=program_projection_hash,
            object_id=program_id,
            function_id=function_ids.program_finish_terminal,
            args=[
                int(terminal_at_unix_ms),
                terminal_status,
                result_summary,
            ],
            commit=True,
        )
        invoke_support.assert_invoke_succeeded(
            response=response,
            label="Program.finish_terminal",
        )

    @staticmethod
    def _extract_wrapped_value(raw: object) -> object:
        if not isinstance(raw, Mapping):
            return raw
        mapping = cast(Mapping[object, object], raw)
        if "value" in mapping:
            return mapping["value"]
        return mapping

    @staticmethod
    def _coerce_uuid_or_none(raw: object) -> UUID | None:
        candidate = ProgramProjectionPersistenceService._extract_wrapped_value(raw)
        if candidate is None:
            return None
        if isinstance(candidate, UUID):
            return candidate
        text = str(candidate).strip()
        if not text:
            return None
        try:
            return UUID(text)
        except Exception:  # noqa: BLE001
            return None

    def _extract_program_id(self, *, response: InvokeFunctionResponse) -> UUID | None:
        payload = response.payload
        if not isinstance(payload, Mapping):
            return None
        return self._coerce_uuid_or_none(payload.get("program_id"))
