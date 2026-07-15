from __future__ import annotations

from pathlib import Path

from aware_experience.compiler.compile import compile_experience_workspace
from aware_experience.compiler.workspace import ExperienceWorkspace


def _write_experience_toml(
    *,
    root: Path,
    environment_handle: str = "kernel",
    sources_dir: str = "experiences",
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
) -> Path:
    include = include_paths or ["**/*.aware"]
    exclude = exclude_paths or []
    toml = (
        "aware_experience = 1\n\n"
        "[experience]\n"
        'package_name = "assistance"\n'
        'fqn_prefix = "assistance"\n\n'
        "[build]\n"
        f'environment_handle = "{environment_handle}"\n'
        f'sources_dir = "{sources_dir}"\n'
        f"include_paths = {include!r}\n"
        f"exclude_paths = {exclude!r}\n"
        "force_fresh_scan = true\n"
    )
    path = root / "aware.experience.toml"
    path.write_text(toml, encoding="utf-8")
    return path


def test_workspace_snapshot_discovers_sources_and_applies_excludes(tmp_path) -> None:
    root = tmp_path
    (root / "aware.workspace.toml").write_text("aware_workspace = 1\n", encoding="utf-8")
    (root / "experiences" / "assistance").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "assistance" / "program.aware").write_text(
        "program X() {}\n", encoding="utf-8"
    )
    (root / "experiences" / "assistance" / "_draft").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "assistance" / "_draft" / "draft.aware").write_text(
        "program Draft() {}\n", encoding="utf-8"
    )
    (root / "experiences" / "shared").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "shared" / "common.aware").write_text(
        "program Common() {}\n", encoding="utf-8"
    )
    spec_path = _write_experience_toml(
        root=root,
        exclude_paths=["**/_draft/**"],
    )

    workspace = ExperienceWorkspace.from_toml(toml_path=spec_path)
    snapshot = workspace.build_snapshot()
    assert snapshot.repo_root == root.resolve()
    assert [p.as_posix() for p in snapshot.source_files] == [
        "experiences/assistance/program.aware",
        "experiences/shared/common.aware",
    ]


def test_compile_experience_workspace_does_not_require_environment_manifest(tmp_path) -> None:
    root = tmp_path
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "program.aware").write_text(
        "program X() {}\n", encoding="utf-8"
    )
    spec_path = _write_experience_toml(root=root)

    result = compile_experience_workspace(toml_path=spec_path)
    assert result.snapshot.source_files == (Path("experiences/program.aware"),)


def test_compile_experience_workspace_is_read_only(tmp_path) -> None:
    root = tmp_path
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "program.aware").write_text(
        "program X() {}\n", encoding="utf-8"
    )
    spec_path = _write_experience_toml(root=root)

    result = compile_experience_workspace(toml_path=spec_path)
    assert result.snapshot.source_files == (Path("experiences/program.aware"),)
    assert not (root / "_aware").exists()
    assert not (root / ".aware").exists()
