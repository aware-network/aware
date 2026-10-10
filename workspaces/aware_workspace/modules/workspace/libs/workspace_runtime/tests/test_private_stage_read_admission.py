"""Isolated refusal mechanics: no fixture supplies V5 or Meta authority."""

import copy
import os
from dataclasses import dataclass
from threading import get_ident
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime import private_stage_read_admission as reads
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeRuntime
from aware_workspace_runtime.source_exclusion import WorkspaceSourceExclusion


@dataclass
class _Sources:
    exclusion: WorkspaceSourceExclusion


@pytest.fixture
def local_family(monkeypatch):
    owner = WorkspaceCommandLifetimeRuntime()
    parent = owner._retain_direct_invocation_parent()
    expected = DirectInvocationExpectation(owner.invocation_identity, owner.epoch_identity, os.getpid())
    exclusion = WorkspaceSourceExclusion(runtime=owner, parent=parent, expected=expected)
    command = composition._DirectWorkspaceCommandResources(owner, parent, _Sources(exclusion), object())
    composition._COMMAND_ASSEMBLIES[owner] = (
        command, composition._resource_references(command), composition._resource_references(command.sources),
    )
    factory = object.__new__(composition._DirectWorkspaceOriginFactory)
    factory._owner, factory._command, factory._joint = owner, command, command.catalog_host
    composition._ORIGIN_FACTORIES.add(factory)
    factory._private_reads = reads._assemble_private_stage_read_runtime(factory)
    use = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    composition._COMMAND_NODE_SESSIONS[use] = composition._CommandNodeSourceSessionRecord(
        command, object(), object(), os.getpid(), get_ident()
    )
    events = []
    monkeypatch.setattr(composition, "_validate_command_owned_graph_node_source", lambda *_: events.append("source"))
    from aware_workspace_runtime import materialization_operation
    monkeypatch.setattr(materialization_operation, "_graph_node_admission_state", lambda _: SimpleNamespace(owner=owner))
    try:
        yield factory, use, expected, events
    finally:
        factory._private_reads.close()
        use.close()
        composition._COMMAND_ASSEMBLIES.pop(owner, None)
        owner.close()


@pytest.mark.parametrize("method", ("validate_private_stage_input_use", "prepare_private_stage_read_input"))
def test_source_liveness_cannot_substitute_for_v5(local_family, method):
    factory, use, _, events = local_family
    with pytest.raises(RuntimeError, match="v5_approval_unavailable"):
        getattr(factory, method)(use, object())
    assert events == ["source"]
    assert use not in composition._COMMAND_NODE_SESSIONS
    with pytest.raises(RuntimeError, match="family terminal"):
        getattr(factory, method)(use, object())
    assert factory.abort_private_stage_read_input(use) is None
    assert events == ["source"]


@pytest.mark.parametrize("method", ("check_private_stage_input_use_locked", "spend_private_stage_read_input_locked"))
def test_locked_refusal_has_no_io(local_family, method):
    factory, use, expected, events = local_family
    owner = factory._owner
    value = object()
    factory._private_reads._family(use, value)
    guard = owner.acquire_catalog_epoch_exclusion(factory._command.invocation_parent, expected=expected)
    try:
        args = (use, value, guard) if method.startswith("spend") else (use, value)
        with pytest.raises(RuntimeError, match="v5_approval_unavailable"):
            getattr(factory, method)(*args)
        assert owner._guard is guard
        assert events == []
        assert use not in composition._COMMAND_NODE_SESSIONS
    finally:
        owner.release_catalog_epoch_exclusion(guard)


def test_wrong_guard_terminalizes_without_io(local_family):
    factory, use, _, events = local_family
    value = object()
    factory._private_reads._family(use, value)
    with pytest.raises(RuntimeError, match="command_guard_foreign"):
        factory.spend_private_stage_read_input_locked(use, value, object())
    assert events == []
    assert use not in composition._COMMAND_NODE_SESSIONS


def test_locked_call_cannot_create_preparation(local_family):
    factory, use, expected, events = local_family
    owner = factory._owner
    guard = owner.acquire_catalog_epoch_exclusion(
        factory._command.invocation_parent, expected=expected
    )
    try:
        with pytest.raises(RuntimeError, match="preparation_unavailable"):
            factory.spend_private_stage_read_input_locked(use, object(), guard)
        assert not reads._RUNTIMES[factory._private_reads].families
        assert events == []
        assert use not in composition._COMMAND_NODE_SESSIONS
    finally:
        owner.release_catalog_epoch_exclusion(guard)


