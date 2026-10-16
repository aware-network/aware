"""Real registered Code syntax production with explicit fixture source/catalog parent."""

from contextlib import contextmanager

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_contribution_contract import (
    GRAMMAR_CONTRIBUTION_OUTPUT_REF,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_profile_role import compose
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import case
from test_grammar_syntax_composition import syntax_inputs


@contextmanager
def production_case(admissions, catalog, **options):
    arguments = syntax_inputs(catalog, **options)
    with case(
        admissions,
        extra_catalog_entries=(catalog[3],),
        ordinary_input=arguments["input"].ordinary,
    ) as (source, host, participant, _):
        first = compose(source, host)
        role = syntax._compose_grammar_syntax_role_join(profile_role=first)
        yield source, host, participant, first, role


@pytest.mark.parametrize("count,scanner", ((1, False), (2, False), (1, True)))
@pytest.mark.asyncio
async def test_registered_dependency_free_syntax_retains_real_result(
    admissions, admitted_catalog, count, scanner
):
    with production_case(
        admissions, admitted_catalog, count=count, scanner=scanner
    ) as (_, host, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
        assert len(value.contribution_bindings) == count
        assert all(
            row.contract == GRAMMAR_CONTRIBUTION_OUTPUT_REF
            for row in value.contribution_coordinates
        )
        assert (
            state.resources.result is result
            and state.resources.result_status == "pending"
        )
        assert state.resources.join_status == "released" and state.join_record.consumed
        assert len(state.resources.profile.host._results) == 2
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "verified"
        assert state.resources.result_status == "released"
        assert len(receipt.resources) <= 16
        assert syntax.close_grammar_syntax_role_join(role) is receipt
        assert not direct._HOSTS[host].closed


@pytest.mark.asyncio
async def test_selected_local_dependencies_use_original_source_admission(
    admissions, admitted_catalog
):
    with production_case(admissions, admitted_catalog, count=2, dependency=True) as (
        _,
        _,
        _,
        first,
        role,
    ):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        assert (
            state.resources.result is result
            and state.resources.result_status == "pending"
        )
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


@pytest.mark.asyncio
async def test_syntax_result_cleanup_precedes_predecessor_and_never_replays(
    admissions, admitted_catalog, monkeypatch
):
    with production_case(admissions, admitted_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        calls = []
        original = cleanup.release_registered_semantic_input_result

        def recorded(*args, **kwargs):
            calls.append(kwargs["result"])
            return original(*args, **kwargs)

        with monkeypatch.context() as changed:
            changed.setattr(
                cleanup, "release_registered_semantic_input_result", recorded
            )
            receipt = syntax.close_grammar_syntax_role_join(role)
            assert syntax.close_grammar_syntax_role_join(role) is receipt
        assert len(calls) == 2 and calls[0] is result and calls[1] is previous


@pytest.mark.asyncio
async def test_invalid_syntax_result_release_remains_unknown(
    admissions, admitted_catalog, monkeypatch
):
    with production_case(admissions, admitted_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        returned = object()
        original = cleanup.release_registered_semantic_input_result
        calls = []

        def invalid(*args, **kwargs):
            if kwargs["result"] is result:
                calls.append(True)
                return returned
            return original(*args, **kwargs)

        with monkeypatch.context() as changed:
            changed.setattr(
                cleanup, "release_registered_semantic_input_result", invalid
            )
            with pytest.raises(ContractViolation, match="disposal returned a value"):
                syntax.close_grammar_syntax_role_join(role)
        receipt = cleanup.read_grammar_role_cleanup(
            state.resources.profile.custody.ticket
        )
        assert (
            receipt.completion == "unverified"
            and state.resources.result_status == "unknown"
        )
        assert state.resources.profile.host._closed
        assert syntax.close_grammar_syntax_role_join(role) is receipt and calls == [
            True
        ]


@pytest.mark.asyncio
async def test_late_owner_record_substitution_cannot_confirm_consumption(
    admissions, admitted_catalog, monkeypatch
):
    with production_case(admissions, admitted_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = inputs.validate_registered_semantic_input_result

        def moved(host, registration, **kwargs):
            returned = original(host, registration, **kwargs)
            if registration is state.resources.registration:
                state.join_record = object()
            return returned

        with monkeypatch.context() as changed:
            changed.setattr(inputs, "validate_registered_semantic_input_result", moved)
            with pytest.raises(ContractViolation, match="consumption unconfirmed"):
                await syntax.execute_grammar_syntax_role_join(
                    role, predecessor=previous
                )
        assert (
            state.resources.result is None
            and state.resources.result_status == "unknown"
        )
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


@pytest.mark.asyncio
async def test_invalid_result_validation_return_does_not_adopt_result(
    admissions, admitted_catalog, monkeypatch
):
    with production_case(admissions, admitted_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = inputs.validate_registered_semantic_input_result
        returned = object()

        def invalid(host, registration, **kwargs):
            result = original(host, registration, **kwargs)
            return returned if registration is state.resources.registration else result

        with monkeypatch.context() as changed:
            changed.setattr(
                inputs, "validate_registered_semantic_input_result", invalid
            )
            with pytest.raises(ContractViolation, match="validator returned a value"):
                await syntax.execute_grammar_syntax_role_join(
                    role, predecessor=previous
                )
        assert (
            state.resources.execution_return_present and state.resources.result is None
        )
        assert state.resources.result_status == "unknown"
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


@pytest.mark.asyncio
async def test_exit_settlement_failure_preserves_known_result_and_unknown_epoch(
    admissions, admitted_catalog, monkeypatch
):
    from aware_code_retained_registry_policy_runtime import (
        epoch_participation as epochs,
    )

    with production_case(admissions, admitted_catalog) as (
        _,
        _,
        participant,
        first,
        role,
    ):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = epochs._TRANSITION
        error = ValueError("syntax final settlement")

        def fail(instance, guard, use, before, after):
            if (
                instance is participant
                and after is None
                and state.resources.result_status == "pending"
            ):
                raise error
            return original(instance, guard, use, before, after)

        with monkeypatch.context() as changed:
            changed.setattr(epochs, "_TRANSITION", fail)
            with pytest.raises(ValueError) as caught:
                await syntax.execute_grammar_syntax_role_join(
                    role, predecessor=previous
                )
        assert caught.value is error
        assert (
            state.resources.result is not None
            and state.resources.result_status == "pending"
        )
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "unverified" and receipt.epoch_state == "uncertain"
        assert (
            state.resources.result_status == "released"
            and state.resources.join_status == "released"
        )


@pytest.mark.asyncio
async def test_positive_execution_is_once_only(admissions, admitted_catalog):
    with production_case(admissions, admitted_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        state = syntax._state(role, live=False)
        assert state.resources.result is result
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "verified"
