from __future__ import annotations

import subprocess
import sys
import textwrap


def test_interface_runtime_imports_without_workspace_runtime_package() -> None:
    """Interface host runtime must be deployable without Workspace installed."""

    script = textwrap.dedent(
        """
        import builtins
        import sys

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if (
                name == "aware_workspace"
                or name.startswith("aware_workspace.")
                or name == "aware_manifests.workspace"
                or name.startswith("aware_manifests.workspace.")
            ):
                error = ModuleNotFoundError(f"No module named {name!r}")
                error.name = name
                raise error
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

        import aware_interface
        from aware_interface.host_runtime import resolve_interface_config_bundle
        from aware_interface.pane_consumer_scope import resolve_workspace_manifest_paths
        from aware_interface.semantic_scope import load_interface_semantic_scope

        assert aware_interface.InterfaceHostRuntime is not None
        assert resolve_interface_config_bundle is not None
        assert resolve_workspace_manifest_paths is not None
        assert load_interface_semantic_scope is not None
        assert "aware_manifests.workspace" not in sys.modules
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
