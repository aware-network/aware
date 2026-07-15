from __future__ import annotations

import json
from pathlib import Path

import msgpack

from _interface_runtime_test_paths import REPO_ROOT


def _repo_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


def _msgpack_text(path: Path) -> str:
    payload = msgpack.unpackb(path.read_bytes(), raw=False, strict_map_key=False)
    return str(payload)


def test_boot_interface_graph_program_is_shell_only() -> None:
    program_path = _repo_path(
        "workspaces",
        "aware_network",
        "modules",
        "interface",
        "experiences",
        "aware_control",
        "programs",
        "interface",
        "ensure_boot_interface_graph.aware",
    )
    source = program_path.read_text(encoding="utf-8")
    impl_source = source.split("program EnsureBootInterfaceGraph impl", maxsplit=1)[1]
    config_source = source.split(
        "program EnsureBootInterfaceGraphConfig",
        maxsplit=1,
    )[
        1
    ].split("program EnsureBootInterfaceGraph impl", maxsplit=1,)[0]

    assert "interface_id UUID = plan.interface_id" in config_source
    assert "os String = plan.os" in config_source
    assert "version String = plan.version" in config_source
    assert "window_key_id UUID = interface.stable_window_key_id" in config_source
    assert "window_id UUID = interface.stable_window_id" in config_source

    assert "plan.environment_id" not in config_source
    assert "plan.thread_id" not in config_source
    assert "plan.opgi_id" not in config_source
    assert "environment_" not in config_source
    assert "thread_" not in config_source
    assert "focus_" not in config_source
    assert "layout_" not in config_source

    assert "interface.Interface.build_via_interface_config" in impl_source
    assert "window.Window.build" in impl_source
    assert "interface.Interface.attach_window" in impl_source

    forbidden_impl_terms = (
        "attach_environment",
        "set_active_window_thread",
        "set_active_window_navigation_context",
        "Environment.",
        "Thread.",
        "Layout.",
        "LayoutSection.",
        "Section.",
        "Focus.",
        "FocusScope.",
    )
    for term in forbidden_impl_terms:
        assert term not in impl_source


def test_interface_python_package_artifacts_use_window_navigation_context() -> None:
    package_root = _repo_path(
        "workspaces",
        "aware_network",
        "modules",
        "interface",
        "ontology",
        "structure",
        "python",
        "orm_runtime",
        "aware_interface_ontology",
        "_aware",
    )
    binding_text = _msgpack_text(package_root / "orm.graph.binding.msgpack")
    bootstrap_text = (package_root / "python.bootstrap.json").read_text(
        encoding="utf-8"
    )

    assert "InterfaceWindowNavigationContext" in binding_text
    assert "InterfaceWindowThread" not in binding_text
    assert "interface_window_thread" not in binding_text

    assert (
        "aware_interface_ontology.interface.interface_window_navigation_context"
        in bootstrap_text
    )
    assert (
        "aware_interface_ontology.interface.interface_window_thread"
        not in bootstrap_text
    )


def test_generated_meta_handlers_use_window_navigation_context_rail() -> None:
    handlers_path = _repo_path(
        "workspaces",
        "aware_network",
        "modules",
        "interface",
        "ontology",
        "runtime",
        "python",
        "aware_interface",
        "handlers",
        "_generated",
        "meta_handlers.py",
    )
    source = handlers_path.read_text(encoding="utf-8")

    assert "set_active_window_navigation_context" in source
    assert "interface_window_navigation_context__create_via_interface_window" in source
    assert "InterfaceWindowNavigationContext" in source
    assert "set_active_window_thread" not in source
    assert "interface_window_thread" not in source
    assert "InterfaceWindowThread" not in source


def test_legacy_runtime_manifest_is_not_the_interface_package_authority() -> None:
    legacy_manifest_path = _repo_path(
        "workspaces",
        "aware_network",
        "modules",
        "interface",
        "ontology",
        "structure",
        ".aware",
        "environment",
        "runtime",
        "environment.manifest.json",
    )
    manifest = json.loads(legacy_manifest_path.read_text(encoding="utf-8"))

    assert (
        manifest["ocg"]["hash"]
        == "sha256:302e76e5f91d0084082281bace79b5e4fbb5a2915f4d04d816a786d7e16305a9"
    )
    assert _repo_path(
        "workspaces",
        "aware_network",
        "modules",
        "interface",
        "ontology",
        "structure",
        "python",
        "orm_runtime",
        "aware_interface_ontology",
        "_aware",
        "orm.graph.binding.msgpack",
    ).exists()
