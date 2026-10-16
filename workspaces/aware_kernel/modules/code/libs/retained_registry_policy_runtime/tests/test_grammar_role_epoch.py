"""Original Code epoch mechanics with the disclosed fixture source/parent.

These are lexical lifetime proofs, not genuine Workspace or productive role
admission. Detached provider work is deliberately outside this internal port.
"""

import asyncio
import copy
import os
from contextlib import contextmanager
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    direct_epoch_tracking as tracking,
)
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_retained_registry_policy_runtime import grammar_role_epoch as owner
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPublicationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import attach, case


def envelope(host, attachment, *, stage=0):
    return owner._grammar_source_epoch_use(
        host, attachment, expected=attachment.expectations[stage]
    )


def work(attachment, *, stage=0):
    return attachment.epoch_work[attachment.expectations[stage].use_ref]


def publication(source, participant):
    guard = source.acquire_catalog_epoch_exclusion(
        source.parent, expected=source.epoch.invocation
    )
    try:
        participant.validate_catalog_publication_exclusion(
            guard,
            expected=CatalogPublicationExpectation(
                object(),
                source.epoch,
                replace(source.epoch, publication_identity=object()),
                ContentDigest.of_bytes(b"explicit publication mechanics fixture"),
            ),
        )
    finally:
        source.release_catalog_epoch_exclusion(guard)


