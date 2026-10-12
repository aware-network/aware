"""Registered resolution roots, real offline UV discovery and effect evidence."""

import hashlib
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupRequest,
    WorkspaceSetupClient,
)


def topology(root):
    client = WorkspaceSetupClient.filesystem(
        repository_root=root, uv_executable=Path(shutil.which("uv"))
    )
    repo = client.create_repository("example", license_expression="MIT")
    repo.create_python_package(
        "base", distribution="example-base", import_root="example_base"
    )
    one = repo.create_workspace("one")
    one.create_python_package(
        "support",
        distribution="example-support",
        import_root="example_support",
        dependencies=("example-base>=0.1,<0.2",),
    )
    two = repo.create_workspace("two")
    two.create_python_package(
        "local", distribution="example-local", import_root="example_local"
    )
    two.create_module("app").create_python_package(
        "client",
        distribution="example-client",
        import_root="example_client",
        dependencies=("example-support>=0.1,<0.2", "example-local>=0.1,<0.2"),
    )
    return client, repo, one, two


def align(repo, one, two):
    one.align_package_manager()
    two.align_package_manager()
    repo.align_package_manager()


def files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_three_actual_roots_cross_context_dependencies_and_leaf_discovery(tmp_path):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        for owner in (repo, one, two):
            assert owner.align_package_manager().status == "unchanged"
            before = files(tmp_path)
            updated = owner.update_locks()[0]
            assert updated.returncode == 0, updated.stderr
            selected = Path(updated.resolution_root)
            lock = selected / "uv.lock"
            assert (
                updated.after_lock_sha256
                == "sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
            )
            checked = owner.check_locks()[0]
            assert checked.returncode == 0, checked.stderr
            assert (
                checked.after_lock_sha256
                == updated.after_lock_sha256
                == checked.before_lock_sha256
            )
            delta = set(files(tmp_path)) - set(before)
            assert delta == {lock.relative_to(tmp_path).as_posix()}
        root_payload = tomllib.loads((tmp_path / "pyproject.toml").read_text())
        assert root_payload["tool"]["uv"]["workspace"]["members"] == [
            "libs/base/python"
        ]
        leaf = tmp_path / "workspaces/two/modules/app/libs/client/python"
        payload = tomllib.loads((leaf / "pyproject.toml").read_text())
        assert payload["tool"]["uv"]["sources"]["example-local"] == {"workspace": True}
        source = payload["tool"]["uv"]["sources"]["example-support"]
        assert (
            leaf / source["path"]
        ).resolve() == tmp_path / "workspaces/one/libs/support/python"
        # Exercise UV's actual leaf discovery; --project alone is not the evidence.
        before = files(tmp_path)
        result = subprocess.run(
            [
                shutil.which("uv"),
                "lock",
                "--offline",
                "--no-python-downloads",
                "--no-progress",
                "--project",
                str(leaf),
                "--check",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert files(tmp_path) == before and not (leaf / "uv.lock").exists()


def test_registered_boundary_is_observed_without_foreign_alignment(tmp_path):
    client, repo, one, _ = topology(tmp_path)
    with client:
        one.align_package_manager()
        foreign = tmp_path / "workspaces/one/pyproject.toml"
        body = foreign.read_bytes()
        receipt = repo.align_package_manager()
        assert foreign.read_bytes() == body
        assert all(
            not path.startswith("workspaces/one/") for path in receipt.written_paths
        )


def test_workspace_lock_requires_explicit_alignment(tmp_path):
    client, _, one, _ = topology(tmp_path)
    with client, pytest.raises(ArchitectureSetupError, match="alignment_required"):
        one.update_locks()
    assert not list(tmp_path.rglob("uv.lock"))


@pytest.mark.parametrize("workspace", ["one", "two"])
def test_context_change_and_absent_intermediate_are_digest_bound(tmp_path, workspace):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        request = ArchitectureSetupRequest("package_manager", workspace=workspace)
        preview = client.preview(request)
        inserted = tmp_path / "workspaces/two/modules/pyproject.toml"
        assert inserted.relative_to(tmp_path).as_posix() in preview.input_paths
        inserted.write_text("[tool.uv.workspace]\nmembers=[]\n")
        before = files(tmp_path)
        with pytest.raises(
            ArchitectureSetupError, match="unregistered_resolution_boundary"
        ):
            client.apply(request, expected_plan_sha256=preview.plan_sha256)
        assert files(tmp_path) == before


@pytest.mark.parametrize("name", ["example-base", "Example_Base", "example.base"])
@pytest.mark.parametrize(
    "value",
    [
        '{ path = "wrong", editable = true }',
        '{ path = "../../../libs/base/python", editable = false }',
        "{ workspace = true }",
    ],
)
def test_workspace_source_policy_is_not_rewritten(tmp_path, name, value):
    client, _, one, _ = topology(tmp_path)
    with client:
        path = tmp_path / "workspaces/one/pyproject.toml"
        path.write_text(f'[tool.uv.sources]\n"{name}" = {value}\n')
        before = files(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="explicit_source_policy"):
            one.align_package_manager()
        assert files(tmp_path) == before


@pytest.mark.parametrize(
    "manifest",
    [
        '[tool.uv.workspace]\nmembers=["unregistered"]\n',
        '[tool.uv.workspace]\nmembers=["libs/*/python"]\n',
        '[tool.uv.workspace]\nmembers=[]\nexclude=["libs/support/python"]\n',
        "[tool.uv]\nmanaged=false\n",
    ],
)
def test_authored_membership_policy_refuses_before_writes(tmp_path, manifest):
    client, _, one, _ = topology(tmp_path)
    with client:
        (tmp_path / "workspaces/one/pyproject.toml").write_text(manifest)
        before = files(tmp_path)
        with pytest.raises(ArchitectureSetupError):
            one.align_package_manager()
        assert files(tmp_path) == before


@pytest.mark.parametrize(
    "path,body",
    [
        ("workspaces/one/uv.toml", "offline=true\n"),
        ("uv.toml", "offline=true\n"),
        (
            "workspaces/two/modules/pyproject.toml",
            '[project]\nname="other"\nversion="0.1.0"\n',
        ),
        (
            "workspaces/one/pyproject.toml",
            '[project]\nname="manager"\nversion="0.1.0"\n',
        ),
    ],
)
def test_unqualified_context_refuses_without_dispatch(
    tmp_path, monkeypatch, path, body
):
    client, repo, _, _ = topology(tmp_path)
    with client:
        (tmp_path / path).write_text(body)
        before = files(tmp_path)
        calls = []
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append(a))
        with pytest.raises(ArchitectureSetupError):
            repo.update_locks()
        assert calls == [] and files(tmp_path) == before


@pytest.mark.parametrize("phase", ["version", "lock"])
def test_selected_metadata_drift_before_or_after_dispatch(tmp_path, monkeypatch, phase):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        calls = []
        manifest = tmp_path / "workspaces/one/pyproject.toml"
        lock = tmp_path / "workspaces/one/uv.lock"

        def run(command, **kwargs):
            calls.append(command)
            if command[1] == "--version":
                if phase == "version":
                    manifest.write_bytes(manifest.read_bytes() + b"# drift\n")
                return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
            lock.write_bytes(b"observed effect\n")
            manifest.write_bytes(manifest.read_bytes() + b"# drift\n")
            return subprocess.CompletedProcess(command, 0, "stdout", "stderr")

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError) as caught:
            one.update_locks()
        assert len(calls) == (1 if phase == "version" else 2)
        if phase == "lock":
            receipt = caught.value.receipt
            assert receipt.status == "uncertain" and receipt.returncode == 0
            assert receipt.stdout == "stdout" and receipt.stderr == "stderr"
            assert receipt.resolution_root == str(tmp_path / "workspaces/one")
            assert receipt.after_lock_observation == "unavailable"
            assert receipt.command[-1] == str(tmp_path / "workspaces/one")
        assert not (tmp_path / "uv.lock").exists()


