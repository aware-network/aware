"""Public selector/owner proofs; fixture parents and genuine intake stay distinct.

No SDK rendering, native parser, installed toolchain or public bootstrap proof.
"""

import asyncio
import copy
import inspect
import pickle
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from aware_code_module_manifest_contract_runtime.grammar_profile_source import (
    GrammarProfileSourceError,
)
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as epoch
from aware_code_retained_registry_policy_runtime import grammar_profile_role as profile
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_retained_registry_policy_runtime import (
    grammar_role_composition as public,
)
from aware_code_retained_registry_policy_runtime import grammar_syntax_role as syntax
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarSyntaxBindingCodec,
)
from test_grammar_original_source_execution import (
    MODULE_PATH,
    PROFILE_KEY,
    original_execution,
)
from test_grammar_original_source_execution import (
    grammar_admissions as grammar_admissions,
)
from test_grammar_original_source_execution import (
    sdk_admission as sdk_admission,
)
from test_grammar_profile_composition import admitted_catalog as admitted_catalog
from test_grammar_role_attachment import admissions as admissions
from test_grammar_role_attachment import case
from test_grammar_syntax_composition import syntax_inputs
from test_materialization_catalog import _binding


def compose(source, host, key="default"):
    return public.compose_registered_grammar_source_roles(
        code_host=host,
        profile_expected=source.inputs[0],
        syntax_expected=source.inputs[1],
        profile_key=key,
    )


def marker(error):
    group = error if isinstance(error, BaseExceptionGroup) else error.__cause__
    assert isinstance(group, BaseExceptionGroup)
    value = group.exceptions[-1]
    assert type(value) is public.CodeGrammarRoleFailureEvidenceError
    assert sum(type(e) is type(value) for e in group.exceptions) == 1
    return value


def test_required_keyword_only_selector_has_no_default():
    signature = inspect.signature(public.compose_registered_grammar_source_roles)
    assert tuple(signature.parameters) == (
        "code_host",
        "profile_expected",
        "syntax_expected",
        "profile_key",
    )
    for field in signature.parameters.values():
        assert field.kind is inspect.Parameter.KEYWORD_ONLY
        assert field.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match="profile_key"):
        public.compose_registered_grammar_source_roles(
            code_host=None, profile_expected=None, syntax_expected=None
        )


@pytest.mark.parametrize(
    "key", (None, False, "", " ", "alias default", "x" * 513, "\ud800")
)
def test_invalid_selector_refuses_before_attachment_or_source_callbacks(
    admissions, key
):
    with case(admissions) as (source, host, participant, _):
        before = tuple(source.calls)
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host, key):
                pytest.fail("invalid selector yielded a host")
        primary = error.value.exceptions[0]
        assert type(primary) is GrammarProfileSourceError
        assert primary.reason == "authored_selector_invalid"
        evidence = marker(error.value)
        assert evidence.original_primary is primary
        assert evidence.cleanup_ticket is None
        assert evidence.snapshot.results_state == "not_started"
        assert evidence.snapshot.cleanup.attempt_ref is None
        assert evidence.snapshot.cleanup.completion == "verified"
        assert not evidence.raw_return_present
        assert direct._HOSTS[host].grammar_attachment is None
        assert tuple(source.calls) == before
        assert not epoch._state(participant).uses
        # An invalid request never spends the valid original attachment attempt.
        with compose(source, host):
            pass


@pytest.mark.parametrize("bad", (None, object(), {}))
def test_foreign_host_refuses_without_attachment_effects(admissions, bad):
    with case(admissions) as (source, host, _, _):
        before = tuple(source.calls)
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, bad):
                pytest.fail("foreign host accepted")
        assert type(error.value.exceptions[0]) is TypeError
        assert marker(error.value).cleanup_ticket is None
        assert tuple(source.calls) == before
        assert direct._HOSTS[host].grammar_attachment is None


@pytest.mark.parametrize("port", ("profile", "syntax"))
def test_substituted_composition_entrance_refuses_before_callbacks(
    admissions, monkeypatch, port
):
    with case(admissions) as (source, host, _, _):
        before = tuple(source.calls)
        module, name = (
            (profile, "_compose_grammar_profile_source_role")
            if port == "profile"
            else (syntax, "_compose_grammar_syntax_role_join")
        )
        with monkeypatch.context() as changed:
            changed.setattr(
                module, name, lambda **kwargs: pytest.fail("substitute called")
            )
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host):
                    pytest.fail("substitution accepted")
        assert type(error.value.exceptions[0]) is ContractViolation
        assert tuple(source.calls) == before
        assert direct._HOSTS[host].grammar_attachment is None


