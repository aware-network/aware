"""Exact-byte currentness over a previously authenticated declaration closure."""

import os

import pytest
from aware_workspace_runtime import source_observation as source_module
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeUnavailable
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    RetainedWorkspaceCompositionProvider,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_declaration_scope_admission import fixture


async def test_unchanged_complete_declaration_revalidation_does_not_reinterpret(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (_, _, observer, _, observed, _):
        calls = []

        def unavailable(*args, **kwargs):
            calls.append("unexpected interpretation")
            raise AssertionError("unchanged admitted declarations were reinterpreted")

        monkeypatch.setattr(LocalCheckoutWorkspaceCompositionProvider, "describe", unavailable)
        monkeypatch.setattr(RetainedWorkspaceCompositionProvider, "describe_captured_bodies", unavailable)
        before = observer.declaration_evidence(observed)
        for _ in range(3):
            current = observer.revalidate_declarations(observed)
            assert current.observation_digest == before.observation_digest
            assert current.started_ns >= before.completed_ns
        assert calls == []


@pytest.mark.parametrize("change", [
    "repository", "workspace", "module", "profile", "package", "delete", "symlink", "same_metadata",
])
async def test_exact_path_revalidation_refuses_every_changed_admitted_body(tmp_path, change):
    async with fixture(tmp_path) as (root, _, observer, _, observed, _):
        paths = {
            "repository": "aware.repo.toml",
            "workspace": "workspaces/kernel/aware.workspace.toml",
            "module": "workspaces/kernel/modules/main/aware.module.toml",
            "profile": "workspaces/kernel/semantic_contract/profiles/kernel.default/aware.semantic_contract_profile.toml",
        }
        path = root / paths.get(change, "workspaces/kernel/modules/main/package/aware.example.toml")
        before = path.read_bytes()
        if change == "delete":
            path.unlink()
        elif change == "symlink":
            path.unlink()
            path.symlink_to(root / "aware.repo.toml")
        elif change == "same_metadata":
            stamp = path.stat()
            path.write_bytes(b"X" * len(before))
            os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        else:
            path.write_bytes(before + b"\nchanged")
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate_declarations(observed)


async def test_undeclared_paths_cannot_change_the_admitted_membership_set(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, _, observed, _):
        original = observer.declaration_evidence(observed)
        extra = root / "unselected/aware.module.toml"
        extra.parent.mkdir()
        extra.write_text('aware=1\n[module]\n')
        observer.revalidate_declarations(observed)
        assert observer.declaration_evidence(observed) == original
        # Only changing a retained parent declaration can admit a new member.
        workspace = root / "workspaces/kernel/aware.workspace.toml"
        workspace.write_bytes(workspace.read_bytes() + b'\n[[workspace.modules]]\nid="new"\npath="../../unselected"\n')
        with pytest.raises(SourceObservationUnavailable):
            observer.revalidate_declarations(observed)


async def test_equal_bytes_with_new_file_metadata_remain_content_current(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, _, observed, _):
        path = root / "aware.repo.toml"
        before = path.read_bytes()
        path.write_bytes(before)
        stamp = path.stat()
        os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns + 1_000_000))
        observer.revalidate_declarations(observed)


@pytest.mark.parametrize("boundary", ["retained_read", "live_capture"])
async def test_parent_loss_at_io_boundaries_refuses_before_revalidation_return(
    tmp_path, monkeypatch, boundary,
):
    async with fixture(tmp_path) as (_, parent, observer, _, observed, _):
        captures = []
        original_capture = source_module.capture_exact_paths
        original_read = observer._store.resolve_body

        def capture(*args, **kwargs):
            captures.append(1)
            value = original_capture(*args, **kwargs)
            if boundary == "live_capture":
                parent.close()
            return value

        def read(*args, **kwargs):
            value = original_read(*args, **kwargs)
            if boundary == "retained_read":
                parent.close()
            return value

        monkeypatch.setattr(source_module, "capture_exact_paths", capture)
        monkeypatch.setattr(observer._store, "resolve_body", read)
        with pytest.raises(WorkspaceCommandLifetimeUnavailable):
            observer.revalidate_declarations(observed)
        assert len(captures) == (0 if boundary == "retained_read" else 1)
