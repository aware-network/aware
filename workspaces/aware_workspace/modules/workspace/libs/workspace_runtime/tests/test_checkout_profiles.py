from __future__ import annotations

import json
from pathlib import Path

import pytest
import test_package_checkout as fixtures
from aware_workspace_runtime.checkout_profiles import (
    CheckoutProfile,
    parse_checkout_profiles,
)
from aware_workspace_runtime.package_checkout import (
    PROFILE_CONTRACT,
    PackageCheckoutError,
    PackageSourceCheckout,
    verify_package_checkout,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable

repository = fixtures.repository
commit_fixture = fixtures.commit_fixture
manifest = fixtures.manifest


def profiles(rows: list[dict]) -> tuple[CheckoutProfile, ...]:
    return parse_checkout_profiles({"checkout_profile_sets": rows}, frozenset({"main"}))


def member(**fields: object) -> dict:
    return {"workspace": "main", "module": "family", "package": "a", **fields}


def source_profile(**fields: object) -> dict:
    return {"key": "source", "version": 2, "package_selections": [member()], **fields}


def test_legacy_profile_meaning_and_trimmed_constructor_preserved() -> None:
    value = profiles([{"key": " old ", "workspace_handles": [" main "]}])[0]
    assert value == CheckoutProfile("old", ("main",))
    assert value.version == 1


@pytest.mark.parametrize(
    "rows,match",
    [
        ([{"key": "old", "workspace_handles": []}], "declared Workspaces"),
        ([{"key": "old", "workspace_handles": ["foreign"]}], "declared Workspaces"),
        ([{"key": "old", "workspace_handles": ["main", "main"]}], "duplicate"),
        ([source_profile(version=True)], "version"),
        ([source_profile(version=3)], "version"),
        ([source_profile(authority="provider")], "unknown"),
        ([source_profile(package_selections=[])], "no package"),
        ([source_profile(), source_profile()], "duplicate"),
        ([source_profile(include_profiles=["missing"])], "unknown included"),
        ([source_profile(include_profiles=["source"])], "cycle"),
        (
            [
                source_profile(include_profiles=["other"]),
                source_profile(key="other", include_profiles=["source"]),
            ],
            "cycle",
        ),
        (
            [source_profile(package_selections=[member(workspace="foreign")])],
            "Workspace",
        ),
        (
            [source_profile(package_selections=[member(module="../family")])],
            "identifier",
        ),
        ([source_profile(package_selections=[member(package="a/b")])], "identifier"),
        (
            [source_profile(package_selections=[{"workspace": "main"}])],
            "exact declared address",
        ),
        (
            [
                source_profile(
                    package_selections=[member(code_manifest="pyproject.toml")]
                )
            ],
            "exact declared address",
        ),
        ([source_profile(package_selections=[member(), member()])], "duplicate"),
        (
            [
                source_profile(
                    package_selections=[member(extras=["Foo_Bar", "foo-bar"])]
                )
            ],
            "canonical extras",
        ),
        (
            [
                source_profile(
                    package_selections=[
                        {"workspace": "main", "code_manifest": "../pyproject.toml"}
                    ]
                )
            ],
            "path",
        ),
    ],
)
def test_invalid_profile_grammar_refuses(rows: list[dict], match: str) -> None:
    with pytest.raises((ValueError, SourceObservationUnavailable), match=match):
        profiles(rows)


@pytest.fixture
def profile_repository(repository: Path) -> Path:
    repo = repository / "aware.repo.toml"
    repo.write_text(
        repo.read_text()
        + """
[[checkout_profile_sets]]
key="old"
workspace_handles=["main"]
[[checkout_profile_sets]]
key="one"
version=2
package_selections=[{workspace="main",module="family",package="a",extras=["tools"]}]
[[checkout_profile_sets]]
key="two"
version=2
package_selections=[{workspace="main",code_manifest="direct/pyproject.toml"}]
[[checkout_profile_sets]]
key="both"
version=2
include_profiles=["one","two"]
overlays=["public_docs"]
[[repository_files]]
role="license"
source_path="LICENSE"
target_path="LICENSE"
[[repository_files]]
role="alignment"
source_path="public.md"
target_path="docs/CURRENT.md"
overlay="public_docs"
"""
    )
    path = manifest(repository, "a")
    path.write_text(
        path.read_text() + '\n[project.optional-dependencies]\ntools=["sample-b"]\n'
    )
    (repository / "LICENSE").write_text("Fixture license\n")
    (repository / "public.md").write_text("Public projection\n")
    commit_fixture(repository)
    return repository


def test_composed_profiles_write_full_union_and_explicit_overlay(
    profile_repository: Path,
    tmp_path: Path,
) -> None:
    with PackageSourceCheckout(profile_repository) as checkout:
        value = checkout.resolve(profiles=["both", "one"])
        assert value["contract"] == PROFILE_CONTRACT
        assert value["profiles"] == {
            "requested": ["both", "one"],
            "expanded": ["both", "one", "two"],
        }
        assert [p["name"] for p in value["packages"]] == [
            "sample-a",
            "sample-b",
            "sample-direct",
        ]
        assert value["packages"][0]["extras"] == ["tools"]
        assert len(value["files"]) == 10
        destination = tmp_path / "combined"
        checkout.write(destination)
        assert verify_package_checkout(destination) == value
        assert (destination / "docs/CURRENT.md").read_bytes() == (
            profile_repository / "public.md"
        ).read_bytes()
        assert not (destination / "public.md").exists()
        assert not (destination / "workspaces/main/modules/family/c").exists()


def test_explicit_packages_and_profiles_share_resolver(
    profile_repository: Path,
) -> None:
    with PackageSourceCheckout(profile_repository) as checkout:
        value = checkout.resolve(["sample-c"], profiles=["two"])
        assert [p["name"] for p in value["packages"]] == ["sample-c", "sample-direct"]
        assert value["overlays"] == []
        assert len(value["repository_files"]) == 1


@pytest.mark.parametrize(
    "key,match", [("old", "revision/generated"), ("missing", "unknown checkout")]
)
def test_legacy_or_unknown_profile_is_not_silently_narrowed(
    profile_repository: Path, key: str, match: str
) -> None:
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match=match),
    ):
        checkout.resolve(profiles=[key])


