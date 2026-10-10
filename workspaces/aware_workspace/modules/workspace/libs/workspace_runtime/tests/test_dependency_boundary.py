from __future__ import annotations

import ast
import tomllib
from pathlib import Path


def _repository_root_from_manifest(start: Path) -> Path:
    location = start.resolve()
    for candidate in (location, *location.parents):
        manifest_path = candidate / "aware.repo.toml"
        if not manifest_path.is_file():
            continue
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("aware_repo") != 1:
            raise AssertionError(f"invalid Aware repository manifest: {manifest_path}")
        repo = manifest.get("repo")
        workspaces_dir = repo.get("workspaces_dir") if isinstance(repo, dict) else None
        if not isinstance(workspaces_dir, str) or not workspaces_dir.strip():
            raise AssertionError(
                f"Aware repository manifest has no workspaces_dir: {manifest_path}"
            )
        resolved_workspaces = (candidate / workspaces_dir).resolve()
        if not resolved_workspaces.is_dir():
            raise AssertionError(
                "Aware repository manifest declares a missing workspaces directory: "
                f"{resolved_workspaces}"
            )
        return candidate
    raise AssertionError(f"no Aware repository manifest above {location}")


def test_runtime_imports_only_stdlib_and_filesystem_provider() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    imported_roots: set[str] = set()
    for source_path in package_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    forbidden = {
        "aware_agent",
        "aware_dev",
        "aware_issue",
        "aware_meta",
        "aware_orm",
        "aware_service",
        "aware_workspace",
        "aware_workspace_service_api",
        "aware_workspace_service_dto",
    }
    assert imported_roots.isdisjoint(forbidden)
    assert {root for root in imported_roots if root.startswith("aware_")} == {
        "aware_file_system",
        "aware_code_package_delta_contract",
        "aware_code_semantic_contract_runtime",
        "aware_local_service_runtime",
        "aware_workspace_sdk",
        "aware_workspace_fs_adapter",
    }


def test_project_dependencies_are_exactly_filesystem_and_neutral_service() -> None:
    project = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    dependencies = project["project"]["dependencies"]
    assert dependencies == [
        "aware-code-package-delta-contract>=0.1.0",
        "aware-code-semantic-contract-runtime>=0.1.0",
        "aware-file-system>=0.1.2",
        "aware-local-service-runtime>=0.1.0",
    ]
    for forbidden in (
        "ontology",
        "service-api",
        "service-dto",
        "aware-orm",
        "materialization",
    ):
        assert all(forbidden not in dependency.lower() for dependency in dependencies)


def test_materialize_command_pack_is_product_and_graph_runtime_free() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_command"
    imported_roots: set[str] = set()
    for source_path in package_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(
        {
            "aware_api",
            "aware_meta",
            "aware_ontology",
            "aware_orm",
            "aware_sdk",
            "aware_workspace",
        }
    )
    assert {root for root in imported_roots if root.startswith("aware_")} == {
        "aware_workspace_materialize_transport"
    }


def test_materialize_transport_contract_is_domain_runtime_free() -> None:
    package_root = (
        Path(__file__).resolve().parents[1] / "aware_workspace_materialize_transport"
    )
    imported_roots: set[str] = set()
    for source_path in package_root.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {
            "aware_api",
            "aware_meta",
            "aware_ontology",
            "aware_orm",
            "aware_sdk",
            "aware_workspace",
            "aware_workspace_runtime",
        }
    )


