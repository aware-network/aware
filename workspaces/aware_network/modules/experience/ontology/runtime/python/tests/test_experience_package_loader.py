import pytest

from aware_experience.manifest.loader import (
    AwareExperienceTomlError,
    load_aware_experience_toml_spec,
)
from aware_experience.manifest.spec import AwareExperienceDependencyKind
from ._experience_runtime_test_paths import REPO_ROOT


DEF_EXPERIENCE_TOML_HAPPY_PATH = """
aware_experience = 1

[experience]
package_name = "assistance"
fqn_prefix = "assistance"
version_number = 3
title = "Assistance Experience"
description = "Role-first assistance package"

[build]
environment_handle = "kernel"
sources_dir = "experiences"
include_paths = ["**/*.aware"]
exclude_paths = ["**/_draft/**"]
force_fresh_scan = true

[[dependencies]]
package_name = "shared-assistance"
kind = "experience_package"
version_number = 2

[[dependencies]]
package_name = "studio-base"
kind = "ontology_package"
"""


def test_load_aware_experience_toml_happy_path(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(DEF_EXPERIENCE_TOML_HAPPY_PATH, encoding="utf-8")

    spec = load_aware_experience_toml_spec(toml_path=p)
    assert spec.aware_experience == 1
    assert spec.experience.package_name == "assistance"
    assert spec.experience.fqn_prefix == "assistance"
    assert spec.experience.version_number == 3
    assert spec.experience.title == "Assistance Experience"
    assert spec.experience.description == "Role-first assistance package"
    assert spec.build.environment_handle == "kernel"
    assert spec.build.sources_dir == "experiences"
    assert spec.build.include_paths == ["**/*.aware"]
    assert spec.build.exclude_paths == ["**/_draft/**"]
    assert spec.build.force_fresh_scan is True
    assert len(spec.dependencies) == 2
    assert spec.dependencies[0].package_name == "shared-assistance"
    assert spec.dependencies[0].kind is AwareExperienceDependencyKind.experience_package
    assert spec.dependencies[0].version_number == 2
    assert spec.dependencies[1].package_name == "studio-base"
    assert spec.dependencies[1].kind is AwareExperienceDependencyKind.ontology_package
    assert spec.dependencies[1].version_number is None


def test_identity_default_experience_declares_actor_roles_authority_dependency() -> (
    None
):
    repo_root = REPO_ROOT
    spec = load_aware_experience_toml_spec(
        toml_path=(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "identity"
            / "experiences"
            / "aware_identity"
            / "aware.experience.toml"
        )
    )

    dependencies = {
        dependency.package_name: (dependency.kind, dependency.version_number)
        for dependency in spec.dependencies
    }
    assert dependencies["aware-actor"] == (
        AwareExperienceDependencyKind.experience_package,
        1,
    )


def test_load_aware_experience_toml_requires_dependency_kind(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(
        """
aware_experience = 1

[experience]
package_name = "assistance"
fqn_prefix = "assistance"

[build]
environment_handle = "kernel"

[[dependencies]]
package_name = "shared-assistance"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        AwareExperienceTomlError,
        match=r"Missing keys in \[\[dependencies\]\] \(index=0\): \['kind'\]",
    ):
        load_aware_experience_toml_spec(toml_path=p)


def test_load_aware_experience_toml_unknown_root_key_fails(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(
        """
aware_experience = 1
extra = "nope"

[experience]
package_name = "assistance"
fqn_prefix = "assistance"

[build]
environment_handle = "kernel"
""",
        encoding="utf-8",
    )

    with pytest.raises(AwareExperienceTomlError, match=r"Unknown keys in root"):
        load_aware_experience_toml_spec(toml_path=p)


def test_load_aware_experience_toml_requires_environment_handle(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(
        """
aware_experience = 1

[experience]
package_name = "assistance"
fqn_prefix = "assistance"

[build]
sources_dir = "experiences"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        AwareExperienceTomlError,
        match=r"Missing keys in \[build\]: \['environment_handle'\]",
    ):
        load_aware_experience_toml_spec(toml_path=p)


def test_load_aware_experience_toml_rejects_parent_path_traversal(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(
        """
aware_experience = 1

[experience]
package_name = "assistance"
fqn_prefix = "assistance"

[build]
environment_handle = "kernel"
sources_dir = "../escape"
""",
        encoding="utf-8",
    )

    with pytest.raises(AwareExperienceTomlError, match=r"must not contain '\.\.'"):
        load_aware_experience_toml_spec(toml_path=p)


def test_load_aware_experience_toml_duplicate_dependencies_fail(tmp_path) -> None:
    p = tmp_path / "aware.experience.toml"
    p.write_text(
        """
aware_experience = 1

[experience]
package_name = "assistance"
fqn_prefix = "assistance"

[build]
environment_handle = "kernel"

[[dependencies]]
package_name = "shared-assistance"
kind = "experience_package"

[[dependencies]]
package_name = "shared-assistance"
kind = "experience_package"
""",
        encoding="utf-8",
    )

    with pytest.raises(AwareExperienceTomlError, match=r"Duplicate dependency"):
        load_aware_experience_toml_spec(toml_path=p)
