"""Original Code cleanup-read mechanics; source/parent fixtures are explicit.

This qualifies no productive registration, original application or resource
disposal. Private custody retrieval below represents the future owner composer,
not a public bootstrap or a way to infer another execution's context.
"""

import asyncio
import copy
import os
import pickle
from threading import Thread

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as owner
from aware_code_retained_registry_policy_runtime import grammar_role_epoch as epochs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarRoleCleanupReceiptV1,
    decode_grammar_role_cleanup,
    encode_grammar_role_cleanup,
)
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import attach, case


def custody(host):
    return direct._HOSTS[host].grammar_attachment.cleanup_custody


def test_original_ticket_and_canonical_receipt_do_not_complete_cleanup(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        before = len(source.calls)
        receipt = owner.read_grammar_role_cleanup(ticket)
        assert type(ticket) is owner.CodeGrammarRoleCleanup
        assert type(receipt) is CodeGrammarRoleCleanupReceiptV1
        assert receipt.operation_ref == source.inputs[0].operation_ref
        assert receipt.profile_input_digest == source.inputs[0].input_digest
        assert receipt.syntax_input_digest == source.inputs[1].input_digest
        assert receipt.profile_input_digest != receipt.syntax_input_digest
        assert receipt.work_state == "quiescent" and receipt.epoch_state == "finished"
        assert receipt.completion == "unverified"
        assert receipt.resources[0].resource_kind == "attachment"
        assert receipt.resources[0].status == "pending"
        assert receipt.resources[1].status == "released"
        assert (
            decode_grammar_role_cleanup(encode_grammar_role_cleanup(receipt)) == receipt
        )
        assert owner.read_grammar_role_cleanup(ticket) == receipt
        assert owner._issue_grammar_role_cleanup(attachment) is ticket
        assert not ep._state(participant).uses
        assert not attachment.retired and len(source.calls) == before
        assert callable(owner.dispose_grammar_role_cleanup)


def test_ticket_is_retained_before_original_source_validation(admissions):
    with case(admissions) as (source, host, _, _):
        observed = []

        def observe():
            state = custody(host)
            before = len(source.calls)
            receipt = owner.read_grammar_role_cleanup(state.ticket)
            assert receipt.operation_ref is None
            assert receipt.profile_input_digest is receipt.syntax_input_digest is None
            assert receipt.work_state == "unverified"
            assert receipt.epoch_state == "uncertain"
            assert receipt.cause == "normal_close"
            assert receipt.completion == "unverified"
            assert len(source.calls) == before
            observed.append(state.ticket)

        source.after_read = observe
        attachment = attach(source, host)
        assert len(observed) == 2
        assert all(ticket is attachment.cleanup_custody.ticket for ticket in observed)


@pytest.mark.parametrize(
    "error", (ValueError("source"), KeyboardInterrupt(), asyncio.CancelledError())
)
def test_failed_construction_has_custody_but_no_unverified_correlation(
    admissions, error
):
    with case(admissions) as (source, host, participant, _):
        source.failure = error
        with pytest.raises(type(error)) as caught:
            attach(source, host)
        assert caught.value is error
        ticket = custody(host).ticket
        assert custody(host).construction_error is error
        before = len(source.calls)
        receipt = owner.read_grammar_role_cleanup(ticket)
        assert receipt.operation_ref is None
        assert receipt.profile_input_digest is receipt.syntax_input_digest is None
        assert receipt.work_state == "quiescent" and receipt.epoch_state == "uncertain"
        assert (
            receipt.cause == "construction_failure"
            and receipt.completion == "unverified"
        )
        # No detached original settlement receipt exists for this failure.
        # An empty tracker must not upgrade this uncertainty into completion.
        assert not ep._state(participant).uses
        assert len(source.calls) == before
        source.failure = None
        with pytest.raises(ContractViolation, match="retired"):
            owner._correlate_grammar_role_cleanup(custody(host).attachment)
        assert custody(host).construction_error is error
        assert owner.read_grammar_role_cleanup(ticket) == receipt


@pytest.mark.parametrize("bad", (None, {}, (), object()))
def test_foreign_ticket_shapes_refuse(admissions, bad):
    with case(admissions) as (source, host, _, _):
        attach(source, host)
        before = len(source.calls)
        with pytest.raises(TypeError):
            owner.read_grammar_role_cleanup(bad)
        assert len(source.calls) == before


@pytest.mark.parametrize("index", (0, 1))
@pytest.mark.parametrize("field", ("operation_ref", "input_digest"))
def test_late_release_movement_retains_error_and_cannot_restore(
    admissions, index, field
):
    with case(admissions) as (source, host, _, _):
        expected = source.inputs[index]
        original_value = getattr(expected, field)
        original_lock = source.lock
        armed = False
        moved = False

        def arm():
            nonlocal armed
            armed = True

        class MovingRelease:
            def acquire(self, *args, **kwargs):
                return original_lock.acquire(*args, **kwargs)

            def release(self):
                nonlocal moved
                original_lock.release()
                if armed and not moved:
                    moved = True
                    value = (
                        "moved.after.original.release"
                        if field == "operation_ref"
                        else ContentDigest.of_bytes(b"moved after original release")
                    )
                    object.__setattr__(expected, field, value)

        source.lock = MovingRelease()
        source.after_read = arm
        try:
            with pytest.raises(ContractViolation) as caught:
                attach(source, host)
            assert moved
            state = custody(host)
            assert state.construction_error is caught.value
            assert state.attachment.retired
            before = len(source.calls)
            receipt = owner.read_grammar_role_cleanup(state.ticket)
            assert receipt.cause == "construction_failure"
            assert receipt.operation_ref is None
            assert receipt.profile_input_digest is receipt.syntax_input_digest is None
            assert receipt.work_state == "quiescent"
            assert receipt.epoch_state == "finished"
            assert receipt.completion == "unverified"
            object.__setattr__(expected, field, original_value)
            with pytest.raises(ContractViolation, match="retired"):
                owner._correlate_grammar_role_cleanup(state.attachment)
            assert state.construction_error is caught.value
            assert owner.read_grammar_role_cleanup(state.ticket) == receipt
            assert len(source.calls) == before
        finally:
            object.__setattr__(expected, field, original_value)
            source.lock = original_lock
            source.after_read = None


@pytest.mark.parametrize("fail_at", (1, 2))
def test_scalar_copy_failure_publishes_no_partial_correlation(
    admissions, monkeypatch, fail_at
):
    with case(admissions) as (source, host, _, _):
        error = ValueError("correlation scalar copy")
        copies = 0

        def copy_digest(value):
            nonlocal copies
            copies += 1
            # Even during the second copy, no first field is published.
            receipt = owner.read_grammar_role_cleanup(custody(host).ticket)
            assert receipt.operation_ref is None
            assert receipt.profile_input_digest is receipt.syntax_input_digest is None
            if copies == fail_at:
                raise error
            return ContentDigest(value)

        with monkeypatch.context() as changed:
            changed.setattr(owner, "ContentDigest", copy_digest)
            with pytest.raises(ValueError) as caught:
                attach(source, host)
        assert caught.value is error
        state = custody(host)
        assert state.construction_error is error and state.attachment.retired
        receipt = owner.read_grammar_role_cleanup(state.ticket)
        assert receipt.cause == "construction_failure"
        assert receipt.operation_ref is None
        assert receipt.profile_input_digest is receipt.syntax_input_digest is None
        assert receipt.epoch_state == "finished"
        assert receipt.work_state == "quiescent"
        assert receipt.completion == "unverified"
        before = len(source.calls)
        with pytest.raises(ContractViolation, match="retired"):
            owner._correlate_grammar_role_cleanup(state.attachment)
        assert state.construction_error is error
        assert owner.read_grammar_role_cleanup(state.ticket) == receipt
        assert len(source.calls) == before


@pytest.mark.parametrize("action", (copy.copy, copy.deepcopy, pickle.dumps))
def test_ticket_cannot_be_copied_or_serialized(admissions, action):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        with pytest.raises(TypeError, match="copied or serialized"):
            action(attachment.cleanup_custody.ticket)
        assert (
            owner.read_grammar_role_cleanup(
                attachment.cleanup_custody.ticket
            ).completion
            == "unverified"
        )


def test_no_ticket_constructor_or_subclass():
    with pytest.raises(TypeError, match="module-issued"):
        owner.CodeGrammarRoleCleanup()
    with pytest.raises(TypeError, match="sealed"):
        type("Foreign", (owner.CodeGrammarRoleCleanup,), {})
    with pytest.raises(ContractViolation, match="unissued"):
        owner.read_grammar_role_cleanup(object.__new__(owner.CodeGrammarRoleCleanup))


def test_forged_ticket_cannot_adopt_original_custody(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        ticket = object.__new__(owner.CodeGrammarRoleCleanup)
        object.__setattr__(ticket, "_custody", attachment.cleanup_custody)
        with pytest.raises(ContractViolation, match="original grammar cleanup custody"):
            owner.read_grammar_role_cleanup(ticket)
        assert (
            owner.read_grammar_role_cleanup(
                attachment.cleanup_custody.ticket
            ).completion
            == "unverified"
        )


def test_copied_attachment_cannot_reissue_original_ticket(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        with pytest.raises(ContractViolation, match="custody unavailable"):
            owner._issue_grammar_role_cleanup(copy.copy(attachment))
        assert (
            owner._issue_grammar_role_cleanup(attachment)
            is attachment.cleanup_custody.ticket
        )


def test_detached_receipt_is_not_a_cleanup_ticket(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        original = owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)
        detached = decode_grammar_role_cleanup(encode_grammar_role_cleanup(original))
        with pytest.raises(TypeError):
            owner.read_grammar_role_cleanup(detached)


def test_copied_custody_cannot_replace_original_association(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        original = attachment.cleanup_custody
        object.__setattr__(ticket, "_custody", copy.copy(original))
        try:
            with pytest.raises(ContractViolation, match="attachment or journal"):
                owner.read_grammar_role_cleanup(ticket)
        finally:
            object.__setattr__(ticket, "_custody", original)


def test_copied_journal_cannot_replace_original_owner_object(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        original = attachment.epoch_work
        attachment.epoch_work = dict(original)
        try:
            with pytest.raises(ContractViolation, match="attachment or journal"):
                owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)
        finally:
            attachment.epoch_work = original


def test_ticket_field_substitution_refuses_before_descriptor_call(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)

        def forbidden(self):
            raise AssertionError("substituted descriptor invoked")

        with monkeypatch.context() as changed:
            changed.setattr(
                owner.CodeGrammarRoleCleanup, "_custody", property(forbidden)
            )
            with pytest.raises(ContractViolation, match="field substituted"):
                owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)


@pytest.mark.parametrize("field", ("operation_ref", "input_digest"))
def test_correlation_snapshot_does_not_restamp_mutated_original_inputs(
    admissions, field
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        original = owner.read_grammar_role_cleanup(ticket)
        expected = source.inputs[0]
        value = getattr(expected, field)
        object.__setattr__(expected, field, object())
        try:
            assert owner.read_grammar_role_cleanup(ticket) == original
        finally:
            object.__setattr__(expected, field, value)


@pytest.mark.parametrize("mode", ("source", "host"))
def test_retired_original_owner_does_not_block_or_refresh_cleanup_read(
    admissions, mode
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        if mode == "source":
            source.failure = AssertionError("cleanup read called borrowed owner")
        else:
            direct.close_direct_validation_host(host)
        before = len(source.calls)
        receipt = owner.read_grammar_role_cleanup(ticket)
        assert receipt.epoch_state == "finished" and receipt.completion == "unverified"
        assert len(source.calls) == before


def test_other_thread_refuses_before_owner_calls(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        before = len(source.calls)
        errors = []

        def read():
            try:
                owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)
            except BaseException as error:
                errors.append(error)

        thread = Thread(target=read)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], ContractViolation)
        assert len(source.calls) == before


def test_other_process_refuses_before_owner_calls(admissions, monkeypatch):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        process = os.getpid()
        before = len(source.calls)
        with monkeypatch.context() as changed:
            changed.setattr(os, "getpid", lambda: process + 1)
            with pytest.raises(ContractViolation, match="process"):
                owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)
        assert len(source.calls) == before


@pytest.mark.parametrize("bad", (None, object(), {}))
def test_invalid_journal_entry_is_not_hidden_as_absence(admissions, bad):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        attachment.epoch_work[source.inputs[0].use_ref] = bad
        with pytest.raises(ContractViolation, match="original grammar epoch work"):
            owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)


@pytest.mark.asyncio
async def test_read_tracks_awaited_work_without_admission_or_disposal(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        async with epochs._grammar_source_epoch_use(
            host, attachment, expected=source.inputs[0]
        ):
            before = len(source.calls)
            receipt = owner.read_grammar_role_cleanup(ticket)
            assert (
                receipt.work_state == "unverified" and receipt.epoch_state == "running"
            )
            assert receipt.resources[0].status == "blocked_active"
            assert receipt.completion == "unverified"
            assert len(ep._state(participant).uses) == 1
            assert len(source.calls) == before
            await asyncio.sleep(0)
        receipt = owner.read_grammar_role_cleanup(ticket)
        assert receipt.work_state == "quiescent" and receipt.epoch_state == "finished"
        assert receipt.completion == "unverified"


@pytest.mark.asyncio
async def test_parent_revocation_cannot_upgrade_running_or_uncertain_evidence(
    admissions,
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        with pytest.raises(ContractViolation):
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                direct.close_direct_validation_host(host)
                assert (
                    ep._STATES[participant].closed and not ep._STATES[participant].uses
                )
                receipt = owner.read_grammar_role_cleanup(ticket)
                assert (
                    receipt.work_state == "unverified"
                    and receipt.epoch_state == "running"
                )
                assert receipt.completion == "unverified"
        receipt = owner.read_grammar_role_cleanup(ticket)
        assert receipt.work_state == "quiescent" and receipt.epoch_state == "uncertain"
        assert receipt.resources[0].status == "pending"
        assert any(row.status == "unknown" for row in receipt.resources)
        assert receipt.completion == "unverified"


@pytest.mark.asyncio
async def test_primary_failure_and_release_evidence_are_not_cleaned_by_read(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        error = ValueError("body")
        with pytest.raises(ValueError) as caught:
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                raise error
        record = attachment.epoch_work[source.inputs[0].use_ref]
        before = record.primary_error, record.settlement_error, record.exclusion_state
        receipt = owner.read_grammar_role_cleanup(attachment.cleanup_custody.ticket)
        assert caught.value is error
        assert before == (
            record.primary_error,
            record.settlement_error,
            record.exclusion_state,
        )
        assert (
            receipt.cause == "execution_failure" and receipt.epoch_state == "finished"
        )
        assert receipt.completion == "unverified" and attachment.retired
