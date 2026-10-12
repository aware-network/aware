from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class AwareSdkCompilationMode(str, Enum):
    raw_xor = "raw_xor"
    sdk_ontology = "sdk_ontology"


class AwareSdkDependencyKind(str, Enum):
    package = "package"
    api = "api"
    api_package = "api_package"
    sdk_package = "sdk_package"


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPythonProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDartProductTargetSpec:
    package_dir: str | None = None
    root_dir: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPythonTargetSpec:
    root_dir: str | None = None
    public_package: AwareSdkTomlPythonProductTargetSpec = field(
        default_factory=AwareSdkTomlPythonProductTargetSpec
    )


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDartTargetSpec:
    root_dir: str | None = None
    public_package: AwareSdkTomlDartProductTargetSpec = field(
        default_factory=AwareSdkTomlDartProductTargetSpec
    )


@dataclass(frozen=True, slots=True)
class AwareSdkTomlTargetsSpec:
    python: AwareSdkTomlPythonTargetSpec | None = None
    dart: AwareSdkTomlDartTargetSpec | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlBuildSpec:
    sources_dir: str = "sdks"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    compilation_mode: AwareSdkCompilationMode = AwareSdkCompilationMode.raw_xor


@dataclass(frozen=True, slots=True)
class AwareSdkTomlDependencySpec:
    package_name: str
    version_number: int | None = None
    kind: AwareSdkDependencyKind = AwareSdkDependencyKind.package
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlObjectConfigGraphPackageSpec:
    manifest: str
    role: str = "local_state"
    description: str | None = None
    expected_hash_sha256: str | None = None
    object_instance_graph_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class AwareSdkTomlGenerationProfileSpec:
    """Authored generation declaration, not selected operation authority."""

    name: str
    renderer_version: str
    operations: list[str]
    python_generated_dir: str
    dart_generated_dir: str
    materialized_dir: str


@dataclass(frozen=True, slots=True)
class AwareSdkTomlSpec:
    aware_sdk: int
    sdk: AwareSdkTomlPackageSpec
    build: AwareSdkTomlBuildSpec
    dependencies: list[AwareSdkTomlDependencySpec]
    object_config_graph_packages: list[AwareSdkTomlObjectConfigGraphPackageSpec] = (
        field(default_factory=list)
    )
    targets: AwareSdkTomlTargetsSpec = field(default_factory=AwareSdkTomlTargetsSpec)
    generation_profiles: list[AwareSdkTomlGenerationProfileSpec] = field(
        default_factory=list
    )


def validate_sdk_manifest_version(value: AwareSdkTomlSpec) -> None:
    """Manifest meaning is package exposure, never SDK operation selection."""
    if type(value.aware_sdk) is not int or value.aware_sdk != 1:
        raise ValueError("unsupported SDK manifest version")
    _validate_generation_profiles(value)


def _profile_path(value: str) -> None:
    if (
        type(value) is not str
        or not 1 <= len(value.encode()) <= 1024
        or "\\" in value
        or any(ord(char) < 32 for char in value)
        or any(
            part in {"", ".", ".."} or part.strip() != part for part in value.split("/")
        )
    ):
        raise ValueError("profile path must be bounded exact POSIX-relative text")


def _validate_generation_profiles(value: AwareSdkTomlSpec) -> None:
    profiles = value.generation_profiles
    if type(profiles) is not list or len(profiles) > 32:
        raise ValueError(
            "generation_profiles must be an exact list of at most 32 profiles"
        )
    names: list[str] = []
    operations: set[str] = set()
    sdk_refs: set[str] = set()
    outputs: set[str] = set()
    for profile in profiles:
        if type(profile) is not AwareSdkTomlGenerationProfileSpec:
            raise ValueError("generation profile must be an exact owner value")
        if (
            type(profile.name) is not str
            or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", profile.name) is None
        ):
            raise ValueError("invalid bounded profile name")
        names.append(profile.name)
        if type(
            profile.renderer_version
        ) is not str or profile.renderer_version not in {
            "aware.sdk.target-renderer.v6",
            "aware.sdk.target-renderer.v7",
        }:
            raise ValueError("unsupported exact profile renderer")
        refs = profile.operations
        if type(refs) is not list or not 1 <= len(refs) <= 1024:
            raise ValueError("profile operations must be a bounded nonempty exact list")
        for ref in refs:
            if (
                type(ref) is not str
                or "." not in ref
                or any(not part.isidentifier() for part in ref.split("."))
            ):
                raise ValueError(
                    "profile operations must be exact qualified references"
                )
            sdk_refs.add(ref.rsplit(".", 1)[0])
        if (
            len(set(refs)) != len(refs)
            or sorted(refs, key=lambda ref: ref.encode()) != refs
        ):
            raise ValueError(
                "profile operations must be unique and canonically ordered"
            )
        if operations.intersection(refs):
            raise ValueError("profile operation partition overlaps")
        operations.update(refs)
        if len(operations) > 1024 or len(sdk_refs) != 1:
            raise ValueError("profiles require at most 1024 operations from one SDK")
        for language, directory, target, suffix in (
            ("python", profile.python_generated_dir, value.targets.python, ""),
            ("dart", profile.dart_generated_dir, value.targets.dart, "/lib/src"),
        ):
            _profile_path(directory)
            if (
                target is None
                or target.root_dir is None
                or target.public_package.package_dir is None
            ):
                raise ValueError(f"profile requires explicit {language} public target")
            rail = f"{target.root_dir}/{target.public_package.package_dir}{suffix}"
            _profile_path(rail)
            if directory != rail and not directory.startswith(rail + "/"):
                raise ValueError(f"profile escapes {language} public rail")
        _profile_path(profile.materialized_dir)
        if (
            profile.materialized_dir != "materialized"
            and not profile.materialized_dir.startswith("materialized/")
        ):
            raise ValueError("profile escapes materialized rail")
        # These are the accepted profile's six declared artifact coordinates.
        # Discovery validates non-overlap; only the selected source/renderer
        # owners may prove complete partitions or produce these artifacts.
        paths = (
            profile.python_generated_dir + "/__init__.py",
            profile.python_generated_dir + "/sdk_contract.py",
            profile.dart_generated_dir + "/sdk_contract.dart",
            profile.materialized_dir + "/sdk_contract_manifest.json",
            profile.materialized_dir + "/sdk_operation_inventory.json",
            profile.materialized_dir + "/sdk_contract_artifacts.json",
        )
        for path in paths:
            _profile_path(path)
            if path in outputs or any(
                path.startswith(old + "/") or old.startswith(path + "/")
                for old in outputs
            ):
                raise ValueError("profile output files conflict")
            outputs.add(path)
    if (
        len(set(names)) != len(names)
        or sorted(names, key=lambda name: name.encode()) != names
    ):
        raise ValueError("profile names must be unique and canonically ordered")


__all__ = [
    "AwareSdkCompilationMode",
    "AwareSdkDependencyKind",
    "AwareSdkTomlBuildSpec",
    "AwareSdkTomlDartProductTargetSpec",
    "AwareSdkTomlDartTargetSpec",
    "AwareSdkTomlDependencySpec",
    "AwareSdkTomlGenerationProfileSpec",
    "AwareSdkTomlObjectConfigGraphPackageSpec",
    "AwareSdkTomlPackageSpec",
    "AwareSdkTomlPythonProductTargetSpec",
    "AwareSdkTomlPythonTargetSpec",
    "AwareSdkTomlSpec",
    "AwareSdkTomlTargetsSpec",
    "validate_sdk_manifest_version",
]
