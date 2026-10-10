"""Lifetime mechanics with inert context markers; no trusted bootstrap claim."""

import copy
import os
import pickle
import threading
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
    RetainedSemanticStageRuntimeExpectation,
)
from aware_workspace_runtime import (
    WorkspaceCommandLifetime,
    WorkspaceCommandLifetimeRuntime,
)
from aware_workspace_runtime import (
    WorkspaceCommandLifetimeUnavailable as Refused,
)
from aware_workspace_runtime.command_lifetime import WorkspaceDirectInvocationParent


def assembled(owner=None):
    owner = owner or WorkspaceCommandLifetimeRuntime()
    resources = {role: object() for role in RESOURCE_ROLES}
    resources["lifetime_runtime"] = owner
    digest = ContentDigest.of_bytes(b"isolated mechanics")
    expected = DirectCommandExpectedContext(
        owner.invocation_identity,
        owner.epoch_identity,
        os.getpid(),
        resources["code_runtime"],
        resources["catalog"],
        SemanticImplementationCoordinate("composition", digest),
        SemanticConfigurationCoordinate("composition", digest),
        SemanticImplementationCoordinate("policy", digest),
        SemanticConfigurationCoordinate("policy", digest),
        tuple(
            DirectCommandResourceBinding(r, resources[r], "borrowed")
            for r in RESOURCE_ROLES
        ),
    )
    return owner, expected, owner.bind_command_lifetime(expected=expected)


def test_nominal_once_and_terminal():
    owner, expected, lifetime = assembled()
    owner.validate_command_lifetime(lifetime, expected=replace(expected))
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(lifetime)
    with pytest.raises(Refused):
        owner.bind_command_lifetime(expected=expected)
    with pytest.raises(Refused):
        owner.validate_command_lifetime(
            object.__new__(WorkspaceCommandLifetime), expected=expected
        )
    owner.close()
    owner.close()
    with pytest.raises(Refused):
        owner.validate_command_lifetime(lifetime, expected=expected)
    with pytest.raises(Refused):
        owner.bind_command_lifetime(expected=expected)


@pytest.mark.parametrize("role", RESOURCE_ROLES)
def test_resource_substitution(role):
    owner, expected, lifetime = assembled()
    resources = tuple(
        replace(b, resource=object()) if b.role == role else b
        for b in expected.resources
    )
    changes = {"resources": resources}
    if role == "code_runtime":
        changes["runtime"] = next(b.resource for b in resources if b.role == role)
    if role == "catalog":
        changes["catalog"] = next(b.resource for b in resources if b.role == role)
    with pytest.raises(Refused):
        owner.validate_command_lifetime(lifetime, expected=replace(expected, **changes))
    owner.close()


@pytest.mark.parametrize(
    "field",
    [
        "invocation_identity",
        "epoch_identity",
        "process_id",
        "composition_configuration",
    ],
)
def test_context_substitution(field):
    owner, expected, lifetime = assembled()
    value = object()
    if field == "process_id":
        value = os.getpid() + 1
    if field == "composition_configuration":
        value = SemanticConfigurationCoordinate(
            "changed", ContentDigest.of_bytes(b"changed")
        )
    with pytest.raises(Refused):
        owner.validate_command_lifetime(
            lifetime, expected=replace(expected, **{field: value})
        )
    owner.close()


def test_guard_thread_replay_and_close():
    owner, expected, lifetime = assembled()
    guard = owner.acquire_command_publication_guard(lifetime, expected=expected)
    errors = []

    def foreign():
        for operation in (
            lambda: owner.release_command_publication_guard(guard),
            lambda: owner.validate_command_publication_guard(
                guard, lifetime=lifetime, expected=expected
            ),
        ):
            try:
                operation()
            except Refused:
                errors.append(True)

    thread = threading.Thread(target=foreign)
    thread.start()
    thread.join(2)
    assert not thread.is_alive() and len(errors) == 2
    with pytest.raises(Refused):
        owner.acquire_command_publication_guard(lifetime, expected=expected)
    owner.validate_command_publication_guard(
        guard, lifetime=lifetime, expected=expected
    )
    owner.close()  # same-thread close revokes even inside the reentrant guard
    with pytest.raises(Refused):
        owner.validate_command_publication_guard(
            guard, lifetime=lifetime, expected=expected
        )
    owner.release_command_publication_guard(guard)
    with pytest.raises(Refused):
        owner.release_command_publication_guard(guard)