def test_selector_is_forwarded_by_identity_and_borrowed_owners_survive(admissions):
    key = "".join(("de", "fault"))
    with case(admissions) as (source, host, participant, _):
        with compose(source, host, key) as role:
            view = public._view(role, live=True)
            original = profile._state(view.profile_role, live=True)
            assert original.profile_key is key
            assert original.original_key is key
            ticket = original.resources.custody.ticket
        receipt = cleanup.read_grammar_role_cleanup(ticket)
        assert receipt.completion == "verified"
        assert receipt.cause == "normal_close"
        assert cleanup.dispose_grammar_role_cleanup(ticket) is receipt
        assert not direct._HOSTS[host].closed
        assert not epoch._state(participant).closed
        assert source.source_live


@pytest.mark.parametrize("action", (copy.copy, copy.deepcopy, pickle.dumps))
def test_public_host_is_sealed_and_not_copyable(admissions, action):
    with case(admissions) as (source, host, _, _):
        with compose(source, host) as role:
            with pytest.raises(TypeError):
                action(role)
            with pytest.raises(TypeError):
                public.CodeGrammarRoleHost()


def test_existing_attachment_is_not_adopted_or_disposed(admissions):
    with case(admissions) as (source, host, _, _):
        first = profile._compose_grammar_profile_source_role(
            code_host=host,
            profile_expected=source.inputs[0],
            syntax_expected=source.inputs[1],
            profile_key="default",
        )
        state = profile._state(first, live=True)
        before = tuple(source.calls)
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host):
                pytest.fail("foreign attachment adopted")
        assert marker(error.value).cleanup_ticket is None
        assert profile._state(first, live=True) is state
        assert not state.resources.host._closed
        assert tuple(source.calls) == before
        profile.close_grammar_profile_source_role(first)


@pytest.mark.asyncio
async def test_selector_substitution_still_refuses(admissions):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host) as role:
                view = public._view(role, live=True)
                state = profile._state(view.profile_role, live=True)
                state.profile_key = "other"
                await public.execute_grammar_profile_selection(role)
        assert type(error.value.exceptions[0]) is ContractViolation
        assert "original profile role is retired or changed" in str(
            error.value.exceptions[0]
        )
        assert not marker(error.value).snapshot.known_results


@pytest.mark.parametrize("key", ("unknown", "Default", "alias.default"))
@pytest.mark.asyncio
async def test_valid_but_absent_selector_has_no_alias_or_fallback(admissions, key):
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host, key) as role:
                await public.execute_grammar_profile_selection(role)
        assert isinstance(error.value.exceptions[0], ContractViolation)
        assert not marker(error.value).snapshot.known_results


@pytest.mark.asyncio
async def test_original_results_validate_release_and_normal_close(
    admissions, admitted_catalog
):
    arguments = syntax_inputs(admitted_catalog, count=2, scanner=True)
    with case(
        admissions,
        extra_catalog_entries=(admitted_catalog[3],),
        ordinary_input=arguments["input"].ordinary,
    ) as (source, host, _, _):
        with compose(source, host) as role:
            view = public._view(role, live=True)
            ticket = profile._state(
                view.profile_role, live=True
            ).resources.custody.ticket
            previous = await public.execute_grammar_profile_selection(role)
            result = await public.execute_grammar_syntax_binding(
                role, predecessor=previous
            )
            assert (
                len(
                    CodeGrammarSyntaxBindingCodec()
                    .decode(result.canonical_body)
                    .contribution_bindings
                )
                == 2
            )
            assert public.validate_grammar_role_result(role, result=previous) is None
            assert public.validate_grammar_role_result(role, result=result) is None
            with pytest.raises(ContractViolation, match="retained"):
                public.validate_grammar_role_result(role, result=replace(result))
            public.release_grammar_role_result(role, result=result)
            public.release_grammar_role_result(role, result=previous)
            with pytest.raises(ContractViolation, match="retained"):
                public.release_grammar_role_result(role, result=result)
        assert cleanup.read_grammar_role_cleanup(ticket).completion == "verified"


