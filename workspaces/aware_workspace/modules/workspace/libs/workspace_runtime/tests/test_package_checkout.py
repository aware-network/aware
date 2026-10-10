from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from aware_workspace_runtime.package_checkout import (
    PackageCheckoutError,
    PackageSourceCheckout,
    verify_package_checkout,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from packaging.markers import default_environment


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def commit_fixture(root: Path) -> None:
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q")
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="consumer"\nworkspaces_dir="workspaces"\n[[workspaces]]\nhandle="main"\npath="main"\n'
    )
    workspace = root / "workspaces/main"
    module = workspace / "modules/family"
    module.mkdir(parents=True)
    (workspace / "aware.workspace.toml").write_text(
        'aware=1\n[workspace]\nhandle="main"\ncodes=["modules/family/a/pyproject.toml","direct/pyproject.toml"]\n[[workspace.modules]]\nid="family"\npath="modules/family"\n'
    )
    (module / "aware.module.toml").write_text(
        "aware=1\n"
        + "".join(
            f'[[packages]]\nid="{name}"\nkind="code"\nmanifest="{name}/pyproject.toml"\n'
            for name in ("a", "b", "c")
        )
    )
    for name in ("a", "b", "c"):
        package = module / name
        package.mkdir()
        (package / "pyproject.toml").write_text(
            f'[project]\nname="sample-{name}"\nversion="1.0.0"\nrequires-python=">=3.12"\ndependencies=[]\n[build-system]\nrequires=["hatchling>=1.27"]\nbuild-backend="hatchling.build"\n'
        )
        (package / "source.py").write_text(f'VALUE = "{name}"\n')
        (package / "resource.bin").write_bytes(b"\x00resource")
    direct = workspace / "direct"
    direct.mkdir()
    (direct / "pyproject.toml").write_text(
        '[project]\nname="sample-direct"\nversion="1.0"\ndependencies=[]\n'
    )
    (direct / "body.txt").write_text("direct")
    commit_fixture(root)
    return root


def manifest(root: Path, name: str) -> Path:
    return root / f"workspaces/main/modules/family/{name}/pyproject.toml"


def change_dependencies(root: Path, name: str, requirements: list[str]) -> None:
    path = manifest(root, name)
    path.write_text(
        path.read_text().replace(
            "dependencies=[]", f"dependencies={json.dumps(requirements)}"
        )
    )


def test_direct_and_module_membership_deduplicate_one_physical_leaf(
    repository: Path, tmp_path: Path
) -> None:
    change_dependencies(
        repository, "a", ["sample-b>=1,<2", "external>=3; python_version >= '3.12'"]
    )
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-a", "sample-a"])
        assert [p["name"] for p in plan["packages"]] == ["sample-a", "sample-b"]
        assert len(plan["packages"][0]["memberships"]) == 2
        assert len(plan["registry_requirements"]) == 1
        assert plan["packages"][0]["build_system"]["requires"] == ["hatchling>=1.27"]
        plan["files"].clear()  # Detached inventory cannot change the live capture.
        target = tmp_path / "checkout"
        receipt = checkout.write(target)
        assert receipt["state"] == "source_checkout_written"
        verified = verify_package_checkout(target)
        assert len(verified["files"]) == 6
        assert not (target / "workspaces/main/modules/family/c").exists()
        assert not any(verified["claims"].values())
        assert (
            target / manifest(repository, "a").relative_to(repository)
        ).read_bytes() == manifest(repository, "a").read_bytes()


def test_direct_workspace_code_does_not_select_module(repository: Path) -> None:
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-direct"])
        assert [p["name"] for p in plan["packages"]] == ["sample-direct"]
        assert len(plan["files"]) == 2


def test_extras_accumulate_transitively_and_cycles_terminate(repository: Path) -> None:
    change_dependencies(repository, "a", ["sample-b[x]", "sample-b[y]"])
    change_dependencies(repository, "b", ["sample-a"])
    path = manifest(repository, "b")
    path.write_text(
        path.read_text()
        + '[project.optional-dependencies]\nx=["sample-c"]\ny=["other>=1; extra == \'y\'"]\n'
    )
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-a"])
        assert [p["name"] for p in plan["packages"]] == [
            "sample-a",
            "sample-b",
            "sample-c",
        ]
        assert plan["packages"][1]["extras"] == ["x", "y"]
        assert plan["registry_requirements"] == ['other>=1; extra == "y"']


def test_inactive_markers_do_not_add_packages_or_forbidden_edges(
    repository: Path,
) -> None:
    change_dependencies(
        repository, "a", ["sample-b; sys_platform == 'unavailable_platform'"]
    )
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-a"], forbidden_packages=["sample-b"])
        assert len(plan["packages"]) == 1


