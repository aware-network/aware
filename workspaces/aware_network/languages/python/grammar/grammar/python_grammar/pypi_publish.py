"""Python package publish planning for PyPI-compatible repositories."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
import re
import tomllib
from typing import cast

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language.tooling import (
    CodeLanguageToolSpec,
    CodeLanguageToolStateRequirement,
)


_VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:(a|b|rc)\d+|\.dev\d+|\.post\d+)?$"
)


@dataclass(frozen=True, slots=True)
class PythonPackageMetadata:
    """Minimal Python project metadata required before publishing."""

    name: str
    version: str


@dataclass(frozen=True, slots=True)
class PyPiRepositoryTarget:
    """PyPI-compatible repository endpoint contract."""

    name: str
    upload_url: str
    simple_index_url: str
    allow_prerelease: bool
    production: bool = False


@dataclass(frozen=True, slots=True)
class PythonPackagePublishPlan:
    """Command plan for building, checking, and publishing a Python package."""

    package: PythonPackageMetadata
    repository: PyPiRepositoryTarget
    package_root: Path
    dist_dir: Path
    artifact_glob: str
    build_command: tuple[str, ...]
    metadata_check_command: tuple[str, ...] | None
    upload_command: tuple[str, ...] | None
    publish_preflight_receipt: Mapping[str, object] | None = None
    upload_secret_env_bindings: Mapping[str, str] = field(default_factory=dict)


PYPI_REPOSITORY = PyPiRepositoryTarget(
    name="pypi",
    upload_url="https://upload.pypi.org/legacy/",
    simple_index_url="https://pypi.org/simple/",
    allow_prerelease=False,
    production=True,
)
TEST_PYPI_REPOSITORY = PyPiRepositoryTarget(
    name="testpypi",
    upload_url="https://test.pypi.org/legacy/",
    simple_index_url="https://test.pypi.org/simple/",
    allow_prerelease=True,
)
PYPI_REPOSITORIES: Mapping[str, PyPiRepositoryTarget] = {
    PYPI_REPOSITORY.name: PYPI_REPOSITORY,
    TEST_PYPI_REPOSITORY.name: TEST_PYPI_REPOSITORY,
}
_FORBIDDEN_CREDENTIAL_HANDLE_KEYS = frozenset(
    {
        "api_key",
        "api_key_value",
        "password",
        "private_key",
        "raw_secret",
        "secret",
        "secret_value",
        "token",
        "token_value",
    }
)


def create_python_pypi_tool_specs(language: CodeLanguage) -> tuple[CodeLanguageToolSpec, ...]:
    """Return language-owned Python package build/check/publish tool specs."""

    return (
        CodeLanguageToolSpec(
            tool_id="python.package.build",
            language=language,
            role="package_builder",
            description="Build a Python package sdist and wheel with uv.",
            backend="cli",
            target_mode="package_root",
            command=("uv", "build"),
            default_timeout_s=180.0,
            network=True,
            mutates_targets=False,
            state_requirements=(
                CodeLanguageToolStateRequirement(
                    key="uv_cache",
                    kind="cache",
                    env_var="UV_CACHE_DIR",
                    default_subdir="uv-cache",
                ),
            ),
            metadata={
                "dist_dir_arg": "--out-dir",
                "project_arg": "--project",
            },
        ),
        CodeLanguageToolSpec(
            tool_id="python.package.metadata_check",
            language=language,
            role="package_checker",
            description="Validate built Python package metadata with twine check.",
            backend="cli",
            target_mode="package_root",
            command=("uvx", "twine", "check"),
            default_timeout_s=120.0,
            network=True,
            mutates_targets=False,
            state_requirements=(
                CodeLanguageToolStateRequirement(
                    key="uv_cache",
                    kind="cache",
                    env_var="UV_CACHE_DIR",
                    default_subdir="uv-cache",
                ),
            ),
        ),
        CodeLanguageToolSpec(
            tool_id="python.package.publish.testpypi",
            language=language,
            role="publisher",
            description="Upload checked Python package artifacts to TestPyPI.",
            backend="cli",
            target_mode="package_root",
            command=("uvx", "twine", "upload"),
            default_timeout_s=180.0,
            network=True,
            mutates_targets=False,
            state_requirements=(
                CodeLanguageToolStateRequirement(
                    key="uv_cache",
                    kind="cache",
                    env_var="UV_CACHE_DIR",
                    default_subdir="uv-cache",
                ),
                CodeLanguageToolStateRequirement(
                    key="publish_preflight_receipt",
                    kind="config",
                    required=True,
                ),
            ),
            metadata={
                "repository": TEST_PYPI_REPOSITORY.name,
                "repository_url": TEST_PYPI_REPOSITORY.upload_url,
                "simple_index_url": TEST_PYPI_REPOSITORY.simple_index_url,
                "requires_publish_preflight_receipt": "true",
                "publish_preflight_target_kind": "test_pypi",
                "username_env": "TWINE_USERNAME",
                "password_env": "TWINE_PASSWORD",
                "recommended_username": "__token__",
                "version_policy": "immutable_index_allow_prerelease",
            },
        ),
        CodeLanguageToolSpec(
            tool_id="python.package.publish.pypi",
            language=language,
            role="publisher",
            description="Upload checked Python package artifacts to production PyPI.",
            backend="cli",
            target_mode="package_root",
            command=("uvx", "twine", "upload"),
            default_timeout_s=180.0,
            network=True,
            mutates_targets=False,
            state_requirements=(
                CodeLanguageToolStateRequirement(
                    key="uv_cache",
                    kind="cache",
                    env_var="UV_CACHE_DIR",
                    default_subdir="uv-cache",
                ),
                CodeLanguageToolStateRequirement(
                    key="publish_preflight_receipt",
                    kind="config",
                    required=True,
                ),
            ),
            metadata={
                "repository": PYPI_REPOSITORY.name,
                "repository_url": PYPI_REPOSITORY.upload_url,
                "simple_index_url": PYPI_REPOSITORY.simple_index_url,
                "requires_publish_preflight_receipt": "true",
                "publish_preflight_target_kind": "pypi",
                "username_env": "TWINE_USERNAME",
                "password_env": "TWINE_PASSWORD",
                "recommended_username": "__token__",
                "version_policy": "immutable_index_production_version_required",
                "requires_version_protocol": "true",
            },
        ),
    )


def load_python_package_metadata(package_root: Path) -> PythonPackageMetadata:
    """Load package name/version from a Python package root."""

    pyproject_path = package_root / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    name = str(project.get("name", "")).strip()
    version = str(project.get("version", "")).strip()
    if not name:
        raise ValueError(f"Python package metadata is missing project.name: {pyproject_path}")
    if not version:
        raise ValueError(f"Python package metadata is missing project.version: {pyproject_path}")
    return PythonPackageMetadata(name=name, version=version)


def build_python_package_publish_plan(
    *,
    package_root: Path,
    dist_dir: Path,
    repository: str = TEST_PYPI_REPOSITORY.name,
    artifact_paths: Iterable[Path] = (),
    publish_preflight_receipt: Mapping[str, object] | None = None,
) -> PythonPackagePublishPlan:
    """Build a deterministic publish command plan for a Python package."""

    target = PYPI_REPOSITORIES.get(repository)
    if target is None:
        known = ", ".join(sorted(PYPI_REPOSITORIES))
        raise ValueError(f"Unknown PyPI repository {repository!r}. Expected one of: {known}")

    package = load_python_package_metadata(package_root)
    ensure_pypi_version_allowed(package.version, target)

    package_root = package_root.resolve()
    dist_dir = dist_dir.resolve()
    artifacts = tuple(path.resolve() for path in artifact_paths)
    validated_preflight_receipt: Mapping[str, object] | None = None
    upload_secret_env_bindings: Mapping[str, str] = {}
    if artifacts:
        validated_preflight_receipt = validate_python_publish_preflight_receipt(
            receipt=publish_preflight_receipt,
            package=package,
            repository=target,
        )
        upload_secret_env_bindings = _twine_secret_env_bindings(validated_preflight_receipt)

    artifact_glob = str(dist_dir / "*")
    build_command = (
        "uv",
        "build",
        "--project",
        str(package_root),
        "--out-dir",
        str(dist_dir),
    )
    metadata_check_command = (
        ("uvx", "twine", "check", *(str(path) for path in artifacts))
        if artifacts
        else None
    )
    upload_command = (
        (
            "uvx",
            "twine",
            "upload",
            "--repository-url",
            target.upload_url,
            *(str(path) for path in artifacts),
        )
        if artifacts
        else None
    )

    return PythonPackagePublishPlan(
        package=package,
        repository=target,
        package_root=package_root,
        dist_dir=dist_dir,
        artifact_glob=artifact_glob,
        build_command=build_command,
        metadata_check_command=metadata_check_command,
        upload_command=upload_command,
        publish_preflight_receipt=validated_preflight_receipt,
        upload_secret_env_bindings=upload_secret_env_bindings,
    )


def validate_python_publish_preflight_receipt(
    *,
    receipt: Mapping[str, object] | None,
    package: PythonPackageMetadata,
    repository: PyPiRepositoryTarget,
) -> Mapping[str, object]:
    """Validate a release publish preflight receipt for Python package upload."""

    if receipt is None:
        raise ValueError(
            "Python package upload requires a ready release publish preflight receipt."
        )
    if _string_value(receipt, "status").lower() != "ready":
        raise ValueError("Python package upload requires a ready preflight receipt.")
    if not _bool_value(receipt, "can_publish"):
        raise ValueError("Python package upload requires can_publish=true.")
    if _list_value(receipt, "missing_requirements"):
        raise ValueError("Python package upload preflight receipt has missing requirements.")

    package_payload = _mapping_value(receipt, "package")
    receipt_name = _string_value(package_payload, "name")
    receipt_version = _string_value(package_payload, "version")
    if receipt_name != package.name or receipt_version != package.version:
        raise ValueError(
            "Python package upload preflight package mismatch: "
            + f"receipt={receipt_name} {receipt_version} "
            + f"package={package.name} {package.version}"
        )
    artifact_kind = _optional_string_value(package_payload, "artifact_kind")
    if artifact_kind is not None and artifact_kind != "python_package":
        raise ValueError(
            f"Python package upload preflight artifact kind is not python_package: {artifact_kind}"
        )

    expected_target_kind = _repository_preflight_target_kind(repository)
    target_kind = _normalize_preflight_target(_string_value(receipt, "target_kind"))
    target_index = _normalize_preflight_target(_string_value(receipt, "target_index"))
    if target_kind != expected_target_kind or target_index != expected_target_kind:
        raise ValueError(
            "Python package upload preflight target mismatch: "
            + f"receipt={target_kind}/{target_index} repository={expected_target_kind}"
        )

    credential_payload = _mapping_value(receipt, "credential")
    if _bool_value(credential_payload, "raw_secret_returned"):
        raise ValueError("Python package upload preflight returned raw secret material.")

    credential_handle = _mapping_value(receipt, "credential_handle")
    if not credential_handle:
        raise ValueError("Python package upload preflight requires a credential handle.")
    forbidden = _find_forbidden_credential_handle_keys(credential_handle)
    if forbidden:
        raise ValueError(
            "Python package upload preflight credential handle contains raw-secret keys: "
            + ", ".join(forbidden)
        )

    return dict(receipt)


def ensure_pypi_version_allowed(version: str, repository: PyPiRepositoryTarget) -> None:
    """Fail fast on placeholder or non-public versions for PyPI-like indexes."""

    normalized = version.strip()
    if not _VERSION_RE.fullmatch(normalized):
        raise ValueError(
            f"Version {version!r} is not accepted for {repository.name}; use an explicit "
            "public version such as 0.1.0 or 0.1.0.dev1."
        )
    if normalized == "0.0.0":
        raise ValueError(f"Version {version!r} is a placeholder and cannot be published.")
    if "+" in normalized:
        raise ValueError(f"Local version {version!r} cannot be published to {repository.name}.")
    if repository.production and not repository.allow_prerelease:
        if any(marker in normalized for marker in ("a", "b", "rc", ".dev")):
            raise ValueError(
                f"Production PyPI publish requires a final public version, got {version!r}."
            )


def _twine_secret_env_bindings(receipt: Mapping[str, object]) -> Mapping[str, str]:
    credential_handle = _mapping_value(receipt, "credential_handle")
    source_env = _string_value(credential_handle, "env_var")
    return {"TWINE_PASSWORD": source_env}


def _repository_preflight_target_kind(repository: PyPiRepositoryTarget) -> str:
    return _normalize_preflight_target(repository.name)


def _normalize_preflight_target(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized == "testpypi":
        return "test_pypi"
    return normalized


def _mapping_value(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    value = payload.get(key)
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"Python package upload preflight field {key!r} must be an object.")


def _string_value(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"Python package upload preflight field {key!r} must be a string.")


def _optional_string_value(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(
        f"Python package upload preflight field {key!r} must be a string when set."
    )


def _bool_value(payload: Mapping[str, object], key: str) -> bool:
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    raise ValueError(f"Python package upload preflight field {key!r} must be a bool.")


def _list_value(payload: Mapping[str, object], key: str) -> tuple[object, ...]:
    value = payload.get(key, ())
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, tuple):
        return value
    raise ValueError(f"Python package upload preflight field {key!r} must be a list.")


def _find_forbidden_credential_handle_keys(
    value: object,
    *,
    prefix: str = "",
) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return ()
    found: list[str] = []
    for key, item in value.items():
        key_text = str(key).strip()
        normalized = key_text.lower().replace("-", "_")
        path = f"{prefix}.{key_text}" if prefix else key_text
        if normalized in _FORBIDDEN_CREDENTIAL_HANDLE_KEYS:
            found.append(path)
        found.extend(_find_forbidden_credential_handle_keys(item, prefix=path))
    return tuple(found)