@pytest.mark.parametrize("check", [False, True])
def test_workspace_timeout_keeps_selected_lock_evidence(tmp_path, monkeypatch, check):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        lock = tmp_path / "workspaces/one/uv.lock"
        lock.write_bytes(b"before")
        root_lock = tmp_path / "uv.lock"
        root_lock.write_bytes(b"foreign")
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
            lock.write_bytes(b"after")
            raise subprocess.TimeoutExpired(
                command, 120, output=b"partial", stderr=b"error"
            )

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError) as caught:
            (one.check_locks if check else one.update_locks)()
        receipt = caught.value.receipt
        assert receipt.status == "uncertain" and receipt.stdout == "partial"
        assert (
            receipt.before_lock_sha256
            == "sha256:" + hashlib.sha256(b"before").hexdigest()
        )
        assert (
            receipt.after_lock_sha256
            == "sha256:" + hashlib.sha256(b"after").hexdigest()
        )
        assert root_lock.read_bytes() == b"foreign" and len(calls) == 2


def test_lock_check_changed_bytes_keeps_receipt(tmp_path, monkeypatch):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)

        def run(command, **kwargs):
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
            (tmp_path / "workspaces/one/uv.lock").write_bytes(b"changed")
            return subprocess.CompletedProcess(command, 0, "changed", "")

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError) as caught:
            one.check_locks()
        assert caught.value.receipt.status == "uncertain"
        assert caught.value.receipt.after_lock_observation == "present"


