from __future__ import annotations

from pathlib import Path

import pytest

from python_grammar.code_language_plugin import PYTHON_CODE_PLUGIN
from python_grammar.pypi_publish import (
    PYPI_REPOSITORY,
    PythonPackageMetadata,
    TEST_PYPI_REPOSITORY,
    build_python_package_publish_plan,
    ensure_pypi_version_allowed,
    validate_python_publish_preflight_receipt,
)


def test_python_plugin_declares_pypi_publish_tooling() -> None:
    tools = {tool.tool_id: tool for tool in PYTHON_CODE_PLUGIN.tooling}

    assert tools["python.package.build"].role == "package_builder"
    assert tools["python.package.metadata_check"].role == "package_checker"
    assert tools["python.package.publish.testpypi"].role == "publisher"
    assert tools["python.package.publish.testpypi"].metadata["repository_url"] == (
        "https://test.pypi.org/legacy/"
    )
    assert (
        tools["python.package.publish.testpypi"].metadata[
            "requires_publish_preflight_receipt"
        ]
        == "true"
    )
    assert {
        requirement.key
        for requirement in tools["python.package.publish.testpypi"].state_requirements
    } == {"uv_cache", "publish_preflight_receipt"}
    assert tools["python.package.publish.pypi"].metadata["requires_version_protocol"] == "true"


def test_build_python_package_publish_plan_from_pyproject(tmp_path: Path) -> None:
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    (package_root / "pyproject.toml").write_text(
        "[project]\nname = \"aware-demo-sdk\"\nversion = \"0.1.0.dev1\"\n",
        encoding="utf-8",
    )
    wheel = tmp_path / "dist" / "aware_demo_sdk-0.1.0.dev1-py3-none-any.whl"
    sdist = tmp_path / "dist" / "aware_demo_sdk-0.1.0.dev1.tar.gz"

    plan = build_python_package_publish_plan(
        package_root=package_root,
        dist_dir=tmp_path / "dist",
        repository="testpypi",
        artifact_paths=(wheel, sdist),
        publish_preflight_receipt=_preflight_receipt(
            package_name="aware-demo-sdk",
            version="0.1.0.dev1",
            target_kind="test_pypi",
            target_index="testpypi",
        ),
    )

    assert plan.package.name == "aware-demo-sdk"
    assert plan.package.version == "0.1.0.dev1"
    assert plan.repository is TEST_PYPI_REPOSITORY
    assert plan.build_command == (
        "uv",
        "build",
        "--project",
        str(package_root.resolve()),
        "--out-dir",
        str((tmp_path / "dist").resolve()),
    )
    assert plan.metadata_check_command == (
        "uvx",
        "twine",
        "check",
        str(wheel.resolve()),
        str(sdist.resolve()),
    )
    assert plan.upload_command == (
        "uvx",
        "twine",
        "upload",
        "--repository-url",
        "https://test.pypi.org/legacy/",
        str(wheel.resolve()),
        str(sdist.resolve()),
    )
    assert plan.publish_preflight_receipt is not None
    assert plan.upload_secret_env_bindings == {
        "TWINE_PASSWORD": "AWARE_TESTPYPI_TOKEN",
    }


def test_pypi_publish_plan_requires_preflight_before_upload(tmp_path: Path) -> None:
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    (package_root / "pyproject.toml").write_text(
        "[project]\nname = \"aware-demo-sdk\"\nversion = \"0.1.0.dev1\"\n",
        encoding="utf-8",
    )
    wheel = tmp_path / "dist" / "aware_demo_sdk-0.1.0.dev1-py3-none-any.whl"

    with pytest.raises(ValueError, match="preflight receipt"):
        build_python_package_publish_plan(
            package_root=package_root,
            dist_dir=tmp_path / "dist",
            repository="testpypi",
            artifact_paths=(wheel,),
        )


def test_pypi_publish_preflight_rejects_mismatched_target() -> None:
    with pytest.raises(ValueError, match="target mismatch"):
        validate_python_publish_preflight_receipt(
            receipt=_preflight_receipt(
                package_name="aware-demo-sdk",
                version="0.1.0",
                target_kind="pypi",
                target_index="pypi",
            ),
            package=PythonPackageMetadata(name="aware-demo-sdk", version="0.1.0"),
            repository=TEST_PYPI_REPOSITORY,
        )


def test_pypi_publish_preflight_rejects_raw_secret_handle() -> None:
    with pytest.raises(ValueError, match="raw-secret keys"):
        validate_python_publish_preflight_receipt(
            receipt=_preflight_receipt(
                package_name="aware-demo-sdk",
                version="0.1.0",
                credential_handle={
                    "resolver": "inline",
                    "token": "pypi-secret-value",
                },
            ),
            package=PythonPackageMetadata(name="aware-demo-sdk", version="0.1.0"),
            repository=TEST_PYPI_REPOSITORY,
        )


def test_production_publish_rejects_prerelease_versions() -> None:
    with pytest.raises(ValueError, match="final public version"):
        ensure_pypi_version_allowed("0.1.0.dev1", PYPI_REPOSITORY)

    ensure_pypi_version_allowed("0.1.0", PYPI_REPOSITORY)


def test_pypi_publish_rejects_placeholder_and_local_versions() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        ensure_pypi_version_allowed("0.0.0", TEST_PYPI_REPOSITORY)
    with pytest.raises(ValueError, match="not accepted"):
        ensure_pypi_version_allowed("0.1.0+local", TEST_PYPI_REPOSITORY)


def _preflight_receipt(
    *,
    package_name: str,
    version: str,
    target_kind: str = "test_pypi",
    target_index: str = "testpypi",
    credential_handle: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "status": "ready",
        "can_publish": True,
        "package": {
            "name": package_name,
            "version": version,
            "artifact_kind": "python_package",
            "package_kind": None,
            "project_path": None,
            "revision_code_package_id": None,
        },
        "target_kind": target_kind,
        "target_index": target_index,
        "credential": {
            "identity_id": "00000000-0000-0000-0000-000000000001",
            "credential_profile_id": "00000000-0000-0000-0000-000000000002",
            "readiness_receipt_id": "00000000-0000-0000-0000-000000000003",
            "status": "ready",
            "available": True,
            "target_kind": target_kind,
            "resolver_kind": "env",
            "secret_ref_key": "AWARE_TESTPYPI_TOKEN",
            "credential_handle_present": True,
            "missing_requirements": [],
            "raw_secret_returned": False,
            "receipt_key": "identity/readiness/testpypi",
        },
        "credential_handle": credential_handle
        or {
            "resolver": "env",
            "env_var": "AWARE_TESTPYPI_TOKEN",
        },
        "checks": [
            {
                "key": "credential_readiness",
                "status": "passed",
                "message": "credential readiness is ready",
            }
        ],
        "missing_requirements": [],
        "track": None,
        "requested_by": None,
    }