@pytest.mark.parametrize("kind", ("error", "group", "cancel", "exit", "interrupt"))
@pytest.mark.asyncio
async def test_failure_delivery_preserves_primary_and_known_result(admissions, kind):
    original = {
        "error": ValueError("body failed"),
        "group": ExceptionGroup("original group", [ValueError("nested")]),
        "cancel": asyncio.CancelledError("cancelled"),
        "exit": SystemExit(17),
        "interrupt": KeyboardInterrupt("interrupted"),
    }[kind]
    old_cause = RuntimeError("original cause")
    original.__cause__ = old_cause
    interrupted = kind in {"cancel", "exit", "interrupt"}
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with pytest.raises(BaseException) as error:
            with compose(source, host) as role:
                result = await public.execute_grammar_profile_selection(role)
                raise original
        if interrupted:
            assert error.value is original
        else:
            assert type(error.value) is ExceptionGroup
            assert error.value.exceptions[0] is original
            assert original.__cause__ is old_cause
        evidence = marker(error.value)
        assert evidence.original_primary is original
        assert evidence.original_cause is old_cause
        assert evidence.snapshot.phase == "context_exit"
        assert evidence.snapshot.results_state == "known"
        assert evidence.snapshot.known_results == (result.coordinate,)
        assert evidence.snapshot.cleanup.completion == "verified"
        with pytest.raises(AttributeError):
            evidence.snapshot = evidence.snapshot
        assert (
            cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)
            is evidence.snapshot.cleanup
        )


@pytest.mark.parametrize("returned", (None, object()))
@pytest.mark.asyncio
async def test_invalid_execution_return_presence_is_retained(
    admissions, monkeypatch, returned
):
    async def invalid(*args, **kwargs):
        return returned

    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with monkeypatch.context() as changed:
            changed.setattr(inputs, "execute_registered_semantic_input", invalid)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host) as role:
                    await public.execute_grammar_profile_selection(role)
        evidence = marker(error.value)
        assert evidence.snapshot.results_state == "unvalidated"
        assert evidence.snapshot.reason == "result_unvalidated"
        assert evidence.raw_return_present and evidence.raw_return is returned
        assert evidence.snapshot.cleanup.completion == "unverified"


@pytest.mark.asyncio
async def test_invalid_syntax_release_remains_unknown_without_replay(
    admissions, admitted_catalog, monkeypatch
):
    arguments = syntax_inputs(admitted_catalog)
    with case(
        admissions,
        extra_catalog_entries=(admitted_catalog[3],),
        ordinary_input=arguments["input"].ordinary,
    ) as (source, host, _, _):
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host) as role:
                previous = await public.execute_grammar_profile_selection(role)
                result = await public.execute_grammar_syntax_binding(
                    role, predecessor=previous
                )
                original = inputs.release_registered_semantic_input_result
                calls = []

                def invalid(*args, **kwargs):
                    if kwargs["result"] is result:
                        calls.append(result)
                        return False
                    return original(*args, **kwargs)

                with monkeypatch.context() as changed:
                    changed.setattr(
                        inputs, "release_registered_semantic_input_result", invalid
                    )
                    public.release_grammar_role_result(role, result=result)
        evidence = marker(error.value)
        assert evidence.snapshot.phase == "release_result"
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert any(
            row.resource_kind == "syntax_result" and row.status == "unknown"
            for row in evidence.snapshot.cleanup.resources
        )
        assert calls == [result]
        assert (
            cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)
            is evidence.snapshot.cleanup
        )
        assert calls == [result]


def test_source_failure_keeps_original_custody_and_error(admissions):
    original = ValueError("original source unavailable")
    with case(admissions) as (source, host, _, _):
        source.failure = original
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host):
                pytest.fail("source failure accepted")
        assert error.value.exceptions[0] is original
        evidence = marker(error.value)
        assert evidence.cleanup_ticket is not None
        assert evidence.snapshot.phase == "construct"
        assert evidence.snapshot.cleanup.cause == "construction_failure"


