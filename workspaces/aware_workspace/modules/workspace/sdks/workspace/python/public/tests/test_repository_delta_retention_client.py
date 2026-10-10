"""Real retention selection, original storage and lifetime proofs."""

import copy
import os
import pickle
from concurrent.futures import ThreadPoolExecutor

import pytest
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
    WorkspaceRepositoryDeltaRetentionFactory,
    WorkspaceRepositoryDeltaRetentionRefusal,
)


def retained(*, state_root, repository_binding_ref, **limits):
    client = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=state_root,
    ).allocate_delta_retention()
    client.initialize_delta_retention(
        repository_binding_ref=repository_binding_ref, **limits
    )
    return client


def test_selection_and_allocation_do_not_resolve_or_create_state(tmp_path, monkeypatch):
    from pathlib import Path

    factory = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path / "missing"
    )
    with monkeypatch.context() as patch:
        patch.setattr(
            Path, "resolve", lambda *a, **k: pytest.fail("allocation performed IO")
        )
        client = factory.allocate_delta_retention()
    snapshot = client.observe_retention()
    assert snapshot.phase == "allocated" and snapshot.repository_binding_ref is None
    assert not (tmp_path / "missing").exists()
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_not_active"
    ):
        client.record_body(b"disabled")
    assert client.release_retention().phase == "released"
    assert snapshot.phase == "allocated"


@pytest.mark.parametrize(
    "action", ["construct", "forge", "subclass", "copy", "deepcopy", "pickle"]
)
def test_clients_cannot_be_constructed_or_replayed(tmp_path, action):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    if action == "construct":
        with pytest.raises(TypeError):
            WorkspaceRepositoryDeltaRetentionClient()
    elif action == "forge":
        forged = object.__new__(WorkspaceRepositoryDeltaRetentionClient)
        with pytest.raises(
            WorkspaceRepositoryDeltaRetentionRefusal, match="retention_not_issued"
        ):
            forged.observe_retention()
    elif action == "subclass":

        class Foreign(WorkspaceRepositoryDeltaRetentionClient):
            pass

        with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal):
            object.__new__(Foreign).record_body(b"forged")
    else:
        operation = {
            "copy": copy.copy,
            "deepcopy": copy.deepcopy,
            "pickle": pickle.dumps,
        }[action]
        with pytest.raises(TypeError):
            operation(client)


@pytest.mark.parametrize("interruption", [ValueError, KeyboardInterrupt, SystemExit])
def test_initializer_retains_partial_original_and_is_spent(
    tmp_path, monkeypatch, interruption
):
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    original = WorkspaceRepositoryDeltaStore.__init__
    captured = []

    def interrupted(store, **kwargs):
        captured.append(store)
        original(store, **kwargs)
        raise interruption("original initializer return unavailable")

    client = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path
    ).allocate_delta_retention()
    with monkeypatch.context() as patch:
        patch.setattr(WorkspaceRepositoryDeltaStore, "__init__", interrupted)
        with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal) as refusal:
            client.initialize_delta_retention(repository_binding_ref="binding:one")
    assert isinstance(refusal.value.__cause__, interruption)
    assert refusal.value.observation.phase == "refused"
    assert len(captured) == 1
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_initializer_spent"
    ):
        client.initialize_delta_retention(repository_binding_ref="binding:one")
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_not_active"
    ):
        client.snapshot()
    assert client.release_retention().phase == "released"
    assert client.release_retention().phase == "released"


def test_independent_shared_store_clients_and_concurrent_original_io(tmp_path):
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    raw = WorkspaceRepositoryDeltaStore(
        state_root=tmp_path, repository_binding_ref="binding:one"
    )
    factory = WorkspaceRepositoryDeltaRetentionFactory.filesystem(state_root=tmp_path)
    first = factory.retain_delta_retention(raw, expected_binding_ref="binding:one")
    second = factory.retain_delta_retention(raw, expected_binding_ref="binding:one")
    with ThreadPoolExecutor(max_workers=8) as executor:
        refs = tuple(executor.map(second.record_body, (b"same original body",) * 24))
    assert len(set(refs)) == 1 and second.snapshot().metrics.body_write_count == 1
    first.release_retention()
    with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal):
        first.resolve_body(refs[0])
    assert second.resolve_body(refs[0]) == b"same original body"
    assert raw.resolve_body(refs[0]) == b"same original body"
    second.release_retention()
    assert raw.resolve_body(refs[0]) == b"same original body"


def test_owner_verification_refuses_foreign_runtime_and_wrong_binding(tmp_path):
    from aware_workspace_runtime.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionRuntime,
    )

    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_binding_mismatch"
    ):
        client.verify_repository_binding(expected_binding_ref="binding:other")
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_owner_mismatch"
    ):
        WorkspaceRepositoryDeltaRetentionRuntime(physical_factory=object())
    forged = object.__new__(WorkspaceRepositoryDeltaRetentionRuntime)
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_owner_mismatch"
    ):
        forged.allocate()


@pytest.mark.parametrize("failure", ["raw", "binding", "factory"])
def test_sdk_selection_and_adoption_refusals_stay_at_the_sdk_boundary(
    tmp_path, failure
):
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    factory = WorkspaceRepositoryDeltaRetentionFactory.filesystem(state_root=tmp_path)
    with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal) as refusal:
        if failure == "factory":
            WorkspaceRepositoryDeltaRetentionFactory.filesystem(state_root="not a Path")
        elif failure == "raw":
            factory.retain_delta_retention(object(), expected_binding_ref="binding:one")
        else:
            raw = WorkspaceRepositoryDeltaStore(
                state_root=tmp_path, repository_binding_ref="binding:other"
            )
            factory.retain_delta_retention(raw, expected_binding_ref="binding:one")
    assert refusal.value.observation is None
    assert refusal.value.__cause__ is not None


def test_real_fork_cannot_reuse_client(tmp_path):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    child = os.fork()
    if child == 0:
        try:
            client.record_body(b"foreign process")
        except WorkspaceRepositoryDeltaRetentionRefusal as error:
            os._exit(0 if error.code == "retention_process_mismatch" else 21)
        os._exit(22)
    _, status = os.waitpid(child, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert client.snapshot().retained_body_count == 0


def test_fixed_surface_does_not_expose_raw_paths_or_dispatch(tmp_path):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    for name in ("store_root", "_store", "_owner", "dispatch", "_states", "state_root"):
        assert not hasattr(client, name)
    assert client.repository_binding_ref == "binding:one"


@pytest.mark.parametrize("retire", [False, True])
def test_concurrent_initialization_is_spent_before_original_effects(
    tmp_path, monkeypatch, retire
):
    import threading

    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    original = WorkspaceRepositoryDeltaStore.__init__
    entered, proceed = threading.Event(), threading.Event()
    calls = []

    def held(store, **kwargs):
        calls.append(store)
        entered.set()
        assert proceed.wait(5)
        original(store, **kwargs)

    client = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path
    ).allocate_delta_retention()
    with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as executor:
        patch.setattr(WorkspaceRepositoryDeltaStore, "__init__", held)
        future = executor.submit(
            client.initialize_delta_retention, repository_binding_ref="binding:one"
        )
        assert entered.wait(5)
        try:
            with pytest.raises(
                WorkspaceRepositoryDeltaRetentionRefusal,
                match="retention_initializer_spent",
            ):
                client.initialize_delta_retention(repository_binding_ref="binding:one")
            if retire:
                client.release_retention()
        finally:
            proceed.set()
        if retire:
            with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal):
                future.result()
            assert client.observe_retention().phase == "released"
        else:
            assert future.result().phase == "active"
    assert len(calls) == 1
