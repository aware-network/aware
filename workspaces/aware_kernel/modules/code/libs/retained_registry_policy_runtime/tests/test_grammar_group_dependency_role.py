"""Registered original execution; source/catalog/command parents are explicit fixtures."""

import copy
from contextlib import contextmanager

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from test_grammar_group_dependency_binding import group_catalog as _catalog_fixture
from test_grammar_group_dependency_binding import grouped_args
from test_grammar_profile_role import compose
from test_grammar_role_attachment import admissions as _admissions_fixture
from test_grammar_role_attachment import case

group_catalog = _catalog_fixture
admissions = _admissions_fixture


@contextmanager
def group_case(admissions, catalog, **options):
    args = grouped_args(catalog, **options)
    with case(
        admissions,
        extra_catalog_entries=catalog[3],
        ordinary_input=args["input"].ordinary,
    ) as (source, host, participant, _):
        first = compose(source, host)
        role = syntax._compose_grammar_syntax_role_join(profile_role=first)
        yield source, host, participant, first, role


@pytest.mark.parametrize("dependency", (True, False))
async def test_registered_grouped_syntax_retains_original_result(
    admissions, group_catalog, dependency
):
    with group_case(admissions, group_catalog, dependency=dependency) as (
        _,
        host,
        _,
        first,
        role,
    ):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
        assert len(value.provider_bindings) == len(value.contribution_bindings) == 2
        assert len({row.occurrence_ref for row in value.contribution_bindings}) == 2
        assert (
            state.resources.result is result
            and state.resources.result_status == "pending"
        )
        assert state.resources.join_status == "released" and state.join_record.consumed
        receipt = syntax.close_grammar_syntax_role_join(role)
        assert receipt.completion == "verified"
        assert syntax.close_grammar_syntax_role_join(role) is receipt
        assert not direct._HOSTS[host].closed


@pytest.mark.parametrize(
    "options",
    (
        {"edge": False},
        {"reverse_edge": True},
        {"wrong_digest": True},
        {"wrong_version": True},
        {"duplicate_label": True},
    ),
)
async def test_grouped_refusal_retires_without_retained_success(
    admissions, group_catalog, options
):
    with group_case(admissions, group_catalog, **options) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        with pytest.raises(ValueError):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert (
            state.resources.result is None
            and state.resources.result_status == "unknown"
        )
        assert state.profile_state.attachment.retired
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


async def test_copied_group_result_does_not_gain_retention(admissions, group_catalog):
    with group_case(admissions, group_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        state = syntax._state(role, live=False)
        with pytest.raises(ContractViolation):
            inputs.validate_registered_semantic_input_result(
                state.resources.profile.host,
                state.resources.registration,
                source_admission=state.resources.expected.source_identity,
                expected=state.resources.expected,
                result=copy.copy(result),
            )
        assert state.resources.result is result
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


async def test_grouped_failure_never_falls_back_to_local_helper(
    admissions, group_catalog, monkeypatch
):
    with group_case(admissions, group_catalog, edge=False) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        calls = []

        def forbidden(*args, **kwargs):
            calls.append(True)
            raise AssertionError("local fallback dispatched")

        with monkeypatch.context() as changed:
            changed.setattr(
                syntax, "reconstruct_grammar_local_dependency_binding", forbidden
            )
            with pytest.raises(ContractViolation, match="grouped provenance"):
                await syntax.execute_grammar_syntax_role_join(
                    role, predecessor=previous
                )
        assert calls == []
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


async def test_group_source_retirement_cannot_be_restored(
    admissions, group_catalog, monkeypatch
):
    with group_case(admissions, group_catalog) as (source, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = syntax.reconstruct_grammar_group_dependency_binding

        def retired(*args, **kwargs):
            result = original(*args, **kwargs)
            source.source_live = False
            return result

        with monkeypatch.context() as changed:
            changed.setattr(
                syntax, "reconstruct_grammar_group_dependency_binding", retired
            )
            with pytest.raises(ContractViolation):
                await syntax.execute_grammar_syntax_role_join(
                    role, predecessor=previous
                )
        source.source_live = True
        assert state.resources.result is None and state.profile_state.attachment.retired
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


async def test_group_result_survives_failed_epoch_settlement(
    admissions, group_catalog, monkeypatch
):
    with group_case(admissions, group_catalog) as (_, _, participant, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = epochs._TRANSITION
        error = ValueError("grouped syntax final settlement")

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
        assert state.resources.result_status == "released"


async def test_group_execution_is_once_only(admissions, group_catalog):
    with group_case(admissions, group_catalog) as (_, _, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert syntax._state(role, live=False).resources.result is result
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"


async def test_direct_group_producer_call_refuses(admissions, group_catalog):
    with group_case(admissions, group_catalog) as (_, _, _, first, role):
        state = syntax._state(role, live=True)
        with pytest.raises(ContractViolation, match="registered syntax execution"):
            await state.producer(None)
        assert state.resources.result is None
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"