def test_cross_thread_view_refuses_without_spending_original(admissions):
    with case(admissions) as (source, host, _, _):
        with compose(source, host) as role:
            before = tuple(source.calls)
            with ThreadPoolExecutor(max_workers=1) as executor:
                attempt = executor.submit(public._view, role, live=True)
                with pytest.raises(ContractViolation, match="thread differs"):
                    attempt.result()
            assert tuple(source.calls) == before
            assert public._view(role, live=True).handle is role


@pytest.mark.asyncio
async def test_invalid_validation_return_is_process_local_evidence(
    admissions, monkeypatch
):
    returned = object()
    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with pytest.raises(ExceptionGroup) as error:
            with compose(source, host) as role:
                result = await public.execute_grammar_profile_selection(role)
                with monkeypatch.context() as changed:
                    changed.setattr(
                        inputs,
                        "validate_registered_semantic_input_result",
                        lambda *args, **kwargs: returned,
                    )
                    public.validate_grammar_role_result(role, result=result)
        evidence = marker(error.value)
        assert evidence.snapshot.phase == "validate_result"
        assert evidence.snapshot.results_state == "unvalidated"
        assert evidence.snapshot.known_results == (result.coordinate,)
        assert evidence.raw_return_present and evidence.raw_return is returned


@pytest.mark.parametrize("invalid_return", (False, True))
def test_cleanup_observation_failure_cannot_replace_original_error(
    admissions, monkeypatch, invalid_return
):
    primary = ValueError("original context failure")
    observation = RuntimeError("original receipt unavailable")
    with case(admissions) as (source, host, _, _):
        with monkeypatch.context() as changed:

            def failed_read(ticket):
                if invalid_return:
                    return None
                raise observation

            changed.setattr(cleanup, "read_grammar_role_cleanup", failed_read)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host):
                    raise primary
        assert error.value.exceptions[0] is primary
        if not invalid_return:
            assert any(item is observation for item in error.value.exceptions)
        evidence = marker(error.value)
        assert evidence.cleanup_ticket is not None
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert (
            evidence.snapshot.cleanup.attempt_ref
            == cleanup._custody(evidence.cleanup_ticket).attempt_ref
        )


@pytest.mark.parametrize("malformed", (False, True))
@pytest.mark.parametrize("two_results", (False, True))
@pytest.mark.asyncio
async def test_cleanup_read_cannot_erase_retained_results(
    admissions, admitted_catalog, monkeypatch, malformed, two_results
):
    arguments = syntax_inputs(admitted_catalog)
    primary = ValueError("original failure after original results")
    observation = RuntimeError("original cleanup observation failed")
    with case(
        admissions,
        extra_catalog_entries=(admitted_catalog[3],),
        ordinary_input=arguments["input"].ordinary,
    ) as (source, host, _, _):
        results = []
        with monkeypatch.context() as changed:
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host) as role:
                    previous = await public.execute_grammar_profile_selection(role)
                    results.append(previous)
                    if two_results:
                        results.append(
                            await public.execute_grammar_syntax_binding(
                                role, predecessor=previous
                            )
                        )

                    def unavailable(ticket):
                        if malformed:
                            return None
                        raise observation

                    changed.setattr(cleanup, "read_grammar_role_cleanup", unavailable)
                    raise primary
        evidence = marker(error.value)
        assert error.value.exceptions[0] is primary
        assert evidence.snapshot.results_state == "known"
        assert set(evidence.snapshot.known_results) == {
            result.coordinate for result in results
        }
        assert evidence.snapshot.cleanup.profile_input_digest is not None
        assert evidence.snapshot.cleanup.syntax_input_digest is not None
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert not evidence.raw_return_present
        assert not evidence.disposal_return_present
        if not malformed:
            assert any(item is observation for item in error.value.exceptions)
        # Explicit test teardown, not a retry made by the public composition.
        cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)


@pytest.mark.parametrize("malformed", (False, True))
@pytest.mark.asyncio
async def test_cleanup_read_cannot_erase_observed_execution_none(
    admissions, monkeypatch, malformed
):
    observation = RuntimeError("cleanup unavailable after invalid return")

    async def invalid(*args, **kwargs):
        return None

    def unavailable(ticket):
        if malformed:
            return None
        raise observation

    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with monkeypatch.context() as changed:
            changed.setattr(inputs, "execute_registered_semantic_input", invalid)
            changed.setattr(cleanup, "read_grammar_role_cleanup", unavailable)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host) as role:
                    await public.execute_grammar_profile_selection(role)
        evidence = marker(error.value)
        assert evidence.raw_return_present and evidence.raw_return is None
        assert evidence.snapshot.results_state == "unvalidated"
        assert evidence.snapshot.cleanup.completion == "unverified"
        cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)


