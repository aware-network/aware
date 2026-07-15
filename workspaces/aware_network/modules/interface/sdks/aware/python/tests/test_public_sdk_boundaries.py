from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import re
import tomllib
from typing import Any, cast


_REPO_ROOT = Path(__file__).resolve().parents[8]


@dataclass(frozen=True, slots=True)
class PublicPackage:
    name: str
    package_dir: Path
    pyproject_path: Path
    readme_path: Path
    readme_phrases: tuple[str, ...]
    kind: str = "sdk"


PUBLIC_PACKAGES = (
    PublicPackage(
        name="aware-environment-service-api",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/apis/environment/python/aware_environment_service_api"
        / "aware_environment_service_api",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/apis/environment/python/aware_environment_service_api/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/apis/environment/python/aware_environment_service_api/README.md",
        readme_phrases=(
            "Generated API client package",
            "public caller boundary",
            "aware-api-client",
            "does not expose or depend on Service internals",
        ),
        kind="generated_api_client",
    ),
    PublicPackage(
        name="aware-workspace-service-api",
        package_dir=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/apis/workspace/python/aware_workspace_service_api"
        / "aware_workspace_service_api",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/apis/workspace/python/aware_workspace_service_api/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/apis/workspace/python/aware_workspace_service_api/README.md",
        readme_phrases=(
            "Generated API client package",
            "public caller boundary",
            "aware-api-client",
            "does not expose or depend on Service internals",
        ),
        kind="generated_api_client",
    ),
    PublicPackage(
        name="aware-hub-service-api",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/apis/hub/python/aware_hub_service_api"
        / "aware_hub_service_api",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/apis/hub/python/aware_hub_service_api/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/apis/hub/python/aware_hub_service_api/README.md",
        readme_phrases=(
            "Generated API client package",
            "public caller boundary",
            "aware-api-client",
            "not the public `aware hub ...` product rail",
        ),
        kind="generated_api_client",
    ),
    PublicPackage(
        name="aware-identity-service-api",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/identity/apis/identity/python/aware_identity_service_api"
        / "aware_identity_service_api",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/identity/apis/identity/python/aware_identity_service_api/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/identity/apis/identity/python/aware_identity_service_api/README.md",
        readme_phrases=(
            "Generated API client package",
            "public caller boundary",
            "aware-api-client",
            "does not expose or depend on Service internals",
        ),
        kind="generated_api_client",
    ),
    PublicPackage(
        name="aware-conversation-sdk",
        package_dir=(
            _REPO_ROOT
            / "workspaces/aware_coordination/modules/conversation/sdks/conversation/python/aware_conversation_sdk"
        ),
        pyproject_path=(
            _REPO_ROOT
            / "workspaces/aware_coordination/modules/conversation/sdks/conversation/python/pyproject.toml"
        ),
        readme_path=(
            _REPO_ROOT
            / "workspaces/aware_coordination/modules/conversation/sdks/conversation/python/README.md"
        ),
        readme_phrases=(
            "Handwritten SDK facade",
            "Wraps the generated Conversation API client only",
            "Does not import Service internals",
        ),
    ),
    PublicPackage(
        name="aware-environment-sdk",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/sdks/environment/python/aware_environment_sdk",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/sdks/environment/python/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/environment/sdks/environment/python/README.md",
        readme_phrases=(
            "Handwritten SDK facade",
            "Wraps the generated Environment API client only",
            "Does not import Service internals",
        ),
    ),
    PublicPackage(
        name="aware-hub-sdk",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/sdks/hub/python/aware_hub_sdk",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/sdks/hub/python/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/hub/sdks/hub/python/README.md",
        readme_phrases=(
            "Handwritten SDK facade",
            "Wraps the generated Hub Api Client only",
            "Does not import Service internals",
        ),
    ),
    PublicPackage(
        name="aware-identity-sdk",
        package_dir=(
            _REPO_ROOT
            / "workspaces/aware_network/modules/identity/sdks/identity/python/public/aware_identity_sdk"
        ),
        pyproject_path=(
            _REPO_ROOT
            / "workspaces/aware_network/modules/identity/sdks/identity/python/public/pyproject.toml"
        ),
        readme_path=(
            _REPO_ROOT
            / "workspaces/aware_network/modules/identity/sdks/identity/python/public/README.md"
        ),
        readme_phrases=(
            "Handwritten SDK facade",
            "Wraps the generated Identity API client only",
            "Does not import Service internals",
        ),
    ),
    PublicPackage(
        name="aware-workspace-sdk",
        package_dir=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md",
        readme_phrases=(
            "Handwritten SDK facade",
            "Wraps the generated Workspace API client for Workspace lifecycle calls",
            "Does not import Service internals",
        ),
    ),
    PublicPackage(
        name="aware-interface-sdk",
        package_dir=_REPO_ROOT
        / "workspaces/aware_network/modules/interface/sdks/interface/python/aware_interface_sdk",
        pyproject_path=_REPO_ROOT
        / "workspaces/aware_network/modules/interface/sdks/interface/python/pyproject.toml",
        readme_path=_REPO_ROOT
        / "workspaces/aware_network/modules/interface/sdks/interface/python/README.md",
        readme_phrases=(
            "Handwritten Interface SDK facade",
            "generated Interface service API",
            "does not import Interface service internals",
        ),
    ),
)


FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "aware_api_runtime",
        "aware_code",
        "aware_code_ontology",
        "aware_conversation_service",
        "aware_conversation_service_protocol",
        "aware_environment_service",
        "aware_environment_service_protocol",
        "aware_environment_service_service",
        "aware_hub_service",
        "aware_hub_service_protocol",
        "aware_hub_service_service",
        "aware_identity_service",
        "aware_identity_service_protocol",
        "aware_identity_service_service",
        "aware_runtime",
        "aware_service",
        "aware_service_runtime",
        "aware_workspace_service",
        "aware_workspace_service_protocol",
        "aware_workspace_service_service",
    }
)


FORBIDDEN_DEPENDENCY_NAMES = frozenset(
    {
        "aware-api-runtime",
        "aware-code",
        "aware-code-ontology",
        "aware-conversation-service",
        "aware-conversation-service-protocol",
        "aware-environment-service",
        "aware-environment-service-protocol",
        "aware-environment-service-service",
        "aware-hub-service",
        "aware-hub-service-protocol",
        "aware-hub-service-service",
        "aware-identity-service",
        "aware-identity-service-protocol",
        "aware-identity-service-service",
        "aware-runtime",
        "aware-service",
        "aware-service-runtime",
        "aware-workspace-service",
        "aware-workspace-service-protocol",
        "aware-workspace-service-service",
    }
)

PUBLIC_FACADE_MANIFEST = _REPO_ROOT / "configs/public/aware_sdk_api_facade.toml"


def test_public_sdk_slice_has_no_private_runtime_imports() -> None:
    violations: list[str] = []
    for package in PUBLIC_PACKAGES:
        for path in _python_files(package.package_dir):
            for import_root in _import_roots(path):
                if import_root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(
                        f"{path.relative_to(_REPO_ROOT)} imports {import_root}"
                    )

    assert not violations, "\n".join(violations)


def test_public_sdk_slice_has_no_private_runtime_dependencies() -> None:
    violations: list[str] = []
    for package in PUBLIC_PACKAGES:
        for dependency in _project_dependencies(package.pyproject_path):
            dependency_name = _normalize_distribution_name(dependency)
            if dependency_name in FORBIDDEN_DEPENDENCY_NAMES:
                relative = package.pyproject_path.relative_to(_REPO_ROOT)
                violations.append(f"{relative} depends on {dependency_name}")

    assert not violations, "\n".join(violations)


def test_public_sdk_readmes_state_product_boundary() -> None:
    violations: list[str] = []
    for package in PUBLIC_PACKAGES:
        readme = package.readme_path.read_text(encoding="utf-8")
        for phrase in package.readme_phrases:
            if phrase not in readme:
                relative = package.readme_path.relative_to(_REPO_ROOT)
                violations.append(f"{relative} missing phrase: {phrase!r}")

    assert not violations, "\n".join(violations)


def test_generated_api_clients_use_invoker_substrate() -> None:
    violations: list[str] = []
    for package in _generated_api_client_packages():
        for path in _python_files(package.package_dir):
            text = path.read_text(encoding="utf-8")
            if "AwareApiClient" in text or "aware_api.client" in text:
                relative = path.relative_to(_REPO_ROOT)
                violations.append(f"{relative} still references legacy AwareApiClient")
        readme = package.readme_path.read_text(encoding="utf-8")
        if "AwareApiEndpointInvoker" not in readme:
            relative = package.readme_path.relative_to(_REPO_ROOT)
            violations.append(f"{relative} missing AwareApiEndpointInvoker")

    assert not violations, "\n".join(violations)


def test_public_sdk_docs_avoid_internal_product_labels() -> None:
    violations: list[str] = []
    for package in PUBLIC_PACKAGES:
        for path in (package.readme_path, package.pyproject_path):
            text = path.read_text(encoding="utf-8")
            if "Product A" in text or "Product B" in text:
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)} contains internal product label"
                )

    assert not violations, "\n".join(violations)


