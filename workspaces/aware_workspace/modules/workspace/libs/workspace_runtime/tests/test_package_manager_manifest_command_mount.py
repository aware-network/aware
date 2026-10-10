from __future__ import annotations

import argparse
import subprocess
import sys

from aware_workspace_command.workspace_command import register_workspace_parser


def test_package_manager_manifest_parser_is_mounted_only_when_selected() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_workspace_parser(
        subparsers,
        args_list=("workspace", "package-manager-manifest"),
    )

    workspace = subparsers.choices["workspace"]
    workspace_subparsers = next(
        action
        for action in workspace._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert tuple(workspace_subparsers.choices) == ("package-manager-manifest",)


def test_lightweight_command_import_does_not_import_semantic_runtime() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import aware_workspace_command.workspace_command; "
                "assert 'aware_workspace.materialization.package_manager_runtime' "
                "not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
