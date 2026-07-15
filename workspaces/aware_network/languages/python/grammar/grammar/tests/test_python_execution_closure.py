from pathlib import Path
import json

from aware_code.language.execution_closure import (
    CodeLanguageExecutionClosureRequest,
    CodeLanguageExecutionPackageRef,
)
from python_grammar.execution_closure import PythonExecutionClosureBuilder


def test_python_execution_closure_renders_required_deps_and_source_map(
    tmp_path: Path,
) -> None:
    platform_package = tmp_path / "platform-src" / "aware-node-service"
    platform_package.mkdir(parents=True)
    (platform_package / "pyproject.toml").write_text(
        "\n".join(
            (
                "[project]",
                "name = 'aware-node-service'",
                "",
                "[tool.uv.sources]",
                "aware-runtime = { workspace = true }",
                "",
            )
        ),
        encoding="utf-8",
    )
    (platform_package / "samples").mkdir()
    (platform_package / "samples" / "fixture.bin").write_bytes(b"sample")
    (platform_package / "tests").mkdir()
    (platform_package / "tests" / "test_runtime.py").write_text(
        "def test_runtime():\n    pass\n",
        encoding="utf-8",
    )
    helper_package = tmp_path / "platform-src" / "aware-runtime"
    helper_package.mkdir(parents=True)
    (helper_package / "pyproject.toml").write_text(
        "[project]\nname = 'aware-runtime'\n",
        encoding="utf-8",
    )
    revision_package = tmp_path / "run" / "fetched" / "pkg"
    revision_package.mkdir(parents=True)
    (revision_package / "pyproject.toml").write_text(
        "[project]\nname = 'home-story-api'\n",
        encoding="utf-8",
    )

    result = PythonExecutionClosureBuilder().materialize_execution_closure(
        CodeLanguageExecutionClosureRequest(
            closure_key="home-runtime",
            output_root=tmp_path / "run" / "runtime" / "python",
            packages=(
                CodeLanguageExecutionPackageRef(
                    package_name="aware-node-service",
                    role="platform_runtime",
                    source_root=platform_package,
                    manifest_path=platform_package / "pyproject.toml",
                    copy_to_closure=True,
                    required=True,
                ),
                CodeLanguageExecutionPackageRef(
                    package_name="aware-runtime",
                    role="platform_runtime",
                    source_root=helper_package,
                    manifest_path=helper_package / "pyproject.toml",
                    copy_to_closure=True,
                    required=False,
                ),
                CodeLanguageExecutionPackageRef(
                    package_name="aware-api",
                    role="platform_runtime",
                    required=True,
                    metadata={"python_dependency_alias_for": "aware-api-client"},
                ),
                CodeLanguageExecutionPackageRef(
                    package_name="home-story-api",
                    role="workspace_revision",
                    source_root=revision_package,
                    required=True,
                ),
            ),
        )
    )

    pyproject_text = result.project_path.read_text(encoding="utf-8")
    assert '"aware-node-service",' in pyproject_text
    assert '"aware-api",' in pyproject_text
    assert '"home-story-api",' in pyproject_text
    assert '"aware-runtime",' not in pyproject_text
    assert '"aware-api" = { path = "sources/platform_runtime/aware-api" }' in (
        pyproject_text
    )
    assert '"aware-runtime" = { path = "sources/platform_runtime/aware-runtime" }' in (
        pyproject_text
    )
    assert '"home-story-api" = { path = "../../fetched/pkg" }' in pyproject_text

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == "aware.code.language.execution_closure.python.v0"
    assert len(manifest["packages"]) == 4
    assert str(tmp_path / "platform-src") not in result.manifest_path.read_text(
        encoding="utf-8"
    )
    alias_pyproject = (
        result.output_root
        / "sources"
        / "platform_runtime"
        / "aware-api"
        / "pyproject.toml"
    )
    assert 'name = "aware-api"' in alias_pyproject.read_text(encoding="utf-8")
    assert '"aware-api-client",' in alias_pyproject.read_text(encoding="utf-8")
    copied_platform_pyproject = (
        result.output_root
        / "sources"
        / "platform_runtime"
        / "aware-node-service"
        / "pyproject.toml"
    )
    assert "workspace = true" not in copied_platform_pyproject.read_text(
        encoding="utf-8"
    )
    assert not (copied_platform_pyproject.parent / "samples").exists()
    assert not (copied_platform_pyproject.parent / "tests").exists()
