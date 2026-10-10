"""Original Code operation consumer, fixture source owner; no bootstrap proof."""

# Nested contexts expose lifecycle boundaries under test.
# ruff: noqa: SIM117

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import (
    dependency_scope_operation as ops,
)
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime.dependency_source_binding import (
    _bind_dependency_source,
    _capture_dependency_source,
)
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _guard,
    _policy_epoch_use,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)
from test_direct_epoch_tracking import setup as host_setup
from test_profile_membership import fixture as closure_fixture


class SourceOwner:
    def __init__(self):
        self.source = object()
        self.membership = object()
        self.closure = closure_fixture()
        self.active = {}
        self.events = []
        self.rewrite = lambda x: x
        self.fail_release = False

    def prepare_dependency_scope_expectation(self, source, **coordinates):
        assert source is self.source
        self.events.append("prepare")
        return self.rewrite(
            RetainedDependencyScopeExpectation(
                **coordinates,
                repository_membership_identity=self.membership,
                closure_runtime_identity=self,
                consumer_scope_key=self.closure.consumer_scope_key,
            )
        )

    def bind_dependency_scope_operation(self, source, *, expected):
        assert source is self.source
        self.validator.validate_dependency_scope_operation(
            expected.operation_identity, expected=expected
        )
        assert expected.operation_identity not in self.active
        self.events.append("bind")
        self.active[expected.operation_identity] = expected

    def release_dependency_scope_operation(self, source, *, expected):
        self.events.append("release")
        if self.fail_release:
            raise ValueError("release failed")
        assert source is self.source
        self.active.pop(expected.operation_identity)

    def validate_dependency_scope_closure(
        self, source, *, expected, closure_digest=None
    ):
        assert source is self.source
        assert self.active[expected.operation_identity] is expected
        self.validator.validate_dependency_scope_operation(
            expected.operation_identity, expected=expected
        )
        if closure_digest is not None and closure_digest != self.closure.closure_digest:
            raise ContractViolation("changed closure")

    def read_dependency_scope_closure(self, source, *, expected):
        self.validate_dependency_scope_closure(source, expected=expected)
        return self.closure

    def check_dependency_scope_closure_locked(
        self, source, *, expected, closure_digest, guard
    ):
        assert guard is not None
        assert source is self.source
        assert self.active[expected.operation_identity] is expected
        assert self.closure.closure_digest == closure_digest


def setup(monkeypatch):
    source = SourceOwner()
    original = hosts._assemble_direct_command_bootstrap

    def assemble(*, lifetime, expected):
        # Fixture composition retains the source before host creation. This is not
        # the qualified fixed application's bootstrap authentication.
        object.__setattr__(
            expected,
            "resources",
            tuple(
                replace(b, resource=source) if b.role == "scope_runtime" else b
                for b in expected.resources
            ),
        )
        return original(lifetime=lifetime, expected=expected)

    monkeypatch.setattr(hosts, "_assemble_direct_command_bootstrap", assemble)
    owner, host, participant = host_setup(monkeypatch)
    validator = ops._create_dependency_scope_operation_validator(host)
    source.validator = validator
    retained = _capture_dependency_source(validator, source.source)
    return owner, host, participant, source, retained


@pytest.mark.parametrize(
    "purpose",
    [
        "policy_calculation",
        "policy_validation",
        "source_planning",
        "authority_derivation",
    ],
)
def test_prepare_retain_bind_read_release_on_original_use(monkeypatch, purpose):
    _, host, participant, source, retained = setup(monkeypatch)
    with _policy_epoch_use(host) as (binding, use):
        with _bind_dependency_source(retained, use, purpose=purpose) as bound:
            value = bound.read()
            with _guard(binding) as guard:
                bound.check_locked(closure_digest=value.closure_digest, guard=guard)
            assert use in ops._STATES[retained.validator].operations
        assert use not in ops._STATES[retained.validator].operations
        assert use in participant_state(participant).uses
    assert not participant_state(participant).uses
    assert not source.active
    assert source.events == ["prepare", "bind", "release"]


def participant_state(participant):
    from aware_code_retained_registry_policy_runtime.epoch_participation import _state

    return _state(participant)


