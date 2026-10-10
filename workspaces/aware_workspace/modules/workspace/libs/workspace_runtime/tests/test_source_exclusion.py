"""Original source-chain exclusion mechanics; no Code host qualification."""

import os
import threading
from contextlib import asynccontextmanager

import pytest
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_workspace_runtime.command_lifetime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceCommandLifetimeUnavailable,
)
from aware_workspace_runtime.complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
)
from aware_workspace_runtime.observed_membership import (
    WorkspaceObservedPackageMembershipRuntime,
)
from aware_workspace_runtime.source_exclusion import WorkspaceSourceExclusion
from aware_workspace_runtime.source_observation import WorkspaceSourceObservationRuntime
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_observed_semantic_issuers import setup


def parent():
    runtime = WorkspaceCommandLifetimeRuntime()
    handle = runtime._retain_direct_invocation_parent()
    expected = DirectInvocationExpectation(
        runtime.invocation_identity, runtime.epoch_identity, os.getpid()
    )
    exclusion = WorkspaceSourceExclusion(
        runtime=runtime, parent=handle, expected=expected
    )
    return runtime, handle, expected, exclusion


@asynccontextmanager
async def chain(tmp_path):
    async with setup(tmp_path) as (_, session, borrowed, _, _, _, _):
        runtime, handle, expected, exclusion = parent()
        observation = WorkspaceSourceObservationRuntime(
            session=session, store=borrowed._store, exclusion=exclusion
        )
        membership = WorkspaceObservedPackageMembershipRuntime(
            observation_runtime=observation, exclusion=exclusion
        )
        scope = WorkspaceCompleteScopeObservationRuntime(
            observation_runtime=observation,
            membership_runtime=membership,
            exclusion=exclusion,
        )
        retained = observation.observe(root_relative_path=".")
        snapshot = scope.capture_complete_scope(
            observation=retained, workspace_manifest_path="aware.workspace.toml"
        )
        try:
            yield (
                runtime,
                handle,
                expected,
                exclusion,
                observation,
                membership,
                scope,
                retained,
                snapshot,
            )
        finally:
            scope.close()
            membership.close()
            observation.close()
            runtime.close()


@pytest.mark.parametrize(
    "operation",
    [
        "scope_release",
        "scope_close",
        "member_release",
        "member_close",
        "root_release",
        "root_close",
    ],
)
async def test_every_direct_retirement_waits_for_publication_guard(tmp_path, operation):
    async with chain(tmp_path) as (
        runtime,
        handle,
        expected,
        _,
        obs,
        members,
        scopes,
        root,
        snapshot,
    ):
        expected_record = scopes._record(snapshot)
        guard = runtime.acquire_catalog_epoch_exclusion(handle, expected=expected)
        record = scopes._check_record_locked(
            snapshot, guard=guard, expected_record=expected_record
        )
        member = record.memberships[0]
        action = {
            "scope_release": lambda: scopes.release(snapshot),
            "scope_close": scopes.close,
            "member_release": lambda: members.release(member),
            "member_close": members.close,
            "root_release": lambda: obs.release(root),
            "root_close": obs.close,
        }[operation]
        started, finished = threading.Event(), threading.Event()
        errors = []

        def retire():
            started.set()
            try:
                action()
            except BaseException as error:
                errors.append(error)
            finally:
                finished.set()

        worker = threading.Thread(target=retire)
        worker.start()
        try:
            assert started.wait(2)
            assert not finished.wait(0.05)
            assert (
                scopes._check_record_locked(
                    snapshot, guard=guard, expected_record=expected_record
                )
                is record
            )
        finally:
            runtime.release_catalog_epoch_exclusion(guard)
            worker.join(2)
        assert not worker.is_alive()
        assert not errors
        guard = runtime.acquire_catalog_epoch_exclusion(handle, expected=expected)
        try:
            with pytest.raises(SourceObservationUnavailable):
                scopes._check_record_locked(
                    snapshot, guard=guard, expected_record=expected_record
                )
        finally:
            runtime.release_catalog_epoch_exclusion(guard)