@pytest.mark.parametrize(
    "selection,match",
    [
        ("absent", "not declared"),
        ("sample-a[unknown]", "unknown extras"),
        ("sample-a>=2", "version conflict"),
        ("sample-a @ https://example.invalid/a.whl", "direct URL"),
        ("sample-a; python_version>'3'", "unconditional"),
    ],
)
def test_invalid_selection_refuses(
    repository: Path, selection: str, match: str
) -> None:
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match=match),
    ):
        checkout.resolve([selection])


def test_required_forbidden_edge_is_not_removed(repository: Path) -> None:
    change_dependencies(repository, "a", ["sample-b"])
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="forbidden dependency"),
    ):
        checkout.resolve(["sample-a"], forbidden_packages=["sample-b"])


def test_conflicting_transitive_local_version_refuses(repository: Path) -> None:
    change_dependencies(repository, "a", ["sample-b>=2"])
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="version conflict"),
    ):
        checkout.resolve(["sample-a"])


def test_undeclared_owner_local_source_is_not_registry_fallback(
    repository: Path,
) -> None:
    change_dependencies(repository, "a", ["missing-local"])
    path = manifest(repository, "a")
    path.write_text(
        path.read_text() + "[tool.uv.sources]\nmissing-local={workspace=true}\n"
    )
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="canonical local/artifact admission"),
    ):
        checkout.resolve(["sample-a"])


def test_duplicate_distribution_at_distinct_roots_is_ambiguous(
    repository: Path,
) -> None:
    path = manifest(repository, "b")
    path.write_text(path.read_text().replace("sample-b", "sample-a"))
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="ambiguous package name"),
    ):
        checkout.resolve(["sample-a"])


def test_target_environment_is_complete_and_python_is_checked(repository: Path) -> None:
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="complete PEP"),
    ):
        checkout.resolve(["sample-a"], marker_environment={"python_version": "3.11"})
    target = {
        **default_environment(),
        "python_version": "3.11",
        "python_full_version": "3.11.9",
    }
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="Python incompatible"),
    ):
        checkout.resolve(["sample-a"], marker_environment=target)


@pytest.mark.parametrize(
    "change", ["source", "dependency_metadata", "membership", "new_file", "revision"]
)
def test_drift_refuses_before_creating_destination(
    repository: Path, tmp_path: Path, change: str
) -> None:
    with PackageSourceCheckout(repository) as checkout:
        checkout.resolve(["sample-a"])
        package = manifest(repository, "a").parent
        if change == "source":
            (package / "source.py").write_text("changed")
        elif change == "dependency_metadata":
            change_dependencies(repository, "a", ["sample-b"])
        elif change == "membership":
            path = repository / "workspaces/main/aware.workspace.toml"
            path.write_text(path.read_text() + "\n# edited declaration\n")
        elif change == "new_file":
            (package / "new.py").write_text("new")
        else:
            (package / "source.py").write_text("changed")
            commit_fixture(repository)
        destination = tmp_path / "refused"
        with pytest.raises(PackageCheckoutError):
            checkout.write(destination)
        assert not destination.exists()


@pytest.mark.parametrize(
    "change", ["modified", "added", "deleted", "mode", "inventory", "symlink"]
)
def test_complete_checkout_verification_rejects_mutations(
    repository: Path, tmp_path: Path, change: str
) -> None:
    destination = tmp_path / "checkout"
    with PackageSourceCheckout(repository) as checkout:
        checkout.resolve(["sample-a"])
        checkout.write(destination)
    source = destination / "workspaces/main/modules/family/a/source.py"
    if change == "modified":
        source.write_text("changed")
    elif change == "added":
        (source.parent / "unexpected").write_text("extra")
    elif change == "deleted":
        source.unlink()
    elif change == "mode":
        source.chmod(0o755)
    elif change == "inventory":
        path = destination / "checkout-inventory.json"
        path.write_text(path.read_text().replace("source_closure_resolved", "changed"))
    else:
        source.unlink()
        source.symlink_to(manifest(repository, "a"))
    with pytest.raises((PackageCheckoutError, SourceObservationUnavailable)):
        verify_package_checkout(destination)


def test_symlink_source_refuses_before_copy(repository: Path) -> None:
    source = manifest(repository, "a").parent / "source.py"
    source.unlink()
    source.symlink_to("../b/source.py")
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(SourceObservationUnavailable),
    ):
        checkout.resolve(["sample-a"])


def test_existing_destination_and_inside_repository_are_preserved(
    repository: Path, tmp_path: Path
) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "keep").write_text("keep")
    with PackageSourceCheckout(repository) as checkout:
        checkout.resolve(["sample-a"])
        with pytest.raises(FileExistsError):
            checkout.write(target)
        assert (target / "keep").read_text() == "keep"
        with pytest.raises(PackageCheckoutError, match="outside"):
            checkout.write(repository / "new")


