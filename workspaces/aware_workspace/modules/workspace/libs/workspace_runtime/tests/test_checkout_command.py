from __future__ import annotations

import argparse
import subprocess
import sys

from aware_workspace_command.workspace_command import register_workspace_parser


def test_workspace_checkout_is_available_in_parent_help() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    workspace = register_workspace_parser(subparsers, args_list=("workspace", "--help"))
    assert "checkout" in workspace.format_help()
    args = parser.parse_args(
        ["workspace", "checkout", "--package", "sample[extra]", "--plan"]
    )
    assert args.package == ["sample[extra]"]


def test_checkout_command_import_does_not_load_ontology_or_service() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import aware_workspace_command.checkout_command; import aware_workspace_runtime.package_checkout; import aware_workspace_runtime.checkout_profiles; assert not any(n == 'aware_workspace' or n.startswith(('aware_orm', 'aware_meta', 'aware_ontology', 'aware_local_dev_service')) for n in sys.modules)",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_named_profiles_and_overlays_are_repeatable_command_selections() -> None:
    parser = argparse.ArgumentParser()
    register_workspace_parser(
        parser.add_subparsers(dest="command"), args_list=("workspace", "checkout")
    )
    args = parser.parse_args(
        [
            "workspace",
            "checkout",
            "--profile",
            "one",
            "--profile",
            "two",
            "--overlay",
            "public_docs",
            "--package",
            "sample-c",
            "--plan",
        ]
    )
    assert args.profile == ["one", "two"]
    assert args.overlay == ["public_docs"]
    assert args.package == ["sample-c"]