def test_publication_then_close_serializes():
    owner, expected, lifetime = assembled()
    guard = owner.acquire_command_publication_guard(lifetime, expected=expected)
    started, finished = threading.Event(), threading.Event()

    def closer():
        started.set()
        owner.close()
        finished.set()

    thread = threading.Thread(target=closer)
    thread.start()
    assert started.wait(2)
    try:
        assert not finished.is_set()
        owner.validate_command_publication_guard(
            guard, lifetime=lifetime, expected=expected
        )
    finally:
        owner.release_command_publication_guard(guard)
    thread.join(2)
    assert finished.is_set()
    with pytest.raises(Refused):
        owner.acquire_command_publication_guard(lifetime, expected=expected)


def test_failed_acquire_and_exception_release_unwind():
    owner, expected, lifetime = assembled()
    with pytest.raises(Refused):
        owner.acquire_command_publication_guard(
            lifetime, expected=replace(expected, epoch_identity=object())
        )
    with pytest.raises(KeyboardInterrupt):
        guard = owner.acquire_command_publication_guard(lifetime, expected=expected)
        try:
            raise KeyboardInterrupt
        finally:
            owner.release_command_publication_guard(guard)
    thread = threading.Thread(target=owner.close)
    thread.start()
    thread.join(2)
    assert not thread.is_alive()


def test_fork_refuses_before_inherited_lock(monkeypatch):
    owner, expected, lifetime = assembled()
    monkeypatch.setattr(os, "getpid", lambda: -1)
    with pytest.raises(Refused, match="process_changed"):
        owner.acquire_command_publication_guard(lifetime, expected=expected)
    with pytest.raises(Refused, match="process_changed"):
        owner.close()


def test_mutating_detached_expected_cannot_restamp_binding():
    owner, expected, lifetime = assembled()
    object.__setattr__(
        expected.composition_configuration, "configuration_ref", "changed"
    )
    with pytest.raises(Refused):
        owner.validate_command_lifetime(lifetime, expected=expected)


def test_foreign_owner_and_fresh_epoch_reject_old_lifetime():
    first, old_context, old_lifetime = assembled()
    second, new_context, new_lifetime = assembled()
    with pytest.raises(Refused):
        second.validate_command_lifetime(old_lifetime, expected=new_context)
    first.close()
    with pytest.raises(Refused):
        first.validate_command_lifetime(new_lifetime, expected=old_context)
    second.close()


# Epoch-parent mechanics use the same original runtime and exclusion as legacy
# full-context publication. Context markers remain explicitly isolated fixtures.


def parent_assembly():
    owner = WorkspaceCommandLifetimeRuntime()
    parent = owner._retain_direct_invocation_parent()
    expected = DirectInvocationExpectation(
        owner.invocation_identity, owner.epoch_identity, os.getpid()
    )
    return owner, parent, expected


def test_parent_before_catalog_and_once_only_full_correspondence():
    owner, parent, invocation = parent_assembly()
    owner.validate_direct_invocation_parent(parent, expected=replace(invocation))
    assert owner._lifetime is None
    _, expected, lifetime = assembled(owner)
    owner.validate_direct_invocation_context_binding(
        parent, lifetime, invocation=invocation, expected=expected
    )
    with pytest.raises(Refused):
        owner._retain_direct_invocation_parent()
    with pytest.raises(Refused):
        owner.bind_command_lifetime(expected=expected)
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(parent)
    with pytest.raises(Refused):
        owner.validate_direct_invocation_parent(
            object.__new__(WorkspaceDirectInvocationParent), expected=invocation
        )
    foreign, foreign_parent, _ = parent_assembly()
    with pytest.raises(Refused):
        foreign.validate_direct_invocation_parent(parent, expected=invocation)
    with pytest.raises(Refused):
        owner.validate_direct_invocation_context_binding(
            foreign_parent, lifetime, invocation=invocation, expected=expected
        )


def test_direct_source_operation_coordinates_are_once_only_and_parent_bound():
    owner, parent, expected = parent_assembly()
    operation, parent_ref, epoch_ref = owner.issue_direct_source_operation_coordinates(
        parent, expected=expected
    )
    assert operation.startswith("workspace-materialize-operation:")
    assert parent_ref.startswith("workspace-command-parent:")
    assert epoch_ref.startswith("workspace-command-epoch:")
    with pytest.raises(Refused, match="already_issued"):
        owner.issue_direct_source_operation_coordinates(parent, expected=expected)
    foreign, foreign_parent, foreign_expected = parent_assembly()
    with pytest.raises(Refused, match="parent_not_live"):
        foreign.issue_direct_source_operation_coordinates(parent, expected=foreign_expected)
    with pytest.raises(Refused, match="context_differs"):
        owner.issue_direct_source_operation_coordinates(
            parent, expected=replace(expected, lifetime_epoch_identity=object())
        )
    owner.close()
    with pytest.raises(Refused, match="parent_not_live"):
        owner.issue_direct_source_operation_coordinates(parent, expected=expected)
    foreign.close()


