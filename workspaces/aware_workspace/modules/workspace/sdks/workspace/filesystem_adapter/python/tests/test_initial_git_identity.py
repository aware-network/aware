"""Prospective metadata observations, not actor or publication authority."""

import os
import subprocess

import pytest
from aware_workspace_fs_adapter.git_identity import observe_initial_git_identity


@pytest.fixture
def root(tmp_path, monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("GIT_") or key == "EMAIL":
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "absent-global"))
    return tmp_path / "customer"


def identities(monkeypatch):
    for name, value in {
        "GIT_AUTHOR_NAME": "Chosen author",
        "GIT_AUTHOR_EMAIL": "author@example.invalid",
        "GIT_COMMITTER_NAME": "Chosen committer",
        "GIT_COMMITTER_EMAIL": "committer@example.invalid",
    }.items():
        monkeypatch.setenv(name, value)


def test_missing_identity_is_no_write_observation(root):
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "unavailable"
    assert result["author"] is None and result["committer"] is None
    assert not result["authorizes_publication"]
    assert not result["authorizes_retry"] and not result["authorizes_redispatch"]
    assert not root.exists()


def test_explicit_effective_identities_are_not_changed_or_created(root, monkeypatch):
    identities(monkeypatch)
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "available"
    assert result["author"] == {
        "name": "Chosen author",
        "email": "author@example.invalid",
    }
    assert result["committer"] == {
        "name": "Chosen committer",
        "email": "committer@example.invalid",
    }
    assert result == observe_initial_git_identity(repository_root=str(root))
    assert not root.exists()


@pytest.mark.parametrize("role", ["AUTHOR", "COMMITTER"])
def test_each_role_is_required(root, monkeypatch, role):
    identities(monkeypatch)
    monkeypatch.delenv(f"GIT_{role}_EMAIL")
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "unavailable"
    assert f"git_{role.lower()}_identity_unavailable" in result["diagnostics"]
    assert not root.exists()


def test_selected_global_config_is_read_without_modifying_it(root, monkeypatch):
    config = root.parent / "customer-global"
    content = "[user]\nname = Explicit customer\nemail = customer@example.invalid\n"
    config.write_text(content)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    before = config.stat()
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "available"
    assert result["author"]["name"] == "Explicit customer"
    assert config.read_text() == content
    assert (config.stat().st_ino, config.stat().st_mtime_ns) == (
        before.st_ino,
        before.st_mtime_ns,
    )
    assert not root.exists()


def test_source_repository_local_identity_is_not_borrowed(root):
    # This invocation's cwd is aware-dev, whose local user config is populated.
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "unavailable"
    assert not root.exists()


@pytest.mark.parametrize(
    "key",
    [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ],
)
def test_repository_redirection_refuses(root, monkeypatch, key):
    identities(monkeypatch)
    monkeypatch.setenv(key, str(root.parent))
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "unavailable"
    assert result["diagnostics"] == ["git_repository_selection_override_refused"]
    assert not root.exists()


def test_symlink_parent_is_not_followed(root, monkeypatch):
    identities(monkeypatch)
    actual = root.parent / "actual"
    actual.mkdir()
    alias = root.parent / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(OSError):
        observe_initial_git_identity(repository_root=str(alias / "target"))
    assert not list(actual.iterdir())


def test_terminal_target_substitution_refuses_and_preserves_foreign_file(
    root, monkeypatch
):
    identities(monkeypatch)
    original = subprocess.run

    def race(*args, **kwargs):
        result = original(*args, **kwargs)
        if "GIT_COMMITTER_IDENT" in args[0]:
            root.write_bytes(b"foreign")
        return result

    monkeypatch.setattr(subprocess, "run", race)
    with pytest.raises(ValueError, match="repository_target_substituted"):
        observe_initial_git_identity(repository_root=str(root))
    assert root.read_bytes() == b"foreign"


def test_git_unavailable_is_not_an_identity_success(root, monkeypatch):
    original = subprocess.run

    def unavailable(*args, **kwargs):
        if "var" in args[0]:
            raise FileNotFoundError("git")
        return original(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", unavailable)
    result = observe_initial_git_identity(repository_root=str(root))
    assert result["status"] == "unavailable"
    assert not root.exists()


@pytest.mark.parametrize(
    "value", ["forged", "Name <> 0 +0000", "Name <mail>\nextra", "Name <mail> 0 bad"]
)
def test_malformed_successful_git_output_refuses(root, monkeypatch, value):
    original = subprocess.run

    def malformed(*args, **kwargs):
        if "var" in args[0]:
            return subprocess.CompletedProcess(args[0], 0, value, "")
        return original(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", malformed)
    assert (
        observe_initial_git_identity(repository_root=str(root))["status"]
        == "unavailable"
    )
