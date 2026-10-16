"""Original staged registration with fixture source/catalog parents, no syntax success."""

import asyncio
import copy
import pickle
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from test_grammar_profile_role import compose
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import case
from test_materialization_catalog import _binding


def join(role):
    return syntax._compose_grammar_syntax_role_join(profile_role=role)


def test_original_staged_registration_closes_only_owned_children(admissions):
    with case(admissions) as (source, host, participant, _):
        first = compose(source, host)
        role = join(first)
        state = syntax._state(role, live=True)
        parent = state.profile_state.resources
        assert parent.host._role_joins[state.resources.join] is state.join_record
        assert state.join_record.slots[0].registration is parent.registration
        assert state.join_record.slots[0].expected is source.inputs[0]
        assert state.join_record.joined_expected is source.inputs[1]
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "verified"
        assert (
            state.resources.join_status
            == state.resources.registration_status
            == "released"
        )
        assert parent.host._closed and not direct._HOSTS[host].closed
        assert profile.close_grammar_profile_source_role(first) is receipt
        assert syntax.close_grammar_syntax_role_join(role) is receipt


@pytest.mark.asyncio
async def test_original_profile_slot_reaches_authenticated_syntax_refusal(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        role = join(first)
        result = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        assert state.join_record.slots[0].result == result
        assert state.join_record.slots[0].result is not result
        with pytest.raises(
            ContractViolation,
            match="anchor differs from complete registered consumer role",
        ):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        received = state.received_input
        assert received is not None
        assert received.ordinary.stage == "syntax_binding"
        assert received.predecessors[0].coordinate == result.coordinate
        assert received.predecessors[0].canonical_body == result.canonical_body
        assert state.resources.execution_attempted
        assert not state.resources.execution_return_present
        assert state.resources.join_status == "unknown"
        assert state.profile_state.attachment.retired
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "unverified"
        assert state.resources.registration_status == "released"
        assert state.resources.join_status == "unknown"
        assert syntax.close_grammar_syntax_role_join(role) is receipt


@pytest.mark.asyncio
async def test_join_cannot_adopt_a_profile_executed_before_enrollment(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        result = await profile.execute_grammar_profile_source_role(first)
        with pytest.raises(ContractViolation, match="syntax role admission"):
            join(first)
        parent = profile._state(first, live=True).resources
        assert parent.syntax is None and parent.result is result
        assert profile.close_grammar_profile_source_role(first).completion == "verified"


@pytest.mark.asyncio
async def test_copied_predecessor_refuses_without_spending_original_join(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        role = join(first)
        result = await profile.execute_grammar_profile_source_role(first)
        with pytest.raises(ContractViolation, match="original retained"):
            await syntax.execute_grammar_syntax_role_join(
                role, predecessor=replace(result)
            )
        state = syntax._state(role, live=True)
        assert not state.resources.execution_attempted
        assert state.resources.join_status == "pending"
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


@pytest.mark.asyncio
async def test_released_predecessor_cannot_be_admitted(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        role = join(first)
        result = await profile.execute_grammar_profile_source_role(first)
        profile.release_grammar_profile_source_result(first, result=result)
        with pytest.raises(ContractViolation, match="original retained"):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


@pytest.mark.parametrize("bad", (None, object(), {}))
def test_foreign_profile_handles_refuse_without_source_calls(admissions, bad):
    with case(admissions) as (source, host, _, _):
        first = compose(source, host)
        before = len(source.calls)
        with pytest.raises(TypeError):
            join(bad)
        assert len(source.calls) == before
        profile.close_grammar_profile_source_role(first)


@pytest.mark.parametrize("action", (copy.copy, copy.deepcopy, pickle.dumps))
def test_syntax_view_is_sealed_and_nonportable(admissions, action):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        with pytest.raises(TypeError):
            action(role)
        with pytest.raises(TypeError):
            syntax.CodeGrammarSyntaxRoleJoin()
        syntax.close_grammar_syntax_role_join(role)


def test_copied_role_record_is_not_an_original_view(admissions):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        forged = object.__new__(syntax.CodeGrammarSyntaxRoleJoin)
        object.__setattr__(forged, "_state", syntax._state(role, live=True))
        with pytest.raises(ContractViolation, match="original syntax role record"):
            syntax.close_grammar_syntax_role_join(forged)
        syntax.close_grammar_syntax_role_join(role)


def test_construction_disposal_is_refused_before_ticket_is_spent(admissions):
    with case(admissions) as (source, host, _, _):
        first = compose(source, host)
        parent = profile._state(first, live=True).resources
        seen = []

        def during():
            assert parent.syntax.constructing
            with pytest.raises(ContractViolation, match="not quiescent"):
                profile.close_grammar_profile_source_role(first)
            assert parent.custody.disposal_state == "pending"
            seen.append(True)

        source.after_read = during
        role = join(first)
        source.after_read = None
        assert seen
        syntax.close_grammar_syntax_role_join(role)


@pytest.mark.parametrize("port", ("registration", "join"))
def test_same_type_foreign_returns_are_not_owned(admissions, monkeypatch, port):
    with case(admissions) as (first_source, first_host, _, _):
        foreign_role = join(compose(first_source, first_host))
        foreign = syntax._state(foreign_role, live=True)
        with case(admissions) as (source, host, _, _):
            first = compose(source, host)
            target = (
                foreign.resources.registration
                if port == "registration"
                else foreign.resources.join
            )
            name = (
                "register_joined_semantic_input_producer"
                if port == "registration"
                else "open_semantic_input_role_join"
            )
            with monkeypatch.context() as changed:
                changed.setattr(inputs, name, lambda *args, **kwargs: target)
                with pytest.raises(ContractViolation):
                    join(first)
            parent = profile._state(first, live=False).resources
            assert (
                parent.syntax.raw_return_present and parent.syntax.raw_return is target
            )
            receipt = profile.close_grammar_profile_source_role(first)
            assert receipt.completion == "unverified"
            assert not foreign.profile_state.resources.host._closed
            assert syntax._state(foreign_role, live=True) is foreign
        syntax.close_grammar_syntax_role_join(foreign_role)


@pytest.mark.parametrize("port", ("registration", "join"))
def test_invalid_acquisition_return_is_retained_without_ownership(
    admissions, monkeypatch, port
):
    with case(admissions) as (source, host, _, _):
        first = compose(source, host)
        name = (
            "register_joined_semantic_input_producer"
            if port == "registration"
            else "open_semantic_input_role_join"
        )
        with monkeypatch.context() as changed:
            changed.setattr(inputs, name, lambda *args, **kwargs: None)
            with pytest.raises(TypeError):
                join(first)
        parent = profile._state(first, live=False).resources
        assert parent.syntax.raw_return_present and parent.syntax.raw_return is None
        assert getattr(parent.syntax, port + "_status") == "unknown"
        assert (
            profile.close_grammar_profile_source_role(first).completion == "unverified"
        )


@pytest.mark.parametrize("port", ("registration", "join"))
def test_invalid_child_disposal_never_upgrades_or_replays(
    admissions, monkeypatch, port
):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        state = syntax._state(role, live=True)
        target = (
            state.resources.registration
            if port == "registration"
            else state.resources.join
        )
        name = (
            "close_semantic_input_producer_registration"
            if port == "registration"
            else "close_semantic_input_role_join"
        )
        original = getattr(cleanup, name)
        returned = object()
        calls = []

        def invalid(owner_host, child):
            if child is target:
                calls.append(True)
                return returned
            return original(owner_host, child)

        with monkeypatch.context() as changed:
            changed.setattr(cleanup, name, invalid)
            with pytest.raises(ContractViolation, match="disposal returned a value"):
                syntax.close_grammar_syntax_role_join(role)
        receipt = cleanup.read_grammar_role_cleanup(
            state.resources.profile.custody.ticket
        )
        assert receipt.completion == "unverified"
        assert getattr(state.resources, port + "_status") == "unknown"
        assert state.resources.profile.host._closed
        assert syntax.close_grammar_syntax_role_join(role) is receipt and calls == [
            True
        ]


@pytest.mark.parametrize("field", ("join", "registration"))
def test_resource_substitution_cannot_close_foreign_values(admissions, field):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        state = syntax._state(role, live=True)
        original = getattr(state.resources, field)
        setattr(state.resources, field, object())
        try:
            with pytest.raises(ContractViolation, match="syntax resource custody"):
                syntax.close_grammar_syntax_role_join(role)
            assert not state.resources.profile.host._closed
        finally:
            setattr(state.resources, field, original)
        syntax.close_grammar_syntax_role_join(role)


@pytest.mark.asyncio
async def test_syntax_cannot_execute_before_original_profile(admissions):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        with pytest.raises(ContractViolation, match="original retained"):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=object())
        assert not syntax._state(role, live=True).resources.execution_attempted
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


@pytest.mark.parametrize(
    "error",
    (
        ValueError("source"),
        asyncio.CancelledError("cancel"),
        KeyboardInterrupt("interrupt"),
    ),
)
@pytest.mark.asyncio
async def test_original_source_failure_survives_restoration_and_cleanup(
    admissions, error
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        role = join(first)
        result = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        source.failure = error
        with pytest.raises(type(error)) as caught:
            await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        assert caught.value is error and state.profile_state.attachment.retired
        source.failure = None
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "unverified"
        assert syntax.close_grammar_syntax_role_join(role) is receipt


@pytest.mark.parametrize("returned", (None, object()))
@pytest.mark.asyncio
async def test_unqualified_execution_return_presence_is_not_success(
    admissions, monkeypatch, returned
):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        first = compose(source, host)
        role = join(first)
        result = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)

        async def invalid(*args, **kwargs):
            return returned

        with monkeypatch.context() as changed:
            changed.setattr(inputs, "execute_registered_joined_semantic_input", invalid)
            with pytest.raises(ContractViolation, match="unqualified syntax"):
                await syntax.execute_grammar_syntax_role_join(role, predecessor=result)
        assert state.resources.execution_return_present
        assert state.resources.execution_return is returned
        assert state.resources.join_status == "unknown"
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


def test_equal_slot_substitution_retires_and_cannot_be_restored(admissions):
    with case(admissions) as (source, host, _, _):
        role = join(compose(source, host))
        state = syntax._state(role, live=True)
        slots = state.join_record.slots
        state.join_record.slots = (replace(slots[0]),)
        try:
            with pytest.raises(ContractViolation, match="predecessor changed"):
                syntax._state(role, live=True)
        finally:
            state.join_record.slots = slots
        with pytest.raises(ContractViolation):
            syntax._state(role, live=True)
        syntax.close_grammar_syntax_role_join(role)


def test_postconstruction_settlement_uncertainty_remains_independent(
    admissions, monkeypatch
):
    with case(admissions) as (source, host, participant, _):
        first = compose(source, host)
        parent = profile._state(first, live=True).resources
        error = ValueError("syntax construction settlement")
        original = epochs._TRANSITION

        def fail(instance, guard, use, before, after):
            if instance is participant and parent.syntax is not None and after is None:
                raise error
            return original(instance, guard, use, before, after)

        with monkeypatch.context() as changed:
            changed.setattr(epochs, "_TRANSITION", fail)
            with pytest.raises(ValueError) as caught:
                join(first)
        assert caught.value is parent.syntax.construction_error is error
        assert parent.syntax.validation_epoch == "uncertain"
        assert len(epochs._state(participant).uses) == 1
        receipt = profile.close_grammar_profile_source_role(first)
        assert receipt.completion == "unverified" and receipt.epoch_state == "uncertain"
        assert (
            parent.syntax.join_status == parent.syntax.registration_status == "released"
        )
        assert len(epochs._state(participant).uses) == 1
