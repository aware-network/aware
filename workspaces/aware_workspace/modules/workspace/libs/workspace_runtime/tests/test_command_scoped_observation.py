"""Genuine command evidence coexists with the maintained observation owner."""

import asyncio
import json
import os
import signal
import threading
from pathlib import Path

import pytest
from aware_workspace_runtime import (
    FileSystemIndexObservationProvider,
    SourceObservationUnavailable,
    WorkspaceObservationLeaseUnavailable,
    WorkspaceObservationNotStartedError,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
    WorkspaceSourceObservationRuntime,
)
from aware_workspace_runtime.lease import FileWorkspaceRepositoryObservationLease
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory,
)


def _session(root, state, *, mode="maintained"):
    binding = WorkspaceRepositoryBinding(root)
    return WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(binding=binding, cache_dir=state),
        observation_mode=mode,
    )


@pytest.mark.asyncio
async def test_original_command_sources_coexist_and_revalidate(tmp_path):
    root = tmp_path / "repository"
    source = root / "package/source.aware"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original source")
    maintained = _session(root, tmp_path / "maintained")
    first = _session(root, tmp_path / "first", mode="command")
    second = _session(root, tmp_path / "second", mode="command")
    store = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
        state_root=tmp_path / "retention",
    ).allocate_delta_retention()
    store.initialize_delta_retention(
        repository_binding_ref=first.binding.binding_key,
        body_capacity=32,
        maximum_bytes=1024 * 1024,
    )
    observer = None
    await maintained.start(background=False)
    lease_path = root / ".aware/workspace/observation/writer.lock"
    lease_body = lease_path.read_bytes()
    maintained_snapshot = maintained.current_snapshot
    try:
        await asyncio.gather(
            first.start(background=False), second.start(background=False)
        )
        assert len({maintained.epoch, first.epoch, second.epoch}) == 3
        assert first._watch_task is second._watch_task is None
        observer = WorkspaceSourceObservationRuntime(session=first, store=store)
        observed = observer.observe(root_relative_path="package")
        assert (
            observer.read(observed, relative_path="source.aware") == b"original source"
        )
        observer.revalidate(observed)
        source.write_bytes(b"changed source")
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate(observed)
        assert maintained.current_snapshot is maintained_snapshot
        assert lease_path.read_bytes() == lease_body
        contender = _session(root, tmp_path / "contender")
        try:
            with pytest.raises(WorkspaceObservationLeaseUnavailable):
                await contender.start(background=False)
        finally:
            await contender.stop()
        await first.stop()
        with pytest.raises(
            SourceObservationUnavailable, match="observation_lifetime_unavailable"
        ):
            observer.revalidate(observed)
        assert second.authority_admitted and maintained.authority_admitted
        assert lease_path.read_bytes() == lease_body
    finally:
        if observer is not None:
            observer.close()
        await first.stop()
        await second.stop()
        await maintained.stop()


