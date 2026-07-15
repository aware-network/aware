from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from aware_code.package.schemas import CodePackageInfo
from aware_code.package import test_execution
from aware_code.package.test_execution import run_code_package_test_inventory
from aware_code.package.test_inventory import (
    CodePackageTestUnitInventory,
    build_code_package_test_inventory_for_package_info,
    build_code_package_test_inventory_from_files,
)
from aware_code_ontology.code.code_enums import CodeLanguage


def test_code_package_test_execution_runs_passing_pytest_unit(tmp_path: Path) -> None:
    inventory = _write_python_inventory(
        tmp_path=tmp_path,
        package_name="demo-passing",
        source="def test_demo_passes():\n    assert True\n",
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.backend_kind == "aware_test_runner"
    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 1
    assert receipt.total_tests == 1
    assert receipt.passed_tests == 1
    assert receipt.failed_tests == 0
    assert receipt.error is None
    assert len(receipt.unit_receipts) == 1
    unit_receipt = receipt.unit_receipts[0]
    inventory_unit = inventory.units[0]
    assert unit_receipt.code_package_id == inventory.code_package_id
    assert unit_receipt.code_test_id == inventory_unit.code_test_id
    assert unit_receipt.code_test_unit_id == inventory_unit.code_test_unit_id
    assert unit_receipt.selector == "tests/test_demo.py::test_demo_passes"
    assert unit_receipt.status == "passed"
    assert unit_receipt.failures == ()


def test_code_package_test_execution_isolates_pytest_from_running_event_loop(
    tmp_path: Path,
) -> None:
    inventory = _write_python_inventory(
        tmp_path=tmp_path,
        package_name="demo-asyncio-run",
        source=(
            "import asyncio\n\n"
            + "async def _value():\n"
            + "    return 1\n\n"
            + "def test_uses_asyncio_run():\n"
            + "    assert asyncio.run(_value()) == 1\n"
        ),
    )

    async def _run_inside_event_loop():
        return run_code_package_test_inventory(
            inventory=inventory,
            workspace_root=tmp_path,
        )

    receipt = asyncio.run(_run_inside_event_loop())

    assert receipt.status == "passed"
    assert receipt.total_tests == 1
    assert receipt.failed_tests == 0
    assert receipt.unit_receipts[0].status == "passed"


def test_code_package_test_execution_returns_failing_pytest_unit_receipt(
    tmp_path: Path,
) -> None:
    inventory = _write_python_inventory(
        tmp_path=tmp_path,
        package_name="demo-failing",
        source="def test_demo_fails():\n    assert False\n",
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "failed"
    assert receipt.total_tests == 1
    assert receipt.failed_tests == 1
    assert receipt.error is not None
    unit_receipt = receipt.unit_receipts[0]
    assert unit_receipt.status == "failed"
    assert unit_receipt.code_test_unit_id == inventory.units[0].code_test_unit_id
    assert unit_receipt.failures
    assert unit_receipt.failures[0].test_name == "test_demo_fails"
    assert "assert False" in unit_receipt.failures[0].failure_reason


def test_code_package_test_execution_batches_pytest_units_once(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(
        "def test_first():\n    assert True\n\n"
        + "def test_second():\n    assert True\n",
        encoding="utf-8",
    )
    inventory = _inventory_for_python_package(
        tmp_path=tmp_path, package_name="demo-batch"
    )
    selected_units = tuple(sorted(inventory.units, key=lambda unit: unit.selector))
    calls: list[tuple[str, ...]] = []

    def fake_run_python_units(**kwargs):
        units = tuple(kwargs["units"])
        calls.append(tuple(unit.selector for unit in units))
        return SimpleNamespace(
            exit_code=0,
            passed=True,
            total_tests=len(units),
            passed_tests=len(units),
            failed_tests=0,
            skipped_tests=0,
            failures=[],
            test_cases=[
                SimpleNamespace(
                    nodeid=f"{tmp_path.name}/{unit.selector}",
                    test_name=unit.name or unit.selector,
                    outcome="passed",
                    duration=0.01,
                    failure=None,
                )
                for unit in units
            ],
            duration=0.02,
        )

    monkeypatch.setattr(test_execution, "_run_python_units", fake_run_python_units)

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert calls == [tuple(unit.selector for unit in selected_units)]
    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 2
    assert receipt.total_tests == 2
    assert [unit.selector for unit in receipt.unit_receipts] == [
        unit.selector for unit in selected_units
    ]


def test_code_package_test_execution_maps_batched_mixed_pytest_results(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(
        "def test_first_passes():\n    assert True\n\n"
        + "def test_second_fails():\n    assert False\n",
        encoding="utf-8",
    )
    inventory = _inventory_for_python_package(
        tmp_path=tmp_path, package_name="demo-mixed"
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "failed"
    assert receipt.selected_unit_count == 2
    assert receipt.total_tests == 2
    assert receipt.passed_tests == 1
    assert receipt.failed_tests == 1
    statuses_by_selector = {
        unit_receipt.selector: unit_receipt.status
        for unit_receipt in receipt.unit_receipts
    }
    assert statuses_by_selector == {
        "tests/test_demo.py::test_first_passes": "passed",
        "tests/test_demo.py::test_second_fails": "failed",
    }
    failed_receipt = next(
        unit_receipt
        for unit_receipt in receipt.unit_receipts
        if unit_receipt.status == "failed"
    )
    assert failed_receipt.failures
    assert "assert False" in failed_receipt.failures[0].failure_reason


def test_code_package_test_execution_aggregates_parameterized_pytest_results(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(
        "import pytest\n\n"
        + "@pytest.mark.parametrize('value', [1, 2])\n"
        + "def test_parameterized(value):\n"
        + "    assert value in {1, 2}\n",
        encoding="utf-8",
    )
    inventory = _inventory_for_python_package(
        tmp_path=tmp_path, package_name="demo-parameterized"
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 1
    assert receipt.total_tests == 2
    assert receipt.passed_tests == 2
    assert receipt.failed_tests == 0
    assert receipt.unit_receipts[0].selector == "tests/test_demo.py::test_parameterized"
    assert receipt.unit_receipts[0].total_tests == 2
    assert receipt.unit_receipts[0].passed_tests == 2


def test_code_package_test_execution_maps_batched_skipped_pytest_results(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(
        "import pytest\n\n"
        + "def test_first_passes():\n    assert True\n\n"
        + "@pytest.mark.skip(reason='not ready')\n"
        + "def test_second_skips():\n    assert True\n",
        encoding="utf-8",
    )
    inventory = _inventory_for_python_package(
        tmp_path=tmp_path, package_name="demo-skip"
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 2
    assert receipt.total_tests == 2
    assert receipt.passed_tests == 1
    assert receipt.skipped_tests == 1
    statuses_by_selector = {
        unit_receipt.selector: unit_receipt.status
        for unit_receipt in receipt.unit_receipts
    }
    assert statuses_by_selector == {
        "tests/test_demo.py::test_first_passes": "passed",
        "tests/test_demo.py::test_second_skips": "skipped",
    }


def test_code_package_test_execution_filters_by_code_test_unit_id(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(
        "def test_first():\n    assert True\n\n"
        + "def test_second():\n    assert True\n",
        encoding="utf-8",
    )
    inventory = _inventory_for_python_package(
        tmp_path=tmp_path, package_name="demo-filter"
    )
    second_unit = next(
        unit for unit in inventory.units if unit.selector.endswith("::test_second")
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
        code_test_unit_ids=(second_unit.code_test_unit_id,),
    )

    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 1
    assert receipt.total_tests == 1
    assert [unit.selector for unit in receipt.unit_receipts] == [second_unit.selector]


def test_code_package_test_execution_fails_closed_for_unsupported_language() -> None:
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo_dart_unsupported",
        language=CodeLanguage.dart,
        manifest_kind="pubspec_yaml",
        manifest_relative_path="pubspec.yaml",
        package_root=".",
        sources_root="lib",
        manifest_text="dev_dependencies:\n  flutter_test:\n    sdk: flutter\n",
        files={
            "test/widget_test.dart": (
                "import 'package:flutter_test/flutter_test.dart';\n"
                "void main() {\n"
                "  testWidgets('renders home', (tester) async {});\n"
                "}\n"
            ),
        },
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=Path("."),
    )

    assert receipt.status == "unsupported"
    assert receipt.selected_unit_count == 1
    assert receipt.total_tests == 0
    assert receipt.unit_receipts[0].status == "unsupported"
    assert (
        receipt.unit_receipts[0].code_test_unit_id
        == inventory.units[0].code_test_unit_id
    )
    assert receipt.error is not None
    assert "supports Python pytest units only" in receipt.error


def test_code_package_test_execution_runs_python_unittest_units_through_pytest(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    source = (
        "import unittest\n\n"
        + "class TestDemo:\n"
        + "    def test_demo(self):\n"
        + "        assert True\n"
    )
    _ = (tests_dir / "test_demo.py").write_text(source, encoding="utf-8")
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo-unittest",
        language=CodeLanguage.python,
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root=tmp_path.as_posix(),
        sources_root=None,
        manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
        files={"tests/test_demo.py": source},
    )
    unittest_framework = next(
        framework for framework in inventory.frameworks if framework.name == "unittest"
    )
    unittest_unit = CodePackageTestUnitInventory(
        code_package_code_id=uuid4(),
        code_id=uuid4(),
        code_section_id=uuid4(),
        code_test_framework_id=unittest_framework.code_test_framework_id,
        code_test_id=uuid4(),
        code_package_test_id=uuid4(),
        code_test_unit_id=uuid4(),
        framework_name="unittest",
        relative_path="tests/test_demo.py",
        unit_key="unittest:tests.test_demo.TestDemo.test_demo",
        selector="tests.test_demo.TestDemo.test_demo",
        kind="method",
        name="test_demo",
    )
    inventory = replace(inventory, units=(unittest_unit,))

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 1
    assert receipt.total_tests == 1
    assert receipt.passed_tests == 1
    assert receipt.unit_receipts[0].status == "passed"
    assert receipt.unit_receipts[0].framework_name == "unittest"
    assert receipt.unit_receipts[0].selector == "tests.test_demo.TestDemo.test_demo"
    assert receipt.error is None


def test_code_package_test_execution_does_not_leak_workspace_backend_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    inventory = _write_python_inventory(
        tmp_path=tmp_path,
        package_name="demo-backend-env",
        source=(
            "import os\n\n"
            + "def test_workspace_backend_env_is_not_inherited():\n"
            + "    assert os.getenv('AWARE_PERSISTENCE_BACKEND') is None\n"
        ),
    )

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert receipt.status == "passed"
    assert receipt.total_tests == 1
    assert receipt.failed_tests == 0
    assert receipt.error is None


def test_code_package_test_execution_maps_shared_pytest_nodeid_to_framework_aliases(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    source = (
        "import unittest\n\n"
        + "class TestDemo(unittest.TestCase):\n"
        + "    def test_demo(self):\n"
        + "        self.assertTrue(True)\n"
    )
    _ = (tests_dir / "test_demo.py").write_text(source, encoding="utf-8")
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo-framework-alias",
        language=CodeLanguage.python,
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root=tmp_path.as_posix(),
        sources_root=None,
        manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
        files={"tests/test_demo.py": source},
    )
    pytest_unit = CodePackageTestUnitInventory(
        code_package_code_id=uuid4(),
        code_id=uuid4(),
        code_section_id=uuid4(),
        code_test_framework_id=uuid4(),
        code_test_id=uuid4(),
        code_package_test_id=uuid4(),
        code_test_unit_id=uuid4(),
        framework_name="pytest",
        relative_path="tests/test_demo.py",
        unit_key="pytest:tests/test_demo.py:TestDemo.test_demo",
        selector="tests/test_demo.py::TestDemo::test_demo",
        kind="method",
        name="test_demo",
    )
    unittest_unit = CodePackageTestUnitInventory(
        code_package_code_id=uuid4(),
        code_id=uuid4(),
        code_section_id=uuid4(),
        code_test_framework_id=uuid4(),
        code_test_id=uuid4(),
        code_package_test_id=uuid4(),
        code_test_unit_id=uuid4(),
        framework_name="unittest",
        relative_path="tests/test_demo.py",
        unit_key="unittest:tests.test_demo.TestDemo.test_demo",
        selector="tests.test_demo.TestDemo.test_demo",
        kind="method",
        name="test_demo",
    )
    inventory = replace(inventory, units=(pytest_unit, unittest_unit))

    receipt = run_code_package_test_inventory(
        inventory=inventory,
        workspace_root=tmp_path,
    )

    assert {(unit.framework_name, unit.selector) for unit in inventory.units} == {
        ("pytest", "tests/test_demo.py::TestDemo::test_demo"),
        ("unittest", "tests.test_demo.TestDemo.test_demo"),
    }
    assert receipt.status == "passed"
    assert receipt.selected_unit_count == 2
    assert receipt.total_tests == 2
    assert receipt.passed_tests == 2
    assert receipt.error is None
    assert {
        (unit_receipt.framework_name, unit_receipt.status)
        for unit_receipt in receipt.unit_receipts
    } == {("pytest", "passed"), ("unittest", "passed")}


def _write_python_inventory(
    *,
    tmp_path: Path,
    package_name: str,
    source: str,
):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tests_dir / "test_demo.py").write_text(source, encoding="utf-8")
    return _inventory_for_python_package(tmp_path=tmp_path, package_name=package_name)


def _inventory_for_python_package(*, tmp_path: Path, package_name: str):
    return build_code_package_test_inventory_for_package_info(
        code_package=CodePackageInfo(
            name=package_name,
            root_path=tmp_path,
            manifest_path=tmp_path / "pyproject.toml",
            language=CodeLanguage.python,
            metadata={},
        ),
        workspace_root=tmp_path,
    )
