from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from _api_runtime_test_paths import REPO_ROOT


_FORBIDDEN_API_RUNTIME_IMPORT_PREFIXES = (
    "aware_runtime",
    "aware_service_runtime",
    "aware_meta_service",
    "aware_meta_service_dto",
    "aware_meta_service_protocol",
)


def test_api_package_ref_service_protocol_runtime_resolution_no_aware_runtime() -> None:
    for relpath in (
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/package_ref_resolution.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/service_protocol/runtime.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/dependencies/runtime_resolution.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/compile_materialization/service.py",
        "modules/service/runtime/aware_service_runtime/runtime_resolution.py",
    ):
        source = (REPO_ROOT / relpath).read_text(encoding="utf-8")
        assert "aware_runtime" not in source
        assert "hydrate_orm_graph_from_oig" not in source


def test_api_runtime_has_no_service_or_meta_service_import_boundary_leaks() -> None:
    source_paths = (
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/compile.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/compile_materialization/service.py",
        "workspaces/aware_kernel/modules/api/ontology/runtime/python/pyproject.toml",
    )

    for relpath in source_paths:
        source = (REPO_ROOT / relpath).read_text(encoding="utf-8")
        assert "aware_runtime" not in source
        assert "aware_service_runtime" not in source
        assert "aware_meta_service" not in source
        assert "aware_meta_service_dto" not in source
        assert "aware_meta_service_protocol" not in source
        assert "RuntimeHarness" not in source
        assert "resolve_module_runtime_manifest" not in source
        assert "activate_runtime_imports" not in source


def test_api_compile_materialization_boundary_is_explicit() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime"
    )

    assert (runtime_root / "compile_materialization/service.py").is_file()
    assert not (runtime_root / "materialization/service.py").exists()


def test_api_materialization_helper_boundaries_are_explicit() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    tests_root = runtime_root.parent / "tests"
    forbidden_tokens = (
        "aware_api_runtime." + "materialization",
        "from aware_api_runtime." + "materialization",
        "import aware_api_runtime." + "materialization",
    )
    offenders: list[str] = []
    for source_root in (runtime_root, tests_root):
        for source_path in sorted(source_root.rglob("*.py")):
            if "__pycache__" in source_path.parts:
                continue
            source = source_path.read_text(encoding="utf-8")
            if any(token in source for token in forbidden_tokens):
                offenders.append(
                    source_path.relative_to(runtime_root.parent).as_posix()
                )

    assert offenders == []
    assert not (runtime_root / "materialization").exists()
    assert (runtime_root / "runtime_context/workspace_materialization.py").is_file()
    assert (runtime_root / "semantic_functions/resolution.py").is_file()
    assert (runtime_root / "semantic_functions/execution.py").is_file()
    assert (runtime_root / "snapshots/commit.py").is_file()


