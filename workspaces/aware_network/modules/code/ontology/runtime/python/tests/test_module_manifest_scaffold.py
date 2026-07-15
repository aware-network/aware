from pathlib import Path

from aware_code.module_manifest.scaffold import (
    build_module_scaffold_files,
    build_module_scaffold_spec,
)


def test_module_scaffold_runtime_pyproject_uses_stable_latest_pydantic_floor(
    tmp_path: Path,
) -> None:
    spec = build_module_scaffold_spec(module_id="demo_module")

    files = build_module_scaffold_files(repo_root=tmp_path, spec=spec)

    pyproject_path = (
        tmp_path.resolve() / "modules" / "demo_module" / "runtime" / "pyproject.toml"
    )
    pyproject_text = files[pyproject_path]
    assert '"pydantic>=2.13.4,<3.0.0"' in pyproject_text
    assert '"pydantic>=2.8.2,<3.0.0"' not in pyproject_text
