"""Language plugin system for code processing."""

from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Generic, Literal

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_code.language.layout import CodeLanguagePluginLayout
from aware_code.language.execution_closure import (
    CodeLanguageExecutionClosureBuilder,
    CodeLanguageExecutionClosureRequest,
    CodeLanguageExecutionClosureResult,
)
from aware_code.language.operational_workspace import (
    CodeLanguageOperationalWorkspaceBuilder,
    CodeLanguageOperationalWorkspaceRequest,
    CodeLanguageOperationalWorkspaceResult,
)
from aware_code.language.schemas import CodeDomain, StructuralFilterDecision
from aware_code.language.test_discovery import (
    CodeLanguageTestDiscovery,
    CodeTestDiscoveryContext,
    CodeTestDiscoveryResult,
    EMPTY_CODE_TEST_DISCOVERY_RESULT,
)
from aware_code.language.tooling import CodeLanguageToolSpec
from aware_code.module.discovery import CodeModuleDiscovery
from aware_code.module.schemas import CodeModuleInfo
from aware_code.package.discovery import CodePackageDiscovery
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package.registry import SemanticPackageRegistry
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.node.node import T_Node
from aware_code.section.metadata import CodeSectionMetadata
from aware_code.tree.adapter import CodeTreeAdapter
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter
from aware_code.primitive_codec import CodePrimitiveCodec


from aware_utils.logging import logger


QualityGateTargetMode = Literal["paths", "repo_root", "none"]


@dataclass(frozen=True)
class CodeLanguageMaterializationOutputDescriptor:
    """Language-owned declaration for materialization artifacts."""

    output_key: str
    description: str
    output_kind: str
    artifact_role: str
    path_templates: tuple[str, ...] = ()
    producer_step: str = "plugin_declared"
    required_for: tuple[str, ...] = ()
    renderer_profiles: tuple[str, ...] = ()
    renderer_kinds: tuple[str, ...] = ()
    materialization_sources: tuple[str, ...] = ()
    required: bool = False
    provider_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CodeLanguageQualityGate:
    """Language-owned quality gate command contract."""

    gate_id: str
    description: str
    command: tuple[str, ...]
    target_mode: QualityGateTargetMode = "paths"


