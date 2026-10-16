"""Original Code profile execution with explicit fixture source/catalog owners.

This is not genuine Workspace/Language dependency admission or installation.
The extra demo catalog row is fixture data, never a production bootstrap.
"""

import asyncio
import copy
import pickle
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as ep
from aware_code_retained_registry_policy_runtime import grammar_profile_role as owner
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarProfileSelectionCodec,
)
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import case
from test_materialization_catalog import _binding


def compose(source, host, *, key="default"):
    return owner._compose_grammar_profile_source_role(
        code_host=host,
        profile_expected=source.inputs[0],
        syntax_expected=source.inputs[1],
        profile_key=key,
    )


@pytest.mark.asyncio
async def test_original_registered_profile_execution_retains_and_releases_result(
    admissions,
):
    binding = _binding(provider_key="demo")
    with case(admissions, extra_catalog_entries=(binding,)) as (
        source,
        host,
        participant,
        _,
    ):
        role = compose(source, host)
        state = owner._state(role, live=True)
        resources = state.resources
        result = await owner.execute_grammar_profile_source_role(role)
        assert (
            CodeGrammarProfileSelectionCodec().decode(result.canonical_body)
            == binding.profile_declaration
        )
        assert resources.result is result and resources.result_status == "pending"
        assert len(resources.host._results) == 1
        assert not ep._state(participant).uses
        before = len(source.calls)
        owner.release_grammar_profile_source_result(role, result=result)
        assert resources.result_status == "released" and not resources.host._results
        assert len(source.calls) == before
        receipt = owner.close_grammar_profile_source_role(role)
        assert receipt.completion == "verified"
        assert all(
            row.status in ("released", "not_acquired") for row in receipt.resources
        )
        assert owner.close_grammar_profile_source_role(role) is receipt
        assert cleanup.read_grammar_role_cleanup(resources.custody.ticket) is receipt
        assert not ep._STATES[participant].closed and not direct._HOSTS[host].closed
        assert resources.host._closed