@pytest.mark.parametrize(
    "field",
    [
        "parent_identity",
        "epoch_identity",
        "operation_identity",
        "process_id",
        "closure_runtime_identity",
    ],
)
def test_prepared_coordinate_substitution_rejects_before_bind(monkeypatch, field):
    _, host, _, source, retained = setup(monkeypatch)
    source.rewrite = lambda e: replace(
        e, **{field: e.process_id + 1 if field == "process_id" else object()}
    )
    with (
        _policy_epoch_use(host) as (_, use),
        pytest.raises((ContractViolation, TypeError)),
    ):
        with _bind_dependency_source(retained, use, purpose="source_planning"):
            pytest.fail("substitution admitted")
    assert source.events == ["prepare"]
    assert not ops._STATES[retained.validator].operations


def test_original_release_runs_after_body_and_method_failure(monkeypatch):
    _, host, _, source, retained = setup(monkeypatch)
    with pytest.raises(BaseExceptionGroup), _policy_epoch_use(host) as (_, use):
        with _bind_dependency_source(retained, use, purpose="authority_derivation"):
            source.release_dependency_scope_operation = lambda *a, **kw: pytest.fail(
                "replacement invoked"
            )
            raise ValueError("body failed")
    assert source.events[-1] == "release"
    assert not source.active
    assert not ops._STATES[retained.validator].operations


def test_source_cleanup_failure_leaves_obligation(monkeypatch):
    _, host, participant, source, retained = setup(monkeypatch)
    source.fail_release = True
    with (
        pytest.raises(ValueError, match="release failed") as failure,
        _policy_epoch_use(host) as (_, use),
    ):
        with _bind_dependency_source(retained, use, purpose="authority_derivation"):
            pass
    assert isinstance(failure.value.__cause__, ContractViolation)
    assert participant_state(participant).uses[use].status == "uncertain"
    assert not ops._STATES[retained.validator].operations


def test_retained_reader_rejects_digest_change(monkeypatch):
    _, host, _, source, retained = setup(monkeypatch)
    with _policy_epoch_use(host) as (_, use):
        with _bind_dependency_source(retained, use, purpose="source_planning") as bound:
            value = bound.read()
            source.closure = replace(
                value, consumer_scope_key=value.scopes[-1].scope_key
            )
            with pytest.raises(ContractViolation):
                bound.read(closure_digest=value.closure_digest)


def test_finished_bound_reader_cannot_reenter(monkeypatch):
    _, host, _, _, retained = setup(monkeypatch)
    with _policy_epoch_use(host) as (_, use):
        with _bind_dependency_source(retained, use, purpose="source_planning") as bound:
            bound.read()
    with pytest.raises((ContractViolation, KeyError)):
        bound.read()


def test_partial_bind_failure_still_releases_original_association(monkeypatch):
    original = SourceOwner.bind_dependency_scope_operation

    def partial(self, source, *, expected):
        original(self, source, expected=expected)
        raise ValueError("partial bind failed")

    monkeypatch.setattr(SourceOwner, "bind_dependency_scope_operation", partial)
    _, host, participant, source, retained = setup(monkeypatch)
    with (
        pytest.raises(ValueError, match="partial bind failed"),
        _policy_epoch_use(host) as (_, use),
    ):
        with _bind_dependency_source(retained, use, purpose="source_planning"):
            pytest.fail("partial bind admitted")
    assert not source.active
    assert not ops._STATES[retained.validator].operations
    assert not participant_state(participant).uses


def test_code_cleanup_failure_preserves_publication_obligation(monkeypatch):
    _, host, participant, source, retained = setup(monkeypatch)

    def fail(*args):
        raise ValueError("Code retirement failed")

    monkeypatch.setattr(ops, "_release_dependency_scope_operation", fail)
    with (
        pytest.raises(ValueError, match="Code retirement failed"),
        _policy_epoch_use(host) as (_, use),
    ):
        with _bind_dependency_source(retained, use, purpose="authority_derivation"):
            pass
    assert not source.active
    assert use in ops._STATES[retained.validator].operations
    assert participant_state(participant).uses[use].status == "uncertain"
