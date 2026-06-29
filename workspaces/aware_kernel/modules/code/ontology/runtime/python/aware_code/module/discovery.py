"""Code module discovery system for detecting logical modules in different programming languages."""

from collections import defaultdict
from collections.abc import Iterable
from abc import ABC, abstractmethod
from pathlib import Path

from aware_code.language.schemas import CodeDiscoveryFile
from aware_code.module.schemas import CodeModuleInfo

from aware_utils.logging import logger


class CodeModuleDiscovery(ABC):
    """Base implementation of code module discovery with common utilities and discovery logic."""

    @abstractmethod
    def is_module_root(self, path: Path, workspace_root: Path) -> bool:
        """Check if a directory is a module root."""
        pass

    @abstractmethod
    def get_module_name(self, module_path: Path, workspace_root: Path) -> str:
        """Get the module name from a root directory."""
        pass

    def get_entry_points(self, module_path: Path, workspace_root: Path) -> list[Path]:
        """Default implementation returns empty list. Override in subclasses."""
        _ = (module_path, workspace_root)
        return []

    def get_metadata(self, module_path: Path, workspace_root: Path) -> dict[str, object]:
        """Default implementation returns empty dict. Override in subclasses."""
        _ = (module_path, workspace_root)
        return {}


def discover_modules(*, workspace_root: Path, files: Iterable[CodeDiscoveryFile]) -> list[CodeModuleInfo]:
    """Discover code modules from a neutral repository file snapshot."""
    from aware_code.language.registry import CodeLanguagePluginRegistry

    trees_by_lang: dict[object, dict[str, str]] = defaultdict(dict)
    for file_info in files:
        if file_info.language is None:
            continue
        trees_by_lang[file_info.language][file_info.relative_path] = file_info.file_content

    discovered_modules: list[CodeModuleInfo] = []

    for language, file_tree in trees_by_lang.items():
        try:
            plugin = CodeLanguagePluginRegistry.get(language)
            if not plugin.module_discovery:
                continue

            modules = plugin.discover_modules(file_tree, workspace_root)
            discovered_modules.extend(modules)
            for module in modules:
                logger.debug(
                    "Discovered %s module: %s at %s",
                    module.language.value,
                    module.name,
                    module.root_path,
                )
        except Exception as exc:
            logger.warning(f"Failed to discover modules for {language.value}: {exc}")
            continue

    discovered_modules.sort(
        key=lambda module: (
            str(module.root_path),
            module.name,
            module.language.value,
        )
    )
    logger.info(
        "✅ Discovered %s modules across %s languages",
        len(discovered_modules),
        len(trees_by_lang),
    )
    return discovered_modules