def test_aware_sdk_default_interface_dependency_is_canonical() -> None:
    default_dependencies = tuple(
        _project_default_dependencies(
            _REPO_ROOT
            / "workspaces/aware_network/modules/interface/sdks/aware/python/pyproject.toml"
        )
    )

    assert default_dependencies == ("aware-interface-sdk",)


def test_aware_sdk_app_session_imports_only_the_shared_interface_sdk_rail() -> None:
    package_root = (
        _REPO_ROOT
        / "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk"
    )
    app_paths = (package_root / "app.py", package_root / "commands/app.py")
    imported_roots: set[str] = set()
    for path in app_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", maxsplit=1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                if node.module is not None:
                    imported_roots.add(node.module.split(".", maxsplit=1)[0])

    aware_roots = {root for root in imported_roots if root.startswith("aware_")}
    assert aware_roots == {"aware_interface_sdk"}

    source = "\n".join(path.read_text(encoding="utf-8") for path in app_paths)
    assert "aware_interface_service" not in source
    assert "aware_workspace" not in source
    assert "workspace_report" not in source
    assert "aware.app.toml" not in source


def test_aware_sdk_has_one_interface_owned_semantic_package_home() -> None:
    package_root = _REPO_ROOT / "workspaces/aware_network/modules/interface/sdks/aware"
    assert package_root.is_dir()
    assert not (_REPO_ROOT / "apps/aware-sdk").exists()

    manifest_path = package_root / "aware/aware.sdk.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    dependencies = cast(list[Mapping[str, object]], manifest["dependencies"])
    assert dependencies == [
        {
            "kind": "sdk_package",
            "package_name": "interface-sdk",
            "version_number": 1,
        }
    ]

    module_manifest_path = (
        _REPO_ROOT / "workspaces/aware_network/modules/interface/aware.module.toml"
    )
    module_manifest = tomllib.loads(module_manifest_path.read_text(encoding="utf-8"))
    packages = cast(list[Mapping[str, object]], module_manifest["packages"])
    aware_packages = [
        package for package in packages if package.get("id") == "aware_sdk"
    ]
    assert aware_packages == [
        {
            "id": "aware_sdk",
            "kind": "sdk",
            "manifest": "sdks/aware/aware/aware.sdk.toml",
            "visibility": "public",
        }
    ]


def test_aware_sdk_identity_uses_interface_sdk_api_surface() -> None:
    identity_command = (
        _REPO_ROOT
        / "workspaces/aware_network/modules/interface/sdks/aware/python/aware_sdk/commands/identity.py"
    ).read_text(encoding="utf-8")

    assert "interface_client.control_client.invoke_api" not in identity_command
    assert "interface_client.invoke_api_endpoint" in identity_command


def test_public_facade_manifest_exports_alignment_protocol_surface() -> None:
    manifest = tomllib.loads(PUBLIC_FACADE_MANIFEST.read_text(encoding="utf-8"))
    document_paths = cast(list[Mapping[str, str]], manifest["document_paths"])
    mappings = {item["target"]: item["source"] for item in document_paths}

    assert (
        mappings["LICENSE"]
        == "workspaces/aware_network/modules/interface/sdks/aware/LICENSE"
    )
    assert mappings["AGENTS.md"] == "AGENTS.md"
    assert mappings["docs/alignment/PROTOCOL.md"] == "docs/alignment/PROTOCOL.md"
    assert mappings["docs/alignment/README.md"] == "docs/alignment/README.md"
    assert mappings["docs/alignment/CURRENT.md"] == "docs/alignment/PUBLIC.md"
    assert mappings["docs/issues/PROTOCOL.md"] == "docs/issues/PROTOCOL.md"
    assert mappings["docs/feed/PROTOCOL.md"] == "docs/feed/PROTOCOL.md"
    assert mappings["docs/goals/PROTOCOL.md"] == "docs/goals/PROTOCOL.md"
    assert mappings["docs/specs/PROTOCOL.md"] == "docs/specs/PROTOCOL.md"


def test_public_facade_manifest_package_paths_exist_and_are_workspace_members() -> None:
    manifest = tomllib.loads(PUBLIC_FACADE_MANIFEST.read_text(encoding="utf-8"))
    package_paths = cast(list[str], manifest["package_paths"])
    violations: list[str] = []
    for package_path in package_paths:
        path = _REPO_ROOT / package_path
        if not path.exists():
            violations.append(f"{package_path} does not exist")
            continue
        if not (path / "pyproject.toml").is_file():
            violations.append(f"{package_path} has no pyproject.toml")

    assert not violations, "\n".join(violations)


