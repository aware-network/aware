"""Public setup over real FS/UV owners; no domain materialization."""

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupRequest,
    PackageManagerReceipt,
    WorkspaceSetupClient,
)


def start(root, *, uv=False):
    client = WorkspaceSetupClient.filesystem(
        repository_root=root, uv_executable=Path(shutil.which("uv")) if uv else None
    )
    repo = client.create_repository("example", license_expression="MIT")
    return client, repo


def package(
    repo,
    *,
    module="greeting",
    package="client",
    distribution="greeting-client",
    dependencies=(),
):
    workspace = repo.create_workspace("application")
    mod = workspace.create_module(module)
    return mod.create_python_package(
        package,
        distribution=distribution,
        import_root=distribution.replace("-", "_"),
        dependencies=dependencies,
    )


def bodies(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def owned_package(
    repo, owner, *, path=None, distribution="example-support", dependencies=()
):
    target = repo
    if owner != "repository":
        target = repo.create_workspace("application")
    if owner == "module":
        target = target.create_module("example")
    return target.create_python_package(
        "support",
        distribution=distribution,
        import_root=distribution.replace("-", "_"),
        path=path,
        dependencies=dependencies,
    )


@pytest.mark.parametrize("owner", ["repository", "workspace", "module"])
def test_owned_creation_registration_repeat_and_authored_source(tmp_path, owner):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        result = owned_package(repo, owner, path="libs/custom/python")
        prefix = {
            "repository": "",
            "workspace": "workspaces/application/",
            "module": "workspaces/application/modules/example/",
        }[owner]
        manifest = {
            "repository": "aware.repo.toml",
            "workspace": "aware.workspace.toml",
            "module": "aware.module.toml",
        }[owner]
        data = tomllib.loads((tmp_path / (prefix + manifest)).read_text())
        if owner == "module":
            assert (
                data["packages"][0]["manifest"] == "libs/custom/python/pyproject.toml"
            )
        else:
            key = "repo" if owner == "repository" else "workspace"
            assert data[key]["codes"] == ["libs/custom/python/pyproject.toml"]
        source = tmp_path / (
            prefix + "libs/custom/python/src/example_support/__init__.py"
        )
        source.write_text("answer = 42\n")
        before = bodies(tmp_path)
        assert result.receipt.status == "succeeded"
        assert (
            owned_package(repo, owner, path="libs/custom/python").receipt.status
            == "unchanged"
        )
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("owner", ["repository", "workspace"])
def test_support_codes_append_preserves_parent_sections(tmp_path, owner):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        target = repo if owner == "repository" else repo.create_workspace("application")
        parent = tmp_path / (
            "aware.repo.toml"
            if owner == "repository"
            else "workspaces/application/aware.workspace.toml"
        )
        parent.write_text(parent.read_text() + '\n[custom]\npolicy = "retain"\n')
        for n in ("first", "second"):
            target.create_python_package(n, distribution=n, import_root=n)
        data = tomllib.loads(parent.read_text())
        assert data["custom"] == {"policy": "retain"}
        assert data["repo" if owner == "repository" else "workspace"]["codes"] == [
            "libs/first/python/pyproject.toml",
            "libs/second/python/pyproject.toml",
        ]


@pytest.mark.parametrize(
    "owner, workspace, module",
    [
        ("repository", "application", ""),
        ("repository", "", "example"),
        ("workspace", "", ""),
        ("workspace", "application", "example"),
        ("module", "", "example"),
        ("module", "application", ""),
    ],
)
def test_owner_dimensions_refuse_before_writes(tmp_path, owner, workspace, module):
    with start(tmp_path)[0] as client:
        before = bodies(tmp_path)
        request = ArchitectureSetupRequest(
            "python_package",
            name="support",
            owner=owner,
            workspace=workspace,
            module=module,
            path="libs/support/python",
            distribution="support",
            import_root="support",
        )
        with pytest.raises(ArchitectureSetupError, match="owner_selection_conflicts"):
            client.apply(request)
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("ancestor", [True, False])
@pytest.mark.parametrize("owner", ["repository", "workspace"])
def test_support_registration_cannot_cross_existing_child_owner(
    tmp_path, owner, ancestor
):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        if owner == "repository":
            # Use an explicit Workspace directory beneath an allowed support surface.
            parent = tmp_path / "aware.repo.toml"
            parent.write_text(
                parent.read_text().replace(
                    'workspaces_dir = "workspaces"', 'workspaces_dir = "libs"'
                )
            )
            repo.create_workspace("child", path="child")
            target = repo
        else:
            target = repo.create_workspace("application")
            target.create_module("child", path="libs/child")
        path = "libs/child" if ancestor else "libs/child/support/python"
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="crosses_child_ownership"):
            target.create_python_package(
                "support", distribution="support", import_root="support", path=path
            )
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("owner", ["repository", "workspace"])
def test_new_child_owner_cannot_adopt_existing_support(tmp_path, owner):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        if owner == "repository":
            parent = tmp_path / "aware.repo.toml"
            parent.write_text(
                parent.read_text().replace(
                    'workspaces_dir = "workspaces"', 'workspaces_dir = "libs"'
                )
            )
            target = repo
        else:
            target = repo.create_workspace("application")
        target.create_python_package(
            "support", distribution="support", import_root="support"
        )
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="crosses_child_ownership"):
            if owner == "repository":
                repo.create_workspace("child", path="support")
            else:
                target.create_module("child", path="libs/support")
        assert bodies(tmp_path) == before