def test_change_evidence_values_and_codec_import_only_stdlib_and_local_runtime() -> (
    None
):
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    for filename in (
        "change_evidence.py",
        "change_evidence_codec.py",
        "repository_delta.py",
    ):
        tree = ast.parse((package_root / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level > 0 or (node.module or "").split(".", 1)[0] in {
                    "__future__",
                    "base64",
                    "bisect",
                    "dataclasses",
                    "datetime",
                    "enum",
                    "functools",
                    "pathlib",
                    "typing",
                    "types",
                }
            elif isinstance(node, ast.Import):
                assert all(
                    alias.name.split(".", 1)[0]
                    in {
                        "base64",
                        "dataclasses",
                        "datetime",
                        "enum",
                        "functools",
                        "hashlib",
                        "pathlib",
                        "typing",
                        "types",
                    }
                    for alias in node.names
                )


def test_delta_store_is_neutral_and_does_not_import_observer_or_consumers() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "repository_delta_store.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    assert relative_modules == {"repository_delta_store_contract"}
    for forbidden in (
        "WorkspaceRepositoryObservationSession",
        "WorkspaceRepositoryObservationProvider",
        "aware_agent",
        "aware_issue",
        "aware_dev",
        "aware_ontology",
        "aware_orm",
        "materialization",
        "import git",
    ):
        assert forbidden not in source


def test_revision_preparation_portable_modules_are_neutral() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    imported_roots: set[str] = set()
    relative_modules: set[str | None] = set()
    for filename in (
        "revision_preparation_codec.py",
        "revision_preparation_contracts.py",
    ):
        tree = ast.parse((package_root / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    relative_modules.add(node.module)
                elif node.module:
                    imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "hashlib",
        "json",
        "re",
        "threading",
        "typing",
        "weakref",
        "aware_code_semantic_contract_runtime",
        "collections",
    }
    assert relative_modules <= {"revision_preparation_codec"}
    for forbidden in ("ontology", "meta", "oig", "orm", "provider"):
        assert all(forbidden not in item.lower() for item in imported_roots)


def test_revision_preparation_has_no_installed_test_or_detached_registrar() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    production_sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in package_root.glob("*.py")
    }
    forbidden_symbols = (
        "_register_workspace_materialization_graph_execution_completion",
        "_issue_workspace_revision_preparation_context_for_test",
    )
    for symbol in forbidden_symbols:
        assert all(symbol not in source for source in production_sources.values())

    coordinator = ast.parse(
        production_sources["materialization_graph_coordinator.py"]
    )
    callable_names = {
        node.name
        for node in ast.walk(coordinator)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert all("revision_preparation" not in name or "verify" in name for name in callable_names)


def test_delta_capture_consumes_values_not_observer_or_consumer_runtime() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "repository_delta_capture.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    assert relative_modules == {
        "change_evidence",
        "contracts",
        "repository_access",
        "repository_delta",
    }
    for forbidden in (
        "WorkspaceRepositoryObservationSession",
        "WorkspaceRepositoryObservationProvider",
        "aware_agent",
        "aware_issue",
        "aware_dev",
        "aware_ontology",
        "aware_orm",
        "materialization",
        "import git",
    ):
        assert forbidden not in source


def test_delta_resident_consumes_journal_without_scanner_or_consumer_coupling() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "repository_delta_resident.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    assert relative_modules == {
        "change_evidence",
        "observation",
        "repository_delta",
        "repository_delta_capture",
        "repository_delta_resolution",
        "repository_delta_store_contract",
    }
    for forbidden in (
        "WorkspaceRepositoryObservationProvider",
        "FileSystemIndexObservationProvider",
        "FileSystemBackendObservationProvider",
        "aware_agent",
        "aware_issue",
        "aware_dev",
        "aware_ontology",
        "aware_orm",
        "materialization",
        "import git",
    ):
        assert forbidden not in source


def test_delta_resolution_is_body_free_and_consumer_neutral() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "repository_delta_resolution.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    assert relative_modules == {
        "change_evidence",
        "repository_access",
        "repository_delta",
    }
    for forbidden in (
        "resolve_body(",
        "read_bytes(",
        "WorkspaceRepositoryObservationProvider",
        "aware_agent",
        "aware_issue",
        "aware_dev",
        "aware_ontology",
        "aware_orm",
        "materialization",
        "import git",
    ):
        assert forbidden not in source


def test_dart_change_transport_is_filesystem_and_materialization_free() -> None:
    repository_root = _repository_root_from_manifest(Path(__file__))
    sources = (
        repository_root
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_documents/dart/aware_workspace_documents/lib/src/repository_change_evidence.dart",
        repository_root
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_documents/dart/aware_workspace_documents/lib/src/wire_protocol.dart",
        repository_root
        / "workspaces/aware_dev/modules/dev/libs/development_workspace/dart/aware_development_workspace/lib/src/workspace_document_host_server.dart",
        repository_root
        / "workspaces/aware_dev/modules/dev/sdks/local_dev/dart/aware_local_dev_sdk/lib/src/local_dev_workspace_document_client.dart",
    )
    for source_path in sources:
        source = source_path.read_text(encoding="utf-8")
        for forbidden in (
            "dart:io",
            "aware_file_system",
            "aware_ontology",
            "aware_orm",
            "service_api",
            "service_dto",
            "materialization",
        ):
            assert forbidden not in source


