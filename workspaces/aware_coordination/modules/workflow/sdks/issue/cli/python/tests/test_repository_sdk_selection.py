"""The genuine consumer selects Workspace only through its public SDK."""

import builtins
import importlib
import subprocess

import pytest
from aware_workspace_sdk.repository_publication.authority import (
    WorkspaceRepositoryPublicationClient,
)
from test_repository_runtime_orchestration import composed_loop

composed = composed_loop


@pytest.mark.parametrize(
    "blocked", ["aware_workspace_runtime", "aware_workspace_fs_adapter"]
)
def test_real_consumer_never_imports_foreign_implementation(
    composed, monkeypatch, blocked
):
    root, source, _, runtime, _, request = composed
    composition = importlib.import_module("aware_issue_cli.composition")
    original = builtins.__import__
    imports = []

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        caller = (globals or {}).get("__name__")
        if caller == "aware_issue_cli.composition":
            imports.append(name)
            if name == blocked or name.startswith(blocked + "."):
                pytest.fail("Consumer crossed the supplying Workspace SDK boundary")
        return original(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    client = composition.create_repository_client(
        provider=runtime._source._provider, repository_root=root
    )
    result = client.commit_workspace_result(request).to_wire()
    assert result["workspace_result"]["publication_state"] == "published"
    assert result["issue_observation"]["consumption_state"] == "consumed"
    assert result["outcome"] == "completed"
    assert b"- Status: In Progress" in source.read_bytes()
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"1"
    )
    assert "aware_workspace_sdk.repository_publication.authority" in imports


def test_selection_preserves_original_root_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "sdk-selection-example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    target = tmp_path / "repository"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="canonical_absolute_repository_root_required"):
        WorkspaceRepositoryPublicationClient.filesystem(repository_root=alias)
    with pytest.raises(ValueError, match="canonical_absolute_repository_root_required"):
        WorkspaceRepositoryPublicationClient.filesystem(repository_root="relative")
    assert not (target / ".git").exists()


def test_selection_refuses_subclass_without_provider_registration(tmp_path):
    class ForeignClient(WorkspaceRepositoryPublicationClient):
        pass

    with pytest.raises(TypeError, match="Original Workspace SDK client required"):
        ForeignClient.filesystem(repository_root=tmp_path)
    assert list(tmp_path.iterdir()) == []
