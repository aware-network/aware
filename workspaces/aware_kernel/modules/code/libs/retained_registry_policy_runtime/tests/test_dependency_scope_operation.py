"""Real Code uses with fixture owner context; no fixed bootstrap qualification."""

import os
from dataclasses import replace
from threading import Thread

import pytest
from aware_code_retained_registry_policy_runtime import (
    dependency_scope_operation as impl,
)
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)
from test_direct_epoch_tracking import setup


def fixture(monkeypatch, *, running=True, purpose="source_planning"):
    owner, host, participant = setup(monkeypatch)
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        use = participant._begin_epoch_use(guard, owner.current, expected=owner.epoch)
        if running:
            participant._start_epoch_use(guard, use)
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    validator = impl._create_dependency_scope_operation_validator(host)
    # These source comparison coordinates are fixture-only. The real fixed
    # composition must supply authenticated original source/context correspondence.
    expected = RetainedDependencyScopeExpectation(
        owner.parent, owner.current, use, os.getpid(), object(), owner, "consumer"
    )
    if running:
        impl._retain_dependency_scope_operation(
            validator, use, expected=expected, purpose=purpose
        )
    return owner, host, participant, use, validator, expected


@pytest.mark.parametrize(
    "purpose",
    [
        "policy_calculation",
        "policy_validation",
        "source_planning",
        "authority_derivation",
    ],
)
def test_original_running_use_and_no_owner_calls(monkeypatch, purpose):
    owner, _, _, use, validator, expected = fixture(monkeypatch, purpose=purpose)
    owner.on_read = lambda: pytest.fail("owner read")
    owner.on_validate = lambda: pytest.fail("owner validation")
    assert validator.validate_dependency_scope_operation(use, expected=expected) is None
    assert (
        validator.validate_dependency_scope_operation(use, expected=replace(expected))
        is None
    )
    with pytest.raises(ContractViolation):
        impl._retain_dependency_scope_operation(
            validator, use, expected=expected, purpose=purpose
        )


@pytest.mark.parametrize(
    "field",
    [
        "parent_identity",
        "epoch_identity",
        "operation_identity",
        "repository_membership_identity",
        "closure_runtime_identity",
        "process_id",
        "consumer_scope_key",
    ],
)
def test_expected_substitution_refuses(monkeypatch, field):
    _, _, _, use, validator, expected = fixture(monkeypatch)
    value = (
        expected.process_id + 1
        if field == "process_id"
        else "other"
        if field == "consumer_scope_key"
        else object()
    )
    with pytest.raises(ContractViolation):
        validator.validate_dependency_scope_operation(
            use, expected=replace(expected, **{field: value})
        )


def test_pending_use_cannot_bind(monkeypatch):
    _, _, _, use, validator, expected = fixture(monkeypatch, running=False)
    with pytest.raises(ContractViolation):
        impl._retain_dependency_scope_operation(
            validator, use, expected=expected, purpose="source_planning"
        )


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
def test_completed_use_cannot_be_reused_and_cleanup_survives(monkeypatch, stage):
    owner, _, participant, use, validator, expected = fixture(
        monkeypatch, purpose=stage
    )
    guard = owner.acquire_catalog_epoch_exclusion(
        owner.parent, expected=owner.epoch.invocation
    )
    try:
        participant._finish_epoch_use(guard, use)
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(ContractViolation):
        validator.validate_dependency_scope_operation(use, expected=expected)
    impl._release_dependency_scope_operation(validator, use)
    with pytest.raises(ContractViolation):
        impl._retain_dependency_scope_operation(
            validator, use, expected=expected, purpose=stage
        )


def test_original_record_replacement_refuses(monkeypatch):
    _, _, participant, use, validator, expected = fixture(monkeypatch)
    tracker = epochs._state(participant)
    tracker.uses[use] = replace(tracker.uses[use])
    with pytest.raises(ContractViolation, match="substituted"):
        validator.validate_dependency_scope_operation(use, expected=expected)


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
def test_host_close_revokes_both_stage_contexts(monkeypatch, stage):
    _, host, _, use, validator, expected = fixture(monkeypatch, purpose=stage)
    direct_host.close_direct_validation_host(host)
    with pytest.raises(ContractViolation):
        validator.validate_dependency_scope_operation(use, expected=expected)
    impl._release_dependency_scope_operation(validator, use)


def test_wrong_thread_refuses(monkeypatch):
    _, _, _, use, validator, expected = fixture(monkeypatch)
    errors = []

    def run():
        try:
            validator.validate_dependency_scope_operation(use, expected=expected)
        except ContractViolation:
            errors.append(True)

    t = Thread(target=run)
    t.start()
    t.join()
    assert errors == [True]


def test_fork_process_refuses(monkeypatch):
    _, _, _, use, validator, expected = fixture(monkeypatch)
    monkeypatch.setattr(impl.os, "getpid", lambda: expected.process_id + 1)
    with pytest.raises(ContractViolation):
        validator.validate_dependency_scope_operation(use, expected=expected)


def test_validator_construction_and_method_substitution_refuse(monkeypatch):
    with pytest.raises(TypeError):
        impl.OriginalDependencyScopeOperationValidator()
    _, _, _, use, validator, expected = fixture(monkeypatch)
    original = validator.validate_dependency_scope_operation
    validator.validate_dependency_scope_operation = lambda *args, **kwargs: None
    with pytest.raises(ContractViolation):
        original(use, expected=expected)


def test_foreign_thread_cannot_adopt_already_running_use(monkeypatch):
    _, _, _, use, validator, expected = fixture(monkeypatch)
    impl._release_dependency_scope_operation(validator, use)
    errors = []

    def run():
        try:
            impl._retain_dependency_scope_operation(
                validator, use, expected=expected, purpose="source_planning"
            )
        except ContractViolation:
            errors.append(True)

    thread = Thread(target=run)
    thread.start()
    thread.join()
    assert errors == [True]


def test_shared_signatures_bind_existing_source_and_use():
    import inspect

    from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
        DependencyScopeOperationBinding,
        DependencyScopeOperationValidator,
    )

    for name in (
        "bind_dependency_scope_operation",
        "release_dependency_scope_operation",
    ):
        signature = inspect.signature(getattr(DependencyScopeOperationBinding, name))
        assert tuple(signature.parameters) == ("self", "source", "expected")
        assert signature.parameters["expected"].kind is inspect.Parameter.KEYWORD_ONLY
    signature = inspect.signature(
        DependencyScopeOperationValidator.validate_dependency_scope_operation
    )
    assert tuple(signature.parameters) == ("self", "operation", "expected")
