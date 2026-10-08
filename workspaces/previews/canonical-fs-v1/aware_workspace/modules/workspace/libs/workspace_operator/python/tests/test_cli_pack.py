from __future__ import annotations

from aware_workspace_operator.cli.pack import get_command_specs


def test_workspace_operator_mounts_commit_and_module_commands() -> None:
    specs = {str(spec["name"]): spec for spec in get_command_specs()}

    assert set(specs) == {"commit", "module"}
    assert specs["module"]["module"] == (
        "aware_workspace_operator.cli.module_command"
    )
    assert specs["module"]["source"] == "workspace-operator-pack"