@pytest.mark.asyncio
async def test_command_requires_initialized_snapshot_and_retires_its_epoch(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    session = _session(root, tmp_path / "command", mode="command")
    with pytest.raises(WorkspaceObservationNotStartedError):
        await session.admit()
    with pytest.raises(ValueError, match="maintained watcher"):
        await session.start()
    assert not session.authority_admitted
    assert not (root / ".aware/workspace/observation/writer.lock").exists()
    try:
        await session.start(background=False)
        epoch = session.epoch
        reference = session.observe_workspace_session(
            execution_id="test-command", actor_ref="actor:test"
        )
        await session.stop()
        with pytest.raises(WorkspaceObservationNotStartedError):
            session.require_workspace_session_current(
                workspace_session_ref=reference,
                execution_id="test-command",
                actor_ref="actor:test",
            )
        await session.start(background=False)
        assert session.epoch != epoch
        with pytest.raises(WorkspaceObservationNotStartedError):
            session.require_workspace_session_current(
                workspace_session_ref=reference,
                execution_id="test-command",
                actor_ref="actor:test",
            )
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_public_cli_admits_while_original_maintained_session_is_live(tmp_path):
    root = tmp_path / "repository"
    package = root / "workspaces/kernel/modules/demo/package"
    package.mkdir(parents=True)
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n'
        '[[workspaces]]\nhandle="Kernel"\npath="workspaces/kernel"\n'
    )
    (root / "workspaces/kernel/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Kernel"\n'
        '[[workspace.modules]]\nid="demo"\npath="modules/demo"\n'
    )
    (package.parent / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="demo"\nkind="example"\n'
        'manifest="package/aware.example.toml"\nvisibility="module"\n'
    )
    (package / "aware.example.toml").write_text("authored owner bytes")
    maintained = _session(root, tmp_path / "maintained")
    await maintained.start(background=False)
    lease_path = root / ".aware/workspace/observation/writer.lock"
    before = lease_path.read_bytes()
    repository = Path(__file__).resolve().parents[7]
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            str(repository / ".venv/bin/aware-cli"),
            "workspace",
            "materialize",
            "--repo-root",
            str(root),
            "--workspace-toml",
            "workspaces/kernel/aware.workspace.toml",
            "--package",
            "demo",
            "--plan",
            "--json",
            env={
                **os.environ,
                "XDG_STATE_HOME": str(tmp_path / "state"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        assert process.returncode == 2, stderr.decode()
        result = json.loads(stdout)
        assert result["failure_code"] == "graph_host_not_ready"
        assert result["operation"]["host_receipt"]
        assert maintained.authority_admitted
        assert lease_path.read_bytes() == before
        assert not tuple((tmp_path / "state").rglob("command-*"))
        contender = FileWorkspaceRepositoryObservationLease(binding=maintained.binding)
        with pytest.raises(WorkspaceObservationLeaseUnavailable):
            contender.acquire()
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        await maintained.stop()


def test_command_rejects_caller_supplied_lease(tmp_path):
    binding = WorkspaceRepositoryBinding(tmp_path)
    lease = FileWorkspaceRepositoryObservationLease(binding=binding)
    with pytest.raises(ValueError, match="writer lease"):
        WorkspaceRepositoryObservationSession(
            binding=binding,
            provider=FileSystemIndexObservationProvider(binding=binding),
            observation_mode="command",
            lease=lease,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", (RuntimeError, asyncio.CancelledError))
async def test_failed_command_initialization_issues_no_authority(tmp_path, failure):
    class FailedProvider:
        root_path = tmp_path.resolve()
        closed = 0

        async def initialize(self):
            raise failure("original source initialization failed")

        async def close(self):
            self.closed += 1

    provider = FailedProvider()
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        observation_mode="command",
    )
    with pytest.raises(failure):
        await session.start(background=False)
    assert not session.authority_admitted
    with pytest.raises(WorkspaceObservationNotStartedError):
        session.observe_workspace_session(execution_id="test", actor_ref="actor:test")
    await session.stop()
    assert provider.closed == 1
    assert not (tmp_path / ".aware/workspace/observation/writer.lock").exists()


@pytest.mark.asyncio
@pytest.mark.skipif(not hasattr(os, "fork"), reason="original POSIX fork proof")
@pytest.mark.filterwarnings("ignore:This process.*multi-threaded:DeprecationWarning")
async def test_inherited_command_refuses_before_inherited_locks(tmp_path):
    session = _session(
        tmp_path, tmp_path.parent / (tmp_path.name + "-state"), mode="command"
    )
    await session.start(background=False)
    reference = session.observe_workspace_session(
        execution_id="test", actor_ref="actor:test"
    )
    ready = threading.Event()
    release = threading.Event()

    def hold_original_lock():
        with session._workspace_session_lock:
            ready.set()
            release.wait()

    holder = threading.Thread(target=hold_original_lock)
    holder.start()
    assert await asyncio.to_thread(ready.wait, 2)
    pid = os.fork()
    if pid == 0:
        signal.alarm(3)
        try:
            assert not session.authority_admitted
            with pytest.raises(WorkspaceObservationNotStartedError):
                asyncio.run(session.start(background=False))
            with pytest.raises(WorkspaceObservationNotStartedError):
                asyncio.run(session.stop())
            with pytest.raises(WorkspaceObservationNotStartedError):
                session.require_workspace_session_current(
                    workspace_session_ref=reference,
                    execution_id="test",
                    actor_ref="actor:test",
                )
            with pytest.raises(WorkspaceObservationNotStartedError):
                session.observe_workspace_session(
                    execution_id="test", actor_ref="actor:test"
                )
            os._exit(0)
        except BaseException:  # noqa: BLE001 - a fork failure must never resume the parent harness
            os._exit(1)
    try:
        _, status = await asyncio.to_thread(os.waitpid, pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
    finally:
        release.set()
        await asyncio.to_thread(holder.join)
    try:
        session.require_workspace_session_current(
            workspace_session_ref=reference,
            execution_id="test",
            actor_ref="actor:test",
        )
    finally:
        await session.stop()