@dataclass
class CodeLanguagePlugin(Generic[T_Node]):
    """
    Plugin definition for a programming language.

    Encapsulates all language-specific behavior including adapters,
    primitive types, metadata extraction logic, and syntax details.
    """

    language: CodeLanguage
    primitive_codec: CodePrimitiveCodec
    tree_sitter_adapter: CodeTreeAdapter[T_Node]
    node_adapters: dict[CodeSectionType, CodeNodeAdapter[T_Node]]
    metadata_adapters: dict[CodeSectionType, type[CodeSectionMetadata]]
    extensions: list[str]  # List of file extensions this language plugin supports
    comment_prefix: str  # Language-specific comment prefix (e.g., '#', '//', '--')
    # Type descriptor adapter (language-specific). Produces language-agnostic TypeNode trees.
    type_descriptor_adapter: CodeTypeDescriptorAdapter
    layout_plugin: CodeLanguagePluginLayout | None = None  # Domain/schema extraction logic
    module_discovery: CodeModuleDiscovery | None = None  # Module discovery logic
    package_discovery: CodePackageDiscovery | None = None  # Package discovery logic
    test_discovery: CodeLanguageTestDiscovery | None = None  # Package-scoped test discovery logic
    quality_gates: tuple[CodeLanguageQualityGate, ...] = ()
    tooling: tuple[CodeLanguageToolSpec, ...] = ()
    materialization_artifact_outputs: tuple[
        CodeLanguageMaterializationOutputDescriptor, ...
    ] = ()
    execution_closure_builder: CodeLanguageExecutionClosureBuilder | None = None
    operational_workspace_builder: CodeLanguageOperationalWorkspaceBuilder | None = None
    # Injected external structural filter (kernel/meta-level).
    # Signature: (relative_path, content) -> StructuralFilterDecision | bool
    injected_structural_filter: Callable[[str, str | None], StructuralFilterDecision | bool] | None = None

    def __post_init__(self):
        """Initialize default layout plugin if none provided."""
        if self.layout_plugin is None:
            from aware_code.language.layout import DefaultCodeLanguagePluginLayout

            self.layout_plugin = DefaultCodeLanguagePluginLayout()

    def extract_metadata(self, section_type: CodeSectionType, raw_comment: str) -> CodeSectionMetadata:
        """
        Extract metadata from a raw comment using the appropriate language plugin.

        Args:
            section_type: Type of code section (CLASS, FUNCTION, etc.)
            raw_comment: Raw comment text

        Returns:
            Parsed metadata with cleaned description
        """
        adapter = self.metadata_adapters.get(section_type)
        if not adapter:
            # No specific adapter for this section type
            return CodeSectionMetadata.from_raw_comment(raw_comment)

        return adapter.from_raw_comment(raw_comment)

    def is_structural(self, relative_path: str, file_content: str | None = None) -> bool:
        """
        Determine if a file should be considered structural (contributes to OCG).

        Args:
            relative_path: Relative path of the file from repository root
            file_content: Optional file content for content-based analysis

        Returns:
            True if the file should be processed for OCG, False for behavioural-only files
        """
        # External injected filter takes precedence when it returns a boolean
        if self.injected_structural_filter is not None:
            try:
                decision = self.injected_structural_filter(relative_path, file_content)
                if isinstance(decision, bool):
                    return decision
                if decision is StructuralFilterDecision.STRUCTURAL:
                    return True
                if decision is StructuralFilterDecision.NON_STRUCTURAL:
                    return False
            except Exception:
                # Ignore external filter errors to avoid breaking discovery
                pass

        # Default implementation: always structural
        # Language plugins should override this to implement filtering logic
        return True

    def update_cache_with_all_files(self, all_files: dict[str, str]) -> None:
        """
        Optional method for plugins that need cross-file analysis.

        Args:
            all_files: Dictionary mapping relative file paths to file contents

        This method is called before structural analysis to allow plugins to
        update their internal caches based on relationships between files.

        Default implementation does nothing - plugins override if needed.
        """
        # Default: no cross-file analysis needed
        _ = all_files
        pass

    def format_source(self, text: str, *, indent_size: int = 4) -> str | None:
        """Format source code for this language.

        Language servers (LSP) and CLIs should treat the formatter as a language plugin capability:
        the plugin owns the canonical formatting rules, while transports simply request edits.

        Args:
            text: Source text to format.
            indent_size: Indentation size (spaces) when formatting applies indentation.

        Returns:
            The formatted source string, or None when formatting is not supported.
        """
        _ = (text, indent_size)
        return None

    def materialize_execution_closure(
        self,
        request: CodeLanguageExecutionClosureRequest,
    ) -> CodeLanguageExecutionClosureResult:
        """Materialize an executable package closure through this language plugin."""
        if self.execution_closure_builder is None:
            raise NotImplementedError(
                f"No execution closure builder available for {self.language.value}"
            )
        return self.execution_closure_builder.materialize_execution_closure(request)

    def materialize_operational_workspace(
        self,
        request: CodeLanguageOperationalWorkspaceRequest,
    ) -> CodeLanguageOperationalWorkspaceResult:
        """Materialize an operational workspace through this language plugin."""
        if self.operational_workspace_builder is None:
            raise NotImplementedError(
                f"No operational workspace builder available for {self.language.value}"
            )
        return self.operational_workspace_builder.materialize_operational_workspace(
            request
        )

    def discover_modules(self, file_tree: dict[str, str], workspace_root: Path) -> list[CodeModuleInfo]:
        """
        Discover all modules for this language.

        Args:
            file_tree: Dictionary mapping relative file paths to their contents
            workspace_root: Root path of the workspace

        Returns:
            List of discovered modules for the language
        """
        if not self.module_discovery:
            logger.warning(f"No module discovery plugin available for {self.language.value}")
            return []

        modules: list[CodeModuleInfo] = []

        for directory_path in self._iter_candidate_directories(file_tree):
            try:
                if self.module_discovery.is_module_root(directory_path, workspace_root):
                    module_name = self.module_discovery.get_module_name(directory_path, workspace_root)
                    entry_points = self.module_discovery.get_entry_points(directory_path, workspace_root)
                    metadata = self.module_discovery.get_metadata(directory_path, workspace_root)

                    module_info = CodeModuleInfo(
                        name=module_name,
                        root_path=directory_path,
                        language=self.language,
                        entry_points=entry_points,
                        metadata=metadata,
                    )
                    modules.append(module_info)
                    logger.debug(f"Discovered {self.language.value} module: {module_name} at {directory_path}")

            except Exception as e:
                logger.warning(f"Failed to process potential module at {directory_path}: {e}")
                continue

        return modules

    def discover_packages(self, file_tree: dict[str, str], workspace_root: Path) -> list[CodePackageInfo]:
        """
        Discover all packages for this language.

        Args:
            file_tree: Dictionary mapping relative file paths to their contents
            workspace_root: Root path of the workspace

        Returns:
            List of discovered packages for the language
        """
        if not self.package_discovery:
            logger.warning(f"No package discovery plugin available for {self.language.value}")
            return []

        packages: list[CodePackageInfo] = []

        for directory_path in self._iter_candidate_directories(file_tree):
            try:
                if self.package_discovery.is_package_root(directory_path, workspace_root):
                    package_name = self.package_discovery.get_package_name(directory_path, workspace_root)
                    manifest_path = self.package_discovery.get_manifest_path(directory_path, workspace_root)
                    metadata = self.package_discovery.get_metadata(directory_path, workspace_root)

                    package_info = CodePackageInfo(
                        name=package_name,
                        root_path=directory_path,
                        manifest_path=manifest_path,
                        language=self.language,
                        metadata=metadata,
                    )
                    package_info = SemanticPackageRegistry.enrich_code_package(package_info)
                    packages.append(package_info)
                    logger.debug(f"Discovered {self.language.value} package: {package_name} at {directory_path}")

            except Exception as e:
                logger.warning(f"Failed to process potential package at {directory_path}: {e}")
                continue

        return packages

    def discover_tests(self, context: CodeTestDiscoveryContext) -> CodeTestDiscoveryResult:
        """Discover package-owned tests using the language plugin contract."""
        if not self.test_discovery:
            return EMPTY_CODE_TEST_DISCOVERY_RESULT
        return self.test_discovery.discover(context)

    def _iter_candidate_directories(self, file_tree: dict[str, str]) -> list[Path]:
        """Collect candidate directories from the file tree, including the workspace root."""
        if not file_tree:
            return []

        directories: set[Path] = {Path(".")}
        for file_path in file_tree.keys():
            path_obj = Path(file_path)
            directories.add(path_obj.parent)
            directories.update(path_obj.parents)

        return sorted(directories, key=lambda p: len(p.parts))

    def _clean_schema_name(self, schema_name: str) -> str:
        """
        Clean schema name by removing trailing underscores.

        This is needed because some schemas use trailing underscores to avoid
        language keyword conflicts (e.g., 'class_' instead of 'class').

        Args:
            schema_name: Raw schema name that might have trailing underscores

        Returns:
            Cleaned schema name with trailing underscores removed
        """
        return schema_name.rstrip("_")

    def get_domains_and_schemas(
        self,
        file_paths: list[str],
        enforce_domains_layout: bool = False,
        **_kwargs: object,
    ) -> list[CodeDomain]:
        """
        Extract domains and schemas using layout-based discovery.

        This method now only handles layout-based extraction using the language-specific
        layout plugin. Configuration-based and other discovery methods are handled
        at the repository level.

        Args:
            file_paths: List of relative file paths from repository root
            enforce_domains_layout: If True, only allow strict domains structure

        Returns:
            List of CodeDomain objects with their associated schemas
        """
        if not self.layout_plugin:
            logger.warning(f"No layout plugin available for {self.language.value}")
            return []

        try:
            domains = self.layout_plugin.extract_domains_and_schemas(
                file_paths,
                self.language,
                enforce_domains_layout,
            )
            logger.debug(f"Layout plugin extracted {len(domains)} domains for {self.language.value}")
            return domains
        except Exception as e:
            logger.error(f"Layout plugin failed for {self.language.value}: {e}")
            return []
