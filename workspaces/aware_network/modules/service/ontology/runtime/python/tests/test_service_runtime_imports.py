from __future__ import annotations

import os
import subprocess
import sys

from _service_runtime_test_paths import REPO_ROOT


def _run_import(script: str) -> subprocess.CompletedProcess[str]:
    repo_root = REPO_ROOT
    env = os.environ.copy()
    pythonpath_entries = [str(repo_root)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_service_runtime_package_is_lazy_for_runtime_bootstrap() -> None:
    result = _run_import(
        "import sys; "
        "import aware_service_runtime; "
        "assert 'aware_service_runtime.api_ingress' not in sys.modules"
    )

    assert result.returncode == 0, (
        "fresh interpreter import should not fail\n"
        + f"stdout:\n{result.stdout}\n"
        + f"stderr:\n{result.stderr}"
    )


def test_runtime_error_registry_import_stays_clear_of_service_api_ingress_cycle() -> (
    None
):
    result = _run_import(
        "import sys; "
        "from aware_service_runtime.error_codes import ("
        "ErrorCategory, ErrorCodeRegistry, ErrorSeverity"
        "); "
        "registry = ErrorCodeRegistry(definitions=[{"
        "'code': 'service.runtime.import_boundary', "
        "'category': ErrorCategory.runtime_invariant, "
        "'default_severity': ErrorSeverity.error, "
        "'title': 'Import boundary', "
        "'description': 'Service local registry proof.', "
        "'owner_package': 'aware-service-runtime'"
        "}]); "
        "assert registry.definition_for('service.runtime.import_boundary') is not None; "
        "assert 'aware_service_runtime.api_ingress' not in sys.modules"
    )

    assert result.returncode == 0, (
        "runtime error registry import should not pull service api ingress\n"
        + f"stdout:\n{result.stdout}\n"
        + f"stderr:\n{result.stderr}"
    )
