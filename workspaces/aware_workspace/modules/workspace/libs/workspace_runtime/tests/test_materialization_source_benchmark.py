"""The diagnostic benchmark preserves exact inventory and its proof grade."""

import importlib.util
import sys
from pathlib import Path

import pytest


def load_benchmark():
    path = Path(__file__).parents[1] / "benchmarks/materialization_source.py"
    spec = importlib.util.spec_from_file_location("materialization_source_benchmark", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("values", [[], [-1], [float("nan")], [float("inf")]])
def test_summary_refuses_invalid_or_missing_measurements(values):
    with pytest.raises(ValueError):
        load_benchmark().summarize(values)


def test_summary_reports_tail_without_dropping_slow_runs():
    value = load_benchmark().summarize([1, 2, 3, 4, 100])
    assert value == {"count": 5, "median_seconds": 3, "p95_seconds": 100, "maximum_seconds": 100}


def test_inventory_digest_binds_paths_bodies_and_lengths():
    module = load_benchmark()
    assert module.inventory_digest((("a", b"same"),)) != module.inventory_digest((("b", b"same"),))
    assert module.inventory_digest((("a", b"same"),)) != module.inventory_digest((("a", b"other"),))


async def test_original_component_benchmark_never_reports_command_success(tmp_path):
    root = tmp_path / "original"
    root.mkdir()
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="bench"\nworkspaces_dir="workspaces"\n'
        '[[workspaces]]\nhandle="test"\npath="test"\n',
    )
    workspace = root / "workspaces/test"
    workspace.mkdir(parents=True)
    (workspace / "aware.workspace.toml").write_text(
        'aware=1\n[workspace]\nhandle="test"\n[[workspace.modules]]\nid="main"\npath="main"\n',
    )
    module = workspace / "main"
    module.mkdir()
    packages = []
    for index in range(3):
        package = module / f"p{index}"
        package.mkdir()
        (package / "manifest.toml").write_bytes(b"original owner bytes")
        packages.append(f'[[packages]]\nid="p{index}"\nkind="example"\nmanifest="p{index}/manifest.toml"\n')
    (module / "aware.module.toml").write_text('aware=1\n[module]\n' + "".join(packages))
    before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = await load_benchmark().benchmark(root, samples=1, workspace="test")
    assert result["command_e2e_qualified"] is False
    assert result["target_command_e2e_seconds"] == 5.0
    assert result["inventory"]["declaration_count"] == 6
    assert [row.get("touched_packages") for row in result["metrics"]] == [None, 1, 3]
    assert all(row["count"] == 1 for row in result["metrics"])
    after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert after == before