def test_three_owners_join_registered_dependencies_and_real_locks(tmp_path):
    with start(tmp_path, uv=True)[0] as client:
        repo = client.repository()
        owned_package(repo, "repository", distribution="example-base")
        owned_package(
            repo,
            "workspace",
            distribution="example-support",
            dependencies=("example-base>=0.1,<0.2",),
        )
        owned_package(
            repo,
            "module",
            distribution="example-client",
            dependencies=("example-support>=0.1,<0.2",),
        )
        assert repo.align_package_manager().status == "succeeded"
        assert repo.align_package_manager().status == "unchanged"
        data = tomllib.loads((tmp_path / "pyproject.toml").read_text())
        assert len(data["tool"]["uv"]["workspace"]["members"]) == 3
        updated, checked = repo.update_locks()[0], repo.check_locks()[0]
        assert updated.returncode == checked.returncode == 0, (
            updated.stderr + checked.stderr
        )
        assert (
            updated.after_lock_sha256
            == checked.before_lock_sha256
            == checked.after_lock_sha256
        )
        checkout = next(
            p for p in Path(__file__).parents if (p / "aware.repo.toml").exists()
        )
        oracle = subprocess.run(
            [
                str(checkout / ".venv/bin/aware-cli"),
                "workspace",
                "package-manager-manifest",
                "--repository-root",
                str(tmp_path),
                "--plan",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert oracle.returncode == 0, oracle.stdout + oracle.stderr
        assert json.loads(oracle.stdout)["plan"]["proposed_write_paths"] == []


def test_duplicate_normalized_distribution_refuses_creation_across_owners(tmp_path):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        owned_package(repo, "repository", distribution="example-base")
        workspace = repo.create_workspace("application")
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="duplicate_distribution"):
            workspace.create_python_package(
                "other", distribution="example.base", import_root="other"
            )
        assert bodies(tmp_path) == before


def test_future_semantic_setup_has_no_guessed_python_fallback(tmp_path):
    with start(tmp_path)[0] as client:
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="unsupported_setup_operation"):
            client.apply(ArchitectureSetupRequest("aware_package", owner="repository"))
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("name", ["example-base", "Example_Base", "example.base"])
@pytest.mark.parametrize(
    "binding",
    [
        '{ path = "vendor/original", editable = false }',
        "{ workspace = true, editable = false }",
        '{ index = "private" }',
    ],
)
def test_root_source_policy_conflict_refuses_before_any_write(tmp_path, name, binding):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        package(repo, distribution="example-base")
        (tmp_path / "pyproject.toml").write_text(
            f'[tool.uv.sources]\n"{name}" = {binding}\n'
        )
        before = bodies(tmp_path)
        with pytest.raises(
            ArchitectureSetupError, match="explicit_source_policy_requires_review"
        ):
            client.preview(ArchitectureSetupRequest("package_manager"))
        with pytest.raises(
            ArchitectureSetupError, match="explicit_source_policy_requires_review"
        ):
            repo.align_package_manager()
        assert bodies(tmp_path) == before


