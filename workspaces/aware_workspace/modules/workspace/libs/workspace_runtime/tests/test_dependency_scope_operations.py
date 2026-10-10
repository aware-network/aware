"""Workspace owner mechanics with fixture Code origin; not host authentication."""

import os
from dataclasses import replace
from threading import Thread

import pytest
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeUnavailable
from aware_workspace_runtime.dependency_scope_adapter import (
    WorkspaceCodeDependencyScopeAdapter,
)
from aware_workspace_runtime.dependency_scope_operations import (
    _install_operation_origin,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from aware_workspace_runtime.source_observation import WorkspaceSourceObservationRuntime
from test_dependency_scope_admission import fixture


class FixtureValidator:
    def __init__(self):
        self.running = set()
        self.calls = 0
        self.action = None

    def validate_dependency_scope_operation(self, operation, *, expected):
        self.calls += 1
        if self.action:
            self.action()
        if operation not in self.running:
            raise SourceObservationUnavailable("fixture use ended")


def setup(owner, observation):
    source = owner.capture(
        observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
    )
    validator, epoch, operation = FixtureValidator(), object(), object()
    validator.running.add(operation)
    # Isolated mechanics only. Original Code host authentication is NOT supplied.
    expected = owner.prepare_dependency_scope_expectation(
        source,
        parent_identity=owner._exclusion._parent,
        epoch_identity=epoch,
        operation_identity=operation,
        process_id=os.getpid(),
    )
    _install_operation_origin(owner, validator=validator, epoch=epoch)
    return source, validator, expected


async def test_running_association_release_replay_and_fresh_use(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, observer, _, _):
        source, validator, expected = setup(owner, observation)
        adapter = WorkspaceCodeDependencyScopeAdapter(runtime=owner)
        with pytest.raises(SourceObservationUnavailable):
            adapter.read_dependency_scope_closure(source, expected=expected)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = adapter.read_dependency_scope_closure(
            source, expected=replace(expected)
        )
        owner.validate_dependency_scope_closure(
            source, expected=expected, closure_digest=value.closure_digest
        )
        with pytest.raises(SourceObservationUnavailable):
            owner.bind_dependency_scope_operation(source, expected=expected)
        owner.release_dependency_scope_operation(source, expected=expected)
        with pytest.raises(SourceObservationUnavailable):
            owner.bind_dependency_scope_operation(source, expected=expected)
        operation = object()
        validator.running.add(operation)
        fresh = replace(expected, operation_identity=operation)
        owner.bind_dependency_scope_operation(source, expected=fresh)
        owner.release_dependency_scope_operation(source, expected=fresh)
        observer.revalidate(observation)
        assert (
            owner.read_preliminary_closure(source).closure_digest
            == value.closure_digest
        )


async def test_validation_reuses_bound_digest_without_rebuilding_projection(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, _, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = owner.read_dependency_scope_closure(source, expected=expected)

        def unexpected_projection(*args, **kwargs):
            pytest.fail("operation validation rebuilt the complete projection")

        monkeypatch.setattr(owner, "_project", unexpected_projection)
        owner.validate_dependency_scope_closure(
            source, expected=expected, closure_digest=value.closure_digest
        )


async def test_validation_rejects_changed_source_without_projection_rebuild(
    tmp_path, monkeypatch
):
    async with fixture(tmp_path) as (root, owner, observation, _, _, _):
        source, _, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = owner.read_dependency_scope_closure(source, expected=expected)
        profile = (
            root
            / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
        )
        profile.write_text(profile.read_text() + "\n# changed during operation\n")
        monkeypatch.setattr(
            owner,
            "_project",
            lambda *args, **kwargs: pytest.fail("projection rebuild is not allowed"),
        )
        with pytest.raises(SourceObservationUnavailable):
            owner.validate_dependency_scope_closure(
                source, expected=expected, closure_digest=value.closure_digest
            )


async def test_operation_validation_batches_shared_observation_currentness(
    tmp_path, monkeypatch
):
    calls = 0
    original = WorkspaceSourceObservationRuntime.revalidate

    def counted(runtime, handle):
        nonlocal calls
        calls += 1
        return original(runtime, handle)

    monkeypatch.setattr(WorkspaceSourceObservationRuntime, "revalidate", counted)
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, _, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = owner.read_dependency_scope_closure(source, expected=expected)
        calls = 0
        owner.validate_dependency_scope_closure(
            source, expected=expected, closure_digest=value.closure_digest
        )
        assert calls == 1


@pytest.mark.parametrize(
    "field",
    [
        "parent_identity",
        "epoch_identity",
        "operation_identity",
        "process_id",
        "repository_membership_identity",
        "closure_runtime_identity",
        "consumer_scope_key",
    ],
)
async def test_context_substitution(tmp_path, field):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, _, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = (
            expected.process_id + 1
            if field == "process_id"
            else "other"
            if field == "consumer_scope_key"
            else object()
        )
        with pytest.raises(SourceObservationUnavailable):
            owner.read_dependency_scope_closure(
                source, expected=replace(expected, **{field: value})
            )


async def test_locked_check_has_no_validator_or_source_io(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, validator, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        value = owner.read_dependency_scope_closure(source, expected=expected)
        calls = validator.calls
        validator.action = lambda: pytest.fail("Code callback under guard")
        original_call = owner._call

        def checked_call(receiver, name, *args, **kwargs):
            assert name == "_check_record_locked", (
                "unexpected full source work under guard"
            )
            return original_call(receiver, name, *args, **kwargs)

        monkeypatch.setattr(owner, "_call", checked_call)
        # A locked check alone never revalidates Code. The host must check its use separately.
        with owner._exclusion.mutation() as guard:
            owner.check_dependency_scope_closure_locked(
                source,
                expected=expected,
                closure_digest=value.closure_digest,
                guard=guard,
            )
        monkeypatch.setattr(owner, "_call", original_call)
        assert validator.calls == calls
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            owner.check_dependency_scope_closure_locked(
                source,
                expected=expected,
                closure_digest=value.closure_digest,
                guard=guard,
            )


@pytest.mark.parametrize(
    "change", ["use_end", "source_retire", "epoch_close", "profile", "validator"]
)
async def test_revocation_and_cleanup(tmp_path, change):
    async with fixture(tmp_path) as (root, owner, observation, _, _, lifetime):
        source, validator, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        if change == "use_end":
            validator.running.clear()
        elif change == "source_retire":
            owner.release(source)
        elif change == "epoch_close":
            lifetime.close()
        elif change == "profile":
            p = (
                root
                / "target/semantic_contract/profiles/arbitrary.profile/aware.semantic_contract_profile.toml"
            )
            p.write_text(p.read_text() + "\n# changed\n")
        else:
            validator.validate_dependency_scope_operation = lambda *a, **k: None
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            owner.read_dependency_scope_closure(source, expected=expected)
        owner.release_dependency_scope_operation(source, expected=expected)
        assert not owner._operation_origin.active


async def test_cross_thread_read_and_cleanup_refuse(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, _, expected = setup(owner, observation)
        owner.bind_dependency_scope_operation(source, expected=expected)
        errors = []

        def run():
            for method in (
                owner.read_dependency_scope_closure,
                owner.release_dependency_scope_operation,
            ):
                try:
                    method(source, expected=expected)
                except SourceObservationUnavailable:
                    errors.append(True)

        thread = Thread(target=run)
        thread.start()
        thread.join()
        assert errors == [True, True]


async def test_callback_retirement_cannot_publish_association(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, validator, expected = setup(owner, observation)
        validator.action = lambda: owner.release(source)
        with pytest.raises(SourceObservationUnavailable):
            owner.bind_dependency_scope_operation(source, expected=expected)
        assert not owner._operation_origin.active


async def test_preparation_is_input_only_without_validator_or_association(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        epoch, use = object(), object()  # deliberately NOT original Code authority
        expected = owner.prepare_dependency_scope_expectation(
            source,
            parent_identity=owner._exclusion._parent,
            epoch_identity=epoch,
            operation_identity=use,
            process_id=os.getpid(),
        )
        assert type(expected) is RetainedDependencyScopeExpectation
        assert expected.repository_membership_identity is observation
        assert expected.closure_runtime_identity is owner
        assert expected.consumer_scope_key == "consumer/aware.workspace.toml"
        assert expected.epoch_identity is epoch and expected.operation_identity is use
        assert owner._operation_origin is None
        with pytest.raises(SourceObservationUnavailable):
            owner.bind_dependency_scope_operation(source, expected=expected)
        with pytest.raises(SourceObservationUnavailable):
            owner.read_dependency_scope_closure(source, expected=expected)


async def test_preparation_never_invokes_even_an_installed_validator(tmp_path):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source, validator, expected = setup(owner, observation)
        validator.action = lambda: pytest.fail(
            "preparation called Code before context retention"
        )
        result = owner.prepare_dependency_scope_expectation(
            source,
            parent_identity=expected.parent_identity,
            epoch_identity=expected.epoch_identity,
            operation_identity=expected.operation_identity,
            process_id=expected.process_id,
        )
        assert result is not expected
        assert validator.calls == 0 and not owner._operation_origin.active


@pytest.mark.parametrize(
    "field",
    [
        "parent_identity",
        "epoch_identity",
        "operation_identity",
        "process_id",
        "boolean_process",
    ],
)
async def test_preparation_refuses_invalid_coordinate_proposals(tmp_path, field):
    async with fixture(tmp_path) as (_, owner, observation, _, _, _):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        args = dict(
            parent_identity=owner._exclusion._parent,
            epoch_identity=object(),
            operation_identity=object(),
            process_id=os.getpid(),
        )
        if field == "boolean_process":
            args["process_id"] = True
        else:
            args[field] = (
                object()
                if field == "parent_identity"
                else os.getpid() + 1
                if field == "process_id"
                else None
            )
        with pytest.raises(SourceObservationUnavailable):
            owner.prepare_dependency_scope_expectation(source, **args)


@pytest.mark.parametrize("change", ["bytes", "released", "parent_closed"])
async def test_preparation_requires_original_current_source(tmp_path, change):
    async with fixture(tmp_path) as (root, owner, observation, _, _, lifetime):
        source = owner.capture(
            observation=observation, consumer_scope_key="consumer/aware.workspace.toml"
        )
        if change == "bytes":
            p = root / "consumer/aware.workspace.toml"
            p.write_text(p.read_text() + "\n# changed\n")
        elif change == "released":
            owner.release(source)
        else:
            lifetime.close()
        with pytest.raises(
            (SourceObservationUnavailable, WorkspaceCommandLifetimeUnavailable)
        ):
            owner.prepare_dependency_scope_expectation(
                source,
                parent_identity=owner._exclusion._parent,
                epoch_identity=object(),
                operation_identity=object(),
                process_id=os.getpid(),
            )
