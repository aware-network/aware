from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Iterator

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package.registry import SemanticPackageRegistry
from aware_code.semantic_scope.registry import SemanticScopeRegistry
from aware_code_ontology.code.code_enums import CodeLanguage


@contextmanager
def _isolated_semantic_registries(*, runtime_roots: tuple[Path, ...]) -> Iterator[None]:
    AwareModulePluginRegistry.clear()
    SemanticPackageRegistry.clear()
    SemanticScopeRegistry.clear()
    try:
        yield
    finally:
        AwareModulePluginRegistry.clear()
        SemanticPackageRegistry.clear()
        SemanticScopeRegistry.clear()
        for runtime_root in runtime_roots:
            runtime_root_text = runtime_root.resolve().as_posix()
            while runtime_root_text in sys.path:
                sys.path.remove(runtime_root_text)
        for module_name in tuple(sys.modules):
            if module_name.startswith("selected_semantic_runtime") or (
                module_name.startswith("empty_semantic_runtime")
            ):
                sys.modules.pop(module_name, None)


def test_semantic_registries_refresh_from_late_module_plugins(
    tmp_path: Path,
) -> None:
    selected_root = _write_semantic_module(
        tmp_path,
        module_id="selected",
        provider_key="aware_selected",
        runtime_package="selected_semantic_runtime",
        manifest_kind="aware_selected_toml",
        semantic_scope_keys=("aware_selected.scope",),
        include_semantic_scope=True,
    )
    empty_root = _write_semantic_module(
        tmp_path,
        module_id="empty",
        provider_key="aware_empty",
        runtime_package="empty_semantic_runtime",
        manifest_kind="aware_empty_toml",
        semantic_scope_keys=(),
        include_semantic_scope=False,
    )
    runtime_roots = (
        selected_root / "runtime",
        empty_root / "runtime",
    )

    with _isolated_semantic_registries(runtime_roots=runtime_roots):
        SemanticPackageRegistry.ensure_builtin_providers_registered()
        SemanticScopeRegistry.ensure_builtin_providers_registered()

        AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
            module_roots=(selected_root, empty_root),
        )
        SemanticPackageRegistry.refresh_from_registered_module_plugins()
        SemanticScopeRegistry.refresh_from_registered_module_plugins()

        assert "aware_selected" in SemanticPackageRegistry.get_provider_keys()
        assert "aware_empty" in SemanticPackageRegistry.get_provider_keys()
        assert "aware_selected" in SemanticScopeRegistry.get_provider_keys()
        assert "aware_empty" not in SemanticScopeRegistry.get_provider_keys()

        code_package = SemanticPackageRegistry.enrich_code_package(
            CodePackageInfo(
                name="selected-package",
                root_path=Path("modules/selected/package"),
                manifest_path=Path("modules/selected/package/aware.selected.toml"),
                language=CodeLanguage.aware,
                metadata={
                    "manifest_kind": "aware_selected_toml",
                    "package_kind": "demo",
                    "fqn_prefix": "aware_selected",
                },
            )
        )
        [descriptor] = code_package.semantic_packages
        assert descriptor.provider_key == "aware_selected"
        assert descriptor.semantic_scope_keys == ("aware_selected.scope",)

        resolutions = SemanticScopeRegistry.resolve(
            code_package,
            workspace_root=tmp_path,
            provider_keys=("aware_selected",),
            scope_keys=("aware_selected.scope",),
        )

    assert [(item.provider_key, item.scope_key) for item in resolutions] == [
        ("aware_selected", "aware_selected.scope")
    ]


def _write_semantic_module(
    root: Path,
    *,
    module_id: str,
    provider_key: str,
    runtime_package: str,
    manifest_kind: str,
    semantic_scope_keys: tuple[str, ...],
    include_semantic_scope: bool,
) -> Path:
    module_root = root / "modules" / module_id
    runtime_root = module_root / "runtime"
    package_root = runtime_root / runtime_package
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "runtime"',
                "",
                "[[plugins]]",
                'kind = "code.module_plugin"',
                f'provider_key = "{provider_key}"',
                f'semantic_contract_module = "{runtime_package}.semantic_contract"',
                "",
                "[[packages]]",
                'id = "runtime"',
                'kind = "runtime"',
                'manifest = "runtime/pyproject.toml"',
                'visibility = "module"',
                "",
                "[packages.semantic_contract]",
                f'role = "{provider_key}.provider"',
                'contract = "aware.semantic_provider"',
                f'provider_key = "{provider_key}"',
                f'module = "{runtime_package}.semantic_contract"',
                f'owns_manifest_kinds = ["{manifest_kind}"]',
                'capabilities = ["semantic_analysis"]',
                "",
            )
        ),
        encoding="utf-8",
    )
    (package_root / "semantic_contract.py").write_text(
        "\n".join(
            (
                "from aware_code.module_semantic_contract import (",
                "    ModuleSemanticContract,",
                "    ModuleSemanticManifestResolutionDescriptor,",
                ")",
                "",
                "AWARE_MODULE_SEMANTIC_CONTRACT = ModuleSemanticContract(",
                f'    provider_key="{provider_key}",',
                f"    semantic_scope_keys={semantic_scope_keys!r},",
                "    manifest_resolution=(",
                "        ModuleSemanticManifestResolutionDescriptor(",
                f'            semantic_owner="{provider_key}.provider",',
                f'            manifest_kind="{manifest_kind}",',
                '            filename="aware.demo.toml",',
                '            contract="aware.demo",',
                f'            loader_module="{runtime_package}.loader",',
                '            loader_name="load_demo",',
                '            semantic_package_family="demo",',
                '            semantic_package_kind="demo_package",',
                '            copy_code_package_metadata_keys=("fqn_prefix",),',
                "        ),",
                "    ),",
                ")",
                "",
            )
        ),
        encoding="utf-8",
    )
    if include_semantic_scope:
        (package_root / "semantic_scope.py").write_text(
            "\n".join(
                (
                    "from aware_code.semantic_scope import (",
                    "    SemanticScopeProvider,",
                    "    SemanticScopeRegistry,",
                    "    SemanticScopeResolution,",
                    ")",
                    "",
                    "class _DemoSemanticScopeProvider(SemanticScopeProvider):",
                    "    @property",
                    "    def provider_key(self) -> str:",
                    f'        return "{provider_key}"',
                    "",
                    "    @property",
                    "    def scope_keys(self) -> tuple[str, ...]:",
                    f"        return {semantic_scope_keys!r}",
                    "",
                    "    def resolve(self, code_package, *, workspace_root):",
                    "        del workspace_root",
                    '        if code_package.metadata.get("manifest_kind") '
                    f'!= "{manifest_kind}":',
                    "            return ()",
                    "        return (",
                    "            SemanticScopeResolution(",
                    f"                scope_key={semantic_scope_keys[0]!r},",
                    f'                provider_key="{provider_key}",',
                    '                payload={"package": code_package.name},',
                    "            ),",
                    "        )",
                    "",
                    "def register_semantic_scope_providers() -> None:",
                    "    SemanticScopeRegistry.register(_DemoSemanticScopeProvider())",
                    "",
                )
            ),
            encoding="utf-8",
        )
    return module_root
