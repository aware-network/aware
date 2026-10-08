from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from aware_workspace_operator.models import WorkspaceQualityOptions
from aware_workspace_operator.quality import run_workspace_quality_gates
from aware_workspace_operator.pipeline.stages.scaffold import ensure_delivery_contracts


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    raise AssertionError("aware.repo.toml not found")


def _write_text(path: Path, contents: str) -> None:
    _ = path.write_text(contents, encoding="utf-8")


def test_quality_gates_plan_python(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    python_file = repo_root / "services" / "environment" / "tests" / "test_sample.py"
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def test_sample() -> None:\n    assert True\n")

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            run_commands=False,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert outcome.report.detected_languages == ["python"]
    assert [item.gate_id for item in outcome.report.commands] == [
        "python.compile.syntax",
        "python.flake8",
        "python.mypy",
        "python.basedpyright",
    ]
    assert all(item.status == "planned" for item in outcome.report.commands)


def test_quality_gates_missing_tool_can_be_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    python_file = repo_root / "module.py"
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def fn() -> None:\n    return None\n")

    def _raise_missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("missing tool")

    monkeypatch.setattr(
        "aware_workspace_operator.quality.subprocess.run", _raise_missing
    )

    failed = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            run_commands=True,
            fail_on_missing_command=True,
        )
    )
    assert failed.exit_code == 2
    assert failed.report.status == "failed"
    assert failed.report.commands[0].status == "failed"

    skipped = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            run_commands=True,
            fail_on_missing_command=False,
        )
    )
    assert skipped.exit_code == 0
    assert skipped.report.status == "ok"
    assert skipped.report.commands[0].status == "skipped"


def test_quality_gates_plan_applies_path_scoped_profile_from_contract(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    contracts_dir = repo_root / "configs" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    _write_text(repo_root / "aware.repo.toml", "aware_repo = 1\n")
    _write_text(
        contracts_dir / "quality_gates.toml",
        """
version = 1

[defaults.profile_by_language]
python = "standard"

[gates.python_flake8]
gate_id = "python.flake8"
language = "python"
command = ["uv", "run", "flake8"]
target_mode = "paths"

[gates.python_mypy]
gate_id = "python.mypy"
language = "python"
command = ["uv", "run", "mypy"]
target_mode = "paths"

[gates.python_basedpyright_error]
gate_id = "python.basedpyright.error"
language = "python"
command = ["uv", "run", "basedpyright", "--level", "error"]
target_mode = "paths"

[gates.python_basedpyright_warning]
gate_id = "python.basedpyright.warning"
language = "python"
command = ["uv", "run", "basedpyright", "--level", "warning", "--warnings"]
target_mode = "paths"

[profiles.python.standard]
gates = ["python.flake8", "python.mypy", "python.basedpyright.error"]

[profiles.python.strict]
gates = ["python.flake8", "python.mypy", "python.basedpyright.warning"]

[[path_profiles]]
language = "python"
path_prefix = "modules/meta"
profile = "strict"
""".strip()
        + "\n",
    )

    python_file = repo_root / "modules" / "meta" / "runtime" / "demo.py"
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def demo() -> None:\n    return None\n")

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            run_commands=False,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert [item.gate_id for item in outcome.report.commands] == [
        "python.flake8",
        "python.mypy",
        "python.basedpyright.warning",
    ]
    basedpyright = outcome.report.commands[-1]
    assert basedpyright.command == [
        "uv",
        "run",
        "basedpyright",
        "--level",
        "warning",
        "--warnings",
        "modules/meta/runtime/demo.py",
    ]


def test_delivery_contracts_are_rendered_without_root_config_authority(
    tmp_path: Path,
) -> None:
    status = ensure_delivery_contracts(
        repo_root=tmp_path,
        write_delivery_contracts=True,
    )

    contracts_root = tmp_path / "configs" / "contracts"
    assert len(status.created_paths) == 4
    assert {path.name for path in contracts_root.iterdir()} == {
        "agent_delivery.toml",
        "environment_experience.toml",
        "evidence_policy.toml",
        "quality_gates.toml",
    }
    for contract_path in contracts_root.iterdir():
        assert tomllib.loads(contract_path.read_text(encoding="utf-8"))["version"] == 1


def test_quality_gates_requested_language_not_detected_fails_closed(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    python_file = repo_root / "service.py"
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def run() -> None:\n    return None\n")

    with pytest.raises(ValueError, match="Requested languages are not detected"):
        _ = run_workspace_quality_gates(
            options=WorkspaceQualityOptions(
                repo_root=repo_root,
                target_paths=(str(python_file),),
                include_languages=("dart",),
                run_commands=False,
            )
        )


def test_quality_gates_requested_gate_filter_preserves_requested_order(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    python_file = repo_root / "service.py"
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def run() -> None:\n    return None\n")

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            include_gate_ids=("python.mypy", "python.flake8"),
            run_commands=False,
        )
    )
    assert [item.gate_id for item in outcome.report.commands] == [
        "python.mypy",
        "python.flake8",
    ]


def test_quality_gates_requested_gate_allows_policy_gate_outside_default_profile(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    contracts_dir = repo_root / "configs" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    _write_text(
        contracts_dir / "quality_gates.toml",
        """
version = 1

[defaults.profile_by_language]
python = "standard"

[gates.python_flake8]
gate_id = "python.flake8"
language = "python"
command = ["uv", "run", "flake8"]
target_mode = "paths"

[gates.python_mypy]
gate_id = "python.mypy"
language = "python"
command = ["uv", "run", "mypy"]
target_mode = "paths"

[gates.python_basedpyright_error]
gate_id = "python.basedpyright.error"
language = "python"
command = ["uv", "run", "basedpyright", "--level", "error"]
target_mode = "paths"

[gates.python_basedpyright_warning]
gate_id = "python.basedpyright.warning"
language = "python"
command = ["uv", "run", "basedpyright", "--level", "warning", "--warnings"]
target_mode = "paths"

[profiles.python.standard]
gates = ["python.flake8", "python.mypy", "python.basedpyright.error"]

[profiles.python.strict]
gates = ["python.flake8", "python.mypy", "python.basedpyright.warning"]
""".strip()
        + "\n",
    )

    python_file = (
        repo_root / "modules" / "agent" / "ontology" / "runtime" / "python" / "demo.py"
    )
    python_file.parent.mkdir(parents=True, exist_ok=True)
    _write_text(python_file, "def demo() -> None:\n    return None\n")

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(python_file),),
            include_gate_ids=(
                "python.flake8",
                "python.mypy",
                "python.basedpyright.warning",
            ),
            run_commands=False,
        )
    )

    assert [item.gate_id for item in outcome.report.commands] == [
        "python.flake8",
        "python.mypy",
        "python.basedpyright.warning",
    ]
    basedpyright = outcome.report.commands[-1]
    assert basedpyright.command == [
        "uv",
        "run",
        "basedpyright",
        "--level",
        "warning",
        "--warnings",
        "modules/agent/ontology/runtime/python/demo.py",
    ]