def test_root_alignment_preserves_unrelated_explicit_source_policy(tmp_path):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        package(repo, distribution="example-base")
        (tmp_path / "pyproject.toml").write_text(
            "[tool.uv.sources]\nExample_Base = { workspace = true }\n"
            'external = { path = "vendor/original", editable = false }\n'
        )
        repo.align_package_manager()
        sources = tomllib.loads((tmp_path / "pyproject.toml").read_text())["tool"][
            "uv"
        ]["sources"]
        assert sources["example-base"] == {"workspace": True}
        assert sources["external"] == {"path": "vendor/original", "editable": False}
        assert repo.align_package_manager().status == "unchanged"


@pytest.mark.parametrize("check", [False, True])
@pytest.mark.parametrize("after_state", ["changed", "absent", "unavailable"])
def test_lock_timeout_preserves_effect_evidence_without_retry(
    tmp_path, monkeypatch, check, after_state
):
    from aware_workspace_fs_adapter.architecture_setup import (
        FilesystemArchitectureSetup,
    )

    with start(tmp_path, uv=True)[0] as client:
        repo = client.repository()
        package(repo)
        repo.align_package_manager()
        lock = tmp_path / "uv.lock"
        lock.write_bytes(b"before lock\n")
        calls = []
        timed_out = False
        original_read = FilesystemArchitectureSetup.read

        def run(command, **kwargs):
            nonlocal timed_out
            calls.append(tuple(command))
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "uv 0.11.19\n", "")
            assert kwargs["timeout"] == 120
            lock.write_bytes(b"changed lock\n")
            if after_state == "absent":
                lock.unlink()
            timed_out = True
            raise subprocess.TimeoutExpired(
                command, 120, output=b"partial stdout\xff", stderr=b"partial stderr\n"
            )

        def read(physical, path):
            if timed_out and path == "uv.lock" and after_state == "unavailable":
                raise PermissionError("cannot observe lock")
            return original_read(physical, path)

        monkeypatch.setattr(subprocess, "run", run)
        monkeypatch.setattr(FilesystemArchitectureSetup, "read", read)
        with pytest.raises(
            ArchitectureSetupError, match="uv_timeout_inspect_lock_before_retry"
        ) as caught:
            (repo.check_locks if check else repo.update_locks)()
        evidence = caught.value.receipt
        assert isinstance(evidence, PackageManagerReceipt)
        assert evidence.command == calls[1]
        assert calls[1] == (
            str(Path(shutil.which("uv"))),
            "lock",
            "--offline",
            "--no-python-downloads",
            "--no-progress",
            "--project",
            str(tmp_path),
        ) + (("--check",) if check else ())
        assert len(calls) == 2  # Version query, then exactly one lock attempt.
        assert evidence.operation == ("check_locks" if check else "update_locks")
        assert evidence.resolution_root == str(tmp_path)
        assert evidence.returncode is None
        assert evidence.status == "uncertain"
        assert (
            evidence.stdout.encode("utf-8", errors="surrogateescape")
            == b"partial stdout\xff"
        )
        assert evidence.stderr == "partial stderr\n"
        assert evidence.before_lock_observation == "present"
        assert (
            evidence.before_lock_sha256
            == "sha256:" + hashlib.sha256(b"before lock\n").hexdigest()
        )
        assert (
            evidence.after_lock_observation
            == {"changed": "present", "absent": "absent", "unavailable": "unavailable"}[
                after_state
            ]
        )
        assert evidence.after_lock_sha256 == (
            "sha256:" + hashlib.sha256(b"changed lock\n").hexdigest()
            if after_state == "changed"
            else None
        )
        assert "lock_effects_uncertain:inspect_before_retry" in evidence.diagnostics
        if after_state == "unavailable":
            assert (
                "after_lock_observation_failed:PermissionError" in evidence.diagnostics
            )
        assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)


