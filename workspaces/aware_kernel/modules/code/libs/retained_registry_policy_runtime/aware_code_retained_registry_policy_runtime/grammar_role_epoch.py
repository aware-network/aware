"""Internal lexical async lifetime on the original grammar attachment.

This supplies no producer, result, dependency or execution admission. The fixed
registered-role owner must enclose its entire awaited work in this envelope;
detached/background work is not supported or declared quiescent here. Original
participant hooks remain the only epoch accounting authority.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from threading import current_thread
from typing import AsyncIterator, Literal, cast

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionExpectation,
)

from . import direct_epoch_tracking as epochs
from . import direct_host as direct
from .epoch_participation import CodeEpochParticipation
from .grammar_role_attachment import (
    _GrammarSourceRoleAttachment,
    _validate_grammar_source_role_attachment,
)


@dataclass(eq=False, slots=True)
class _GrammarRoleEpochWork:
    attachment: _GrammarSourceRoleAttachment
    expected: SemanticInputProductionExpectation
    task: asyncio.Task[object]
    process: int
    thread: object
    use: object = None
    work_state: Literal["not_started", "running", "quiescent", "unverified"] = (
        "not_started"
    )
    epoch_state: Literal["not_started", "running", "finished", "uncertain"] = (
        "not_started"
    )
    exclusion_state: Literal["not_acquired", "released", "uncertain"] = "not_acquired"
    primary_error: BaseException | None = None
    settlement_error: BaseException | None = None
    # Reserve through entry and settlement callbacks, not just the yielded body.
    # Revocation cannot clear this original lexical lifetime evidence.
    lifetime_active: bool = True
    validation_epoch: Literal["not_started", "finished", "uncertain"] = "not_started"
    exit_validation_epoch: Literal["not_started", "finished", "uncertain"] = (
        "not_started"
    )


def _same_task(work: _GrammarRoleEpochWork) -> bool:
    return (
        work.process == os.getpid()
        and work.thread is current_thread()
        and work.task is asyncio.current_task()
    )


def _reserve(host, attachment, expected) -> _GrammarRoleEpochWork:
    if type(host) is not direct.DirectValidationHost:
        raise TypeError("exact original Code host required")
    if type(attachment) is not _GrammarSourceRoleAttachment:
        raise TypeError("exact original grammar attachment required")
    if type(expected) is not SemanticInputProductionExpectation:
        raise TypeError("exact original grammar expectation required")
    if not any(expected is value for value in attachment.expectations):
        raise ContractViolation("original grammar expectation identity required")
    task = asyncio.current_task()
    if task is None:
        raise ContractViolation("original async grammar task required")
    if attachment.process != os.getpid() or attachment.thread is not current_thread():
        raise ContractViolation("grammar attachment process or thread differs")
    work = _GrammarRoleEpochWork(
        attachment, expected, task, os.getpid(), current_thread()
    )
    with direct._LOCK:
        if (
            direct._HOSTS.get(host) is not attachment.state
            or attachment.host is not host
            or attachment.state.grammar_attachment is not attachment
            or attachment.retired
        ):
            raise ContractViolation("original grammar attachment is retired or changed")
        if expected.use_ref in attachment.epoch_work:
            raise ContractViolation("grammar role epoch use already consumed")
        if any(
            type(value) is not _GrammarRoleEpochWork
            or value.work_state not in ("quiescent", "not_started")
            or value.epoch_state != "finished"
            for value in attachment.epoch_work.values()
        ):
            raise ContractViolation("grammar role work is active or unresolved")
        attachment.epoch_work[expected.use_ref] = work
    # Reserve lexical evidence before the first borrowed validation callback.
    # This synchronous validator supplies finish evidence only on return.
    work.validation_epoch = "uncertain"
    try:
        _validate_grammar_source_role_attachment(host, attachment)
        work.validation_epoch = "finished"
    except BaseException as error:
        work.primary_error = error
        attachment.retired = True
        work.lifetime_active = False
        raise
    return work


def _settle(work: _GrammarRoleEpochWork) -> None:
    """Once-only original settlement; never retry an uncertain obligation."""
    attachment = work.attachment
    participant = cast(CodeEpochParticipation, attachment.binding.participant)
    if not _same_task(work) or work.work_state not in ("not_started", "quiescent"):
        raise ContractViolation("original grammar work is not quiescent")
    if work.epoch_state != "running":
        raise ContractViolation("grammar epoch settlement is terminal")
    settlement_primary = None
    released = None
    try:
        work.exclusion_state = "uncertain"
        released = epochs._GuardRelease()
        with epochs._guard(attachment.binding, release_state=released) as guard:
            try:
                if work.primary_error is None:
                    epochs._original(attachment.binding, attachment.host, guard)
                participant._finish_epoch_use(guard, work.use)
            except BaseException as error:
                settlement_primary = error
                raise
        # A successful hook with an unconfirmed exclusion release is not
        # complete settlement. The retained record stays uncertain even if
        # the original tracker already discharged its operation.
        work.epoch_state = "finished"
        work.exclusion_state = "released"
    except BaseException as error:
        work.epoch_state = "uncertain"
        if released is not None and released.confirmed:
            work.exclusion_state = "released"
        work.settlement_error = (
            settlement_primary if settlement_primary is not None else error
        )
        attachment.retired = True
        if settlement_primary is not None and settlement_primary is not error:
            raise settlement_primary from error
        raise


@asynccontextmanager
async def _grammar_source_epoch_use(
    host: direct.DirectValidationHost,
    attachment: _GrammarSourceRoleAttachment,
    *,
    expected: SemanticInputProductionExpectation,
) -> AsyncIterator[None]:
    """Fixed owner support, not a caller-configurable provider wrapper.

    No parent exclusion spans a source read or await. Exiting the original
    lexical task proves only its enclosed work ended, not a detached child's
    completion. Known results and resource disposal remain separate owners.
    """
    work = _reserve(host, attachment, expected)
    binding = attachment.binding
    participant = cast(CodeEpochParticipation, binding.participant)
    released = epochs._GuardRelease()
    try:
        work.exclusion_state = "uncertain"
        with epochs._guard(binding, release_state=released) as guard:
            try:
                epochs._original(binding, host, guard)
                work.epoch_state = "uncertain"
                work.use = participant._begin_epoch_use(
                    guard, binding.epoch, expected=binding.expected
                )
                try:
                    participant._start_epoch_use(guard, work.use)
                except BaseException as primary:
                    try:
                        participant._abandon_unstarted_epoch_use(guard, work.use)
                        work.epoch_state = "finished"
                    except BaseException as cleanup:
                        work.epoch_state = "uncertain"
                        work.settlement_error = cleanup
                        raise primary from cleanup
                    raise
                work.epoch_state = "running"
            except BaseException as primary:
                work.primary_error = primary
                raise
        work.exclusion_state = "released"
    except BaseException as primary:
        if work.primary_error is None:
            work.primary_error = primary
        # Unknown begin/start/release outcomes cannot be relabelled as absence.
        # The caller owns no usable entry and no work has been yielded.
        if released.confirmed:
            work.exclusion_state = "released"
        if work.epoch_state == "running" or (
            not released.confirmed and work.epoch_state != "not_started"
        ):
            work.epoch_state = "uncertain"
        attachment.retired = True
        work.lifetime_active = False
        if work.primary_error is not primary:
            work.settlement_error = primary
            raise work.primary_error from primary
        raise

    work.work_state = "running"
    try:
        yield
    except BaseException as primary:
        work.primary_error = primary
        attachment.retired = True
        raise
    finally:
        try:
            if not _same_task(work):
                work.work_state = "unverified"
                work.epoch_state = "uncertain"
                attachment.retired = True
                error = ContractViolation("grammar role exited from another task")
                work.settlement_error = error
                if work.primary_error is not None:
                    raise work.primary_error from error
                raise error
            work.work_state = "quiescent"
            if work.primary_error is None:
                # Exit validation acquires a distinct synchronous obligation.
                # Async settlement cannot authenticate this validator's finish.
                work.exit_validation_epoch = "uncertain"
                try:
                    _validate_grammar_source_role_attachment(host, attachment)
                    work.exit_validation_epoch = "finished"
                except BaseException as primary:
                    work.primary_error = primary
                    attachment.retired = True
            try:
                _settle(work)
            except BaseException as cleanup:
                if work.primary_error is not None:
                    raise work.primary_error from cleanup
                raise
            if work.primary_error is not None:
                raise work.primary_error
        finally:
            work.lifetime_active = False
