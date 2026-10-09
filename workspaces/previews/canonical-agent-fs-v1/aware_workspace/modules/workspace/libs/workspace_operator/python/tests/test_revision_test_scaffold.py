from __future__ import annotations

from pathlib import Path

from aware_workspace_operator.pipeline.stages.scaffold import (
    ensure_workspace_scaffold,
)
from aware_workspace_operator.renderers import (
    render_workspace_ci_workflow,
    render_workspace_pyproject,
)


def test_workspace_scaffold_uses_revision_test_rail(tmp_path: Path) -> None:
    pyproject = render_workspace_pyproject(repo_root=tmp_path)
    workflow = render_workspace_ci_workflow(
        environment_file_relpath="aware.environment.toml"
    )

    assert "aware-test-runner" not in pyproject
    assert "aware-cli workspace test" in workflow
    assert "aware-tests" not in workflow
    assert "AWARE_TEST_RUNNER_MANIFEST_DIRS" not in workflow


def test_workspace_scaffold_does_not_materialize_runner_manifests(
    tmp_path: Path,
) -> None:
    report = ensure_workspace_scaffold(
        repo_root=tmp_path,
        module_ids=("demo",),
        environment_file_relpath="aware.environment.toml",
        write_workspace_scaffold=True,
    )

    assert report.write_requested is True
    assert not (tmp_path / "configs/manifests").exists()