def test_real_four_layer_creation_preserves_physical_repository(tmp_path):
    unrelated = tmp_path / "existing.txt"
    unrelated.write_bytes(b"original\n")
    client, repo = start(tmp_path)
    try:
        workspace = repo.create_workspace("application")
        module = workspace.create_module("greeting")
        # Independently parse the empty Module using Code's canonical grammar.
        from aware_code_module_manifest_contract_runtime import parse_module_manifest

        module_path = (
            tmp_path / "workspaces/application/modules/greeting/aware.module.toml"
        )
        assert parse_module_manifest(module_path.read_bytes()).packages == ()
        result = module.create_python_package(
            "client", distribution="greeting-client", import_root="greeting_client"
        )
        assert result.receipt.status == "succeeded"
        assert unrelated.read_bytes() == b"original\n"
        assert not (tmp_path / ".git").exists()
        assert not (tmp_path / "pyproject.toml").exists()
        assert not (tmp_path / "uv.lock").exists()
        assert (
            parse_module_manifest(module_path.read_bytes()).packages[0].kind == "code"
        )
        repo_manifest = tomllib.loads((tmp_path / "aware.repo.toml").read_text())
        assert repo_manifest["workspaces"] == [
            {"handle": "application", "path": "application"}
        ]
    finally:
        client.close()


def test_preview_is_read_only_and_stale_plan_refuses_before_creation(tmp_path):
    client, _repo = start(tmp_path)
    try:
        request = ArchitectureSetupRequest("workspace", name="new", path="new")
        before = bodies(tmp_path)
        preview = client.preview(request)
        assert bodies(tmp_path) == before
        assert len(preview.changes) == 2
        (tmp_path / "aware.repo.toml").write_bytes(
            before["aware.repo.toml"] + b"\n# concurrent comment\n"
        )
        with pytest.raises(ArchitectureSetupError, match="setup_plan_changed"):
            client.apply(request, expected_plan_sha256=preview.plan_sha256)
        assert not (tmp_path / "workspaces/new").exists()
        fresh = client.preview(request)
        assert (
            client.apply(request, expected_plan_sha256=fresh.plan_sha256).status
            == "succeeded"
        )
    finally:
        client.close()


def test_existing_repository_and_authored_source_survive_repeat_setup(tmp_path):
    client, repo = start(tmp_path)
    try:
        package(repo)
        repo.align_package_manager()
        source = (
            tmp_path
            / "workspaces/application/modules/greeting/libs/client/python/src/greeting_client/__init__.py"
        )
        source.write_text("answer = 42\n")
        before = bodies(tmp_path)
        assert (
            client.create_repository("example", license_expression="MIT").receipt.status
            == "unchanged"
        )
        assert package(repo).receipt.status == "unchanged"
        assert bodies(tmp_path) == before
        assert source.read_text() == "answer = 42\n"
        with pytest.raises(ArchitectureSetupError, match="conflicts"):
            client.create_repository("other", license_expression="MIT")
    finally:
        client.close()


@pytest.mark.parametrize(
    "path", ["../escape", "/outside", "a/../b", "a\\b", "a/*", "a//b"]
)
def test_invalid_child_paths_refuse_without_effects(tmp_path, path):
    client, repo = start(tmp_path)
    try:
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError):
            repo.create_workspace("bad", path=path)
        assert bodies(tmp_path) == before
    finally:
        client.close()


def test_symlinked_child_and_root_refuse(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    client, repo = start(root)
    try:
        (root / "workspaces").symlink_to(outside, target_is_directory=True)
        with pytest.raises(ArchitectureSetupError, match="source_observation_refused"):
            repo.create_workspace("application")
        assert not list(outside.iterdir())
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        with pytest.raises(ArchitectureSetupError, match="symlink"):
            WorkspaceSetupClient.filesystem(repository_root=alias)
    finally:
        client.close()


def test_overlapping_registrations_refuse(tmp_path):
    client, repo = start(tmp_path)
    try:
        repo.create_workspace("first", path="first")
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="overlapping"):
            repo.create_workspace("second", path="first/nested")
        assert bodies(tmp_path) == before
    finally:
        client.close()


def test_partial_creation_retains_file_effects_and_original_registration(
    tmp_path, monkeypatch
):
    import aware_workspace_fs_adapter.architecture_setup as fs
    from aware_file_system.confined_mutation import ConfinedMutationKind

    client, repo = start(tmp_path)
    original = fs.mutate_confined_file
    before = (tmp_path / "aware.repo.toml").read_bytes()

    def fail_parent(**kwargs):
        if kwargs["request"].kind is ConfinedMutationKind.UPDATE:
            raise OSError("injected parent publication failure")
        return original(**kwargs)

    monkeypatch.setattr(fs, "mutate_confined_file", fail_parent)
    try:
        with pytest.raises(ArchitectureSetupError) as caught:
            repo.create_workspace("application")
        receipt = caught.value.receipt
        assert receipt.status == "uncertain"
        assert receipt.written_paths == ("workspaces/application/aware.workspace.toml",)
        assert receipt.remaining_paths == ("aware.repo.toml",)
        assert (tmp_path / "aware.repo.toml").read_bytes() == before
    finally:
        client.close()