def test_repository_root_discovery_uses_manifest_not_ancestor_basename(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "portable-checkout"
    workspaces_root = repository_root / "workspaces"
    nested_source = workspaces_root / "package" / "aware" / "tests" / "test_source.py"
    nested_source.parent.mkdir(parents=True)
    (repository_root / "aware.repo.toml").write_text(
        'aware_repo = 1\n\n[repo]\nworkspaces_dir = "workspaces"\n',
        encoding="utf-8",
    )

    assert _repository_root_from_manifest(nested_source) == repository_root


def test_change_evidence_resolver_consumes_only_the_existing_observer_rail() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "change_evidence_resolver.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    assert relative_modules == {
        "change_evidence",
        "contracts",
        "observation",
        "repository_access",
    }
    for forbidden in (
        "WorkspaceSourceChangeSet",
        "WorkspaceRepositoryObservationJournal",
        "WorkspaceRepositoryObservationProvider",
        "FileSystemIndexObservationProvider",
        "aware_agent",
        "aware_issue",
        "aware_ontology",
        "aware_orm",
        "materialization",
    ):
        assert forbidden not in source


def test_mutation_and_diff_keep_workspace_authority_dependency_clean() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    expected_relative = {
        "repository_mutation.py": {
            "change_evidence",
            "contracts",
            "observation",
            "repository_access",
            "repository_diff",
        },
        "repository_diff.py": {"change_evidence"},
    }
    for filename, expected_modules in expected_relative.items():
        source = (package_root / filename).read_text(encoding="utf-8")
        tree = ast.parse(source)
        relative_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level > 0
        }
        absolute_roots = {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        absolute_roots.update(
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert relative_modules == expected_modules
        assert absolute_roots <= {
            "__future__",
            "aware_file_system",
            "asyncio",
            "collections",
            "dataclasses",
            "datetime",
            "difflib",
            "hashlib",
            "pathlib",
            "typing",
        }
        for forbidden in (
            "aware_agent",
            "aware_issue",
            "aware_ontology",
            "aware_orm",
            "ServiceHost",
            "materialization",
            "WorkspaceSourceChangeSet",
            "WorkspaceRepositoryObservationProvider",
        ):
            assert forbidden not in source


def test_materialization_session_uses_only_neutral_runtime_and_publication_contract() -> (
    None
):
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "materialization_session.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    absolute_roots = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0
    }
    absolute_roots.update(
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert relative_modules == {"semantic_materialization_publication"}
    assert absolute_roots <= {
        "__future__",
        "aware_code_semantic_contract_runtime",
        "aware_local_service_runtime",
        "collections",
        "dataclasses",
        "enum",
        "json",
        "threading",
        "time",
        "typing",
        "weakref",
    }
    for forbidden in (
        "aware_agent",
        "aware_dev",
        "aware_ontology",
        "aware_orm",
        "aware_sdk",
        "aware_service_api",
        "aware_service_dto",
        "aware_workspace_sdk",
        "aware_workspace_service",
        "FunctionImpl",
        "OIG",
        "OCG",
    ):
        assert forbidden not in source


def test_materialize_operation_composes_only_neutral_workspace_children() -> None:
    package_root = Path(__file__).resolve().parents[1] / "aware_workspace_runtime"
    source = (package_root / "materialization_operation.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    relative_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    }
    absolute_roots = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0
    }
    absolute_roots.update(
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert relative_modules == {
        "materialization_session",
        "semantic_dependency_graph",
        "semantic_materialization_publication",
    }
    assert absolute_roots <= {
        "__future__",
        "aware_code_semantic_contract_runtime",
        "collections",
        "dataclasses",
        "json",
        "threading",
        "time",
        "typing",
        "weakref",
    }
    for forbidden in (
        "aware_agent",
        "aware_api",
        "aware_dev",
        "aware_meta",
        "aware_ontology",
        "aware_orm",
        "aware_sdk",
        "aware_service_api",
        "aware_service_dto",
        "FunctionImpl",
        "OIG",
        "OCG",
        "importlib",
    ):
        assert forbidden not in source