def test_composition_cannot_hide_unsupported_legacy_member(
    profile_repository: Path,
) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace(
            'include_profiles=["one","two"]', 'include_profiles=["one","old"]'
        )
    )
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match="revision/generated"),
    ):
        checkout.resolve(profiles=["both"])


@pytest.mark.parametrize(
    "change,match",
    [
        ('module="family",package="a"', "not one declared"),
        ('code_manifest="direct/pyproject.toml"', "not one declared"),
    ],
)
def test_matching_names_and_paths_cannot_replace_declared_profile_members(
    profile_repository: Path, change: str, match: str
) -> None:
    path = profile_repository / "aware.repo.toml"
    replacement = (
        'module="wrong",package="a"'
        if change.startswith("module")
        else 'code_manifest="modules/family/b/pyproject.toml"'
    )
    path.write_text(path.read_text().replace(change, replacement))
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match=match),
    ):
        checkout.resolve(profiles=["both"])


def test_required_forbidden_dependency_refuses_entire_profile(
    profile_repository: Path,
) -> None:
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(PackageCheckoutError, match="forbidden dependency"),
    ):
        checkout.resolve(profiles=["one"], forbidden_packages=["sample-b"])


@pytest.mark.parametrize("path", ["aware.repo.toml", "LICENSE", "public.md"])
def test_profile_and_repository_file_drift_refuse_before_write(
    profile_repository: Path, tmp_path: Path, path: str
) -> None:
    with PackageSourceCheckout(profile_repository) as checkout:
        checkout.resolve(profiles=["both"])
        source = profile_repository / path
        source.write_bytes(source.read_bytes() + b"\nchanged\n")
        destination = tmp_path / "refused"
        with pytest.raises(PackageCheckoutError, match="sources changed"):
            checkout.write(destination)
        assert not destination.exists()