def test_target_collision_is_not_adopted(tmp_path):
    client, repo = start(tmp_path)
    try:
        target = tmp_path / "workspaces/application"
        target.mkdir(parents=True)
        (target / "aware.workspace.toml").write_text(
            'aware=2\n[workspace]\nhandle="application"\n'
        )
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="already_exists"):
            repo.create_workspace("application")
        assert bodies(tmp_path) == before
    finally:
        client.close()


def test_package_metadata_and_real_offline_locks(tmp_path):
    client, repo = start(tmp_path, uv=True)
    try:
        package(repo, module="base", distribution="greeting-base")
        package(
            repo,
            module="consumer",
            distribution="greeting-client",
            dependencies=("greeting-base>=0.1,<0.2",),
        )
        assert repo.align_package_manager().status == "succeeded"
        assert repo.align_package_manager().status == "unchanged"
        member = (
            tmp_path
            / "workspaces/application/modules/consumer/libs/client/python/pyproject.toml"
        )
        assert tomllib.loads(member.read_text())["tool"]["uv"]["sources"] == {
            "greeting-base": {"workspace": True}
        }
        updated = repo.update_locks()[0]
        assert updated.returncode == 0, updated.stderr
        checked = repo.check_locks()[0]
        assert checked.returncode == 0, checked.stderr
        assert (
            updated.after_lock_sha256
            == checked.before_lock_sha256
            == checked.after_lock_sha256
        )
        assert "greeting-base" in (tmp_path / "uv.lock").read_text()
        assert not (member.parent / "uv.lock").exists()
        member.write_text(member.read_text().replace(">=0.1,<0.2", ">=0.2,<0.3"))
        with pytest.raises(ArchitectureSetupError, match="configuration_conflicts"):
            repo.check_locks()
    finally:
        client.close()


def test_unregistered_nearer_resolution_root_is_explicitly_refused(tmp_path):
    client, repo = start(tmp_path)
    try:
        package(repo)
        config = tmp_path / "workspaces/application/modules/greeting/pyproject.toml"
        config.write_text("[tool.uv.workspace]\nmembers=[]\n")
        before = bodies(tmp_path)
        with pytest.raises(
            ArchitectureSetupError, match="unregistered_resolution_boundary"
        ):
            repo.align_package_manager()
        assert bodies(tmp_path) == before
    finally:
        client.close()


def test_shadowed_leaf_lock_is_not_silently_ignored(tmp_path):
    client, repo = start(tmp_path, uv=True)
    try:
        package(repo)
        repo.align_package_manager()
        leaf = (
            tmp_path
            / "workspaces/application/modules/greeting/libs/client/python/uv.lock"
        )
        leaf.write_text("original consumer lock\n")
        with pytest.raises(ArchitectureSetupError, match="shadowed_leaf_lock"):
            repo.update_locks()
        assert leaf.read_text() == "original consumer lock\n"
        assert not (tmp_path / "uv.lock").exists()
    finally:
        client.close()