@pytest.mark.parametrize(
    "field", ["invocation_identity", "lifetime_epoch_identity", "process_id"]
)
def test_parent_expected_substitution(field):
    owner, parent, expected = parent_assembly()
    bad = replace(expected, **{field: False if field == "process_id" else object()})
    with pytest.raises(Refused):
        owner.acquire_catalog_epoch_exclusion(parent, expected=bad)
    # A failed acquire must release the lock.
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    owner.release_catalog_epoch_exclusion(guard)


def test_both_guard_entrances_share_exclusion_and_reject_cross_release():
    owner, parent, invocation = parent_assembly()
    _, expected, lifetime = assembled(owner)
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    owner.validate_catalog_epoch_exclusion(guard, parent=parent, expected=invocation)
    with pytest.raises(Refused):
        owner.acquire_command_publication_guard(lifetime, expected=expected)
    with pytest.raises(Refused):
        owner.release_command_publication_guard(guard)
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(guard)
    owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(Refused):
        owner.release_catalog_epoch_exclusion(guard)
    old_guard = owner.acquire_command_publication_guard(lifetime, expected=expected)
    with pytest.raises(Refused):
        owner.acquire_catalog_epoch_exclusion(parent, expected=invocation)
    with pytest.raises(Refused):
        owner.release_catalog_epoch_exclusion(old_guard)
    owner.release_command_publication_guard(old_guard)


def test_epoch_guard_release_after_close_and_wrong_thread():
    owner, parent, expected = parent_assembly()
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    errors = []

    def foreign_release():
        try:
            owner.release_catalog_epoch_exclusion(guard)
        except Refused as error:
            errors.append(error)

    thread = threading.Thread(target=foreign_release)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive() and len(errors) == 1
    owner.close()
    with pytest.raises(Refused):
        owner.validate_catalog_epoch_exclusion(guard, parent=parent, expected=expected)
    owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(Refused):
        owner.acquire_catalog_epoch_exclusion(parent, expected=expected)


def test_parent_fork_check_precedes_lock(monkeypatch):
    owner, parent, expected = parent_assembly()

    class ForbiddenLock:
        def acquire(self):
            pytest.fail("forked runtime touched inherited lock")

        def __enter__(self):
            pytest.fail("forked runtime touched inherited lock")

    monkeypatch.setattr(owner, "_lock", ForbiddenLock())
    monkeypatch.setattr(os, "getpid", lambda: expected.process_id + 1)
    with pytest.raises(Refused):
        owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    with pytest.raises(Refused):
        owner.validate_direct_invocation_parent(parent, expected=expected)


def test_epoch_guard_serializes_other_thread_close():
    owner, parent, expected = parent_assembly()
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    attempted = threading.Event()
    closed = threading.Event()

    def close():
        attempted.set()
        owner.close()
        closed.set()

    thread = threading.Thread(target=close)
    thread.start()
    try:
        assert attempted.wait(timeout=2)
        assert not closed.is_set()
        owner.validate_catalog_epoch_exclusion(guard, parent=parent, expected=expected)
    finally:
        owner.release_catalog_epoch_exclusion(guard)
        thread.join(timeout=2)
    assert not thread.is_alive() and closed.is_set()
    with pytest.raises(Refused):
        owner.acquire_catalog_epoch_exclusion(parent, expected=expected)


class _NoLockAccess:
    def __enter__(self):
        raise AssertionError("locked validation reacquired an owner lock")

    def acquire(self, *args, **kwargs):
        raise AssertionError("locked validation acquired an owner lock")


def test_epoch_guard_validation_is_in_place_and_keeps_context_checks(monkeypatch):
    owner, parent, expected = parent_assembly()
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(owner, "_lock", _NoLockAccess())
            owner.validate_catalog_epoch_exclusion(
                guard, parent=parent, expected=expected
            )
            for field in (
                "invocation_identity",
                "lifetime_epoch_identity",
                "process_id",
            ):
                bad = replace(
                    expected, **{field: False if field == "process_id" else object()}
                )
                with pytest.raises(Refused, match="context_differs"):
                    owner.validate_catalog_epoch_exclusion(
                        guard, parent=parent, expected=bad
                    )
            with pytest.raises(Refused, match="parent_not_live"):
                owner.validate_catalog_epoch_exclusion(
                    guard,
                    parent=object.__new__(WorkspaceDirectInvocationParent),
                    expected=expected,
                )
            with pytest.raises(Refused, match="guard_foreign"):
                owner.validate_catalog_epoch_exclusion(
                    object(), parent=parent, expected=expected
                )
            patch.setattr(owner, "_closed", True)
            with pytest.raises(Refused, match="parent_not_live"):
                owner.validate_catalog_epoch_exclusion(
                    guard, parent=parent, expected=expected
                )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    with pytest.raises(Refused, match="guard_foreign"):
        owner.validate_catalog_epoch_exclusion(guard, parent=parent, expected=expected)


