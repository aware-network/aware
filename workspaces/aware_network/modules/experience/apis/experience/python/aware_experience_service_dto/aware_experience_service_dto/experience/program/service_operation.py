from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    JsonArray,
    JsonObject,
)


class ExperienceProgramServiceRequest(BaseModel):
    """
    Service DTOs for Experience-owned Program execution.
    Ownership:
    - Experience owns ProgramConfig, Program, ProgramTurn, and run/turn receipts.
    - Environment supplies topology ids and generic profile topology only.
    - Program execution must not be exposed through Environment API/SDK surfaces.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    request_context: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "apply_program_ref": "aware_experience_service_dto.experience.program.service_operation.ApplyProgramRefRequest",
        "submit_program_turn": "aware_experience_service_dto.experience.program.service_operation.SubmitProgramTurnRequest",
        "run_program": "aware_experience_service_dto.experience.program.service_operation.RunProgramRequest",
        "get_turn_execution": "aware_experience_service_dto.experience.program.service_operation.GetTurnExecutionRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownExperienceProgramServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceProgramServiceRequest(ExperienceProgramServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceProgramServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    status: str
    error: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "apply_program_ref": "aware_experience_service_dto.experience.program.service_operation.ApplyProgramRefResponse",
        "submit_program_turn": "aware_experience_service_dto.experience.program.service_operation.SubmitProgramTurnResponse",
        "run_program": "aware_experience_service_dto.experience.program.service_operation.RunProgramResponse",
        "get_turn_execution": "aware_experience_service_dto.experience.program.service_operation.GetTurnExecutionResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownExperienceProgramServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceProgramServiceResponse(ExperienceProgramServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ApplyProgramRefRequest(ExperienceProgramServiceRequest):
    """
    Internal Experience-owned pre-resolved invocation plan execution.
    Canonical external product boundary is `run_program`.
    """

    # Discriminator Tag
    operation: Literal["apply_program_ref"] = "apply_program_ref"

    # Attributes
    program_ref: str
    symbols: JsonObject = Field(default_factory=JsonObject)
    validate_only: bool = Field(default=False)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class SubmitProgramTurnRequest(ExperienceProgramServiceRequest):
    """Submit one Experience-owned Program turn."""

    # Discriminator Tag
    operation: Literal["submit_program_turn"] = "submit_program_turn"

    # Attributes
    target_actor_id: UUID
    program_ref: str
    symbols: JsonObject = Field(default_factory=JsonObject)
    message: str
    turn_index: int = Field(default=1)
    mailbox_key: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    max_attempts: int = Field(default=1)
    input_received_unix_ms: int | None = Field(default=None)
    turn_accepted_unix_ms: int | None = Field(default=None)
    wait_for_terminal: bool = Field(default=True)
    wait_timeout_ms: int | None = Field(default=None)


class RunProgramRequest(ExperienceProgramServiceRequest):
    """Run an Experience-owned Program with Experience-owned turn orchestration."""

    # Discriminator Tag
    operation: Literal["run_program"] = "run_program"

    # Attributes
    target_actor_id: UUID
    program_ref: str
    symbols: JsonObject = Field(default_factory=JsonObject)
    message: str
    turn_index: int = Field(default=1)
    mailbox_key: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    max_attempts: int = Field(default=1)
    input_received_unix_ms: int | None = Field(default=None)
    turn_accepted_unix_ms: int | None = Field(default=None)
    wait_for_terminal: bool = Field(default=True)
    wait_timeout_ms: int | None = Field(default=None)


class GetTurnExecutionRequest(ExperienceProgramServiceRequest):
    """Read one Experience-owned Program turn execution by id."""

    # Discriminator Tag
    operation: Literal["get_turn_execution"] = "get_turn_execution"

    # Attributes
    turn_id: UUID
    include_feedback: bool = Field(default=False)


class ApplyProgramRefResponse(ExperienceProgramServiceResponse):
    # Discriminator Tag
    operation: Literal["apply_program_ref"] = "apply_program_ref"

    # Attributes
    program_ref: str
    results: JsonArray = Field(default_factory=JsonArray)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)


class SubmitProgramTurnResponse(ExperienceProgramServiceResponse):
    # Discriminator Tag
    operation: Literal["submit_program_turn"] = "submit_program_turn"

    # Attributes
    turn_id: UUID | None = Field(default=None)
    mailbox_key: str | None = Field(default=None)
    deduped: bool = Field(default=False)
    terminal_status: str | None = Field(default=None)
    result_summary: str | None = Field(default=None)
    feedback_count: int = Field(default=0)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)


class RunProgramResponse(ExperienceProgramServiceResponse):
    # Discriminator Tag
    operation: Literal["run_program"] = "run_program"

    # Attributes
    program_ref: str
    program_run_id: UUID | None = Field(default=None)
    turn_id: UUID | None = Field(default=None)
    mailbox_key: str | None = Field(default=None)
    deduped: bool = Field(default=False)
    terminal_status: str | None = Field(default=None)
    result_summary: str | None = Field(default=None)
    feedback_count: int = Field(default=0)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)


class GetTurnExecutionResponse(ExperienceProgramServiceResponse):
    # Discriminator Tag
    operation: Literal["get_turn_execution"] = "get_turn_execution"

    # Attributes
    turn_id: UUID | None = Field(default=None)
    mailbox_key: str | None = Field(default=None)
    state: str | None = Field(default=None)
    terminal_status: str | None = Field(default=None)
    target_actor_id: UUID | None = Field(default=None)
    attempt_count: int | None = Field(default=None)
    max_attempts: int | None = Field(default=None)
    accepted_at_unix_ms: int | None = Field(default=None)
    started_at_unix_ms: int | None = Field(default=None)
    terminal_at_unix_ms: int | None = Field(default=None)
    error_code: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    result_summary: str | None = Field(default=None)
    feedback_count: int = Field(default=0)
    feedback: JsonArray = Field(default_factory=JsonArray)
    resolved_branch_id: UUID | None = Field(default=None)
    resolved_projection_hash: str | None = Field(default=None)
    lane_resolution_source: str | None = Field(default=None)