@pytest.mark.parametrize("returned", (None, object()))
@pytest.mark.parametrize("failure_path", (False, True))
def test_top_level_disposal_return_requires_original_confirmation(
    admissions, monkeypatch, returned, failure_path
):
    primary = ValueError("body primary")
    calls = []
    with case(admissions) as (source, host, _, _):
        with monkeypatch.context() as changed:

            def invalid(ticket):
                calls.append(ticket)
                return returned

            changed.setattr(cleanup, "dispose_grammar_role_cleanup", invalid)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host) as role:
                    if failure_path:
                        raise primary
        evidence = marker(error.value)
        if failure_path:
            assert error.value.exceptions[0] is primary
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert evidence.raw_return_present and evidence.raw_return is returned
        assert evidence.disposal_return_present and evidence.disposal_return is returned
        assert calls == [evidence.cleanup_ticket]
        with pytest.raises(ContractViolation):
            public._view(role, live=True)
        cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)
        assert calls == [evidence.cleanup_ticket]


@pytest.mark.parametrize("returned", (None, object()))
def test_original_disposer_final_malformed_observation_refuses(
    admissions, monkeypatch, returned
):
    calls = []
    original_read = cleanup.read_grammar_role_cleanup
    original_dispose = cleanup.dispose_grammar_role_cleanup
    with case(admissions) as (source, host, _, _):
        with monkeypatch.context() as changed:

            def invalid_final(ticket):
                receipt = original_read(ticket)
                if cleanup._custody(ticket).attachment_status == "released":
                    return returned
                return receipt

            def counted(ticket):
                calls.append(ticket)
                return original_dispose(ticket)

            changed.setattr(cleanup, "read_grammar_role_cleanup", invalid_final)
            changed.setattr(cleanup, "dispose_grammar_role_cleanup", counted)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host):
                    pass
        evidence = marker(error.value)
        assert evidence.snapshot.phase == "close"
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert evidence.raw_return_present and evidence.raw_return is returned
        assert evidence.disposal_return_present and evidence.disposal_return is returned
        assert calls == [evidence.cleanup_ticket]
        custody = cleanup._custody(evidence.cleanup_ticket)
        assert (
            custody.disposal_state == "complete"
            and custody.terminal_receipt is returned
        )
        # No repair or repeated disposal manufactures the missing original receipt.


def test_equal_but_copied_terminal_receipt_is_not_confirmation(admissions, monkeypatch):
    original = cleanup.dispose_grammar_role_cleanup
    calls = []
    with case(admissions) as (source, host, _, _):
        with monkeypatch.context() as changed:

            def copied(ticket):
                calls.append(ticket)
                return replace(original(ticket))

            changed.setattr(cleanup, "dispose_grammar_role_cleanup", copied)
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host):
                    pass
        evidence = marker(error.value)
        custody = cleanup._custody(evidence.cleanup_ticket)
        assert evidence.raw_return == custody.terminal_receipt
        assert evidence.raw_return is not custody.terminal_receipt
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert calls == [evidence.cleanup_ticket]


@pytest.mark.asyncio
async def test_invalid_disposal_cannot_mask_primary_raw_none(admissions, monkeypatch):
    returned = object()

    async def invalid(*args, **kwargs):
        return None

    with case(admissions, extra_catalog_entries=(_binding(provider_key="demo"),)) as (
        source,
        host,
        _,
        _,
    ):
        with monkeypatch.context() as changed:
            changed.setattr(inputs, "execute_registered_semantic_input", invalid)
            changed.setattr(
                cleanup, "dispose_grammar_role_cleanup", lambda ticket: returned
            )
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host) as role:
                    await public.execute_grammar_profile_selection(role)
        evidence = marker(error.value)
        assert evidence.raw_return_present and evidence.raw_return is None
        assert evidence.disposal_return_present and evidence.disposal_return is returned
        assert evidence.snapshot.results_state == "unvalidated"
        assert evidence.snapshot.cleanup.completion == "unverified"
        cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)


