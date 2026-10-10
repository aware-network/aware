"""Read-only validation on the existing original selected-provider test factory."""

import copy
from dataclasses import replace
from types import MethodType

import pytest
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from test_selected_provider import _BINDING, _runtime, _selected, _SelectedProvider


def validate(runtime, provider, registration, **changes):
    values = {
        "expected_profile": runtime.profile,
        "expected_declaration": provider.declaration,
        "expected_binding": _BINDING,
    }
    values.update(changes)
    selected.validate_selected_provider_registration(runtime, registration, **values)


def test_readonly_validation_never_derives_or_consumes_execution():
    runtime, provider, _, registration = _selected()
    before = selected._registration_state(registration).sequence
    for _ in range(3):
        validate(runtime, provider, registration)
    assert selected._registration_state(registration).sequence == before
    assert provider.calls == 0
    assert provider.last_input_value is None
    selected.close_selected_provider_registration(runtime, registration)


def test_detached_equal_expectations_are_checks_not_new_authority():
    runtime, provider, _, registration = _selected()
    validate(
        runtime,
        provider,
        registration,
        expected_profile=copy.deepcopy(runtime.profile),
        expected_declaration=copy.deepcopy(provider.declaration),
        expected_binding=copy.deepcopy(_BINDING),
    )
    selected.close_selected_provider_registration(runtime, registration)
    with pytest.raises(ContractViolation):
        validate(runtime, provider, registration)


def test_foreign_runtime_rejects():
    runtime, provider, _, registration = _selected()
    foreign, _ = _runtime()
    with pytest.raises(ContractViolation):
        validate(foreign, provider, registration)
    selected.close_selected_provider_registration(runtime, registration)


@pytest.mark.parametrize("field", ["profile", "binding", "declaration"])
def test_wrong_expected_context_rejects(field):
    runtime, provider, _, registration = _selected()
    if field == "profile":
        changes = {"expected_profile": replace(runtime.profile, profile_ref="foreign")}
    elif field == "binding":
        changes = {"expected_binding": replace(_BINDING, provider_key="foreign")}
    else:
        changes = {
            "expected_declaration": replace(
                provider.declaration, provider_key="foreign"
            )
        }
    with pytest.raises(ContractViolation):
        validate(runtime, provider, registration, **changes)
    selected.close_selected_provider_registration(runtime, registration)


@pytest.mark.parametrize("method", ["execute", "input_closure"])
def test_current_method_substitution_rejects(method):
    runtime, provider, _, registration = _selected()
    setattr(provider, method, MethodType(lambda self, *args: None, provider))
    with pytest.raises(ContractViolation, match="substituted"):
        validate(runtime, provider, registration)
    selected.close_selected_provider_registration(runtime, registration)


def test_matching_declaration_provider_substitution_rejects():
    runtime, provider, _, registration = _selected()
    runtime._providers["sdk"] = _SelectedProvider()
    with pytest.raises(ContractViolation, match="substituted"):
        validate(runtime, provider, registration)
    selected.close_selected_provider_registration(runtime, registration)


def test_changed_artifact_rejects():
    runtime, provider, _, registration = _selected()
    state = selected._registration_state(registration)
    original = state.semantic_implementation_contract_body
    try:
        state.semantic_implementation_contract_body = b"changed"
        with pytest.raises(ContractViolation):
            validate(runtime, provider, registration)
    finally:
        state.semantic_implementation_contract_body = original
        selected.close_selected_provider_registration(runtime, registration)


def test_pid_change_rejects(monkeypatch):
    runtime, provider, _, registration = _selected()
    pid = selected.os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(selected.os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            validate(runtime, provider, registration)
    selected.close_selected_provider_registration(runtime, registration)
