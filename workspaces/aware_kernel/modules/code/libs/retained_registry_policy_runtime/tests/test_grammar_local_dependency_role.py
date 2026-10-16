"""Original registered Code execution; source/catalog/lifetime parents are fixtures."""

import copy

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from aware_language_parsed_document_contract import SyntaxAssemblyContractError
from test_grammar_contribution_production import production_case
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_role_attachment import admissions as admissions


@pytest.mark.parametrize("count,scanner", ((2, False), (4, False), (2, True)))
@pytest.mark.asyncio
async def test_original_selected_local_dependencies_retain_result(
    admissions, admitted_catalog, count, scanner
):
    with production_case(
        admissions, admitted_catalog, count=count, dependency=True, scanner=scanner
    ) as (_, host, _, first, role):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        result = await syntax.execute_grammar_syntax_role_join(
            role, predecessor=previous
        )
        assert (
            len(
                CodeGrammarSyntaxBindingCodec()
                .decode(result.canonical_body)
                .contribution_bindings
            )
            == count
        )
        assert (
            state.resources.result is result
            and state.resources.join_status == "released"
        )
        assert syntax.close_grammar_syntax_role_join(role).completion == "verified"
        assert not direct._HOSTS[host].closed


@pytest.mark.parametrize(
    "options",
    (
        {"missing_dependency": True},
        {"count": 2, "dependency": True, "bad_dependency_digest": True},
    ),
)
@pytest.mark.asyncio
async def test_dependency_failure_is_terminal_without_retained_success(
    admissions, admitted_catalog, options
):
    with production_case(admissions, admitted_catalog, **options) as (
        _,
        _,
        _,
        first,
        role,
    ):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        with pytest.raises(SyntaxAssemblyContractError):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert (
            state.resources.result is None
            and state.resources.result_status == "unknown"
        )
        assert state.profile_state.attachment.retired
        with pytest.raises(ContractViolation):
            await syntax.execute_grammar_syntax_role_join(role, predecessor=previous)
        assert syntax.close_grammar_syntax_role_join(role).completion == "unverified"


@pytest.mark.asyncio
async def test_local_binding_copied_result_does_not_gain_retention(
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


@pytest.mark.asyncio
async def test_source_retirement_during_local_reconstruction_cannot_revive(
    admissions, admitted_catalog, monkeypatch
):
    with production_case(admissions, admitted_catalog, count=2, dependency=True) as (
        source,
        _,
        _,
        first,
        role,
    ):
        previous = await profile.execute_grammar_profile_source_role(first)
        state = syntax._state(role, live=True)
        original = syntax.reconstruct_grammar_local_dependency_binding

        def retired(*args, **kwargs):
            result = original(*args, **kwargs)
            source.source_live = False
            return result

        with monkeypatch.context() as changed:
            changed.setattr(
                syntax, "reconstruct_grammar_local_dependency_binding", retired
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