@pytest.mark.parametrize("kind", ("registration", "host"))
def test_invalid_close_return_stays_unknown_and_does_not_replay(
    admissions, monkeypatch, kind
):
    returned = object()
    calls = []
    with case(admissions) as (source, host, _, _):
        with monkeypatch.context() as changed:

            def invalid(*args, **kwargs):
                calls.append(True)
                return returned

            if kind == "host":
                changed.setattr(inputs.SemanticInputProducerHost, "close", invalid)
            else:
                original = cleanup.close_semantic_input_producer_registration

                def selected(input_host, registration):
                    if (
                        registration
                        is direct._HOSTS[
                            host
                        ].grammar_attachment.profile_resources.registration
                    ):
                        return invalid()
                    return original(input_host, registration)

                changed.setattr(
                    cleanup, "close_semantic_input_producer_registration", selected
                )
            with pytest.raises(ExceptionGroup) as error:
                with compose(source, host):
                    pass
        evidence = marker(error.value)
        assert evidence.snapshot.phase == "close"
        assert evidence.snapshot.cleanup.completion == "unverified"
        assert evidence.raw_return_present and evidence.raw_return is returned
        assert calls == [True]
        assert (
            cleanup.dispose_grammar_role_cleanup(evidence.cleanup_ticket)
            is evidence.snapshot.cleanup
        )
        assert calls == [True]


@pytest.mark.asyncio
async def test_genuine_workspace_public_constructor_execution_and_close(
    tmp_path, grammar_admissions, sdk_admission
):
    async with original_execution(
        tmp_path, (*grammar_admissions, sdk_admission), compose_roles=False
    ) as c:
        key = "".join(("original.", "grammar"))
        with public.compose_registered_grammar_source_roles(
            code_host=c.paired.code_host,
            profile_expected=c.expected[0],
            syntax_expected=c.expected[1],
            profile_key=key,
        ) as role:
            view = public._view(role, live=True)
            state = profile._state(view.profile_role, live=True)
            assert state.profile_key is key
            assert state.attachment.methods[0].receiver is c.issuer
            assert (
                c.expected[0].operation_identity
                is c.paired.staged.command.invocation_parent
            )
            ticket = state.resources.custody.ticket
            previous = await public.execute_grammar_profile_selection(role)
            result = await public.execute_grammar_syntax_binding(
                role, predecessor=previous
            )
            value = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
            assert value.interpretation_profile == previous.coordinate
            assert len(value.contribution_bindings) == 1
            public.validate_grammar_role_result(role, result=result)
        receipt = cleanup.read_grammar_role_cleanup(ticket)
        assert receipt.cause == "normal_close" and receipt.completion == "verified"
        assert not direct._HOSTS[c.paired.code_host].closed


@pytest.mark.asyncio
async def test_genuine_selector_refuses_early_then_original_mutation_retires(
    tmp_path, grammar_admissions, sdk_admission
):
    async with original_execution(
        tmp_path, (*grammar_admissions, sdk_admission), compose_roles=False
    ) as c:
        with pytest.raises(ExceptionGroup) as early:
            with public.compose_registered_grammar_source_roles(
                code_host=c.paired.code_host,
                profile_expected=c.expected[0],
                syntax_expected=c.expected[1],
                profile_key="invalid selector",
            ):
                pytest.fail("invalid selector accepted")
        assert marker(early.value).cleanup_ticket is None
        assert direct._HOSTS[c.paired.code_host].grammar_attachment is None
        with pytest.raises(ExceptionGroup) as failed:
            with public.compose_registered_grammar_source_roles(
                code_host=c.paired.code_host,
                profile_expected=c.expected[0],
                syntax_expected=c.expected[1],
                profile_key=PROFILE_KEY,
            ) as role:
                original = (c.root / MODULE_PATH).read_bytes()
                (c.root / MODULE_PATH).write_bytes(original + b"\n# moved\n")
                try:
                    await public.execute_grammar_profile_selection(role)
                finally:
                    (c.root / MODULE_PATH).write_bytes(original)
        evidence = marker(failed.value)
        assert evidence.snapshot.phase == "profile_selection"
        assert not evidence.snapshot.known_results
        assert direct._HOSTS[c.paired.code_host].grammar_attachment.retired
        with pytest.raises(ContractViolation):
            public._view(role, live=True)