@pytest.mark.parametrize(
    "target",
    [
        "checkout-inventory.json",
        "workspaces/main/direct/body.txt",
        "workspaces/main/direct",
    ],
)
def test_overlay_cannot_overwrite_inventory_or_package_files(
    profile_repository: Path, target: str
) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace(
            'target_path="docs/CURRENT.md"', f'target_path="{target}"'
        )
    )
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(PackageCheckoutError, match="collision"),
    ):
        checkout.resolve(profiles=["both"])


def test_missing_repository_file_and_unknown_overlay_refuse(
    profile_repository: Path,
) -> None:
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match="unknown repository-file"),
    ):
        checkout.resolve(profiles=["one"], overlays=["absent"])
    (profile_repository / "LICENSE").unlink()
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises((OSError, SourceObservationUnavailable)),
    ):
        checkout.resolve(profiles=["one"])


def test_untracked_repository_file_refuses(profile_repository: Path) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace('source_path="LICENSE"', 'source_path="untracked.txt"')
    )
    (profile_repository / "untracked.txt").write_text("untracked")
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(PackageCheckoutError, match="Git-tracked"),
    ):
        checkout.resolve(profiles=["one"])


def test_repository_file_link_refuses(profile_repository: Path) -> None:
    path = profile_repository / "LICENSE"
    path.unlink()
    path.symlink_to("public.md")
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(SourceObservationUnavailable),
    ):
        checkout.resolve(profiles=["one"])


def test_explicit_overlay_is_same_declared_mapping(profile_repository: Path) -> None:
    with PackageSourceCheckout(profile_repository) as checkout:
        value = checkout.resolve(["sample-direct"], overlays=["public_docs"])
        assert value["profiles"] == {"requested": [], "expanded": []}
        assert value["overlays"] == ["public_docs"]
        assert len(value["repository_files"]) == 2


def test_repo_owned_code_selection_preserves_owner_declaration(
    profile_repository: Path,
) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace(
            'workspaces_dir="workspaces"',
            'workspaces_dir="workspaces"\ncodes=["workspaces/main/direct/pyproject.toml"]',
        )
        + """
[[checkout_profile_sets]]
key="repo_owned"
version=2
package_selections=[{repo_code_manifest="workspaces/main/direct/pyproject.toml"}]
"""
    )
    with PackageSourceCheckout(profile_repository) as checkout:
        value = checkout.resolve(profiles=["repo_owned"])
        assert value["selection"] == ["sample-direct"]
        assert len(value["packages"][0]["memberships"]) == 2