@pytest.mark.parametrize(
    ("path_parts",),
    [
        (
            (
                "workspaces",
                "aware_kernel",
                "languages",
                "aware",
                "grammar",
                "grammar",
                "aware_grammar",
                "code_language_plugin.py",
            ),
        ),
        (
            (
                "workspaces",
                "aware_kernel",
                "languages",
                "python",
                "grammar",
                "grammar",
                "python_grammar",
                "code_language_plugin.py",
            ),
        ),
        (
            (
                "workspaces",
                "aware_kernel",
                "languages",
                "sql",
                "grammar",
                "grammar",
                "sql_grammar",
                "code_language_plugin.py",
            ),
        ),
        (
            (
                "workspaces",
                "aware_kernel",
                "languages",
                "dart",
                "grammar",
                "grammar",
                "dart_grammar",
                "code_language_plugin.py",
            ),
        ),
    ],
)
def test_repo_quality_contract_applies_strict_profile_for_grammar_paths(
    path_parts: tuple[str, ...]
) -> None:
    repo_root = _repo_root()
    grammar_file = repo_root.joinpath(*path_parts)
    assert grammar_file.exists()

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(grammar_file),),
            run_commands=False,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert [item.gate_id for item in outcome.report.commands] == [
        "python.flake8",
        "python.mypy",
        "python.basedpyright.warning",
    ]


def test_repo_quality_contract_applies_meta_ocg_lane_profile() -> None:
    repo_root = _repo_root()
    target_file = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "meta"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_meta"
        / "graph"
        / "instance"
        / "scoped_index.py"
    )
    assert target_file.exists()

    outcome = run_workspace_quality_gates(
        options=WorkspaceQualityOptions(
            repo_root=repo_root,
            target_paths=(str(target_file),),
            run_commands=False,
        )
    )

    assert outcome.exit_code == 0
    assert outcome.report.status == "ok"
    assert [item.gate_id for item in outcome.report.commands] == [
        "python.flake8",
        "python.mypy",
        "python.basedpyright.warning",
        "python.no_reflection.ocg_via_oig",
    ]