def test_unaligned_dependency_owner_and_shadowed_lock_are_refused(tmp_path):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        root = tmp_path / "pyproject.toml"
        root.write_bytes(root.read_bytes() + b"# same config\n")
        # An external dependency's manifest still needs its original context.
        leaf = tmp_path / "libs/base/python/pyproject.toml"
        leaf.write_bytes(
            leaf.read_bytes() + b'\n[tool.uv.sources]\nexternal={path="vendor"}\n'
        )
        with pytest.raises(
            ArchitectureSetupError, match="dependency_context_alignment_required"
        ):
            one.update_locks()
        repo.align_package_manager()  # Preserve the unrelated policy, align its formatting.
        one.update_locks()
        nested_lock = tmp_path / "workspaces/one/libs/uv.lock"
        nested_lock.write_text("shadowed")
        with pytest.raises(ArchitectureSetupError, match="shadowed_leaf_lock"):
            one.update_locks()


def test_unregistered_workspace_selector_has_no_effect(tmp_path):
    client, _, _, _ = topology(tmp_path)
    with client:
        before = files(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="workspace_not_registered"):
            client.preview(
                ArchitectureSetupRequest("package_manager", workspace="absent")
            )
        assert files(tmp_path) == before


@pytest.mark.parametrize("phase", ["version", "lock"])
def test_selected_directory_replacement_refuses_with_effect_evidence(
    tmp_path, monkeypatch, phase
):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        selected = tmp_path / "workspaces/one"
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            is_version = command[1] == "--version"
            if (phase == "version") == is_version:
                selected.rename(tmp_path / "workspaces/retained-one")
                shutil.copytree(tmp_path / "workspaces/retained-one", selected)
            return subprocess.CompletedProcess(
                command, 0, "uv 0.11.19\n" if is_version else "output", ""
            )

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError) as caught:
            one.update_locks()
        assert len(calls) == (1 if phase == "version" else 2)
        if phase == "lock":
            assert caught.value.receipt.status == "uncertain"
            assert caught.value.receipt.after_lock_observation == "unavailable"


def test_lock_dispatch_oserror_keeps_selected_receipt(tmp_path, monkeypatch):
    client, repo, one, two = topology(tmp_path)
    with client:
        align(repo, one, two)
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
            raise OSError("process dispatch failed")

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError) as caught:
            one.update_locks()
        receipt = caught.value.receipt
        assert receipt.status == "uncertain" and receipt.returncode is None
        assert receipt.resolution_root == str(tmp_path / "workspaces/one")
        assert receipt.after_lock_observation == "absent" and len(calls) == 2


def test_external_ancestor_created_after_version_refuses_before_lock(
    tmp_path, monkeypatch
):
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    client, repo, one, two = topology(prepared)
    with client:
        align(repo, one, two)
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            (tmp_path / "pyproject.toml").write_text(
                "[tool.uv.workspace]\nmembers=[]\n"
            )
            return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(ArchitectureSetupError, match="external_ancestor_project"):
            one.update_locks()
        assert len(calls) == 1 and not list(prepared.rglob("uv.lock"))


def test_empty_registered_workspace_gets_its_own_lock(tmp_path):
    with WorkspaceSetupClient.filesystem(
        repository_root=tmp_path, uv_executable=Path(shutil.which("uv"))
    ) as client:
        repo = client.create_repository("empty", license_expression="MIT")
        ws = repo.create_workspace("empty")
        ws.align_package_manager()
        repo.align_package_manager()
        for check in (False, True):
            result = (ws.check_locks if check else ws.update_locks)()[0]
            assert result.returncode == 0, result.stderr
            assert result.resolution_root == str(tmp_path / "workspaces/empty")
        assert not (tmp_path / "uv.lock").exists()
