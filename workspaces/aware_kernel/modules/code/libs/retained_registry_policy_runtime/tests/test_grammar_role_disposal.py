"""Original attachment disposal mechanics with explicit fixture source owners.

No productive role, borrowed-owner disposal or installed/public constructor is
qualified by these tests. Fault injections target the fixed owner release only.
"""

import asyncio
import copy
import os
from threading import Thread

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as owner
from aware_code_retained_registry_policy_runtime import grammar_role_epoch as epochs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    decode_grammar_role_cleanup,
    encode_grammar_role_cleanup,
)
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import attach, case


def test_disposal_is_once_only_and_does_not_close_borrowed_owners(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        before = len(source.calls)
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.completion == "verified" and receipt.cause == "normal_close"
        assert all(row.status == "released" for row in receipt.resources)
        assert attachment.retired and state.disposal_state == "complete"
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert owner.read_grammar_role_cleanup(state.ticket) is receipt
        assert (
            decode_grammar_role_cleanup(encode_grammar_role_cleanup(receipt)) == receipt
        )
        assert direct._HOSTS[host] is attachment.state
        assert not attachment.state.closed and not ep._STATES[participant].closed
        assert len(source.calls) == before
        with pytest.raises(ContractViolation, match="retired"):
            owner._correlate_grammar_role_cleanup(attachment)


@pytest.mark.parametrize(
    "error", (ValueError("source"), KeyboardInterrupt(), asyncio.CancelledError())
)
def test_failed_construction_can_release_only_owned_attachment(admissions, error):
    with case(admissions) as (source, host, _, _):
        source.failure = error
        with pytest.raises(type(error)) as caught:
            attach(source, host)
        state = direct._HOSTS[host].grammar_attachment.cleanup_custody
        assert caught.value is error
        before = len(source.calls)
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert state.construction_error is error
        assert receipt.cause == "construction_failure"
        assert receipt.epoch_state == "uncertain" and receipt.completion == "unverified"
        assert receipt.resources[0].status == "released"
        assert receipt.operation_ref is None
        source.failure = None
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert owner.read_grammar_role_cleanup(state.ticket) is receipt
        assert len(source.calls) == before


def test_construction_callback_refusal_does_not_spend_ticket(admissions):
    with case(admissions) as (source, host, _, _):
        seen = []

        def during():
            state = direct._HOSTS[host].grammar_attachment.cleanup_custody
            with pytest.raises(ContractViolation, match="not quiescent"):
                owner.dispose_grammar_role_cleanup(state.ticket)
            assert state.disposal_state == "pending" and not state.attachment.retired
            seen.append(state.ticket)

        source.after_read = during
        attachment = attach(source, host)
        assert len(seen) == 2
        assert owner.dispose_grammar_role_cleanup(seen[0]).completion == "verified"
        assert attachment.retired


@pytest.mark.parametrize("bad", (None, object(), {}, ()))
def test_foreign_disposal_ticket_refuses(admissions, bad):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        before = len(source.calls)
        with pytest.raises(TypeError):
            owner.dispose_grammar_role_cleanup(bad)
        assert not attachment.retired and len(source.calls) == before


def test_forged_or_copied_custody_cannot_dispose(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        original = attachment.cleanup_custody
        forged = object.__new__(owner.CodeGrammarRoleCleanup)
        object.__setattr__(forged, "_custody", original)
        with pytest.raises(ContractViolation):
            owner.dispose_grammar_role_cleanup(forged)
        object.__setattr__(original.ticket, "_custody", copy.copy(original))
        try:
            with pytest.raises(ContractViolation):
                owner.dispose_grammar_role_cleanup(original.ticket)
            assert not attachment.retired
        finally:
            object.__setattr__(original.ticket, "_custody", original)


@pytest.mark.parametrize("terminal", (False, True))
def test_other_thread_and_process_refuse_before_disposal(
    admissions, monkeypatch, terminal
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        ticket = attachment.cleanup_custody.ticket
        if terminal:
            owner.dispose_grammar_role_cleanup(ticket)
        errors = []

        def invoke():
            try:
                owner.dispose_grammar_role_cleanup(ticket)
            except BaseException as error:
                errors.append(error)

        worker = Thread(target=invoke)
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive() and len(errors) == 1
        assert isinstance(errors[0], ContractViolation)
        pid = os.getpid()
        with monkeypatch.context() as changed:
            changed.setattr(os, "getpid", lambda: pid + 1)
            with pytest.raises(ContractViolation, match="process"):
                owner.dispose_grammar_role_cleanup(ticket)


def test_reentrant_disposal_refuses_without_replaying_release(admissions, monkeypatch):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        original = owner._release_owned_grammar_attachment
        calls = []

        def release(retained):
            calls.append(retained)
            assert not direct._LOCK._is_owned()
            with pytest.raises(ContractViolation, match="already consumed"):
                owner.dispose_grammar_role_cleanup(state.ticket)
            original(retained)

        with monkeypatch.context() as changed:
            changed.setattr(owner, "_release_owned_grammar_attachment", release)
            receipt = owner.dispose_grammar_role_cleanup(state.ticket)
            assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert calls == [state] and receipt.completion == "verified"


@pytest.mark.parametrize(
    "error", (ValueError("release"), KeyboardInterrupt(), asyncio.CancelledError())
)
def test_release_failure_is_unknown_spent_and_keeps_original_error(
    admissions, monkeypatch, error
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        calls = []

        def fail(retained):
            calls.append(retained)
            retained.attachment.retired = True
            raise error

        with monkeypatch.context() as changed:
            changed.setattr(owner, "_release_owned_grammar_attachment", fail)
            with pytest.raises(type(error)) as caught:
                owner.dispose_grammar_role_cleanup(state.ticket)
            assert caught.value is error and state.disposal_error is error
            receipt = owner.read_grammar_role_cleanup(state.ticket)
            assert receipt.resources[0].status == "unknown"
            assert (
                receipt.epoch_state == "finished" and receipt.completion == "unverified"
            )
            assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert calls == [state]


def test_invalid_release_return_does_not_infer_success_from_retirement(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody

        def invalid(retained):
            retained.attachment.retired = True
            return object()

        with monkeypatch.context() as changed:
            changed.setattr(owner, "_release_owned_grammar_attachment", invalid)
            with pytest.raises(ContractViolation, match="returned a value"):
                owner.dispose_grammar_role_cleanup(state.ticket)
        receipt = owner.read_grammar_role_cleanup(state.ticket)
        assert receipt.resources[0].status == "unknown"
        assert receipt.completion == "unverified"
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt


@pytest.mark.parametrize("release_fails", (False, True))
def test_terminal_snapshot_failure_never_reopens_disposal(
    admissions, monkeypatch, release_fails
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        original_read = owner.read_grammar_role_cleanup
        release_error = ValueError("release primary")
        snapshot_error = ValueError("terminal snapshot")

        def read(ticket):
            if state.disposal_state == "in_progress":
                raise snapshot_error
            return original_read(ticket)

        def fail(retained):
            raise release_error

        with monkeypatch.context() as changed:
            changed.setattr(owner, "read_grammar_role_cleanup", read)
            if release_fails:
                changed.setattr(owner, "_release_owned_grammar_attachment", fail)
            with pytest.raises(ValueError) as caught:
                owner.dispose_grammar_role_cleanup(state.ticket)
        assert caught.value is (release_error if release_fails else snapshot_error)
        assert state.disposal_error is caught.value
        if release_fails:
            assert caught.value.__cause__ is snapshot_error
        assert state.disposal_state == "complete" and state.terminal_receipt is None
        assert state.attachment_status == ("unknown" if release_fails else "released")
        with pytest.raises(ContractViolation, match="already consumed"):
            owner.dispose_grammar_role_cleanup(state.ticket)
        with pytest.raises(ContractViolation, match="receipt unavailable"):
            owner.read_grammar_role_cleanup(state.ticket)


@pytest.mark.asyncio
async def test_running_and_settlement_phases_cannot_dispose(admissions, monkeypatch):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        original_settle = epochs._settle
        observed = []

        def settle(work):
            assert work.work_state == "quiescent" and work.lifetime_active
            with pytest.raises(ContractViolation, match="not quiescent"):
                owner.dispose_grammar_role_cleanup(state.ticket)
            observed.append(work)
            original_settle(work)

        with monkeypatch.context() as changed:
            changed.setattr(epochs, "_settle", settle)
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                with pytest.raises(ContractViolation, match="not quiescent"):
                    owner.dispose_grammar_role_cleanup(state.ticket)
                assert state.disposal_state == "pending"
                await asyncio.sleep(0)
        assert len(observed) == 1 and not observed[0].lifetime_active
        assert owner.dispose_grammar_role_cleanup(state.ticket).completion == "verified"


@pytest.mark.asyncio
async def test_entry_callback_cannot_dispose_before_work_is_yielded(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        original_lock = source.lock
        saw_entry = []

        class EntryRelease:
            def acquire(self, *args, **kwargs):
                return original_lock.acquire(*args, **kwargs)

            def release(self):
                original_lock.release()
                rows = list(attachment.epoch_work.values())
                if (
                    rows
                    and rows[0].lifetime_active
                    and rows[0].work_state == "not_started"
                ):
                    with pytest.raises(ContractViolation, match="not quiescent"):
                        owner.dispose_grammar_role_cleanup(state.ticket)
                    saw_entry.append(rows[0])

        source.lock = EntryRelease()
        try:
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                pass
        finally:
            source.lock = original_lock
        assert saw_entry and all(not work.lifetime_active for work in saw_entry)
        assert owner.dispose_grammar_role_cleanup(state.ticket).completion == "verified"


@pytest.mark.asyncio
async def test_pre_reservation_source_callbacks_cannot_dispose(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        observed = []

        def during():
            work = attachment.epoch_work[source.inputs[0].use_ref]
            if work.validation_epoch == "uncertain":
                assert work.lifetime_active
                with pytest.raises(ContractViolation, match="not quiescent"):
                    owner.dispose_grammar_role_cleanup(state.ticket)
                assert state.disposal_state == "pending"
                observed.append(state.ticket)

        source.after_read = during
        async with epochs._grammar_source_epoch_use(
            host, attachment, expected=source.inputs[0]
        ):
            pass
        work = attachment.epoch_work[source.inputs[0].use_ref]
        assert observed and not work.lifetime_active
        assert owner.dispose_grammar_role_cleanup(state.ticket).completion == "verified"


@pytest.mark.asyncio
async def test_failed_pre_reservation_validation_preserves_unknown_settlement(
    admissions,
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        error = ValueError("pre-reservation source")
        source.failure = error
        with pytest.raises(ValueError) as caught:
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                raise AssertionError("failed entry yielded")
        work = attachment.epoch_work[source.inputs[0].use_ref]
        assert caught.value is error and work.primary_error is error
        assert not work.lifetime_active
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.resources[0].status == "released"
        assert receipt.epoch_state == "uncertain" and receipt.completion == "unverified"
        source.failure = None
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt


@pytest.mark.asyncio
async def test_uncertain_settlement_allows_only_owned_release_after_unwind(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        error = ValueError("settlement")
        original = epochs._settle

        def fail(work):
            original(work)
            work.epoch_state = "uncertain"
            work.settlement_error = error
            attachment.retired = True
            raise error

        with monkeypatch.context() as changed:
            changed.setattr(epochs, "_settle", fail)
            with pytest.raises(ValueError) as caught:
                async with epochs._grammar_source_epoch_use(
                    host, attachment, expected=source.inputs[0]
                ):
                    pass
        work = attachment.epoch_work[source.inputs[0].use_ref]
        assert caught.value is error and not work.lifetime_active
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.resources[0].status == "released"
        assert receipt.work_state == "quiescent" and receipt.epoch_state == "uncertain"
        assert receipt.completion == "unverified" and work.settlement_error is error
        work.epoch_state = "finished"
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert owner.read_grammar_role_cleanup(state.ticket) is receipt


@pytest.mark.asyncio
async def test_parent_revocation_does_not_unlock_active_work(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        with pytest.raises(ContractViolation):
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                direct.close_direct_validation_host(host)
                assert ep._STATES[participant].closed
                with pytest.raises(ContractViolation, match="not quiescent"):
                    owner.dispose_grammar_role_cleanup(state.ticket)
                assert state.disposal_state == "pending"
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.resources[0].status == "released"
        assert receipt.epoch_state == "uncertain" and receipt.completion == "unverified"


@pytest.mark.parametrize("phase", ("entry", "settlement"))
@pytest.mark.asyncio
async def test_original_release_failure_retains_obligation_after_disposal(
    admissions, monkeypatch, phase
):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        original_lock = source.lock
        error = ValueError("original release uncertainty")
        armed = False

        class FailingRelease:
            def acquire(self):
                return original_lock.acquire()

            def release(self):
                original_lock.release()
                if armed:
                    raise error

        source.lock = FailingRelease()
        try:
            context = epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            )
            if phase == "entry":
                original_reserve = epochs._reserve

                def reserve(*args, **kwargs):
                    nonlocal armed
                    result = original_reserve(*args, **kwargs)
                    armed = True
                    return result

                with monkeypatch.context() as changed:
                    changed.setattr(epochs, "_reserve", reserve)
                    with pytest.raises(ValueError) as caught:
                        await context.__aenter__()
            else:
                await context.__aenter__()
                armed = True
                with pytest.raises(ValueError) as caught:
                    await context.__aexit__(None, None, None)
            work = attachment.epoch_work[source.inputs[0].use_ref]
            assert caught.value is error and not work.lifetime_active
            assert work.epoch_state == "uncertain"
            original_evidence = (
                work.primary_error,
                work.settlement_error,
                work.exclusion_state,
            )
            before = len(source.calls)
            receipt = owner.dispose_grammar_role_cleanup(state.ticket)
            assert receipt.resources[0].status == "released"
            assert (
                receipt.epoch_state == "uncertain"
                and receipt.completion == "unverified"
            )
            assert len(source.calls) == before
            assert (
                work.primary_error,
                work.settlement_error,
                work.exclusion_state,
            ) == original_evidence
            armed = False
            source.lock = original_lock
            assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        finally:
            armed = False
            source.lock = original_lock


@pytest.mark.asyncio
async def test_cancelled_task_unwinds_before_disposal_is_available(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        entered = asyncio.Event()
        unwound = []

        async def run():
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=source.inputs[0]
            ):
                try:
                    entered.set()
                    await asyncio.Event().wait()
                finally:
                    await asyncio.sleep(0)
                    with pytest.raises(ContractViolation, match="not quiescent"):
                        owner.dispose_grammar_role_cleanup(state.ticket)
                    unwound.append(True)

        task = asyncio.create_task(run())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled() and unwound == [True]
        work = attachment.epoch_work[source.inputs[0].use_ref]
        assert not work.lifetime_active and work.work_state == "quiescent"
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.cause == "execution_failure" and receipt.completion == "verified"
        assert isinstance(work.primary_error, asyncio.CancelledError)


@pytest.mark.asyncio
async def test_complete_two_stage_inventory_is_retained_without_foreign_close(
    admissions,
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        for expected in source.inputs:
            async with epochs._grammar_source_epoch_use(
                host, attachment, expected=expected
            ):
                pass
        receipt = owner.dispose_grammar_role_cleanup(attachment.cleanup_custody.ticket)
        assert len(receipt.resources) == 8
        assert all(row.status == "released" for row in receipt.resources)
        assert receipt.completion == "verified"
        assert not ep._STATES[participant].closed and not direct._HOSTS[host].closed


@pytest.mark.parametrize(
    "error", (ValueError("exit finish"), KeyboardInterrupt(), asyncio.CancelledError())
)
@pytest.mark.asyncio
async def test_exit_validation_failure_cannot_be_erased_by_async_settlement(
    admissions, monkeypatch, error
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        expected = source.inputs[0]
        original_transition = ep._TRANSITION
        armed = False
        failed_uses = []

        def transition(instance, guard, use, before, after):
            work = attachment.epoch_work.get(expected.use_ref)
            if (
                armed
                and instance is participant
                and after is None
                and work is not None
                and use is not work.use
            ):
                failed_uses.append(use)
                raise error
            return original_transition(instance, guard, use, before, after)

        with monkeypatch.context() as changed:
            changed.setattr(ep, "_TRANSITION", transition)
            with pytest.raises(type(error)) as caught:
                async with epochs._grammar_source_epoch_use(
                    host, attachment, expected=expected
                ):
                    armed = True
        assert caught.value is error and len(failed_uses) == 1
        work = attachment.epoch_work[expected.use_ref]
        assert work.primary_error is error and work.validation_epoch == "finished"
        assert work.exit_validation_epoch == "uncertain"
        assert work.epoch_state == "finished" and work.exclusion_state == "released"
        assert not work.lifetime_active and work.work_state == "quiescent"
        assert len(ep._state(participant).uses) == 1
        assert failed_uses[0] in ep._state(participant).uses
        before = len(source.calls)
        state = attachment.cleanup_custody
        receipt = owner.dispose_grammar_role_cleanup(state.ticket)
        assert receipt.resources[0].status == "released"
        assert receipt.epoch_state == "uncertain" and receipt.completion == "unverified"
        unknown = [row for row in receipt.resources if row.status == "unknown"]
        assert len(unknown) == 1
        assert unknown[0].resource_ref.endswith(".epoch.validation.exit.0")
        assert all(
            row.status == "released" for row in receipt.resources if row not in unknown
        )
        assert work.primary_error is error and len(ep._state(participant).uses) == 1
        assert owner.read_grammar_role_cleanup(state.ticket) is receipt
        assert owner.dispose_grammar_role_cleanup(state.ticket) is receipt
        assert len(source.calls) == before


@pytest.mark.asyncio
async def test_exit_validation_is_unconfirmed_before_original_callbacks(admissions):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        state = attachment.cleanup_custody
        observed = []

        def during():
            work = attachment.epoch_work[source.inputs[0].use_ref]
            assert work.validation_epoch == "finished"
            assert work.exit_validation_epoch == "uncertain" and work.lifetime_active
            receipt = owner.read_grammar_role_cleanup(state.ticket)
            assert (
                receipt.epoch_state == "uncertain"
                and receipt.completion == "unverified"
            )
            assert any(
                row.status == "unknown" and ".validation.exit." in row.resource_ref
                for row in receipt.resources
            )
            with pytest.raises(ContractViolation, match="not quiescent"):
                owner.dispose_grammar_role_cleanup(state.ticket)
            observed.append(work)

        async with epochs._grammar_source_epoch_use(
            host, attachment, expected=source.inputs[0]
        ):
            source.after_read = during
        assert len(observed) == 2
        assert all(work.exit_validation_epoch == "finished" for work in observed)
        assert owner.dispose_grammar_role_cleanup(state.ticket).completion == "verified"
