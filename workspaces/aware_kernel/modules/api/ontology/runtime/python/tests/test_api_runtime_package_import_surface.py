from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_aware_api_runtime_root_import_stays_lightweight() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    script = "\n".join(
        [
            "import json",
            "import sys",
            f"sys.path.insert(0, {str(repo_root)!r})",
            "import aware_api_runtime as api_runtime",
            'after_root = "aware_api_runtime.compile_materialization.service" in sys.modules',
            "_ = api_runtime.compile_api_workspace",
            'after_compile_export = "aware_api_runtime.compile_materialization.service" in sys.modules',
            "print(json.dumps({",
            '    "after_root": after_root,',
            '    "after_compile_export": after_compile_export,',
            "}))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["after_root"] is False
    assert payload["after_compile_export"] is False


def test_api_compile_plan_ir_import_surface_has_no_builder_facade() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    script = "\n".join(
        [
            "import importlib.util",
            "import json",
            "import sys",
            f"sys.path.insert(0, {str(repo_root)!r})",
            "from aware_api_runtime import ir",
            "payload = {",
            '    "ir_module": ir.APICompilePlan.__module__,',
            '    "has_builder_facade": importlib.util.find_spec("aware_api_runtime." + "builder") is not None,',
            "}",
            "print(json.dumps(payload, sort_keys=True))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "has_builder_facade": False,
        "ir_module": "aware_api_runtime.ir.compile_plan",
    }
