from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys
import textwrap


def test_service_semantic_contract_import_does_not_bootstrap_ontology_runtime() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import aware_service_runtime.semantic_contract; "
            "assert 'aware_service_ontology' not in sys.modules",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_service_runtime_resolution_has_no_direct_deprecated_runtime_imports() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "aware_service_runtime"
        / "runtime_resolution.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))

    deprecated_imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "aware_runtime":
                    deprecated_imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] == "aware_runtime":
                deprecated_imports.append((node.module, node.lineno))

    assert deprecated_imports == []
    top_level_source = source.split("if TYPE_CHECKING:", 1)[0]
    assert "aware_structure.environment_config" not in top_level_source
    assert "resolve_module_runtime_artifact_sources" in source
    assert "aware.service_protocol.runtime_sources.v1" in source


def test_service_runtime_resolution_imports_without_workspace_runtime_package() -> None:
    script = textwrap.dedent(
        """
        import builtins

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("aware_workspace"):
                error = ModuleNotFoundError(f"No module named {name!r}")
                error.name = name
                raise error
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

        import aware_service_runtime.runtime_resolution as runtime_resolution

        assert runtime_resolution is not None
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