def test_parent_close_waits_for_original_guard_and_then_revokes():
    owner, parent, expected = parent_assembly()
    guard = owner.acquire_catalog_epoch_exclusion(parent, expected=expected)
    started = threading.Event()
    finished = threading.Event()

    def retire():
        started.set()
        owner.close()
        finished.set()

    worker = threading.Thread(target=retire)
    worker.start()
    try:
        assert started.wait(2)
        assert not finished.wait(0.05)
        owner.validate_catalog_epoch_exclusion(guard, parent=parent, expected=expected)
    finally:
        owner.release_catalog_epoch_exclusion(guard)
        worker.join(2)
    assert not worker.is_alive()
    assert finished.is_set()
    with pytest.raises(Refused, match="parent_not_live"):
        owner.validate_direct_invocation_parent(parent, expected=expected)


def two_stage_expected(expected):
    authority = object()
    return replace(
        expected,
        resources=(
            DirectCommandResourceBinding(
                "authority_code_runtime", authority, "borrowed"
            ),
            *expected.resources,
        ),
        stage_runtime_bindings=(
            RetainedSemanticStageRuntimeExpectation(
                "source_planning", expected.runtime, object()
            ),
            RetainedSemanticStageRuntimeExpectation(
                "authority_derivation", authority, object()
            ),
        ),
    )


@pytest.mark.parametrize("stage_index", (0, 1))
def test_two_stage_nested_registration_substitution(stage_index):
    source_owner, source, _ = assembled()
    source_owner.close()
    owner = WorkspaceCommandLifetimeRuntime()
    expected = two_stage_expected(
        replace(
            source,
            invocation_identity=owner.invocation_identity,
            epoch_identity=owner.epoch_identity,
            resources=tuple(
                replace(b, resource=owner) if b.role == "lifetime_runtime" else b
                for b in source.resources
            ),
        )
    )
    lifetime = owner.bind_command_lifetime(expected=expected)
    owner.validate_command_lifetime(lifetime, expected=replace(expected))
    object.__setattr__(
        expected.stage_runtime_bindings[stage_index], "registration", object()
    )
    with pytest.raises(Refused, match="context_substituted"):
        owner.validate_command_lifetime(lifetime, expected=expected)
    owner.close()


def test_two_stage_late_attachment_refused():
    owner, expected, lifetime = assembled()
    with pytest.raises(Refused, match="context_substituted"):
        owner.validate_command_lifetime(lifetime, expected=two_stage_expected(expected))
    owner.validate_command_lifetime(lifetime, expected=expected)
    owner.close()


@pytest.mark.parametrize("change", ("runtime", "disposition", "remove", "close"))
def test_two_stage_resource_and_lifetime_changes_refuse(change):
    source_owner, source, _ = assembled()
    source_owner.close()
    owner = WorkspaceCommandLifetimeRuntime()
    expected = two_stage_expected(
        replace(
            source,
            invocation_identity=owner.invocation_identity,
            epoch_identity=owner.epoch_identity,
            resources=tuple(
                replace(b, resource=owner) if b.role == "lifetime_runtime" else b
                for b in source.resources
            ),
        )
    )
    lifetime = owner.bind_command_lifetime(expected=expected)
    if change == "runtime":
        replacement = object()
        expected = replace(
            expected,
            resources=(
                replace(expected.resources[0], resource=replacement),
                *expected.resources[1:],
            ),
            stage_runtime_bindings=(
                expected.stage_runtime_bindings[0],
                replace(expected.stage_runtime_bindings[1], runtime=replacement),
            ),
        )
    elif change == "disposition":
        expected = replace(
            expected,
            resources=(
                replace(expected.resources[0], disposition="owned"),
                *expected.resources[1:],
            ),
        )
    elif change == "remove":
        expected = replace(
            expected, resources=expected.resources[1:], stage_runtime_bindings=()
        )
    else:
        owner.close()
    with pytest.raises(Refused):
        owner.validate_command_lifetime(lifetime, expected=expected)
    owner.close()