def test_closed_reader_cannot_resume(repository: Path) -> None:
    checkout = PackageSourceCheckout(repository)
    checkout.resolve(["sample-a"])
    checkout.close()
    with pytest.raises(PackageCheckoutError, match="closed"):
        checkout.revalidate()


def test_optional_marker_is_bound_to_its_own_extra(repository: Path) -> None:
    path = manifest(repository, "a")
    path.write_text(
        path.read_text()
        + "[project.optional-dependencies]\nx=[\"sample-b; extra == 'y'\"]\ny=[]\n"
    )
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-a[x,y]"])
        assert [p["name"] for p in plan["packages"]] == ["sample-a"]


def test_owner_path_cannot_substitute_an_equal_named_member(repository: Path) -> None:
    change_dependencies(repository, "a", ["sample-b"])
    path = manifest(repository, "a")
    path.write_text(path.read_text() + '[tool.uv.sources]\nsample-b={path="../c"}\n')
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="membership disagree"),
    ):
        checkout.resolve(["sample-a"])


def test_target_python_marker_fields_must_agree(repository: Path) -> None:
    target = {
        **default_environment(),
        "python_version": "3.11",
        "python_full_version": "3.12.1",
    }
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="marker fields disagree"),
    ):
        checkout.resolve(["sample-a"], marker_environment=target)


def test_repository_direct_codes_reuse_same_manifest_membership(
    repository: Path,
) -> None:
    path = repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace(
            'handle="consumer"',
            'handle="consumer"\ncodes=["workspaces/main/modules/family/b/pyproject.toml"]',
        )
    )
    with PackageSourceCheckout(repository) as checkout:
        plan = checkout.resolve(["sample-b"])
        assert len(plan["packages"]) == 1
        assert len(plan["packages"][0]["memberships"]) == 2


def test_workspace_handle_alias_does_not_create_membership(repository: Path) -> None:
    path = repository / "aware.repo.toml"
    path.write_text(path.read_text().replace('handle="main"', 'handle="other"'))
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(Exception, match="handle mismatch"),
    ):
        checkout.resolve(["sample-a"])


def test_public_command_runs_plan_write_and_verify(
    repository: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from aware_workspace_command.workspace_command import (
        handle_workspace_command,
        register_workspace_parser,
    )

    parser = argparse.ArgumentParser()
    register_workspace_parser(
        parser.add_subparsers(dest="command"), args_list=("workspace", "checkout")
    )
    destination = tmp_path / "public-checkout"
    args = parser.parse_args(
        [
            "workspace",
            "checkout",
            "--repo-root",
            str(repository),
            "--package",
            "sample-a",
            "--destination",
            str(destination),
            "--json",
        ]
    )
    assert handle_workspace_command(args, parser, None) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["state"] == "source_checkout_written"
    args = parser.parse_args(
        ["workspace", "checkout", "--verify", str(destination), "--json"]
    )
    assert handle_workspace_command(args, parser, None) == 0
    assert (
        json.loads(capsys.readouterr().out)["inventory_digest"]
        == output["inventory_digest"]
    )


def test_public_command_refusal_returns_no_checkout(
    repository: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from aware_workspace_command.workspace_command import (
        handle_workspace_command,
        register_workspace_parser,
    )

    parser = argparse.ArgumentParser()
    register_workspace_parser(
        parser.add_subparsers(dest="command"), args_list=("workspace", "checkout")
    )
    destination = tmp_path / "refused-public-checkout"
    args = parser.parse_args(
        [
            "workspace",
            "checkout",
            "--repo-root",
            str(repository),
            "--package",
            "absent",
            "--destination",
            str(destination),
            "--json",
        ]
    )
    assert handle_workspace_command(args, parser, None) == 2
    assert json.loads(capsys.readouterr().err)["state"] == "refused"
    assert not destination.exists()


@pytest.mark.parametrize("field", ["version", "dependencies", "optional-dependencies"])
def test_dynamic_dependency_metadata_requires_owner_build(
    repository: Path, field: str
) -> None:
    path = manifest(repository, "a")
    path.write_text(
        path.read_text().replace("[project]", f'[project]\ndynamic=["{field}"]')
    )
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="owner build"),
    ):
        checkout.resolve(["sample-a"])


def test_false_workspace_hint_cannot_choose_local_package(repository: Path) -> None:
    change_dependencies(repository, "a", ["sample-b"])
    path = manifest(repository, "a")
    path.write_text(
        path.read_text() + "[tool.uv.sources]\nsample-b={workspace=false}\n"
    )
    with (
        PackageSourceCheckout(repository) as checkout,
        pytest.raises(PackageCheckoutError, match="invalid owner source"),
    ):
        checkout.resolve(["sample-a"])