def test_api_compile_imports_without_forbidden_runtime_dependencies() -> None:
    script = textwrap.dedent(
        """
        import builtins

        real_import = builtins.__import__
        forbidden_prefixes = {
            "aware_runtime",
            "aware_service_runtime",
            "aware_meta_service",
            "aware_meta_service_dto",
            "aware_meta_service_protocol",
        }

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if any(name.startswith(prefix) for prefix in forbidden_prefixes):
                error = ModuleNotFoundError(f"No module named {name!r}")
                error.name = name
                raise error
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

        from aware_api_runtime.compile import (
            compile_api_accessible_dependency_graphs_via_meta_runtime,
            compile_api_workspace,
        )

        assert compile_api_accessible_dependency_graphs_via_meta_runtime is not None
        assert compile_api_workspace is not None
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_api_compile_plan_materialization_imports_without_env_artifacts() -> None:
    """API ontology materialization is deployable runtime surface, not env-artifacts."""

    script = textwrap.dedent(
        """
        import builtins

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("aware_environment_artifacts") or name.startswith("aware_runtime"):
                error = ModuleNotFoundError(f"No module named {name!r}")
                error.name = name
                raise error
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

        from aware_api_runtime.compile_materialization.service import (
            materialize_api_compile_plan_ontology,
        )

        assert materialize_api_compile_plan_ontology is not None
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_api_runtime_resolution_imports_without_env_artifacts() -> None:
    """API runtime resolution consumes prepared artifacts; env-artifacts is upstream."""

    script = textwrap.dedent(
        """
        import builtins

        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("aware_environment_artifacts"):
                error = ModuleNotFoundError(f"No module named {name!r}")
                error.name = name
                raise error
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import

        from aware_api_runtime.dependencies.runtime_resolution import (
            resolve_api_workspace_runtime_manifest,
        )

        assert resolve_api_workspace_runtime_manifest is not None
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_api_runtime_internals_use_dependencies_runtime_resolution_boundary() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    retired_facade = runtime_root / "runtime_resolution.py"
    forbidden_tokens = (
        "aware_api_runtime." + "runtime_resolution",
        "from .runtime_resolution import",
        "from .." + "runtime_resolution import",
        "from ..." + "runtime_resolution import",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert not retired_facade.exists()


def test_api_runtime_internals_use_source_feature_boundary() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    retired_facades = {
        runtime_root / "compiler.py",
        runtime_root / "semantic_analysis.py",
    }
    source_root = runtime_root / "source"
    forbidden_tokens = (
        "aware_api_runtime." + "compiler",
        "aware_api_runtime." + "semantic_analysis",
        "from .compiler import",
        "from .semantic_analysis import",
        "from .." + "compiler import",
        "from .." + "semantic_analysis import",
        "from ..." + "compiler import",
        "from ..." + "semantic_analysis import",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if source_root in source_path.parents:
            continue
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert all(not facade.exists() for facade in retired_facades)


def test_api_runtime_root_facades_are_retired() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    retired_facades = (
        runtime_root / "builder.py",
        runtime_root / "compiler.py",
        runtime_root / "runtime_resolution.py",
        runtime_root / "semantic_analysis.py",
    )
    forbidden_tokens = (
        "aware_api_runtime." + "builder",
        "aware_api_runtime." + "compiler",
        "aware_api_runtime." + "runtime_resolution",
        "aware_api_runtime." + "semantic_analysis",
        "from .." + "builder import",
        "from .." + "compiler import",
        "from .." + "runtime_resolution import",
        "from .." + "semantic_analysis import",
        "from ..." + "builder import",
        "from ..." + "compiler import",
        "from ..." + "runtime_resolution import",
        "from ..." + "semantic_analysis import",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert all(not facade.exists() for facade in retired_facades)


def test_api_runtime_internals_use_packages_feature_boundary() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    forbidden_tokens = (
        "aware_api_runtime." + "products",
        "from ." + "products import",
        "from .." + "products import",
        "from ..." + "products import",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert not (runtime_root / "products").exists()


def test_api_runtime_internals_use_ontology_graph_feature_boundary() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    forbidden_tokens = (
        "aware_api_runtime." + "graph",
        "from ." + "graph import",
        "from .." + "graph import",
        "from ..." + "graph import",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert not (runtime_root / "graph").exists()


def test_api_runtime_invocation_materialization_boundary_is_explicit() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    tests_root = runtime_root.parent / "tests"
    retired_package = runtime_root / "ontology"
    forbidden_tokens = (
        "aware_api_runtime." + "ontology.materialization",
        "from aware_api_runtime." + "ontology import",
        "from .." + "ontology.materialization",
        "from ..." + "ontology.materialization",
    )
    offenders: list[str] = []
    for source_root in (runtime_root, tests_root):
        for source_path in sorted(source_root.rglob("*.py")):
            if "__pycache__" in source_path.parts:
                continue
            source = source_path.read_text(encoding="utf-8")
            if any(token in source for token in forbidden_tokens):
                offenders.append(
                    source_path.relative_to(runtime_root.parent).as_posix()
                )

    assert offenders == []
    assert not retired_package.exists()


def test_api_runtime_workspace_provider_boundary_is_explicit() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    retired_paths = (
        runtime_root / "materialization" / "workspace_provider.py",
        runtime_root / "materialization" / "deltas",
    )
    forbidden_tokens = (
        "aware_api_runtime." + "materialization.workspace_provider",
        "aware_api_runtime." + "materialization.deltas",
        "from aware_api_runtime." + "materialization import workspace_provider",
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
    assert all(not path.exists() for path in retired_paths)


def test_api_workspace_provider_public_surface_imports() -> None:
    import aware_api_runtime.workspace_provider as workspace_provider
    from aware_api_runtime.workspace_provider import deltas

    assert workspace_provider.materialize is not None
    assert workspace_provider.materialize_delta is not None
    assert deltas.materialize_delta is not None
    assert deltas.api_delta_materialization_event_report is not None


def test_api_import_boundary_tests_do_not_execute_legacy_runtime_ops() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    legacy_ops_import = (
        "from " + "aware_" + "runtime.environment.operation.ops import experience"
    )

    assert legacy_ops_import not in source


def test_api_compile_runtime_has_no_compat_authored_graph_mode() -> None:
    runtime_root = (
        REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "api"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_api_runtime"
    )
    forbidden_tokens = (
        "compat_authored",
        "dependency_graph_mode='compat",
        'dependency_graph_mode="compat',
        "dependency_graph_mode='authored",
        'dependency_graph_mode="authored',
    )
    offenders: list[str] = []
    for source_path in sorted(runtime_root.rglob("*.py")):
        if "__pycache__" in source_path.parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden_tokens):
            offenders.append(source_path.relative_to(runtime_root).as_posix())

    assert offenders == []
