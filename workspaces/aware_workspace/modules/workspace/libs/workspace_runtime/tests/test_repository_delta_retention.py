"""Neutral lifecycle using genuine original FS supplier, not a callable shim."""

import pytest
from aware_workspace_fs_adapter.repository_delta_retention import (
    FilesystemDeltaRetentionFactory,
)
from aware_workspace_runtime.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionRefusal,
    WorkspaceRepositoryDeltaRetentionRuntime,
)


def test_states_cannot_cross_original_runtime_providers(tmp_path):
    factory = FilesystemDeltaRetentionFactory.filesystem(state_root=tmp_path)
    first = WorkspaceRepositoryDeltaRetentionRuntime(physical_factory=factory)
    second = WorkspaceRepositoryDeltaRetentionRuntime(physical_factory=factory)
    state = first.allocate()
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_not_issued"
    ):
        second.initialize(state, repository_binding_ref="binding:one")
    first.initialize(state, repository_binding_ref="binding:one")
    ref = first.record_body(state, b"original")
    first.release(state)
    assert first.observe(state).phase == "released"
    with pytest.raises(WorkspaceRepositoryDeltaRetentionRefusal):
        first.resolve_body(state, ref)


def test_runtime_observations_are_detached_and_do_not_issue_states(tmp_path):
    runtime = WorkspaceRepositoryDeltaRetentionRuntime(
        physical_factory=FilesystemDeltaRetentionFactory.filesystem(
            state_root=tmp_path
        ),
    )
    state = runtime.allocate()
    snapshot = runtime.observe(state)
    with pytest.raises(
        WorkspaceRepositoryDeltaRetentionRefusal, match="retention_not_issued"
    ):
        runtime.release(snapshot)
    runtime.initialize(state, repository_binding_ref="binding:one")
    assert snapshot.phase == "allocated" and snapshot.repository_binding_ref is None
