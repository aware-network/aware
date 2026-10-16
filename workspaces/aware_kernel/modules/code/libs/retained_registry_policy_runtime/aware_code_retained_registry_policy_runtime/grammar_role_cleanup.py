"""Original cleanup custody, detached reads and once-only owned disposal.

The original attachment retains the ticket before source validation. This cut
can retain profile host/registration/result resources; it closes no borrowed owner.
Unknown epoch/release evidence survives direct-host retirement; readers never
consult a cleared tracker to reconstruct completion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from threading import current_thread
from uuid import uuid4

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarRoleCleanupReceiptV1,
    CodeGrammarRoleCleanupResourceV1,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    AdmittedSemanticInputProducerRegistration,
    AdmittedSemanticInputRoleJoin,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    close_semantic_input_producer_registration,
    close_semantic_input_role_join,
    release_registered_semantic_input_result,
)

from . import direct_host as direct
from .grammar_role_attachment import (
    _GrammarSourceRoleAttachment,
    _validate_grammar_source_role_attachment,
)
from .grammar_role_epoch import _GrammarRoleEpochWork


class CodeGrammarRoleCleanup(direct._Opaque):
    """Original attachment-issued, sealed and nonportable cleanup-only ticket."""

    _custody: object = None

    def __init_subclass__(cls, **kwargs):
        raise TypeError("grammar cleanup ticket is sealed")


@dataclass(eq=False, slots=True)
class _CleanupCustody:
    ticket: CodeGrammarRoleCleanup
    attachment: _GrammarSourceRoleAttachment
    host: direct.DirectValidationHost
    original_state: direct._State
    journal: dict[str, object]
    expectations: tuple[SemanticInputProductionExpectation, ...]
    use_refs: tuple[str, str]
    attempt_ref: str
    process: int
    thread: object
    correlation: tuple[str, ContentDigest, ContentDigest] | None = None
    construction_work: str = "not_started"
    construction_epoch: str = "not_started"
    construction_error: BaseException | None = None
    disposal_state: str = "pending"
    attachment_status: str = "pending"
    disposal_cause: str | None = None
    disposal_error: BaseException | None = None
    terminal_receipt: CodeGrammarRoleCleanupReceiptV1 | None = None
    profile_resources: _ProfileRoleResources | None = None


@dataclass(eq=False, slots=True)
class _ProfileRoleResources:
    custody: _CleanupCustody
    expected: SemanticInputProductionExpectation
    role_state: object = None
    constructing: bool = True
    validation_epoch: str = "not_started"
    construction_error: BaseException | None = None
    host: SemanticInputProducerHost | None = None
    host_origin: SemanticInputProducerHost | None = None
    host_status: str = "not_acquired"
    registration: AdmittedSemanticInputProducerRegistration | None = None
    registration_origin: AdmittedSemanticInputProducerRegistration | None = None
    registration_status: str = "not_acquired"
    result: SemanticBody | None = None
    result_origin: SemanticBody | None = None
    result_status: str = "not_acquired"
    raw_return_present: bool = False
    raw_return: object = None
    cleanup_errors: tuple[BaseException, ...] = ()
    cleanup_return_evidence: tuple[tuple[str, object], ...] = ()
    syntax: _SyntaxRoleResources | None = None


@dataclass(eq=False, slots=True)
class _SyntaxRoleResources:
    profile: _ProfileRoleResources
    expected: SemanticInputProductionExpectation
    role_state: object = None
    constructing: bool = True
    validation_epoch: str = "not_started"
    construction_error: BaseException | None = None
    registration: AdmittedSemanticInputProducerRegistration | None = None
    registration_origin: AdmittedSemanticInputProducerRegistration | None = None
    registration_status: str = "not_acquired"
    join: AdmittedSemanticInputRoleJoin | None = None
    join_origin: AdmittedSemanticInputRoleJoin | None = None
    join_status: str = "not_acquired"
    raw_return_present: bool = False
    raw_return: object = None
    execution_attempted: bool = False
    execution_return_present: bool = False
    execution_return: object = None
    result: SemanticBody | None = None
    result_origin: SemanticBody | None = None
    result_status: str = "not_acquired"


def _custody(ticket: CodeGrammarRoleCleanup) -> _CleanupCustody:
    if type(ticket) is not CodeGrammarRoleCleanup:
        raise TypeError("exact original grammar cleanup ticket required")
    declaration = CodeGrammarRoleCleanup.__dict__
    if "_custody" not in declaration or declaration["_custody"] is not None:
        raise ContractViolation("original cleanup ticket field substituted")
    # Bypass descriptors/instance attribute hooks. Identity is verified in
    # the original attachment's retained custody, not this detached field.
    state = object.__getattribute__(ticket, "__dict__").get("_custody")
    if state is None:
        raise ContractViolation("unissued grammar cleanup ticket")
    if type(state) is not _CleanupCustody or state.ticket is not ticket:
        raise ContractViolation("original grammar cleanup custody required")
    if state.process != os.getpid() or state.thread is not current_thread():
        raise ContractViolation("cleanup ticket process or thread differs")
    attachment = state.attachment
    if (
        attachment.cleanup_custody is not state
        or attachment.state is not state.original_state
        or attachment.host is not state.host
        or state.original_state.grammar_attachment is not attachment
        or attachment.epoch_work is not state.journal
        or attachment.expectations is not state.expectations
    ):
        raise ContractViolation("original cleanup attachment or journal substituted")
    resources = state.profile_resources
    if resources is not None and (
        type(resources) is not _ProfileRoleResources
        or resources.custody is not state
        or resources.expected is not state.expectations[0]
        or attachment.profile_resources is not resources
        or resources.host is not resources.host_origin
        or resources.registration is not resources.registration_origin
        or resources.result is not resources.result_origin
    ):
        raise ContractViolation("original profile resource custody substituted")
    if resources is not None and resources.syntax is not None:
        syntax = resources.syntax
        if (
            type(syntax) is not _SyntaxRoleResources
            or syntax.profile is not resources
            or attachment.syntax_resources is not syntax
            or syntax.expected is not state.expectations[1]
            or syntax.registration is not syntax.registration_origin
            or syntax.join is not syntax.join_origin
            or syntax.result is not syntax.result_origin
        ):
            raise ContractViolation("original syntax resource custody substituted")
    return state


def _reserve_syntax_role_resources(
    profile: _ProfileRoleResources,
) -> _SyntaxRoleResources:
    state = _custody(profile.custody.ticket)
    with direct._LOCK:
        if (
            state.profile_resources is not profile
            or state.attachment.retired
            or state.disposal_state != "pending"
            or profile.constructing
            or profile.result_status != "not_acquired"
            or profile.syntax is not None
            or state.attachment.syntax_resources is not None
        ):
            raise ContractViolation("original syntax role admission is unavailable")
        syntax = _SyntaxRoleResources(profile, state.expectations[1])
        profile.syntax = syntax
        state.attachment.syntax_resources = syntax
    return syntax


def _reserve_profile_role_resources(
    attachment: _GrammarSourceRoleAttachment,
) -> _ProfileRoleResources:
    retained = attachment.cleanup_custody
    if type(retained) is not _CleanupCustody:
        raise ContractViolation("original cleanup custody required")
    state = _custody(retained.ticket)
    with direct._LOCK:
        if (
            attachment.retired
            or state.disposal_state != "pending"
            or state.profile_resources is not None
            or attachment.profile_resources is not None
        ):
            raise ContractViolation("profile resource construction is consumed")
        resources = _ProfileRoleResources(state, state.expectations[0])
        state.profile_resources = resources
        attachment.profile_resources = resources
    return resources


def _issue_grammar_role_cleanup(
    attachment: _GrammarSourceRoleAttachment,
) -> CodeGrammarRoleCleanup:
    """Fixed attachment construction only; caller values cannot issue custody."""
    if type(attachment) is not _GrammarSourceRoleAttachment:
        raise TypeError("exact original grammar attachment required")
    if attachment.process != os.getpid() or attachment.thread is not current_thread():
        raise ContractViolation("grammar attachment process or thread differs")
    with direct._LOCK:
        if attachment.cleanup_custody is not None:
            state = attachment.cleanup_custody
            if type(state) is not _CleanupCustody or state.attachment is not attachment:
                raise ContractViolation("original cleanup custody unavailable")
            _custody(state.ticket)
            return state.ticket
        if (
            direct._HOSTS.get(attachment.host) is not attachment.state
            or attachment.state.closed
            or attachment.state.grammar_attachment is not attachment
        ):
            raise ContractViolation("original retained attachment required")
        ticket = object.__new__(CodeGrammarRoleCleanup)
        state = _CleanupCustody(
            ticket,
            attachment,
            attachment.host,
            attachment.state,
            attachment.epoch_work,
            attachment.expectations,
            (
                attachment.expectations[0].use_ref,
                attachment.expectations[1].use_ref,
            ),
            "aware.code.grammar.cleanup." + uuid4().hex,
            os.getpid(),
            current_thread(),
        )
        object.__setattr__(ticket, "_custody", state)
        attachment.cleanup_custody = state
    return ticket


def _correlate_grammar_role_cleanup(attachment: _GrammarSourceRoleAttachment) -> None:
    """Only after the original construction's complete validation succeeds.

    Before that point, detached labels/digests remain unauthenticated and are
    omitted from the receipt. Copy validated scalar values so later movement
    or mutation cannot restamp the original association.
    """
    retained = attachment.cleanup_custody
    if type(retained) is not _CleanupCustody:
        raise ContractViolation("original cleanup custody required")
    state = _custody(retained.ticket)
    if state.construction_error is not None or attachment.retired:
        raise ContractViolation("original grammar correlation attempt is retired")
    # The synchronous original validator has no detached settlement receipt.
    # A returned exception cannot reveal whether finish succeeded; preserve
    # uncertainty instead of consulting an empty/revoked tracker afterward.
    state.construction_work = "unverified"
    state.construction_epoch = "uncertain"
    try:
        _validate_grammar_source_role_attachment(attachment.host, attachment)
        # Preserve independently confirmed settlement even if later snapshot
        # checks or scalar preparation fail. It is not resource cleanup.
        state.construction_epoch = "finished"
        for expected, snapshot in zip(
            attachment.expectations, attachment.snapshots, strict=True
        ):
            snapshot.check(expected)
        profile, syntax = attachment.expectations
        correlation = (
            profile.operation_ref,
            ContentDigest(profile.input_digest.value),
            ContentDigest(syntax.input_digest.value),
        )
        for expected, snapshot in zip(
            attachment.expectations, attachment.snapshots, strict=True
        ):
            snapshot.check(expected)
        # One publication: readers see either no correlation or all three
        # validated scalar copies, never a partially prepared association.
        state.correlation = correlation
    except BaseException as error:
        if state.construction_error is None:
            state.construction_error = error
        attachment.retired = True
        raise
    finally:
        state.construction_work = "quiescent"


def read_grammar_role_cleanup(
    ticket: CodeGrammarRoleCleanup,
) -> CodeGrammarRoleCleanupReceiptV1:
    """Noncreating/non-authorizing original read; no borrowed owner calls.

    Retired original hosts remain readable through this issued custody. This
    never refreshes borrowed owners or upgrades a terminal disposal receipt.
    """
    state = _custody(ticket)
    if state.terminal_receipt is not None:
        return state.terminal_receipt
    if state.disposal_state == "complete":
        raise ContractViolation("original terminal cleanup receipt unavailable")
    attachment = state.attachment
    profile = state.profile_resources
    syntax = None if profile is None else profile.syntax
    if any(key not in state.use_refs for key in state.journal):
        raise ContractViolation("foreign grammar epoch journal entry")
    records = []
    for index, use_ref in enumerate(state.use_refs):
        if use_ref not in state.journal:
            continue
        work = state.journal[use_ref]
        if (
            type(work) is not _GrammarRoleEpochWork
            or work.attachment is not attachment
            or work.expected is not state.expectations[index]
        ):
            raise ContractViolation("original grammar epoch work required")
        records.append((index, work))
    work_state = (
        "unverified"
        if state.construction_work == "unverified"
        or (profile is not None and profile.constructing)
        or (syntax is not None and syntax.constructing)
        or any(
            row.lifetime_active or row.work_state in ("running", "unverified")
            for _, row in records
        )
        else "quiescent"
        if state.construction_work == "quiescent"
        or any(row.work_state == "quiescent" for _, row in records)
        else "not_started"
    )
    if (
        state.construction_epoch == "uncertain"
        or (profile is not None and profile.validation_epoch == "uncertain")
        or (syntax is not None and syntax.validation_epoch == "uncertain")
    ) or any(
        row.validation_epoch == "uncertain"
        or row.exit_validation_epoch == "uncertain"
        or row.epoch_state == "uncertain"
        or row.exclusion_state == "uncertain"
        for _, row in records
    ):
        epoch_state = "uncertain"
    elif any(row.epoch_state == "running" for _, row in records):
        epoch_state = "running"
    elif state.construction_epoch == "finished" and all(
        row.epoch_state == "finished" for _, row in records
    ):
        epoch_state = "finished"
    else:
        epoch_state = "not_started"
    rows = [
        CodeGrammarRoleCleanupResourceV1(
            "attachment",
            state.attempt_ref + ".attachment",
            "blocked_active" if work_state == "unverified" else state.attachment_status,
        )
    ]
    if state.construction_epoch != "not_started":
        rows.append(
            CodeGrammarRoleCleanupResourceV1(
                "epoch_use",
                state.attempt_ref + ".epoch.construction",
                "released" if state.construction_epoch == "finished" else "unknown",
            )
        )
    for index, row in records:
        if row.exit_validation_epoch != "not_started":
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    "epoch_use",
                    state.attempt_ref + ".epoch.validation.exit." + str(index),
                    "released"
                    if row.exit_validation_epoch == "finished"
                    else "unknown",
                )
            )
        if row.validation_epoch != "not_started":
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    "epoch_use",
                    state.attempt_ref + ".epoch.validation." + str(index),
                    "released" if row.validation_epoch == "finished" else "unknown",
                )
            )
        status = {
            "not_started": "not_acquired",
            "running": "blocked_active",
            "finished": "released",
            "uncertain": "unknown",
        }[row.epoch_state]
        rows.append(
            CodeGrammarRoleCleanupResourceV1(
                "epoch_use", state.attempt_ref + ".epoch." + str(index), status
            )
        )
    if profile is not None:
        for kind, status in (
            ("role_host", profile.host_status),
            ("profile_registration", profile.registration_status),
            ("profile_result", profile.result_status),
        ):
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    kind, state.attempt_ref + "." + kind, status
                )
            )
        if profile.validation_epoch != "not_started":
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    "epoch_use",
                    state.attempt_ref + ".epoch.profile-construction",
                    "released" if profile.validation_epoch == "finished" else "unknown",
                )
            )
    if syntax is not None:
        for kind, status in (
            ("syntax_registration", syntax.registration_status),
            ("role_join", syntax.join_status),
            ("syntax_result", syntax.result_status),
        ):
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    kind, state.attempt_ref + "." + kind, status
                )
            )
        if syntax.validation_epoch != "not_started":
            rows.append(
                CodeGrammarRoleCleanupResourceV1(
                    "epoch_use",
                    state.attempt_ref + ".epoch.syntax-construction",
                    "released" if syntax.validation_epoch == "finished" else "unknown",
                )
            )
    cause = (
        "construction_failure"
        if state.construction_error is not None
        or (profile is not None and profile.construction_error is not None)
        or (syntax is not None and syntax.construction_error is not None)
        else state.disposal_cause
        if state.disposal_cause is not None
        else "execution_failure"
        if attachment.retired
        else "normal_close"
    )
    correlation = state.correlation
    operation_ref, profile_digest, syntax_digest = (
        (None, None, None) if correlation is None else correlation
    )
    resources = tuple(
        sorted(
            rows,
            key=lambda row: (row.resource_kind.encode(), row.resource_ref.encode()),
        )
    )
    settled = (
        work_state in {"not_started", "quiescent"}
        and epoch_state in {"not_started", "finished"}
        and all(row.status in {"not_acquired", "released"} for row in resources)
    )
    return CodeGrammarRoleCleanupReceiptV1(
        state.attempt_ref,
        operation_ref,
        profile_digest,
        syntax_digest,
        cause,
        work_state,
        epoch_state,
        resources,
        "verified" if settled else "unverified",
    )


def _require_profile_disposal_none(
    profile: _ProfileRoleResources, resource_kind: str, returned: object
) -> None:
    # Presence is the retained row, including a genuine None. Raw values never
    # enter the portable receipt; an invalid return cannot confirm release.
    profile.cleanup_return_evidence += ((resource_kind, returned),)
    if returned is not None:
        raise ContractViolation(
            "original " + resource_kind + " disposal returned a value"
        )


def _release_owned_grammar_attachment(state: _CleanupCustody) -> None:
    """Release this owned execution association, retaining custody evidence.

    Borrowed host, participant, catalogs, sources and products remain untouched.
    Retirement prevents all original grammar execution/validation on the record.
    """
    profile = state.profile_resources
    failures: list[BaseException] = []
    if profile is not None:
        syntax = profile.syntax
        if syntax is not None:
            if syntax.result_status == "pending":
                syntax.result_status = "unknown"
                try:
                    if (
                        profile.host is None
                        or syntax.registration is None
                        or syntax.result is None
                    ):
                        raise ContractViolation("original syntax result missing")
                    returned = release_registered_semantic_input_result(
                        profile.host,
                        syntax.registration,
                        source_admission=syntax.expected.source_identity,
                        expected=syntax.expected,
                        result=syntax.result,
                    )
                    _require_profile_disposal_none(profile, "syntax_result", returned)
                    syntax.result_status = "released"
                except BaseException as error:
                    failures.append(error)
            if syntax.join_status == "pending":
                syntax.join_status = "unknown"
                try:
                    if profile.host is None or syntax.join is None:
                        raise ContractViolation("original syntax join missing")
                    returned = close_semantic_input_role_join(profile.host, syntax.join)
                    _require_profile_disposal_none(profile, "role_join", returned)
                    syntax.join_status = "released"
                except BaseException as error:
                    failures.append(error)
            if syntax.registration_status == "pending":
                syntax.registration_status = "unknown"
                try:
                    if profile.host is None or syntax.registration is None:
                        raise ContractViolation("original syntax registration missing")
                    returned = close_semantic_input_producer_registration(
                        profile.host, syntax.registration
                    )
                    _require_profile_disposal_none(
                        profile, "syntax_registration", returned
                    )
                    syntax.registration_status = "released"
                except BaseException as error:
                    failures.append(error)
        if profile.result_status == "pending":
            profile.result_status = "unknown"
            try:
                if (
                    profile.host is None
                    or profile.registration is None
                    or profile.result is None
                ):
                    raise ContractViolation("original profile result resources missing")
                returned = release_registered_semantic_input_result(
                    profile.host,
                    profile.registration,
                    source_admission=profile.expected.source_identity,
                    expected=profile.expected,
                    result=profile.result,
                )
                _require_profile_disposal_none(profile, "profile_result", returned)
                profile.result_status = "released"
            except BaseException as error:
                failures.append(error)
        if profile.registration_status == "pending":
            profile.registration_status = "unknown"
            try:
                if profile.host is None or profile.registration is None:
                    raise ContractViolation("original profile registration missing")
                returned = close_semantic_input_producer_registration(
                    profile.host, profile.registration
                )
                _require_profile_disposal_none(
                    profile, "profile_registration", returned
                )
                profile.registration_status = "released"
            except BaseException as error:
                failures.append(error)
        if profile.host_status == "pending":
            profile.host_status = "unknown"
            try:
                if profile.host is None:
                    raise ContractViolation("original profile host missing")
                returned = profile.host.close()
                _require_profile_disposal_none(profile, "role_host", returned)
                profile.host_status = "released"
            except BaseException as error:
                failures.append(error)
        profile.cleanup_errors = tuple(failures)
    state.attachment.retired = True
    # This fixed owner records retirement independently of child cleanup.
    state.attachment_status = "released"
    if failures:
        raise failures[0]


def dispose_grammar_role_cleanup(
    ticket: CodeGrammarRoleCleanup,
) -> CodeGrammarRoleCleanupReceiptV1:
    """Once-only disposal; no source callbacks, epoch retry or borrowed close.

    Unwound but uncertain epoch work permits owned attachment retirement, never
    verified whole-context cleanup. A preflight refusal does not spend custody.
    """
    state = _custody(ticket)
    with direct._LOCK:
        if state.terminal_receipt is not None:
            return state.terminal_receipt
        if state.disposal_state != "pending":
            raise ContractViolation("original grammar disposal is already consumed")
        before = read_grammar_role_cleanup(ticket)
        if before.work_state not in {"not_started", "quiescent"}:
            raise ContractViolation("original grammar work is not quiescent")
        state.disposal_cause = before.cause
        state.disposal_state = "in_progress"
    # No original owner lock spans disposal. The fixed release uses only original
    # owned disposal ports; partial/invalid returns remain unknown and spent.
    primary = None
    try:
        returned = _release_owned_grammar_attachment(state)
        if returned is not None:
            raise ContractViolation("original attachment release returned a value")
        state.attachment_status = "released"
    except BaseException as error:
        state.disposal_error = error
        if state.attachment_status != "released":
            state.attachment_status = "unknown"
        state.attachment.retired = True
        primary = error
    try:
        state.terminal_receipt = read_grammar_role_cleanup(ticket)
    except BaseException as error:
        if state.disposal_error is None:
            state.disposal_error = error
        if primary is not None:
            raise primary from error
        raise
    finally:
        state.disposal_state = "complete"
    if primary is not None:
        raise primary
    return state.terminal_receipt
