"""Optional public view over the original registered grammar source roles.

The required selector is request data, not source authority. No Workspace import,
new registry, lifecycle implementation, wire codec or automatic selection exists.
Failure evidence is delivered on leaving the composed operation's context.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import current_thread
from typing import NoReturn, TypeVar

from aware_code_module_manifest_contract_runtime.grammar_profile_source import _selector
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarRoleCleanupReceiptV1,
    CodeGrammarRoleFailureEvidenceV1,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody

from . import direct_host as direct
from . import grammar_profile_role as profile
from . import grammar_role_cleanup as cleanup
from . import grammar_syntax_role as syntax
from .grammar_role_attachment import _GrammarSourceRoleAttachment

_PROFILE_COMPOSE = profile._compose_grammar_profile_source_role
_PROFILE_CODE = _PROFILE_COMPOSE.__code__
_SYNTAX_COMPOSE = syntax._compose_grammar_syntax_role_join
_SYNTAX_CODE = _SYNTAX_COMPOSE.__code__
_T = TypeVar("_T")


class CodeGrammarRoleHost(direct._Opaque):
    """Sealed owner-issued view; copying it supplies no original association."""

    _state: object = None

    def __init_subclass__(cls, **kwargs):
        raise TypeError("grammar role host is sealed")


_ROLE_HOST = CodeGrammarRoleHost


@dataclass(eq=False, slots=True)
class _View:
    handle: CodeGrammarRoleHost
    profile_role: profile.CodeGrammarProfileSourceRole
    syntax_role: syntax.CodeGrammarSyntaxRoleJoin
    attachment: _GrammarSourceRoleAttachment
    process: int
    thread: object
    failure_phase: str | None = None
    primary: BaseException | None = None
    raw_return_present: bool = False
    raw_return: object = None


class CodeGrammarRoleFailureEvidenceError(Exception):
    """Immutable portable snapshot plus process-local original failure custody."""

    def __init__(
        self,
        snapshot: CodeGrammarRoleFailureEvidenceV1,
        ticket: cleanup.CodeGrammarRoleCleanup | None,
        primary: BaseException,
        *,
        raw_return_present: bool,
        raw_return: object,
    ) -> None:
        super().__init__("Code grammar role failure evidence")
        self._snapshot = snapshot
        self.cleanup_ticket = ticket
        self.raw_return_present = raw_return_present
        self.raw_return = raw_return
        self.original_primary = primary
        self.original_cause = primary.__cause__
        self.original_context = primary.__context__
        self.original_suppress_context = primary.__suppress_context__
        self.disposal_return_present = False
        self.disposal_return: object = None

    @property
    def snapshot(self) -> CodeGrammarRoleFailureEvidenceV1:
        return self._snapshot


def _ports() -> None:
    if (
        CodeGrammarRoleHost is not _ROLE_HOST
        or _ROLE_HOST.__dict__.get("_state", object()) is not None
        or profile._compose_grammar_profile_source_role is not _PROFILE_COMPOSE
        or _PROFILE_COMPOSE.__code__ is not _PROFILE_CODE
        or syntax._compose_grammar_syntax_role_join is not _SYNTAX_COMPOSE
        or _SYNTAX_COMPOSE.__code__ is not _SYNTAX_CODE
    ):
        raise ContractViolation("original grammar composition entrance differs")


def _view(host: CodeGrammarRoleHost, *, live: bool) -> _View:
    _ports()
    if type(host) is not _ROLE_HOST:
        raise TypeError("exact original grammar role host required")
    value = object.__getattribute__(host, "__dict__").get("_state")
    if type(value) is not _View or value.handle is not host:
        raise ContractViolation("original grammar public view required")
    if value.process != os.getpid() or value.thread is not current_thread():
        raise ContractViolation("grammar public view process or thread differs")
    if value.attachment.public_view is not host:
        raise ContractViolation("original grammar view attachment differs")
    first = profile._state(value.profile_role, live=live)
    second = syntax._state(value.syntax_role, live=live)
    if first.attachment is not value.attachment or second.profile_state is not first:
        raise ContractViolation("original grammar public role pair differs")
    return value


def _interrupted(error: BaseException) -> bool:
    return (
        any(_interrupted(child) for child in error.exceptions)
        if isinstance(error, BaseExceptionGroup)
        else isinstance(error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError))
    )


def _ticket_from_attempt(
    state, code_host, expected
) -> cleanup.CodeGrammarRoleCleanup | None:
    attachment = state.grammar_attachment
    if (
        type(attachment) is not _GrammarSourceRoleAttachment
        or attachment.state is not state
        or attachment.host is not code_host
        or attachment.expectations[0] is not expected
    ):
        return None
    custody = attachment.cleanup_custody
    if type(custody) is not cleanup._CleanupCustody:
        return None
    cleanup._custody(custody.ticket)
    return custody.ticket


@dataclass(frozen=True, slots=True)
class _OperationEvidence:
    attempt_ref: str | None = None
    correlation: tuple[str, ContentDigest, ContentDigest] | None = None
    known: tuple[SemanticValueCoordinate, ...] = ()
    raw_present: bool = False
    raw_return: object = None
    unvalidated: bool = False


@dataclass(slots=True)
class _DisposalObservation:
    invalid: bool = False
    raw_present: bool = False
    raw_return: object = None


def _operation_evidence(ticket: cleanup.CodeGrammarRoleCleanup) -> _OperationEvidence:
    # No cleanup observer/callback supplies or authenticates operation evidence.
    custody = cleanup._custody(ticket)
    resources = custody.profile_resources
    known: list[SemanticValueCoordinate] = []
    raw_present, raw_return, unvalidated = False, None, False
    if resources is not None:
        for row in (resources, resources.syntax):
            if row is None:
                continue
            if row.result_origin is not None:
                known.append(row.result_origin.coordinate)
            if row.raw_return_present and (
                row.registration_status == "unknown"
                and row.registration_origin is None
                or isinstance(row, cleanup._ProfileRoleResources)
                and row.host_status == "unknown"
                and row.host_origin is None
                or isinstance(row, cleanup._SyntaxRoleResources)
                and row.join_status == "unknown"
                and row.join_origin is None
            ):
                raw_present, raw_return = True, row.raw_return
            if (
                isinstance(row, cleanup._SyntaxRoleResources)
                and row.execution_return_present
                and row.result_origin is None
            ):
                raw_present, raw_return, unvalidated = True, row.execution_return, True
        if (
            resources.raw_return_present
            and resources.result_origin is None
            and resources.result_status == "unknown"
            and resources.raw_return is not resources.registration_origin
        ):
            raw_present, raw_return, unvalidated = True, resources.raw_return, True
        for _, returned in resources.cleanup_return_evidence:
            if returned is not None and not raw_present:
                raw_present, raw_return = True, returned
        handle = custody.attachment.public_view
        if type(handle) is _ROLE_HOST:
            view = object.__getattribute__(handle, "__dict__").get("_state")
            if (
                type(view) is _View
                and view.handle is handle
                and view.raw_return_present
            ):
                raw_present, raw_return, unvalidated = True, view.raw_return, True
    return _OperationEvidence(
        custody.attempt_ref,
        custody.correlation,
        tuple(sorted(known, key=lambda row: canonical_json_bytes(row.to_wire()))),
        raw_present,
        raw_return,
        unvalidated,
    )


def _unknown_cleanup(
    account: _OperationEvidence, *, cause: str
) -> CodeGrammarRoleCleanupReceiptV1:
    correlation = account.correlation
    return CodeGrammarRoleCleanupReceiptV1(
        account.attempt_ref,
        None if correlation is None else correlation[0],
        None if correlation is None else correlation[1],
        None if correlation is None else correlation[2],
        cause,
        "unverified",
        "unavailable",
        (),
        "unverified",
    )


def _receipt(
    ticket: cleanup.CodeGrammarRoleCleanup,
    returned: object,
    account: _OperationEvidence,
    *,
    terminal: bool,
) -> CodeGrammarRoleCleanupReceiptV1:
    if type(returned) is not CodeGrammarRoleCleanupReceiptV1:
        raise ContractViolation("original grammar cleanup returned an invalid receipt")
    returned.__post_init__()
    custody = cleanup._custody(ticket)
    correlation = account.correlation
    if (
        returned.attempt_ref != account.attempt_ref
        or returned.operation_ref != (None if correlation is None else correlation[0])
        or returned.profile_input_digest
        != (None if correlation is None else correlation[1])
        or returned.syntax_input_digest
        != (None if correlation is None else correlation[2])
        or custody.correlation != correlation
        or (
            custody.terminal_receipt is not None
            and returned is not custody.terminal_receipt
        )
        or (
            terminal
            and (
                custody.disposal_state != "complete"
                or returned is not custody.terminal_receipt
            )
        )
        or (custody.disposal_state == "complete" and custody.terminal_receipt is None)
    ):
        raise ContractViolation(
            "original ticket-bound grammar cleanup receipt required"
        )
    return returned


def _dispose(
    ticket: cleanup.CodeGrammarRoleCleanup,
    account: _OperationEvidence,
    observation: _DisposalObservation,
) -> None:
    returned = cleanup.dispose_grammar_role_cleanup(ticket)
    try:
        _receipt(ticket, returned, account, terminal=True)
    except BaseException as primary:
        observation.invalid = observation.raw_present = True
        observation.raw_return = returned  # Including an observed None.
        # Terminate this owned association; never adopt or close the raw return.
        try:
            cleanup._custody(ticket).attachment.retired = True
        except BaseException as observation_error:
            raise primary from observation_error
        raise


def _deliver(
    primary: BaseException,
    *,
    phase: str,
    ticket: cleanup.CodeGrammarRoleCleanup | None,
    attempted: bool,
    errors: tuple[BaseException, ...],
    account: _OperationEvidence,
    disposal: _DisposalObservation,
) -> NoReturn:
    raw_present, raw_return = account.raw_present, account.raw_return
    if ticket is None:
        receipt = (
            _unknown_cleanup(account, cause="construction_failure")
            if attempted
            else CodeGrammarRoleCleanupReceiptV1(
                None,
                None,
                None,
                None,
                "construction_failure",
                "not_started",
                "not_started",
                (),
                "verified",
            )
        )
    else:
        try:
            receipt = _receipt(
                ticket,
                cleanup.read_grammar_role_cleanup(ticket),
                account,
                terminal=False,
            )
        except BaseException as observation_error:
            errors = (*errors, observation_error)
            receipt = _unknown_cleanup(account, cause="context_exit")
        if disposal.invalid:
            # A later observation cannot validate a malformed disposal return.
            receipt = _unknown_cleanup(account, cause="context_exit")
        # Post-disposal child-return evidence cannot overwrite prior operation data.
        try:
            later = _operation_evidence(ticket)
            if later.raw_present and not raw_present:
                raw_present, raw_return = True, later.raw_return
        except BaseException as observation_error:
            errors = (*errors, observation_error)
    if disposal.raw_present and not raw_present:
        raw_present, raw_return = True, disposal.raw_return
    reason = (
        "interrupted"
        if _interrupted(primary)
        else "admission_refused"
        if phase == "validate_host"
        else "construction_failed"
        if phase == "construct"
        else "result_unvalidated"
        if phase == "validate_result" or account.unvalidated
        else "cleanup_failed"
        if phase == "close" or disposal.invalid
        else "execution_failed"
    )
    snapshot = CodeGrammarRoleFailureEvidenceV1(
        phase,
        reason,
        "unvalidated"
        if account.unvalidated
        else "known"
        if account.known
        else "unverified"
        if attempted
        else "not_started",
        account.known,
        receipt,
    )
    marker = CodeGrammarRoleFailureEvidenceError(
        snapshot,
        ticket,
        primary,
        raw_return_present=raw_present,
        raw_return=raw_return,
    )
    # Separate process-local ports can both return invalid values. Retain both;
    # these attributes do not extend the portable failure wire.
    marker.disposal_return_present = disposal.raw_present
    marker.disposal_return = disposal.raw_return
    if _interrupted(primary):
        raise primary from BaseExceptionGroup(
            "Code grammar cleanup and evidence", [*errors, marker]
        )
    raise BaseExceptionGroup(
        "Code grammar role failure", [primary, *errors, marker]
    ) from None


@contextmanager
def compose_registered_grammar_source_roles(
    *,
    code_host: direct.DirectValidationHost,
    profile_expected: inputs.SemanticInputProductionExpectation,
    syntax_expected: inputs.SemanticInputProductionExpectation,
    profile_key: str,
) -> Iterator[CodeGrammarRoleHost]:
    """Required unchanged request selector, then original two-stage construction.

    Only owned original custody is disposed. The context never closes the borrowed
    Code/Workspace host, source/catalog/product owners or epoch participant.
    """
    state = None
    ticket = None
    attempted = False
    view = None
    account = _OperationEvidence()
    disposal = _DisposalObservation()
    phase = "validate_host"
    try:
        key = _selector(profile_key)  # Before even looking up an attachment owner.
        _ports()
        state = direct._state(code_host)
        if state.grammar_attachment is not None:
            raise ContractViolation("grammar host attachment attempt already consumed")
        phase = "construct"
        attempted = True
        first = _PROFILE_COMPOSE(
            code_host=code_host,
            profile_expected=profile_expected,
            syntax_expected=syntax_expected,
            profile_key=key,
        )
        ticket = profile._state(first, live=False).resources.custody.ticket
        _ports()
        second = _SYNTAX_COMPOSE(profile_role=first)
        attachment = profile._state(first, live=True).attachment
        if attachment.public_view is not None:
            raise ContractViolation("grammar public view already issued")
        _ports()
        handle = object.__new__(_ROLE_HOST)
        view = _View(handle, first, second, attachment, os.getpid(), current_thread())
        object.__setattr__(handle, "_state", view)
        attachment.public_view = handle
        _view(handle, live=True)
        phase = "context_exit"
        yield handle
    except BaseException as primary:
        errors: list[BaseException] = []
        if ticket is None and attempted and state is not None:
            try:
                ticket = _ticket_from_attempt(state, code_host, profile_expected)
            except BaseException as error:
                errors.append(error)
        if view is not None and view.primary is primary:
            phase = view.failure_phase or phase
        if ticket is not None:
            try:
                account = _operation_evidence(ticket)
            except BaseException as error:
                errors.append(error)
            try:
                _dispose(ticket, account, disposal)
            except BaseException as error:
                try:
                    owned = cleanup._custody(ticket).profile_resources
                except BaseException as observation_error:
                    owned = None
                    errors.append(observation_error)
                for original in () if owned is None else owned.cleanup_errors:
                    if not any(original is item for item in errors):
                        errors.append(original)
                if not any(error is item for item in errors):
                    errors.append(error)
        _deliver(
            primary,
            phase=phase,
            ticket=ticket,
            attempted=attempted,
            errors=tuple(errors),
            account=account,
            disposal=disposal,
        )
    else:
        if ticket is None:
            raise ContractViolation("original grammar cleanup ticket required")
        try:
            account = _operation_evidence(ticket)
            _dispose(ticket, account, disposal)
        except BaseException as primary:
            close_errors: tuple[BaseException, ...] = ()
            try:
                owned = cleanup._custody(ticket).profile_resources
                if owned is not None:
                    close_errors = tuple(
                        error for error in owned.cleanup_errors if error is not primary
                    )
            except BaseException as observation_error:
                close_errors = (observation_error,)
            _deliver(
                primary,
                phase="close",
                ticket=ticket,
                attempted=True,
                errors=close_errors,
                account=account,
                disposal=disposal,
            )


def _call(host: CodeGrammarRoleHost, phase: str, call: Callable[[_View], _T]) -> _T:
    view = _view(host, live=False)
    try:
        return call(view)
    except BaseException as primary:
        view.failure_phase, view.primary = phase, primary
        raise


async def execute_grammar_profile_selection(host: CodeGrammarRoleHost) -> SemanticBody:
    view = _view(host, live=True)
    try:
        return await profile.execute_grammar_profile_source_role(view.profile_role)
    except BaseException as primary:
        view.failure_phase, view.primary = "profile_selection", primary
        raise


async def execute_grammar_syntax_binding(
    host: CodeGrammarRoleHost,
    *,
    predecessor: SemanticBody,
) -> SemanticBody:
    view = _view(host, live=True)
    try:
        return await syntax.execute_grammar_syntax_role_join(
            view.syntax_role, predecessor=predecessor
        )
    except BaseException as primary:
        view.failure_phase, view.primary = "syntax_binding", primary
        raise


def _result(view: _View, result: SemanticBody):
    state = profile._state(view.profile_role, live=False)
    rows: list[cleanup._ProfileRoleResources | cleanup._SyntaxRoleResources] = [
        state.resources
    ]
    if state.resources.syntax is not None:
        rows.append(state.resources.syntax)
    matches = [
        row for row in rows if row.result is result and row.result_status == "pending"
    ]
    if type(result) is not SemanticBody or len(matches) != 1:
        raise ContractViolation("original retained grammar result required")
    row = matches[0]
    if state.resources.host is None or row.registration is None:
        raise ContractViolation("original retained grammar resource required")
    return state.resources.host, row, row.registration


def validate_grammar_role_result(
    host: CodeGrammarRoleHost, *, result: SemanticBody
) -> None:
    def validate(view: _View) -> None:
        input_host, row, registration = _result(view, result)
        returned = inputs.validate_registered_semantic_input_result(
            input_host,
            registration,
            source_admission=row.expected.source_identity,
            expected=row.expected,
            result=result,
        )
        if returned is not None:
            view.raw_return_present, view.raw_return = True, returned
            raise ContractViolation(
                "original grammar result validation returned a value"
            )

    _call(host, "validate_result", validate)


def release_grammar_role_result(
    host: CodeGrammarRoleHost, *, result: SemanticBody
) -> None:
    def release(view: _View) -> None:
        input_host, row, registration = _result(view, result)
        if isinstance(row, cleanup._ProfileRoleResources):
            profile.release_grammar_profile_source_result(
                view.profile_role, result=result
            )
            return
        row.result_status = "unknown"
        try:
            returned = inputs.release_registered_semantic_input_result(
                input_host,
                registration,
                source_admission=row.expected.source_identity,
                expected=row.expected,
                result=result,
            )
            cleanup._require_profile_disposal_none(
                row.profile, "syntax_result", returned
            )
        except BaseException:
            view.attachment.retired = True
            raise
        row.result_status = "released"

    _call(host, "release_result", release)


__all__ = [
    "CodeGrammarRoleHost",
    "CodeGrammarRoleFailureEvidenceError",
    "compose_registered_grammar_source_roles",
    "execute_grammar_profile_selection",
    "execute_grammar_syntax_binding",
    "validate_grammar_role_result",
    "release_grammar_role_result",
]
