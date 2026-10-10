"""Original physical issuance and per-retention lifetime checks."""

import pytest
from aware_workspace_fs_adapter.repository_delta_retention import (
    DeltaRetentionOwnerRefusal,
    FilesystemDeltaRetentionFactory,
    FilesystemDeltaRetentionOwner,
)
from aware_workspace_fs_adapter.repository_delta_store import (
    WorkspaceRepositoryDeltaStore,
)


def test_physical_owner_cannot_be_forged_and_adoption_checks_type_first(tmp_path):
    factory = FilesystemDeltaRetentionFactory.filesystem(state_root=tmp_path)

    class Duck:
        @property
        def repository_binding_ref(self):
            pytest.fail("duck attributes were read before original type verification")

    with pytest.raises(DeltaRetentionOwnerRefusal, match="retention_owner_mismatch"):
        factory.retain_owner(Duck(), expected_binding_ref="binding:one")
    with pytest.raises(DeltaRetentionOwnerRefusal, match="retention_owner_mismatch"):
        object.__new__(FilesystemDeltaRetentionOwner).retire_owner()


def test_admitted_physical_call_can_finish_during_independent_retirement(
    tmp_path, monkeypatch
):
    raw = WorkspaceRepositoryDeltaStore(
        state_root=tmp_path, repository_binding_ref="binding:one"
    )
    factory = FilesystemDeltaRetentionFactory.filesystem(state_root=tmp_path)
    owner = factory.retain_owner(raw, expected_binding_ref="binding:one")
    original = WorkspaceRepositoryDeltaStore.record_body

    def retire_then_complete(store, content):
        owner.retire_owner()
        return original(store, content)

    with monkeypatch.context() as patch:
        patch.setattr(
            WorkspaceRepositoryDeltaStore, "record_body", retire_then_complete
        )
        ref = owner.record_body(b"admitted before retirement")
    assert raw.resolve_body(ref) == b"admitted before retirement"
    with pytest.raises(DeltaRetentionOwnerRefusal):
        owner.resolve_body(ref)