def test_public_command_profile_write_and_verify(
    profile_repository: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from aware_workspace_command.checkout_command import (
        handle_workspace_checkout_command,
        register_workspace_checkout_parser,
    )

    parser = argparse.ArgumentParser()
    register_workspace_checkout_parser(parser.add_subparsers(dest="command"))
    destination = tmp_path / "profile-cli"
    args = parser.parse_args(
        [
            "checkout",
            "--repo-root",
            str(profile_repository),
            "--profile",
            "both",
            "--destination",
            str(destination),
            "--json",
        ]
    )
    assert handle_workspace_checkout_command(args, None) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["inventory"]["profiles"]["expanded"] == ["both", "one", "two"]
    verify = parser.parse_args(["checkout", "--verify", str(destination), "--json"])
    assert handle_workspace_checkout_command(verify, None) == 0
    capsys.readouterr()
    override = parser.parse_args(
        ["checkout", "--verify", str(destination), "--profile", "one"]
    )
    assert handle_workspace_checkout_command(override, None) == 2


def test_legacy_loader_delegates_grammar_and_preserves_v1_projection(
    profile_repository: Path,
) -> None:
    from aware_workspace.source_repo_root import (
        load_aware_repo_toml_manifest,
        render_selected_aware_repo_toml_manifest,
    )

    repo_path = profile_repository / "aware.repo.toml"
    licensing = '\n[licensing]\ndefault_spdx_expression="Apache-2.0"\n' + "".join(
        f'{field}="LICENSE"\n'
        for field in (
            "license_path",
            "notice_path",
            "third_party_notices_path",
            "generated_output_policy_path",
            "artifact_provenance_path",
            "contribution_policy_path",
            "security_policy_path",
        )
    )
    repo_path.write_text(repo_path.read_text() + licensing)
    value = load_aware_repo_toml_manifest(
        toml_path=profile_repository / "aware.repo.toml"
    )
    assert [(p.key, p.version) for p in value.checkout_profile_sets] == [
        ("old", 1),
        ("one", 2),
        ("two", 2),
        ("both", 2),
    ]
    projected = render_selected_aware_repo_toml_manifest(
        manifest=value, workspace_handles=["main"]
    )
    assert 'key = "old"' in projected
    assert 'workspace_handles = ["main"]' in projected
    assert 'key = "both"' not in projected
    from aware_workspace.revision.filesystem.checkout_profile_source import (
        _checkout_profile_source_profile_paths,
    )

    assert _checkout_profile_source_profile_paths(
        source_root=profile_repository, checkout_profile="old"
    ) == (profile_repository / "workspaces/main/aware.workspace.toml",)
    with pytest.raises(
        RuntimeError, match="v2 source profiles require workspace checkout"
    ):
        _checkout_profile_source_profile_paths(
            source_root=profile_repository, checkout_profile="both"
        )


def test_repo_file_literal_git_path_and_mode_currentness(
    profile_repository: Path, tmp_path: Path
) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text().replace(
            'source_path="LICENSE"', 'source_path="license[public].md"'
        )
    )
    source = profile_repository / "license[public].md"
    source.write_text("literal Git path\n")
    commit_fixture(profile_repository)
    with PackageSourceCheckout(profile_repository) as checkout:
        checkout.resolve(profiles=["one"])
        source.chmod(0o755)
        with pytest.raises(PackageCheckoutError, match="mode changed"):
            checkout.write(tmp_path / "bad-mode")


def test_copied_overlay_drift_rejects_independent_verification(
    profile_repository: Path, tmp_path: Path
) -> None:
    with PackageSourceCheckout(profile_repository) as checkout:
        checkout.resolve(profiles=["both"])
        destination = tmp_path / "overlay-copy"
        checkout.write(destination)
    (destination / "docs/CURRENT.md").write_text("substitute")
    with pytest.raises(PackageCheckoutError, match="member changed"):
        verify_package_checkout(destination)


def test_undeclared_repo_code_path_is_not_inferred_from_distribution(
    profile_repository: Path,
) -> None:
    path = profile_repository / "aware.repo.toml"
    path.write_text(
        path.read_text()
        + """
[[checkout_profile_sets]]
key="unadmitted_repo"
version=2
package_selections=[{repo_code_manifest="workspaces/main/direct/pyproject.toml"}]
"""
    )
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match="not one declared"),
    ):
        checkout.resolve(profiles=["unadmitted_repo"])


def test_profile_never_drops_conflicting_explicit_requirement(
    profile_repository: Path,
) -> None:
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(PackageCheckoutError, match="version conflict"),
    ):
        checkout.resolve(["sample-a>=2"], profiles=["one"])


def test_non_python_module_slot_is_not_a_source_profile_leaf(
    profile_repository: Path,
) -> None:
    module = profile_repository / "workspaces/main/modules/family"
    (module / "semantic").mkdir()
    (module / "semantic/aware.toml").write_text(
        'aware=1\n[package]\nname="semantic"\nkind="ontology"\nversion="1.0"\nfqn_prefix="sample"\n'
    )
    path = module / "aware.module.toml"
    path.write_text(
        path.read_text()
        + '\n[[packages]]\nid="semantic"\nkind="ontology"\nmanifest="semantic/aware.toml"\n'
    )
    repo = profile_repository / "aware.repo.toml"
    repo.write_text(
        repo.read_text().replace(
            'module="family",package="a"', 'module="family",package="semantic"'
        )
    )
    commit_fixture(profile_repository)
    with (
        PackageSourceCheckout(profile_repository) as checkout,
        pytest.raises(ValueError, match="not one declared Python"),
    ):
        checkout.resolve(profiles=["one"])