async def test_parent_close_revokes_but_allows_owned_retirement(tmp_path):
    async with chain(tmp_path) as (
        runtime,
        _,
        _,
        _,
        obs,
        members,
        scopes,
        root,
        snapshot,
    ):
        runtime.close()
        with pytest.raises(WorkspaceCommandLifetimeUnavailable):
            scopes.read_complete_scope(snapshot)
        with pytest.raises(WorkspaceCommandLifetimeUnavailable):
            obs.observe(root_relative_path=".")
        scopes.release(snapshot)
        members.close()
        obs.release(root)
        obs.close()


async def test_mixed_or_foreign_participation_refuses(tmp_path):
    async with chain(tmp_path) as (_, _, _, exclusion, obs, members, _, _, _):
        foreign, _, _, other = parent()
        try:
            for value in (None, other):
                with pytest.raises(
                    SourceObservationUnavailable, match="origin_mismatch"
                ):
                    WorkspaceObservedPackageMembershipRuntime(
                        observation_runtime=obs, exclusion=value
                    )
                with pytest.raises(
                    SourceObservationUnavailable, match="origin_mismatch"
                ):
                    WorkspaceCompleteScopeObservationRuntime(
                        observation_runtime=obs,
                        membership_runtime=members,
                        exclusion=value,
                    )
            assert exclusion is not other
        finally:
            foreign.close()


class NoLock:
    def __enter__(self):
        raise AssertionError("final check acquired a lock")

    def acquire(self, *args, **kwargs):
        raise AssertionError("final check acquired a lock")


async def test_final_original_chain_check_has_no_reads_or_lock_acquisitions(
    tmp_path, monkeypatch
):
    async with chain(tmp_path) as (
        runtime,
        handle,
        expected,
        _,
        obs,
        members,
        scopes,
        _,
        snapshot,
    ):
        expected_record = scopes._record(snapshot)
        guard = runtime.acquire_catalog_epoch_exclusion(handle, expected=expected)
        try:
            with monkeypatch.context() as patch:
                for owner in (runtime, obs, members, scopes):
                    patch.setattr(owner, "_lock", NoLock())

                def no_read(*args, **kwargs):
                    raise AssertionError("source work under guard")

                patch.setattr(obs, "evidence", no_read)
                patch.setattr(obs, "read", no_read)
                patch.setattr(obs, "revalidate", no_read)
                scopes._check_record_locked(
                    snapshot, guard=guard, expected_record=expected_record
                )
                with pytest.raises(WorkspaceCommandLifetimeUnavailable):
                    scopes._check_record_locked(
                        snapshot, guard=object(), expected_record=expected_record
                    )
        finally:
            runtime.release_catalog_epoch_exclusion(guard)


async def test_cleanup_is_outside_exclusion_and_attempts_every_owned_member(
    tmp_path, monkeypatch
):
    async with chain(tmp_path) as (
        runtime,
        _,
        _,
        _,
        obs,
        members,
        scopes,
        root,
        snapshot,
    ):
        original = members.release
        calls = []
        with monkeypatch.context() as patch:

            def cleanup(member):
                assert runtime._guard is None
                calls.append(member)
                if len(calls) != 2:
                    raise OSError("injected cleanup failure")
                original(member)

            patch.setattr(members, "release", cleanup)
            with pytest.raises(BaseExceptionGroup) as errors:
                scopes.release(snapshot)
        assert len(calls) == 3
        assert len(errors.value.exceptions) == 2
        assert snapshot not in scopes._records
        obs.evidence(root)  # borrowed observation and parent remain live


async def test_descriptor_cleanup_is_after_nominal_retirement(tmp_path, monkeypatch):
    async with chain(tmp_path) as (runtime, _, _, _, obs, _, _, _, _):
        real_close = os.close
        descriptor = obs._root_fd
        seen = []

        def close(fd):
            if fd == descriptor:
                assert runtime._guard is None
                assert obs._closed and not obs._records
                seen.append(fd)
            real_close(fd)

        with monkeypatch.context() as patch:
            patch.setattr(os, "close", close)
            obs.close()
        assert seen == [descriptor]