def test_public_facade_manifest_exports_kernel_orm_and_installer_surface() -> None:
    manifest = tomllib.loads(PUBLIC_FACADE_MANIFEST.read_text(encoding="utf-8"))
    package_paths = set(cast(list[str], manifest["package_paths"]))
    tree_paths = set(cast(list[str], manifest["tree_paths"]))
    document_paths = cast(list[Mapping[str, str]], manifest["document_paths"])
    mappings = {item["target"]: item["source"] for item in document_paths}

    assert manifest["target_root"] == "targets/public/aware"
    assert (
        "workspaces/aware_network/modules/interface/sdks/aware/python" in package_paths
    )
    assert "workspaces/aware_kernel" in tree_paths
    assert "apps/web/aware_run/distribution/bootstrap/aware-dev-sdk" in tree_paths
    assert "workspaces/aware_kernel/libs/orm" in package_paths
    assert (
        "workspaces/aware_workspace/modules/workspace/apis/workspace/python/aware_workspace_service_dto"
        in package_paths
    )
    assert mappings["install-aware-dev.sh"] == "apps/web/aware_run/install-aware-dev.sh"
    assert mappings["install.sh"] == "apps/web/aware_run/install.sh"


def test_public_facade_target_root_allows_only_public_target_inside_repo() -> None:
    materializer = _load_public_facade_materializer()

    assert materializer._target_root_is_allowed(
        repo_root=_REPO_ROOT,
        target_root=_REPO_ROOT / "targets/public/aware",
    )
    assert materializer._target_root_is_allowed(
        repo_root=_REPO_ROOT,
        target_root=Path("/tmp/aware-public-facade"),
    )
    assert not materializer._target_root_is_allowed(
        repo_root=_REPO_ROOT,
        target_root=_REPO_ROOT,
    )
    assert not materializer._target_root_is_allowed(
        repo_root=_REPO_ROOT,
        target_root=_REPO_ROOT / "targets/workspace-authorities/aware",
    )


def test_public_facade_protocol_docs_do_not_publish_private_issue_refs() -> None:
    manifest = tomllib.loads(PUBLIC_FACADE_MANIFEST.read_text(encoding="utf-8"))
    document_paths = cast(list[Mapping[str, str]], manifest["document_paths"])
    violations: list[str] = []
    for item in document_paths:
        source = item["source"]
        target = item["target"]
        if not target.startswith("docs/") and target != "AGENTS.md":
            continue
        text = (_REPO_ROOT / source).read_text(encoding="utf-8")
        if "docs/issues/2026/" in text or "docs/feed/2026/" in text:
            violations.append(f"{source} -> {target}")

    assert not violations, "\n".join(violations)


def _python_files(package_dir: Path) -> Iterator[Path]:
    yield from sorted(path for path in package_dir.rglob("*.py") if path.is_file())


def _load_public_facade_materializer() -> Any:
    path = _REPO_ROOT / "scripts/public_facade/materialize_public_aware.py"
    spec = importlib.util.spec_from_file_location("materialize_public_aware", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load materializer from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generated_api_client_packages() -> Iterator[PublicPackage]:
    yield from (
        package for package in PUBLIC_PACKAGES if package.kind == "generated_api_client"
    )


def _import_roots(path: Path) -> Iterator[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.partition(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                yield node.module.partition(".")[0]


def _project_dependencies(pyproject_path: Path) -> Iterator[str]:
    data = cast(
        Mapping[str, object],
        tomllib.loads(pyproject_path.read_text(encoding="utf-8")),
    )
    project = _mapping_value(data.get("project"))
    if project is None:
        return
    yield from _string_list(project.get("dependencies"))
    optional_dependencies = _mapping_value(project.get("optional-dependencies"))
    if optional_dependencies is None:
        return
    for dependencies in optional_dependencies.values():
        yield from _string_list(dependencies)


def _project_default_dependencies(pyproject_path: Path) -> Iterator[str]:
    data = cast(
        Mapping[str, object],
        tomllib.loads(pyproject_path.read_text(encoding="utf-8")),
    )
    project = _mapping_value(data.get("project"))
    if project is None:
        return
    yield from _string_list(project.get("dependencies"))


def _normalize_distribution_name(dependency: str) -> str:
    name = re.split(r"\s*(?:\[|<|>|=|!|~|;|@)\s*", dependency, maxsplit=1)[0]
    return re.sub(r"[-_.]+", "-", name).lower()


def _mapping_value(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return None


def _string_list(value: object) -> Iterator[str]:
    if not isinstance(value, list):
        return
    for item in cast(list[object], value):
        if isinstance(item, str):
            yield item