def test_currentness_after_release_and_root_replacement(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    client, repo = start(root)
    root.rename(tmp_path / "retired")
    root.mkdir()
    with pytest.raises(ArchitectureSetupError, match="root_changed"):
        repo.create_workspace("application")
    client.close()
    with pytest.raises(ArchitectureSetupError, match="not_current"):
        repo.create_workspace("application")


def test_canonical_package_projector_agrees_with_setup_projection(tmp_path):
    # The selected CLI is a parity oracle; it performs no materialization or apply.
    client, repo = start(tmp_path)
    try:
        package(repo, module="base", distribution="greeting-base")
        package(
            repo,
            module="consumer",
            distribution="greeting-client",
            dependencies=("greeting-base>=0.1",),
        )
        repo.align_package_manager()
        checkout = next(
            p for p in Path(__file__).parents if (p / "aware.repo.toml").exists()
        )
        result = subprocess.run(
            [
                str(checkout / ".venv/bin/aware-cli"),
                "workspace",
                "package-manager-manifest",
                "--repository-root",
                str(tmp_path),
                "--plan",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["plan"]["proposed_write_paths"] == []
    finally:
        client.close()


def test_neutral_renderer_is_the_original_renderer():
    checkout = next(
        p for p in Path(__file__).parents if (p / "aware.repo.toml").exists()
    )
    path = "workspaces/aware_workspace/modules/workspace/ontology/runtime/python/aware_workspace/materialization/package_manager_toml_runtime.py"
    original = subprocess.run(
        ["git", "show", "492cac2c4419b5de1df6e76b3b1c038f581576db:" + path],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    import aware_workspace_runtime.package_manager_toml as neutral

    old = {
        n.name: ast.dump(n, include_attributes=False)
        for n in ast.parse(original).body
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    }
    new = {
        n.name: ast.dump(n, include_attributes=False)
        for n in ast.parse(Path(neutral.__file__).read_text()).body
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    }
    assert new and all(old[name] == body for name, body in new.items())


def test_creation_does_not_implicitly_select_uv_or_semantic_runtime(tmp_path):
    code = f"""
from pathlib import Path
import sys
from aware_workspace_sdk.architecture_setup import WorkspaceSetupClient
with WorkspaceSetupClient.filesystem(repository_root=Path({str(tmp_path)!r})) as c:
    r=c.create_repository("example",license_expression="MIT")
    m=r.create_workspace("application").create_module("greeting")
    m.create_python_package("client",distribution="greeting-client",import_root="greeting_client")
assert not any(n == "aware_workspace" or n.startswith("aware_workspace.") for n in sys.modules)
assert not any("orm_models" in n or "service_sdk_adapter" in n for n in sys.modules)
assert not any(n.startswith("aware_issue") for n in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def existing_support_catalog(root, repo, *, nested=True, mixed=True):
    """Existing locators and bodies are preserved by structural setup."""
    repo.create_workspace("application")
    repository_manifest = root / "aware.repo.toml"
    workspace_manifest = root / "workspaces/application/aware.workspace.toml"
    repository_codes = (
        ["tools/cli/pyproject.toml", "tools/cli/compile_pack/pyproject.toml"]
        if nested
        else []
    )
    workspace_codes = (
        ["libs/comms/python/pyproject.toml", "libs/comms/dart/pubspec.yaml"]
        if mixed
        else []
    )
    for parent, codes in (
        (repository_manifest, repository_codes),
        (workspace_manifest, workspace_codes),
    ):
        parent.write_text(
            parent.read_text().replace("codes = []", "codes = " + json.dumps(codes))
        )
        for index, manifest in enumerate(codes):
            target = parent.parent / manifest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f'[project]\nname = "original-{index}"\nversion = "0.1.0"\n'
                if manifest.endswith(".toml")
                else "name: original_dart\n# retain exact bytes\n"
            )


@pytest.mark.parametrize("operation", ["repository", "workspace", "module"])
def test_structural_setup_preserves_nested_and_mixed_existing_codes(
    tmp_path, operation
):
    with start(tmp_path)[0] as client:
        existing_support_catalog(tmp_path, client.repository())
        before = bodies(tmp_path)
        if operation == "repository":
            request = ArchitectureSetupRequest(
                operation, name="example", license_expression="MIT"
            )
            writes = set()
        elif operation == "workspace":
            request = ArchitectureSetupRequest(
                operation, name="additional", path="additional"
            )
            writes = {
                "aware.repo.toml",
                "workspaces/additional/aware.workspace.toml",
            }
        else:
            request = ArchitectureSetupRequest(
                operation,
                workspace="application",
                name="platform",
                path="modules/platform",
            )
            writes = {
                "workspaces/application/aware.workspace.toml",
                "workspaces/application/modules/platform/aware.module.toml",
            }
        preview = client.preview(request)
        assert bodies(tmp_path) == before
        assert {change.path for change in preview.changes} == writes
        receipt = client.apply(request, expected_plan_sha256=preview.plan_sha256)
        assert receipt.status == ("succeeded" if writes else "unchanged")
        after = bodies(tmp_path)
        assert {path for path in after if before.get(path) != after[path]} == writes
        for path, body in before.items():
            if path not in writes:
                assert after[path] == body
        for path, owner in (
            ("aware.repo.toml", "repo"),
            ("workspaces/application/aware.workspace.toml", "workspace"),
        ):
            assert (
                tomllib.loads(after[path].decode())[owner]["codes"]
                == tomllib.loads(before[path].decode())[owner]["codes"]
            )
        assert client.apply(request).status == "unchanged"
        assert bodies(tmp_path) == after


@pytest.mark.parametrize("operation", ["python_package", "package_manager"])
@pytest.mark.parametrize("incompatible", ["nested", "mixed"])
def test_python_profile_still_refuses_incompatible_support_catalog(
    tmp_path, operation, incompatible
):
    with start(tmp_path)[0] as client:
        existing_support_catalog(
            tmp_path,
            client.repository(),
            nested=incompatible == "nested",
            mixed=incompatible == "mixed",
        )
        before = bodies(tmp_path)
        request = (
            ArchitectureSetupRequest(
                operation,
                name="support",
                owner="repository",
                path="libs/support/python",
                distribution="support",
                import_root="support",
            )
            if operation == "python_package"
            else ArchitectureSetupRequest(operation)
        )
        code = (
            "duplicate_or_overlapping_code_registration"
            if incompatible == "nested"
            else "support_profile_requires_python_manifest"
        )
        with pytest.raises(ArchitectureSetupError, match=code):
            client.apply(request)
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("owner", ["repo", "workspace"])
@pytest.mark.parametrize("second", ["pyproject.toml", "pubspec.yaml"])
def test_structural_setup_rejects_duplicate_support_root_before_writes(
    tmp_path, owner, second
):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        repo.create_workspace("application")
        parent = tmp_path / (
            "aware.repo.toml"
            if owner == "repo"
            else "workspaces/application/aware.workspace.toml"
        )
        codes = ["libs/support/python/pyproject.toml", "libs/support/python/" + second]
        parent.write_text(
            parent.read_text().replace("codes = []", "codes = " + json.dumps(codes))
        )
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="duplicate_or_overlapping"):
            client.repository().workspace("application").create_module("platform")
        assert bodies(tmp_path) == before


def test_structural_setup_guard_detects_mixed_catalog_drift_before_writes(tmp_path):
    with start(tmp_path)[0] as client:
        existing_support_catalog(tmp_path, client.repository())
        request = ArchitectureSetupRequest(
            "module", workspace="application", name="platform", path="modules/platform"
        )
        preview = client.preview(request)
        parent = tmp_path / "workspaces/application/aware.workspace.toml"
        parent.write_text(parent.read_text() + '\n[custom]\npolicy = "advanced"\n')
        before = bodies(tmp_path)
        with pytest.raises(ArchitectureSetupError, match="setup_plan_changed"):
            client.apply(request, expected_plan_sha256=preview.plan_sha256)
        assert bodies(tmp_path) == before


@pytest.mark.parametrize("owner", ["repo", "workspace"])
def test_structural_support_cannot_claim_entire_owner_root(tmp_path, owner):
    with start(tmp_path)[0] as client:
        repo = client.repository()
        repo.create_workspace("application")
        parent = tmp_path / (
            "aware.repo.toml"
            if owner == "repo"
            else "workspaces/application/aware.workspace.toml"
        )
        parent.write_text(
            parent.read_text().replace("codes = []", 'codes = ["pubspec.yaml"]')
        )
        before = bodies(tmp_path)
        with pytest.raises(
            ArchitectureSetupError, match="support_package_requires_explicit_root"
        ):
            client.repository().workspace("application").create_module("platform")
        assert bodies(tmp_path) == before


def test_selected_cli_previews_module_in_preserved_existing_catalog(tmp_path):
    with start(tmp_path)[0] as client:
        existing_support_catalog(tmp_path, client.repository())
    before = bodies(tmp_path)
    checkout = next(
        p for p in Path(__file__).parents if (p / "aware.repo.toml").exists()
    )
    result = subprocess.run(
        [
            str(checkout / ".venv/bin/aware-cli"),
            "workspace",
            "setup",
            "module",
            "--repository-root",
            str(tmp_path),
            "--workspace",
            "application",
            "--name",
            "platform",
            "--preview",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "planned"
    assert set(payload["proposed_write_paths"]) == {
        "workspaces/application/aware.workspace.toml",
        "workspaces/application/modules/platform/aware.module.toml",
    }
    assert bodies(tmp_path) == before