@pytest.mark.parametrize("layer", ["scope", "membership", "root"])
async def test_replaced_original_records_reject_even_equal_values(tmp_path, layer):
    from dataclasses import replace

    async with chain(tmp_path) as (
        runtime,
        handle,
        expected,
        _,
        obs,
        members,
        scopes,
        root,
        snapshot,
    ):
        original = scopes._record(snapshot)
        guard = runtime.acquire_catalog_epoch_exclusion(handle, expected=expected)
        try:
            if layer == "scope":
                scopes._records[snapshot] = replace(original)
            elif layer == "membership":
                member = original.memberships[0]
                members._records[member] = tuple(list(members._records[member]))
            else:
                obs._records[root] = replace(obs._records[root])
            with pytest.raises(SourceObservationUnavailable):
                scopes._check_record_locked(
                    snapshot, guard=guard, expected_record=original
                )
        finally:
            runtime.release_catalog_epoch_exclusion(guard)


async def test_prepared_observation_cannot_publish_after_parent_closure(
    tmp_path, monkeypatch
):
    async with chain(tmp_path) as (runtime, handle, expected, _, obs, _, _, _, _):
        original = obs._store.record_bodies
        prepared = threading.Event()
        completed = threading.Event()
        errors = []
        before = dict(obs._records)

        def retain(bodies):
            assert runtime._thread is not threading.current_thread()
            result = original(bodies)
            prepared.set()
            return result

        def produce():
            try:
                obs.observe(root_relative_path=".")
            except BaseException as error:
                errors.append(error)
            finally:
                completed.set()

        guard = runtime.acquire_catalog_epoch_exclusion(handle, expected=expected)
        worker = threading.Thread(target=produce)
        with monkeypatch.context() as patch:
            patch.setattr(obs._store, "record_bodies", retain)
            worker.start()
            try:
                assert prepared.wait(2)
                assert not completed.wait(0.05)
                runtime.close()
            finally:
                runtime.release_catalog_epoch_exclusion(guard)
                worker.join(2)
        assert not worker.is_alive()
        assert len(errors) == 1
        assert isinstance(errors[0], WorkspaceCommandLifetimeUnavailable)
        assert obs._records == before


async def test_scope_preparation_failure_retires_all_created_memberships(
    tmp_path, monkeypatch
):
    async with chain(tmp_path) as (runtime, _, _, _, _, members, scopes, root, _):
        before = set(members._records)
        original = members.admit
        calls = []
        with monkeypatch.context() as patch:

            def admit(**kwargs):
                assert runtime._guard is None
                calls.append(1)
                if len(calls) == 2:
                    raise OSError("second member preparation failed")
                return original(**kwargs)

            patch.setattr(members, "admit", admit)
            with pytest.raises(OSError, match="second member"):
                scopes.capture_complete_scope(
                    observation=root, workspace_manifest_path="aware.workspace.toml"
                )
        assert set(members._records) == before


async def test_root_construction_failure_closes_only_new_descriptor(tmp_path, monkeypatch):
    from aware_workspace_runtime import source_observation as source_module

    async with setup(tmp_path) as (_, session, borrowed, _, _, _, _):
        runtime, handle, expected, exclusion = parent()
        opened, closed = [], []
        original_open, original_close = os.open, os.close
        def open_fd(*args, **kwargs):
            fd = original_open(*args, **kwargs)
            opened.append(fd)
            return fd
        def close_fd(fd):
            closed.append(fd)
            original_close(fd)
        def fail_identity(fd):
            raise OSError("identity failed")
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", open_fd)
            patch.setattr(os, "close", close_fd)
            patch.setattr(source_module, "identity", fail_identity)
            with pytest.raises(OSError, match="identity failed"):
                WorkspaceSourceObservationRuntime(session=session, store=borrowed._store, exclusion=exclusion)
        assert len(opened) == 1 and closed == opened
        runtime.validate_direct_invocation_parent(handle, expected=expected)
        borrowed.observe(root_relative_path=".")
        runtime.close()