@pytest.mark.asyncio
async def test_disposal_closes_owned_result_registration_host_in_order(
    admissions, monkeypatch
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        await owner.execute_grammar_profile_source_role(role)
        original_result = cleanup.release_registered_semantic_input_result
        original_registration = cleanup.close_semantic_input_producer_registration
        original_host = inputs.SemanticInputProducerHost.close
        calls = []

        def release(*args, **kwargs):
            calls.append("result")
            return original_result(*args, **kwargs)

        def registration(*args, **kwargs):
            calls.append("registration")
            return original_registration(*args, **kwargs)

        def close(value):
            calls.append("host")
            return original_host(value)

        with monkeypatch.context() as changed:
            changed.setattr(
                cleanup, "release_registered_semantic_input_result", release
            )
            changed.setattr(
                cleanup, "close_semantic_input_producer_registration", registration
            )
            changed.setattr(inputs.SemanticInputProducerHost, "close", close)
            receipt = owner.close_grammar_profile_source_role(role)
            assert owner.close_grammar_profile_source_role(role) is receipt
        assert calls == ["result", "registration", "host"]
        assert (
            resources.result_status
            == resources.registration_status
            == resources.host_status
            == "released"
        )


@pytest.mark.parametrize("bad", (None, object(), {}, ()))
@pytest.mark.asyncio
async def test_foreign_role_shapes_refuse_without_callbacks(admissions, bad):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        before = len(source.calls)
        with pytest.raises(TypeError):
            await owner.execute_grammar_profile_source_role(bad)
        assert len(source.calls) == before
        owner.close_grammar_profile_source_role(role)


@pytest.mark.parametrize("action", (copy.copy, copy.deepcopy, pickle.dumps))
def test_role_is_not_copyable_or_constructible(admissions, action):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        with pytest.raises(TypeError):
            action(role)
        with pytest.raises(TypeError):
            owner.CodeGrammarProfileSourceRole()
        owner.close_grammar_profile_source_role(role)


@pytest.mark.parametrize("key", (None, "", "alias default", "x" * 513))
def test_invalid_selector_refuses_before_attachment_admission(admissions, key):
    with case(admissions) as (source, host, _, _):
        before = len(source.calls)
        with pytest.raises((TypeError, ValueError)):
            compose(source, host, key=key)
        assert direct._HOSTS[host].grammar_attachment is None
        assert len(source.calls) == before


@pytest.mark.asyncio
async def test_missing_profile_is_not_selected_from_helper_catalog(admissions):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        with pytest.raises(ContractViolation, match="profile.*absent"):
            await owner.execute_grammar_profile_source_role(role)
        state = owner._state(role, live=False)
        assert state.attachment.retired and state.resources.result is None
        receipt = owner.close_grammar_profile_source_role(role)
        assert receipt.completion == "unverified"


@pytest.mark.asyncio
async def test_copied_result_refuses_and_original_remains_releasable(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        result = await owner.execute_grammar_profile_source_role(role)
        with pytest.raises(ContractViolation, match="retained"):
            owner.release_grammar_profile_source_result(role, result=replace(result))
        owner.release_grammar_profile_source_result(role, result=result)
        assert owner.close_grammar_profile_source_role(role).completion == "verified"


@pytest.mark.asyncio
async def test_original_once_only_execution_cannot_replay(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        await owner.execute_grammar_profile_source_role(role)
        before = len(source.calls)
        with pytest.raises(ContractViolation, match="consumed"):
            await owner.execute_grammar_profile_source_role(role)
        assert len(source.calls) == before
        assert owner.close_grammar_profile_source_role(role).completion == "verified"


@pytest.mark.parametrize(
    "error", (ValueError("source"), asyncio.CancelledError(), KeyboardInterrupt())
)
@pytest.mark.asyncio
async def test_source_failure_preserves_original_and_never_retries(admissions, error):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        source.failure = error
        with pytest.raises(type(error)) as caught:
            await owner.execute_grammar_profile_source_role(role)
        assert caught.value is error
        source.failure = None
        before = len(source.calls)
        with pytest.raises(ContractViolation, match="retired"):
            await owner.execute_grammar_profile_source_role(role)
        assert len(source.calls) == before
        assert owner.close_grammar_profile_source_role(role).completion == "unverified"


def test_construction_return_failure_keeps_owned_host_and_unknown_registration(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, _, _):
        returned = object()
        with monkeypatch.context() as changed:
            changed.setattr(
                inputs,
                "register_semantic_input_producer",
                lambda *args, **kwargs: returned,
            )
            with pytest.raises(ContractViolation, match="invalid registration"):
                compose(source, host)
        attachment = direct._HOSTS[host].grammar_attachment
        resources = attachment.profile_resources
        assert resources.raw_return_present and resources.raw_return is returned
        receipt = cleanup.dispose_grammar_role_cleanup(
            attachment.cleanup_custody.ticket
        )
        assert resources.host._closed and resources.host_status == "released"
        assert resources.registration_status == "unknown"
        assert (
            receipt.cause == "construction_failure"
            and receipt.completion == "unverified"
        )


@pytest.mark.asyncio
async def test_unknown_child_cleanup_does_not_erase_confirmed_host_and_attachment(
    admissions, monkeypatch
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        await owner.execute_grammar_profile_source_role(role)
        error = ValueError("result release")

        def fail(*args, **kwargs):
            raise error

        with monkeypatch.context() as changed:
            changed.setattr(cleanup, "release_registered_semantic_input_result", fail)
            with pytest.raises(ValueError) as caught:
                owner.close_grammar_profile_source_role(role)
        assert caught.value is error and resources.cleanup_errors == (error,)
        assert resources.result_status == "unknown"
        assert resources.host_status == resources.registration_status == "released"
        receipt = cleanup.read_grammar_role_cleanup(resources.custody.ticket)
        assert (
            receipt.resources[0].status == "released"
            and receipt.completion == "unverified"
        )
        assert owner.close_grammar_profile_source_role(role) is receipt


@pytest.mark.parametrize("field", ("profile_key", "producer", "declaration"))
@pytest.mark.asyncio
async def test_owner_record_substitution_retires_without_restoration(admissions, field):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        state = owner._state(role, live=True)
        original = getattr(state, field)
        setattr(
            state, field, "other" if field == "profile_key" else copy.copy(original)
        )
        try:
            with pytest.raises(ContractViolation):
                await owner.execute_grammar_profile_source_role(role)
            assert state.attachment.retired
        finally:
            setattr(state, field, original)
        with pytest.raises(ContractViolation, match="retired"):
            await owner.execute_grammar_profile_source_role(role)
        owner.close_grammar_profile_source_role(role)


def test_forged_role_cannot_adopt_original_record(admissions):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        state = owner._state(role, live=True)
        forged = object.__new__(owner.CodeGrammarProfileSourceRole)
        object.__setattr__(forged, "_state", state)
        with pytest.raises(ContractViolation, match="original profile role record"):
            owner.close_grammar_profile_source_role(forged)
        assert not state.attachment.retired
        owner.close_grammar_profile_source_role(role)


def test_owned_construction_blocks_disposal_during_original_validation(admissions):
    with case(admissions) as (source, host, _, _):
        seen = []

        def during():
            attachment = direct._HOSTS[host].grammar_attachment
            resources = attachment.profile_resources
            if resources is not None:
                assert resources.constructing
                with pytest.raises(ContractViolation, match="not quiescent"):
                    cleanup.dispose_grammar_role_cleanup(resources.custody.ticket)
                assert resources.custody.disposal_state == "pending"
                seen.append(resources)

        source.after_read = during
        role = compose(source, host)
        assert len(seen) == 2
        assert not seen[0].constructing
        owner.close_grammar_profile_source_role(role)


@pytest.mark.parametrize("entrance", ("namespace", "allocation", "initializer", "code"))
def test_substituted_host_construction_refuses_before_acquisition(
    admissions, monkeypatch, entrance
):
    with case(admissions) as (first_source, first_host, _, _):
        first_role = compose(first_source, first_host)
        first_resources = owner._state(first_role, live=True).resources
        foreign = first_resources.host
        foreign_registration = inputs._registration_state(
            foreign, first_resources.registration
        )
        original_registry = foreign._registrations
        called = []

        def substitute(*args, **kwargs):
            called.append(True)
            return foreign

        with case(admissions) as (source, host, _, _):
            with monkeypatch.context() as changed:
                if entrance == "namespace":
                    changed.setattr(inputs, "SemanticInputProducerHost", substitute)
                elif entrance == "allocation":
                    changed.setattr(
                        owner._HOST_TYPE, "__new__", staticmethod(substitute)
                    )
                elif entrance == "initializer":
                    changed.setattr(owner._HOST_TYPE, "__init__", substitute)
                else:

                    def altered_initializer(self):
                        return None

                    changed.setattr(
                        owner._HOST_TYPE.__init__,
                        "__code__",
                        altered_initializer.__code__,
                    )
                with pytest.raises(ContractViolation, match="construction entrance"):
                    compose(source, host)
            attachment = direct._HOSTS[host].grammar_attachment
            resources = attachment.profile_resources
            assert not called and not resources.raw_return_present
            assert resources.host is None and resources.host_status == "not_acquired"
            assert resources.registration is None
            receipt = cleanup.dispose_grammar_role_cleanup(resources.custody.ticket)
            assert receipt.cause == "construction_failure"
            assert not foreign._closed and not foreign_registration.closed
            assert foreign._registrations is original_registry
            assert (
                inputs._registration_state(foreign, first_resources.registration)
                is foreign_registration
            )
        assert (
            owner.close_grammar_profile_source_role(first_role).completion == "verified"
        )


@pytest.mark.parametrize("child", ("result", "registration", "host"))
@pytest.mark.asyncio
async def test_invalid_disposal_returns_remain_unknown_and_never_replay(
    admissions, monkeypatch, child
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        await owner.execute_grammar_profile_source_role(role)
        returned = object()
        called = []

        def invalid(*args, **kwargs):
            called.append(True)
            return returned

        with monkeypatch.context() as changed:
            if child == "host":
                changed.setattr(inputs.SemanticInputProducerHost, "close", invalid)
            else:
                name = (
                    "release_registered_semantic_input_result"
                    if child == "result"
                    else "close_semantic_input_producer_registration"
                )
                changed.setattr(cleanup, name, invalid)
            with pytest.raises(
                ContractViolation, match="disposal returned a value"
            ) as caught:
                owner.close_grammar_profile_source_role(role)
            receipt = cleanup.read_grammar_role_cleanup(resources.custody.ticket)
            assert owner.close_grammar_profile_source_role(role) is receipt
        assert called == [True] and resources.cleanup_errors == (caught.value,)
        assert getattr(resources, child + "_status") == "unknown"
        assert resources.custody.attachment_status == "released"
        assert receipt.completion == "unverified"
        expected_kind = {
            "result": "profile_result",
            "registration": "profile_registration",
            "host": "role_host",
        }[child]
        assert any(
            kind == expected_kind and value is returned
            for kind, value in resources.cleanup_return_evidence
        )
        assert owner.close_grammar_profile_source_role(role) is receipt
        assert getattr(resources, child + "_status") == "unknown" and called == [True]
        assert resources.host._closed is (child != "host")


@pytest.mark.asyncio
async def test_explicit_result_release_validates_none_and_does_not_retry(
    admissions, monkeypatch
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        result = await owner.execute_grammar_profile_source_role(role)
        called = []
        returned = object()

        def invalid(*args, **kwargs):
            called.append(True)
            return returned

        with monkeypatch.context() as changed:
            changed.setattr(inputs, "release_registered_semantic_input_result", invalid)
            with pytest.raises(ContractViolation, match="disposal returned a value"):
                owner.release_grammar_profile_source_result(role, result=result)
            with pytest.raises(ContractViolation, match="retained"):
                owner.release_grammar_profile_source_result(role, result=result)
        assert called == [True] and resources.result_status == "unknown"
        assert resources.cleanup_return_evidence == (("profile_result", returned),)
        receipt = owner.close_grammar_profile_source_role(role)
        assert (
            receipt.completion == "unverified" and resources.result_status == "unknown"
        )
        assert resources.registration_status == resources.host_status == "released"


def test_postconstruction_finish_failure_preserves_owned_resources_and_uncertainty(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, participant, _):
        error = ValueError("profile constructor finish")
        transition = ep._TRANSITION

        def fail(instance, guard, use, before, after):
            attachment = direct._HOSTS[host].grammar_attachment
            if (
                instance is participant
                and attachment is not None
                and attachment.profile_resources is not None
                and after is None
            ):
                raise error
            return transition(instance, guard, use, before, after)

        with monkeypatch.context() as changed:
            changed.setattr(ep, "_TRANSITION", fail)
            with pytest.raises(ValueError) as caught:
                compose(source, host)
        resources = direct._HOSTS[host].grammar_attachment.profile_resources
        assert caught.value is resources.construction_error is error
        assert resources.validation_epoch == "uncertain"
        assert len(ep._state(participant).uses) == 1
        receipt = cleanup.dispose_grammar_role_cleanup(resources.custody.ticket)
        assert resources.host_status == resources.registration_status == "released"
        assert receipt.epoch_state == "uncertain" and receipt.completion == "unverified"
        assert len(ep._state(participant).uses) == 1


@pytest.mark.asyncio
async def test_direct_producer_call_is_not_registered_execution(admissions):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        state = owner._state(role, live=True)
        with pytest.raises(ContractViolation, match="registered profile execution"):
            await state.producer(source.ordinary)
        owner.close_grammar_profile_source_role(role)


@pytest.mark.parametrize("bad", (None, object()))
@pytest.mark.asyncio
async def test_unvalidated_return_presence_is_lossless_and_not_admitted(
    admissions, monkeypatch, bad
):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)

        async def invalid(*args, **kwargs):
            return bad

        with monkeypatch.context() as changed:
            changed.setattr(inputs, "execute_registered_semantic_input", invalid)
            with pytest.raises(ContractViolation):
                await owner.execute_grammar_profile_source_role(role)
        resources = owner._state(role, live=False).resources
        assert resources.raw_return_present and resources.raw_return is bad
        assert resources.result is None and resources.result_status == "unknown"
        assert owner.close_grammar_profile_source_role(role).completion == "unverified"


@pytest.mark.asyncio
async def test_running_source_callback_cannot_dispose_role(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        observed = []

        def during():
            with pytest.raises(ContractViolation, match="not quiescent"):
                owner.close_grammar_profile_source_role(role)
            assert resources.custody.disposal_state == "pending"
            observed.append(True)

        source.after_read = during
        await owner.execute_grammar_profile_source_role(role)
        assert observed
        owner.close_grammar_profile_source_role(role)


@pytest.mark.parametrize("field", ("host", "registration"))
def test_resource_alias_substitution_never_closes_foreign_objects(admissions, field):
    with case(admissions) as (source, host, _, _):
        role = compose(source, host)
        resources = owner._state(role, live=True).resources
        original = getattr(resources, field)
        setattr(resources, field, object())
        try:
            with pytest.raises(ContractViolation, match="custody substituted"):
                owner.close_grammar_profile_source_role(role)
            assert resources.custody.disposal_state == "pending"
            assert not resources.host_origin._closed
        finally:
            setattr(resources, field, original)
        owner.close_grammar_profile_source_role(role)