@pytest.mark.parametrize("discharged", (False, True))
@pytest.mark.parametrize("body_fails", (False, True))
@pytest.mark.asyncio
async def test_confirmed_release_survives_failed_finish(
    admissions, monkeypatch, discharged, body_fails
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        finish_error = ValueError("original finish failed")
        body_error = ValueError("original body failed")
        original_transition = ep._TRANSITION
        original_guard = tracking._guard
        target = {"use": None}
        confirmations = []

        def transition(instance, guard, use, before, after):
            if instance is participant and use is target["use"] and after is None:
                if discharged:
                    original_transition(instance, guard, use, before, after)
                raise finish_error
            return original_transition(instance, guard, use, before, after)

        @contextmanager
        def observe_guard(binding, **kwargs):
            try:
                with original_guard(binding, **kwargs) as guard:
                    yield guard
            finally:
                if kwargs.get("release_state") is not None:
                    confirmations.append(kwargs["release_state"])

        with monkeypatch.context() as injection:
            injection.setattr(ep, "_TRANSITION", transition)
            injection.setattr(tracking, "_guard", observe_guard)
            with pytest.raises(ValueError) as caught:
                async with envelope(host, attachment):
                    target["use"] = work(attachment).use
                    if body_fails:
                        raise body_error

        record = work(attachment)
        assert confirmations[-1].confirmed is True
        assert record.exclusion_state == "released" and not source.guards
        assert record.work_state == "quiescent"
        assert record.epoch_state == "uncertain" and attachment.retired
        assert record.settlement_error is finish_error
        assert caught.value is (body_error if body_fails else finish_error)
        if body_fails:
            assert record.primary_error is body_error
            assert caught.value.__cause__ is finish_error
        assert bool(ep._state(participant).uses) is not discharged
        with pytest.raises(ContractViolation, match="terminal"):
            owner._settle(record)
        assert record.epoch_state == "uncertain"
        assert record.exclusion_state == "released"
        # Release is independent evidence, not a resource-cleanup receipt.
        assert record.attachment is attachment and record.task is asyncio.current_task()


@pytest.mark.parametrize("stage", (0, 1))
@pytest.mark.asyncio
async def test_original_obligation_spans_await_without_parent_exclusion(
    admissions, stage
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        entered = asyncio.Event()
        leave = asyncio.Event()

        async def role():
            async with envelope(host, attachment, stage=stage):
                entered.set()
                await leave.wait()
                assert not source.guards

        task = asyncio.create_task(role())
        await entered.wait()
        record = work(attachment, stage=stage)
        assert record.task is task
        assert record.work_state == record.epoch_state == "running"
        assert record.exclusion_state == "released"
        assert not source.guards
        with pytest.raises(ContractViolation, match="active or unresolved"):
            publication(source, participant)
        leave.set()
        await task
        assert record.work_state == "quiescent"
        assert record.epoch_state == "finished"
        assert not ep._state(participant).uses
        publication(source, participant)


@pytest.mark.asyncio
async def test_both_lexical_stages_settle_separately_and_replay_refuses(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        for stage in (0, 1):
            async with envelope(host, attachment, stage=stage):
                await asyncio.sleep(0)
            with pytest.raises(ContractViolation, match="consumed"):
                async with envelope(host, attachment, stage=stage):
                    pytest.fail("replayed lexical work")
        assert len(attachment.epoch_work) == 2
        assert all(
            row.epoch_state == "finished" for row in attachment.epoch_work.values()
        )
        assert not ep._state(participant).uses


@pytest.mark.parametrize("stage", (0, 1))
@pytest.mark.asyncio
async def test_concurrent_entry_refuses_without_spending_second_stage(
    admissions, stage
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        async with envelope(host, attachment):
            expected_message = "consumed" if stage == 0 else "active or unresolved"
            with pytest.raises(ContractViolation, match=expected_message):
                async with envelope(host, attachment, stage=stage):
                    pytest.fail("concurrent work admitted")
            assert len(attachment.epoch_work) == 1
            assert len(ep._state(participant).uses) == 1
        assert not attachment.retired


@pytest.mark.parametrize("field", ("host", "attachment", "expected"))
@pytest.mark.parametrize("bad", (None, (), {}, object()))
@pytest.mark.asyncio
async def test_exact_shapes_refuse_before_callbacks(admissions, field, bad):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        before = len(source.calls)
        args = dict(host=host, attachment=attachment, expected=source.inputs[0])
        args[field] = bad
        with pytest.raises(TypeError):
            async with owner._grammar_source_epoch_use(**args):
                pytest.fail("foreign shape admitted")
        assert not attachment.epoch_work
        assert len(source.calls) == before


@pytest.mark.parametrize("field", ("attachment", "expected"))
@pytest.mark.asyncio
async def test_copied_values_do_not_acquire_original_use(admissions, field):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        args = dict(host=host, attachment=attachment, expected=source.inputs[0])
        args[field] = copy.copy(args[field])
        with pytest.raises(ContractViolation):
            async with owner._grammar_source_epoch_use(**args):
                pytest.fail("copy admitted")
        assert not attachment.epoch_work
        assert not attachment.retired


@pytest.mark.parametrize(
    "kind", (ValueError, KeyboardInterrupt, SystemExit, asyncio.CancelledError)
)
@pytest.mark.asyncio
async def test_primary_failures_preserve_identity_and_actual_quiescence(
    admissions, kind
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        error = kind()
        with pytest.raises(kind) as caught:
            async with envelope(host, attachment):
                await asyncio.sleep(0)
                raise error
        assert caught.value is error
        record = work(attachment)
        assert record.primary_error is error and record.settlement_error is None
        assert record.work_state == "quiescent" and record.epoch_state == "finished"
        assert attachment.retired
        assert not ep._state(participant).uses


@pytest.mark.asyncio
async def test_cancellation_waits_for_enclosed_async_finally(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        entered = asyncio.Event()
        unwinding = asyncio.Event()
        finished = asyncio.Event()

        async def role():
            async with envelope(host, attachment):
                try:
                    entered.set()
                    await asyncio.Future()
                finally:
                    unwinding.set()
                    await finished.wait()

        task = asyncio.create_task(role())
        await entered.wait()
        task.cancel()
        await unwinding.wait()
        record = work(attachment)
        assert record.work_state == record.epoch_state == "running"
        assert len(ep._state(participant).uses) == 1
        assert not source.guards
        finished.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert record.work_state == "quiescent" and record.epoch_state == "finished"
        assert not ep._state(participant).uses


@pytest.mark.parametrize(
    "kind", (ValueError, asyncio.CancelledError, KeyboardInterrupt)
)
@pytest.mark.asyncio
async def test_failed_settlement_retains_primary_and_terminal_uncertainty(
    admissions, kind
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        original_epoch = source.current
        primary = kind()
        with pytest.raises(kind) as caught:
            async with envelope(host, attachment):
                source.current = object()
                raise primary
        record = work(attachment)
        assert caught.value is primary
        assert caught.value.__cause__ is record.settlement_error
        assert record.work_state == "quiescent" and record.epoch_state == "uncertain"
        assert len(ep._state(participant).uses) == 1
        source.current = original_epoch
        with pytest.raises(ContractViolation, match="terminal"):
            owner._settle(record)
        with pytest.raises(ContractViolation, match="retired"):
            async with envelope(host, attachment):
                pytest.fail("restored uncertain work")
        assert record.epoch_state == "uncertain"
        assert len(ep._state(participant).uses) == 1


@pytest.mark.asyncio
async def test_stale_source_after_body_preserves_failure_and_settles_ended_work(
    admissions,
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        primary = ValueError("original source failure")
        with pytest.raises(ValueError) as caught:
            async with envelope(host, attachment):
                source.failure = primary
        assert caught.value is primary
        record = work(attachment)
        assert record.work_state == "quiescent" and record.epoch_state == "finished"
        assert attachment.retired and not ep._state(participant).uses
        source.failure = None
        with pytest.raises(ContractViolation, match="retired"):
            async with envelope(host, attachment):
                pytest.fail("restoration revived attachment")


@pytest.mark.asyncio
async def test_cross_task_exit_never_claims_quiescence(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        context = envelope(host, attachment)
        await context.__aenter__()
        with pytest.raises(ContractViolation, match="another task"):
            await asyncio.create_task(context.__aexit__(None, None, None))
        record = work(attachment)
        assert record.work_state == "unverified" and record.epoch_state == "uncertain"
        assert attachment.retired and len(ep._state(participant).uses) == 1


@pytest.mark.asyncio
async def test_parent_revocation_is_not_quiescence_or_settlement(admissions):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        with pytest.raises(ContractViolation):
            async with envelope(host, attachment):
                record = work(attachment)
                direct.close_direct_validation_host(host)
                assert record.work_state == record.epoch_state == "running"
                assert record.use is not None
                await asyncio.sleep(0)
        assert record.work_state == "quiescent" and record.epoch_state == "uncertain"
        assert record.use is not None and record.settlement_error is not None
        assert ep._STATES[participant].closed
        assert attachment.epoch_work[source.inputs[0].use_ref] is record


@pytest.mark.asyncio
async def test_process_change_refuses_before_callbacks(admissions, monkeypatch):
    with case(admissions) as (source, host, _, _):
        attachment = attach(source, host)
        before = len(source.calls)
        process = os.getpid()
        with monkeypatch.context() as changed:
            changed.setattr(os, "getpid", lambda: process + 1)
            with pytest.raises(ContractViolation, match="process"):
                async with envelope(host, attachment):
                    pytest.fail("foreign process admitted")
        assert not attachment.epoch_work and len(source.calls) == before


@pytest.mark.parametrize("abandon_fails", (False, True))
@pytest.mark.asyncio
async def test_start_failure_accounts_original_pending_use(
    admissions, monkeypatch, abandon_fails
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        primary = ValueError("original start failure")
        cleanup = ValueError("original abandon failure")
        original = ep._TRANSITION
        target = {"use": None}
        armed = {"value": False}
        reserve = owner._reserve

        def reserve_and_arm(*a, **kw):
            result = reserve(*a, **kw)
            armed["value"] = True
            return result

        def transition(instance, guard, use, before, after):
            if armed["value"] and instance is participant and after == "running":
                target["use"] = use
                raise primary
            if use is target["use"] and after is None and abandon_fails:
                raise cleanup
            return original(instance, guard, use, before, after)

        with monkeypatch.context() as injection:
            injection.setattr(ep, "_TRANSITION", transition)
            injection.setattr(owner, "_reserve", reserve_and_arm)
            with pytest.raises(ValueError) as caught:
                async with envelope(host, attachment):
                    pytest.fail("failed start yielded work")
        record = work(attachment)
        assert caught.value is primary and record.primary_error is primary
        assert record.work_state == "not_started"
        assert record.exclusion_state == "released"
        assert attachment.retired
        if abandon_fails:
            assert caught.value.__cause__ is cleanup
            assert record.epoch_state == "uncertain"
            assert ep._state(participant).uses[record.use].status == "pending"
        else:
            assert record.epoch_state == "finished"
            assert not ep._state(participant).uses


@pytest.mark.parametrize("phase", ("entry", "settlement"))
@pytest.mark.asyncio
async def test_failed_exclusion_release_cannot_complete_epoch(
    admissions, monkeypatch, phase
):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        cleanup = ValueError("release failed after original release")
        original = type(source).release_catalog_epoch_exclusion
        armed = {"value": False}

        # Captured class entrance must remain original. Inject the error in
        # the existing owner lock release rather than replacing a bound method.
        original_lock = source.lock

        class ReleaseFailure:
            def acquire(self):
                return original_lock.acquire()

            def release(self):
                original_lock.release()
                if armed["value"]:
                    raise cleanup

        assert original is type(source).release_catalog_epoch_exclusion
        source.lock = ReleaseFailure()
        try:
            context = envelope(host, attachment)
            if phase == "entry":
                # Reserve/preflight makes its own synchronous epoch calls;
                # arm only after reservation, before the actual new use.
                reserve = owner._reserve

                def reserve_and_arm(*a, **kw):
                    result = reserve(*a, **kw)
                    armed["value"] = True
                    return result

                with monkeypatch.context() as injection:
                    injection.setattr(owner, "_reserve", reserve_and_arm)
                    with pytest.raises(ValueError) as caught:
                        await context.__aenter__()
            else:
                await context.__aenter__()
                armed["value"] = True
                with pytest.raises(ValueError) as caught:
                    await context.__aexit__(None, None, None)
            assert caught.value is cleanup
            record = work(attachment)
            assert record.epoch_state == "uncertain" and attachment.retired
            assert record.exclusion_state == "uncertain"
            assert not source.guards
            if phase == "entry":
                assert record.work_state == "not_started"
                assert len(ep._state(participant).uses) == 1
            else:
                assert record.work_state == "quiescent"
        finally:
            armed["value"] = False
            source.lock = original_lock


@pytest.mark.asyncio
async def test_body_error_survives_finish_and_release_failures(admissions, monkeypatch):
    with case(admissions) as (source, host, participant, _):
        attachment = attach(source, host)
        primary = ValueError("body")
        finish = ValueError("finish")
        release = ValueError("release")
        original_transition = ep._TRANSITION
        original_lock = source.lock
        armed = {"value": False}

        def transition(instance, guard, use, before, after):
            if armed["value"] and instance is participant and after is None:
                raise finish
            return original_transition(instance, guard, use, before, after)

        class ReleaseFailure:
            def acquire(self):
                return original_lock.acquire()

            def release(self):
                original_lock.release()
                if armed["value"]:
                    raise release

        source.lock = ReleaseFailure()
        try:
            with monkeypatch.context() as injection:
                injection.setattr(ep, "_TRANSITION", transition)
                with pytest.raises(ValueError) as caught:
                    async with envelope(host, attachment):
                        armed["value"] = True
                        raise primary
            record = work(attachment)
            assert caught.value is primary and primary.__cause__ is finish
            assert finish.__cause__ is release
            assert record.settlement_error is finish
            assert (
                record.work_state == "quiescent" and record.epoch_state == "uncertain"
            )
            assert len(ep._state(participant).uses) == 1
        finally:
            armed["value"] = False
            source.lock = original_lock