def test_full_validation_under_guard_refuses_before_io(local_family):
    factory, use, expected, events = local_family
    owner = factory._owner
    guard = owner.acquire_catalog_epoch_exclusion(factory._command.invocation_parent, expected=expected)
    try:
        with pytest.raises(RuntimeError, match="released guard"):
            factory.prepare_private_stage_read_input(use, object())
        assert events == []
    finally:
        owner.release_catalog_epoch_exclusion(guard)


class Hostile:
    def __getattribute__(self, _name):
        pytest.fail("foreign attribute accessed")

    def __eq__(self, _other):
        pytest.fail("foreign equality invoked")

    def __hash__(self) -> int:
        raise AssertionError("foreign object hashed")


class _RestampedUse:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    __getattribute__ = Hostile.__getattribute__
    __eq__ = Hostile.__eq__
    __hash__ = Hostile.__hash__


@pytest.mark.parametrize("action", ("prepare", "abort", "close"))
def test_registered_restamped_use_retires_before_rejection(local_family, action):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    value = object()
    runtime._family(use, value)
    family = reads._RUNTIMES[runtime].families[use]
    record = composition._COMMAND_NODE_SESSIONS[use]
    original_class = type(use)
    object.__setattr__(use, "__class__", _RestampedUse)
    try:
        if action == "prepare":
            with pytest.raises(TypeError, match="command-owned"):
                factory.prepare_private_stage_read_input(use, value)
        elif action == "abort":
            assert factory.abort_private_stage_read_input(use) is None
        else:
            runtime.close()
        assert family.terminal and family.semantic_input is None
        assert not record.live
        assert events == []
    finally:
        object.__setattr__(use, "__class__", original_class)
    assert use not in composition._COMMAND_NODE_SESSIONS
    with pytest.raises(RuntimeError, match="closed"):
        use.validate()
    with pytest.raises(RuntimeError, match="terminal|retired"):
        factory.prepare_private_stage_read_input(use, value)
    assert events == []


def test_unknown_foreign_use_preserves_registered_family(local_family):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    value = object()
    runtime._family(use, value)
    family = reads._RUNTIMES[runtime].families[use]
    for action in (runtime.prepare, runtime.abort):
        args = (Hostile(), value) if action == runtime.prepare else (Hostile(),)
        with pytest.raises(TypeError, match="command-owned"):
            action(*args)
    assert not family.terminal and family.semantic_input is value
    assert composition._COMMAND_NODE_SESSIONS[use].live
    runtime._family(use, value)
    assert events == []


def test_node_close_substitution_cannot_block_local_retirement(local_family, monkeypatch):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    runtime._family(use, object())
    family = reads._RUNTIMES[runtime].families[use]

    def hostile_close(_self):
        pytest.fail("substituted close invoked")

    with monkeypatch.context() as patch:
        patch.setattr(type(use), "close", hostile_close)
        runtime.close()
    assert family.terminal and family.semantic_input is None
    assert use not in composition._COMMAND_NODE_SESSIONS
    with pytest.raises(RuntimeError, match="closed"):
        use.validate()
    assert events == []


def test_cleanup_failure_releases_every_family(local_family, monkeypatch):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    runtime._family(use, object())
    second_use = object.__new__(composition._CommandOwnedGraphNodeSourceSession)
    composition._COMMAND_NODE_SESSIONS[second_use] = composition._CommandNodeSourceSessionRecord(
        factory._command, object(), object(), os.getpid(), get_ident()
    )
    runtime._family(second_use, object())
    families = tuple(reads._RUNTIMES[runtime].families.values())
    original_retire = composition._retire_command_node_session_by_identity
    calls = []

    def failing_cleanup(operation_use):
        original_retire(operation_use)
        calls.append(operation_use)
        raise RuntimeError("owner cleanup failed")

    with monkeypatch.context() as patch:
        patch.setattr(composition, "_retire_command_node_session_by_identity", failing_cleanup)
        with pytest.raises(BaseExceptionGroup, match="cleanup failed") as caught:
            runtime.close()
    assert len(caught.value.exceptions) == 2
    assert len(calls) == 2
    assert all(family.terminal and family.semantic_input is None for family in families)
    for operation_use in (use, second_use):
        assert operation_use not in composition._COMMAND_NODE_SESSIONS
        with pytest.raises(RuntimeError, match="closed"):
            operation_use.validate()
    assert events == []


