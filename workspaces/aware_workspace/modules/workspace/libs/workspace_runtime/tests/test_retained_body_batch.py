"""Original ordered bulk reads, fresh body checks and terminal refusal."""

import io
import sys

import pytest

# isort: split
from aware_workspace_fs_adapter import repository_delta_retention as fs

# isort: split
from aware_workspace_runtime import repository_delta_retention as retention
from aware_workspace_runtime.repository_delta_store_contract import (
    WorkspaceRepositoryDeltaStoreCorrupt,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable

# isort: split
from aware_workspace_sdk import repository_delta_retention as sdk

# isort: split
from test_repository_delta_retention_client import retained
from test_source_observation import runtime


def after_physical_read(monkeypatch, callback):
    original_open = io.open

    class Stream:
        def __init__(self, original):
            self.original = original

        def __enter__(self):
            self.original.__enter__()
            return self

        def __exit__(self, *args):
            return self.original.__exit__(*args)

        def read(self):
            return callback(self.original.read())

    def instrumented_open(path, *args, **kwargs):
        original = original_open(path, *args, **kwargs)
        return Stream(original) if str(path).endswith(".blob") else original

    monkeypatch.setattr(io, "open", instrumented_open)


def resources(client):
    owner_runtime, state = sdk._CLIENTS[client]
    return owner_runtime, state, state.owner, fs._OWNERS[state.owner].store


def test_bulk_reads_keep_order_duplicates_and_every_physical_read(tmp_path):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second"))
    before = client.snapshot().metrics
    requested = (refs[1], refs[0], refs[1], "missing")
    assert client.resolve_bodies(requested) == (b"second", b"first", b"second", None)
    after = client.snapshot().metrics
    assert after.body_read_count - before.body_read_count == 3
    assert after.body_hash_count - before.body_hash_count == 3
    assert client.resolve_bodies(()) == ()
    client.release_retention()
    with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
        client.resolve_bodies(refs)


def test_bulk_amortizes_outer_verification_without_caching_bytes(tmp_path):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies(tuple(str(i).encode() for i in range(12)))
    code = retention.WorkspaceRepositoryDeltaRetentionRuntime.verify_original_runtime.__code__
    counts = []
    count = 0

    def profile(frame, event, arg):
        nonlocal count
        if event == "call" and frame.f_code is code:
            count += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        expected = tuple(client.resolve_body(ref) for ref in refs)
        counts.append(count)
        count = 0
        assert client.resolve_bodies(refs) == expected
        counts.append(count)
    finally:
        sys.setprofile(previous)
    assert 0 < counts[1] < counts[0]
    _, state, _, store = resources(client)
    path = store._body_path(store._bodies[refs[0]].content_digest)
    path.write_bytes(b"corrupted")
    with pytest.raises(WorkspaceRepositoryDeltaStoreCorrupt):
        client.resolve_bodies(refs)
    assert state.phase == "refused"


@pytest.mark.parametrize("layer", ["runtime", "state", "owner", "factory", "store"])
@pytest.mark.parametrize("name", ["__hash__", "__eq__", "__getattribute__"])
def test_bulk_rejects_behavior_substitution_without_dispatch(tmp_path, monkeypatch, layer, name):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second"))
    owner_runtime, state, owner, store = resources(client)
    target = {"runtime": type(owner_runtime), "state": type(state),
              "owner": type(owner), "factory": type(owner_runtime._physical),
              "store": type(store)}[layer]
    calls = []

    def hostile(*args):
        calls.append(True)
        raise RuntimeError("hostile behavior")

    with monkeypatch.context() as patch:
        patch.setattr(target, name, hostile, raising=False)
        with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
            client.resolve_bodies(refs)
    assert calls == []
    assert state.phase == "refused"
    with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
        client.resolve_bodies(refs)


@pytest.mark.parametrize("layer,name", [
    ("runtime", "resolve_bodies"), ("runtime", "verify_original_runtime"),
    ("runtime", "_active_owner"), ("owner", "resolve_body"),
    ("owner", "_active_store"), ("owner", "verify_original_owner"),
    ("store", "resolve_body"), ("store", "_body_path"),
])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
@pytest.mark.parametrize("phase", ["entry", "io"])
@pytest.mark.parametrize("body_count", [1, 2])
def test_bulk_reader_substitution_never_dispatches_and_is_terminal(
    tmp_path, monkeypatch, layer, name, mode, phase, body_count,
):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second")[:body_count])
    owner_runtime, state, owner, store = resources(client)
    target = {"runtime": owner_runtime, "owner": type(owner), "store": store}[layer]
    calls = []
    original = getattr(target, name)
    fired = False

    def hostile(*args, **kwargs):
        calls.append(True)
        if mode == "restore":
            setattr(target, name, original)
        if mode == "raise":
            raise RuntimeError("hostile body reader")
        return b"forged"


    def after_read(value):
        nonlocal fired
        if not fired:
            fired = True
            monkeypatch.setattr(target, name, hostile)
        return value

    with monkeypatch.context() as patch:
        if phase == "entry":
            monkeypatch.setattr(target, name, hostile)
            fired = True
        else:
            after_physical_read(patch, after_read)
        with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
            client.resolve_bodies(refs)
    monkeypatch.undo()
    assert fired
    assert calls == []
    assert state.phase == "refused"
    with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
        client.resolve_bodies(refs)


@pytest.mark.parametrize("failure", [KeyboardInterrupt, SystemExit])
def test_bulk_interruption_retires_registered_family(tmp_path, monkeypatch, failure):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second"))
    _, state, _, _ = resources(client)
    calls = []

    def interrupt(value):
        calls.append(True)
        raise failure("original read interrupted")

    with monkeypatch.context() as patch:
        after_physical_read(patch, interrupt)
        with pytest.raises(failure):
            client.resolve_bodies(refs)
    assert calls == [True]
    assert state.phase == "refused"
    with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
        client.resolve_body(refs[0])


@pytest.mark.parametrize("body_count", [2, 7, 8, 9])
async def test_observer_bulk_preserves_digest_checks_and_freshness(tmp_path, body_count):
    async with runtime(tmp_path) as (observer, _, store, package):
        for index in range(body_count - 2):
            (package / f"extra-{index}").write_bytes(str(index).encode())
        handle = observer.observe(root_relative_path="package")
        previous = sys.getprofile()
        bulk_code = sdk.WorkspaceRepositoryDeltaRetentionClient.resolve_bodies.__code__
        bulk_calls = 0

        def profile(frame, event, arg):
            nonlocal bulk_calls
            if event == "call" and frame.f_code is bulk_code:
                bulk_calls += 1

        try:
            sys.setprofile(profile)
            assert observer.read(handle, relative_path="plain.bin") == b"initial"
        finally:
            sys.setprofile(previous)
        assert (bulk_calls > 0) is (body_count >= 8)
        (package / "plain.bin").write_bytes(b"changed")
        with pytest.raises(SourceObservationUnavailable, match="changed"):
            observer.revalidate(handle)
        store.release_retention()
        with pytest.raises(SourceObservationUnavailable):
            observer.read(handle, relative_path="plain.bin")


def test_unknown_client_does_not_revoke_real_family(tmp_path):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    ref = client.record_body(b"original")
    foreign = object.__new__(sdk.WorkspaceRepositoryDeltaRetentionClient)
    with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
        foreign.resolve_bodies((ref,))
    assert client.resolve_bodies((ref,)) == (b"original",)


@pytest.mark.parametrize("change", ["retire", "state_owner", "state_binding", "store_owner"])
def test_bulk_rejects_currentness_loss_during_physical_read(tmp_path, monkeypatch, change):
    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second"))
    _, state, owner, _store = resources(client)
    calls = []

    def change_after_read(value):
        calls.append(True)
        if len(calls) == 1:
            if change == "retire":
                client.release_retention()
            elif change == "state_owner":
                state.owner = object()
            elif change == "state_binding":
                state.binding = "changed"
            else:
                fs._OWNERS[owner].store = object()
        return value

    with monkeypatch.context() as patch:
        after_physical_read(patch, change_after_read)
        with pytest.raises(sdk.WorkspaceRepositoryDeltaRetentionRefusal):
            client.resolve_bodies(refs)
    assert calls == [True]
    assert state.phase in ("refused", "released")


def test_terminal_readback_rejection_does_not_retain_family_in_held_error(
    tmp_path, monkeypatch,
):
    import gc
    import weakref

    client = retained(state_root=tmp_path, repository_binding_ref="binding:one")
    refs = client.record_bodies((b"first", b"second"))
    owner_runtime, state, _, _ = resources(client)
    runtime_ref = weakref.ref(owner_runtime)
    state_ref = weakref.ref(state)
    genuine_static = sdk.inspect.getattr_static
    calls = 0

    def terminal_mismatch(value, name, default=None):
        nonlocal calls
        try:
            result = genuine_static(value, name, default)
            if value is runtime_ref() and name == "resolve_bodies":
                calls += 1
                if calls == 2:
                    return object()
            return result
        finally:
            del value

    error = None
    with monkeypatch.context() as patch:
        patch.setattr(sdk.inspect, "getattr_static", terminal_mismatch)
        try:
            client.resolve_bodies(refs)
        except sdk.WorkspaceRepositoryDeltaRetentionRefusal as failure:
            error = failure
    assert error is not None and calls == 2
    assert state.phase == "refused"
    client.release_retention()
    del client, state, owner_runtime
    gc.collect()
    assert runtime_ref() is None and state_ref() is None
    assert error.args == ("retention_reader_origin_changed",)


@pytest.mark.parametrize("failure", ["root_absent", "dependency_absent", "other_import_error"])
def test_neutral_import_respects_optional_filesystem_boundary(failure):
    import subprocess

    script = r'''
import importlib, importlib.abc, sys
mode = sys.argv[1]
class MissingOptionalRoot(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "aware_workspace_fs_adapter":
            if mode == "root_absent":
                raise ModuleNotFoundError("optional root absent", name=fullname)
            if mode == "dependency_absent":
                raise ModuleNotFoundError("broken installed dependency", name="missing_store_dependency")
            raise ImportError("broken optional package")
sys.meta_path.insert(0, MissingOptionalRoot())
if mode == "root_absent":
    sdk = importlib.import_module("aware_workspace_sdk.repository_delta_retention")
    runtime = importlib.import_module("aware_workspace_runtime.repository_delta_retention")
    assert "aware_workspace_fs_adapter" not in sys.modules
    try:
        runtime.WorkspaceRepositoryDeltaRetentionRuntime.resolve_bodies(object(), object(), ())
    except sdk.WorkspaceRepositoryDeltaRetentionRefusal as error:
        assert error.code == "retention_filesystem_unavailable"
    else:
        raise AssertionError("absent backend issued a read")
    from pathlib import Path
    try:
        sdk.WorkspaceRepositoryDeltaRetentionFactory.filesystem(state_root=Path("/unused"))
    except ModuleNotFoundError as error:
        assert error.name == "aware_workspace_fs_adapter"
    else:
        raise AssertionError("absent backend issued a factory")
else:
    try:
        importlib.import_module("aware_workspace_sdk.repository_delta_retention")
    except ModuleNotFoundError as error:
        assert mode == "dependency_absent" and error.name == "missing_store_dependency"
    except ImportError as error:
        assert mode == "other_import_error" and str(error) == "broken optional package"
    else:
        raise AssertionError("broken dependency was hidden")
'''
    result = subprocess.run([sys.executable, "-B", "-c", script, failure],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