def test_input_substitution_is_terminal_without_foreign_behavior(local_family):
    factory, use, _, events = local_family
    # Direct private state inspection exercises mechanics, never approval.
    factory._private_reads._family(use, object())
    with pytest.raises(RuntimeError, match="input substituted"):
        factory.prepare_private_stage_read_input(use, Hostile())
    assert events == []
    assert use not in composition._COMMAND_NODE_SESSIONS


def test_hostile_use_rejects_before_behavior(local_family):
    factory, _, _, events = local_family
    with pytest.raises(TypeError, match="command-owned"):
        factory.prepare_private_stage_read_input(Hostile(), object())
    assert events == []


def test_changed_original_source_is_terminal(local_family, monkeypatch):
    factory, use, _, _ = local_family
    def changed(*_args):
        raise RuntimeError("original source changed")
    monkeypatch.setattr(composition, "_validate_command_owned_graph_node_source", changed)
    with pytest.raises(RuntimeError, match="original source changed"):
        factory.prepare_private_stage_read_input(use, object())
    assert use not in composition._COMMAND_NODE_SESSIONS
    assert factory.abort_private_stage_read_input(use) is None


@pytest.mark.parametrize("change", ("process", "thread", "descriptor"))
def test_origin_loss_retires_family(local_family, monkeypatch, change):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    value = object()
    runtime._family(use, value)
    if change == "process":
        reads._RUNTIMES[runtime].process_id = -1
    elif change == "thread":
        reads._RUNTIMES[runtime].thread = object()
    else:
        def substituted(*_args, **_kwargs):
            pytest.fail("substituted origin invoked")
        monkeypatch.setattr(type(factory), "validate_selected_graph_node_use", substituted)
    with pytest.raises(RuntimeError, match="origin changed"):
        runtime.prepare(use, value)
    assert events == []
    assert use not in composition._COMMAND_NODE_SESSIONS
    assert factory.abort_private_stage_read_input(use) is None


def test_cleanup_after_parent_closure_is_idempotent(local_family):
    factory, use, _, _ = local_family
    factory._private_reads._family(use, object())
    factory._owner.close()
    factory._private_reads.close()
    assert factory.abort_private_stage_read_input(use) is None
    with pytest.raises(RuntimeError, match="retired"):
        factory.prepare_private_stage_read_input(use, object())


def test_original_use_retirement_clears_retained_input(local_family):
    factory, use, _, events = local_family
    runtime = factory._private_reads
    value = object()
    runtime._family(use, value)
    use.close()
    with pytest.raises(RuntimeError, match="retired fixed graph-node use"):
        runtime.prepare(use, value)
    family = reads._RUNTIMES[runtime].families[use]
    assert family.terminal and family.semantic_input is None
    assert events == []


def test_no_constructor_copy_or_reassembly(local_family):
    factory, _, _, _ = local_family
    with pytest.raises(TypeError, match="assembly required"):
        reads._WorkspacePrivateStageReadRuntime()
    with pytest.raises(TypeError, match="process-local"):
        copy.copy(factory._private_reads)
    with pytest.raises(RuntimeError, match="assembly replay"):
        reads._assemble_private_stage_read_runtime(factory)
    with pytest.raises(TypeError, match="fixed Workspace factory"):
        reads._assemble_private_stage_read_runtime(object())


def test_runtime_substitution_does_not_borrow_origin(local_family):
    factory, use, _, events = local_family
    foreign = object.__new__(composition._DirectWorkspaceOriginFactory)
    composition._ORIGIN_FACTORIES.add(foreign)
    foreign._private_reads = factory._private_reads
    with pytest.raises(RuntimeError, match="runtime substituted"):
        foreign.prepare_private_stage_read_input(use, object())
    assert events == []
    assert use in composition._COMMAND_NODE_SESSIONS


def test_substituted_field_descriptor_executes_no_behavior(local_family, monkeypatch):
    factory, use, _, events = local_family
    runtime = factory._private_reads

    def hostile(_self):
        pytest.fail("substituted field descriptor invoked")

    with monkeypatch.context() as patch:
        patch.setattr(type(factory), "_private_reads", property(hostile), raising=False)
        with pytest.raises(RuntimeError, match="original Workspace private-read runtime"):
            factory.prepare_private_stage_read_input(use, object())
    assert events == []
    assert reads._RUNTIMES[runtime].live
